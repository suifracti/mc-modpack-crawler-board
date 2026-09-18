"""
Cutover Transaction / Resume Regression Tests (Architecture V2 - Phase 3G-F-B).

The previous full cutover completed its swap and was then killed while the
driving process appeared idle. Nothing durable recorded how far it had got, so
the remaining steps had to be finished by hand and there was no way to tell a
stall from a hang.

These tests lock down the recovery contract that replaced the guesswork:

  T1  stage ordering is monotonic and unambiguous
  T2  no journal                       -> fresh run
  T3  journal says "swapped" and production matches the staged manifest
                                       -> resume at the swap boundary (no re-copy)
  T4  journal says "swapped" but production diverged
                                       -> REFUSE, never overwrite silently
  T5  journal says "swapped" but the staging manifest content changed
                                       -> refuse to resume
  T6  journal is before the swap       -> safe to redo from the start
  T7  converted_output missing + staged modern tree valid
                                       -> complete the interrupted swap
  T8  converted_output missing + staged tree unusable
                                       -> roll back to the parked legacy tree
  T9  converted_output missing + nothing to restore from
                                       -> raise, do not invent a production
  T10 rollup digest is order independent
  T11 the journal write is atomic (tmp + replace) and round-trips
  T12 advance() records completed stages in order
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import pipeline.cutover_frontend_to_modern as ct  # noqa: E402
from pipeline.manifest import generate_manifest  # noqa: E402

PATCHED = [
    "CONVERTED_OUTPUT_DIR", "STAGING_TEMP_DIR", "SWAP_TEMP_DIR",
    "MODERN_STAGING_MANIFEST_PATH", "TRANSACTION_PATH",
]


def write_tree(root, files):
    for rel, content in files.items():
        p = os.path.join(root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fp:
            fp.write(content)


class CutoverTransactionTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="cutover_txn_")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.prod = os.path.join(self.root, "converted_output")
        self.staging_tmp = os.path.join(self.root, "modern_staging_temp")
        self.swap_tmp = os.path.join(self.root, "legacy_pre_cutover_swap")
        self.manifests = os.path.join(self.root, "manifests")
        os.makedirs(self.manifests, exist_ok=True)
        self.staging_manifest = os.path.join(self.manifests, "staging.json")
        self.txn_path = os.path.join(self.root, "cutover_transaction.json")

        self._saved = {name: getattr(ct, name) for name in PATCHED}
        ct.CONVERTED_OUTPUT_DIR = self.prod
        ct.STAGING_TEMP_DIR = self.staging_tmp
        ct.SWAP_TEMP_DIR = self.swap_tmp
        ct.MODERN_STAGING_MANIFEST_PATH = self.staging_manifest
        ct.TRANSACTION_PATH = self.txn_path
        ct._TIMINGS.clear()
        self.addCleanup(self._restore)

    def _restore(self):
        for name, value in self._saved.items():
            setattr(ct, name, value)
        ct._TIMINGS.clear()

    # -- helpers ----------------------------------------------------------
    def _make_modern_tree(self):
        write_tree(self.staging_tmp, {
            "index.html": "<html>modern</html>",
            "assets/index.js": "console.log(1)",
            "data/mcmod_data.js": "window.mcmodData=[]",
        })
        m = generate_manifest(self.staging_tmp, self.staging_manifest)
        return m

    def _journal(self, stage, staging_rollup=None):
        txn = {"stage": stage, "completed_stages": ct.STAGES[:ct.STAGES.index(stage) + 1]}
        if staging_rollup:
            txn["staging_rollup"] = staging_rollup
            txn["staging_manifest_path"] = self.staging_manifest
        ct.write_transaction(txn)
        return txn

    # -- T1 ---------------------------------------------------------------
    def test_t1_stage_order_is_monotonic(self):
        expected = ["prepared", "legacy_manifested", "legacy_backed_up",
                    "staging_manifested", "swapped", "post_swap_verified",
                    "state_written", "browser_verified", "complete"]
        self.assertEqual(ct.STAGES, expected)
        idx = [ct.stage_index(s) for s in expected]
        self.assertEqual(idx, sorted(idx))
        self.assertEqual(ct.stage_index("nonsense"), -1)

    # -- T2 ---------------------------------------------------------------
    def test_t2_no_journal_is_a_fresh_run(self):
        d = ct.plan_resume({}, allow_resume=True)
        self.assertIsNone(d["resume_stage"])

    # -- T3 ---------------------------------------------------------------
    def test_t3_resumes_at_swap_boundary_without_recopy(self):
        m = self._make_modern_tree()
        shutil.copytree(self.staging_tmp, self.prod)
        self._journal("swapped", ct.rollup_digest(m))
        d = ct.plan_resume(ct.read_transaction(), allow_resume=True)
        self.assertEqual(d["resume_stage"], "swapped")
        self.assertIn("skipping", d["reason"])

    # -- T4 ---------------------------------------------------------------
    def test_t4_refuses_when_production_diverged_after_swap(self):
        m = self._make_modern_tree()
        shutil.copytree(self.staging_tmp, self.prod)
        self._journal("swapped", ct.rollup_digest(m))
        # Someone edited production after the swap.
        with open(os.path.join(self.prod, "index.html"), "w", encoding="utf-8") as fp:
            fp.write("<html>tampered</html>")
        with self.assertRaises(RuntimeError) as ctx:
            ct.plan_resume(ct.read_transaction(), allow_resume=True)
        self.assertIn("Refusing to resume", str(ctx.exception))

    # -- T5 ---------------------------------------------------------------
    def test_t5_refuses_when_staging_manifest_changed(self):
        self._make_modern_tree()
        shutil.copytree(self.staging_tmp, self.prod)
        self._journal("swapped", "0" * 64)   # rollup that cannot match
        d = ct.plan_resume(ct.read_transaction(), allow_resume=True)
        self.assertIsNone(d["resume_stage"])
        self.assertIn("refusing", d["reason"].lower())

    # -- T6 ---------------------------------------------------------------
    def test_t6_before_swap_is_a_safe_redo(self):
        self._journal("legacy_backed_up")
        d = ct.plan_resume(ct.read_transaction(), allow_resume=True)
        self.assertIsNone(d["resume_stage"])
        self.assertIn("safe to redo", d["reason"])

    # -- T7 ---------------------------------------------------------------
    def test_t7_completes_interrupted_swap(self):
        m = self._make_modern_tree()
        self.assertFalse(os.path.exists(self.prod))
        write_tree(self.swap_tmp, {"index.html": "<html>legacy</html>"})
        txn = {}
        stage = ct.recover_torn_swap(txn)
        self.assertEqual(stage, "swapped")
        self.assertTrue(os.path.exists(self.prod))
        self.assertFalse(os.path.exists(self.staging_tmp))
        with open(os.path.join(self.prod, "index.html"), "r", encoding="utf-8") as fp:
            self.assertIn("modern", fp.read())
        self.assertEqual(txn.get("stage"), "swapped")
        self.assertTrue(os.path.exists(self.txn_path))

    # -- T8 ---------------------------------------------------------------
    def test_t8_rolls_back_when_staged_tree_unusable(self):
        # staging temp exists but does NOT match the staging manifest
        write_tree(self.staging_tmp, {"index.html": "<html>garbage</html>"})
        write_tree(self.swap_tmp, {"index.html": "<html>legacy</html>"})
        # Create a manifest that the garbage tree cannot satisfy.
        good = os.path.join(self.root, "good")
        write_tree(good, {"index.html": "<html>modern</html>"})
        generate_manifest(good, self.staging_manifest)

        txn = {}
        stage = ct.recover_torn_swap(txn)
        self.assertIsNone(stage)
        self.assertTrue(os.path.exists(self.prod))
        with open(os.path.join(self.prod, "index.html"), "r", encoding="utf-8") as fp:
            self.assertIn("legacy", fp.read())

    # -- T9 ---------------------------------------------------------------
    def test_t9_raises_when_nothing_can_be_restored(self):
        with self.assertRaises(RuntimeError) as ctx:
            ct.recover_torn_swap({})
        self.assertIn("needs a human", str(ctx.exception))

    # -- T10 --------------------------------------------------------------
    def test_t10_rollup_digest_is_order_independent(self):
        a = {"files": [
            {"path": "b.js", "sha256": "22"},
            {"path": "a.js", "sha256": "11"},
        ]}
        b = {"files": [
            {"path": "a.js", "sha256": "11"},
            {"path": "b.js", "sha256": "22"},
        ]}
        self.assertEqual(ct.rollup_digest(a), ct.rollup_digest(b))
        c = {"files": [{"path": "a.js", "sha256": "99"},
                       {"path": "b.js", "sha256": "22"}]}
        self.assertNotEqual(ct.rollup_digest(a), ct.rollup_digest(c))

    # -- T11 --------------------------------------------------------------
    def test_t11_journal_write_is_atomic_and_round_trips(self):
        txn = {"stage": "prepared", "completed_stages": ["prepared"]}
        ct.write_transaction(txn)
        self.assertFalse(os.path.exists(self.txn_path + ".tmp"),
                         "a temp journal file was left behind")
        loaded = ct.read_transaction()
        self.assertEqual(loaded["stage"], "prepared")
        self.assertIn("updated_at", loaded)
        self.assertIn("pid", loaded)

    def test_t11b_corrupt_journal_reads_as_empty(self):
        with open(self.txn_path, "w", encoding="utf-8") as fp:
            fp.write("{ not json")
        self.assertEqual(ct.read_transaction(), {})

    # -- T12 --------------------------------------------------------------
    def test_t12_advance_records_stages_in_order(self):
        txn = {}
        for stage in ["prepared", "legacy_manifested", "legacy_backed_up"]:
            ct.advance(txn, stage)
        self.assertEqual(txn["stage"], "legacy_backed_up")
        self.assertEqual(txn["completed_stages"],
                         ["prepared", "legacy_manifested", "legacy_backed_up"])
        ct.advance(txn, "legacy_backed_up")   # idempotent
        self.assertEqual(len(txn["completed_stages"]), 3)


    # -- T13 --------------------------------------------------------------
    def test_t13_acceptance_gates_are_not_skipped_on_a_fresh_run(self):
        """Regression: the stage order must match execution order.

        An earlier revision listed `browser_verified` before `state_written`,
        which made a completed fresh run skip its own acceptance gates.
        """
        self.assertTrue(ct.needs_browser_gates({}), "fresh run must run the gates")
        self.assertTrue(ct.needs_browser_gates({"stage": "state_written"}))
        self.assertTrue(ct.needs_browser_gates({"stage": "post_swap_verified"}))
        self.assertFalse(ct.needs_browser_gates({"stage": "browser_verified"}))
        self.assertFalse(ct.needs_browser_gates({"stage": "complete"}))
        # Execution order: state is written before the acceptance gates run.
        self.assertLess(ct.stage_index("state_written"),
                        ct.stage_index("browser_verified"))

    # -- T14 --------------------------------------------------------------
    def test_t14_resume_after_state_written_only_runs_the_gates(self):
        m = self._make_modern_tree()
        shutil.copytree(self.staging_tmp, self.prod)
        self._journal("state_written", ct.rollup_digest(m))
        d = ct.plan_resume(ct.read_transaction(), allow_resume=True)
        self.assertEqual(d["resume_stage"], "state_written")
        self.assertTrue(ct.needs_browser_gates({"stage": d["resume_stage"]}))


if __name__ == "__main__":
    unittest.main(verbosity=2)

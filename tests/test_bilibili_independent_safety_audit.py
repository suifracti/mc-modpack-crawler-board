"""Independent Phase 3G-F.3-A safety-audit regression tests.

These tests exercise the audit against the current runtime and assert that the
audit cannot turn incomplete independent evidence into a safety PASS.  The
temporary reports are disposable; frozen evidence and ground truth are never
rewritten.
"""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NODE = "node"
AUDIT = ROOT / "pipeline" / "audit" / "phase3gf_expanded_runtime_audit.js"


def run_node(args):
    env = dict(os.environ)
    env.setdefault("SOURCE_DATE_EPOCH", "1786000000")
    return subprocess.run(
        [NODE, str(AUDIT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )


class TestIndependentSafetyAudit(unittest.TestCase):
    def test_fault_injections_are_real_relation_checks(self):
        result = run_node(["--self-test"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("MUST split => false_split", result.stdout)
        self.assertIn("CANNOT merge => false_merge", result.stdout)
        self.assertIn("runtime rerun stable", result.stdout)

    def test_incomplete_independent_evidence_blocks_safety_pass(self):
        with tempfile.TemporaryDirectory(prefix="phase3gf-independent-audit-") as tmp:
            out = Path(tmp) / "audit.json"
            holdout = Path(tmp) / "holdout.json"
            result = run_node([
                "--out", str(out),
                "--holdout-out", str(holdout),
            ])
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            report = json.loads(out.read_text(encoding="utf-8"))
            holdout_report = report["holdout_independent"]

            self.assertEqual(report["status"], "BLOCKED")
            self.assertTrue(report["runtime"]["compiled_from_current_source"])
            self.assertTrue(
                holdout_report["source"]["membership_frozen_before_candidate_run"]
            )
            self.assertFalse(holdout_report["source"]["legacy_group_keys_used_as_labels"])
            self.assertFalse(
                holdout_report["source"]["candidate_output_used_to_select_members"]
            )
            self.assertFalse(
                holdout_report["independent_relation_labels"]["generation_contract_met"]
            )
            self.assertEqual(holdout_report["source"]["legacy_derived_positive_cases"], 40)
            self.assertEqual(holdout_report["source"]["legacy_derived_negative_cases"], 62)
            self.assertEqual(
                holdout_report["independent_relation_labels"]["total_cases"], 44
            )
            self.assertEqual(holdout_report["case_partition"]["conflict_cases"], 28)
            self.assertEqual(holdout_report["case_partition"]["unknown_coverage_cases"], 30)
            self.assertEqual(holdout_report["pairwise"]["false_merge"], 0)
            self.assertEqual(holdout_report["pairwise"]["false_split"], 0)
            self.assertGreater(holdout_report["pairwise"]["uncovered"], 0)
            self.assertGreater(holdout_report["pairwise"]["conflict"], 0)

            known = report["known_8_pair_audit"]
            self.assertEqual(
                (known["expected"], known["checked"], known["retired_by_pair"],
                 known["fault_injection_passed"]),
                (8, 8, 8, 8),
            )
            self.assertEqual(len(known["cases"]), 8)
            self.assertTrue(all(not case["still_merging"] for case in known["cases"]))
            self.assertTrue(all(
                case["fault_injection"]["detected_false_merge"]
                for case in known["cases"]
            ))

            population = report["population_936"]
            coverage = population["safety_audit"]["coverage"]
            self.assertEqual(population["stats"]["raw_records"], 936)
            self.assertEqual(population["stats"]["unique_bvids"], 936)
            self.assertEqual(coverage["confirmed_false_merges"], 0)
            self.assertEqual(coverage["false_split"], 0)
            self.assertGreater(coverage["uncovered"], 0)
            self.assertGreater(coverage["relation_conflict"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

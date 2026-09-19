"""
Phase 3G-F.2-B - under-merge ground-truth adjudication regression test.

Module 2 produced a REVIEW LIST: 58 uploader-scoped cluster candidates that might be
one logical pack the grouping algorithm split apart. This phase decides each one.

The dangerous failure modes this suite pins:

  * a candidate silently disappears and nobody notices (hence: every cluster must be
    adjudicated, and the count must match)
  * an AMBIGUOUS case leaks into the runtime gate (that would turn an admission of
    ignorance into a behaviour change)
  * the 涅槃 ground-truth lesson gets mis-encoded, i.e. the two 涅槃-labelled groups
    get merged back together. They are DIFFERENT packs, and merging them would
    introduce a real false merge.

DELIBERATELY NOT ASSERTED
  * that DISCONFIRMED cases are zero (they are not; 27 of 58 are different packs)
  * that the gate is large (it is SMALL by design - only what the evidence settles)
  * anything about the runtime grouping algorithm (this audit does not touch it)
"""
import hashlib
import gzip
import json
import os
import subprocess
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CANDIDATES = os.path.join(REPO_ROOT, "build", "audit",
                          "bilibili_cross_group_undermerge_v2.json")
IDENTITY = os.path.join(REPO_ROOT, "build", "audit",
                        "undermerge_project_identity_v2.json")
EVIDENCE = os.path.join(REPO_ROOT, "build", "audit", "undermerge_evidence_v2.json")
LEDGER = os.path.join(REPO_ROOT, "pipeline", "audit",
                      "bilibili_undermerge_adjudication_v2.json")
GATE = os.path.join(REPO_ROOT, "pipeline", "audit",
                    "confirmed_undermerge_runtime_gate.json")
OLD_ADJ = os.path.join(REPO_ROOT, "pipeline", "audit",
                       "bilibili_population_adjudication_v2.json")
OLD_HOLDOUT = os.path.join(REPO_ROOT, "pipeline", "audit",
                           "bilibili_population_holdout_v2.json")

# These are the committed 1bee6de corpus bytes.  They are intentionally kept
# separate from the cbbfb58/a690d3d adjudication corpus: A starts from 1bee6de,
# whose pre-existing population artifacts are gzip containers with the
# post-remediation 100/100 and 44/71 semantics.  The byte hashes prove that the
# compatibility reader did not replace or regenerate that ground truth.
OLD_ADJ_RAW_SHA256 = "a6a6a4f92c10bf0c9d87dfb9501263fd3967405e3d750ae8854282b0602d18a8"
OLD_HOLDOUT_RAW_SHA256 = "bb3da23781dc1a2ac82780c63c37c81a1273d933dd52571d2e5f588e11ecf072"

AUDIT_SCRIPTS = [
    "extract_undermerge_evidence.js",
    "extract_undermerge_project_identity.js",
    # must run AFTER the two extractors: it consumes their output
    "bilibili_undermerge_adjudication_v2.js",
    # additive gate builder; consumes the ledger
    "build_undermerge_runtime_gate.js",
]

VERDICTS = {"CONFIRMED_SAME_PACK", "STRONG_SAME_PACK",
            "DIFFERENT_PACKS", "AMBIGUOUS", "PARTIAL"}
GATED = {"CONFIRMED_SAME_PACK", "STRONG_SAME_PACK"}

# The 58 clusters traced back to the two 涅槃-labelled groups. These MUST NOT be
# merged: 涅槃 is one pack, 未尽之路-涅槃 is a different pack that merely uses the
# word as a subtitle.
NIRVANA_GROUP = "墨言eclipse::涅槃 无神明渡我 我亦是神明"
NOT_NIRVANA_GROUP = "墨言eclipse::未尽之路涅槃"


def load(path):
    # 1bee6de stores the two large legacy audit JSON files as gzip bytes while
    # retaining their historical .json paths.  Keep the raw-file identity
    # unchanged and adapt only the read path; never regenerate labels or
    # ground-truth from the current runtime.
    with open(path, "rb") as fp:
        raw = fp.read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return json.loads(raw.decode("utf-8"))


def raw_sha256(path):
    with open(path, "rb") as fp:
        return hashlib.sha256(fp.read()).hexdigest()


def run(cmd):
    # SOURCE_DATE_EPOCH pins `generated_at` so running this suite leaves the
    # tracked artifacts clean. Without it every run dirties two tracked files and
    # real drift hides behind timestamp noise.
    env = dict(os.environ)
    env.setdefault("SOURCE_DATE_EPOCH", "1786000000")
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env)


class TestBilibiliUnderMergeAdjudication(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        for script in AUDIT_SCRIPTS:
            r = run(["node", os.path.join("pipeline", "audit", script)])
            assert r.returncode == 0, f"{script} failed: {r.stdout}\n{r.stderr}"

        cls.cand = load(CANDIDATES)
        cls.identity = load(IDENTITY)
        cls.evidence = load(EVIDENCE)
        cls.ledger = load(LEDGER)
        cls.gate = load(GATE)

    # ------------------------------------------------------------- coverage
    def test_every_candidate_cluster_is_adjudicated(self):
        """The whole point: no candidate may be left undecided."""
        self.assertEqual(self.ledger["unadjudicated"], [],
                         "some under-merge candidates were never adjudicated")
        self.assertEqual(self.ledger["adjudicated_total"],
                         self.ledger["candidates_total"])

    def test_candidate_total_matches_the_scanner(self):
        """The ledger must cover exactly what module 2 flagged."""
        self.assertEqual(self.ledger["candidates_total"],
                         self.cand["clusters_flagged"])
        self.assertEqual(self.ledger["candidates_total"],
                         len(self.cand["findings"]))

    def test_no_duplicate_ledger_keys(self):
        keys = [f["cluster_key"] for f in self.ledger["findings"]]
        self.assertEqual(len(keys), len(set(keys)),
                         "duplicate cluster_key in the adjudication ledger")

    def test_every_ledger_entry_maps_to_a_candidate(self):
        live = {f["author"] + "||" + "|".join(sorted(f["group_keys"]))
                for f in self.cand["findings"]}
        for f in self.ledger["findings"]:
            self.assertIn(f["cluster_key"], live,
                          f"ledger entry not backed by a live cluster: {f['cluster_key']}")

    def test_no_undeclared_adjudication(self):
        """A verdict pointing at a cluster that does not exist is a silent typo."""
        self.assertEqual(self.ledger["declared_but_absent"], [])

    def test_every_entry_has_verdict_confidence_and_evidence(self):
        for f in self.ledger["findings"]:
            self.assertIn(f["verdict"], VERDICTS, f"bad verdict: {f['cluster_key']}")
            self.assertIn(f["confidence"], {"high", "medium", "low"},
                          f"bad confidence: {f['cluster_key']}")
            self.assertTrue(f["evidence"]["note"],
                            f"missing evidence note: {f['cluster_key']}")
            self.assertIsInstance(f["expected_identity_count"], int)
            self.assertGreaterEqual(f["expected_identity_count"], 1)

    def test_counts_match_the_rows(self):
        c = self.ledger["counts"]
        rows = self.ledger["findings"]
        for verdict in VERDICTS:
            self.assertEqual(c[verdict],
                             len([r for r in rows if r["verdict"] == verdict]),
                             f"count mismatch for {verdict}")
        self.assertEqual(sum(c[v] for v in VERDICTS), len(rows))

    # ------------------------------------------------------- 涅槃 correction
    def test_nirvana_expected_groups_is_two(self):
        """§2/§9: the 涅槃-labelled groups are TWO packs, not one."""
        ev = self.ledger["the_nirvana_lesson"]["evidence"]
        self.assertEqual(ev["expected_packs"], 2)
        # records: 5 belong to 涅槃, 2 to 未尽之路-涅槃
        self.assertEqual(ev["涅槃"]["records"], 5)
        self.assertEqual(ev["未尽之路-涅槃"]["records"], 2)

    def test_nirvana_and_its_namesake_are_not_merged(self):
        """The two 涅槃-labelled groups must be DIFFERENT packs in the ledger."""
        by_group = {}
        for f in self.ledger["findings"]:
            for gk in f["group_keys"]:
                by_group[gk] = f
        self.assertIn(NIRVANA_GROUP, by_group, "涅槃 group missing from ledger")
        self.assertIn(NOT_NIRVANA_GROUP, by_group,
                      "未尽之路涅槃 group missing from ledger")

        a = by_group[NIRVANA_GROUP]
        b = by_group[NOT_NIRVANA_GROUP]
        self.assertEqual(a["verdict"], "CONFIRMED_SAME_PACK")
        self.assertEqual(a["expected_identity_count"], 1)
        # the namesake must NOT be recorded as the same pack
        self.assertEqual(b["verdict"], "DIFFERENT_PACKS")
        self.assertGreaterEqual(b["expected_identity_count"], 2)
        self.assertNotEqual(a["cluster_key"], b["cluster_key"],
                            "涅槃 and 未尽之路涅槃 were placed in one cluster")

    def test_nirvana_identities_are_disjoint(self):
        """Ground the lesson in registered ids, not in prose."""
        a = set(self.ledger["the_nirvana_lesson"]["evidence"]["涅槃"]["identities"])
        b = set(self.ledger["the_nirvana_lesson"]["evidence"]["未尽之路-涅槃"]["identities"])
        self.assertTrue(a, "涅槃 must carry at least one registered identity")
        self.assertTrue(b, "未尽之路-涅槃 must carry at least one registered identity")
        self.assertEqual(a & b, set(),
                         "the two packs share a registered identity - lesson invalid")

    def test_nirvana_case_is_not_in_the_gate(self):
        gated_keys = {c["cluster_key"] for c in self.gate["cases"]}
        for f in self.ledger["findings"]:
            if NOT_NIRVANA_GROUP in f["group_keys"]:
                self.assertNotIn(f["cluster_key"], gated_keys,
                                 "the 涅槃 namesake leaked into the runtime gate")

    # ------------------------------------------------------------ runtime gate
    def test_ambiguous_is_never_in_the_runtime_gate(self):
        for c in self.gate["cases"]:
            self.assertIn(c["verdict"], GATED,
                          f"non-gated verdict in gate: {c['verdict']}")
            self.assertNotEqual(c["verdict"], "AMBIGUOUS")

    def test_gate_contains_only_confirmed_and_strong(self):
        self.assertEqual(set(self.gate["gated_verdicts"]), GATED)
        allowed = {f["cluster_key"] for f in self.ledger["findings"]
                   if f["verdict"] in GATED}
        self.assertEqual({c["cluster_key"] for c in self.gate["cases"]}, allowed)

    def test_every_gate_item_has_evidence(self):
        for c in self.gate["cases"]:
            self.assertTrue(c["evidence"], f"gate item without evidence: {c['cluster_key']}")
            self.assertIn(c["confidence"], {"high", "medium", "low"})
            self.assertGreaterEqual(c["expected_identity_count"], 1)
            self.assertEqual(c["expected_identity_count"], 1,
                             "a gated case must expect exactly one pack")

    def test_gate_excludes_everything_not_confirmed(self):
        excluded = {c["cluster_key"] for c in self.gate["excluded_cases"]}
        for f in self.ledger["findings"]:
            if f["verdict"] not in GATED:
                self.assertIn(f["cluster_key"], excluded,
                              f"non-gated case not listed as excluded: {f['cluster_key']}")
                for reason in [c for c in self.gate["excluded_cases"]
                               if c["cluster_key"] == f["cluster_key"]]:
                    self.assertTrue(reason["reason"])

    def test_gate_totals_are_consistent(self):
        cases = self.gate["cases"]
        self.assertEqual(self.gate["gate_size"], len(cases))
        self.assertEqual(self.gate["distinct_uploaders"],
                         len({c["author"] for c in cases}))
        self.assertEqual(self.gate["records_involved"],
                         sum(c["record_count"] for c in cases))
        self.assertEqual(self.gate["packs_to_unify"],
                         sum(c["group_count"] - 1 for c in cases))

    # ----------------------------------------------------- named-case review
    def test_named_cases_were_reviewed(self):
        """§5: these specific cases must be present and decided."""
        by_author_groups = {}
        for f in self.ledger["findings"]:
            by_author_groups.setdefault(f["author"], []).append(f)

        for author in ("科里森Corrison", "落烟雨辰呀", "ZangHeRo",
                       "在职玩家JoStar"):
            self.assertIn(author, by_author_groups,
                          f"named case uploader missing from ledger: {author}")

        # 神之征伐 / apotheosis conquest must be one pack, and gated
        core = [f for f in by_author_groups["科里森Corrison"]]
        self.assertTrue(core, "Corrison rows missing")
        for f in core:
            self.assertEqual(f["verdict"], "CONFIRMED_SAME_PACK",
                             f"Corrison should be confirmed, got {f['verdict']}")
            self.assertIn("xyebbs:resource/1421",
                          f["project_identities_shared_by_all_groups"])

    def test_zanghero_is_not_confirmed(self):
        """Module 2 called this UNDER_MERGE; the evidence says different packs."""
        rows = [f for f in self.ledger["findings"] if f["author"] == "ZangHeRo"]
        self.assertTrue(rows, "ZangHeRo row missing")
        for f in rows:
            self.assertEqual(f["verdict"], "DIFFERENT_PACKS",
                             "ZangHeRo should be overturned to DIFFERENT_PACKS")
            self.assertGreaterEqual(f["expected_identity_count"], 2)

    def test_overturns_are_documented(self):
        self.assertTrue(self.ledger["overturns_of_module2"],
                        "module-2 disagreements must be documented explicitly")

    # ----------------------------------------------------- corpus immutability
    def test_existing_corpora_are_untouched(self):
        """§7: nothing pre-existing may be rewritten by this phase."""
        self.assertEqual(raw_sha256(OLD_ADJ), OLD_ADJ_RAW_SHA256)
        old_adj = load(OLD_ADJ)
        self.assertEqual(old_adj["candidates_total"], 100)
        self.assertEqual(old_adj["counts"]["real_false_merge"], 0)
        self.assertEqual(old_adj["counts"]["known_8_retired"], 8)
        self.assertEqual(old_adj["counts"]["known_8_still_merging"], [])
        # The module-2 under-merge verdicts in the pre-existing 1bee6de corpus
        # are read-only; the final 58-case adjudication is a separate layer.
        self.assertEqual(old_adj["under_merge"]["clusters_reviewed"], 60)
        self.assertEqual(old_adj["under_merge"]["confirmed_under_merge"], 33)

        self.assertEqual(raw_sha256(OLD_HOLDOUT), OLD_HOLDOUT_RAW_SHA256)
        old_holdout = load(OLD_HOLDOUT)
        self.assertTrue(old_holdout["old_corpus"]["frozen"])
        self.assertEqual(old_holdout["old_corpus"]["positive"], 24)
        self.assertEqual(old_holdout["old_corpus"]["negative"], 22)
        self.assertEqual(old_holdout["holdout_v2"]["positive"], 44)
        self.assertEqual(old_holdout["holdout_v2"]["negative"], 71)

    # ---------------------------------------------------------- architecture
    def test_extractors_emit_no_verdicts(self):
        """§2 separation of concerns: evidence layers must not decide anything."""
        for name, path in (("evidence", EVIDENCE), ("identity", IDENTITY)):
            blob = json.dumps(load(path), ensure_ascii=False)
            for v in VERDICTS:
                self.assertNotIn(v, blob,
                                 f"{name} artifact leaks a verdict string: {v}")
            self.assertIn("disclaimer", load(path),
                          f"{name} artifact must carry a disclaimer")

    def test_evidence_does_not_cite_verdicts(self):
        ev = load(EVIDENCE)
        allowed_keys = {"phase", "artifact", "purpose", "source_cluster_artifact",
                        "payload_records", "findings_total", "disclaimer", "findings"}
        self.assertTrue(set(ev) <= allowed_keys,
                        f"unexpected top-level keys in evidence artifact: {set(ev) - allowed_keys}")

    # -------------------------------------------------------- reproducibility
    def test_tracked_artifacts_are_byte_reproducible(self):
        for path in (LEDGER, GATE):
            with open(path, "rb") as fp:
                before = hashlib.sha256(fp.read()).hexdigest()
            for script in AUDIT_SCRIPTS:
                r = run(["node", os.path.join("pipeline", "audit", script)])
                self.assertEqual(r.returncode, 0, f"{script} failed:\n{r.stderr}")
            with open(path, "rb") as fp:
                after = hashlib.sha256(fp.read()).hexdigest()
            self.assertEqual(
                before, after,
                f"{os.path.relpath(path, REPO_ROOT)} is not byte-reproducible")

    def test_generated_at_honours_source_date_epoch(self):
        for art in (self.ledger, self.gate):
            self.assertEqual(art["generated_at"], "2026-08-06T07:06:40.000Z",
                             "SOURCE_DATE_EPOCH was not honoured")

    # ---------------------------------------------------------------- §9/§10
    def test_quantities_are_reported(self):
        t = self.ledger["totals"]
        for key in ("confirmed_same_pack", "strong_same_pack", "different_packs",
                    "ambiguous", "partial", "runtime_gate_size"):
            self.assertIsInstance(t[key], int, f"missing quantity: {key}")
        self.assertEqual(t["runtime_gate_size"],
                         t["confirmed_same_pack"] + t["strong_same_pack"])
        self.assertGreater(self.gate["distinct_uploaders"], 0)
        self.assertGreater(self.gate["records_involved"], 0)

    def test_the_nirvana_lesson_is_recorded(self):
        lesson = self.ledger["the_nirvana_lesson"]
        self.assertIn("!=", lesson["principle"])
        self.assertIn("FALSE-POSITIVE", lesson["explanation"])
        self.assertTrue(lesson["consequence"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

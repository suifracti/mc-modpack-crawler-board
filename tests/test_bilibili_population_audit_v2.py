"""
Phase 3G-F.1-B - population-wide grouping audit expansion regression test.

Phase 3G-F-A pinned 7 confirmed population-level false merges and the 涅槃
under-merge. It also quantified its own blind spot: `MIN_ANCHOR_INDEX = 1` meant
the scanner could NEVER see a group whose anchor sat at index 0 -- which is 43% of
all multi-member groups (56 of 129) in the 936-record payload.

This suite pins the EXPANDED evidence, and in particular pins the coverage claim
itself. The dangerous failure mode is not "the fix broke" -- it is "a case quietly
fell out of the candidate list and nobody noticed". So the assertions here are
written so that REMOVING a known case fails, and so that ADDING an unadjudicated
candidate fails.

DELIBERATELY NOT ASSERTED
  * that population-level false merges are zero (they are not; that is the finding)
  * that the detector is exhaustive (it is not; see remaining_blind_spots)
  * that candidate-detector precision is high (it is LOW BY DESIGN -- the detector
    over-reports so nothing is silently missed; see §14)
"""
import json
import os
import subprocess
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CANDIDATES = os.path.join(REPO_ROOT, "build", "audit",
                          "bilibili_population_candidates_v2.json")
UNDERMERGE = os.path.join(REPO_ROOT, "build", "audit",
                          "bilibili_cross_group_undermerge_v2.json")
LEDGER = os.path.join(REPO_ROOT, "pipeline", "audit",
                      "bilibili_population_adjudication_v2.json")
HOLDOUT = os.path.join(REPO_ROOT, "pipeline", "audit",
                       "bilibili_population_holdout_v2.json")
OLD_CORPUS = os.path.join(REPO_ROOT, "pipeline", "audit",
                          "bilibili_grouping_corpus.json")
OLD_SPLIT = os.path.join(REPO_ROOT, "pipeline", "audit",
                         "bilibili_grouping_split.json")
AUDIT_DOC = os.path.join(REPO_ROOT, "docs", "audit",
                         "BILIBILI_GROUPING_POPULATION_EXPANSION.md")

# ---- §7: the 7 confirmed false merges. If ANY of these disappears from the
# candidate list, or is no longer adjudicated REAL_FALSE_MERGE, the expanded
# detector has REGRESSED and the test must fail loudly.
KNOWN_FALSE_MERGES = [
    "一个小寂哦::星辉死神",
    "一个小寂哦::四叶草",
    "一个小寂哦::各大主播同款",
    "墨言eclipse::颠覆性的",
    "原界环::or not",
    "叙利亚自爆民兵::voxy",
    "tibsalta::难度驱动",
]

# ---- §8: 涅槃 is ONE logical pack spread across FIVE group keys (hand-verified
# against bili_data in 3G-F-A). All five must be surfaced as one under-merge.
NIE_SPLIT_GROUP_KEYS = [
    "墨言eclipse::涅槃 无神明渡我 我亦是神明",
    "墨言eclipse::涅槃 神吞降世 邪神投影 万魂幡 超越法则的 镰刀 之旅",
    "墨言eclipse::大型 禁忌 远古炼金 世界污染 3万行代码深度 涅槃v 0 宣传视频",
    "墨言eclipse::沉浸 深度 a 咒镰双生",
    "墨言eclipse::未尽之路涅槃",
]

VERDICTS = {"REAL_FALSE_MERGE", "LEGITIMATE_SAME_PACK",
            "FALSE_SPLIT_INDICATOR", "AMBIGUOUS"}

AUDIT_SCRIPTS = [
    "bilibili_population_candidate_scan_v2.js",
    "bilibili_cross_group_undermerge_scan.js",
    # must run AFTER the two detectors: it consumes their output
    "bilibili_population_adjudication_v2.js",
    # additive holdout builder; consumes the ledger
    "build_population_holdout_v2.js",
]


def load(path):
    with open(path, encoding="utf-8") as fp:
        return json.load(fp)


def run(cmd):
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


class TestBilibiliPopulationAuditV2(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        esbuild = os.path.join(REPO_ROOT, "apps", "web", "node_modules", ".bin",
                               "esbuild.cmd" if os.name == "nt" else "esbuild")
        for entry, out in (("apps/web/src/domain/bilibiliGrouping.ts",
                            "build/audit/bilibili_grouping_module.js"),
                           ("apps/web/src/domain/packName.ts",
                            "build/audit/pack_name_module.js")):
            r = run([esbuild, entry, "--bundle", "--format=cjs", "--platform=node",
                     f"--outfile={out}", "--log-level=warning"])
            assert r.returncode == 0, f"esbuild failed for {entry}: {r.stdout}\n{r.stderr}"
        for script in AUDIT_SCRIPTS:
            r = run(["node", os.path.join("pipeline", "audit", script)])
            assert r.returncode == 0, f"{script} failed: {r.stdout}\n{r.stderr}"

        cls.cand = load(CANDIDATES)
        cls.um = load(UNDERMERGE)
        cls.ledger = load(LEDGER)
        cls.holdout = load(HOLDOUT)

    # ---------------------------------------------------------------- §7
    def test_all_known_7_still_detected_as_candidates(self):
        found = {c["group_key"] for c in self.cand["candidates"]}
        missing = [k for k in KNOWN_FALSE_MERGES if k not in found]
        self.assertEqual(
            missing, [],
            f"Detector regression: known false merges no longer reach the candidate "
            f"list: {missing}")

    def test_all_known_7_adjudicated_real(self):
        real = {r["group_key"] for r in self.ledger["real_false_merges"]}
        for key in KNOWN_FALSE_MERGES:
            self.assertIn(key, real,
                          f"Known false merge {key} is no longer REAL_FALSE_MERGE")

    def test_voxy_and_difficulty_driven_explicitly(self):
        """§7 names these two as must-haves; pin them independently."""
        found = {c["group_key"] for c in self.cand["candidates"]}
        self.assertIn("叙利亚自爆民兵::voxy", found)
        self.assertIn("tibsalta::难度驱动", found)
        real = {r["group_key"] for r in self.ledger["real_false_merges"]}
        self.assertIn("叙利亚自爆民兵::voxy", real)
        self.assertIn("tibsalta::难度驱动", real)

    def test_voxy_keeps_generic_component_signal(self):
        """voxy must still be flagged as a GENERIC component, not just a bad anchor."""
        c = next(x for x in self.cand["candidates"]
                 if x["group_key"] == "叙利亚自爆民兵::voxy")
        self.assertIn("generic_component_anchor", c["detector_reasons"])

    def test_difficulty_driven_keeps_bracket_signal(self):
        c = next(x for x in self.cand["candidates"]
                 if x["group_key"] == "tibsalta::难度驱动")
        self.assertIn("bracket_series_tag", c["detector_reasons"])

    # ---------------------------------------------------------------- §8
    def test_nie_undermerge_detected(self):
        """涅槃 5-way split must be surfaced; §8 requires it be exposed as
        UNDER-MERGE, not mis-recorded as a false merge."""
        um = self.ledger["under_merge"]
        self.assertGreaterEqual(um["nie_under_merge_clusters"], 1)
        self.assertEqual(
            um["nie_group_keys_missing"], [],
            f"涅槃 split keys no longer covered: {um['nie_group_keys_missing']}")
        self.assertEqual(len(um["nie_group_keys_covered"]), len(NIE_SPLIT_GROUP_KEYS))

    def test_nie_not_recorded_as_false_merge(self):
        """Two of the 涅槃 groups sit in the candidate list. They MUST NOT be
        counted as false merges -- the defect is a false SPLIT."""
        real = {r["group_key"] for r in self.ledger["real_false_merges"]}
        for key in ("墨言eclipse::沉浸 深度 a 咒镰双生",
                    "墨言eclipse::未尽之路涅槃"):
            self.assertNotIn(key, real, f"{key} must not be counted as a false merge")

    def test_nie_groups_are_marked_false_split(self):
        split = {r["group_key"] for r in self.ledger["false_split_indicators"]}
        self.assertIn("墨言eclipse::沉浸 深度 a 咒镰双生", split)
        self.assertIn("墨言eclipse::未尽之路涅槃", split)

    # ------------------------------------------------------- §6 / §14 ledger
    def test_every_candidate_is_adjudicated(self):
        self.assertEqual(
            self.ledger["unadjudicated"], [],
            f"Candidates with no verdict: {self.ledger['unadjudicated']}")

    def test_adjudicated_count_matches_candidate_total(self):
        self.assertEqual(self.ledger["candidates_total"],
                         self.cand["candidates_total"])
        self.assertEqual(self.ledger["adjudicated_total"],
                         self.cand["candidates_total"])

    def test_no_duplicate_ledger_keys(self):
        keys = [r["group_key"] for r in self.ledger["real_false_merges"]] \
            + [r["group_key"] for r in self.ledger["legitimate_same_pack"]] \
            + [r["group_key"] for r in self.ledger["false_split_indicators"]] \
            + [r["group_key"] for r in self.ledger["ambiguous"]]
        self.assertEqual(len(keys), len(set(keys)),
                         "a group_key appears under more than one verdict")

    def test_every_ledger_item_maps_to_a_candidate(self):
        cand_keys = {c["group_key"] for c in self.cand["candidates"]}
        for bucket in ("real_false_merges", "legitimate_same_pack",
                       "false_split_indicators", "ambiguous"):
            for r in self.ledger[bucket]:
                self.assertIn(r["group_key"], cand_keys,
                              f"ledger item {r['group_key']} has no candidate")

    def test_no_undeclared_adjudication(self):
        """A verdict table entry pointing at a candidate that does not exist is
        stale and must be removed, not silently ignored."""
        self.assertEqual(self.ledger["declared_but_absent"], [])

    def test_every_ledger_item_has_verdict_evidence_confidence(self):
        for bucket in ("real_false_merges", "legitimate_same_pack",
                       "false_split_indicators", "ambiguous"):
            for r in self.ledger[bucket]:
                self.assertIn(r["verdict"], VERDICTS)
                self.assertIn(r["confidence"], ("high", "medium", "low"))
                self.assertTrue(r["evidence"]["note"],
                                f"{r['group_key']} has no evidence note")

    def test_counts_are_consistent(self):
        c = self.ledger["counts"]
        self.assertEqual(c["real_false_merge"],
                         len(self.ledger["real_false_merges"]))
        self.assertEqual(c["legitimate_same_pack"],
                         len(self.ledger["legitimate_same_pack"]))
        self.assertEqual(c["false_split_indicator"],
                         len(self.ledger["false_split_indicators"]))
        self.assertEqual(c["ambiguous"], len(self.ledger["ambiguous"]))
        self.assertEqual(c["known_7_missing"], [],
                         "known-7 coverage regressed")
        self.assertEqual(c["known_7_detected"], 7)

    # ------------------------------------------------- §2 separation of layers
    def test_detector_emits_no_verdicts(self):
        """§2: the detector must never announce a verdict."""
        for c in self.cand["candidates"]:
            self.assertNotIn("verdict", c)
            self.assertNotIn("confidence", c)
        blob = json.dumps(self.cand, ensure_ascii=False)
        self.assertNotIn("REAL_FALSE_MERGE", blob)
        self.assertNotIn("LEGITIMATE_SAME_PACK", blob)

    def test_undermerge_scanner_emits_no_verdicts(self):
        for f in self.um["findings"]:
            self.assertNotIn("verdict", f)
        blob = json.dumps(self.um, ensure_ascii=False)
        self.assertNotIn("UNDER_MERGE", blob)

    # ---------------------------------------------- §9 cross-group scanning
    def test_cross_group_scan_produced_findings(self):
        self.assertGreater(self.um["clusters_flagged"], 0)
        self.assertEqual(self.um["clusters_flagged"], len(self.um["findings"]))

    def test_every_cross_group_finding_is_adjudicated(self):
        self.assertEqual(
            self.ledger["under_merge"]["unreviewed"], [],
            "cross-group findings left unreviewed")

    def test_cross_group_counts_consistent(self):
        um = self.ledger["under_merge"]
        self.assertEqual(um["clusters_reviewed"], self.um["clusters_flagged"])
        self.assertEqual(um["confirmed_under_merge"] + um["not_under_merge"]
                         + len([r for r in self.ledger["cross_group_adjudication"]
                                if r["verdict"] not in
                                ("UNDER_MERGE", "NOT_UNDER_MERGE")]),
                         um["clusters_reviewed"])

    # ------------------------------------------------------ §10 holdout
    def test_holdout_meets_requirement(self):
        h = self.holdout["holdout_v2"]
        self.assertGreaterEqual(h["positive"], 10)
        self.assertGreaterEqual(h["negative"], 10)
        self.assertTrue(h["meets_requirement"])

    def test_holdout_uploaders_disjoint_from_dev_corpus(self):
        h = self.holdout["holdout_v2"]
        self.assertEqual(h["uploader_overlap_with_old_corpus"], [])
        split = load(OLD_SPLIT)
        dev = {u.lower() for u in split["dev"]["uploaders"]}
        hold = {u for u in h["uploaders"]}
        self.assertEqual(dev & hold, set(),
                         "holdout v2 shares an uploader with the dev corpus")

    def test_holdout_uploaders_disjoint_from_whole_old_corpus(self):
        """Disjoint from BOTH sides of the old split, not just dev."""
        split = load(OLD_SPLIT)
        old = {u.lower() for u in split["dev"]["uploaders"]} \
            | {u.lower() for u in split["holdout"]["uploaders"]}
        self.assertEqual(old & {u for u in self.holdout["holdout_v2"]["uploaders"]},
                         set())

    def test_old_frozen_corpus_untouched(self):
        """§10: the old corpus must NOT be modified. Its shape is pinned here."""
        old = load(OLD_CORPUS)
        self.assertEqual(len(old["positive_cases"]), 24)
        self.assertEqual(len(old["negative_cases"]), 22)

    def test_holdout_cases_carry_evidence(self):
        for c in self.holdout["positive_cases"] + self.holdout["negative_cases"]:
            self.assertTrue(c["videos"], f"{c['case_id']} has no videos")
            self.assertTrue(c["uploader"])
            self.assertIn(c["expected"], ("merge", "separate"))

    # ------------------------------------------------------ §14 precision
    def test_candidate_precision_is_reported_and_low_by_design(self):
        p = self.ledger["candidate_detector_precision"]
        self.assertEqual(p["numerator"], self.ledger["counts"]["real_false_merge"])
        self.assertEqual(p["denominator"], self.ledger["adjudicated_total"])
        self.assertAlmostEqual(p["value"], p["numerator"] / p["denominator"], places=6)
        # Over-reporting is intentional: a HIGH value would mean the net is too
        # narrow, i.e. blind spots remain. Pin that the design goal is documented.
        self.assertLess(p["value"], 0.5)
        self.assertIn("DESIGN GOAL", p["caveat"])

    # ------------------------------------------------------ §15 lower bound
    def test_remaining_blind_spots_declared(self):
        self.assertGreaterEqual(len(self.ledger["remaining_blind_spots"]), 4)
        for s in self.ledger["remaining_blind_spots"]:
            self.assertTrue(s.strip())

    # ------------------------------------------------------ §5 candidate schema
    def test_candidate_artifact_has_required_fields(self):
        required = {"group_key", "author", "anchor", "anchor_index",
                    "anchor_frequency", "key_length", "detector_reasons",
                    "bracket_segments", "members"}
        for c in self.cand["candidates"]:
            self.assertTrue(required <= set(c),
                            f"{c['group_key']} missing {required - set(c)}")
            self.assertIn("shared", c["download_identities"])
            self.assertIn("shared", c["qq_identities"])

    def test_blind_spot_classes_are_actually_covered(self):
        """The whole point of 3G-F.1-B: classes the old scanner structurally
        could not emit must be present in the candidate list."""
        counts = self.cand["detector_class_counts"]
        self.assertGreater(counts.get("anchor_index_zero", 0), 0,
                           "anchor_index_zero coverage lost -- the v1 blind spot is back")
        self.assertGreater(counts.get("anchor_index_one", 0), 0)
        self.assertGreater(counts.get("short_anchor", 0), 0)
        self.assertGreater(counts.get("bracket_series_tag", 0), 0)
        self.assertGreater(counts.get("generic_component_anchor", 0), 0)
        self.assertGreater(counts.get("low_discriminative_key", 0), 0)
        self.assertGreater(counts.get("large_group", 0), 0)
        self.assertGreater(counts.get("mixed_anchor_position", 0), 0)
        self.assertGreater(counts.get("late_anchor_distinct_prefix", 0), 0)
        self.assertGreater(counts.get("repeated_title_boilerplate", 0), 0)

    def test_old_scanner_blind_spot_is_real(self):
        """Guard the premise: the v1 threshold really did exclude index 0, so the
        expansion is not solving a non-problem."""
        self.assertEqual(self.cand["thresholds"]["v1"]["min_anchor_index"], 1)

    # ------------------------------------------------------ §13 audit doc
    def test_audit_document_exists_with_required_sections(self):
        self.assertTrue(os.path.exists(AUDIT_DOC),
                        "docs/audit/BILIBILI_GROUPING_POPULATION_EXPANSION.md missing")
        with open(AUDIT_DOC, encoding="utf-8") as fp:
            body = fp.read()
        for needle in ("scanner coverage", "candidate classes",
                       "adjudication counts", "new confirmed false merges",
                       "new under-merges", "ambiguous", "blind spot"):
            self.assertIn(needle.lower(), body.lower(),
                          f"audit doc is missing the '{needle}' section")


if __name__ == "__main__":
    unittest.main(verbosity=2)

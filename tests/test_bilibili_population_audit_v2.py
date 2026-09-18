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

Phase 3G-F.2-A (this revision) -- CORRECTED PREMISES. The runtime was remediated
(`3f81db2`) and this audit now runs AGAINST the fixed runtime. Three premises were
found to be STALE and are corrected here, not relaxed:

  1. 涅槃 is TWO packs, not one. 3G-F-A's "7 records, ONE pack, split into 5 groups"
     is REFUTED by the records' own structured registration ids (5 -> 涅槃,
     2 -> 未尽之路-涅槃). Asserting "7 merge into 1" would now demand a real
     OVER-merge, so §9 of the phase brief requires the test to stop requiring it.
  2. The 7 known false merges are now 8 (怪物大乱斗 joined them) and ALL EIGHT are
     CLOSED. They therefore must NOT appear as live REAL_FALSE_MERGE -- the old
     `known_7_adjudicated_real` assertion inverted the sign of the fix and is
     replaced by "retired, with a cause, and not present".
  3. The holdout is DERIVED from (ledger x runtime x old-vs-new diff), so fixing
     the runtime legitimately re-derives it. The pinned numbers are therefore the
     CURRENT derivation's, and the test asserts the DERIVATION RULES hold --
     uploader disjointness, evidence on every case -- rather than that a
     previously-measured count never moves.

DELIBERATELY NOT ASSERTED
  * that population-level false merges are zero in the DETECTOR output (they are
    not; the detector over-reports by design and the ledger is what judges)
  * that the detector is exhaustive (it is not; see remaining_blind_spots)
  * that candidate-detector precision is high (it is LOW BY DESIGN; see §14)
"""
import hashlib
import gzip
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

# ---- §7: the EIGHT confirmed population-level false merges, all closed by the
# 3G-F.1-A / 3G-F.2-A runtime remediation. Two complementary assertions are
# needed and they are NOT the same claim:
#   (a) every one must be RETIRED with a documented cause (the fix landed), and
#   (b) NONE may appear live as REAL_FALSE_MERGE (the fix did not regress).
# The pre-3G-F.2-A `known_7_adjudicated_real` assertion demanded the OPPOSITE of
# (b), i.e. that the defect still exist -- it inverted the sign of the fix.
RETIRED_FALSE_MERGES = [
    "一个小寂哦::星辉死神",
    "一个小寂哦::四叶草",
    "一个小寂哦::各大主播同款",
    "墨言eclipse::颠覆性的",
    "原界环::or not",
    "叙利亚自爆民兵::voxy",
    "tibsalta::难度驱动",
    "一个小寂哦::怪物大乱斗",
]

# ---- §9: 涅槃 occupies exactly TWO group keys in the remediated runtime. The
# 3G-F-A "one pack, 5 groups" list is kept ONLY as a regression detector: if the
# family re-fragments into two or more of those legacy keys, the corrected 涅槃
# key has already been swallowed and the fix must be considered regressed.
NIE_SPLIT_GROUP_KEYS = [
    "墨言eclipse::涅槃",
    "墨言eclipse::未尽之路涅槃",
]
NIE_LEGACY_SPLIT_GROUP_KEYS = [
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
    """Load a JSON audit artifact, transparently handling the gzipped form.

    The two large TRACKED artifacts (ledger, holdout) are stored gzipped: they
    are 309 KB / 129 KB of per-record EVIDENCE, and gzip shrinks them to 18% /
    20% while keeping every byte of that evidence intact (minifying or dropping
    member titles would save far less and would destroy reviewability). The
    untracked build/audit/ copies stay plain JSON for eyeballing.
    """
    with open(path, "rb") as fp:
        buf = fp.read()
    if buf[:2] == b"\x1f\x8b":
        buf = gzip.decompress(buf)
    return json.loads(buf.decode("utf-8"))


def run(cmd):
    # SOURCE_DATE_EPOCH pins the `generated_at` field of the generated JSON so
    # that running this suite does NOT leave the tracked audit artifacts dirty.
    # Without it, every test run rewrites only a timestamp and `git status` shows
    # two modified files - which trains everyone to ignore real drift.
    env = dict(os.environ)
    env.setdefault("SOURCE_DATE_EPOCH", "1786000000")
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env)


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
    def test_all_known_false_merges_are_retired_with_a_cause(self):
        """3G-F.2-A: all 8 are CLOSED. Each must carry a cause and a fix.

        This replaces the pre-3G-F.2-A assertion that they were still
        REAL_FALSE_MERGE. Demanding the defect still exist inverts the sign of
        the fix: after remediation a correct audit must show it GONE.
        """
        retired = self.ledger["retired_false_merges"]
        self.assertIsInstance(retired, dict)
        for key in RETIRED_FALSE_MERGES:
            self.assertIn(key, retired,
                          f"known false merge {key} is not in the retired table")
            entry = retired[key]
            self.assertTrue(entry.get("fixed_by"),
                            f"{key} retired with no `fixed_by` cause")
            self.assertFalse(entry.get("still_present", False),
                             f"{key} is still a live group - not actually closed")

    def test_no_known_false_merge_is_live(self):
        """The complementary half: none may reappear as a live REAL_FALSE_MERGE."""
        real = {r["group_key"] for r in self.ledger["real_false_merges"]}
        for key in RETIRED_FALSE_MERGES:
            self.assertNotIn(key, real,
                             f"REGRESSION: {key} became a false merge again")
        self.assertEqual(self.ledger["counts"]["known_8_still_merging"], [])
        self.assertEqual(self.ledger["counts"]["known_8_unexplained"], [])
        self.assertEqual(self.ledger["counts"]["known_8_retired"], len(RETIRED_FALSE_MERGES))

    def test_voxy_and_difficulty_driven_explicitly(self):
        """§7 names these two as must-haves; pin them independently.

        3G-F.2-A: both are now CLOSED. They are pinned by (a) being retired with
        a cause and (b) being absent from the live false-merge set. Their absence
        from the CANDIDATE list is also expected -- a bad anchor that the
        admissibility rules now reject does not reach the candidate net.
        """
        retired = self.ledger["retired_false_merges"]
        for key in ("叙利亚自爆民兵::voxy", "tibsalta::难度驱动"):
            self.assertIn(key, retired, f"{key} not retired")
            self.assertTrue(retired[key].get("fixed_by"))
            self.assertFalse(retired[key].get("still_present", False))
        real = {r["group_key"] for r in self.ledger["real_false_merges"]}
        self.assertNotIn("叙利亚自爆民兵::voxy", real)
        self.assertNotIn("tibsalta::难度驱动", real)

    def test_voxy_and_difficulty_driven_ledger_via_retired_or_candidate(self):
        """Each retired bad-anchor key must be accounted for EXACTLY ONCE: either
        it is still a candidate under the same key, or it is a retired candidate
        key with a documented reason. Nothing may silently vanish."""
        cand_keys = {c["group_key"] for c in self.cand["candidates"]}
        retired_keys = self.ledger["retired_candidate_keys"]
        for key in ("叙利亚自爆民兵::voxy", "tibsalta::难度驱动",
                    "一个小寂哦::星辉死神"):
            accounted = (key in cand_keys) or (key in retired_keys)
            self.assertTrue(accounted,
                            f"{key} vanished from BOTH the candidate list and the "
                            f"retired-candidate ledger")

    def test_voxy_keeps_generic_component_signal(self):
        """voxy must still be flagged as a GENERIC component, not just a bad anchor.

        3G-F.2-A: `叙利亚自爆民兵::voxy` was the ONLY member of this class, and
        the fix RESELECTED that group's anchor away from the bare renderer name
        (voxy) to a real pack name (`你好 新世代`). A live count of 0 is therefore
        the CORRECT state, not a lost capability -- so the assertion is that the
        class is (a) still implemented and (b) the retired row documents where the
        member went. Demanding a live member would demand the defect persist.
        """
        src = os.path.join(REPO_ROOT, "pipeline", "audit",
                           "bilibili_population_candidate_scan_v2.js")
        with open(src, encoding="utf-8") as fp:
            body = fp.read()
        self.assertIn("generic_component_anchor", body,
                      "the generic_component_anchor detector was deleted")
        # The generic word list must still contain the renderer names.
        for word in ("voxy", "sodium", "iris"):
            self.assertIn(f"'{word}'", body,
                          f"generic word '{word}' was dropped from the detector")
        retired = self.ledger["retired_candidate_keys"].get("叙利亚自爆民兵::voxy")
        self.assertIsNotNone(retired, "voxy row missing from the retired ledger")
        self.assertEqual(retired["kind"], "anchor_reselected")
        self.assertIn("voxy", retired["note"])
        self.assertTrue(retired.get("now"), "voxy was retired with no replacement anchor")

    def test_difficulty_driven_keeps_bracket_signal(self):
        counts = self.cand["detector_class_counts"]
        self.assertGreater(
            counts.get("bracket_series_tag", 0), 0,
            "bracket_series_tag coverage lost entirely")
        hit = [c for c in self.cand["candidates"]
               if c["group_key"] == "tibsalta::难度驱动"]
        if hit:
            self.assertIn("bracket_series_tag", hit[0]["detector_reasons"])

    # ---------------------------------------------------------------- §9
    def test_nie_corrected_target_is_two_groups(self):
        """涅槃 is TWO packs (5 + 2), per the records' own registration ids.

        The 3G-F-A premise (7 records -> ONE pack) is REFUTED. Asserting 7->1
        would now demand a real OVER-merge.
        """
        um = self.ledger["under_merge"]
        self.assertEqual(um["nie_corrected_target_groups"], 2)
        self.assertEqual(sorted(um["nie_group_keys_satisfied"]),
                         sorted(NIE_SPLIT_GROUP_KEYS))
        self.assertEqual(um["nie_group_keys_missing"], [])

    def test_nie_does_not_regress_to_legacy_split(self):
        """A regression would re-fragment the family into the 5 legacy keys.

        Threshold, not any-overlap: `未尽之路涅槃` is itself one of the legacy
        keys AND is part of the CORRECT target, so >1 is the real signal.
        """
        um = self.ledger["under_merge"]
        self.assertFalse(um["nie_regressed_to_legacy_split"],
                         f"涅槃 re-fragmented into {um['nie_legacy_split_keys_present']}")
        self.assertLessEqual(len(um["nie_legacy_split_keys_present"]), 1)

    def test_nie_not_recorded_as_false_merge(self):
        """涅槃 keys MUST NOT be counted as false merges -- the defect is a
        false SPLIT, not a false merge."""
        real = {r["group_key"] for r in self.ledger["real_false_merges"]}
        for key in NIE_SPLIT_GROUP_KEYS + NIE_LEGACY_SPLIT_GROUP_KEYS:
            self.assertNotIn(key, real, f"{key} must not be counted as a false merge")

    def test_nie_premise_correction_is_documented(self):
        """The correction itself must be recorded, so a future reader cannot
        re-inherit the refuted premise."""
        um = self.ledger["under_merge"]
        self.assertTrue(um["nie_premise_correction"])
        self.assertIn("2", str(um["nie_corrected_target_groups"]))

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
        # ---- 3G-F.2-A: the known-defect counters are about RETIREMENT, not
        # detection. A correct audit after remediation shows 0 still-merging.
        self.assertEqual(c["known_8_still_merging"], [],
                         "a known false merge regressed")
        self.assertEqual(c["known_8_unexplained"], [],
                         "a retired false merge has no documented cause")
        self.assertEqual(c["known_8_retired"], len(RETIRED_FALSE_MERGES))
        self.assertEqual(c["candidates_total"], c["candidates_adjudicated"])
        self.assertEqual(c["retired_candidate_keys"],
                         len(self.ledger["retired_candidate_keys"]))

    def test_retired_candidate_keys_are_actually_absent(self):
        """Every retired candidate key must really be gone. A 'retired' row that
        is still a live candidate means the ledger is double-counting."""
        cand_keys = {c["group_key"] for c in self.cand["candidates"]}
        for key in self.ledger["retired_candidate_keys"]:
            self.assertNotIn(key, cand_keys,
                             f"{key} is retired but still a live candidate")
        self.assertEqual(self.ledger["retired_candidate_keys_still_present"], [])

    def test_every_retired_candidate_key_has_a_cause(self):
        for key, entry in self.ledger["retired_candidate_keys"].items():
            self.assertIn(entry.get("kind"),
                          ("merged_into_live_group", "anchor_reselected"),
                          f"{key} retired with an undocumented kind")
            self.assertTrue(entry.get("note"), f"{key} retired with no note")

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
        """The holdout is DERIVED (ledger x runtime x old-vs-new diff), so fixing
        the runtime legitimately re-derives it. Assert the DERIVATION CONTRACT
        and the §6 gates, not a frozen count from a different runtime."""
        h = self.holdout["holdout_v2"]
        self.assertGreaterEqual(h["positive"], 30,
                                "holdout lost most of its positives")
        self.assertGreaterEqual(h["negative"], 30,
                                "holdout lost most of its negatives")
        self.assertGreaterEqual(h["uploader_count"], 80)
        self.assertTrue(h["meets_requirement"])
        self.assertEqual(h["uploader_overlap_with_old_corpus"], [])

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
        could not emit must be present in the candidate list.

        3G-F.2-A note: the CLASSES are the invariant, not their counts. Fixing
        the runtime legitimately removes candidates, so a class whose entire
        membership was a defect disappears. The classes pinned here are the ones
        that must survive as DETECTOR CAPABILITY; two narrow ones
        (`anchor_index_one`, `generic_component_anchor`) are asserted only as
        "coverage not entirely lost" because the fix took their last member.
        """
        counts = self.cand["detector_class_counts"]
        # The v1 blind spot: index-0 anchors were structurally invisible.
        self.assertGreater(counts.get("anchor_index_zero", 0), 0,
                           "anchor_index_zero coverage lost -- the v1 blind spot is back")
        self.assertGreater(counts.get("short_anchor", 0), 0)
        self.assertGreater(counts.get("bracket_series_tag", 0), 0)
        self.assertGreater(counts.get("low_discriminative_key", 0), 0)
        self.assertGreater(counts.get("large_group", 0), 0)
        self.assertGreater(counts.get("mixed_anchor_position", 0), 0)
        self.assertGreater(counts.get("late_anchor_distinct_prefix", 0), 0)
        self.assertGreater(counts.get("repeated_title_boilerplate", 0), 0)
        # `anchor_index_one` had exactly 2 members and `generic_component_anchor`
        # one: both were bad anchors the admissibility rules now reject. The
        # CLASS must not be deleted along with its last member -- the detector
        # source still implements it, and the threshold block still documents it.
        self.assertIn("detector_classes", self.cand["thresholds"]["v2"])
        src = os.path.join(REPO_ROOT, "pipeline", "audit",
                           "bilibili_population_candidate_scan_v2.js")
        with open(src, encoding="utf-8") as fp:
            body = fp.read()
        for cls in ("generic_component_anchor", "anchor_index_one"):
            self.assertIn(cls, body,
                          f"detector class {cls} was deleted from the scanner source")

    def test_old_scanner_blind_spot_is_real(self):
        """Guard the premise: the v1 threshold really did exclude index 0, so the
        expansion is not solving a non-problem."""
        self.assertEqual(self.cand["thresholds"]["v1"]["min_anchor_index"], 1)

    # ---------------------------------------------------- reproducibility
    def test_tracked_artifacts_are_byte_reproducible(self):
        """The two TRACKED JSON artifacts must not change when regenerated.

        They carry a `generated_at` field. Before this was pinned, running the
        suite rewrote only that timestamp, so `git status` showed two modified
        files after every run. That is worse than untidy: a permanently-dirty
        tracked artifact trains you to ignore drift, and real drift then hides
        behind the noise. SOURCE_DATE_EPOCH pins it (see run()).
        """
        for path in (LEDGER, HOLDOUT):
            with open(path, "rb") as fp:
                before = hashlib.sha256(fp.read()).hexdigest()
            for script in AUDIT_SCRIPTS:
                r = run(["node", os.path.join("pipeline", "audit", script)])
                self.assertEqual(r.returncode, 0, f"{script} failed:\n{r.stderr}")
            with open(path, "rb") as fp:
                after = hashlib.sha256(fp.read()).hexdigest()
            self.assertEqual(
                before, after,
                f"{os.path.relpath(path, REPO_ROOT)} is not byte-reproducible; "
                f"regenerating it changed the file content")

    def test_generated_at_honours_source_date_epoch(self):
        """Guard the mechanism, not just its effect."""
        self.assertEqual(self.ledger["generated_at"], "2026-08-06T07:06:40.000Z",
                         "SOURCE_DATE_EPOCH was not honoured by the ledger builder")
        self.assertEqual(self.holdout["generated_at"], "2026-08-06T07:06:40.000Z",
                         "SOURCE_DATE_EPOCH was not honoured by the holdout builder")

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

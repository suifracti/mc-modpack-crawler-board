"""
Phase 3G-F-A - Bilibili grouping precision-audit regression test.

The frozen benchmark (tests/test_bilibili_grouping_benchmark.py) scores 46
corpus cases. It can only ever say "FalseMerge = 0" about those 46 cases. This
suite pins the *corpus-independent* evidence produced by Phase 3G-F-A, including
the defects it found, so that:

  * the audit artifacts cannot silently disappear,
  * the known population-level false merges are pinned (fixing them makes this
    test fail loudly, forcing the audit doc to be updated rather than letting the
    matrix drift),
  * the rejected URL-disjointness heuristic is not quietly reused as if valid.

Deliberately NOT asserted: that population-level false merges are zero. They are
not. That is the finding.
"""
import json
import os
import subprocess
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROBE = os.path.join(REPO_ROOT, "build", "audit", "bilibili_grouping_precision_probe.json")
AUDIT = os.path.join(REPO_ROOT, "build", "audit", "bilibili_grouping_precision_audit.json")
CAND = os.path.join(REPO_ROOT, "build", "audit", "bilibili_grouping_candidate_false_merge_check.json")
SLOGAN = os.path.join(REPO_ROOT, "build", "audit", "bilibili_grouping_slogan_anchor_scan.json")
ADJUDICATION = os.path.join(REPO_ROOT, "build", "audit", "bilibili_grouping_anchor_adjudication.json")
RUNTIME = os.path.join(REPO_ROOT, "build", "audit", "bilibili_grouping_runtime_probe.json")

# Confirmed by manual adjudication in Phase 3G-F-A: groups the 3G-F identity-run
# rule merged even though the members are DIFFERENT packs. All are NEW merges
# (the pre-3G-F algorithm kept them apart). None of these pairs is covered by the
# frozen 22-case negative corpus, which is exactly why the benchmark reports FM=0.
KNOWN_FALSE_MERGES = {
    "一个小寂哦::星辉死神": 4,
    "一个小寂哦::四叶草": 2,
    "一个小寂哦::各大主播同款": 2,
    "墨言eclipse::颠覆性的": 2,
    "原界环::or not": 2,
    # Added after widening the anchor-position scan (MIN_ANCHOR_INDEX 2 -> 1) closed a
    # proven false negative (各大主播同款 sat at index 1). These two were MISSED by the
    # first pass and are pinned here with their new root-cause classes:
    #   voxy        -> a generic render-mod name used as the identity anchor
    #   难度驱动    -> a bracketed SERIES TAG taken as the anchor while the real pack name
    #                  sits in the preceding bracket 【抗争之际】/【旅途痕迹】
    "叙利亚自爆民兵::voxy": 2,
    "tibsalta::难度驱动": 2,
}

# Reverse finding: the pack 涅槃 (uploader 墨言eclipse) is ONE pack spread across FIVE
# groupKeys. The two groups below are LEGITIMATE (members really are the same pack) and
# must NOT be treated as false merges. Pinned so the count cannot silently drift.
NIHUAN_UNDER_MERGED = {
    "墨言eclipse::涅槃 无神明渡我 我亦是神明": 1,
    "墨言eclipse::涅槃 神吞降世 邪神投影 万魂幡 超越法则的 镰刀 之旅": 1,
    "墨言eclipse::大型 禁忌 远古炼金 世界污染 3万行代码深度 涅槃v 0 宣传视频": 1,
    "墨言eclipse::沉浸 深度 a 咒镰双生": 2,
    "墨言eclipse::未尽之路涅槃": 2,
}

AUDIT_SCRIPTS = [
    "bilibili_grouping_precision_probe.js",
    "bilibili_grouping_precision_audit.js",
    "bilibili_grouping_candidate_false_merge_check.js",
    "bilibili_grouping_slogan_anchor_scan.js",
    # must run AFTER the scan: it consumes the scan output
    "bilibili_grouping_anchor_adjudication.js",
]


def load(path):
    with open(path, encoding="utf-8") as fp:
        return json.load(fp)


def candidate_groups(cand):
    """Flatten the per-uploader candidate report into one group list."""
    out = []
    for entry in cand["candidates"]:
        for g in entry["groups"]:
            g = dict(g, uploader=entry["uploader"])
            out.append(g)
    return out


def run(cmd, env=None):
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env)


class TestBilibiliGroupingPrecisionAudit(unittest.TestCase):

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
        # The runtime probe needs headless Edge + a deployed frontend. It is a
        # browser gate, not an offline evaluator, so it is only regenerated when
        # the artifact is absent (a fresh tree) - never silently skipped.
        cls.runtime_available = os.path.exists(RUNTIME)
        if not cls.runtime_available:
            r = run(["node", os.path.join("pipeline", "audit",
                                          "probe_bili_grouping_runtime.js")])
            cls.runtime_available = r.returncode == 0 and os.path.exists(RUNTIME)
            if not cls.runtime_available:
                print(f"[warn] runtime probe unavailable: {r.stdout[-400:]} {r.stderr[-400:]}")

    # ------------------------------------------------------------------ 1
    def test_p1_audit_artifacts_exist(self):
        for p in (PROBE, AUDIT, CAND, SLOGAN, ADJUDICATION):
            self.assertTrue(os.path.exists(p), f"missing audit artifact: {p}")

    # ------------------------------------------------------------------ 2
    def test_p2_author_scope_is_structurally_enforced(self):
        """No group may ever span two uploaders, at population scale."""
        audit = load(AUDIT)
        self.assertEqual(audit["payload_records"], 936)
        self.assertEqual(audit["cross_uploader_groups"], 0)
        self.assertEqual(audit["cross_uploader_group_detail"], [])

    # ------------------------------------------------------------------ 3
    def test_p3_rejected_url_heuristic_is_recorded_as_rejected(self):
        """A pack publishing per-version share links looks URL-disjoint.

        The heuristic was tried in Phase 3G-F-A and rejected; the rejection must
        stay on record so it is not reused as evidence of a false merge.
        """
        audit = load(AUDIT)
        h = audit["url_disjointness_heuristic"]
        self.assertEqual(h["verdict"], "REJECTED")
        self.assertGreater(h["flagged_count"], 0)
        self.assertTrue(h["counterexamples"])

    # ------------------------------------------------------------------ 4
    def test_p4_known_population_false_merges_are_pinned(self):
        """Pin the defects. Fixing one must fail this test and update the audit."""
        cand = load(CAND)
        found = {}
        for g in candidate_groups(cand):
            if g["size"] >= 2 and g["group_key"] in KNOWN_FALSE_MERGES:
                found[g["group_key"]] = g["size"]
        self.assertEqual(
            found, KNOWN_FALSE_MERGES,
            "the set of confirmed population-level false merges changed - update "
            "docs/audit/BILIBILI_GROUPING_AUDIT.md and docs/FEATURE_TRUTH_MATRIX.md")

    # ------------------------------------------------------------------ 5
    def test_p5_known_false_merges_are_regressions_not_pre_existing(self):
        """They must all be NEW: the pre-3G-F algorithm kept these packs apart."""
        cand = load(CAND)
        for g in candidate_groups(cand):
            if g["group_key"] in KNOWN_FALSE_MERGES:
                self.assertFalse(
                    g["pre_existing_in_old_algorithm"],
                    f"{g['group_key']} was already merged before 3G-F - re-adjudicate")

    # ------------------------------------------------------------------ 6
    def test_p6_known_false_merges_mix_different_pack_names(self):
        """Each pinned group must genuinely mix different packs."""
        cand = load(CAND)
        expectations = {
            "一个小寂哦::星辉死神": ("神器收集计划", "无尽幸运方块大陆"),
            "一个小寂哦::四叶草": ("泰坦生物", "执行之龙"),
            "一个小寂哦::各大主播同款": ("幸运方块大全", "神器泰坦随机合成"),
            "墨言eclipse::颠覆性的": ("摄影奇境", "千界万锻"),
            "叙利亚自爆民兵::voxy": ("新蒸程", "新世代"),
            "tibsalta::难度驱动": ("抗争之际", "旅途痕迹"),
        }
        for g in candidate_groups(cand):
            if g["group_key"] not in expectations:
                continue
            blob = " ".join(m["title"] for m in g["members"])
            for needle in expectations[g["group_key"]]:
                self.assertIn(needle, blob, f"{g['group_key']} lost member '{needle}'")

    # ------------------------------------------------------------------ 7
    def test_p7_batch_dependence_is_recorded(self):
        """Same records, different batch -> different groupKey.

        The dashboard groups the full 936 payload; the search view groups only the
        filtered batch. The counts are therefore batch-specific, and `53 raw` is
        the only invariant.
        """
        probe = load(PROBE)
        bd = probe["batch_dependence"]
        self.assertEqual(bd["batch_size"], 53)
        self.assertEqual(bd["filtered_batch_cards"], 36)
        self.assertGreater(bd["records_with_different_group_key"], 0)
        self.assertFalse(bd["identical"])

    # ------------------------------------------------------------------ 8
    def test_p8_black_gold_reconstructed_negative_stays_separate(self):
        probe = load(PROBE)
        hj = probe["heijin_negative"]
        self.assertEqual(hj["expected"], "separate")
        self.assertFalse(hj["merged"])
        self.assertTrue(hj["correct"])
        self.assertEqual(hj["distinct_keys"], len(hj["videos"]))

    # ------------------------------------------------------------------ 9
    def test_p9_download_and_qq_are_not_merge_inputs(self):
        """groupBilibiliPacks consumes only (bvid, title, author)."""
        probe = load(PROBE)
        s = probe["download_qq_safety"]
        self.assertIn("never read", s["note"])
        # 豆腐ki is the shared-URL / 手机移植版 cluster named in the phase brief
        self.assertGreaterEqual(s["doufuki"]["records"], 20)
        self.assertEqual(s["doufuki"]["groups"], s["doufuki"]["records"],
                         "豆腐ki records must never collapse into one group")

    # ------------------------------------------------------------------ 10
    def test_p10_runtime_bridge_proof_passed(self):
        """The offline evaluator cannot catch a broken TS -> legacy bridge."""
        if not self.runtime_available:
            self.skipTest("runtime probe unavailable (needs headless Edge + deployed frontend)")
        rt = load(RUNTIME)
        self.assertTrue(rt["all_passed"], f"runtime probe failed: {rt['checks']}")
        names = {c["name"]: c for c in rt["checks"]}
        self.assertTrue(names["bridge returns a plain object (not a Map)"]["pass"])
        self.assertEqual(rt["mechanical_power"]["raw"], 53)
        self.assertLess(rt["mechanical_power"]["grouped"], 53)

    # ------------------------------------------------------------------ 11
    def test_p11_slogan_anchor_scan_is_advisory_not_a_verdict(self):
        scan = load(SLOGAN)
        self.assertIn("over-reports", scan["heuristic"]["note"])
        self.assertGreater(scan["flagged_count"], 0)
        # every flag must carry the members needed to adjudicate it
        for f in scan["flagged"]:
            self.assertTrue(f["members"])
            self.assertTrue(f["distinct_prefixes"])

    # ------------------------------------------------------------------ 12
    def test_p12_every_flagged_group_is_adjudicated(self):
        """The scan is a review-list generator; nothing may be left unjudged.

        If this fails, the headline false-merge count is stale - either a new
        flagged group appeared (adjudicate it) or a verdict key went unused.
        """
        ledger = load(ADJUDICATION)
        self.assertEqual(ledger["unadjudicated"], [],
                         "flagged groups exist with no recorded verdict")
        self.assertEqual(ledger["declared_but_absent"], [],
                         "a verdict was recorded for a group that is no longer flagged")
        self.assertEqual(
            ledger["real_false_merge_count"] + ledger["legitimate_count"]
            + ledger["undecided_count"],
            ledger["scan_flagged_count"],
            "adjudication ledger does not account for every flagged group")

    # ------------------------------------------------------------------ 13
    def test_p13_adjudicated_real_false_merges_match_the_pin(self):
        ledger = load(ADJUDICATION)
        counted = {r["group_key"] for r in ledger["real_false_merges"]}
        self.assertEqual(
            counted, set(KNOWN_FALSE_MERGES),
            "the hand adjudication and the pinned defect list disagree")

    # ------------------------------------------------------------------ 14
    def test_p14_nihuan_is_under_merged_not_false_merged(self):
        """涅槃 is ONE pack split across five groupKeys (a false-SPLIT symptom).

        All 7 records containing 涅槃 come from 墨言eclipse and are the same pack.
        Two of those groups are internally legitimate - they must never be
        reclassified as false merges just because their anchor is a bad anchor.
        """
        cand = load(CAND)
        mixed = {
            g["group_key"]: g["size"]
            for g in candidate_groups(cand)
            if g["group_key"] in NIHUAN_UNDER_MERGED
        }
        self.assertEqual(mixed, NIHUAN_UNDER_MERGED,
                         "the 涅槃 under-merge shape changed - re-adjudicate §23.2b")
        self.assertGreater(len(NIHUAN_UNDER_MERGED), 1,
                           "涅槃 must still be fragmented; a single group would mean fixed")
        overlap = set(NIHUAN_UNDER_MERGED) & set(KNOWN_FALSE_MERGES)
        self.assertEqual(overlap, set(),
                         "a 涅槃 group was reclassified as a false merge")


if __name__ == "__main__":
    unittest.main(verbosity=2)

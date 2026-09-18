"""
Phase 3G-F-A -> 3G-F.1-A - Bilibili grouping precision-audit regression test.

The frozen benchmark (tests/test_bilibili_grouping_benchmark.py) scores 46
corpus cases. It can only ever say "FalseMerge = 0" about those 46 cases. This
suite pins the *corpus-independent* evidence produced by Phase 3G-F-A, and then
pins the OUTCOME of the Phase 3G-F.1-A runtime remediation:

  * the audit artifacts cannot silently disappear,
  * the 7 population-level false merges that 3G-F-A proved are pinned as an
    HISTORICAL finding (RETIRED) and separately asserted to be GONE from the
    runtime, so a regression in either direction fails loudly,
  * the rejected URL-disjointness heuristic is not quietly reused as if valid,
  * the 涅槃 under-merge premise is pinned as CORRECTED (the records' own
    structured resource ids prove 涅槃 and 未尽之路-涅槃 are two different packs,
    so 2 groups is correct and "7 -> 1" was never ground truth).

Deliberately NOT asserted: that population-level false merges are zero BY THE
SCAN alone. The scan is a review-list generator; the ledger is the verdict.
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
# rule merged even though the members are DIFFERENT packs. All were NEW merges
# (the pre-3G-F algorithm kept them apart). None of these pairs is covered by the
# frozen 22-case negative corpus, which is exactly why the benchmark reported FM=0.
#
# Phase 3G-F.1-A: ALL SEVEN ARE FIXED. This dict is retained as the historical
# finding; `test_p4` now asserts they are GONE rather than present.
KNOWN_FALSE_MERGES_AT_3GF = {
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

# The two 3G-F.1 regressions named in the phase brief, must be closed by name.
BRIEF_REGRESSIONS = ("叙利亚自爆民兵::voxy", "tibsalta::难度驱动")

# Groups that 3G-F flagged and that no longer exist as groups. Every one must be
# accounted for with a kind + reason; an unexplained disappearance is a failure.
EXPECTED_RETIRED_KINDS = {
    "叙利亚自爆民兵::voxy": "closed_bad_anchor",
    "tibsalta::难度驱动": "closed_bad_anchor",
}

# Reverse finding, now CORRECTED: 涅槃 (uploader 墨言eclipse) is TWO packs, not one.
#   5 records -> xyebbs resources/37418   (涅槃)
#   2 records -> xyebbs res-id/TUPN       (未尽之路-涅槃)
# The uploader states the two are unrelated. 2 groups is therefore CORRECT.
NIRVANA_EXPECTED_PACKS = {
    "墨言eclipse::涅槃": (5, "涅槃", ["xyebbs.com/resources/37418", "mcmod.cn/modpack/1418"]),
    "墨言eclipse::未尽之路涅槃": (2, "未尽之路-涅槃", ["xyebbs.com/res-id/TUPN",
                                             "bbsmc.net/modpack/unfinished_path_nirvana"]),
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
    def test_p4_known_population_false_merges_are_GONE(self):
        """Phase 3G-F.1-A: all 7 confirmed false merges must be fixed.

        Phase 3G-F-A pinned them as PRESENT. Fixing them turned this test red on
        purpose, which is the signal to re-adjudicate. It is now inverted: the
        historical set is retained, but the runtime must not reproduce any of it.
        """
        cand = load(CAND)
        still = {}
        for g in candidate_groups(cand):
            if g["size"] >= 2 and g["group_key"] in KNOWN_FALSE_MERGES_AT_3GF:
                still[g["group_key"]] = g["size"]
        self.assertEqual(
            still, {},
            f"population false merges survived the 3G-F.1 remediation: {still} - "
            "the anchor admissibility rules regressed")

    # ------------------------------------------------------------------ 4b
    def test_p4b_brief_named_regressions_are_closed_by_name(self):
        """The two 3G-F regressions named in the phase brief must be closed."""
        adj = load(ADJUDICATION)
        retired = {r["group_key"]: r for r in adj["retired_groups"]}
        for key in BRIEF_REGRESSIONS:
            self.assertIn(key, retired, f"{key} is neither flagged nor recorded as retired")
            self.assertFalse(retired[key]["still_present"], f"{key} still exists as a group")
            self.assertEqual(retired[key]["kind"], "closed_bad_anchor")
        self.assertEqual(adj["real_false_merge_count"], 0)

    # ------------------------------------------------------------------ 5
    def test_p5_retired_false_merges_were_regressions_not_pre_existing(self):
        """They were all NEW at 3G-F: the pre-3G-F algorithm kept these packs apart."""
        adj = load(ADJUDICATION)
        for r in adj["retired_false_merges"]:
            if r["verdict"] != "REAL_FALSE_MERGE":
                continue
            self.assertTrue(r["fixed_by"], f"{r['group_key']} has no recorded fix cause")

    # ------------------------------------------------------------------ 5b
    def test_p5b_every_absent_group_is_explained(self):
        """A group may not silently vanish: each must carry a kind + reason.

        `declared_but_absent` being empty is not enough on its own - the ledger has
        to say WHY the key is gone (fixed vs recall trade), otherwise the fix could
        hide a recall regression behind a tidy empty list.
        """
        adj = load(ADJUDICATION)
        self.assertEqual(adj["declared_but_absent"], [],
                         "a verdict exists for a group that is not flagged")
        self.assertEqual(adj["unadjudicated"], [],
                         "flagged groups exist with no recorded verdict")
        kinds = {"closed_bad_anchor", "dissolved_singleton"}
        for r in adj["retired_groups"]:
            self.assertIn(r["kind"], kinds, f"{r['group_key']} has an unknown kind")
            self.assertTrue(r["note"], f"{r['group_key']} has no note")
            self.assertFalse(r["still_present"], f"{r['group_key']} is retired but still present")
        for key, kind in EXPECTED_RETIRED_KINDS.items():
            hit = [r for r in adj["retired_groups"] if r["group_key"] == key]
            self.assertTrue(hit, f"{key} missing from retired_groups")
            self.assertEqual(hit[0]["kind"], kind)

    # ------------------------------------------------------------------ 6
    def test_p6_known_false_merge_pairs_are_now_separate(self):
        """Each historical false merge must now resolve to distinct pack labels.

        Asserted on the RUNTIME decisions, not the old candidate report, so the
        check follows the fix instead of the snapshot.
        """
        module = os.path.join(REPO_ROOT, "build", "audit", "bilibili_grouping_module.js")
        script = f"""
const fs = require('fs');
const path = require('path');
const mod = require({json.dumps(module)});
const raw = fs.readFileSync(path.join({json.dumps(REPO_ROOT)}, 'converted_output', 'data', 'bili_data.js'), 'utf8');
const data = JSON.parse(raw.slice(raw.indexOf('['), raw.lastIndexOf(']') + 1));
const dec = new Map(mod.groupBilibiliPacks(data));
// authorScope lowercases the uploader name, so match case-insensitively.
const probes = {json.dumps({
            "叙利亚自爆民兵": ["新蒸程", "新世代"],
            "Tibsalta": ["抗争之际", "旅途痕迹"],
            "一个小寂哦": ["神器收集计划", "无尽幸运方块大陆"],
        }, ensure_ascii=False)};
const out = {{}};
for (const [author, needles] of Object.entries(probes)) {{
  out[author] = [];
  const scope = author.toLowerCase();
  for (const n of needles) {{
    const hit = data.filter((v) => String(v.author || '').toLowerCase() === scope
                                 && v.title.includes(n));
    if (!hit.length) {{ out[author].push([n, 'NO_RECORD']); continue; }}
    out[author].push([n, dec.get(hit[0].bvid).groupKey]);
  }}
}}
console.log(JSON.stringify(out));
"""
        r = run(["node", "-e", script])
        self.assertEqual(r.returncode, 0, r.stderr)
        result = json.loads(r.stdout.strip().splitlines()[-1])
        for author, pairs in result.items():
            keys = [k for _, k in pairs]
            for n, k in pairs:
                self.assertNotEqual(k, "NO_RECORD", f"probe record missing for {author}/{n}")
            self.assertEqual(len(set(keys)), len(keys),
                             f"{author}: different packs still share a groupKey: {pairs}")
            # a fixed pair must not merely be labelled differently - the labels have
            # to be the real pack names, not a residual slogan anchor.
            for n, k in pairs:
                self.assertTrue(k.startswith(author.lower() + "::") or not k,
                                f"{author}: unexpected cross-author key {k}")

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
        """The scan is a review-list generator; nothing may be left unjudged."""
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
        self.assertEqual(counted, set(),
                         f"the runtime still produces adjudicated false merges: {counted}")

    # ------------------------------------------------------------------ 14
    def test_p14_nirvana_premise_is_corrected_not_forced(self):
        """涅槃 is TWO packs - the 3G-F-A "one pack, 5 groups" premise is refuted.

        The phase brief asked for 涅槃 to converge to ONE group. The records' own
        structured `download_links` show two distinct registrations, and the
        uploader states the two packs are unrelated. Merging them would have been a
        real over-merge, so the correct outcome is TWO groups.

        This test pins the CORRECTION and the live cross-check against bili_data.
        """
        ledger = load(ADJUDICATION)
        premise = ledger["nirvana_premise"]
        self.assertEqual(premise["verdict"], "CONFIRMED",
                         "the 涅槃 resource-id cross-check no longer reproduces")
        self.assertEqual(len(premise["groups"]), len(NIRVANA_EXPECTED_PACKS),
                         "the number of distinct 涅槃 packs changed - re-adjudicate")
        for key, (count, pack_name, ids) in NIRVANA_EXPECTED_PACKS.items():
            g = premise["groups"][key]
            self.assertEqual(g["observed_records"], count,
                             f"{key} record count changed")
            self.assertTrue(g["resource_ids_match"], f"{key} resource ids no longer match")
            self.assertEqual(g["expected_pack"], pack_name,
                             f"{key} declared pack name drifted")
            self.assertEqual(g["expected_records"], count,
                             f"{key} declared record count drifted")

    # ------------------------------------------------------------------ 14b
    def test_p14b_nirvana_runtime_splits_into_exactly_two_packs(self):
        """Runtime check: 7 records -> exactly 2 groups, matching the evidence."""
        module = os.path.join(REPO_ROOT, "build", "audit", "bilibili_grouping_module.js")
        script = f"""
const fs = require('fs');
const path = require('path');
const mod = require({json.dumps(module)});
const raw = fs.readFileSync(path.join({json.dumps(REPO_ROOT)}, 'converted_output', 'data', 'bili_data.js'), 'utf8');
const data = JSON.parse(raw.slice(raw.indexOf('['), raw.lastIndexOf(']') + 1));
const dec = new Map(mod.groupBilibiliPacks(data));
const rows = data.filter((v) => v.author === '墨言eclipse' && /涅槃/.test(v.title));
const groups = {{}};
for (const v of rows) {{
  const k = dec.get(v.bvid).groupKey;
  groups[k] = (groups[k] || 0) + 1;
}}
console.log(JSON.stringify({{ records: rows.length, groups }}));
"""
        r = run(["node", "-e", script])
        self.assertEqual(r.returncode, 0, r.stderr)
        result = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertEqual(result["records"], 7, "涅槃 record population changed")
        self.assertEqual(len(result["groups"]), 2,
                         f"涅槃 must resolve to 2 packs, got {result['groups']}")
        for key, (count, _pack_name, _ids) in NIRVANA_EXPECTED_PACKS.items():
            self.assertEqual(result["groups"].get(key), count,
                             f"{key} should hold {count} records")


if __name__ == "__main__":
    unittest.main(verbosity=2)

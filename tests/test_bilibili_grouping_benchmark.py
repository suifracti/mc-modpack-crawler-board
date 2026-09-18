"""
Phase 3G-F - Bilibili grouping benchmark + remediation contract test.

Verifies:
  * the frozen Phase 3G-E corpus is intact (counts, phase-named cases, 黑金 control)
  * the remediation is reproducible and the extracted OLD implementation still
    reproduces the production 53-RAW invariant
  * the NEW domain implementation keeps false merges at zero (both in isolation
    and in full-population context) while recovering recall
  * dev / holdout are uploader-disjoint and reported separately (overfit check)

Deliberately NOT asserted: "53 raw -> 47 grouped cards" as a correctness golden.
47 was only ever a stability invariant; after correctness remediation the grouped
count is expected to move. What must hold is `53 raw` (Flat Mode identity).
"""
import json
import os
import subprocess
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

CORPUS_PATH = os.path.join(REPO_ROOT, "pipeline", "audit", "bilibili_grouping_corpus.json")
SPLIT_PATH = os.path.join(REPO_ROOT, "pipeline", "audit", "bilibili_grouping_split.json")
BENCH_PATH = os.path.join(REPO_ROOT, "build", "audit", "bilibili_grouping_benchmark.json")
REMED_PATH = os.path.join(REPO_ROOT, "build", "audit", "bilibili_grouping_remediation.json")
ANALYSIS_PATH = os.path.join(REPO_ROOT, "build", "audit", "bilibili_grouping_analysis.json")

EXTRACTOR = os.path.join(REPO_ROOT, "pipeline", "audit", "extract_bili_grouping_impl.py")
LEGACY_FIXTURE = os.path.join(REPO_ROOT, "pipeline", "audit", "fixtures",
                              "bili_grouping_legacy_impl.js")
OLD_EVAL = os.path.join(REPO_ROOT, "pipeline", "audit", "bilibili_grouping_benchmark.js")
SPLITTER = os.path.join(REPO_ROOT, "pipeline", "audit", "split_bili_grouping_corpus.py")
NEW_EVAL = os.path.join(REPO_ROOT, "pipeline", "audit", "bilibili_grouping_remediation_eval.js")

SCORED_CONFIDENCE = {"confirmed", "strong"}


def run(cmd):
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


class TestBilibiliGroupingBenchmark(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Bundle the real TS domain module with the project's own esbuild.
        esbuild = os.path.join(REPO_ROOT, "apps", "web", "node_modules", ".bin",
                               "esbuild.cmd" if os.name == "nt" else "esbuild")
        r0 = run([esbuild, "apps/web/src/domain/bilibiliGrouping.ts", "--bundle",
                  "--format=cjs", "--platform=node",
                  "--outfile=build/audit/bilibili_grouping_module.js", "--log-level=warning"])
        assert r0.returncode == 0, f"esbuild failed: {r0.stdout}\n{r0.stderr}"
        for cmd in ([sys.executable, EXTRACTOR], [sys.executable, SPLITTER],
                    ["node", OLD_EVAL], [sys.executable, SPLITTER],
                    ["node", NEW_EVAL]):
            r = run(cmd)
            assert r.returncode == 0, f"{cmd} failed: {r.stdout}\n{r.stderr}"
        cls.corpus = json.load(open(CORPUS_PATH, encoding="utf-8"))
        cls.split = json.load(open(SPLIT_PATH, encoding="utf-8"))
        cls.bench = json.load(open(BENCH_PATH, encoding="utf-8"))
        cls.remed = json.load(open(REMED_PATH, encoding="utf-8"))

    # ------------------------------------------------------------------ 1
    def test_c1_corpus_schema_and_counts(self):
        required = {"case_id", "expected", "confidence", "uploader", "videos", "ground_truth_evidence"}
        for section in ("positive_cases", "negative_cases", "reconstructed_cases"):
            self.assertIn(section, self.corpus)
            for c in self.corpus[section]:
                self.assertTrue(required <= set(c), f"{c.get('case_id')} missing fields")
                self.assertIn(c["expected"], ("merge", "separate"))
                self.assertGreaterEqual(len(c["videos"]), 2)
                self.assertTrue(c["ground_truth_evidence"])
        self.assertEqual(len(self.corpus["positive_cases"]), 24)
        self.assertEqual(len(self.corpus["negative_cases"]), 22)

    # ------------------------------------------------------------------ 2
    def test_c2_phase_named_cases_present(self):
        by_id = {c["case_id"]: c for c in self.corpus["positive_cases"]}
        self.assertIn("POS-SPEC-MIXIN-A", by_id)
        self.assertIn("POS-SPEC-MIXIN-B", by_id)
        self.assertIn("POS-SPEC-HORIZON", by_id)
        self.assertEqual({v["bvid"] for v in by_id["POS-SPEC-MIXIN-A"]["videos"]},
                         {"BV1Ziuw6ZE7C", "BV1fqNe6rEt5", "BV1tVeVzDELy"})
        self.assertEqual({v["bvid"] for v in by_id["POS-SPEC-MIXIN-B"]["videos"]},
                         {"BV1vuVH6XErM", "BV1k3Lg6zEjY", "BV1ACA8zjELd"})
        self.assertEqual(by_id["POS-SPEC-HORIZON"]["uploader"], "ConfectionaryQwQ")

    # ------------------------------------------------------------------ 3
    def test_c3_black_gold_control_present(self):
        rec = {c["case_id"]: c for c in self.corpus["reconstructed_cases"]}
        self.assertIn("NEG-SPEC-HEIJIN", rec)
        self.assertEqual(rec["NEG-SPEC-HEIJIN"]["expected"], "separate")
        self.assertEqual(rec["NEG-SPEC-HEIJIN"]["confidence"], "reconstructed")
        self.assertIn("生存整合包", " ".join(v["title"] for v in rec["NEG-SPEC-HEIJIN"]["videos"]))
        # and it must stay OUT of the scored corpus
        self.assertNotIn("NEG-SPEC-HEIJIN", {c["case_id"] for c in self.bench["cases"]})

    # ------------------------------------------------------------------ 4
    def test_c4_split_is_uploader_disjoint_with_minimums(self):
        dev = set(self.split["dev"]["uploaders"])
        hold = set(self.split["holdout"]["uploaders"])
        self.assertFalse(dev & hold, "uploader leaked between dev and holdout")
        self.assertGreaterEqual(self.split["holdout"]["positive"], 5)
        self.assertGreaterEqual(self.split["holdout"]["negative"], 5)

    # ------------------------------------------------------------------ 5
    def test_c5_old_impl_reproduces_53_raw_invariant(self):
        """`53 raw` is the invariant (Flat Mode identity). 47 is NOT a golden."""
        mp = self.remed["mechanical_power"]
        self.assertEqual(mp["before"]["raw_matches"], 53)
        self.assertEqual(mp["after"]["raw_matches"], 53)
        self.assertTrue(mp["after"]["flat_mode_invariant_ok"])
        self.assertEqual(mp["after"]["flat_mode_raw_records"], 53)
        # The grouped count is allowed to change; it must simply be recorded.
        self.assertIn("grouped_cards", mp["after"])
        self.assertEqual(self.bench["invariant_check"]["reproduced"], True)

    # ------------------------------------------------------------------ 6
    def test_c6_no_false_merge_in_isolation(self):
        """Hard safety gate: not a single negative control may merge."""
        neg = self.remed["negative_regression"]
        self.assertEqual(neg["total"], 22)
        self.assertEqual(neg["still_separate"], 22)
        self.assertTrue(neg["all_separate"])
        self.assertEqual(self.remed["after"]["overall"]["false_merge"], 0)
        self.assertEqual(self.remed["after"]["dev"]["false_merge"], 0)
        self.assertEqual(self.remed["after"]["holdout"]["false_merge"], 0)
        self.assertEqual(self.remed["new_false_merges"], [])

    # ------------------------------------------------------------------ 7
    def test_c7_no_false_merge_in_population_context(self):
        """The same gate must hold when all 936 records are grouped together."""
        js = (
            "global.window={};const fs=require('fs');"
            "const m=require('./build/audit/bilibili_grouping_module.js');"
            "const raw=fs.readFileSync('converted_output/data/bili_data.js','utf8');"
            "const d=JSON.parse(raw.slice(raw.indexOf('['),raw.lastIndexOf(']')+1));"
            "const o={};for(const [b,x] of m.groupBilibiliPacks(d)) o[b]=x.groupKey;"
            "console.log(JSON.stringify(o));"
        )
        r = run(["node", "-e", js])
        self.assertEqual(r.returncode, 0, r.stderr)
        pop = json.loads(r.stdout)
        violations = []
        for n in self.corpus["negative_cases"]:
            if n["confidence"] not in SCORED_CONFIDENCE:
                continue
            keys = {pop.get(v["bvid"]) for v in n["videos"]}
            if len(keys) != len(n["videos"]):
                violations.append(n["case_id"])
        self.assertEqual(violations, [], f"population-context false merge: {violations}")

    # ------------------------------------------------------------------ 8
    def test_c8_recall_recovered_and_reported_per_split(self):
        before = self.remed["before"]["overall"]
        after = self.remed["after"]["overall"]
        self.assertEqual(before["false_split"], 21)
        self.assertLess(after["false_split"], 21, "remediation did not reduce false splits")
        self.assertGreater(after["recall"], before["recall"])
        self.assertEqual(after["precision"], 1.0)
        # per-split metrics must exist and be internally consistent
        for name in ("dev", "holdout", "overall"):
            m = self.remed["after"][name]
            self.assertIn("recall", m)
            self.assertIn("precision", m)
        self.assertGreaterEqual(self.remed["after"]["holdout"]["precision"], 1.0)

    # ------------------------------------------------------------------ 9
    def test_c9_old_false_split_regression_listed(self):
        outcomes = self.remed["old_false_split_outcomes"]
        self.assertEqual(len(outcomes), 21)
        for o in outcomes:
            for f in ("case_id", "uploader", "video_count", "before_keys", "after_keys", "fixed"):
                self.assertIn(f, o)
        self.assertGreaterEqual(sum(1 for o in outcomes if o["fixed"]), 15)

    # ------------------------------------------------------------------ 10
    def test_c10_large_group_audit_present(self):
        pop = self.remed["population"]["after"]
        self.assertIn("large_groups_ge5", pop)
        for g in pop["large_groups_ge5"]:
            self.assertGreaterEqual(g["size"], 5)
            self.assertTrue(g["titles"])
        self.assertIn("size_distribution", pop)

    # ------------------------------------------------------------------ 11
    def test_c11_analysis_sections_still_present(self):
        analysis = json.load(open(ANALYSIS_PATH, encoding="utf-8"))
        for section in ("key_space", "key_strength", "generic_vocabulary",
                        "version_signals", "download_identity", "qq_identity"):
            self.assertIn(section, analysis)
        self.assertEqual(analysis["key_space"]["raw_videos"], 936)

    # ------------------------------------------------------------------ 12
    def test_c12_frozen_legacy_implementation_is_available(self):
        """The pre-3G-F algorithm must stay available as a frozen reference.

        Phase 3G-F removed it from the production bundle, so the before/after
        comparison would silently lose its baseline if the fixture went missing.
        """
        self.assertTrue(os.path.exists(LEGACY_FIXTURE), "frozen legacy impl missing")
        with open(LEGACY_FIXTURE, encoding="utf-8") as fp:
            src = fp.read()
        for marker in ("function cleanPackKey", "function groupPacks",
                       "BILI_GENERIC_PACK_KEYS2", "BILI_GENRE_BUZZWORDS"):
            self.assertIn(marker, src)
        self.assertIn("FROZEN REFERENCE", src)
        # and the live bundle must NOT still carry the legacy generic set
        with open(os.path.join(REPO_ROOT, "converted_output", "assets", "index.js"),
                  encoding="utf-8") as fp:
            bundle = fp.read()
        self.assertNotIn("BILI_GENERIC_PACK_KEYS2", bundle,
                         "legacy grouping set still present in the production bundle")


if __name__ == "__main__":
    unittest.main(verbosity=2)

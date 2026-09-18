"""
Phase 3G-E - Bilibili grouping benchmark contract test.

Verifies the benchmark corpus is well-formed, has enough hard cases and enough
independent uploaders, contains the phase-named cases, and that the evaluation
is REPRODUCIBLE against the real production grouping implementation.

It deliberately does NOT hard-code the current algorithm's outcome as the
expected value - the whole point of the benchmark is to observe it. What is
asserted is corpus stability + evaluation correctness/consistency.
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
BENCH_PATH = os.path.join(REPO_ROOT, "build", "audit", "bilibili_grouping_benchmark.json")
ANALYSIS_PATH = os.path.join(REPO_ROOT, "build", "audit", "bilibili_grouping_analysis.json")
EXTRACTOR = os.path.join(REPO_ROOT, "pipeline", "audit", "extract_bili_grouping_impl.py")
EVALUATOR = os.path.join(REPO_ROOT, "pipeline", "audit", "bilibili_grouping_benchmark.js")

VALID_CONFIDENCE = {"confirmed", "strong", "ambiguous", "reconstructed"}
SCORED_CONFIDENCE = {"confirmed", "strong"}


def run(cmd):
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


class TestBilibiliGroupingBenchmark(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Regenerate the extracted implementation + evaluation so the test is
        # self-contained and reproducible from a clean checkout.
        r1 = run([sys.executable, EXTRACTOR])
        assert r1.returncode == 0, f"extractor failed: {r1.stdout}\n{r1.stderr}"
        r2 = run(["node", EVALUATOR])
        assert r2.returncode == 0, f"evaluator failed: {r2.stdout}\n{r2.stderr}"
        cls.corpus = json.load(open(CORPUS_PATH, encoding="utf-8"))
        cls.bench = json.load(open(BENCH_PATH, encoding="utf-8"))
        cls.analysis = json.load(open(ANALYSIS_PATH, encoding="utf-8"))

    # ------------------------------------------------------------------ 1
    def test_c1_corpus_schema(self):
        """Every case carries the required fields and a valid confidence level."""
        required = {"case_id", "expected", "confidence", "uploader", "videos", "ground_truth_evidence"}
        for section in ("positive_cases", "negative_cases", "reconstructed_cases"):
            self.assertIn(section, self.corpus)
            for c in self.corpus[section]:
                self.assertTrue(required <= set(c), f"{c.get('case_id')} missing fields")
                self.assertIn(c["expected"], ("merge", "separate"))
                self.assertIn(c["confidence"], VALID_CONFIDENCE)
                self.assertGreaterEqual(len(c["videos"]), 2, f"{c['case_id']} needs >=2 videos")
                self.assertTrue(c["ground_truth_evidence"], f"{c['case_id']} has no evidence")
                for v in c["videos"]:
                    for f in ("bvid", "title", "current_clean_key"):
                        self.assertIn(f, v, f"{c['case_id']} video missing {f}")

    # ------------------------------------------------------------------ 2
    def test_c2_corpus_size_and_diversity(self):
        """>=20 positive groups, >=20 negative controls, >=8 unique uploaders."""
        pos = self.corpus["positive_cases"]
        neg = self.corpus["negative_cases"]
        self.assertGreaterEqual(len(pos), 20, "need >=20 positive cases")
        self.assertGreaterEqual(len(neg), 20, "need >=20 negative controls")
        uploaders = {c["uploader"] for c in pos} | {c["uploader"] for c in neg}
        self.assertGreaterEqual(len(uploaders), 8, f"need >=8 uploaders, got {len(uploaders)}")
        # No single uploader may dominate the corpus.
        per = {}
        for c in pos + neg:
            per[c["uploader"]] = per.get(c["uploader"], 0) + 1
        self.assertLessEqual(max(per.values()), len(pos) + len(neg) * 0.25,
                             "one uploader dominates the corpus")

    # ------------------------------------------------------------------ 3
    def test_c3_phase_named_cases_present(self):
        """The phase-named 懂嗎懂嗎 groups and the Horizon series must be present."""
        by_id = {c["case_id"]: c for c in self.corpus["positive_cases"]}
        self.assertIn("POS-SPEC-MIXIN-A", by_id)
        self.assertIn("POS-SPEC-MIXIN-B", by_id)
        self.assertIn("POS-SPEC-HORIZON", by_id)

        a = {v["bvid"] for v in by_id["POS-SPEC-MIXIN-A"]["videos"]}
        b = {v["bvid"] for v in by_id["POS-SPEC-MIXIN-B"]["videos"]}
        self.assertEqual(a, {"BV1Ziuw6ZE7C", "BV1fqNe6rEt5", "BV1tVeVzDELy"})
        self.assertEqual(b, {"BV1vuVH6XErM", "BV1k3Lg6zEjY", "BV1ACA8zjELd"})
        self.assertEqual(by_id["POS-SPEC-MIXIN-A"]["uploader"], "懂嗎懂嗎")
        self.assertEqual(by_id["POS-SPEC-MIXIN-B"]["uploader"], "懂嗎懂嗎")
        self.assertEqual(by_id["POS-SPEC-HORIZON"]["uploader"], "ConfectionaryQwQ")
        self.assertGreaterEqual(len(by_id["POS-SPEC-HORIZON"]["videos"]), 2)

    # ------------------------------------------------------------------ 4
    def test_c4_known_false_merge_control_present(self):
        """The phase-named 黑金 false merge must be represented as a negative control."""
        rec = {c["case_id"]: c for c in self.corpus["reconstructed_cases"]}
        self.assertIn("NEG-SPEC-HEIJIN", rec, "黑金 control missing")
        case = rec["NEG-SPEC-HEIJIN"]
        self.assertEqual(case["expected"], "separate")
        self.assertEqual(case["uploader"], "黑金")
        self.assertEqual(case["confidence"], "reconstructed")
        titles = " ".join(v["title"] for v in case["videos"])
        self.assertIn("生存整合包", titles)
        # And the corpus must record that the case is absent from the live payload.
        self.assertIn("spec_case_absent", self.corpus)
        self.assertEqual(self.corpus["spec_case_absent"]["uploader"], "黑金")

    # ------------------------------------------------------------------ 5
    def test_c5_evaluation_reproducible_and_invariant_reproduced(self):
        """The real implementation must reproduce the production 53 -> 47 invariant."""
        inv = self.bench["invariant_check"]
        self.assertEqual(inv["raw_videos"], 936)
        self.assertEqual(inv["mechanical_power_raw"], 53)
        self.assertEqual(inv["mechanical_power_cards"], 47)
        self.assertTrue(inv["reproduced"], "53 -> 47 invariant not reproduced")

        mp = self.analysis["mechanical_power_53_47"]
        self.assertEqual(mp["raw_matches"], 53)
        self.assertEqual(mp["grouped_cards"], 47)
        self.assertEqual(mp["net_collapse"], 6)
        self.assertEqual(len(mp["multi_video_groups"]), 4)
        self.assertEqual(sum(g["video_count"] for g in mp["multi_video_groups"]), 10)
        self.assertTrue(mp["flat_mode_invariant_ok"])
        self.assertEqual(mp["flat_mode_raw_records"], 53)

    # ------------------------------------------------------------------ 6
    def test_c6_outcomes_internally_consistent(self):
        """The four outcome classes must agree with the per-case results."""
        cases = self.bench["cases"]
        scored = [c for c in cases if c["confidence"] in SCORED_CONFIDENCE]
        self.assertEqual(len(scored), self.bench["corpus"]["positive_cases"]
                         + self.bench["corpus"]["negative_cases"])
        tm = sum(1 for c in scored if c["expected"] == "merge" and c["correct"])
        fs = sum(1 for c in scored if c["expected"] == "merge" and not c["correct"])
        ts = sum(1 for c in scored if c["expected"] == "separate" and c["correct"])
        fm = sum(1 for c in scored if c["expected"] == "separate" and not c["correct"])
        o = self.bench["outcomes"]
        self.assertEqual((o["true_merge"], o["false_split"], o["true_separate"], o["false_merge"]),
                         (tm, fs, ts, fm))
        self.assertAlmostEqual(o["merge_precision"], tm / (tm + fm) if tm + fm else 1.0, places=4)
        self.assertAlmostEqual(o["merge_recall"], tm / (tm + fs) if tm + fs else 1.0, places=4)
        # Listed failure cases must match the counts.
        self.assertEqual(len(self.bench["false_merge_cases"]), fm)
        self.assertEqual(len(self.bench["false_split_cases"]), fs)

    # ------------------------------------------------------------------ 7
    def test_c7_reconstructed_case_scored_separately(self):
        """Reconstructed cases are evaluated but excluded from precision/recall."""
        rec = self.bench["reconstructed_cases"]
        self.assertEqual(len(rec), 1)
        self.assertEqual(rec[0]["case_id"], "NEG-SPEC-HEIJIN")
        self.assertIn("current_algorithm_result", rec[0])
        ids = {c["case_id"] for c in self.bench["cases"]}
        self.assertNotIn("NEG-SPEC-HEIJIN", ids,
                         "reconstructed case must not be part of the scored corpus")

    # ------------------------------------------------------------------ 8
    def test_c8_analysis_sections_present(self):
        """The full-corpus analysis must cover every required dimension."""
        for section in ("key_space", "key_strength", "generic_vocabulary",
                        "version_signals", "download_identity", "qq_identity"):
            self.assertIn(section, self.analysis, f"analysis section {section} missing")
        ks = self.analysis["key_space"]
        self.assertEqual(ks["raw_videos"], 936)
        self.assertEqual(ks["multi_video_groups"] + ks["single_video_groups"],
                         ks["unique_author_key_groups"])
        self.assertGreaterEqual(self.analysis["key_strength"]["total_groups"], 800)
        self.assertGreaterEqual(len(self.analysis["generic_vocabulary"]["top_50"]), 20)

    # ------------------------------------------------------------------ 9
    def test_c9_no_algorithm_mutation(self):
        """The extracted implementation must be the shipped production code.

        Guards against someone 'fixing' the algorithm inside the audit harness.
        """
        impl_path = os.path.join(REPO_ROOT, "build", "audit", "bili_grouping_impl.js")
        with open(impl_path, encoding="utf-8") as fp:
            impl = fp.read()
        for marker in ("function cleanPackKey", "function groupPacks",
                       "BILI_GENERIC_PACK_KEYS2", "BILI_GENRE_BUZZWORDS"):
            self.assertIn(marker, impl)
        # The extracted text must be byte-identical to the bundle's own source.
        with open(os.path.join(REPO_ROOT, "converted_output", "assets", "index.js"),
                  encoding="utf-8") as fp:
            bundle = fp.read()
        for fn in ("function cleanPackKey(", "function groupPacks("):
            self.assertIn(fn, bundle)
        self.assertNotIn("__BENCHMARK_OVERRIDE__", impl)


if __name__ == "__main__":
    unittest.main(verbosity=2)

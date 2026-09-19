"""Phase 3G-F.3-A audit/runtime-probe contract.

This suite deliberately accepts BLOCKED: A must not smuggle a BVID-specific
runtime map into production grouping.  It verifies that the real probe is
complete and that a non-closed generic runtime is reported as FAIL/BLOCKED,
not relabelled as PASS.
"""
import json
import os
import re
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLOSURE = os.path.join(ROOT, "pipeline", "audit",
                       "bilibili_undermerge_runtime_closure.json")
PROBE = os.path.join(ROOT, "pipeline", "audit",
                     "bilibili_undermerge_runtime_probe.json")
GROUPING = os.path.join(ROOT, "apps", "web", "src", "domain",
                        "bilibiliGrouping.ts")


def load(path):
    with open(path, encoding="utf-8") as fp:
        return json.load(fp)


class TestBilibiliUndermergeRuntimeClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.closure = load(CLOSURE)
        cls.probe = load(PROBE)

    def test_original_gate_maps_to_26_cases_and_80_unique_bvids(self):
        c = self.closure
        self.assertEqual(c["gate_size"], 26)
        self.assertEqual(c["coverage"]["gate_cases_mapped"], 26)
        self.assertEqual(c["coverage"]["bvids_mapped_unique"], 80)
        self.assertEqual(c["records_involved_sum"], 80)
        self.assertEqual(c["packs_to_unify"], 34)
        self.assertEqual(c["coverage"]["missing_cases"], [])
        self.assertEqual(c["coverage"]["duplicate_bvids"], [])
        self.assertEqual(c["coverage"]["empty_groups"], [])
        self.assertEqual(c["coverage"]["non_unique_mappings"], [])

    def test_probe_has_every_case_with_real_before_after_expected_evidence_result(self):
        p = self.probe
        self.assertEqual(p["coverage"]["gate_cases_checked"], 26)
        self.assertEqual(len(p["gate_cases"]), 26)
        for case in p["gate_cases"]:
            for key in ("before", "after", "expected", "evidence", "result"):
                self.assertIn(key, case)
            self.assertGreater(case["before"]["distinct_group_count"], 0)
            self.assertGreater(case["after"]["distinct_group_count"], 0)
            self.assertEqual(case["expected"]["target_group_count"], 1)
            self.assertTrue(case["evidence"]["note"])
            self.assertGreater(len(case["before"]["group_keys_by_bvid"]), 0)

    def test_generic_runtime_is_not_falsely_reported_as_closed(self):
        p = self.probe
        self.assertEqual(p["status"], "BLOCKED")
        self.assertEqual(p["coverage"]["gate_cases_passed"], 5)
        self.assertEqual(p["coverage"]["gate_cases_failed"], 21)
        self.assertNotEqual(p["status"], "PASS")

    def test_different_and_ambiguous_partition_is_complete_and_boundary_checked(self):
        p = self.probe
        excluded = p["excluded_cases"]
        self.assertEqual(len(excluded), 32)
        different = [x for x in excluded if x["verdict"] == "DIFFERENT_PACKS"]
        ambiguous = [x for x in excluded if x["verdict"] == "AMBIGUOUS"]
        self.assertEqual(len(different), 27)
        self.assertEqual(len(ambiguous), 5)
        self.assertEqual(sum(x["result"] == "PROTECTED" for x in different), 22)
        self.assertEqual(sum(x["result"] == "FAIL" for x in different), 5)
        self.assertEqual(sum(x["result"] == "PROTECTED" for x in ambiguous), 4)
        self.assertEqual(sum(x["result"] == "FAIL" for x in ambiguous), 1)
        self.assertEqual(sum(x["before_after_unchanged"] for x in different), 22)
        self.assertEqual(sum(x["before_after_unchanged"] for x in ambiguous), 4)
        self.assertTrue(all("do not claim different-pack proof" in x["expected"]
                            for x in ambiguous))

    def test_no_production_bvid_closure_import_or_map(self):
        with open(GROUPING, encoding="utf-8") as fp:
            source = fp.read()
        self.assertNotIn("bilibiliUndermergeClosure", source)
        self.assertNotIn("audited_undermerge", source)
        self.assertNotIn("BILIBILI_UNDERMERGE_RUNTIME", source)
        # The historical source contains BVIDs in explanatory comments; reject
        # only an actual quoted BVID-to-key object entry.
        self.assertIsNone(re.search(r"['\"]BV1[A-Za-z0-9]+['\"]\s*:", source))


if __name__ == "__main__":
    unittest.main(verbosity=2)

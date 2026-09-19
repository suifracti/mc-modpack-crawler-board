"""Historical Phase 3G-F.3-A probe fixture contract.

The old probe is retained as a named 5/21 diagnostic baseline.  Dynamic
candidate acceptance lives in ``test_bilibili_undermerge_runtime_acceptance``
and is never inferred from this historical JSON.
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

    def test_historical_probe_is_not_used_as_candidate_acceptance(self):
        p = self.probe
        self.assertIn(p["status"], ("BLOCKED", "PASS"))
        self.assertEqual(p["artifact"], "bilibili_undermerge_runtime_probe")
        self.assertIn("current_runtime_bundle_sha256", p["source"])
        self.assertNotIn("candidate_runtime", p["source"])

    def test_different_and_ambiguous_partition_is_complete_and_boundary_checked(self):
        p = self.probe
        excluded = p["excluded_cases"]
        self.assertEqual(len(excluded), 32)
        different = [x for x in excluded if x["verdict"] == "DIFFERENT_PACKS"]
        ambiguous = [x for x in excluded if x["verdict"] == "AMBIGUOUS"]
        self.assertEqual(len(different), 27)
        self.assertEqual(len(ambiguous), 5)
        self.assertEqual(sum(x["result"] in ("PROTECTED", "FAIL") for x in different), 27)
        self.assertEqual(sum(x["result"] in ("PROTECTED", "FAIL") for x in ambiguous), 5)
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

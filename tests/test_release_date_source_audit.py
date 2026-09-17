"""
Architecture V2 - Phase 3G-A: Release-Date Source Semantics Audit Contract Tests.

Validates the contracts of the Phase 3G-A evidence audit:
1. Mathematical lineage and violation counts across Modrinth, CurseForge, MCMod.
2. Exact structure and categories of the 30 Golden Samples (5 normal, 3 edge, 2 ambiguous per platform).
3. Freshness Guard source file SHA-256 hardening verification.
"""
import os
import json
import sqlite3
import unittest
from pipeline.audit.release_date_source_auditor import ReleaseDateSourceAuditor, GOLDEN_OUTPUT_PATH
from pipeline.audit.verify_fresh_equivalence import check_freshness_guard, ROOT


class TestReleaseDateSourceAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.auditor = ReleaseDateSourceAuditor()
        cls.auditor.load_data()
        cls.results = cls.auditor.audit_target_platforms()

    @classmethod
    def tearDownClass(cls):
        cls.auditor.close()

    def test_target_platform_totals_and_non_nulls(self):
        """Verify release counts and non-null totals for Modrinth, CurseForge, MCMod."""
        mr = self.results["modrinth"]
        cf = self.results["curseforge"]
        mc = self.results["mcmod"]

        self.assertEqual(mr["total_releases"], 18328)
        self.assertEqual(mr["non_null_releases"], 18328)
        self.assertEqual(mr["null_releases"], 0)

        self.assertEqual(cf["total_releases"], 45797)
        self.assertEqual(cf["non_null_releases"], 45797)
        self.assertEqual(cf["null_releases"], 0)

        self.assertEqual(mc["total_releases"], 1484)
        self.assertEqual(mc["non_null_releases"], 326)
        self.assertEqual(mc["null_releases"], 1158)

        summary = self.results["summary"]
        self.assertEqual(summary["total_target_releases"], 65609)
        self.assertEqual(summary["total_target_non_null"], 64451)
        self.assertEqual(summary["total_target_null"], 1158)

    def test_strict_rule_violations_and_blast_radius(self):
        """Verify strict Canonical Rule violation counts and blast radius."""
        mr = self.results["modrinth"]
        cf = self.results["curseforge"]
        mc = self.results["mcmod"]

        # Modrinth: 100% project-level date modified/created -> 18328 violations
        self.assertEqual(mr["scope"], "project")
        self.assertEqual(mr["evidence_certainty"], "PROJECT_LEVEL_ONLY")
        self.assertFalse(mr["strict_rule_valid"])
        self.assertEqual(mr["strict_rule_violating_rows"], 18328)
        self.assertEqual(mr["potential_blast_radius"], 18328)

        # CurseForge: 100% project-level date modified/released -> 45797 violations
        self.assertEqual(cf["scope"], "project")
        self.assertEqual(cf["evidence_certainty"], "PROJECT_LEVEL_ONLY")
        self.assertFalse(cf["strict_rule_valid"])
        self.assertEqual(cf["strict_rule_violating_rows"], 45797)
        self.assertEqual(cf["potential_blast_radius"], 45797)

        # MCMod: 326 non-null releases are version-scoped dates from /modpack/version/{mid}.html
        self.assertEqual(mc["scope"], "version")
        self.assertEqual(mc["evidence_certainty"], "CONFIRMED_RELEASE_SCOPED")
        self.assertTrue(mc["strict_rule_valid"])
        self.assertEqual(mc["strict_rule_violating_rows"], 0)
        self.assertEqual(mc["potential_blast_radius"], 0)

        # Total violating rows across 3 platforms: 18328 + 45797 + 0 = 64125
        summary = self.results["summary"]
        self.assertEqual(summary["total_strict_rule_violating_rows"], 64125)
        self.assertEqual(summary["total_potential_blast_radius"], 64125)

    def test_golden_30_contract(self):
        """Verify the 30 Golden Samples exist, with 10 per platform (5 normal, 3 edge, 2 ambiguous)."""
        self.assertTrue(os.path.exists(GOLDEN_OUTPUT_PATH), f"Golden samples file missing: {GOLDEN_OUTPUT_PATH}")
        with open(GOLDEN_OUTPUT_PATH, "r", encoding="utf-8") as f:
            samples = json.load(f)

        self.assertEqual(len(samples), 30, "Must have exactly 30 golden samples")

        for plat in ("modrinth", "curseforge", "mcmod"):
            plat_samples = [s for s in samples if s["platform"] == plat]
            self.assertEqual(len(plat_samples), 10, f"{plat} must have exactly 10 samples")

            normal_samples = [s for s in plat_samples if s["sample_category"] == "normal"]
            edge_samples = [s for s in plat_samples if s["sample_category"] == "edge"]
            ambiguous_samples = [s for s in plat_samples if s["sample_category"] == "ambiguous"]

            self.assertEqual(len(normal_samples), 5, f"{plat} must have 5 normal samples")
            self.assertEqual(len(edge_samples), 3, f"{plat} must have 3 edge samples")
            self.assertEqual(len(ambiguous_samples), 2, f"{plat} must have 2 ambiguous samples")

            required_fields = [
                "platform", "sample_category", "pack_title", "source_id",
                "canonical_release_id", "version_name", "raw_json_source_path",
                "scope_classification", "evidence_certainty", "strict_rule_valid",
                "blast_radius_action", "notes"
            ]
            for s in plat_samples:
                for field in required_fields:
                    self.assertIn(field, s, f"Field {field} missing in sample {s.get('canonical_release_id')}")

    def test_freshness_guard_source_hash_rejection(self):
        """Verify check_freshness_guard rejects source file hash mismatch."""
        fresh_db = os.path.join(ROOT, "build", "canonical_fresh_verify.db")
        prov_path = os.path.join(ROOT, "build", "audit", "fresh_rebuild_provenance.json")
        if not os.path.exists(fresh_db) or not os.path.exists(prov_path):
            self.skipTest("fresh db or provenance not found")

        # 1. Normal state should pass
        check_freshness_guard(fresh_db)

        # 2. Tampered provenance hash should raise RuntimeError
        with open(prov_path, "r", encoding="utf-8") as f:
            prov = json.load(f)

        orig_hash = prov["source_hashes"]["bbsmc_adapter"]
        prov["source_hashes"]["bbsmc_adapter"] = "0000000000000000000000000000000000000000000000000000000000000000"
        tampered_path = os.path.join(ROOT, "build", "audit", "_tmp_tampered_prov.json")
        try:
            with open(tampered_path, "w", encoding="utf-8") as f:
                json.dump(prov, f)

            # Test by temporarily swapping or mocking
            import unittest.mock as mock
            with mock.patch("pipeline.audit.verify_fresh_equivalence.ROOT", ROOT):
                with open(tampered_path, "r", encoding="utf-8") as tf:
                    bad_prov = json.load(tf)
                with mock.patch("json.load", return_value=bad_prov):
                    with self.assertRaises(RuntimeError) as ctx:
                        check_freshness_guard(fresh_db)
                    self.assertIn("FAIL: Fresh verification DB source hash does not match current source", str(ctx.exception))
        finally:
            if os.path.exists(tampered_path):
                os.remove(tampered_path)


if __name__ == "__main__":
    unittest.main()

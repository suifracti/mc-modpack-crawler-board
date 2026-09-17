"""
Architecture V2 - Phase 3G-A.1: Release-Date Source Semantics Audit Contract Tests.

Validates the contracts of the Phase 3G-A.1 evidence audit:
1. Mathematical lineage and violation counts across Modrinth, CurseForge, MCMod.
2. Modrinth date_modified semantic classification (CONFIRMED_VERSION_AGGREGATE) & snapshot check.
3. CurseForge project/file distinction (PROJECT_LEVEL_ONLY & 45,797 violations).
4. MCMod verified version scope (CONFIRMED_RELEASE_SCOPED & 0 violations).
5. Exact structure and categories of the 30 Golden Samples (5 normal, 3 edge, 2 ambiguous per platform).
6. Freshness Guard source file SHA-256 hardening verification.
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

    def test_modrinth_semantic_classification_and_snapshot(self):
        """Verify Modrinth date_modified is classified as CONFIRMED_VERSION_AGGREGATE."""
        mr = self.results["modrinth"]
        self.assertEqual(mr["scope"], "version_aggregate")
        self.assertEqual(mr["evidence_certainty"], "CONFIRMED_VERSION_AGGREGATE")
        self.assertTrue(mr["strict_rule_valid"])
        self.assertEqual(mr["strict_rule_violating_rows"], 0)
        self.assertEqual(mr["potential_blast_radius"], 0)
        # Verify latest_version was not retained in offline crawler snapshot
        self.assertEqual(mr["latest_version_retained_in_snapshot"], 0)

    def test_curseforge_project_file_distinction(self):
        """Verify CurseForge dateModified/dateReleased remain PROJECT_LEVEL_ONLY."""
        cf = self.results["curseforge"]
        self.assertEqual(cf["scope"], "project")
        self.assertEqual(cf["evidence_certainty"], "PROJECT_LEVEL_ONLY")
        self.assertFalse(cf["strict_rule_valid"])
        self.assertEqual(cf["strict_rule_violating_rows"], 45797)
        self.assertEqual(cf["potential_blast_radius"], 45797)
        # Verify latestFiles/fileDate was not retained in offline crawler snapshot
        self.assertEqual(cf["latest_files_retained_in_snapshot"], 0)

    def test_mcmod_verified_version_scope(self):
        """Verify MCMod last_update_date is confirmed version-scoped."""
        mc = self.results["mcmod"]
        self.assertEqual(mc["scope"], "version")
        self.assertEqual(mc["evidence_certainty"], "CONFIRMED_RELEASE_SCOPED")
        self.assertTrue(mc["strict_rule_valid"])
        self.assertEqual(mc["strict_rule_violating_rows"], 0)
        self.assertEqual(mc["potential_blast_radius"], 0)

    def test_recalculated_total_violations_and_blast_radius(self):
        """Verify recalculated total violations (CurseForge only = 45,797)."""
        summary = self.results["summary"]
        self.assertEqual(summary["total_strict_rule_violating_rows"], 45797)
        self.assertEqual(summary["total_potential_blast_radius"], 45797)

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

    def test_modrinth_repaired_golden_identity_contract(self):
        """Phase 3G-A.2: Verify 10 repaired Modrinth Golden Samples identity & semantic contract."""
        repaired_path = os.path.join(ROOT, "build", "audit", "modrinth_repaired_golden_10.json")
        self.assertTrue(os.path.exists(repaired_path), f"Missing {repaired_path}")
        with open(repaired_path, "r", encoding="utf-8") as f:
            samples = json.load(f)

        self.assertEqual(len(samples), 10, "Must have exactly 10 repaired Modrinth golden samples")

        # 1. 10 unique project IDs
        pids = [s["raw_project_id"] for s in samples]
        self.assertEqual(len(set(pids)), 10, "All 10 project IDs must be unique")

        # 2. All exist in local raw modrinth_modpacks.json
        raw_map = {item.get("project_id"): item for item in self.auditor.modrinth_raw}
        for s in samples:
            pid = s["raw_project_id"]
            self.assertIn(pid, raw_map, f"Sample project_id {pid} must exist in local raw snapshot")
            raw_item = raw_map[pid]
            # 3. raw ID == API ID, raw slug == API slug
            self.assertEqual(s["raw_project_id"], s["api_project_id"])
            self.assertEqual(s["raw_slug"], s["api_slug"])
            self.assertEqual(raw_item.get("slug"), s["api_slug"])
            # 4. API project_type == modpack
            self.assertEqual(s["api_project_type"], "modpack")
            # 5. latest version project_id == project_id
            self.assertEqual(s["version_project_id"], pid)
            self.assertEqual(s["version_id"], s["search_latest_version"])
            # 6. date_modified vs version date_published semantic comparison
            self.assertTrue(s["identity_verified"])
            self.assertTrue(s["semantic_match"])
            self.assertLessEqual(s["delta_ms"], 15000.0)


if __name__ == "__main__":
    unittest.main()


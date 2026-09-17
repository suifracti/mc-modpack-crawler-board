"""
Unit tests for derive_legacy_has_server and Golden Samples.
Verifies strict truth table and platform semantic claims.
"""
import unittest
import sqlite3
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from pipeline.exporters.legacy.base import BaseLegacyExporter

class TestLegacyHasServer(unittest.TestCase):

    def test_truth_table_positive(self):
        """Positive claims must derive to True."""
        # Confirmed positive
        self.assertTrue(BaseLegacyExporter.derive_legacy_has_server("required", "confirmed"))
        self.assertTrue(BaseLegacyExporter.derive_legacy_has_server("optional", "confirmed"))
        self.assertTrue(BaseLegacyExporter.derive_legacy_has_server("supported", "confirmed"))

        # Strong inferred positive
        self.assertTrue(BaseLegacyExporter.derive_legacy_has_server("supported", "strong_inferred"))
        self.assertTrue(BaseLegacyExporter.derive_legacy_has_server("required", "strong_inferred"))

        # Inferred positive
        self.assertTrue(BaseLegacyExporter.derive_legacy_has_server("supported", "inferred"))
        self.assertTrue(BaseLegacyExporter.derive_legacy_has_server("optional", "inferred"))

    def test_truth_table_negative(self):
        """Negative and unknown claims must derive to False."""
        # Confirmed unsupported
        self.assertFalse(BaseLegacyExporter.derive_legacy_has_server("unsupported", "confirmed"))

        # Inferred unsupported
        self.assertFalse(BaseLegacyExporter.derive_legacy_has_server("unsupported", "inferred"))
        self.assertFalse(BaseLegacyExporter.derive_legacy_has_server("unsupported", "strong_inferred"))

        # Unknown / No evidence
        self.assertFalse(BaseLegacyExporter.derive_legacy_has_server("unknown", "unknown"))
        self.assertFalse(BaseLegacyExporter.derive_legacy_has_server("unknown", "no_evidence"))
        self.assertFalse(BaseLegacyExporter.derive_legacy_has_server("unknown", "inferred"))

        # Empty or None claims
        self.assertFalse(BaseLegacyExporter.derive_legacy_has_server(None, None))
        self.assertFalse(BaseLegacyExporter.derive_legacy_has_server("", ""))
        self.assertFalse(BaseLegacyExporter.derive_legacy_has_server("supported", None))
        self.assertFalse(BaseLegacyExporter.derive_legacy_has_server(None, "confirmed"))

    def test_golden_samples_from_db(self):
        """Verify actual Golden Samples queried directly from canonical.db."""
        db_path = os.path.join(REPO_ROOT, "build", "canonical.db")
        if not os.path.exists(db_path):
            self.skipTest(f"Database {db_path} does not exist.")

        conn = sqlite3.connect(db_path)

        def check_claim(source_item_id, expected_status, expected_cert, expected_legacy):
            row = conn.execute("""
                SELECT status, certainty FROM environment_claims
                WHERE source_item_id = ? AND side = 'server'
            """, (source_item_id,)).fetchone()
            self.assertIsNotNone(row, f"Claim not found for {source_item_id}")
            self.assertEqual(row[0], expected_status, f"Status mismatch for {source_item_id}")
            self.assertEqual(row[1], expected_cert, f"Certainty mismatch for {source_item_id}")
            derived = BaseLegacyExporter.derive_legacy_has_server(row[0], row[1])
            self.assertEqual(derived, expected_legacy, f"Legacy has_server mismatch for {source_item_id}")

        # 1. Modrinth required sample (e.g. Fabulously Optimized or similar)
        # Find one sample with required
        row_mr_req = conn.execute("""
            SELECT source_item_id FROM environment_claims
            WHERE side = 'server' AND status = 'required' AND certainty = 'confirmed'
            LIMIT 1
        """).fetchone()
        if row_mr_req:
            check_claim(row_mr_req[0], "required", "confirmed", True)

        # 2. Modrinth unsupported sample
        row_mr_un = conn.execute("""
            SELECT source_item_id FROM environment_claims
            WHERE side = 'server' AND status = 'unsupported' AND certainty = 'confirmed'
            LIMIT 1
        """).fetchone()
        if row_mr_un:
            check_claim(row_mr_un[0], "unsupported", "confirmed", False)

        # 3. MCMod supported sample (inferred positive)
        row_mc_pos = conn.execute("""
            SELECT source_item_id FROM environment_claims
            WHERE side = 'server' AND status = 'supported' AND certainty = 'inferred' AND source_item_id LIKE 'mcmod:%'
            LIMIT 1
        """).fetchone()
        if row_mc_pos:
            check_claim(row_mc_pos[0], "supported", "inferred", True)

        # 4. MCMod unsupported sample (inferred negative)
        row_mc_neg = conn.execute("""
            SELECT source_item_id FROM environment_claims
            WHERE side = 'server' AND status = 'unsupported' AND certainty = 'inferred' AND source_item_id LIKE 'mcmod:%'
            LIMIT 1
        """).fetchone()
        if row_mc_neg:
            check_claim(row_mc_neg[0], "unsupported", "inferred", False)

        # 5. MCMod unknown sample
        row_mc_unk = conn.execute("""
            SELECT source_item_id FROM environment_claims
            WHERE side = 'server' AND status = 'unknown' AND source_item_id LIKE 'mcmod:%'
            LIMIT 1
        """).fetchone()
        if row_mc_unk:
            check_claim(row_mc_unk[0], "unknown", "unknown", False)

        # 6. CurseForge ServerPack sample (download link / release is_server)
        row_cf_pos = conn.execute("""
            SELECT source_item_id FROM environment_claims
            WHERE side = 'server' AND status = 'supported' AND certainty IN ('confirmed', 'strong_inferred', 'inferred') AND source_item_id LIKE 'curseforge:%'
            LIMIT 1
        """).fetchone()
        if row_cf_pos:
            row_stat = conn.execute("SELECT status, certainty FROM environment_claims WHERE source_item_id = ? AND side = 'server'", (row_cf_pos[0],)).fetchone()
            check_claim(row_cf_pos[0], row_stat[0], row_stat[1], True)

        # 7. CurseForge unknown sample
        row_cf_unk = conn.execute("""
            SELECT source_item_id FROM environment_claims
            WHERE side = 'server' AND status = 'unknown' AND source_item_id LIKE 'curseforge:%'
            LIMIT 1
        """).fetchone()
        if row_cf_unk:
            check_claim(row_cf_unk[0], "unknown", "unknown", False)

        conn.close()

if __name__ == "__main__":
    unittest.main()

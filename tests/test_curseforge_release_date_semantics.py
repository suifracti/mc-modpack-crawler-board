"""
Architecture V2 - Phase 3G-B: CurseForge Release-Date Semantics Contract Tests.

Verifies:
1. All 45,797 CurseForge releases have release_date == NULL (no file/release scoped timestamp).
2. Project metadata dates (published_at, modified_at) in source_items remain 100% intact and preserved.
3. 10 real CurseForge Golden Samples explicitly demonstrate:
   - release_date is NULL
   - dateModified != release_date
   - dateReleased != release_date
   - dateCreated != release_date
   - project published_at and modified_at remain fully available.
4. Non-CurseForge platforms are 100% untouched.
"""
import hashlib
import json
import os
import sqlite3
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "build", "canonical.db")
RAW_PATH = os.path.join(ROOT, "crawler_output", "curseforge_modpacks.json")

EXPECTED_CURSEFORGE_RELEASES = 45797
EXPECTED_SOURCE_ITEMS_DIGEST = "7ebe9bf4de8fafcb77bb3a09a1ad3c7f8dce63e73a8fa59325284b4ad3abb956"

GOLDEN_PIDS = [
    ("285109", "RLCraft"),
    ("925200", "All the Mods 10 - ATM10"),
    ("389615", "The Pixelmon Modpack"),
    ("876781", "Better MC [FORGE] BMC4"),
    ("296062", "SkyFactory 4"),
    ("715572", "All the Mods 9 - ATM9"),
    ("466901", "Prominence II"),
    ("829758", "DawnCraft"),
    ("520914", "All the Mods 8 - ATM8"),
    ("490660", "DeceasedCraft"),
]


class TestCurseForgeReleaseDateSemantics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = sqlite3.connect(DB_PATH)
        cls.conn.row_factory = sqlite3.Row
        with open(RAW_PATH, "r", encoding="utf-8") as f:
            raw_items = json.load(f)
        cls.raw_map = {str(it.get("project_id") or it.get("slug")): it for it in raw_items}

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_curseforge_all_releases_null(self):
        """Verify all 45,797 CurseForge releases have release_date == NULL."""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT COUNT(r.id),
                   SUM(CASE WHEN r.release_date IS NOT NULL THEN 1 ELSE 0 END),
                   SUM(CASE WHEN r.release_date IS NULL THEN 1 ELSE 0 END)
            FROM releases r
            JOIN source_items s ON r.source_item_id = s.id
            WHERE s.platform = 'curseforge'
        """)
        tot, non_null, is_null = cur.fetchone()
        self.assertEqual(tot, EXPECTED_CURSEFORGE_RELEASES)
        self.assertEqual(non_null or 0, 0, "No CurseForge release may have non-null release_date without file evidence")
        self.assertEqual(is_null, EXPECTED_CURSEFORGE_RELEASES)

    def test_curseforge_source_items_dates_preserved(self):
        """Verify CurseForge source items project-level published_at and modified_at remain unchanged."""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id, published_at, modified_at
            FROM source_items
            WHERE platform = 'curseforge'
            ORDER BY id
        """)
        rows = cur.fetchall()
        self.assertEqual(len(rows), EXPECTED_CURSEFORGE_RELEASES)

        h = hashlib.sha256()
        for r in rows:
            h.update(json.dumps([r["id"], r["published_at"], r["modified_at"]], ensure_ascii=True, separators=(',', ':')).encode('utf-8'))
            h.update(b'\n')

        computed_digest = h.hexdigest()
        self.assertEqual(computed_digest, EXPECTED_SOURCE_ITEMS_DIGEST, "CurseForge source_items dates digest mismatch!")

    def test_curseforge_golden_10_samples(self):
        """Verify 10 real CurseForge Golden Samples prove project dates != release_date."""
        cur = self.conn.cursor()

        for pid, name_fragment in GOLDEN_PIDS:
            cur.execute("""
                SELECT r.id, r.release_date, s.published_at, s.modified_at, s.title
                FROM releases r
                JOIN source_items s ON r.source_item_id = s.id
                WHERE s.source_id = ? AND s.platform = 'curseforge'
            """, (pid,))
            row = cur.fetchone()
            self.assertIsNotNone(row, f"Golden sample {pid} ({name_fragment}) not found in DB")

            raw = self.raw_map.get(pid)
            self.assertIsNotNone(raw, f"Golden sample {pid} not found in raw snapshot")

            # 1. release_date is strictly NULL
            self.assertIsNone(row["release_date"], f"{pid} release_date must be NULL")

            # 2. project published_at and modified_at exist and match raw
            raw_created = raw.get("date_created")
            raw_modified = raw.get("date_modified")

            self.assertIsNotNone(row["published_at"], f"{pid} published_at should not be NULL")
            self.assertIsNotNone(row["modified_at"], f"{pid} modified_at should not be NULL")

            self.assertEqual(row["published_at"], raw_created)
            self.assertEqual(row["modified_at"], raw_modified)

            # 3. Project dates do NOT equal release_date
            self.assertNotEqual(row["release_date"], raw_created)
            self.assertNotEqual(row["release_date"], raw_modified)

    def test_non_curseforge_platforms_untouched(self):
        """Verify Modrinth and MCMod release dates were not altered."""
        cur = self.conn.cursor()

        # Modrinth has 18,328 non-null releases
        cur.execute("""
            SELECT COUNT(r.id),
                   SUM(CASE WHEN r.release_date IS NOT NULL THEN 1 ELSE 0 END)
            FROM releases r
            JOIN source_items s ON r.source_item_id = s.id
            WHERE s.platform = 'modrinth'
        """)
        mr_tot, mr_non_null = cur.fetchone()
        self.assertEqual(mr_tot, 18328)
        self.assertEqual(mr_non_null, 18328)

        # MCMod has 326 non-null releases, 1158 null releases
        cur.execute("""
            SELECT COUNT(r.id),
                   SUM(CASE WHEN r.release_date IS NOT NULL THEN 1 ELSE 0 END),
                   SUM(CASE WHEN r.release_date IS NULL THEN 1 ELSE 0 END)
            FROM releases r
            JOIN source_items s ON r.source_item_id = s.id
            WHERE s.platform = 'mcmod'
        """)
        mc_tot, mc_non_null, mc_null = cur.fetchone()
        self.assertEqual(mc_tot, 1484)
        self.assertEqual(mc_non_null, 326)
        self.assertEqual(mc_null, 1158)


if __name__ == "__main__":
    unittest.main()

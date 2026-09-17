"""
Release-Date Semantics Contract Tests (Architecture V2 - Phase 3F.2).

Locks down the single canonical `release_date` rule and guarantees that the
Migration Path and the Fresh Build Path can never diverge again.

Canonical rule under test
-------------------------
    release_date = the release/version-scoped publication timestamp published by
                   the source platform for that release/version.
    Forbidden    : crawler observed time, forum post/edit time, video publish time,
                   project-level publication/update metadata.
    No release-scoped evidence  ->  NULL (never a fallback for field completeness).

Covered contract clauses
------------------------
  C1  unknown placeholder ('未知'/'未知时间'/'N/A'/'-'/'') -> NULL
  C2  Bilibili video `published_at` does NOT automatically become `release_date`
  C3  official structured release timestamp -> release_date preserved
  C4  migration path == fresh path (row-level, whole table)
  C5  forum post time is never promoted to release_date
  C6  adapter-level: absence of release-scoped evidence -> NULL (no fallback)
"""
import json
import os
import sqlite3
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

CANONICAL_DB_PATH = os.path.join(REPO_ROOT, "build", "canonical.db")
FRESH_DB_PATH = os.path.join(REPO_ROOT, "build", "canonical_fresh_verify.db")

# --- Golden samples (real production rows) ---------------------------------
GOLDEN_BBSMC_VERSION = "bbsmc:1p2TFl6X:rel:Vt03UhFi"     # structured version date_published
GOLDEN_BBSMC_VERSION_DATE = "2026-02-26 16:24:58"
GOLDEN_XYEBBS_VERSION = "xyebbs:547:rel:167437"           # structured release createDate
GOLDEN_XYEBBS_VERSION_DATE = "2026-07-20 20:10:32"
GOLDEN_XYEBBS_SYNTHETIC = "xyebbs:801:rel:latest"         # forum thread, no release evidence
GOLDEN_BBSMC_SYNTHETIC = "bbsmc:XMUypeti:rel:latest"      # forum thread, no release evidence
GOLDEN_BILI = "bilibili:BV1aRYC6cE4p:rel:latest"          # video, no release evidence


def _load_raw(platform_file: str):
    with open(os.path.join(REPO_ROOT, "crawler_output", platform_file), "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data if isinstance(data, list) else data.get("items") or []


class TestReleaseDateSemantics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(CANONICAL_DB_PATH):
            raise unittest.SkipTest(f"canonical.db not found at {CANONICAL_DB_PATH}")
        cls.conn = sqlite3.connect(CANONICAL_DB_PATH)
        cls.cur = cls.conn.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def _release_date(self, release_id):
        self.cur.execute("SELECT release_date FROM releases WHERE id = ?", (release_id,))
        row = self.cur.fetchone()
        self.assertIsNotNone(row, f"golden release row missing: {release_id}")
        return row[0]

    # ---------------------------------------------------------------- C1
    def test_c1_unknown_placeholder_maps_to_null(self):
        """'未知' style placeholders must sanitize to NULL, never reach the DB."""
        from pipeline.adapters.bbsmc import clean_date_str as bbsmc_clean
        from pipeline.adapters.xyebbs import clean_date_str as xyebbs_clean
        from pipeline.adapters.mcmod import clean_date_str as mcmod_clean

        for cleaner in (bbsmc_clean, xyebbs_clean, mcmod_clean):
            for placeholder in ("未知", "未知时间", "N/A", "-", "", "   ", None):
                self.assertIsNone(cleaner(placeholder), f"{cleaner.__module__} leaked {placeholder!r}")
            self.assertEqual(cleaner("2025-01-04 09:34"), "2025-01-04 09:34")

        # No placeholder may survive in the canonical DB.
        self.cur.execute("SELECT COUNT(*) FROM releases WHERE release_date LIKE '%未知%'")
        self.assertEqual(self.cur.fetchone()[0], 0)

    # ---------------------------------------------------------------- C2
    def test_c2_bilibili_video_published_at_never_becomes_release_date(self):
        """Bilibili video publish time is NOT a modpack release date."""
        from pipeline.adapters.bilibili import BilibiliAdapter

        adapter = BilibiliAdapter()
        raw_items = _load_raw("bilibili_modpacks.json")
        self.assertTrue(raw_items, "bilibili raw snapshot is empty")

        with_video_time = [it for it in raw_items if it.get("pub_time")][:25]
        self.assertTrue(with_video_time, "no bilibili items carry pub_time")

        for idx, item in enumerate(with_video_time):
            bundle = adapter.adapt_item(item, idx)
            for rel in bundle.releases:
                self.assertIsNone(
                    rel.release_date,
                    f"bilibili release_date fabricated for {item.get('bvid')}",
                )
            # published_at must still carry the video publish time (untouched semantics).
            self.assertIsNotNone(bundle.source_item.published_at)

        # Canonical DB level: zero Bilibili releases may carry a release_date.
        self.cur.execute("""
            SELECT COUNT(*) FROM releases r JOIN source_items s ON r.source_item_id = s.id
            WHERE s.platform = 'bilibili' AND r.release_date IS NOT NULL
        """)
        self.assertEqual(self.cur.fetchone()[0], 0)

        # Golden sample.
        self.assertIsNone(self._release_date(GOLDEN_BILI))

    # ---------------------------------------------------------------- C3
    def test_c3_official_structured_release_timestamp_is_preserved(self):
        """Structured, version-scoped platform timestamps must survive."""
        from pipeline.adapters.bbsmc import BbsmcAdapter
        from pipeline.adapters.xyebbs import XyebbsAdapter

        # --- BBSMC: version-scoped `date_published` (ISO-8601 UTC)
        bbsmc_raw = {str(i.get("project_id")): i for i in _load_raw("bbsmc_modpacks.json")}
        project = bbsmc_raw["1p2TFl6X"]
        self.assertTrue(project.get("versions_data"), "golden bbsmc project lost versions_data")
        bundle = BbsmcAdapter().adapt_item(project, 0)
        by_name = {r.version_name: r.release_date for r in bundle.releases}
        self.assertEqual(by_name.get("乌托邦探险之旅3.5.2"), GOLDEN_BBSMC_VERSION_DATE)
        self.assertEqual(self._release_date(GOLDEN_BBSMC_VERSION), GOLDEN_BBSMC_VERSION_DATE)
        # ISO-8601 must be normalized to the canonical "YYYY-MM-DD HH:MM:SS" form.
        self.assertNotIn("T", self._release_date(GOLDEN_BBSMC_VERSION))
        self.assertNotIn("Z", self._release_date(GOLDEN_BBSMC_VERSION))

        # --- XYEBBS: release-scoped `createDate`
        xyebbs_raw = {str(i.get("project_id")): i for i in _load_raw("xyebbs_modpacks.json")}
        xyebbs_project = xyebbs_raw["547"]
        self.assertTrue(xyebbs_project.get("releases_data"), "golden xyebbs project lost releases_data")
        bundle = XyebbsAdapter().adapt_item(xyebbs_project, 0)
        by_name = {r.version_name: r.release_date for r in bundle.releases}
        self.assertEqual(by_name.get("2.7.1"), GOLDEN_XYEBBS_VERSION_DATE)
        self.assertEqual(self._release_date(GOLDEN_XYEBBS_VERSION), GOLDEN_XYEBBS_VERSION_DATE)

    # ---------------------------------------------------------------- C4
    def test_c4_migration_path_equals_fresh_path(self):
        """Migrated DB and freshly rebuilt DB must agree on release_date, row by row."""
        if not os.path.exists(FRESH_DB_PATH):
            self.skipTest(f"fresh verify DB not found at {FRESH_DB_PATH}")

        fresh = sqlite3.connect(FRESH_DB_PATH)
        try:
            migrated_rows = {
                r[0]: (r[1], r[2], r[3])
                for r in self.cur.execute(
                    "SELECT id, release_date, version_name, is_latest FROM releases ORDER BY id"
                )
            }
            fresh_rows = {
                r[0]: (r[1], r[2], r[3])
                for r in fresh.execute(
                    "SELECT id, release_date, version_name, is_latest FROM releases ORDER BY id"
                )
            }
        finally:
            fresh.close()

        self.assertEqual(set(migrated_rows), set(fresh_rows), "release id sets differ between DBs")

        mismatches = [
            (rid, migrated_rows[rid][0], fresh_rows[rid][0])
            for rid in migrated_rows
            if migrated_rows[rid][0] != fresh_rows[rid][0]
        ]
        self.assertEqual(
            mismatches, [],
            f"{len(mismatches)} release_date rows diverge between migration and fresh build: {mismatches[:5]}",
        )
        self.assertEqual(len(migrated_rows), 73533, "unexpected release row count")

    # ---------------------------------------------------------------- C5
    def test_c5_forum_post_time_is_never_promoted_to_release_date(self):
        """XYEBBS / BBSMC forum thread aggregates must not carry a fabricated date."""
        self.cur.execute("""
            SELECT COUNT(*) FROM releases
            WHERE (id LIKE 'xyebbs:%:rel:latest' OR id LIKE 'bbsmc:%:rel:latest')
              AND release_date IS NOT NULL
        """)
        self.assertEqual(self.cur.fetchone()[0], 0)

        for golden, platform in (
            (GOLDEN_XYEBBS_SYNTHETIC, "xyebbs"),
            (GOLDEN_BBSMC_SYNTHETIC, "bbsmc"),
        ):
            self.assertIsNone(self._release_date(golden), f"{platform} aggregate fabricated a date")
            self.cur.execute("SELECT published_at FROM source_items WHERE id = ?", (golden.rsplit(":rel:", 1)[0],))
            self.assertIsNotNone(
                self.cur.fetchone()[0],
                f"{platform} source published_at must be preserved (other time semantics untouched)",
            )

    # ---------------------------------------------------------------- C6
    def test_c6_adapter_absence_of_evidence_yields_null_not_fallback(self):
        """Adapters must return NULL when no release-scoped timestamp exists."""
        from pipeline.adapters.xyebbs import XyebbsAdapter
        from pipeline.adapters.bbsmc import BbsmcAdapter

        # Synthetic item WITH a project-level date_created: must still be NULL.
        xyebbs_item = {
            "project_id": "SYNTH",
            "name": "合成测试包",
            "url": "https://www.xyebbs.com/x",
            "date_created": "2024-01-01 00:00:00",
            "date_modified": "2025-06-06 12:00:00",
            "download_links": [],
        }
        bundle = XyebbsAdapter().adapt_item(xyebbs_item, 0)
        self.assertEqual(len(bundle.releases), 1)
        self.assertIsNone(bundle.releases[0].release_date, "xyebbs fell back to forum post time")
        self.assertEqual(bundle.source_item.published_at, "2024-01-01 00:00:00")

        bbsmc_item = {
            "project_id": "SYNTH",
            "name": "合成测试包",
            "url": "https://www.bbsmc.net/x",
            "date_created": "2024-01-01 00:00:00",
            "date_modified": "2025-06-06 12:00:00",
            "download_links": [],
        }
        bundle = BbsmcAdapter().adapt_item(bbsmc_item, 0)
        self.assertEqual(len(bundle.releases), 1)
        self.assertIsNone(bundle.releases[0].release_date, "bbsmc fell back to forum post time")
        self.assertEqual(bundle.source_item.published_at, "2024-01-01 00:00:00")

        # A version-scoped timestamp IS accepted.
        bbsmc_versioned = dict(bbsmc_item)
        bbsmc_versioned["versions_data"] = [
            {"id": "V1", "name": "v1.0", "date_published": "2025-02-03T04:05:06.000000Z"}
        ]
        bundle = BbsmcAdapter().adapt_item(bbsmc_versioned, 0)
        self.assertEqual(bundle.releases[0].release_date, "2025-02-03 04:05:06")


if __name__ == "__main__":
    unittest.main(verbosity=2)

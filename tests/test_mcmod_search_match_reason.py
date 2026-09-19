"""
Architecture V2 - Phase 3G-C.1: Search Match-Reason Exactness Contract Tests.

Validates:
1. RLCraft 96 vs 93 exact mathematical resolution and runtime parity.
2. 20-query corpus parity between Python simulation and Production runtime.
3. Strict definition of "mods-only" matching.
4. Exact matched mod strings (proving RLArtifacts/RLCombat match via -RLCraft版, while RLMixins does not).
5. Category != Importance invariant (preventing false inference from category to importance).
"""
import os
import sys
import json
import sqlite3
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

CANONICAL_DB_PATH = os.path.join(REPO_ROOT, "build", "canonical.db")
MCMOD_DATA_PATH = os.path.join(REPO_ROOT, "converted_output", "data", "mcmod_data.js")
MATCH_REASON_PATH = os.path.join(REPO_ROOT, "build", "audit", "mcmod_rlcraft_match_reason.json")
RUNTIME_20_PATH = os.path.join(REPO_ROOT, "build", "audit", "mcmod_runtime_search_20.json")


class TestMcmodSearchMatchReason(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(CANONICAL_DB_PATH):
            raise unittest.SkipTest(f"canonical.db not found at {CANONICAL_DB_PATH}")
        if not os.path.exists(MCMOD_DATA_PATH):
            raise unittest.SkipTest(f"mcmod_data.js not found at {MCMOD_DATA_PATH}")

        cls.conn = sqlite3.connect(CANONICAL_DB_PATH)
        cls.cur = cls.conn.cursor()

        with open(MCMOD_DATA_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        json_str = content.split("window.mcmodData = ")[1].rsplit(";", 1)[0]
        cls.mcmod_data = json.loads(json_str)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_rlcraft_96_vs_93_exact_resolution(self):
        """Verify the exact mathematical origin of 96 (DB) vs 93 (Client Runtime) RLCraft matches."""
        # 1. Client runtime replication (Title + typeName + formerTitles + categories + modSearchText)
        client_matches = []
        for r in self.mcmod_data:
            former = " ".join(r.get("formerTitles") or [])
            target = " ".join([
                r.get("title") or "",
                r.get("typeName") or "",
                former,
                " ".join(r.get("categories") or []),
                ", ".join(r.get("includedModNames") or [])
            ]).lower()
            if "rlcraft" in target:
                client_matches.append(r["mid"])

        self.assertEqual(len(client_matches), 93, "Client runtime must match exactly 93 packs")

        # 2. Canonical DB all-text search (including source_items.description)
        db_mods = [r[0] for r in self.cur.execute("""
            SELECT DISTINCT source_item_id FROM included_mods 
            WHERE lower(mod_name) LIKE '%rlcraft%' OR lower(mod_title) LIKE '%rlcraft%'
        """).fetchall()]
        db_titles = [r[0] for r in self.cur.execute("""
            SELECT id FROM source_items WHERE platform = 'mcmod' AND lower(title) LIKE '%rlcraft%'
        """).fetchall()]
        db_descs = [r[0] for r in self.cur.execute("""
            SELECT id FROM source_items WHERE platform = 'mcmod' AND lower(description) LIKE '%rlcraft%'
        """).fetchall()]

        all_db_ids = {int(x.split(":")[1]) for x in set(db_mods) | set(db_titles) | set(db_descs)}
        self.assertEqual(len(all_db_ids), 96, "Canonical DB including description must match exactly 96 packs")

        # 3. Exact 3-pack symmetric difference
        diff_ids = sorted(all_db_ids - set(client_matches))
        self.assertEqual(diff_ids, [255, 413, 1231], "Exact 3 diff IDs must be [255, 413, 1231]")

        # 4. Prove the 3 diff packs match SOLELY in source_items.description
        for mid in diff_ids:
            item = self.cur.execute("SELECT title, description FROM source_items WHERE id = ?", (f"mcmod:{mid}",)).fetchone()
            self.assertNotIn("rlcraft", (item[0] or "").lower(), f"Pack {mid} must not have rlcraft in title")
            self.assertIn("rlcraft", (item[1] or "").lower(), f"Pack {mid} must have rlcraft in description")
            
            # verify none of their included mods contain rlcraft
            mods = self.cur.execute("""
                SELECT mod_name, mod_title FROM included_mods 
                WHERE source_item_id = ? AND (lower(mod_name) LIKE '%rlcraft%' OR lower(mod_title) LIKE '%rlcraft%')
            """, (f"mcmod:{mid}",)).fetchall()
            self.assertEqual(len(mods), 0, f"Pack {mid} must have 0 rlcraft included mods")

    def test_exact_matched_mod_strings_and_rlmixins_absence(self):
        """Verify the exact 6 mods with literal 'rlcraft' and prove RLMixins lacks literal 'rlcraft'."""
        rows = self.cur.execute("""
            SELECT DISTINCT mod_name, mod_title 
            FROM included_mods 
            WHERE lower(mod_name) LIKE '%rlcraft%' OR lower(mod_title) LIKE '%rlcraft%'
            ORDER BY mod_name
        """).fetchall()

        matched_names = [r[0] for r in rows]
        expected_names = [
            'RLCraft Structures (not official)',
            '冰火传说-RLCraft版 (I&F：RLCraft Edition)',
            '可穿戴背包-RLCraft版 (Wearable Backpacks: RLCraft Edition)',
            '奇异饰品-RLCraft版 (RLArtifacts)',
            '斯巴达之冰与火-RLCraft版 (Spartan and Fire: RLCraft Edition)',
            '更好的战斗-RLCraft版 (RLCombat)'
        ]
        self.assertEqual(matched_names, expected_names, "Exactly 6 distinct mods contain literal rlcraft")

        # Prove RLArtifacts matches because of '-RLCraft版', not because of 'RLArtifacts'
        artifact_mod = [r for r in rows if 'RLArtifacts' in r[0]][0]
        self.assertIn("-rlcraft版", artifact_mod[0].lower())

        # Prove RLMixins in canonical.db does NOT contain literal 'rlcraft'
        mixins = self.cur.execute("""
            SELECT mod_name, mod_title FROM included_mods WHERE lower(mod_name) LIKE '%rlmixins%'
        """).fetchall()
        self.assertGreater(len(mixins), 0, "RLMixins must exist in canonical.db")
        for m_name, m_title in mixins:
            self.assertNotIn("rlcraft", m_name.lower(), "RLMixins stored name must not contain rlcraft")
            self.assertNotIn("rlcraft", m_title.lower(), "RLMixins stored title must not contain rlcraft")

    def test_strict_mods_only_definition(self):
        """Verify strict definition of 'mods-only' matching on the 96 RLCraft candidates."""
        self.assertTrue(os.path.exists(MATCH_REASON_PATH), f"Missing {MATCH_REASON_PATH}")
        with open(MATCH_REASON_PATH, "r", encoding="utf-8") as f:
            candidates = json.load(f)

        self.assertEqual(len(candidates), 96)

        multi_field_count = sum(1 for c in candidates if c["match_classification"] == "multi-field")
        mods_only_count = sum(1 for c in candidates if c["match_classification"] == "included_mod")
        desc_only_count = sum(1 for c in candidates if c["match_classification"] == "description")

        self.assertEqual(multi_field_count, 7, "Exactly 7 multi-field packs")
        self.assertEqual(mods_only_count, 86, "Exactly 86 strict mods-only packs")
        self.assertEqual(desc_only_count, 3, "Exactly 3 DB description-only packs")
        self.assertEqual(multi_field_count + mods_only_count + desc_only_count, 96)

        # In runtime (client), 86 + 7 = 93
        runtime_matched = [c for c in candidates if c["runtime_matched"]]
        self.assertEqual(len(runtime_matched), 93)

        # For every mods-only pack, verify query does NOT match title, author, description, or categories
        for c in candidates:
            if c["is_mods_only"]:
                self.assertEqual(len(c["fields"]["title"]), 0)
                self.assertEqual(len(c["fields"]["author"]), 0)
                self.assertEqual(len(c["fields"]["description"]), 0)
                self.assertEqual(len(c["fields"]["categories"]), 0)
                self.assertGreater(len(c["fields"]["included_mods"]), 0)

    def test_category_not_conflated_with_importance(self):
        """Invariant: Mod Category must never be treated as pack dependency importance."""
        total = self.cur.execute("SELECT COUNT(*) FROM included_mods").fetchone()[0]
        lib_count = self.cur.execute("SELECT COUNT(*) FROM included_mods WHERE category_name = 'LIB'").fetchone()[0]
        aux_count = self.cur.execute("SELECT COUNT(*) FROM included_mods WHERE category_name = '辅助'").fetchone()[0]

        lib_and_aux_pct = (lib_count + aux_count) / total * 100
        self.assertAlmostEqual(lib_and_aux_pct, 52.55, delta=0.1)

        # Ensure canonical schema has no relationship_type column to prevent false inference
        cols = [c[1] for c in self.cur.execute("PRAGMA table_info(included_mods)").fetchall()]
        self.assertNotIn("relationship_type", cols)
        self.assertNotIn("is_core", cols)
        self.assertNotIn("is_required", cols)

    def test_runtime_parity_across_corpus_artifacts(self):
        """Verify that runtime search 20-corpus artifact exists and confirms parity."""
        if not os.path.exists(RUNTIME_20_PATH):
            raise unittest.SkipTest(f"Missing {RUNTIME_20_PATH}")
        with open(RUNTIME_20_PATH, "r", encoding="utf-8") as f:
            runtime_data = json.load(f)

        self.assertEqual(len(runtime_data), 20)
        rlcraft_item = [x for x in runtime_data if x["query"] == "RLCraft"][0]
        self.assertEqual(rlcraft_item["runtime"]["tsMatchedCount"], 93)
        self.assertEqual(rlcraft_item["runtime"]["dtMatchedCount"], 93)


if __name__ == "__main__":
    unittest.main()

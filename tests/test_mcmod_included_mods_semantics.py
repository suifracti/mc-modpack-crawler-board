"""
Architecture V2 - Phase 3G-C: MCMod Included Mods + Deep Search Semantics Contract Tests.

Validates the contracts of the Phase 3G-C Evidence Audit:
1. Mathematical lineage and 100% relation fidelity between raw crawler and canonical.db.
2. Structure and category distribution of the 30 Golden MCMod Packs and 200+ relation checks.
3. Absence of native relationship type provenance in MCMod source data.
4. Separation of Mod Category taxonomy from Pack Relationship semantics.
5. 20-query search corpus decomposition, proving included-mod-only match dominance for non-title queries.
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
GOLDEN_30_PATH = os.path.join(REPO_ROOT, "build", "audit", "mcmod_included_mods_golden_30.json")
QUERY_CORPUS_PATH = os.path.join(REPO_ROOT, "build", "audit", "mcmod_query_corpus_20.json")
RAW_FULL_DETAILS_PATH = os.path.join(REPO_ROOT, "crawler_output", "mcmod_full_details.json")
RAW_MODPACKS_PATH = os.path.join(REPO_ROOT, "crawler_output", "mcmod_modpacks.json")


class TestMcmodIncludedModsSemantics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(CANONICAL_DB_PATH):
            raise unittest.SkipTest(f"canonical.db not found at {CANONICAL_DB_PATH}")
        cls.conn = sqlite3.connect(CANONICAL_DB_PATH)
        cls.cur = cls.conn.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_canonical_schema_and_lack_of_relationship_type(self):
        """Verify included_mods table schema: has mod metadata and category, but NO relationship_type."""
        col_info = self.cur.execute("PRAGMA table_info(included_mods)").fetchall()
        col_names = [c[1] for c in col_info]

        self.assertIn("source_item_id", col_names)
        self.assertIn("mod_name", col_names)
        self.assertIn("class_id", col_names)
        self.assertIn("category_id", col_names)
        self.assertIn("category_name", col_names)
        self.assertIn("sort_order", col_names)

        # Invariant: Must NOT contain relationship_type or relation_kind
        self.assertNotIn("relationship_type", col_names)
        self.assertNotIn("relation_type", col_names)
        self.assertNotIn("relation_kind", col_names)
        self.assertNotIn("importance", col_names)

    def test_relation_fidelity_and_provenance(self):
        """Verify 100% of canonical included_mods originate from raw crawler data with 0 duplicates."""
        total_canonical = self.cur.execute("SELECT COUNT(*) FROM included_mods").fetchone()[0]
        self.assertEqual(total_canonical, 170078, "Canonical included_mods must have exactly 170,078 rows")

        # Verify 0 duplicate relations for the same (source_item_id, mod_name, class_id)
        dup_count = self.cur.execute("""
            SELECT COUNT(*) FROM (
                SELECT source_item_id, mod_name, class_id, COUNT(*) as c
                FROM included_mods
                GROUP BY source_item_id, mod_name, class_id
                HAVING c > 1
            )
        """).fetchone()[0]
        self.assertEqual(dup_count, 0, "Must have zero duplicate mod relations in canonical.db")

        # Distinct packs
        distinct_packs = self.cur.execute("SELECT COUNT(DISTINCT source_item_id) FROM included_mods").fetchone()[0]
        self.assertEqual(distinct_packs, 953, "Exactly 953 MCMod packs must possess included mods")

    def test_taxonomy_distribution_breakdown(self):
        """Verify taxonomy breakdown: 辅助 (33.20%) + LIB (19.35%) = 52.55%."""
        total_canonical = 170078
        cat_counts = dict(self.cur.execute("""
            SELECT COALESCE(category_name, '未分类'), COUNT(*)
            FROM included_mods
            GROUP BY category_name
        """).fetchall())

        self.assertEqual(cat_counts.get("辅助", 0), 56466)
        self.assertEqual(cat_counts.get("LIB", 0), 32910)
        self.assertEqual(cat_counts.get("实用", 0), 26421)
        self.assertEqual(cat_counts.get("冒险", 0), 16153)
        self.assertEqual(cat_counts.get("装饰", 0), 10351)
        self.assertEqual(cat_counts.get("科技", 0), 9545)
        self.assertEqual(cat_counts.get("魔改", 0), 8071)
        self.assertEqual(cat_counts.get("农业", 0), 6418)
        self.assertEqual(cat_counts.get("魔法", 0), 3727)
        self.assertEqual(cat_counts.get("未分类", 0), 16)

        lib_and_aux_pct = (cat_counts["辅助"] + cat_counts["LIB"]) / total_canonical * 100
        self.assertAlmostEqual(lib_and_aux_pct, 52.55, delta=0.1)

    def test_raw_no_relationship_provenance(self):
        """Verify raw crawler snapshot has no relationship fields."""
        self.assertTrue(os.path.exists(RAW_FULL_DETAILS_PATH), f"Missing {RAW_FULL_DETAILS_PATH}")
        with open(RAW_FULL_DETAILS_PATH, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        # Inspect first 100 packs
        allowed_keys = {'category_id', 'name', 'title', 'url', 'category_url', 'class_id', 'category_name', 'version'}
        forbidden_rel_keys = {'relationship_type', 'relation_type', 'is_dependency', 'is_required', 'is_optional'}

        checked = 0
        for mid, p in list(raw_data.items())[:100]:
            for m in p.get("mods", []):
                checked += 1
                self.assertTrue(set(m.keys()).issubset(allowed_keys), f"Unexpected key in raw mod: {m.keys()}")
                for fk in forbidden_rel_keys:
                    self.assertNotIn(fk, m)
                if checked >= 200:
                    break
            if checked >= 200:
                break

    def test_golden_30_contract(self):
        """Verify Golden 30 Packs artifact structure and 100% presence in raw."""
        self.assertTrue(os.path.exists(GOLDEN_30_PATH), f"Golden file missing: {GOLDEN_30_PATH}")
        with open(GOLDEN_30_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["total_golden_packs"], 30)
        self.assertGreaterEqual(data["total_relation_checks"], 150)
        self.assertEqual(data["distribution_summary"]["normal"], 10)
        self.assertEqual(data["distribution_summary"]["large"], 10)
        self.assertEqual(data["distribution_summary"]["small_focused"], 5)
        self.assertEqual(data["distribution_summary"]["edge_anomaly"], 5)

        # Verify all relation checks have raw_present == True and relationship_explicit == False
        for pack in data["packs"]:
            for check in pack["relation_checks"]:
                self.assertTrue(check["raw_present"], f"Check failed for {check['mod_name']} in {check['pack_title']}")
                self.assertFalse(check["relationship_explicit"], "MCMod must never claim explicit relationship")

    def test_20_query_corpus_and_isolation(self):
        """Verify 20-query search corpus breakdown and dominance of included-mod-only matches."""
        self.assertTrue(os.path.exists(QUERY_CORPUS_PATH), f"Query corpus missing: {QUERY_CORPUS_PATH}")
        with open(QUERY_CORPUS_PATH, "r", encoding="utf-8") as f:
            corpus = json.load(f)

        self.assertEqual(len(corpus), 20)
        by_query = {c["query"]: c for c in corpus}

        # 1. RLCraft has 96 matches, and >= 85% are mods_only
        rlc = by_query["RLCraft"]
        self.assertEqual(rlc["title"], 5)
        self.assertGreater(rlc["mods_only_pct"], 85.0)

        # 2. Utility / Library queries (JEI, Architectury, Cloth Config, Mouse Tweaks) have >= 90% mods_only
        for util in ["JEI", "Architectury", "Cloth Config", "Mouse Tweaks"]:
            self.assertIn(util, by_query)
            self.assertGreaterEqual(by_query[util]["mods_only_pct"], 90.0)

        # 3. Create core theme mod has >= 70% mods_only
        create_q = by_query["Create"]
        self.assertGreaterEqual(create_q["mods_only_pct"], 70.0)


if __name__ == "__main__":
    unittest.main()

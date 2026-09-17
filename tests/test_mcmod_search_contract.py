"""
Architecture V2 - Phase 3G-C.2: MCMod Search Contract Automated Test Suite.

Validates:
1. Multi-word search follows canonical TS SearchEngine whitespace tokens AND contract.
2. Contiguous phrase vs tokenized AND divergence (e.g. Fabric API: 664 vs 111; Ice and Fire: 260 vs 125).
3. Option B Description Contract: description is not in main table index (MIDs 255/413/1231 do not match).
4. UI Placeholder honesty: no false promise of searching 简介 (description).
5. Single Source of Truth: DataTables visible IDs == TS SearchEngine matched IDs across the 20-query corpus.
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
INDEX_HTML_PATH = os.path.join(REPO_ROOT, "apps", "web", "index.html")
CONVERTED_INDEX_PATH = os.path.join(REPO_ROOT, "converted_output", "index.html")
RUNTIME_20_PATH = os.path.join(REPO_ROOT, "build", "audit", "mcmod_runtime_search_20.json")


class TestMcmodSearchContract(unittest.TestCase):
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

    def _simulate_search_engine(self, query: str):
        """Simulates TS SearchEngine whitespace tokenized AND matching on mcmod_data."""
        tokens = query.lower().strip().split()
        if not tokens:
            return [r["mid"] for r in self.mcmod_data]

        matched = []
        for r in self.mcmod_data:
            former = " ".join(r.get("formerTitles") or [])
            searchable_text = " ".join([
                r.get("title") or "",
                r.get("typeName") or "",
                former,
                r.get("author") or "",
                " ".join(r.get("categories") or []),
                r.get("modSearchText") or ""
            ]).lower()

            if all(t in searchable_text for t in tokens):
                matched.append(r["mid"])
        return matched

    def _simulate_contiguous_phrase_search(self, query: str):
        """Simulates legacy DataTables smart:false exact contiguous substring match."""
        q = query.lower().strip()
        if not q:
            return [r["mid"] for r in self.mcmod_data]

        matched = []
        for r in self.mcmod_data:
            former = " ".join(r.get("formerTitles") or [])
            searchable_text = " ".join([
                r.get("title") or "",
                r.get("typeName") or "",
                former,
                r.get("author") or "",
                " ".join(r.get("categories") or []),
                r.get("modSearchText") or ""
            ]).lower()

            if q in searchable_text:
                matched.append(r["mid"])
        return matched

    def test_multiword_canonical_tokens_and_semantics(self):
        """Verify multi-word queries match via whitespace tokenized AND, not contiguous phrase."""
        # 1. 'Fabric API': TS Engine must match 664, whereas contiguous phrase only matches 111
        fabric_api_tokens = self._simulate_search_engine("Fabric API")
        fabric_api_contiguous = self._simulate_contiguous_phrase_search("Fabric API")

        self.assertEqual(len(fabric_api_tokens), 664, "Fabric API tokenized AND must match exactly 664 packs")
        self.assertEqual(len(fabric_api_contiguous), 111, "Fabric API contiguous phrase matches 111 packs")
        self.assertGreater(len(fabric_api_tokens), len(fabric_api_contiguous),
                           "Canonical multi-word search must encompass tokenized AND hits")

        # 2. 'Ice and Fire': TS Engine must match 260, whereas contiguous phrase only matches 125
        iaf_tokens = self._simulate_search_engine("Ice and Fire")
        iaf_contiguous = self._simulate_contiguous_phrase_search("Ice and Fire")

        self.assertEqual(len(iaf_tokens), 260, "Ice and Fire tokenized AND must match exactly 260 packs")
        self.assertEqual(len(iaf_contiguous), 125, "Ice and Fire contiguous phrase matches 125 packs")

        # 3. Other benchmark queries
        self.assertEqual(len(self._simulate_search_engine("Cloth Config")), 595)
        self.assertEqual(len(self._simulate_search_engine("Mouse Tweaks")), 736)
        self.assertEqual(len(self._simulate_search_engine("Applied Energistics")), 354)

    def test_option_b_description_contract_verification(self):
        """Verify Option B: description is excluded from main table search index."""
        # Query canonical.db for MIDs where 'rlcraft' only appears in description
        self.cur.execute("""
            SELECT id, title, description FROM source_items
            WHERE platform = 'mcmod'
              AND lower(description) LIKE '%rlcraft%'
              AND lower(title) NOT LIKE '%rlcraft%'
              AND id NOT IN (
                  SELECT source_item_id FROM included_mods
                  WHERE lower(mod_name) LIKE '%rlcraft%' OR lower(mod_title) LIKE '%rlcraft%'
              )
        """)
        rows = self.cur.fetchall()
        db_desc_only_mids = [int(r[0].split(":")[1]) for r in rows]

        # In DB, these 3 packs (255, 413, 1231) have RLCraft in description only
        expected_desc_only = {255, 413, 1231}
        self.assertEqual(set(db_desc_only_mids), expected_desc_only,
                         f"Expected DB desc-only MIDs to be {expected_desc_only}, got {set(db_desc_only_mids)}")

        # Verify NONE of these 3 MIDs match in client runtime mcmod_data.js search
        client_rlcraft_matches = set(self._simulate_search_engine("RLCraft"))
        self.assertEqual(len(client_rlcraft_matches), 93, "Client runtime must match exactly 93 RLCraft packs")

        for mid in expected_desc_only:
            self.assertNotIn(mid, client_rlcraft_matches,
                             f"MID {mid} should NOT match client table search under Option B description contract")

    def test_ui_placeholder_honesty(self):
        """Verify UI search input placeholders do NOT falsely claim to search 简介 (description)."""
        for html_path in [INDEX_HTML_PATH, CONVERTED_INDEX_PATH]:
            if not os.path.exists(html_path):
                continue
            with open(html_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Find mcmodUnifiedSearch input element
            import re
            m = re.search(r'id=["\']mcmodUnifiedSearch["\'][^>]*placeholder=["\']([^"\']+)["\']', content)
            if not m:
                m = re.search(r'placeholder=["\']([^"\']+)["\'][^>]*id=["\']mcmodUnifiedSearch["\']', content)

            self.assertIsNotNone(m, f"mcmodUnifiedSearch input not found in {html_path}")
            placeholder_text = m.group(1)

            # Assert placeholder does NOT claim to search 简介 or description
            self.assertNotIn("简介", placeholder_text,
                             f"Placeholder in {html_path} falsely promises searching 简介: '{placeholder_text}'")
            self.assertNotIn("描述", placeholder_text,
                             f"Placeholder in {html_path} falsely promises searching 描述: '{placeholder_text}'")
            self.assertNotIn("description", placeholder_text.lower(),
                             f"Placeholder in {html_path} falsely promises searching description: '{placeholder_text}'")

    def test_single_source_of_truth_runtime_parity(self):
        """Verify TS SearchEngine matched IDs == DataTables visible IDs for all 20 queries."""
        if not os.path.exists(RUNTIME_20_PATH):
            raise unittest.SkipTest(f"Runtime 20-query audit file not found at {RUNTIME_20_PATH}")

        with open(RUNTIME_20_PATH, "r", encoding="utf-8") as f:
            audit_data = json.load(f)

        self.assertEqual(len(audit_data), 20, "Expected 20 queries in runtime audit")

        for item in audit_data:
            q = item["query"]
            rt = item["runtime"]
            ts_count = rt["tsMatchedCount"]
            dt_count = rt["dtMatchedCount"]
            ts_ids = rt["tsMatchedIds"]
            dt_ids = rt["dtMatchedIds"]

            # 1. Exact count equality
            self.assertEqual(ts_count, dt_count,
                             f"Query '{q}': TS count ({ts_count}) != DT count ({dt_count})")

            # 2. Exact 100% ID-set equality (0 difference)
            self.assertEqual(ts_ids, dt_ids,
                             f"Query '{q}': TS matched IDs != DT visible IDs. Diff count: {len(set(ts_ids) ^ set(dt_ids))}")

    def test_search_match_reasons_audit_integrity(self):
        """Phase 3G-D: Verify search match reasons integrity and explainability across the 20-query corpus."""
        if not os.path.exists(RUNTIME_20_PATH):
            raise unittest.SkipTest(f"Runtime 20-query audit file not found at {RUNTIME_20_PATH}")

        with open(RUNTIME_20_PATH, "r", encoding="utf-8") as f:
            audit_data = json.load(f)

        for item in audit_data:
            q = item["query"]
            rt = item["runtime"]
            ts_count = rt["tsMatchedCount"]
            reasons_count = rt.get("reasonsCount", 0)

            # Every matched pack must have an associated match reason
            self.assertEqual(ts_count, reasons_count,
                             f"Query '{q}': tsMatchedCount ({ts_count}) != reasonsCount ({reasons_count})")

            # Option B & Phase 3G-D Contract: Match Reason MUST NEVER report '命中简介'
            sample_reasons = rt.get("sampleReasons", {})
            for mid, reason_info in sample_reasons.items():
                label = reason_info.get("primaryReasonLabel", "")
                self.assertNotIn("命中简介", label,
                                 f"Query '{q}' MID {mid} falsely contains '命中简介': '{label}'")
                self.assertNotIn("简介", label,
                                 f"Query '{q}' MID {mid} falsely contains '简介': '{label}'")

        # Golden Assertions for RLCraft
        rlcraft_entry = next(x for x in audit_data if x["query"] == "RLCraft")
        rl_samples = rlcraft_entry["runtime"]["sampleReasons"]

        # MID 16 has RLCraft in title -> must be '名称匹配'
        self.assertIn("16", rl_samples)
        self.assertEqual(rl_samples["16"]["primaryReasonLabel"], "名称匹配")
        self.assertIn("title", rl_samples["16"]["fields"])

        # MID 304 matches included mod '奇异饰品-RLCraft版 (RLArtifacts)'
        self.assertIn("304", rl_samples)
        self.assertIn("奇异饰品-RLCraft版 (RLArtifacts)", rl_samples["304"]["primaryReasonLabel"])
        self.assertIn("included_mod", rl_samples["304"]["fields"])

        # Negative check: RLMixins does not contain 'rlcraft', so it must never be the matched mod reason
        for mid, r_info in rl_samples.items():
            label = r_info.get("primaryReasonLabel", "")
            self.assertNotIn("RLMixins", label,
                             f"RLMixins falsely matched for RLCraft query in MID {mid}: '{label}'")


if __name__ == "__main__":
    unittest.main()


"""
Architecture V2 - Phase 3G-D.1: Match-Reason Structured Source Integrity Tests.

The risk this suite guards against: search hits can be correct while the UI's
"包含模组：XXX" explanation is wrong.

Before this phase the pipeline was:

    canonical included_mods (structured)
      -> exporter:  modSearchText = ", ".join(all_mod_names)
      -> frontend:  includedModNames = modSearchText.split(", ").map(trim).filter(Boolean)

That reverse-parse is NOT injective. When a real mod name contains the ", "
delimiter the flat string silently splits into fabricated mod names.

This suite locks in the corrected architecture:

    canonical included_mods (structured)
      -> exporter:  includedModNames: string[]          (structured, complete, ordered)
      -> frontend:  modsLower = includedModNames.join(", ")   (forward derivation only)
                    includedModNames                            (exact reason provenance)

Coverage:
    C1 payload carries structured provenance only (no flat modSearchText)
    C2 structured array == canonical mod_name, order and content, all packs
    C3 flat search index is forward-derived and identical to the legacy value
    C4 delimiter collision scan (full 170,078-relation corpus)
    C5 full round-trip audit over all packs; legacy path loss is documented
    C6 20-query matched-ID invariance
    C7 exact canonical mod name equality in match reason
    C8 RLMixins negative (no fabricated reason entry)
    C9 multi-word cross-field reason is not merged into a fake mod name
"""
import json
import os
import sqlite3
import sys
import unittest
from collections import defaultdict

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

CANONICAL_DB_PATH = os.path.join(REPO_ROOT, "build", "canonical.db")
MCMOD_DATA_PATH = os.path.join(REPO_ROOT, "converted_output", "data", "mcmod_data.js")
GOLDEN_20_PATH = os.path.join(REPO_ROOT, "build", "audit", "mcmod_runtime_search_20.json")
ROUNDTRIP_ARTIFACT = os.path.join(REPO_ROOT, "build", "audit", "mcmod_modsearch_roundtrip_failures.json")

DELIMITER = ", "

# Exact canonical names involved in the delimiter collision.
COLLIDING_NAME = "Get It Together, Drops!"
COLLIDING_PACK = 1007
# The two fabricated names the legacy reverse-parse produced for that pack.
FABRICATED_FROM_COLLIDING_NAME = {"Get It Together", "Drops!"}

# Real pack that bundles RLMixins alongside four RLCraft-bearing mod names.
RLMIXINS_PACK = 16
RLMIXINS_RL_CRAFT_MODS = [
    "奇异饰品-RLCraft版 (RLArtifacts)",
    "斯巴达之冰与火-RLCraft版 (Spartan and Fire: RLCraft Edition)",
    "可穿戴背包-RLCraft版 (Wearable Backpacks: RLCraft Edition)",
    "更好的战斗-RLCraft版 (RLCombat)",
]

# 8-query exactness corpus required by Phase 3G-D.1.
REASON_QUERIES = [
    "RLCraft",
    "Create",
    "JEI",
    "Architectury",
    "Cloth Config",
    "Fabric API",
    "Ice and Fire",
    "Thermal",
]


def load_mcmod_data():
    with open(MCMOD_DATA_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    json_str = content.split("window.mcmodData = ")[1].rsplit(";", 1)[0]
    return json.loads(json_str)


def legacy_flat_text(pack):
    """What the pre-3G-D.1 exporter wrote into `modSearchText`."""
    return DELIMITER.join(pack.get("includedModNames") or [])


def legacy_reverse_parse(text):
    """What the pre-3G-D.1 frontend did to rebuild mod names."""
    if not text:
        return []
    return [p for p in (s.strip() for s in text.split(DELIMITER)) if p]


def searchable_text(pack):
    """Mirror of buildMcmodSearchDocument's searchable projection."""
    return " ".join([
        pack.get("title") or "",
        pack.get("typeName") or "",
        " ".join(pack.get("formerTitles") or []),
        pack.get("author") or "",
        " ".join(pack.get("categories") or []),
        DELIMITER.join(pack.get("includedModNames") or []),
    ]).lower()


def match_reason_mod_names(pack, query):
    """Mirror of the `included_mod` branch of matchDocument (searchEngine.ts).

    Returns {mod_name: {matched terms}} built ONLY from the structured array.
    """
    terms = query.lower().strip().split()
    hits = {}
    for name in pack.get("includedModNames") or []:
        low = name.lower()
        for t in terms:
            if t in low:
                hits.setdefault(name, set()).add(t)
    return hits


class TestMcmodMatchReasonSourceIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path in (CANONICAL_DB_PATH, MCMOD_DATA_PATH):
            if not os.path.exists(path):
                raise unittest.SkipTest(f"required artifact missing: {path}")

        cls.data = load_mcmod_data()
        cls.by_mid = {r["mid"]: r for r in cls.data}

        cls.conn = sqlite3.connect(CANONICAL_DB_PATH)
        cls.conn.row_factory = sqlite3.Row

        cls.canonical_names = defaultdict(list)   # mid -> [mod_name] in canonical order
        cls.canonical_set = set()
        for row in cls.conn.execute(
            "SELECT source_item_id, mod_name FROM included_mods "
            "WHERE source_item_id LIKE 'mcmod:%' "
            "ORDER BY source_item_id, sort_order, id"
        ):
            nm = row["mod_name"]
            if not nm:
                continue
            cls.canonical_names[int(row["source_item_id"].split(":", 1)[1])].append(nm)
            cls.canonical_set.add(nm)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    # ------------------------------------------------------------------ C1
    def test_c1_payload_carries_structured_provenance_only(self):
        """The payload must expose the structured array and no flat modSearchText."""
        with_flat = [r["mid"] for r in self.data if "modSearchText" in r]
        self.assertEqual(
            with_flat, [],
            f"flat modSearchText must be gone from the payload; still present on {len(with_flat)} packs",
        )

        missing = [r["mid"] for r in self.data if "includedModNames" not in r]
        self.assertEqual(missing, [], f"{len(missing)} packs missing includedModNames")

        not_list = [r["mid"] for r in self.data if not isinstance(r["includedModNames"], list)]
        self.assertEqual(not_list, [], f"{len(not_list)} packs where includedModNames is not a list")

        for r in self.data:
            for nm in r["includedModNames"]:
                self.assertIsInstance(nm, str, f"mid={r['mid']} non-string element in includedModNames")

    # ------------------------------------------------------------------ C2
    def test_c2_structured_array_equals_canonical_mod_name(self):
        """The array must be exactly canonical `included_mods.mod_name`, order included."""
        mismatched = []
        for r in self.data:
            expected = self.canonical_names.get(r["mid"], [])
            if r["includedModNames"] != expected:
                mismatched.append(r["mid"])

        self.assertEqual(
            mismatched, [],
            f"{len(mismatched)} packs whose includedModNames != canonical mod_name list (order+content)",
        )

    # ------------------------------------------------------------------ C3
    def test_c3_flat_index_is_forward_derived_and_identical(self):
        """join(array) must equal the legacy flat string -> search semantics provably unchanged."""
        mismatched = [
            r["mid"] for r in self.data
            if legacy_flat_text(r) != DELIMITER.join(self.canonical_names.get(r["mid"], []))
        ]
        self.assertEqual(mismatched, [], f"{len(mismatched)} packs where the derived flat index differs")

    # ------------------------------------------------------------------ C4
    def test_c4_delimiter_collision_scan(self):
        """Full-corpus delimiter collision scan with real counts."""
        total = self.conn.execute("SELECT COUNT(*) FROM included_mods").fetchone()[0]
        names_with = self.conn.execute(
            "SELECT COUNT(*) FROM included_mods WHERE mod_name LIKE '%, %'"
        ).fetchone()[0]
        titles_with = self.conn.execute(
            "SELECT COUNT(*) FROM included_mods WHERE mod_title LIKE '%, %'"
        ).fetchone()[0]
        distinct_mods = self.conn.execute(
            "SELECT COUNT(DISTINCT mod_name) FROM included_mods WHERE mod_name LIKE '%, %'"
        ).fetchone()[0]
        affected_packs = self.conn.execute(
            "SELECT COUNT(DISTINCT source_item_id) FROM included_mods WHERE mod_name LIKE '%, %'"
        ).fetchone()[0]

        self.assertEqual(total, 170078, "corpus size changed")
        self.assertGreater(names_with, 0, "expected real delimiter collisions in canonical data")
        self.assertEqual(names_with, titles_with, "mod_name / mod_title collision counts diverged")
        self.assertEqual(distinct_mods, 23, f"distinct affected mods = {distinct_mods}")
        self.assertEqual(affected_packs, 178, f"affected packs = {affected_packs}")

        self.assertIn(
            COLLIDING_NAME, self.canonical_set,
            "the reference colliding name must exist in canonical data",
        )

    # ------------------------------------------------------------------ C5
    def test_c5_full_roundtrip_audit(self):
        """Structured path is lossless for every pack; the legacy path was not."""
        new_exact = 0
        new_failed = []
        legacy_failed = []
        legacy_fabricated = set()

        for mid, r in self.by_mid.items():
            canonical = self.canonical_names.get(mid, [])

            # NEW path: payload array -> SearchDocument.includedModNames
            doc_names = r["includedModNames"]
            if doc_names == canonical:
                new_exact += 1
            else:
                new_failed.append(mid)

            # LEGACY path: flat string -> reverse parse
            parsed = legacy_reverse_parse(legacy_flat_text(r))
            if parsed != canonical:
                legacy_failed.append(mid)
                legacy_fabricated.update(n for n in parsed if n not in self.canonical_set)

        self.assertEqual(len(self.by_mid), 1484, "expected 1484 MCMod packs")
        self.assertEqual(new_failed, [], f"structured path failed for {len(new_failed)} packs")
        self.assertEqual(new_exact, 1484, f"exact round-trip packs = {new_exact}")

        # The legacy path is documented as lossy - this is WHY the change was made.
        self.assertEqual(len(legacy_failed), 178, f"legacy lossy packs = {len(legacy_failed)}")
        self.assertEqual(len(legacy_fabricated), 47, f"legacy fabricated names = {len(legacy_fabricated)}")
        self.assertIn("Get It Together", legacy_fabricated)
        self.assertIn("Drops!", legacy_fabricated)

        # The shipped failure artifact must agree with this recomputation.
        if os.path.exists(ROUNDTRIP_ARTIFACT):
            with open(ROUNDTRIP_ARTIFACT, "r", encoding="utf-8") as f:
                art = json.load(f)
            rt = art["roundtrip"]
            self.assertEqual(rt["failed_roundtrip_packs"], len(legacy_failed))
            self.assertEqual(rt["distinct_fabricated_names"], len(legacy_fabricated))
            self.assertFalse(rt["lossless"], "audit artifact must record the legacy path as lossy")

    # ------------------------------------------------------------------ C6
    def test_c6_20_query_matched_id_invariance(self):
        """Matched IDs must be 100% unchanged across the 20-query corpus."""
        if not os.path.exists(GOLDEN_20_PATH):
            self.skipTest(f"golden corpus missing: {GOLDEN_20_PATH}")

        with open(GOLDEN_20_PATH, "r", encoding="utf-8") as f:
            golden = json.load(f)

        def simulate(query):
            tokens = query.lower().strip().split()
            if not tokens:
                return [r["mid"] for r in self.data]
            return [r["mid"] for r in self.data if all(t in searchable_text(r) for t in tokens)]

        drift = []
        for entry in golden:
            expected = entry["runtime"].get("tsMatchedIds") or []
            got = simulate(entry["query"])
            if sorted(expected) != sorted(got):
                drift.append((entry["query"], len(expected), len(got)))

        self.assertEqual(drift, [], f"matched-ID drift on {len(drift)} queries: {drift}")

        # The four anchor queries called out by the phase spec.
        anchors = {"RLCraft": 93, "Fabric API": 664, "Ice and Fire": 260, "JEI": 740}
        for q, expected in anchors.items():
            self.assertEqual(len(simulate(q)), expected, f"{q} must match exactly {expected}")

    # ------------------------------------------------------------------ C7
    def test_c7_exact_canonical_mod_name_equality(self):
        """Every mod name surfaced as a match reason must be an exact canonical name."""
        checked = 0
        offenders = []
        for q in REASON_QUERIES:
            for r in self.data:
                for name in match_reason_mod_names(r, q):
                    checked += 1
                    if name not in self.canonical_set:
                        offenders.append((q, r["mid"], name))

        self.assertGreater(checked, 0, "reason corpus produced no matches - query set is wrong")
        self.assertEqual(
            offenders[:20], [],
            f"{len(offenders)} match-reason names are not canonical (e.g. {offenders[:3]})",
        )

    # ------------------------------------------------------------------ C8
    def test_c8_rlmixins_negative(self):
        """'RLCraft' must not surface RLMixins as an included-mod reason."""
        pack = self.by_mid.get(RLMIXINS_PACK)
        self.assertIsNotNone(pack, f"fixture pack mcmod:{RLMIXINS_PACK} must exist")
        self.assertIn("RLMixins", pack["includedModNames"], "fixture pack must contain RLMixins")

        rlcraft_mods = [n for n in pack["includedModNames"] if "rlcraft" in n.lower()]
        self.assertTrue(rlcraft_mods, "fixture pack must also contain RLCraft-bearing mod names")

        hits = match_reason_mod_names(pack, "RLCraft")
        self.assertNotIn(
            "RLMixins", hits,
            "RLMixins does not contain 'rlcraft' and must never be reported as the reason",
        )
        self.assertEqual(
            sorted(hits), sorted(rlcraft_mods),
            "the RLCraft reason must list exactly the canonical RLCraft-bearing mod names",
        )
        for name in hits:
            self.assertIn(name, self.canonical_set, f"reason name is not canonical: {name!r}")

    # ------------------------------------------------------------------ C9
    def test_c9_multiword_cross_field_reason_not_merged(self):
        """Multi-word queries must not merge terms from different mods into a fake name."""
        cross_pack = None
        for r in self.data:
            names = r["includedModNames"]
            has_fabric_only = any("fabric" in n.lower() and "api" not in n.lower() for n in names)
            has_api_only = any("api" in n.lower() and "fabric" not in n.lower() for n in names)
            if has_fabric_only and has_api_only:
                cross_pack = r
                break

        self.assertIsNotNone(cross_pack, "expected at least one pack with cross-field Fabric/API hits")

        hits = match_reason_mod_names(cross_pack, "Fabric API")
        self.assertGreaterEqual(len(hits), 2, "cross-field query must report multiple distinct mods")

        for name in hits:
            self.assertIn(name, self.canonical_set, f"reason merged into non-canonical name: {name!r}")
            self.assertNotIn(
                ", ", name,
                f"reason must report real mod names, not delimiter-joined fragments: {name!r}",
            )

        # Terms are attributed per real mod, never merged into one synthetic entry.
        merged = [n for n, terms in hits.items() if terms == {"fabric", "api"}]
        for name in merged:
            self.assertIn(name.lower(), "fabric api", f"{name!r} claims both terms but is unrelated")


if __name__ == "__main__":
    unittest.main(verbosity=2)

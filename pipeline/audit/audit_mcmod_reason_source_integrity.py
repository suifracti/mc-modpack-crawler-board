"""
Phase 3G-D.1 - Match-Reason Structured Source Integrity Audit.

Verifies whether the current MCMod match-reason provenance is lossless:

    canonical included_mods (structured)
      -> exporter:  modSearchText = ", ".join(all_mod_names)
      -> frontend:  includedModNames = modSearchText.split(", ").map(trim).filter(Boolean)

The search hit-set may be correct while the UI's "包含模组：XXX" explanation is
wrong, if that flat-string round-trip is not injective.

This script is READ-ONLY. It never writes to canonical.db.

Usage:
    python pipeline/audit/audit_mcmod_reason_source_integrity.py \
        [--db build/canonical.db] \
        [--out build/audit/mcmod_modsearch_roundtrip_failures.json]
"""
import argparse
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

import sqlite3  # noqa: E402

DELIMITER = ", "

MODS_QUERY = """
    SELECT source_item_id, mod_name, mod_title, sort_order, id
    FROM included_mods
    WHERE source_item_id LIKE 'mcmod:%'
    ORDER BY source_item_id, sort_order, id
"""

PACKS_QUERY = """
    SELECT id FROM source_items WHERE id LIKE 'mcmod:%' ORDER BY id
"""


def serialize(names):
    """Mirror of structured_mcmod_exporter.py:301 -> `", ".join(all_mod_names)`."""
    return DELIMITER.join(names)


def parse(text):
    """Mirror of apps/web/src/search/searchDocument.ts:43-45.

    JS: item.modSearchText
          ? item.modSearchText.split(', ').map(s => s.trim()).filter(Boolean)
          : []
    """
    if not text:
        return []
    return [p for p in (s.strip() for s in text.split(DELIMITER)) if p]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.join(ROOT, "build", "canonical.db"))
    ap.add_argument("--out", default=os.path.join(ROOT, "build", "audit", "mcmod_modsearch_roundtrip_failures.json"))
    args = ap.parse_args()

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(MODS_QUERY).fetchall()
    pack_ids = [r["id"] for r in conn.execute(PACKS_QUERY).fetchall()]

    # ---------------------------------------------------------------- #
    # 1. Delimiter collision scan (full corpus, 170,078 relations)
    # ---------------------------------------------------------------- #
    total_relations = len(rows)
    names_with_delim = 0
    titles_with_delim = 0
    names_ws_edge = 0          # names whose trim() would change the string
    names_empty_or_blank = 0
    affected_mods = set()
    affected_packs_delim = set()
    collision_examples = []
    whitespace_examples = []

    for r in rows:
        name = r["mod_name"]
        title = r["mod_title"]

        if name is None:
            names_empty_or_blank += 1
            continue
        if name.strip() == "":
            names_empty_or_blank += 1
            continue

        if DELIMITER in name:
            names_with_delim += 1
            affected_mods.add(name)
            affected_packs_delim.add(r["source_item_id"])
            if len(collision_examples) < 50:
                collision_examples.append({
                    "source_item_id": r["source_item_id"],
                    "mod_name": name,
                })

        if title is not None and DELIMITER in title:
            titles_with_delim += 1

        if name != name.strip():
            names_ws_edge += 1
            if len(whitespace_examples) < 20:
                whitespace_examples.append({
                    "source_item_id": r["source_item_id"],
                    "mod_name": name,
                })

    # ---------------------------------------------------------------- #
    # 2. Per-pack round-trip audit (all MCMod packs, not just 953)
    # ---------------------------------------------------------------- #
    per_pack = {}
    for r in rows:
        per_pack.setdefault(r["source_item_id"], []).append(r["mod_name"])

    exact_packs = 0
    failed_packs = 0
    failed_relations = 0
    failures = []
    packs_with_mods = 0
    empty_packs = 0

    # Full-corpus fabrication metrics (not limited to the truncated samples below)
    real_names = {r["mod_name"] for r in rows if r["mod_name"]}
    fabricated_counter = Counter()
    packs_with_fabricated = set()
    fabricated_occurrences = 0

    for pid in pack_ids:
        pack_rows = per_pack.get(pid, [])
        original = [n for n in pack_rows if n]      # exporter: `if m.get("name")`
        if not pack_rows:
            empty_packs += 1
        else:
            packs_with_mods += 1

        text = serialize(original)
        parsed = parse(text)

        length_ok = len(original) == len(parsed)
        order_ok = length_ok and all(a == b for a, b in zip(original, parsed))
        exact_ok = length_ok and original == parsed

        for p in parsed:
            if p not in real_names:
                fabricated_counter[p] += 1
                fabricated_occurrences += 1
                packs_with_fabricated.add(pid)

        if exact_ok:
            exact_packs += 1
        else:
            failed_packs += 1
            if length_ok:
                bad = [i for i, (a, b) in enumerate(zip(original, parsed)) if a != b]
                failed_relations += len(bad)
            else:
                bad = []
                failed_relations += abs(len(original) - len(parsed)) or 1
            failures.append({
                "pack_id": pid,
                "same_length": length_ok,
                "same_order": order_ok,
                "same_exact_strings": exact_ok,
                "original_count": len(original),
                "parsed_count": len(parsed),
                "mismatched_indices": bad[:50],
                "original_sample": original[:20],
                "parsed_sample": parsed[:20],
            })

    # ---------------------------------------------------------------- #
    # 3. Duplicate-name sanity (duplicates are fine, but record them)
    # ---------------------------------------------------------------- #
    dup_packs = 0
    for pid in pack_ids:
        names = [n for n in per_pack.get(pid, []) if n]
        if len(names) != len(set(names)):
            dup_packs += 1

    # ---------------------------------------------------------------- #
    # 4. Real serialized payload size (from the exported artifact)
    # ---------------------------------------------------------------- #
    report = {
        "phase": "Architecture V2 - Phase 3G-D.1 Match-Reason Structured Source Integrity Gate",
        "db": os.path.relpath(args.db, ROOT).replace("\\", "/"),
        "serialization": {
            "site": "pipeline/exporters/structured_mcmod_exporter.py:301",
            "code": '"modSearchText": ", ".join(all_mod_names),',
            "source_field": "included_mods.mod_name (NOT mod_title)",
            "source_filter": '[m["name"] for m in pack_mods if m.get("name")]',
            "order": "ORDER BY source_item_id, sort_order, id",
        },
        "parser": {
            "site": "apps/web/src/search/searchDocument.ts:43-45",
            "code": "item.modSearchText ? item.modSearchText.split(', ').map(s => s.trim()).filter(Boolean) : []",
        },
        "delimiter": {
            "literal": DELIMITER,
            "codepoints": [ord(c) for c in DELIMITER],
            "escaping_rule": "NONE - names are concatenated verbatim",
        },
        "collision_scan": {
            "total_relations": total_relations,
            "names_containing_delimiter": names_with_delim,
            "titles_containing_delimiter": titles_with_delim,
            "distinct_affected_mods": len(affected_mods),
            "affected_packs": len(affected_packs_delim),
            "names_with_edge_whitespace": names_ws_edge,
            "names_empty_or_blank": names_empty_or_blank,
            "collision_examples": collision_examples,
            "whitespace_examples": whitespace_examples,
        },
        "roundtrip": {
            "packs_total": len(pack_ids),
            "packs_with_included_mods": packs_with_mods,
            "packs_without_included_mods": empty_packs,
            "packs_with_duplicate_names": dup_packs,
            "exact_roundtrip_packs": exact_packs,
            "failed_roundtrip_packs": failed_packs,
            "failed_relation_count": failed_relations,
            "packs_with_fabricated_names": len(packs_with_fabricated),
            "distinct_fabricated_names": len(fabricated_counter),
            "fabricated_name_occurrences": fabricated_occurrences,
            "fabricated_name_top": [
                {"name": n, "packs": k} for n, k in fabricated_counter.most_common(30)
            ],
            "lossless": failed_packs == 0,
        },
        "failures": failures,
    }

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    cs = report["collision_scan"]
    rt = report["roundtrip"]
    print("=" * 74)
    print("  Phase 3G-D.1 - Match-Reason Structured Source Integrity Audit")
    print("=" * 74)
    print(f"  delimiter                     : {DELIMITER!r} (codepoints {[ord(c) for c in DELIMITER]})")
    print(f"  escaping rule                 : NONE")
    print()
    print(f"  total relations               : {cs['total_relations']}")
    print(f"  names containing delimiter    : {cs['names_containing_delimiter']}")
    print(f"  titles containing delimiter   : {cs['titles_containing_delimiter']}")
    print(f"  distinct affected mods        : {cs['distinct_affected_mods']}")
    print(f"  affected packs                : {cs['affected_packs']}")
    print(f"  names w/ edge whitespace      : {cs['names_with_edge_whitespace']}")
    print(f"  names empty/blank             : {cs['names_empty_or_blank']}")
    print()
    print(f"  packs total                   : {rt['packs_total']}")
    print(f"  packs with included mods      : {rt['packs_with_included_mods']}")
    print(f"  packs without included mods   : {rt['packs_without_included_mods']}")
    print(f"  packs w/ duplicate names      : {rt['packs_with_duplicate_names']}")
    print(f"  exact round-trip packs        : {rt['exact_roundtrip_packs']}")
    print(f"  failed round-trip packs       : {rt['failed_roundtrip_packs']}")
    print(f"  failed relation count         : {rt['failed_relation_count']}")
    print(f"  packs w/ fabricated names     : {rt['packs_with_fabricated_names']}")
    print(f"  distinct fabricated names     : {rt['distinct_fabricated_names']}")
    print(f"  fabricated name occurrences   : {rt['fabricated_name_occurrences']}")
    print(f"  LOSSLESS                      : {rt['lossless']}")
    print("=" * 74)
    print(f"  artifact -> {os.path.relpath(args.out, ROOT).replace(chr(92), '/')}")

    conn.close()
    return 0 if rt["lossless"] else 2


if __name__ == "__main__":
    sys.exit(main())

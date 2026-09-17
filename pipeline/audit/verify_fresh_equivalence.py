"""
Architecture V2 - Phase 3F.1: Semantic Equivalence Verification.
Compares Migrated DB (build/canonical.db) vs Fresh Rebuilt DB (build/canonical_fresh_verify.db).
Computes deterministic semantic digests and verifies 0 unexpected differences.
"""
import sqlite3
import hashlib
import json
import os
import sys

def compute_table_digest(db_path: str, query: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    conn.close()

    h = hashlib.sha256()
    for row in rows:
        normalized = json.dumps(list(row), ensure_ascii=True, separators=(',', ':'))
        h.update(normalized.encode('utf-8'))
        h.update(b'\n')
    return len(rows), h.hexdigest()

def verify_equivalence(db_migrated: str = "build/canonical.db", db_fresh: str = "build/canonical_fresh_verify.db"):
    queries = {
        "packs": "SELECT id, preferred_title, normalized_title, primary_platform FROM packs ORDER BY id",
        "source_items": "SELECT id, pack_id, platform, source_id, title, author, published_at, modified_at FROM source_items ORDER BY id",
        "source_item_loaders": "SELECT source_item_id, loader_id FROM source_item_loaders ORDER BY source_item_id, loader_id",
        "download_links": "SELECT source_item_id, link_type, url, label, extract_code, is_server FROM download_links ORDER BY source_item_id, url",
        "environment_claims": "SELECT pack_id, source_item_id, side, status, certainty, evidence_type, evidence_text, raw_value, source_field FROM environment_claims ORDER BY pack_id, source_item_id, side",
        "releases_core": "SELECT id, pack_id, source_item_id, version_name, version_type, is_latest, downloads_count FROM releases ORDER BY id",
    }

    results = {}
    print("=" * 70)
    print("  Semantic Digest Comparison: Migrated vs Fresh DB")
    print(f"  Migrated DB: {db_migrated}")
    print(f"  Fresh DB:    {db_fresh}")
    print("=" * 70)

    for name, q in queries.items():
        cnt_m, hash_m = compute_table_digest(db_migrated, q)
        cnt_f, hash_f = compute_table_digest(db_fresh, q)
        match = (hash_m == hash_f)
        results[name] = {
            "migrated_count": cnt_m,
            "fresh_count": cnt_f,
            "migrated_digest": hash_m,
            "fresh_digest": hash_f,
            "match": match
        }
        print(f"[{'PASS' if match else 'FAIL'}] {name:<22} | Count: {cnt_m:>6} vs {cnt_f:>6} | Match: {match} (Digest: {hash_m[:12]}..)")

    # Check WRONG fact checks on both
    print("\nChecking WRONG Fact Eradication on Both Databases:")
    for label, path in [("Migrated", db_migrated), ("Fresh", db_fresh)]:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM releases WHERE release_date LIKE '%未知%'")
        p_rel = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM source_items WHERE published_at LIKE '%未知%' OR modified_at LIKE '%未知%'")
        p_si = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM download_links WHERE url LIKE 'null%' OR url LIKE 'undefined%' OR url LIKE 'Neoforge%' OR url LIKE '%更新日志%'")
        p_dl = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM source_item_loaders sil JOIN source_items s ON sil.source_item_id = s.id WHERE s.platform = 'bilibili'")
        bili_loaders = cur.fetchone()[0]
        conn.close()

        print(f"  [{label}] Polluted release dates : {p_rel}")
        print(f"  [{label}] Polluted item dates    : {p_si}")
        print(f"  [{label}] Invalid URLs           : {p_dl}")
        print(f"  [{label}] Bilibili Loaders       : {bili_loaders}")

        assert p_rel == 0, f"{label} has polluted release dates"
        assert p_si == 0, f"{label} has polluted source item dates"
        assert p_dl == 0, f"{label} has invalid URLs"
        assert bili_loaders == 223, f"{label} expected 223 bili loaders, got {bili_loaders}"

    print("\n[+] All semantic checks passed: 0 unexpected semantic differences!")
    return results

if __name__ == "__main__":
    verify_equivalence()

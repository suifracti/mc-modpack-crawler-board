"""
Architecture V2 - Phase 3F.2: Semantic Equivalence Verification (Release-Date Gate).

Compares Migrated DB (build/canonical.db) vs Fresh Rebuilt DB
(build/canonical_fresh_verify.db) and verifies 0 unexpected semantic differences.

Phase 3F.2 adds the `releases_full` digest, which - unlike the Phase 3F.1
`releases_core` digest - actually includes `release_date` (plus `version_type`),
so a release-date divergence can no longer hide behind a passing gate.
"""
import sqlite3
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# NOTE: releases_full is the authoritative release digest as of Phase 3F.2.
# releases_core is retained for continuity with the Phase 3F.1 gate.
QUERIES = {
    "packs": "SELECT id, preferred_title, normalized_title, primary_platform FROM packs ORDER BY id",
    "source_items": "SELECT id, pack_id, platform, source_id, title, author, published_at, modified_at FROM source_items ORDER BY id",
    "source_item_loaders": "SELECT source_item_id, loader_id FROM source_item_loaders ORDER BY source_item_id, loader_id",
    "download_links": "SELECT source_item_id, link_type, url, label, extract_code, is_server FROM download_links ORDER BY source_item_id, url",
    "environment_claims": "SELECT pack_id, source_item_id, side, status, certainty, evidence_type, evidence_text, raw_value, source_field FROM environment_claims ORDER BY pack_id, source_item_id, side",
    "releases_core": "SELECT id, pack_id, source_item_id, version_name, version_type, is_latest, downloads_count FROM releases ORDER BY id",
    "releases_full": "SELECT id, pack_id, source_item_id, version_name, version_type, release_date, is_latest, downloads_count FROM releases ORDER BY id",
}

RELEASE_DATE_QUERY = """
SELECT r.id,
       r.release_date,
       s.platform,
       s.source_id,
       s.published_at,
       s.modified_at,
       r.version_name
FROM releases r
LEFT JOIN source_items s ON r.source_item_id = s.id
ORDER BY r.id
"""


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


def release_date_report(db_migrated: str, db_fresh: str):
    """Per-row release_date comparison with the 3 difference categories."""
    def load(p):
        conn = sqlite3.connect(p)
        try:
            return {r[0]: r for r in conn.execute(RELEASE_DATE_QUERY)}
        finally:
            conn.close()

    migrated = load(db_migrated)
    fresh = load(db_fresh)

    stats = {
        "total_release_rows": len(migrated),
        "same_release_date_rows": 0,
        "different_release_date_rows": 0,
        "migrated_null_fresh_nonnull": 0,
        "migrated_nonnull_fresh_null": 0,
        "both_nonnull_but_different": 0,
    }
    samples = []

    for rid in sorted(migrated):
        m_date = migrated[rid][1]
        f_date = fresh[rid][1]
        if m_date == f_date:
            stats["same_release_date_rows"] += 1
            continue

        stats["different_release_date_rows"] += 1
        if m_date is None:
            stats["migrated_null_fresh_nonnull"] += 1
        elif f_date is None:
            stats["migrated_nonnull_fresh_null"] += 1
        else:
            stats["both_nonnull_but_different"] += 1

        if len(samples) < 10:
            samples.append({
                "release_id": rid,
                "platform": migrated[rid][2],
                "migrated_release_date": m_date,
                "fresh_release_date": f_date,
            })

    return stats, samples


def verify_equivalence(db_migrated: str = None, db_fresh: str = None):
    db_migrated = db_migrated or os.path.join(ROOT, "build", "canonical.db")
    db_fresh = db_fresh or os.path.join(ROOT, "build", "canonical_fresh_verify.db")

    results = {}
    print("=" * 78)
    print("  Semantic Digest Comparison: Migrated vs Fresh DB (Phase 3F.2)")
    print(f"  Migrated DB: {os.path.relpath(db_migrated, ROOT)}")
    print(f"  Fresh DB:    {os.path.relpath(db_fresh, ROOT)}")
    print("=" * 78)

    for name, q in QUERIES.items():
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
        tag = "MATCH" if match else "DIFFER"
        print(f"[{tag}] {name:<22} | Count: {cnt_m:>6} vs {cnt_f:>6} | {hash_m[:16]}.. vs {hash_f[:16]}..")

    # ---------------------------------------------------------- release_date
    print("\n--- release_date row-level equivalence ---")
    stats, samples = release_date_report(db_migrated, db_fresh)
    for k in ("total_release_rows", "same_release_date_rows", "different_release_date_rows",
              "migrated_null_fresh_nonnull", "migrated_nonnull_fresh_null",
              "both_nonnull_but_different"):
        print(f"  {k:<34}: {stats[k]}")
    if samples:
        print("  first differences:")
        for s in samples:
            print(f"    {s}")

    # ---------------------------------------------- WRONG fact eradication
    print("\n--- WRONG fact eradication on both databases ---")
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
        cur.execute("""
            SELECT COUNT(*) FROM releases
            WHERE release_date IS NOT NULL AND release_date NOT LIKE '19%' AND release_date NOT LIKE '20%'
        """)
        junk = cur.fetchone()[0]
        cur.execute("""
            SELECT COUNT(*) FROM releases
            WHERE (id LIKE 'xyebbs:%:rel:latest' OR id LIKE 'bbsmc:%:rel:latest')
              AND release_date IS NOT NULL
        """)
        forum_fabricated = cur.fetchone()[0]
        cur.execute("""
            SELECT COUNT(*) FROM releases r JOIN source_items s ON r.source_item_id = s.id
            WHERE s.platform = 'bilibili' AND r.release_date IS NOT NULL
        """)
        bili_rel_date = cur.fetchone()[0]
        conn.close()

        print(f"  [{label}] Polluted release dates        : {p_rel}")
        print(f"  [{label}] Polluted item dates           : {p_si}")
        print(f"  [{label}] Invalid URLs                  : {p_dl}")
        print(f"  [{label}] Bilibili Loaders              : {bili_loaders}")
        print(f"  [{label}] Non-timestamp release_date    : {junk}")
        print(f"  [{label}] Forum-aggregate fabricated    : {forum_fabricated}")
        print(f"  [{label}] Bilibili release_date non-NULL: {bili_rel_date}")

        assert p_rel == 0, f"{label} has polluted release dates"
        assert p_si == 0, f"{label} has polluted source item dates"
        assert p_dl == 0, f"{label} has invalid URLs"
        assert bili_loaders == 223, f"{label} expected 223 bili loaders, got {bili_loaders}"
        assert junk == 0, f"{label} has non-timestamp release_date values"
        assert forum_fabricated == 0, f"{label} still fabricates release_date from forum post time"
        assert bili_rel_date == 0, f"{label} has Bilibili release_date values (must be NULL)"

    # ------------------------------------------------------------- verdict
    print("\n" + "=" * 78)
    digest_ok = results["releases_full"]["match"]
    date_ok = stats["different_release_date_rows"] == 0
    print(f"  releases_full semantic digest = {'MATCH' if digest_ok else 'DIFFER'}")
    print(f"  release_date differing rows   = {stats['different_release_date_rows']}")
    print(f"  releases_core semantic digest = {'MATCH' if results['releases_core']['match'] else 'DIFFER'}")
    all_match = all(v["match"] for v in results.values())
    print(f"  unexpected semantic differences = {0 if (all_match and date_ok) else 'NON-ZERO'}")
    print("=" * 78)

    assert digest_ok, "releases_full digest mismatch (release_date semantics diverge)"
    assert date_ok, "release_date differs between migrated and fresh DB"
    assert all_match, "some semantic digest does not match"
    print("[+] 0 unexpected semantic differences. Phase 3F.2 gate PASSED.")
    return results


if __name__ == "__main__":
    verify_equivalence()

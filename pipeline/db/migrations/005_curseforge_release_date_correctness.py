"""
Migration 005: CurseForge Release-Date Correctness Remediation (Architecture V2 - Phase 3G-B).

Purpose:
Remediates TIME-CURSEFORGE-02 (proven WRONG fact) in canonical SQLite database:
CurseForge raw crawler snapshot does NOT contain `latestFiles[].fileDate` or any other
file/release-scoped publication timestamp.
Under the strict Canonical Rule:
    release_date = the release/version-scoped publication timestamp published by
                   the source platform for that release/version.
    Project-level metadata (dateModified, dateReleased, dateCreated) CANNOT masquerade
    as a release date.
    No file/release-scoped evidence -> release_date = NULL.

Target:
CurseForge synthetic release rows (`curseforge:<pid>:rel:latest`).
All 45,797 rows have their release_date set to NULL.

Guards & Invariants:
1. Export all 45,797 targets to build/audit/curseforge_release_date_migration_targets.json before update.
2. Invariants preserved:
   - packs count = 73,522 (unchanged)
   - source_items count = 73,522 (unchanged)
   - releases count = 73,533 (unchanged)
3. CurseForge source_items.published_at and modified_at remain 100% untouched.
   Deterministic digest (id, published_at, modified_at) before == after.
4. Non-CurseForge releases (Modrinth, MCMod, BBSMC, XYEBBS, Bilibili) remain 100% untouched.
"""
import hashlib
import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

DEFAULT_DB = os.path.join(ROOT, "build", "canonical.db")
TARGETS_EXPORT_PATH = os.path.join(ROOT, "build", "audit", "curseforge_release_date_migration_targets.json")

EXPECTED_PACKS = 73522
EXPECTED_SOURCE_ITEMS = 73522
EXPECTED_RELEASES = 73533
EXPECTED_CURSEFORGE_RELEASES = 45797


def compute_curseforge_source_items_digest(cur: sqlite3.Cursor) -> str:
    cur.execute("""
        SELECT id, published_at, modified_at
        FROM source_items
        WHERE platform = 'curseforge'
        ORDER BY id
    """)
    rows = cur.fetchall()
    h = hashlib.sha256()
    for r in rows:
        normalized = json.dumps(list(r), ensure_ascii=True, separators=(',', ':'))
        h.update(normalized.encode('utf-8'))
        h.update(b'\n')
    return h.hexdigest()


def run_migration(db_path: str = DEFAULT_DB):
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    try:
        # 1. Pre-check invariants
        cur.execute("SELECT COUNT(*) FROM packs")
        initial_packs = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM source_items")
        initial_source_items = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM releases")
        initial_releases = cur.fetchone()[0]

        print(f"[*] Initial status: packs={initial_packs}, source_items={initial_source_items}, releases={initial_releases}")
        assert initial_packs == EXPECTED_PACKS, f"Expected {EXPECTED_PACKS} packs, got {initial_packs}"
        assert initial_source_items == EXPECTED_SOURCE_ITEMS, f"Expected {EXPECTED_SOURCE_ITEMS} source_items, got {initial_source_items}"
        assert initial_releases == EXPECTED_RELEASES, f"Expected {EXPECTED_RELEASES} releases, got {initial_releases}"

        # 2. Check CurseForge release counts before
        cur.execute("""
            SELECT COUNT(r.id),
                   SUM(CASE WHEN r.release_date IS NOT NULL THEN 1 ELSE 0 END),
                   SUM(CASE WHEN r.release_date IS NULL THEN 1 ELSE 0 END)
            FROM releases r
            JOIN source_items s ON r.source_item_id = s.id
            WHERE s.platform = 'curseforge'
        """)
        cf_total_before, cf_non_null_before, cf_null_before = cur.fetchone()
        print(f"[*] CurseForge releases before: total={cf_total_before}, non-null={cf_non_null_before}, null={cf_null_before}")
        assert cf_total_before == EXPECTED_CURSEFORGE_RELEASES, f"Expected {EXPECTED_CURSEFORGE_RELEASES} CurseForge releases, got {cf_total_before}"

        # 3. Compute source items digest before
        digest_before = compute_curseforge_source_items_digest(cur)
        print(f"[*] CurseForge source items digest before: {digest_before}")

        # 4. Export targets before updating
        print(f"[*] Exporting migration targets to {TARGETS_EXPORT_PATH}...")
        cur.execute("""
            SELECT r.id, r.source_item_id, r.release_date, s.published_at, s.modified_at
            FROM releases r
            JOIN source_items s ON r.source_item_id = s.id
            WHERE s.platform = 'curseforge'
            ORDER BY r.id
        """)
        targets = []
        for r_id, si_id, old_rd, pub_at, mod_at in cur.fetchall():
            targets.append({
                "release_id": r_id,
                "source_item_id": si_id,
                "old_release_date": old_rd,
                "source_published_at": pub_at,
                "source_modified_at": mod_at
            })

        os.makedirs(os.path.dirname(TARGETS_EXPORT_PATH), exist_ok=True)
        with open(TARGETS_EXPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(targets, f, indent=2, ensure_ascii=False)
        print(f"    Exported {len(targets)} targets successfully.")

        # 5. Snapshot non-CurseForge releases digest to ensure 0 unexpected changes
        cur.execute("""
            SELECT r.id, r.release_date
            FROM releases r
            JOIN source_items s ON r.source_item_id = s.id
            WHERE s.platform != 'curseforge'
            ORDER BY r.id
        """)
        non_cf_before = cur.fetchall()

        # 6. Execute update: set CurseForge release_date to NULL
        print("\n[*] Executing Migration 005: updating CurseForge release_date to NULL...")
        cur.execute("""
            UPDATE releases
            SET release_date = NULL
            WHERE id IN (
                SELECT r.id
                FROM releases r
                JOIN source_items s ON r.source_item_id = s.id
                WHERE s.platform = 'curseforge'
            )
        """)
        updated_rows = cur.rowcount
        print(f"    Updated rows: {updated_rows}")
        assert updated_rows == cf_non_null_before, f"Expected {cf_non_null_before} rows updated, got {updated_rows}"

        # 7. Verify CurseForge release counts after
        cur.execute("""
            SELECT COUNT(r.id),
                   SUM(CASE WHEN r.release_date IS NOT NULL THEN 1 ELSE 0 END),
                   SUM(CASE WHEN r.release_date IS NULL THEN 1 ELSE 0 END)
            FROM releases r
            JOIN source_items s ON r.source_item_id = s.id
            WHERE s.platform = 'curseforge'
        """)
        cf_total_after, cf_non_null_after, cf_null_after = cur.fetchone()
        print(f"[*] CurseForge releases after: total={cf_total_after}, non-null={cf_non_null_after or 0}, null={cf_null_after}")
        assert cf_total_after == EXPECTED_CURSEFORGE_RELEASES, f"Total CurseForge releases changed: {cf_total_after}"
        assert (cf_non_null_after or 0) == 0, f"Expected 0 non-null CurseForge releases, got {cf_non_null_after}"
        assert cf_null_after == EXPECTED_CURSEFORGE_RELEASES, f"Expected {EXPECTED_CURSEFORGE_RELEASES} null CurseForge releases, got {cf_null_after}"

        # 8. Verify non-CurseForge releases are 100% untouched
        cur.execute("""
            SELECT r.id, r.release_date
            FROM releases r
            JOIN source_items s ON r.source_item_id = s.id
            WHERE s.platform != 'curseforge'
            ORDER BY r.id
        """)
        non_cf_after = cur.fetchall()
        assert non_cf_before == non_cf_after, "Non-CurseForge releases were unexpectedly modified!"
        print("[+] Verified non-CurseForge releases: 100% identical (0 unexpected changes).")

        # 9. Verify source items digest after
        digest_after = compute_curseforge_source_items_digest(cur)
        print(f"[*] CurseForge source items digest after:  {digest_after}")
        assert digest_before == digest_after, f"Source items dates were modified! {digest_before} != {digest_after}"
        print("[+] Verified CurseForge source_items dates: 100% identical (digest MATCH).")

        # 10. Verify global table invariants
        cur.execute("SELECT COUNT(*) FROM packs")
        final_packs = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM source_items")
        final_source_items = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM releases")
        final_releases = cur.fetchone()[0]

        assert final_packs == initial_packs == EXPECTED_PACKS, f"Pack count invariant violated: {final_packs}"
        assert final_source_items == initial_source_items == EXPECTED_SOURCE_ITEMS, f"SourceItem count invariant violated: {final_source_items}"
        assert final_releases == initial_releases == EXPECTED_RELEASES, f"Release count invariant violated: {final_releases}"
        print(f"[+] All invariants verified: packs={final_packs}, source_items={final_source_items}, releases={final_releases}")

        conn.commit()
        print("[+] Migration 005 committed successfully.")

        return {
            "cf_total_before": cf_total_before,
            "cf_non_null_before": cf_non_null_before,
            "cf_null_before": cf_null_before,
            "updated_rows": updated_rows,
            "cf_total_after": cf_total_after,
            "cf_non_null_after": cf_non_null_after or 0,
            "cf_null_after": cf_null_after,
            "unexpected_changed_rows": 0,
            "digest_before": digest_before,
            "digest_after": digest_after,
        }

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


if __name__ == "__main__":
    db = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB
    print(f"Running Migration 005 on {db}...")
    stats = run_migration(db)
    print("\nMigration 005 Summary:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

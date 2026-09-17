"""
Migration 004: Release-Date Semantic Equivalence (Architecture V2 - Phase 3F.2).

Purpose
-------
Enforce the single canonical `release_date` rule on the MIGRATED database so that
`Migration Path == Fresh Build Path` produces byte-identical canonical facts.

Canonical rule (derived from factual semantics, not from field-completeness):
    release_date = the release/version-scoped publication timestamp published by
                   the source platform for that release/version.
    NOT allowed  : crawler observed time, forum post/edit time, video publish time,
                   project-level publication/update metadata.
    No release-scoped evidence  ->  NULL. No fallback for field completeness.

What this migration changes
---------------------------
R1. xyebbs synthetic aggregate rows (`<si>:rel:latest`): the value previously stored
    was the XYEBBS forum thread's `date_created`/`date_modified` (forum post/edit
    time), which is NOT a release date -> NULL.
R2. bbsmc synthetic aggregate rows (`<si>:rel:latest`): same reasoning
    (BBSMC forum thread post/edit time) -> NULL.
R3. bbsmc real version rows: the adapter previously read the non-existent fields
    `date_created` / `release_date` on BBSMC version objects and silently fell back
    to the forum post time. The genuine, version-scoped, structured field is
    `date_published` (ISO-8601 UTC). This migration backfills those rows from the
    same raw snapshot the adapter consumes, so both paths agree.

Explicitly NOT touched (Phase 3F.2 scope guard):
    published_at, modified_at, observed_at, last_observed_update_at,
    pinned_comment_at, update_notice_at, and every other platform's release_date.

Invariants preserved: packs, source_items, releases row counts are unchanged.
"""
import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Single source of truth: the migration MUST reuse the adapter's sanitizer so that
# Migration Path and Fresh Build Path can never drift apart again.
from pipeline.adapters.bbsmc import clean_date_str  # noqa: E402

BBSMC_RAW = os.path.join(ROOT, "crawler_output", "bbsmc_modpacks.json")

EXPECTED_PACKS = 73522
EXPECTED_SOURCE_ITEMS = 73522
EXPECTED_RELEASES = 73533


def _load_bbsmc_version_published():
    """(project_id, version_id) -> date_published, straight from the raw snapshot."""
    with open(BBSMC_RAW, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    items = data if isinstance(data, list) else data.get("items") or []
    mapping = {}
    for item in items:
        pid = str(item.get("project_id"))
        for v in item.get("versions_data") or []:
            dp = clean_date_str(v.get("date_published"))
            if pid and v.get("id") and dp:
                mapping[(pid, str(v["id"]))] = dp
    return mapping


def run_migration(db_path: str):
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    try:
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

        # ---------------------------------------------------------------- R1
        print("\n[R1] XYEBBS synthetic aggregate rows: forum post time is NOT release_date -> NULL")
        cur.execute("""
            UPDATE releases
            SET release_date = NULL
            WHERE id LIKE 'xyebbs:%:rel:latest'
              AND release_date IS NOT NULL
        """)
        r1 = cur.rowcount
        print(f"     -> {r1} rows set to NULL")

        # ---------------------------------------------------------------- R2
        print("\n[R2] BBSMC synthetic aggregate rows: forum post time is NOT release_date -> NULL")
        cur.execute("""
            UPDATE releases
            SET release_date = NULL
            WHERE id LIKE 'bbsmc:%:rel:latest'
              AND release_date IS NOT NULL
        """)
        r2 = cur.rowcount
        print(f"     -> {r2} rows set to NULL")

        # ---------------------------------------------------------------- R3
        print("\n[R3] BBSMC real version rows: restore structured version-scoped `date_published`")
        published = _load_bbsmc_version_published()
        cur.execute("""
            SELECT r.id, s.source_id
            FROM releases r
            JOIN source_items s ON r.source_item_id = s.id
            WHERE s.platform = 'bbsmc' AND r.id NOT LIKE '%:rel:latest'
        """)
        backfills = []
        missing = []
        for release_id, project_id in cur.fetchall():
            version_id = release_id.rsplit(":rel:", 1)[-1]
            dp = published.get((str(project_id), version_id))
            if dp:
                backfills.append((dp, release_id))
            else:
                missing.append(release_id)
        if missing:
            print(f"     [!] {len(missing)} BBSMC version rows have no `date_published` evidence -> left NULL")
        if backfills:
            cur.executemany("UPDATE releases SET release_date = ? WHERE id = ?", backfills)
        r3 = len(backfills)
        print(f"     -> {r3} rows backfilled from raw version `date_published`")

        # ------------------------------------------------------- Invariants
        print("\n[V] Verifying invariants...")
        cur.execute("SELECT COUNT(*) FROM packs")
        final_packs = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM source_items")
        final_source_items = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM releases")
        final_releases = cur.fetchone()[0]

        assert final_packs == initial_packs == EXPECTED_PACKS, f"Pack count invariant violated: {final_packs}"
        assert final_source_items == initial_source_items == EXPECTED_SOURCE_ITEMS, f"SourceItem count invariant violated: {final_source_items}"
        assert final_releases == initial_releases == EXPECTED_RELEASES, f"Release count invariant violated: {final_releases}"

        # No BBSMC/XYEBBS synthetic row may carry a fabricated release_date any more.
        cur.execute("""
            SELECT COUNT(*) FROM releases
            WHERE (id LIKE 'xyebbs:%:rel:latest' OR id LIKE 'bbsmc:%:rel:latest')
              AND release_date IS NOT NULL
        """)
        residual = cur.fetchone()[0]
        assert residual == 0, f"{residual} synthetic forum aggregate rows still carry a release_date"

        # No non-timestamp junk may exist.
        cur.execute("""
            SELECT COUNT(*) FROM releases
            WHERE release_date IS NOT NULL AND release_date NOT LIKE '19%' AND release_date NOT LIKE '20%'
        """)
        junk = cur.fetchone()[0]
        assert junk == 0, f"{junk} release_date values are not ISO-like timestamps"

        conn.commit()
        print(f"\n>>> MIGRATION 004 APPLIED SUCCESSFULLY: {r1 + r2 + r3} rows changed (R1={r1}, R2={r2}, R3={r3}) <<<")
        return {"R1_xyebbs_null": r1, "R2_bbsmc_null": r2, "R3_bbsmc_backfill": r3, "total": r1 + r2 + r3}

    except Exception as e:
        conn.rollback()
        print(f"\n[!] Migration 004 failed, transaction rolled back: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    db = os.path.join(ROOT, "build", "canonical.db")
    run_migration(db)

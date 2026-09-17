"""
Architecture V2 - Canonical SQLite Ingestion Pipeline (Phase 1).
Builds build/canonical.db from raw JSON snapshots in crawler_output/.
Strictly preserves crawler files and existing dashboard contracts.
"""
import argparse
from datetime import datetime, timezone
import os
import sys
import time
from typing import Dict, Tuple, List, Any

# Ensure project root is on PYTHONPATH
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from pipeline.db import get_connection, init_db, DEFAULT_DB_PATH
from pipeline.adapters import (
    BaseAdapter,
    MCModAdapter,
    BilibiliAdapter,
    BbsmcAdapter,
    XyebbsAdapter,
    ModrinthAdapter,
    CurseForgeAdapter,
)
from pipeline.models.canonical import CanonicalPackBundle


def build_canonical_db(db_path: str = DEFAULT_DB_PATH, recreate: bool = True) -> Dict[str, Any]:
    start_time = time.time()
    print(f"[*] Starting Canonical DB Ingestion -> {db_path}")

    if recreate and os.path.exists(db_path):
        print(f"[-] Removing existing database: {db_path}")
        try:
            os.remove(db_path)
            wal_file = f"{db_path}-wal"
            shm_file = f"{db_path}-shm"
            if os.path.exists(wal_file):
                os.remove(wal_file)
            if os.path.exists(shm_file):
                os.remove(shm_file)
        except OSError as e:
            print(f"[!] Warning removing old db files: {e}")

    conn = get_connection(db_path)
    # Speed up bulk ingestion while keeping integrity
    conn.execute("PRAGMA cache_size = -64000;")  # 64MB cache
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA temp_store = MEMORY;")

    init_db(conn)
    print("[+] Database schema initialized successfully.")

    run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    started_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO ingest_runs (run_id, started_at, status, notes) VALUES (?, ?, ?, ?)",
        (run_id, started_at, "running", "Phase 1 Canonical SQLite Ingestion"),
    )
    conn.commit()

    # Pre-seed loaders
    standard_loaders = ["Fabric", "Forge", "NeoForge", "Quilt"]
    for ldr in standard_loaders:
        conn.execute("INSERT OR IGNORE INTO loaders (name) VALUES (?)", (ldr,))
    conn.commit()

    cur = conn.execute("SELECT id, name FROM loaders")
    loaders_cache: Dict[str, int] = {row["name"].lower(): row["id"] for row in cur.fetchall()}

    # Category cache: (platform, name) -> category_id
    categories_cache: Dict[Tuple[str, str], int] = {}
    cur = conn.execute("SELECT id, platform, name FROM categories")
    for row in cur.fetchall():
        categories_cache[(row["platform"], row["name"])] = row["id"]

    def get_or_create_category(platform: str, name: str) -> int:
        clean_name = name.strip()
        key = (platform, clean_name)
        if key in categories_cache:
            return categories_cache[key]
        conn.execute("INSERT OR IGNORE INTO categories (platform, name) VALUES (?, ?)", (platform, clean_name))
        cat_cur = conn.execute("SELECT id FROM categories WHERE platform = ? AND name = ?", (platform, clean_name))
        cat_id = cat_cur.fetchone()[0]
        categories_cache[key] = cat_id
        return cat_id

    adapters: List[BaseAdapter] = [
        MCModAdapter(workspace_root=PROJECT_ROOT),
        BilibiliAdapter(workspace_root=PROJECT_ROOT),
        BbsmcAdapter(workspace_root=PROJECT_ROOT),
        XyebbsAdapter(workspace_root=PROJECT_ROOT),
        ModrinthAdapter(workspace_root=PROJECT_ROOT),
        CurseForgeAdapter(workspace_root=PROJECT_ROOT),
    ]

    total_records = 0

    for adapter in adapters:
        plat_start = time.time()
        p_name = adapter.platform_name
        file_path, file_size, content_hash, rec_count = adapter.get_snapshot_provenance()
        print(f"\n[>] Ingesting platform [{p_name.upper()}]: {rec_count} records ({file_size / 1024 / 1024:.2f} MB)")

        # Record snapshot ref
        now_dt = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            """
            INSERT INTO raw_snapshot_refs 
            (run_id, platform, file_path, file_size_bytes, content_hash, record_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, p_name, file_path, file_size, content_hash, rec_count, now_dt),
        )
        conn.commit()

        # Batch accumulator buffers
        BATCH_SIZE = 5000
        packs_rows = []
        sources_rows = []
        aliases_rows = []
        releases_rows = []
        rel_mc_rows = []
        si_loaders_rows = []
        si_cats_rows = []
        dl_rows = []
        rv_rows = []
        metrics_rows = []
        claims_rows = []

        def flush_batch():
            nonlocal packs_rows, sources_rows, aliases_rows, releases_rows, rel_mc_rows
            nonlocal si_loaders_rows, si_cats_rows, dl_rows, rv_rows, metrics_rows, claims_rows
            if not packs_rows:
                return

            with conn:
                conn.executemany(
                    """
                    INSERT OR REPLACE INTO packs 
                    (id, preferred_title, normalized_title, summary, primary_platform, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    packs_rows,
                )
                conn.executemany(
                    """
                    INSERT OR REPLACE INTO source_items 
                    (id, pack_id, platform, source_id, slug, source_url, title, author, description, 
                     icon_url, published_at, modified_at, raw_ref, extra_json, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    sources_rows,
                )
                if aliases_rows:
                    conn.executemany(
                        """
                        INSERT OR IGNORE INTO aliases 
                        (pack_id, alias_type, alias_text, source, created_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        aliases_rows,
                    )
                if releases_rows:
                    conn.executemany(
                        """
                        INSERT OR REPLACE INTO releases 
                        (id, pack_id, source_item_id, version_name, version_type, release_date, 
                         is_latest, changelog, downloads_count, extra_json, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        releases_rows,
                    )
                if rel_mc_rows:
                    conn.executemany(
                        """
                        INSERT OR IGNORE INTO release_mc_versions 
                        (release_id, mc_version, is_primary)
                        VALUES (?, ?, ?)
                        """,
                        rel_mc_rows,
                    )
                if si_loaders_rows:
                    conn.executemany(
                        """
                        INSERT OR IGNORE INTO source_item_loaders 
                        (source_item_id, loader_id)
                        VALUES (?, ?)
                        """,
                        si_loaders_rows,
                    )
                if si_cats_rows:
                    conn.executemany(
                        """
                        INSERT OR IGNORE INTO source_item_categories 
                        (source_item_id, category_id)
                        VALUES (?, ?)
                        """,
                        si_cats_rows,
                    )
                if dl_rows:
                    conn.executemany(
                        """
                        INSERT INTO download_links 
                        (source_item_id, release_id, link_type, url, label, extract_code, is_server, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        dl_rows,
                    )
                if rv_rows:
                    conn.executemany(
                        """
                        INSERT INTO related_videos 
                        (source_item_id, bvid, aid, title, author, url, published_at, views, danmaku, likes, coins, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        rv_rows,
                    )
                if metrics_rows:
                    conn.executemany(
                        """
                        INSERT INTO metrics 
                        (source_item_id, views, downloads, followers, likes, coins, favorites, 
                         comments_count, score, red_votes, black_votes, trend_days, trend_latest, observed_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        metrics_rows,
                    )
                if claims_rows:
                    conn.executemany(
                        """
                        INSERT INTO environment_claims 
                        (pack_id, source_item_id, side, status, certainty, evidence_type, evidence_text, 
                         raw_value, source_field, source_url, observed_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        claims_rows,
                    )

            packs_rows = []
            sources_rows = []
            aliases_rows = []
            releases_rows = []
            rel_mc_rows = []
            si_loaders_rows = []
            si_cats_rows = []
            dl_rows = []
            rv_rows = []
            metrics_rows = []
            claims_rows = []

        item_count = 0
        for bundle in adapter.load_and_adapt():
            item_count += 1
            total_records += 1

            # Pack
            p = bundle.pack
            packs_rows.append((p.id, p.preferred_title, p.normalized_title, p.summary, p.primary_platform, p.created_at, p.updated_at))

            # Source Item
            s = bundle.source_item
            sources_rows.append((
                s.id, s.pack_id, s.platform, s.source_id, s.slug, s.source_url, s.title, s.author,
                s.description, s.icon_url, s.published_at, s.modified_at, s.raw_ref, s.extra_json,
                s.created_at, s.updated_at
            ))

            # Aliases
            for a in bundle.aliases:
                aliases_rows.append((a.pack_id, a.alias_type, a.alias_text, a.source, a.created_at))

            # Releases & MC versions
            for r in bundle.releases:
                releases_rows.append((
                    r.id, r.pack_id, r.source_item_id, r.version_name, r.version_type,
                    r.release_date, 1 if r.is_latest else 0, r.changelog, r.downloads_count,
                    r.extra_json, r.created_at
                ))
                for v_idx, mc_v in enumerate(r.mc_versions):
                    rel_mc_rows.append((r.id, mc_v.strip(), 1 if v_idx == 0 else 0))

            # Loaders
            for ldr_name in bundle.loaders:
                ldr_clean = ldr_name.strip()
                ldr_lower = ldr_clean.lower()
                if ldr_lower not in loaders_cache:
                    conn.execute("INSERT OR IGNORE INTO loaders (name) VALUES (?)", (ldr_clean,))
                    l_cur = conn.execute("SELECT id FROM loaders WHERE name = ?", (ldr_clean,))
                    loaders_cache[ldr_lower] = l_cur.fetchone()[0]
                si_loaders_rows.append((s.id, loaders_cache[ldr_lower]))

            # Categories
            for cat_name in bundle.categories:
                cat_id = get_or_create_category(s.platform, cat_name)
                si_cats_rows.append((s.id, cat_id))

            # Download Links
            for dl in bundle.download_links:
                dl_rows.append((
                    dl.source_item_id, dl.release_id, dl.link_type, dl.url,
                    dl.label, dl.extract_code, 1 if dl.is_server else 0, dl.created_at
                ))

            # Related Videos
            for rv in bundle.related_videos:
                rv_rows.append((
                    rv.source_item_id, rv.bvid, rv.aid, rv.title, rv.author,
                    rv.url, rv.published_at, rv.views, rv.danmaku, rv.likes, rv.coins, rv.created_at
                ))

            # Metrics
            if bundle.metrics:
                m = bundle.metrics
                metrics_rows.append((
                    m.source_item_id, m.views, m.downloads, m.followers, m.likes,
                    m.coins, m.favorites, m.comments_count, m.score, m.red_votes,
                    m.black_votes, m.trend_days, m.trend_latest, m.observed_at
                ))

            # Environment Claims
            for cl in bundle.environment_claims:
                claims_rows.append((
                    cl.pack_id, cl.source_item_id, cl.side, cl.status, cl.certainty,
                    cl.evidence_type, cl.evidence_text, cl.raw_value, cl.source_field,
                    cl.source_url, cl.observed_at
                ))

            if len(packs_rows) >= BATCH_SIZE:
                flush_batch()
                print(f"  ... inserted {item_count}/{rec_count} items")

        flush_batch()
        plat_elapsed = time.time() - plat_start
        print(f"[+] [{p_name.upper()}] completed: {item_count} items in {plat_elapsed:.2f}s ({item_count / max(plat_elapsed, 0.001):.0f} items/s)")

    # Build FTS index
    print("\n[*] Populating FTS5 Full-Text Search index (pack_fts)...")
    fts_start = time.time()
    conn.execute(
        """
        INSERT INTO pack_fts(pack_id, title, aliases, author, summary, categories)
        SELECT 
            p.id,
            p.preferred_title,
            COALESCE((SELECT GROUP_CONCAT(alias_text, ' ') FROM aliases a WHERE a.pack_id = p.id), ''),
            COALESCE(s.author, ''),
            COALESCE(p.summary, ''),
            COALESCE((SELECT GROUP_CONCAT(c.name, ' ') FROM source_item_categories sic JOIN categories c ON sic.category_id = c.id WHERE sic.source_item_id = s.id), '')
        FROM packs p
        LEFT JOIN source_items s ON s.pack_id = p.id;
        """
    )
    conn.commit()
    print(f"[+] FTS5 index populated in {time.time() - fts_start:.2f}s.")

    # Mark ingest run completed
    completed_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE ingest_runs SET status = 'completed', completed_at = ?, notes = ? WHERE run_id = ?",
        (completed_at, f"Total records ingested: {total_records}", run_id),
    )
    conn.commit()

    total_elapsed = time.time() - start_time
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0

    print("\n" + "=" * 60)
    print(f"[*] Ingestion Finished Successfully!")
    print(f"    Total Processed Items : {total_records:,}")
    print(f"    Elapsed Time          : {total_elapsed:.2f} seconds")
    print(f"    Ingestion Speed       : {total_records / max(total_elapsed, 0.001):.0f} items/s")
    print(f"    Canonical DB Path     : {db_path}")
    print(f"    Canonical DB Size     : {db_size / (1024 * 1024):.2f} MB")
    print("=" * 60)

    # Print table row counts
    tables = [
        "ingest_runs",
        "raw_snapshot_refs",
        "packs",
        "source_items",
        "aliases",
        "releases",
        "release_mc_versions",
        "loaders",
        "source_item_loaders",
        "categories",
        "source_item_categories",
        "download_links",
        "related_videos",
        "metrics",
        "environment_claims",
        "pack_fts",
    ]
    print("\nTable Row Counts:")
    counts = {}
    for tbl in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        counts[tbl] = count
        print(f"  - {tbl:<24}: {count:>8,}")

    conn.close()
    return {
        "run_id": run_id,
        "total_records": total_records,
        "total_elapsed": total_elapsed,
        "db_size": db_size,
        "counts": counts,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Canonical SQLite DB for Architecture V2")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="Output SQLite DB path")
    parser.add_argument("--no-recreate", action="store_true", help="Do not remove existing DB file")
    args = parser.parse_args()

    build_canonical_db(db_path=args.db_path, recreate=not args.no_recreate)

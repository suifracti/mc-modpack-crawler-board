"""
Architecture V2 - Phase 3E: Anomaly Detector.
Runs automated forensic anomaly queries against Canonical SQLite (build/canonical.db)
to detect contradictory claims, logical impossibilities, and heuristic hazards.
"""
import os
import sys
import sqlite3
import json

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CANONICAL_DB = os.path.join(REPO_ROOT, "build", "canonical.db")

def run_anomaly_queries():
    conn = sqlite3.connect(CANONICAL_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    anomalies = {}

    print("============================================================")
    print("  Phase 3E: Canonical SQLite Forensic Anomaly Detection")
    print("============================================================")

    # 1. Environment Claims Anomalies
    print("\n[1] Environment Claims Anomalies...")
    # 1.1: Supported/Required with no evidence or unknown certainty
    cursor.execute("""
        SELECT s.platform, e.side, e.status, e.certainty, e.evidence_type, COUNT(*) as cnt
        FROM environment_claims e
        JOIN source_items s ON e.source_item_id = s.id
        WHERE e.status IN ('supported', 'required', 'optional') 
          AND (e.certainty = 'unknown' OR e.evidence_type = 'no_evidence')
        GROUP BY s.platform, e.side, e.status, e.certainty, e.evidence_type
    """)
    anomalies["env_supported_without_evidence"] = [dict(r) for r in cursor.fetchall()]
    print(f"  - Supported/Required without evidence: {len(anomalies['env_supported_without_evidence'])} groups found")

    # 1.2: Unsupported claims with no evidence (absence == unsupported fallacy check)
    cursor.execute("""
        SELECT s.platform, e.side, e.status, e.certainty, e.evidence_type, COUNT(*) as cnt
        FROM environment_claims e
        JOIN source_items s ON e.source_item_id = s.id
        WHERE e.status = 'unsupported' AND e.evidence_type = 'no_evidence'
        GROUP BY s.platform, e.side, e.status, e.certainty, e.evidence_type
    """)
    anomalies["env_unsupported_without_evidence"] = [dict(r) for r in cursor.fetchall()]
    print(f"  - Unsupported without evidence (absence fallacy): {len(anomalies['env_unsupported_without_evidence'])} groups found")

    # 1.3: Confirmed certainty but evidence_type is text_rule (heuristic masquerading as confirmed)
    cursor.execute("""
        SELECT s.platform, e.side, e.status, e.certainty, e.evidence_type, COUNT(*) as cnt
        FROM environment_claims e
        JOIN source_items s ON e.source_item_id = s.id
        WHERE e.certainty = 'confirmed' AND e.evidence_type = 'text_rule'
        GROUP BY s.platform, e.side, e.status, e.certainty, e.evidence_type
    """)
    anomalies["env_confirmed_text_rule"] = [dict(r) for r in cursor.fetchall()]
    print(f"  - Confirmed certainty derived from text_rule heuristic: {len(anomalies['env_confirmed_text_rule'])} groups found")

    # 1.4: Distribution of environment support by platform
    cursor.execute("""
        SELECT s.platform, e.side, e.status, e.certainty, e.evidence_type, COUNT(*) as cnt
        FROM environment_claims e
        JOIN source_items s ON e.source_item_id = s.id
        GROUP BY s.platform, e.side, e.status, e.certainty, e.evidence_type
        ORDER BY s.platform, e.side, e.status
    """)
    anomalies["env_distribution"] = [dict(r) for r in cursor.fetchall()]

    # 2. Time Semantics Anomalies
    print("\n[2] Time Semantics Anomalies...")
    # 2.1: Published at > Modified at (impossible forward chronology)
    cursor.execute("""
        SELECT s.platform, s.id, s.title, s.published_at, s.modified_at
        FROM source_items s
        WHERE s.published_at IS NOT NULL 
          AND s.modified_at IS NOT NULL 
          AND s.published_at > s.modified_at
        LIMIT 20
    """)
    anomalies["time_published_after_modified"] = [dict(r) for r in cursor.fetchall()]
    print(f"  - published_at > modified_at anomalies: {len(anomalies['time_published_after_modified'])} samples found")

    # 2.2: Release date > 2026-12-31 (future dates)
    cursor.execute("""
        SELECT s.platform, r.id, r.version_name, r.release_date
        FROM releases r
        JOIN source_items s ON r.source_item_id = s.id
        WHERE r.release_date > '2026-12-31'
        LIMIT 20
    """)
    anomalies["time_future_release_date"] = [dict(r) for r in cursor.fetchall()]
    print(f"  - Future release dates (> 2026): {len(anomalies['time_future_release_date'])} samples found")

    # 2.3: Null published_at counts per platform
    cursor.execute("""
        SELECT s.platform, 
               COUNT(*) as total_items,
               SUM(CASE WHEN s.published_at IS NULL THEN 1 ELSE 0 END) as null_published,
               SUM(CASE WHEN s.modified_at IS NULL THEN 1 ELSE 0 END) as null_modified
        FROM source_items s
        GROUP BY s.platform
    """)
    anomalies["time_null_counts"] = [dict(r) for r in cursor.fetchall()]
    print("  - Time null counts by platform:")
    for r in anomalies["time_null_counts"]:
        print(f"    * {r['platform']}: total {r['total_items']}, null published: {r['null_published']}, null modified: {r['null_modified']}")

    # 3. Loader Anomalies
    print("\n[3] Loader Anomalies...")
    # 3.1: Source item with unknown loader while title strongly indicates Forge/Fabric/NeoForge/Quilt
    cursor.execute("""
        SELECT s.platform, s.id, s.title, GROUP_CONCAT(l.name) as loaders
        FROM source_items s
        LEFT JOIN source_item_loaders sil ON s.id = sil.source_item_id
        LEFT JOIN loaders l ON sil.loader_id = l.id
        WHERE (l.name IS NULL OR l.name = 'unknown')
          AND (
            LOWER(s.title) LIKE '%forge%' OR 
            LOWER(s.title) LIKE '%fabric%' OR 
            LOWER(s.title) LIKE '%neoforge%' OR 
            LOWER(s.title) LIKE '%quilt%'
          )
        GROUP BY s.id
        LIMIT 25
    """)
    anomalies["loader_missed_in_title"] = [dict(r) for r in cursor.fetchall()]
    print(f"  - Packs with unknown/missing loader but title mentions loader: {len(anomalies['loader_missed_in_title'])} samples found")

    # 3.2: Loader distribution by platform
    cursor.execute("""
        SELECT s.platform, COALESCE(l.name, 'None') as loader, COUNT(DISTINCT s.id) as count
        FROM source_items s
        LEFT JOIN source_item_loaders sil ON s.id = sil.source_item_id
        LEFT JOIN loaders l ON sil.loader_id = l.id
        GROUP BY s.platform, l.name
        ORDER BY s.platform, count DESC
    """)
    anomalies["loader_distribution"] = [dict(r) for r in cursor.fetchall()]

    # 4. Minecraft Version Anomalies
    print("\n[4] Minecraft Version Anomalies...")
    cursor.execute("""
        SELECT s.platform, COUNT(DISTINCT s.id) as items_without_mc_version
        FROM source_items s
        LEFT JOIN releases r ON s.id = r.source_item_id
        LEFT JOIN release_mc_versions rmv ON r.id = rmv.release_id
        WHERE rmv.mc_version IS NULL
        GROUP BY s.platform
    """)
    anomalies["mc_version_missing_per_platform"] = [dict(r) for r in cursor.fetchall()]
    print("  - Items without MC Version by platform:")
    for r in anomalies["mc_version_missing_per_platform"]:
        print(f"    * {r['platform']}: {r['items_without_mc_version']} items without MC version")

    # 4.2: Abnormal version strings
    cursor.execute("""
        SELECT DISTINCT rmv.mc_version, COUNT(*) as cnt
        FROM release_mc_versions rmv
        WHERE rmv.mc_version NOT GLOB '[0-9]*.[0-9]*'
          AND rmv.mc_version NOT GLOB '[0-9]*.[0-9]*.[0-9]*'
          AND rmv.mc_version NOT GLOB '[0-9]*.[0-9]*.*'
        GROUP BY rmv.mc_version
        ORDER BY cnt DESC
        LIMIT 30
    """)
    anomalies["mc_version_nonstandard_patterns"] = [dict(r) for r in cursor.fetchall()]
    print(f"  - Non-standard MC Version patterns: {len(anomalies['mc_version_nonstandard_patterns'])} patterns found")

    # 5. Download Links Anomalies
    print("\n[5] Download Links Anomalies...")
    cursor.execute("""
        SELECT s.platform, dl.id, dl.url, dl.link_type, dl.label
        FROM download_links dl
        JOIN source_items s ON dl.source_item_id = s.id
        WHERE dl.url IS NULL OR dl.url = '' OR (dl.url NOT LIKE 'http%' AND dl.url NOT LIKE 'ftp%' AND dl.url NOT LIKE 'magnet%')
        LIMIT 25
    """)
    anomalies["download_invalid_urls"] = [dict(r) for r in cursor.fetchall()]
    print(f"  - Download links with empty/invalid URLs: {len(anomalies['download_invalid_urls'])} samples found")

    cursor.execute("""
        SELECT s.platform, dl.link_type, COUNT(*) as cnt
        FROM download_links dl
        JOIN source_items s ON dl.source_item_id = s.id
        GROUP BY s.platform, dl.link_type
        ORDER BY s.platform, cnt DESC
    """)
    anomalies["download_link_types"] = [dict(r) for r in cursor.fetchall()]

    # 6. Included Mods Anomalies (MCMod)
    print("\n[6] MCMod Included Mods Anomalies...")
    cursor.execute("""
        SELECT COUNT(*) as total_included_mods,
               COUNT(DISTINCT mod_name) as distinct_mod_names,
               COUNT(DISTINCT mod_title) as distinct_mod_titles,
               SUM(CASE WHEN mod_title IS NULL OR mod_title = '' THEN 1 ELSE 0 END) as empty_titles,
               SUM(CASE WHEN mod_name IS NULL OR mod_name = '' THEN 1 ELSE 0 END) as empty_names,
               SUM(CASE WHEN category_name IS NULL OR category_name = '' THEN 1 ELSE 0 END) as empty_categories
        FROM included_mods
    """)
    anomalies["included_mods_summary"] = dict(cursor.fetchone())
    print(f"  - Included mods total: {anomalies['included_mods_summary']['total_included_mods']}")
    print(f"  - Distinct mod titles: {anomalies['included_mods_summary']['distinct_mod_titles']}")
    print(f"  - Empty titles: {anomalies['included_mods_summary']['empty_titles']}, Empty names: {anomalies['included_mods_summary']['empty_names']}")

    # Included mod categories breakdown
    cursor.execute("""
        SELECT category_name, COUNT(*) as cnt
        FROM included_mods
        GROUP BY category_name
        ORDER BY cnt DESC
        LIMIT 15
    """)
    anomalies["included_mods_categories"] = [dict(r) for r in cursor.fetchall()]
    print("  - Top included mod categories:")
    for r in anomalies["included_mods_categories"]:
        print(f"    * {r['category_name']}: {r['cnt']}")

    # 7. Metrics Anomalies
    print("\n[7] Metrics Anomalies...")
    cursor.execute("""
        SELECT s.platform,
               COUNT(*) as total_rows,
               SUM(CASE WHEN m.downloads IS NOT NULL AND m.downloads < 0 THEN 1 ELSE 0 END) as negative_downloads,
               SUM(CASE WHEN m.views IS NOT NULL AND m.views < 0 THEN 1 ELSE 0 END) as negative_views,
               SUM(CASE WHEN m.likes IS NOT NULL AND m.likes < 0 THEN 1 ELSE 0 END) as negative_likes,
               SUM(CASE WHEN m.score IS NOT NULL AND (m.score < 0 OR m.score > 100) THEN 1 ELSE 0 END) as out_of_range_score
        FROM metrics m
        JOIN source_items s ON m.source_item_id = s.id
        GROUP BY s.platform
    """)
    anomalies["metrics_ranges"] = [dict(r) for r in cursor.fetchall()]
    print("  - Metrics range validity by platform:")
    for r in anomalies["metrics_ranges"]:
        print(f"    * {r['platform']}: negative downloads={r['negative_downloads']}, negative views={r['negative_views']}, negative likes={r['negative_likes']}, invalid score={r['out_of_range_score']}")

    # Save full anomaly report to file
    out_path = os.path.join(REPO_ROOT, "build", "anomaly_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(anomalies, f, indent=2, ensure_ascii=False)
    print(f"\n[+] Anomaly report saved to {out_path}")

    conn.close()
    return anomalies

if __name__ == "__main__":
    run_anomaly_queries()

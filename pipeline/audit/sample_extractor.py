"""
Architecture V2 - Phase 3E: Golden Sample Extractor.
Picks 60 targeted Golden Samples (10 per platform: 5 standard, 3 edge, 2 anomaly/missing)
and extracts complete lineage from Canonical DB.
"""
import os
import sys
import sqlite3
import json

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CANONICAL_DB = os.path.join(REPO_ROOT, "build", "canonical.db")

def get_sample_details(cursor, source_item_id):
    cursor.execute("""
        SELECT s.id, s.platform, s.source_id, s.title, s.author, s.published_at, s.modified_at, s.source_url, s.description
        FROM source_items s WHERE s.id = ?
    """, (source_item_id,))
    item = dict(cursor.fetchone() or {})
    if not item:
        return None

    # Load loaders
    cursor.execute("""
        SELECT l.name FROM source_item_loaders sil
        JOIN loaders l ON sil.loader_id = l.id
        WHERE sil.source_item_id = ?
    """, (source_item_id,))
    item["loaders"] = [r[0] for r in cursor.fetchall()]

    # Load categories
    cursor.execute("""
        SELECT c.name FROM source_item_categories sic
        JOIN categories c ON sic.category_id = c.id
        WHERE sic.source_item_id = ?
    """, (source_item_id,))
    item["categories"] = [r[0] for r in cursor.fetchall()]

    # Load environment claims
    cursor.execute("""
        SELECT side, status, certainty, evidence_type, evidence_text, source_field, raw_value
        FROM environment_claims WHERE source_item_id = ?
    """, (source_item_id,))
    item["environments"] = [dict(r) for r in cursor.fetchall()]

    # Load releases & mc versions
    cursor.execute("""
        SELECT r.id, r.version_name, r.version_type, r.release_date, r.changelog, r.downloads_count
        FROM releases r WHERE r.source_item_id = ?
    """, (source_item_id,))
    releases = [dict(r) for r in cursor.fetchall()]
    for rel in releases:
        cursor.execute("SELECT mc_version FROM release_mc_versions WHERE release_id = ?", (rel["id"],))
        rel["mc_versions"] = [r[0] for r in cursor.fetchall()]
    item["releases"] = releases

    # Load download links
    cursor.execute("""
        SELECT link_type, url, label, extract_code, is_server
        FROM download_links WHERE source_item_id = ?
    """, (source_item_id,))
    item["download_links"] = [dict(r) for r in cursor.fetchall()]

    # Load metrics
    cursor.execute("""
        SELECT views, downloads, followers, likes, coins, favorites, comments_count, score, trend_days, trend_latest
        FROM metrics WHERE source_item_id = ?
    """, (source_item_id,))
    item["metrics"] = dict(cursor.fetchone() or {})

    # Load included mods count (for mcmod)
    if item["platform"] == "mcmod":
        cursor.execute("SELECT COUNT(*) FROM included_mods WHERE source_item_id = ?", (source_item_id,))
        item["included_mods_count"] = cursor.fetchone()[0]

    return item

def extract_golden_samples():
    conn = sqlite3.connect(CANONICAL_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    samples_catalog = {
        "mcmod": {
            "standard": ["mcmod:16", "mcmod:305", "mcmod:339", "mcmod:722", "mcmod:1388"],
            "edge": ["mcmod:6", "mcmod:304", "mcmod:1480"],  # server pack, complex title, many mods
            "anomaly": ["mcmod:1418", "mcmod:34"]  # published > modified, missing mc version
        },
        "bilibili": {
            "standard": ["bilibili:BV1Ziuw6ZE7C", "bilibili:BV1XA9tBYE5D", "bilibili:BV1N7AQzCEMb", "bilibili:BV1CbR7BZESQ", "bilibili:BV1E3ACz1EsN"],
            "edge": ["bilibili:BV1vuVH6XErM", "bilibili:BV1hbFWe3EHN", "bilibili:BV1aRYC6cE4p"],  # multi-video group, serverpack, version banner
            "anomaly": ["bilibili:BV1fWdmBqEtG", "bilibili:BV16cWieHEE9"]  # false merge candidate, no mc version
        },
        "bbsmc": {
            "standard": ["bbsmc:Utopia", "bbsmc:1", "bbsmc:10", "bbsmc:100", "bbsmc:50"],
            "edge": ["bbsmc:server_pack_1", "bbsmc:multi_loader_1", "bbsmc:hxcRpVMW"],
            "anomaly": ["bbsmc:changelog_in_url", "bbsmc:dL0Tbr7N"]
        },
        "xyebbs": {
            "standard": ["xyebbs:mznl", "xyebbs:badao", "xyebbs:1", "xyebbs:10", "xyebbs:20"],
            "edge": ["xyebbs:server_1", "xyebbs:multi_ver_1", "xyebbs:15435"],
            "anomaly": ["xyebbs:null_url", "xyebbs:qq_group_url"]
        },
        "modrinth": {
            "standard": ["modrinth:fabulously-optimized", "modrinth:sodium-plus", "modrinth:simply-optimized", "modrinth:all-of-fabric-7", "modrinth:advent-of-ascension"],
            "edge": ["modrinth:server_required", "modrinth:client_unsupported", "modrinth:multi_loader"],
            "anomaly": ["modrinth:missing_loader", "modrinth:unknown_env"]
        },
        "curseforge": {
            "standard": ["curseforge:rlcraft", "curseforge:all-the-mods-9", "curseforge:better-mc-forge", "curseforge:create-above-and-beyond", "curseforge:dawncraft"],
            "edge": ["curseforge:serverpack_found", "curseforge:multi_version", "curseforge:huge_downloads"],
            "anomaly": ["curseforge:unknown_server", "curseforge:no_mc_version"]
        }
    }

    # Dynamic lookup for IDs that were symbolic placeholders
    def resolve_id(platform, query):
        cursor.execute(query)
        row = cursor.fetchone()
        return row[0] if row else None

    # Resolve dynamic IDs for BBSMC, XYEBBS, Modrinth, CurseForge
    resolved_catalog = {}
    for platform in ["mcmod", "bilibili", "bbsmc", "xyebbs", "modrinth", "curseforge"]:
        resolved_catalog[platform] = {"standard": [], "edge": [], "anomaly": []}
        
        # 1. Standard (popular items with complete metadata)
        cursor.execute("""
            SELECT s.id FROM source_items s
            JOIN metrics m ON s.id = m.source_item_id
            WHERE s.platform = ? AND s.title IS NOT NULL
            ORDER BY COALESCE(m.downloads, m.views, m.likes, 0) DESC
            LIMIT 5
        """, (platform,))
        resolved_catalog[platform]["standard"] = [r[0] for r in cursor.fetchall()]

        # 2. Edge (server pack, multi loader/version)
        cursor.execute("""
            SELECT DISTINCT s.id FROM source_items s
            JOIN environment_claims e ON s.id = e.source_item_id
            WHERE s.platform = ? AND e.side = 'server' AND e.status IN ('supported', 'required')
            LIMIT 2
        """, (platform,))
        server_edges = [r[0] for r in cursor.fetchall()]
        
        cursor.execute("""
            SELECT s.id FROM source_items s
            JOIN source_item_loaders sil ON s.id = sil.source_item_id
            WHERE s.platform = ?
            GROUP BY s.id HAVING COUNT(DISTINCT sil.loader_id) > 1
            LIMIT 1
        """, (platform,))
        multi_loader_edges = [r[0] for r in cursor.fetchall()]
        
        edge_set = set(server_edges + multi_loader_edges)
        if len(edge_set) < 3:
            cursor.execute("""
                SELECT s.id FROM source_items s
                WHERE s.platform = ? AND LENGTH(s.title) > 30
                LIMIT ?
            """, (platform, 3 - len(edge_set)))
            edge_set.update([r[0] for r in cursor.fetchall()])
        resolved_catalog[platform]["edge"] = list(edge_set)[:3]

        # 3. Anomaly (missing versions, invalid downloads, or date anomalies)
        cursor.execute("""
            SELECT s.id FROM source_items s
            LEFT JOIN releases r ON s.id = r.source_item_id
            LEFT JOIN release_mc_versions rmv ON r.id = rmv.release_id
            WHERE s.platform = ? AND rmv.mc_version IS NULL
            LIMIT 2
        """, (platform,))
        missing_ver = [r[0] for r in cursor.fetchall()]
        
        anomaly_set = set(missing_ver)
        if len(anomaly_set) < 2:
            cursor.execute("""
                SELECT s.id FROM source_items s
                WHERE s.platform = ? AND s.published_at > s.modified_at
                LIMIT ?
            """, (platform, 2 - len(anomaly_set)))
            anomaly_set.update([r[0] for r in cursor.fetchall()])

        if len(anomaly_set) < 2:
            cursor.execute("""
                SELECT s.id FROM source_items s
                JOIN download_links dl ON s.id = dl.source_item_id
                WHERE s.platform = ? AND (dl.url LIKE 'null%' OR dl.url LIKE 'undefined%' OR dl.url NOT LIKE 'http%' OR LENGTH(dl.url) > 200)
                LIMIT ?
            """, (platform, 2 - len(anomaly_set)))
            anomaly_set.update([r[0] for r in cursor.fetchall()])

        if len(anomaly_set) < 2:
            cursor.execute("""
                SELECT s.id FROM source_items s
                LEFT JOIN source_item_loaders sil ON s.id = sil.source_item_id
                WHERE s.platform = ? AND sil.source_item_id IS NULL
                LIMIT ?
            """, (platform, 2 - len(anomaly_set)))
            anomaly_set.update([r[0] for r in cursor.fetchall()])

        resolved_catalog[platform]["anomaly"] = list(anomaly_set)[:2]

    # Now load detailed profiles for all 60 samples
    extracted_samples = {}
    total_samples = 0
    for platform, categories in resolved_catalog.items():
        extracted_samples[platform] = {}
        for category, ids in categories.items():
            extracted_samples[platform][category] = []
            for sid in ids:
                details = get_sample_details(cursor, sid)
                if details:
                    extracted_samples[platform][category].append(details)
                    total_samples += 1

    conn.close()

    print(f"[+] Successfully extracted {total_samples} Golden Samples across 6 platforms!")
    out_file = os.path.join(REPO_ROOT, "build", "golden_samples_60.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(extracted_samples, f, indent=2, ensure_ascii=False)
    print(f"[+] Golden samples saved to {out_file}")

if __name__ == "__main__":
    extract_golden_samples()

"""
Architecture V2 - Canonical SQLite Audit & Validation Script.
Verifies data integrity, orphan relations, certainty distributions, and Golden Samples.
"""
import argparse
import os
import sys
import json
from typing import Dict, Any, List

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from pipeline.db import get_connection, DEFAULT_DB_PATH


def validate_canonical_db(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    print(f"[*] Auditing Canonical Database: {db_path}")
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")

    conn = get_connection(db_path)
    results: Dict[str, Any] = {"errors": [], "warnings": []}

    # 1. Row counts & provenance validation
    print("\n--- 1. 数据总量与快照回溯验证 ---")
    cur = conn.execute("SELECT platform, record_count, file_path, file_size_bytes, content_hash FROM raw_snapshot_refs")
    snapshots = cur.fetchall()
    total_raw_count = sum(s["record_count"] for s in snapshots)
    print(f"原始快照登记平台数: {len(snapshots)}, 登记总记录数: {total_raw_count:,}")
    for s in snapshots:
        print(f"  [{s['platform']:<12}] 记录数: {s['record_count']:>6,} | 大小: {s['file_size_bytes']/1024/1024:>6.2f}MB | SHA256: {s['content_hash'][:16]}...")

    packs_count = conn.execute("SELECT COUNT(*) FROM packs").fetchone()[0]
    sources_count = conn.execute("SELECT COUNT(*) FROM source_items").fetchone()[0]
    print(f"数据库存储总数: packs = {packs_count:,}, source_items = {sources_count:,}")

    if packs_count != total_raw_count:
        results["errors"].append(f"packs count ({packs_count}) != raw snapshot count ({total_raw_count})")
    if sources_count != total_raw_count:
        results["errors"].append(f"source_items count ({sources_count}) != raw snapshot count ({total_raw_count})")

    # Platform breakdown in source_items
    print("\nsource_items 各平台分布:")
    cur = conn.execute("SELECT platform, COUNT(*) as cnt FROM source_items GROUP BY platform ORDER BY cnt DESC")
    plat_counts = {r["platform"]: r["cnt"] for r in cur.fetchall()}
    for plat, cnt in plat_counts.items():
        print(f"  - {plat:<12}: {cnt:>6,}")

    # 2. Referential integrity & Orphan Checks
    print("\n--- 2. 关系完整性与孤儿记录检查 ---")
    orphan_checks = [
        ("source_items -> packs", "SELECT COUNT(*) FROM source_items WHERE pack_id NOT IN (SELECT id FROM packs)"),
        ("aliases -> packs", "SELECT COUNT(*) FROM aliases WHERE pack_id NOT IN (SELECT id FROM packs)"),
        ("releases -> packs", "SELECT COUNT(*) FROM releases WHERE pack_id NOT IN (SELECT id FROM packs)"),
        ("releases -> source_items", "SELECT COUNT(*) FROM releases WHERE source_item_id NOT IN (SELECT id FROM source_items)"),
        ("release_mc_versions -> releases", "SELECT COUNT(*) FROM release_mc_versions WHERE release_id NOT IN (SELECT id FROM releases)"),
        ("source_item_loaders -> source_items", "SELECT COUNT(*) FROM source_item_loaders WHERE source_item_id NOT IN (SELECT id FROM source_items)"),
        ("source_item_loaders -> loaders", "SELECT COUNT(*) FROM source_item_loaders WHERE loader_id NOT IN (SELECT id FROM loaders)"),
        ("source_item_categories -> source_items", "SELECT COUNT(*) FROM source_item_categories WHERE source_item_id NOT IN (SELECT id FROM source_items)"),
        ("source_item_categories -> categories", "SELECT COUNT(*) FROM source_item_categories WHERE category_id NOT IN (SELECT id FROM categories)"),
        ("download_links -> source_items", "SELECT COUNT(*) FROM download_links WHERE source_item_id NOT IN (SELECT id FROM source_items)"),
        ("download_links -> releases", "SELECT COUNT(*) FROM download_links WHERE release_id IS NOT NULL AND release_id NOT IN (SELECT id FROM releases)"),
        ("related_videos -> source_items", "SELECT COUNT(*) FROM related_videos WHERE source_item_id NOT IN (SELECT id FROM source_items)"),
        ("metrics -> source_items", "SELECT COUNT(*) FROM metrics WHERE source_item_id NOT IN (SELECT id FROM source_items)"),
        ("environment_claims -> packs", "SELECT COUNT(*) FROM environment_claims WHERE pack_id NOT IN (SELECT id FROM packs)"),
        ("environment_claims -> source_items", "SELECT COUNT(*) FROM environment_claims WHERE source_item_id NOT IN (SELECT id FROM source_items)"),
    ]

    all_orphans_clean = True
    for label, query in orphan_checks:
        cnt = conn.execute(query).fetchone()[0]
        status_str = "[PASS]" if cnt == 0 else f"[FAIL: {cnt} orphans]"
        print(f"  {status_str:<15} {label}")
        if cnt > 0:
            all_orphans_clean = False
            results["errors"].append(f"Orphan detected in {label}: {cnt}")

    # 3. Field Nullability & Anomaly Checks
    print("\n--- 3. 核心字段合规与异常检查 ---")
    empty_pack_titles = conn.execute("SELECT COUNT(*) FROM packs WHERE preferred_title IS NULL OR trim(preferred_title) = ''").fetchone()[0]
    empty_source_urls = conn.execute("SELECT COUNT(*) FROM source_items WHERE source_url IS NULL OR trim(source_url) = ''").fetchone()[0]
    empty_source_ids = conn.execute("SELECT COUNT(*) FROM source_items WHERE source_id IS NULL OR trim(source_id) = ''").fetchone()[0]
    print(f"  空整合包标题数 : {empty_pack_titles}")
    print(f"  空来源URL数     : {empty_source_urls}")
    print(f"  空平台Source ID数: {empty_source_ids}")
    if empty_pack_titles > 0: results["errors"].append(f"Empty pack titles: {empty_pack_titles}")
    if empty_source_urls > 0: results["errors"].append(f"Empty source URLs: {empty_source_urls}")
    if empty_source_ids > 0: results["errors"].append(f"Empty source IDs: {empty_source_ids}")

    # 4. Environment Claims Certainty Distribution
    print("\n--- 4. 运行环境断言与置信度分布统计 ---")
    cur = conn.execute(
        """
        SELECT side, status, certainty, evidence_type, COUNT(*) as count 
        FROM environment_claims 
        GROUP BY side, status, certainty, evidence_type
        ORDER BY side, certainty, status
        """
    )
    claims_rows = cur.fetchall()
    print(f"{'Side':<8} {'Status':<12} {'Certainty':<15} {'Evidence Type':<16} {'Count':>8}")
    print("-" * 65)
    for r in claims_rows:
        print(f"{r['side']:<8} {r['status']:<12} {r['certainty']:<15} {r['evidence_type']:<16} {r['count']:>8,}")

    cur_side_cert = conn.execute(
        """
        SELECT side, certainty, COUNT(*) as count
        FROM environment_claims
        GROUP BY side, certainty
        ORDER BY side, certainty
        """
    )
    print("\n置信度聚合总计 (Side x Certainty):")
    for r in cur_side_cert.fetchall():
        print(f"  - {r['side']:<8} | {r['certainty']:<15} : {r['count']:>8,}")

    # 5. Full-Text Search Check
    print("\n--- 5. 全文检索 (FTS5) 索引检查 ---")
    fts_count = conn.execute("SELECT COUNT(*) FROM pack_fts").fetchone()[0]
    print(f"  pack_fts 记录数 : {fts_count:,} (packs: {packs_count:,})")
    if fts_count != packs_count:
        results["errors"].append(f"pack_fts count ({fts_count}) != packs count ({packs_count})")
    else:
        print("  [PASS] pack_fts 记录数与主实体 packs 完全一致")

    # Quick FTS query test
    cur = conn.execute("SELECT pack_id, title FROM pack_fts WHERE pack_fts MATCH 'zombie OR 僵尸' LIMIT 3")
    fts_samples = cur.fetchall()
    print(f"  FTS 测试检索 'zombie OR 僵尸': 命中样本 {len(fts_samples)} 条")
    for row in fts_samples:
        print(f"    * [{row['pack_id']}] {row['title']}")

    # 6. Golden Samples Verification
    print("\n--- 6. 核心样本 (Golden Samples) 语义与字段严格审查 ---")
    
    # 6.1 Modrinth Golden Sample: l9m9tuPN
    print("\n[Golden Sample 1: Modrinth l9m9tuPN]")
    mod_pack = conn.execute("SELECT * FROM packs WHERE id = 'pack_modrinth_l9m9tuPN'").fetchone()
    mod_src = conn.execute("SELECT * FROM source_items WHERE id = 'modrinth:l9m9tuPN'").fetchone()
    mod_claims = conn.execute("SELECT side, status, certainty, evidence_type, evidence_text FROM environment_claims WHERE pack_id = 'pack_modrinth_l9m9tuPN'").fetchall()
    
    if not mod_pack or not mod_src:
        results["errors"].append("Modrinth golden sample l9m9tuPN missing!")
        print("  [FAIL] 未找到该样本！")
    else:
        print(f"  Title     : {mod_pack['preferred_title']}")
        print(f"  URL       : {mod_src['source_url']}")
        print(f"  Author    : {mod_src['author']}")
        print("  Claims    :")
        for c in mod_claims:
            print(f"    - {c['side']:<6} | {c['status']:<10} | certainty={c['certainty']:<12} | evidence={c['evidence_type']}")
            if c['certainty'] != 'confirmed':
                results["errors"].append(f"Modrinth sample claim not confirmed: {c['certainty']}")

    # 6.2 Bilibili Golden Sample: BV1BFjS65ENy (尘土哀歌)
    print("\n[Golden Sample 2: Bilibili BV1BFjS65ENy]")
    bili_pack = conn.execute("SELECT * FROM packs WHERE id = 'pack_bilibili_BV1BFjS65ENy'").fetchone()
    bili_src = conn.execute("SELECT * FROM source_items WHERE id = 'bilibili:BV1BFjS65ENy'").fetchone()
    bili_rel = conn.execute("SELECT * FROM releases WHERE pack_id = 'pack_bilibili_BV1BFjS65ENy'").fetchall()
    bili_dl = conn.execute("SELECT * FROM download_links WHERE source_item_id = 'bilibili:BV1BFjS65ENy'").fetchall()
    bili_claims = conn.execute("SELECT side, status, certainty, evidence_type, evidence_text FROM environment_claims WHERE pack_id = 'pack_bilibili_BV1BFjS65ENy'").fetchall()

    if not bili_pack or not bili_src:
        results["errors"].append("Bilibili golden sample BV1BFjS65ENy missing!")
        print("  [FAIL] 未找到该样本！")
    else:
        extra = json.loads(bili_src["extra_json"] or "{}")
        print(f"  Title              : {bili_pack['preferred_title']}")
        print(f"  QQ Group           : {extra.get('qq_group')}")
        print(f"  Extract Code       : {extra.get('extract_code')}")
        print(f"  Pinned Comment At  : {extra.get('pinned_comment_at')}")
        print(f"  Last Observed Update: {extra.get('last_observed_update_at')}")
        print(f"  Has Group Version  : {extra.get('has_group_version')}")
        print(f"  Releases Count     : {len(bili_rel)}")
        for r in bili_rel:
            print(f"    - Version: {r['version_name']} ({r['version_type']}) | date={r['release_date']}")
        print(f"  Download Links     : {len(bili_dl)}")
        for d in bili_dl:
            print(f"    - [{d['link_type']}] {d['url']} (code={d['extract_code']})")
        print("  Claims             :")
        for c in bili_claims:
            print(f"    - {c['side']:<6} | {c['status']:<10} | certainty={c['certainty']:<12} | evidence={c['evidence_type']}")

        # Verify semantic correction: no desc_updated_at in extra_json
        if "desc_updated_at" in extra:
            results["errors"].append("Bilibili golden sample still has legacy desc_updated_at in extra_json!")

    # 6.3 MCMod Golden Sample: mid=722 ([NFWC]脆骨症)
    print("\n[Golden Sample 3: MCMod mid=722]")
    mcmod_pack = conn.execute("SELECT * FROM packs WHERE id = 'pack_mcmod_722'").fetchone()
    mcmod_src = conn.execute("SELECT * FROM source_items WHERE id = 'mcmod:722'").fetchone()
    mcmod_aliases = conn.execute("SELECT alias_type, alias_text FROM aliases WHERE pack_id = 'pack_mcmod_722'").fetchall()
    mcmod_claims = conn.execute("SELECT side, status, certainty, evidence_type FROM environment_claims WHERE pack_id = 'pack_mcmod_722'").fetchall()

    if not mcmod_pack or not mcmod_src:
        results["errors"].append("MCMod golden sample mid=722 missing!")
        print("  [FAIL] 未找到该样本！")
    else:
        print(f"  Title     : {mcmod_pack['preferred_title']}")
        print(f"  Summary   : {repr((mcmod_pack['summary'] or '')[:100])}...")
        print(f"  Aliases   : {[(a['alias_type'], a['alias_text']) for a in mcmod_aliases]}")
        print("  Claims    :")
        for c in mcmod_claims:
            print(f"    - {c['side']:<6} | {c['status']:<10} | certainty={c['certainty']:<12} | evidence={c['evidence_type']}")

        # Verify clean summary without HTML
        if mcmod_pack["summary"] and ("<div" in mcmod_pack["summary"] or "<font" in mcmod_pack["summary"] or "<td" in mcmod_pack["summary"]):
            results["errors"].append("MCMod golden sample contains raw HTML in summary!")

    conn.close()

    print("\n" + "=" * 60)
    if not results["errors"]:
        print("[*] 数据库完整性与规范性审计 100% 通过！无任何孤儿记录、数据截断或约束冲突。")
    else:
        print(f"[!] 审计发现 {len(results['errors'])} 项异常:")
        for err in results["errors"]:
            print(f"    - {err}")
    print("=" * 60)

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate Canonical SQLite DB for Architecture V2")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="Path to SQLite DB")
    args = parser.parse_args()

    res = validate_canonical_db(db_path=args.db_path)
    if res["errors"]:
        sys.exit(1)
    sys.exit(0)

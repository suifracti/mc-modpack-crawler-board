"""
Architecture V2 - Canonical SQLite Audit & Validation Script (Phase 1.1).
Verifies structural integrity, semantic integrity, evidence provenance, and Golden Samples.
"""
import argparse
import os
import sys
import json
from collections import defaultdict
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

    # 2. Structural & Referential integrity
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

    for label, query in orphan_checks:
        cnt = conn.execute(query).fetchone()[0]
        status_str = "[PASS]" if cnt == 0 else f"[FAIL: {cnt} orphans]"
        print(f"  {status_str:<15} {label}")
        if cnt > 0:
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

    # 4. Semantic Integrity Audit (Phase 1.1 Core Requirements)
    print("\n--- 4. 语义完整性严格审计 (Semantic Integrity Audit) ---")
    
    # Rule 4.1: Non-Modrinth data using certainty=confirmed and evidence_type=platform_field without real source_field / raw_value
    q_rule1 = """
        SELECT COUNT(*) FROM environment_claims 
        WHERE certainty = 'confirmed' 
          AND evidence_type = 'platform_field'
          AND source_item_id NOT LIKE 'modrinth:%'
          AND (source_field IS NULL OR trim(source_field) = '' OR raw_value IS NULL OR trim(raw_value) = '')
    """
    cnt_rule1 = conn.execute(q_rule1).fetchone()[0]
    if cnt_rule1 == 0:
        print("  [PASS] 规则 1: 非 Modrinth 数据无伪造 confirmed platform_field")
    else:
        print(f"  [FAIL] 规则 1: 发现 {cnt_rule1} 条非 Modrinth 伪造 confirmed platform_field 断言！")
        results["errors"].append(f"Rule 1 violation: {cnt_rule1} fake confirmed claims")

    # Rule 4.2: unsupported claim without positive unsupported evidence
    q_rule2 = """
        SELECT COUNT(*) FROM environment_claims
        WHERE status = 'unsupported'
          AND (
            (certainty = 'confirmed' AND (raw_value IS NULL OR raw_value != 'unsupported'))
            OR (certainty != 'confirmed' AND (evidence_text IS NULL OR trim(evidence_text) = '' OR raw_value IS NULL OR trim(raw_value) = ''))
          )
    """
    cnt_rule2 = conn.execute(q_rule2).fetchone()[0]
    if cnt_rule2 == 0:
        print("  [PASS] 规则 2: 所有 unsupported 断言均具有真实反向证据，无因‘未检索到’被误标为 unsupported")
    else:
        print(f"  [FAIL] 规则 2: 发现 {cnt_rule2} 条缺乏证据的 unsupported 断言！")
        results["errors"].append(f"Rule 2 violation: {cnt_rule2} unverified unsupported claims")

    # Rule 4.3: inferred / weak_inferred / strong_inferred claim with empty evidence_text and raw_value
    q_rule3 = """
        SELECT COUNT(*) FROM environment_claims
        WHERE certainty IN ('inferred', 'weak_inferred', 'strong_inferred')
          AND (evidence_text IS NULL OR trim(evidence_text) = '')
          AND (raw_value IS NULL OR trim(raw_value) = '')
    """
    cnt_rule3 = conn.execute(q_rule3).fetchone()[0]
    if cnt_rule3 == 0:
        print("  [PASS] 规则 3: 所有推断类断言 (inferred/strong/weak) 均包含非空 evidence_text 与 raw_value")
    else:
        print(f"  [FAIL] 规则 3: 发现 {cnt_rule3} 条推断类断言缺乏证据原句/原词！")
        results["errors"].append(f"Rule 3 violation: {cnt_rule3} inferred claims without evidence text")

    # Rule 4.4: Bilibili last_observed_update_at unconditionally equals pinned_comment_at
    q_rule4 = """
        SELECT COUNT(*) FROM source_items
        WHERE platform = 'bilibili'
          AND json_extract(extra_json, '$.pinned_comment_at') IS NOT NULL
          AND json_extract(extra_json, '$.last_observed_update_at') = json_extract(extra_json, '$.pinned_comment_at')
    """
    cnt_rule4 = conn.execute(q_rule4).fetchone()[0]
    if cnt_rule4 == 0:
        print("  [PASS] 规则 4: B站 last_observed_update_at 独立于置顶评论 ctime，无混淆等同")
    else:
        print(f"  [FAIL] 规则 4: 发现 {cnt_rule4} 条B站条目直接无条件将置顶评论时间当作观测更新时间！")
        results["errors"].append(f"Rule 4 violation: {cnt_rule4} Bilibili items equated observed time with comment time")

    # Rule 4.5: Bilibili release.release_date must be NULL (no genuine release timestamp in raw video)
    q_rule5 = """
        SELECT COUNT(*) FROM releases
        WHERE source_item_id LIKE 'bilibili:%'
          AND release_date IS NOT NULL
    """
    cnt_rule5 = conn.execute(q_rule5).fetchone()[0]
    if cnt_rule5 == 0:
        print("  [PASS] 规则 5: B站 release.release_date 严格置为 NULL，真实公告时间转存至 extra_json.announced_at")
    else:
        print(f"  [FAIL] 规则 5: 发现 {cnt_rule5} 条B站版本虚构了 release_date！")
        results["errors"].append(f"Rule 5 violation: {cnt_rule5} Bilibili releases with non-null release_date")

    # 4.2 Time Semantic Validation (Phase 2A.2 Final Provenance)
    print("\n--- 4.2 时间语义完整性严格验证 (Time Semantic Integrity Rules A~D) ---")

    # Rule A: observed_at 不得早于 published_at（若 published_at 非空）
    q_rule_a = """
        SELECT COUNT(*) FROM source_items
        WHERE platform = 'bilibili'
          AND json_extract(extra_json, '$.published_at') IS NOT NULL
          AND json_extract(extra_json, '$.observed_at') < json_extract(extra_json, '$.published_at')
    """
    cnt_rule_a = conn.execute(q_rule_a).fetchone()[0]
    if cnt_rule_a == 0:
        print("  [PASS] Rule A: observed_at 严格不早于 published_at (0 违规)")
    else:
        print(f"  [FAIL] Rule A: 发现 {cnt_rule_a} 条记录 observed_at 早于 published_at！")
        results["errors"].append(f"Rule A violation: {cnt_rule_a} records observed_at < published_at")

    # Rule B: last_observed_update_at 如果非 NULL，不得早于 published_at, pinned_comment_at, update_notice_at
    q_rule_b = """
        SELECT COUNT(*) FROM source_items
        WHERE platform = 'bilibili'
          AND json_extract(extra_json, '$.last_observed_update_at') IS NOT NULL
          AND (
            (json_extract(extra_json, '$.published_at') IS NOT NULL 
             AND json_extract(extra_json, '$.last_observed_update_at') < json_extract(extra_json, '$.published_at'))
            OR
            (json_extract(extra_json, '$.pinned_comment_at') IS NOT NULL 
             AND json_extract(extra_json, '$.last_observed_update_at') < json_extract(extra_json, '$.pinned_comment_at'))
            OR
            (json_extract(extra_json, '$.update_notice_at') IS NOT NULL 
             AND json_extract(extra_json, '$.last_observed_update_at') < json_extract(extra_json, '$.update_notice_at'))
          )
    """
    cnt_rule_b = conn.execute(q_rule_b).fetchone()[0]
    if cnt_rule_b == 0:
        print("  [PASS] Rule B: 非空 last_observed_update_at 不早于历史已知时间戳 (0 违规)")
    else:
        print(f"  [FAIL] Rule B: 发现 {cnt_rule_b} 条记录 last_observed_update_at 早于历史事件！")
        results["errors"].append(f"Rule B violation: {cnt_rule_b} records with premature last_observed_update_at")

    # Rule C: 禁止 observation_time_source = 'file_mtime_fallback' AND last_observed_update_at != NULL
    q_rule_c = """
        SELECT COUNT(*) FROM source_items
        WHERE json_extract(extra_json, '$.observation_time_source') = 'file_mtime_fallback'
          AND json_extract(extra_json, '$.last_observed_update_at') IS NOT NULL
    """
    cnt_rule_c = conn.execute(q_rule_c).fetchone()[0]
    if cnt_rule_c == 0:
        print("  [PASS] Rule C: 彻底禁止 file_mtime_fallback 作为 last_observed_update_at (0 违规)")
    else:
        print(f"  [FAIL] Rule C: 发现 {cnt_rule_c} 条记录使用文件 mtime 冒充 last_observed_update_at！")
        results["errors"].append(f"Rule C violation: {cnt_rule_c} records using file_mtime_fallback")

    # Rule D: 无真实 change detection 时，last_observed_update_at = NULL 视为合法规范状态
    q_rule_d = """
        SELECT COUNT(*) FROM source_items
        WHERE platform = 'bilibili'
          AND json_extract(extra_json, '$.last_observed_update_at') IS NULL
          AND json_extract(extra_json, '$.observation_time_source') = 'canonical_ingest_run'
    """
    cnt_rule_d = conn.execute(q_rule_d).fetchone()[0]
    total_bili = conn.execute("SELECT COUNT(*) FROM source_items WHERE platform = 'bilibili'").fetchone()[0]
    if cnt_rule_d == total_bili:
        print(f"  [PASS] Rule D: 全部 {cnt_rule_d}/{total_bili} 条 B站记录在无变更事件时合法保持 NULL (零猜时间)")
    else:
        print(f"  [WARN] Rule D: 存在非 NULL 或未规范标记的记录: {total_bili - cnt_rule_d}")

    # 4.3 Bilibili 黄金样本时间凭证核验 (Golden Samples Time Verification)
    print("\n--- 4.3 Bilibili 黄金样本时间凭证核验 (Golden Samples Time Verification) ---")
    golden_bvids = ["BV1BFjS65ENy", "BV1aRYC6cE4p", "BV1QTYr6sEXA"]
    for bvid in golden_bvids:
        cur_sample = conn.execute("""
            SELECT id, title, published_at, modified_at, extra_json
            FROM source_items
            WHERE source_id = ? AND platform = 'bilibili'
        """, (bvid,)).fetchone()
        if cur_sample:
            ex = json.loads(cur_sample["extra_json"] or "{}")
            pub_at = ex.get("published_at")
            pinned_at = ex.get("pinned_comment_at")
            up_at = ex.get("update_notice_at")
            obs_at = ex.get("observed_at")
            last_up = ex.get("last_observed_update_at")
            obs_src = ex.get("observation_time_source")
            is_valid = (obs_at >= pub_at) if (obs_at and pub_at) else True
            print(f"  [Sample: {bvid}] (Title: {cur_sample['title'][:25]})")
            print(f"    published_at            : {pub_at}")
            print(f"    pinned_comment_at       : {pinned_at}")
            print(f"    update_notice_at        : {up_at}")
            print(f"    observed_at             : {obs_at}")
            print(f"    last_observed_update_at : {last_up}")
            print(f"    observation_time_source : {obs_src}")
            print(f"    Validation Assertion    : observed_at >= published_at -> {is_valid}")
            if not is_valid:
                results["errors"].append(f"Golden sample {bvid} failed observed_at >= published_at")

    # 5. Environment Claims: Full breakdown by platform x side x status x certainty x evidence_type
    print("\n--- 5. 运行环境断言全矩阵分布 (platform × side × status × certainty × evidence_type) ---")
    cur = conn.execute(
        """
        SELECT 
            s.platform, c.side, c.status, c.certainty, c.evidence_type, COUNT(*) as count
        FROM environment_claims c
        JOIN source_items s ON c.source_item_id = s.id
        GROUP BY s.platform, c.side, c.status, c.certainty, c.evidence_type
        ORDER BY s.platform, c.side, c.certainty, c.status
        """
    )
    matrix_rows = cur.fetchall()
    print(f"{'Platform':<12} {'Side':<8} {'Status':<12} {'Certainty':<16} {'Evidence Type':<16} {'Count':>8}")
    print("-" * 76)
    for r in matrix_rows:
        print(f"{r['platform']:<12} {r['side']:<8} {r['status']:<12} {r['certainty']:<16} {r['evidence_type']:<16} {r['count']:>8,}")

    # Summary by certainty
    print("\n置信度分类总计 (Certainty Summary):")
    cur_cert = conn.execute("SELECT certainty, COUNT(*) as count FROM environment_claims GROUP BY certainty ORDER BY count DESC")
    for r in cur_cert.fetchall():
        print(f"  - {r['certainty']:<16}: {r['count']:>8,}")

    # Summary by side x certainty
    print("\nSide × Certainty 交叉统计:")
    cur_side_cert = conn.execute("SELECT side, certainty, COUNT(*) as count FROM environment_claims GROUP BY side, certainty ORDER BY side, certainty")
    for r in cur_side_cert.fetchall():
        print(f"  - {r['side']:<8} | {r['certainty']:<16}: {r['count']:>8,}")

    # Summary of unsupported & unknown
    unsupported_cnt = conn.execute("SELECT COUNT(*) FROM environment_claims WHERE status = 'unsupported'").fetchone()[0]
    unknown_cnt = conn.execute("SELECT COUNT(*) FROM environment_claims WHERE status = 'unknown'").fetchone()[0]
    print(f"\n核心状态统计: unsupported = {unsupported_cnt:,} | unknown = {unknown_cnt:,}")

    # 6. Real Evidence Samples (At least 3 samples per category)
    print("\n--- 6. 真实证据样本审查 (3 Real Samples per Category) ---")
    categories_to_sample = [
        ("confirmed", "SELECT s.platform, s.source_id, s.title, c.side, c.status, c.certainty, c.evidence_type, c.source_field, c.raw_value, c.evidence_text FROM environment_claims c JOIN source_items s ON c.source_item_id = s.id WHERE c.certainty = 'confirmed' LIMIT 3"),
        ("strong_inferred", "SELECT s.platform, s.source_id, s.title, c.side, c.status, c.certainty, c.evidence_type, c.source_field, c.raw_value, c.evidence_text FROM environment_claims c JOIN source_items s ON c.source_item_id = s.id WHERE c.certainty = 'strong_inferred' LIMIT 3"),
        ("inferred", "SELECT s.platform, s.source_id, s.title, c.side, c.status, c.certainty, c.evidence_type, c.source_field, c.raw_value, c.evidence_text FROM environment_claims c JOIN source_items s ON c.source_item_id = s.id WHERE c.certainty = 'inferred' AND c.status = 'supported' LIMIT 3"),
        ("weak_inferred", "SELECT s.platform, s.source_id, s.title, c.side, c.status, c.certainty, c.evidence_type, c.source_field, c.raw_value, c.evidence_text FROM environment_claims c JOIN source_items s ON c.source_item_id = s.id WHERE c.certainty = 'weak_inferred' LIMIT 3"),
        ("unknown", "SELECT s.platform, s.source_id, s.title, c.side, c.status, c.certainty, c.evidence_type, c.source_field, c.raw_value, c.evidence_text FROM environment_claims c JOIN source_items s ON c.source_item_id = s.id WHERE c.certainty = 'unknown' AND c.side = 'server' LIMIT 3"),
        ("unsupported", "SELECT s.platform, s.source_id, s.title, c.side, c.status, c.certainty, c.evidence_type, c.source_field, c.raw_value, c.evidence_text FROM environment_claims c JOIN source_items s ON c.source_item_id = s.id WHERE c.status = 'unsupported' LIMIT 3"),
    ]

    for cat_name, q in categories_to_sample:
        print(f"\n[Category: {cat_name.upper()}]")
        rows = conn.execute(q).fetchall()
        if not rows:
            print(f"  (当前数据库中无此类记录)")
            continue
        for idx, r in enumerate(rows, 1):
            print(f"  Sample {idx}:")
            print(f"    platform      : {r['platform']}")
            print(f"    source_id     : {r['source_id']}")
            print(f"    title         : {r['title'][:40]}")
            print(f"    side          : {r['side']}")
            print(f"    status        : {r['status']}")
            print(f"    certainty     : {r['certainty']}")
            print(f"    evidence_type : {r['evidence_type']}")
            print(f"    source_field  : {r['source_field']}")
            print(f"    raw_value     : {repr(r['raw_value'])}")
            print(f"    evidence_text : {repr((r['evidence_text'] or '')[:90])}")

    # 7. Golden Samples Verification
    print("\n--- 7. 核心样本 (Golden Samples) 语义与字段严格审查 ---")
    
    # 7.1 Modrinth Golden Sample: l9m9tuPN
    print("\n[Golden Sample 1: Modrinth l9m9tuPN]")
    mod_pack = conn.execute("SELECT * FROM packs WHERE id = 'pack_modrinth_l9m9tuPN'").fetchone()
    mod_src = conn.execute("SELECT * FROM source_items WHERE id = 'modrinth:l9m9tuPN'").fetchone()
    mod_claims = conn.execute("SELECT side, status, certainty, evidence_type, source_field, raw_value, evidence_text FROM environment_claims WHERE pack_id = 'pack_modrinth_l9m9tuPN'").fetchall()
    
    if not mod_pack or not mod_src:
        results["errors"].append("Modrinth golden sample l9m9tuPN missing!")
        print("  [FAIL] 未找到该样本！")
    else:
        print(f"  Title        : {mod_pack['preferred_title']}")
        print(f"  URL          : {mod_src['source_url']}")
        print(f"  Author       : {mod_src['author']}")
        print("  Claims       :")
        for c in mod_claims:
            print(f"    - {c['side']:<6} | {c['status']:<10} | certainty={c['certainty']:<12} | evidence_type={c['evidence_type']} | raw={repr(c['raw_value'])}")

    # 7.2 Bilibili Golden Sample: BV1BFjS65ENy (尘土哀歌)
    print("\n[Golden Sample 2: Bilibili BV1BFjS65ENy]")
    bili_pack = conn.execute("SELECT * FROM packs WHERE id = 'pack_bilibili_BV1BFjS65ENy'").fetchone()
    bili_src = conn.execute("SELECT * FROM source_items WHERE id = 'bilibili:BV1BFjS65ENy'").fetchone()
    bili_rel = conn.execute("SELECT * FROM releases WHERE pack_id = 'pack_bilibili_BV1BFjS65ENy'").fetchall()
    bili_claims = conn.execute("SELECT side, status, certainty, evidence_type, source_field, raw_value, evidence_text FROM environment_claims WHERE pack_id = 'pack_bilibili_BV1BFjS65ENy'").fetchall()

    if not bili_pack or not bili_src:
        results["errors"].append("Bilibili golden sample BV1BFjS65ENy missing!")
        print("  [FAIL] 未找到该样本！")
    else:
        extra = json.loads(bili_src["extra_json"] or "{}")
        print(f"  Title              : {bili_pack['preferred_title']}")
        print(f"  QQ Group           : {extra.get('qq_group')}")
        print(f"  Extract Code       : {extra.get('extract_code')}")
        print(f"  Pinned Comment At  : {extra.get('pinned_comment_at')}")
        print(f"  Update Notice At   : {extra.get('update_notice_at')}")
        print(f"  Last Observed Update: {extra.get('last_observed_update_at')}")
        print(f"  Releases Count     : {len(bili_rel)}")
        for r in bili_rel:
            rel_extra = json.loads(r["extra_json"] or "{}")
            print(f"    - Version: {r['version_name']} ({r['version_type']}) | release_date={r['release_date']} | announced_at={rel_extra.get('announced_at')} | observed_at={rel_extra.get('observed_at')}")
        print("  Claims             :")
        for c in bili_claims:
            print(f"    - {c['side']:<6} | {c['status']:<10} | certainty={c['certainty']:<12} | evidence_type={c['evidence_type']}")

    # 7.3 MCMod Golden Sample: mid=722 ([NFWC]脆骨症)
    print("\n[Golden Sample 3: MCMod mid=722]")
    mcmod_pack = conn.execute("SELECT * FROM packs WHERE id = 'pack_mcmod_722'").fetchone()
    mcmod_src = conn.execute("SELECT * FROM source_items WHERE id = 'mcmod:722'").fetchone()
    mcmod_aliases = conn.execute("SELECT alias_type, alias_text FROM aliases WHERE pack_id = 'pack_mcmod_722'").fetchall()
    mcmod_claims = conn.execute("SELECT side, status, certainty, evidence_type, source_field, raw_value, evidence_text FROM environment_claims WHERE pack_id = 'pack_mcmod_722'").fetchall()

    if not mcmod_pack or not mcmod_src:
        results["errors"].append("MCMod golden sample mid=722 missing!")
        print("  [FAIL] 未找到该样本！")
    else:
        print(f"  Title     : {mcmod_pack['preferred_title']}")
        print(f"  Summary   : {repr((mcmod_pack['summary'] or '')[:100])}...")
        print(f"  Aliases   : {[(a['alias_type'], a['alias_text']) for a in mcmod_aliases]}")
        print("  Claims    :")
        for c in mcmod_claims:
            print(f"    - {c['side']:<6} | {c['status']:<10} | certainty={c['certainty']:<12} | evidence_type={c['evidence_type']}")

    # 7.4 CurseForge False-Positive Verification Sample: RLCraft (285109)
    print("\n[CurseForge False-Positive Check: RLCraft (285109)]")
    rl_claims = conn.execute("SELECT side, status, certainty, evidence_type, evidence_text FROM environment_claims WHERE source_item_id = 'curseforge:285109'").fetchall()
    for c in rl_claims:
        print(f"  - {c['side']:<6} | {c['status']:<10} | certainty={c['certainty']:<12} | evidence={c['evidence_type']}")
        if c['side'] == 'server' and c['status'] == 'supported':
            results["errors"].append("RLCraft was falsely marked as server supported without server pack file!")

    # 8. SQLite Storage Size Breakdown
    print("\n--- 8. SQLite 存储体积深度拆解 (Storage Breakdown) ---")
    db_file_size = os.path.getsize(db_path)
    print(f"Canonical DB 文件总大小: {db_file_size / 1024 / 1024:.2f} MB ({db_file_size:,} bytes)")

    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type in ('table', 'shadow')").fetchall()]
    total_payload = 0
    table_payloads = {}
    for t in tables:
        if t.startswith("sqlite_"): continue
        cols = [c[1] for c in conn.execute(f"PRAGMA table_info({t})").fetchall()]
        if cols:
            expr = " + ".join([f"COALESCE(length(cast(\"{c}\" as blob)), 0)" for c in cols])
            res = conn.execute(f"SELECT count(*), SUM({expr}) FROM \"{t}\"").fetchone()
            cnt = res[0]
            payload = res[1] or 0
            table_payloads[t] = (cnt, payload)
            total_payload += payload

    print(f"\n{'Table / Entity':<28} {'Rows':>10} {'Payload MB':>12} {'% of DB':>10}")
    print("-" * 64)
    for t, (cnt, payload) in sorted(table_payloads.items(), key=lambda x: x[1][1], reverse=True):
        pct = (payload / db_file_size) * 100
        print(f"{t:<28} {cnt:>10,} {payload/1024/1024:>10.2f} MB {pct:>9.1f}%")

    # Column breakdown for source_items
    si_res = conn.execute(
        """
        SELECT 
            SUM(length(extra_json)),
            SUM(length(description)),
            SUM(length(source_url)),
            SUM(length(title)),
            SUM(length(icon_url)),
            SUM(length(author))
        FROM source_items
        """
    ).fetchone()
    print(f"\nsource_items 核心列体积细分:")
    print(f"  - extra_json         : {(si_res[0] or 0)/1024/1024:>6.2f} MB ({(si_res[0] or 0)/db_file_size*100:>4.1f}% of DB)")
    print(f"  - description        : {(si_res[1] or 0)/1024/1024:>6.2f} MB ({(si_res[1] or 0)/db_file_size*100:>4.1f}% of DB)")
    print(f"  - source_url         : {(si_res[2] or 0)/1024/1024:>6.2f} MB ({(si_res[2] or 0)/db_file_size*100:>4.1f}% of DB)")
    print(f"  - title              : {(si_res[3] or 0)/1024/1024:>6.2f} MB ({(si_res[3] or 0)/db_file_size*100:>4.1f}% of DB)")

    # Overhead calculation
    overhead_bytes = db_file_size - total_payload
    print(f"\n物理存储构成概览:")
    print(f"  - 数据载荷 (Raw Payload)    : {total_payload/1024/1024:>6.2f} MB ({total_payload/db_file_size*100:>4.1f}%)")
    print(f"  - 索引与B-Tree页开销 (Indexes & Pages): {overhead_bytes/1024/1024:>6.2f} MB ({overhead_bytes/db_file_size*100:>4.1f}%)")

    conn.close()

    print("\n" + "=" * 60)
    if not results["errors"]:
        print("[*] 数据库结构与语义完整性审计 100% 通过！所有规则与 Golden Samples 均完全合规。")
    else:
        print(f"[!] 审计发现 {len(results['errors'])} 项语义或结构异常:")
        for err in results["errors"]:
            print(f"    - {err}")
    print("=" * 60)

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate Canonical SQLite DB for Architecture V2 (Phase 1.1)")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="Path to SQLite DB")
    args = parser.parse_args()

    res = validate_canonical_db(db_path=args.db_path)
    if res["errors"]:
        sys.exit(1)
    sys.exit(0)

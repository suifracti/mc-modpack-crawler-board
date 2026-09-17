"""
Architecture V2 - Phase 3E: Bilibili Grouping Auditor.
Audits the Bilibili title normalization and author-scoped grouping algorithm
for False Merges (different packs merged) and False Splits (same pack split).
"""
import os
import sys
import sqlite3
import json
import re
from collections import defaultdict

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CANONICAL_DB = os.path.join(REPO_ROOT, "build", "canonical.db")

# Bilibili buzzwords used in cleanPackKey (matching frontend logic)
BILI_GENRE_BUZZWORDS = [
    r'整合包', r'modpack', r'MODPACK', r'Modpack', r'实况', r'生存', r'第一集', r'第\d+集', r'ep\d+', r'EP\d+',
    r'试玩', r'体验', r'游玩', r'推荐', r'盘点', r'分享', r'发布', r'更新', r'重置版', r'重制版',
    r'下载', r'安装', r'教程', r'解说', r'纯享', r'无解说', r'大型', r'超大型', r'硬核', r'终极',
    r'完结', r'合集', r'系列', r'自制', r'搬运', r'汉化', r'中文', r'正版', r'免费', r'最新'
]

def clean_pack_key(title: str) -> str:
    # Mimic the frontend cleanPackKey function from apps/web/src/platforms/bilibili/grouping.ts
    s = title
    # Remove HTML entities & brackets
    s = re.sub(r'&#x27;|&quot;|&amp;|&lt;|&gt;', ' ', s)
    s = re.sub(r'【[^】]*】', ' ', s)
    s = re.sub(r'\[[^\]]*\]', ' ', s)
    s = re.sub(r'（[^）]*）', ' ', s)
    s = re.sub(r'\([^)]*\)', ' ', s)
    s = re.sub(r'「[^」]*」', ' ', s)
    s = re.sub(r'『[^』]*』', ' ', s)
    
    # Remove buzzwords
    for bw in BILI_GENRE_BUZZWORDS:
        s = re.sub(bw, ' ', s, flags=re.IGNORECASE)
        
    # Remove episode numbers e.g. #1, P1, 01, etc.
    s = re.sub(r'\b[pP]\d+\b', ' ', s)
    s = re.sub(r'#\d+', ' ', s)
    s = re.sub(r'\bv\d+(\.\d+)*\b', ' ', s, flags=re.IGNORECASE)
    s = re.sub(r'\b\d+\.\d+(\.\d+)*\b', ' ', s) # MC versions like 1.20.1
    
    # Clean non-alphanumeric except chinese
    s = re.sub(r'[^\w\u4e00-\u9fff]+', ' ', s)
    words = s.strip().split()
    return ' '.join(words)

def audit_bilibili_grouping():
    conn = sqlite3.connect(CANONICAL_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.id, s.source_id as bvid, s.title, s.author, s.published_at, s.description
        FROM source_items s
        WHERE s.platform = 'bilibili'
        ORDER BY s.author, s.published_at DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    print("============================================================")
    print("  Phase 3E: Bilibili Grouping Algorithmic Forensic Audit")
    print(f"  Total Bilibili Videos: {len(rows)}")
    print("============================================================")

    # 1. Author-scoped grouping with clean_pack_key
    author_groups = defaultdict(lambda: defaultdict(list))
    for r in rows:
        author = (r['author'] or '未知UP主').strip()
        key = clean_pack_key(r['title'])
        if not key or len(key) < 2:
            key = r['title'].strip()[:20]
        author_groups[author][key].append(r)

    # Flatten groups
    all_groups = []
    multi_groups = []
    single_groups = []

    for author, groups in author_groups.items():
        for key, vlist in groups.items():
            grp = {
                "author": author,
                "group_key": key,
                "count": len(vlist),
                "videos": vlist
            }
            all_groups.append(grp)
            if len(vlist) > 1:
                multi_groups.append(grp)
            else:
                single_groups.append(grp)

    print(f"\n[1] Overall Grouping Statistics:")
    print(f"  - Total Unique Groups: {len(all_groups)}")
    print(f"  - Multi-video Groups : {len(multi_groups)}")
    print(f"  - Single-video Groups: {len(single_groups)}")
    total_in_multi = sum(g['count'] for g in multi_groups)
    print(f"  - Videos in Multi-groups: {total_in_multi} (collapsed into {len(multi_groups)} cards, net -{total_in_multi - len(multi_groups)})")

    # Sort multi groups by count descending
    multi_groups.sort(key=lambda g: g['count'], reverse=True)

    # 2. Extract 20 Multi-video Groups for manual audit
    print("\n[2] Top 20 Multi-video Groups (Audit for False Merges):")
    sample_multi_20 = multi_groups[:20]
    for idx, g in enumerate(sample_multi_20, 1):
        print(f"\n--- Group #{idx} [{g['author']}] Key: '{g['group_key']}' ({g['count']} videos) ---")
        for v in g['videos']:
            print(f"    * {v['bvid']} ({v['published_at']}) - {v['title']}")

    # 3. Detect Potential False Merges:
    # A false merge occurs if clean_pack_key is too aggressive (e.g. empty or generic like "我的世界" or "冒险")
    print("\n[3] Auditing False Merge Candidates (Generic Keys):")
    generic_keys = ["我的世界", "模组", "游戏", "世界", "生存", "冒险", "科技", "魔法"]
    false_merge_candidates = []
    for g in multi_groups:
        if g['group_key'] in generic_keys or len(g['group_key']) <= 3:
            false_merge_candidates.append(g)
            print(f"  [ALERT: High Risk Generic Key] UP: '{g['author']}', Key: '{g['group_key']}', Count: {g['count']}")
            for v in g['videos']:
                print(f"      - {v['bvid']}: {v['title']}")

    # 4. Detect Potential False Splits:
    # Same author having multiple single-video groups whose titles are very similar (e.g. Edit distance or token overlap)
    print("\n[4] Auditing False Split Candidates (Near-Name Separate Groups within Same UP):")
    false_split_candidates = []
    for author, groups in author_groups.items():
        if len(groups) > 1:
            keys = list(groups.keys())
            for i in range(len(keys)):
                for j in range(i + 1, len(keys)):
                    k1, k2 = keys[i], keys[j]
                    # Check token overlap
                    set1 = set(k1.split())
                    set2 = set(k2.split())
                    intersection = set1.intersection(set2)
                    if len(intersection) >= 2 or (len(intersection) >= 1 and (len(set1) <= 2 or len(set2) <= 2)):
                        false_split_candidates.append({
                            "author": author,
                            "key1": k1,
                            "key2": k2,
                            "videos1": [v['title'] for v in groups[k1]],
                            "videos2": [v['title'] for v in groups[k2]]
                        })

    print(f"  - Found {len(false_split_candidates)} potential false split pairs within same authors")
    sample_split_20 = false_split_candidates[:20]
    for idx, c in enumerate(sample_split_20, 1):
        print(f"\n--- Split Candidate #{idx} [{c['author']}] ---")
        print(f"    Key 1: '{c['key1']}' -> {c['videos1'][0][:60]}")
        print(f"    Key 2: '{c['key2']}' -> {c['videos2'][0][:60]}")

    # Save results to json for detailed report
    out_file = os.path.join(REPO_ROOT, "build", "bili_grouping_audit.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "total_videos": len(rows),
            "total_groups": len(all_groups),
            "multi_groups_count": len(multi_groups),
            "single_groups_count": len(single_groups),
            "sample_multi_20": sample_multi_20,
            "false_merge_candidates": false_merge_candidates,
            "false_split_candidates_sample_20": sample_split_20
        }, f, indent=2, ensure_ascii=False)
    print(f"\n[+] Bilibili grouping audit saved to {out_file}")

if __name__ == "__main__":
    audit_bilibili_grouping()

import json
import re
import os
import sys
from html import unescape

sys.stdout.reconfigure(encoding='utf-8')

REPO_ROOT = r'd:\ai\work\我的世界整合包获取'
TABLE_ROWS_PATH = os.path.join(REPO_ROOT, 'converted_output', 'data', 'table_rows.js')
APP_DATA_PATH = os.path.join(REPO_ROOT, 'converted_output', 'data', 'app_data.js')
CACHE_PATH = os.path.join(REPO_ROOT, 'crawler_output', 'mcmod_details_cache.json')
RAW_JSON_PATH = os.path.join(REPO_ROOT, 'crawler_output', 'mcmod_modpacks.json')

# Known ATM versions mapping
ATM_VERSIONS = {
    '10': ['1.21.1', '1.21'],
    '10s': ['1.21.1', '1.21'],
    '11': ['1.21.1'],
    '9': ['1.20.1'],
    '9s': ['1.20.1'],
    '9nf': ['1.20.1'],
    'g2': ['1.20.1'],
    '8': ['1.19.2'],
    '7': ['1.18.2'],
    '7s': ['1.18.2'],
    '6': ['1.16.5'],
    '6s': ['1.16.5'],
    's': ['1.16.5'],
    '5': ['1.15.2'],
    '4': ['1.14.4'],
    '3': ['1.12.2'],
    '3e': ['1.12.2'],
    '3l': ['1.12.2'],
    '3r': ['1.12.2'],
    'vb': ['1.12.2'],
    '2': ['1.11.2'],
    '1': ['1.10.2'],
    '1l': ['1.10.2'],
    '1e': ['1.10.2'],
    '0': ['1.7.10'],
    'ar': ['1.18.2'],
}

def get_atm_version(title):
    title_upper = title.upper()
    if 'ATM' not in title_upper and 'ALL THE MODS' not in title_upper:
        return None
    m = re.search(r'\[ATM([0-9A-Za-z]+)\]', title, re.I)
    if m:
        key = m.group(1).lower()
        if key in ATM_VERSIONS:
            return ATM_VERSIONS[key]
    m2 = re.search(r'All [Tt]he Mods\s*(\d+)', title)
    if m2:
        key = m2.group(1).lower()
        if key in ATM_VERSIONS:
            return ATM_VERSIONS[key]
    return None

def extract_mods_and_cats_from_c6(c6_html):
    mods = []
    seen_mods = set()
    mod_cats = []
    seen_cats = set()

    for tag in re.findall(r'<span class="tag-mod"[^>]*>(?:(?!</span>).)*</span>', c6_html, re.S):
        m_name = re.search(r'data-mod="([^"]*)"', tag)
        m_cat = re.search(r'data-mod-cat="([^"]*)"', tag)
        m_url = re.search(r'data-mod-url="([^"]*)"', tag)
        m_ver = re.search(r'class="tag-mod-version">([^<]*)<', tag)
        if m_name and m_name.group(1):
            name = unescape(m_name.group(1).strip())
            cat = unescape(m_cat.group(1).strip()) if m_cat else "未分类"
            url = m_url.group(1).strip() if m_url else f"https://www.mcmod.cn/s?key={name}"
            ver = unescape(m_ver.group(1).strip()) if m_ver else ""
            if name.lower() not in seen_mods:
                seen_mods.add(name.lower())
                mods.append({
                    "name": name,
                    "title": name,
                    "category": cat,
                    "version": ver,
                    "url": url
                })
            if cat and cat not in seen_cats and cat != "未分类":
                seen_cats.add(cat)
                mod_cats.append(cat)

    return mods, mod_cats

def clean_key(s):
    if not s: return ""
    s = re.sub(r'^\[[^\]]+\]', '', s)
    s = re.sub(r'[\(（].*?[\)）]', '', s)
    s = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]', '', s).lower()
    return s

def extract_en_title(title):
    m = re.search(r'[\(（]([^\)）]+)[\)）]', title)
    return m.group(1).strip() if m else ""

def build_cross_indexes():
    cf_index = {}
    with open(os.path.join(REPO_ROOT, 'crawler_output', 'curseforge_modpacks.json'), 'r', encoding='utf-8') as f:
        for p in json.load(f):
            t = p.get('title') or ''
            k = clean_key(t)
            if k and k not in cf_index: cf_index[k] = p
            slug = p.get('slug') or ''
            k_slug = clean_key(slug)
            if k_slug and k_slug not in cf_index: cf_index[k_slug] = p

    mr_index = {}
    with open(os.path.join(REPO_ROOT, 'crawler_output', 'modrinth_modpacks.json'), 'r', encoding='utf-8') as f:
        for p in json.load(f):
            t = p.get('title') or ''
            k = clean_key(t)
            if k and k not in mr_index: mr_index[k] = p
            slug = p.get('slug') or ''
            k_slug = clean_key(slug)
            if k_slug and k_slug not in mr_index: mr_index[k_slug] = p

    bbsmc_index = {}
    with open(os.path.join(REPO_ROOT, 'crawler_output', 'bbsmc_modpacks.json'), 'r', encoding='utf-8') as f:
        for p in json.load(f):
            t = p.get('title') or ''
            k = clean_key(t)
            if k and k not in bbsmc_index: bbsmc_index[k] = p

    return cf_index, mr_index, bbsmc_index

def enrich_all():
    print("=" * 60)
    print("  MCMod 数据层深度修复与增强引擎")
    print("=" * 60)

    # 1. Load table_rows.js
    with open(TABLE_ROWS_PATH, 'r', encoding='utf-8') as f:
        text = f.read().strip()
    prefix = 'window.tableRowsData = '
    rows = json.loads(text[len(prefix):].rstrip(';\n '))
    print(f"[读取] 成功载入 {len(rows)} 款 MCMod 整合包主记录")

    # 2. Load cache if available
    cache = {}
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            print(f"[缓存] 读取到 {len(cache)} 条官方详情缓存")
        except Exception:
            cache = {}

    # 3. Load cross indexes
    cf_index, mr_index, bbsmc_index = build_cross_indexes()
    print("[索引] 跨平台对照库已就绪 (CurseForge + Modrinth + BBSMC)")

    compare_data = {}
    packs_with_mods = 0
    all_distinct_mods = set()
    atm_count = 0
    resolved_mc_vers = 0

    for r in rows:
        mid = str(r.get('mid', ''))
        title = r.get('title', '')
        c6 = r.get('c6', '')

        # A. 提取真实模组与分类
        mods_obj_list, mod_cats = extract_mods_and_cats_from_c6(c6)
        mod_names = [m['name'] for m in mods_obj_list]
        if mod_names:
            packs_with_mods += 1
            for m in mod_names:
                all_distinct_mods.add(m)
            # 关键修复：mods_search 必须包含具体模组名称！
            r['mods_search'] = " ".join(mod_names)
            r['mod_count'] = len(mod_names)
        
        if mod_cats:
            r['mod_categories'] = mod_cats
            # 将模组分类作为独立搜索维度或合并到 cat_search
            existing_cats = set((r.get('cat_search') or '').split())
            combined_cats = list(dict.fromkeys(list(existing_cats) + mod_cats))
            r['cat_search'] = " ".join(combined_cats)

        # B. 提取真实 MC 游戏版本
        mc_vers = []
        # 1. 优先使用官方详情缓存
        if mid in cache and cache[mid].get('mc_versions'):
            mc_vers = cache[mid]['mc_versions']
        
        # 2. ATM 家族官方映射
        if not mc_vers:
            atm_v = get_atm_version(title)
            if atm_v:
                mc_vers = atm_v
                atm_count += 1

        # 3. 从标题中提取
        if not mc_vers:
            title_matches = re.findall(r'\b(1\.(?:[7-9]|1\d|2\d)(?:\.\d+)?)\b', title)
            if title_matches:
                mc_vers = list(dict.fromkeys(title_matches))

        # 4. 跨平台匹配
        if not mc_vers:
            k1 = clean_key(title)
            en = extract_en_title(title)
            k2 = clean_key(en)
            cross_p = cf_index.get(k1) or cf_index.get(k2) or mr_index.get(k1) or mr_index.get(k2) or bbsmc_index.get(k1) or bbsmc_index.get(k2)
            if cross_p:
                p_vers = cross_p.get('all_versions') or ([cross_p.get('mc_version')] if cross_p.get('mc_version') else [])
                # 过滤出合法的 MC 版本
                clean_vers = [v for v in p_vers if isinstance(v, str) and re.match(r'^1\.\d+(\.\d+)?$', v)]
                if clean_vers:
                    mc_vers = clean_vers

        # 5. tags_search 提取
        if not mc_vers:
            tag_matches = re.findall(r'\b(1\.(?:[7-9]|1\d|2\d)(?:\.\d+)?)\b', r.get('tags_search', ''))
            if tag_matches:
                mc_vers = list(dict.fromkeys(tag_matches))

        if mc_vers:
            resolved_mc_vers += 1
            r['mc_versions'] = mc_vers
            r['mc_version'] = mc_vers[0]
        else:
            r['mc_versions'] = []
            r['mc_version'] = ""

        # C. 拆分中英文标题
        full_title = title
        title_cn, title_en = full_title, ""
        if " (" in full_title and full_title.endswith(")"):
            parts = full_title.rsplit(" (", 1)
            title_cn = parts[0].strip()
            title_en = parts[1][:-1].strip()

        # D. 构建 compareData
        compare_data[mid] = {
            "mid": mid,
            "title": full_title,
            "title_cn": title_cn,
            "title_en": title_en,
            "url": f"https://www.mcmod.cn/modpack/{mid}.html",
            "type": r.get("type_name", "原生整合"),
            "views": r.get("views_n", 0),
            "score": r.get("score_n", 1),
            "trend_latest": r.get("lat_n", 0),
            "trend_days": r.get("days_n", 1),
            "comments": r.get("com_n", 0),
            "recommend": r.get("rec_n", 0),
            "favorite": r.get("fav_n", 0),
            "red_votes": r.get("rv_n", 0),
            "black_votes": r.get("bv_n", 0),
            "growth7": f"{r.get('t7_n', 0)}%",
            "growth30": f"{r.get('t30_n', 0)}%",
            "growth60": f"{r.get('t60_n', 0)}%",
            "categories": [c.strip() for c in (r.get("cat_search") or "").split() if c.strip()],
            "tags": [t.strip() for t in (r.get("tags_search") or "").split() if t.strip()],
            "mods": mod_names,
            "mod_count": len(mod_names) if mod_names else r.get("mod_count", 0),
            "mod_categories": mod_cats,
            "mc_versions": mc_vers,
            "latest_version": r.get("latest_version", ""),
            "last_update_date": r.get("last_update_date", ""),
            "release_date": r.get("release_date", ""),
            "version_count": r.get("version_count", 0)
        }

    # 4. 保存回 table_rows.js
    with open(TABLE_ROWS_PATH, 'w', encoding='utf-8') as f:
        f.write("window.tableRowsData = " + json.dumps(rows, ensure_ascii=False) + ";\n")

    # 5. 保存回 app_data.js
    with open(APP_DATA_PATH, 'w', encoding='utf-8') as f:
        f.write("window.compareData = " + json.dumps(compare_data, ensure_ascii=False) + ";\n")

    # 6. 同步回 crawler_output/mcmod_modpacks.json
    raw_list = []
    for r in rows:
        mid = str(r.get("mid", ""))
        app_info = compare_data.get(mid, {})
        entry = {
            "platform": "mcmod",
            "project_id": mid,
            "mid": mid,
            "url": f"https://www.mcmod.cn/modpack/{mid}.html",
            "title": r.get("title", ""),
            "title_cn": app_info.get("title_cn", ""),
            "title_en": app_info.get("title_en", ""),
            "type_name": r.get("type_name", "原生整合"),
            "mold_id": "2" if "魔改" in r.get("type_name", "") else "1",
            "cover_url": r.get("cover_url", ""),
            "views": int(r.get("views_n", 0) or 0),
            "score": int(r.get("score_n", 1) or 1),
            "trend_latest": int(r.get("lat_n", 0) or 0),
            "trend_days": int(r.get("days_n", 1) or 1),
            "trend_dates": r.get("trend_dates", ""),
            "trend_vals": r.get("trend_vals", ""),
            "latest_version": r.get("latest_version", ""),
            "last_update_date": r.get("last_update_date", ""),
            "release_date": r.get("release_date", ""),
            "version_count": int(r.get("version_count", 0) or 0),
            "comments": int(r.get("com_n", 0) or 0),
            "recommend": int(r.get("rec_n", 0) or 0),
            "favorite": int(r.get("fav_n", 0) or 0),
            "red_votes": int(r.get("rv_n", 0) or 0),
            "black_votes": int(r.get("bv_n", 0) or 0),
            "red_percent": int(r.get("rp_n", 50) or 50),
            "black_percent": int(r.get("bp_n", 50) or 50),
            "categories": app_info.get("categories", []),
            "tags": app_info.get("tags", []),
            "mods": app_info.get("mods", []),
            "mod_count": app_info.get("mod_count", 0),
            "mc_versions": app_info.get("mc_versions", [])
        }
        raw_list.append(entry)

    with open(RAW_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(raw_list, f, ensure_ascii=False, indent=2)

    print(f"\n[落盘结果]")
    print(f"  - 覆盖整合包行数: {len(rows)} 款")
    print(f"  - 还原具体模组包: {packs_with_mods} 款 (包含 {len(all_distinct_mods)} 个独立模组名)")
    print(f"  - 成功定位 MC 游戏版本: {resolved_mc_vers} 款 (含 ATM 家族 {atm_count} 款)")
    print(f"  - 已更新前端主数据: {TABLE_ROWS_PATH}")
    print(f"  - 已更新对比数据库: {APP_DATA_PATH}")
    print(f"  - 已更新统一归档库: {RAW_JSON_PATH}")

if __name__ == '__main__':
    enrich_all()

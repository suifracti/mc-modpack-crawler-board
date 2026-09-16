import os
import sys
import json
import re

sys.stdout.reconfigure(encoding='utf-8')

REPO_ROOT = r'd:\ai\work\我的世界整合包获取'
MCMOD_FULL_DETAILS = os.path.join(REPO_ROOT, 'crawler_output', 'mcmod_full_details.json')
MCMOD_PACKS_JSON = os.path.join(REPO_ROOT, 'crawler_output', 'mcmod_modpacks.json')
MCMOD_CACHE_JSON = os.path.join(REPO_ROOT, 'crawler_output', 'mcmod_details_cache.json')
DESC_DATA_JS = os.path.join(REPO_ROOT, 'converted_output', 'data', 'desc_data.js')
APP_DATA_JS = os.path.join(REPO_ROOT, 'converted_output', 'data', 'app_data.js')
TABLE_ROWS_JS = os.path.join(REPO_ROOT, 'converted_output', 'data', 'table_rows.js')
MODS_DIR = os.path.join(REPO_ROOT, 'converted_output', 'data', 'mods')

def esc(s):
    if not s:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def esc_attr(s):
    if not s:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")

def build_c6_html(det):
    groups = det.get("category_groups", [])
    total_mods = det.get("mod_count", 0)
    if not groups or total_mods == 0:
        return '<span class="tag-empty">—</span>'

    mod_summary_chips = []
    mod_sections = []
    preview_limit = 8
    preview_used = 0
    hidden_mod_count = 0

    for g_idx, g in enumerate(groups):
        g_name = g.get("name", "未分类")
        g_url = g.get("url", "")
        g_mods = g.get("mods", [])
        g_key = f"cat{g_idx}"

        mod_summary_chips.append(
            f'<button type="button" class="mod-summary-chip" data-mod-cat-key="{g_key}" title="跳到 {esc_attr(g_name)} 分类">{esc(g_name)}<b>{len(g_mods)}</b></button>'
        )

        links = []
        for m in g_mods:
            name = m.get("name") or m.get("title") or ""
            if not name:
                continue
            if preview_used >= preview_limit:
                hidden_mod_count += 1
                continue
            preview_used += 1

            version = m.get("version", "")
            title_bits = [m.get("title") or name]
            if version:
                title_bits.append(f"版本: {version}")
            if m.get("category_name"):
                title_bits.append(f"分类: {m['category_name']}")
            version_html = f'<span class="tag-mod-version">{esc(version)}</span>' if version else ''

            links.append(
                f'<span class="tag-mod" role="button" tabindex="0" title="{esc_attr(" · ".join(title_bits))}" data-mod="{esc_attr(name)}" data-mod-cat="{esc_attr(m.get("category_name", ""))}" data-mod-url="{esc_attr(m.get("url") or "#")}"><span class="tag-mod-name">{esc(name)}</span>{version_html}<a class="tag-mod-open" href="{esc_attr(m.get("url") or "#")}" target="_blank" title="打开 MC百科模组页">↗</a></span>'
            )

        cat_head = f'<a class="mod-category-link" href="{esc_attr(g_url)}" target="_blank">{esc(g_name)}</a>' if g_url else f'<span>{esc(g_name)}</span>'
        if links:
            mod_sections.append(
                f'<section class="mod-category-section" data-mod-cat-key="{g_key}"><div class="mod-category-head">{cat_head}<span>{len(g_mods)}</span></div><div class="mod-grid">{"".join(links)}</div></section>'
            )

    more_html = f'<div class="tag-empty">折叠状态精选预览前 {preview_limit} 个模组；展开抽屉或点击分类可查看全部 {total_mods} 款收录模组。</div>' if hidden_mod_count > 0 else ''

    return (
        f'<div class="tag-wrap mod-container">'
        f'<details class="mod-details">'
        f'<summary><span class="mod-summary-main">包含模组 <b>{total_mods}</b></span><span class="mod-summary-cats">{"".join(mod_summary_chips)}</span></summary>'
        f'<div class="mod-details-body">{"".join(mod_sections)}{more_html}<div class="mod-full-list" data-loaded="0"></div></div>'
        f'</details>'
        f'</div>'
    )

def sync_all():
    print("=== 开始同步 MCMod 丰富详情至各平台数据文件 ===")
    if not os.path.exists(MCMOD_FULL_DETAILS):
        print(f"错误: 找不到 {MCMOD_FULL_DETAILS}")
        return

    with open(MCMOD_FULL_DETAILS, 'r', encoding='utf-8') as f:
        details = json.load(f)
    print(f"[1/6] 读取爬虫详情: {len(details)} 条")

    # 1. 更新 mcmod_modpacks.json
    if os.path.exists(MCMOD_PACKS_JSON):
        with open(MCMOD_PACKS_JSON, 'r', encoding='utf-8') as f:
            packs = json.load(f)
        updated_packs = 0
        for p in packs:
            mid = str(p.get('mid'))
            if mid in details:
                d = details[mid]
                if d.get('intro_text'):
                    p['desc'] = d['intro_text']
                if d.get('intro_images'):
                    p['intro_images'] = d['intro_images']
                if d.get('tags'):
                    p['tags'] = d['tags']
                if d.get('mc_versions'):
                    p['mc_versions'] = d['mc_versions']
                p['mod_count'] = d.get('mod_count', len(d.get('mods', [])))
                p['mods'] = d.get('mods', [])
                p['mod_categories'] = [g['name'] for g in d.get('category_groups', [])]
                updated_packs += 1
        with open(MCMOD_PACKS_JSON, 'w', encoding='utf-8') as f:
            json.dump(packs, f, ensure_ascii=False, indent=2)
        print(f"[2/6] 更新 mcmod_modpacks.json: 成功同步 {updated_packs} 款")

    # 2. 更新 mcmod_details_cache.json
    cache = {}
    if os.path.exists(MCMOD_CACHE_JSON):
        try:
            with open(MCMOD_CACHE_JSON, 'r', encoding='utf-8') as f:
                cache = json.load(f)
        except Exception:
            cache = {}
    for mid, d in details.items():
        cache[str(mid)] = {
            "mid": str(mid),
            "text": d.get("intro_text", ""),
            "desc": d.get("intro_text", ""),
            "images": d.get("intro_images", []),
            "intro_images": d.get("intro_images", []),
            "mc_versions": d.get("mc_versions", []),
            "source": "mcmod"
        }
    with open(MCMOD_CACHE_JSON, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    print(f"[3/6] 更新 mcmod_details_cache.json: 共 {len(cache)} 条记录")

    # 3. 更新 desc_data.js
    if os.path.exists(DESC_DATA_JS):
        with open(DESC_DATA_JS, 'w', encoding='utf-8', errors='replace') as f:
            f.write("window.descData = " + json.dumps(cache, ensure_ascii=False) + ";\n")
        print(f"[4/6] 更新 desc_data.js: 共 {len(cache)} 条记录")

    # 4. 更新 app_data.js
    if os.path.exists(APP_DATA_JS):
        with open(APP_DATA_JS, 'r', encoding='utf-8') as f:
            raw_app = f.read().strip()
        prefix = 'window.compareData = '
        if raw_app.startswith(prefix):
            app_data = json.loads(raw_app[len(prefix):].rstrip(';\n '))
            updated_app = 0
            for mid, d in details.items():
                if mid in app_data:
                    # 获取唯一模组名称列表
                    mod_names = []
                    seen_m = set()
                    for m in d.get("mods", []):
                        name = m.get("name") or m.get("title") or ""
                        if name and name.lower() not in seen_m:
                            seen_m.add(name.lower())
                            mod_names.append(name)
                    app_data[mid]['mods'] = mod_names
                    app_data[mid]['mod_categories'] = [g['name'] for g in d.get('category_groups', [])]
                    app_data[mid]['mod_count'] = d.get('mod_count', len(mod_names))
                    if d.get('tags'):
                        app_data[mid]['tags'] = d['tags']
                    if d.get('intro_text'):
                        app_data[mid]['desc'] = d['intro_text']
                    updated_app += 1
            with open(APP_DATA_JS, 'w', encoding='utf-8', errors='replace') as f:
                f.write(prefix + json.dumps(app_data, ensure_ascii=False, separators=(',', ':')) + ";\n")
            print(f"[5/6] 更新 app_data.js: 成功更新 {updated_app} 款")

    # 5. 生成/覆盖 converted_output/data/mods/{mid}.js 侧边分包
    os.makedirs(MODS_DIR, exist_ok=True)
    sidecars_written = 0
    for mid, d in details.items():
        payload = []
        for g_idx, g in enumerate(d.get("category_groups", [])):
            mod_items = []
            for m in g.get("mods", []):
                name = m.get("name") or m.get("title") or ""
                if not name:
                    continue
                version = m.get("version", "")
                url = m.get("url", "")
                title = m.get("title") or name
                mod_items.append([name, version, url, title])
            payload.append({
                "k": f"cat{g_idx}",
                "n": g.get("name", "未分类"),
                "u": g.get("url", ""),
                "m": mod_items
            })
        body = f'window.__registerModDetailData({json.dumps(str(mid))},{json.dumps(payload, ensure_ascii=False, separators=(",", ":"))});\n'
        with open(os.path.join(MODS_DIR, f"{mid}.js"), "w", encoding="utf-8", errors="replace") as f:
            f.write(body)
        sidecars_written += 1
    print(f"[6/6] 生成 data/mods/*.js 模组分包: 写入 {sidecars_written} 个文件")

    # 6. 更新 table_rows.js
    if os.path.exists(TABLE_ROWS_JS):
        with open(TABLE_ROWS_JS, 'r', encoding='utf-8') as f:
            raw_rows = f.read().strip()
        r_prefix = 'window.tableRowsData = '
        if raw_rows.startswith(r_prefix):
            rows = json.loads(raw_rows[len(r_prefix):].rstrip(';\n '))
            updated_rows = 0
            for r in rows:
                mid = str(r.get('mid'))
                if mid in details:
                    d = details[mid]
                    # 更新 mods_search
                    mod_words = []
                    for m in d.get('mods', []):
                        name = m.get('name') or m.get('title') or ''
                        if name:
                            mod_words.append(name)
                        if m.get('category_name'):
                            mod_words.append(m['category_name'])
                    r['mods_search'] = " ".join(dict.fromkeys(mod_words))
                    # 更新 c6
                    r['c6'] = build_c6_html(d)
                    updated_rows += 1
            with open(TABLE_ROWS_JS, 'w', encoding='utf-8', errors='replace') as f:
                f.write(r_prefix + json.dumps(rows, ensure_ascii=False, separators=(',', ':')) + ";\n")
            print(f"[完成] 更新 table_rows.js: 成功更新 {updated_rows} 行")

if __name__ == '__main__':
    sync_all()

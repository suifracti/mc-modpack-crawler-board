# -*- coding: utf-8 -*-
import json
import os
import re

TABLE_ROWS_PATH = os.path.join("converted_output", "data", "table_rows.js")
APP_DATA_PATH = os.path.join("converted_output", "data", "app_data.js")

with open(TABLE_ROWS_PATH, "r", encoding="utf-8") as f:
    text = f.read()

prefix = "window.tableRowsData = "
rows = json.loads(text[len(prefix):].rstrip(";\n "))

compare_data = {}
for r in rows:
    mid = str(r.get("mid", ""))
    if not mid:
        continue
    full_title = r.get("title", f"Modpack {mid}")
    title_cn, title_en = full_title, ""
    if " (" in full_title and full_title.endswith(")"):
        parts = full_title.rsplit(" (", 1)
        title_cn = parts[0].strip()
        title_en = parts[1][:-1].strip()

    cats = [c.strip() for c in (r.get("cat_search") or "").split() if c.strip()]
    mods = [m.strip() for m in (r.get("mods_search") or "").split() if m.strip()]

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
        "categories": cats,
        "tags": [t.strip() for t in (r.get("tags_search") or "").split() if t.strip()],
        "mods": mods,
        "mod_count": r.get("mod_count", len(mods)),
        "mc_versions": []
    }

with open(APP_DATA_PATH, "w", encoding="utf-8") as f:
    f.write("window.compareData = " + json.dumps(compare_data, ensure_ascii=False) + ";\n")

print(f"[OK] 成功同步 {len(compare_data)} 款完整模组对比映射到 {APP_DATA_PATH}！")

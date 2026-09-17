"""
Architecture V2 — Phase 3B: Structured MCMod Exporter.
Exports pure structured JSONP sidecar (data/mcmod_data.js) strictly from build/canonical.db.
STRICT RULES:
1. Only read from canonical SQLite (no crawler_output, no table_rows.js).
2. ZERO pre-rendered HTML (no <div, <span, <svg, <button, onclick=).
3. Full environment claims evidence.
"""
import os
import sys
import json
import sqlite3
from typing import Dict, Any, List, Tuple, Optional

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from pipeline.exporters.legacy.mcmod_renderer import compute_trend_stats

class StructuredMCModExporter:
    def __init__(self, db_path: str, output_dir: str):
        self.db_path = db_path
        self.output_dir = output_dir

    def export(self) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            # 1. Fetch items and metrics
            items_cur = conn.execute("""
                SELECT 
                    si.id, si.source_id, si.title, si.author, si.description, si.icon_url,
                    si.published_at, si.modified_at, si.extra_json,
                    m.views, m.score, m.trend_latest, m.trend_days, m.comments_count,
                    m.likes, m.favorites, m.red_votes, m.black_votes
                FROM source_items si
                LEFT JOIN metrics m ON si.id = m.source_item_id
                WHERE si.platform = 'mcmod'
                ORDER BY CAST(si.source_id AS INTEGER) ASC
            """)
            items = items_cur.fetchall()

            # 2. Fetch categories
            cats_cur = conn.execute("""
                SELECT sc.source_item_id, c.name
                FROM source_item_categories sc
                JOIN categories c ON sc.category_id = c.id
                WHERE c.platform = 'mcmod'
            """)
            cats_map: Dict[str, List[str]] = {}
            for row in cats_cur.fetchall():
                cats_map.setdefault(row["source_item_id"], []).append(row["name"])

            # 3. Fetch MC versions
            mc_cur = conn.execute("""
                SELECT r.source_item_id, rm.mc_version
                FROM releases r
                JOIN release_mc_versions rm ON r.id = rm.release_id
                WHERE r.source_item_id LIKE 'mcmod:%'
                ORDER BY rm.is_primary DESC, rm.id ASC
            """)
            mc_map: Dict[str, List[str]] = {}
            for row in mc_cur.fetchall():
                v = row["mc_version"].strip()
                if v and v not in mc_map.setdefault(row["source_item_id"], []):
                    mc_map[row["source_item_id"]].append(v)

            # 4. Fetch aliases (former titles)
            alias_cur = conn.execute("""
                SELECT si.id, a.alias_text
                FROM aliases a
                JOIN packs p ON a.pack_id = p.id
                JOIN source_items si ON p.id = si.pack_id
                WHERE si.platform = 'mcmod' AND a.alias_type = 'former_title'
            """)
            former_map: Dict[str, List[str]] = {}
            for row in alias_cur.fetchall():
                former_map.setdefault(row["id"], []).append(row["alias_text"])

            # 5. Fetch included mods
            mods_cur = conn.execute("""
                SELECT source_item_id, mod_name, mod_title, mod_version, mod_url, class_id,
                       category_id, category_name, category_url, sort_order
                FROM included_mods
                WHERE source_item_id LIKE 'mcmod:%'
                ORDER BY source_item_id, sort_order, id
            """)
            mods_map: Dict[str, List[Dict[str, Any]]] = {}
            for row in mods_cur.fetchall():
                mods_map.setdefault(row["source_item_id"], []).append({
                    "name": row["mod_name"],
                    "title": row["mod_title"] or row["mod_name"],
                    "version": row["mod_version"] or "",
                    "url": row["mod_url"] or (f"https://www.mcmod.cn/class/{row['class_id']}.html" if row["class_id"] else "#"),
                    "class_id": str(row["class_id"]) if row["class_id"] else None,
                    "category_id": str(row["category_id"] or "1"),
                    "category_name": row["category_name"] or "未分类",
                    "category_url": row["category_url"] or "",
                })

            # 6. Fetch trend points
            trend_cur = conn.execute("""
                SELECT source_item_id, point_date, views_delta
                FROM trend_points
                WHERE source_item_id LIKE 'mcmod:%'
                ORDER BY source_item_id, point_date ASC
            """)
            trend_map: Dict[str, List[Tuple[str, float]]] = {}
            for row in trend_cur.fetchall():
                trend_map.setdefault(row["source_item_id"], []).append((row["point_date"], float(row["views_delta"])))

            # 7. Fetch environment claims (both client and server)
            claims_cur = conn.execute("""
                SELECT source_item_id, side, status, certainty, evidence_type, evidence_text, source_field, raw_value
                FROM environment_claims
                WHERE source_item_id LIKE 'mcmod:%'
                ORDER BY source_item_id, side ASC
            """)
            claims_map: Dict[str, List[Dict[str, Any]]] = {}
            for row in claims_cur.fetchall():
                claims_map.setdefault(row["source_item_id"], []).append({
                    "side": row["side"],
                    "status": row["status"],
                    "certainty": row["certainty"],
                    "evidenceType": row["evidence_type"],
                    "evidenceText": row["evidence_text"],
                    "sourceField": row["source_field"],
                    "rawValue": row["raw_value"],
                })

            structured_packs = []

            for it in items:
                si_id = it["id"]
                mid = int(it["source_id"])
                full_title = it["title"] or f"Modpack {mid}"
                author = it["author"] or "未知"
                cover_url = it["icon_url"] or ""
                pub_at = it["published_at"] or ""
                mod_at = it["modified_at"] or ""
                description = it["description"] or ""

                # Parse extra_json
                extra = json.loads(it["extra_json"] or "{}")
                type_name = extra.get("type_name") or "原生整合"
                mold_id = str(extra.get("mold_id") or ("2" if "魔改" in type_name else "1"))

                # Metrics
                views_n = int(it["views"] or 0)
                com_n = int(it["comments_count"] or 0)
                rec_n = int(it["likes"] or extra.get("recommend") or 0)
                fav_n = int(it["favorites"] or extra.get("favorite") or 0)
                rv_n = int(it["red_votes"] or 0)
                bv_n = int(it["black_votes"] or 0)
                tot_v = rv_n + bv_n
                rp_n = round((rv_n / tot_v) * 100) if tot_v > 0 else 50
                bp_n = 100 - rp_n if tot_v > 0 else 50

                # Categories & tags
                cats = cats_map.get(si_id, [])
                mc_vers = mc_map.get(si_id, [])
                former_titles = former_map.get(si_id, [])

                # Split titles
                title_cn, title_en = full_title, ""
                if " (" in full_title and full_title.endswith(")"):
                    parts = full_title.rsplit(" (", 1)
                    title_cn = parts[0].strip()
                    title_en = parts[1][:-1].strip()

                # Trend stats
                t_points = trend_map.get(si_id, [])
                if not t_points:
                    t_points = [("2026-09-17", float(it["trend_latest"] or 0))]
                lat_n, max_n, avg_n, days_n, t7_n, t30_n, t60_n, tall_n = compute_trend_stats(t_points)
                # SCORE-MCMOD-01 Remediation: Do NOT synthesize star rating from daily views.
                score_raw = it["score"]
                score_n = int(score_raw) if score_raw is not None and score_raw > 0 else None
                trend_dates_str = ",".join(p[0] for p in t_points)
                trend_vals_str = ",".join(f"{p[1]:.1f}" if p[1] != int(p[1]) else str(int(p[1])) for p in t_points)

                trend_points_list = [{"date": p[0], "viewsDelta": p[1]} for p in t_points]

                # Group included mods by category & build preview
                pack_mods = mods_map.get(si_id, [])
                all_mod_names = [m["name"] for m in pack_mods if m.get("name")]
                all_mod_cats = []
                seen_cat = set()
                category_counts = {}
                category_urls = {}
                category_order = []

                for m in pack_mods:
                    c_name = m.get("category_name") or "未分类"
                    if c_name not in category_counts:
                        category_counts[c_name] = 0
                        category_urls[c_name] = m.get("category_url") or ""
                        category_order.append(c_name)
                    category_counts[c_name] += 1
                    if c_name not in seen_cat:
                        seen_cat.add(c_name)
                        all_mod_cats.append(c_name)

                mod_categories = []
                cat_key_map = {}
                for idx, c_name in enumerate(category_order):
                    k = f"cat{idx}"
                    cat_key_map[c_name] = k
                    mod_categories.append({
                        "categoryKey": k,
                        "categoryName": c_name,
                        "categoryUrl": category_urls.get(c_name, ""),
                        "count": category_counts[c_name],
                    })

                # Preview up to 8 mods for the initial cell
                preview_mods = []
                for m in pack_mods[:8]:
                    c_name = m.get("category_name") or "未分类"
                    preview_mods.append({
                        "name": m["name"],
                        "title": m["title"],
                        "version": m["version"],
                        "url": m["url"],
                        "classId": m["class_id"],
                        "categoryKey": cat_key_map.get(c_name, "cat0"),
                        "categoryName": c_name,
                    })

                # Environment claims
                env_claims = claims_map.get(si_id, [
                    {
                        "side": "client",
                        "status": "unknown",
                        "certainty": "unknown",
                        "evidenceType": "no_evidence",
                        "evidenceText": None,
                        "sourceField": None,
                        "rawValue": None,
                    },
                    {
                        "side": "server",
                        "status": "unknown",
                        "certainty": "unknown",
                        "evidenceType": "no_evidence",
                        "evidenceText": None,
                        "sourceField": None,
                        "rawValue": None,
                    }
                ])

                structured_pack = {
                    "mid": mid,
                    "title": full_title,
                    "chineseName": title_cn,
                    "englishName": title_en,
                    "formerTitles": former_titles,
                    "url": f"https://www.mcmod.cn/modpack/{mid}.html",
                    "author": author,
                    "typeName": type_name,
                    "moldId": mold_id,
                    "coverUrl": cover_url,
                    "views": views_n,
                    "score": score_n,
                    "recommendations": rec_n,
                    "favorites": fav_n,
                    "commentsCount": com_n,
                    "votes": {
                        "redVotes": rv_n,
                        "blackVotes": bv_n,
                        "redPercent": rp_n,
                        "blackPercent": bp_n,
                    },
                    "trendStats": {
                        "lat": lat_n,
                        "max": max_n,
                        "avg": avg_n,
                        "days": days_n,
                        "t7": t7_n,
                        "t30": t30_n,
                        "t60": t60_n,
                        "tall": tall_n,
                        "score": score_n,
                        "history7d": [float(v) for _, v in t_points[-7:]] if t_points else [],
                        "trendValsStr": trend_vals_str,
                        "trendDatesStr": trend_dates_str,
                    },
                    "tags": [],
                    "categories": cats,
                    "mcVersions": mc_vers,
                    "loaders": [],
                    "includedModsCount": len(pack_mods),
                    "has_server": any(c["side"] == "server" and c["status"] in ("supported", "required", "optional") for c in env_claims),
                    "name_order": full_title.lower(),
                    "cat_search": ", ".join(cats),
                    "pack_search": "",
                    "mod_cat_search": ", ".join(all_mod_cats),
                    "modCategories": mod_categories,
                    "previewMods": preview_mods,
                    "modSearchText": ", ".join(all_mod_names),
                    "modCategorySearch": ", ".join(all_mod_cats),
                    "environmentClaims": env_claims,
                    "publishedAt": pub_at,
                    "modifiedAt": mod_at,
                }
                structured_packs.append(structured_pack)

            os.makedirs(self.output_dir, exist_ok=True)
            output_file = os.path.join(self.output_dir, "mcmod_data.js")
            json_str = json.dumps(structured_packs, ensure_ascii=False, separators=(',', ':'))
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"window.mcmodData = {json_str};\n")

            size_bytes = os.path.getsize(output_file)
            print(f"[+] Exported {len(structured_packs)} structured MCMod records to {output_file} ({size_bytes / 1024:.1f} KB)")

            # Export full history to a separate lazy sidecar for on-demand details
            trends_file = os.path.join(self.output_dir, "mcmod_trends.js")
            all_trends = {
                int(k.split(":", 1)[1]): [{"date": d, "viewsDelta": v} for d, v in pts]
                for k, pts in trend_map.items() if k.startswith("mcmod:")
            }
            with open(trends_file, "w", encoding="utf-8") as f:
                f.write(f"window.mcmodTrendsData = {json.dumps(all_trends, ensure_ascii=False, separators=(',', ':'))};\n")
            trends_size = os.path.getsize(trends_file)
            print(f"[+] Exported separate lazy full trend history to {trends_file} ({trends_size / 1024:.1f} KB)")

            return {
                "count": len(structured_packs),
                "output_file": output_file,
                "size_bytes": size_bytes,
                "trends_file": trends_file,
                "trends_size_bytes": trends_size,
            }
        finally:
            conn.close()

if __name__ == "__main__":
    db = os.path.join(REPO_ROOT, "build", "canonical.db")
    out = os.path.join(REPO_ROOT, "build", "frontend_preview", "data")
    exporter = StructuredMCModExporter(db, out)
    res = exporter.export()
    print("Done:", res)

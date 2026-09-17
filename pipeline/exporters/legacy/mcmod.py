"""
MCMod Legacy Exporter for Architecture V2.
Exports table_rows.js, app_data.js, desc_data.js, mods/*.js, and comments/*.js
strictly from build/canonical.db.
"""
import os
import json
import sqlite3
from typing import Dict, Any, List, Optional, Tuple
from pipeline.exporters.legacy.base import BaseLegacyExporter
from pipeline.exporters.legacy import mcmod_renderer as renderer

class MCModExporter(BaseLegacyExporter):
    platform_name = "mcmod"

    def export_all(self) -> Dict[str, Any]:
        conn = self.get_connection()
        try:
            # 1. Fetch source items and metrics
            items_cur = conn.execute("""
                SELECT 
                    si.id, si.source_id, si.title, si.author, si.description, si.icon_url,
                    si.published_at, si.modified_at, si.extra_json,
                    m.views, m.score, m.trend_latest, m.trend_days, m.comments_count,
                    m.likes, m.favorites, m.red_votes, m.black_votes
                FROM source_items si
                LEFT JOIN metrics m ON si.id = m.source_item_id
                WHERE si.platform = 'mcmod'
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
                    "class_id": row["class_id"],
                    "category_id": row["category_id"] or "1",
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

            # 7. Fetch source comments
            cmt_cur = conn.execute("""
                SELECT source_item_id, page_count, true_count, comments_json
                FROM source_comments
                WHERE source_item_id LIKE 'mcmod:%'
            """)
            cmt_map: Dict[str, Dict[str, Any]] = {}
            for row in cmt_cur.fetchall():
                cmt_map[row["source_item_id"]] = {
                    "page_count": row["page_count"],
                    "true_count": row["true_count"],
                    "comments": json.loads(row["comments_json"] or "[]"),
                }

            # 8. Fetch environment claims (server)
            claim_cur = conn.execute("""
                SELECT source_item_id, status, certainty
                FROM environment_claims
                WHERE source_item_id LIKE 'mcmod:%' AND side = 'server'
            """)
            server_claim_map: Dict[str, Tuple[str, str]] = {}
            for row in claim_cur.fetchall():
                server_claim_map[row["source_item_id"]] = (row["status"], row["certainty"])

            # Data collections to export
            table_rows = []
            compare_data = {}
            desc_data = {}
            mods_exported_count = 0
            cmts_exported_count = 0

            for it in items:
                si_id = it["id"]
                mid = str(it["source_id"])
                full_title = it["title"] or f"Modpack {mid}"
                author = it["author"] or "未知"
                cover_url = it["icon_url"] or ""
                pub_at = it["published_at"] or ""
                mod_at = it["modified_at"] or ""
                description = it["description"] or ""

                # Parse extra_json
                extra = json.loads(it["extra_json"] or "{}")
                type_name = extra.get("type_name") or "原生整合"
                mold_id = extra.get("mold_id") or ("2" if "魔改" in type_name else "1")
                intro_images = extra.get("intro_images") or []

                # Metrics
                views_n = int(it["views"] or 0)
                views_d = f"{views_n / 10000.0:.2f}万" if views_n >= 10000 else str(views_n)
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

                # Versions
                mc_vers = mc_map.get(si_id, [])
                mc_version = mc_vers[0] if mc_vers else ""

                # Former titles
                former_titles = former_map.get(si_id, [])

                # Server claim
                s_stat, s_cert = server_claim_map.get(si_id, (None, None))
                has_server = self.derive_legacy_has_server(s_stat, s_cert)

                # Trend stats
                t_points = trend_map.get(si_id, [])
                if not t_points:
                    t_points = [("2026-09-17", float(it["trend_latest"] or 0))]
                lat_n, max_n, avg_n, days_n, t7_n, t30_n, t60_n, tall_n = renderer.compute_trend_stats(t_points)
                score_n = int(it["score"] or (5 if lat_n > 500 else (4 if lat_n > 200 else (3 if lat_n > 50 else (2 if lat_n > 10 else 1)))))
                trend_dates = ",".join(p[0] for p in t_points)
                trend_vals = ",".join(f"{p[1]:.1f}" if p[1] != int(p[1]) else str(int(p[1])) for p in t_points)

                # Split titles
                title_cn, title_en = full_title, ""
                if " (" in full_title and full_title.endswith(")"):
                    parts = full_title.rsplit(" (", 1)
                    title_cn = parts[0].strip()
                    title_en = parts[1][:-1].strip()

                # Included mods & group details
                pack_mods = mods_map.get(si_id, [])
                mod_names = [m["name"] for m in pack_mods]
                mod_cats = []
                detail_groups = []
                detail_group_map = {}
                seen_cat = set()

                for m in pack_mods:
                    c_name = m.get("category_name") or "未分类"
                    if c_name and c_name not in seen_cat:
                        seen_cat.add(c_name)
                        mod_cats.append(c_name)
                    c_id = m.get("category_id") or "1"
                    g_key = f"{c_id}|{c_name}"
                    if g_key not in detail_group_map:
                        g_obj = {
                            "k": f"cat{len(detail_groups)}",
                            "n": c_name,
                            "u": m.get("category_url") or "",
                            "mods": [],
                            "m": []
                        }
                        detail_group_map[g_key] = g_obj
                        detail_groups.append(g_obj)
                    detail_group_map[g_key]["mods"].append(m)
                    detail_group_map[g_key]["m"].append([
                        m["name"],
                        m.get("version") or "",
                        m.get("url") or "#",
                        m.get("title") or m["name"]
                    ])

                # HTML cells rendered via mcmod_renderer
                c0 = renderer.build_c0(mid, full_title, title_cn, title_en, cover_url, mold_id, type_name, views_d, "", mod_at)
                c1 = renderer.build_c1(score_n, lat_n, max_n, avg_n, days_n, [p[1] for p in t_points])
                c2 = renderer.build_c2(t7_n, t30_n, t60_n, tall_n)
                c3 = renderer.build_c3(rv_n, rp_n, bv_n, bp_n)
                c4 = renderer.build_c4(rec_n, fav_n, com_n)
                c5 = renderer.build_c5(cats)
                c6 = renderer.build_c6(detail_groups, len(pack_mods))

                # Build row for table_rows.js
                row_dict = {
                    "mid": mid,
                    "has_cover": bool(cover_url),
                    "type_name": type_name,
                    "name_order": full_title.lower(),
                    "views_n": views_n,
                    "score_n": score_n,
                    "lat_n": lat_n,
                    "max_n": max_n,
                    "avg_n": avg_n,
                    "days_n": days_n,
                    "com_n": com_n,
                    "rec_n": rec_n,
                    "fav_n": fav_n,
                    "rv_n": rv_n,
                    "bv_n": bv_n,
                    "rp_n": rp_n,
                    "bp_n": bp_n,
                    "t7_n": t7_n,
                    "t30_n": t30_n,
                    "t60_n": t60_n,
                    "tall_n": tall_n,
                    "c0": c0,
                    "c1": c1,
                    "c2": c2,
                    "c3": c3,
                    "c4": c4,
                    "c5": c5,
                    "c6": c6,
                    "title": full_title,
                    "trend_dates": trend_dates,
                    "trend_vals": trend_vals,
                    "cat_search": " ".join(cats),
                    "tags_search": " ".join(cats),
                    "pack_search": "",
                    "tag_count": len(cats),
                    "mods_search": " ".join(mod_names),
                    "mod_count": len(mod_names),
                    "mod_categories": mod_cats,
                    "latest_version": "",
                    "last_update_date": mod_at,
                    "release_date": pub_at,
                    "version_count": 0,
                    "version_checked": True,
                    "former_titles": former_titles,
                    "mc_versions": mc_vers,
                    "mc_version": mc_version,
                    "has_server": has_server,
                }
                table_rows.append(row_dict)

                # Build compareData for app_data.js
                compare_data[mid] = {
                    "mid": mid,
                    "title": full_title,
                    "title_cn": title_cn,
                    "title_en": title_en,
                    "url": f"https://www.mcmod.cn/modpack/{mid}.html",
                    "type": type_name,
                    "has_server": has_server,
                    "views": views_n,
                    "score": score_n,
                    "trend_latest": lat_n,
                    "trend_days": days_n,
                    "comments": com_n,
                    "recommend": rec_n,
                    "favorite": fav_n,
                    "red_votes": rv_n,
                    "black_votes": bv_n,
                    "growth7": f"{t7_n:.0f}%",
                    "growth30": f"{t30_n:.0f}%",
                    "growth60": f"{t60_n:.0f}%",
                    "categories": cats,
                    "tags": cats,
                    "mods": mod_names,
                    "mod_count": len(mod_names),
                    "mod_categories": mod_cats,
                    "mc_versions": mc_vers,
                    "latest_version": "",
                    "last_update_date": mod_at,
                    "release_date": pub_at,
                    "version_count": 0,
                }

                # Build desc_data for desc_data.js
                desc_data[mid] = {
                    "mid": mid,
                    "text": description,
                    "images": intro_images,
                }

                # Export mods/{mid}.js sidecar
                mod_sidecar_payload = [
                    {
                        "k": g["k"],
                        "n": g["n"],
                        "u": g["u"],
                        "m": g["m"]
                    }
                    for g in detail_groups
                ]
                self.write_register_script("mods", f"{mid}.js", "__registerModDetailData", mid, mod_sidecar_payload)
                mods_exported_count += 1

                # Export comments/{mid}.js sidecar (legacy only wrote when comments existed or page_count > 0)
                sc_info = cmt_map.get(si_id, {"page_count": com_n, "true_count": 0, "comments": []})
                if sc_info.get("page_count", 0) > 0 or sc_info.get("true_count", 0) > 0 or sc_info.get("comments"):
                    cmt_payload = {
                        "true_count": sc_info.get("true_count", 0),
                        "page_count": sc_info.get("page_count", com_n),
                        "comments": sc_info.get("comments", [])
                    }
                    self.write_register_script("comments", f"{mid}.js", "__registerCommentData", mid, cmt_payload)
                    cmts_exported_count += 1

            # Sort table_rows by views_n descending (exact legacy order)
            table_rows.sort(key=lambda x: x.get("views_n", 0), reverse=True)

            # Write master sidecar JS files
            tr_path = self.write_sidecar("table_rows.js", "tableRowsData", table_rows)
            app_path = self.write_sidecar("app_data.js", "compareData", compare_data)
            desc_path = self.write_sidecar("desc_data.js", "descData", desc_data)

            return {
                "platform": "mcmod",
                "table_rows_count": len(table_rows),
                "app_data_count": len(compare_data),
                "desc_data_count": len(desc_data),
                "mods_sidecars_count": mods_exported_count,
                "comments_sidecars_count": cmts_exported_count,
                "files": [tr_path, app_path, desc_path],
            }
        finally:
            conn.close()

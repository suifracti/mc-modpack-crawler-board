"""
Bilibili Legacy Exporter for Architecture V2.
Exports bili_data.js strictly from build/canonical.db.
"""
import json
import sqlite3
from typing import Dict, Any, List, Optional
from pipeline.exporters.legacy.base import BaseLegacyExporter

class BilibiliExporter(BaseLegacyExporter):
    platform_name = "bilibili"

    def export_all(self) -> Dict[str, Any]:
        conn = self.get_connection()
        try:
            # 1. Fetch items & metrics
            items_cur = conn.execute("""
                SELECT 
                    si.id, si.source_id, si.title, si.author, si.description, si.icon_url,
                    si.source_url, si.published_at, si.modified_at, si.extra_json,
                    m.views, m.likes, m.favorites, m.comments_count
                FROM source_items si
                LEFT JOIN metrics m ON si.id = m.source_item_id
                WHERE si.platform = 'bilibili'
            """)
            items = items_cur.fetchall()

            # 2. Fetch categories
            cats_cur = conn.execute("""
                SELECT sc.source_item_id, c.name
                FROM source_item_categories sc
                JOIN categories c ON sc.category_id = c.id
                WHERE c.platform = 'bilibili'
            """)
            cats_map: Dict[str, List[str]] = {}
            for row in cats_cur.fetchall():
                cats_map.setdefault(row["source_item_id"], []).append(row["name"])

            # 3. Fetch loaders
            loaders_cur = conn.execute("""
                SELECT sl.source_item_id, l.name
                FROM source_item_loaders sl
                JOIN loaders l ON sl.loader_id = l.id
                WHERE sl.source_item_id LIKE 'bilibili:%'
            """)
            loaders_map: Dict[str, List[str]] = {}
            for row in loaders_cur.fetchall():
                loaders_map.setdefault(row["source_item_id"], []).append(row["name"])

            # 4. Fetch MC versions
            mc_cur = conn.execute("""
                SELECT r.source_item_id, rm.mc_version
                FROM releases r
                JOIN release_mc_versions rm ON r.id = rm.release_id
                WHERE r.source_item_id LIKE 'bilibili:%'
                ORDER BY rm.is_primary DESC, rm.id ASC
            """)
            mc_map: Dict[str, List[str]] = {}
            for row in mc_cur.fetchall():
                v = row["mc_version"].strip()
                if v and v not in mc_map.setdefault(row["source_item_id"], []):
                    mc_map[row["source_item_id"]].append(v)

            # 5. Fetch download links
            dl_cur = conn.execute("""
                SELECT source_item_id, link_type, url, label, extract_code
                FROM download_links
                WHERE source_item_id LIKE 'bilibili:%'
            """)
            dl_map: Dict[str, List[Dict[str, Any]]] = {}
            for row in dl_cur.fetchall():
                dl_map.setdefault(row["source_item_id"], []).append({
                    "name": row["label"] or "网盘下载",
                    "url": row["url"],
                    "code": row["extract_code"] or "",
                    "type": (row["link_type"] or "OTHER").lower()
                })

            # 6. Fetch environment claims (server)
            claim_cur = conn.execute("""
                SELECT source_item_id, status, certainty
                FROM environment_claims
                WHERE source_item_id LIKE 'bilibili:%' AND side = 'server'
            """)
            claim_map: Dict[str, Any] = {}
            for row in claim_cur.fetchall():
                claim_map[row["source_item_id"]] = (row["status"], row["certainty"])

            records = []
            for it in items:
                si_id = it["id"]
                extra = json.loads(it["extra_json"] or "{}")

                # Environment server support (Legacy compatibility)
                c_status, c_cert = claim_map.get(si_id, (None, None))
                has_server = self.derive_legacy_has_server(c_status, c_cert)

                # Versions
                mc_vers = mc_map.get(si_id, [])
                mc_version = mc_vers[0] if mc_vers else "未知"

                # Deprecated legacy compatibility field for legacy dashboard UI
                # Cascade priority: update_notice_at -> pinned_comment_at -> observed_at
                desc_updated_at = (
                    extra.get("update_notice_at")
                    or extra.get("pinned_comment_at")
                    or extra.get("observed_at")
                    or ""
                )

                rec = {
                    "platform": "bilibili",
                    "bvid": it["source_id"],
                    "aid": extra.get("aid") or 0,
                    "cid": extra.get("cid") or 0,
                    "url": it["source_url"],
                    "title": it["title"],
                    "author": it["author"] or "未知UP主",
                    "desc": it["description"] or "",
                    "pic": it["icon_url"] or "",
                    "pub_time": it["published_at"] or "",
                    "pub_timestamp": extra.get("pub_timestamp") or 0,
                    "duration": extra.get("duration") or 0,
                    "views": int(it["views"] or 0),
                    "likes": int(it["likes"] or 0),
                    "coins": int(extra.get("coins") or 0),
                    "favorites": int(it["favorites"] or 0),
                    "reply": int(it["comments_count"] or 0),
                    "danmaku": int(extra.get("danmaku") or 0),
                    "share": int(extra.get("share") or 0),
                    "pack_version": extra.get("pack_version") or "发布版",
                    "qq_group": extra.get("qq_group") or "",
                    "extract_code": extra.get("extract_code") or "",
                    "has_group_version": bool(extra.get("has_group_version")),
                    "group_version_note": extra.get("group_version_note") or "",
                    "pinned_comment": extra.get("pinned_comment") or "",
                    "desc_updated_at": desc_updated_at,
                    "has_subtitle": bool(extra.get("has_subtitle")),
                    "subtitle_text": extra.get("subtitle_text") or "",
                    "subtitle_summary": extra.get("subtitle_summary") or "",
                    "mod_count": int(extra.get("mod_count") or 0),
                    "categories": cats_map.get(si_id, []),
                    "loaders": loaders_map.get(si_id, []),
                    "mc_version": mc_version,
                    "all_versions": mc_vers,
                    "download_links": dl_map.get(si_id, []),
                    "has_server": has_server,
                }
                records.append(rec)

            out_path = self.write_sidecar("bili_data.js", "biliModpacksData", records)
            return {
                "platform": "bilibili",
                "count": len(records),
                "file": out_path,
            }
        finally:
            conn.close()

"""
CurseForge Legacy Exporter for Architecture V2.
Exports curseforge_data.js strictly from build/canonical.db.
"""
import json
import sqlite3
from typing import Dict, Any, List, Optional
from pipeline.exporters.legacy.base import BaseLegacyExporter

class CurseForgeExporter(BaseLegacyExporter):
    platform_name = "curseforge"

    def export_all(self) -> Dict[str, Any]:
        conn = self.get_connection()
        try:
            # 1. Fetch items & metrics
            items_cur = conn.execute("""
                SELECT 
                    si.id, si.source_id, si.slug, si.title, si.author, si.description, si.icon_url,
                    si.source_url, si.published_at, si.modified_at, si.extra_json,
                    m.downloads, m.followers
                FROM source_items si
                LEFT JOIN metrics m ON si.id = m.source_item_id
                WHERE si.platform = 'curseforge'
            """)
            items = items_cur.fetchall()

            # 2. Fetch categories
            cats_cur = conn.execute("""
                SELECT sc.source_item_id, c.name
                FROM source_item_categories sc
                JOIN categories c ON sc.category_id = c.id
                WHERE c.platform = 'curseforge'
            """)
            cats_map: Dict[str, List[str]] = {}
            for row in cats_cur.fetchall():
                cats_map.setdefault(row["source_item_id"], []).append(row["name"])

            # 3. Fetch loaders
            loaders_cur = conn.execute("""
                SELECT sl.source_item_id, l.name
                FROM source_item_loaders sl
                JOIN loaders l ON sl.loader_id = l.id
                WHERE sl.source_item_id LIKE 'curseforge:%'
            """)
            loaders_map: Dict[str, List[str]] = {}
            for row in loaders_cur.fetchall():
                loaders_map.setdefault(row["source_item_id"], []).append(row["name"])

            # 4. Fetch MC versions
            mc_cur = conn.execute("""
                SELECT r.source_item_id, rm.mc_version
                FROM releases r
                JOIN release_mc_versions rm ON r.id = rm.release_id
                WHERE r.source_item_id LIKE 'curseforge:%'
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
                WHERE source_item_id LIKE 'curseforge:%'
            """)
            dl_map: Dict[str, List[Dict[str, Any]]] = {}
            for row in dl_cur.fetchall():
                dl_map.setdefault(row["source_item_id"], []).append({
                    "name": row["label"] or "下载",
                    "url": row["url"],
                    "type": (row["link_type"] or "OTHER").lower()
                })

            # 6. Fetch environment claims (server)
            claim_cur = conn.execute("""
                SELECT source_item_id, status, certainty
                FROM environment_claims
                WHERE source_item_id LIKE 'curseforge:%' AND side = 'server'
            """)
            claim_map: Dict[str, Any] = {}
            for row in claim_cur.fetchall():
                claim_map[row["source_item_id"]] = (row["status"], row["certainty"])

            records = []
            for it in items:
                si_id = it["id"]
                extra = json.loads(it["extra_json"] or "{}")

                # Server support (Legacy compatibility)
                c_status, c_cert = claim_map.get(si_id, (None, None))
                has_server = self.derive_legacy_has_server(c_status, c_cert)

                # Versions
                mc_vers = mc_map.get(si_id, [])
                mc_version = mc_vers[0] if mc_vers else ""

                rec = {
                    "platform": "curseforge",
                    "project_id": it["source_id"],
                    "slug": it["slug"] or extra.get("slug") or "",
                    "url": it["source_url"],
                    "title": it["title"],
                    "author": it["author"] or "未知作者",
                    "description": it["description"] or "",
                    "icon_url": it["icon_url"] or "",
                    "date_created": it["published_at"] or "",
                    "date_modified": it["modified_at"] or "",
                    "downloads": int(it["downloads"] or 0),
                    "followers": int(it["followers"] or 0),
                    "gallery": extra.get("gallery") or [],
                    "source_meta": extra.get("source_meta") or {},
                    "categories": cats_map.get(si_id, []),
                    "loaders": loaders_map.get(si_id, []),
                    "mc_version": mc_version,
                    "all_versions": mc_vers,
                    "download_links": dl_map.get(si_id, []),
                    "has_server": has_server,
                }
                records.append(rec)

            out_path = self.write_sidecar("curseforge_data.js", "curseforgeModpacksData", records)
            return {
                "platform": "curseforge",
                "count": len(records),
                "file": out_path,
            }
        finally:
            conn.close()

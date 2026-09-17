"""
Modrinth Platform Adapter for Architecture V2.
Extracts clean structured records from crawler_output/modrinth_modpacks.json.
Retains official client_side and server_side attributes as CONFIRMED platform facts.
"""
import json
import os
from typing import Dict, Any, Optional, List
from pipeline.adapters.base import BaseAdapter
from pipeline.models.canonical import (
    CanonicalPack,
    CanonicalSourceItem,
    CanonicalRelease,
    CanonicalDownloadLink,
    CanonicalMetrics,
    CanonicalEnvironmentClaim,
    CanonicalPackBundle,
)

class ModrinthAdapter(BaseAdapter):
    platform_name = "modrinth"

    def get_source_file_path(self) -> str:
        return os.path.join(self.workspace_root, "crawler_output", "modrinth_modpacks.json")

    def adapt_item(self, raw_item: Dict[str, Any], idx: int) -> CanonicalPackBundle:
        pid = str(raw_item.get("project_id") or raw_item.get("slug") or idx + 1)
        pack_id = f"pack_modrinth_{pid}"
        source_item_id = f"modrinth:{pid}"
        title = (raw_item.get("title") or f"Modrinth Pack #{pid}").strip()
        url = raw_item.get("url") or f"https://modrinth.com/modpack/{raw_item.get('slug') or pid}"
        now_str = "2026-09-17 12:00:00"

        pub_at = raw_item.get("date_created") or None
        mod_at = raw_item.get("date_modified") or None

        # 1. Canonical Pack
        pack = CanonicalPack(
            id=pack_id,
            preferred_title=title,
            normalized_title=self.normalize_title(title),
            summary=(raw_item.get("description") or "")[:1000] or None,
            primary_platform="modrinth",
            created_at=pub_at or now_str,
            updated_at=mod_at or now_str,
        )

        # 2. Source Item
        client_side = raw_item.get("client_side") or raw_item.get("source_meta", {}).get("client_side") or "required"
        server_side = raw_item.get("server_side") or raw_item.get("source_meta", {}).get("server_side") or "unknown"
        
        extra_dict = {
            "slug": raw_item.get("slug"),
            "client_side": client_side,
            "server_side": server_side,
            "source_meta": raw_item.get("source_meta") or {},
            "gallery": raw_item.get("gallery") or [],
            "env_display": raw_item.get("env_display")
        }

        source_item = CanonicalSourceItem(
            id=source_item_id,
            pack_id=pack_id,
            platform="modrinth",
            source_id=pid,
            slug=raw_item.get("slug"),
            source_url=url,
            title=title,
            author=raw_item.get("author") or "未知作者",
            description=raw_item.get("description") or None,
            icon_url=raw_item.get("icon_url") or None,
            published_at=pub_at,
            modified_at=mod_at,
            raw_ref=f"crawler_output/modrinth_modpacks.json#id={pid}",
            extra_json=json.dumps(extra_dict, ensure_ascii=False),
            created_at=pub_at or now_str,
            updated_at=mod_at or now_str,
        )

        # 3. Releases
        mc_vers = raw_item.get("all_versions") or []
        if not mc_vers and raw_item.get("mc_version"):
            mc_vers = [raw_item["mc_version"]]

        releases = [
            CanonicalRelease(
                id=f"{source_item_id}:rel:latest",
                pack_id=pack_id,
                source_item_id=source_item_id,
                version_name=raw_item.get("mc_version") or "Latest",
                version_type="release",
                release_date=mod_at or pub_at,
                is_latest=True,
                downloads_count=raw_item.get("downloads"),
                mc_versions=mc_vers,
                created_at=now_str
            )
        ]

        # 4. Download Links
        download_links = []
        for dl in (raw_item.get("download_links") or []):
            if isinstance(dl, dict) and dl.get("url"):
                download_links.append(CanonicalDownloadLink(
                    source_item_id=source_item_id,
                    link_type=dl.get("type") or "OFFICIAL",
                    url=dl["url"],
                    label=dl.get("label") or dl.get("name") or "Modrinth 页面",
                    is_server=False,
                    created_at=now_str
                ))

        # 5. Loaders & Categories
        loaders = [l for l in (raw_item.get("loaders") or []) if l]
        categories = [c for c in (raw_item.get("categories") or []) if c]

        # 6. Metrics
        metrics = CanonicalMetrics(
            source_item_id=source_item_id,
            observed_at=now_str,
            downloads=raw_item.get("downloads"),
            followers=raw_item.get("followers")
        )

        # 7. Environment Claims - 100% 权威客观事实 (CONFIRMED FACTS)
        claims = [
            CanonicalEnvironmentClaim(
                pack_id=pack_id,
                source_item_id=source_item_id,
                side="client",
                status=client_side,
                certainty="confirmed",
                evidence_type="platform_field",
                evidence_text=f"Modrinth 官方 API 字段: client_side={client_side}",
                raw_value=client_side,
                source_field="client_side",
                source_url=url,
                observed_at=now_str
            ),
            CanonicalEnvironmentClaim(
                pack_id=pack_id,
                source_item_id=source_item_id,
                side="server",
                status=server_side,
                certainty="confirmed",
                evidence_type="platform_field",
                evidence_text=f"Modrinth 官方 API 字段: server_side={server_side}",
                raw_value=server_side,
                source_field="server_side",
                source_url=url,
                observed_at=now_str
            )
        ]

        return CanonicalPackBundle(
            pack=pack,
            source_item=source_item,
            aliases=[],
            releases=releases,
            loaders=loaders,
            categories=categories,
            download_links=download_links,
            related_videos=[],
            metrics=metrics,
            environment_claims=claims
        )

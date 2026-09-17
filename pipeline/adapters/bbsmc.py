"""
BBSMC Platform Adapter for Architecture V2.
Extracts clean structured records from crawler_output/bbsmc_modpacks.json.
"""
import json
import os
import re
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

class BbsmcAdapter(BaseAdapter):
    platform_name = "bbsmc"

    def get_source_file_path(self) -> str:
        return os.path.join(self.workspace_root, "crawler_output", "bbsmc_modpacks.json")

    def adapt_item(self, raw_item: Dict[str, Any], idx: int) -> CanonicalPackBundle:
        pid = str(raw_item.get("project_id") or raw_item.get("slug") or idx + 1)
        pack_id = f"pack_bbsmc_{pid}"
        source_item_id = f"bbsmc:{pid}"
        title = (raw_item.get("title") or f"BBSMC 模组包 #{pid}").strip()
        url = raw_item.get("url") or f"https://www.bbsmc.net/modpack/{pid}"
        now_str = "2026-09-17 12:00:00"

        pub_at = raw_item.get("date_created") or None
        mod_at = raw_item.get("date_modified") or None

        # 1. Canonical Pack
        pack = CanonicalPack(
            id=pack_id,
            preferred_title=title,
            normalized_title=self.normalize_title(title),
            summary=(raw_item.get("description") or "")[:1000] or None,
            primary_platform="bbsmc",
            created_at=pub_at or now_str,
            updated_at=mod_at or now_str,
        )

        # 2. Source Item
        extra_dict = {
            "slug": raw_item.get("slug"),
            "gallery": raw_item.get("gallery") or [],
        }
        source_item = CanonicalSourceItem(
            id=source_item_id,
            pack_id=pack_id,
            platform="bbsmc",
            source_id=pid,
            slug=raw_item.get("slug"),
            source_url=url,
            title=title,
            author=raw_item.get("author") or "未知作者",
            description=raw_item.get("description") or None,
            icon_url=raw_item.get("icon_url") or None,
            published_at=pub_at,
            modified_at=mod_at,
            raw_ref=f"crawler_output/bbsmc_modpacks.json#id={pid}",
            extra_json=json.dumps(extra_dict, ensure_ascii=False),
            created_at=pub_at or now_str,
            updated_at=mod_at or now_str,
        )

        # 3. Releases & MC Versions
        releases = []
        raw_versions = raw_item.get("versions_data") or []
        for v_idx, v in enumerate(raw_versions):
            v_name = v.get("version_name") or v.get("name") or f"v_{v_idx+1}"
            v_date = v.get("date_created") or v.get("release_date")
            v_mc = v.get("game_versions") or raw_item.get("all_versions") or []
            v_extra = {"files": v.get("files") or []}
            releases.append(CanonicalRelease(
                id=f"{source_item_id}:rel:{v.get('id') or v_idx}",
                pack_id=pack_id,
                source_item_id=source_item_id,
                version_name=v_name,
                version_type="release",
                release_date=v_date,
                is_latest=(v_idx == 0),
                changelog=v.get("changelog"),
                downloads_count=v.get("downloads"),
                mc_versions=v_mc,
                extra_json=json.dumps(v_extra, ensure_ascii=False),
                created_at=now_str
            ))

        if not releases:
            releases.append(CanonicalRelease(
                id=f"{source_item_id}:rel:latest",
                pack_id=pack_id,
                source_item_id=source_item_id,
                version_name="最新版",
                version_type="release",
                release_date=mod_at or pub_at,
                is_latest=True,
                mc_versions=raw_item.get("all_versions") or ([raw_item["mc_version"]] if raw_item.get("mc_version") else []),
                created_at=now_str
            ))

        # 4. Download Links
        download_links = []
        has_server_file = False
        server_evidence_text = ""
        for dl in (raw_item.get("download_links") or []):
            if isinstance(dl, dict) and dl.get("url"):
                l_name = dl.get("name") or "下载"
                is_server = bool(re.search(r'(?:服务端|server|开服)', l_name, re.IGNORECASE))
                if is_server:
                    has_server_file = True
                    server_evidence_text = l_name

                download_links.append(CanonicalDownloadLink(
                    source_item_id=source_item_id,
                    link_type=dl.get("type") or "OFFICIAL",
                    url=dl["url"],
                    label=l_name,
                    extract_code=dl.get("extract_code"),
                    is_server=is_server,
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

        # 7. Environment Claims
        claims = [
            CanonicalEnvironmentClaim(
                pack_id=pack_id,
                source_item_id=source_item_id,
                side="client",
                status="supported",
                certainty="confirmed",
                evidence_type="platform_field",
                evidence_text="BBSMC开源整合包默认支持单人客户端运行",
                raw_value="client: supported",
                source_field="bbsmc:modpack",
                source_url=url,
                observed_at=now_str
            )
        ]
        if has_server_file:
            claims.append(CanonicalEnvironmentClaim(
                pack_id=pack_id,
                source_item_id=source_item_id,
                side="server",
                status="supported",
                certainty="inferred",
                evidence_type="file_name",
                evidence_text=f"下载文件名称包含服务端: {server_evidence_text}",
                raw_value="server: supported",
                source_field="download_links[].name",
                source_url=url,
                observed_at=now_str
            ))
        else:
            claims.append(CanonicalEnvironmentClaim(
                pack_id=pack_id,
                source_item_id=source_item_id,
                side="server",
                status="unsupported",
                certainty="weak_inferred",
                evidence_type="file_name",
                evidence_text="下载文件列表中未检索到服务端包",
                raw_value="server: none",
                source_field="download_links",
                source_url=url,
                observed_at=now_str
            ))

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

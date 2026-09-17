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
            "featured_gallery": raw_item.get("featured_gallery") or [],
            "created_timestamp": raw_item.get("created_timestamp"),
            "modified_timestamp": raw_item.get("modified_timestamp"),
            "versions_data": raw_item.get("versions_data") or [],
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
        import urllib.parse
        download_links = []
        has_server_file = False
        server_evidence_text = ""
        server_raw_value = ""

        for dl in (raw_item.get("download_links") or []):
            if isinstance(dl, dict) and dl.get("url"):
                l_name = dl.get("name") or "下载"
                dl_texts = " ".join([
                    str(dl.get("name") or ""),
                    str(dl.get("filename") or ""),
                    str(dl.get("version") or ""),
                    urllib.parse.unquote(str(dl.get("url") or ""))
                ])
                m_srv = self.SERVER_FILE_REGEX.search(dl_texts)
                is_server = bool(m_srv)
                if is_server and not has_server_file:
                    has_server_file = True
                    server_evidence_text = dl.get("filename") or l_name
                    server_raw_value = m_srv.group(0)

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

        # 7. Environment Claims (Phase 1.1 Strict Semantics)
        claims = []
        full_text = f"{title} {raw_item.get('description') or ''}"

        # Client Claim
        m_c_neg = self.SERVER_TEXT_NEG_REGEX.search(full_text)
        if m_c_neg and "客户端" in m_c_neg.group(0):
            claims.append(CanonicalEnvironmentClaim(
                pack_id=pack_id,
                source_item_id=source_item_id,
                side="client",
                status="supported",
                certainty="inferred",
                evidence_type="text_rule",
                evidence_text=self.extract_snippet(full_text, m_c_neg),
                raw_value=m_c_neg.group(0),
                source_field="description",
                source_url=url,
                observed_at=now_str
            ))
        else:
            claims.append(self.create_unknown_claim(
                pack_id, source_item_id, "client",
                "BBSMC未提供结构化客户端运行环境字段",
                url, now_str
            ))

        # Server Claim
        m_s_neg = self.SERVER_TEXT_NEG_REGEX.search(full_text)
        m_s_pos = self.SERVER_TEXT_POS_REGEX.search(full_text)

        if has_server_file:
            claims.append(CanonicalEnvironmentClaim(
                pack_id=pack_id,
                source_item_id=source_item_id,
                side="server",
                status="supported",
                certainty="strong_inferred",
                evidence_type="file_name",
                evidence_text=f"下载文件名称包含服务端: {server_evidence_text}",
                raw_value=server_raw_value or "服务端",
                source_field="download_links[].filename",
                source_url=url,
                observed_at=now_str
            ))
        elif m_s_neg:
            claims.append(CanonicalEnvironmentClaim(
                pack_id=pack_id,
                source_item_id=source_item_id,
                side="server",
                status="unsupported",
                certainty="inferred",
                evidence_type="text_rule",
                evidence_text=self.extract_snippet(full_text, m_s_neg),
                raw_value=m_s_neg.group(0),
                source_field="description",
                source_url=url,
                observed_at=now_str
            ))
        elif m_s_pos:
            claims.append(CanonicalEnvironmentClaim(
                pack_id=pack_id,
                source_item_id=source_item_id,
                side="server",
                status="supported",
                certainty="inferred",
                evidence_type="text_rule",
                evidence_text=self.extract_snippet(full_text, m_s_pos),
                raw_value=m_s_pos.group(0),
                source_field="description",
                source_url=url,
                observed_at=now_str
            ))
        else:
            claims.append(self.create_unknown_claim(
                pack_id, source_item_id, "server",
                "BBSMC开源项目未检索到服务端文件且简介未声明开服支持",
                url, now_str
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

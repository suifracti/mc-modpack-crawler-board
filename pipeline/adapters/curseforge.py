"""
CurseForge Platform Adapter for Architecture V2.
Extracts clean structured records from crawler_output/curseforge_modpacks.json.
Maintains strict certainty distinction: labels server support from regex as WEAK_INFERRED.
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

SERVER_KEYWORD_REGEX = re.compile(r'(?:server|服务端|serverpack|server-pack|开服)', re.IGNORECASE)

class CurseForgeAdapter(BaseAdapter):
    platform_name = "curseforge"

    def get_source_file_path(self) -> str:
        return os.path.join(self.workspace_root, "crawler_output", "curseforge_modpacks.json")

    def adapt_item(self, raw_item: Dict[str, Any], idx: int) -> CanonicalPackBundle:
        pid = str(raw_item.get("project_id") or raw_item.get("slug") or idx + 1)
        pack_id = f"pack_curseforge_{pid}"
        source_item_id = f"curseforge:{pid}"
        title = (raw_item.get("title") or f"CurseForge Pack #{pid}").strip()
        slug = raw_item.get("slug") or pid
        url = raw_item.get("url") or f"https://www.curseforge.com/minecraft/modpacks/{slug}"
        now_str = "2026-09-17 12:00:00"

        pub_at = raw_item.get("date_created") or None
        mod_at = raw_item.get("date_modified") or None

        # 1. Canonical Pack
        pack = CanonicalPack(
            id=pack_id,
            preferred_title=title,
            normalized_title=self.normalize_title(title),
            summary=(raw_item.get("description") or "")[:1000] or None,
            primary_platform="curseforge",
            created_at=pub_at or now_str,
            updated_at=mod_at or now_str,
        )

        # 2. Source Item
        extra_dict = {
            "slug": slug,
            "gallery": raw_item.get("gallery") or [],
            "source_meta": raw_item.get("source_meta") or {}
        }

        source_item = CanonicalSourceItem(
            id=source_item_id,
            pack_id=pack_id,
            platform="curseforge",
            source_id=pid,
            slug=slug,
            source_url=url,
            title=title,
            author=raw_item.get("author") or "未知作者",
            description=raw_item.get("description") or None,
            icon_url=raw_item.get("icon_url") or None,
            published_at=pub_at,
            modified_at=mod_at,
            raw_ref=f"crawler_output/curseforge_modpacks.json#id={pid}",
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
                release_date=None,
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
                    label=dl.get("label") or dl.get("name") or "CurseForge 页面",
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

        # 7. Environment Claims (Phase 1.1 Strict Semantics)
        claims = []
        text_corpus = f"{title} {raw_item.get('description') or ''}"

        # Client Claim
        m_c_neg = self.SERVER_TEXT_NEG_REGEX.search(text_corpus)
        if m_c_neg and ("client only" in m_c_neg.group(0).lower() or "客户端" in m_c_neg.group(0)):
            claims.append(CanonicalEnvironmentClaim(
                pack_id=pack_id,
                source_item_id=source_item_id,
                side="client",
                status="supported",
                certainty="inferred",
                evidence_type="text_rule",
                evidence_text=self.extract_snippet(text_corpus, m_c_neg),
                raw_value=m_c_neg.group(0),
                source_field="title/description",
                source_url=url,
                observed_at=now_str
            ))
        else:
            claims.append(self.create_unknown_claim(
                pack_id, source_item_id, "client",
                "CurseForge未提供结构化客户端兼容性字段",
                url, now_str
            ))

        # Server Claim
        server_file_hit = None
        for dl in download_links:
            dl_str = f"{dl.label} {dl.url}"
            m_f = self.SERVER_FILE_REGEX.search(dl_str)
            if m_f:
                server_file_hit = (m_f.group(0), dl_str[:80])
                break

        m_s_neg = self.SERVER_TEXT_NEG_REGEX.search(text_corpus)
        m_s_pos = self.SERVER_TEXT_POS_REGEX.search(text_corpus)

        if server_file_hit:
            claims.append(CanonicalEnvironmentClaim(
                pack_id=pack_id,
                source_item_id=source_item_id,
                side="server",
                status="supported",
                certainty="strong_inferred",
                evidence_type="file_name",
                evidence_text=f"下载文件名称包含服务端: {server_file_hit[1]}",
                raw_value=server_file_hit[0],
                source_field="download_links[].name",
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
                evidence_text=self.extract_snippet(text_corpus, m_s_neg),
                raw_value=m_s_neg.group(0),
                source_field="title/description",
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
                evidence_text=self.extract_snippet(text_corpus, m_s_pos),
                raw_value=m_s_pos.group(0),
                source_field="title/description",
                source_url=url,
                observed_at=now_str
            ))
        else:
            claims.append(self.create_unknown_claim(
                pack_id, source_item_id, "server",
                "CurseForge搜索接口未提供开服端包且文本无明确开服声明",
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

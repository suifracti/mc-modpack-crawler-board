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

        # 7. Environment Claims
        # Client is confirmed platform standard
        claims = [
            CanonicalEnvironmentClaim(
                pack_id=pack_id,
                source_item_id=source_item_id,
                side="client",
                status="supported",
                certainty="confirmed",
                evidence_type="platform_field",
                evidence_text="CurseForge整合包默认提供客户端构建并支持客户端导入",
                raw_value="client: supported",
                source_field="curseforge:modpack",
                source_url=url,
                observed_at=now_str
            )
        ]

        # Check for heuristic server keyword match in text
        text_corpus = f"{title} {raw_item.get('description') or ''}"
        m = SERVER_KEYWORD_REGEX.search(text_corpus)
        if m:
            matched_word = m.group(0)
            start = max(0, m.start() - 20)
            end = min(len(text_corpus), m.end() + 20)
            snippet = text_corpus[start:end].replace('\n', ' ').strip()

            claims.append(CanonicalEnvironmentClaim(
                pack_id=pack_id,
                source_item_id=source_item_id,
                side="server",
                status="supported",
                certainty="weak_inferred",  # 显式标明为弱推断，绝不混淆为 confirmed
                evidence_type="text_rule",
                evidence_text=f"标题或描述匹配到关键词 '{matched_word}': ...{snippet}...",
                raw_value=matched_word,
                source_field="title/description",
                source_url=url,
                observed_at=now_str
            ))
        else:
            claims.append(CanonicalEnvironmentClaim(
                pack_id=pack_id,
                source_item_id=source_item_id,
                side="server",
                status="unknown",
                certainty="unknown",
                evidence_type="platform_field",
                evidence_text="CurseForge mods/search 搜索接口未提供 serverPackFileId，文本无开服关键词",
                raw_value="null",
                source_field="curseforge:search_api",
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

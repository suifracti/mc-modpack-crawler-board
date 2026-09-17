"""
Bilibili Platform Adapter for Architecture V2.
Extracts clean structured records from crawler_output/bilibili_modpacks.json.
Fixes semantic naming: transforms legacy desc_updated_at into pinned_comment_at.
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
    CanonicalRelatedVideo,
    CanonicalMetrics,
    CanonicalEnvironmentClaim,
    CanonicalPackBundle,
)

class BilibiliAdapter(BaseAdapter):
    platform_name = "bilibili"

    def get_source_file_path(self) -> str:
        return os.path.join(self.workspace_root, "crawler_output", "bilibili_modpacks.json")

    def adapt_item(self, raw_item: Dict[str, Any], idx: int) -> CanonicalPackBundle:
        bvid = raw_item.get("bvid") or f"BV_unknown_{idx}"
        pack_id = f"pack_bilibili_{bvid}"
        source_item_id = f"bilibili:{bvid}"
        title = (raw_item.get("title") or f"B站整合包 {bvid}").strip()
        url = raw_item.get("url") or f"https://www.bilibili.com/video/{bvid}"

        now_str = "2026-09-17 12:00:00"
        pub_time = raw_item.get("pub_time") or None
        
        # 语义校正：将历史错误命名的 desc_updated_at 正确识别为 pinned_comment_at 与 last_observed_update_at
        pinned_comment_at = raw_item.get("desc_updated_at") or None
        last_observed_update_at = pinned_comment_at or pub_time or now_str

        # 1. Canonical Pack
        pack = CanonicalPack(
            id=pack_id,
            preferred_title=title,
            normalized_title=self.normalize_title(title),
            summary=(raw_item.get("desc") or "")[:1000] or None,
            primary_platform="bilibili",
            created_at=pub_time or now_str,
            updated_at=last_observed_update_at,
        )

        # 2. Source Item
        extra_dict = {
            "bvid": bvid,
            "aid": raw_item.get("aid"),
            "cid": raw_item.get("cid"),
            "qq_group": raw_item.get("qq_group"),
            "extract_code": raw_item.get("extract_code"),
            "pack_version": raw_item.get("pack_version"),
            "has_group_version": bool(raw_item.get("has_group_version")),
            "group_version_note": raw_item.get("group_version_note"),
            "pinned_comment": raw_item.get("pinned_comment"),
            "pinned_comment_at": pinned_comment_at,
            "last_observed_update_at": last_observed_update_at,
            "subtitle_summary": raw_item.get("subtitle_summary"),
        }

        source_item = CanonicalSourceItem(
            id=source_item_id,
            pack_id=pack_id,
            platform="bilibili",
            source_id=bvid,
            slug=bvid,
            source_url=url,
            title=title,
            author=raw_item.get("author") or "未知UP主",
            description=raw_item.get("desc") or None,
            icon_url=raw_item.get("pic") or None,
            published_at=pub_time,
            modified_at=last_observed_update_at,
            raw_ref=f"crawler_output/bilibili_modpacks.json#bvid={bvid}",
            extra_json=json.dumps(extra_dict, ensure_ascii=False),
            created_at=pub_time or now_str,
            updated_at=last_observed_update_at,
        )

        # 3. Releases
        releases = []
        mc_vers = raw_item.get("all_versions") or []
        if not mc_vers and raw_item.get("mc_version") and raw_item.get("mc_version") != "未知":
            mc_vers = [raw_item["mc_version"]]

        pack_ver = raw_item.get("pack_version") or "发布版"
        releases.append(CanonicalRelease(
            id=f"{source_item_id}:rel:latest",
            pack_id=pack_id,
            source_item_id=source_item_id,
            version_name=pack_ver,
            version_type="group_test" if raw_item.get("has_group_version") else "release",
            release_date=pinned_comment_at or pub_time,
            is_latest=True,
            changelog=raw_item.get("group_version_note") or raw_item.get("pinned_comment"),
            downloads_count=None,
            mc_versions=mc_vers,
            extra_json=None,
            created_at=now_str
        ))

        # 4. Download Links
        download_links = []
        for l in (raw_item.get("download_links") or []):
            if isinstance(l, dict) and l.get("url"):
                l_type_raw = str(l.get("name") or l.get("type") or "OTHER").upper()
                if "百度" in l_type_raw: link_type = "BAIDU"
                elif "夸克" in l_type_raw: link_type = "QUARK"
                elif "蓝奏" in l_type_raw: link_type = "LANZOU"
                elif "123" in l_type_raw: link_type = "PAN123"
                elif "APP" in l_type_raw: link_type = "APP_IMPORT"
                elif "OFFICIAL" in l_type_raw: link_type = "OFFICIAL"
                else: link_type = "OTHER"

                download_links.append(CanonicalDownloadLink(
                    source_item_id=source_item_id,
                    link_type=link_type,
                    url=l["url"],
                    label=l.get("name") or l.get("type") or "网盘下载",
                    extract_code=raw_item.get("extract_code"),
                    is_server=False,
                    release_id=f"{source_item_id}:rel:latest",
                    created_at=now_str
                ))

        # 5. Related Videos
        related_videos = [
            CanonicalRelatedVideo(
                source_item_id=source_item_id,
                bvid=bvid,
                title=title,
                author=raw_item.get("author") or "",
                url=url,
                aid=raw_item.get("aid"),
                published_at=pub_time,
                views=raw_item.get("views"),
                danmaku=raw_item.get("danmaku"),
                likes=raw_item.get("likes"),
                coins=raw_item.get("coins"),
                created_at=now_str
            )
        ]

        # 6. Loaders & Categories
        loaders = [l for l in (raw_item.get("loaders") or []) if l]
        categories = [c for c in (raw_item.get("categories") or []) if c]

        # 7. Metrics
        metrics = CanonicalMetrics(
            source_item_id=source_item_id,
            observed_at=now_str,
            views=raw_item.get("views"),
            likes=raw_item.get("likes"),
            coins=raw_item.get("coins"),
            favorites=raw_item.get("favorites"),
            comments_count=raw_item.get("reply")
        )

        # 8. Environment Claims
        claims = [
            CanonicalEnvironmentClaim(
                pack_id=pack_id,
                source_item_id=source_item_id,
                side="client",
                status="supported",
                certainty="confirmed",
                evidence_type="platform_field",
                evidence_text="B站自制整合包默认支持单人客户端游玩",
                raw_value="client: supported",
                source_field="bilibili:video",
                source_url=url,
                observed_at=now_str
            )
        ]
        has_server = bool(raw_item.get("has_server"))
        claims.append(CanonicalEnvironmentClaim(
            pack_id=pack_id,
            source_item_id=source_item_id,
            side="server",
            status="supported" if has_server else "unsupported",
            certainty="inferred" if has_server else "weak_inferred",
            evidence_type="text_rule",
            evidence_text="B站简介/置顶评论/网盘包含服务端或开服关键词" if has_server else "视频简介未提及专用服务端",
            raw_value=str(has_server),
            source_field="desc/pinned_comment/download_links",
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
            related_videos=related_videos,
            metrics=metrics,
            environment_claims=claims
        )

"""
Bilibili Platform Adapter for Architecture V2.
Extracts clean structured records from crawler_output/bilibili_modpacks.json.
Fixes semantic naming: transforms legacy desc_updated_at into pinned_comment_at.
"""
import json
import os
import re
from datetime import datetime, timezone
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

    def __init__(self, workspace_root: Optional[str] = None):
        super().__init__(workspace_root)
        source_path = self.get_source_file_path()
        if os.path.exists(source_path):
            mtime = os.path.getmtime(source_path)
            self.snapshot_mtime_str = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        else:
            self.snapshot_mtime_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    def get_source_file_path(self) -> str:
        return os.path.join(self.workspace_root, "crawler_output", "bilibili_modpacks.json")

    def adapt_item(self, raw_item: Dict[str, Any], idx: int) -> CanonicalPackBundle:
        bvid = raw_item.get("bvid") or f"BV_unknown_{idx}"
        pack_id = f"pack_bilibili_{bvid}"
        source_item_id = f"bilibili:{bvid}"
        title = (raw_item.get("title") or f"B站整合包 {bvid}").strip()
        url = raw_item.get("url") or f"https://www.bilibili.com/video/{bvid}"

        now_str = self.snapshot_mtime_str
        pub_time = raw_item.get("pub_time") or None
        
        # 语义校正 (Phase 1.1):
        # 1. pinned_comment_at 严格对应评论 ctime
        pinned_comment_at = raw_item.get("desc_updated_at") or None
        # 2. update_notice_at 仅在置顶评论包含版本更新公告特征时成立
        pinned_text = str(raw_item.get("pinned_comment") or "")
        is_update_notice = bool(raw_item.get("has_group_version")) or bool(
            re.search(r'(?:更新|新版本|修复|v\d|已更新|升级)', pinned_text)
        )
        update_notice_at = pinned_comment_at if (pinned_comment_at and is_update_notice) else None
        # 3. last_observed_update_at 对应 Crawler 观测同步时间，真实来源为快照文件修改时间
        last_observed_update_at = self.snapshot_mtime_str

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
            "update_notice_at": update_notice_at,
            "last_observed_update_at": last_observed_update_at,
            "subtitle_summary": raw_item.get("subtitle_summary"),
            "subtitle_text": raw_item.get("subtitle_text") or "",
            "has_subtitle": bool(raw_item.get("has_subtitle")),
            "duration": raw_item.get("duration") or 0,
            "pub_timestamp": raw_item.get("pub_timestamp") or 0,
            "mod_count": raw_item.get("mod_count") or 0,
            "coins": raw_item.get("coins") or 0,
            "danmaku": raw_item.get("danmaku") or 0,
            "share": raw_item.get("share") or 0,
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

        # 3. Releases (Release Provenance: 不凭空伪造 published_at)
        releases = []
        mc_vers = raw_item.get("all_versions") or []
        if not mc_vers and raw_item.get("mc_version") and raw_item.get("mc_version") != "未知":
            mc_vers = [raw_item["mc_version"]]

        pack_ver = raw_item.get("pack_version") or "发布版"
        rel_extra = {
            "source": "bilibili_video",
            "evidence_type": "pinned_comment_notice" if update_notice_at else "video_description",
            "announced_at": update_notice_at or pinned_comment_at,
            "observed_at": last_observed_update_at,
        }
        releases.append(CanonicalRelease(
            id=f"{source_item_id}:rel:latest",
            pack_id=pack_id,
            source_item_id=source_item_id,
            version_name=pack_ver,
            version_type="group_test" if raw_item.get("has_group_version") else "release",
            release_date=None,  # 严谨语义：B站无官方版本发布时间戳字段，设为 NULL
            is_latest=True,
            changelog=raw_item.get("group_version_note") or raw_item.get("pinned_comment"),
            downloads_count=None,
            mc_versions=mc_vers,
            extra_json=json.dumps(rel_extra, ensure_ascii=False),
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

        # 8. Environment Claims (Phase 1.1 Strict Semantics)
        claims = []
        full_text = f"{title} {raw_item.get('desc') or ''} {raw_item.get('pinned_comment') or ''}"

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
                source_field="desc/pinned_comment",
                source_url=url,
                observed_at=now_str
            ))
        else:
            claims.append(self.create_unknown_claim(
                pack_id, source_item_id, "client",
                "B站视频未提供结构化客户端运行环境字段",
                url, now_str
            ))

        # Server Claim
        server_file_hit = None
        for dl in (raw_item.get("download_links") or []):
            dl_str = f"{dl.get('name', '')} {dl.get('type', '')} {dl.get('url', '')}"
            m_f = self.SERVER_FILE_REGEX.search(dl_str)
            if m_f:
                server_file_hit = (m_f.group(0), dl_str[:80])
                break

        m_s_neg = self.SERVER_TEXT_NEG_REGEX.search(full_text)
        m_s_pos = self.SERVER_TEXT_POS_REGEX.search(full_text)

        if server_file_hit:
            claims.append(CanonicalEnvironmentClaim(
                pack_id=pack_id,
                source_item_id=source_item_id,
                side="server",
                status="supported",
                certainty="strong_inferred",
                evidence_type="file_name",
                evidence_text=f"网盘链接包含服务端包: {server_file_hit[1]}",
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
                evidence_text=self.extract_snippet(full_text, m_s_neg),
                raw_value=m_s_neg.group(0),
                source_field="desc/pinned_comment",
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
                source_field="desc/pinned_comment",
                source_url=url,
                observed_at=now_str
            ))
        else:
            claims.append(self.create_unknown_claim(
                pack_id, source_item_id, "server",
                "视频简介与置顶评论未提及开服支持或服务端文件",
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
            related_videos=related_videos,
            metrics=metrics,
            environment_claims=claims
        )

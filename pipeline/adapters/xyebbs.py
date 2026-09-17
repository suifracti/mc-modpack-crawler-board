"""
XYEBBS Platform Adapter for Architecture V2.
Extracts clean structured records from crawler_output/xyebbs_modpacks.json.
"""
import json
import os
import re
from typing import Dict, Any, Optional, List
from pipeline.adapters.base import BaseAdapter
from pipeline.models.canonical import (
    CanonicalPack,
    CanonicalSourceItem,
    CanonicalAlias,
    CanonicalRelease,
    CanonicalDownloadLink,
    CanonicalMetrics,
    CanonicalEnvironmentClaim,
    CanonicalPackBundle,
)

VALID_URL_SCHEMES = ("http://", "https://", "ftp://", "magnet:")

def clean_date_str(val: Any) -> Optional[str]:
    if not val or not isinstance(val, str):
        return None
    val = val.strip()
    if val in ('未知', '未知时间', 'N/A', '-', ''):
        return None
    return val

def clean_download_link_item(dl: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    raw_url = dl.get("url")
    if not raw_url or not isinstance(raw_url, str):
        return None
    raw_url = raw_url.strip()
    if raw_url.lower() in ("null", "undefined", "none", "neoforge", "forge", "fabric"):
        return None
    if "qq群" in raw_url.lower():
        return None
    if len(raw_url) > 1000 or any(c in raw_url for c in ('\n', '\r')):
        return None
    
    clean_url = None
    extract_code = dl.get("extract_code")

    if raw_url.startswith(VALID_URL_SCHEMES) and ' ' not in raw_url:
        clean_url = raw_url
    else:
        m = re.search(r'https?://[^\s<>"\']+|ftp://[^\s<>"\']+|magnet:\?[^\s<>"\']+', raw_url)
        if m:
            clean_url = m.group(0).rstrip('.,;!?#')
            if not extract_code:
                m_code = re.search(r'(?:提取码|pwd|密码)[:：\s]+([a-zA-Z0-9]{4,8})', raw_url)
                if m_code:
                    extract_code = m_code.group(1)
    
    if not clean_url or len(clean_url) > 1000:
        return None

    return {
        "url": clean_url,
        "extract_code": extract_code
    }

class XyebbsAdapter(BaseAdapter):
    platform_name = "xyebbs"

    def get_source_file_path(self) -> str:
        return os.path.join(self.workspace_root, "crawler_output", "xyebbs_modpacks.json")

    def adapt_item(self, raw_item: Dict[str, Any], idx: int) -> CanonicalPackBundle:
        pid = str(raw_item.get("project_id") or idx + 1)
        pack_id = f"pack_xyebbs_{pid}"
        source_item_id = f"xyebbs:{pid}"
        title = (raw_item.get("title") or f"XYEBBS 模组包 #{pid}").strip()
        url = raw_item.get("url") or f"https://www.xyebbs.com/thread-{pid}-1-1.html"
        now_str = "2026-09-17 12:00:00"

        pub_at = clean_date_str(raw_item.get("date_created"))
        mod_at = clean_date_str(raw_item.get("date_modified"))

        # 1. Canonical Pack
        pack = CanonicalPack(
            id=pack_id,
            preferred_title=title,
            normalized_title=self.normalize_title(title),
            summary=(raw_item.get("description") or "")[:1000] or None,
            primary_platform="xyebbs",
            created_at=pub_at or now_str,
            updated_at=mod_at or now_str,
        )

        # 2. Source Item
        extra_dict = {
            "english_name": raw_item.get("english_name"),
            "views": raw_item.get("views"),
            "likes": raw_item.get("likes"),
            "comments": raw_item.get("comments"),
            "gallery": raw_item.get("gallery") or [],
            "head_url": raw_item.get("head_url"),
            "source_meta": raw_item.get("source_meta") or {},
            "created_timestamp": raw_item.get("created_timestamp"),
            "modified_timestamp": raw_item.get("modified_timestamp"),
            "releases_data": raw_item.get("releases_data") or [],
        }
        source_item = CanonicalSourceItem(
            id=source_item_id,
            pack_id=pack_id,
            platform="xyebbs",
            source_id=pid,
            slug=raw_item.get("slug") or pid,
            source_url=url,
            title=title,
            author=raw_item.get("author") or "未知作者",
            description=raw_item.get("description") or None,
            icon_url=raw_item.get("icon_url") or None,
            published_at=pub_at,
            modified_at=mod_at,
            raw_ref=f"crawler_output/xyebbs_modpacks.json#id={pid}",
            extra_json=json.dumps(extra_dict, ensure_ascii=False),
            created_at=pub_at or now_str,
            updated_at=mod_at or now_str,
        )

        # 3. Aliases
        aliases = []
        if raw_item.get("english_name"):
            aliases.append(CanonicalAlias(
                pack_id=pack_id,
                alias_type="english_name",
                alias_text=raw_item["english_name"].strip(),
                source="xyebbs",
                created_at=now_str
            ))

        # 4. Releases
        releases = []
        raw_releases = raw_item.get("releases_data") or []
        for r_idx, r in enumerate(raw_releases):
            r_name = r.get("label") or r.get("name") or r.get("title") or r.get("version_name") or f"Release_{r_idx+1}"
            r_date = clean_date_str(r.get("createDate") or r.get("date")) or pub_at
            r_mc = r.get("mc_versions") or raw_item.get("all_versions") or []
            r_extra = {"links": r.get("links") or []}
            releases.append(CanonicalRelease(
                id=f"{source_item_id}:rel:{r.get('id') or r_idx}",
                pack_id=pack_id,
                source_item_id=source_item_id,
                version_name=r_name,
                version_type="release",
                release_date=r_date,
                is_latest=(r_idx == 0),
                changelog=r.get("notes") or r.get("changelog"),
                downloads_count=r.get("downloadCount") or r.get("downloads"),
                mc_versions=r_mc,
                extra_json=json.dumps(r_extra, ensure_ascii=False),
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

        # 5. Download Links
        import urllib.parse
        download_links = []
        has_server_link = False
        server_evidence = ""
        server_raw_value = ""

        for dl in (raw_item.get("download_links") or []):
            if isinstance(dl, dict) and dl.get("url"):
                cleaned = clean_download_link_item(dl)
                if not cleaned:
                    continue
                clean_url = cleaned["url"]
                clean_code = cleaned["extract_code"]
                l_name = dl.get("name") or "下载"
                dl_texts = " ".join([
                    str(dl.get("name") or ""),
                    str(dl.get("filename") or ""),
                    str(dl.get("version") or ""),
                    urllib.parse.unquote(str(clean_url))
                ])
                m_srv = self.SERVER_FILE_REGEX.search(dl_texts)
                is_server = bool(m_srv)
                if is_server and not has_server_link:
                    has_server_link = True
                    server_evidence = dl.get("filename") or l_name
                    server_raw_value = m_srv.group(0)

                download_links.append(CanonicalDownloadLink(
                    source_item_id=source_item_id,
                    link_type=dl.get("type") or "OTHER",
                    url=clean_url,
                    label=l_name,
                    extract_code=clean_code,
                    is_server=is_server,
                    created_at=now_str
                ))

        # 6. Loaders & Categories
        loaders = [l for l in (raw_item.get("loaders") or []) if l]
        categories = [c for c in (raw_item.get("categories") or []) if c]

        # 7. Metrics
        metrics = CanonicalMetrics(
            source_item_id=source_item_id,
            observed_at=now_str,
            downloads=raw_item.get("downloads"),
            views=raw_item.get("views"),
            likes=raw_item.get("likes"),
            comments_count=raw_item.get("comments")
        )

        # 8. Environment Claims (Phase 1.1 Strict Semantics)
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
                "XYEBBS未提供结构化客户端运行环境字段",
                url, now_str
            ))

        # Server Claim
        m_s_neg = self.SERVER_TEXT_NEG_REGEX.search(full_text)
        m_s_pos = self.SERVER_TEXT_POS_REGEX.search(full_text)

        if has_server_link:
            claims.append(CanonicalEnvironmentClaim(
                pack_id=pack_id,
                source_item_id=source_item_id,
                side="server",
                status="supported",
                certainty="strong_inferred",
                evidence_type="file_name",
                evidence_text=f"网盘链接名称包含服务端: {server_evidence}",
                raw_value=server_raw_value or "服务端",
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
                "XYEBBS帖子未提供服务端下载且正文未声明开服支持",
                url, now_str
            ))

        return CanonicalPackBundle(
            pack=pack,
            source_item=source_item,
            aliases=aliases,
            releases=releases,
            loaders=loaders,
            categories=categories,
            download_links=download_links,
            related_videos=[],
            metrics=metrics,
            environment_claims=claims
        )

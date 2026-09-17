"""
MCMod Platform Adapter for Architecture V2.
Extracts clean structured records from crawler_output/mcmod_modpacks.json and details cache.
Strictly avoids storing pre-rendered HTML cells (c0-c6).
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
    CanonicalMetrics,
    CanonicalEnvironmentClaim,
    CanonicalIncludedMod,
    CanonicalTrendPoint,
    CanonicalSourceComment,
    CanonicalPackBundle,
)

class MCModAdapter(BaseAdapter):
    platform_name = "mcmod"

    def __init__(self, workspace_root: Optional[str] = None):
        super().__init__(workspace_root)
        self.details_cache: Dict[str, Any] = {}
        self.full_details: Dict[str, Any] = {}
        self._load_details_cache()

    def get_source_file_path(self) -> str:
        return os.path.join(self.workspace_root, "crawler_output", "mcmod_modpacks.json")

    def _load_details_cache(self) -> None:
        cache_path = os.path.join(self.workspace_root, "crawler_output", "mcmod_details_cache.json")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    self.details_cache = json.load(f)
            except Exception:
                self.details_cache = {}

        full_path = os.path.join(self.workspace_root, "crawler_output", "mcmod_full_details.json")
        if os.path.exists(full_path):
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    self.full_details = json.load(f)
            except Exception:
                self.full_details = {}

    def adapt_item(self, raw_item: Dict[str, Any], idx: int) -> CanonicalPackBundle:
        mid = str(raw_item.get("mid") or raw_item.get("project_id") or idx + 1)
        pack_id = f"pack_mcmod_{mid}"
        source_item_id = f"mcmod:{mid}"
        title = (raw_item.get("title") or f"整合包 #{mid}").strip()
        url = raw_item.get("url") or f"https://www.mcmod.cn/modpack/{mid}.html"
        
        cached_info = self.details_cache.get(mid, {})
        # Use clean text summary, never HTML!
        summary = cached_info.get("desc") or cached_info.get("text") or ""
        if summary and ("<" in summary and ">" in summary):
            summary = re.sub(r'<[^>]+>', '', summary).strip()

        now_str = "2026-09-17 12:00:00"

        # 1. Canonical Pack
        pack = CanonicalPack(
            id=pack_id,
            preferred_title=title,
            normalized_title=self.normalize_title(title),
            summary=summary[:1000] if summary else None,
            primary_platform="mcmod",
            created_at=now_str,
            updated_at=now_str,
        )

        # 2. Source Item
        pub_at = raw_item.get("release_date") or None
        mod_at = raw_item.get("last_update_date") or None
        intro_images = cached_info.get("images") or cached_info.get("intro_images") or []
        extra_dict = {
            "type_name": raw_item.get("type_name"),
            "mold_id": raw_item.get("mold_id"),
            "trend_dates": raw_item.get("trend_dates"),
            "trend_vals": raw_item.get("trend_vals"),
            "intro_images": intro_images,
            "has_server": bool(raw_item.get("has_server")),
            "recommend": raw_item.get("recommend") or 0,
            "favorite": raw_item.get("favorite") or 0,
        }
        source_item = CanonicalSourceItem(
            id=source_item_id,
            pack_id=pack_id,
            platform="mcmod",
            source_id=mid,
            slug=mid,
            source_url=url,
            title=title,
            author=raw_item.get("author") or "未知",
            description=summary or None,
            icon_url=raw_item.get("cover_url") or None,
            published_at=pub_at,
            modified_at=mod_at,
            raw_ref=f"crawler_output/mcmod_modpacks.json#mid={mid}",
            extra_json=json.dumps(extra_dict, ensure_ascii=False),
            created_at=now_str,
            updated_at=now_str,
        )

        # 3. Aliases
        aliases = []
        for former in (raw_item.get("former_titles") or []):
            if former and former.strip() and former.strip() != title:
                aliases.append(CanonicalAlias(
                    pack_id=pack_id,
                    alias_type="former_title",
                    alias_text=former.strip(),
                    source="mcmod",
                    created_at=now_str
                ))
        if raw_item.get("title_en"):
            aliases.append(CanonicalAlias(
                pack_id=pack_id,
                alias_type="english_name",
                alias_text=raw_item["title_en"].strip(),
                source="mcmod",
                created_at=now_str
            ))
        if raw_item.get("title_cn") and raw_item["title_cn"] != title:
            aliases.append(CanonicalAlias(
                pack_id=pack_id,
                alias_type="chinese_name",
                alias_text=raw_item["title_cn"].strip(),
                source="mcmod",
                created_at=now_str
            ))

        # 4. Loaders & Categories
        loaders = []
        raw_text_for_loaders = f"{title} {' '.join(raw_item.get('tags') or [])}"
        for ldr in ["Fabric", "Forge", "NeoForge", "Quilt"]:
            if re.search(rf'\b{ldr}\b', raw_text_for_loaders, re.IGNORECASE):
                loaders.append(ldr)

        categories = []
        if raw_item.get("type_name"):
            categories.append(raw_item["type_name"].strip())
        for c in (raw_item.get("categories") or []):
            if c and c.strip() and c.strip() not in categories:
                categories.append(c.strip())
        for t in (raw_item.get("tags") or []):
            if t and t.strip() and t.strip() not in categories:
                categories.append(t.strip())

        # 5. Releases
        releases = []
        mc_vers = raw_item.get("mc_versions") or []
        if not mc_vers and raw_item.get("mc_version") and raw_item.get("mc_version") != "未知":
            mc_vers = [raw_item["mc_version"]]
        
        ver_name = raw_item.get("latest_version") or (mc_vers[0] if mc_vers else "最新版")
        releases.append(CanonicalRelease(
            id=f"{source_item_id}:rel:latest",
            pack_id=pack_id,
            source_item_id=source_item_id,
            version_name=ver_name,
            version_type="release",
            release_date=mod_at or pub_at,
            is_latest=True,
            downloads_count=None,
            mc_versions=mc_vers,
            extra_json=None,
            created_at=now_str
        ))

        # 6. Metrics
        metrics = CanonicalMetrics(
            source_item_id=source_item_id,
            observed_at=now_str,
            views=raw_item.get("views"),
            likes=raw_item.get("recommend"),
            favorites=raw_item.get("favorite"),
            score=float(raw_item.get("score")) if raw_item.get("score") is not None else None,
            comments_count=raw_item.get("comments"),
            red_votes=raw_item.get("red_votes"),
            black_votes=raw_item.get("black_votes"),
            trend_days=raw_item.get("trend_days"),
            trend_latest=raw_item.get("trend_latest")
        )

        # 7. Environment Claims (Phase 1.1 Strict Semantics)
        claims = []
        full_text = f"{title} {summary or ''}"

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
                "MC百科未提供结构化客户端运行环境字段",
                url, now_str
            ))

        # Server Claim
        m_s_neg = self.SERVER_TEXT_NEG_REGEX.search(full_text)
        m_s_pos = self.SERVER_TEXT_POS_REGEX.search(full_text)
        if m_s_neg:
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
                "MC百科页面与描述未提供服务端支持证据或声明",
                url, now_str
            ))

        # 7. Included Mods
        included_mods = []
        full_item = self.full_details.get(mid, {})
        mods_list = full_item.get("mods") or raw_item.get("mods") or []
        for s_idx, m in enumerate(mods_list):
            if isinstance(m, dict):
                m_name = (m.get("name") or m.get("title") or "").strip()
                if not m_name:
                    continue
                included_mods.append(CanonicalIncludedMod(
                    source_item_id=source_item_id,
                    mod_name=m_name,
                    mod_title=m.get("title") or m_name,
                    mod_version=m.get("version"),
                    mod_url=m.get("url") or (f"https://www.mcmod.cn/class/{m['class_id']}.html" if m.get("class_id") else None),
                    class_id=str(m.get("class_id")) if m.get("class_id") else None,
                    category_id=str(m.get("category_id")) if m.get("category_id") else None,
                    category_name=m.get("category_name") or "未分类",
                    category_url=m.get("category_url"),
                    sort_order=s_idx
                ))
            elif isinstance(m, str) and m.strip():
                m_name = m.strip()
                included_mods.append(CanonicalIncludedMod(
                    source_item_id=source_item_id,
                    mod_name=m_name,
                    mod_title=m_name,
                    mod_version=None,
                    mod_url=None,
                    class_id=None,
                    category_id=None,
                    category_name="未分类",
                    category_url=None,
                    sort_order=s_idx
                ))

        # 8. Trend Points
        trend_points = []
        t_dates = (raw_item.get("trend_dates") or "").split(",")
        t_vals = (raw_item.get("trend_vals") or "").split(",")
        for d, v in zip(t_dates, t_vals):
            d = d.strip()
            v = v.strip()
            if d and v:
                try:
                    trend_points.append(CanonicalTrendPoint(
                        source_item_id=source_item_id,
                        point_date=d,
                        views_delta=float(v)
                    ))
                except ValueError:
                    pass

        # 9. Source Comments
        com_n = int(raw_item.get("comments") or 0)
        source_comments = CanonicalSourceComment(
            source_item_id=source_item_id,
            page_count=com_n,
            true_count=0,
            comments_json="[]"
        )

        return CanonicalPackBundle(
            pack=pack,
            source_item=source_item,
            aliases=aliases,
            releases=releases,
            loaders=loaders,
            categories=categories,
            download_links=[],
            related_videos=[],
            metrics=metrics,
            environment_claims=claims,
            included_mods=included_mods,
            trend_points=trend_points,
            source_comments=source_comments
        )

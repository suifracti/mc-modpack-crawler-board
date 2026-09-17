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
    CanonicalPackBundle,
)

class MCModAdapter(BaseAdapter):
    platform_name = "mcmod"

    def __init__(self, workspace_root: Optional[str] = None):
        super().__init__(workspace_root)
        self.details_cache: Dict[str, Any] = {}
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
        extra_dict = {
            "type_name": raw_item.get("type_name"),
            "mold_id": raw_item.get("mold_id"),
            "trend_dates": raw_item.get("trend_dates"),
            "trend_vals": raw_item.get("trend_vals"),
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
            score=float(raw_item.get("score")) if raw_item.get("score") is not None else None,
            comments_count=raw_item.get("comments"),
            red_votes=raw_item.get("red_votes"),
            black_votes=raw_item.get("black_votes"),
            trend_days=raw_item.get("trend_days"),
            trend_latest=raw_item.get("trend_latest")
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
                evidence_text="MC百科整合包默认支持单人客户端运行",
                raw_value="client: supported",
                source_field="mcmod:mold",
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
            evidence_text="MC百科详情/更新记录标注包含服务端关键词" if has_server else "MC百科页面未标记专用开服包",
            raw_value=str(has_server),
            source_field="description/has_server",
            source_url=url,
            observed_at=now_str
        ))

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
            environment_claims=claims
        )

"""
Canonical Data Models for Architecture V2.
Encapsulates dataclasses for Packs, Source Items, Environment Claims, etc.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class CanonicalPack:
    id: str                                    # e.g. "pack_mcmod_722"
    preferred_title: str
    normalized_title: str
    summary: Optional[str] = None
    primary_platform: str = ""
    created_at: str = ""
    updated_at: str = ""

@dataclass
class CanonicalSourceItem:
    id: str                                    # e.g. "mcmod:722"
    pack_id: str
    platform: str
    source_id: str
    slug: Optional[str] = None
    source_url: str = ""
    title: str = ""
    author: Optional[str] = None
    description: Optional[str] = None
    icon_url: Optional[str] = None
    published_at: Optional[str] = None
    modified_at: Optional[str] = None
    raw_ref: Optional[str] = None
    extra_json: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

@dataclass
class CanonicalAlias:
    pack_id: str
    alias_type: str                            # 'former_title', 'english_name', 'chinese_name', 'search_keyword'
    alias_text: str
    source: str
    created_at: str = ""

@dataclass
class CanonicalRelease:
    id: str                                    # e.g. "mcmod:722:rel:0"
    pack_id: str
    source_item_id: str
    version_name: str
    version_type: str = "release"              # 'release', 'beta', 'alpha', 'group_test', 'latest'
    release_date: Optional[str] = None
    is_latest: bool = False
    changelog: Optional[str] = None
    downloads_count: Optional[int] = None
    mc_versions: List[str] = field(default_factory=list)
    extra_json: Optional[str] = None
    created_at: str = ""

@dataclass
class CanonicalDownloadLink:
    source_item_id: str
    link_type: str                             # 'OFFICIAL', 'APP_IMPORT', 'BAIDU', 'QUARK', 'LANZOU', 'PAN123', 'OTHER'
    url: str
    label: Optional[str] = None
    extract_code: Optional[str] = None
    is_server: bool = False
    release_id: Optional[str] = None
    created_at: str = ""

@dataclass
class CanonicalRelatedVideo:
    source_item_id: str
    bvid: str
    title: str
    author: str
    url: str
    aid: Optional[int] = None
    published_at: Optional[str] = None
    views: Optional[int] = None
    danmaku: Optional[int] = None
    likes: Optional[int] = None
    coins: Optional[int] = None
    created_at: str = ""

@dataclass
class CanonicalMetrics:
    source_item_id: str
    observed_at: str
    views: Optional[int] = None
    downloads: Optional[int] = None
    followers: Optional[int] = None
    likes: Optional[int] = None
    coins: Optional[int] = None
    favorites: Optional[int] = None
    comments_count: Optional[int] = None
    score: Optional[float] = None
    red_votes: Optional[int] = None
    black_votes: Optional[int] = None
    trend_days: Optional[int] = None
    trend_latest: Optional[int] = None

@dataclass
class CanonicalEnvironmentClaim:
    pack_id: str
    source_item_id: str
    side: str                                  # 'client', 'server', 'both'
    status: str                                # 'required', 'optional', 'unsupported', 'supported', 'unknown'
    certainty: str                             # 'confirmed', 'inferred', 'weak_inferred', 'unknown'
    evidence_type: str                         # 'platform_field', 'file_name', 'text_rule', 'url_parameter', 'user_report'
    evidence_text: Optional[str] = None
    raw_value: Optional[str] = None
    source_field: Optional[str] = None
    source_url: Optional[str] = None
    observed_at: str = ""

@dataclass
class CanonicalIncludedMod:
    source_item_id: str
    mod_name: str
    mod_title: Optional[str] = None
    mod_version: Optional[str] = None
    mod_url: Optional[str] = None
    class_id: Optional[str] = None
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    category_url: Optional[str] = None
    sort_order: int = 0

@dataclass
class CanonicalTrendPoint:
    source_item_id: str
    point_date: str
    views_delta: float

@dataclass
class CanonicalSourceComment:
    source_item_id: str
    page_count: int = 0
    true_count: int = 0
    comments_json: str = "[]"

@dataclass
class CanonicalPackBundle:
    """A bundle representing 1 canonical pack and all its associated source items, releases, links, claims."""
    pack: CanonicalPack
    source_item: CanonicalSourceItem
    aliases: List[CanonicalAlias] = field(default_factory=list)
    releases: List[CanonicalRelease] = field(default_factory=list)
    loaders: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    download_links: List[CanonicalDownloadLink] = field(default_factory=list)
    related_videos: List[CanonicalRelatedVideo] = field(default_factory=list)
    metrics: Optional[CanonicalMetrics] = None
    environment_claims: List[CanonicalEnvironmentClaim] = field(default_factory=list)
    included_mods: List[CanonicalIncludedMod] = field(default_factory=list)
    trend_points: List[CanonicalTrendPoint] = field(default_factory=list)
    source_comments: Optional[CanonicalSourceComment] = None

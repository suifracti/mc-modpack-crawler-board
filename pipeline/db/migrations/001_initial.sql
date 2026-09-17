-- Migration 001: Initial Architecture V2 Schema
-- See pipeline/db/schema.sql for documentation.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS ingest_runs (
    run_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL DEFAULT 'running',
    notes TEXT
);

CREATE TABLE IF NOT EXISTS raw_snapshot_refs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT REFERENCES ingest_runs(run_id) ON DELETE SET NULL,
    platform TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    record_count INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS packs (
    id TEXT PRIMARY KEY,
    preferred_title TEXT NOT NULL,
    normalized_title TEXT NOT NULL,
    summary TEXT,
    primary_platform TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_packs_norm_title ON packs(normalized_title);
CREATE INDEX IF NOT EXISTS idx_packs_primary_platform ON packs(primary_platform);

CREATE TABLE IF NOT EXISTS source_items (
    id TEXT PRIMARY KEY,
    pack_id TEXT NOT NULL REFERENCES packs(id) ON DELETE CASCADE,
    platform TEXT NOT NULL,
    source_id TEXT NOT NULL,
    slug TEXT,
    source_url TEXT NOT NULL,
    title TEXT NOT NULL,
    author TEXT,
    description TEXT,
    icon_url TEXT,
    published_at TEXT,
    modified_at TEXT,
    raw_ref TEXT,
    extra_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT uq_platform_source UNIQUE(platform, source_id)
);

CREATE INDEX IF NOT EXISTS idx_source_items_pack_id ON source_items(pack_id);
CREATE INDEX IF NOT EXISTS idx_source_items_platform ON source_items(platform);
CREATE INDEX IF NOT EXISTS idx_source_items_source_url ON source_items(source_url);

CREATE TABLE IF NOT EXISTS aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pack_id TEXT NOT NULL REFERENCES packs(id) ON DELETE CASCADE,
    alias_type TEXT NOT NULL,
    alias_text TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL,
    CONSTRAINT uq_pack_alias UNIQUE(pack_id, alias_type, alias_text)
);

CREATE INDEX IF NOT EXISTS idx_aliases_pack_id ON aliases(pack_id);
CREATE INDEX IF NOT EXISTS idx_aliases_text ON aliases(alias_text);

CREATE TABLE IF NOT EXISTS releases (
    id TEXT PRIMARY KEY,
    pack_id TEXT NOT NULL REFERENCES packs(id) ON DELETE CASCADE,
    source_item_id TEXT NOT NULL REFERENCES source_items(id) ON DELETE CASCADE,
    version_name TEXT NOT NULL,
    version_type TEXT DEFAULT 'release',
    release_date TEXT,
    is_latest INTEGER DEFAULT 0,
    changelog TEXT,
    downloads_count INTEGER,
    extra_json TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_releases_pack_id ON releases(pack_id);
CREATE INDEX IF NOT EXISTS idx_releases_source_item ON releases(source_item_id);

CREATE TABLE IF NOT EXISTS release_mc_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    release_id TEXT NOT NULL REFERENCES releases(id) ON DELETE CASCADE,
    mc_version TEXT NOT NULL,
    is_primary INTEGER DEFAULT 0,
    CONSTRAINT uq_release_mc_ver UNIQUE(release_id, mc_version)
);

CREATE INDEX IF NOT EXISTS idx_rel_mc_version ON release_mc_versions(mc_version);

CREATE TABLE IF NOT EXISTS loaders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS source_item_loaders (
    source_item_id TEXT NOT NULL REFERENCES source_items(id) ON DELETE CASCADE,
    loader_id INTEGER NOT NULL REFERENCES loaders(id) ON DELETE CASCADE,
    PRIMARY KEY (source_item_id, loader_id)
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    slug TEXT,
    name TEXT NOT NULL,
    CONSTRAINT uq_platform_cat UNIQUE(platform, name)
);

CREATE TABLE IF NOT EXISTS source_item_categories (
    source_item_id TEXT NOT NULL REFERENCES source_items(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (source_item_id, category_id)
);

CREATE INDEX IF NOT EXISTS idx_cat_name ON categories(name);

CREATE TABLE IF NOT EXISTS download_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_item_id TEXT NOT NULL REFERENCES source_items(id) ON DELETE CASCADE,
    release_id TEXT REFERENCES releases(id) ON DELETE SET NULL,
    link_type TEXT NOT NULL,
    url TEXT NOT NULL,
    label TEXT,
    extract_code TEXT,
    is_server INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_download_links_source ON download_links(source_item_id);

CREATE TABLE IF NOT EXISTS related_videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_item_id TEXT NOT NULL REFERENCES source_items(id) ON DELETE CASCADE,
    bvid TEXT NOT NULL,
    aid INTEGER,
    title TEXT NOT NULL,
    author TEXT,
    url TEXT NOT NULL,
    published_at TEXT,
    views INTEGER,
    danmaku INTEGER,
    likes INTEGER,
    coins INTEGER,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_related_videos_bvid ON related_videos(bvid);
CREATE INDEX IF NOT EXISTS idx_related_videos_source ON related_videos(source_item_id);

CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_item_id TEXT NOT NULL REFERENCES source_items(id) ON DELETE CASCADE,
    views INTEGER,
    downloads INTEGER,
    followers INTEGER,
    likes INTEGER,
    coins INTEGER,
    favorites INTEGER,
    comments_count INTEGER,
    score REAL,
    red_votes INTEGER,
    black_votes INTEGER,
    trend_days INTEGER,
    trend_latest INTEGER,
    observed_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_metrics_source ON metrics(source_item_id);

CREATE TABLE IF NOT EXISTS environment_claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pack_id TEXT NOT NULL REFERENCES packs(id) ON DELETE CASCADE,
    source_item_id TEXT NOT NULL REFERENCES source_items(id) ON DELETE CASCADE,
    side TEXT NOT NULL,
    status TEXT NOT NULL,
    certainty TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    evidence_text TEXT,
    raw_value TEXT,
    source_field TEXT,
    source_url TEXT,
    observed_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_env_claims_pack ON environment_claims(pack_id);
CREATE INDEX IF NOT EXISTS idx_env_claims_certainty ON environment_claims(certainty);
CREATE INDEX IF NOT EXISTS idx_env_claims_side_status ON environment_claims(side, status);

CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT REFERENCES ingest_runs(run_id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    details_json TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_events_run ON audit_events(run_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_type ON audit_events(event_type);

CREATE VIRTUAL TABLE IF NOT EXISTS pack_fts USING fts5(
    pack_id UNINDEXED,
    title,
    aliases,
    author,
    summary,
    categories,
    tokenize = 'unicode61'
);

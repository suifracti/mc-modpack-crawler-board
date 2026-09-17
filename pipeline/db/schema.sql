-- Architecture V2 Canonical SQLite Schema (Phase 1)
-- Strict separation between canonical Pack entity and Source Items.
-- Environment claims record side, status, certainty, and verifiable evidence.
-- Provenance tracked via raw_snapshot_refs and audit_events.
-- Full-text search powered by SQLite FTS5.

PRAGMA foreign_keys = ON;

-- 1. 运行记录 (Ingestion Runs)
CREATE TABLE IF NOT EXISTS ingest_runs (
    run_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL DEFAULT 'running', -- 'running', 'completed', 'failed'
    notes TEXT
);

-- 2. 原始快照元数据 (Raw Snapshot Provenance)
CREATE TABLE IF NOT EXISTS raw_snapshot_refs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT REFERENCES ingest_runs(run_id) ON DELETE SET NULL,
    platform TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    content_hash TEXT NOT NULL,                -- SHA-256
    record_count INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

-- 3. Canonical 整合包主实体 (Packs)
-- Phase 1 策略: 1 source item -> 1 canonical pack (跨平台合并留待 Phase 2)
CREATE TABLE IF NOT EXISTS packs (
    id TEXT PRIMARY KEY,                       -- e.g. "pack_mcmod_722", "pack_bilibili_BV1BFjS65ENy"
    preferred_title TEXT NOT NULL,
    normalized_title TEXT NOT NULL,
    summary TEXT,
    primary_platform TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_packs_norm_title ON packs(normalized_title);
CREATE INDEX IF NOT EXISTS idx_packs_primary_platform ON packs(primary_platform);

-- 4. 平台来源条目 (Source Items)
CREATE TABLE IF NOT EXISTS source_items (
    id TEXT PRIMARY KEY,                       -- e.g. "mcmod:722", "bilibili:BV1BFjS65ENy"
    pack_id TEXT NOT NULL REFERENCES packs(id) ON DELETE CASCADE,
    platform TEXT NOT NULL,                    -- mcmod, bilibili, bbsmc, xyebbs, modrinth, curseforge
    source_id TEXT NOT NULL,                   -- e.g. "722", "BV1BFjS65ENy", "l9m9tuPN"
    slug TEXT,
    source_url TEXT NOT NULL,
    title TEXT NOT NULL,
    author TEXT,
    description TEXT,
    icon_url TEXT,
    published_at TEXT,                         -- ISO8601 or YYYY-MM-DD HH:MM
    modified_at TEXT,
    raw_ref TEXT,                              -- provenance reference
    extra_json TEXT,                           -- unmapped platform-specific attributes
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT uq_platform_source UNIQUE(platform, source_id)
);

CREATE INDEX IF NOT EXISTS idx_source_items_pack_id ON source_items(pack_id);
CREATE INDEX IF NOT EXISTS idx_source_items_platform ON source_items(platform);
CREATE INDEX IF NOT EXISTS idx_source_items_source_url ON source_items(source_url);

-- 5. 别名与历史曾用名 (Aliases)
CREATE TABLE IF NOT EXISTS aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pack_id TEXT NOT NULL REFERENCES packs(id) ON DELETE CASCADE,
    alias_type TEXT NOT NULL,                  -- former_title, english_name, chinese_name, search_keyword
    alias_text TEXT NOT NULL,
    source TEXT NOT NULL,                      -- e.g. "mcmod", "xyebbs"
    created_at TEXT NOT NULL,
    CONSTRAINT uq_pack_alias UNIQUE(pack_id, alias_type, alias_text)
);

CREATE INDEX IF NOT EXISTS idx_aliases_pack_id ON aliases(pack_id);
CREATE INDEX IF NOT EXISTS idx_aliases_text ON aliases(alias_text);

-- 6. 版本发布树 (Releases)
CREATE TABLE IF NOT EXISTS releases (
    id TEXT PRIMARY KEY,                       -- e.g. "mcmod:722:rel:0"
    pack_id TEXT NOT NULL REFERENCES packs(id) ON DELETE CASCADE,
    source_item_id TEXT NOT NULL REFERENCES source_items(id) ON DELETE CASCADE,
    version_name TEXT NOT NULL,                -- e.g. "v0.4.1", "1.0.0", "最新发布"
    version_type TEXT DEFAULT 'release',       -- release, beta, alpha, group_test, latest
    release_date TEXT,
    is_latest INTEGER DEFAULT 0,               -- 1 = true, 0 = false
    changelog TEXT,
    downloads_count INTEGER,
    extra_json TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_releases_pack_id ON releases(pack_id);
CREATE INDEX IF NOT EXISTS idx_releases_source_item ON releases(source_item_id);

-- 7. 版本对应的 MC 运行版本关联 (Release MC Versions)
CREATE TABLE IF NOT EXISTS release_mc_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    release_id TEXT NOT NULL REFERENCES releases(id) ON DELETE CASCADE,
    mc_version TEXT NOT NULL,                  -- e.g. "1.20.1", "1.19.2"
    is_primary INTEGER DEFAULT 0,
    CONSTRAINT uq_release_mc_ver UNIQUE(release_id, mc_version)
);

CREATE INDEX IF NOT EXISTS idx_rel_mc_version ON release_mc_versions(mc_version);

-- 8. 模组加载器字典及关联 (Loaders & Source Item Loaders)
CREATE TABLE IF NOT EXISTS loaders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE                  -- Fabric, Forge, NeoForge, Quilt
);

CREATE TABLE IF NOT EXISTS source_item_loaders (
    source_item_id TEXT NOT NULL REFERENCES source_items(id) ON DELETE CASCADE,
    loader_id INTEGER NOT NULL REFERENCES loaders(id) ON DELETE CASCADE,
    PRIMARY KEY (source_item_id, loader_id)
);

-- 9. 分类字典及关联 (Categories & Source Item Categories)
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,                    -- global, mcmod, bilibili, etc.
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

-- 10. 下载链接 (Download Links)
CREATE TABLE IF NOT EXISTS download_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_item_id TEXT NOT NULL REFERENCES source_items(id) ON DELETE CASCADE,
    release_id TEXT REFERENCES releases(id) ON DELETE SET NULL,
    link_type TEXT NOT NULL,                   -- OFFICIAL, APP_IMPORT, BAIDU, QUARK, LANZOU, PAN123, OTHER
    url TEXT NOT NULL,
    label TEXT,
    extract_code TEXT,
    is_server INTEGER DEFAULT 0,               -- 1 if specific to server download
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_download_links_source ON download_links(source_item_id);

-- 11. 关联视频 (Related Videos)
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

-- 12. 交互与数值指标快照 (Metrics Snapshot)
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

-- 13. 运行环境证据断言表 (Environment Claims)
-- 严格区分平台事实 (confirmed) 与文本推断 (inferred / weak_inferred)
CREATE TABLE IF NOT EXISTS environment_claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pack_id TEXT NOT NULL REFERENCES packs(id) ON DELETE CASCADE,
    source_item_id TEXT NOT NULL REFERENCES source_items(id) ON DELETE CASCADE,
    side TEXT NOT NULL,                        -- client, server, both
    status TEXT NOT NULL,                      -- required, optional, unsupported, supported, unknown
    certainty TEXT NOT NULL,                   -- confirmed, inferred, weak_inferred, unknown
    evidence_type TEXT NOT NULL,               -- platform_field, file_name, text_rule, url_parameter, user_report
    evidence_text TEXT,                        -- verbatim text or filename
    raw_value TEXT,                            -- raw source value (e.g. "required", "true")
    source_field TEXT,                         -- field path where evidence was found
    source_url TEXT,
    observed_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_env_claims_pack ON environment_claims(pack_id);
CREATE INDEX IF NOT EXISTS idx_env_claims_certainty ON environment_claims(certainty);
CREATE INDEX IF NOT EXISTS idx_env_claims_side_status ON environment_claims(side, status);

-- 14. 审计事件 (Audit Events)
CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT REFERENCES ingest_runs(run_id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,                  -- pack_added, pack_removed, pack_updated, server_flag_ambiguous
    entity_type TEXT NOT NULL,                 -- pack, source_item, environment_claim
    entity_id TEXT NOT NULL,
    details_json TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_events_run ON audit_events(run_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_type ON audit_events(event_type);

-- 15. 全文检索虚拟表 (FTS5 Virtual Table)
CREATE VIRTUAL TABLE IF NOT EXISTS pack_fts USING fts5(
    pack_id UNINDEXED,
    title,
    aliases,
    author,
    summary,
    categories,
    tokenize = 'unicode61'
);

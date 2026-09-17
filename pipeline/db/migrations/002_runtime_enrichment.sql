-- Migration 002: Runtime Enrichment Tables for Architecture V2 Phase 2A
-- Adds structured tables for included mods, trend time series, and comment metadata.

PRAGMA foreign_keys = ON;

-- 1. 整合包收录的具体模组明细 (MC百科 / 各平台)
CREATE TABLE IF NOT EXISTS included_mods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_item_id TEXT NOT NULL REFERENCES source_items(id) ON DELETE CASCADE,
    mod_name TEXT NOT NULL,
    mod_title TEXT,
    mod_version TEXT,
    mod_url TEXT,
    class_id TEXT,
    category_id TEXT,
    category_name TEXT,
    category_url TEXT,
    sort_order INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_included_mods_item ON included_mods(source_item_id);
CREATE INDEX IF NOT EXISTS idx_included_mods_name ON included_mods(mod_name);

-- 2. 整合包长期趋势每日观测时序点
CREATE TABLE IF NOT EXISTS trend_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_item_id TEXT NOT NULL REFERENCES source_items(id) ON DELETE CASCADE,
    point_date TEXT NOT NULL,
    views_delta REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_trend_points_item_date ON trend_points(source_item_id, point_date);

-- 3. 整合包评论元数据与评论缓存
CREATE TABLE IF NOT EXISTS source_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_item_id TEXT NOT NULL REFERENCES source_items(id) ON DELETE CASCADE,
    page_count INTEGER DEFAULT 0,
    true_count INTEGER DEFAULT 0,
    comments_json TEXT DEFAULT '[]'
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_source_comments_item ON source_comments(source_item_id);

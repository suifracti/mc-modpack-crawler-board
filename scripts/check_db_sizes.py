import sqlite3
import os

db_path = 'build/canonical.db'
conn = sqlite3.connect(db_path)
db_sz = os.path.getsize(db_path)
print(f"Canonical DB Total File Size: {db_sz / (1024*1024):.2f} MB ({db_sz:,} bytes)\n")

# Compute data payload size per table
tables = [
    "source_items",
    "packs",
    "releases",
    "release_mc_versions",
    "environment_claims",
    "metrics",
    "download_links",
    "related_videos",
    "source_item_categories",
    "source_item_loaders",
    "included_mods",
    "trend_points",
    "source_comments",
    "pack_fts",
]

print(f"{'Table Name':<26} | {'Row Count':<12} | {'Estimated Data Payload':<22}")
print("-" * 66)

for t in tables:
    row_count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    # Get column names
    col_info = conn.execute(f"PRAGMA table_info({t})").fetchall()
    if col_info:
        len_expr = " + ".join([f"COALESCE(LENGTH({c[1]}), 0)" for c in col_info])
        total_payload = conn.execute(f"SELECT SUM({len_expr}) FROM {t}").fetchone()[0] or 0
        mb_str = f"{total_payload / (1024 * 1024):.2f} MB"
        print(f"{t:<26} | {row_count:<12,d} | {mb_str:>10} ({total_payload:>10,d} B)")
    else:
        print(f"{t:<26} | {row_count:<12,d} | {'Virtual / FTS':>10}")

conn.close()

"""
Migration 003: Correctness Remediation for Architecture V2 Phase 3F.
Remediates proven WRONG facts in build/canonical.db:
1. P0-6: Purges non-timestamp Chinese strings ('未知', '未知时间') from releases & source_items date columns.
2. P0-4 & P0-5: Purges/sanitizes invalid download URLs (changelogs, QQ groups, null, undefined).
3. P0-7: Ingests missing loaders from titles for Bilibili source items.
Preserves strict invariants: packs = 73522, source_items = 73522.
"""
import os
import re
import sqlite3
import sys

VALID_URL_SCHEMES = ("http://", "https://", "ftp://", "magnet:", "modrinth:", "curseforge:")

def run_migration(db_path: str):
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    try:
        # Pre-check Invariants
        cur.execute("SELECT COUNT(*) FROM packs")
        initial_packs = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM source_items")
        initial_source_items = cur.fetchone()[0]

        print(f"[*] Initial status: packs={initial_packs}, source_items={initial_source_items}")
        assert initial_packs == 73522, f"Expected 73522 packs, got {initial_packs}"
        assert initial_source_items == 73522, f"Expected 73522 source_items, got {initial_source_items}"

        # 1. P0-6: Date Pollution Remediation
        print("\n[1] Remediating Date Pollution (TIME-MCMOD-01, TIME-XYEBBS-01)...")
        cur.execute("""
            UPDATE releases 
            SET release_date = NULL 
            WHERE release_date IN ('未知', '未知时间', 'N/A', '-', '') OR release_date LIKE '%未知%'
        """)
        print(f"    Cleaned releases.release_date: {cur.rowcount} rows updated to NULL")

        cur.execute("""
            UPDATE source_items 
            SET published_at = NULL 
            WHERE published_at IN ('未知', '未知时间', 'N/A', '-', '') OR published_at LIKE '%未知%'
        """)
        print(f"    Cleaned source_items.published_at: {cur.rowcount} rows updated to NULL")

        cur.execute("""
            UPDATE source_items 
            SET modified_at = NULL 
            WHERE modified_at IN ('未知', '未知时间', 'N/A', '-', '') OR modified_at LIKE '%未知%'
        """)
        print(f"    Cleaned source_items.modified_at: {cur.rowcount} rows updated to NULL")

        # 2. P0-4 & P0-5: Download Links Sanitization
        print("\n[2] Remediating Download Links (DL-BBSMC-02, DL-XYEBBS-01)...")
        cur.execute("SELECT id, url, extract_code FROM download_links")
        all_links = cur.fetchall()

        deleted_ids = []
        updated_links = []

        url_regex = re.compile(r'https?://[^\s<>"\'`]+|ftp://[^\s<>"\'`]+|magnet:\?[^\s<>"\'`]+|modrinth:[^\s<>"\'`]+|curseforge:[^\s<>"\'`]+')
        code_regex = re.compile(r'(?:提取码|pwd|密码)[:：\s]+([a-zA-Z0-9]{4,8})')

        for link_id, raw_url, raw_code in all_links:
            if not raw_url or not isinstance(raw_url, str):
                deleted_ids.append(link_id)
                continue
            
            raw_url_clean = raw_url.strip()
            # Explicit fake strings & overlength changelogs
            if raw_url_clean.lower() in ("null", "undefined", "none", "neoforge", "forge", "fabric"):
                deleted_ids.append(link_id)
                continue
            if "qq群" in raw_url_clean.lower() or "qq group" in raw_url_clean.lower():
                deleted_ids.append(link_id)
                continue
            if len(raw_url_clean) > 1000 or any(c in raw_url_clean for c in ('\n', '\r')):
                deleted_ids.append(link_id)
                continue

            # Check if pure valid url
            if any(raw_url_clean.startswith(s) for s in VALID_URL_SCHEMES) and ' ' not in raw_url_clean:
                continue

            # Try to extract embedded URL
            m = url_regex.search(raw_url_clean)
            if m:
                clean_url = m.group(0).rstrip('.,;!?#')
                new_code = raw_code
                if not new_code:
                    m_code = code_regex.search(raw_url_clean)
                    if m_code:
                        new_code = m_code.group(1)
                updated_links.append((clean_url, new_code, link_id))
            else:
                deleted_ids.append(link_id)

        if deleted_ids:
            cur.executemany("DELETE FROM download_links WHERE id = ?", [(i,) for i in deleted_ids])
            print(f"    Deleted invalid/fake download links: {len(deleted_ids)} rows")

        if updated_links:
            cur.executemany("UPDATE download_links SET url = ?, extract_code = ? WHERE id = ?", updated_links)
            print(f"    Sanitized embedded download links: {len(updated_links)} rows")

        # 3. P0-7: Ingest Missing Bilibili Loaders
        print("\n[3] Remediating Bilibili Missing Loaders (LOADER-BILI-01)...")
        cur.execute("""
            SELECT s.id, s.title, s.description FROM source_items s
            WHERE s.platform = 'bilibili'
        """)
        bili_items = cur.fetchall()

        cur.execute("SELECT DISTINCT id, name FROM loaders")
        existing_loaders = {name.lower(): (lid, name) for lid, name in cur.fetchall()}

        loader_inserts = []
        for s_id, title, desc in bili_items:
            text = f"{title or ''} {desc or ''}"
            matched_loaders = []
            for ldr in ["NeoForge", "Fabric", "Quilt", "Forge"]:
                if re.search(rf'(?<![a-zA-Z]){ldr}(?![a-zA-Z])', text, re.I):
                    matched_loaders.append(ldr)

            for ldr_name in matched_loaders:
                key = ldr_name.lower()
                if key not in existing_loaders:
                    cur.execute("INSERT OR IGNORE INTO loaders (name) VALUES (?)", (ldr_name,))
                    cur.execute("SELECT id, name FROM loaders WHERE LOWER(name) = ?", (key,))
                    row = cur.fetchone()
                    existing_loaders[key] = (row[0], row[1])
                
                lid = existing_loaders[key][0]
                loader_inserts.append((s_id, lid))

        if loader_inserts:
            cur.executemany("INSERT OR IGNORE INTO source_item_loaders (source_item_id, loader_id) VALUES (?, ?)", loader_inserts)
            print(f"    Ingested Bilibili source_item_loaders: {cur.rowcount} additions")

        # 4. Invariant Verification
        print("\n[4] Verifying Final Invariants...")
        cur.execute("SELECT COUNT(*) FROM packs")
        final_packs = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM source_items")
        final_source_items = cur.fetchone()[0]

        assert final_packs == initial_packs == 73522, f"Pack count invariant violated: {final_packs} != 73522"
        assert final_source_items == initial_source_items == 73522, f"SourceItem count invariant violated: {final_source_items} != 73522"

        # Verify no Chinese date strings remain
        cur.execute("""
            SELECT COUNT(*) FROM releases 
            WHERE release_date IS NOT NULL AND release_date NOT LIKE '19%' AND release_date NOT LIKE '20%'
        """)
        assert cur.fetchone()[0] == 0, "Polluted releases date strings still exist!"

        cur.execute("""
            SELECT COUNT(*) FROM source_items 
            WHERE (published_at IS NOT NULL AND published_at NOT LIKE '19%' AND published_at NOT LIKE '20%')
               OR (modified_at IS NOT NULL AND modified_at NOT LIKE '19%' AND modified_at NOT LIKE '20%')
        """)
        assert cur.fetchone()[0] == 0, "Polluted source_items date strings still exist!"

        # Verify no invalid download URLs remain
        cur.execute("""
            SELECT COUNT(*) FROM download_links 
            WHERE url NOT LIKE 'http://%'
              AND url NOT LIKE 'https://%'
              AND url NOT LIKE 'ftp://%'
              AND url NOT LIKE 'magnet:%'
              AND url NOT LIKE 'modrinth:%'
              AND url NOT LIKE 'curseforge:%'
        """)
        assert cur.fetchone()[0] == 0, "Invalid download URLs still exist!"

        conn.commit()
        print("\n>>> MIGRATION 003 APPLIED SUCCESSFULLY WITH ALL GATES PASSING <<<")

    except Exception as e:
        conn.rollback()
        print(f"\n[!] Migration 003 failed, transaction rolled back: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    db = os.path.join(root, "build", "canonical.db")
    run_migration(db)

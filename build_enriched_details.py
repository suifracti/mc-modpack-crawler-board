import os
import sys
import json
import re

sys.stdout.reconfigure(encoding='utf-8')

REPO_ROOT = r'd:\ai\work\我的世界整合包获取'
CACHE_PATH = os.path.join(REPO_ROOT, 'crawler_output', 'mcmod_details_cache.json')
TABLE_ROWS_PATH = os.path.join(REPO_ROOT, 'converted_output', 'data', 'table_rows.js')

with open(TABLE_ROWS_PATH, 'r', encoding='utf-8') as f:
    rows = json.loads(f.read().strip()[len('window.tableRowsData = '):].rstrip(';\n '))

def clean_key(s):
    if not s: return ""
    s = re.sub(r'^\[[^\]]+\]', '', s)
    s = re.sub(r'[\(（].*?[\)）]', '', s)
    s = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]', '', s).lower()
    return s

def extract_en_title(title):
    m = re.search(r'[\(（]([^\)）]+)[\)）]', title)
    return m.group(1).strip() if m else ""

# Load existing cache
cache = {}
if os.path.exists(CACHE_PATH):
    try:
        with open(CACHE_PATH, 'r', encoding='utf-8') as f:
            cache = json.load(f)
    except Exception:
        cache = {}

# Build cross platform index for descriptions and images
cross_sources = [
    ('crawler_output/curseforge_modpacks.json', 'cf'),
    ('crawler_output/modrinth_modpacks.json', 'mr'),
    ('crawler_output/bbsmc_modpacks.json', 'bbsmc'),
    ('crawler_output/xyebbs_modpacks.json', 'xyebbs'),
    ('crawler_output/bilibili_modpacks.json', 'bili'),
]

index_by_key = {}
for path, name in cross_sources:
    full_path = os.path.join(REPO_ROOT, path)
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            packs = json.load(f)
            for p in packs:
                t = p.get('title') or p.get('name') or ''
                k = clean_key(t)
                desc = p.get('description') or p.get('intro') or p.get('summary') or ''
                if k and desc and k not in index_by_key:
                    index_by_key[k] = p
                slug = p.get('slug') or ''
                k_slug = clean_key(slug)
                if k_slug and desc and k_slug not in index_by_key:
                    index_by_key[k_slug] = p

print(f"Loaded {len(index_by_key)} cross-platform indexed items with descriptions.")

# Enrich cache for all rows
enriched_count = 0
for r in rows:
    mid = str(r.get('mid'))
    # If already has high-quality mcmod cache, keep it
    if mid in cache and cache[mid].get('desc'):
        continue

    title = r.get('title') or ''
    k1 = clean_key(title)
    en = extract_en_title(title)
    k2 = clean_key(en)

    match = index_by_key.get(k1) or index_by_key.get(k2)
    if match:
        desc = match.get('description') or match.get('intro') or match.get('summary') or ''
        images = match.get('intro_images') or match.get('gallery') or []
        clean_images = []
        for img in images:
            src = img if isinstance(img, str) else (img.get('url') or img.get('src') or '')
            if src:
                clean_images.append(src)

        mc_vers = r.get('mc_versions') or []
        if not mc_vers:
            match_vers = match.get('all_versions') or ([match.get('mc_version')] if match.get('mc_version') else [])
            mc_vers = [v for v in match_vers if isinstance(v, str) and re.match(r'^1\.\d+(\.\d+)?$', v)]

        cache[mid] = {
            "mid": mid,
            "mc_versions": mc_vers,
            "desc": desc.strip(),
            "intro_images": clean_images[:6],
            "source": match.get('platform') or 'cross'
        }
        enriched_count += 1

with open(CACHE_PATH, 'w', encoding='utf-8') as f:
    json.dump(cache, f, ensure_ascii=False, indent=2)

print(f"Enriched {enriched_count} packs into cache. Total cache size: {len(cache)} / {len(rows)}")

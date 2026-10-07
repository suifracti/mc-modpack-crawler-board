# -*- coding: utf-8 -*-
"""
Modrinth 整合包全量/热门数据采集器
数据源：Modrinth 官方 REST API v2 (https://api.modrinth.com/v2)
"""
import os
import sys
import json
import time
import urllib.error
import urllib.parse
import argparse
from datetime import datetime
from desktop_collection_contract import write_collection_result
from public_api_transport import read_public_api_json
from catalog_refresh_policy import load_previous

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

WORKSPACE_ROOT = os.path.abspath(os.environ.get("MC_DESKTOP_WORKSPACE") or os.getcwd())
OUTPUT_JSON = os.path.join(WORKSPACE_ROOT, "crawler_output", "modrinth_modpacks.json")
OUTPUT_JS = os.path.join(WORKSPACE_ROOT, "converted_output", "data", "modrinth_data.js")
TARGET_COUNT = 100000  # 全量采集 Modrinth 全部整合包 (约 18,328 款)
PAGE_LIMIT = 100       # Modrinth search 每页上限 100

HEADERS = {
    "User-Agent": "MCModpackCrawlerDashboard/1.0 (contact: admin@mcmod.local)",
    "Accept": "application/json"
}

SOURCE_STOPPED = False
VERSIONS_CHECKED = 0
MISSING_LATEST_IDS = set()
REQUEST_STATS = {"requests": 0, "successful": 0, "failed": 0, "errors": []}

def fetch_page(offset, limit=100, retries=3):
    global SOURCE_STOPPED
    if SOURCE_STOPPED: return None
    query_params = {
        "facets": '[["project_type:modpack"]]',
        "index": "downloads",
        "offset": offset,
        "limit": limit
    }
    qs = urllib.parse.urlencode(query_params)
    url = f"https://api.modrinth.com/v2/search?{qs}"
    
    for attempt in range(retries):
        try:
            REQUEST_STATS["requests"] += 1
            value = read_public_api_json(url, HEADERS, timeout=15)
            REQUEST_STATS["successful"] += 1
            return value
        except urllib.error.HTTPError as e:
            if e.code in {401, 403, 412, 429}:
                SOURCE_STOPPED = True
                REQUEST_STATS["failed"] += 1
                REQUEST_STATS["errors"].append(f"HTTP {e.code} offset={offset}; source stopped")
                print(f"[来源停止] HTTP {e.code}；本轮不再访问 Modrinth。", flush=True)
                return None
            if attempt == retries - 1:
                REQUEST_STATS["failed"] += 1
                REQUEST_STATS["errors"].append(f"HTTP {e.code} offset={offset}")
            else:
                time.sleep(2)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                REQUEST_STATS["failed"] += 1
                REQUEST_STATS["errors"].append(f"offset={offset}: {e}")
                print(f"  [警告] 请求失败 (offset={offset}): {e}")
                return None
    return None

def fetch_versions(ids):
    global SOURCE_STOPPED, VERSIONS_CHECKED
    if SOURCE_STOPPED: return {}
    ids=list(dict.fromkeys(str(v) for v in ids if v))
    if not ids:return {}
    url='https://api.modrinth.com/v2/versions?'+urllib.parse.urlencode({'ids':json.dumps(ids,separators=(',',':'))})
    REQUEST_STATS['requests']+=1
    try:
        value=read_public_api_json(url,HEADERS,timeout=20)
        if not isinstance(value,list):raise ValueError('Invalid multiple-version response')
        found={v['id']:v for v in value if isinstance(v,dict) and v.get('id') in ids and v.get('project_id')}
        missing=set(ids)-set(found)
        if missing:
            MISSING_LATEST_IDS.update(missing)
            print(f'[版本未核实] {len(missing)} 个目录版本ID未返回；其他已核实版本保留。',flush=True)
        VERSIONS_CHECKED += len(found)
        REQUEST_STATS['successful']+=1
        return found
    except Exception as error:
        if isinstance(error, urllib.error.HTTPError) and error.code in {401, 403, 412, 429}: SOURCE_STOPPED = True
        REQUEST_STATS['failed']+=1;REQUEST_STATS['errors'].append('latest releases: '+str(error))
        print('[版本核对失败] '+str(error),flush=True)
        return {}

def standardize_pack(item, releases_by_id=None):
    slug = (item.get("slug") or "").strip()
    proj_id = (item.get("project_id") or "").strip()
    title = (item.get("title") or slug).strip()
    author = (item.get("author") or "Modrinth Creator").strip()
    description = (item.get("description") or "").strip()
    downloads = int(item.get("downloads") or 0)
    follows = int(item.get("follows") or 0)
    icon_url = (item.get("icon_url") or "").strip()
    
    # 提取所有支持版本及主要版本
    raw_versions = item.get("versions") or []
    # 过滤出标准 MC 版本（形如 1.20.1, 1.12.2）
    mc_versions = [v for v in raw_versions if isinstance(v, str) and (v.startswith("1.") or v.startswith("2."))]
    latest_ver = mc_versions[-1] if mc_versions else (raw_versions[-1] if raw_versions else "未知")
    
    # 分类标签与加载器识别
    raw_categories = item.get("categories") or []
    display_categories = item.get("display_categories") or []
    all_cats = list(dict.fromkeys(raw_categories + display_categories))
    
    loaders = []
    game_cats = []
    known_loaders = {"fabric", "forge", "neoforge", "quilt", "liteloader", "rift"}
    for c in all_cats:
        c_low = str(c).lower().strip()
        if c_low in known_loaders:
            loader_name = "NeoForge" if c_low == "neoforge" else c_low.capitalize()
            if loader_name not in loaders:
                loaders.append(loader_name)
        else:
            if c and c not in game_cats:
                game_cats.append(c)
                
    if not loaders:
        loaders = ["Fabric"]  # Modrinth 平台大部分默认为 Fabric
        
    date_created = (item.get("date_created") or "")[:19].replace("T", " ")
    date_modified = (item.get("date_modified") or "")[:19].replace("T", " ")
    
    # 构建下载直链与客户端一键导入链接
    page_url = f"https://modrinth.com/modpack/{slug}" if slug else f"https://modrinth.com/project/{proj_id}"
    app_install_url = f"modrinth://modpack/{slug}" if slug else f"modrinth://project/{proj_id}"
    
    download_links = [
        {
            "name": "Modrinth 官方页面",
            "url": page_url,
            "type": "OFFICIAL",
            "label": "官网直达"
        },
        {
            "name": "Modrinth App 一键安装",
            "url": app_install_url,
            "type": "APP_IMPORT",
            "label": "一键导入"
        }
    ]
    
    gallery = item.get("gallery") or []
    clean_gallery = [g for g in gallery if isinstance(g, str) and g.startswith("http")]
    
    record = {
        "platform": "modrinth",
        "project_id": proj_id,
        "slug": slug,
        "url": page_url,
        "title": title,
        "author": author,
        "description": description,
        "downloads": downloads,
        "followers": follows,
        "mc_version": latest_ver,
        "all_versions": mc_versions[:12],
        "loaders": loaders,
        "categories": game_cats[:8],
        "icon_url": icon_url,
        "gallery": clean_gallery[:6],
        "date_created": date_created,
        "date_modified": date_modified,
        "download_links": download_links,
        "client_side": item.get("client_side") or "required",
        "server_side": item.get("server_side") or "unsupported",
        "has_server": (item.get("server_side") in ("required", "optional")),
        "env_display": "客户端和服务端" if (item.get("server_side") in ("required", "optional") and item.get("client_side") in ("required", "optional", None)) else ("仅服务端" if item.get("server_side") in ("required", "optional") else "仅客户端"),
        "source_meta": {
            "license": item.get("license"),
            "client_side": item.get("client_side"),
            "server_side": item.get("server_side"),
            "environment": item.get("environment")
        }
    }

    release=(releases_by_id or {}).get(item.get('latest_version'))
    if isinstance(release,dict) and release.get('project_id')==proj_id and release.get('version_number'):
        record.update(latest_version=release['version_number'],releases=[release],version_checked_at=datetime.now().astimezone().isoformat())
    return record

def deduplicate_catalog(records):
    """Collapse exact repeated page observations while keeping the latest local check."""
    positions = {}
    unique = []
    duplicate_ids = []
    duplicate_count = 0
    for record in records:
        ident = str(record.get("project_id") or "")
        if not ident:
            raise ValueError("Modrinth catalog row has no stable project ID")
        if ident not in positions:
            positions[ident] = len(unique)
            unique.append(record)
            continue
        duplicate_count += 1
        if ident not in duplicate_ids:
            duplicate_ids.append(ident)
        index = positions[ident]
        previous = unique[index]
        previous_source = {key: value for key, value in previous.items() if key != "version_checked_at"}
        current_source = {key: value for key, value in record.items() if key != "version_checked_at"}
        if previous_source != current_source:
            raise ValueError(f"Modrinth repeated project ID has conflicting source fields: {ident}")
        if str(record.get("version_checked_at") or "") > str(previous.get("version_checked_at") or ""):
            unique[index] = record
    return unique, duplicate_count, duplicate_ids

def main(max_total=None, daily=False):
    previous=load_previous(OUTPUT_JSON) if daily else []
    prior_by_id={str(row['project_id']):row for row in previous if row.get('project_id')}
    cached_releases={}
    for row in previous:
        for release in row.get('releases') or []:
            if isinstance(release,dict) and release.get('id') and release.get('project_id')==row.get('project_id') and release.get('version_number'):
                cached_releases[release['id']]=release
    versions_reused=0
    target_count = int(max_total) if max_total else TARGET_COUNT
    print("=" * 60)
    print("  🚀 Modrinth 整合包数据采集器 (API v2)")
    print(f"  目标采集量: {target_count} 款热门整合包")
    print("=" * 60)
    
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_JS), exist_ok=True)
    
    all_packs = []
    offset = 0
    total_available = 0
    pages_completed = 0
    target_reached = False
    
    start_time = time.time()
    hits = []
    
    while len(all_packs) < target_count:
        limit = min(PAGE_LIMIT, target_count - len(all_packs))
        if len(all_packs) % 500 == 0 or len(all_packs) == 0:
            print(f"[{len(all_packs)}/{total_available or target_count}] 正在拉取 offset={offset} ...")
        res = fetch_page(offset, limit=limit)
        if res is None:
            print("  [失败] 请求没有完成，拒绝把旧缓存当作本轮结果。")
            break
        pages_completed += 1
        if not res.get("hits"):
            print("  [提示] 接口没有返回更多数据或拉取完毕。")
            break
            
        total_available = res.get("total_hits", total_available)
        hits = res.get("hits", [])
        latest=fetch_versions([h.get('latest_version') for h in hits if not (cached_releases.get(h.get('latest_version')) or {}).get('project_id')==h.get('project_id')])
        for h in hits:
            reused=cached_releases.get(h.get('latest_version'))
            if reused and reused.get('project_id')==h.get('project_id'):
                latest[h['latest_version']]=reused
                versions_reused+=1
            pack = standardize_pack(h,latest)
            if reused and reused.get('project_id')==h.get('project_id'):
                prior=prior_by_id.get(str(h['project_id']),{})
                if prior.get('version_checked_at'):pack['version_checked_at']=prior['version_checked_at']
                else:pack.pop('version_checked_at',None)
            all_packs.append(pack)

        if len(all_packs) >= target_count:
            target_reached = True
            all_packs = all_packs[:target_count]
            break
            
        offset += len(hits)
        time.sleep(0.6)  # 礼貌并发间隔
        
        if len(hits) < limit:
            break
            
    fetched_rows = len(all_packs)
    all_packs, duplicate_count, duplicate_ids = deduplicate_catalog(all_packs)
    if duplicate_count:
        REQUEST_STATS["errors"].append(f"Catalog pagination repeated {duplicate_count} project IDs; duplicate observations were collapsed")
    elapsed = time.time() - start_time
    print(f"\n[完成] 成功采集并标准化 {len(all_packs)} 款 Modrinth 整合包 (耗时 {elapsed:.1f}s)")
    print(f"  平台总收录量: {total_available:,} 款")
    
    # 写入 JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_packs, f, ensure_ascii=False, indent=2)
    print(f"  [OK] 保存 JSON: {OUTPUT_JSON} ({os.path.getsize(OUTPUT_JSON) / 1024 / 1024:.2f} MB)")
    
    # 写入 JS 数据源
    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write("window.modrinthModpacksData = " + json.dumps(all_packs, ensure_ascii=False) + ";\n")

    request_completed = REQUEST_STATS["failed"] == 0
    truncated = bool(
        request_completed
        and not target_reached
        and total_available
        and fetched_rows < total_available
    )
    catalog_completed = bool(total_available and len(all_packs) >= total_available)
    pages_expected = (total_available + PAGE_LIMIT - 1) // PAGE_LIMIT if total_available else None
    scan_pages_complete = bool(request_completed and not truncated and not SOURCE_STOPPED
                               and pages_expected and pages_completed >= pages_expected)
    status = "success" if all_packs and scan_pages_complete and catalog_completed and not MISSING_LATEST_IDS else "empty" if request_completed and not all_packs else "partial" if all_packs and scan_pages_complete else "failed"
    write_collection_result(
        "modrinth",
        request_completed=request_completed,
        fetched_count=len(all_packs),
        pages_completed=pages_completed,
        pages_expected=pages_expected,
        truncated=truncated,
        failed_requests=int(REQUEST_STATS["failed"]),
        errors=REQUEST_STATS["errors"],
        status=status,
        details={"totalAvailable": total_available, "targetCount": target_count, "targetReached": target_reached, "catalogCompleted": catalog_completed, "catalogCoverage": "complete-pages-with-duplicate-ids" if duplicate_count and scan_pages_complete else "complete-pages" if scan_pages_complete else "incomplete-pages", "catalogDuplicateCount": duplicate_count, "catalogDuplicateIds": duplicate_ids, "catalogUniqueCount": len(all_packs), "catalogFetchedRows": fetched_rows, "scanPagesComplete": scan_pages_complete, "versionsChecked": VERSIONS_CHECKED, "versionsReused":versions_reused,"versionRefreshMode":"reuse-exact-release-id" if daily else "full-requested-range", "sourceStopped": SOURCE_STOPPED, "versionParseFailures": 0, "missingLatestReleaseIds": sorted(MISSING_LATEST_IDS), "unverifiedLatestVersionCount": len(MISSING_LATEST_IDS)},
    )
    print(f"  [OK] 保存 JS: {OUTPUT_JS} ({os.path.getsize(OUTPUT_JS) / 1024 / 1024:.2f} MB)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Modrinth 整合包数据采集器")
    parser.add_argument("--max", type=int, default=0, help="最多采集条数（0 表示按默认全量目标）")
    parser.add_argument('--daily',action='store_true',help='完整目录核对，版本ID未变时复用已核实发布资料')
    args = parser.parse_args()
    main(max_total=args.max or None,daily=args.daily)

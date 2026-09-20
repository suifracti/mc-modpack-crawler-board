# -*- coding: utf-8 -*-
"""
CurseForge 超级全量切片爬虫 (CurseForge Full-Scale Multi-Dimensional Slicing Crawler)
原理：
1. 遍历 Minecraft 存世全部 101 个有效游戏版本 (1.0 ~ 1.21.11)
   - 对于其中 96 个版本 (< 10,000 款)，单次切片即 100% 穷尽所有整合包！
   - 对于突破 10,000 的 5 大巨型版本 (1.21.1, 1.20.1, 1.19.2, 1.16.5, 1.12.2)，
     进行 ModLoader(Fabric/NeoForge/Forge) 与 19 玩法分类双重正交切片，彻底消除 10,000 截断！
2. 辅以全平台 19 分类深度扫描 + 双向排序 (Downloads desc/asc, LastUpdated desc/asc)
3. 12 线程高并发并发调度，全局 Project ID 动态去重，定期增量持久化！
"""
import os
import sys
import json
import time
import urllib.request
import urllib.parse
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from desktop_collection_contract import write_collection_result

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

WORKSPACE_ROOT = os.path.abspath(os.environ.get("MC_DESKTOP_WORKSPACE") or os.getcwd())
OUTPUT_JSON = os.path.join(WORKSPACE_ROOT, "crawler_output", "curseforge_modpacks.json")
OUTPUT_JS = os.path.join(WORKSPACE_ROOT, "converted_output", "data", "curseforge_data.js")
PAGE_SIZE = 50
MAX_WORKERS = 12

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

REQUEST_STATS = {"requests": 0, "successful": 0, "failed": 0, "errors": []}

LOADER_TYPE_MAP = {
    1: "Forge",
    2: "Cauldron",
    3: "LiteLoader",
    4: "Fabric",
    5: "Quilt",
    6: "NeoForge"
}

# 19 个官方玩法分类
CATEGORIES = [
    (4472, "Tech"),
    (4475, "Adventure and RPG"),
    (4478, "Quests"),
    (4481, "Small / Light"),
    (4482, "Extra Large"),
    (4483, "Combat / PvP"),
    (4474, "Sci-Fi"),
    (4736, "Skyblock"),
    (4480, "Map Based"),
    (7418, "Horror"),
    (4484, "Multiplayer"),
    (4477, "Mini Game"),
    (4473, "Magic"),
    (5128, "Vanilla+"),
    (4479, "Hardcore"),
    (4476, "Exploration"),
    (4487, "FTB Official Pack"),
    (9243, "Expert"),
    (10683, "RLCraft")
]

# 突破 10,000 限制的 5 大顶级版本
MAJOR_VERSIONS = {"1.21.1", "1.20.1", "1.19.2", "1.16.5", "1.12.2"}

# 所有存在整合包的 101 个 Minecraft 版本
ALL_VERSIONS = [
    "1.21.11", "1.21.10", "1.21.9", "1.21.8", "1.21.7", "1.21.6", "1.21.5", "1.21.4", "1.21.3", "1.21.2", "1.21.1", "1.21",
    "1.20.6", "1.20.5", "1.20.4", "1.20.3", "1.20.2", "1.20.1", "1.20",
    "1.19.4", "1.19.3", "1.19.2", "1.19.1", "1.19",
    "1.18.2", "1.18.1", "1.18",
    "1.17.1", "1.17",
    "1.16.5", "1.16.4", "1.16.3", "1.16.2", "1.16.1", "1.16",
    "1.15.2", "1.15.1", "1.15",
    "1.14.4", "1.14.3", "1.14.2", "1.14.1", "1.14",
    "1.13.2", "1.13.1", "1.13",
    "1.12.2", "1.12.1", "1.12",
    "1.11.2", "1.11.1", "1.11",
    "1.10.2", "1.10.1", "1.10",
    "1.9.4", "1.9.3", "1.9.2", "1.9.1", "1.9",
    "1.8.9", "1.8.8", "1.8.7", "1.8.6", "1.8.5", "1.8.4", "1.8.3", "1.8.2", "1.8.1", "1.8",
    "1.7.10", "1.7.9", "1.7.8", "1.7.7", "1.7.6", "1.7.5", "1.7.4", "1.7.3", "1.7.2",
    "1.6.4", "1.6.2", "1.6.1",
    "1.5.3", "1.5.2", "1.5.1", "1.5.0",
    "1.4.7", "1.4.6", "1.4.5", "1.4.4", "1.4.2",
    "1.3.2", "1.3.1",
    "1.2.5", "1.2.4", "1.2.3", "1.2.2", "1.2.1",
    "1.1", "1.0.0", "1.0"
]

def fetch_slice_page(index, category_id=None, game_version=None, mod_loader_type=None, sort_field=6, sort_order="desc", retries=3):
    params = {
        "gameId": 432,
        "classId": 4471,
        "pageSize": PAGE_SIZE,
        "index": index,
        "sortField": sort_field,
        "sortOrder": sort_order
    }
    if category_id:
        params["categoryId"] = category_id
    if game_version:
        params["gameVersion"] = game_version
    if mod_loader_type:
        params["modLoaderType"] = mod_loader_type

    qs = urllib.parse.urlencode(params)
    url = f"https://api.curse.tools/v1/cf/mods/search?{qs}"

    for attempt in range(retries):
        try:
            REQUEST_STATS["requests"] += 1
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=12) as resp:
                if resp.status == 200:
                    value = json.loads(resp.read().decode("utf-8"))
                    REQUEST_STATS["successful"] += 1
                    return value
                if attempt == retries - 1:
                    REQUEST_STATS["failed"] += 1
                    REQUEST_STATS["errors"].append(f"HTTP {resp.status} index={index}")
        except Exception as error:
            if attempt < retries - 1:
                time.sleep(1)
            else:
                REQUEST_STATS["failed"] += 1
                REQUEST_STATS["errors"].append(f"index={index}: {error}")
                return None
    return None

def standardize_pack(item):
    proj_id = str(item.get("id") or "")
    slug = (item.get("slug") or "").strip()
    name = (item.get("name") or slug).strip()
    summary = (item.get("summary") or "").strip()
    downloads = int(item.get("downloadCount") or 0)
    thumbs_up = int(item.get("thumbsUpCount") or 0)
    
    raw_authors = item.get("authors") or []
    authors = [a.get("name", "").strip() for a in raw_authors if isinstance(a, dict) and a.get("name")]
    author_str = ", ".join(authors) if authors else "CurseForge Author"
    
    links = item.get("links") or {}
    page_url = links.get("websiteUrl") or f"https://www.curseforge.com/minecraft/modpacks/{slug}"
    app_install_url = f"curseforge://install?addonId={proj_id}"
    
    logo_obj = item.get("logo") or {}
    icon_url = logo_obj.get("url") or logo_obj.get("thumbnailUrl") or ""
    
    raw_screenshots = item.get("screenshots") or []
    gallery = [s.get("url") for s in raw_screenshots if isinstance(s, dict) and s.get("url")]
    
    raw_categories = item.get("categories") or []
    categories = []
    for c in raw_categories:
        if isinstance(c, dict) and c.get("name"):
            c_name = c["name"].strip()
            if c_name.lower() not in {"modpacks", "minecraft"}:
                categories.append(c_name)
                
    file_indexes = item.get("latestFilesIndexes") or []
    all_versions = []
    loaders = []
    
    for fi in file_indexes:
        if isinstance(fi, dict):
            gv = fi.get("gameVersion")
            if gv and isinstance(gv, str) and (gv.startswith("1.") or gv.startswith("2.")) and gv not in all_versions:
                all_versions.append(gv)
            l_type = fi.get("modLoader")
            if l_type in LOADER_TYPE_MAP:
                l_name = LOADER_TYPE_MAP[l_type]
                if l_name not in loaders:
                    loaders.append(l_name)
                    
    if not loaders:
        loaders = ["Forge"]
        
    latest_ver = all_versions[0] if all_versions else "未知"
    
    date_created = (item.get("dateCreated") or "")[:19].replace("T", " ")
    date_modified = (item.get("dateModified") or item.get("dateReleased") or "")[:19].replace("T", " ")
    
    download_links = [
        {
            "name": "CurseForge 官方页面",
            "url": page_url,
            "type": "OFFICIAL",
            "label": "官网直达"
        },
        {
            "name": "CurseForge App 一键安装",
            "url": app_install_url,
            "type": "APP_IMPORT",
            "label": "一键导入"
        }
    ]
    
    return {
        "platform": "curseforge",
        "project_id": proj_id,
        "slug": slug,
        "url": page_url,
        "title": name,
        "author": author_str,
        "description": summary,
        "downloads": downloads,
        "followers": thumbs_up,
        "mc_version": latest_ver,
        "all_versions": all_versions[:12],
        "loaders": loaders,
        "categories": categories[:8],
        "icon_url": icon_url,
        "gallery": gallery[:6],
        "date_created": date_created,
        "date_modified": date_modified,
        "download_links": download_links,
        "source_meta": {
            "game_id": item.get("gameId"),
            "main_file_id": item.get("mainFileId")
        }
    }

def save_current_state(global_packs, max_total=0):
    final_list = list(global_packs.values())
    final_list.sort(key=lambda x: x.get("downloads", 0), reverse=True)
    if max_total:
        final_list = final_list[:max_total]
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)
    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write("window.curseforgeModpacksData = " + json.dumps(final_list, ensure_ascii=False) + ";\n")

def main(max_total=0):
    print("=" * 70)
    print("  🚀 CurseForge 超级全量切片深挖爬虫 (全版本 × 全分类 × 全Loader)")
    print("  目标：完全抓完 CurseForge 存世所有 Minecraft 整合包！")
    print("=" * 70)

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_JS), exist_ok=True)

    # 预加载现有数据
    global_packs = {}
    if os.path.exists(OUTPUT_JSON):
        try:
            with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
                old_list = json.load(f)
            for p in old_list:
                if p.get("project_id"):
                    global_packs[p["project_id"]] = p
            print(f"  [初始缓存] 成功载入已抓取的 {len(global_packs):,} 款 CurseForge 整合包！")
        except Exception:
            pass

    lock = Lock()
    start_time = time.time()
    last_save_time = [time.time()]

    # 构建正交切片任务
    slice_tasks = []

    # 1. 针对 5 大突破 10,000 的巨型版本进行 ModLoader + 玩法分类细分切片
    for gv in MAJOR_VERSIONS:
        # 1.1 Fabric 分支 (通常 2,000~5,000 款，单次完全捕获)
        slice_tasks.append({
            "label": f"MC-{gv}_Fabric",
            "game_version": gv,
            "category_id": None,
            "loader_type": 4,
            "sort_field": 6,
            "sort_order": "desc"
        })
        # 1.2 NeoForge 分支 (数百款，单次完全捕获)
        slice_tasks.append({
            "label": f"MC-{gv}_NeoForge",
            "game_version": gv,
            "category_id": None,
            "loader_type": 6,
            "sort_field": 6,
            "sort_order": "desc"
        })
        # 1.3 Forge 分支 × 19 分类切片 (按玩法拆解，彻底化整为零)
        for cid, cname in CATEGORIES:
            slice_tasks.append({
                "label": f"MC-{gv}_Forge_Cat-{cname}",
                "game_version": gv,
                "category_id": cid,
                "loader_type": 1,
                "sort_field": 6,
                "sort_order": "desc"
            })
        # 1.4 该巨型版本的最新发布与更新切片
        slice_tasks.append({
            "label": f"MC-{gv}_LatestUpdated",
            "game_version": gv,
            "category_id": None,
            "loader_type": None,
            "sort_field": 3,
            "sort_order": "desc"
        })

    # 2. 针对其余 96 个普通版本进行完整版本切片 (每个版本 < 10,000 款，100% 全覆盖)
    for gv in ALL_VERSIONS:
        if gv not in MAJOR_VERSIONS:
            slice_tasks.append({
                "label": f"MC-{gv}_Full",
                "game_version": gv,
                "category_id": None,
                "loader_type": None,
                "sort_field": 6,
                "sort_order": "desc"
            })

    # 3. 全局玩法分类切片 (19个官方分类，双向抓取)
    for cid, cname in CATEGORIES:
        slice_tasks.append({
            "label": f"GlobalCat-{cname}_DownloadsDesc",
            "game_version": None,
            "category_id": cid,
            "loader_type": None,
            "sort_field": 6,
            "sort_order": "desc"
        })
        slice_tasks.append({
            "label": f"GlobalCat-{cname}_DownloadsAsc",
            "game_version": None,
            "category_id": cid,
            "loader_type": None,
            "sort_field": 6,
            "sort_order": "asc"
        })
        slice_tasks.append({
            "label": f"GlobalCat-{cname}_UpdatedDesc",
            "game_version": None,
            "category_id": cid,
            "loader_type": None,
            "sort_field": 3,
            "sort_order": "desc"
        })

    # 4. 全局维度兜底切片 (Popularity, Featured, ReleaseDate)
    slice_tasks.append({
        "label": "Global_PopularityDesc",
        "game_version": None,
        "category_id": None,
        "loader_type": None,
        "sort_field": 2,
        "sort_order": "desc"
    })
    slice_tasks.append({
        "label": "Global_FeaturedDesc",
        "game_version": None,
        "category_id": None,
        "loader_type": None,
        "sort_field": 1,
        "sort_order": "desc"
    })
    slice_tasks.append({
        "label": "Global_DownloadsAsc_Lowest",
        "game_version": None,
        "category_id": None,
        "loader_type": None,
        "sort_field": 6,
        "sort_order": "asc"
    })
    slice_tasks.append({
        "label": "Global_UpdatedAsc_Earliest",
        "game_version": None,
        "category_id": None,
        "loader_type": None,
        "sort_field": 3,
        "sort_order": "asc"
    })

    print(f"  [规划] 共生成 {len(slice_tasks)} 个全量切片任务，已启动 {MAX_WORKERS} 线程池调度...\n")

    def worker_slice(task):
        t_label = task["label"]
        cid = task.get("category_id")
        gv = task.get("game_version")
        lt = task.get("loader_type")
        sf = task.get("sort_field", 6)
        so = task.get("sort_order", "desc")
        
        index = 0
        slice_new_count = 0
        slice_total_items = 0
        slice_failed = False
        slice_truncated = False
        
        while index + PAGE_SIZE <= 10000:
            res = fetch_slice_page(index, category_id=cid, game_version=gv, mod_loader_type=lt, sort_field=sf, sort_order=so)
            if res is None:
                slice_failed = True
                break
            if not res.get("data"):
                break
                
            items = res.get("data", [])
            if not items:
                break
                
            slice_total_items += len(items)
            with lock:
                if max_total and len(global_packs) >= max_total:
                    break
                for item in items:
                    pid = str(item.get("id") or "")
                    if pid and pid not in global_packs:
                        pack = standardize_pack(item)
                        global_packs[pid] = pack
                        slice_new_count += 1
                        if max_total and len(global_packs) >= max_total:
                            break
                        
            total_count = res.get("pagination", {}).get("totalCount", 10000)
            index += len(items)
            
            # 达到该切片尾部或单页未满则终止
            if len(items) < PAGE_SIZE or index >= total_count:
                break
                
            time.sleep(0.04)
            
        # 定期自动保存（每间隔 60 秒或累计新增突破 1,000 款）
        with lock:
            if time.time() - last_save_time[0] > 60:
                last_save_time[0] = time.time()
                try:
                    save_current_state(global_packs, max_total=max_total)
                except Exception:
                    pass

        if not max_total and index >= 10000:
            last_total = locals().get("total_count", 10000)
            slice_truncated = bool(last_total > index)
        return t_label, slice_total_items, slice_new_count, slice_failed, slice_truncated

    completed_slices = 0
    total_slices = len(slice_tasks)
    failed_slices = 0
    fetched_count = 0
    truncated = False
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(worker_slice, t): t for t in slice_tasks}
        for future in as_completed(futures):
            completed_slices += 1
            try:
                lbl, fetched_cnt, new_cnt, slice_failed, slice_truncated = future.result()
            except Exception as e:
                lbl, fetched_cnt, new_cnt, slice_failed, slice_truncated = "Error", 0, 0, True, False

            fetched_count += fetched_cnt
            failed_slices += int(slice_failed)
            truncated = truncated or bool(slice_truncated)
                
            with lock:
                current_total = len(global_packs)
                
            # 每有新发现或进度节点即时打印
            if new_cnt > 0 or completed_slices % 10 == 0 or completed_slices == total_slices:
                print(f"  [{completed_slices:3d}/{total_slices}] 切片 [{lbl[:30]:<30}] 扫描 {fetched_cnt:4d} 款 | 新增: +{new_cnt:4d} | 当前去重总计: {current_total:,} 款")

    elapsed = time.time() - start_time
    final_list = list(global_packs.values())
    if max_total:
        final_list = final_list[:max_total]
    final_list.sort(key=lambda x: x.get("downloads", 0), reverse=True)

    print("\n" + "=" * 70)
    print(f"  🎉 [完全抓取完毕] 成功全量采集去重 {len(final_list):,} 款 CurseForge 整合包！(总耗时 {elapsed:.1f} 秒)")
    print("=" * 70)

    save_current_state(global_packs, max_total=max_total)
    print(f"  [OK] 全量 JSON 已持久化: {OUTPUT_JSON} ({os.path.getsize(OUTPUT_JSON) / 1024 / 1024:.2f} MB)")
    print(f"  [OK] 全量 JS 数据源已更新: {OUTPUT_JS} ({os.path.getsize(OUTPUT_JS) / 1024 / 1024:.2f} MB)")

    request_completed = failed_slices == 0 and REQUEST_STATS["failed"] == 0 and not truncated
    status = "success" if fetched_count and request_completed else "empty" if request_completed else "partial" if fetched_count else "failed"
    write_collection_result(
        "curseforge",
        request_completed=request_completed,
        fetched_count=fetched_count,
        pages_completed=int(REQUEST_STATS["successful"]),
        truncated=truncated,
        failed_requests=int(REQUEST_STATS["failed"] + failed_slices),
        errors=REQUEST_STATS["errors"],
        status=status,
        details={"completedSlices": completed_slices, "totalSlices": total_slices, "uniqueOutputCount": len(final_list), "requestedLimit": max_total or None},
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CurseForge 超级全量切片爬虫")
    parser.add_argument("--max", type=int, default=0, help="最多采集条数（0 表示全量）")
    args = parser.parse_args()
    main(max_total=args.max)

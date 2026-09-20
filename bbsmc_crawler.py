#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
====================================================================
  BBSMC (好创/BBSMC) Minecraft 资源专版采集引擎 v1.0
====================================================================
特性：
1. 原生对齐 Modrinth / Labymined v2 开放 REST API（毫秒级极速拉取）
2. 支持批量分页全量采集（1,800+ 独立整合包）
3. 智能解析云盘直链（夸克网盘、百度网盘、123云盘、蓝奏云）与官方 CDN 客户端直链
4. 深度抽取 MC 游戏版本、模组加载器（Forge/Fabric/NeoForge/Quilt）、多维分类标签与游戏截图画廊
5. 同时产出 JSON 归档数据与前端直接加载的 JS 数据源（bbsmc_data.js）
"""

import os
import sys
import time
import json
import random
import argparse
import urllib.request
import urllib.parse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Referer': 'https://bbsmc.net/',
}

BASE_API = "https://api.bbsmc.net/v2"


class BbsmcCrawler:
    def __init__(self, api_base: str = BASE_API, max_workers: int = 10):
        self.api_base = api_base.rstrip('/')
        self.max_workers = max_workers
        self.headers = dict(HEADERS)

    def _get_json(self, endpoint: str, params: Optional[Dict[str, Any]] = None, timeout: int = 10) -> Optional[Any]:
        url = f"{self.api_base}/{endpoint.lstrip('/')}"
        if params:
            qs = urllib.parse.urlencode(params)
            url = f"{url}?{qs}"
        req = urllib.request.Request(url, headers=self.headers)
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    if resp.status == 200:
                        return json.loads(resp.read().decode('utf-8'))
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return None
                time.sleep(0.5 * (attempt + 1))
            except Exception:
                time.sleep(0.5 * (attempt + 1))
        return None

    def search_all_projects(self, project_type: str = "modpack", max_total: int = 0, page_size: int = 100) -> List[Dict[str, Any]]:
        """全量分页拉取项目列表"""
        all_hits = []
        offset = 0
        total_hits = None

        print(f"[*] 正在从 BBSMC 获取 [{project_type}] 列表 (单页步长: {page_size})...")

        while True:
            params = {
                "facets": json.dumps([[f"project_type:{project_type}"]]),
                "index": "downloads",
                "limit": page_size,
                "offset": offset
            }
            res = self._get_json("search", params)
            if not res or 'hits' not in res:
                print(f"  [!] 在 offset={offset} 处请求失败或无数据，停止拉取。")
                break

            hits = res.get('hits', [])
            if not hits:
                break

            if total_hits is None:
                total_hits = res.get('total_hits', 0)
                print(f"  [√] BBSMC 官方返回该类型总计: {total_hits} 款项目")

            all_hits.extend(hits)
            print(f"  -> 已获取 {len(all_hits):4d} / {total_hits} 款 (当前页: {len(hits)} 款 | offset={offset})")

            if max_total and len(all_hits) >= max_total:
                all_hits = all_hits[:max_total]
                break

            offset += len(hits)
            if offset >= total_hits or len(hits) < page_size:
                break

            time.sleep(0.15)

        print(f"[+] 列表检索完成，共纳录 {len(all_hits)} 款项目元数据。\n")
        return all_hits

    def fetch_project_versions(self, project_id: str) -> List[Dict[str, Any]]:
        """获取单个项目的版本发布历史与文件下载直链"""
        data = self._get_json(f"project/{project_id}/version", timeout=8)
        if isinstance(data, list):
            return data
        return []

    def enrich_project_downloads(self, projects: List[Dict[str, Any]], max_enrich: int = 300) -> None:
        """并发丰富前 N 款热门项目的实际下载网盘与直链"""
        to_enrich = projects[:max_enrich]
        print(f"[*] 正在并发拉取前 {len(to_enrich)} 款热门项目的详细版本与下载直链 (线程数: {self.max_workers})...")
        
        start_time = time.time()
        completed = 0
        enriched_count = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_proj = {executor.submit(self.fetch_project_versions, p['project_id']): p for p in to_enrich}
            for future in as_completed(future_to_proj):
                p = future_to_proj[future]
                completed += 1
                try:
                    versions = future.result()
                    if versions:
                        download_links = self._extract_download_links(versions)
                        p['download_links'] = download_links
                        cleaned_versions = []
                        for v in versions[:15]:
                            cleaned_versions.append({
                                "version_number": v.get("version_number", ""),
                                "name": v.get("name", ""),
                                "date_published": format_iso_time(v.get("date_published", "")),
                                "downloads": v.get("downloads", 0),
                                "game_versions": v.get("game_versions", []),
                                "loaders": v.get("loaders", []),
                                "changelog": (v.get("changelog") or "").strip(),
                                "files": [
                                    {
                                        "name": f.get("filename") or "下载",
                                        "url": f.get("url"),
                                        "size": f"{f.get('size', 0) / (1024 * 1024):.1f}MB" if f.get("size", 0) > 1024 * 1024 else "",
                                        "is_server": bool(re.search(r'(?:server|服务端|开服包|服端)', (f.get("filename") or "") + " " + (v.get("name") or ""), re.I))
                                    }
                                    for f in v.get("files", []) if f.get("url")
                                ]
                            })
                        p['versions_data'] = cleaned_versions
                        p['has_server'] = any(fl.get('is_server') for ver in cleaned_versions for fl in ver.get('files', [])) or bool(re.search(r'(?:服务端|server|开服|服端)', (p.get('title') or "") + " " + (p.get('description') or ""), re.I))
                        if download_links:
                            enriched_count += 1
                except Exception:
                    pass

                if completed % 50 == 0 or completed == len(to_enrich):
                    elapsed = time.time() - start_time
                    print(f"  [{completed:3d}/{len(to_enrich)}] 版本直链解析中... 耗时: {elapsed:.1f}s, 已解析直链项目: {enriched_count}")

        print(f"[+] 版本解析完成！共为 {enriched_count} 款整合包提取到了直接下载/网盘链接。\n")

    @staticmethod
    def _extract_download_links(versions: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """从版本文件列表中智能提取网盘和直链"""
        links = []
        seen = set()

        for ver in versions:
            ver_name = ver.get('name') or ver.get('version_number') or ''
            files = ver.get('files', [])
            for f in files:
                url = (f.get('url') or '').strip()
                if not url or url in seen:
                    continue
                seen.add(url)

                fn = (f.get('filename') or '').strip()
                size = f.get('size', 0)
                size_mb = f"{size / (1024 * 1024):.1f}MB" if size > 1024 * 1024 else ""

                # 识别网盘类型
                if 'quark.cn' in url:
                    pan_name = "夸克网盘"
                elif 'baidu.com' in url:
                    pan_name = "百度网盘"
                elif '123pan.com' in url:
                    pan_name = "123云盘"
                elif 'lanzou' in url:
                    pan_name = "蓝奏云"
                elif 'aliyundrive.com' in url or 'alipan.com' in url:
                    pan_name = "阿里云盘"
                elif url.endswith('.mrpack'):
                    pan_name = f"Modrinth包 ({size_mb})" if size_mb else "Modrinth包下载"
                elif url.endswith('.zip'):
                    pan_name = f"ZIP客户端 ({size_mb})" if size_mb else "客户端ZIP下载"
                else:
                    pan_name = "直接下载"

                links.append({
                    "name": pan_name,
                    "url": url,
                    "version": ver_name,
                    "filename": fn,
                    "size": size_mb
                })

        return links


def format_iso_time(iso_str: str) -> str:
    """将 ISO 时间字符串转换为可读格式 YYYY-MM-DD HH:MM"""
    if not iso_str:
        return "未知"
    try:
        clean = iso_str.replace('Z', '+00:00')
        dt = datetime.fromisoformat(clean)
        return dt.strftime('%Y-%m-%d %H:%M')
    except Exception:
        return iso_str[:10] if len(iso_str) >= 10 else iso_str


def parse_timestamp(iso_str: str) -> int:
    """将 ISO 时间转换为秒级时间戳"""
    if not iso_str:
        return 0
    try:
        clean = iso_str.replace('Z', '+00:00')
        dt = datetime.fromisoformat(clean)
        return int(dt.timestamp())
    except Exception:
        return 0


def standardize_pack(item: Dict[str, Any]) -> Dict[str, Any]:
    """标准化单个项目格式，对齐看板数据模型"""
    pid = item.get('project_id') or item.get('id') or ''
    slug = item.get('slug') or pid
    ptype = item.get('project_type', 'modpack')
    
    # 类别提取
    cats = item.get('display_categories') or []
    all_cats = item.get('categories') or []
    
    # 加载器提取
    loaders = []
    loaders_set = {'forge', 'fabric', 'neoforge', 'quilt'}
    for c in all_cats:
        c_low = c.lower()
        if c_low in loaders_set:
            loaders.append(c_low.capitalize() if c_low != 'neoforge' else 'NeoForge')
    if not loaders:
        loaders = ['Forge']  # 默认降级

    clean_categories = [c for c in cats if c.lower() not in loaders_set]
    if not clean_categories:
        clean_categories = [c for c in all_cats if c.lower() not in loaders_set]

    # 图标与画廊
    icon_url = item.get('icon_url') or ''
    gallery = item.get('gallery') or []
    featured_gallery = item.get('featured_gallery') or (gallery[0] if gallery else '')

    # 时间解析
    created_str = format_iso_time(item.get('date_created', ''))
    modified_str = format_iso_time(item.get('date_modified', ''))
    created_ts = parse_timestamp(item.get('date_created', ''))
    modified_ts = parse_timestamp(item.get('date_modified', ''))

    # MC 版本
    mc_versions = item.get('versions') or []
    primary_version = mc_versions[0] if mc_versions else "未知"

    return {
        "platform": "bbsmc",
        "project_id": pid,
        "slug": slug,
        "url": f"https://bbsmc.net/{'modpack' if ptype == 'modpack' else 'mod'}/{slug}",
        "title": item.get('title', '').strip(),
        "author": item.get('author', '').strip(),
        "description": item.get('description', '').strip(),
        "downloads": item.get('downloads', 0),
        "followers": item.get('follows', 0),
        "mc_version": primary_version,
        "all_versions": mc_versions,
        "loaders": loaders,
        "categories": clean_categories,
        "icon_url": icon_url,
        "gallery": gallery,
        "featured_gallery": featured_gallery,
        "date_created": created_str,
        "date_modified": modified_str,
        "created_timestamp": created_ts,
        "modified_timestamp": modified_ts,
        "download_links": item.get('download_links', []),
        "latest_version": item.get('latest_version', ''),
        "has_server": item.get('has_server', False),
        "versions_data": item.get('versions_data', [])
    }


def crawl_bbsmc(project_type: str = "modpack", max_total: int = 0, enrich_versions_count: int = 400) -> List[Dict[str, Any]]:
    """主采集流水线"""
    print("=" * 65)
    print(f"  BBSMC (好创/BBSMC) Minecraft 资源专版采集引擎启动")
    print(f"  -> 目标类型: {project_type}")
    print(f"  -> 采集上限: {'全量无限制' if not max_total else f'{max_total} 款'}")
    print("=" * 65)

    crawler = BbsmcCrawler()
    raw_projects = crawler.search_all_projects(project_type=project_type, max_total=max_total)

    if not raw_projects:
        print("[!] 未获取到任何项目数据，退出。")
        return []

    # 丰富前 N 款热门项目的实际下载链接
    if enrich_versions_count > 0:
        actual_enrich = min(len(raw_projects), enrich_versions_count)
        crawler.enrich_project_downloads(raw_projects, max_enrich=actual_enrich)

    # 标准化转换
    processed = [standardize_pack(p) for p in raw_projects]

    # 按下载量降序排序
    processed.sort(key=lambda x: x['downloads'], reverse=True)

    print(f"\n[正在保存数据]...")
    repo_root = os.path.abspath(
        os.environ.get("MC_DESKTOP_WORKSPACE")
        or os.path.dirname(os.path.abspath(__file__))
    )

    # 1. 保存 JSON
    out_dir = os.path.join(repo_root, "crawler_output")
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "bbsmc_modpacks.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(processed, f, ensure_ascii=False, indent=2)

    # 2. 保存前端 JS 数据源
    data_dir = os.path.join(repo_root, "converted_output", "data")
    os.makedirs(data_dir, exist_ok=True)
    js_path = os.path.join(data_dir, "bbsmc_data.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("window.bbsmcModpacksData = " + json.dumps(processed, ensure_ascii=False) + ";\n")

    total_downloads = sum(x['downloads'] for x in processed)
    total_pan = sum(len(x['download_links']) for x in processed)

    print("=" * 65)
    print("BBSMC 资源采集完成！")
    print(f"  - 成功获取项目: {len(processed)} 款")
    print(f"  - 累计总下载量: {total_downloads:,} 次")
    print(f"  - 已解析直达下载/网盘链接: {total_pan} 个")
    print(f"  - JSON 归档: {json_path}")
    print(f"  - 前端数据源: {js_path}")
    print("=" * 65)

    return processed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BBSMC (好创) 整合包/模组资源采集引擎")
    parser.add_argument("-t", "--type", default="modpack", choices=["modpack", "mod"], help="项目类型: modpack(整合包, 默认) 或 mod(单体模组)")
    parser.add_argument("-m", "--max", type=int, default=0, help="最多拉取条数（默认: 0 为全量）")
    parser.add_argument("-e", "--enrich", type=int, default=400, help="深入解析下载网盘直链的项目数（默认: 400 款）")
    args = parser.parse_args()

    crawl_bbsmc(project_type=args.type, max_total=args.max, enrich_versions_count=args.enrich)

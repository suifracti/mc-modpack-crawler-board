#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
====================================================================
  XYEBBS (小叶论坛/像素世界) Minecraft 整合包专区采集引擎 v1.0
====================================================================
特性：
1. 原生对接 XYEBBS (resource-api.xyeidc.com) REST API，毫秒级快速拉取
2. 支持分页批量全量采集（5,100+ 独立整合包）
3. 并发解析各整合包真实发布版本（Releases）与下载网盘（夸克、百度、迅雷、123网盘等）
4. 结构化抽取 MC 游戏版本、模组加载器（Forge/Fabric/NeoForge/Quilt）、多维分类标签与封面图标
5. 同步产出 JSON 归档数据与前端直接加载的 JS 数据源（xyebbs_data.js）
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
    'Origin': 'https://www.xyebbs.com',
    'Referer': 'https://www.xyebbs.com/',
}

BASE_API = "https://resource-api.xyeidc.com"


class XyebbsCrawler:
    def __init__(self, api_base: str = BASE_API, max_workers: int = 20):
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
                time.sleep(0.4 * (attempt + 1))
            except Exception:
                time.sleep(0.4 * (attempt + 1))
        return None

    def fetch_all_resources(self, max_total: int = 0, page_size: int = 100) -> List[Dict[str, Any]]:
        """全量分页拉取整合包元数据列表"""
        all_items = []
        page = 1
        total_count = None
        total_pages = None

        print(f"[*] 正在从 XYEBBS 获取整合包全量列表 (单页步长: {page_size})...")

        while True:
            params = {
                "page": page,
                "per": page_size,
                "resourceTypeId": 2,
                "view": "true",
                "verified": "true",
                "archived": "false",
                "sortBy": "HOT"
            }
            res = self._get_json("client/resources", params)
            if not res or 'data' not in res or not res['data']:
                print(f"  [!] 在 page={page} 处请求失败或无数据，停止拉取。")
                break

            data_obj = res.get('data', {})
            items = data_obj.get('data', [])
            if not items:
                break

            if total_count is None:
                total_count = data_obj.get('count', 0)
                total_pages = data_obj.get('totalPages', 1)
                print(f"  [√] XYEBBS 官方返回整合包总数: {total_count} 款 (共 {total_pages} 页)")

            all_items.extend(items)
            print(f"  -> 已获取 {len(all_items):4d} / {total_count} 款 (当前页: {page}/{total_pages})")

            if max_total and len(all_items) >= max_total:
                all_items = all_items[:max_total]
                break

            if page >= total_pages or len(items) < page_size:
                break

            page += 1
            time.sleep(0.08)

        print(f"[+] 列表检索完成，共纳录 {len(all_items)} 款整合包项目元数据。\n")
        return all_items

    def fetch_resource_releases(self, resource_id: int) -> List[Dict[str, Any]]:
        """获取单个整合包的版本发布历史与下载网盘链接"""
        data = self._get_json(f"client/resources/{resource_id}/releases", {"includes": "links"}, timeout=6)
        if data and isinstance(data, dict):
            inner = data.get('data')
            if isinstance(inner, dict):
                return inner.get('data', [])
            elif isinstance(inner, list):
                return inner
        return []

    def enrich_resource_downloads(self, resources: List[Dict[str, Any]], max_enrich: int = 1500) -> None:
        """并发丰富前 N 款热门整合包的实际下载网盘直链"""
        to_enrich = resources[:max_enrich]
        print(f"[*] 正在并发拉取前 {len(to_enrich)} 款热门项目的详细版本与下载网盘 (线程数: {self.max_workers})...")

        start_time = time.time()
        completed = 0
        enriched_count = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_res = {executor.submit(self.fetch_resource_releases, r['id']): r for r in to_enrich}
            for future in as_completed(future_to_res):
                r = future_to_res[future]
                completed += 1
                try:
                    releases = future.result()
                    if releases:
                        download_links = self._extract_download_links(releases, r['id'])
                        r['download_links'] = download_links
                        cleaned_releases = []
                        for rel in releases[:15]:
                            rel_links = []
                            for lk in rel.get('links', []):
                                u = (lk.get('url') or '').strip()
                                if u:
                                    pname = "网盘下载"
                                    ltype = str(lk.get('linkType') or '').upper()
                                    if 'quark.cn' in u or ltype == 'QUARK':
                                        pname = "夸克网盘"
                                    elif 'baidu.com' in u or ltype == 'BAIDU':
                                        pname = "百度网盘"
                                    elif '123pan.com' in u or '123684.com' in u or ltype == 'PAN123':
                                        pname = "123云盘"
                                    elif 'xunlei.com' in u or ltype == 'XUN_LEI':
                                        pname = "迅雷网盘"
                                    elif 'lanzou' in u or ltype == 'LANZOU':
                                        pname = "蓝奏云"
                                    is_server = bool(re.search(r'(?:server|服务端|开服包|服端)', (lk.get("name") or "") + " " + (rel.get("label") or ""), re.I))
                                    rel_links.append({
                                        "name": pname,
                                        "url": u,
                                        "type": ltype,
                                        "is_server": is_server
                                    })
                            cleaned_releases.append({
                                "label": rel.get("label", ""),
                                "create_date": format_iso_time(rel.get("createDate", "")),
                                "downloads": rel.get("downloadCount", 0),
                                "notes": (rel.get("notes") or "").strip(),
                                "links": rel_links
                            })
                        r['releases_data'] = cleaned_releases
                        r['has_server'] = any(lk.get('is_server') for rel in cleaned_releases for lk in rel.get('links', [])) or bool(re.search(r'(?:服务端|server|开服|服端)', (r.get('title') or "") + " " + (r.get('description') or "") + " " + (r.get('sub_title') or ""), re.I))
                        if download_links:
                            enriched_count += 1
                except Exception:
                    pass

                if completed % 100 == 0 or completed == len(to_enrich):
                    elapsed = time.time() - start_time
                    rate = completed / elapsed if elapsed > 0 else 0
                    print(f"  [{completed:4d}/{len(to_enrich)}] 网盘解析中... 耗时: {elapsed:.1f}s ({rate:.1f}req/s), 已解析直链项目: {enriched_count}")

        print(f"[+] 下载直链解析完成！共为 {enriched_count} 款整合包提取到了直接网盘转存/下载链接。\n")

    @staticmethod
    def _extract_download_links(releases: List[Dict[str, Any]], resource_id: int) -> List[Dict[str, str]]:
        """从版本发布列表中提取多网盘与直链"""
        links = []
        seen = set()

        for rel in releases:
            rel_label = rel.get('label') or '发布版'
            for link_obj in rel.get('links', []):
                url = (link_obj.get('url') or '').strip()
                if not url or url in seen:
                    continue
                seen.add(url)

                ltype = str(link_obj.get('linkType') or '').upper()
                # 识别网盘分类名
                if 'quark.cn' in url or ltype == 'QUARK':
                    pan_name = "夸克网盘"
                    pan_type = "QUARK"
                elif 'baidu.com' in url or ltype == 'BAIDU':
                    pan_name = "百度网盘"
                    pan_type = "BAIDU"
                elif '123pan.com' in url or '123684.com' in url or ltype == 'PAN123':
                    pan_name = "123云盘"
                    pan_type = "PAN123"
                elif 'lanzou' in url or ltype == 'LANZOU':
                    pan_name = "蓝奏云"
                    pan_type = "LANZOU"
                elif 'xunlei.com' in url or ltype == 'XUN_LEI':
                    pan_name = "迅雷网盘"
                    pan_type = "XUNLEI"
                elif 'aliyundrive.com' in url or 'alipan.com' in url or ltype == 'ALI':
                    pan_name = "阿里云盘"
                    pan_type = "ALIPAN"
                else:
                    pan_name = "网盘下载"
                    pan_type = "OTHER"

                links.append({
                    "name": pan_name,
                    "url": url,
                    "type": pan_type,
                    "label": rel_label
                })

        return links


def format_iso_time(date_str: str) -> str:
    """格式化时间字符串 YYYY-MM-DD HH:MM"""
    if not date_str:
        return "未知"
    try:
        if 'T' in date_str:
            clean = date_str.replace('Z', '+00:00')
            dt = datetime.fromisoformat(clean)
            return dt.strftime('%Y-%m-%d %H:%M')
        else:
            return date_str[:16]
    except Exception:
        return date_str[:10] if len(date_str) >= 10 else date_str


def parse_timestamp(date_str: str) -> int:
    """将日期转换为秒级时间戳"""
    if not date_str:
        return 0
    try:
        if 'T' in date_str:
            clean = date_str.replace('Z', '+00:00')
            dt = datetime.fromisoformat(clean)
            return int(dt.timestamp())
        else:
            dt = datetime.strptime(date_str[:19], '%Y-%m-%d %H:%M:%S')
            return int(dt.timestamp())
    except Exception:
        return 0


def standardize_pack(item: Dict[str, Any]) -> Dict[str, Any]:
    """标准化单个 XYEBBS 项目格式，对齐看板数据模型"""
    rid = item.get('id')
    slug = item.get('identify') or str(rid)
    url = f"https://www.xyebbs.com/res-id/{item['identify']}" if item.get('identify') else f"https://www.xyebbs.com/resources/{rid}"

    # 提取标签与分类
    raw_tags = item.get('tags') or []
    tags = []
    seen_tags = set()
    for t in raw_tags:
        if isinstance(t, dict):
            name = (t.get('name') or '').strip()
            if name and name not in seen_tags:
                seen_tags.add(name)
                tags.append(name)
        elif isinstance(t, str) and t.strip() and t.strip() not in seen_tags:
            seen_tags.add(t.strip())
            tags.append(t.strip())

    # 提取 MC 版本
    raw_vers = item.get('versions') or []
    vers = []
    seen_vers = set()
    for v in raw_vers:
        if isinstance(v, dict):
            name = (v.get('name') or '').strip()
            if name and name not in seen_vers:
                seen_vers.add(name)
                vers.append(name)
        elif isinstance(v, str) and v.strip() and v.strip() not in seen_vers:
            seen_vers.add(v.strip())
            vers.append(v.strip())
    primary_version = vers[0] if vers else "未知"

    # 提取模组加载器
    raw_cores = item.get('cores') or []
    cores = []
    seen_cores = set()
    for c in raw_cores:
        if isinstance(c, dict):
            name = (c.get('name') or '').strip()
            if name and name not in seen_cores:
                seen_cores.add(name)
                cores.append(name)
        elif isinstance(c, str) and c.strip() and c.strip() not in seen_cores:
            seen_cores.add(c.strip())
            cores.append(c.strip())
    if not cores:
        cores = ['Forge']  # 降级兜底

    # 统计数据
    stat = item.get('stat') or {}
    downloads = stat.get('downloadCount') or 0
    views = stat.get('viewCount') or 0
    likes = item.get('likeCount') or 0
    comments = item.get('postCount') or 0

    # 作者
    owner = item.get('owner') or {}
    author = owner.get('username') or owner.get('gameId') or 'XYEBBS用户'

    # 图片
    logo_uuid = item.get('logoImgUuid')
    head_uuid = item.get('headImgUuid')
    icon_url = f"https://resource-api.xyeidc.com/client/members/pics/{logo_uuid}/mini" if logo_uuid else ""
    head_url = f"https://resource-api.xyeidc.com/client/members/pics/{head_uuid}/mini" if head_uuid else ""

    # 时间
    create_date = format_iso_time(item.get('createDate', ''))
    update_date = format_iso_time(item.get('updateDate', ''))
    create_ts = parse_timestamp(item.get('createDate', ''))
    update_ts = parse_timestamp(item.get('updateDate', ''))

    # 下载链接
    download_links = item.get('download_links') or []
    # 若无提取到特定网盘，注入默认原站资源下载专页
    if not download_links:
        download_links = [{
            "name": "XYEBBS 资源下载页",
            "url": f"https://www.xyebbs.com/resources/{rid}/downloads",
            "type": "OFFICIAL",
            "label": "站内发布"
        }]

    return {
        "platform": "xyebbs",
        "project_id": str(rid),
        "slug": slug,
        "url": url,
        "title": (item.get('name') or '').strip(),
        "english_name": (item.get('englishName') or '').strip(),
        "author": author,
        "description": (item.get('description') or '').strip(),
        "downloads": downloads,
        "views": views,
        "likes": likes,
        "comments": comments,
        "mc_version": primary_version,
        "all_versions": vers,
        "loaders": cores,
        "categories": tags,
        "icon_url": icon_url,
        "head_url": head_url,
        "date_created": create_date,
        "date_modified": update_date,
        "created_timestamp": create_ts,
        "modified_timestamp": update_ts,
        "download_links": download_links,
        "has_server": item.get('has_server', False),
        "releases_data": item.get('releases_data', []),
        "source_meta": item.get('meta') or {}
    }


def crawl_xyebbs(max_total: int = 0, enrich_count: int = 1500) -> List[Dict[str, Any]]:
    """主采集流水线"""
    print("=" * 65)
    print(f"  XYEBBS (小叶论坛/像素世界) 整合包专区采集引擎启动")
    print(f"  -> 采集上限: {'全量无限制' if not max_total else f'{max_total} 款'}")
    print(f"  -> 下载网盘深度解析数量: 前 {enrich_count} 款热门项目")
    print("=" * 65)

    crawler = XyebbsCrawler(max_workers=25)
    repo_root = os.path.abspath(
        os.environ.get("MC_DESKTOP_WORKSPACE")
        or os.path.dirname(os.path.abspath(__file__))
    )
    out_dir = os.path.join(repo_root, "crawler_output")
    os.makedirs(out_dir, exist_ok=True)
    raw_cache_path = os.path.join(out_dir, "xyebbs_raw.json")

    raw_items = []
    if os.path.exists(raw_cache_path) and not max_total:
        try:
            with open(raw_cache_path, "r", encoding="utf-8") as f:
                raw_items = json.load(f)
            print(f"  [√] 从本地缓存命中 {len(raw_items)} 款整合包元数据！", flush=True)
        except Exception:
            raw_items = []

    if not raw_items:
        raw_items = crawler.fetch_all_resources(max_total=max_total)
        if raw_items and not max_total:
            with open(raw_cache_path, "w", encoding="utf-8") as f:
                json.dump(raw_items, f, ensure_ascii=False)

    if not raw_items:
        print("[!] 未获取到任何项目数据，退出。", flush=True)
        return []

    # 丰富前 N 款热门项目的实际网盘链接
    if enrich_count > 0:
        actual_enrich = min(len(raw_items), enrich_count)
        crawler.enrich_resource_downloads(raw_items, max_enrich=actual_enrich)

    # 标准化数据
    standardized = [standardize_pack(it) for it in raw_items]

    # 保存路径
    repo_root = os.path.abspath(
        os.environ.get("MC_DESKTOP_WORKSPACE")
        or os.path.dirname(os.path.abspath(__file__))
    )
    out_dir = os.path.join(repo_root, "crawler_output")
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "xyebbs_modpacks.json")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(standardized, f, ensure_ascii=False, indent=2)

    # 产出 JS 数据源
    js_dir = os.path.join(repo_root, "converted_output", "data")
    os.makedirs(js_dir, exist_ok=True)
    js_path = os.path.join(js_dir, "xyebbs_data.js")

    with open(js_path, "w", encoding="utf-8") as f:
        f.write("window.xyebbsModpacksData = ")
        json.dump(standardized, f, ensure_ascii=False)
        f.write(";\n")

    # 统计信息
    total_dl = sum(p['downloads'] for p in standardized)
    total_views = sum(p['views'] for p in standardized)
    with_links = sum(1 for p in standardized if any(l.get('type') != 'OFFICIAL' for l in p.get('download_links', [])))

    print("=" * 65)
    print("  [SUCCESS] XYEBBS 采集完成！")
    print(f"  -> 收录整合包总数: {len(standardized)} 款")
    print(f"  -> 累计全网下载量: {total_dl:,} 次")
    print(f"  -> 累计全网浏览量: {total_views:,} 次")
    print(f"  -> 拥有独立网盘直链: {with_links} 款")
    print(f"  -> 归档 JSON 路径: {json_path} ({os.path.getsize(json_path)/1024/1024:.2f} MB)")
    print(f"  -> 前端 JS 路径:   {js_path} ({os.path.getsize(js_path)/1024/1024:.2f} MB)")
    print("=" * 65)

    return standardized


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="XYEBBS 整合包专区全量采集引擎")
    parser.add_argument("--max", type=int, default=0, help="最多抓取整合包数量 (0 表示全量)")
    parser.add_argument("--enrich", type=int, default=1500, help="并发深度解析下载网盘的前 N 款热门包")
    args = parser.parse_args()

    crawl_xyebbs(max_total=args.max, enrich_count=args.enrich)

# -*- coding: utf-8 -*-
"""
====================================================================
  MC百科 (MCMod.cn) 超级全量全自动深挖增量采集引擎 v2.1
====================================================================
特性：
1. 自适应动态 ID 探针 (Dynamic Adaptive Probing)：
   - 彻底移除硬编码 probe_max 限制；
   - 自动读取本地已知 ID 集合，计算当前最大 ID (max_mid)；
   - 从 max_mid + 1 向上逐个探测，连续遇到 N 个 404 (默认 8 个，可配置) 时安全终止；
   - 维护已知 404 墓碑黑名单（历史 28 个删帖 ID），避免重复无效请求，支持 --recheck-holes 复查。
2. 无限历史走势时间线缝合引擎 (Infinite Trend Merger)：
   - 免登录逆向打通官方 POST /frame/modpack/ModpackChart/ 走势接口；
   - 自动提取官方近 60 天滚动每日指数与日期；
   - 与本地历史 trend_dates 动态并集融合，破除 60 天截断，支持无限沉淀 120天、365天甚至更长；
   - 自动重算全周期峰值、均值、沉淀天数与多周期涨幅，重新渲染高清 SVG Sparkline 微图。
3. 真实整合包版本更新日志系统 (Real Modpack Version Releases)：
   - 打通 https://www.mcmod.cn/modpack/version/{mid}.html 版本专页；
   - 提取真正的整合包最新版本号、最新更新日期、初代发布时间及版本发布总数；
   - 彻底纠正将百科词条编辑时间混同于整合包更新时间的偏差；
   - 前端看板直接挂载“📜 更新日志 ↗”直达链接。
4. 智能多模式运行 (Intelligent Multi-Mode)：
   - --mode new (默认): 仅向上增量探测全新整合包，秒级轻量退出，适合日常高频轮询；
   - --mode trend: 多线程并发刷新存量整合包走势并执行“无限时间线缝合”与真实版本日志提取；
   - --mode metrics: 多线程定向刷新存量整合包实时基础指标（浏览量/指数/红黑票）；
   - --mode all: 串联执行：新包探测 + 指标刷新 + 走势缝合 + 版本日志。
5. 全网流水线对齐归档：
   - 保持 converted_output/data/table_rows.js 与 converted_output/data/app_data.js 完整兼容；
   - 同步自动归档 crawler_output/mcmod_modpacks.json，补齐六大平台标准化数据链路。
====================================================================
"""

import os
import sys
import json
import time
import re
import ast
import random
import argparse
import urllib.request
import urllib.parse
import http.cookiejar
from concurrent.futures import ThreadPoolExecutor, as_completed
from desktop_collection_contract import write_collection_result

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

REPO_ROOT = os.path.abspath(
    os.environ.get("MC_DESKTOP_WORKSPACE")
    or os.path.dirname(os.path.abspath(__file__))
)
TABLE_ROWS_PATH = os.path.join(REPO_ROOT, "converted_output", "data", "table_rows.js")
APP_DATA_PATH = os.path.join(REPO_ROOT, "converted_output", "data", "app_data.js")
RAW_OUTPUT_DIR = os.path.join(REPO_ROOT, "crawler_output")
RAW_JSON_PATH = os.path.join(RAW_OUTPUT_DIR, "mcmod_modpacks.json")

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
]

def get_headers(referer=None):
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': referer or 'https://www.mcmod.cn/',
    }

COOKIE_JAR = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(COOKIE_JAR))
IS_BANNED = False
COLLECTION_STATS = {"requests": 0, "successful": 0, "not_found": 0, "failed": 0, "errors": []}

def init_network(proxy=None, no_proxy=False):
    """初始化网络层，支持纯直连模式或指定 HTTP/HTTPS 代理"""
    global OPENER
    handlers = [urllib.request.HTTPCookieProcessor(COOKIE_JAR)]
    if no_proxy:
        # 强制纯直连：传入空的 ProxyHandler 字典，彻底屏蔽任何系统/环境变量代理
        handlers.append(urllib.request.ProxyHandler({}))
        print("  [网络连接] 纯直连模式 (Direct Connection，已强制忽略系统/环境变量代理)")
    elif proxy:
        handlers.append(urllib.request.ProxyHandler({'http': proxy, 'https': proxy}))
        print(f"  [网络代理] 已配置代理服务器: {proxy}")
    else:
        print("  [网络连接] 默认纯直连模式 (Direct Connection，温和防封已就绪)")
    OPENER = urllib.request.build_opener(*handlers)

def check_banned_response(text):
    """检测是否触发 MC百科 临时反爬频次拦截并输出友好的用户指引"""
    global IS_BANNED
    if text and ("已被系统封禁" in text or "banned for security reasons" in text):
        if not IS_BANNED:
            IS_BANNED = True
            print("\n  " + "=" * 68)
            print("  ⚠️ 【MC百科 访问频次安全防护提示】")
            print("  当前网络 IP 触发了 MC百科 服务器的临时访问频控防护。")
            print("  🛡️ 系统已即刻安全熔断中止，之前已缝合的数据 100% 完整安全保存在本地！")
            print("  💡 解封与继续爬取建议：")
            print("     1. [最推荐] 电脑断开 Wi-Fi 连一下手机移动热点，手机每次联网都会分配全新独立公网 IP，秒级即可继续！")
            print("     2. 重启光猫/路由器（重新拨号获取新公网 IP）；")
            print("     3. 若使用了代理软件（如 Clash/V2Ray），请将分流模式切换为【全局模式 (Global)】而非【规则模式】；")
            print("     4. 或静置数小时，服务器通常会自动解除临时频控限制。")
            print("  " + "=" * 68 + "\n")
        return True
    return False

# ═══════════════════════ 网络请求层 ═══════════════════════

def fetch_html(url, retries=3, timeout=12):
    """通用的轻量 HTML 获取函数 (带 CookieJar 与退避重试)"""
    global IS_BANNED
    if IS_BANNED:
        return None
    for attempt in range(retries):
        if IS_BANNED:
            return None
        try:
            COLLECTION_STATS["requests"] += 1
            req = urllib.request.Request(url, headers=get_headers())
            with OPENER.open(req, timeout=timeout) as resp:
                if resp.status == 404:
                    COLLECTION_STATS["not_found"] += 1
                    return None
                if resp.status == 200:
                    text = resp.read().decode('utf-8', errors='ignore')
                    if check_banned_response(text):
                        COLLECTION_STATS["failed"] += 1
                        COLLECTION_STATS["errors"].append("MC百科访问频控")
                        return None
                    COLLECTION_STATS["successful"] += 1
                    return text
        except urllib.error.HTTPError as e:
            if e.code == 404:
                COLLECTION_STATS["not_found"] += 1
                return None
            if attempt == retries - 1:
                COLLECTION_STATS["failed"] += 1
                COLLECTION_STATS["errors"].append(f"HTTP {e.code} {url}")
            else:
                time.sleep(1.0 * (attempt + 1))
        except Exception as error:
            if attempt == retries - 1:
                COLLECTION_STATS["failed"] += 1
                COLLECTION_STATS["errors"].append(f"{url}: {error}")
            else:
                time.sleep(1.5 * (attempt + 1))
    return None

def fetch_trend_data(mid, retries=3, timeout=12):
    """免登录提取官方近 60 天滚动走势数据 (带 CookieJar 与退避重试)"""
    global IS_BANNED
    if IS_BANNED:
        return []
    url = "https://www.mcmod.cn/frame/modpack/ModpackChart/"
    post_data = urllib.parse.urlencode({"data": json.dumps({"todo": "index", "id": int(mid)})}).encode("utf-8")
    headers = get_headers(referer=f'https://www.mcmod.cn/modpack/{mid}.html')
    headers['X-Requested-With'] = 'XMLHttpRequest'
    headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
    for attempt in range(retries):
        if IS_BANNED:
            return []
        try:
            COLLECTION_STATS["requests"] += 1
            req = urllib.request.Request(url, data=post_data, headers=headers)
            with OPENER.open(req, timeout=timeout) as resp:
                raw_text = resp.read().decode('utf-8', errors='ignore')
                if check_banned_response(raw_text):
                    COLLECTION_STATS["failed"] += 1
                    COLLECTION_STATS["errors"].append("MC百科走势请求触发风控")
                    return []
                COLLECTION_STATS["successful"] += 1
                data = json.loads(raw_text)
                if data.get("state") == 0:
                    html = data.get("html", "")
                    arrays = re.findall(r'data:\s*(\[[^\]]+\])', html)
                    if len(arrays) >= 2:
                        dates = [str(d) for d in ast.literal_eval(arrays[0])]
                        values = [float(v) for v in ast.literal_eval(arrays[1])]
                        return list(zip(dates, values))
        except urllib.error.HTTPError as error:
            if error.code == 404:
                COLLECTION_STATS["not_found"] += 1
                return []
            if attempt == retries - 1:
                COLLECTION_STATS["failed"] += 1
                COLLECTION_STATS["errors"].append(f"走势 HTTP {error.code} {mid}")
            else:
                time.sleep(1.5 * (attempt + 1))
        except Exception as error:
            if attempt == retries - 1:
                COLLECTION_STATS["failed"] += 1
                COLLECTION_STATS["errors"].append(f"走势 {mid}: {error}")
            else:
                time.sleep(1.5 * (attempt + 1))
    return []

def fetch_version_data(mid, retries=3, timeout=12):
    """提取真实整合包版本日志页面数据

    返回值里的 checked 用来区分两种"没有版本"：
      - checked=False：请求失败 / 被风控，属于没抓到，下次应重试；
      - checked=True ：页面正常返回但确认无更新日志（页面提示"暂无…更新日志"），
                       属于该整合包本身没发布日志，不需要反复重抓。
    """
    if IS_BANNED:
        return {
            "version_count": 0,
            "latest_version": "",
            "latest_date": "",
            "release_date": "",
            "versions": [],
            "checked": False
        }
    url = f"https://www.mcmod.cn/modpack/version/{mid}.html"
    html = fetch_html(url, retries=retries, timeout=timeout)
    if not html:
        return {
            "version_count": 0,
            "latest_version": "",
            "latest_date": "",
            "release_date": "",
            "versions": [],
            "checked": False
        }
    entries = re.findall(r'<span class="time">([^<]+)</span>.*?<span class="name">([^<]+)</span>', html, re.S)
    clean_entries = []
    for d_str, v_str in entries:
        d = d_str.strip()
        v = v_str.strip()
        if d and v:
            clean_entries.append({"version": v, "date": d})
    return {
        "version_count": len(clean_entries),
        "latest_version": clean_entries[0]["version"] if clean_entries else "",
        "latest_date": clean_entries[0]["date"] if clean_entries else "",
        "release_date": clean_entries[-1]["date"] if clean_entries else "",
        "versions": clean_entries,
        "checked": True
    }

# ═══════════════════════ 走势缝合与数据算法 ═══════════════════════

def merge_trend_series(existing_dates_str, existing_vals_str, new_points):
    """将本地历史走势与新抓取的走势点按日期并集融合，实现无限历史走势库"""
    timeline = {}
    if existing_dates_str and existing_vals_str:
        d_list = [d.strip() for d in str(existing_dates_str).split(",") if d.strip()]
        v_list = [v.strip() for v in str(existing_vals_str).split(",") if v.strip()]
        for d, v in zip(d_list, v_list):
            try:
                timeline[d] = float(v)
            except ValueError:
                pass
    for d, v in new_points:
        timeline[str(d)] = float(v)
    if not timeline:
        return "", "", []
    sorted_items = sorted(timeline.items(), key=lambda x: x[0])
    merged_dates = ",".join(x[0] for x in sorted_items)
    merged_vals = ",".join(f"{x[1]:.1f}" if x[1] != int(x[1]) else str(int(x[1])) for x in sorted_items)
    return merged_dates, merged_vals, sorted_items

def compute_trend_stats(sorted_points):
    """根据合并后的时间序列计算关键派生统计指标"""
    if not sorted_points:
        return 0, 0, 0, 0, 0, 0, 0, 0
    vals = [p[1] for p in sorted_points]
    n = len(vals)
    lat_n = int(vals[-1])
    max_n = int(max(vals))
    avg_n = round(sum(vals) / n, 1)
    days_n = n

    def growth(lookback):
        if n > lookback:
            base = vals[-1 - lookback]
            return round(((vals[-1] - base) / base) * 100, 1) if base > 0 else 0.0
        return 0.0

    t7_n = growth(7)
    t30_n = growth(30)
    t60_n = growth(60)
    tall_n = round(((vals[-1] - vals[0]) / vals[0]) * 100, 1) if vals[0] > 0 else 0.0
    return lat_n, max_n, avg_n, days_n, t7_n, t30_n, t60_n, tall_n

def generate_sparkline_svg(vals, width=118, height=34):
    """绘制高保真紧凑 SVG Sparkline 走势微图"""
    if not vals or len(vals) < 2:
        return ""
    min_v, max_v = min(vals), max(vals)
    v_range = max_v - min_v if max_v > min_v else 1.0
    pts = []
    n = len(vals)
    for i, v in enumerate(vals):
        x = round((i / (n - 1)) * 100.0, 1)
        y = round(22.0 - ((v - min_v) / v_range) * 20.0, 1)
        pts.append((x, y))
    line_d = "M " + " L ".join(f"{x} {y}" for x, y in pts)
    area_d = line_d + f" L {pts[-1][0]} 24 L {pts[0][0]} 24 Z"
    return (
        f'<svg class="sparkline-svg" viewBox="0 0 100 24" width="{width}" height="{height}" style="opacity: 0.95;">'
        f'<path d="{area_d}" fill="rgba(var(--primary-rgb), 0.1)"></path>'
        f'<path d="{line_d}" fill="none" stroke="var(--primary)" stroke-width="2" stroke-linecap="round"></path>'
        f'</svg>'
    )

# ═══════════════════════ HTML 单元格渲染组件 ═══════════════════════

def build_c0(mid, full_title, title_cn, title_en, cover_url, mold_id, type_name, views_d, latest_ver="", latest_date=""):
    title_en_display = title_en or "&nbsp;"
    ver_badge_html = ""
    if latest_ver:
        tip = f"最新版本: {latest_ver} ({latest_date})" if latest_date else f"最新版本: {latest_ver}"
        ver_badge_html = f'<a class="modpack-version-badge" href="https://www.mcmod.cn/modpack/version/{mid}.html" target="_blank" title="{tip}">📜 {latest_ver} ↗</a>'
    else:
        ver_badge_html = f'<a class="modpack-version-badge" href="https://www.mcmod.cn/modpack/version/{mid}.html" target="_blank" title="查看整合包真实版本发布与更新日志">📜 更新日志 ↗</a>'

    return (
        f'<button type="button" class="fav-star" data-mid="{mid}" title="收藏用于对比" aria-label="收藏用于对比">★</button>'
        f'<button type="button" class="modpack-cover-thumb image-thumb" data-image-url="{cover_url}" title="{full_title} 封面（悬停 1 秒放大）" aria-label="查看整合包封面">'
        f'<img src="{cover_url}" alt="{full_title} 封面" loading="lazy"></button>'
        f'<a href="https://www.mcmod.cn/modpack/{mid}.html" target="_blank" class="modpack-link" data-url="https://www.mcmod.cn/modpack/{mid}.html" data-mid="{mid}" data-full-title="{full_title}">'
        f'<span class="modpack-title-cn">{title_cn}</span><span class="modpack-title-en">{title_en_display}</span></a>'
        f'<div class="modpack-meta-row"><a class="modpack-type-badge" href="https://www.mcmod.cn/modpack.html?mold={mold_id}" target="_blank" title="打开 MC百科类型页">{type_name}</a>'
        f'<span class="modpack-views-badge" title="总浏览量">👁 {views_d}</span> {ver_badge_html}</div>'
    )

def build_c1(score_n, lat_n, max_n, avg_n, days_n, vals=None):
    svg_html = generate_sparkline_svg(vals) if vals and len(vals) >= 2 else ""
    hint = "点击看图" if svg_html else "MC百科"
    mid_row = f'{svg_html}<span class="trend-val-lat" title="最新指数" style="font-weight: 700; color: var(--primary-light);">最新: {lat_n}</span><span class="trend-open-hint">{hint}</span>'
    return (
        f'<div class="trend-consolidated-cell"><div class="trend-score-badge" title="官方流行指数评分"><span>流行</span><b>{score_n}</b></div>'
        f'<div class="trend-main-row">{mid_row}</div>'
        f'<div class="trend-meta-row"><span class="trend-val-max" title="最高指数">高: {max_n}</span><span class="trend-val-avg" title="平均指数">平: {avg_n}</span><span class="trend-val-days" title="走势天数">{days_n}天</span></div></div>'
    )

def build_c2(t7_n, t30_n, t60_n, tall_n):
    def fmt_item(label, val, title):
        cls = "td-up" if val > 0 else ("td-down" if val < 0 else "td-neutral")
        sign = "+" if val > 0 else ""
        return f'<span class="growth-val-{label} {cls}" title="{title}">{label}: {sign}{val:.0f}%</span>'
    i7 = fmt_item("7日", t7_n, "7日涨幅")
    i30 = fmt_item("30日", t30_n, "30日涨幅")
    i60 = fmt_item("60日", t60_n, "60日涨幅")
    iall = fmt_item("总幅", tall_n, "总涨幅")
    return (
        '<div class="growth-consolidated-cell" style="display: flex; flex-direction: column; gap: 2px; font-size: 0.76rem;">'
        f'<div style="display: flex; justify-content: space-between; gap: 8px;">{i7}{i30}</div>'
        f'<div style="display: flex; justify-content: space-between; gap: 8px;">{i60}{iall}</div></div>'
    )

def build_c3(rv_n, rp_n, bv_n, bp_n):
    return (
        f'<div class="votes-consolidated-cell" style="display: flex; flex-direction: column; gap: 4px; padding: 4px 0; font-size: 0.76rem;">'
        f'<div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;"><span style="font-weight: 700; color: var(--success); font-size: 0.82rem;">{rv_n + bv_n} 票</span>'
        f'<span style="font-size: 0.72rem; padding: 1px 5px; border-radius: 6px; background: rgba(16, 185, 129, 0.12); color: var(--success); font-weight: 600;">{rp_n}% 红</span></div>'
        f'<div class="vote-ratio-bar" style="width: 100%; height: 5px; border-radius: 3px; background: rgba(128,128,128,0.15); display: flex; overflow: hidden; margin: 2px 0;" title="红占比: {rp_n}% | 黑占比: {bp_n}%">'
        f'<div class="vote-ratio-red" style="height: 100%; width: {rp_n}%; background: var(--success);"></div><div class="vote-ratio-black" style="height: 100%; width: {bp_n}%; background: #6b7280;"></div></div>'
        f'<div style="display: flex; justify-content: space-between; font-size: 0.7rem; color: var(--text-muted);"><span>黑票: {bv_n}</span><span>占比: {bp_n}%</span></div></div>'
    )

def build_c4(rec_n, fav_n, com_n):
    return (
        f'<div class="engage-cell"><span><b>{rec_n}</b><em>推</em></span><span><b>{fav_n}</b><em>藏</em></span>'
        f'<span class="engage-comment-trigger" role="button" tabindex="0" title="点击评论格打开 / 再点关闭"><b>{com_n}</b><em>评</em><i class="comment-open-dot" aria-hidden="true">⌕</i></span></div>'
    )

# ═══════════════════════ 页面解析层 ═══════════════════════

def parse_mcmod_pack(mid, html):
    """完整解析整合包详情页数据"""
    t_m = re.search(r'<title>(.*?)</title>', html)
    full_title = t_m.group(1).split(' - MC百科')[0].strip() if t_m else f"Modpack {mid}"
    title_cn, title_en = full_title, ""
    if ' (' in full_title and full_title.endswith(')'):
        p = full_title.rsplit(' (', 1)
        title_cn = p[0].strip()
        title_en = p[1][:-1].strip()

    cover_m = re.search(r'data-src="([^"]*modpack/cover[^"]*)"', html) or re.search(r'src="([^"]*modpack/cover[^"]*)"', html)
    cover_url = ""
    if cover_m:
        raw_cov = cover_m.group(1)
        cover_url = ('https:' + raw_cov) if raw_cov.startswith('//') else raw_cov

    views_m = re.search(r'title="(\d+)"[^>]*class="span"[^>]*>\s*<p class="n">([^<]+)</p>\s*<p class="t">总浏览</p>', html)
    views_n = int(views_m.group(1)) if views_m else 0
    views_d = f"{views_n / 10000.0:.2f}万" if views_n >= 10000 else str(views_n)

    idx_m = re.search(r'昨日指数:\s*([0-9.]+)', html)
    lat_n = int(float(idx_m.group(1))) if idx_m else 0

    mold_m = re.search(r'mold=([12])[^>]*>([^<]+)</a>', html)
    mold_id = mold_m.group(1) if mold_m else "1"
    type_name = mold_m.group(2).strip() if mold_m else "原生整合"

    rv_m = re.search(r'投红票[：:\s]*(\d+)', html) or re.search(r'红票[：:\s]*(\d+)', html)
    rv_n = int(rv_m.group(1)) if rv_m else 0
    bv_m = re.search(r'投黑票[：:\s]*(\d+)', html) or re.search(r'黑票[：:\s]*(\d+)', html)
    bv_n = int(bv_m.group(1)) if bv_m else 0
    tot_v = rv_n + bv_n
    rp_n = round((rv_n / tot_v) * 100) if tot_v > 0 else 50
    bp_n = 100 - rp_n if tot_v > 0 else 50

    rec_m = re.search(r'推荐[：:\s]*(\d+)', html)
    rec_n = int(rec_m.group(1)) if rec_m else 0
    fav_m = re.search(r'收藏[：:\s]*(\d+)', html)
    fav_n = int(fav_m.group(1)) if fav_m else 0
    com_m = re.search(r'评论[：:\s]*(\d+)', html)
    com_n = int(com_m.group(1)) if com_m else 0

    cats = list(dict.fromkeys(re.findall(r'/modpack/category/\d+-\d+\.html[^>]*>([^<]+)</a>', html)))
    mc_vers = list(dict.fromkeys(re.findall(r'mcver=([0-9.]+)', html)))
    
    # 提取模组
    raw_mods = re.findall(r'/class/(\d+)\.html[^>]*>([^<]+)</a>', html)
    mods = []
    seen_m = set()
    for cid, mname in raw_mods:
        mname = mname.strip()
        if mname and mname not in seen_m and not mname.startswith(('添加', '编辑', '评论', '回复')):
            seen_m.add(mname)
            mods.append({
                "name": mname,
                "title": mname,
                "class_id": cid,
                "url": f"https://www.mcmod.cn/class/{cid}.html"
            })

    score_n = 5 if lat_n > 500 else (4 if lat_n > 200 else (3 if lat_n > 50 else (2 if lat_n > 10 else 1)))

    return {
        "mid": str(mid),
        "full_title": full_title,
        "title_cn": title_cn,
        "title_en": title_en,
        "cover_url": cover_url,
        "views_n": views_n,
        "views_d": views_d,
        "lat_n": lat_n,
        "score_n": score_n,
        "mold_id": mold_id,
        "type_name": type_name,
        "rv_n": rv_n,
        "rp_n": rp_n,
        "bv_n": bv_n,
        "bp_n": bp_n,
        "rec_n": rec_n,
        "fav_n": fav_n,
        "com_n": com_n,
        "categories": cats,
        "mc_versions": mc_vers,
        "mods": mods
    }

def parse_metrics_only(html):
    """轻量提取存量包动态指标"""
    views_m = re.search(r'title="(\d+)"[^>]*class="span"[^>]*>\s*<p class="n">([^<]+)</p>\s*<p class="t">总浏览</p>', html)
    views_n = int(views_m.group(1)) if views_m else None
    views_d = f"{views_n / 10000.0:.2f}万" if views_n and views_n >= 10000 else (str(views_n) if views_n is not None else "")

    idx_m = re.search(r'昨日指数:\s*([0-9.]+)', html)
    lat_n = int(float(idx_m.group(1))) if idx_m else None
    score_n = (5 if lat_n > 500 else (4 if lat_n > 200 else (3 if lat_n > 50 else (2 if lat_n > 10 else 1)))) if lat_n is not None else None

    rv_m = re.search(r'投红票[：:\s]*(\d+)', html) or re.search(r'红票[：:\s]*(\d+)', html)
    rv_n = int(rv_m.group(1)) if rv_m else 0
    bv_m = re.search(r'投黑票[：:\s]*(\d+)', html) or re.search(r'黑票[：:\s]*(\d+)', html)
    bv_n = int(bv_m.group(1)) if bv_m else 0
    tot_v = rv_n + bv_n
    rp_n = round((rv_n / tot_v) * 100) if tot_v > 0 else 50
    bp_n = 100 - rp_n if tot_v > 0 else 50

    rec_m = re.search(r'推荐[：:\s]*(\d+)', html)
    rec_n = int(rec_m.group(1)) if rec_m else 0
    fav_m = re.search(r'收藏[：:\s]*(\d+)', html)
    fav_n = int(fav_m.group(1)) if fav_m else 0
    com_m = re.search(r'评论[：:\s]*(\d+)', html)
    com_n = int(com_m.group(1)) if com_m else 0

    # 标题与更名检测 (提取最新标题以支持增量改名识别)
    t_m = re.search(r'<title>(.*?)</title>', html)
    full_title = t_m.group(1).split(' - MC百科')[0].strip() if t_m else None
    title_cn, title_en = "", ""
    if full_title:
        title_cn = full_title
        if ' (' in full_title and full_title.endswith(')'):
            p = full_title.rsplit(' (', 1)
            title_cn = p[0].strip()
            title_en = p[1][:-1].strip()

    return {
        "full_title": full_title,
        "title_cn": title_cn,
        "title_en": title_en,
        "views_n": views_n,
        "views_d": views_d,
        "lat_n": lat_n,
        "score_n": score_n,
        "rv_n": rv_n,
        "rp_n": rp_n,
        "bv_n": bv_n,
        "bp_n": bp_n,
        "rec_n": rec_n,
        "fav_n": fav_n,
        "com_n": com_n,
    }

# ═══════════════════════ 行构建与更新层 ═══════════════════════

def build_table_row(p, trend_points=None, version_info=None):
    """为整合包构建完整的前端表格行数据结构"""
    mid = p["mid"]
    full_title = p["full_title"]
    title_cn = p["title_cn"]
    title_en = p["title_en"]
    cover_url = p["cover_url"]
    views_n = p["views_n"]
    views_d = p["views_d"]
    lat_n = p["lat_n"]
    score_n = p["score_n"]
    mold_id = p["mold_id"]
    type_name = p["type_name"]
    rv_n, rp_n = p["rv_n"], p["rp_n"]
    bv_n, bp_n = p["bv_n"], p["bp_n"]
    rec_n, fav_n, com_n = p["rec_n"], p["fav_n"], p["com_n"]
    cats = p["categories"]
    mods = p["mods"]

    # 版本信息
    v_info = version_info or {}
    latest_ver = v_info.get("latest_version", "")
    latest_date = v_info.get("latest_date", "")

    # 走势处理
    t_points = trend_points or [(time.strftime("%Y-%m-%d"), float(lat_n))]
    trend_dates = ",".join(x[0] for x in t_points)
    trend_vals = ",".join(f"{x[1]:.1f}" if x[1] != int(x[1]) else str(int(x[1])) for x in t_points)
    lat_n, max_n, avg_n, days_n, t7_n, t30_n, t60_n, tall_n = compute_trend_stats(t_points)
    score_n = 5 if lat_n > 500 else (4 if lat_n > 200 else (3 if lat_n > 50 else (2 if lat_n > 10 else 1)))

    c0 = build_c0(mid, full_title, title_cn, title_en, cover_url, mold_id, type_name, views_d, latest_ver, latest_date)
    c1 = build_c1(score_n, lat_n, max_n, avg_n, days_n, [x[1] for x in t_points])
    c2 = build_c2(t7_n, t30_n, t60_n, tall_n)
    c3 = build_c3(rv_n, rp_n, bv_n, bp_n)
    c4 = build_c4(rec_n, fav_n, com_n)

    cat_spans = "".join([f'<span class="tag-cat" data-tag="{c}"><span class="tag-filter-name">{c}</span></span>' for c in cats])
    c5 = f'<div class="tag-wrap tag-combo-container"><div class="tag-group-block"><div class="tag-group-label tag-group-label-cat">整合包分类</div><div class="tag-group tag-group-cat">{cat_spans}</div></div></div>'

    mod_spans = "".join([
        f'<span class="tag-mod" role="button" tabindex="0" title="{m["name"]}" data-mod="{m["name"]}">'
        f'<span class="tag-mod-name">{m["name"]}</span><a class="tag-mod-open" href="{m["url"]}" target="_blank">↗</a></span>'
        for m in mods[:8]
    ])
    c6 = (
        f'<div class="tag-wrap mod-container"><details class="mod-details"><summary>'
        f'<span class="mod-summary-main">包含模组 <b>{len(mods)}</b></span></summary>'
        f'<div class="mod-details-body"><div class="mod-grid">{mod_spans}</div></div></details></div>'
    )

    return {
        "mid": str(mid),
        "has_cover": bool(cover_url),
        "type_name": type_name,
        "name_order": full_title.lower(),
        "views_n": views_n,
        "score_n": score_n,
        "lat_n": lat_n,
        "max_n": max_n,
        "avg_n": avg_n,
        "days_n": days_n,
        "trend_vals": trend_vals,
        "trend_dates": trend_dates,
        "title": full_title,
        "t7_n": t7_n,
        "t30_n": t30_n,
        "t60_n": t60_n,
        "tall_n": tall_n,
        "rv_n": rv_n,
        "rp_n": rp_n,
        "bv_n": bv_n,
        "bp_n": bp_n,
        "rec_n": rec_n,
        "fav_n": fav_n,
        "com_n": com_n,
        "latest_version": latest_ver,
        "last_update_date": latest_date,
        "release_date": v_info.get("release_date", ""),
        "version_count": v_info.get("version_count", 0),
        # 只有页面成功返回才置位：用于区分"确认无日志"与"抓取失败"，
        # 供 refresh_trend_and_versions 的增量回填判定使用。
        "version_checked": bool(v_info.get("checked")),
        "tags_search": " ".join(cats),
        "cat_search": " ".join(cats),
        "pack_search": "",
        "tag_count": len(cats),
        "mods_search": " ".join([m["name"] for m in mods]),
        "mod_count": len(mods),
        "c0": c0,
        "c1": c1,
        "c2": c2,
        "c3": c3,
        "c4": c4,
        "c5": c5,
        "c6": c6
    }

def update_table_row_metrics(row, m=None, new_trend_points=None, version_info=None):
    """更新存量行的指标、走势图表与真实版本数据"""
    # 1. 基础浏览量与指数更新
    if m:
        # 0. 增量更名检测与历史别名记录
        new_title = m.get("full_title")
        if new_title and row.get("title") and new_title != row["title"]:
            old_title = row["title"]
            former = list(row.get("former_titles") or [])
            if old_title not in former:
                former.append(old_title)
            row["former_titles"] = former
            row["title"] = new_title
            row["title_cn"] = m.get("title_cn", new_title)
            row["title_en"] = m.get("title_en", "")
            row["name_order"] = (m.get("title_cn") or new_title).lower()
            c0 = row.get("c0", "")
            if c0:
                c0 = re.sub(r'(<a class="modpack-title-link"[^>]*>).*?(</a>)', r'\g<1>' + re.escape(new_title) + r'\2', c0)
                row["c0"] = c0
            print(f"  🔄 [更名捕获] #{row.get('mid')} 标题已变更: '{old_title}' -> '{new_title}' (已保留历史别名检索)")

        if m.get("views_n") is not None and m["views_n"] > 0:
            row["views_n"] = m["views_n"]
            c0 = row.get("c0", "")
            c0 = re.sub(r'<span class="modpack-views-badge"[^>]*>👁 [^<]+</span>',
                        f'<span class="modpack-views-badge" title="总浏览量">👁 {m["views_d"]}</span>', c0)
            row["c0"] = c0

        # 投票数据更新
        if m.get("rv_n", 0) > 0 or m.get("bv_n", 0) > 0:
            row["rv_n"] = m["rv_n"]
            row["rp_n"] = m["rp_n"]
            row["bv_n"] = m["bv_n"]
            row["bp_n"] = m["bp_n"]
            row["c3"] = build_c3(m["rv_n"], m["rp_n"], m["bv_n"], m["bp_n"])

        # 推荐/收藏/评论（若网页未在静态HTML中返回，安全沿用存量历史数据）
        rec_n = m["rec_n"] if m.get("rec_n", 0) > 0 else int(row.get("rec_n") or 0)
        fav_n = m["fav_n"] if m.get("fav_n", 0) > 0 else int(row.get("fav_n") or 0)
        com_n = m["com_n"] if m.get("com_n", 0) > 0 else int(row.get("com_n") or 0)
        row["rec_n"] = rec_n
        row["fav_n"] = fav_n
        row["com_n"] = com_n
        row["c4"] = build_c4(rec_n, fav_n, com_n)

    # 2. 版本日志更新
    if version_info:
        row["latest_version"] = version_info.get("latest_version", "")
        row["last_update_date"] = version_info.get("latest_date", "")
        row["release_date"] = version_info.get("release_date", "")
        row["version_count"] = version_info.get("version_count", 0)
        # 只有页面成功返回才置位。用来把"确认无日志"与"抓取失败"区分开：
        # 前者不该反复重抓，后者必须能被补回来。
        if version_info.get("checked"):
            row["version_checked"] = True
        # 更新 c0 上的版本直达链接
        mid = row.get("mid", "")
        latest_ver = row["latest_version"]
        latest_date = row["last_update_date"]
        tip = f"最新版本: {latest_ver} ({latest_date})" if latest_date else f"最新版本: {latest_ver}"
        new_badge = f'<a class="modpack-version-badge" href="https://www.mcmod.cn/modpack/version/{mid}.html" target="_blank" title="{tip}">📜 {latest_ver or "更新日志"} ↗</a>'
        c0 = row.get("c0", "")
        if "modpack-version-badge" in c0:
            c0 = re.sub(r'<a class="modpack-version-badge"[^>]*>.*?</a>', new_badge, c0)
        else:
            c0 = re.sub(r'(<div class="modpack-meta-row">.*?)(</div>)', r'\1 ' + new_badge + r'\2', c0)
        row["c0"] = c0

    # 3. 走势时间线缝合更新 (无限历史天数)
    if new_trend_points:
        m_dates, m_vals, sorted_pts = merge_trend_series(row.get("trend_dates", ""), row.get("trend_vals", ""), new_trend_points)
        if sorted_pts:
            lat_n, max_n, avg_n, days_n, t7_n, t30_n, t60_n, tall_n = compute_trend_stats(sorted_pts)
            score_n = 5 if lat_n > 500 else (4 if lat_n > 200 else (3 if lat_n > 50 else (2 if lat_n > 10 else 1)))
            row["trend_dates"] = m_dates
            row["trend_vals"] = m_vals
            row["lat_n"] = lat_n
            row["max_n"] = max_n
            row["avg_n"] = avg_n
            row["days_n"] = days_n
            row["score_n"] = score_n
            row["t7_n"] = t7_n
            row["t30_n"] = t30_n
            row["t60_n"] = t60_n
            row["tall_n"] = tall_n
            row["c1"] = build_c1(score_n, lat_n, max_n, avg_n, days_n, [x[1] for x in sorted_pts])
            row["c2"] = build_c2(t7_n, t30_n, t60_n, tall_n)

# ═══════════════════════ 数据存储与归档层 ═══════════════════════

def load_data():
    """读取本地 table_rows.js 与 app_data.js"""
    rows = []
    if os.path.exists(TABLE_ROWS_PATH):
        try:
            with open(TABLE_ROWS_PATH, "r", encoding="utf-8") as f:
                text = f.read().strip()
            prefix = "window.tableRowsData = "
            if text.startswith(prefix):
                rows = json.loads(text[len(prefix):].rstrip(";\n "))
        except Exception as e:
            print(f"  [警告] 载入 table_rows.js 异常: {e}")

    compare_data = {}
    if os.path.exists(APP_DATA_PATH):
        try:
            with open(APP_DATA_PATH, "r", encoding="utf-8") as f:
                c_text = f.read().strip()
            c_prefix = "window.compareData = "
            if c_text.startswith(c_prefix):
                compare_data = json.loads(c_text[len(c_prefix):].rstrip(";\n "))
        except Exception as e:
            print(f"  [警告] 载入 app_data.js 异常: {e}")

    return rows, compare_data

def build_raw_modpack_entry(r, app_info):
    """构造标准化的 crawler_output 原始条目"""
    mid = str(r.get("mid", ""))
    c0 = r.get("c0", "")
    cover_url = ""
    cov_m = re.search(r'data-image-url="([^"]+)"', c0) or re.search(r'src="([^"]+)"', c0)
    if cov_m:
        cover_url = cov_m.group(1)

    title = r.get("title") or app_info.get("title") or f"Modpack {mid}"
    title_cn = app_info.get("title_cn") or title
    title_en = app_info.get("title_en") or ""
    if not title_en and ' (' in title and title.endswith(')'):
        parts = title.rsplit(' (', 1)
        title_cn = parts[0].strip()
        title_en = parts[1][:-1].strip()

    mold_m = re.search(r'mold=([12])', c0)
    mold_id = mold_m.group(1) if mold_m else ("2" if r.get("type_name") == "魔改整合" else "1")

    cats = app_info.get("categories") or [c for c in (r.get("cat_search") or "").split() if c]
    tags = app_info.get("tags") or [t for t in (r.get("tags_search") or "").split() if t]
    mods = app_info.get("mods") or [m for m in (r.get("mods_search") or "").split() if m]

    return {
        "platform": "mcmod",
        "project_id": mid,
        "mid": mid,
        "url": f"https://www.mcmod.cn/modpack/{mid}.html",
        "title": title,
        "title_cn": title_cn,
        "title_en": title_en,
        "type_name": r.get("type_name") or app_info.get("type", "原生整合"),
        "mold_id": str(mold_id),
        "cover_url": cover_url,
        "views": int(r.get("views_n", 0) or 0),
        "score": r.get("score_n", 1),
        "trend_latest": int(r.get("lat_n", 0) or 0),
        "trend_days": int(r.get("days_n", 1) or 1),
        "trend_dates": r.get("trend_dates", ""),
        "trend_vals": r.get("trend_vals", ""),
        "latest_version": r.get("latest_version") or app_info.get("latest_version", ""),
        "last_update_date": r.get("last_update_date") or app_info.get("last_update_date", ""),
        "release_date": r.get("release_date") or app_info.get("release_date", ""),
        "version_count": int(r.get("version_count") or app_info.get("version_count", 0) or 0),
        "version_checked": bool(r.get("version_checked") or app_info.get("version_checked")),
        "comments": int(r.get("com_n", 0) or 0),
        "recommend": int(r.get("rec_n", 0) or 0),
        "favorite": int(r.get("fav_n", 0) or 0),
        "red_votes": int(r.get("rv_n", 0) or 0),
        "black_votes": int(r.get("bv_n", 0) or 0),
        "red_percent": int(r.get("rp_n", 50) or 50),
        "black_percent": int(r.get("bp_n", 50) or 50),
        "categories": cats,
        "tags": tags,
        "mods": mods,
        "mod_count": int(r.get("mod_count", len(mods)) or len(mods)),
        "mc_versions": app_info.get("mc_versions", [])
    }

def build_modern_mcmod_entry(r, app_info):
    """Build the structured mcmod_data.js contract from this run's rows."""
    raw = build_raw_modpack_entry(r, app_info)
    mid = int(raw.get("mid") or 0)
    trend_dates = [item.strip() for item in str(r.get("trend_dates", "")).split(",") if item.strip()]
    trend_values = [item.strip() for item in str(r.get("trend_vals", "")).split(",") if item.strip()]
    trend_points = []
    for date, value in zip(trend_dates, trend_values):
        try:
            trend_points.append({"date": date, "viewsDelta": float(value)})
        except (TypeError, ValueError):
            continue
    included_mod_names = app_info.get("includedModNames")
    if not isinstance(included_mod_names, list):
        included_mod_names = app_info.get("mods") or []
    included_mod_names = [str(name) for name in included_mod_names if name]
    claims = app_info.get("environmentClaims")
    if not isinstance(claims, list):
        has_server = bool(app_info.get("has_server"))
        claims = [
            {
                "side": "server",
                "status": "supported" if has_server else "unknown",
                "certainty": "inferred" if has_server else "unknown",
                "evidenceType": "text_rule" if has_server else "no_evidence",
                "evidenceText": "MC百科历史字段推断" if has_server else None,
                "sourceField": "has_server" if has_server else None,
                "rawValue": app_info.get("has_server") if has_server else None,
            },
            {
                "side": "client",
                "status": "unknown",
                "certainty": "unknown",
                "evidenceType": "no_evidence",
                "evidenceText": None,
                "sourceField": None,
                "rawValue": None,
            },
        ]
    mc_versions = app_info.get("mc_versions") or raw.get("mc_versions") or []
    categories = app_info.get("categories") or raw.get("categories") or []
    pack_version = raw.get("latest_version")
    pack_version = pack_version.strip() if isinstance(pack_version, str) else ""
    return {
        **({"packVersion": pack_version} if pack_version else {}),
        "mid": mid,
        "title": raw.get("title", ""),
        "chineseName": app_info.get("title_cn") or raw.get("title_cn", ""),
        "englishName": app_info.get("title_en") or raw.get("title_en", ""),
        "formerTitles": app_info.get("former_titles") or r.get("former_titles") or [],
        "url": raw.get("url", ""),
        "author": app_info.get("author") or r.get("author") or "未知",
        "typeName": raw.get("type_name", "原生整合"),
        "moldId": raw.get("mold_id", "1"),
        "coverUrl": raw.get("cover_url", ""),
        "views": raw.get("views", 0),
        "score": raw.get("score"),
        "recommendations": int(r.get("rec_n", 0) or app_info.get("recommend", 0) or 0),
        "favorites": int(r.get("fav_n", 0) or app_info.get("favorite", 0) or 0),
        "commentsCount": int(r.get("com_n", 0) or app_info.get("comments", 0) or 0),
        "votes": {
            "redVotes": int(r.get("rv_n", 0) or app_info.get("red_votes", 0) or 0),
            "blackVotes": int(r.get("bv_n", 0) or app_info.get("black_votes", 0) or 0),
            "redPercent": int(r.get("rp_n", 50) or 50),
            "blackPercent": int(r.get("bp_n", 50) or 50),
        },
        "trendStats": {
            "lat": int(r.get("lat_n", 0) or 0),
            "max": int(r.get("max_n", 0) or 0),
            "avg": float(r.get("avg_n", 0) or 0),
            "days": int(r.get("days_n", 0) or 0),
            "t7": float(r.get("t7_n", 0) or 0),
            "t30": float(r.get("t30_n", 0) or 0),
            "t60": float(r.get("t60_n", 0) or 0),
            "tall": float(r.get("tall_n", 0) or 0),
            "score": raw.get("score"),
            "history7d": [point["viewsDelta"] for point in trend_points[-7:]],
            "trendValsStr": r.get("trend_vals", ""),
            "trendDatesStr": r.get("trend_dates", ""),
        },
        "tags": app_info.get("tags") or raw.get("tags") or [],
        "categories": categories,
        "mcVersions": mc_versions,
        "loaders": app_info.get("loaders") or raw.get("loaders") or [],
        "includedModsCount": int(r.get("mod_count", len(included_mod_names)) or len(included_mod_names)),
        "modCategories": app_info.get("modCategories") or [],
        "previewMods": app_info.get("previewMods") or [],
        "includedModNames": included_mod_names,
        "modCategorySearch": ", ".join(str(item) for item in (app_info.get("mod_categories") or [])),
        "trendPoints": trend_points,
        "environmentClaims": claims,
        "has_server": bool(app_info.get("has_server")),
        "publishedAt": app_info.get("published_at") or app_info.get("release_date") or "",
        "modifiedAt": app_info.get("modified_at") or app_info.get("last_update_date") or "",
    }

def save_all_outputs(rows, compare_data):
    """保存 legacy inputs, raw archive, and the current structured sidecar."""
    # 按总浏览量倒序排序
    rows.sort(key=lambda x: int(x.get("views_n", 0) or 0), reverse=True)

    # 1. 写入 table_rows.js
    os.makedirs(os.path.dirname(TABLE_ROWS_PATH), exist_ok=True)
    with open(TABLE_ROWS_PATH, "w", encoding="utf-8") as f:
        f.write("window.tableRowsData = " + json.dumps(rows, ensure_ascii=False) + ";\n")

    # 2. 写入 app_data.js
    os.makedirs(os.path.dirname(APP_DATA_PATH), exist_ok=True)
    with open(APP_DATA_PATH, "w", encoding="utf-8") as f:
        f.write("window.compareData = " + json.dumps(compare_data, ensure_ascii=False) + ";\n")

    # 3. 构造并写入 crawler_output/mcmod_modpacks.json
    os.makedirs(RAW_OUTPUT_DIR, exist_ok=True)
    raw_list = []
    for r in rows:
        mid = str(r.get("mid", ""))
        app_info = compare_data.get(mid, {})
        raw_list.append(build_raw_modpack_entry(r, app_info))

    with open(RAW_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(raw_list, f, ensure_ascii=False, indent=2)

    modern_list = [build_modern_mcmod_entry(row, compare_data.get(str(row.get("mid", "")), {})) for row in rows]
    modern_path = os.path.join(REPO_ROOT, "converted_output", "data", "mcmod_data.js")
    with open(modern_path, "w", encoding="utf-8") as f:
        f.write("window.mcmodData = " + json.dumps(modern_list, ensure_ascii=False, separators=(",", ":")) + ";\n")

    print(f"  [落盘成功] 已同步保存:")
    print(f"    - 前端主数据: {TABLE_ROWS_PATH} ({len(rows):,} 条)")
    print(f"    - 模组对比库: {APP_DATA_PATH} ({len(compare_data):,} 条)")
    print(f"    - 标准归档库: {RAW_JSON_PATH} ({len(raw_list):,} 条)")
    print(f"    - 现代结构化数据: {modern_path} ({len(modern_list):,} 条)")

# ═══════════════════════ 采集调度引擎 ═══════════════════════

def probe_new_modpacks(rows, compare_data, max_404=8, recheck_holes=False):
    """自适应向上探测全新整合包（包含抓取详情、走势与版本日志）"""
    existing_mids = set()
    for r in rows:
        m = str(r.get("mid", ""))
        if m.isdigit():
            existing_mids.add(int(m))

    max_mid = max(existing_mids) if existing_mids else 0
    print(f"\n  [自适应探针] 本地已收录最大 ID 为: #{max_mid} (共 {len(existing_mids)} 款)")

    holes = sorted([m for m in range(1, max_mid + 1) if m not in existing_mids])
    print(f"  [墓碑黑名单] 历史跳过/删帖 ID 共 {len(holes)} 个 (1 ~ {max_mid} 区间)")

    new_discovered = 0

    if recheck_holes and holes:
        print(f"  [复查墓碑] 正在复查历史跳过的 {len(holes)} 个 ID...")
        for mid in holes:
            url = f"https://www.mcmod.cn/modpack/{mid}.html"
            html = fetch_html(url)
            if not html:
                continue
            pack_info = parse_mcmod_pack(mid, html)
            if not pack_info or not pack_info["full_title"]:
                continue
            t_pts = fetch_trend_data(mid)
            v_info = fetch_version_data(mid)
            row = build_table_row(pack_info, trend_points=t_pts, version_info=v_info)
            rows.append(row)
            compare_data[str(mid)] = {
                "mid": str(mid),
                "title": pack_info["full_title"],
                "title_cn": pack_info["title_cn"],
                "title_en": pack_info["title_en"],
                "url": f"https://www.mcmod.cn/modpack/{mid}.html",
                "type": pack_info["type_name"],
                "views": pack_info["views_n"],
                "score": pack_info["score_n"],
                "trend_latest": pack_info["lat_n"],
                "trend_days": row.get("days_n", 1),
                "latest_version": row.get("latest_version", ""),
                "last_update_date": row.get("last_update_date", ""),
                "release_date": row.get("release_date", ""),
                "version_count": row.get("version_count", 0),
                "version_checked": row.get("version_checked", False),
                "comments": pack_info["com_n"],
                "recommend": pack_info["rec_n"],
                "favorite": pack_info["fav_n"],
                "red_votes": pack_info["rv_n"],
                "black_votes": pack_info["bv_n"],
                "growth7": f"{row.get('t7_n', 0)}%",
                "growth30": f"{row.get('t30_n', 0)}%",
                "growth60": f"{row.get('t60_n', 0)}%",
                "categories": pack_info["categories"],
                "tags": [],
                "mods": [m["name"] for m in pack_info["mods"]],
                "mod_count": len(pack_info["mods"]),
                "mc_versions": pack_info["mc_versions"]
            }
            existing_mids.add(mid)
            new_discovered += 1
            print(f"  🎉 [墓碑复活] #{mid} {pack_info['full_title']} 成功补录！")
            time.sleep(0.15)

    curr_mid = max_mid + 1
    consecutive_404 = 0
    print(f"  [自适应探针] 开始从 ID #{curr_mid} 向上连续探测 (容忍阈值: 连续 {max_404} 次 404)...")

    while consecutive_404 < max_404:
        url = f"https://www.mcmod.cn/modpack/{curr_mid}.html"
        html = fetch_html(url)

        if not html:
            consecutive_404 += 1
            print(f"  [探针扫描] #{curr_mid:4d} -> 404 未发布 (连续 404: {consecutive_404}/{max_404})")
            curr_mid += 1
            time.sleep(0.12)
            continue

        pack_info = parse_mcmod_pack(curr_mid, html)
        if not pack_info or not pack_info["full_title"]:
            consecutive_404 += 1
            curr_mid += 1
            time.sleep(0.12)
            continue

        consecutive_404 = 0
        t_pts = fetch_trend_data(curr_mid)
        v_info = fetch_version_data(curr_mid)
        row = build_table_row(pack_info, trend_points=t_pts, version_info=v_info)
        rows.append(row)
        compare_data[str(curr_mid)] = {
            "mid": str(curr_mid),
            "title": pack_info["full_title"],
            "title_cn": pack_info["title_cn"],
            "title_en": pack_info["title_en"],
            "url": f"https://www.mcmod.cn/modpack/{curr_mid}.html",
            "type": pack_info["type_name"],
            "views": pack_info["views_n"],
            "score": pack_info["score_n"],
            "trend_latest": pack_info["lat_n"],
            "trend_days": row.get("days_n", 1),
            "latest_version": row.get("latest_version", ""),
            "last_update_date": row.get("last_update_date", ""),
            "release_date": row.get("release_date", ""),
            "version_count": row.get("version_count", 0),
            "version_checked": row.get("version_checked", False),
            "comments": pack_info["com_n"],
            "recommend": pack_info["rec_n"],
            "favorite": pack_info["fav_n"],
            "red_votes": pack_info["rv_n"],
            "black_votes": pack_info["bv_n"],
            "growth7": f"{row.get('t7_n', 0)}%",
            "growth30": f"{row.get('t30_n', 0)}%",
            "growth60": f"{row.get('t60_n', 0)}%",
            "categories": pack_info["categories"],
            "tags": [],
            "mods": [m["name"] for m in pack_info["mods"]],
            "mod_count": len(pack_info["mods"]),
            "mc_versions": pack_info["mc_versions"]
        }
        existing_mids.add(curr_mid)
        new_discovered += 1
        print(f"  ✨ [全新收录] #{curr_mid:4d} {pack_info['full_title'][:28]} | 走势: {len(t_pts)}天 | 版本: {v_info.get('latest_version') or '无'} | 模组: {len(pack_info['mods'])} 款！")
        curr_mid += 1
        time.sleep(0.15)

    print(f"\n  [探测收工] 连续遇到 {max_404} 次 404，安全触达当前 MC百科 最新边界 (最新有效 ID: #{max(existing_mids)})。")
    print(f"  本次探针共新增收录: {new_discovered} 款整合包！")
    return new_discovered

def refresh_metrics(rows, compare_data, concurrency=6, limit=None):
    """多线程刷新存量整合包实时基础指标（浏览量/指数/红黑票）"""
    target_rows = rows[:limit] if limit else rows
    total = len(target_rows)
    print(f"\n  [指标刷新] 启动多线程并发刷新 {total:,} 款存量包基础指标 (并发数: {concurrency})...")

    mid_to_row = {str(r.get("mid")): r for r in target_rows if r.get("mid")}

    def worker(mid):
        url = f"https://www.mcmod.cn/modpack/{mid}.html"
        html = fetch_html(url, retries=2, timeout=8)
        if not html:
            return mid, None
        return mid, parse_metrics_only(html)

    done = 0
    updated = 0
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {executor.submit(worker, mid): mid for mid in mid_to_row.keys()}
        for future in as_completed(futures):
            done += 1
            mid, metrics = future.result()
            if metrics and metrics.get("views_n") is not None:
                row = mid_to_row.get(mid)
                if row:
                    update_table_row_metrics(row, m=metrics)
                app = compare_data.get(mid)
                if app:
                    app["views"] = metrics["views_n"]
                    if metrics["score_n"] is not None:
                        app["score"] = metrics["score_n"]
                    if metrics["lat_n"] is not None:
                        app["trend_latest"] = metrics["lat_n"]
                    if metrics.get("rv_n", 0) > 0 or metrics.get("bv_n", 0) > 0:
                        app["red_votes"] = metrics["rv_n"]
                        app["black_votes"] = metrics["bv_n"]
                    if metrics.get("rec_n", 0) > 0:
                        app["recommend"] = metrics["rec_n"]
                    if metrics.get("fav_n", 0) > 0:
                        app["favorite"] = metrics["fav_n"]
                    if metrics.get("com_n", 0) > 0:
                        app["comments"] = metrics["com_n"]
                    if row.get("former_titles"):
                        app["former_titles"] = row["former_titles"]
                    if row.get("title") and row["title"] != app.get("title"):
                        app["title"] = row["title"]
                        app["title_cn"] = row.get("title_cn", row["title"])
                        app["title_en"] = row.get("title_en", "")
                updated += 1

            if done % 50 == 0 or done == total:
                pct = (done / total) * 100
                elapsed = time.time() - t0
                speed = done / elapsed if elapsed > 0 else 0
                print(f"  [刷新进度] ({pct:5.1f}%) 已处理 {done:,}/{total:,} | 成功更新 {updated:,} | 速度: {speed:.1f} 款/秒")

    print(f"  🎉 [基础指标刷新完成] 成功刷新 {updated:,}/{total:,} 款整合包基础动态数据！")
    return updated

def is_trend_stale(row, max_stale_days=5):
    """
    科学智能增量判定：按【最新走势日期】而非写死固定天数。
    - 只要该整合包的最新走势日期距今在有效天数阈值之内，说明近期已同步，跳过；
    - 针对新发布整合包（总沉淀天数 <= 14 天）：处于 1~7 天、7~14 天的初创爆发期，
      自适应启动高敏模式（阈值缩短为 min(max_stale_days, 3) 天），精准捕捉早期爆发走势；
    - 针对成熟整合包（天数 > 14 天）：采用默认 5 天的平滑增量节奏；
    - 若最新日期距今超过阈值，或根本没有走势数据，则自动触发增量拉取；
    - 哪怕是刚发布 15 天或 30 天的新包，只要近期已更新就跳过，未来随着天数增长又会自动触发更新，
      彻底实现 15天变30天、30天变45天、60天变120+天的全自动平滑生长！
    """
    trend_dates = row.get("trend_dates", "")
    if not trend_dates:
        return True
    dates = [d.strip() for d in str(trend_dates).split(",") if d.strip()]
    if not dates:
        return True

    # 新包自适应高敏判定：幼年期包（<=14天）缩短为 3 天，常规包使用 5 天（或由命令行指定）
    total_days = len(dates)
    effective_stale_days = min(max_stale_days, 3) if total_days <= 14 else max_stale_days

    last_date_str = dates[-1]
    try:
        from datetime import datetime
        last_dt = datetime.strptime(last_date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        return (today - last_dt).days >= effective_stale_days
    except Exception:
        return True

def refresh_trend_and_versions(rows, compare_data, concurrency=2, limit=None, force=False, max_stale_days=5, gentle=True, cache_size=50):
    """多线程并发抓取官方走势数据（执行无限时间线缝合）与真实版本更新日志"""
    if force:
        target_rows = rows[:limit] if limit else rows
    else:
        # 科学智能增量：按最新走势日期过滤出陈旧或未同步的整合包。
        # 此外必须补上"版本日志缺失、且从未成功抓取过"的包：走势已经刷新、
        # 但版本页那次请求失败过的条目，只看 is_trend_stale 会被永久跳过，
        # 再也补不回来（实测 mid=449 等约 174 款正是这样漏掉的）。
        # 用 version_checked 兜底：页面已确认无日志的包不会被反复重抓。
        target_rows = [
            r for r in rows
            if is_trend_stale(r, max_stale_days=max_stale_days)
            or (not str(r.get("latest_version") or "").strip()
                and not r.get("version_checked"))
        ]
        if limit:
            target_rows = target_rows[:limit]

    total = len(target_rows)
    print(f"\n  [走势与版本缝合] 启动提取 {total:,} 款待更新整合包的走势图与版本更新日志...")
    print(f"  [智能增量判定] 依据【最新走势日期】(成熟包 >{max_stale_days}天 / 幼年包 >{min(max_stale_days, 3)}天需更新) | 并发: {concurrency} | 温和慢速防封: {gentle} | 自动落盘间隔: 每 {cache_size} 条")
    stale_n = sum(1 for r in target_rows if is_trend_stale(r, max_stale_days=max_stale_days))
    print(f"  [目标构成] 走势陈旧 {stale_n:,} 款 · 仅补版本日志 {total - stale_n:,} 款")
    if total == 0:
        print("  🎉 [无需更新] 当前所有整合包走势均已处于最新扩展缝合状态！")
        return 0, 0

    mid_to_row = {str(r.get("mid")): r for r in target_rows if r.get("mid")}

    def worker(mid):
        if IS_BANNED:
            return mid, [], {}
        # 温和防封延迟：随机停顿，避免触发 Apache 频控
        sleep_range = (1.0, 2.0) if gentle else (0.1, 0.25)
        time.sleep(random.uniform(*sleep_range))
        t_pts = fetch_trend_data(mid)
        if IS_BANNED:
            return mid, t_pts, {}
        time.sleep(random.uniform(*sleep_range))
        v_info = fetch_version_data(mid)
        return mid, t_pts, v_info

    done = 0
    updated_trend = 0
    updated_ver = 0
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {executor.submit(worker, mid): mid for mid in mid_to_row.keys()}
        for future in as_completed(futures):
            if IS_BANNED:
                print("  🛑 [安全熔断] 检测到访问频率受限，提前中止后续请求并执行安全落盘。")
                break
            done += 1
            mid, t_pts, v_info = future.result()
            row = mid_to_row.get(mid)
            if row:
                update_table_row_metrics(row, new_trend_points=t_pts, version_info=v_info)
                app = compare_data.get(mid)
                if app:
                    if t_pts:
                        app["trend_latest"] = row.get("lat_n", app.get("trend_latest"))
                        app["trend_days"] = row.get("days_n", app.get("trend_days"))
                        app["score"] = row.get("score_n", app.get("score"))
                        app["growth7"] = f"{row.get('t7_n', 0)}%"
                        app["growth30"] = f"{row.get('t30_n', 0)}%"
                        app["growth60"] = f"{row.get('t60_n', 0)}%"
                    if v_info and v_info.get("latest_version"):
                        app["latest_version"] = v_info["latest_version"]
                        app["last_update_date"] = v_info["latest_date"]
                        app["release_date"] = v_info["release_date"]
                        app["version_count"] = v_info["version_count"]

            if t_pts:
                updated_trend += 1
            if v_info and v_info.get("latest_version"):
                updated_ver += 1

            if done % 20 == 0 or done == total:
                pct = (done / total) * 100
                elapsed = time.time() - t0
                speed = done / elapsed if elapsed > 0 else 0
                print(f"  [走势进度] ({pct:5.1f}%) 已完成 {done:,}/{total:,} | 成功缝合走势: {updated_trend:,} | 提取真实版本: {updated_ver:,} | 速度: {speed:.1f} 款/秒")

            # 每处理 cache_size 款自动安全落盘一次，确保即使异常中断也不丢失任何成果 (响应指令: 缓存50条)
            if done % cache_size == 0 and done < total:
                save_all_outputs(rows, compare_data)

    print(f"  🎉 [走势与版本更新完成] 成功缝合走势 {updated_trend:,} 款，获取版本日志 {updated_ver:,} 款！")
    return updated_trend, updated_ver

# ═══════════════════════ 主入口 ═══════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="MC百科 (MCMod.cn) 超级全量全自动深挖增量采集引擎 v2.1",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--mode",
        choices=["new", "trend", "metrics", "all", "sync-titles"],
        default="new",
        help=(
            "运行模式：\n"
            "  new         - 仅向上探测全新整合包 (含走势与版本日志，秒级完成，默认)\n"
            "  trend       - 并发刷新存量整合包走势（执行无限时间线缝合）与版本更新日志\n"
            "  metrics     - 多线程定向刷新存量整合包基础指标 (浏览量/指数/投票等)\n"
            "  sync-titles - 并发扫描存量整合包更名情况，更新标题并记录历史别名 (解决更名后搜不到问题)\n"
            "  all         - 串联执行：先探测新包，再全量刷新指标与缝合走势"
        )
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="限制存量处理的整合包数量 (默认全部，测试时可指定如 10)"
    )
    parser.add_argument(
        "--max-404",
        type=int,
        default=8,
        help="自适应探测新包时允许的最大连续 404 页面数，达到此阈值判定已至最新前沿并安全退出 (默认 8)"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=2,
        help="存量指标刷新时的并发线程数 (默认 2，温和防封)"
    )
    parser.add_argument(
        "--stale-days",
        type=int,
        default=5,
        help="判定成熟走势是否陈旧的天数阈值 (默认 5 天，幼年新包自适应 3 天高敏捕捉)"
    )
    parser.add_argument(
        "--cache-size",
        type=int,
        default=50,
        help="批量自动落盘缓存大小，每处理 N 款自动写入磁盘 (默认 50，响应用户指定)"
    )
    parser.add_argument(
        "--no-gentle",
        action="store_true",
        default=False,
        help="关闭拟人化温和慢速防封模式 (不推荐，可能触发频控)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="是否强制重新抓取所有整合包走势（默认智能按最新日期增量跳过近期已同步的包）"
    )
    parser.add_argument(
        "--proxy",
        type=str,
        default=None,
        help="配置网络代理服务器地址 (例如: http://127.0.0.1:7890，如不想用代理请勿传此参数)"
    )
    parser.add_argument(
        "--no-proxy",
        action="store_true",
        default=False,
        help="强制使用纯直连模式（忽略任何系统代理或环境变量，纯本土地理 IP 直连）"
    )
    parser.add_argument(
        "--recheck-holes",
        action="store_true",
        default=False,
        help="是否重新探测 1~max_mid 之间的历史缺失 ID 墓碑 (默认跳过，避免无效请求)"
    )

    args = parser.parse_args()

    # 网络连接与代理策略 (默认纯直连，用户无需懂任何代理)
    proxy_to_use = None
    if args.no_proxy:
        init_network(no_proxy=True)
    else:
        if args.proxy:
            proxy_to_use = args.proxy
        else:
            env_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or os.environ.get("all_proxy")
            if env_proxy:
                proxy_to_use = env_proxy
        if proxy_to_use:
            init_network(proxy=proxy_to_use)
        else:
            init_network(no_proxy=False)

    gentle = not args.no_gentle

    print("=" * 70)
    print("  🚀 MC百科 (MCMod.cn) 全自动增量深挖采集引擎 v2.1")
    print(f"  运行模式: [{args.mode.upper()}] | 连续404上限: {args.max_404} | 并发: {args.concurrency} | 温和模式: {gentle}")
    print(f"  增量过期阈值: {args.stale_days} 天 | 自动落盘间隔: {args.cache_size} 条 | 强制全量: {args.force}")
    if proxy_to_use:
        print(f"  代理配置: {proxy_to_use}")
    if args.limit:
        print(f"  测试限制: 仅处理前 {args.limit} 款整合包")
    print("=" * 70)

    # 1. 读取现有数据
    rows, compare_data = load_data()
    print(f"  [数据就绪] 载入 table_rows: {len(rows):,} 款 | compareData: {len(compare_data):,} 款")

    if not os.path.exists(RAW_JSON_PATH):
        print(f"  [架构对齐] 首次检测到 {RAW_JSON_PATH} 尚未生成，正在生成基线归档...")
        save_all_outputs(rows, compare_data)

    new_count = 0
    updated_metrics_count = 0
    updated_trend_count = 0
    updated_ver_count = 0

    # 2. 执行对应模式
    if args.mode in ("new", "all"):
        new_count = probe_new_modpacks(rows, compare_data, max_404=args.max_404, recheck_holes=args.recheck_holes)

    if args.mode in ("metrics", "all", "sync-titles"):
        updated_metrics_count = refresh_metrics(rows, compare_data, concurrency=args.concurrency, limit=args.limit)

    if args.mode in ("trend", "all"):
        updated_trend_count, updated_ver_count = refresh_trend_and_versions(
            rows, compare_data,
            concurrency=args.concurrency,
            limit=args.limit,
            force=args.force,
            max_stale_days=args.stale_days,
            gentle=gentle,
            cache_size=args.cache_size
        )

    # 3. 保存全量统一归档与前端主数据
    print("\n" + "-" * 70)
    save_all_outputs(rows, compare_data)
    print("-" * 70)
    print(f"  🏆 [执行完毕] 新增收录: {new_count} 款 | 基础指标刷新: {updated_metrics_count} 款 | 走势缝合: {updated_trend_count} 款 | 版本日志提取: {updated_ver_count} 款 | 当前全量: {len(rows):,} 款")
    print("=" * 70 + "\n")

    request_completed = not IS_BANNED and COLLECTION_STATS["failed"] == 0
    no_change_confirmed = request_completed and new_count == 0 and COLLECTION_STATS["not_found"] > 0
    status = "success" if new_count > 0 and request_completed else "success_no_change" if no_change_confirmed else "partial" if not request_completed and rows else "failed"
    write_collection_result(
        "mcmod",
        request_completed=request_completed,
        fetched_count=int(new_count),
        pages_completed=int(COLLECTION_STATS["successful"] + COLLECTION_STATS["not_found"]),
        failed_requests=int(COLLECTION_STATS["failed"]),
        errors=COLLECTION_STATS["errors"],
        status=status,
        no_change_confirmed=no_change_confirmed,
        details={"rowsBefore": len(rows) - int(new_count), "rowsAfter": len(rows), "notFoundProbes": int(COLLECTION_STATS["not_found"]), "mode": args.mode},
    )

if __name__ == "__main__":
    main()


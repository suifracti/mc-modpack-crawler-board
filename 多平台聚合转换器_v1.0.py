#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多平台整合包 JSONL 转 HTML 看板生成器。"""

# v10.4.2: 标签/分类列改宽并取消内部滚动；悬浮窗点 X 后冷却改为 5 秒；
#          文案补充：鼠标移出只会正常关闭，不触发冷却。
# v10.4.3: 评论悬浮窗头部改为和介绍窗一致的图标/操作区；增强 X 可见性；
#          增加跳转 MC百科原页面评论区入口。
# v10.4.4: 支持爬虫写入每条评论/楼中楼原站定位链接；评论卡片右上角增加跳转按钮。
# v10.4.5: 模组卡片主体点击筛选/再次点击取消，右上角箭头独立跳转；
#          评论仅在存在精确原站链接时显示单条跳转，并补充楼层/页内位置。
# v10.4.6: 爬虫结构化保存整合包分类/标签 URL；看板标签主体筛选、箭头跳转。
# v10.4.7: 稳定评论悬浮窗尺寸与关闭节奏；筛选区增加“排除所选”反向筛选；
#          转换器继续只读取当前新数据，不再兼容旧 JSON 结构。
# v10.4.8: 指数评分并入趋势列；趋势窗不再跟随鼠标移动；筛选选项补频次；
#          “动漫”主题改名为流光玻璃，评论窗关闭节奏改得更自然。
# v10.4.9: 趋势悬浮窗增加可进入缓冲；评论窗去掉本地条数口径，只显示官方楼层/官方评论数。
# v10.4.10: 趋势悬浮窗增加透明安全桥，便于鼠标移入；评分文案改为官方流行指数。
# v10.4.11: 趋势大窗改为默认点击打开，并增加悬浮开关；表格外层小波形支持直接读日期/指数。
# v10.4.12: 评论详情改为点击打开；评论列增加圆形详情入口；趋势/评论关闭按钮不再触发冷却；
#           顶部提示文案同步为当前点击/悬浮混合交互。
# v10.4.13: 评论列与趋势列支持再次点击原入口关闭；趋势列增加“点击看图”提示；
#           顶部说明改为覆盖当前看板主要操作。
# v10.4.14: 评论入口改为更轻的图标按钮；评论窗空白处可点击关闭；
#           删除“原站评论”等误导性回退文案，仅在有抓取楼层时显示第 X 楼。
# v10.4.15: 趋势弹窗按整合包标题识别开关，同一包趋势区域再次点击即可关闭；
#           弹窗空白处也可点击关闭。
# v10.4.16: 增加“悬浮评论窗”开关；趋势/评论均可在点击打开与悬浮打开之间切换；
#           清理爬虫旧楼层估算字段，评论楼层只保留真实抓取值。
# v10.4.17: 趋势列点击改用捕获兜底，同一包趋势区域任意位置再次点击都可关闭；
#           悬浮开关移动到对应趋势/评论区域，并统一为小圆角胶囊样式。
# v10.4.18: 修复表头悬浮开关被排序事件吞掉的问题；趋势/评论开关都内嵌到对应表头；
#           开关改为紧凑滑块样式，减少视觉占位。
# v10.4.19: 表头悬浮开关改为 class 绑定，兼容 DataTables 克隆表头；
#           模组详情展开后点击分类间隔/右侧空白可直接收起。
# v10.4.20: 表头悬浮开关改用捕获阶段拦截并手动切换，彻底避开 DataTables 表头排序。
# v10.4.21: 趋势弹窗按整行整合包 ID 开关，左右趋势格都能关闭同一弹窗；
#           介绍弹窗增加点击/悬浮模式开关；生成固定文件同时输出版本号副本。
# v10.4.22: Switches use the whole pill as the click target; trend popups close from either trend cell in the same row; default output filename carries APP_VERSION.
# v10.4.23: Move hover switches above the table; add modpack type filtering, two-line titles, comment totals, and fix 60-day trend filtering.
# v10.4.24: Merge total views into the title column, remove the standalone views column, and make the mod list grid fully adaptive for fullscreen density.
# v10.4.25: Stabilize the 7-column table after the views merge; restore readable 3-column mod grids; add title-column views sorting; refresh glass pagination.
# v10.4.26: Restyle filter/search/pagination controls; make the Flow theme neon-iridescent; add sortable mod-count column behavior.
# v10.4.27: Convert type/trend/search selectors to rounded glass Select2 controls and rebuild pagination as a theme-colored soft pill.
# v10.4.28: Add tag-count sorting, redesign collapsed mod summaries to fill the mod column, and force pagination colors to follow the active theme.
# v10.4.29: Fix tag sorting click handling, simplify tag header, fully expand collapsed mod summaries, and harden themed pagination color overrides.
# v10.5.0: Add compact category filter UI plus favorites, compare tray, and full-screen glass comparison matrix.
# v10.5.1: Move the favorite star to the upper-right of each title cell and keep the title text clear.
# v10.5.2: Render crawled cover/intro/comment images in popups and normalize image URLs for file:// dashboards.
# v10.5.3: Filter comment avatars, keep emotion images inline, enlarge image previews, and add an in-page image lightbox.
# v10.5.4: Show modpack cover thumbs in the title column, lift image previews above popups, and restore per-row mod scrolling.
# v10.5.5: Enlarge title-column cover thumbs and allow the title text to share a little of the cover area.
# v10.5.6: Make title-column covers larger, keep favorite stars above covers, and add delayed cover hover preview.
# v10.5.7: Restore a visible page-size selector; cap inline mod previews so local HTML opens smoothly on Windows.
# v10.5.8: Build each row's complete mod list only when that row is opened.
# v10.5.9: Load the full mod list directly from the summary click, including browsers that do not bubble toggle events.
# v10.5.10: Write the default dashboard only to its stable local entry; version copies go straight to local archive.
# v10.5.11: Lazily render the complete original grouped mod-card preview on row expansion.
# v10.5.12: Compact the oversized pagination controls into a quiet table footer.
# v10.5.13: Default the dashboard to 25 rows per page.
# v10.5.14: Split comments into per-pack API data, load on demand, add an
#           in-popup comment search field, and shorten cover preview delay.
# v10.5.15: Keep generated artifacts under one dashboard folder and serve table
#           rows plus detail payloads through the local API.
# v10.5.16: Fold the local API server into this converter; one command now
#           generates, opens, and serves the dashboard.
# v10.5.17: Flatten trend history into one file, simplify root folders, and
#           reuse an already-running local dashboard port.
# v10.5.18: Remove the remaining Python string-escape warning from generated JS.
# v10.5.19: Escape whitespace regexp in the generated JavaScript template.
# v10.5.20: Escape the remaining JavaScript regexp templates for clean startup.
# v10.5.21: Finish escaping ordered-list regexp literals in the HTML template.
import re
import sys
import os
import json
import html as _html
import urllib.parse
import webbrowser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from collections import Counter
from datetime import date

APP_VERSION = "v10.5.22"
DEFAULT_OUTPUT_STEM = "\u591a\u5e73\u53f0\u805a\u5408\u770b\u677f_V1.0"
GENERATED_DASHBOARD_DIR = "converted_output"
OPEN_DASHBOARD_NAME = "点击打开.html"

def default_output_file():
    return "{}_{}.html".format(DEFAULT_OUTPUT_STEM, APP_VERSION)

# ───────────────────────── 配置 ─────────────────────────

INPUT_FILE  = "多平台爬虫数据_v1.0.jsonl"

FALLBACK_INPUT_FILE = "MC百科整合包数据.json"

# The converter does not use browser cache or cookies. Browser state belongs to
# the crawler only, under ignored_local_files/browser_data.
TREND_HISTORY_FILE = "trend_history.jsonl"

MCMOD_BASE  = "https://www.mcmod.cn/modpack/"

MCMOD_CLASS_CATEGORY_NAMES = {
    "1": "科技",
    "2": "魔法",
    "3": "冒险",
    "4": "农业",
    "5": "装饰",
    "6": "安全",
    "7": "LIB",
    "8": "资源",
    "9": "世界",
    "10": "群系",
    "11": "生物",
    "12": "能源",
    "13": "存储",
    "14": "物流",
    "15": "道具",
    "16": "红石",
    "17": "食物",
    "18": "模型",
    "19": "指南",
    "20": "破坏",
    "21": "魔改",
    "22": "Meme",
    "23": "实用",
    "24": "辅助",
    "25": "中式",
    "26": "日式",
    "27": "西式",
    "28": "恐怖",
    "29": "建材",
    "30": "生存",
    "31": "指令",
    "32": "优化",
    "33": "国创",
    "34": "关卡",
    "35": "结构",
}

# ═══════════════════════ 工具函数 ═══════════════════════

def _s(val):
    if val is None:
        return ""
    return str(val).strip()

def normalize_image_url(url, base="https://www.mcmod.cn/"):
    raw = _s(url)
    if not raw:
        return ""
    if raw.startswith("//"):
        return "https:" + raw
    return urllib.parse.urljoin(base, raw)

def normalize_image_list(value):
    out = []
    seen = set()
    if not value:
        return out
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            value = parsed
        except (TypeError, ValueError):
            value = [value]
    if not isinstance(value, (list, tuple)):
        value = [value]
    for idx, item in enumerate(value):
        if isinstance(item, dict):
            url = normalize_image_url(item.get("url") or item.get("src") or item.get("data-src"))
            alt = _s(item.get("alt") or item.get("title"))
            source = _s(item.get("source"))
            kind = _s(item.get("kind"))
            section = _s(item.get("section") or item.get("heading"))
            width = _s(item.get("width"))
            height = _s(item.get("height"))
        else:
            url = normalize_image_url(item)
            alt = ""
            source = ""
            kind = ""
            section = ""
            width = ""
            height = ""
        if not url or url in seen:
            continue
        if "loading" in url.lower() or "loadfail" in url.lower():
            continue
        seen.add(url)
        out.append({
            "url": url,
            "src": url,
            "alt": alt,
            "source": source,
            "kind": kind,
            "section": section,
            "width": width,
            "height": height,
            "index": idx + 1,
        })
    return out

def esc(text):
    return _html.escape(str(text), quote=False)

def esc_attr(text):
    return _html.escape(str(text), quote=True)

def fmt_order(v):
    if isinstance(v, (int, float)):
        if v == int(v):
            return str(int(v))
        return "{:.4g}".format(v)
    return str(v)

def today_str():
    d = date.today()
    return "{}.{}.{}".format(d.year, d.month, d.day)

def fmt_views(count):
    try:
        n = int(count)
    except (ValueError, TypeError):
        return str(count)
    if n >= 10000:
        s = "{:.2f}".format(n / 10000.0).rstrip("0").rstrip(".")
        return s + "万"
    return str(n)

# ═══════════════════════ 解析函数 ═══════════════════════

def parse_tags(val):
    raw = _s(val)
    if not raw:
        return []
    if "<span" in raw.lower():
        tags = re.findall(r">([^<]+)<", raw)
        tags = [t.strip() for t in tags if t.strip()]
        if tags:
            return tags
    m = re.search(r'data-search="([^"]*)"', raw)
    if m:
        raw = m.group(1)
    if any(c in raw for c in [",", "，", "、", ";", "；", "|", "/"]):
        parts = re.split(r"[,，、;；|/]", raw)
        return [p.strip() for p in parts if p.strip()]
    parts = raw.split()
    if parts:
        return parts
    return [raw] if raw else []

def parse_tag_details(val, fallback_names=None):
    fallback_names = fallback_names or []
    raw_items = val
    if isinstance(val, str):
        if not val.strip():
            raw_items = []
        else:
            try:
                raw_items = json.loads(val)
            except Exception:
                raw_items = []
    if not isinstance(raw_items, (list, tuple)):
        raw_items = []
    details = []
    seen = set()
    for item in raw_items:
        if isinstance(item, dict):
            name = _s(item.get("name") or item.get("title") or item.get("标签") or item.get("分类"))
            url = _s(item.get("url") or item.get("href") or item.get("link") or item.get("链接"))
            tip = _s(item.get("title") or item.get("tooltip") or item.get("desc") or item.get("说明"))
            color = _s(item.get("color") or item.get("style"))
        else:
            name = _s(item)
            url = tip = color = ""
        if not name or name in seen:
            continue
        seen.add(name)
        details.append({"name": name, "url": url, "title": tip, "color": color})
    for name in fallback_names:
        if name and name not in seen:
            seen.add(name)
            details.append({"name": name, "url": "", "title": "", "color": ""})
    return details

def parse_mods(val):
    if not val:
        return []
    raw_items = val
    if isinstance(val, str):
        try:
            raw_items = json.loads(val)
        except Exception:
            names = parse_tags(val)
            return [{"name": n, "title": n, "url": "", "class_id": "", "version": ""} for n in names]
    if not isinstance(raw_items, (list, tuple)):
        return []
    mods = []
    seen = set()
    for item in raw_items:
        if isinstance(item, dict):
            name = _s(item.get("name") or item.get("名称") or item.get("title") or item.get("标题"))
            title = _s(item.get("title") or item.get("标题") or name)
            url = _s(item.get("url") or item.get("链接"))
            class_id = _s(item.get("class_id") or item.get("id") or item.get("模组ID"))
            version = _s(item.get("version") or item.get("版本"))
            category_id = _s(item.get("category_id") or item.get("分类ID"))
            category_name = _s(item.get("category_name") or item.get("分类"))
            category_url = _s(item.get("category_url") or item.get("分类链接"))
            group_name = _s(item.get("group_name") or item.get("分类组"))
        else:
            name = _s(item)
            title = name
            url = ""
            class_id = ""
            version = ""
            category_id = ""
            category_name = ""
            category_url = ""
            group_name = ""
        if not name and not title:
            continue
        if not url and class_id:
            url = "https://www.mcmod.cn/class/{}.html".format(class_id)
        if not category_name and category_id:
            category_name = MCMOD_CLASS_CATEGORY_NAMES.get(category_id, "分类 {}".format(category_id))
        if not category_url and category_id:
            category_url = "https://www.mcmod.cn/class/category/{}-1.html".format(category_id)
        key = url or class_id or name or title
        if key in seen:
            continue
        seen.add(key)
        mods.append({
            "name": name or title,
            "title": title or name,
            "url": url,
            "class_id": class_id,
            "version": version,
            "category_id": category_id,
            "category_name": category_name,
            "category_url": category_url,
            "group_name": group_name,
        })
    return mods

def parse_views(val):
    raw = _s(val)
    if not raw:
        return "", 0
    m = re.match(r"^([\d.]+)\s*万$", raw)
    if m:
        num = float(m.group(1))
        return raw, int(num * 10000)
    if "万" in raw:
        num_str = raw.replace("万", "").replace(",", "").strip()
        try:
            num = float(num_str)
            return raw, int(num * 10000)
        except ValueError:
            pass
    clean = raw.replace(",", "").replace("，", "").strip()
    try:
        num = float(clean)
        return raw, int(num)
    except ValueError:
        return raw, 0

def parse_views_count(val):
    raw = _s(val)
    if not raw:
        return "", 0
    if "万" in raw:
        try:
            num = float(raw.replace("万", "").replace(",", "").strip())
            return int(num * 10000), int(num * 10000)
        except ValueError:
            pass
    clean = raw.replace(",", "").replace("，", "").strip()
    try:
        num = float(clean)
        return int(num), int(num)
    except ValueError:
        return raw, 0

def parse_number(val):
    raw = _s(val)
    if not raw:
        return "", 0
    if "<" in raw:
        m = re.search(r'data-order="([^"]*)"', raw)
        display = re.sub(r"<[^>]+>", "", raw).strip()
        if m:
            try:
                return display, float(m.group(1))
            except ValueError:
                pass
        try:
            return display, float(display)
        except ValueError:
            return display, 0
    clean = raw.replace(",", "").replace("，", "").strip()
    try:
        return raw, float(clean)
    except ValueError:
        return raw, 0

def parse_pct(val):
    raw = _s(val)
    if not raw:
        return "", 0
    clean = raw.replace("%", "").replace("％", "").strip()
    try:
        return raw, float(clean)
    except ValueError:
        return raw, 0

def format_pct_display(val_str, val_num):
    if not val_str or val_str == "—":
        return "—"
    if "%" in str(val_str):
        return str(val_str)
    try:
        if val_num is not None:
            return "{:+.0f}%".format(val_num) if val_num != 0 else "0%"
    except (TypeError, ValueError):
        pass
    return str(val_str)

def parse_trend_json(val):
    raw = _s(val)
    if not raw:
        return []
    raw = raw.strip()
    try:
        arr = json.loads(raw)
    except (ValueError, TypeError):
        return []
    out = []
    if isinstance(arr, list):
        for it in arr:
            if isinstance(it, dict):
                d_v = it.get("日期") or it.get("date") or ""
                i_v = it.get("指数") if "指数" in it else it.get("index", 0)
                try:
                    i_v = float(i_v)
                except (ValueError, TypeError):
                    i_v = 0
                out.append((str(d_v), i_v))
    return out

def clean_intro_text(text):
    raw = _s(text).replace("\r\n", "\n").replace("\r", "\n")
    if not raw:
        return ""
    lines = []
    for line in raw.split("\n"):
        t = re.sub(r"\s+", " ", line.replace("\u00a0", " ")).strip()
        if t:
            lines.append(t)
    if not lines:
        return ""
    def is_toc(line):
        return line.startswith("目录:") or line.startswith("目录：") or line == "目录"
    def is_intro_heading(line):
        return re.match(r"^(?:\d+(?:\.\d+)*\s*)?简介[:：]?$", line) is not None
    heading_words = (
        "说明", "一些说明及建议", "配置需求", "DLC管理器相关", "特别鸣谢",
        "整合特征介绍", "性能优化", "功能辅助", "兼容版本", "整合内容摘要", "常见问题",
        "先来说点啥吧", "一些游戏内图片",
    )
    def is_heading(line):
        if is_intro_heading(line):
            return True
        if re.match(r"^\d+(?:\.\d+)*\s+\S{1,30}$", line):
            return True
        return any(line == w or line == w + "：" or line == w + ":" for w in heading_words)
    seen = set()
    compact = []
    for line in lines:
        key = re.sub(r"\s+", "", line)
        if not key or is_toc(line) or key in seen:
            continue
        seen.add(key)
        compact.append(line)
    start = -1
    for i, line in enumerate(compact):
        if is_intro_heading(line):
            start = i + 1
            break
    if start >= 0:
        picked = compact[start:]
    else:
        picked = compact
    noise_re = re.compile(r"^(过于丰富的|明确的阶段引导|数量庞大的|可制作的|丰富的BOSS指引)[:：]?$")
    cleaned = []
    max_intro_chars = 30000
    for line in picked:
        if is_toc(line) or noise_re.match(line):
            continue
        if len("\n".join(cleaned)) + len(line) > max_intro_chars:
            break
        cleaned.append(line)
    return "\n\n".join(cleaned).strip() or raw

def compute_growth_pct(trend, days):
    if not trend or len(trend) < 2:
        return "—", None
    latest = trend[-1][1]
    if len(trend) >= days + 1:
        base = trend[-(days + 1)][1]
    else:
        base = trend[0][1]
    if base == 0:
        if latest == 0:
            return "0%", 0.0
        return "—", None
    pct = (latest - base) / base * 100
    return "{:+.0f}%".format(round(pct)), round(pct, 2)

def compute_total_growth_pct(trend):
    if not trend or len(trend) < 2:
        return "—", None
    latest = trend[-1][1]
    base = trend[0][1]
    if base == 0:
        if latest == 0:
            return "0%", 0.0
        return "—", None
    pct = (latest - base) / base * 100
    return "{:+.0f}%".format(round(pct)), round(pct, 2)

def normalize_trend_points(points):
    by_date = {}
    for item in points or []:
        if isinstance(item, dict):
            day = _s(item.get("date") or item.get("日期") or item.get("captured_at") or item.get("抓取日期"))
            val = item.get("index") if "index" in item else item.get("指数")
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            day, val = item[0], item[1]
        else:
            continue
        day = _s(day)[:10]
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", day):
            continue
        try:
            val = float(val)
        except (TypeError, ValueError):
            continue
        by_date[day] = val
    return sorted(by_date.items(), key=lambda x: x[0])

def load_local_trend_history(history_file):
    """Load the compact single-file trend store once, indexed by platform/id."""
    history = {}
    if not history_file or not os.path.exists(history_file):
        return history
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                key = (str(obj.get("platform") or ""), str(obj.get("stable_id") or ""))
                if key[0] and key[1]:
                    history.setdefault(key, []).append(obj)
    except OSError:
        return {}
    return {key: normalize_trend_points(points) for key, points in history.items()}

def apply_local_trend_history(data, history_file=TREND_HISTORY_FILE):
    history = load_local_trend_history(history_file)
    applied = 0
    for d in data:
        mid = _extract_mid(d.get("url", ""))
        if not mid:
            continue
        local_trend = history.get(("mcmod", mid), [])
        if len(local_trend) < 2:
            continue
        existing = normalize_trend_points(d.get("trend_arr") or [])
        merged = normalize_trend_points(existing + local_trend)
        if len(merged) < 2:
            continue
        d["trend_arr"] = merged
        latest = merged[-1][1]
        vals = [x[1] for x in merged]
        d["lat_n"] = latest
        d["lat_d"] = str(int(latest)) if latest == int(latest) else "{:.2f}".format(latest).rstrip("0").rstrip(".")
        d["max_n"] = max(vals)
        d["max_d"] = str(int(d["max_n"])) if d["max_n"] == int(d["max_n"]) else "{:.2f}".format(d["max_n"]).rstrip("0").rstrip(".")
        avg = sum(vals) / len(vals)
        d["avg_n"] = round(avg, 2)
        d["avg_d"] = str(int(round(avg)))
        d["tc_n"] = len(merged)
        d["tc_d"] = str(len(merged))
        d["t7_d"], d["t7_n"] = compute_growth_pct(merged, 7)
        d["t30_d"], d["t30_n"] = compute_growth_pct(merged, 30)
        d["t60_d"], d["t60_n"] = compute_growth_pct(merged, 60)
        d["tall_d"], d["tall_n"] = compute_total_growth_pct(merged)
        applied += 1
    return applied

def parse_title_and_url(title_val, id_url_val=None):
    raw = _s(title_val).replace('\n', ' ')
    if not raw:
        return "", "#"
    if "<a" in raw.lower():
        href_m = re.search(r'href="([^"]+)"', raw)
        text_m = re.search(r'>([^<]*)</a>', raw)
        href = href_m.group(1).strip() if href_m else "#"
        text = text_m.group(1).strip() if text_m else re.sub(r"<[^>]+>", "", raw).strip()
        return text, href
    if id_url_val is not None:
        id_str = _s(id_url_val)
        if id_str:
            if id_str.isdigit():
                return raw, "{}{}.html".format(MCMOD_BASE, id_str)
            if id_str.startswith("http"):
                return raw, id_str
            m = re.search(r"/(\d+)\.html", id_str)
            if m:
                return raw, "{}{}.html".format(MCMOD_BASE, m.group(1))
    m = re.search(r"mcmod\.cn/modpack/(\d+)", raw)
    if m:
        title_text = re.sub(r"<[^>]+>", "", raw).strip()
        return title_text, "{}{}.html".format(MCMOD_BASE, m.group(1))
    return raw, "#"

# ═══════════════════════ JSON 读取 ═══════════════════════

def read_json(path):
    rows = []
    meta = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict) and item.get("source") == "mcmod":
                rows.append(item.get("normalized") or item.get("data") or item.get("raw") or {})
    meta = {"type": "multi-platform-jsonl", "version": "v1.0"}
    return rows, meta

def first_value(row, *keys, default=""):
    for key in keys:
        if isinstance(row, dict) and key in row and row.get(key) not in (None, ""):
            return row.get(key)
    return default

def comments_to_json_text(val):
    if val in (None, ""):
        return ""
    if isinstance(val, str):
        return val
    try:
        return json.dumps(val, ensure_ascii=False)
    except TypeError:
        return ""

def data_quality(d):
    desc = _s(d.get("desc"))
    lines = [x.strip() for x in desc.splitlines() if x.strip()]
    numeric_lines = sum(1 for x in lines if re.match(r"^\d+(?:\.\d+)*$", x))
    chinese_sentence = 1 if re.search(r"[\u4e00-\u9fff]{8,}", desc) else 0
    score = 0
    score += chinese_sentence * 100
    score += min(len(desc), 500) / 10
    score -= numeric_lines * 20
    if float(d.get("score_n") or 0) > 0:
        score += 40
    score += min(int(d.get("tc_n") or 0), 60)
    score += min(len(d.get("pack") or []), 12) * 5
    score += min(len(d.get("cat") or []), 8) * 2
    score += int(float(d.get("com_n") or 0))
    if d.get("comments_raw"):
        score += 30
    return score

def dedupe_data(data):
    picked = {}
    order = []
    for d in data:
        key = d.get("url") or d.get("title")
        if not key:
            order.append(key)

def parse_title_and_url(title_val, id_url_val=None):
    raw = _s(title_val).replace('\n', ' ')
    if not raw:
        return "", "#"
    if "<a" in raw.lower():
        href_m = re.search(r'href="([^"]+)"', raw)
        text_m = re.search(r'>([^<]*)</a>', raw)
        href = href_m.group(1).strip() if href_m else "#"
        text = text_m.group(1).strip() if text_m else re.sub(r"<[^>]+>", "", raw).strip()
        return text, href
    if id_url_val is not None:
        id_str = _s(id_url_val)
        if id_str:
            if id_str.isdigit():
                return raw, "{}{}.html".format(MCMOD_BASE, id_str)
            if id_str.startswith("http"):
                return raw, id_url_val
            m = re.search(r"/(\d+)\.html", id_str)
            if m:
                return raw, "{}{}.html".format(MCMOD_BASE, m.group(1))
    m = re.search(r"mcmod\.cn/modpack/(\d+)", raw)
    if m:
        title_text = re.sub(r"<[^>]+>", "", raw).strip()
        return title_text, "{}{}.html".format(MCMOD_BASE, m.group(1))
    return raw, "#"

# ═══════════════════════ JSON 读取 ═══════════════════════

def read_json(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict) and item.get("source") == "mcmod":
                rows.append(item.get("normalized") or item.get("data") or item.get("raw") or {})
    meta = {"type": "multi-platform-jsonl", "version": "v1.0"}
    return rows, meta

def first_value(row, *keys, default=""):
    for key in keys:
        if isinstance(row, dict) and key in row and row.get(key) not in (None, ""):
            return row.get(key)
    return default

def comments_to_json_text(val):
    if val in (None, ""):
        return ""
    if isinstance(val, str):
        return val
    try:
        return json.dumps(val, ensure_ascii=False)
    except TypeError:
        return ""

def data_quality(d):
    desc = _s(d.get("desc"))
    lines = [x.strip() for x in desc.splitlines() if x.strip()]
    numeric_lines = sum(1 for x in lines if re.match(r"^\d+(?:\.\d+)*$", x))
    chinese_sentence = 1 if re.search(r"[\u4e00-\u9fff]{8,}", desc) else 0
    score = 0
    score += chinese_sentence * 100
    score += min(len(desc), 500) / 10
    score -= numeric_lines * 20
    score += int(float(d.get("com_n") or 0))
    if d.get("comments_raw"):
        score += 30
    return score

def dedupe_data(data):
    picked = {}
    order = []
    for d in data:
        key = d.get("url") or d.get("title")
        if not key:
            order.append(key)
            continue
        if key not in picked:
            picked[key] = d
            order.append(key)
            continue
        old = picked[key]
        if data_quality(d) > data_quality(old):
            picked[key] = d
    return [picked[k] for k in order if k in picked]

def normalize_json_row(row):
    if not isinstance(row, dict):
        return None
    if "basic" in row and isinstance(row.get("basic"), dict):
        basic = dict(row.get("basic") or {})
        merged = dict(basic)
        merged["链接"] = row.get("url") or basic.get("链接", "")
        merged["整合包介绍"] = row.get("intro") or basic.get("整合包介绍", "")
        merged["评论总数"] = row.get("comment_total", basic.get("评论总数", 0))
        merged["评论详情"] = row.get("comments", basic.get("评论详情", []))
        merged["包含模组"] = row.get("mods") or basic.get("包含模组", [])
        merged["模组数量"] = row.get("mod_count") or basic.get("模组数量", 0)
        merged["intro_images"] = row.get("intro_images") or basic.get("intro_images") or []
        merged["comment_images"] = row.get("comment_images") or basic.get("comment_images") or []
        merged["cover_image"] = row.get("cover_image") or basic.get("cover_image") or ""
        if isinstance(row.get("trend"), dict):
            merged.update(row["trend"])
        row = merged
    return row

def process_data(raw_rows):
    data = []
    for row in raw_rows:
        row = normalize_json_row(row)
        if not row:
            continue
        if all(_s(v) == "" for v in row.values()):
            continue
        title, url = parse_title_and_url(first_value(row, "标题", "名称", "整合包名"), first_value(row, "链接", "url", "地址"))
        vc_d, vc_n = parse_views_count(first_value(row, "总浏览量"))
        if vc_n == 0:
            v_d, v_n = parse_views(first_value(row, "总浏览"))
            views_d = v_d
            views_n = v_n
        else:
            views_d = fmt_views(vc_n)
            views_n = vc_n
        comment_display = first_value(row, "评论总数", "评论数", "评论")
        score_d, score_n = parse_number(first_value(row, "指数评分", "评分"))
        rec_d, rec_n = parse_number(first_value(row, "推荐数", "推荐"))
        fav_d, fav_n = parse_number(first_value(row, "收藏数", "收藏"))
        com_d, com_n = parse_number(comment_display)
        max_d, max_n = parse_number(first_value(row, "走势最高指数", "最高指数", "最高"))
        avg_d, avg_n = parse_number(first_value(row, "走势平均指数", "平均指数", "平均"))
        lat_d, lat_n = parse_number(first_value(row, "走势最新指数", "最新指数", "最新", "昨日指数"))
        cat_tags = parse_tags(first_value(row, "分类标签", "分类"))
        pack_tags = parse_tags(first_value(row, "整合包标签", "标签"))
        cat_tag_details = parse_tag_details(first_value(row, "category_tag_details", "分类标签详情", "分类详情"), cat_tags)
        pack_tag_details = parse_tag_details(first_value(row, "pack_tag_details", "整合包标签详情", "标签详情"), pack_tags)
        modpack_type = _s(first_value(row, "modpack_type", "整合包类型", "类型")).strip() or "未标明"
        modpack_type_url = _s(first_value(row, "modpack_type_url", "整合包类型链接", "类型链接")).strip()
        mods = parse_mods(first_value(row, "包含模组", "mods", "模组"))
        mod_names = [m.get("name", "") for m in mods if m.get("name")]
        mod_categories = []
        seen_mod_categories = set()
        for m in mods:
            cname = m.get("category_name") or ""
            cid = m.get("category_id") or ""
            label = cname or ("分类 {}".format(cid) if cid else "")
            if label and label not in seen_mod_categories:
                seen_mod_categories.add(label)
                mod_categories.append(label)
        rv_d, rv_n = parse_number(first_value(row, "红票数"))
        rp_d, rp_n = parse_pct(first_value(row, "红票%"))
        bp_d_v, bp_n_v = parse_number(first_value(row, "黑票数"))
        bp_d, bp_n = parse_pct(first_value(row, "黑票%"))
        trend_data = first_value(row, "指数走势数据", "走势数据")
        if isinstance(trend_data, (list, tuple)):
            trend_data = json.dumps(trend_data, ensure_ascii=False)
        tc_d, tc_n = parse_number(first_value(row, "走势数据点"))
        trend_arr = parse_trend_json(trend_data)
        if tc_n == 0 and trend_arr:
            tc_d, tc_n = str(len(trend_arr)), len(trend_arr)
        t7_d, t7_n = parse_number(first_value(row, "走势涨幅_7天", "涨幅_7天", "涨幅7"))
        if t7_n == 0 and trend_arr:
            t7_d, t7_n = compute_growth_pct(trend_arr, 7)
        else:
            t7_d = format_pct_display(t7_d, t7_n)
        t30_d, t30_n = parse_number(first_value(row, "走势涨幅_30天", "涨幅_30天", "涨幅30"))
        if t30_n == 0 and trend_arr:
            t30_d, t30_n = compute_growth_pct(trend_arr, 30)
        else:
            t30_d = format_pct_display(t30_d, t30_n)
        t60_d, t60_n = parse_number(first_value(row, "走势涨幅_60天", "涨幅_60天", "涨幅60"))
        if t60_n == 0 and trend_arr:
            t60_d, t60_n = compute_growth_pct(trend_arr, 60)
        else:
            t60_d = format_pct_display(t60_d, t60_n)
        tall_d, tall_n = compute_total_growth_pct(trend_arr)
        desc_text = clean_intro_text(first_value(row, "整合包介绍", "介绍"))
        intro_images = normalize_image_list(first_value(row, "intro_images"))
        cover_image = normalize_image_url(first_value(row, "cover_image"))
        if cover_image:
            intro_images = normalize_image_list([{"url": cover_image, "alt": title, "source": "cover"}] + intro_images)
        comment_images = normalize_image_list(first_value(row, "comment_images"))
        comments_raw = comments_to_json_text(first_value(row, "评论详情", "comments"))
        data.append({
            "title": title, "url": url,
            "desc": desc_text, "comments_raw": comments_raw, "trend_arr": trend_arr,
            "intro_images": intro_images, "comment_images": comment_images, "cover_image": cover_image,
            "comment_total": _s(first_value(row, "评论总数", "评论数")),
            "score_d": score_d, "score_n": score_n,
            "views_d": views_d, "views_n": views_n,
            "rec_d": rec_d, "rec_n": rec_n,
            "fav_d": fav_d, "fav_n": fav_n,
            "com_d": com_d, "com_n": com_n,
            "max_d": max_d, "max_n": max_n,
            "avg_d": avg_d, "avg_n": avg_n,
            "lat_d": lat_d, "lat_n": lat_n,
            "cat": cat_tags, "pack": pack_tags,
            "cat_details": cat_tag_details, "pack_details": pack_tag_details,
            "modpack_type": modpack_type, "modpack_type_url": modpack_type_url,
            "mods": mods, "mod_names": mod_names, "mod_categories": mod_categories,
            "rv_d": rv_d, "rv_n": rv_n,
            "rp_d": rp_d, "rp_n": rp_n,
            "bp_d": bp_d, "bp_n": bp_n,
            "bpv_d": bp_d_v, "bpv_n": bp_n_v,
            "tc_d": tc_d, "tc_n": tc_n,
            "t7_d": t7_d, "t7_n": t7_n if t7_n is not None else 0,
            "t30_d": t30_d, "t30_n": t30_n if t30_n is not None else 0,
            "t60_d": t60_d, "t60_n": t60_n if t60_n is not None else 0,
            "tall_d": tall_d, "tall_n": tall_n if tall_n is not None else 0,
        })
    return dedupe_data(data)

# ═══════════════════════ 筛选选项 ═══════════════════════

def build_category_options(data):
    c = Counter()
    for d in data:
        c.update(d["cat"])
    return sorted(c.items(), key=lambda x: (-x[1], x[0]))

def build_packtag_options(data):
    c = Counter()
    for d in data:
        c.update(d["pack"])
    return sorted(c.items(), key=lambda x: (-x[1], x[0]))

def build_modpack_type_options(data):
    c = Counter()
    for d in data:
        c.update([d.get("modpack_type") or "未标明"])
    return sorted(c.items(), key=lambda x: (x[0] == "未标明", -x[1], x[0]))

def build_mod_options(data):
    c = Counter()
    for d in data:
        c.update(d.get("mod_names", []))
    return sorted(c.items(), key=lambda x: (-x[1], x[0]))

def build_mod_category_options(data):
    c = Counter()
    for d in data:
        c.update(d.get("mod_categories", []))
    return sorted(c.items(), key=lambda x: (-x[1], x[0]))

def build_trend_filter_options(data):
    specs = [
        ("7_in", "7天内（刚出新包）", lambda n: n <= 7),
        ("7-14", "7-14天（两周内成长包）", lambda n: 8 <= n <= 14),
        ("14-30", "14-30天（半月到满月稳定包）", lambda n: 15 <= n <= 30),
        ("30_in", "30天内（大集合）", lambda n: n <= 30),
        ("30-59", "30-59天（成长中期包）", lambda n: 31 <= n <= 59),
        ("60", "至少60天（历史老包）", lambda n: n >= 60),
    ]
    out = []
    for value, label, pred in specs:
        count = sum(1 for d in data if pred(int(d.get("tc_n") or 0)))
        out.append((value, label, count))
    return out

# ═══════════════════════ 美化版行生成 ═══════════════════════

def _growth_class(num):
    if num is None or num == 0:
        return "td-flat"
    return "td-up" if num > 0 else "td-down"

def gen_sparkline_svg_path(trend_arr):
    if not trend_arr or len(trend_arr) < 2:
        return "M 0 12 L 100 12", "M 0 12 L 100 12 L 100 24 L 0 24 Z"
    vals = [it[1] for it in trend_arr]
    min_v = min(vals)
    max_v = max(vals)
    diff = max_v - min_v
    if diff == 0:
        diff = 1
    points = []
    n = len(vals)
    for i, val in enumerate(vals):
        x = (i / (n - 1)) * 100
        y = 22 - ((val - min_v) / diff) * 20
        points.append((x, y))
    
    sparkline_path = "M " + " L ".join("{:.1f} {:.1f}".format(x, y) for x, y in points)
    sparkline_closed = sparkline_path + " L {:.1f} 24 L {:.1f} 24 Z".format(points[-1][0], points[0][0])
    return sparkline_path, sparkline_closed

def _extract_mid(url):
    """从 url https://www.mcmod.cn/modpack/1159.html 提取 ID 1159"""
    m = re.search(r'/modpack/(\d+)', url or '')
    return m.group(1) if m else ''

def split_modpack_title(title):
    title = _s(title).strip()
    if not title:
        return "", ""
    m = re.match(r'^(.*?)\s*[\(（]([^()（）]{2,120})[\)）]\s*$', title)
    if m:
        cn = re.sub(r'\s+', ' ', m.group(1)).strip()
        en = re.sub(r'\s+', ' ', m.group(2)).strip()
        return cn or title, en
    return title, ""

def gen_row_pretty(d, idx=0):
    mid = _extract_mid(d.get("url", ""))
    title_cn, title_en = split_modpack_title(d.get("title", ""))
    title_en_html = esc(title_en) if title_en else "&nbsp;"
    cover_image = normalize_image_url(d.get("cover_image") or "")
    cover_html = ""
    title_extra_class = ""
    if cover_image:
        title_extra_class = " has-cover"
        cover_html = (
            '<button type="button" class="modpack-cover-thumb image-thumb" '
            'data-image-url="{cover}" title="{title} 封面（悬停 1 秒放大）" aria-label="查看整合包封面">'
            '<img src="{cover}" alt="{title} 封面" loading="lazy">'
            '</button>'
        ).format(cover=esc_attr(cover_image), title=esc_attr(title_cn or d.get("title", "")))
    type_name = d.get("modpack_type") or "未标明"
    type_url = d.get("modpack_type_url") or ""
    if type_url:
        type_badge = '<a class="modpack-type-badge" href="{}" target="_blank" title="打开 MC百科类型页">{}</a>'.format(esc_attr(type_url), esc(type_name))
    else:
        type_badge = '<span class="modpack-type-badge">{}</span>'.format(esc(type_name))
    views_badge = '<span class="modpack-views-badge" title="总浏览量">👁 {}</span>'.format(esc(d["views_d"]))
    L = []
    L.append('            <tr data-row="{}" data-mid="{}">'.format(idx, esc_attr(mid)))
    # 标题（链接，hover 触发预览卡片）
    L.append(
        '                <td class="td-title{title_extra_class}" data-type-search="{type_name}" data-name="{name_order}" data-order="{name_order}" data-views="{views_n}">'
        '<button type="button" class="fav-star" data-mid="{mid}" title="收藏用于对比" aria-label="收藏用于对比">★</button>'
        '{cover_html}'
        '<a href="{url}" target="_blank" class="modpack-link" data-url="{url}" data-mid="{mid}" data-full-title="{full_title}">'
        '<span class="modpack-title-cn">{title_cn}</span><span class="modpack-title-en">{title_en}</span></a>'
        '<div class="modpack-meta-row">{type_badge}{views_badge}</div></td>'.format(
            url=esc_attr(d["url"]), mid=mid, full_title=esc_attr(d["title"]),
            title_extra_class=title_extra_class, cover_html=cover_html,
            title_cn=esc(title_cn), title_en=title_en_html,
            name_order=esc_attr((title_cn or d.get("title", "")).lower()),
            views_n=int(d.get("views_n") or 0),
            type_name=esc_attr(type_name), type_badge=type_badge, views_badge=views_badge)
    )
    # 总浏览量

    # trend helper for tooltips
    trend_vals_str = ""
    trend_dates_str = ""
    if d.get("trend_arr"):
        trend_vals_str = ",".join(str(it[1]) for it in d["trend_arr"])
        trend_dates_str = ",".join(it[0] for it in d["trend_arr"])
    trend_data_attrs = 'data-trend="{}" data-dates="{}" data-title="{}"'.format(
        esc_attr(trend_vals_str), esc_attr(trend_dates_str), esc_attr(d["title"])
    )

    # Column 3: Index Trend
    sparkline_path, sparkline_closed = gen_sparkline_svg_path(d["trend_arr"])
    col3_html = (
        '                <td class="td-trend" data-score="{score_n}" data-lat="{lat_n}" data-max="{max_n}" data-avg="{avg_n}" data-days="{days_n}" data-order="{score_n}" {trend_data_attrs}>'
        '<div class="trend-consolidated-cell">'
        '<div class="trend-score-badge" title="官方流行指数评分"><span>流行</span><b>{score_d}</b></div>'
        '<div class="trend-main-row">'
        '<svg class="sparkline-svg" viewBox="0 0 100 24" width="118" height="34" style="opacity: 0.95;">'
        '<path d="{sparkline_closed}" fill="rgba(var(--primary-rgb), 0.1)"></path>'
        '<path d="{sparkline_path}" fill="none" stroke="var(--primary)" stroke-width="2" stroke-linecap="round"></path>'
        '</svg>'
        '<span class="trend-val-lat" title="最新指数" style="font-weight: 700; color: var(--primary-light);">最新: {lat_d}</span>'
        '<span class="trend-open-hint">点击看图</span>'
        '</div>'
        '<div class="trend-meta-row">'
        '<span class="trend-val-max" title="最高指数">高: {max_d}</span>'
        '<span class="trend-val-avg" title="平均指数">平: {avg_d}</span>'
        '<span class="trend-val-days" title="走势天数">{days_d}天</span>'
        '</div>'
        '</div></td>'
    ).format(
        score_n=fmt_order(d["score_n"]),
        lat_n=fmt_order(d["lat_n"]),
        max_n=fmt_order(d["max_n"]),
        avg_n=fmt_order(d["avg_n"]),
        days_n=fmt_order(d["tc_n"]),
        trend_data_attrs=trend_data_attrs,
        sparkline_closed=sparkline_closed,
        sparkline_path=sparkline_path,
        score_d=esc(d["score_d"]),
        lat_d=esc(d["lat_d"]),
        max_d=esc(d["max_d"]),
        avg_d=esc(d["avg_d"]),
        days_d=esc(d["tc_d"])
    )
    L.append(col3_html)

    # Column 4: Growth Rates
    col4_html = (
        '                <td class="td-trend" data-t7="{t7_n}" data-t30="{t30_n}" data-t60="{t60_n}" data-tall="{tall_n}" data-order="{t7_n}" {trend_data_attrs}>'
        '<div class="growth-consolidated-cell" style="display: flex; flex-direction: column; gap: 2px; font-size: 0.76rem;">'
        '<div style="display: flex; justify-content: space-between; gap: 8px;">'
        '<span class="growth-val-t7 {t7_cls}" title="7日涨幅">7日: {t7_d}</span>'
        '<span class="growth-val-t30 {t30_cls}" title="30日涨幅">30日: {t30_d}</span>'
        '</div>'
        '<div style="display: flex; justify-content: space-between; gap: 8px;">'
        '<span class="growth-val-t60 {t60_cls}" title="60日涨幅">60日: {t60_d}</span>'
        '<span class="growth-val-tall {tall_cls}" title="总涨幅">总幅: {tall_d}</span>'
        '</div>'
        '</div></td>'
    ).format(
        t7_n=fmt_order(d["t7_n"]),
        t30_n=fmt_order(d["t30_n"]),
        t60_n=fmt_order(d["t60_n"]),
        tall_n=fmt_order(d["tall_n"]),
        trend_data_attrs=trend_data_attrs,
        t7_cls=_growth_class(d["t7_n"]),
        t30_cls=_growth_class(d["t30_n"]),
        t60_cls=_growth_class(d["t60_n"]),
        tall_cls=_growth_class(d["tall_n"]),
        t7_d=esc(d["t7_d"]),
        t30_d=esc(d["t30_d"]),
        t60_d=esc(d["t60_d"]),
        tall_d=esc(d["tall_d"])
    )
    L.append(col4_html)

    # Column 5: Votes & Ratings
    col5_html = (
        '                <td class="td-votes" data-rv="{rv_n}" data-rp="{rp_n}" data-bv="{bv_n}" data-bp="{bp_n}" data-order="{rv_n}">'
        '<div class="votes-consolidated-cell" style="display: flex; flex-direction: column; gap: 4px; padding: 4px 0; font-size: 0.76rem;">'
        '<div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">'
        '<span style="font-weight: 700; color: var(--success); font-size: 0.82rem;">{rv_d} 票</span>'
        '<span style="font-size: 0.72rem; padding: 1px 5px; border-radius: 6px; background: rgba(16, 185, 129, 0.12); color: var(--success); font-weight: 600;">{rp_d}% 红</span>'
        '</div>'
        '<div class="vote-ratio-bar" style="width: 100%; height: 5px; border-radius: 3px; background: rgba(128,128,128,0.15); display: flex; overflow: hidden; margin: 2px 0;" title="红占比: {rp_d}% | 黑占比: {bp_d}%">'
        '<div class="vote-ratio-red" style="height: 100%; width: {rp_d}%; background: var(--success);"></div>'
        '<div class="vote-ratio-black" style="height: 100%; width: {bp_d}%; background: #6b7280;"></div>'
        '</div>'
        '<div style="display: flex; justify-content: space-between; font-size: 0.7rem; color: var(--text-muted);">'
        '<span>黑票: {bv_d}</span>'
        '<span>占比: {bp_d}%</span>'
        '</div>'
        '</div></td>'
    ).format(
        rv_n=fmt_order(d["rv_n"]),
        rp_n=fmt_order(d["rp_n"]),
        bv_n=fmt_order(d["bpv_n"]),
        bp_n=fmt_order(d["bp_n"]),
        rv_d=esc(d["rv_d"]),
        rp_d=esc(d["rp_d"].rstrip('%') if d["rp_d"] else "0"),
        bv_d=esc(d["bpv_d"]),
        bp_d=esc(d["bp_d"].rstrip('%') if d["bp_d"] else "0")
    )
    L.append(col5_html)

    # 推荐 / 收藏 / 评论
    engagement_html = (
        '                <td class="td-engage td-comment" data-rec="{rec_n}" data-fav="{fav_n}" data-com="{com_n}" data-order="{com_n}" data-mid="{mid}">'
        '<div class="engage-cell">'
        '<span><b>{rec_d}</b><em>推</em></span>'
        '<span><b>{fav_d}</b><em>藏</em></span>'
        '<span class="engage-comment-trigger" role="button" tabindex="0" title="点击评论格打开 / 再点关闭"><b>{com_d}</b><em>评</em><i class="comment-open-dot" aria-hidden="true">⌕</i></span>'
        '</div></td>'
    ).format(
        rec_n=fmt_order(d["rec_n"]),
        fav_n=fmt_order(d["fav_n"]),
        com_n=fmt_order(d["com_n"]),
        mid=mid,
        rec_d=esc(d["rec_d"]),
        fav_d=esc(d["fav_d"]),
        com_d=esc(d["com_d"]),
    )
    L.append(engagement_html)
    # 分类标签 + 整合包标签
    search_cat = esc_attr(" ".join(d["cat"]))
    def render_filter_tag(item, cls):
        name = item.get("name", "") if isinstance(item, dict) else _s(item)
        url = item.get("url", "") if isinstance(item, dict) else ""
        tip = item.get("title", "") if isinstance(item, dict) else ""
        title = tip or name
        open_html = '<a class="tag-filter-open" href="{}" target="_blank" title="打开 MC百科标签页">↗</a>'.format(esc_attr(url)) if url else ''
        return '<span class="{}" data-tag="{}" title="{}"><span class="tag-filter-name">{}</span>{}</span>'.format(
            cls, esc_attr(name), esc_attr(title), esc(name), open_html
        )
    badges_cat = "".join(
        render_filter_tag(t, "tag-cat") for t in d.get("cat_details", [])
    )
    search_pack = esc_attr(" ".join(d["pack"]))
    badges_pack = "".join(
        render_filter_tag(t, "tag-pack") for t in d.get("pack_details", [])
    )
    tags_html = (
        '<div class="tag-group-block"><div class="tag-group-label tag-group-label-cat">整合包分类</div><div class="tag-group tag-group-cat">{}</div></div>'.format(badges_cat)
        if badges_cat else ''
    )
    tags_html += (
        '<div class="tag-group-block"><div class="tag-group-label tag-group-label-pack">整合包标签</div><div class="tag-group tag-group-pack">{}</div></div>'.format(badges_pack)
        if badges_pack else ''
    )
    tag_count = len(d.get("cat", [])) + len(d.get("pack", []))
    L.append('                <td class="td-tags" data-search="{}" data-cat-search="{}" data-pack-search="{}" data-count="{}" data-order="{}"><div class="tag-wrap tag-combo-container">{}</div></td>'.format(
        esc_attr(" ".join(d["cat"] + d["pack"])), search_cat, search_pack, tag_count, tag_count, tags_html if tags_html else '<span class="tag-empty">—</span>'))
    mod_search_parts = []
    mod_groups = []
    group_map = {}
    for m in d.get("mods", []):
        cat_name = m.get("category_name") or "未分类"
        cat_id = m.get("category_id") or ""
        key = "{}|{}".format(cat_id, cat_name)
        if key not in group_map:
            group_map[key] = {
                "name": cat_name,
                "url": m.get("category_url") or "",
                "mods": [],
            }
            mod_groups.append(group_map[key])
        group_map[key]["mods"].append(m)
        mod_search_parts.extend([
            m.get("name", ""),
            m.get("title", ""),
            m.get("version", ""),
            m.get("category_name", ""),
            m.get("group_name", ""),
        ])
    mod_sections = []
    mod_summary_chips = []
    preview_limit = 8
    preview_used = 0
    hidden_mod_count = 0
    for group_idx, group in enumerate(mod_groups):
        links = []
        for m in group["mods"]:
            name = m.get("name") or m.get("title") or ""
            if not name:
                continue
            title_bits = [m.get("title") or name]
            if m.get("version"):
                title_bits.append("版本: {}".format(m.get("version")))
            if m.get("category_name"):
                title_bits.append("分类: {}".format(m.get("category_name")))
            version_html = '<span class="tag-mod-version">{}</span>'.format(esc(m.get("version", ""))) if m.get("version") else ''
            if preview_used >= preview_limit:
                hidden_mod_count += 1
                continue
            preview_used += 1
            links.append(
                '<span class="tag-mod" role="button" tabindex="0" title="{title}" data-mod="{mod}" data-mod-cat="{cat}" data-mod-url="{href}"><span class="tag-mod-name">{name}</span>{version}<a class="tag-mod-open" href="{href}" target="_blank" title="打开 MC百科模组页">↗</a></span>'.format(
                    href=esc_attr(m.get("url") or "#"),
                    title=esc_attr(" · ".join([x for x in title_bits if x])),
                    mod=esc_attr(name),
                    cat=esc_attr(m.get("category_name", "")),
                    name=esc(name),
                    version=version_html,
                )
            )
        cat_label = esc(group["name"])
        if group.get("url"):
            cat_head = '<a class="mod-category-link" href="{}" target="_blank">{}</a>'.format(esc_attr(group["url"]), cat_label)
        else:
            cat_head = '<span>{}</span>'.format(cat_label)
        mod_summary_chips.append(
            '<button type="button" class="mod-summary-chip" data-mod-cat-key="{key}" title="跳到 {name} 分类">{name}<b>{count}</b></button>'.format(
                key="cat{}".format(group_idx), name=cat_label, count=len(group["mods"])
            )
        )
        if not links:
            continue
        mod_sections.append(
            '<section class="mod-category-section" data-mod-cat-key="{key}"><div class="mod-category-head">{head}<span>{count}</span></div><div class="mod-grid">{mods}</div></section>'.format(
                key="cat{}".format(group_idx), head=cat_head, count=len(group["mods"]), mods="".join(links)
            )
        )
    # 完整模组名只保留在 compareData 中供筛选/对比使用，避免在每行 HTML 属性里再复制一遍。
    search_mods = esc_attr(" ".join(sorted({m.get("category_name", "") for m in d.get("mods", []) if m.get("category_name")})))
    mod_count = len(d.get("mods", []))
    if mod_sections:
        mod_html = (
            '<details class="mod-details">'
            '<summary><span class="mod-summary-main">包含模组 <b>{count}</b></span><span class="mod-summary-cats">{chips}</span></summary>'
            '<div class="mod-details-body">{sections}{more}<div class="mod-full-list" data-loaded="0"></div></div>'
            '</details>'
        ).format(
            count=mod_count, chips="".join(mod_summary_chips), sections="".join(mod_sections),
            more=('<div class="tag-empty">为保持本地看板流畅，仅预览前 {} 个模组；完整名单仍可用上方筛选与收藏对比查看。</div>'.format(preview_limit) if hidden_mod_count else '')
        )
    else:
        mod_html = '<span class="tag-empty">—</span>'
    L.append('                <td class="td-mods" data-search="{}" data-count="{}" data-order="{}"><div class="tag-wrap mod-container">{}</div></td>'.format(
        search_mods, mod_count, mod_count, mod_html))
    L.append('            </tr>')
    return "\n".join(L)

# ═══════════════════════════════════ 多主题配色系统 ═══════════════════════════════════
# 极致毛玻璃感重构版：降低透明度、增强底色透光率、强化阴影与对比

THEMES = {
    "warm": {
        "name": "暖色",
        "desc": "琥珀奶金 · 强效毛玻璃",
        "root": """            --primary: #d97706;
            --primary-light: #f59e0b;
            --primary-dark: #b45309;
            --secondary: #0d9488;
            --secondary-light: #14b8a6;
            --accent: #ea580c;
            --emerald: #059669;
            --gold: #b45309;
            --gold-light: #d4a574;
            --coral: #dc2626;
            --danger: #dc2626;
            --success: #059669;
            --glass-bg: rgba(253, 246, 230, 0.55);
            --glass-bg-solid: rgba(253, 246, 230, 0.7);
            --glass-border: rgba(217, 119, 6, 0.25);
            --glass-hover: rgba(217, 119, 6, 0.15);
            --glass-shadow: rgba(61, 43, 31, 0.18);
            --bg-main: #f5ead8;
            --bg-gradient-1: #fbf1e0;
            --bg-gradient-2: #e9d5b5;
            --bg-gradient-3: #ddc199;
            --text: #3d2b1f;
            --text-secondary: #4a3525;
            --text-muted: rgba(61, 43, 31, 0.55);
            --border: rgba(217, 119, 6, 0.2);
            --shadow: 0 8px 32px 0 rgba(61, 43, 31, 0.12);
            --shadow-lg: 0 16px 48px 0 rgba(61, 43, 31, 0.2);
            --radius: 24px;
            --radius-sm: 14px;
            --primary-rgb: 217, 119, 6;
            --primary-light-rgb: 245, 158, 11;
            --primary-dark-rgb: 180, 83, 9;
            --secondary-rgb: 13, 148, 136;
            --accent-rgb: 234, 88, 12;
            --gold-light-rgb: 212, 165, 116;
            --shadow-rgb: 61, 43, 31;
            --glass-tint-rgb: 253, 246, 230;
            --glass-tint2-rgb: 233, 213, 181;
            --line-rgb: 217, 119, 6;
            --th-bg-1: rgba(254, 249, 239, 0.6);
            --th-bg-2: rgba(243, 227, 201, 0.5);
            --th-sort-bg-1: rgba(255, 238, 199, 0.7);
            --th-sort-bg-2: rgba(243, 214, 168, 0.6);
            --th-sort-active-bg-1: rgba(255, 228, 168, 0.8);
            --th-sort-active-bg-2: rgba(240, 198, 130, 0.7);""",
    },
    "dark": {
        "name": "暗色",
        "desc": "靛蓝深空 · 暗色毛玻璃",
        "root": """            --primary: #6366f1;
            --primary-light: #818cf8;
            --primary-dark: #4f46e5;
            --secondary: #0ea5e9;
            --secondary-light: #38bdf8;
            --accent: #f59e0b;
            --emerald: #10b981;
            --gold: #d4a574;
            --gold-light: #e8c9a0;
            --coral: #e07a5f;
            --danger: #ef4444;
            --success: #10b981;
            --glass-bg: rgba(10, 14, 26, 0.6);
            --glass-bg-solid: rgba(19, 26, 46, 0.75);
            --glass-border: rgba(255, 255, 255, 0.12);
            --glass-hover: rgba(255, 255, 255, 0.12);
            --glass-shadow: rgba(0, 0, 0, 0.4);
            --bg-main: #0a0e1a;
            --bg-gradient-1: #0d1320;
            --bg-gradient-2: #131a2e;
            --bg-gradient-3: #1a2340;
            --text: #f1f5f9;
            --text-secondary: rgba(241, 245, 249, 0.85);
            --text-muted: rgba(241, 245, 249, 0.5);
            --border: rgba(255, 255, 255, 0.1);
            --shadow: 0 8px 32px 0 rgba(0,0,0,.3);
            --shadow-lg: 0 16px 48px 0 rgba(0,0,0,.45);
            --radius: 24px;
            --radius-sm: 14px;
            --primary-rgb: 99, 102, 241;
            --primary-light-rgb: 129, 140, 248;
            --primary-dark-rgb: 79, 70, 229;
            --secondary-rgb: 14, 165, 233;
            --accent-rgb: 245, 158, 11;
            --gold-light-rgb: 232, 201, 160;
            --shadow-rgb: 0, 0, 0;
            --glass-tint-rgb: 255, 255, 255;
            --glass-tint2-rgb: 241, 245, 249;
            --line-rgb: 255, 255, 255;
            --th-bg-1: rgba(15, 20, 35, 0.6);
            --th-bg-2: rgba(20, 28, 48, 0.5);
            --th-sort-bg-1: rgba(30, 38, 60, 0.7);
            --th-sort-bg-2: rgba(35, 43, 70, 0.6);
            --th-sort-active-bg-1: rgba(99, 102, 241, 0.35);
            --th-sort-active-bg-2: rgba(129, 140, 248, 0.25);""",
    },
    "light": {
        "name": "亮色",
        "desc": "冰蓝白银 · 强效毛玻璃",
        "root": """            --primary: #2563eb;
            --primary-light: #3b82f6;
            --primary-dark: #1d4ed8;
            --secondary: #0891b2;
            --secondary-light: #06b6d4;
            --accent: #8b5cf6;
            --emerald: #059669;
            --gold: #6366f1;
            --gold-light: #a5b4fc;
            --coral: #f43f5e;
            --danger: #ef4444;
            --success: #10b981;
            --glass-bg: rgba(240, 246, 255, 0.55);
            --glass-bg-solid: rgba(240, 246, 255, 0.7);
            --glass-border: rgba(37, 99, 235, 0.18);
            --glass-hover: rgba(37, 99, 235, 0.12);
            --glass-shadow: rgba(37, 99, 235, 0.12);
            --bg-main: #e2e8f0;
            --bg-gradient-1: #f8fafc;
            --bg-gradient-2: #cbd5e1;
            --bg-gradient-3: #94a3b8;
            --text: #0f172a;
            --text-secondary: #1e293b;
            --text-muted: rgba(15, 23, 42, 0.55);
            --border: rgba(37, 99, 235, 0.12);
            --shadow: 0 8px 32px 0 rgba(37, 99, 235, .08);
            --shadow-lg: 0 16px 48px 0 rgba(37, 99, 235, .15);
            --radius: 24px;
            --radius-sm: 14px;
            --primary-rgb: 37, 99, 235;
            --primary-light-rgb: 59, 130, 246;
            --primary-dark-rgb: 29, 78, 216;
            --secondary-rgb: 8, 145, 178;
            --accent-rgb: 139, 92, 246;
            --gold-light-rgb: 165, 180, 252;
            --shadow-rgb: 37, 99, 235;
            --glass-tint-rgb: 255, 255, 255;
            --glass-tint2-rgb: 241, 245, 249;
            --line-rgb: 37, 99, 235;
            --th-bg-1: rgba(255, 255, 255, 0.6);
            --th-bg-2: rgba(241, 245, 249, 0.5);
            --th-sort-bg-1: rgba(224, 242, 254, 0.7);
            --th-sort-bg-2: rgba(186, 230, 253, 0.6);
            --th-sort-active-bg-1: rgba(186, 230, 253, 0.8);
            --th-sort-active-bg-2: rgba(125, 211, 252, 0.7);""",
    },
    "eye": {
        "name": "护眼",
        "desc": "低蓝光暖米色 · 阅读友好",
        "root": """            --primary: #8a6a28;
            --primary-light: #a98534;
            --primary-dark: #6f531d;
            --secondary: #6f7d3a;
            --secondary-light: #87974a;
            --accent: #b86b3f;
            --emerald: #607a36;
            --gold: #8a6a28;
            --gold-light: #d4b46a;
            --coral: #b25b4b;
            --danger: #b25b4b;
            --success: #607a36;
            --glass-bg: rgba(255, 249, 235, 0.82);
            --glass-bg-solid: rgba(255, 252, 242, 0.97);
            --glass-border: rgba(138, 106, 40, 0.16);
            --glass-hover: rgba(138, 106, 40, 0.08);
            --glass-shadow: rgba(73, 61, 42, 0.12);
            --bg-main: #f5ecd8;
            --bg-gradient-1: #fff8e8;
            --bg-gradient-2: #f3e6c9;
            --bg-gradient-3: #e7d8b8;
            --text: #251f15;
            --text-secondary: #493d2a;
            --text-muted: rgba(73, 61, 42, 0.62);
            --border: rgba(138, 106, 40, 0.16);
            --shadow: 0 14px 36px rgba(73, 61, 42, 0.10);
            --shadow-lg: 0 24px 60px rgba(73, 61, 42, 0.14);
            --radius: 14px;
            --radius-sm: 10px;
            --primary-rgb: 138, 106, 40;
            --primary-light-rgb: 169, 133, 52;
            --primary-dark-rgb: 111, 83, 29;
            --secondary-rgb: 111, 125, 58;
            --accent-rgb: 184, 107, 63;
            --gold-light-rgb: 212, 180, 106;
            --shadow-rgb: 73, 61, 42;
            --glass-tint-rgb: 255, 252, 242;
            --glass-tint2-rgb: 243, 230, 201;
            --line-rgb: 138, 106, 40;
            --th-bg-1: rgba(255, 250, 237, 0.98);
            --th-bg-2: rgba(244, 232, 207, 0.96);
            --th-sort-bg-1: rgba(255, 242, 204, 0.88);
            --th-sort-bg-2: rgba(238, 218, 174, 0.72);
            --th-sort-active-bg-1: rgba(246, 224, 181, 0.92);
            --th-sort-active-bg-2: rgba(224, 196, 136, 0.78);""",
    },
    "pink": {
        "name": "粉色",
        "desc": "樱粉莓白 · 现代柔和",
        "root": """            --primary: #e84a8a;
            --primary-light: #ff7ab1;
            --primary-dark: #c72f70;
            --secondary: #8b5cf6;
            --secondary-light: #a78bfa;
            --accent: #06b6d4;
            --emerald: #10b981;
            --gold: #e84a8a;
            --gold-light: #f9a8d4;
            --coral: #fb7185;
            --danger: #e11d48;
            --success: #10b981;
            --glass-bg: rgba(255, 247, 251, 0.84);
            --glass-bg-solid: rgba(255, 250, 253, 0.98);
            --glass-border: rgba(232, 74, 138, 0.16);
            --glass-hover: rgba(232, 74, 138, 0.08);
            --glass-shadow: rgba(126, 34, 86, 0.12);
            --bg-main: #fdf2f8;
            --bg-gradient-1: #fffafd;
            --bg-gradient-2: #fce7f3;
            --bg-gradient-3: #eef2ff;
            --text: #20101a;
            --text-secondary: #4a263b;
            --text-muted: rgba(74, 38, 59, 0.58);
            --border: rgba(232, 74, 138, 0.14);
            --shadow: 0 14px 36px rgba(126, 34, 86, 0.09);
            --shadow-lg: 0 24px 60px rgba(126, 34, 86, 0.14);
            --radius: 14px;
            --radius-sm: 10px;
            --primary-rgb: 232, 74, 138;
            --primary-light-rgb: 255, 122, 177;
            --primary-dark-rgb: 199, 47, 112;
            --secondary-rgb: 139, 92, 246;
            --accent-rgb: 6, 182, 212;
            --gold-light-rgb: 249, 168, 212;
            --shadow-rgb: 126, 34, 86;
            --glass-tint-rgb: 255, 250, 253;
            --glass-tint2-rgb: 252, 231, 243;
            --line-rgb: 232, 74, 138;
            --th-bg-1: rgba(255, 250, 253, 0.98);
            --th-bg-2: rgba(252, 231, 243, 0.96);
            --th-sort-bg-1: rgba(253, 242, 248, 0.94);
            --th-sort-bg-2: rgba(251, 207, 232, 0.72);
            --th-sort-active-bg-1: rgba(251, 207, 232, 0.9);
            --th-sort-active-bg-2: rgba(244, 114, 182, 0.48);""",
    },
    "anime": {
        "name": "流光",
        "desc": "流光玻璃 · 香槟紫褐",
        "root": """            --primary: #d98f5b;
            --primary-light: #ffd7a1;
            --primary-dark: #9f5a3b;
            --secondary: #8c6bb1;
            --secondary-light: #c4a7e7;
            --accent: #b8875d;
            --emerald: #b46a5d;
            --gold: #b8875d;
            --gold-light: #f1c894;
            --coral: #c96f58;
            --danger: #d26b72;
            --success: #c98a5d;
            --glass-bg: rgba(54, 41, 45, 0.28);
            --glass-bg-solid: rgba(54, 41, 45, 0.62);
            --glass-border: rgba(255, 215, 161, 0.34);
            --glass-hover: rgba(255, 215, 161, 0.12);
            --glass-shadow: rgba(24, 18, 22, 0.34);
            --bg-main: #2f2830;
            --bg-gradient-1: #2f2830;
            --bg-gradient-2: #4b3734;
            --bg-gradient-3: #6a4738;
            --text: #fff3dc;
            --text-secondary: #ecd6b8;
            --text-muted: rgba(236, 214, 184, 0.72);
            --border: rgba(255, 215, 161, 0.22);
            --shadow: 0 18px 54px rgba(24, 18, 22, 0.30);
            --shadow-lg: 0 30px 88px rgba(24, 18, 22, 0.42);
            --radius: 14px;
            --radius-sm: 10px;
            --primary-rgb: 217, 143, 91;
            --primary-light-rgb: 255, 215, 161;
            --primary-dark-rgb: 159, 90, 59;
            --secondary-rgb: 140, 107, 177;
            --accent-rgb: 184, 135, 93;
            --gold-light-rgb: 241, 200, 148;
            --shadow-rgb: 24, 18, 22;
            --glass-tint-rgb: 71, 54, 54;
            --glass-tint2-rgb: 102, 71, 56;
            --line-rgb: 217, 143, 91;
            --th-bg-1: rgba(54, 41, 45, 0.62);
            --th-bg-2: rgba(102, 71, 56, 0.48);
            --th-sort-bg-1: rgba(217, 143, 91, 0.18);
            --th-sort-bg-2: rgba(140, 107, 177, 0.12);
            --th-sort-active-bg-1: rgba(255, 215, 161, 0.26);
            --th-sort-active-bg-2: rgba(217, 143, 91, 0.18);""",
    },
}

# ═══════════════════════ 美化版模板 v2.0 ═══════════════════════

PRETTY_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN" data-theme="{default_theme}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <!-- ★ 防闪烁 (Anti-FOUC)：在渲染 DOM 前立即加载保存的主题 -->
    <script>
        (function() {{
            var theme = localStorage.getItem('mcmod-theme-v2') || '{default_theme}';
            if (theme) document.documentElement.setAttribute('data-theme', theme);
        }})();
    </script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/datatables.net-bs5@1.13.6/css/dataTables.bootstrap5.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />
    <link href="https://cdn.jsdelivr.net/npm/select2-bootstrap-5-theme@1.3.0/dist/select2-bootstrap-5-theme.min.css" rel="stylesheet" />
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Noto+Sans+SC:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        /* ════════ CSS 变量：玻璃态暗色主题 ════════ */
        /* ═══ 默认: 冷白现代风 ═══ */
        :root {{
{theme_light}
        }}
        /* ═══ 暗色毛玻璃 ═══ */
        :root[data-theme="dark"] {{
{theme_dark}
        }}
        :root[data-theme="warm"] {{
{theme_warm}
        }}
        /* ═══ 亮色毛玻璃 ═══ */
        :root[data-theme="light"] {{
{theme_light}
        }}
        :root[data-theme="eye"] {{
{theme_eye}
        }}
        :root[data-theme="pink"] {{
{theme_pink}
        }}
        :root[data-theme="anime"] {{
{theme_anime}
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        html {{ scroll-behavior: smooth; }}
        body {{
        font-family: 'Plus Jakarta Sans', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: var(--bg-main);
            color: var(--text);
            line-height: 1.6;
            min-height: 100vh;
            overflow-x: hidden;
        }}
        /* ════════ 动画背景 + 浮动光球 ════════ */
        .bg-layer {{
            position: fixed; top: 0; left: 0;
            width: 100%; height: 100%; z-index: -2;
            background: linear-gradient(135deg, var(--bg-gradient-1) 0%, var(--bg-gradient-2) 50%, var(--bg-gradient-3) 100%);
        }}
        .bg-layer::before {{
            content: ''; position: absolute; inset: 0;
            background:
                radial-gradient(ellipse 80% 50% at 20% 30%, rgba(var(--primary-rgb), 0.12) 0%, transparent 50%),
                radial-gradient(ellipse 60% 40% at 80% 70%, rgba(var(--secondary-rgb), 0.10) 0%, transparent 50%),
                radial-gradient(ellipse 50% 30% at 50% 80%, rgba(var(--gold-light-rgb), 0.08) 0%, transparent 50%);
        }}
        .orb {{
            position: fixed; border-radius: 50%;
            filter: blur(120px);
            z-index: -1; animation: orb-float 20s ease-in-out infinite;
        }}
        .orb-1 {{ width: 380px; height: 380px; background: rgba(var(--primary-light-rgb),0.2); top: 8%; left: 5%; animation-delay: 0s; }}
        .orb-2 {{ width: 320px; height: 320px; background: rgba(var(--secondary-rgb),0.12); top: 55%; right: 5%; animation-delay: -5s; }}
        .orb-3 {{ width: 280px; height: 280px; background: rgba(var(--gold-light-rgb),0.15); bottom: 8%; left: 30%; animation-delay: -10s; }}
                @keyframes orb-float {{
            0%, 100% {{ transform: translate(0, 0) scale(1); }}
            25% {{ transform: translate(30px, -30px) scale(1.05); }}
            50% {{ transform: translate(-20px, 20px) scale(0.95); }}
            75% {{ transform: translate(20px, 10px) scale(1.02); }}
        }}
        /* ════════ Hero 区域 ════════ */
        .hero {{
            background: linear-gradient(135deg, rgba(var(--glass-tint-rgb),0.8), rgba(var(--glass-tint2-rgb),0.6));
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--glass-border);
            padding: 2.5rem 2rem 3.5rem;
            position: relative; overflow: hidden;
        }}
        .hero::before {{
            content: ''; position: absolute;
            top: 0; left: 0; right: 0; height: 1px;
            background: linear-gradient(90deg, transparent, var(--primary), transparent);
        }}
        .hero-inner {{ max-width: 2400px; margin: 0 auto; position: relative; z-index: 1; }}
        .hero-title {{
            font-size: 2.4rem; font-weight: 800;
            letter-spacing: -1px;
            background: linear-gradient(135deg, var(--primary-dark), var(--accent), var(--secondary));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .hero-sub {{
            font-size: 0.95rem; opacity: 0.8; margin-top: 0.5rem;
            color: var(--text-secondary);
        }}
        .hero-sub a {{
            color: var(--gold-light); text-decoration: underline;
            text-underline-offset: 2px; font-weight: 600;
        }}
        .hero-sub a:hover {{ color: var(--text); }}
        /* ════════ 统计卡片 ════════ */
        .stats-bar {{
            display: flex; gap: 1.5rem; flex-wrap: wrap;
            max-width: 2400px; margin: -3rem auto 1.5rem;
            padding: 0 2rem; position: relative; z-index: 2;
        }}
        .stat-card {{
            flex: 1; min-width: 240px;
            background: var(--glass-bg);
            backdrop-filter: blur(28px); -webkit-backdrop-filter: blur(28px);
            border: 1px solid var(--glass-border);
            border-radius: var(--radius);
            padding: 1.5rem 1.8rem;
            box-shadow: var(--shadow-lg);
            display: flex; align-items: center; gap: 1.2rem;
            transition: transform .3s, box-shadow .3s;
            position: relative; overflow: hidden;
        }}
        .stat-card::before {{
            content: ''; position: absolute;
            top: 0; left: 0; right: 0; height: 1px;
            background: linear-gradient(90deg, transparent, rgba(var(--primary-dark-rgb), 0.15), transparent);
        }}
        .stat-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 20px 50px rgba(0,0,0,.3), 0 0 40px rgba(var(--primary-rgb),.1);
        }}
        .stat-icon {{
            width: 56px; height: 56px; border-radius: 16px;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.6rem; flex-shrink: 0;
        }}
        .stat-icon.s1 {{ background: linear-gradient(135deg, rgba(var(--primary-light-rgb),.2), rgba(var(--primary-light-rgb),.05)); box-shadow: 0 8px 32px rgba(var(--primary-light-rgb),.15); }}
        .stat-icon.s2 {{ background: linear-gradient(135deg, rgba(var(--secondary-rgb),.2), rgba(var(--secondary-rgb),.05)); box-shadow: 0 8px 32px rgba(var(--secondary-rgb),.15); }}
        .stat-icon.s3 {{ background: linear-gradient(135deg, rgba(var(--accent-rgb),.2), rgba(var(--accent-rgb),.05)); box-shadow: 0 8px 32px rgba(var(--accent-rgb),.15); }}
        .stat-label {{ font-size: 0.8rem; color: var(--text-muted); font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase; }}
        .stat-value {{
            font-size: 1.8rem; font-weight: 800; margin-top: 2px;
            font-family: 'JetBrains Mono', monospace;
            color: var(--text);
            background-clip: text;
        }}
        /* ════════ 免责声明 + 提示 ════════ */
        .notice-wrap {{ max-width: 2400px; margin: 0 auto 1rem; padding: 0 2rem; }}
        .disclaimer-inner {{
            background: var(--glass-bg);
            backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(var(--primary-light-rgb), 0.2);
            border-radius: var(--radius-sm);
            padding: 1rem 1.5rem; font-size: 0.85rem;
            color: var(--text-secondary); line-height: 1.7;
        }}
        .disclaimer-inner strong {{ color: var(--primary-dark); }}
        .disclaimer-inner a {{ color: var(--secondary); text-decoration: underline; }}
        .sort-hint-inner {{
            background: var(--glass-bg);
            backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(var(--primary-light-rgb), 0.2);
            border-radius: var(--radius-sm);
            padding: 0.7rem 1.2rem; font-size: 0.85rem;
            color: var(--text-secondary); font-weight: 500;
            display: flex; align-items: center; gap: 0.55rem; line-height: 1.6;
        }}
        .sort-hint-inner b {{ color: var(--accent); }}
        .stats-bar {{
            margin: -2.25rem auto 0.75rem !important;
            gap: 0.55rem !important;
            align-items: stretch;
        }}
        .stat-card {{
            min-width: 170px !important;
            padding: 0.65rem 0.85rem !important;
            border-radius: 14px !important;
            gap: 0.65rem !important;
            box-shadow: var(--shadow) !important;
        }}
        .stat-icon {{
            width: 34px !important;
            height: 34px !important;
            border-radius: 10px !important;
            font-size: 1rem !important;
        }}
        .stat-label {{
            font-size: 0.68rem !important;
            letter-spacing: 0.2px !important;
        }}
        .stat-value {{
            font-size: 1.12rem !important;
            margin-top: 0 !important;
            line-height: 1.15;
        }}
        .notice-compact {{
            display: block;
            max-width: 2400px;
            margin: 0 auto 0.75rem;
            padding: 0 2rem;
        }}
        .notice-compact > summary {{
            list-style: none;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.38rem 0.72rem;
            border-radius: 999px;
            border: 1px solid rgba(var(--primary-rgb), 0.16);
            background: rgba(var(--glass-tint-rgb), 0.54);
            color: var(--text-secondary);
            font-size: 0.78rem;
            font-weight: 850;
            cursor: pointer;
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
        }}
        .notice-compact > summary::-webkit-details-marker {{
            display: none;
        }}
        .notice-compact[open] > summary {{
            margin-bottom: 0.55rem;
            color: var(--primary-dark);
            background: rgba(var(--primary-rgb), 0.10);
        }}
        .notice-compact .disclaimer-inner,
        .notice-compact .sort-hint-inner {{
            font-size: 0.78rem !important;
            padding: 0.55rem 0.85rem !important;
            line-height: 1.45 !important;
            border-radius: 12px !important;
        }}
        /* ════════ 主容器 ════════ */
        .main-wrap {{
            max-width: 2400px; margin: 0 auto;
            padding: 0 2rem 3rem;
        }}
        /* ════════ 筛选卡片 ════════ */
        .filter-card {{
            background:
                linear-gradient(135deg, rgba(var(--glass-tint-rgb), 0.56), rgba(var(--glass-tint2-rgb), 0.28)),
                rgba(var(--glass-tint-rgb), 0.22);
            backdrop-filter: blur(38px) saturate(175%);
            -webkit-backdrop-filter: blur(38px) saturate(175%);
            border: 1px solid rgba(var(--primary-rgb), 0.18);
            border-radius: calc(var(--radius) + 4px);
            padding: 1.35rem; box-shadow: 0 18px 56px rgba(var(--shadow-rgb), 0.13), inset 0 1px 0 rgba(255,255,255,.18);
            margin-bottom: 1.5rem; position: relative; overflow: hidden;
        }}
        .filter-card::before {{
            content: ''; position: absolute;
            top: 0; left: 0; right: 0; height: 1px;
            background: linear-gradient(90deg, transparent, rgba(var(--primary-dark-rgb), 0.15), transparent);
        }}
        .filter-row {{
            display: flex; gap: 1rem; flex-wrap: wrap; align-items: flex-end;
        }}
        .filter-col {{ flex: 1; min-width: 200px; }}
        .filter-col-type {{ flex: 0 0 150px; min-width: 150px; }}
        .filter-col-btn {{ flex: 0 0 auto; }}
        .filter-label {{
            display: block; font-size: 0.76rem; font-weight: 850;
            color: var(--text-secondary); margin-bottom: 0.42rem;
            text-transform: none; letter-spacing: 0;
        }}
        .filter-card .form-select,
        #searchScope,
        .dataTables_wrapper .dataTables_filter input {{
            min-height: 38px;
            border-radius: 16px !important;
            border: 1px solid rgba(var(--primary-rgb), 0.22) !important;
            background:
                linear-gradient(135deg, rgba(var(--glass-tint-rgb), 0.72), rgba(var(--glass-tint2-rgb), 0.42)),
                rgba(var(--glass-tint-rgb), 0.28) !important;
            color: var(--text) !important;
            box-shadow: 0 10px 28px rgba(var(--shadow-rgb), 0.08), inset 0 1px 0 rgba(255,255,255,.18) !important;
            backdrop-filter: blur(22px) saturate(165%);
            -webkit-backdrop-filter: blur(22px) saturate(165%);
            font-weight: 750;
            transition: border-color .18s ease, box-shadow .18s ease, transform .18s ease, background .18s ease;
        }}
        .filter-card .form-select:hover,
        #searchScope:hover,
        .dataTables_wrapper .dataTables_filter input:hover {{
            border-color: rgba(var(--primary-rgb), 0.38) !important;
            box-shadow: 0 14px 34px rgba(var(--shadow-rgb), 0.12), inset 0 1px 0 rgba(255,255,255,.22) !important;
        }}
        .filter-card .form-select:focus,
        #searchScope:focus,
        .dataTables_wrapper .dataTables_filter input:focus {{
            border-color: rgba(var(--primary-rgb), 0.56) !important;
            box-shadow: 0 0 0 4px rgba(var(--primary-rgb), 0.14), 0 14px 36px rgba(var(--shadow-rgb), 0.14) !important;
            outline: none !important;
        }}
        .filter-card .form-select option,
        #searchScope option {{
            background: var(--glass-bg-solid);
            color: var(--text);
            font-weight: 700;
        }}
        .filter-tools {{
            display: flex; align-items: center; justify-content: flex-end; gap: 0.35rem;
            min-height: 24px; margin-top: 0.35rem;
        }}
        .exclude-toggle {{
            display: inline-flex; align-items: center; gap: 0.25rem;
            border: 1px solid rgba(var(--primary-rgb), 0.18);
            background: rgba(var(--glass-tint-rgb), 0.45);
            color: var(--text-secondary);
            border-radius: 999px; padding: 0.12rem 0.5rem;
            font-size: 0.72rem; font-weight: 800; cursor: pointer; user-select: none;
            transition: background .16s ease, color .16s ease, border-color .16s ease, transform .16s ease;
        }}
        .exclude-toggle:hover {{
            transform: translateY(-1px);
            border-color: rgba(var(--primary-rgb), 0.34);
            color: var(--primary-dark);
        }}
        .exclude-toggle input {{
            width: 13px; height: 13px; margin: 0; accent-color: var(--danger);
        }}
        .exclude-toggle:has(input:checked) {{
            background: rgba(225, 29, 72, 0.12);
            border-color: rgba(225, 29, 72, 0.34);
            color: var(--danger);
        }}
        .hover-mode-panel {{
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 0.45rem;
            flex-wrap: wrap;
            margin-top: 0.85rem;
            padding-top: 0.75rem;
            border-top: 1px solid rgba(var(--primary-rgb), 0.12);
        }}
        .hover-mode-label {{
            font-size: 0.76rem;
            font-weight: 900;
            color: var(--text-muted);
            margin-right: 0.1rem;
        }}
        .mode-toggle {{
            display: inline-flex; align-items: center; justify-content: center; gap: 0.35rem;
            border: 1px solid rgba(var(--primary-rgb), 0.20);
            background: rgba(var(--glass-tint-rgb), 0.50);
            color: var(--text-secondary);
            border-radius: 999px; padding: 0.38rem 0.7rem;
            font-size: 0.76rem; font-weight: 850; cursor: pointer; user-select: none;
            white-space: nowrap;
            transition: background .16s ease, color .16s ease, border-color .16s ease, transform .16s ease;
        }}
        .mode-toggle:hover {{
            transform: translateY(-1px);
            color: var(--primary-dark);
            border-color: rgba(var(--primary-rgb), 0.34);
        }}
        .mode-toggle input {{
            width: 14px; height: 14px; margin: 0; accent-color: var(--primary);
        }}
        .mode-toggle:has(input:checked) {{
            background: rgba(var(--primary-rgb), 0.13);
            color: var(--primary-dark);
        }}
        .mode-toggle-mini {{
            padding: 0.25rem 0.55rem;
            font-size: 0.72rem;
            border-radius: 8px;
        }}
        .mode-toggle-header {{
            position: relative;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            z-index: 30;
            margin-top: 4px;
            min-width: 58px;
            height: 24px;
            padding: 0 10px 0 25px;
            border-radius: 999px;
            background: rgba(var(--primary-rgb), 0.08);
            vertical-align: middle;
            pointer-events: auto;
            cursor: pointer;
            user-select: none;
            line-height: 1;
            overflow: visible;
        }}
        .mode-toggle-header > span {{
            position: relative;
            z-index: 2;
            font-size: 0.68rem;
            line-height: 1;
            font-weight: 900;
            color: var(--text-muted);
            pointer-events: none;
            white-space: nowrap;
        }}
        .mode-toggle-header input {{
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            opacity: 0;
            cursor: pointer;
            pointer-events: none;
        }}
        .mode-toggle-header::before {{
            content: "";
            position: absolute;
            left: 7px;
            top: 50%;
            width: 10px;
            height: 10px;
            border-radius: 999px;
            background: rgba(100, 116, 139, 0.72);
            box-shadow: 0 1px 3px rgba(var(--shadow-rgb), 0.18);
            transform: translateY(-50%);
            transition: background .16s ease, box-shadow .16s ease, transform .16s ease;
        }}
        .mode-toggle-header.is-on,
        .mode-toggle-header:has(input:checked) {{
            background: rgba(var(--primary-rgb), 0.18);
            border-color: rgba(var(--primary-rgb), 0.38);
        }}
        .mode-toggle-header.is-on::before,
        .mode-toggle-header:has(input:checked)::before {{
            transform: translateY(-50%) scale(1.18);
            background: var(--primary);
            box-shadow: 0 0 0 4px rgba(var(--primary-rgb), 0.14);
        }}
        .mode-toggle-header.is-on > span,
        .mode-toggle-header:has(input:checked) > span {{
            color: var(--primary);
        }}
        /* ════════ 表格卡片 ════════ */
        .table-card {{
            background: var(--glass-bg);
            backdrop-filter: blur(28px); -webkit-backdrop-filter: blur(28px);
            border: 1px solid var(--glass-border);
            border-radius: var(--radius);
            padding: 1.25rem; box-shadow: var(--shadow-lg);
            position: relative; overflow: visible;
        }}
        .table-card::before {{
            content: ''; position: absolute;
            top: 0; left: 0; right: 0; height: 1px;
            background: linear-gradient(90deg, transparent, rgba(var(--primary-dark-rgb), 0.15), transparent);
        }}
        .table-responsive {{ overflow-x: auto !important; -webkit-overflow-scrolling: touch; }}
        /* DataTables scrollBody 滚动条美化 */
        .dataTables_scrollBody {{
            scrollbar-width: thin;
            scrollbar-color: rgba(var(--primary-rgb),.3) transparent;
        }}
        .dataTables_scrollBody::-webkit-scrollbar {{ width: 8px; height: 8px; }}
        .dataTables_scrollBody::-webkit-scrollbar-track {{ background: transparent; }}
        .dataTables_scrollBody::-webkit-scrollbar-thumb {{
            background: linear-gradient(180deg, var(--primary), var(--secondary));
            border-radius: 6px;
        }}
        .dataTables_wrapper {{ width: 100% !important; }}
        /* ★★★ 覆盖 Bootstrap 表格 CSS 变量：修复暗色主题下文字不可见 ★★★ */
        .table {{
            --bs-table-color: var(--text-secondary) !important;
            --bs-table-bg: transparent !important;
            --bs-table-striped-color: var(--text-secondary) !important;
            --bs-table-striped-bg: transparent !important;
            --bs-table-hover-color: var(--text) !important;
            --bs-table-hover-bg: rgba(var(--primary-light-rgb),0.06) !important;
            color: var(--text-secondary) !important;
            background-color: transparent !important;
            border-color: var(--border) !important;
        }}
        table.dataTable {{
            border-collapse: separate !important;
            border-spacing: 0;
            width: 100% !important;
        }}
        /* ★★★ 修复表头 UI：glassmorphism sticky 表头 ★★★ */
        table.dataTable thead th {{
            background: linear-gradient(135deg, var(--th-bg-1), var(--th-bg-2)) !important;
            color: var(--text) !important;
            font-weight: 700;
            font-size: 0.78rem;
            letter-spacing: 0.3px;
            border: none !important;
            border-bottom: 0 !important;
            padding: 0.85rem 2.15rem 0.85rem 0.8rem !important;
            white-space: nowrap;
            cursor: pointer;
            transition: background 0.2s;
            position: relative;
            min-width: 72px;
        }}
        table.dataTable thead th:hover {{
            background: linear-gradient(135deg, var(--th-sort-bg-1), var(--th-sort-bg-2)) !important;
        }}
        table.dataTable thead th.sorting::after,
        table.dataTable thead th.sorting::before,
        table.dataTable thead th.sorting_asc::after,
        table.dataTable thead th.sorting_asc::before,
        table.dataTable thead th.sorting_desc::after,
        table.dataTable thead th.sorting_desc::before {{
            position: absolute !important;
            top: 50% !important;
            transform: translateY(-50%) !important;
            font-size: 0.58em !important;
            width: auto !important;
            text-align: center;
            line-height: 1;
        }}
        table.dataTable thead th.sorting::before,
        table.dataTable thead th.sorting_asc::before,
        table.dataTable thead th.sorting_desc::before {{
            right: 0.92rem !important;
            content: "▲" !important;
            opacity: 0.15;
            color: var(--text-muted);
        }}
        table.dataTable thead th.sorting::after,
        table.dataTable thead th.sorting_asc::after,
        table.dataTable thead th.sorting_desc::after {{
            right: 0.42rem !important;
            content: "▼" !important;
            opacity: 0.15;
            color: var(--text-muted);
        }}
        table.dataTable thead th.sorting_asc {{
            background: linear-gradient(135deg, var(--th-sort-active-bg-1), var(--th-sort-active-bg-2)) !important;
            color: var(--primary-dark) !important;
        }}
        table.dataTable thead th.sorting_desc {{
            background: linear-gradient(135deg, var(--th-sort-active-bg-1), var(--th-sort-active-bg-2)) !important;
            color: var(--primary-dark) !important;
        }}
        table.dataTable thead th.sorting_asc::before {{
            opacity: 1 !important; color: var(--primary) !important;
        }}
        table.dataTable thead th.sorting_desc::after {{
            opacity: 1 !important; color: var(--primary) !important;
        }}
        table.dataTable thead th.sorting_asc,
        table.dataTable thead th.sorting_desc,
        table.dataTable thead th.dt-active-sort {{
            box-shadow: inset 0 0 0 999px rgba(var(--primary-rgb), 0.055) !important;
        }}
        .dataTables_scrollHead th {{
            cursor: pointer !important;
        }}
        .dataTables_scrollHead th.dt-active-sort::after {{
            z-index: 2;
        }}
        .sort-strip {{
            position: relative;
            z-index: 3;
            overflow: hidden;
            height: 26px;
            border-top: 0;
            border-bottom: 0;
            background: linear-gradient(180deg, rgba(var(--primary-rgb), 0.075), rgba(var(--primary-rgb), 0.045));
            pointer-events: auto;
        }}
        .sort-strip::before {{
            content: "";
            position: absolute;
            left: 0;
            right: 0;
            top: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(var(--primary-rgb), 0.24), transparent);
            pointer-events: none;
        }}
        .sort-strip-inner {{
            position: relative;
            height: 100%;
            white-space: nowrap;
        }}
        .sort-strip-seg {{
            position: absolute;
            top: 0;
            height: 100%;
            margin: 0;
            padding: 0;
            border: 0;
            border-right: 0;
            background: transparent;
            cursor: pointer;
            appearance: none;
            -webkit-appearance: none;
            transition: background .16s ease, box-shadow .16s ease, opacity .16s ease;
        }}
        .sort-strip-seg:hover {{
            background: rgba(var(--primary-rgb), 0.10);
        }}
        .sort-strip-seg.active {{
            background: linear-gradient(180deg, rgba(var(--primary-rgb), 0.18), rgba(var(--primary-rgb), 0.26));
            box-shadow: none;
        }}
        .sort-strip-seg.active::after {{
            content: "";
            position: absolute;
            left: 50%;
            top: 50%;
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: var(--primary);
            transform: translate(-50%, -50%);
            box-shadow: 0 0 0 3px rgba(var(--primary-rgb), 0.12), 0 8px 18px rgba(var(--primary-rgb), 0.25);
        }}
        table.dataTable tbody td.dt-active-sort {{
            background: linear-gradient(180deg, rgba(var(--primary-rgb), 0.045), rgba(var(--primary-rgb), 0.018)) !important;
        }}
        table.dataTable tbody tr:hover td.dt-active-sort {{
            background: linear-gradient(180deg, rgba(var(--primary-rgb), 0.085), rgba(var(--primary-rgb), 0.035)) !important;
        }}
        table.dataTable tbody td {{
            padding: 0.45rem 0.5rem !important;
            font-size: 0.8rem;
            border-bottom: 1px solid rgba(var(--line-rgb), 0.04);
            vertical-align: middle;
            color: var(--text-secondary) !important;
        }}
        table.dataTable tbody tr {{
            transition: background 0.15s;
        }}
        table.dataTable tbody tr:nth-child(odd) {{
            background: rgba(var(--primary-light-rgb),0.02);
        }}
        table.dataTable tbody tr:hover {{
            background: rgba(var(--primary-light-rgb),0.08) !important;
        }}
        /* ★★★ 表格列样式 ★★★ */
        .td-title {{ min-width: 220px; position: relative; }}
        .td-title.has-cover {{
            padding-right: 122px !important;
        }}
        .modpack-cover-thumb {{
            position: absolute !important;
            right: 2px;
            top: 50%;
            transform: translateY(-50%);
            width: 124px !important;
            height: 78px !important;
            aspect-ratio: 480 / 300 !important;
            padding: 0;
            border: 1px solid rgba(var(--primary-rgb), 0.20);
            border-radius: 18px;
            background: rgba(var(--glass-tint-rgb), 0.46);
            box-shadow: 0 12px 26px rgba(var(--shadow-rgb), 0.18);
            overflow: hidden;
            z-index: 2;
            cursor: zoom-in;
        }}
        .modpack-cover-thumb img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }}
        .modpack-cover-thumb:hover {{
            transform: translateY(-50%) scale(1.06);
            border-color: rgba(var(--primary-rgb), 0.45);
        }}
        .td-title .modpack-link {{
            color: var(--primary-light); text-decoration: none;
            font-weight: 600; transition: all 0.2s; cursor: pointer;
            display: flex; flex-direction: column; gap: 2px;
            padding: 2px 0 5px;
            line-height: 1.24;
            max-width: 100%;
        }}
        .modpack-title-cn {{
            color: var(--text);
            font-weight: 850;
            font-size: 0.9rem;
            white-space: normal;
        }}
        .modpack-title-en {{
            color: var(--text-muted);
            font-weight: 650;
            font-size: 0.74rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .modpack-type-badge {{
            display: inline-flex;
            align-items: center;
            width: fit-content;
            max-width: 100%;
            margin-top: 2px;
            padding: 1px 7px;
            border-radius: 999px;
            border: 1px solid rgba(var(--primary-rgb), 0.18);
            background: rgba(var(--primary-rgb), 0.08);
            color: var(--primary-dark);
            font-size: 0.68rem;
            font-weight: 850;
            text-decoration: none;
        }}
        a.modpack-type-badge:hover {{
            background: rgba(var(--primary-rgb), 0.16);
            color: var(--primary);
        }}
        .modpack-meta-row {{
            display: flex;
            align-items: center;
            gap: 6px;
            flex-wrap: wrap;
            margin-top: 1px;
        }}
        .modpack-views-badge {{
            display: inline-flex;
            align-items: center;
            width: fit-content;
            padding: 1px 7px;
            border-radius: 999px;
            border: 1px solid rgba(var(--secondary-rgb), 0.16);
            background: rgba(var(--secondary-rgb), 0.07);
            color: var(--text-muted);
            font-size: 0.68rem;
            font-weight: 850;
            white-space: nowrap;
        }}
        .td-title .modpack-link:hover {{
            color: var(--text); text-decoration: underline;
            text-underline-offset: 2px;
        }}
        .td-num {{
            text-align: right; font-variant-numeric: tabular-nums;
            font-weight: 500; white-space: nowrap;
            font-family: 'JetBrains Mono', monospace;
            color: var(--text-secondary) !important;
        }}
        .td-engage {{
            min-width: 132px;
            max-width: 150px;
            cursor: pointer;
        }}
        .engage-cell {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 4px;
            align-items: stretch;
        }}
        .engage-cell span {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-width: 0;
            padding: 3px 4px;
            border-radius: 7px;
            background: rgba(var(--primary-rgb), .055);
            border: 1px solid rgba(var(--primary-rgb), .10);
            position: relative;
        }}
        .engage-comment-trigger {{
            cursor: pointer;
            padding-right: 22px !important;
            background: linear-gradient(135deg, rgba(var(--primary-rgb), .12), rgba(var(--secondary-rgb), .08)) !important;
            border-color: rgba(var(--primary-rgb), .22) !important;
            outline: none;
            transition: transform .16s ease, border-color .16s ease, background .16s ease, box-shadow .16s ease;
        }}
        .engage-comment-trigger:hover,
        .engage-comment-trigger:focus-visible {{
            transform: translateY(-1px);
            border-color: rgba(var(--primary-rgb), .42) !important;
            background: linear-gradient(135deg, rgba(var(--primary-rgb), .18), rgba(var(--secondary-rgb), .12)) !important;
            box-shadow: 0 8px 18px rgba(var(--primary-rgb), .12);
        }}
        .comment-open-dot {{
            position: absolute;
            right: 4px;
            top: 50%;
            transform: translateY(-50%);
            width: 18px;
            height: 18px;
            border-radius: 999px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, var(--primary), var(--primary-light));
            color: #fff;
            font-size: 0.72rem;
            line-height: 1;
            font-style: normal;
            font-weight: 900;
            box-shadow: 0 5px 12px rgba(var(--primary-rgb), .26), inset 0 1px 0 rgba(255,255,255,.32);
        }}
        .engage-comment-trigger:hover .comment-open-dot,
        .engage-comment-trigger:focus-visible .comment-open-dot {{
            transform: translateY(-50%) scale(1.08);
        }}
        .engage-cell b {{
            color: var(--text);
            font-family: 'JetBrains Mono', monospace;
            font-size: .78rem;
            line-height: 1.05;
        }}
        .engage-cell em {{
            color: var(--text-muted);
            font-style: normal;
            font-size: .64rem;
            line-height: 1.1;
        }}
        .td-score {{ color: var(--success) !important; font-weight: 700; font-size: 0.92rem; }}
        .td-views {{ color: var(--secondary) !important; font-weight: 800; min-width: 86px; white-space: nowrap; }}
        .td-max {{ color: var(--coral) !important; font-weight: 600; }}
        .td-latest {{ color: var(--primary-light) !important; font-weight: 600; }}
        .td-avg {{ color: var(--text) !important; font-weight: 500; }}
        .td-days {{ color: var(--text-muted) !important; font-weight: 500; font-size: 0.78rem; }}
        .td-up {{ color: var(--success) !important; font-weight: 700; }}
        .td-down {{ color: var(--danger) !important; font-weight: 700; }}
        .td-flat {{ color: var(--text-muted) !important; font-weight: 500; }}
        .td-trend {{
            min-width: 190px;
            position: relative;
        }}
        .trend-consolidated-cell {{
            position: relative;
            display: flex;
            flex-direction: column;
            gap: 4px;
            min-height: 64px;
            justify-content: center;
            padding-top: 4px;
        }}
        .trend-score-badge {{
            position: absolute;
            left: 0;
            top: 0;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 2px 7px;
            border-radius: 999px;
            border: 1px solid rgba(var(--primary-rgb), 0.22);
            background: rgba(var(--primary-rgb), 0.10);
            color: var(--primary-dark);
            font-size: 0.66rem;
            font-weight: 850;
            line-height: 1.1;
            box-shadow: 0 6px 16px rgba(var(--primary-rgb), 0.08);
        }}
        .trend-score-badge span {{
            color: var(--text-muted);
            font-weight: 750;
        }}
        .trend-score-badge b {{
            color: var(--primary);
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.74rem;
        }}
        .trend-main-row {{
            display: grid;
            grid-template-columns: minmax(120px, 1fr) auto;
            align-items: center;
            gap: 10px;
            margin-top: 14px;
        }}
        .trend-val-lat {{
            align-self: end;
        }}
        .trend-open-hint {{
            grid-column: 2;
            justify-self: end;
            margin-top: -6px;
            padding: 1px 6px;
            border-radius: 999px;
            border: 1px solid rgba(var(--primary-rgb), .18);
            background: rgba(var(--primary-rgb), .08);
            color: var(--primary);
            font-size: 0.64rem;
            font-weight: 800;
            line-height: 1.35;
            white-space: nowrap;
        }}
        .td-trend:hover .trend-open-hint {{
            background: rgba(var(--primary-rgb), .16);
            border-color: rgba(var(--primary-rgb), .32);
        }}
        .sparkline-svg {{
            width: 100%;
            max-width: 150px;
            min-width: 118px;
            height: 42px;
            filter: drop-shadow(0 5px 10px rgba(var(--primary-rgb), .10));
            cursor: crosshair;
        }}
        .trend-inline-probe {{
            position: absolute;
            z-index: 20;
            min-width: 92px;
            padding: 5px 7px;
            border-radius: 9px;
            border: 1px solid rgba(var(--primary-rgb), 0.24);
            background: rgba(var(--glass-tint-rgb), 0.92);
            color: var(--text);
            box-shadow: 0 10px 24px rgba(var(--shadow-rgb), 0.16);
            font-size: 0.72rem;
            line-height: 1.25;
            pointer-events: none;
            backdrop-filter: blur(14px) saturate(150%);
            -webkit-backdrop-filter: blur(14px) saturate(150%);
        }}
        .trend-inline-probe b {{
            display: block;
            color: var(--primary);
            font-size: 0.78rem;
            font-family: 'JetBrains Mono', monospace;
        }}
        .trend-meta-row {{
            display: flex;
            justify-content: space-between;
            font-size: 0.72rem;
            color: var(--text-muted);
            gap: 8px;
            padding-left: 2px;
        }}
        .header-consolidated {{
            padding: 0.4rem 0.5rem !important;
            vertical-align: middle;
        }}
        .header-sort-switcher {{
            display: inline-flex;
            gap: 2px;
            background: rgba(var(--primary-rgb), 0.08);
            border: 1px solid rgba(var(--line-rgb), 0.15);
            border-radius: 6px;
            padding: 2px;
        }}
        .header-mode-title {{
            display: inline-flex;
            align-items: center;
            min-height: 24px;
            padding: 2px 7px;
            border-radius: 6px;
            background: rgba(var(--primary-rgb), 0.08);
            border: 1px solid rgba(var(--line-rgb), 0.15);
            color: var(--text);
            font-size: 0.72rem;
            font-weight: 800;
        }}
        .sort-option {{
            font-size: 0.7rem;
            padding: 2px 6px;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
            color: var(--text-secondary);
            font-weight: 600;
            user-select: none;
        }}
        .sort-option:hover {{
            background: rgba(var(--primary-rgb), 0.12);
            color: var(--text);
        }}
        .sort-option.active {{
            background: var(--primary);
            color: #fff !important;
            box-shadow: 0 2px 6px rgba(var(--primary-rgb), 0.25);
        }}
        /* 标签 */
        .tag-wrap {{
            display: flex; flex-wrap: wrap;
            gap: 6px 5px; align-content: flex-start;
            line-height: 1.5; max-height: 280px;
            overflow-y: auto; padding: 2px;
            scrollbar-width: thin; scrollbar-color: rgba(var(--primary-rgb),.3) transparent;
        }}
        .tag-wrap::-webkit-scrollbar {{ width: 4px; }}
        .tag-wrap::-webkit-scrollbar-thumb {{ background: rgba(var(--primary-rgb),.3); border-radius: 4px; }}
        .tag-combo-container {{
            max-height: none;
            min-width: 280px;
            overflow: visible;
            display: grid;
            gap: 8px;
        }}
        .tag-group {{
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }}
        .tag-group-block + .tag-group-block {{
            padding-top: 7px;
            border-top: 1px solid rgba(var(--line-rgb), .12);
        }}
        .tag-group-label {{
            display: flex;
            align-items: center;
            gap: 5px;
            margin: 0 0 4px;
            font-size: 0.68rem;
            font-weight: 800;
            color: var(--text-muted);
            letter-spacing: 0;
        }}
        .tag-group-label::before {{
            content: "";
            width: 5px;
            height: 5px;
            border-radius: 999px;
            background: var(--primary);
            box-shadow: 0 0 0 3px rgba(var(--primary-rgb), .10);
        }}
        .tag-group-label-pack::before {{
            background: var(--secondary);
            box-shadow: 0 0 0 3px rgba(var(--secondary-rgb), .10);
        }}
        .mod-container {{
            max-height: 420px;
            min-width: 0;
            width: 100%;
            display: block;
            padding-right: 4px;
        }}
        .mod-details {{
            display: block;
            width: 100%;
        }}
        .mod-details > summary {{
            list-style: none;
            cursor: pointer;
            display: grid;
            grid-template-columns: auto minmax(0, 1fr) auto;
            gap: 8px;
            align-items: center;
            padding: 5px 7px;
            border: 1px solid rgba(var(--primary-rgb), .18);
            border-radius: 8px;
            background: rgba(var(--primary-rgb), .06);
            user-select: none;
        }}
        .mod-details > summary::-webkit-details-marker {{
            display: none;
        }}
        .mod-details > summary::after {{
            content: "展开";
            justify-self: end;
            color: var(--primary-light);
            font-size: .68rem;
            font-weight: 800;
            padding-left: 6px;
        }}
        .mod-details[open] > summary::after {{
            content: "收起";
        }}
        .mod-summary-main {{
            white-space: nowrap;
            font-size: .78rem;
            font-weight: 800;
            color: var(--text);
        }}
        .mod-summary-main b {{
            color: var(--primary-light);
            font-family: 'JetBrains Mono', monospace;
        }}
        .mod-summary-cats {{
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            min-width: 0;
            max-height: 54px;
            overflow-y: auto;
        }}
        .mod-summary-chip {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            color: var(--text-secondary);
            background: rgba(var(--secondary-rgb), .08);
            border: 1px solid rgba(var(--secondary-rgb), .13);
            border-radius: 6px;
            padding: 1px 5px;
            font-size: .68rem;
            white-space: nowrap;
            cursor: pointer;
            font: inherit;
            line-height: 1.35;
            transition: all .16s ease;
        }}
        .mod-summary-chip:hover {{
            color: var(--primary-light);
            background: rgba(var(--primary-rgb), .14);
            border-color: rgba(var(--primary-rgb), .28);
        }}
        .mod-summary-chip b {{
            color: var(--primary-light);
            font-family: 'JetBrains Mono', monospace;
        }}
        .mod-details-body {{
            margin-top: 8px;
        }}
        .mod-category-section.jump-focus {{
            animation: modJumpFocus 1.25s ease;
        }}
        @keyframes modJumpFocus {{
            0%, 100% {{ box-shadow: none; }}
            18% {{ box-shadow: 0 0 0 2px rgba(var(--primary-rgb), .28), 0 12px 28px rgba(var(--primary-rgb), .18); }}
            55% {{ box-shadow: 0 0 0 1px rgba(var(--primary-rgb), .18), 0 8px 18px rgba(var(--primary-rgb), .12); }}
        }}
        .tag-cat {{
            position: relative;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            background: linear-gradient(135deg, rgba(var(--primary-light-rgb),.15), rgba(var(--primary-rgb),.05));
            color: var(--primary-light);
            border: 1px solid rgba(var(--primary-rgb),.25);
            border-radius: 7px; padding: 2px 7px;
            font-size: 0.8rem; font-weight: 600; white-space: nowrap;
            cursor: pointer;
            transition: all .2s ease;
        }}
        .tag-cat:hover {{
            background: linear-gradient(135deg, rgba(var(--primary-light-rgb),.25), rgba(var(--primary-rgb),.1));
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(var(--primary-rgb),.15);
        }}
        .tag-pack {{
            position: relative;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            background: rgba(var(--secondary-rgb),.06);
            color: var(--text-secondary);
            border: 1px solid rgba(var(--secondary-rgb),.15);
            border-radius: 7px; padding: 2px 7px;
            font-size: 0.78rem; font-weight: 500; white-space: nowrap;
            cursor: pointer;
            transition: all .2s ease;
        }}
        .tag-pack:hover {{
            background: rgba(var(--secondary-rgb),.12);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(var(--secondary-rgb),.15);
        }}
        .tag-filter-name {{
            pointer-events: none;
        }}
        .tag-filter-open {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 17px;
            height: 17px;
            border-radius: 5px;
            border: 1px solid rgba(var(--line-rgb), .14);
            background: rgba(var(--glass-tint-rgb), .42);
            color: var(--text-secondary) !important;
            text-decoration: none;
            font-size: .66rem;
            font-weight: 850;
            opacity: .78;
        }}
        .tag-filter-open:hover {{
            opacity: 1;
            background: rgba(var(--primary-rgb), .18);
            color: var(--primary-dark) !important;
        }}
        .tag-mod {{
            position: relative;
            display: inline-flex;
            flex-direction: column;
            align-items: flex-start;
            gap: 1px;
            background: rgba(var(--primary-rgb),.055);
            color: var(--text);
            border: 1px solid rgba(var(--primary-rgb),.12);
            border-radius: 7px; padding: 4px 28px 4px 7px;
            font-size: 0.75rem; font-weight: 550;
            min-width: 0;
            text-decoration: none;
            transition: all .2s ease;
            cursor: pointer;
        }}
        .tag-mod:hover {{
            background: rgba(var(--primary-rgb),.16);
            color: var(--primary-light);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(var(--primary-rgb),.14);
        }}
        .tag-mod.active-tag {{
            background: rgba(var(--secondary-rgb),.18);
            border-color: rgba(var(--secondary-rgb),.42);
            color: var(--secondary);
            box-shadow: 0 0 0 2px rgba(var(--secondary-rgb),.10);
        }}
        .tag-mod-name {{
            padding-right: 2px;
        }}
        .tag-mod-open {{
            position: absolute;
            top: 4px;
            right: 4px;
            width: 20px;
            height: 20px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 6px;
            border: 1px solid rgba(var(--line-rgb), .14);
            background: rgba(var(--glass-tint-rgb), .46);
            color: var(--text-secondary) !important;
            text-decoration: none;
            font-size: .72rem;
            font-weight: 850;
            opacity: .78;
            transition: all .16s ease;
        }}
        .tag-mod-open:hover {{
            opacity: 1;
            background: rgba(var(--primary-rgb), .18);
            color: var(--primary-dark) !important;
            transform: translateY(-1px);
        }}
        .tag-mod-version {{
            color: var(--text-muted);
            font-size: 0.66rem;
            font-family: 'JetBrains Mono', monospace;
            line-height: 1.15;
        }}
        .mod-category-section {{
            margin: 0 0 9px 0;
        }}
        .mod-category-section:last-child {{
            margin-bottom: 0;
        }}
        .mod-category-head {{
            display: inline-flex;
            align-items: center;
            gap: 7px;
            margin: 0 0 5px 0;
            padding: 2px 8px;
            border-radius: 7px;
            color: #fff;
            background: linear-gradient(135deg, rgba(var(--primary-rgb), .9), rgba(var(--secondary-rgb), .72));
            box-shadow: 0 4px 14px rgba(var(--primary-rgb), .14);
            font-size: 0.72rem;
            font-weight: 750;
        }}
        .mod-category-head a {{
            color: #fff;
            text-decoration: none;
        }}
        .mod-category-head span:last-child {{
            opacity: .78;
            font-family: 'JetBrains Mono', monospace;
            font-size: .66rem;
        }}
        .mod-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 5px 7px;
        }}
        .tag-empty {{
            color: var(--text-muted); font-size: 0.78rem; opacity: 0.5;
        }}
        /* 按钮 */
        .mod-details > summary {{
            width: 100%;
            grid-template-columns: auto minmax(0, 1fr) 26px !important;
            gap: 10px !important;
            padding: 7px 9px !important;
            min-height: 38px;
            border-radius: 12px !important;
            background:
                linear-gradient(135deg, rgba(var(--glass-tint-rgb), .58), rgba(var(--glass-tint2-rgb), .30)),
                rgba(var(--primary-rgb), .045) !important;
            border-color: rgba(var(--primary-rgb), .20) !important;
            box-shadow: 0 8px 20px rgba(var(--shadow-rgb), .08), inset 0 1px 0 rgba(255,255,255,.16);
            backdrop-filter: blur(14px) saturate(145%);
            -webkit-backdrop-filter: blur(14px) saturate(145%);
        }}
        .mod-details > summary::after {{
            content: "⌄" !important;
            width: 26px;
            height: 26px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 999px;
            background: rgba(var(--primary-rgb), .12);
            border: 1px solid rgba(var(--primary-rgb), .20);
            padding: 0 !important;
            font-size: .9rem !important;
        }}
        .mod-details[open] > summary::after {{
            content: "⌃" !important;
        }}
        .mod-summary-cats {{
            justify-content: flex-end;
            max-height: 28px !important;
            overflow: hidden !important;
            min-width: 0;
        }}
        .mod-details[open] .mod-summary-cats {{
            justify-content: flex-start;
            max-height: 52px !important;
        }}
        .mod-details-body {{
            margin-top: 6px !important;
        }}
        .mod-grid {{
            grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
            gap: 5px 8px !important;
            align-items: stretch;
        }}
        .tag-mod {{
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            min-height: 28px;
            padding: 4px 30px 4px 8px !important;
            border-radius: 6px !important;
            background: rgba(var(--glass-tint-rgb), .34) !important;
            border: 1px solid rgba(var(--line-rgb), .12) !important;
            box-shadow: none !important;
        }}
        .tag-mod:hover {{
            background: rgba(var(--primary-rgb), .09) !important;
            box-shadow: 0 4px 12px rgba(var(--shadow-rgb), .08) !important;
        }}
        .tag-mod-name {{
            display: block;
            min-width: 0;
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            padding-right: 0 !important;
        }}
        .tag-mod-version {{
            flex: 0 0 auto;
            margin-left: 4px;
            white-space: nowrap;
        }}
        .tag-mod-open {{
            position: absolute !important;
            top: 50% !important;
            right: 4px !important;
            transform: translateY(-50%) !important;
            width: 20px !important;
            height: 20px !important;
        }}
        .tag-mod-open:hover {{
            transform: translateY(-50%) scale(1.05) !important;
        }}
        .btn-reset {{
            background: var(--glass-bg);
            backdrop-filter: blur(10px);
            border: 1px solid var(--glass-border);
            color: var(--text-secondary); font-weight: 700;
            padding: 0.6rem 1.4rem; border-radius: 10px;
            transition: all 0.2s; cursor: pointer; white-space: nowrap;
        }}
        .btn-reset:hover {{
            background: var(--primary); color: #fff; border-color: var(--primary);
            box-shadow: 0 8px 24px rgba(var(--primary-rgb),.25);
        }}
        /* Select2 玻璃态 */
        .select2-container--bootstrap-5 .select2-selection {{
            border-radius: 16px !important;
            background:
                linear-gradient(135deg, rgba(var(--glass-tint-rgb), 0.72), rgba(var(--glass-tint2-rgb), 0.42)),
                rgba(var(--glass-tint-rgb), 0.28) !important;
            border: 1px solid rgba(var(--primary-rgb), 0.22) !important;
            color: var(--text) !important;
            min-height: 40px;
            box-shadow: 0 10px 28px rgba(var(--shadow-rgb), 0.08), inset 0 1px 0 rgba(255,255,255,.18) !important;
            backdrop-filter: blur(22px) saturate(165%);
            -webkit-backdrop-filter: blur(22px) saturate(165%);
            transition: border-color .18s ease, box-shadow .18s ease, background .18s ease;
        }}
        .select2-container--bootstrap-5.select2-container--focus .select2-selection,
        .select2-container--bootstrap-5.select2-container--open .select2-selection {{
            border-color: rgba(var(--primary-rgb), 0.56) !important;
            box-shadow: 0 0 0 4px rgba(var(--primary-rgb), 0.14), 0 14px 36px rgba(var(--shadow-rgb), 0.14) !important;
        }}
        .select2-container--bootstrap-5 .select2-selection--multiple {{
            max-height: 98px;
            overflow-y: auto;
            padding: 3px 8px !important;
        }}
        .select2-container--bootstrap-5 .select2-selection--multiple .select2-selection__choice {{
            background: linear-gradient(135deg, rgba(var(--primary-rgb), .92), rgba(var(--secondary-rgb), .76)) !important;
            border: 1px solid rgba(255,255,255,.24) !important;
            color: #fff !important;
            border-radius: 999px !important;
            box-shadow: 0 6px 16px rgba(var(--primary-rgb), .18);
            font-weight: 800;
        }}
        .select2-container--bootstrap-5 .select2-selection--single .select2-selection__rendered {{
            line-height: 38px; color: var(--text) !important; font-weight: 750;
        }}
        .select2-container--bootstrap-5 .select2-results__option {{
            color: var(--text) !important;
            font-weight: 700;
            padding: 8px 12px !important;
        }}
        .select2-dropdown {{
            background: rgba(var(--glass-tint-rgb), 0.86) !important;
            backdrop-filter: blur(28px) saturate(180%);
            -webkit-backdrop-filter: blur(28px) saturate(180%);
            border: 1px solid rgba(var(--primary-rgb), 0.25) !important;
            border-radius: 16px !important;
            overflow: hidden;
            box-shadow: 0 18px 46px rgba(var(--shadow-rgb), .18);
        }}
        .select2-container--bootstrap-5 .select2-results__option--selected {{
            background: rgba(var(--primary-rgb),.14) !important;
        }}
        .select2-container--bootstrap-5 .select2-results__option--highlighted {{
            background: linear-gradient(135deg, rgba(var(--primary-rgb),.86), rgba(var(--secondary-rgb),.72)) !important; color: #fff !important;
        }}
        /* DataTables 控件 */
        .dataTables_wrapper {{
            background: transparent !important;
        }}
        .dataTables_wrapper > div {{
            background: transparent !important;
            padding: 0 !important;
        }}
        .dataTables_wrapper > .row:not(.dt-row) {{
            padding: 0.5rem 0 !important;
        }}
        .dataTables_wrapper .dataTables_scroll {{
            background: transparent !important;
            padding: 0 !important;
            margin: 0 !important;
        }}
        .dataTables_wrapper .dataTables_scrollHead {{
            background: transparent !important;
            border-bottom: none !important;
            padding-bottom: 0 !important;
        }}
        .dataTables_wrapper .dataTables_scrollBody {{
            background: transparent !important;
            border: none !important;
            padding-top: 0 !important;
            margin-top: 0 !important;
        }}
        .dataTables_wrapper .dataTables_scrollBody thead,
        .dataTables_wrapper .dataTables_scrollBody thead tr,
        .dataTables_wrapper .dataTables_scrollBody thead th {{
            height: 0 !important;
            max-height: 0 !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            border: 0 !important;
            line-height: 0 !important;
            overflow: hidden !important;
            visibility: collapse !important;
        }}
        .dataTables_wrapper .dataTables_scrollHead table.dataTable thead th {{
            background: linear-gradient(135deg, var(--th-bg-1), var(--th-bg-2)) !important;
        }}
        .dataTables_wrapper .dataTables_processing {{
            background: transparent !important;
            color: var(--text-secondary) !important;
        }}
        .dataTables_wrapper .dataTables_filter,
        .dataTables_wrapper .dataTables_info,
        .dataTables_wrapper .dataTables_paginate {{
            font-size: 0.82rem; color: var(--text-secondary);
            margin: 0.4rem 0;
        }}
        .dataTables_wrapper .dataTables_filter label,
        .dataTables_wrapper .dataTables_info,
        .dataTables_wrapper .dataTables_paginate {{
            color: var(--text-secondary) !important;
        }}
        .dataTables_wrapper .dataTables_length {{
            display: inline-block !important;
            color: var(--text-secondary) !important;
            font-size: 0.82rem;
            vertical-align: middle;
        }}
        .dataTables_wrapper .dataTables_length select {{
            background: var(--glass-bg-solid) !important;
            color: var(--text) !important;
            border: 1px solid var(--glass-border) !important;
            border-radius: 8px !important;
            padding: 4px 10px !important;
            margin: 0 4px !important;
            font-size: 0.82rem;
            cursor: pointer;
        }}
        .dataTables_wrapper .dataTables_length select option {{
            background: var(--glass-bg-solid) !important;
            color: var(--text) !important;
        }}
        .dataTables_wrapper .dataTables_filter input {{
            min-width: 250px;
            padding: 0.42rem 0.78rem;
            margin-left: 0.45rem;
        }}
        .dataTables_wrapper .dataTables_filter input:focus {{
            border-color: var(--primary-light);
            box-shadow: 0 0 0 .2rem rgba(var(--primary-light-rgb),.15);
            outline: none;
        }}
        .dataTables_wrapper .dataTables_filter input::placeholder {{ color: var(--text-muted); }}
        .dataTables_wrapper .dataTables_filter label {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 7px;
            border-radius: 22px;
            background: rgba(var(--glass-tint-rgb), 0.22);
            border: 1px solid rgba(var(--primary-rgb), 0.10);
            box-shadow: inset 0 1px 0 rgba(255,255,255,.12);
            backdrop-filter: blur(18px) saturate(150%);
            -webkit-backdrop-filter: blur(18px) saturate(150%);
        }}
        #searchScope {{
            width: auto !important;
            min-width: 190px;
            padding: 0.42rem 2.25rem 0.42rem 0.78rem !important;
            margin-right: 0 !important;
        }}
        /* 分页按钮 */
        .dataTables_wrapper .dataTables_paginate .paginate_button {{
            background: var(--glass-bg-solid) !important;
            border: 1px solid var(--glass-border) !important;
            border-radius: 8px !important;
            color: var(--text-secondary) !important;
            margin: 0 2px !important; padding: 4px 12px !important;
        }}
        .dataTables_wrapper .dataTables_paginate .paginate_button.current,
        .dataTables_wrapper .dataTables_paginate .paginate_button.current:hover {{
            background: var(--primary) !important;
            border-color: var(--primary) !important;
            color: #fff !important;
        }}
        .dataTables_wrapper .dataTables_paginate .paginate_button:hover {{
            background: var(--glass-hover) !important;
            border-color: var(--primary-light) !important;
            color: var(--text) !important;
        }}
        .dataTables_wrapper .dataTables_paginate {{
            display: inline-flex !important;
            align-items: center;
            justify-content: center;
            gap: 7px;
            padding: 9px 10px;
            border-radius: 999px;
            background:
                linear-gradient(135deg, rgba(var(--glass-tint-rgb), 0.70), rgba(var(--glass-tint2-rgb), 0.34)),
                rgba(var(--glass-tint-rgb), 0.22);
            border: 1px solid rgba(var(--primary-rgb), 0.18);
            box-shadow: 0 18px 44px rgba(var(--shadow-rgb), 0.14), inset 0 1px 0 rgba(255,255,255,.22);
            backdrop-filter: blur(28px) saturate(180%);
            -webkit-backdrop-filter: blur(28px) saturate(180%);
            overflow: hidden;
        }}
        .dataTables_wrapper .dataTables_paginate .paginate_button {{
            display: inline-flex !important;
            align-items: center;
            justify-content: center;
            background: rgba(var(--glass-tint-rgb), 0.36) !important;
            border: 1px solid rgba(var(--line-rgb), 0.12) !important;
            border-radius: 999px !important;
            margin: 0 !important;
            padding: 0 !important;
            min-width: 38px;
            height: 38px;
            color: var(--text-secondary) !important;
            font-weight: 900;
            line-height: 1 !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.16);
            transition: transform .16s ease, background .16s ease, border-color .16s ease, box-shadow .16s ease, color .16s ease;
        }}
        .dataTables_wrapper .dataTables_paginate .paginate_button.current,
        .dataTables_wrapper .dataTables_paginate .paginate_button.current:hover {{
            background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
            border-color: rgba(var(--primary-rgb), 0.50) !important;
            color: #fff !important;
            box-shadow: 0 10px 24px rgba(var(--primary-rgb), 0.30), inset 0 1px 0 rgba(255,255,255,.26);
        }}
        .dataTables_wrapper .dataTables_paginate .paginate_button:hover {{
            transform: translateY(-1px);
            background: rgba(var(--primary-rgb), 0.16) !important;
            border-color: rgba(var(--primary-rgb), 0.30) !important;
            color: var(--text) !important;
            box-shadow: 0 9px 20px rgba(var(--shadow-rgb), 0.12), inset 0 1px 0 rgba(255,255,255,.20);
        }}
        .dataTables_wrapper .dataTables_paginate .paginate_button.disabled,
        .dataTables_wrapper .dataTables_paginate .paginate_button.disabled:hover {{
            opacity: .42;
            background: transparent !important;
            border-color: transparent !important;
            color: var(--text-muted) !important;
            box-shadow: none !important;
        }}
/* ───── 整合包介绍预览窗（优雅雾化淡入淡出版） ───── */
        .pv-popup {{
            position: fixed; z-index: 99999;
            width: 700px;
            height: 650px;
            max-height: calc(100vh - 40px); max-width: calc(100vw - 24px);
            background: var(--glass-bg-solid);
            border: 2px solid var(--primary);
            border-radius: var(--radius);
            box-shadow: 0 28px 75px rgba(var(--shadow-rgb), 0.35), 0 0 40px rgba(var(--primary-rgb), 0.1);
            overflow: hidden;
            opacity: 0;
            transform: scale(0.9) translateY(12px);
            backdrop-filter: blur(0px) saturate(100%);
            -webkit-backdrop-filter: blur(0px) saturate(100%);
            pointer-events: none;
            display: flex; flex-direction: column;
            transition: opacity .25s cubic-bezier(0.34, 1.56, 0.64, 1), 
                        transform .25s cubic-bezier(0.34, 1.56, 0.64, 1),
                        backdrop-filter .25s ease,
                        -webkit-backdrop-filter .25s ease;
        }}
        .pv-popup.show {{
            opacity: 1;
            transform: scale(1) translateY(0);
            backdrop-filter: blur(28px) saturate(160%) contrast(112%);
            -webkit-backdrop-filter: blur(28px) saturate(160%) contrast(112%);
            pointer-events: auto;
        }}
        .pv-head {{
            display: flex; align-items: center; justify-content: space-between;
            background: linear-gradient(135deg, var(--primary-dark), var(--primary));
            padding: 0.8rem 1.2rem; gap: 0.5rem; flex-shrink: 0;
        }}
        .pv-head-icon {{
            width: 36px; height: 36px; border-radius: 10px;
            background: rgba(255,255,255,.2);
            display: flex; align-items: center; justify-content: center;
            font-size: 1.1rem; flex-shrink: 0;
        }}
        .pv-head-title {{
            flex: 1; overflow: hidden; text-overflow: ellipsis;
            white-space: nowrap; color: #fff; font-weight: 700; font-size: 0.95rem;
            letter-spacing: 0.5px;
        }}
        .pv-actions {{ display: flex; gap: 0.4rem; flex-shrink: 0; }}
        .pv-actions a, .pv-actions span, .pv-actions button {{
            display: inline-flex; align-items: center; justify-content: center;
            width: 28px; height: 28px; border-radius: 7px;
            border: 0;
            background: rgba(255,255,255,.2); color: #fff;
            cursor: pointer; font-size: 0.85rem;
            transition: background 0.15s; text-decoration: none;
        }}
        .pv-actions a:hover, .pv-actions span:hover, .pv-actions button:hover {{ background: rgba(255,255,255,.4); }}
        .pv-body {{
            padding: 1.2rem 1.5rem; overflow-y: auto; flex: 1;
            font-size: 0.95rem; line-height: 1.75;
            color: var(--text) !important;
            word-break: break-word;
        }}
        .pv-para {{
            margin-bottom: 0.6rem;
            line-height: 1.7;
            color: var(--text-main);
            text-align: justify;
        }}
        .intro-blockquote {{
            border-left: 4px solid var(--primary);
            padding: 0.6rem 1rem;
            margin: 0.8rem 0;
            background: rgba(180, 140, 100, 0.08);
            border-radius: 0 4px 4px 0;
            color: var(--text-main);
            font-size: 0.92rem;
            line-height: 1.6;
        }}
        [data-theme="dark"] .intro-blockquote {{
            background: rgba(220, 180, 120, 0.08);
        }}
        .intro-p {{
            margin-bottom: 0.8rem;
            text-align: justify;
        }}
        .pv-section-title {{
            font-weight: 700; font-size: 1.05rem; color: var(--primary);
            margin: 1.2rem 0 0.6rem 0; padding-left: 0.8rem;
            position: relative;
        }}
        .pv-section-title::before {{
            content: ""; position: absolute; left: 0; top: 0.15rem; bottom: 0.15rem;
            width: 4px; background: var(--primary); border-radius: 2px;
        }}
        .pv-list-item {{
            margin-bottom: 0.4rem; padding-left: 1.5rem;
            position: relative; line-height: 1.6;
            color: var(--text-main);
        }}
        .pv-list-item::before {{
            content: "•"; position: absolute; left: 0.5rem; color: var(--primary);
            font-weight: bold; font-size: 1.2rem; line-height: 1.2;
        }}
        .pv-body::-webkit-scrollbar {{ width: 6px; }}
        .pv-body::-webkit-scrollbar-thumb {{ background: rgba(var(--primary-rgb),.3); border-radius: 3px; }}
        .pv-body-empty {{ text-align: center; padding: 2.5rem; color: var(--text-muted); }}
        .pv-body-empty a {{
            display: inline-block; margin-top: 0.5rem; padding: 0.4rem 1rem;
            background: var(--primary); color: #fff; border-radius: 8px;
            text-decoration: none; font-size: 0.85rem;
        }}
        .pv-tip {{
            padding: 0.5rem 1.2rem; background: var(--bg-gradient-2);
            font-size: 0.75rem; color: var(--text-muted);
            border-top: 1px solid var(--border); flex-shrink: 0;
        }}
        .mcmod-consent {{
            position: absolute;
            left: 0; right: 0; bottom: 0; top: auto;
            height: auto;
            z-index: 30;
            display: none;
            padding: 0;
            background: transparent !important;
            backdrop-filter: none !important;
            -webkit-backdrop-filter: none !important;
        }}
        .pv-popup.needs-consent .mcmod-consent,
        .comment-popup.needs-consent .mcmod-consent {{
            display: block;
        }}
        .mcmod-consent-panel {{
            width: 100% !important;
            max-width: 100% !important;
            border: none !important;
            border-top: 1px solid var(--glass-border) !important;
            border-radius: 0 0 var(--radius) var(--radius) !important;
            padding: 1rem 1.25rem;
            background: rgba(var(--glass-tint-rgb), 0.85) !important;
            backdrop-filter: blur(20px) saturate(160%) !important;
            -webkit-backdrop-filter: blur(20px) saturate(160%) !important;
            box-shadow: 0 -10px 30px rgba(var(--shadow-rgb), 0.15) !important;
            text-align: center;
            transform: translateY(100%);
            animation: consentSlideUp 0.35s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
        }}
        @keyframes consentSlideUp {{
            to {{ transform: translateY(0); }}
        }}
        .pv-popup.needs-consent .mcmod-consent,
        .comment-popup.needs-consent .mcmod-consent {{
            display: flex;
        }}
        .mcmod-consent-panel {{
            width: min(420px, 92%);
            border: 1px solid rgba(var(--primary-rgb), 0.35);
            border-radius: 18px;
            padding: 1.2rem 1.25rem;
            background: rgba(var(--glass-tint-rgb), 0.76);
            box-shadow: 0 18px 44px rgba(var(--shadow-rgb), 0.24);
            text-align: center;
        }}
        .mcmod-consent-brand {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 128px;
            height: 42px;
            padding: 0 16px;
            border-radius: 10px;
            background: linear-gradient(135deg, var(--primary-dark), var(--primary));
            color: #fff;
            font-weight: 800;
            letter-spacing: 0.02em;
            margin-bottom: 0.9rem;
            box-shadow: 0 10px 24px rgba(var(--primary-rgb), 0.28);
        }}
        .mcmod-consent-title {{
            font-size: 1rem;
            font-weight: 800;
            color: var(--text);
            margin-bottom: 0.45rem;
        }}
        .mcmod-consent-text {{
            color: var(--text-secondary);
            font-size: 0.86rem;
            line-height: 1.65;
            margin-bottom: 1rem;
        }}
        .mcmod-consent-ok {{
            border: 0;
            border-radius: 10px;
            background: var(--primary);
            color: #fff;
            padding: 0.55rem 1.2rem;
            font-size: 0.9rem;
            font-weight: 800;
            cursor: pointer;
            box-shadow: 0 8px 20px rgba(var(--primary-rgb), 0.28);
        }}
        .mcmod-consent-ok:hover {{
            background: var(--primary-dark);
        }}
        /* ───── 迷你走势悬浮窗（微缩 ECharts 风格 SVG 版） ───── */
        .trend-tooltip {{
            position: fixed; z-index: 100000;
            width: 320px; padding: 12px;
            background: var(--glass-bg-solid);
            border: 2px solid var(--primary);
            border-radius: var(--radius-sm);
            box-shadow: 0 16px 45px rgba(var(--shadow-rgb), 0.4);
            pointer-events: auto;
            display: flex; flex-direction: column; gap: 8px;
            opacity: 0; 
            transform: scale(0.9) translateY(8px);
            backdrop-filter: blur(0px) saturate(100%);
            -webkit-backdrop-filter: blur(0px) saturate(100%);
            transition: opacity 0.25s cubic-bezier(0.34, 1.56, 0.64, 1),
                        transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1),
                        backdrop-filter 0.25s ease,
                        -webkit-backdrop-filter 0.25s ease;
        }}
        .trend-tooltip.show {{
            opacity: 1; 
            transform: scale(1) translateY(0);
            backdrop-filter: blur(28px) saturate(160%) contrast(112%);
            -webkit-backdrop-filter: blur(28px) saturate(160%) contrast(112%);
        }}
        .trend-tooltip.hiding,
        .comment-popup.hiding,
        .pv-popup.hiding {{
            opacity: 0 !important;
            transform: scale(0.98) translateY(8px) !important;
            pointer-events: none !important;
        }}
        .trend-hover-bridge {{
            position: fixed;
            z-index: 99999;
            display: none;
            background: rgba(0, 0, 0, 0.001);
            pointer-events: auto;
        }}
        .trend-tooltip-title {{
            font-size: 0.9rem; font-weight: 700; color: var(--text);
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
            padding-right: 28px;
        }}
        .hover-close {{
            width: 26px;
            height: 26px;
            border: 0;
            border-radius: 999px;
            display: inline-grid;
            place-items: center;
            background: rgba(var(--primary-rgb), .12);
            color: var(--primary-dark);
            font-weight: 900;
            cursor: pointer;
            line-height: 1;
            transition: background .16s ease, transform .16s ease;
        }}
        .hover-close:hover {{
            background: rgba(var(--primary-rgb), .22);
            transform: translateY(-1px);
        }}
        .trend-tooltip .hover-close {{
            position: absolute;
            right: 8px;
            top: 8px;
        }}
        .hover-cooldown-tip {{
            font-size: 0.68rem;
            color: var(--text-muted);
            line-height: 1.35;
        }}
        .trend-tooltip-subtitle {{
            font-size: 0.72rem; color: var(--text-secondary);
        }}
        .trend-tooltip-chart-container {{
            width: 100%; height: 130px; position: relative;
        }}
        .trend-tooltip-footer {{
            display: flex; justify-content: space-between; font-size: 0.72rem; color: var(--text-secondary);
            border-top: 1px solid var(--glass-border); padding-top: 6px;
        }}
        .trend-tooltip-footer span {{
            font-weight: 600; color: var(--text);
        }}
        /* ───── 评论悬浮窗（加高 + 优雅雾化淡入淡出版） ───── */
        .comment-popup {{
            position: fixed; z-index: 99999;
            width: 580px;
            height: min(720px, calc(100vh - 48px));
            max-height: min(720px, calc(100vh - 48px)); max-width: calc(100vw - 24px);
            background: var(--glass-bg-solid);
            border: 2px solid var(--primary);
            border-radius: var(--radius-sm);
            box-shadow: 0 28px 75px rgba(var(--shadow-rgb), 0.35);
            overflow: hidden;
            opacity: 0;
            transform: scale(0.9) translateY(12px);
            backdrop-filter: blur(0px) saturate(100%);
            -webkit-backdrop-filter: blur(0px) saturate(100%);
            pointer-events: none;
            display: flex; flex-direction: column;
            transition: opacity .25s cubic-bezier(0.34, 1.56, 0.64, 1), 
                        transform .25s cubic-bezier(0.34, 1.56, 0.64, 1),
                        backdrop-filter .25s ease,
                        -webkit-backdrop-filter .25s ease;
        }}
        .comment-popup.show {{
            opacity: 1; 
            transform: scale(1) translateY(0);
            backdrop-filter: blur(28px) saturate(160%) contrast(112%);
            -webkit-backdrop-filter: blur(28px) saturate(160%) contrast(112%);
            pointer-events: auto;
        }}
        .comment-head {{
            display: flex; align-items: center; justify-content: space-between; gap: 0.5rem;
            background: linear-gradient(135deg, var(--primary-dark), var(--primary));
            padding: 0.6rem 1rem; color: #fff; font-size: 0.9rem; font-weight: 700;
        }}
        .comment-head-icon {{
            width: 36px; height: 36px; border-radius: 10px;
            background: rgba(255,255,255,.2);
            display: flex; align-items: center; justify-content: center;
            font-size: 1.1rem; flex-shrink: 0;
        }}
        .comment-head-title {{
            flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis;
            white-space: nowrap; color: #fff; font-weight: 700; font-size: 0.95rem;
            letter-spacing: 0.5px;
        }}
        .comment-head #commentCount {{
            flex-shrink: 0;
            color: inherit;
            font-size: 0.84rem;
        }}
        .comment-search-input {{
            width: min(260px, 35vw); height: 32px; padding: 0 10px;
            border: 2px solid rgba(255,255,255,.82); border-radius: 10px;
            background: rgba(255,255,255,.96); color: #1b3445;
            outline: none; font: inherit; font-size: 0.8rem; font-weight: 500;
        }}
        .comment-search-input::placeholder {{ color: #6c8290; }}
        .comment-search-input:focus {{ border-color: #fff; box-shadow: 0 0 0 3px rgba(255,255,255,.24); }}
        .comment-body {{
            padding: 0.8rem 1.2rem 0.8rem 0.8rem; /* 右边距稍微加大，给滚动条留出安全视觉空间 */
            overflow-y: auto; flex: 1 1 auto; min-height: 0; background: transparent;
            overscroll-behavior: contain;
            position: relative;
        }}
        mark.comment-highlight {{
            background: linear-gradient(135deg, rgba(var(--primary-rgb), 0.28), rgba(var(--secondary-rgb), 0.18)) !important;
            color: var(--text) !important;
            border: 1px solid rgba(var(--primary-rgb), 0.34);
            border-radius: 6px;
            padding: 0 4px;
            font-weight: 850;
            box-shadow: 0 0 0 2px rgba(var(--primary-rgb), 0.07), 0 6px 16px rgba(var(--primary-rgb), 0.12);
        }}
        .search-nav {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            margin-left: 0.55rem;
            padding: 0.18rem 0.25rem 0.18rem 0.55rem;
            border: 1px solid rgba(var(--primary-rgb), 0.18);
            border-radius: 999px;
            background: rgba(var(--glass-tint-rgb), 0.52);
            color: var(--text-secondary);
            vertical-align: middle;
            box-shadow: 0 8px 20px rgba(var(--shadow-rgb), 0.08);
        }}
        .search-nav-info {{
            min-width: 4.4rem;
            font-size: 0.75rem;
            font-weight: 750;
            text-align: center;
            color: var(--text-secondary);
        }}
        .search-nav-btn {{
            width: 26px;
            height: 26px;
            border: 0;
            border-radius: 999px;
            background: rgba(var(--primary-rgb), 0.12);
            color: var(--primary-dark);
            font-weight: 900;
            line-height: 1;
            cursor: pointer;
            transition: transform .16s ease, background .16s ease, opacity .16s ease;
        }}
        .search-nav-btn:hover {{
            transform: translateY(-1px);
            background: rgba(var(--primary-rgb), 0.22);
        }}
        .search-nav-btn:disabled {{
            opacity: 0.38;
            cursor: default;
            transform: none;
        }}
        table.dataTable tbody tr.search-hit-row > td {{
            box-shadow: inset 3px 0 0 rgba(var(--primary-rgb), 0.5);
        }}
        table.dataTable tbody tr.search-current-row > td {{
            background: linear-gradient(90deg, rgba(var(--primary-rgb), 0.16), rgba(var(--secondary-rgb), 0.08)) !important;
            box-shadow: inset 3px 0 0 var(--primary), inset 0 0 0 999px rgba(var(--primary-rgb), 0.035);
        }}
        /* ───── 滚动条终极视觉高亮（常驻轨道版） ───── */
        /* 1. 宽度锁定 8px */
        .comment-body::-webkit-scrollbar {{
            width: 8px;
        }}
        /* 2. 核心改动：让轨道常驻可见，使用微弱的主题反差色，像一条“滑道”一样标示出来 */
        .comment-body::-webkit-scrollbar-track {{
            background: rgba(var(--primary-rgb), 0.08);
            border-radius: 4px;
            margin: 4px 0;
        }}
        /* 3. 滑块本体：不再使用高透明度，直接给到 0.55 的基础不透明度，确保一眼看得见 */
        .comment-body::-webkit-scrollbar-thumb {{
            background: rgba(var(--primary-rgb), 0.55);
            border-radius: 20px;
            border: 1px solid transparent;
        }}
        /* 4. 鼠标悬停或拖拽时，颜色直接拉满到接近纯色 */
        .comment-body::-webkit-scrollbar-thumb:hover {{
            background: rgba(var(--primary-rgb), 0.9);
            box-shadow: 0 0 8px rgba(var(--primary-rgb), 0.5);
        }}
        /* ───── 新增：底部滑动提示器动画 ───── */
        .scroll-hint-arrow {{
            position: absolute;
            bottom: 55px; /* 定位在分页栏上方一点点 */
            right: 20px;
            background: var(--primary);
            color: #fff !important;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.72rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 4px;
            pointer-events: none; /* 穿透鼠标，不干扰点击 */
            box-shadow: 0 4px 10px rgba(var(--primary-rgb), 0.3);
            opacity: 0;
            transform: translateY(5px);
            transition: opacity 0.3s, transform 0.3s;
            z-index: 10;
            animation: hintBounce 1.6s infinite ease-in-out; /* 呼吸浮动动画 */
        }}
        /* 只有当内容溢出、需要滚动时，通过 JS 给 comment-popup 加上 .has-overflow 类名才显示 */
        .comment-popup.has-overflow .scroll-hint-arrow {{
            opacity: 0.85;
            transform: translateY(0);
        }}
        /* 浮动微动动画 */
        @keyframes hintBounce {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-4px); }}
        }}
        /* ──────────────────────────────────────────────────────── */
        .comment-floor {{
            border-bottom: 1px solid var(--border); padding: 0.8rem 0.4rem;
            background: rgba(var(--primary-light-rgb), 0.02);
        }}
        .comment-floor:last-child {{ border-bottom: none; }}
        .comment-floor-head {{
            font-size: 0.82rem; color: var(--primary-dark); font-weight: 700;
            margin-bottom: 0.3rem; display: flex; gap: 0.5rem; align-items: center; justify-content: space-between;
        }}
        .comment-floor-main {{
            min-width: 0; display: inline-flex; gap: 0.5rem; align-items: center; flex-wrap: wrap;
        }}
        .comment-floor-head .floor-num {{
            background: var(--primary); color: #fff; padding: 1px 7px; border-radius: 4px; font-size: 0.72rem; font-weight: 600;
        }}
        .comment-floor-link, .comment-reply-link {{
            display: inline-flex; align-items: center; justify-content: center;
            width: 24px; height: 24px; border-radius: 7px;
            border: 1px solid rgba(var(--line-rgb), 0.14);
            background: rgba(var(--primary-rgb), 0.08);
            color: var(--text-secondary) !important;
            text-decoration: none; flex-shrink: 0; font-weight: 800;
            transition: background .16s ease, transform .16s ease, color .16s ease;
        }}
        .comment-floor-link:hover, .comment-reply-link:hover {{
            background: rgba(var(--primary-rgb), 0.18);
            color: var(--primary-dark) !important;
            transform: translateY(-1px);
        }}
        .comment-origin-meta {{
            color: var(--text-muted);
            font-size: 0.72rem;
            font-weight: 650;
        }}
        .comment-floor-text {{ font-size: 0.9rem; color: var(--text) !important; line-height: 1.6; font-weight: 500; }}
        .image-gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
            gap: 0.8rem;
            margin: 0.85rem 0 0.35rem;
        }}
        .pv-image-gallery {{
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            margin: 1rem 0 1.05rem;
        }}
        .pv-image-gallery.section-bound {{
            margin-top: 0.7rem;
            margin-bottom: 1.1rem;
        }}
        .pv-cover-wrap {{
            margin: 0.2rem 0 1rem;
        }}
        .pv-cover-wrap .image-thumb {{
            max-width: 360px;
            aspect-ratio: 480 / 300;
        }}
        .comment-image-gallery {{
            grid-template-columns: repeat(auto-fit, minmax(220px, 320px));
            justify-content: start;
        }}
        .image-thumb {{
            display: block;
            position: relative;
            overflow: hidden;
            border-radius: 14px;
            border: 1px solid rgba(var(--line-rgb), 0.12);
            background: rgba(var(--glass-tint-rgb), 0.42);
            box-shadow: 0 10px 24px rgba(var(--shadow-rgb), 0.10);
            aspect-ratio: 16 / 9;
            text-decoration: none;
            cursor: zoom-in;
        }}
        .image-thumb img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
            transition: transform .22s ease, filter .22s ease;
        }}
        .image-thumb:hover img {{
            transform: scale(1.035);
            filter: saturate(1.08) contrast(1.04);
        }}
        .image-caption {{
            position: absolute;
            left: 8px;
            right: 8px;
            bottom: 8px;
            padding: 3px 8px;
            border-radius: 999px;
            background: rgba(var(--glass-tint-rgb), 0.78);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            color: var(--text);
            font-size: 0.68rem;
            font-weight: 700;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .inline-emotions {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            margin-left: 6px;
            vertical-align: middle;
        }}
        .inline-emotion {{
            width: 30px;
            height: 30px;
            object-fit: contain;
            vertical-align: middle;
        }}
        .image-lightbox {{
            position: fixed;
            inset: 0;
            z-index: 2147483600;
            display: none;
            align-items: center;
            justify-content: center;
            padding: 4vh 4vw;
            background: rgba(8, 12, 24, 0.58);
            backdrop-filter: blur(24px) saturate(145%);
            -webkit-backdrop-filter: blur(24px) saturate(145%);
        }}
        .image-lightbox.show {{ display: flex; }}
        .image-lightbox-panel {{
            position: relative;
            max-width: min(1180px, 94vw);
            max-height: 92vh;
            padding: 14px;
            border-radius: 22px;
            border: 1px solid rgba(var(--glass-tint-rgb), 0.28);
            background: rgba(var(--glass-tint-rgb), 0.20);
            box-shadow: 0 34px 90px rgba(0, 0, 0, 0.34);
        }}
        .image-lightbox-img {{
            display: block;
            max-width: calc(94vw - 28px);
            max-height: calc(86vh - 72px);
            object-fit: contain;
            border-radius: 14px;
            background: rgba(0, 0, 0, 0.18);
        }}
        .image-lightbox-caption {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            color: #fff;
            margin-top: 10px;
            font-size: 0.86rem;
            font-weight: 700;
        }}
        .image-lightbox-caption a {{
            color: #fff !important;
            text-decoration: none;
            padding: 6px 12px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.16);
        }}
        .image-lightbox-close {{
            position: absolute;
            right: 12px;
            top: 12px;
            width: 38px;
            height: 38px;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.28);
            background: rgba(255, 255, 255, 0.22);
            color: #fff;
            font-size: 1.4rem;
            line-height: 1;
            cursor: pointer;
        }}
        .comment-reply {{
            margin-left: 1.2rem; padding: 0.5rem 0.8rem;
            background: rgba(var(--shadow-rgb), 0.04); border-left: 3px solid var(--primary-light);
            border-radius: 4px; margin-top: 0.4rem;
        }}
        .comment-reply-head {{ font-size: 0.78rem; color: var(--secondary); font-weight: 700; margin-bottom: 0.2rem; }}
        .comment-reply-head {{
            display: flex; align-items: center; justify-content: space-between; gap: 0.5rem;
        }}
        .comment-reply-link {{
            width: 22px; height: 22px; font-size: 0.76rem;
            background: rgba(var(--secondary-rgb), 0.08);
        }}
        .comment-reply-text {{ font-size: 0.84rem; color: var(--text-secondary) !important; line-height: 1.5; }}
        .comment-page-bar {{
            display: flex; align-items: center; justify-content: center; gap: 0.5rem;
            padding: 0.6rem 0.8rem; background: rgba(var(--glass-tint-rgb), 0.25);
            border-top: 1px solid var(--glass-border); flex-shrink: 0; height: 44px;
        }}
        .comment-page-btn {{
            display: inline-flex; align-items: center; justify-content: center;
            min-width: 30px; height: 30px; padding: 0 10px; border-radius: 6px;
            border: 1px solid var(--glass-border); background: var(--glass-bg);
            color: var(--text); font-size: 0.8rem; cursor: pointer;
            transition: all 0.15s; user-select: none; font-weight: 600;
        }}
        .comment-page-btn:hover:not(.disabled) {{ background: rgba(var(--primary-light-rgb), 0.2); border-color: var(--primary); }}
        .comment-page-btn.active {{ background: var(--primary); color: #fff; border-color: var(--primary); }}
        .comment-page-btn.disabled {{ opacity: 0.3; cursor: default; pointer-events: none; }}
        .comment-page-info {{ font-size: 0.78rem; color: var(--text-muted); padding: 0 0.4rem; font-weight: 600; }}
        .comment-empty-hint {{ text-align: center; padding: 2.5rem; color: var(--text-muted); font-size: 0.85rem; }}
        .comment-empty-hint a {{
            display: inline-block; margin-top: 0.5rem; padding: 0.4rem 1rem;
            background: var(--primary); color: #fff; border-radius: 6px;
            text-decoration: none; font-size: 0.8rem;
        }}
    .comment-search-nav {{
        display: flex; align-items: center; justify-content: center; gap: 0.6rem;
        padding: 0.5rem 0.8rem; background: rgba(var(--primary-rgb), 0.05);
        border-top: 1px solid var(--glass-border); flex-shrink: 0;
    }}
    .search-nav-btn {{
        display: inline-flex; align-items: center; justify-content: center;
        height: 26px; padding: 0 10px; border-radius: 6px;
        border: 1px solid rgba(var(--primary-rgb), 0.2); background: rgba(var(--glass-tint-rgb), 0.6);
        color: var(--primary); font-size: 0.74rem; cursor: pointer;
        transition: all 0.2s; user-select: none; font-weight: 600;
    }}
    .search-nav-btn:hover {{
        background: var(--primary) !important; color: #fff !important; border-color: var(--primary) !important;
        transform: translateY(-1px);
    }}
    .search-nav-info {{ font-size: 0.74rem; color: var(--text-secondary); font-weight: 600; margin-right: 0.4rem; }}
    .comment-floor.matched-active {{
        border: 1.5px solid var(--primary) !important;
        background: rgba(var(--primary-rgb), 0.08) !important;
        box-shadow: 0 0 10px rgba(var(--primary-rgb), 0.15) !important;
        transform: scale(1.005);
        transition: all 0.2s ease;
    }}
    .comment-tip {{
            padding: 0.5rem 1rem;
            background: rgba(var(--glass-tint-rgb), 0.15);
            font-size: 0.75rem;
            line-height: 1.6;
            border-top: 1px solid var(--glass-border);
            text-align: center;
        }}
        .comment-tip a {{
            color: var(--primary-dark);
            font-weight: 600;
            text-decoration: none;
        }}
        .comment-tip a:hover {{
            text-decoration: underline;
        }}
        /* ════════ 主题切换器 ════════ */
        .theme-switcher {{
            display: inline-flex;
            gap: 6px;
            background: rgba(var(--glass-tint-rgb), 0.35);
            backdrop-filter: blur(24px) saturate(180%);
            -webkit-backdrop-filter: blur(24px) saturate(180%);
            border: 1px solid rgba(var(--line-rgb), 0.2);
            border-radius: 16px !important;
            padding: 6px !important;
            box-shadow: 0 8px 32px rgba(var(--shadow-rgb), 0.15), inset 0 1px 0 rgba(255,255,255,0.2) !important;
            vertical-align: middle;
            margin-left: 1rem;
        }}
        .theme-btn {{
            width: auto !important;
            height: 28px !important;
            padding: 4px 10px !important;
            font-size: 0.75rem !important;
            font-weight: 500 !important;
            border-radius: 8px !important;
            border: 1px solid rgba(var(--line-rgb), 0.12) !important;
            cursor: pointer;
            transition: all 0.25s ease;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            color: var(--text-secondary);
            background: rgba(var(--glass-tint2-rgb), 0.4) !important;
        }}
        .theme-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
            transition: transform 0.2s ease;
        }}
        .theme-btn:hover {{
            transform: translateY(-1px);
            color: var(--text);
            background: rgba(var(--glass-tint2-rgb), 0.7) !important;
            border-color: rgba(var(--line-rgb), 0.24) !important;
        }}
        .theme-btn.active {{
            border-color: var(--primary) !important;
            background: rgba(var(--primary-rgb), 0.12) !important;
            color: var(--primary) !important;
            box-shadow: 0 0 10px rgba(var(--primary-rgb), 0.2) !important;
            font-weight: 600 !important;
        }}
        .theme-btn.active .theme-dot {{
            transform: scale(1.2);
        }}
        .theme-btn-warm {{ background: linear-gradient(135deg, #f59e0b, #d97706); }}
        .theme-btn-dark {{ background: linear-gradient(135deg, #6366f1, #1a2340); }}
        .theme-btn-light {{ background: linear-gradient(135deg, #ffffff, #e2e8f0); border: 2px solid var(--border); }}
        .theme-btn-anime {{ background: conic-gradient(from 210deg, #2f2830, #d98f5b, #8c6bb1, #b8875d, #4b3734, #ffd7a1, #2f2830); }}
        /* 入场动画 */
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .stat-card {{ animation: fadeInUp 0.6s ease-out backwards; }}
        .stats-bar .stat-card:nth-child(1) {{ animation-delay: 0.1s; }}
        .stats-bar .stat-card:nth-child(2) {{ animation-delay: 0.2s; }}
        .stats-bar .stat-card:nth-child(3) {{ animation-delay: 0.3s; }}
        .filter-card {{ animation: fadeInUp 0.6s ease-out 0.3s backwards; }}
        .table-card {{ animation: fadeInUp 0.6s ease-out 0.4s backwards; }}
        /* 响应式 */
        @media (max-width: 768px) {{
            .hero {{ padding: 2rem 1rem 3.5rem; }}
            .hero-title {{ font-size: 1.5rem; }}
            .stats-bar {{ padding: 0 1rem; }}
            .stat-card {{ min-width: 100%; padding: 1rem; }}
            .stat-value {{ font-size: 1.3rem; }}
            .main-wrap {{ padding: 0 1rem 2rem; }}
            .notice-wrap {{ padding: 0 1rem; }}
            .filter-col {{ min-width: 100%; }}
            .pv-popup {{ width: 92vw; }}
            .comment-popup {{ width: 92vw !important; max-width: 580px; }}
            /* DataTables 小屏响应式堆叠与对齐 */
            .dataTables_wrapper .dataTables_length,
            .dataTables_wrapper .dataTables_filter {{
                display: block !important;
                float: none !important;
                text-align: left !important;
                width: 100% !important;
                margin-bottom: 0.5rem !important;
            }}
            .dataTables_wrapper .dataTables_filter input {{
                width: 100% !important;
                margin-left: 0 !important;
                margin-top: 0.25rem !important;
            }}
            .dataTables_wrapper .dataTables_paginate {{
                text-align: center !important;
                float: none !important;
                width: 100% !important;
                display: flex !important;
                justify-content: center !important;
                flex-wrap: wrap !important;
                gap: 4px !important;
            }}
            .dataTables_wrapper .dataTables_paginate .paginate_button {{
                padding: 4px 8px !important;
                margin: 0 !important;
            }}
        }}
        .tag-cat.active-tag {{
            outline: 2px solid var(--primary) !important;
            box-shadow: 0 0 8px rgba(var(--primary-rgb),.6) !important;
            background: linear-gradient(135deg, rgba(var(--primary-light-rgb),.4), rgba(var(--primary-rgb),.15)) !important;
        }}
        .tag-pack.active-tag {{
            outline: 2px solid var(--secondary) !important;
            box-shadow: 0 0 8px rgba(var(--secondary-rgb),.6) !important;
            background: rgba(var(--secondary-rgb),.2) !important;
        }}
        .tag-cat.exclude-active-tag,
        .tag-pack.exclude-active-tag,
        .tag-mod.exclude-active-tag {{
            outline: 2px solid var(--danger) !important;
            box-shadow: 0 0 8px rgba(225, 29, 72, .38) !important;
            background: rgba(225, 29, 72, .12) !important;
            color: var(--danger) !important;
        }}
        /* ════════ 2026 数据终端视觉覆盖层 ════════ */
        :root {{
            --primary: #006adc;
            --primary-light: #248cff;
            --primary-dark: #004fb3;
            --secondary: #00a884;
            --secondary-light: #00c99d;
            --accent: #d946ef;
            --success: #009e73;
            --danger: #e11d48;
            --glass-bg: rgba(255, 255, 255, 0.78);
            --glass-bg-solid: rgba(255, 255, 255, 0.96);
            --glass-border: rgba(0, 83, 179, 0.12);
            --glass-hover: rgba(0, 106, 220, 0.08);
            --glass-shadow: rgba(15, 23, 42, 0.08);
            --bg-main: #eef4fb;
            --bg-gradient-1: #f8fbff;
            --bg-gradient-2: #e9f2ff;
            --bg-gradient-3: #dce8f7;
            --text: #0b1220;
            --text-secondary: #243447;
            --text-muted: rgba(36, 52, 71, 0.6);
            --border: rgba(0, 83, 179, 0.12);
            --shadow: 0 14px 36px rgba(15, 23, 42, 0.08);
            --shadow-lg: 0 24px 60px rgba(15, 23, 42, 0.11);
            --radius: 14px;
            --radius-sm: 10px;
            --primary-rgb: 0, 106, 220;
            --primary-light-rgb: 36, 140, 255;
            --primary-dark-rgb: 0, 79, 179;
            --secondary-rgb: 0, 168, 132;
            --accent-rgb: 217, 70, 239;
            --gold-light-rgb: 165, 180, 252;
            --shadow-rgb: 15, 23, 42;
            --line-rgb: 0, 83, 179;
            --glass-tint-rgb: 255, 255, 255;
            --glass-tint2-rgb: 248, 251, 255;
            --th-bg-1: rgba(248, 251, 255, 0.98);
            --th-bg-2: rgba(233, 242, 255, 0.98);
            --th-sort-bg-1: rgba(224, 242, 254, 0.9);
            --th-sort-bg-2: rgba(186, 230, 253, 0.72);
            --th-sort-active-bg-1: rgba(186, 230, 253, 0.9);
            --th-sort-active-bg-2: rgba(125, 211, 252, 0.78);
        }}
        :root[data-theme="light"] {{
            --primary: #006adc;
            --primary-light: #248cff;
            --primary-dark: #004fb3;
            --secondary: #00a884;
            --secondary-light: #00c99d;
            --accent: #d946ef;
            --success: #009e73;
            --danger: #e11d48;
            --glass-bg: rgba(255, 255, 255, 0.78);
            --glass-bg-solid: rgba(255, 255, 255, 0.96);
            --glass-border: rgba(0, 83, 179, 0.12);
            --glass-hover: rgba(0, 106, 220, 0.08);
            --glass-shadow: rgba(15, 23, 42, 0.08);
            --bg-main: #eef4fb;
            --bg-gradient-1: #f8fbff;
            --bg-gradient-2: #e9f2ff;
            --bg-gradient-3: #dce8f7;
            --text: #0b1220;
            --text-secondary: #243447;
            --text-muted: rgba(36, 52, 71, 0.6);
            --border: rgba(0, 83, 179, 0.12);
            --shadow: 0 14px 36px rgba(15, 23, 42, 0.08);
            --shadow-lg: 0 24px 60px rgba(15, 23, 42, 0.11);
            --primary-rgb: 0, 106, 220;
            --primary-light-rgb: 36, 140, 255;
            --primary-dark-rgb: 0, 79, 179;
            --secondary-rgb: 0, 168, 132;
            --accent-rgb: 217, 70, 239;
            --line-rgb: 0, 83, 179;
            --glass-tint-rgb: 255, 255, 255;
            --glass-tint2-rgb: 248, 251, 255;
            --th-bg-1: rgba(248, 251, 255, 0.98);
            --th-bg-2: rgba(233, 242, 255, 0.98);
            --th-sort-bg-1: rgba(221, 236, 255, 0.96);
            --th-sort-bg-2: rgba(202, 226, 255, 0.88);
            --th-sort-active-bg-1: rgba(188, 219, 255, 0.96);
            --th-sort-active-bg-2: rgba(147, 197, 253, 0.86);
        }}
        :root[data-theme="warm"] {{
            --primary: #008c7a;
            --primary-light: #18b7a1;
            --primary-dark: #006b61;
            --secondary: #2563eb;
            --secondary-light: #60a5fa;
            --accent: #7c3aed;
            --success: #059669;
            --danger: #e11d48;
            --glass-bg: rgba(248, 253, 251, 0.86);
            --glass-bg-solid: rgba(252, 255, 254, 0.98);
            --glass-border: rgba(0, 140, 122, 0.12);
            --glass-hover: rgba(0, 140, 122, 0.075);
            --bg-main: #edf7f5;
            --bg-gradient-1: #fbfffd;
            --bg-gradient-2: #e8f7f2;
            --bg-gradient-3: #dceef4;
            --text: #0b1718;
            --text-secondary: #233b3d;
            --text-muted: rgba(35, 59, 61, 0.58);
            --primary-rgb: 0, 140, 122;
            --primary-light-rgb: 24, 183, 161;
            --primary-dark-rgb: 0, 107, 97;
            --secondary-rgb: 37, 99, 235;
            --accent-rgb: 124, 58, 237;
            --line-rgb: 0, 140, 122;
            --glass-tint-rgb: 252, 255, 254;
            --glass-tint2-rgb: 232, 247, 242;
            --th-bg-1: rgba(252, 255, 254, 0.98);
            --th-bg-2: rgba(234, 247, 244, 0.98);
            --th-sort-bg-1: rgba(214, 246, 240, 0.96);
            --th-sort-bg-2: rgba(188, 235, 226, 0.88);
            --th-sort-active-bg-1: rgba(171, 226, 216, 0.96);
            --th-sort-active-bg-2: rgba(118, 207, 193, 0.84);
        }}
        :root[data-theme="dark"] {{
            --primary: #22d3ee;
            --primary-light: #67e8f9;
            --primary-dark: #0891b2;
            --secondary: #a78bfa;
            --secondary-light: #c4b5fd;
            --accent: #34d399;
            --success: #34d399;
            --danger: #fb7185;
            --glass-bg: rgba(17, 24, 39, 0.82);
            --glass-bg-solid: rgba(20, 28, 42, 0.97);
            --glass-border: rgba(148, 163, 184, 0.18);
            --glass-hover: rgba(34, 211, 238, 0.11);
            --bg-main: #0b1018;
            --bg-gradient-1: #0b1018;
            --bg-gradient-2: #111827;
            --bg-gradient-3: #182033;
            --text: #f8fafc;
            --text-secondary: #d3dee9;
            --text-muted: rgba(211, 222, 233, 0.62);
            --primary-rgb: 34, 211, 238;
            --primary-light-rgb: 103, 232, 249;
            --primary-dark-rgb: 8, 145, 178;
            --secondary-rgb: 167, 139, 250;
            --accent-rgb: 52, 211, 153;
            --line-rgb: 34, 211, 238;
            --glass-tint-rgb: 20, 28, 42;
            --glass-tint2-rgb: 17, 24, 39;
            --th-bg-1: rgba(18, 26, 39, 0.98);
            --th-bg-2: rgba(24, 35, 52, 0.98);
            --th-sort-bg-1: rgba(20, 49, 66, 0.98);
            --th-sort-bg-2: rgba(20, 61, 76, 0.92);
            --th-sort-active-bg-1: rgba(18, 93, 112, 0.72);
            --th-sort-active-bg-2: rgba(34, 211, 238, 0.34);
        }}
        :root[data-theme="eye"] {{
            --primary: #7a6a34;
            --primary-light: #9b894c;
            --primary-dark: #5f5228;
            --secondary: #4f7d67;
            --secondary-light: #6ea38a;
            --accent: #9a6b54;
            --success: #4f7d67;
            --danger: #b45f5a;
            --glass-bg: rgba(255, 252, 243, 0.9);
            --glass-bg-solid: rgba(255, 253, 247, 0.985);
            --glass-border: rgba(122, 106, 52, 0.13);
            --glass-hover: rgba(122, 106, 52, 0.065);
            --bg-main: #f4efe3;
            --bg-gradient-1: #fffdf7;
            --bg-gradient-2: #f3ecdd;
            --bg-gradient-3: #e9e1d0;
            --text: #201d16;
            --text-secondary: #403b2f;
            --text-muted: rgba(64, 59, 47, 0.6);
            --primary-rgb: 122, 106, 52;
            --primary-light-rgb: 155, 137, 76;
            --primary-dark-rgb: 95, 82, 40;
            --secondary-rgb: 79, 125, 103;
            --accent-rgb: 154, 107, 84;
            --line-rgb: 122, 106, 52;
            --glass-tint-rgb: 255, 253, 247;
            --glass-tint2-rgb: 243, 236, 221;
            --th-bg-1: rgba(255, 253, 247, 0.98);
            --th-bg-2: rgba(244, 238, 224, 0.98);
            --th-sort-bg-1: rgba(246, 238, 214, 0.98);
            --th-sort-bg-2: rgba(232, 219, 188, 0.9);
            --th-sort-active-bg-1: rgba(221, 205, 162, 0.96);
            --th-sort-active-bg-2: rgba(194, 171, 113, 0.82);
        }}
        :root[data-theme="pink"] {{
            --primary: #e84a8a;
            --primary-light: #ff7ab1;
            --primary-dark: #c72f70;
            --secondary: #8b5cf6;
            --secondary-light: #a78bfa;
            --accent: #06b6d4;
            --success: #0f9f7a;
            --danger: #e11d48;
            --glass-bg: rgba(255, 247, 251, 0.86);
            --glass-bg-solid: rgba(255, 250, 253, 0.98);
            --glass-border: rgba(232, 74, 138, 0.14);
            --glass-hover: rgba(232, 74, 138, 0.08);
            --bg-main: #fdf2f8;
            --bg-gradient-1: #fffafd;
            --bg-gradient-2: #fce7f3;
            --bg-gradient-3: #eef2ff;
            --text: #20101a;
            --text-secondary: #4a263b;
            --text-muted: rgba(74, 38, 59, 0.58);
            --primary-rgb: 232, 74, 138;
            --primary-light-rgb: 255, 122, 177;
            --primary-dark-rgb: 199, 47, 112;
            --secondary-rgb: 139, 92, 246;
            --accent-rgb: 6, 182, 212;
            --line-rgb: 232, 74, 138;
            --glass-tint-rgb: 255, 250, 253;
            --glass-tint2-rgb: 252, 231, 243;
            --th-bg-1: rgba(255, 250, 253, 0.98);
            --th-bg-2: rgba(252, 231, 243, 0.98);
            --th-sort-bg-1: rgba(253, 226, 240, 0.98);
            --th-sort-bg-2: rgba(251, 207, 232, 0.9);
            --th-sort-active-bg-1: rgba(251, 190, 221, 0.96);
            --th-sort-active-bg-2: rgba(244, 114, 182, 0.72);
        }}
        :root[data-theme="anime"] {{
            --primary: #d98f5b;
            --primary-light: #ffd7a1;
            --primary-dark: #9f5a3b;
            --secondary: #8c6bb1;
            --secondary-light: #c4a7e7;
            --accent: #b8875d;
            --success: #c98a5d;
            --danger: #d26b72;
            --glass-bg: rgba(54, 41, 45, 0.28);
            --glass-bg-solid: rgba(54, 41, 45, 0.62);
            --glass-border: rgba(255, 215, 161, 0.34);
            --glass-hover: rgba(255, 215, 161, 0.12);
            --bg-main: #2f2830;
            --bg-gradient-1: #2f2830;
            --bg-gradient-2: #4b3734;
            --bg-gradient-3: #6a4738;
            --text: #fff3dc;
            --text-secondary: #ecd6b8;
            --text-muted: rgba(236, 214, 184, 0.72);
            --primary-rgb: 217, 143, 91;
            --primary-light-rgb: 255, 215, 161;
            --primary-dark-rgb: 159, 90, 59;
            --secondary-rgb: 140, 107, 177;
            --accent-rgb: 184, 135, 93;
            --line-rgb: 217, 143, 91;
            --glass-tint-rgb: 71, 54, 54;
            --glass-tint2-rgb: 102, 71, 56;
            --th-bg-1: rgba(54, 41, 45, 0.62);
            --th-bg-2: rgba(102, 71, 56, 0.48);
            --th-sort-bg-1: rgba(217, 143, 91, 0.18);
            --th-sort-bg-2: rgba(140, 107, 177, 0.12);
            --th-sort-active-bg-1: rgba(255, 215, 161, 0.26);
            --th-sort-active-bg-2: rgba(217, 143, 91, 0.18);
        }}
        body {{
            background:
                linear-gradient(rgba(var(--line-rgb), 0.035) 1px, transparent 1px),
                linear-gradient(90deg, rgba(var(--line-rgb), 0.035) 1px, transparent 1px),
                radial-gradient(circle at 18% 0%, rgba(var(--primary-rgb), 0.18), transparent 34%),
                radial-gradient(circle at 86% 10%, rgba(var(--secondary-rgb), 0.14), transparent 30%),
                linear-gradient(135deg, var(--bg-gradient-1), var(--bg-gradient-2) 52%, var(--bg-gradient-3)) !important;
            background-size: 32px 32px, 32px 32px, auto, auto, auto !important;
        }}
        .bg-layer {{
            background:
                linear-gradient(120deg, transparent 0 38%, rgba(var(--primary-rgb), 0.08) 38% 39%, transparent 39% 100%),
                linear-gradient(180deg, rgba(var(--glass-tint-rgb), 0.28), transparent 42%) !important;
        }}
        .bg-layer::before {{
            background: linear-gradient(90deg, rgba(var(--primary-rgb), 0.16), rgba(var(--secondary-rgb), 0.1), rgba(var(--accent-rgb), 0.12)) !important;
            height: 3px; bottom: auto;
        }}
        :root[data-theme="anime"] body {{
            background:
                radial-gradient(circle at 15% 8%, rgba(255, 215, 161, 0.18), transparent 30%),
                radial-gradient(circle at 84% 18%, rgba(196, 167, 231, 0.12), transparent 34%),
                radial-gradient(circle at 20% 86%, rgba(184, 135, 93, 0.20), transparent 36%),
                linear-gradient(rgba(255, 215, 161, 0.045) 1px, transparent 1px),
                linear-gradient(90deg, rgba(196, 167, 231, 0.035) 1px, transparent 1px),
                linear-gradient(135deg, #2f2830, #4b3734 52%, #6a4738) !important;
            background-size: auto, auto, auto, 34px 34px, 34px 34px, auto !important;
        }}
        :root[data-theme="anime"] .bg-layer {{
            background:
                linear-gradient(115deg, transparent 0 18%, rgba(255, 215, 161, 0.16) 28% 34%, transparent 50%),
                linear-gradient(42deg, transparent 0 52%, rgba(196, 167, 231, 0.10) 62% 68%, transparent 84%),
                radial-gradient(circle at 22% 8%, rgba(255, 243, 220, 0.16), transparent 18%),
                linear-gradient(180deg, rgba(47, 40, 48, 0.50), transparent 48%) !important;
        }}
        :root[data-theme="anime"] .bg-layer::after {{
            content: "";
            position: fixed;
            inset: -20%;
            z-index: -1;
            pointer-events: none;
            background:
                linear-gradient(104deg, transparent 0 8%, rgba(255, 215, 161, 0.20) 18%, transparent 36%),
                linear-gradient(24deg, transparent 0 56%, rgba(184, 135, 93, 0.18) 68%, transparent 88%);
            filter: none;
            opacity: 0.85;
            mix-blend-mode: screen;
            animation: none;
        }}
        @keyframes animeFlow {{
            0% {{ transform: translate3d(-14%, -8%, 0) rotate(-7deg) scale(1.18); filter: hue-rotate(0deg) blur(12px) saturate(260%); }}
            45% {{ transform: translate3d(9%, 7%, 0) rotate(8deg) scale(1.30); filter: hue-rotate(24deg) blur(16px) saturate(330%); }}
            100% {{ transform: translate3d(15%, -9%, 0) rotate(-5deg) scale(1.24); filter: hue-rotate(-18deg) blur(13px) saturate(290%); }}
        }}
        @keyframes animeSheen {{
            0% {{ transform: translateX(-120%) skewX(-18deg); opacity: 0; }}
            18% {{ opacity: 0.42; }}
            100% {{ transform: translateX(120%) skewX(-18deg); opacity: 0; }}
        }}
        :root[data-theme="anime"] .stat-card,
        :root[data-theme="anime"] .filter-card,
        :root[data-theme="anime"] .table-card,
        :root[data-theme="anime"] .disclaimer-inner,
        :root[data-theme="anime"] .sort-hint-inner {{
            position: relative;
            overflow: hidden;
            background: linear-gradient(135deg, rgba(80, 24, 52, 0.58), rgba(156, 63, 34, 0.28)) !important;
            border: 1px solid rgba(255, 138, 36, 0.40) !important;
            box-shadow: 0 24px 80px rgba(97, 20, 58, 0.44), inset 0 1px 0 rgba(255,247,239,0.18), inset 0 0 56px rgba(143, 53, 255, 0.12) !important;
            backdrop-filter: blur(36px) saturate(230%) contrast(118%) !important;
            -webkit-backdrop-filter: blur(36px) saturate(230%) contrast(118%) !important;
        }}
        :root[data-theme="anime"] .stat-card::after,
        :root[data-theme="anime"] .filter-card::after,
        :root[data-theme="anime"] .table-card::after,
        :root[data-theme="anime"] .disclaimer-inner::after,
        :root[data-theme="anime"] .sort-hint-inner::after {{
            content: "";
            position: absolute;
            inset: 0;
            pointer-events: none;
            background:
                linear-gradient(108deg, transparent 0 16%, rgba(255, 138, 36, 0.36) 30%, rgba(143, 53, 255, 0.24) 44%, transparent 66%),
                linear-gradient(72deg, transparent 0 44%, rgba(184, 115, 51, 0.26) 58%, transparent 80%),
                radial-gradient(circle at 18% 0%, rgba(255,247,239,0.18), transparent 24%);
            mix-blend-mode: screen;
            animation: none;
            opacity: 0.42;
        }}
        :root[data-theme="anime"] .table-card {{
            background:
                linear-gradient(135deg, rgba(80, 24, 52, 0.62), rgba(156, 63, 34, 0.32)),
                linear-gradient(90deg, rgba(255, 77, 31, 0.20), transparent 28%, rgba(143, 53, 255, 0.16), transparent 58%, rgba(184, 115, 51, 0.18)) !important;
        }}
        :root[data-theme="anime"] .dataTables_scrollHead,
        :root[data-theme="anime"] .sort-strip {{
            background: linear-gradient(90deg, rgba(255, 77, 31, 0.26), rgba(184, 115, 51, 0.18), rgba(143, 53, 255, 0.18)) !important;
        }}
        :root[data-theme="anime"] table.dataTable tbody td {{
            color: rgba(255, 247, 239, 0.86) !important;
            border-bottom-color: rgba(255, 138, 36, 0.12) !important;
        }}
        :root[data-theme="anime"] table.dataTable tbody tr:hover {{
            background: linear-gradient(90deg, rgba(255, 77, 31, 0.22), rgba(143, 53, 255, 0.12), rgba(184, 115, 51, 0.16)) !important;
        }}
        :root[data-theme="anime"] .hero-title,
        :root[data-theme="anime"] .stat-value,
        :root[data-theme="anime"] .modpack-link {{
            background: linear-gradient(90deg, #ff8a24, #fff7ef, #ff2d16, #8f35ff, #b87333, #ff8a24) !important;
            background-size: 320% 100% !important;
            -webkit-background-clip: text !important;
            background-clip: text !important;
            color: transparent !important;
            -webkit-text-fill-color: transparent !important;
            animation: none;
        }}
        @keyframes animeTextFlow {{
            0% {{ background-position: 0% 50%; }}
            100% {{ background-position: 320% 50%; }}
        }}
        :root[data-theme="anime"] .theme-switcher {{
            background: rgba(80, 24, 52, 0.68) !important;
            border-color: rgba(255, 138, 36, 0.42) !important;
            box-shadow: 0 12px 34px rgba(255, 77, 31, 0.20), inset 0 1px 0 rgba(255,247,239,0.16) !important;
        }}
        :root[data-theme="anime"] .theme-btn.active {{
            border-color: #ff8a24 !important;
            box-shadow: 0 0 0 2px rgba(255, 77, 31, 0.34), 0 0 24px rgba(143, 53, 255, 0.38) !important;
        }}
        :root[data-theme="anime"] .dataTables_scrollBody::-webkit-scrollbar-thumb,
        :root[data-theme="anime"] .comment-body::-webkit-scrollbar-thumb,
        :root[data-theme="anime"] .pv-body::-webkit-scrollbar-thumb {{
            background: linear-gradient(180deg, #ff8a24, #8f35ff 52%, #b87333) !important;
            box-shadow: 0 0 18px rgba(255, 77, 31, 0.44) !important;
        }}
        :root[data-theme="anime"] .tag-cat {{
            background: rgba(255, 77, 31, 0.20) !important;
            border-color: rgba(255, 138, 36, 0.34) !important;
            color: #ffd5bd !important;
        }}
        :root[data-theme="anime"] .tag-pack {{
            background: rgba(143, 53, 255, 0.18) !important;
            border-color: rgba(189, 120, 255, 0.30) !important;
            color: #e5c8ff !important;
        }}
        .orb {{ display: none !important; }}
        .hero {{
            padding: 1.55rem 2rem 4rem !important;
            background: linear-gradient(180deg, rgba(var(--glass-tint-rgb), 0.62), rgba(var(--glass-tint2-rgb), 0.2)) !important;
            border-bottom: 1px solid var(--glass-border) !important;
        }}
        .hero-title {{
            font-size: clamp(1.65rem, 2.2vw, 2.45rem) !important;
            letter-spacing: 0 !important;
            -webkit-text-fill-color: unset !important;
            background: none !important;
            color: var(--text) !important;
        }}
        .hero-sub {{ color: var(--text-muted) !important; }}
        .stats-bar {{ gap: 0.9rem !important; margin-top: -2.45rem !important; }}
        .stat-card, .filter-card, .table-card, .disclaimer-inner, .sort-hint-inner {{
            border-radius: var(--radius) !important;
            background: var(--glass-bg) !important;
            border: 1px solid var(--glass-border) !important;
            box-shadow: var(--shadow) !important;
        }}
        .stat-card {{ min-width: 220px !important; padding: 1.05rem 1.2rem !important; }}
        .stat-card:hover {{ transform: translateY(-2px) !important; box-shadow: var(--shadow-lg) !important; }}
        .stat-icon {{
            width: 44px !important; height: 44px !important; border-radius: 10px !important;
            font-size: 1.18rem !important;
        }}
        .stat-label {{ letter-spacing: 0 !important; text-transform: none !important; }}
        .stat-value {{ font-size: 1.45rem !important; }}
        .filter-card {{ padding: 1rem !important; }}
        .filter-label {{ letter-spacing: 0 !important; text-transform: none !important; }}
        .table-card {{ padding: 0.8rem !important; }}
        table.dataTable thead th {{
            border-bottom: 0 !important;
            font-size: 0.74rem !important;
            letter-spacing: 0 !important;
            padding: 0.72rem 2.1rem 0.72rem 0.72rem !important;
            min-width: 78px;
        }}
        table.dataTable tbody td {{
            padding: 0.42rem 0.55rem !important;
            border-bottom: 1px solid rgba(var(--line-rgb), 0.07) !important;
        }}
        table.dataTable tbody tr:hover {{
            background: linear-gradient(90deg, rgba(var(--primary-rgb), 0.12), rgba(var(--secondary-rgb), 0.06)) !important;
        }}
        .td-trend {{
            cursor: crosshair;
            text-decoration: underline;
            text-decoration-style: dotted;
            text-decoration-color: rgba(var(--primary-rgb), 0.42);
            text-underline-offset: 3px;
        }}
        .td-up, .td-down, .td-flat {{
            position: relative;
        }}
        .td-up::before, .td-down::before, .td-flat::before {{
            display: inline-block;
            margin-right: 0.25rem;
            font-size: 0.72rem;
            opacity: 0.9;
        }}
        .td-up::before {{ content: "▲"; }}
        .td-down::before {{ content: "▼"; }}
        .td-flat::before {{ content: "●"; font-size: 0.56rem; }}
        .trend-tooltip {{
            width: 380px !important;
            padding: 14px !important;
            border: 1px solid rgba(var(--primary-rgb), 0.42) !important;
            border-radius: 14px !important;
            background: color-mix(in srgb, var(--glass-bg-solid) 94%, transparent) !important;
            box-shadow: 0 24px 80px rgba(0,0,0,.38), 0 0 0 1px rgba(255,255,255,.04) inset !important;
            pointer-events: auto !important;
        }}
        .trend-tooltip-title {{ font-size: 0.86rem !important; }}
        .trend-tooltip-subtitle {{ font-size: 0.72rem !important; color: var(--text-muted) !important; }}
        .trend-tooltip-chart-container {{ height: 150px !important; }}
        .trend-tooltip-chart-container svg {{ overflow: visible; cursor: crosshair; }}
        .trend-chart-capture {{ cursor: crosshair; pointer-events: all; }}
        .trend-point-hit {{ cursor: crosshair; pointer-events: all; }}
        .trend-guide-line {{
            visibility: hidden;
            pointer-events: none;
            stroke: var(--primary);
            stroke-width: 1.2;
            stroke-dasharray: 3 4;
            opacity: 0.58;
        }}
        .trend-point-visible {{
            filter: drop-shadow(0 2px 5px rgba(0,0,0,.22));
            pointer-events: none;
        }}
        .trend-point-label {{
            display: none;
            position: absolute;
            z-index: 3;
            min-width: 108px;
            padding: 6px 8px;
            border: 1px solid rgba(var(--line-rgb), 0.18);
            border-radius: 8px;
            background: var(--glass-bg-solid);
            color: var(--text);
            box-shadow: 0 10px 28px rgba(0,0,0,.16);
            font-size: 0.72rem;
            line-height: 1.35;
            pointer-events: none;
        }}
        .trend-point-label b {{ color: var(--primary); font-weight: 800; }}
        .trend-tooltip-footer {{ display: grid !important; grid-template-columns: repeat(3, 1fr); gap: 6px; border-top: 0 !important; }}
        .trend-tooltip-footer span {{
            display: block;
            padding: 6px 8px;
            border: 1px solid var(--glass-border);
            border-radius: 8px;
            background: rgba(var(--primary-rgb), 0.07);
            color: var(--text) !important;
        }}
        .trend-tooltip-footer b,
        .trend-tooltip-footer em {{
            display: block;
            font-style: normal;
            line-height: 1.35;
            white-space: nowrap;
        }}
        .trend-tooltip-footer em {{
            margin-top: 2px;
            color: var(--primary-light);
            font-weight: 800;
        }}
        /* theme-switcher overrides removed */
        .theme-btn-warm {{ background: linear-gradient(135deg, #fafffd, #18b7a1 58%, #2563eb) !important; }}
        .theme-btn-dark {{ background: linear-gradient(135deg, #0b1018, #22d3ee 58%, #a78bfa) !important; }}
        .theme-btn-light {{ background: linear-gradient(135deg, #ffffff, #248cff) !important; }}
        .theme-btn-eye {{ background: linear-gradient(135deg, #fffdf7, #9b894c 58%, #6ea38a) !important; }}
        .theme-btn-pink {{ background: linear-gradient(135deg, #fffafd, #ff7ab1 58%, #8b5cf6) !important; }}
        .theme-btn-anime {{ background: conic-gradient(from 210deg, #2f2830, #d98f5b, #8c6bb1, #b8875d, #4b3734, #ffd7a1, #2f2830) !important; }}
        .pv-popup, .comment-popup {{
            border: 1px solid rgba(var(--line-rgb), 0.18) !important;
            border-radius: 14px !important;
            background: color-mix(in srgb, var(--glass-bg-solid) 96%, transparent) !important;
            box-shadow: 0 24px 70px rgba(0,0,0,.34), 0 0 0 1px rgba(255,255,255,.04) inset !important;
            backdrop-filter: blur(18px) saturate(130%) !important;
            -webkit-backdrop-filter: blur(18px) saturate(130%) !important;
        }}
        .pv-popup {{ width: 620px !important; max-height: min(720px, calc(100vh - 32px)) !important; }}
        .comment-popup {{
            width: clamp(620px, 58vw, 900px) !important;
            height: min(720px, calc(100vh - 48px)) !important;
            max-height: min(720px, calc(100vh - 48px)) !important;
        }}
        .pv-head, .comment-head {{
            min-height: 46px !important;
            padding: 0.72rem 0.95rem !important;
            background: linear-gradient(90deg, rgba(var(--primary-rgb), 0.16), rgba(var(--secondary-rgb), 0.08)) !important;
            color: var(--text) !important;
            border-bottom: 1px solid rgba(var(--line-rgb), 0.12) !important;
        }}
        .pv-title, .comment-title {{
            color: var(--text) !important;
            font-size: 0.92rem !important;
            font-weight: 750 !important;
            letter-spacing: 0 !important;
            text-shadow: none !important;
        }}
        .pv-head-title, .comment-head-title {{
            color: var(--text) !important;
            font-size: 0.98rem !important;
            font-weight: 850 !important;
            letter-spacing: 0 !important;
            text-shadow: none !important;
        }}
        .pv-head-icon, .comment-head-icon {{
            background: rgba(var(--primary-rgb), 0.11) !important;
            color: var(--primary-dark) !important;
            box-shadow: none !important;
        }}
        .pv-actions a, .pv-actions span, .pv-actions button {{
            background: rgba(var(--primary-rgb), 0.08) !important;
            border: 1px solid rgba(var(--line-rgb), 0.14) !important;
            color: var(--text-secondary) !important;
            border-radius: 8px !important;
        }}
        .pv-body, .comment-body {{
            background: transparent !important;
            color: var(--text-secondary) !important;
            padding: 1rem 1.05rem !important;
        }}
        .comment-body {{
            max-height: min(600px, calc(100vh - 280px)) !important;
            overflow: auto !important;
        }}
        :root[data-theme="light"] .pv-head,
        :root[data-theme="light"] .comment-head {{
            background: linear-gradient(90deg, rgba(255, 255, 255, 0.96), rgba(232, 244, 255, 0.94)) !important;
            box-shadow: inset 4px 0 0 #006adc, inset 0 -1px 0 rgba(0, 83, 179, 0.12) !important;
        }}
        :root[data-theme="light"] .pv-head-icon,
        :root[data-theme="light"] .comment-head-icon {{
            background: #e7f1ff !important;
            color: #0053b3 !important;
        }}
        :root[data-theme="light"] .pv-head-title,
        :root[data-theme="light"] .comment-head-title {{
            color: #0b1220 !important;
        }}
        :root[data-theme="light"] .pv-title,
        :root[data-theme="light"] .comment-title {{
            color: #0b1220 !important;
            text-shadow: none !important;
        }}
        :root[data-theme="light"] .pv-actions a,
        :root[data-theme="light"] .pv-actions span,
        :root[data-theme="light"] .pv-actions button {{
            color: #1e293b !important;
        }}
        .pv-body {{
            font-size: 0.92rem !important;
            line-height: 1.78 !important;
        }}
        .pv-section-title {{
            margin: 1rem 0 0.45rem !important;
            padding-left: 0.65rem !important;
            border-left: 3px solid var(--primary) !important;
            color: var(--text) !important;
            background: transparent !important;
            font-size: 0.95rem !important;
        }}
        .pv-para {{
            margin: 0.45rem 0 !important;
            padding: 0 !important;
            background: transparent !important;
            border: 0 !important;
        }}
        .comment-floor {{
            margin: 0 0 0.65rem !important;
            padding: 0.78rem 0.85rem !important;
            border: 1px solid rgba(var(--line-rgb), 0.1) !important;
            border-radius: 10px !important;
            background: rgba(var(--primary-rgb), 0.045) !important;
        }}
        .comment-floor:last-child {{ margin-bottom: 0 !important; }}
        .comment-floor-head {{
            color: var(--text) !important;
            font-size: 0.8rem !important;
            margin-bottom: 0.38rem !important;
        }}
        .comment-floor-head .floor-num {{
            border-radius: 999px !important;
            background: rgba(var(--primary-rgb), 0.16) !important;
            color: var(--primary-light) !important;
        }}
        .comment-floor-text {{
            color: var(--text-secondary) !important;
            font-size: 0.9rem !important;
            line-height: 1.66 !important;
            font-weight: 450 !important;
        }}
        .comment-reply {{
            margin-left: 0.75rem !important;
            border-left: 2px solid rgba(var(--secondary-rgb), 0.45) !important;
            background: rgba(var(--secondary-rgb), 0.055) !important;
            border-radius: 8px !important;
        }}
        .comment-page-bar, .comment-tip {{
            background: rgba(var(--glass-tint-rgb), 0.16) !important;
            border-top: 1px solid rgba(var(--line-rgb), 0.1) !important;
        }}
        .mcmod-consent {{
            background: transparent !important;
        }}
        .mcmod-consent-panel {{
            background: rgba(var(--glass-tint-rgb), 0.85) !important;
        }}
        /* 最终毛玻璃统一增强：所有主题更透，同时保留文字底色与阴影 */
        :root,
        :root[data-theme] {{
            --radius: 12px;
            --radius-sm: 8px;
        }}
        :root[data-theme="light"],
        :root[data-theme="warm"],
        :root[data-theme="eye"],
        :root[data-theme="pink"] {{
            --glass-bg: rgba(var(--glass-tint-rgb), 0.34);
            --glass-bg-solid: rgba(var(--glass-tint-rgb), 0.58);
        }}
        :root[data-theme="dark"] {{
            --glass-bg: rgba(17, 24, 39, 0.34);
            --glass-bg-solid: rgba(20, 28, 42, 0.58);
        }}
        :root[data-theme="anime"] {{
            --glass-bg: rgba(54, 41, 45, 0.24);
            --glass-bg-solid: rgba(54, 41, 45, 0.54);
            --text: #fff4de;
            --text-secondary: #ecd6b8;
            --text-muted: rgba(236, 214, 184, 0.76);
        }}
        .stat-card, .filter-card, .table-card, .disclaimer-inner, .sort-hint-inner,
        .theme-switcher, .pv-popup, .comment-popup, .trend-tooltip {{
            background-color: transparent !important;
            border-radius: var(--radius) !important;
            backdrop-filter: blur(34px) saturate(190%) contrast(112%) !important;
            -webkit-backdrop-filter: blur(34px) saturate(190%) contrast(112%) !important;
            box-shadow:
                var(--shadow),
                inset 0 1px 0 rgba(255,255,255,0.24),
                inset 0 0 0 1px rgba(255,255,255,0.07) !important;
        }}
        .stat-card, .filter-card, .table-card, .disclaimer-inner, .sort-hint-inner {{
            background:
                linear-gradient(135deg, rgba(var(--glass-tint-rgb), 0.24), rgba(var(--glass-tint2-rgb), 0.10)),
                linear-gradient(180deg, rgba(255,255,255,0.18), rgba(255,255,255,0.04)) !important;
        }}
        .pv-popup, .comment-popup, .trend-tooltip {{
            background: color-mix(in srgb, var(--glass-bg-solid) 58%, transparent) !important;
        }}
        table.dataTable tbody td,
        .filter-label, .stat-label, .hero-sub, .pv-body, .comment-body {{
            text-shadow: 0 1px 2px rgba(0,0,0,0.22);
        }}
        :root[data-theme="anime"] body,
        :root[data-theme="anime"] body *:not(input):not(select):not(option):not(textarea):not(svg):not(path),
        :root[data-theme="anime"] table.dataTable tbody td,
        :root[data-theme="anime"] .filter-label,
        :root[data-theme="anime"] .hero-sub,
        :root[data-theme="anime"] .pv-body,
        :root[data-theme="anime"] .comment-body,
        :root[data-theme="anime"] .comment-floor-text,
        :root[data-theme="anime"] .sort-hint-inner,
        :root[data-theme="anime"] .disclaimer-inner {{
            color: #fff4de !important;
            text-shadow:
                0 1px 1px rgba(30, 22, 24, 0.75),
                0 0 8px rgba(255, 215, 161, 0.26) !important;
        }}
        :root[data-theme="anime"] .hero-title,
        :root[data-theme="anime"] .stat-value,
        :root[data-theme="anime"] .modpack-link,
        :root[data-theme="anime"] table.dataTable thead th,
        :root[data-theme="anime"] .filter-label,
        :root[data-theme="anime"] .pv-title,
        :root[data-theme="anime"] .comment-title {{
            background: linear-gradient(90deg, #fff6df, #ffd7a1, #ffffff, #dbc6f0, #fff6df) !important;
            background-size: 180% 100% !important;
            -webkit-background-clip: text !important;
            background-clip: text !important;
            color: transparent !important;
            -webkit-text-fill-color: transparent !important;
            text-shadow:
                0 0 2px rgba(255, 247, 223, 0.96),
                0 0 9px rgba(255, 215, 161, 0.46),
                0 2px 4px rgba(30, 22, 24, 0.62) !important;
            -webkit-text-stroke: 0.35px rgba(255, 247, 223, 0.52);
            animation: none;
        }}
        :root[data-theme="anime"] .hero-title,
        :root[data-theme="anime"] .stat-value {{
            filter: drop-shadow(0 0 5px rgba(255, 215, 161, 0.36));
        }}
        :root[data-theme="anime"] .stat-card,
        :root[data-theme="anime"] .filter-card,
        :root[data-theme="anime"] .table-card,
        :root[data-theme="anime"] .disclaimer-inner,
        :root[data-theme="anime"] .sort-hint-inner {{
            background:
                linear-gradient(135deg, rgba(54, 41, 45, 0.22), rgba(102, 71, 56, 0.12)),
                linear-gradient(180deg, rgba(255,255,255,0.16), rgba(255,255,255,0.03)) !important;
            border-color: rgba(255, 215, 161, 0.30) !important;
        }}
        :root[data-theme="anime"] .table-card {{
            background:
                linear-gradient(135deg, rgba(54, 41, 45, 0.20), rgba(102, 71, 56, 0.12)),
                linear-gradient(180deg, rgba(255,255,255,0.16), rgba(255,255,255,0.03)) !important;
        }}
        /* 流光主题终版：刻意脱离其它主题的“普通玻璃卡片”观感 */
        :root[data-theme="anime"] {{
            --primary: #ff2bd6;
            --primary-light: #79f7ff;
            --primary-dark: #a100ff;
            --secondary: #00ff9d;
            --secondary-light: #fff05a;
            --accent: #ff7a00;
            --success: #00ff9d;
            --danger: #ff2d55;
            --glass-bg: rgba(15, 8, 38, 0.24);
            --glass-bg-solid: rgba(22, 10, 54, 0.66);
            --glass-border: rgba(121, 247, 255, 0.36);
            --glass-hover: rgba(255, 43, 214, 0.16);
            --bg-main: #070313;
            --text: #fff8ff;
            --text-secondary: #dffcff;
            --text-muted: rgba(223, 252, 255, 0.72);
            --primary-rgb: 255, 43, 214;
            --primary-light-rgb: 121, 247, 255;
            --primary-dark-rgb: 161, 0, 255;
            --secondary-rgb: 0, 255, 157;
            --accent-rgb: 255, 122, 0;
            --line-rgb: 121, 247, 255;
            --shadow-rgb: 255, 43, 214;
            --glass-tint-rgb: 18, 9, 46;
            --glass-tint2-rgb: 55, 12, 86;
            --radius: 28px;
            --radius-sm: 18px;
            --th-bg-1: rgba(17, 9, 48, 0.76);
            --th-bg-2: rgba(67, 12, 92, 0.56);
            --th-sort-bg-1: rgba(255, 43, 214, 0.18);
            --th-sort-bg-2: rgba(0, 255, 157, 0.12);
            --th-sort-active-bg-1: rgba(255, 43, 214, 0.44);
            --th-sort-active-bg-2: rgba(121, 247, 255, 0.26);
        }}
        :root[data-theme="anime"] body {{
            background:
                radial-gradient(circle at 12% 10%, rgba(255, 43, 214, 0.42), transparent 26%),
                radial-gradient(circle at 88% 7%, rgba(0, 255, 157, 0.30), transparent 24%),
                radial-gradient(circle at 58% 92%, rgba(255, 122, 0, 0.34), transparent 32%),
                conic-gradient(from 210deg at 50% 45%, rgba(255, 43, 214, .26), rgba(121, 247, 255, .20), rgba(0,255,157,.18), rgba(255,240,90,.18), rgba(161,0,255,.24), rgba(255,43,214,.26)),
                #070313 !important;
            background-attachment: fixed !important;
        }}
        :root[data-theme="anime"] .bg-layer {{
            opacity: 1 !important;
            background:
                repeating-linear-gradient(100deg, rgba(255,255,255,.08) 0 1px, transparent 1px 18px),
                linear-gradient(115deg, transparent 0 20%, rgba(121,247,255,.24) 31%, transparent 42%, rgba(255,43,214,.22) 56%, transparent 70%),
                radial-gradient(circle at 20% 12%, rgba(255,255,255,.22), transparent 18%) !important;
            mix-blend-mode: screen;
        }}
        :root[data-theme="anime"] .bg-layer::after {{
            background:
                linear-gradient(96deg, transparent 0 12%, rgba(255, 43, 214, .42) 22%, rgba(121,247,255,.34) 34%, transparent 48%),
                linear-gradient(28deg, transparent 0 50%, rgba(0,255,157,.32) 62%, rgba(255,240,90,.22) 70%, transparent 86%) !important;
            filter: blur(18px) saturate(190%) !important;
            opacity: .9 !important;
        }}
        :root[data-theme="anime"] .hero {{
            background:
                linear-gradient(135deg, rgba(255,43,214,.22), rgba(121,247,255,.12) 45%, rgba(0,255,157,.10)),
                rgba(7, 3, 19, .38) !important;
            border-bottom: 1px solid rgba(121,247,255,.28) !important;
        }}
        :root[data-theme="anime"] .stat-card,
        :root[data-theme="anime"] .filter-card,
        :root[data-theme="anime"] .table-card,
        :root[data-theme="anime"] .disclaimer-inner,
        :root[data-theme="anime"] .sort-hint-inner {{
            border-radius: 28px !important;
            border: 1px solid rgba(121,247,255,.34) !important;
            background:
                linear-gradient(135deg, rgba(255,43,214,.20), rgba(121,247,255,.10) 34%, rgba(0,255,157,.09) 64%, rgba(255,122,0,.14)),
                rgba(10, 5, 28, .34) !important;
            box-shadow:
                0 24px 80px rgba(255,43,214,.26),
                0 0 42px rgba(121,247,255,.16),
                inset 0 1px 0 rgba(255,255,255,.32),
                inset 0 0 60px rgba(255,255,255,.06) !important;
            backdrop-filter: blur(42px) saturate(240%) contrast(122%) !important;
            -webkit-backdrop-filter: blur(42px) saturate(240%) contrast(122%) !important;
        }}
        :root[data-theme="anime"] .hero-title,
        :root[data-theme="anime"] .stat-value,
        :root[data-theme="anime"] .modpack-link,
        :root[data-theme="anime"] table.dataTable thead th,
        :root[data-theme="anime"] .filter-label {{
            background: linear-gradient(90deg, #fff, #79f7ff, #ff2bd6, #fff05a, #00ff9d, #fff) !important;
            background-size: 260% 100% !important;
            -webkit-background-clip: text !important;
            background-clip: text !important;
            color: transparent !important;
            -webkit-text-fill-color: transparent !important;
            text-shadow: 0 0 12px rgba(121,247,255,.35), 0 0 24px rgba(255,43,214,.24) !important;
            filter: drop-shadow(0 0 10px rgba(255,43,214,.20));
        }}
        :root[data-theme="anime"] .dataTables_scrollHead,
        :root[data-theme="anime"] .sort-strip,
        :root[data-theme="anime"] .dataTables_wrapper .dataTables_paginate {{
            background:
                linear-gradient(90deg, rgba(255,43,214,.30), rgba(121,247,255,.18), rgba(0,255,157,.18), rgba(255,122,0,.22)),
                rgba(7,3,19,.40) !important;
            border-color: rgba(121,247,255,.30) !important;
            box-shadow: 0 18px 54px rgba(255,43,214,.22), inset 0 1px 0 rgba(255,255,255,.28) !important;
        }}
        :root[data-theme="anime"] .header-sort-switcher,
        :root[data-theme="anime"] .filter-card .form-select,
        :root[data-theme="anime"] #searchScope,
        :root[data-theme="anime"] .dataTables_wrapper .dataTables_filter input,
        :root[data-theme="anime"] .select2-container--bootstrap-5 .select2-selection,
        :root[data-theme="anime"] .mod-details > summary {{
            border-color: rgba(121,247,255,.34) !important;
            background:
                linear-gradient(135deg, rgba(255,43,214,.18), rgba(121,247,255,.12), rgba(0,255,157,.08)),
                rgba(9, 4, 26, .42) !important;
            box-shadow: 0 10px 30px rgba(255,43,214,.14), inset 0 1px 0 rgba(255,255,255,.22) !important;
        }}
        :root[data-theme="anime"] .sort-option.active,
        :root[data-theme="anime"] .dataTables_wrapper .dataTables_paginate .paginate_button.current {{
            background: linear-gradient(135deg, #ff2bd6, #a100ff 42%, #79f7ff) !important;
            box-shadow: 0 0 22px rgba(255,43,214,.46), 0 0 14px rgba(121,247,255,.32) !important;
        }}
        :root[data-theme="anime"] .tag-cat,
        :root[data-theme="anime"] .tag-pack,
        :root[data-theme="anime"] .tag-mod,
        :root[data-theme="anime"] .mod-summary-chip {{
            border-radius: 999px !important;
            border-color: rgba(121,247,255,.24) !important;
            background: linear-gradient(135deg, rgba(255,43,214,.18), rgba(121,247,255,.10), rgba(0,255,157,.10)) !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.18), 0 5px 16px rgba(255,43,214,.10) !important;
        }}
        /* 最终控件重塑：筛选/搜索单选框与分页统一为圆润主题玻璃 */
        .filter-card {{
            border-radius: 30px !important;
            background:
                radial-gradient(circle at 18% 0%, rgba(var(--primary-rgb), .12), transparent 34%),
                linear-gradient(135deg, rgba(var(--glass-tint-rgb), .62), rgba(var(--glass-tint2-rgb), .30)),
                rgba(var(--glass-tint-rgb), .20) !important;
            border: 1px solid rgba(var(--primary-rgb), .20) !important;
            box-shadow: 0 22px 70px rgba(var(--shadow-rgb), .14), inset 0 1px 0 rgba(255,255,255,.24) !important;
            backdrop-filter: blur(46px) saturate(190%) contrast(112%) !important;
            -webkit-backdrop-filter: blur(46px) saturate(190%) contrast(112%) !important;
        }}
        .filter-col-type {{
            flex-basis: 190px !important;
            min-width: 190px !important;
        }}
        .filter-label {{
            font-size: .82rem !important;
            margin-bottom: .5rem !important;
            color: var(--text-secondary) !important;
            text-shadow: 0 1px 2px rgba(0,0,0,.16);
        }}
        .select2-container--bootstrap-5 .select2-selection.select2-glass-selection,
        .select2-container--bootstrap-5 .select2-selection.select2-glass-selection.select2-selection--single {{
            min-height: 54px !important;
            border-radius: 999px !important;
            padding: 0 42px 0 18px !important;
            background:
                linear-gradient(180deg, rgba(255,255,255,.30), rgba(255,255,255,.08)),
                linear-gradient(135deg, rgba(var(--glass-tint-rgb), .78), rgba(var(--glass-tint2-rgb), .46)) !important;
            border: 2px solid rgba(var(--primary-rgb), .26) !important;
            box-shadow:
                0 12px 30px rgba(var(--shadow-rgb), .12),
                inset 0 1px 0 rgba(255,255,255,.34),
                inset 0 -10px 24px rgba(var(--primary-rgb), .04) !important;
            backdrop-filter: blur(28px) saturate(180%) !important;
            -webkit-backdrop-filter: blur(28px) saturate(180%) !important;
        }}
        .select2-container--bootstrap-5.select2-container--open .select2-selection.select2-glass-selection,
        .select2-container--bootstrap-5.select2-container--focus .select2-selection.select2-glass-selection {{
            border-color: rgba(var(--primary-rgb), .52) !important;
            box-shadow:
                0 0 0 5px rgba(var(--primary-rgb), .13),
                0 18px 44px rgba(var(--shadow-rgb), .18),
                inset 0 1px 0 rgba(255,255,255,.38) !important;
        }}
        .select2-container--bootstrap-5 .select2-selection.select2-glass-selection .select2-selection__rendered {{
            line-height: 52px !important;
            padding-left: 0 !important;
            color: var(--text) !important;
            font-size: 1rem !important;
            font-weight: 900 !important;
        }}
        .select2-container--bootstrap-5 .select2-selection.select2-glass-selection .select2-selection__arrow {{
            width: 38px !important;
            height: 52px !important;
            right: 8px !important;
        }}
        .select2-container--bootstrap-5 .select2-selection.select2-glass-selection .select2-selection__arrow b {{
            border-color: var(--primary) transparent transparent transparent !important;
            border-width: 6px 5px 0 5px !important;
            filter: drop-shadow(0 2px 4px rgba(var(--primary-rgb), .22));
        }}
        .select2-container--bootstrap-5.select2-container--open .select2-selection.select2-glass-selection .select2-selection__arrow b {{
            border-color: transparent transparent var(--primary) transparent !important;
            border-width: 0 5px 6px 5px !important;
        }}
        .select2-dropdown.select2-glass-dropdown {{
            margin-top: 8px;
            border-radius: 26px !important;
            border: 1px solid rgba(var(--primary-rgb), .24) !important;
            background:
                linear-gradient(135deg, rgba(var(--glass-tint-rgb), .88), rgba(var(--glass-tint2-rgb), .68)),
                rgba(var(--glass-tint-rgb), .82) !important;
            box-shadow: 0 28px 74px rgba(var(--shadow-rgb), .22), inset 0 1px 0 rgba(255,255,255,.25) !important;
            backdrop-filter: blur(34px) saturate(190%) !important;
            -webkit-backdrop-filter: blur(34px) saturate(190%) !important;
            overflow: hidden;
        }}
        .select2-dropdown.select2-glass-dropdown .select2-results__options {{
            max-height: 360px !important;
            padding: 8px !important;
        }}
        .select2-dropdown.select2-glass-dropdown .select2-results__options::-webkit-scrollbar {{
            width: 12px;
        }}
        .select2-dropdown.select2-glass-dropdown .select2-results__options::-webkit-scrollbar-thumb {{
            border: 3px solid transparent;
            border-radius: 999px;
            background: linear-gradient(180deg, var(--primary), var(--secondary)) border-box;
        }}
        .select2-dropdown.select2-glass-dropdown .select2-results__option {{
            border-radius: 16px !important;
            padding: 11px 14px !important;
            margin: 2px 0 !important;
            font-size: 1rem !important;
            font-weight: 850 !important;
            color: var(--text) !important;
        }}
        .select2-dropdown.select2-glass-dropdown .select2-results__option--highlighted {{
            background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
            color: #fff !important;
            box-shadow: 0 8px 22px rgba(var(--primary-rgb), .22);
        }}
        .select2-dropdown.select2-glass-dropdown .select2-results__option--selected {{
            background: rgba(var(--primary-rgb), .14) !important;
            color: var(--text) !important;
        }}
        .dataTables_wrapper .dataTables_filter label {{
            border-radius: 999px !important;
            padding: 8px !important;
            background:
                linear-gradient(135deg, rgba(var(--glass-tint-rgb), .52), rgba(var(--glass-tint2-rgb), .22)),
                rgba(var(--glass-tint-rgb), .18) !important;
            border: 1px solid rgba(var(--primary-rgb), .16) !important;
            backdrop-filter: blur(30px) saturate(170%) !important;
            -webkit-backdrop-filter: blur(30px) saturate(170%) !important;
        }}
        .dataTables_wrapper .dataTables_filter input {{
            height: 54px !important;
            min-width: 280px !important;
            border-radius: 999px !important;
            padding: 0 18px !important;
            font-size: .96rem !important;
            font-weight: 800 !important;
        }}
        .dataTables_wrapper .dataTables_paginate.paging_simple_numbers {{
            float: none !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 3px !important;
            padding: 5px 7px !important;
            margin: .65rem auto .35rem !important;
            border-radius: 14px !important;
            background:
                linear-gradient(180deg, rgba(255,255,255,.30), rgba(255,255,255,.07)),
                linear-gradient(135deg, rgba(var(--glass-tint-rgb), .76), rgba(var(--glass-tint2-rgb), .36)) !important;
            border: 1px solid rgba(var(--primary-rgb), .18) !important;
            box-shadow: 0 8px 24px rgba(var(--shadow-rgb), .10), inset 0 1px 0 rgba(255,255,255,.26) !important;
            backdrop-filter: blur(22px) saturate(155%) !important;
            -webkit-backdrop-filter: blur(22px) saturate(155%) !important;
        }}
        .dataTables_wrapper .dataTables_paginate.paging_simple_numbers .paginate_button {{
            width: 30px !important;
            min-width: 30px !important;
            height: 30px !important;
            padding: 0 !important;
            margin: 0 !important;
            border-radius: 8px !important;
            background: rgba(var(--glass-tint-rgb), .42) !important;
            border: 1px solid rgba(var(--line-rgb), .10) !important;
            color: var(--text-secondary) !important;
            font-size: .82rem !important;
            font-weight: 800 !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.18) !important;
        }}
        .dataTables_wrapper .dataTables_paginate.paging_simple_numbers .paginate_button.previous,
        .dataTables_wrapper .dataTables_paginate.paging_simple_numbers .paginate_button.next {{
            width: 30px !important;
            min-width: 30px !important;
            color: var(--primary) !important;
            background: rgba(var(--primary-rgb), .08) !important;
        }}
        .dataTables_wrapper .dataTables_paginate.paging_simple_numbers .ellipsis {{
            width: 18px !important;
            min-width: 18px !important;
            color: var(--text-muted) !important;
        }}
        .dataTables_wrapper .dataTables_paginate.paging_simple_numbers .paginate_button.current,
        .dataTables_wrapper .dataTables_paginate.paging_simple_numbers .paginate_button.current:hover {{
            border-radius: 14px !important;
            background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
            border-color: rgba(var(--primary-rgb), .46) !important;
            color: #fff !important;
            box-shadow: 0 12px 28px rgba(var(--primary-rgb), .30), inset 0 1px 0 rgba(255,255,255,.28) !important;
        }}
        .dataTables_wrapper .dataTables_paginate .paginate_button.current,
        .dataTables_wrapper .dataTables_paginate .paginate_button.current:active,
        .dataTables_wrapper .dataTables_paginate .paginate_button.current:focus,
        .dataTables_wrapper .dataTables_paginate .paginate_button.current:hover {{
            background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
            border-color: rgba(var(--primary-rgb), .52) !important;
            color: #fff !important;
            background-color: var(--primary) !important;
            box-shadow: 0 12px 30px rgba(var(--primary-rgb), .32), inset 0 1px 0 rgba(255,255,255,.30) !important;
        }}
        div.dataTables_wrapper div.dataTables_paginate span .paginate_button.current,
        div.dataTables_wrapper div.dataTables_paginate span .paginate_button.current:hover,
        div.dataTables_wrapper div.dataTables_paginate a.paginate_button.current,
        div.dataTables_wrapper div.dataTables_paginate a.paginate_button.current:hover,
        .pagination .page-item.active .page-link,
        .page-item.active .page-link {{
            background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
            background-color: var(--primary) !important;
            border-color: rgba(var(--primary-rgb), .55) !important;
            color: #fff !important;
            box-shadow: 0 12px 30px rgba(var(--primary-rgb), .32), inset 0 1px 0 rgba(255,255,255,.30) !important;
        }}
        :root[data-theme="warm"] div.dataTables_wrapper div.dataTables_paginate .paginate_button.current,
        :root[data-theme="warm"] .page-item.active .page-link {{
            background: linear-gradient(135deg, #d97706, #7a6a34) !important;
            background-color: #d97706 !important;
        }}
        :root[data-theme="eye"] div.dataTables_wrapper div.dataTables_paginate .paginate_button.current,
        :root[data-theme="eye"] .page-item.active .page-link {{
            background: linear-gradient(135deg, #7a6a34, #4f7d67) !important;
            background-color: #7a6a34 !important;
        }}
        :root[data-theme="pink"] div.dataTables_wrapper div.dataTables_paginate .paginate_button.current,
        :root[data-theme="pink"] .page-item.active .page-link {{
            background: linear-gradient(135deg, #e84a8a, #8b5cf6) !important;
            background-color: #e84a8a !important;
        }}
        :root[data-theme="dark"] div.dataTables_wrapper div.dataTables_paginate .paginate_button.current,
        :root[data-theme="dark"] .page-item.active .page-link {{
            background: linear-gradient(135deg, #22d3ee, #a78bfa) !important;
            background-color: #22d3ee !important;
        }}
        .mod-container {{
            height: 100%;
            width: 100%;
            padding-right: 4px !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            overscroll-behavior: contain;
            scrollbar-gutter: stable;
        }}
        .td-mods {{
            height: 100%;
            min-width: 0;
        }}
        .td-mods .tag-wrap {{
            min-width: 100% !important;
        }}
        .mod-details {{
            width: 100%;
            min-height: 72px;
        }}
        .mod-details:not([open]) {{
            max-height: 84px;
            overflow: hidden;
        }}
        .mod-details:not([open]) .mod-details-body {{
            display: none !important;
        }}
        .mod-details[open] {{
            max-height: min(520px, 66vh);
            overflow: hidden;
        }}
        .mod-details[open] .mod-details-body {{
            max-height: calc(min(520px, 66vh) - 92px);
            overflow-y: auto;
            overflow-x: hidden;
            overscroll-behavior: contain;
            padding-right: 6px;
            scrollbar-width: thin;
            scrollbar-color: rgba(var(--primary-rgb), .35) transparent;
        }}
        .mod-details[open] .mod-details-body::-webkit-scrollbar {{
            width: 7px;
        }}
        .mod-details[open] .mod-details-body::-webkit-scrollbar-thumb {{
            background: rgba(var(--primary-rgb), .35);
            border-radius: 999px;
        }}
        .mod-details > summary {{
            min-height: 72px !important;
            height: auto;
            width: 100%;
            grid-template-columns: minmax(86px, auto) minmax(0, 1fr) 34px !important;
            gap: 12px !important;
            padding: 10px 12px !important;
            border-radius: 18px !important;
            background:
                radial-gradient(circle at 8% 20%, rgba(var(--primary-rgb), .18), transparent 34%),
                linear-gradient(135deg, rgba(var(--glass-tint-rgb), .66), rgba(var(--glass-tint2-rgb), .32)),
                rgba(var(--primary-rgb), .05) !important;
            border: 1px solid rgba(var(--primary-rgb), .24) !important;
            box-shadow:
                0 12px 30px rgba(var(--shadow-rgb), .10),
                inset 0 1px 0 rgba(255,255,255,.22),
                inset 0 -14px 30px rgba(var(--primary-rgb), .035) !important;
            backdrop-filter: blur(22px) saturate(165%) !important;
            -webkit-backdrop-filter: blur(22px) saturate(165%) !important;
        }}
        .mod-summary-main {{
            display: inline-flex !important;
            flex-direction: column;
            align-items: flex-start;
            gap: 3px;
            line-height: 1.05;
            font-size: .76rem !important;
            color: var(--text-secondary) !important;
        }}
        .mod-summary-main b {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 40px;
            padding: 2px 8px;
            border-radius: 999px;
            color: #fff !important;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            box-shadow: 0 8px 18px rgba(var(--primary-rgb), .20);
            font-size: .82rem;
        }}
        .mod-summary-cats {{
            width: 100%;
            max-height: none !important;
            display: flex !important;
            flex-wrap: wrap;
            align-items: center;
            justify-content: flex-start !important;
            gap: 5px;
            overflow: visible !important;
        }}
        .mod-details:not([open]) .mod-summary-cats {{
            mask-image: none;
            -webkit-mask-image: none;
        }}
        .mod-details[open] .mod-summary-cats {{
            max-height: none !important;
            mask-image: none;
            -webkit-mask-image: none;
        }}
        .mod-summary-chip {{
            padding: 3px 8px !important;
            border-radius: 999px !important;
            font-size: .72rem !important;
            background: rgba(var(--primary-rgb), .10) !important;
            border: 1px solid rgba(var(--primary-rgb), .18) !important;
        }}
        .mod-details > summary::after {{
            width: 34px !important;
            height: 34px !important;
            border-radius: 14px !important;
            background: linear-gradient(135deg, rgba(var(--primary-rgb), .18), rgba(var(--secondary-rgb), .12)) !important;
            color: var(--primary) !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.22);
        }}
        .filter-card-compact {{
            padding: 0.85rem !important;
        }}
        .filter-card-compact .filter-row {{
            display: grid !important;
            grid-template-columns: minmax(160px, .72fr) repeat(4, minmax(180px, 1fr)) minmax(160px, .72fr) auto;
            gap: 0.7rem !important;
            align-items: start !important;
        }}
        .filter-card-compact .filter-col,
        .filter-card-compact .filter-col-type {{
            min-width: 0 !important;
            flex: none !important;
        }}
        .filter-card-compact .filter-label {{
            display: inline-flex;
            align-items: center;
            min-height: 18px;
            margin-bottom: 0.26rem !important;
            font-size: .72rem !important;
            opacity: .9;
        }}
        .filter-card-compact .filter-tools {{
            min-height: 18px !important;
            margin-top: .22rem !important;
            justify-content: flex-start !important;
        }}
        .filter-card-compact .exclude-toggle {{
            padding: .08rem .46rem !important;
            font-size: .66rem !important;
        }}
        .filter-card-compact .select2-container--bootstrap-5 .select2-selection {{
            min-height: 36px !important;
        }}
        .filter-card-compact .select2-container--bootstrap-5 .select2-selection.select2-glass-selection,
        .filter-card-compact .select2-container--bootstrap-5 .select2-selection.select2-glass-selection.select2-selection--single {{
            min-height: 42px !important;
        }}
        .filter-card-compact .select2-container--bootstrap-5 .select2-selection.select2-glass-selection .select2-selection__rendered {{
            line-height: 40px !important;
            font-size: .88rem !important;
        }}
        .filter-card-compact .select2-container--bootstrap-5 .select2-selection.select2-glass-selection .select2-selection__arrow {{
            height: 40px !important;
        }}
        .filter-card-compact .hover-mode-panel {{
            margin-top: .65rem;
            padding-top: .65rem;
            border-top: 1px solid rgba(var(--line-rgb), .12);
        }}
        @media (max-width: 1600px) {{
            .filter-card-compact .filter-row {{
                grid-template-columns: repeat(3, minmax(180px, 1fr));
            }}
        }}
        @media (max-width: 900px) {{
            .filter-card-compact .filter-row {{
                grid-template-columns: 1fr;
            }}
        }}
        .td-title {{
            padding-left: 0.75rem !important;
            padding-right: 42px !important;
        }}
        table.dataTable tbody td.td-title {{
            padding-left: 0.75rem !important;
            padding-right: 42px !important;
        }}
        table.dataTable tbody td.td-title.has-cover {{
            padding-right: 122px !important;
        }}
        .fav-star {{
            position: absolute;
            right: 10px;
            top: 9px;
            transform: none;
            width: 28px;
            height: 28px;
            border-radius: 999px;
            border: 1px solid rgba(var(--primary-rgb), .18);
            background: rgba(var(--glass-tint-rgb), .38);
            color: var(--text-muted);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: .94rem;
            line-height: 1;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.14);
            transition: transform .16s ease, color .16s ease, background .16s ease, box-shadow .16s ease;
            z-index: 8;
        }}
        .fav-star:hover {{
            transform: scale(1.08);
            color: var(--primary);
            background: rgba(var(--primary-rgb), .12);
        }}
        .fav-star.active {{
            color: #fff;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-color: rgba(var(--primary-rgb), .42);
            box-shadow: 0 8px 22px rgba(var(--primary-rgb), .24), inset 0 1px 0 rgba(255,255,255,.24);
        }}
        .compare-tray {{
            position: fixed;
            left: 50%;
            bottom: 18px;
            top: auto;
            right: auto;
            transform: translateX(-50%) translateY(120%);
            z-index: 2147483000;
            width: min(860px, calc(100vw - 28px));
            min-height: 76px;
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            gap: 14px;
            align-items: center;
            padding: 12px 14px 12px 16px;
            border-radius: 24px;
            border: 1px solid rgba(var(--primary-rgb), .24);
            background:
                linear-gradient(135deg, rgba(var(--glass-tint-rgb), .76), rgba(var(--glass-tint2-rgb), .38)),
                rgba(var(--glass-tint-rgb), .32);
            box-shadow: 0 24px 70px rgba(var(--shadow-rgb), .22), inset 0 1px 0 rgba(255,255,255,.25);
            backdrop-filter: blur(34px) saturate(190%);
            -webkit-backdrop-filter: blur(34px) saturate(190%);
            opacity: 0;
            pointer-events: none;
            transition: transform .28s ease, opacity .22s ease;
            overflow: hidden;
        }}
        .compare-tray.show {{
            transform: translateX(-50%) translateY(0);
            opacity: 1;
            pointer-events: auto;
        }}
        .compare-tray-glow {{
            position: absolute;
            inset: -40% auto auto -8%;
            width: 260px;
            height: 160px;
            background: radial-gradient(circle, rgba(var(--primary-rgb), .24), transparent 68%);
            pointer-events: none;
        }}
        .compare-tray-main, .compare-tray-actions {{
            position: relative;
            z-index: 1;
        }}
        .compare-tray-kicker, .compare-kicker {{
            display: block;
            color: var(--primary);
            font-size: .68rem;
            font-weight: 950;
            letter-spacing: .04em;
            text-transform: uppercase;
        }}
        .compare-tray-main strong {{
            display: block;
            color: var(--text);
            font-size: 1rem;
            margin: 1px 0 5px;
        }}
        .compare-tray-names {{
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
            max-height: 28px;
            overflow: hidden;
        }}
        .compare-mini-chip {{
            padding: 3px 8px;
            border-radius: 999px;
            background: rgba(var(--primary-rgb), .10);
            border: 1px solid rgba(var(--primary-rgb), .16);
            color: var(--text-secondary);
            font-size: .72rem;
            font-weight: 800;
        }}
        .compare-tray-actions {{
            display: flex;
            gap: 8px;
            align-items: center;
        }}
        .compare-primary-btn, .compare-ghost-btn, .compare-close-btn {{
            border: 0;
            border-radius: 999px;
            padding: 10px 14px;
            font-weight: 950;
            cursor: pointer;
            color: var(--text);
        }}
        .compare-primary-btn {{
            color: #fff;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            box-shadow: 0 12px 28px rgba(var(--primary-rgb), .28);
        }}
        .compare-ghost-btn {{
            background: rgba(var(--glass-tint-rgb), .40);
            border: 1px solid rgba(var(--line-rgb), .14);
            color: var(--text-secondary);
        }}
        .compare-close-btn {{
            width: 42px;
            height: 42px;
            padding: 0;
            background: rgba(var(--glass-tint-rgb), .42);
            border: 1px solid rgba(var(--line-rgb), .14);
        }}
        .compare-overlay {{
            position: fixed;
            inset: 0;
            z-index: 2147483001;
            display: none;
            padding: 22px;
            background:
                radial-gradient(circle at 18% 0%, rgba(var(--primary-rgb), .18), transparent 34%),
                rgba(5, 8, 16, .42);
            backdrop-filter: blur(28px) saturate(170%);
            -webkit-backdrop-filter: blur(28px) saturate(170%);
        }}
        .compare-overlay.show {{
            display: block;
        }}
        .compare-shell {{
            height: calc(100vh - 44px);
            border-radius: 28px;
            border: 1px solid rgba(var(--primary-rgb), .24);
            background:
                linear-gradient(135deg, rgba(var(--glass-tint-rgb), .74), rgba(var(--glass-tint2-rgb), .34)),
                rgba(var(--glass-tint-rgb), .24);
            box-shadow: 0 30px 110px rgba(0,0,0,.34), inset 0 1px 0 rgba(255,255,255,.24);
            backdrop-filter: blur(42px) saturate(190%);
            -webkit-backdrop-filter: blur(42px) saturate(190%);
            display: grid;
            grid-template-rows: auto minmax(0, 1fr);
            overflow: hidden;
        }}
        .compare-head {{
            display: flex;
            justify-content: space-between;
            gap: 16px;
            align-items: center;
            padding: 18px 20px;
            border-bottom: 1px solid rgba(var(--line-rgb), .12);
        }}
        .compare-head h2 {{
            margin: 3px 0 0;
            color: var(--text);
            font-size: clamp(1.2rem, 2vw, 1.8rem);
            letter-spacing: 0;
        }}
        .compare-head-actions {{
            display: flex;
            gap: 8px;
            align-items: center;
        }}
        .compare-body {{
            overflow: auto;
            padding: 18px;
        }}
        .compare-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 12px;
            margin-bottom: 14px;
        }}
        .compare-card, .compare-section {{
            border-radius: 18px;
            border: 1px solid rgba(var(--line-rgb), .13);
            background: rgba(var(--glass-tint-rgb), .30);
            box-shadow: inset 0 1px 0 rgba(255,255,255,.12);
        }}
        .compare-card {{
            padding: 12px;
        }}
        .compare-card h3 {{
            margin: 0 0 8px;
            color: var(--text);
            font-size: .98rem;
        }}
        .compare-metric {{
            display: grid;
            grid-template-columns: 90px minmax(0, 1fr);
            gap: 8px;
            font-size: .78rem;
            color: var(--text-secondary);
            margin: 4px 0;
        }}
        .compare-metric b {{
            color: var(--primary);
            font-family: 'JetBrains Mono', monospace;
        }}
        .compare-section {{
            padding: 14px;
            margin: 12px 0;
        }}
        .compare-section h3 {{
            margin: 0 0 10px;
            font-size: 1rem;
            color: var(--text);
        }}
        .compare-chip-cloud {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}
        .compare-chip {{
            border-radius: 999px;
            padding: 4px 9px;
            background: rgba(var(--primary-rgb), .10);
            border: 1px solid rgba(var(--primary-rgb), .15);
            color: var(--text-secondary);
            font-size: .76rem;
            font-weight: 800;
        }}
        .compare-columns {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 12px;
        }}
        .compare-table-wrap {{
            overflow: auto;
            border-radius: 16px;
            border: 1px solid rgba(var(--line-rgb), .12);
        }}
        .compare-table {{
            width: 100%;
            border-collapse: collapse;
            min-width: 720px;
            font-size: .8rem;
        }}
        .compare-table th,
        .compare-table td {{
            padding: 8px 10px;
            border-bottom: 1px solid rgba(var(--line-rgb), .10);
            text-align: left;
            color: var(--text-secondary);
        }}
        .compare-table th {{
            position: sticky;
            top: 0;
            z-index: 1;
            background: rgba(var(--glass-tint-rgb), .78);
            color: var(--text);
            backdrop-filter: blur(18px);
        }}
        .compare-hit {{
            color: var(--primary);
            font-weight: 950;
        }}
        .compare-miss {{
            color: var(--text-muted);
            opacity: .55;
        }}
    </style>
</head>
<body>
<!-- 动画背景 -->
<div class="bg-layer"></div>
<div class="orb orb-1"></div>
<div class="orb orb-2"></div>
<div class="orb orb-3"></div>
<div class="hero">
    <div class="hero-inner">
        <div class="hero-title">{title}</div>
        <div class="hero-sub">基于 <a href="https://www.mcmod.cn/" target="_blank">mcmod.cn</a> 公开数据整理 · 仅供学习交流参考</div>
        <div class="theme-switcher" style="margin-top: 1rem; align-items: center; display: inline-flex; gap: 8px; padding: 6px 12px; background: rgba(var(--glass-tint-rgb), 0.25); border: 1px solid rgba(var(--line-rgb), 0.12); border-radius: 12px; backdrop-filter: blur(8px);">
            <span style="font-size: 0.75rem; font-weight: 600; color: var(--text-secondary); margin-right: 4px; user-select: none; letter-spacing: 0.5px;">切换主题</span>
            <div class="theme-btn theme-btn-light active" data-theme="light" title="冷白现代风"><span class="theme-dot" style="background: #2563eb;"></span>冷白</div>
            <div class="theme-btn theme-btn-dark" data-theme="dark" title="深邃毛玻璃"><span class="theme-dot" style="background: #6366f1;"></span>深邃</div>
            <div class="theme-btn theme-btn-warm" data-theme="warm" title="暖橘秋意"><span class="theme-dot" style="background: #d97706;"></span>温润</div>
            <div class="theme-btn theme-btn-eye" data-theme="eye" title="绿意护眼"><span class="theme-dot" style="background: #059669;"></span>护眼</div>
            <div class="theme-btn theme-btn-pink" data-theme="pink" title="樱花粉"><span class="theme-dot" style="background: #ec4899;"></span>樱粉</div>
            <div class="theme-btn theme-btn-anime" data-theme="anime" title="流光玻璃"><span class="theme-dot" style="background: #8b5cf6;"></span>流光</div>
        </div>
    </div>
</div>
<div class="stats-bar">
    <div class="stat-card">
        <div class="stat-icon s1">📦</div>
        <div>
            <div class="stat-label">整合包总数</div>
            <div class="stat-value" id="statTotal">{total}</div>
        </div>
    </div>
    <div class="stat-card">
        <div class="stat-icon s2">👁️</div>
        <div>
            <div class="stat-label">总浏览量（全部）</div>
            <div class="stat-value" id="statViews">{total_views}</div>
        </div>
    </div>
    <div class="stat-card">
        <div class="stat-icon s3">💬</div>
        <div>
            <div class="stat-label">总评论数（含楼中楼）</div>
            <div class="stat-value" id="statComments">{total_comments}</div>
        </div>
    </div>
</div>
<details class="notice-wrap notice-compact">
    <summary>ℹ️ 说明与免责声明</summary>
    <div class="disclaimer-inner" style="margin-bottom:0.55rem;">
        <strong>📋 免责声明</strong><br>
        本页面仅为个人整理与学习交流用途，不涉及任何商业用途。排序、热度等数据均基于公开信息整理或统计，<strong>仅供参考，不代表任何作品或作者的实际质量评价，也不构成排名高低优劣的结论。</strong>如涉及版权、数据使用或其他权益问题，请联系我处理，我会第一时间修改或删除相关内容。本项目与<a href="https://www.mcmod.cn/" target="_blank">MC百科</a>（mcmod.cn）及相关作者无官方关联。
    </div>
    <div class="sort-hint-inner">
        <span style="font-size:1rem;">💡</span>看板操作说明
        <span><b>排序：</b>点击表头排序，再次点击切换 ↑升序 / ↓降序，蓝色条内的小项可直接切换同组排序。<b>详情：</b>整合包名称悬停查看介绍；趋势列小波形可直接读日期/指数，默认点击趋势格打开或关闭大图，可开启悬浮模式；评论列默认点击打开或关闭详情，也可开启悬浮模式。<b>筛选：</b>分类、标签、模组分类和模组可多选，也可开启「排除所选」反向筛选；分页可切换每页 25 / 50 / 100 / 200 条。</span>
    </div>
</details>
<div class="main-wrap">
    <div class="filter-card filter-card-compact">
        <div class="filter-row">
            <div class="filter-col filter-col-type">
                <label class="filter-label">整合包类型</label>
                <select id="typeFilter" class="form-select select2-glass-single" data-placeholder="全部类型">
                    <option value="">全部类型（{total}）</option>
{type_opts}
                </select>
            </div>
            <div class="filter-col">
                <label class="filter-label">📌 分类标签</label>
                <select id="categoryFilter" class="form-select select2-basic" multiple="multiple" data-placeholder="全部分类">
{cat_opts}
                </select>
                <div class="filter-tools"><label class="exclude-toggle" title="选中的分类改为排除"><input type="checkbox" id="categoryExclude">排除所选</label></div>
            </div>
            <div class="filter-col">
                <label class="filter-label">🏷️ 整合包标签（含频次）</label>
                <select id="packTagFilter" class="form-select select2-basic" multiple="multiple" data-placeholder="全部标签">
{pack_opts}
                </select>
                <div class="filter-tools"><label class="exclude-toggle" title="选中的标签改为排除"><input type="checkbox" id="packTagExclude">排除所选</label></div>
            </div>
            <div class="filter-col">
                <label class="filter-label">🧩 模组分类（含频次）</label>
                <select id="modCategoryFilter" class="form-select select2-basic" multiple="multiple" data-placeholder="全部模组分类">
{mod_cat_opts}
                </select>
                <div class="filter-tools"><label class="exclude-toggle" title="选中的模组分类改为排除"><input type="checkbox" id="modCategoryExclude">排除所选</label></div>
            </div>
            <div class="filter-col">
                <label class="filter-label">🔗 包含模组（含频次）</label>
                <select id="modFilter" class="form-select select2-basic" multiple="multiple" data-placeholder="全部模组">
{mod_opts}
                </select>
                <div class="filter-tools"><label class="exclude-toggle" title="选中的模组改为排除"><input type="checkbox" id="modExclude">排除所选</label></div>
            </div>
            <div class="filter-col">
                <label class="filter-label">📈 走势周期</label>
                <select id="trendFilter" class="form-select select2-glass-single" data-placeholder="全部走势">
                    <option value="">全部（{total}）</option>
{trend_opts}
                </select>
            </div>
            <div class="filter-col-btn">
                <button id="resetFilters" class="btn-reset">重置筛选</button>
            </div>
        </div>
        <div class="hover-mode-panel" aria-label="悬浮模式开关">
            <span class="hover-mode-label">悬浮打开</span>
            <label class="mode-toggle mode-toggle-header" title="开启后悬停整合包名称显示介绍；关闭后点击名称打开/关闭"><span>介绍</span><input type="checkbox" class="js-desc-hover-toggle"></label>
            <label class="mode-toggle mode-toggle-header" title="开启后悬停趋势格显示趋势图；关闭后点击趋势格打开/关闭"><span>趋势</span><input type="checkbox" class="js-trend-hover-toggle"></label>
            <label class="mode-toggle mode-toggle-header" title="开启后悬停评论格显示评论详情；关闭后点击评论格打开/关闭"><span>评论</span><input type="checkbox" class="js-comment-hover-toggle"></label>
        </div>
    </div>
    <div class="table-card">
        <div class="table-responsive">
            <table id="modpackTable" class="table table-hover align-middle" style="width:100%">
                <thead>
                    <tr>
                        <th class="header-consolidated" style="min-width:220px">
                            <div class="header-sort-switcher title-sort-switcher" data-col="0">
                                <span class="sort-option active" data-subkey="name">名称</span>
                                <span class="sort-option" data-subkey="views">浏览</span>
                            </div>
                        </th>
                        <th class="header-consolidated" style="min-width:170px">
                            <div class="header-sort-switcher" data-col="1">
                                <span class="sort-option active" data-subkey="score">流行</span>
                                <span class="sort-option" data-subkey="lat">最新</span>
                                <span class="sort-option" data-subkey="max">最高</span>
                                <span class="sort-option" data-subkey="avg">平均</span>
                                <span class="sort-option" data-subkey="days">天数</span>
                            </div>
                        </th>
                        <th class="header-consolidated" style="min-width:140px">
                            <div class="header-sort-switcher" data-col="2">
                                <span class="sort-option active" data-subkey="t7">7日</span>
                                <span class="sort-option" data-subkey="t30">30日</span>
                                <span class="sort-option" data-subkey="t60">60日</span>
                                <span class="sort-option" data-subkey="tall">总幅</span>
                            </div>
                        </th>
                        <th class="header-consolidated" style="min-width:140px">
                            <div class="header-sort-switcher" data-col="3">
                                <span class="sort-option active" data-subkey="rv">红票</span>
                                <span class="sort-option" data-subkey="rp">红占比</span>
                                <span class="sort-option" data-subkey="bv">黑票</span>
                                <span class="sort-option" data-subkey="bp">黑占比</span>
                            </div>
                        </th>
                        <th class="header-consolidated" style="min-width:132px">
                            <div class="header-sort-switcher" data-col="4">
                                <span class="sort-option active" data-subkey="com">评论</span>
                                <span class="sort-option" data-subkey="rec">推荐</span>
                                <span class="sort-option" data-subkey="fav">收藏</span>
                            </div>
                        </th>
                        <th class="header-consolidated" style="min-width:280px">
                            <div class="header-sort-switcher" data-col="5">
                                <span class="sort-option active" data-subkey="count">标签</span>
                            </div>
                        </th>
                        <th class="header-consolidated" style="min-width:420px;width:38vw">
                            <div class="header-sort-switcher" data-col="6">
                                <span class="sort-option active" data-subkey="count">包含模组</span>
                            </div>
                        </th>
                    </tr>
                </thead>
                <tbody>
{rows}
                </tbody>
            </table>
    </div>
</div>
<div id="compareTray" class="compare-tray" aria-live="polite">
    <div class="compare-tray-glow"></div>
    <div class="compare-tray-main">
        <span class="compare-tray-kicker">收藏对比</span>
        <strong id="compareTrayCount">0 个整合包</strong>
        <div id="compareTrayNames" class="compare-tray-names"></div>
    </div>
    <div class="compare-tray-actions">
        <button type="button" id="compareClear" class="compare-ghost-btn">清空</button>
        <button type="button" id="compareOpen" class="compare-primary-btn">全面对比</button>
    </div>
</div>
<div id="compareOverlay" class="compare-overlay" aria-hidden="true">
    <div class="compare-shell" role="dialog" aria-modal="true" aria-labelledby="compareTitle">
        <div class="compare-head">
            <div>
                <span class="compare-kicker">Modpack Intelligence</span>
                <h2 id="compareTitle">收藏整合包全面对比</h2>
            </div>
            <div class="compare-head-actions">
                <button type="button" id="compareCopy" class="compare-ghost-btn">复制摘要</button>
                <button type="button" id="compareClose" class="compare-close-btn" aria-label="关闭">✕</button>
            </div>
        </div>
        <div id="compareBody" class="compare-body"></div>
    </div>
</div>
</div>
<!-- ─── 整合包介绍预览窗 ─── -->
<div id="pvPopup" class="pv-popup" role="dialog" aria-hidden="true">
    <div class="pv-head">
        <div class="pv-head-icon">📦</div>
        <span class="pv-head-title" id="pvTitle"></span>
        <div class="pv-actions">
            <a id="pvOpen" href="#" target="_blank" title="在新标签页打开 ↗">↗</a>
            <button type="button" class="hover-close" id="pvClose" title="关闭，短时间内不再弹出这个整合包">✕</button>
        </div>
    </div>
    <div class="pv-body" id="pvBody"></div>
    <div class="pv-tip" style="line-height:1.6;">
        📋 本页面仅作信息整理预览，含已抓取图片预览但不保证完整排版 · 鼠标移出会正常关闭且不进入冷却 · 点 ✕ 后 5 秒内悬停同一整合包不会再弹出 · 详细内容请访问 <a href="https://www.mcmod.cn/" target="_blank" style="color:var(--primary-dark);font-weight:600;">MC百科 mcmod.cn</a> 原页面查看
    </div>
    <div class="mcmod-consent">
        <div class="mcmod-consent-panel">
            <div class="mcmod-consent-brand">MC百科</div>
            <div class="mcmod-consent-title">内容来自 mcmod.cn 公开页面</div>
            <div class="mcmod-consent-text">这里显示的是本地整理预览，图片为已抓取链接预览，完整排版与最新修订请以 MC百科 原页面为准。确认后继续查看介绍内容。</div>
            <button type="button" class="mcmod-consent-ok">知道了</button>
        </div>
    </div>
</div>
<!-- ─── 评论悬浮窗 ─── -->
<div id="commentPopup" class="comment-popup">
    <div class="comment-head">
        <div class="comment-head-icon">💬</div>
        <span class="comment-head-title">评论详情</span>
        <input id="commentSearchInput" class="comment-search-input" type="search" placeholder="搜索当前整合包的评论内容" autocomplete="off">
        <span id="commentCount"></span>
        <div class="pv-actions">
            <a id="commentOpen" href="#" target="_blank" title="打开 MC百科原页面 ↗">↗</a>
            <button type="button" class="hover-close" id="commentClose" title="关闭评论详情">✕</button>
        </div>
    </div>
    <div class="comment-body" id="commentBody"></div>
    <div class="scroll-hint-arrow"><span>滚动查看更多</span> ↓</div>
    <div class="comment-search-nav" id="commentSearchNav" style="display:none;">
        <span class="search-nav-info" id="searchNavInfo"></span>
        <span class="search-nav-btn" id="searchNavPrev" title="上一个匹配">上一个匹配</span>
        <span class="search-nav-btn" id="searchNavNext" title="下一个匹配">下一个匹配</span>
    </div>
    <div class="comment-page-bar" id="commentPageBar" style="display:none;">
        <span class="comment-page-btn" id="cmtFirst" title="第一页">«</span>
        <span class="comment-page-btn" id="cmtPrev" title="上一页">‹</span>
        <span class="comment-page-info" id="cmtPageInfo"></span>
        <span class="comment-page-btn" id="cmtNext" title="下一页">›</span>
        <span class="comment-page-btn" id="cmtLast" title="最后一页">»</span>
    </div>
    <div class="comment-tip">
        📋 评论整理与检索辅助 · 按 Esc、点窗外或点评论格可关闭 · 完整上下文与最新内容请访问 <a href="https://www.mcmod.cn/" target="_blank" id="commentModpackLink">MC百科 mcmod.cn</a>
    </div>
    <div class="mcmod-consent">
        <div class="mcmod-consent-panel">
            <div class="mcmod-consent-brand">MC百科</div>
            <div class="mcmod-consent-title">评论来自 mcmod.cn 公开页面</div>
            <div class="mcmod-consent-text">评论仅作整理与检索辅助，完整上下文请以 MC百科原页面为准。确认后继续查看评论。</div>
            <button type="button" class="mcmod-consent-ok">知道了</button>
        </div>
    </div>
</div>
<div id="imageLightbox" class="image-lightbox" aria-hidden="true">
    <div class="image-lightbox-panel">
        <button type="button" class="image-lightbox-close" id="imageLightboxClose" aria-label="关闭">×</button>
        <img class="image-lightbox-img" id="imageLightboxImg" src="" alt="">
        <div class="image-lightbox-caption">
            <span id="imageLightboxTitle"></span>
            <a id="imageLightboxOpen" href="#" target="_blank" rel="noreferrer">打开原图 ↗</a>
        </div>
    </div>
</div>
<script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/datatables.net/js/jquery.dataTables.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/datatables.net-bs5@1.13.6/js/dataTables.bootstrap5.min.js"></script>
<script>
$(document).ready(function() {{
    var dashboardApiBase = {dashboard_api_base_json};
    /* ════════ 主题切换 ════════ */
    var savedTheme = localStorage.getItem('mcmod-theme-v2') || '{default_theme}';
    function setTheme(theme) {{
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('mcmod-theme-v2', theme);
        $('.theme-btn').removeClass('active');
        $('.theme-btn[data-theme="' + theme + '"]').addClass('active');
    }}
    setTheme(savedTheme);
    $('.theme-btn').on('click', function() {{
        setTheme($(this).data('theme'));
    }});
    $('.select2-basic').select2({{
        theme: 'bootstrap-5',
        width: '100%',
        closeOnSelect: false,
        placeholder: function() {{ return $(this).data('placeholder') || '全部'; }}
    }});
    $('.select2-glass-single').select2({{
        theme: 'bootstrap-5',
        width: '100%',
        minimumResultsForSearch: 8,
        selectionCssClass: 'select2-glass-selection',
        dropdownCssClass: 'select2-glass-dropdown',
        placeholder: function() {{ return $(this).data('placeholder') || '全部'; }}
    }});
    /* ════════ DataTables 初始化（scrollY 固定表头 + 分页优化） ════════ */
    // 🌟 性能优化：将重量级的表格初始化推入下一个事件循环，让 Select2 优先完成重绘，彻底解除页面开启瞬间的 UI 卡死
    fetch(dashboardApiBase + '/table', {{ cache: 'no-store' }})
        .then(function(resp) {{ if (!resp.ok) throw new Error('HTTP ' + resp.status); return resp.text(); }})
        .then(function(rows) {{ $('#modpackTable tbody').html(rows); }})
        .catch(function(err) {{
            $('#modpackTable tbody').html('<tr><td colspan="7" style="padding:2rem;text-align:center">看板数据加载失败。请直接运行转换器，它会自动打开看板。</td></tr>');
        }})
        .finally(function() {{ setTimeout(function() {{
        /* ════════ 全文穿透搜索引擎：支持范围自定义的全局检索 ════════ */
        function normalizeSearchKeyword() {{
            var $filterInput = $('#modpackTable_filter input');
            return $filterInput.length > 0 ? $filterInput.val().trim() : '';
        }}
        function textHasKeyword(text, keyword) {{
            return !!(text && keyword && String(text).toLowerCase().indexOf(keyword.toLowerCase()) !== -1);
        }}
        function findCommentMatch(cmt, keyword) {{
            if (!cmt || !cmt.comments || !keyword) return -1;
            for (var j = 0; j < cmt.comments.length; j++) {{
                var c = cmt.comments[j];
                if (textHasKeyword(c.text, keyword) || textHasKeyword(c.author, keyword)) return j;
                if (c.replies) {{
                    for (var k = 0; k < c.replies.length; k++) {{
                        var r = c.replies[k];
                        if (textHasKeyword(r.text, keyword) || textHasKeyword(r.author, keyword)) return j;
                    }}
                }}
            }}
            return -1;
        }}
        function matchRowSearch(data, tr, keyword, scope) {{
            var result = {{ basic: false, title: false, cat: false, desc: false, comment: false, commentIndex: -1 }};
            if (!keyword) return result;
            var kw = keyword.toLowerCase();
            for (var i = 0; i < data.length; i++) {{
                if (String(data[i] || '').toLowerCase().indexOf(kw) !== -1) {{
                    result.basic = true; break;
                }}
            }}
            result.title = String(data[0] || '').toLowerCase().indexOf(kw) !== -1;
            result.cat = String(data[6] || '').toLowerCase().indexOf(kw) !== -1 ||
                         String(data[7] || '').toLowerCase().indexOf(kw) !== -1;
            var mid = $(tr).find('a.modpack-link').data('mid');
            if (mid) {{
                result.desc = textHasKeyword(getDescText(descData[mid]), keyword);
                result.commentIndex = findCommentMatch(commentData[mid], keyword);
                result.comment = result.commentIndex >= 0;
            }}
            return result;
        }}
        function rowMatchesScope(match, scope) {{
            if (scope === 'title') return match.title;
            if (scope === 'cat') return match.cat;
            if (scope === 'desc') return match.desc;
            if (scope === 'comment') return match.comment;
            if (scope === 'basic') return match.basic;
            return match.basic || match.desc || match.comment;
        }}
        $.fn.dataTable.ext.search.push(
            function(settings, data, dataIndex) {{
                var keyword = normalizeSearchKeyword();
                if (!keyword) return true;
                var scope = $('#searchScope').val() || 'all';
                var tr = settings.aoData[dataIndex].nTr;
                return rowMatchesScope(matchRowSearch(data, tr, keyword, scope), scope);
            }}
        );
        var _scrollH = Math.max(400, $(window).height() - 320);
    var table = $('#modpackTable').DataTable({{
        "scrollX": true,
        "autoWidth": false,
        "search": {{
            "smart": false
        }},
        "order": [[1, "desc"]],       // 默认按「官方流行指数」降序（已并入趋势列）
        "pageLength": 25,             // ★ 默认每页 25 条
        "paging": true,
        "deferRender": true,
        "lengthChange": true,
        "lengthMenu": [[25, 50, 100, 200, -1], [25, 50, 100, 200, "全部"]],
        "scrollY": _scrollH,
        "scrollCollapse": true,
        "language": {{
            "search": "🔍 全局关键字检索：",
            "info": "当前第 _START_ - _END_ 条 / 共 _TOTAL_ 条 · 筛选自 _MAX_ 条",
            "infoEmpty": "暂无匹配记录",
            "infoFiltered": "(从 _MAX_ 条总记录中筛选)",
            "zeroRecords": "没有找到符合条件的整合包",
            "lengthMenu": "每页显示 _MENU_ 条",
            "paginate": {{
                "first": "«",
                "last": "»",
                "next": "›",
                "previous": "‹"
            }}
        }},
        "columnDefs": [
            {{ "width": "220px", "targets": 0 }},
            {{ "width": "150px", "targets": 1 }},
            {{ "width": "118px", "targets": 2 }},
            {{ "width": "112px", "targets": 3 }},
            {{ "width": "104px", "targets": 4 }},
            {{ "width": "220px", "targets": 5 }},
            {{ "width": "calc(100vw - 900px)", "targets": 6 }},
            {{ "orderable": true,  "targets": [0,1,2,3,4,5,6] }}
        ],
        "initComplete": function() {{
            var api = this.api();
            /* 将每页条数选择器移到右上角 */
            var $wrapper = $(this.api().table().container());
            var $length = $wrapper.find('.dataTables_length');
            var $filter = $wrapper.find('.dataTables_filter');
            var $info = $wrapper.find('.dataTables_info');
            var $paginate = $wrapper.find('.dataTables_paginate');
            /* 每页条数必须紧挨搜索框显示，不能只依赖 DataTables 默认的页尾位置。 */
            $length.addClass('page-size-control').detach().prependTo($filter);
            $length.css({{ 'display': 'inline-flex', 'align-items': 'center', 'margin-right': '0.8rem' }});
            $length.find('select').attr('aria-label', '选择每页显示数量').val(api.page.len());
            $filter.css({{ 'display': 'inline-block', 'float': 'right' }});
            $info.css({{ 'padding-top': '0.6rem', 'clear': 'both' }});
            $paginate.css({{ 'padding-top': '0.3rem', 'text-align': 'center' }});
            /* ★ 动态注入：全局搜索靶向选择器 */
            var scopeSelect = '<select id="searchScope" class="form-select form-select-sm d-inline-block w-auto me-2 select2-glass-single" data-placeholder="穿透搜索">' +
                              '<option value="all">🔍 穿透搜索 (全部内容)</option>' +
                              '<option value="title">📘 仅搜整合包名称</option>' +
                              '<option value="cat">🏷️ 仅搜分类与标签</option>' +
                              '<option value="desc">📖 仅搜百科长篇介绍</option>' +
                              '<option value="comment">💬 仅搜评论与讨论区</option>' +
                              '</select>';
            $filter.find('label').prepend(scopeSelect);
            $('#searchScope').select2({{
                theme: 'bootstrap-5',
                width: '210px',
                minimumResultsForSearch: Infinity,
                selectionCssClass: 'select2-glass-selection',
                dropdownCssClass: 'select2-glass-dropdown search-scope-dropdown'
            }});
            var $searchNav = $('<span class="search-nav" id="searchNav" style="display:none;"><span class="search-nav-info" id="searchNavInfo">0 / 0</span><button type="button" class="search-nav-btn" id="searchPrev" title="上一个搜索结果">‹</button><button type="button" class="search-nav-btn" id="searchNext" title="下一个搜索结果">›</button><button type="button" class="search-nav-btn" id="searchOpen" title="打开命中的介绍或评论">⌖</button></span>');
            $filter.find('label').append($searchNav);
            var searchHits = [];
            var searchHitIndex = -1;
            var rawCellHtml = new WeakMap();
            function restoreSearchHighlights() {{
                $wrapper.find('tbody td').each(function() {{
                    var raw = rawCellHtml.get(this);
                    if (raw !== undefined) {{
                        this.innerHTML = raw;
                    }}
                }});
                $wrapper.find('tbody tr').removeClass('search-hit-row search-current-row');
            }}
            function highlightCell($td, keyword) {{
                if (!$td.length || !keyword) return;
                var node = $td[0];
                if (!rawCellHtml.has(node)) rawCellHtml.set(node, node.innerHTML);
                var rawText = $td.text();
                if (!textHasKeyword(rawText, keyword)) return;
                node.innerHTML = highlightText(rawText, keyword);
            }}
            function updateSearchNav() {{
                var keyword = normalizeSearchKeyword();
                var scope = $('#searchScope').val() || 'all';
                restoreSearchHighlights();
                searchHits = [];
                searchHitIndex = -1;
                if (!keyword) {{
                    $('#searchNav').hide();
                    return;
                }}
                table.rows({{ search: 'applied' }}).every(function() {{
                    var tr = this.node();
                    var data = this.data();
                    var match = matchRowSearch(data, tr, keyword, scope);
                    if (!rowMatchesScope(match, scope)) return;
                    var $tr = $(tr);
                    var hitType = match.title ? 'title' : match.cat ? 'cat' : match.desc ? 'desc' : match.comment ? 'comment' : 'basic';
                    if (scope === 'desc') hitType = 'desc';
                    if (scope === 'comment') hitType = 'comment';
                    if (scope === 'cat') hitType = 'cat';
                    if (scope === 'title') hitType = 'title';
                    $tr.addClass('search-hit-row');
                    if (hitType === 'title' || hitType === 'basic') highlightCell($tr.children('td').eq(0), keyword);
                    if (hitType === 'cat' || hitType === 'basic') {{
                        highlightCell($tr.children('td').eq(5), keyword);
                        highlightCell($tr.children('td').eq(6), keyword);
                        if ($tr.children('td').eq(6).text().toLowerCase().indexOf(keyword.toLowerCase()) !== -1) {{
                            $tr.find('.mod-details').prop('open', true);
                        }}
                    }}
                    searchHits.push({{ tr: tr, type: hitType, commentIndex: match.commentIndex }});
                }});
                if (searchHits.length > 0) searchHitIndex = 0;
                $('#searchNav').show();
                refreshSearchNavState(false);
            }}
            function refreshSearchNavState(scrollToRow) {{
                var total = searchHits.length;
                $('#searchNavInfo').text(total ? ((searchHitIndex + 1) + ' / ' + total) : '0 / 0');
                $('#searchPrev, #searchNext, #searchOpen').prop('disabled', total === 0);
                $wrapper.find('tbody tr').removeClass('search-current-row');
                if (!total) return;
                var hit = searchHits[searchHitIndex];
                var $tr = $(hit.tr).addClass('search-current-row');
                if (scrollToRow && $tr.length) {{
                    var body = $wrapper.find('.dataTables_scrollBody')[0];
                    if (body) {{
                        body.scrollTop = Math.max(0, hit.tr.offsetTop - 72);
                    }} else {{
                        hit.tr.scrollIntoView({{ block: 'center', behavior: 'smooth' }});
                    }}
                }}
            }}
            function jumpSearch(delta) {{
                if (!searchHits.length) return;
                searchHitIndex = (searchHitIndex + delta + searchHits.length) % searchHits.length;
                refreshSearchNavState(true);
            }}
            function openSearchHit() {{
                if (!searchHits.length) return;
                refreshSearchNavState(true);
                var hit = searchHits[searchHitIndex];
                var $tr = $(hit.tr);
                if (hit.type === 'comment') {{
                    showCommentPopup($tr.children('td.td-comment'));
                }} else {{
                    showDescPopup($tr.find('a.modpack-link'));
                }}
            }}
            $('#searchScope').on('change', function() {{ table.draw(); }});
            $('#searchPrev').on('click', function() {{ jumpSearch(-1); }});
            $('#searchNext').on('click', function() {{ jumpSearch(1); }});
            $('#searchOpen').on('click', function() {{ openSearchHit(); }});
            /* ★ 强力拦截：解除 DataTables 原生绑定的搜索框事件，防止原生过滤机制对无单元格内容的评论进行误杀 */
            var $filterInput = $filter.find('input');
            $filterInput.off('keyup.DT search.DT input.DT paste.DT cut.DT');
            var searchTimer = null;
            $filterInput.on('keyup input', function() {{
                clearTimeout(searchTimer);
                searchTimer = setTimeout(function() {{
                    table.draw();
                }}, 100);
            }});
            /* ★ [v10.0] 顶部数据栏跟随横向滚动 */
            var $scrollBody = $wrapper.find('.dataTables_scrollBody');
            var $scrollHead = $wrapper.find('.dataTables_scrollHead');
            var $sortStrip = $('<div class="sort-strip"><div class="sort-strip-inner"></div></div>');
            $scrollHead.append($sortStrip);
            var $sortStripInner = $sortStrip.find('.sort-strip-inner');
            $scrollBody.on('scroll', function() {{
                $scrollHead.scrollLeft($(this).scrollLeft());
                $sortStrip.scrollLeft($(this).scrollLeft());
            }});
            $scrollHead.find('th').off('.DT');
            function rebuildSortStrip() {{
                var html = '';
                var maxRight = 0;
                var $headTable = $wrapper.find('.dataTables_scrollHead table').first();
                $wrapper.find('.dataTables_scrollHead thead tr:first th').each(function(idx) {{
                    var left = Math.round(this.offsetLeft || 0);
                    var w = Math.ceil(this.getBoundingClientRect().width || $(this).outerWidth());
                    if (w < 1) return;
                    html += '<button type="button" class="sort-strip-seg" data-col="' + idx + '" title="' + $(this).text().trim() + '" style="left:' + left + 'px;width:' + w + 'px"></button>';
                    maxRight = Math.max(maxRight, left + w);
                }});
                var tableW = Math.ceil($headTable.outerWidth() || maxRight);
                $sortStripInner.css('width', Math.max(maxRight, tableW) + 'px').html(html);
            }}
            function refreshActiveSortColumn() {{
                var order = api.order();
                var colIdx = order && order.length ? order[0][0] : 2;
                var dir = order && order.length ? order[0][1] : 'desc';
                $wrapper.find('th, td').removeClass('dt-active-sort');
                $wrapper.find('.dataTables_scrollHead th').eq(colIdx).addClass('dt-active-sort').attr('data-order-dir', dir);
                $sortStrip.find('.sort-strip-seg').removeClass('active').attr('data-order-dir', '');
                $sortStrip.find('.sort-strip-seg[data-col="' + colIdx + '"]').addClass('active').attr('data-order-dir', dir);
                $wrapper.find('.dataTables_scrollBody tbody tr').each(function() {{
                    $(this).children('td').eq(colIdx).addClass('dt-active-sort');
                }});
            }}
            function sortByColumn(colIdx) {{
                if (colIdx < 0 || colIdx > 6) return;
                var current = api.order();
                var currentIdx = current && current.length ? current[0][0] : -1;
                var currentDir = current && current.length ? current[0][1] : 'desc';
                var nextDir = (currentIdx === colIdx && currentDir === 'asc') ? 'desc' : 'asc';
                api.order([colIdx, nextDir]).draw();
                refreshActiveSortColumn();
            }}
            $wrapper.on('click', '.sort-option', function(e) {{
                e.preventDefault();
                e.stopPropagation();
                var $opt = $(this);
                var $switcher = $opt.closest('.header-sort-switcher');
                var colIdx = parseInt($switcher.attr('data-col'));
                if ($opt.hasClass('active')) {{
                    sortByColumn(colIdx);
                    return;
                }}
                $switcher.find('.sort-option').removeClass('active');
                $opt.addClass('active');
                var subKey = $opt.attr('data-subkey');
                api.rows().every(function() {{
                    var cellNode = api.cell(this.index(), colIdx).node();
                    var $cell = $(cellNode);
                    var raw = $cell.attr('data-' + subKey);
                    var val = subKey === 'name' ? (raw || '') : (parseFloat(raw) || 0);
                    $cell.attr('data-order', val);
                }});
                api.rows().invalidate('dom');
                var order = api.order();
                var currentIdx = order && order.length ? order[0][0] : -1;
                var currentDir = order && order.length ? order[0][1] : 'desc';
                if (currentIdx === colIdx) {{
                    api.order([colIdx, currentDir]).draw();
                }} else {{
                    api.order([colIdx, 'desc']).draw();
                }}
            }});
            $wrapper.on('click', '.dataTables_scrollHead th', function(e) {{
                var colIdx = $(this).index();
                e.preventDefault();
                e.stopImmediatePropagation();
                sortByColumn(colIdx);
            }});
            $sortStrip.on('click', '.sort-strip-seg', function(e) {{
                e.preventDefault();
                e.stopPropagation();
                sortByColumn(Number($(this).data('col')));
            }});
            rebuildSortStrip();
            refreshActiveSortColumn();
            updateSearchNav();
            api.on('order.dt draw.dt column-sizing.dt', function() {{
                rebuildSortStrip();
                refreshActiveSortColumn();
                updateSearchNav();
            }});
            function loadFullModList($details) {{
                var $full = $details.find('.mod-full-list');
                if (!$full.length || $full.attr('data-loaded') === '1') return;
                var mid = $details.closest('tr').attr('data-mid') || '';
                var groups = (window.modDetailData && window.modDetailData[mid]) || [];
                if (!groups.length) return;
                // 用完整分组卡片替换初始的轻量预览：打开前不创建大量 DOM，打开后外观与旧版一致。
                $details.find('.mod-details-body > .mod-category-section, .mod-details-body > .tag-empty').remove();
                var html = '';
                groups.forEach(function(group) {{
                    var name = group.n || '未分类';
                    var head = group.u ? '<a class="mod-category-link" href="' + escHtml(group.u, true) + '" target="_blank">' + escHtml(name, true) + '</a>' : '<span>' + escHtml(name, true) + '</span>';
                    html += '<section class="mod-category-section" data-mod-cat-key="' + escHtml(group.k || '', true) + '"><div class="mod-category-head">' + head + '<span>' + (group.m || []).length + '</span></div><div class="mod-grid">';
                    (group.m || []).forEach(function(mod) {{
                        var modName = mod[0] || '';
                        if (!modName) return;
                        var version = mod[1] || '';
                        var url = mod[2] || '#';
                        var title = mod[3] || modName;
                        var hint = title + (version ? ' · 版本: ' + version : '') + ' · 分类: ' + name;
                        html += '<span class="tag-mod" role="button" tabindex="0" title="' + escHtml(hint, true) + '" data-mod="' + escHtml(modName, true) + '" data-mod-cat="' + escHtml(name, true) + '" data-mod-url="' + escHtml(url, true) + '"><span class="tag-mod-name">' + escHtml(modName, true) + '</span>' + (version ? '<span class="tag-mod-version">' + escHtml(version, true) + '</span>' : '') + '<a class="tag-mod-open" href="' + escHtml(url, true) + '" target="_blank" title="打开 MC百科模组页">↗</a></span>';
                    }});
                    html += '</div></section>';
                }});
                $full.attr('data-loaded', '1').html(html);
            }}
            $wrapper.on('click', '.mod-summary-chip', function(e) {{
                e.preventDefault();
                e.stopPropagation();
                var $chip = $(this);
            var key = $chip.data('mod-cat-key');
            var $details = $chip.closest('.mod-details');
            if (!$details.prop('open')) {{
                $details.prop('open', true);
            }}
            loadFullModList($details);
            setTimeout(function() {{
                var $target = $details.find('.mod-category-section[data-mod-cat-key="' + key + '"]');
                if (!$target.length) return;
                var $scrollBox = $details.find('.mod-details-body');
                var currentTop = $scrollBox.scrollTop();
                var targetTop = $target.position().top + currentTop - 6;
                $scrollBox.stop(true).animate({{ scrollTop: Math.max(0, targetTop) }}, 220);
                    $target.removeClass('jump-focus');
                    void $target[0].offsetWidth;
                    $target.addClass('jump-focus');
                    api.columns.adjust();
                    rebuildSortStrip();
                    refreshActiveSortColumn();
                }}, 40);
            }});
            $wrapper.on('click', '.mod-details-body, .mod-category-section, .mod-grid', function(e) {{
                if ($(e.target).closest('.tag-mod, .tag-mod-open, .mod-category-head, .mod-category-link, a, button').length) return;
                var $details = $(this).closest('.mod-details');
                if ($details.length && $details.prop('open')) {{
                    $details.prop('open', false);
                    api.columns.adjust();
                    rebuildSortStrip();
                    refreshActiveSortColumn();
                }}
            }});
            $wrapper.on('click', '.mod-details > summary', function() {{
                var current = $(this).closest('.mod-details')[0];
                setTimeout(function() {{
                    if (current && current.open) {{
                        $wrapper.find('.mod-details[open]').each(function() {{
                            if (this !== current) this.open = false;
                        }});
                        // 某些浏览器不让 <details> 的 toggle 事件冒泡；这里直接补载完整名单。
                        loadFullModList($(current));
                        api.columns.adjust();
                        rebuildSortStrip();
                        refreshActiveSortColumn();
                    }}
                }}, 0);
            }});
            $wrapper.on('toggle', '.mod-details', function() {{
                if (this.open) {{
                    var current = this;
                    $wrapper.find('.mod-details[open]').each(function() {{
                        if (this !== current) this.open = false;
                    }});
                    loadFullModList($(this));
                }}
                setTimeout(function() {{
                    api.columns.adjust();
                    rebuildSortStrip();
                    refreshActiveSortColumn();
                }}, 30);
            }});
            $wrapper.on('wheel', '.mod-container, .mod-details-body', function(e) {{
                var el = this;
                if (!el || el.scrollHeight <= el.clientHeight) return;
                var oe = e.originalEvent;
                var delta = oe.deltaY || 0;
                var atTop = el.scrollTop <= 0;
                var atBottom = Math.ceil(el.scrollTop + el.clientHeight) >= el.scrollHeight;
                if ((delta < 0 && atTop) || (delta > 0 && atBottom)) return;
                e.stopPropagation();
            }});
            function toggleMultiSelect(selector, val) {{
                var $sel = $(selector);
                var current = $sel.val() || [];
                if (!Array.isArray(current)) current = current ? [current] : [];
                var idx = current.indexOf(val);
                if (idx >= 0) {{
                    current.splice(idx, 1);
                }} else {{
                    if ($sel.find('option').filter(function() {{ return $(this).val() === val; }}).length === 0) {{
                        $sel.append($('<option>', {{ value: val, text: val }}));
                    }}
                    current.push(val);
                }}
                $sel.val(current).trigger('change');
            }}
            /* ★ [v10.0] 点击单元格内标签筛选/取消 */
            $wrapper.on('click', '.tag-cat', function(e) {{
                if ($(e.target).closest('.tag-filter-open').length) return;
                e.preventDefault();
                e.stopPropagation();
                var val = ($(this).attr('data-tag') || $(this).find('.tag-filter-name').text() || $(this).text()).trim();
                toggleMultiSelect('#categoryFilter', val);
            }});
            $wrapper.on('click', '.tag-pack', function(e) {{
                if ($(e.target).closest('.tag-filter-open').length) return;
                e.preventDefault();
                e.stopPropagation();
                var val = ($(this).attr('data-tag') || $(this).find('.tag-filter-name').text() || $(this).text()).trim();
                toggleMultiSelect('#packTagFilter', val);
            }});
            $wrapper.on('click', '.tag-filter-open', function(e) {{
                e.stopPropagation();
            }});
            $wrapper.on('click keydown', '.tag-mod', function(e) {{
                if (e.type === 'keydown' && e.key !== 'Enter' && e.key !== ' ') return;
                if ($(e.target).closest('.tag-mod-open').length) return;
                e.preventDefault();
                e.stopPropagation();
                var val = ($(this).attr('data-mod') || $(this).find('.tag-mod-name').text() || $(this).text()).trim();
                if (val) toggleMultiSelect('#modFilter', val);
            }});
            $wrapper.on('click', '.tag-mod-open', function(e) {{
                e.stopPropagation();
            }});
            // 初始化完成后，延迟微调一下列宽，保证表头对齐
            setTimeout(function() {{
                api.columns.adjust();
                rebuildSortStrip();
                refreshActiveSortColumn();
            }}, 100);
        }}
    }});
/* ══════════════ 1. DataTables 自定义多条件过滤器 ══════════════ */
    $.fn.dataTable.ext.search.push(
        function(settings, data, dataIndex) {{
            var selectedCat   = $('#categoryFilter').val();
            var selectedPack  = $('#packTagFilter').val();
            var selectedModCat = $('#modCategoryFilter').val();
            var selectedMod = $('#modFilter').val();
            var selectedTrend = $('#trendFilter').val();
            var selectedType = $('#typeFilter').val();
            var excludeCat = $('#categoryExclude').is(':checked');
            var excludePack = $('#packTagExclude').is(':checked');
            var excludeModCat = $('#modCategoryExclude').is(':checked');
            var excludeMod = $('#modExclude').is(':checked');
            function asArray(v) {{
                if (!v) return [];
                return Array.isArray(v) ? v : [v];
            }}
            function hasAll(rowText, selected) {{
                selected = asArray(selected);
                if (!selected.length) return true;
                rowText = String(rowText || '').toLowerCase();
                for (var i = 0; i < selected.length; i++) {{
                    if (rowText.indexOf(String(selected[i]).toLowerCase()) === -1) return false;
                }}
                return true;
            }}
            function passFilter(rowText, selected, exclude) {{
                selected = asArray(selected);
                if (!selected.length) return true;
                var matched = hasAll(rowText, selected);
                return exclude ? !matched : matched;
            }}
            // 分类和标签筛选
            var tagCell = $(table.cell(dataIndex, 5).node());
            var titleCell = $(table.cell(dataIndex, 0).node());
            var rowType = titleCell.attr('data-type-search') || '';
            var rowCat  = tagCell.attr('data-cat-search') || '';
            var rowPack = tagCell.attr('data-pack-search') || '';
            var rowMid = titleCell.closest('tr').attr('data-mid') || '';
            var rowModData = (window.compareData && window.compareData[rowMid]) || {{}};
            var rowModCategories = (rowModData.mod_categories || []).join(' ');
            var rowModNames = (rowModData.mods || []).map(function(m) {{ return typeof m === 'string' ? m : (m.name || ''); }}).join(' ');
            if (selectedType && rowType !== selectedType) return false;
            if (!passFilter(rowCat, selectedCat, excludeCat)) return false;
            if (!passFilter(rowPack, selectedPack, excludePack)) return false;
            if (!passFilter(rowModCategories, selectedModCat, excludeModCat)) return false;
            if (!passFilter(rowModNames, selectedMod, excludeMod)) return false;
            // 💡 升级：直接从单元格的 data-days 属性中抓取纯数字，避开文本干扰
            var cellNode = table.cell(dataIndex, 1).node();
            var trendDays = cellNode ? parseInt($(cellNode).attr('data-days')) : 0;
            if (isNaN(trendDays)) trendDays = 0; // 安全防御
            if (selectedTrend) {{
                if (selectedTrend === "7_in") {{
                    if (trendDays > 7) return false;      // 7天内：0~7天显示，大于7的隐藏
                }} else if (selectedTrend === "7-14") {{
                    if (trendDays < 8 || trendDays > 14) return false;  // 7-14天：实际抓取 8~14天
                }} else if (selectedTrend === "14-30") {{
                    if (trendDays < 15 || trendDays > 30) return false; // 14-30天：实际抓取 15~30天
                }} else if (selectedTrend === "30_in") {{
                    if (trendDays > 30) return false;     // 30天内：大集合！0~30天都显示，大于30的隐藏
                }} else if (selectedTrend === "30-59") {{
                    if (trendDays < 31 || trendDays > 59) return false; // 30-59天：实际抓取 31~59天
                }} else if (selectedTrend === "60") {{
                    if (trendDays < 60) return false;   // 至少60天：本地长期历史超过60天也保留
                }}
            }}
            return true;
        }}
    );
    $('#typeFilter, #categoryFilter, #packTagFilter, #modCategoryFilter, #modFilter, #trendFilter, #categoryExclude, #packTagExclude, #modCategoryExclude, #modExclude').on('change', function() {{
        table.draw();
    }});
    // 表格重绘时，同步更新顶部的总条数统计
    table.on('draw', function() {{
        var info = table.page.info();
        $('#statTotal').text(info.recordsDisplay);
        /* ★ [v10.0] 高亮当前被激活筛选的标签 */
        var $wrap = $('#modpackTable_wrapper');
        $wrap.find('.tag-cat, .tag-pack, .tag-mod').removeClass('active-tag exclude-active-tag');
        var activeCat = $('#categoryFilter').val() || [];
        if (!Array.isArray(activeCat)) activeCat = activeCat ? [activeCat] : [];
        if (activeCat.length) {{
            $wrap.find('.tag-cat').filter(function() {{ return activeCat.indexOf(($(this).attr('data-tag') || '').trim()) >= 0; }}).addClass($('#categoryExclude').is(':checked') ? 'exclude-active-tag' : 'active-tag');
        }}
        var activePack = $('#packTagFilter').val() || [];
        if (!Array.isArray(activePack)) activePack = activePack ? [activePack] : [];
        if (activePack.length) {{
            $wrap.find('.tag-pack').filter(function() {{ return activePack.indexOf(($(this).attr('data-tag') || '').trim()) >= 0; }}).addClass($('#packTagExclude').is(':checked') ? 'exclude-active-tag' : 'active-tag');
        }}
        var activeMod = $('#modFilter').val() || [];
        if (!Array.isArray(activeMod)) activeMod = activeMod ? [activeMod] : [];
        if (activeMod.length) {{
            $wrap.find('.tag-mod').filter(function() {{ return activeMod.indexOf(($(this).attr('data-mod') || '').trim()) >= 0; }}).addClass($('#modExclude').is(':checked') ? 'exclude-active-tag' : 'active-tag');
        }}
    }});
    // 一键重置所有筛选条件
    $('#resetFilters').on('click', function() {{
        $('#categoryFilter').val(null).trigger('change');
        $('#typeFilter').val('').trigger('change');
        $('#packTagFilter').val(null).trigger('change');
        $('#modCategoryFilter').val(null).trigger('change');
        $('#modFilter').val(null).trigger('change');
        $('#categoryExclude, #packTagExclude, #modCategoryExclude, #modExclude').prop('checked', false);
        $('#trendFilter').val('').trigger('change'); // 加上走势的重置
        table.search('').draw();
    }});
    /* ═══════ 整合包介绍预览 ═══════ */
    var descData = {desc_json};
    // 评论数据不再内嵌进 HTML：按整合包 ID 在首次打开评论时再从本地 API 读取。
    var commentData = {{}};
    var commentLoadJobs = {{}};
    var commentApiBase = {comment_api_base_json};
    var compareData = {compare_json};
    var modDetailData = {mod_detail_json};
    window.compareData = compareData;
    window.modDetailData = modDetailData;
    var $popup = $('#pvPopup');
    var $pvTitle = $('#pvTitle');
    var $pvBody = $('#pvBody');
    var $pvOpen = $('#pvOpen');
    var $cpopup = $('#commentPopup');
    var $cBody = $('#commentBody');
    var $cCount = $('#commentCount');
    var $commentOpen = $('#commentOpen');
    var hoverTimer = null;
    var commentHoverTimer = null;
    var HOVER_DELAY = 600;
    var HOVER_COOLDOWN_MS = 5000;
    var hoverCooldowns = {{}};
    var descHoverPopupEnabled = localStorage.getItem('desc-hover-popup-enabled') !== '0';
    var commentHoverPopupEnabled = localStorage.getItem('comment-hover-popup-enabled') === '1';
    var activeDescKey = '';
    var activeCommentKey = '';
    var activeTrendKey = '';
    $('#compareTray, #compareOverlay').appendTo(document.body);
    var favoriteKey = 'mcmod-compare-favorites-v1';
    var favoriteIds = [];
    try {{
        favoriteIds = JSON.parse(localStorage.getItem(favoriteKey) || '[]').filter(function(mid) {{ return compareData[mid]; }});
    }} catch(e) {{
        favoriteIds = [];
    }}
    function saveFavorites() {{
        favoriteIds = favoriteIds.filter(function(mid, idx, arr) {{ return compareData[mid] && arr.indexOf(mid) === idx; }});
        localStorage.setItem(favoriteKey, JSON.stringify(favoriteIds));
    }}
    function compactTitle(item) {{
        return (item && (item.title_cn || item.title || item.mid)) || '';
    }}
    function updateFavoriteStars() {{
        $('.fav-star').each(function() {{
            var mid = String($(this).data('mid') || '');
            $(this).toggleClass('active', favoriteIds.indexOf(mid) >= 0)
                   .attr('title', favoriteIds.indexOf(mid) >= 0 ? '已收藏，点击取消' : '收藏用于对比');
        }});
    }}
    function updateCompareTray() {{
        saveFavorites();
        updateFavoriteStars();
        var selected = favoriteIds.map(function(mid) {{ return compareData[mid]; }}).filter(Boolean);
        $('#compareTrayCount').text(selected.length + ' 个整合包');
        $('#compareTrayNames').html(selected.slice(0, 8).map(function(item) {{
            return '<span class="compare-mini-chip">' + escHtml(compactTitle(item), true) + '</span>';
        }}).join('') + (selected.length > 8 ? '<span class="compare-mini-chip">+' + (selected.length - 8) + '</span>' : ''));
        $('#compareTray').toggleClass('show', selected.length > 0);
        $('#compareOpen').prop('disabled', selected.length < 2).attr('title', selected.length < 2 ? '至少收藏 2 个整合包才能对比' : '打开全面对比');
    }}
    function numFmt(n) {{
        n = Number(n || 0);
  if (n >= 100000000) return (n / 100000000).toFixed(1).replace(/\\.0$/, '') + '亿';
        if (n >= 10000) return (n / 10000).toFixed(1).replace(/\\.0$/, '') + '万';
        return String(n);
    }}
    function listNames(arr, limit) {{
        arr = arr || [];
        if (!arr.length) return '<span class="compare-chip">无</span>';
        return arr.slice(0, limit || 80).map(function(x) {{
            var name = typeof x === 'string' ? x : x.name;
            return '<span class="compare-chip">' + escHtml(name || '', true) + '</span>';
        }}).join('') + (arr.length > (limit || 80) ? '<span class="compare-chip">+' + (arr.length - (limit || 80)) + '</span>' : '');
    }}
    function setIntersection(listOfSets) {{
        if (!listOfSets.length) return [];
        var base = Array.from(listOfSets[0]);
        return base.filter(function(x) {{ return listOfSets.every(function(s) {{ return s.has(x); }}); }}).sort();
    }}
    function setUnion(listOfSets) {{
        var out = new Set();
        listOfSets.forEach(function(s) {{ s.forEach(function(x) {{ out.add(x); }}); }});
        return Array.from(out).sort();
    }}
    function renderCompare() {{
        var selected = favoriteIds.map(function(mid) {{ return compareData[mid]; }}).filter(Boolean);
        if (selected.length < 2) return;
        var modSets = selected.map(function(item) {{ return new Set((item.mods || []).map(function(m) {{ return (typeof m === 'string' ? m : (m.name || '')).toLowerCase(); }})); }});
        var modNameMap = {{}};
        selected.forEach(function(item) {{
            (item.mods || []).forEach(function(m) {{ var name = typeof m === 'string' ? m : (m.name || ''); modNameMap[name.toLowerCase()] = name; }});
        }});
        var commonMods = setIntersection(modSets).map(function(k) {{ return modNameMap[k] || k; }});
        var allMods = setUnion(modSets);
        var tagSets = selected.map(function(item) {{ return new Set([].concat(item.categories || [], item.tags || [])); }});
        var commonTags = setIntersection(tagSets);
        var typeLine = selected.map(function(item) {{ return item.type || '未标明'; }});
        var html = '';
        html += '<div class="compare-grid">';
        selected.forEach(function(item) {{
            html += '<div class="compare-card">';
            html += '<h3>' + escHtml(compactTitle(item), true) + '</h3>';
            html += '<div class="compare-metric"><span>类型</span><b>' + escHtml(item.type || '未标明', true) + '</b></div>';
            html += '<div class="compare-metric"><span>官方流行</span><b>' + numFmt(item.score) + '</b></div>';
            html += '<div class="compare-metric"><span>浏览</span><b>' + numFmt(item.views) + '</b></div>';
            html += '<div class="compare-metric"><span>模组</span><b>' + numFmt((item.mods || []).length) + '</b></div>';
            html += '<div class="compare-metric"><span>评论</span><b>' + numFmt(item.comments) + '</b></div>';
            html += '<div class="compare-metric"><span>推荐/收藏</span><b>' + numFmt(item.recommend) + ' / ' + numFmt(item.favorite) + '</b></div>';
            html += '<div class="compare-metric"><span>7/30/60日</span><b>' + escHtml([item.growth7, item.growth30, item.growth60].join(' / '), true) + '</b></div>';
            html += '</div>';
        }});
        html += '</div>';
        html += '<div class="compare-section"><h3>共有模组 · ' + commonMods.length + '</h3><div class="compare-chip-cloud">' + listNames(commonMods, 120) + '</div></div>';
        html += '<div class="compare-section"><h3>共有分类/标签 · ' + commonTags.length + '</h3><div class="compare-chip-cloud">' + listNames(commonTags, 120) + '</div></div>';
        html += '<div class="compare-section"><h3>各包独有模组</h3><div class="compare-columns">';
        selected.forEach(function(item, idx) {{
            var unique = (item.mods || []).filter(function(m) {{
                var key = (typeof m === 'string' ? m : (m.name || '')).toLowerCase();
                return modSets.filter(function(s) {{ return s.has(key); }}).length === 1;
            }}).map(function(m) {{ return typeof m === 'string' ? m : m.name; }});
            html += '<div class="compare-card"><h3>' + escHtml(compactTitle(item), true) + ' · ' + unique.length + '</h3><div class="compare-chip-cloud">' + listNames(unique, 120) + '</div></div>';
        }});
        html += '</div></div>';
        html += '<div class="compare-section"><h3>模组差异矩阵 · ' + allMods.length + '</h3><div class="compare-table-wrap"><table class="compare-table"><thead><tr><th>模组</th>';
        selected.forEach(function(item) {{ html += '<th>' + escHtml(compactTitle(item), true) + '</th>'; }});
        html += '</tr></thead><tbody>';
        allMods.forEach(function(key) {{
            html += '<tr><td>' + escHtml(modNameMap[key] || key, true) + '</td>';
            modSets.forEach(function(s) {{ html += s.has(key) ? '<td class="compare-hit">有</td>' : '<td class="compare-miss">无</td>'; }});
            html += '</tr>';
        }});
        html += '</tbody></table></div></div>';
        html += '<div class="compare-section"><h3>分类/标签差异矩阵</h3><div class="compare-table-wrap"><table class="compare-table"><thead><tr><th>分类/标签</th>';
        selected.forEach(function(item) {{ html += '<th>' + escHtml(compactTitle(item), true) + '</th>'; }});
        html += '</tr></thead><tbody>';
        setUnion(tagSets).forEach(function(tag) {{
            html += '<tr><td>' + escHtml(tag, true) + '</td>';
            tagSets.forEach(function(s) {{ html += s.has(tag) ? '<td class="compare-hit">有</td>' : '<td class="compare-miss">无</td>'; }});
            html += '</tr>';
        }});
        html += '</tbody></table></div></div>';
        $('#compareBody').html(html);
        $('#compareOverlay').addClass('show').attr('aria-hidden', 'false');
    }}
    $(document).off('click.compareFav').on('click.compareFav', '.fav-star', function(e) {{
        e.preventDefault();
        e.stopPropagation();
        var mid = String($(this).data('mid') || '');
        if (!compareData[mid]) return;
        var idx = favoriteIds.indexOf(mid);
        if (idx >= 0) favoriteIds.splice(idx, 1);
        else favoriteIds.push(mid);
        updateCompareTray();
    }});
    table.on('draw', updateFavoriteStars);
    $('#compareClear').on('click', function() {{ favoriteIds = []; updateCompareTray(); }});
    $('#compareOpen').on('click', renderCompare);
    $('#compareClose, #compareOverlay').on('click', function(e) {{
        if (e.target === this) $('#compareOverlay').removeClass('show').attr('aria-hidden', 'true');
    }});
    $('#compareCopy').on('click', function() {{
        var selected = favoriteIds.map(function(mid) {{ return compareData[mid]; }}).filter(Boolean);
        var text = selected.map(function(item) {{
            return compactTitle(item) + ' | 模组 ' + (item.mods || []).length + ' | 流行 ' + item.score + ' | 浏览 ' + item.views;
        }}).join('\\n');
        if (navigator.clipboard) navigator.clipboard.writeText(text);
    }});
    updateCompareTray();
    function isHoverCooling(key) {{
        return key && hoverCooldowns[key] && hoverCooldowns[key] > Date.now();
    }}
    function setHoverCooldown(key) {{
        if (key) hoverCooldowns[key] = Date.now() + HOVER_COOLDOWN_MS;
    }}
    function getCommentUrl(url) {{
        var clean = (url || 'https://www.mcmod.cn/').split('#')[0];
        return clean;
    }}
    function escAttrJs(str) {{
        return escHtml(str || '', true).replace(/<br>/g, '&#10;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }}
    function getSingleCommentUrl(c) {{
        if (c && (c.comment_url || c.url || c.href || c.link)) {{
            return c.comment_url || c.url || c.href || c.link;
        }}
        return '';
    }}
    function commentOriginMeta(c, localIndex) {{
        return '';
    }}
    function getDescText(desc) {{
        if (!desc) return '';
        if (typeof desc === 'string') return desc;
        return desc.text || '';
    }}
    function getDescImages(desc) {{
        if (!desc || typeof desc === 'string') return [];
        return Array.isArray(desc.images) ? desc.images : [];
    }}
    function normalizeImageUrlJs(url) {{
        if (!url) return '';
        try {{ return new URL(url, window.location.href).href; }} catch(e) {{
            if (String(url).indexOf('//') === 0) return 'https:' + url;
            return String(url);
        }}
    }}
    function isAvatarImage(img) {{
        if (img && String(img.kind || '').toLowerCase() === 'avatar') return true;
        var raw = (typeof img === 'string') ? img : (img.url || img.src || '');
        var url = normalizeImageUrlJs(raw).toLowerCase();
        return url.indexOf('/user/avatar/') >= 0 || url.indexOf('/identicons/') >= 0 || url.indexOf('@60x60') >= 0;
    }}
    function isEmotionImage(img) {{
        if (img && String(img.kind || '').toLowerCase() === 'emotion') return true;
        var raw = (typeof img === 'string') ? img : (img.url || img.src || '');
        var url = normalizeImageUrlJs(raw).toLowerCase();
        return url.indexOf('/emotion/images/') >= 0 || url.indexOf('/dialogs/emotion/') >= 0;
    }}
    function filterGalleryImages(images) {{
        if (!Array.isArray(images)) return [];
        return images.filter(function(img) {{ return !isAvatarImage(img) && !isEmotionImage(img); }});
    }}
    function filterEmotionImages(images) {{
        if (!Array.isArray(images)) return [];
        return images.filter(function(img) {{ return isEmotionImage(img); }});
    }}
    function renderInlineEmotions(images) {{
        var emos = filterEmotionImages(images);
        if (!emos.length) return '';
        var html = '<span class="inline-emotions">';
        emos.forEach(function(img, idx) {{
            var raw = (typeof img === 'string') ? img : (img.url || img.src || '');
            var url = normalizeImageUrlJs(raw);
            if (!url) return;
            html += '<img class="inline-emotion" src="' + escAttrJs(url) + '" alt="表情" loading="lazy">';
        }});
        html += '</span>';
        return html;
    }}
    function renderImageGallery(images, extraClass) {{
        images = filterGalleryImages(images);
        if (!Array.isArray(images) || !images.length) return '';
        var html = '<div class="image-gallery ' + (extraClass || '') + '">';
        images.forEach(function(img, idx) {{
            var raw = (typeof img === 'string') ? img : (img.url || img.src || '');
            var url = normalizeImageUrlJs(raw);
            if (!url || /loading|loadfail/i.test(url)) return;
            var alt = (typeof img === 'string') ? '' : (img.alt || img.title || '');
            var caption = alt || ('图片 ' + (idx + 1));
            html += '<a class="image-thumb" href="' + escAttrJs(url) + '" target="_blank" rel="noreferrer" title="' + escAttrJs(caption) + '">';
            html += '<img src="' + escAttrJs(url) + '" alt="' + escAttrJs(caption) + '" loading="lazy">';
            html += '<span class="image-caption">' + escHtml(caption, true) + '</span></a>';
        }});
        html += '</div>';
        return html;
    }}
    function splitIntroImages(images) {{
        var cover = [];
        var rest = [];
        (images || []).forEach(function(img) {{
            var source = (img && img.source ? String(img.source).toLowerCase() : '');
            if (source === 'cover') cover.push(img);
            else rest.push(img);
        }});
        return {{ cover: cover, rest: rest }};
    }}
    function sectionKeyFromText(text) {{
        var s = String(text || '').replace(/\\s+/g, '');
        if (!s) return '';
        if (s.indexOf('任务截图') >= 0 || s.indexOf('游戏截图') >= 0 || s.indexOf('截图') >= 0 || s.indexOf('图片') >= 0) return 'screenshots';
        if (s.indexOf('使用') >= 0) return 'usage';
        if (s.indexOf('介绍') >= 0 || s.indexOf('简介') >= 0) return 'intro';
        return '';
    }}
    function imageSectionKey(img) {{
        var s = ((img && (img.section || img.heading || img.alt || img.title)) || '').replace(/\\s+/g, '');
        return sectionKeyFromText(s);
    }}
    function renderDescHtml(desc, images, keyword) {{
        var splitImages = splitIntroImages(images || []);
        var textHtml = '';
        if (desc) {{
            if (keyword && desc.toLowerCase().indexOf(keyword.toLowerCase()) !== -1) {{
                textHtml = '<div class="pv-para">' + highlightText(desc, keyword) + '</div>';
            }} else {{
                textHtml = escHtml(desc);
            }}
        }}
        var coverHtml = splitImages.cover.length ? '<div class="pv-cover-wrap">' + renderImageGallery(splitImages.cover, 'pv-cover-gallery') + '</div>' : '';
        var rest = splitImages.rest;
        if (!rest.length) return coverHtml + textHtml;

        var used = new Set();
        var $box = $('<div>' + textHtml + '</div>');
        $box.children().each(function() {{
            var key = sectionKeyFromText($(this).text());
            if (!key) return;
            var group = rest.filter(function(img, idx) {{
                return !used.has(idx) && (imageSectionKey(img) === key || (!imageSectionKey(img) && key === 'screenshots'));
            }});
            if (group.length) {{
                group.forEach(function(img) {{ used.add(rest.indexOf(img)); }});
                $(this).after(renderImageGallery(group, 'pv-image-gallery section-bound'));
            }}
        }});
        var leftovers = rest.filter(function(img, idx) {{ return !used.has(idx); }});
        return coverHtml + $box.html() + renderImageGallery(leftovers, 'pv-image-gallery');
    }}
    $(document).on('click', '.mcmod-consent-ok', function(e) {{
        e.preventDefault();
        e.stopPropagation();
        $(this).closest('.pv-popup, .comment-popup').removeClass('needs-consent');
    }});
    function openImageLightbox(url, title) {{
        url = normalizeImageUrlJs(url);
        if (!url) return;
        $('#imageLightboxImg').attr('src', url).attr('alt', title || '');
        $('#imageLightboxTitle').text(title || '图片预览');
        $('#imageLightboxOpen').attr('href', url);
        $('#imageLightbox').addClass('show').attr('aria-hidden', 'false');
    }}
    function closeImageLightbox() {{
        $('#imageLightbox').removeClass('show').attr('aria-hidden', 'true');
        $('#imageLightboxImg').attr('src', '');
    }}
    var coverHoverPreviewTimer = null;
    $(document).on('mouseenter', '.modpack-cover-thumb', function() {{
        var $thumb = $(this);
        clearTimeout(coverHoverPreviewTimer);
        coverHoverPreviewTimer = setTimeout(function() {{
            openImageLightbox($thumb.data('image-url') || $thumb.attr('href'), $thumb.attr('title') || '封面预览');
        }}, 1000);
    }});
    $(document).on('mouseleave', '.modpack-cover-thumb', function() {{
        clearTimeout(coverHoverPreviewTimer);
        coverHoverPreviewTimer = null;
    }});
    $(document).on('click', '.image-thumb', function(e) {{
        e.preventDefault();
        e.stopPropagation();
        clearTimeout(coverHoverPreviewTimer);
        openImageLightbox($(this).attr('href') || $(this).data('image-url'), $(this).attr('title') || $(this).find('.image-caption').text());
    }});
    $('#imageLightboxClose, #imageLightbox').on('click', function(e) {{
        if (e.target === this) closeImageLightbox();
    }});
    function showDescPopup($link) {{
        var url = $link.attr('href') || '#';
        var title = $link.data('full-title') || $link.text();
        var mid = $link.data('mid') || '';
        activeDescKey = 'desc:' + (mid || url || title);
        if (isHoverCooling(activeDescKey)) return;
        $pvTitle.text(title);
        $pvOpen.attr('href', url);
        var descObj = descData[mid];
        var desc = getDescText(descObj);
        var descImages = getDescImages(descObj);
        if (desc || descImages.length) {{
            var $filterInput = $('#modpackTable_filter input');
            var keyword = $filterInput.length > 0 ? $filterInput.val().trim() : '';
            $pvBody.html(renderDescHtml(desc, descImages, keyword));
        }} else {{
            $pvBody.html('<div class="pv-body-empty">暂无介绍数据<div><a href="' + url + '" target="_blank">点击打开 mcmod.cn 原页面 →</a></div></div>');
        }}
        $popup.addClass('show needs-consent').attr('aria-hidden', 'false');
        var rect = $link[0].getBoundingClientRect();
        var linkH = $link.outerHeight();
        var pw = $popup.outerWidth();
        var ph = $popup.outerHeight();
        var vw = window.innerWidth;
        var vh = window.innerHeight;
        // 默认显示在链接上方
        var top = rect.top - ph - 14;
        var left = rect.left;
        // 上方空间不够 → 显示在下方
        if (top < 12) top = rect.bottom + 14;
        // 如果下方也不够，则从顶部开始
        if (top + ph > vh - 12) top = Math.max(12, Math.min(vh - ph - 12, 12));
        // 水平方向 clamp
        if (left + pw > vw - 12) left = vw - pw - 12;
        if (left < 12) left = 12;
        $popup.css({{ top: top, left: left }});
    }}
    function hideDescPopup() {{
        $popup.removeClass('show needs-consent').attr('aria-hidden', 'true');
    }}
    function escapeRegExp(str) {{
        if (!str) return "";
        // 1. 先把反斜杠转义（必须最先执行）
        str = str.split('\\\\').join('\\\\\\\\');
        // 2. 逐个将其他正则敏感元字符转义
        var specials = ['/', '^', '$', '*', '+', '?', '.', '(', ')', '|', '[', ']', '{{', '}}', '-'];
        for (var i = 0; i < specials.length; i++) {{
            var c = specials[i];
            str = str.split(c).join('\\\\' + c);
        }}
        return str;
    }}
    function highlightText(str, keyword) {{
        var escaped = escHtml(str, true);
        if (!keyword) return escaped;
        var cleanKeyword = keyword.trim();
        if (!cleanKeyword) return escaped;
        var escapedKeyword = escHtml(cleanKeyword, true);
        if (!escapedKeyword) return escaped;
        try {{
            var regex = new RegExp('(' + escapeRegExp(escapedKeyword) + ')', 'gi');
            return escaped.replace(regex, '<mark class="comment-highlight">$1</mark>');
        }} catch(e) {{
            return escaped;
        }}
    }}
    function escHtml(str, noFormat) {{
    if (str === null || str === undefined) return "";
    var d = document.createElement('div');
        d.textContent = str;
        var raw = d.innerHTML;
        var LF = String.fromCharCode(10);
        var CR = String.fromCharCode(13);
        var text = raw.split(CR + LF).join(LF).split(CR).join(LF);
        if (noFormat) {{
            return text.split(LF).join('<br>');
        }}
        var lines = text.split(LF);
        var html = '';
        var currentPara = [];
        var currentQuote = [];
        function flushPara() {{
            if (currentPara.length > 0) {{
                html += '<div class="pv-para">' + currentPara.join('<br>') + '</div>';
                currentPara = [];
            }}
        }}
        function flushQuote() {{
            if (currentQuote.length > 0) {{
                html += '<blockquote class="intro-blockquote">' + currentQuote.join('<br>') + '</blockquote>';
                currentQuote = [];
            }}
        }}
        for (var i = 0; i < lines.length; i++) {{
            var line = lines[i].trim();
            if (!line) {{
                flushPara();
                flushQuote();
                continue;
            }}
            var firstChar = line.charAt(0);
            var isQuote = firstChar === '|' || firstChar === '>';
            if (isQuote) {{
                flushPara();
                var quoteContent = line.substring(1).trim();
                currentQuote.push(quoteContent);
                continue;
            }} else {{
                flushQuote();
            }}
            var isList = false;
            var listContent = line;
            if (firstChar === '-' || firstChar === '*' || firstChar === '•' || /^\\d+\\.\\s/.test(line)) {{
                isList = true;
                listContent = line.replace(/^[-*•\\s]+|^\\d+\\.\\s+/, '');
            }} else {{
                var colonMatch = line.match(/^([^，。！、；：:]{{2,15}})[：:]/);
                if (colonMatch) {{
                    isList = true;
                    listContent = '<strong>' + colonMatch[1] + ': </strong>' + line.substring(colonMatch[0].length).trim();
                }}
            }}
            var isTitle = false;
            if (!isList) {{
                var isShort = line.length <= 25;
                var hasPunctuation = /[，。！、；]/.test(line);
                var lastChar = line.slice(-1);
                if ((isShort && !hasPunctuation && !lastChar.match(/[。！；]/)) || lastChar === ':' || lastChar === '：' || line.indexOf('——') >= 0) {{
                    isTitle = true;
                }}
            }}
            if (isList) {{
                flushPara();
                html += '<div class="pv-list-item">' + listContent + '</div>';
            }} else if (isTitle) {{
                flushPara();
                html += '<div class="pv-section-title">' + line + '</div>';
            }} else {{
                currentPara.push(line);
            }}
        }}
        flushPara();
        flushQuote();
        return html || text.split(LF).join('<br>');
    }}
    var cmtPerPage = 8;
    var cmtCurrentPage = 1;
    var cmtTotalPages = 1;
    var cmtCurrentData = null;
    var cmtTargetIndex = -1;
    var activeCommentCell = null;
    var cmtSearchMatches = [];
    var cmtSearchMatchPointer = -1;
    function renderCommentPage(page) {{
        if (!cmtCurrentData || !cmtCurrentData.comments) return;
        var comments = cmtCurrentData.comments;
        cmtTotalPages = Math.max(1, Math.ceil(comments.length / cmtPerPage));
        if (page < 1) page = 1;
        if (page > cmtTotalPages) page = cmtTotalPages;
        cmtCurrentPage = page;
        var keyword = $('#commentSearchInput').val().trim();
        var start = (page - 1) * cmtPerPage;
        var end = Math.min(start + cmtPerPage, comments.length);
        var html = '';
        for (var i = start; i < end; i++) {{
            var c = comments[i];
            var isActiveMatch = (cmtSearchMatchPointer >= 0 && i === cmtSearchMatches[cmtSearchMatchPointer]);
            html += '<div class="comment-floor' + (isActiveMatch ? ' matched-active' : '') + '" data-comment-index="' + i + '">';
            var cUrl = getSingleCommentUrl(c);
            html += '<div class="comment-floor-head">';
            html += '<div class="comment-floor-main">';
            if (c.floor) {{
                html += '<span class="floor-num">第 ' + c.floor + ' 楼</span> ';
            }}
            var originMeta = commentOriginMeta(c, i);
            html += highlightText(c.author || '', keyword) + (originMeta ? '<span class="comment-origin-meta">' + originMeta + '</span>' : '') + '</div>';
            if (cUrl) {{
                html += '<a class="comment-floor-link" href="' + escAttrJs(cUrl) + '" target="_blank" title="在 MC百科原页面定位这条评论">↗</a>';
            }}
            html += '</div>';
            html += '<div class="comment-floor-text">' + highlightText(c.text || '', keyword) + renderInlineEmotions(c.images || []) + '</div>';
            html += renderImageGallery(c.images || [], 'comment-image-gallery');
            if (c.replies && c.replies.length > 0) {{
                c.replies.forEach(function(r) {{
                    var rUrl = getSingleCommentUrl(r);
                    html += '<div class="comment-reply">';
                    html += '<div class="comment-reply-head"><span>' + highlightText(r.author || '', keyword) + '</span>';
                    if (rUrl) {{
                        html += '<a class="comment-reply-link" href="' + escAttrJs(rUrl) + '" target="_blank" title="在 MC百科原页面定位这条回复">↗</a>';
                    }}
                    html += '</div>';
                    html += '<div class="comment-reply-text">' + highlightText(r.text || '', keyword) + renderInlineEmotions(r.images || []) + '</div>';
                    html += renderImageGallery(r.images || [], 'comment-image-gallery');
                    html += '</div>';
                }});
            }}
            html += '</div>';
        }}
        $cBody.html(html);
        $cBody.scrollTop(0); // 确保翻页后滚动条滑回最上方，极大地改善了翻页可读性
        if (cmtTargetIndex >= start && cmtTargetIndex < end) {{
            setTimeout(function() {{
                var target = $cBody.find('[data-comment-index="' + cmtTargetIndex + '"]')[0];
                if (target) $cBody.scrollTop(Math.max(0, target.offsetTop - 14));
                cmtTargetIndex = -1;
            }}, 30);
        }}
        // 更新分页栏
        var $bar = $('#commentPageBar');
        var $info = $('#cmtPageInfo');
        var $first = $('#cmtFirst');
        var $prev = $('#cmtPrev');
        var $next = $('#cmtNext');
        var $last = $('#cmtLast');
        if (cmtTotalPages > 1) {{
            $bar.show();
            $info.text('第 ' + page + ' / ' + cmtTotalPages + ' 页');
            $first.removeClass('disabled').addClass(page <= 1 ? 'disabled' : '');
            $prev.removeClass('disabled').addClass(page <= 1 ? 'disabled' : '');
            $next.removeClass('disabled').addClass(page >= cmtTotalPages ? 'disabled' : '');
            $last.removeClass('disabled').addClass(page >= cmtTotalPages ? 'disabled' : '');
        }} else {{
            $bar.hide();
        }}
        repositionCommentPopup();
    }}
    /* ─── 智能高度监测系统工具方法 ─── */
    // 【1. 统一变量绑定的高度测算方法】
    function checkCommentOverflow() {{
        // 使用 setTimeout 延迟 25 毫秒，确保 DOM 节点完全重绘重排完毕，拿取绝对真实高度
        setTimeout(function() {{
            if ($cBody[0]) {{
                // 🌟 引入 8 像素溢出容差缓冲区，彻底规避小数像素四舍五入和滚动边距带来的误差
                var hasScroll = $cBody[0].scrollHeight > ($cBody.innerHeight() + 8);
                if (hasScroll) {{
                    $cpopup.addClass('has-overflow'); // 激活“滚动查看更多”胶囊
                }} else {{
                    $cpopup.removeClass('has-overflow');
                }}
            }}
        }}, 25);
    }}
    // 【2. 修正：直接绑定到局部容器，并支持滑回顶部时恢复提示】
    $('#commentBody').on('scroll', function() {{
        var scrollTop = $(this).scrollTop();
        if (scrollTop > 15) {{
            // 向下滑动超过 15px，说明用户已经发现并开始阅读，优雅隐藏提示
            $cpopup.removeClass('has-overflow');
        }} else if (scrollTop <= 5) {{
            // 如果用户又滑回了最顶部，且内容依然是超长的，把提示重新亮起来引导
            if (this.scrollHeight > $(this).innerHeight()) {{
                $cpopup.addClass('has-overflow');
            }}
        }}
    }});
    // 【3. 翻页控制】：点击各翻页按钮后安全触发重新判定
    $('#cmtFirst').on('click', function(e) {{
        e.stopPropagation();
        clearTimeout(commentHoverTimer); // ★ 防秒退保护
        if (cmtCurrentPage > 1) {{
            renderCommentPage(1);
            checkCommentOverflow();
        }}
    }});
    $('#cmtPrev').on('click', function(e) {{
        e.stopPropagation();
        clearTimeout(commentHoverTimer); // ★ 防秒退保护
        if (cmtCurrentPage > 1) {{
            renderCommentPage(cmtCurrentPage - 1);
            checkCommentOverflow();
        }}
    }});
    $('#cmtNext').on('click', function(e) {{
        e.stopPropagation();
        clearTimeout(commentHoverTimer); // ★ 防秒退保护
        if (cmtCurrentPage < cmtTotalPages) {{
            renderCommentPage(cmtCurrentPage + 1);
            checkCommentOverflow();
        }}
    }});
    $('#cmtLast').on('click', function(e) {{
        e.stopPropagation();
        clearTimeout(commentHoverTimer); // ★ 防秒退保护
        if (cmtCurrentPage < cmtTotalPages) {{
            renderCommentPage(cmtTotalPages);
            checkCommentOverflow();
        }}
    }});
    // 搜索匹配项跳转控制
    $(document).on('click', '#searchNavNext', function(e) {{
        e.stopPropagation();
        if (!cmtSearchMatches || cmtSearchMatches.length === 0) return;
        cmtSearchMatchPointer = (cmtSearchMatchPointer + 1) % cmtSearchMatches.length;
        var targetIndex = cmtSearchMatches[cmtSearchMatchPointer];
        var targetPage = Math.floor(targetIndex / cmtPerPage) + 1;
        cmtTargetIndex = targetIndex;
        $('#searchNavInfo').text('找到 ' + cmtSearchMatches.length + ' 条匹配评论 (当前第 ' + (cmtSearchMatchPointer + 1) + ' 条)');
        renderCommentPage(targetPage);
        checkCommentOverflow();
    }});
    $(document).on('click', '#searchNavPrev', function(e) {{
        e.stopPropagation();
        if (!cmtSearchMatches || cmtSearchMatches.length === 0) return;
        cmtSearchMatchPointer = (cmtSearchMatchPointer - 1 + cmtSearchMatches.length) % cmtSearchMatches.length;
        var targetIndex = cmtSearchMatches[cmtSearchMatchPointer];
        var targetPage = Math.floor(targetIndex / cmtPerPage) + 1;
        cmtTargetIndex = targetIndex;
        $('#searchNavInfo').text('找到 ' + cmtSearchMatches.length + ' 条匹配评论 (当前第 ' + (cmtSearchMatchPointer + 1) + ' 条)');
        renderCommentPage(targetPage);
        checkCommentOverflow();
    }});
    function repositionCommentPopup() {{
        if (!$cpopup.hasClass('show') || !activeCommentCell) return;
        var rect = activeCommentCell[0].getBoundingClientRect();
        var cellW = activeCommentCell.outerWidth();
        var vw = window.innerWidth;
        var vh = window.innerHeight;
        var safeTop = 24;
        var safeBottom = 24;
        var fixedHeight = Math.min(720, Math.max(420, vh - safeTop - safeBottom));
        $cpopup.css({{
            height: fixedHeight + 'px',
            'max-height': fixedHeight + 'px'
        }});
        $cBody.css('max-height', 'none');
        var ph = fixedHeight;
        var top = rect.top - ph - 10;
        // 如果上方放不下，则尝试放在下方
        if (top < safeTop) {{
            top = rect.bottom + 10;
        }}
        // 如果下方穿出了浏览器底部，则向上推起，将底部固定在 vh - safeBottom 位置，顶部向上延伸
        if (top + ph > vh - safeBottom) {{
            top = Math.max(safeTop, vh - safeBottom - ph);
        }}
        var pw = $cpopup.outerWidth();
        var left = rect.left + cellW / 2 - pw / 2;
        // 水平 clamp 锁定
        if (left + pw > vw - 12) left = vw - pw - 12;
        if (left < 12) left = 12;
        $cpopup.css({{
            top: top + 'px',
            bottom: 'auto',
            left: left
        }});
    }}
    function lockCommentPopupSize() {{
        var vh = window.innerHeight;
        var fixedHeight = Math.min(720, Math.max(420, vh - 48));
        $cpopup.css({{ height: fixedHeight + 'px', 'max-height': fixedHeight + 'px' }});
        $cBody.css('max-height', 'none');
    }}
    function isCommentHoverAlive() {{
        var overPopup = $cpopup.is(':hover');
        var overCell = activeCommentCell && activeCommentCell.length && activeCommentCell.is(':hover');
        return !!(overPopup || overCell);
    }}
    function scheduleCommentHide(delay) {{
        clearTimeout(commentHoverTimer);
        commentHoverTimer = setTimeout(function() {{
            if (isCommentHoverAlive()) return;
            hideCommentPopup();
            $('body').css({{ 'overflow': '', 'height': '' }});
        }}, delay || 120);
    }}
    // 【4. 弹窗主渲染逻辑】：渲染完数据并全部定位成功后，激活检测
    function commentSearchMatches(comments, keyword) {{
        var matches = [];
        keyword = String(keyword || '').trim().toLowerCase();
        if (!keyword || !comments) return matches;
        for (var i = 0; i < comments.length; i++) {{
            var c = comments[i] || {{}};
            var match = String(c.author || '').toLowerCase().indexOf(keyword) !== -1 ||
                        String(c.text || '').toLowerCase().indexOf(keyword) !== -1;
            (c.replies || []).forEach(function(r) {{
                if (String(r.author || '').toLowerCase().indexOf(keyword) !== -1 ||
                    String(r.text || '').toLowerCase().indexOf(keyword) !== -1) match = true;
            }});
            if (match) matches.push(i);
        }}
        return matches;
    }}
    function applyCommentSearch() {{
        if (!cmtCurrentData || !cmtCurrentData.comments) return;
        cmtSearchMatches = commentSearchMatches(cmtCurrentData.comments, $('#commentSearchInput').val());
        cmtSearchMatchPointer = cmtSearchMatches.length ? 0 : -1;
        cmtTargetIndex = cmtSearchMatches.length ? cmtSearchMatches[0] : -1;
        if (cmtSearchMatches.length) {{
            $('#searchNavInfo').text('找到 ' + cmtSearchMatches.length + ' 条匹配评论 (当前第 1 条)');
            $('#commentSearchNav').show();
            renderCommentPage(Math.floor(cmtTargetIndex / cmtPerPage) + 1);
        }} else {{
            $('#commentSearchNav').hide();
            renderCommentPage(1);
        }}
        checkCommentOverflow();
    }}
    $('#commentSearchInput').on('input', function() {{ applyCommentSearch(); }});
    function loadCommentData(mid) {{
        if (commentData[mid]) return Promise.resolve(commentData[mid]);
        if (commentLoadJobs[mid]) return commentLoadJobs[mid];
        commentLoadJobs[mid] = fetch(commentApiBase + '/comments/' + encodeURIComponent(mid), {{ cache: 'no-store' }})
            .then(function(resp) {{
                if (!resp.ok) throw new Error('HTTP ' + resp.status);
                return resp.json();
            }})
            .then(function(payload) {{
                commentData[mid] = payload || {{ comments: [] }};
                return commentData[mid];
            }})
            .catch(function(err) {{
                console.warn('评论数据加载失败:', err);
                return null;
            }})
            .finally(function() {{ delete commentLoadJobs[mid]; }});
        return commentLoadJobs[mid];
    }}
    function showCommentPopup($cell) {{
        var mid = String($cell.data('mid') || '');
        activeCommentCell = $cell;
        activeCommentKey = 'comment:' + mid;
        if (isHoverCooling(activeCommentKey)) return;
        if (commentData[mid]) {{
            renderCommentPopup($cell, commentData[mid]);
            return;
        }}
        var url = $cell.closest('tr').find('a.modpack-link').attr('href') || 'https://www.mcmod.cn/';
        var commentUrl = getCommentUrl(url);
        $('#commentModpackLink').attr('href', commentUrl);
        $commentOpen.attr('href', commentUrl);
        $('#commentSearchInput').val('').prop('disabled', true);
        $('#commentSearchNav, #commentPageBar').hide();
        $cCount.text('正在加载评论…');
        $cBody.html('<div class="comment-empty-hint">正在按需读取这一个整合包的评论…</div>');
        $cpopup.addClass('show needs-consent');
        lockCommentPopupSize();
        repositionCommentPopup();
        loadCommentData(mid).then(function(cdata) {{
            if (!activeCommentCell || !activeCommentCell.is($cell)) return;
            renderCommentPopup($cell, cdata);
        }});
    }}
    function renderCommentPopup($cell, cdata) {{
        activeCommentCell = $cell;
        var mid = $cell.data('mid') || '';
        activeCommentKey = 'comment:' + mid;
        if (isHoverCooling(activeCommentKey)) return;
        var floorCount = $cell.data('order') || 0;
        var pageCount = (cdata && cdata.page_count) ? cdata.page_count : floorCount;
        // 重置样式，以进行正确的初始测量
        $cpopup.css({{
            height: '',
            'min-height': '',
            'max-height': '',
            top: '',
            bottom: '',
            left: ''
        }});
        lockCommentPopupSize();
        if (cdata && cdata.comments && cdata.comments.length > 0) {{
            var scrapedFloors = cdata.comments.length;
            // 诱饵数据清洗与非逆向计算：直接正向统计回复数
            var scrapedReplies = 0;
            cdata.comments.forEach(function(c) {{
                if (c.replies) scrapedReplies += c.replies.length;
            }});
            pageCount = Math.max(pageCount, scrapedFloors + scrapedReplies);
            var totalLabel = '共 ' + pageCount + ' 条 · 主楼 ' + scrapedFloors + ' · 楼中楼 ' + scrapedReplies;
            $cCount.text(totalLabel);
            cmtCurrentData = cdata;
            $('#commentSearchInput').prop('disabled', false);
            /* 评论搜索只针对当前打开的评论，不再借用整合包总搜索框。 */
            var startPage = 1;
            var keyword = $('#commentSearchInput').val().trim().toLowerCase();
            var url = $cell.closest('tr').find('a.modpack-link').attr('href') || 'https://www.mcmod.cn/';
            var commentUrl = getCommentUrl(url);
            $('#commentModpackLink').attr('href', commentUrl);
            $commentOpen.attr('href', commentUrl);
            
            cmtSearchMatches = commentSearchMatches(cdata.comments, keyword);
            cmtSearchMatchPointer = -1;
            if (cmtSearchMatches.length > 0) {{
                cmtSearchMatchPointer = 0;
                var targetIndex = cmtSearchMatches[0];
                startPage = Math.floor(targetIndex / cmtPerPage) + 1;
                cmtTargetIndex = targetIndex;
            }}
            
            if (cmtSearchMatches.length > 1) {{
                $('#searchNavInfo').text('找到 ' + cmtSearchMatches.length + ' 条匹配评论 (当前第 1 条)');
                $('#commentSearchNav').show();
            }} else {{
                $('#commentSearchNav').hide();
            }}
            
            renderCommentPage(startPage);
        }} else {{
            var url = $cell.closest('tr').find('a.modpack-link').attr('href') || 'https://www.mcmod.cn/';
            var commentUrl = getCommentUrl(url);
            $('#commentModpackLink').attr('href', commentUrl);
            $commentOpen.attr('href', commentUrl);
            $('#commentSearchNav').hide();
            $('#commentSearchInput').prop('disabled', true);
            $cCount.text('共 ' + pageCount + ' 条 · 主楼 0 · 楼中楼 0');
            $cBody.html('<div class="comment-empty-hint">暂无详细评论预览<br>' + (pageCount > 0 ? '共 ' + pageCount + ' 条 · 主楼 0 · 楼中楼 0<br>' : '') + '<a href="' + commentUrl + '" target="_blank">前往 MC百科 原页面查看 →</a></div>');
            $('#commentPageBar').hide();
        }}
        $cpopup.addClass('show needs-consent');
        repositionCommentPopup();
        // ✨ 完美的咬合节点：弹窗加载和精准坐标偏置完成后，立刻调取判定
        checkCommentOverflow();
    }}
    function hideCommentPopup() {{
        function clearCommentPopupLayout() {{
            $cpopup.css({{
                height: '',
                'min-height': '',
                'max-height': '',
                top: '',
                bottom: '',
                left: ''
            }});
            $cBody.css('max-height', '');
        }}
        if ($cpopup.hasClass('show')) {{
            $cpopup.addClass('hiding').removeClass('show needs-consent');
            setTimeout(function() {{
                $cpopup.removeClass('hiding');
                clearCommentPopupLayout();
            }}, 180);
        }} else {{
            $cpopup.removeClass('show needs-consent hiding');
            clearCommentPopupLayout();
        }}
        activeCommentCell = null;
        cmtSearchMatches = [];
        cmtSearchMatchPointer = -1;
    }}
    // =====================================================================
    // ───── 迷你走势悬浮窗渲染系统 ─────
    var $trendTooltip = $('<div class="trend-tooltip" id="trendTooltip">' +
        '<button type="button" class="hover-close" id="trendClose" title="关闭趋势图">✕</button>' +
        '<div class="trend-tooltip-title" id="trendTooltipTitle"></div>' +
        '<div class="trend-tooltip-subtitle" id="trendTooltipSubtitle">近 60 天指数走势历史</div>' +
        '<div class="trend-tooltip-chart-container" id="trendTooltipChartContainer"></div>' +
        '<div class="trend-point-label" id="trendPointLabel"></div>' +
        '<div class="trend-tooltip-footer" id="trendTooltipFooter"></div>' +
        '<div class="hover-cooldown-tip">再次点击同一趋势格、按 Esc 或点右上角可关闭</div>' +
        '</div>').appendTo('body');
    var $trendBridge = $('<div class="trend-hover-bridge" id="trendHoverBridge"></div>').appendTo('body');
    var trendHoverTimer = null;
    var activeTrendCell = null;
    var activeTrendRowKey = '';
    var trendSuppressOpenUntil = 0;
    var trendPopupPinned = false;
    var trendHoverPopupEnabled = localStorage.getItem('trend-hover-popup-enabled') === '1';
    function getTrendRowKey(cell) {{
        var $cell = $(cell);
        var $row = $cell.closest('tr');
        return String($row.attr('data-mid') || $row.data('mid') || $cell.data('title') || '');
    }}
    function syncHoverToggles() {{
        $('.js-desc-hover-toggle').prop('checked', descHoverPopupEnabled).closest('.mode-toggle-header').toggleClass('is-on', descHoverPopupEnabled).attr('aria-pressed', descHoverPopupEnabled ? 'true' : 'false');
        $('.js-trend-hover-toggle').prop('checked', trendHoverPopupEnabled).closest('.mode-toggle-header').toggleClass('is-on', trendHoverPopupEnabled).attr('aria-pressed', trendHoverPopupEnabled ? 'true' : 'false');
        $('.js-comment-hover-toggle').prop('checked', commentHoverPopupEnabled).closest('.mode-toggle-header').toggleClass('is-on', commentHoverPopupEnabled).attr('aria-pressed', commentHoverPopupEnabled ? 'true' : 'false');
    }}
    function setDescHoverMode(enabled) {{
        descHoverPopupEnabled = !!enabled;
        localStorage.setItem('desc-hover-popup-enabled', descHoverPopupEnabled ? '1' : '0');
        syncHoverToggles();
    }}
    function setTrendHoverMode(enabled) {{
        trendHoverPopupEnabled = !!enabled;
        localStorage.setItem('trend-hover-popup-enabled', trendHoverPopupEnabled ? '1' : '0');
        syncHoverToggles();
        if (!trendHoverPopupEnabled && !trendPopupPinned) {{
            $('#trendPointLabel').hide();
            $('#trendGuideLine').css('visibility', 'hidden');
            hideTrendBridge();
            $trendTooltip.removeClass('show').hide();
        }}
    }}
    function setCommentHoverMode(enabled) {{
        commentHoverPopupEnabled = !!enabled;
        localStorage.setItem('comment-hover-popup-enabled', commentHoverPopupEnabled ? '1' : '0');
        syncHoverToggles();
    }}
    function toggleHeaderMode(toggle) {{
        if (!toggle) return;
        if (toggle.querySelector('.js-desc-hover-toggle')) {{
            setDescHoverMode(!descHoverPopupEnabled);
        }} else if (toggle.querySelector('.js-trend-hover-toggle')) {{
            setTrendHoverMode(!trendHoverPopupEnabled);
        }} else if (toggle.querySelector('.js-comment-hover-toggle')) {{
            setCommentHoverMode(!commentHoverPopupEnabled);
        }}
    }}
    document.addEventListener('click', function(e) {{
        var toggle = e.target && e.target.closest ? e.target.closest('.mode-toggle-header') : null;
        if (!toggle) return;
        e.preventDefault();
        e.stopPropagation();
        if (e.stopImmediatePropagation) e.stopImmediatePropagation();
        toggleHeaderMode(toggle);
    }}, true);
    ['pointerdown', 'mousedown', 'mouseup', 'dblclick'].forEach(function(evtName) {{
        document.addEventListener(evtName, function(e) {{
            var toggle = e.target && e.target.closest ? e.target.closest('.mode-toggle-header') : null;
            if (!toggle) return;
            e.stopPropagation();
            if (e.stopImmediatePropagation) e.stopImmediatePropagation();
        }}, true);
    }});
    document.addEventListener('keydown', function(e) {{
        var toggle = e.target && e.target.closest ? e.target.closest('.mode-toggle-header') : null;
        if (!toggle || (e.key !== 'Enter' && e.key !== ' ')) return;
        e.preventDefault();
        e.stopPropagation();
        if (e.stopImmediatePropagation) e.stopImmediatePropagation();
        toggleHeaderMode(toggle);
    }}, true);
    $(document).on('mousedown click dblclick', '.mode-toggle, .mode-toggle input', function(e) {{
        e.stopPropagation();
    }});
    syncHoverToggles();
    $(document).on('change', '.js-desc-hover-toggle', function(e) {{
        e.stopPropagation();
        setDescHoverMode($(this).is(':checked'));
    }});
    $(document).on('change', '.js-trend-hover-toggle', function(e) {{
        e.stopPropagation();
        setTrendHoverMode($(this).is(':checked'));
    }});
    $(document).on('change', '.js-comment-hover-toggle', function(e) {{
        e.stopPropagation();
        setCommentHoverMode($(this).is(':checked'));
    }});
    function isTrendHoverAlive() {{
        var overTooltip = $trendTooltip.is(':hover');
        var overBridge = $trendBridge.is(':hover');
        var overCell = activeTrendCell && activeTrendCell.length && activeTrendCell.is(':hover');
        return !!(overTooltip || overBridge || overCell);
    }}
    function hideTrendBridge() {{
        $trendBridge.hide();
    }}
    function hideTrendTooltipSoon(delay) {{
        if (trendPopupPinned) return;
        clearTimeout(trendHoverTimer);
        trendHoverTimer = setTimeout(function() {{
            if (isTrendHoverAlive()) return;
            $('#trendPointLabel').hide();
            $('#trendGuideLine').css('visibility', 'hidden');
            $trendTooltip.addClass('hiding').removeClass('show');
            hideTrendBridge();
            setTimeout(function() {{
                if (!$trendTooltip.hasClass('show')) $trendTooltip.hide().removeClass('hiding');
                activeTrendCell = null;
            }}, 180);
        }}, delay || 720);
    }}
    function hideTrendTooltipNow() {{
        clearTimeout(trendHoverTimer);
        trendPopupPinned = false;
        $('#trendPointLabel').hide();
        $('#trendGuideLine').css('visibility', 'hidden');
        hideTrendBridge();
        $trendTooltip.removeClass('show hiding').hide();
        activeTrendCell = null;
        activeTrendRowKey = '';
    }}
    function updateTrendBridge($cell) {{
        if (!$cell || !$cell.length || !$trendTooltip.is(':visible')) return;
        var c = $cell[0].getBoundingClientRect();
        var t = $trendTooltip[0].getBoundingClientRect();
        var left = Math.min(c.left, t.left) - 8;
        var right = Math.max(c.right, t.right) + 8;
        var top = Math.min(c.top, t.top) - 8;
        var bottom = Math.max(c.bottom, t.bottom) + 8;
        $trendBridge.css({{
            left: Math.max(0, left) + 'px',
            top: Math.max(0, top) + 'px',
            width: Math.max(1, right - left) + 'px',
            height: Math.max(1, bottom - top) + 'px'
        }}).show();
    }}
    function positionTrendTooltip(anchorEvent, $cell) {{
        var tw = $trendTooltip.outerWidth();
        var th = $trendTooltip.outerHeight();
        var vw = window.innerWidth;
        var vh = window.innerHeight;
        var gap = 2;
        var rect = $cell && $cell.length ? $cell[0].getBoundingClientRect() : null;
        var left = rect ? (rect.left + rect.width / 2 - tw / 2) : 10;
        var top = rect ? (rect.top - th - gap) : 10;
        if (rect && top < 10) {{
            top = Math.min(rect.bottom + gap, vh - th - 10);
        }}
        if (top + th > vh - 10) top = vh - th - 10;
        if (top < 10) top = 10;
        if (left + tw > vw - 10) left = vw - tw - 10;
        if (left < 10) left = 10;
        $trendTooltip.css({{ left: left + 'px', top: top + 'px' }});
        updateTrendBridge($cell);
    }}
    $(document).on('trend:open', '.td-trend', function(e, pinned, sourceEvent) {{
        clearTimeout(trendHoverTimer);
        if (Date.now() < trendSuppressOpenUntil) return;
        if (!pinned && (!trendHoverPopupEnabled || trendPopupPinned)) return;
        if (pinned) trendPopupPinned = true;
        var anchorEvent = sourceEvent || e;
        var $cell = $(this);
        activeTrendCell = $cell;
        activeTrendRowKey = getTrendRowKey($cell);
        var title = $cell.data('title') || '';
        var trendKey = 'trend:' + title + ':' + ($cell.data('trend') || '');
        activeTrendKey = trendKey;
        if (isHoverCooling(trendKey)) return;
        if ($trendTooltip.hasClass('show') && $trendTooltip.data('active-row-key') === activeTrendRowKey && activeTrendCell && activeTrendCell.length && $cell.is(activeTrendCell)) {{
            return;
        }}
        var metric = $cell.data('metric') || '走势';
        var trendStr = $cell.data('trend') || '';
        var datesStr = $cell.data('dates') || '';
        if (!trendStr) {{
            $trendTooltip.hide();
            return;
        }}
        var trendVals = trendStr.split(',').map(Number).filter(function(v) {{ return !isNaN(v); }});
        var dates = datesStr.split(',');
        if (trendVals.length < 2) {{
            $trendTooltip.hide();
            return;
        }}
        // 渲染标题
        $('#trendTooltipTitle').text(title);
        $('#trendTooltipSubtitle').text(metric + ' · 近 ' + trendVals.length + ' 天指数走势');
        // 测算数值范围
        var minVal = Math.min.apply(null, trendVals);
        var maxVal = Math.max.apply(null, trendVals);
        var latestVal = trendVals[trendVals.length - 1];
        var startVal = trendVals[0];
        var avgVal = Math.round(trendVals.reduce(function(a, b){{ return a + b; }}, 0) / trendVals.length);
        var firstDate = dates[0] || '';
        var lastDate = dates[trendVals.length - 1] || '';
        var delta = latestVal - startVal;
        var deltaPct = startVal ? (delta / startVal * 100) : 0;
        var deltaAbs = Math.abs(Math.round(delta));
        var deltaPctAbs = Math.abs(deltaPct).toFixed(1);
        var deltaDir = delta === 0 ? '基本不变' : (delta > 0 ? '增加 ' : '减少 ') + deltaAbs + ' 点';
        var deltaPctText = delta === 0 ? '0%' : (delta > 0 ? '上涨 ' : '下降 ') + deltaPctAbs + '%';
        var rangeText = firstDate && lastDate ? (firstDate + ' 至 ' + lastDate) : ('共 ' + trendVals.length + ' 天');
        // 填充页脚统计
        $('#trendTooltipFooter').html(
            '<span>最新指数<br><b>' + latestVal + '</b></span>' +
            '<span>总涨幅<br><b>' + deltaDir + '</b><em>' + deltaPctText + '</em></span>' +
            '<span>平均 / 最高<br><b>' + avgVal + ' / ' + maxVal + '</b></span>'
        );
        $('#trendTooltipSubtitle').text(metric + ' · 本地/官网历史 ' + trendVals.length + ' 天 · ' + rangeText);
        // 生成 SVG 走势图
        var width = 352;
        var height = 150;
        var paddingT = 18;
        var paddingB = 22;
        var paddingL = 28;
        var paddingR = 12;
        var chartW = width - paddingL - paddingR;
        var chartH = height - paddingT - paddingB;
        var valDiff = maxVal - minVal;
        if (valDiff === 0) valDiff = 1;
        var points = [];
        var len = trendVals.length;
        for (var i = 0; i < len; i++) {{
            var x = paddingL + (i / (len - 1)) * chartW;
            var y = height - paddingB - ((trendVals[i] - minVal) / valDiff) * chartH;
            points.push({{ x: x, y: y, value: trendVals[i], date: dates[i] || '' }});
        }}
        // 生成连线 path 和渐变填充 path
        var pathD = 'M ' + points[0].x + ' ' + points[0].y;
        for (var i = 1; i < len; i++) {{
            pathD += ' L ' + points[i].x + ' ' + points[i].y;
        }}
        var areaD = pathD +
            ' L ' + points[len-1].x + ' ' + (height - paddingB) +
            ' L ' + points[0].x + ' ' + (height - paddingB) + ' Z';
        var trendColor = 'var(--primary)';
        var markerHtml = '';
        var hitHtml = '<line class="trend-guide-line" id="trendGuideLine" x1="' + paddingL + '" y1="' + paddingT + '" x2="' + paddingL + '" y2="' + (height - paddingB) + '" />' +
            '<rect class="trend-chart-capture" x="' + paddingL + '" y="' + paddingT + '" width="' + chartW + '" height="' + chartH + '" fill="rgba(0,0,0,0.001)" pointer-events="all" />';
        for (var i = 0; i < len; i++) {{
            var p = points[i];
            var isMax = p.value === maxVal;
            var isMin = p.value === minVal;
            var isLatest = i === len - 1;
            if (isMax || isMin || isLatest || i === 0) {{
                markerHtml += '<circle class="trend-point-visible" cx="' + p.x + '" cy="' + p.y + '" r="' + (isMax ? 5.5 : isLatest ? 5 : 3.5) + '" fill="var(--glass-bg-solid)" stroke="' + trendColor + '" stroke-width="' + (isMax ? 2.4 : 1.8) + '" />';
            }}
            hitHtml += '<circle class="trend-point-hit" cx="' + p.x + '" cy="' + p.y + '" r="8" fill="rgba(0,0,0,0.001)" data-x="' + p.x + '" data-y="' + p.y + '" data-date="' + p.date + '" data-value="' + p.value + '" data-kind="' + (isMax ? '峰值' : isMin ? '低点' : isLatest ? '最新' : '') + '" />';
        }}
        // 绘制 SVG (使用主题颜色)
        var svgHtml = '<svg width="' + width + '" height="' + height + '">' +
            '<defs>' +
            '  <linearGradient id="trendGrad" x1="0%" y1="0%" x2="0%" y2="100%">' +
            '    <stop offset="0%" stop-color="' + trendColor + '" stop-opacity="0.36"/>' +
            '    <stop offset="100%" stop-color="' + trendColor + '" stop-opacity="0.0"/>' +
            '  </linearGradient>' +
            '</defs>' +
            '<line x1="' + paddingL + '" y1="' + paddingT + '" x2="' + (width - paddingR) + '" y2="' + paddingT + '" stroke="var(--glass-border)" stroke-dasharray="4,4" />' +
            '<line x1="' + paddingL + '" y1="' + (height - paddingB) + '" x2="' + (width - paddingR) + '" y2="' + (height - paddingB) + '" stroke="var(--glass-border)" stroke-dasharray="4,4" />' +
            '<text x="2" y="' + (paddingT + 4) + '" font-size="10" fill="var(--text-secondary)" text-anchor="start">' + maxVal + '</text>' +
            '<text x="2" y="' + (height - paddingB + 4) + '" font-size="10" fill="var(--text-secondary)" text-anchor="start">' + minVal + '</text>' +
            '<path d="' + areaD + '" fill="url(#trendGrad)" />' +
            '<path d="' + pathD + '" fill="none" stroke="' + trendColor + '" stroke-width="2.7" stroke-linecap="round" stroke-linejoin="round" />' +
            markerHtml +
            hitHtml +
            '<text x="' + paddingL + '" y="' + (height - 5) + '" font-size="10" fill="var(--text-secondary)" text-anchor="start">' + firstDate + '</text>' +
            '<text x="' + (width - paddingR) + '" y="' + (height - 5) + '" font-size="10" fill="var(--text-secondary)" text-anchor="end">' + lastDate + '</text>' +
            '</svg>';
        $('#trendTooltipChartContainer').html(svgHtml + '<div class="trend-point-label" id="trendPointLabel" style="display:none; position:absolute; z-index:10; pointer-events:none;"></div>');
        function showTrendPoint(point) {{
            if (!point) return;
            var x = Number(point.x) || 0;
            var y = Number(point.y) || 0;
            var kind = point.kind || '';
            var date = point.date || '未知日期';
            var value = point.value;
            $('#trendPointLabel')
                .html((kind ? '<b>' + kind + '</b><br>' : '') + date + '<br>指数 ' + value)
                .css({{ left: Math.min(Math.max(x + 10, 8), width - 118) + 'px', top: Math.max(y - 34, 6) + 'px' }})
                .show();
            $('#trendGuideLine')
                .attr('x1', x).attr('x2', x)
                .css('visibility', 'visible');
        }}
        function pointFromNode(node) {{
            return {{
                x: Number(node.getAttribute('data-x')) || 0,
                y: Number(node.getAttribute('data-y')) || 0,
                date: node.getAttribute('data-date') || '',
                value: node.getAttribute('data-value') || '',
                kind: node.getAttribute('data-kind') || ''
            }};
        }}
        function nearestPointFromEvent(e) {{
            var svg = e.currentTarget.ownerSVGElement || e.currentTarget;
            var rect = svg.getBoundingClientRect();
            var clickX = e.clientX - rect.left;
            var chartX = clickX - paddingL;
            var ratio = chartX / chartW;
            var idx = Math.round(ratio * (len - 1));
            if (idx < 0) idx = 0;
            if (idx >= len) idx = len - 1;
            var point = points[idx];
            var isMax = point.value === maxVal;
            var isMin = point.value === minVal;
            var isLatest = idx === len - 1;
            return {{ x: point.x, y: point.y, date: point.date, value: point.value, kind: isMax ? '峰值' : isMin ? '低点' : isLatest ? '最新' : '' }};
        }}
        showTrendPoint({{
            x: points[len - 1].x,
            y: points[len - 1].y,
            date: points[len - 1].date,
            value: points[len - 1].value,
            kind: '最新'
        }});
        $('#trendTooltipChartContainer .trend-chart-capture').on('mouseenter mousemove click', function(e) {{
            showTrendPoint(nearestPointFromEvent(e));
        }});
        $('#trendTooltipChartContainer .trend-point-hit').on('mouseenter mousemove click', function() {{
            showTrendPoint(pointFromNode(this));
        }});
        $trendTooltip.removeClass('hiding').addClass('show').data('active-title', title).data('active-row-key', activeTrendRowKey).show();
        positionTrendTooltip(anchorEvent, $cell);
    }});
    $(document).on('mouseenter', '.td-trend', function(e) {{
        $(this).trigger('trend:open', [false, e]);
    }});
    $(document).on('click', '.td-trend', function(e) {{
        if ($(e.target).closest('a, button').length) return;
        if (Date.now() < trendSuppressOpenUntil) {{
            e.preventDefault();
            e.stopPropagation();
            return;
        }}
        e.preventDefault();
        e.stopPropagation();
        var clickedRowKey = getTrendRowKey(this);
        if ($trendTooltip.hasClass('show') && $trendTooltip.data('active-row-key') === clickedRowKey) {{
            hideTrendTooltipNow();
            trendSuppressOpenUntil = Date.now() + 220;
            return;
        }}
        $(this).trigger('trend:open', [true, e]);
    }});
    document.addEventListener('click', function(e) {{
        var cell = e.target && e.target.closest ? e.target.closest('td.td-trend') : null;
        if (!cell || e.target.closest('a, button')) return;
        var clickedRowKey = getTrendRowKey(cell);
        if ($trendTooltip.hasClass('show') && $trendTooltip.data('active-row-key') === clickedRowKey) {{
            e.preventDefault();
            e.stopPropagation();
            if (e.stopImmediatePropagation) e.stopImmediatePropagation();
            hideTrendTooltipNow();
            trendSuppressOpenUntil = Date.now() + 220;
        }}
    }}, true);
    $(document).on('mouseleave', '.td-trend', function() {{
        hideTrendTooltipSoon(720);
    }});
    $trendTooltip.on('mouseenter', function() {{
        clearTimeout(trendHoverTimer);
    }}).on('mouseleave', function() {{
        hideTrendTooltipSoon(360);
    }});
    $trendTooltip.on('mousedown', function(e) {{
        if ($(e.target).is('#trendTooltip')) {{
            hideTrendTooltipNow();
        }}
    }});
    $trendBridge.on('mouseenter', function() {{
        clearTimeout(trendHoverTimer);
    }}).on('mouseleave', function() {{
        hideTrendTooltipSoon(360);
    }});
    function showInlineTrendProbe(e, $svg) {{
        var $cell = $svg.closest('.td-trend');
        var trendStr = $cell.data('trend') || '';
        var datesStr = $cell.data('dates') || '';
        if (!trendStr) return;
        var vals = trendStr.split(',').map(Number).filter(function(v) {{ return !isNaN(v); }});
        var dates = datesStr ? datesStr.split(',') : [];
        if (vals.length < 2) return;
        var rect = $svg[0].getBoundingClientRect();
        var ratio = (e.clientX - rect.left) / rect.width;
        if (ratio < 0) ratio = 0;
        if (ratio > 1) ratio = 1;
        var idx = Math.round(ratio * (vals.length - 1));
        var value = vals[idx];
        var date = dates[idx] || '';
        var $probe = $cell.children('.trend-inline-probe');
        if (!$probe.length) {{
            $probe = $('<div class="trend-inline-probe"></div>').appendTo($cell);
        }}
        var cellRect = $cell[0].getBoundingClientRect();
        var left = e.clientX - cellRect.left + 10;
        var top = e.clientY - cellRect.top - 42;
        if (left > cellRect.width - 104) left = Math.max(6, cellRect.width - 104);
        if (top < 6) top = e.clientY - cellRect.top + 12;
        $probe.html('<b>' + value + '</b>' + (date ? date : '')).
            css({{ left: left + 'px', top: top + 'px' }}).show();
    }}
    $(document).on('mousemove', '.sparkline-svg', function(e) {{
        showInlineTrendProbe(e, $(this));
    }});
    $(document).on('mouseleave', '.sparkline-svg', function() {{
        $(this).closest('.td-trend').children('.trend-inline-probe').hide();
    }});
    // ────── 悬浮窗智能自适应延迟关闭与滚轮管理系统 ──────
    // =====================================================================
    /* ── 1. 悬停整合包名称 → 显示介绍（带 300ms 延迟及淡入淡出锁死） ── */
    $(document).on('mouseenter', '.modpack-link', function() {{
        if (!descHoverPopupEnabled) return;
        var $self = $(this);
        var descKey = 'desc:' + (($self.data('mid') || '') || ($self.attr('href') || '') || $self.text());
        if (isHoverCooling(descKey)) return;
        clearTimeout(hoverTimer);
        hoverTimer = setTimeout(function() {{
            showDescPopup($self);
            $('body').css({{ 'overflow': 'hidden', 'height': '100vh' }});
        }}, HOVER_DELAY);
    }});
    $(document).on('mouseleave', '.modpack-link', function() {{
        if (!descHoverPopupEnabled) return;
        clearTimeout(hoverTimer);
        hoverTimer = setTimeout(function() {{
            hideDescPopup();
            $('body').css({{ 'overflow': '', 'height': '' }});
        }}, 300);
    }});
    $(document).on('click', '.modpack-link', function(e) {{
        if (descHoverPopupEnabled) return;
        e.preventDefault();
        e.stopPropagation();
        var $self = $(this);
        var descKey = 'desc:' + (($self.data('mid') || '') || ($self.attr('href') || '') || $self.text());
        if ($popup.hasClass('show') && activeDescKey === descKey) {{
            hideDescPopup();
            $('body').css({{ 'overflow': '', 'height': '' }});
            return;
        }}
        clearTimeout(hoverTimer);
        showDescPopup($self);
        $('body').css({{ 'overflow': 'hidden', 'height': '100vh' }});
    }});
    $popup.on('mouseenter', function() {{
        clearTimeout(hoverTimer);
        $('body').css({{ 'overflow': 'hidden', 'height': '100vh' }});
    }}).on('mouseleave', function() {{
        if (!descHoverPopupEnabled) return;
        clearTimeout(hoverTimer);
        hoverTimer = setTimeout(function() {{
            hideDescPopup();
            $('body').css({{ 'overflow': '', 'height': '' }});
        }}, 300);
    }});
    /* ── 2. 点击评论列 → 稳定打开评论详情；不再扫过表格就弹大窗 ── */
    $(document).on('click', '.td-comment', function(e) {{
        if ($(e.target).closest('a, button').length) return;
        var $self = $(this);
        clearTimeout(commentHoverTimer);
        if ($cpopup.hasClass('show') && activeCommentCell && activeCommentCell.length && $self.is(activeCommentCell)) {{
            hideCommentPopup();
            $('body').css({{ 'overflow': '', 'height': '' }});
            return;
        }}
        showCommentPopup($self);
        $('body').css({{ 'overflow': 'hidden', 'height': '100vh' }});
    }});
    $(document).on('keydown', '.engage-comment-trigger', function(e) {{
        if (e.key !== 'Enter' && e.key !== ' ') return;
        e.preventDefault();
        $(this).closest('.td-comment').trigger('click');
    }});
    $(document).on('mouseenter', '.td-comment', function() {{
        if (!commentHoverPopupEnabled) return;
        var $self = $(this);
        clearTimeout(commentHoverTimer);
        commentHoverTimer = setTimeout(function() {{
            if (!$self.is(':hover')) return;
            showCommentPopup($self);
            $('body').css({{ 'overflow': 'hidden', 'height': '100vh' }});
        }}, HOVER_DELAY);
    }});
    $(document).on('mouseleave', '.td-comment', function() {{
        if (!commentHoverPopupEnabled) return;
        clearTimeout(commentHoverTimer);
        commentHoverTimer = setTimeout(function() {{
            if ($cpopup.is(':hover')) return;
            hideCommentPopup();
            $('body').css({{ 'overflow': '', 'height': '' }});
        }}, 260);
    }});
    $(document).on('mousedown', function(e) {{
        if (!$cpopup.hasClass('show')) return;
        if ($(e.target).closest('#commentPopup, .td-comment, .comment-search-nav, .comment-page-bar').length) return;
        hideCommentPopup();
        $('body').css({{ 'overflow': '', 'height': '' }});
    }});
    $cpopup.on('mousedown', function(e) {{
        if ($(e.target).is('#commentPopup')) {{
            hideCommentPopup();
            $('body').css({{ 'overflow': '', 'height': '' }});
        }}
    }});
    $cpopup.on('mouseenter', function() {{
        clearTimeout(commentHoverTimer);
        $('body').css({{ 'overflow': 'hidden', 'height': '100vh' }});
    }}).on('mouseleave', function() {{
        if (!commentHoverPopupEnabled) return;
        clearTimeout(commentHoverTimer);
        commentHoverTimer = setTimeout(function() {{
            hideCommentPopup();
            $('body').css({{ 'overflow': '', 'height': '' }});
        }}, 280);
    }});
    /* ── 3. 关闭/Escape 恢复现场 ── */
    $('#pvClose').on('click', function(e) {{
        e.preventDefault();
        e.stopPropagation();
        setHoverCooldown(activeDescKey);
        hideDescPopup();
        $('body').css({{ 'overflow': '', 'height': '' }});
    }});
    $('#commentClose').on('click', function(e) {{
        e.preventDefault();
        e.stopPropagation();
        hideCommentPopup();
        $('body').css({{ 'overflow': '', 'height': '' }});
    }});
    $('#trendClose').on('click', function(e) {{
        e.preventDefault();
        e.stopPropagation();
        hideTrendTooltipNow();
    }});
    $(document).on('keydown', function(e) {{
        if (e.key === 'Escape') {{
            hideDescPopup();
            hideCommentPopup();
            hideTrendTooltipNow();
            closeImageLightbox();
            $('body').css({{ 'overflow': '', 'height': '' }});
        }} else if ($cpopup.hasClass('show')) {{
            if (e.key === 'ArrowLeft') {{
                e.preventDefault();
                $('#cmtPrev').trigger('click');
            }} else if (e.key === 'ArrowRight') {{
                e.preventDefault();
                $('#cmtNext').trigger('click');
            }}
        }}
    }});
    /* 窗口缩放 → 更新 scrollY */
    var resizeTimer = null;
    $(window).on('resize', function() {{
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {{
            var newH = Math.max(400, $(window).height() - 320);
            $('.dataTables_scrollBody').height(newH);
            if (table) {{
                table.columns.adjust();
            }}
            if ($cpopup.hasClass('show')) {{
                lockCommentPopupSize();
                repositionCommentPopup();
                checkCommentOverflow();
            }}
        }}, 300);
    }});
    }}, 10); }}); // 数据到位后再初始化表格
}});
</script>
</body>
</html>'''

def gen_pretty_html(data, theme_name="light", comment_api_base="/api"):
    # 直接从爬虫 JSON 行中构建介绍/评论预览数据
    _ill_re = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
    desc_data = {}
    comment_data = {}
    for d in data:
        mid = _extract_mid(d.get("url", ""))
        if not mid:
            continue
        # 介绍：直接从 JSON 的整合包介绍字段读取
        desc_text = _ill_re.sub('', d.get("desc") or "")
        desc_images = normalize_image_list(d.get("intro_images") or [])
        if desc_text or desc_images:
            desc_data[mid] = {"text": desc_text, "images": desc_images}
        # 评论：page_count = JSON 评论数字段（页面统计的总数）
        cmt_page_val = int(d.get("com_n") or 0)
        if d.get("comments_raw") and d["comments_raw"].strip():
            try:
                # 1. 先用正则剔除掉恶心的低位非法控制字符
                clean_comments = _ill_re.sub('', d["comments_raw"])
                # 2. 增加 strict=False 允许合法的换行符/制表符等控制字符直接解析
                cmt_list = json.loads(clean_comments, strict=False)
                # 诱饵数据清洗：实际提取数 = 楼层数 + 楼中楼回复数
                actual_scraped = len(cmt_list) + sum(len(c.get('replies', [])) for c in cmt_list if isinstance(c, dict))
                cmt_total = max(int(d.get("comment_total") or 0), actual_scraped)
                cmt_page_val = max(cmt_page_val, cmt_total)
                comment_data[mid] = {"true_count": cmt_total, "page_count": cmt_page_val, "comments": cmt_list}
                d["com_n"] = cmt_total
                d["com_d"] = str(cmt_total)
                continue
            except (ValueError, TypeError) as e:
                # 临时打印一下到底是哪个整合包的 JSON 格式写错了，方便排查
                print(f"[提示] 整合包 ID {mid} 评论 JSON 解析失败，原因: {e}")
                pass
        if cmt_page_val > 0:
            comment_data[mid] = {"true_count": 0, "page_count": cmt_page_val, "comments": []}
    print("  -> 介绍数据: {} 条 | 评论数据: {} 条".format(len(desc_data), len(comment_data)))
    desc_json_str = json.dumps(desc_data, ensure_ascii=False)
    compare_data = {}
    # 完整模组卡片数据只作为延迟渲染源存在：页面初始不把它们插进 DOM。
    mod_detail_data = {}
    for d in data:
        mid = _extract_mid(d.get("url", ""))
        if not mid:
            continue
        title_cn, title_en = split_modpack_title(d.get("title", ""))
        mods = []
        mod_categories = []
        detail_groups = []
        detail_group_map = {}
        seen_mod = set()
        seen_cat = set()
        for m in d.get("mods", []):
            if not isinstance(m, dict):
                continue
            name = _s(m.get("name") or m.get("title"))
            if not name:
                continue
            key = name.lower()
            if key not in seen_mod:
                seen_mod.add(key)
                # 对比只需要模组名称；链接和重复元数据会让单文件看板膨胀到数百 MB。
                mods.append(name)
            cat_name = _s(m.get("category_name") or "未分类")
            if cat_name and cat_name not in seen_cat:
                seen_cat.add(cat_name)
                mod_categories.append(cat_name)
            cat_id = _s(m.get("category_id"))
            group_key = "{}|{}".format(cat_id, cat_name)
            if group_key not in detail_group_map:
                detail_group_map[group_key] = {
                    "k": "cat{}".format(len(detail_groups)),
                    "n": cat_name,
                    "u": _s(m.get("category_url")),
                    "m": [],
                }
                detail_groups.append(detail_group_map[group_key])
            detail_group_map[group_key]["m"].append([
                name,
                _s(m.get("version")),
                _s(m.get("url")),
                _s(m.get("title") or name),
            ])
        compare_data[mid] = {
            "mid": mid,
            "title": d.get("title", ""),
            "title_cn": title_cn or d.get("title", ""),
            "title_en": title_en,
            "url": d.get("url", ""),
            "type": d.get("modpack_type") or "未标明",
            "views": int(d.get("views_n") or 0),
            "score": int(d.get("score_n") or 0),
            "trend_latest": int(d.get("lat_n") or 0),
            "trend_days": int(d.get("trend_days") or 0),
            "comments": int(d.get("com_n") or 0),
            "recommend": int(d.get("rec_n") or 0),
            "favorite": int(d.get("fav_n") or 0),
            "red_votes": int(d.get("rv_n") or 0),
            "black_votes": int(d.get("bpv_n") or 0),
            "growth7": d.get("t7_d") or "",
            "growth30": d.get("t30_d") or "",
            "growth60": d.get("t60_d") or "",
            "categories": list(d.get("cat", [])),
            "tags": list(d.get("pack", [])),
            "mods": mods,
            "mod_categories": mod_categories,
        }
        mod_detail_data[mid] = detail_groups
    compare_json_str = json.dumps(compare_data, ensure_ascii=False)
    mod_detail_json_str = json.dumps(mod_detail_data, ensure_ascii=False, separators=(',', ':'))
    cat_opts = "\n".join(
        '                    <option value="{}">{} ({})</option>'.format(esc_attr(tag), esc(tag), count)
        for tag, count in build_category_options(data)
    )
    pack_opts = "\n".join(
        '                    <option value="{}">{} ({})</option>'.format(esc_attr(tag), esc(tag), count)
        for tag, count in build_packtag_options(data)
    )
    type_opts = "\n".join(
        '                    <option value="{}">{} ({})</option>'.format(esc_attr(tag), esc(tag), count)
        for tag, count in build_modpack_type_options(data)
    )
    mod_cat_opts = "\n".join(
        '                    <option value="{}">{} ({})</option>'.format(esc_attr(tag), esc(tag), count)
        for tag, count in build_mod_category_options(data)
    )
    mod_opts = "\n".join(
        '                    <option value="{}">{} ({})</option>'.format(esc_attr(tag), esc(tag), count)
        for tag, count in build_mod_options(data)
    )
    trend_opts = "\n".join(
        '                    <option value="{}">{} ({})</option>'.format(esc_attr(value), esc(label), count)
        for value, label, count in build_trend_filter_options(data)
    )
    rows_html = "\n\n".join(gen_row_pretty(d, idx) for idx, d in enumerate(data))
    total = len(data)
    total_views = sum(d["views_n"] for d in data)
    if total_views >= 10000:
        total_views_str = "{:.1f}万".format(total_views / 10000.0)
    else:
        total_views_str = str(total_views)
    total_comments = int(sum(d["com_n"] for d in data))
    total_comments_str = "{:,}".format(total_comments)
    title = "{} mcmod 整合包数据（仅供参考）".format(today_str())
    theme = THEMES.get(theme_name, THEMES["light"])
    return PRETTY_TEMPLATE.format(
        title=title, cat_opts=cat_opts, pack_opts=pack_opts, type_opts=type_opts,
        trend_opts=trend_opts,
        mod_cat_opts=mod_cat_opts, mod_opts=mod_opts, rows="",
        total=total, total_views=total_views_str, total_comments=total_comments_str,
        desc_json=desc_json_str,
        comment_api_base_json=json.dumps(comment_api_base, ensure_ascii=False),
        dashboard_api_base_json=json.dumps(comment_api_base, ensure_ascii=False),
        compare_json=compare_json_str,
        mod_detail_json=mod_detail_json_str,
        theme_warm=THEMES["warm"]["root"],
        theme_dark=THEMES["dark"]["root"],
        theme_light=THEMES["light"]["root"],
        theme_eye=THEMES["eye"]["root"],
        theme_pink=THEMES["pink"]["root"],
        theme_anime=THEMES["anime"]["root"],
        default_theme=theme_name,
    ), comment_data, rows_html


def dashboard_data_dir_for_html(html_path):
    """All generated data for one dashboard stays in its sibling data folder."""
    return os.path.join(os.path.dirname(os.path.abspath(html_path)), "data")


def comment_data_dir_for_html(html_path):
    return os.path.join(dashboard_data_dir_for_html(html_path), "comments")


def write_dashboard_sidecars(comment_data, rows_html, html_path):
    """Write one small comment payload per pack so the browser can request it on demand."""
    comment_dir = comment_data_dir_for_html(html_path)
    os.makedirs(comment_dir, exist_ok=True)
    for mid, payload in comment_data.items():
        safe_mid = str(mid)
        if not safe_mid.isdigit():
            continue
        with open(os.path.join(comment_dir, safe_mid + ".json"), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(dashboard_data_dir_for_html(html_path), "table_rows.html"), "w", encoding="utf-8") as f:
        f.write(rows_html)
    return comment_dir, len(comment_data)

# ═══════════════════════ 主程序 ═══════════════════════

def list_themes():
    """列出所有可用主题"""
    print("可用主题：")
    for key, t in THEMES.items():
        print("  {:<10}  {}  -  {}".format(key, t["name"], t["desc"]))


class DashboardHandler(SimpleHTTPRequestHandler):
    """The converter's built-in local API for generated table/comment data."""
    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/api/health":
            return self._send_json({"ok": True, "version": APP_VERSION})
        match = re.fullmatch(r"/api/data/([^/]+)/(table|comments/(\d+))", path)
        if not match:
            return super().do_GET()
        dataset, resource, mid = urllib.parse.unquote(match.group(1)), match.group(2), match.group(3)
        parts = dataset.replace("\\", "/").split("/")
        if (not parts or parts[-1] != "data" or any(x in ("", ".", "..") for x in parts) or
                (mid is not None and not mid.isdigit())):
            return self.send_error(HTTPStatus.BAD_REQUEST, "非法数据请求")
        target = os.path.join(self.directory, dataset, "table_rows.html" if resource == "table" else os.path.join("comments", mid + ".json"))
        if os.path.commonpath([os.path.abspath(self.directory), os.path.abspath(target)]) != os.path.abspath(self.directory):
            return self.send_error(HTTPStatus.FORBIDDEN, "非法数据路径")
        if not os.path.isfile(target):
            return self.send_error(HTTPStatus.NOT_FOUND, "未找到看板数据")
        with open(target, "rb") as f:
            body = f.read()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8" if resource == "table" else "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve_dashboard(host, port, html_path, open_browser=True):
    root = os.path.dirname(os.path.abspath(__file__))
    handler = lambda *a, **kw: DashboardHandler(*a, directory=root, **kw)
    relative_url = urllib.parse.quote(os.path.relpath(html_path, root).replace(os.sep, "/"))
    url = "http://{}:{}/{}".format(host, port, relative_url)
    try:
        server = ThreadingHTTPServer((host, port), handler)
    except OSError as exc:
        if getattr(exc, "errno", None) == 48:
            print("\n检测到看板已经在运行，直接打开：\n  {}".format(url))
            if open_browser:
                webbrowser.open(url)
            return
        raise
    print("\n看板已打开：\n  {}\n\n保持此窗口运行；按 Ctrl+C 关闭看板。".format(url))
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n看板已关闭。")
    finally:
        server.server_close()

def main():
    import argparse
    parser = argparse.ArgumentParser(description="整合包 JSON 转 HTML 生成器（多主题版）")
    parser.add_argument("-i", "--input", default=None,
                        help="输入 JSONL 文件（默认: 多平台爬虫数据_v1.0.jsonl）")
    parser.add_argument("-o", "--output", default=os.path.join(GENERATED_DASHBOARD_DIR, OPEN_DASHBOARD_NAME),
                        help="输出 HTML 文件（默认 generated_dashboard/打开这个看板.html）")
    parser.add_argument("-t", "--theme", default="light",
                        choices=list(THEMES.keys()),
                        help="选择配色主题（默认: light）")
    parser.add_argument("--trend-history-file", default=TREND_HISTORY_FILE,
                        help="本地长期趋势历史文件（默认: trend_history.jsonl）")
    parser.add_argument("-l", "--list", action="store_true",
                        help="列出所有可用主题")
    parser.add_argument("--no-serve", action="store_true", help="仅生成，不启动看板")
    parser.add_argument("--port", type=int, default=8765, help="看板端口（默认 8765）")
    args = parser.parse_args()
    if args.list:
        list_themes()
        return
    theme = THEMES[args.theme]
    output_html = args.output
    print("=" * 55)
    print("  整合包 JSON 转 HTML 生成器 {}  [{}]".format(APP_VERSION, theme["name"]))
    print("=" * 55)
    input_file = args.input
    if not input_file:
        input_file = INPUT_FILE if os.path.exists(INPUT_FILE) else FALLBACK_INPUT_FILE
    if not os.path.exists(input_file):
        print("\n[错误] 找不到 JSON 文件：{}".format(input_file))
        print("  请先运行爬虫生成 '{}'，或使用 --input 指定 JSON。".format(INPUT_FILE))
        sys.exit(1)
    print("\n[1/3] 正在读取 {} ...".format(input_file))
    raw_rows, meta = read_json(input_file)
    if meta:
        meta_preview = ", ".join("{}={}".format(k, v) for k, v in list(meta.items())[:4])
        print("  元信息: {}".format(meta_preview))
    print("  JSON记录: {} 条".format(len(raw_rows)))
    print("\n[2/3] 正在解析数据 ...")
    data = process_data(raw_rows)
    trend_history_applied = apply_local_trend_history(data, args.trend_history_file)
    if trend_history_applied:
        print("  本地长期趋势: 已增强 {} 条记录（文件: {}）".format(trend_history_applied, args.trend_history_file))
    else:
        print("  本地长期趋势: 未发现可用历史，沿用当前抓取数据")
    # [V1.0 新增] 为应对异步并发抓取导致的乱序写入，在此进行强制后处理排序
    data.sort(key=lambda x: x.get("views_n", 0), reverse=True)
    print("  解析成功：{} 条记录（已按浏览量降序）".format(len(data)))
    if not data:
        print("[警告] 未解析到任何有效数据，请检查 JSON 是否包含 packs 或 results。")
        sys.exit(1)
    print("\n  首条记录预览：")
    print("    标题: {}".format(data[0]["title"]))
    print("    总浏览量: {}  -> data-order={}".format(data[0]["views_d"], data[0]["views_n"]))
    print("    分类: {}".format(data[0]["cat"]))
    pack_preview = data[0]["pack"][:5]
    print("    标签: {}{}".format(pack_preview, "..." if len(data[0]["pack"]) > 5 else ""))
    print("    红票: {} ({}%)  黑票: {} ({}%)".format(
        data[0]["rv_d"], data[0]["rp_d"], data[0]["bpv_d"], data[0]["bp_d"]))
    print("    走势天数: {}  7日:{} 30日:{} 60日:{}".format(
        data[0]["tc_d"], data[0]["t7_d"], data[0]["t30_d"], data[0]["t60_d"]))
    print("\n[3/3] 生成 [{}] -> {}".format(theme["name"], output_html))
    # 只生成一次完整页面；不同输出副本只替换各自的评论 API 地址。
    html_template, comment_data, rows_html = gen_pretty_html(data, args.theme, "__COMMENT_API_BASE__")
    output_dir = os.path.dirname(output_html) or "."
    os.makedirs(output_dir, exist_ok=True)
    stable_html = os.path.join(output_dir, OPEN_DASHBOARD_NAME)
    output_targets = []
    for target in (output_html, stable_html):
        target_abs = os.path.abspath(target)
        if target_abs not in [os.path.abspath(x) for x in output_targets]:
            output_targets.append(target)
    extra_outputs = [x for x in output_targets if os.path.abspath(x) != os.path.abspath(output_html)]
    sidecar_notes = []
    for target_html in output_targets:
        comment_dir = comment_data_dir_for_html(target_html)
        # 保留相对目录（版本归档也能通过同一个本地服务读到对应快照）。
        api_dataset_path = os.path.relpath(os.path.dirname(comment_dir), ".").replace(os.sep, "/")
        api_dataset = urllib.parse.quote(api_dataset_path, safe="")
        html_out = html_template.replace('"__COMMENT_API_BASE__"', '"/api/data/{}"'.format(api_dataset))
        with open(target_html, "w", encoding="utf-8") as f:
            f.write(html_out)
        written_dir, written_count = write_dashboard_sidecars(comment_data, rows_html, target_html)
        sidecar_notes.append((written_dir, written_count))
    print("  [OK] 看板完成（{:,} 字节，不含按需评论数据）".format(len(html_out)))
    print("  [OK] 评论已拆分：{} 个整合包 payload，首次打开评论时才由 API 读取".format(len(comment_data)))
    print("\n" + "=" * 55)
    print("  生成完毕！[{}] {}".format(theme["name"], theme["desc"]))
    print("  -> {}".format(output_html))
    for extra_html in extra_outputs:
        print("  -> {}".format(extra_html))
    print("=" * 55)
    if not args.no_serve:
        serve_dashboard("127.0.0.1", args.port, output_html)

if __name__ == "__main__":
    main()

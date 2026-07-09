#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多平台整合包 JSONL 转 HTML 看板生成器。"""
import re
import sys
import os
import json
import html as _html
from collections import Counter
from datetime import date

# ───────────────────────── 配置 ─────────────────────────

INPUT_FILE  = "多平台爬虫数据_v1.0.jsonl"

FALLBACK_INPUT_FILE = "MC百科整合包数据.json"

# The converter does not use browser cache or cookies. Browser state belongs to
# the crawler only, under ignored_local_files/browser_data.
TREND_HISTORY_DIR = "trend_history"

MCMOD_BASE  = "https://www.mcmod.cn/modpack/"

# ═══════════════════════ 工具函数 ═══════════════════════

def _s(val):
    if val is None:
        return ""
    return str(val).strip()

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

def load_local_trend_history(history_dir, platform, stable_id):
    if not history_dir or not stable_id:
        return []
    path = os.path.join(history_dir, platform, stable_id + ".jsonl")
    if not os.path.exists(path):
        return []
    points = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                points.append(obj)
    except OSError:
        return []
    return normalize_trend_points(points)

def apply_local_trend_history(data, history_dir=TREND_HISTORY_DIR):
    applied = 0
    for d in data:
        mid = _extract_mid(d.get("url", ""))
        if not mid:
            continue
        local_trend = load_local_trend_history(history_dir, "mcmod", mid)
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
        first_line = f.readline()
        if not first_line:
            return [], meta
        try:
            obj = json.loads(first_line)
            # 嗅探是否为多平台聚合 JSONL 格式
            if isinstance(obj, dict) and "source" in obj and "data" in obj:
                meta = {"type": "multi-platform", "version": "v1.0"}
                if obj["source"] == "mcmod":
                    rows.append(obj.get("normalized") or obj.get("data") or obj.get("raw") or {})
                for line in f:
                    if line.strip():
                        item = json.loads(line)
                        if item.get("source") == "mcmod":
                            rows.append(item.get("normalized") or item.get("data") or item.get("raw") or {})
                return rows, meta
        except json.JSONDecodeError:
            pass
    # 退回原版全局解析
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        rows = payload.get("packs") or payload.get("results") or []
        meta = payload.get("meta") or payload.get("list_meta") or {}
    else:
        rows = []
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
    meta = {}
    with open(path, "r", encoding="utf-8") as f:
        first_line = f.readline()
        if not first_line:
            return [], meta
        try:
            obj = json.loads(first_line)
            # 嗅探是否为多平台聚合 JSONL 格式
            if isinstance(obj, dict) and "source" in obj and "data" in obj:
                meta = {"type": "multi-platform", "version": "v1.0"}
                if obj["source"] == "mcmod":
                    rows.append(obj.get("normalized") or obj.get("data") or obj.get("raw") or {})
                for line in f:
                    if line.strip():
                        item = json.loads(line)
                        if item.get("source") == "mcmod":
                            rows.append(item.get("normalized") or item.get("data") or item.get("raw") or {})
                return rows, meta
        except json.JSONDecodeError:
            pass
    # 退回原版全局解析
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        rows = payload.get("packs") or payload.get("results") or []
        meta = payload.get("meta") or payload.get("list_meta") or {}
    else:
        rows = []
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
        comments_raw = comments_to_json_text(first_value(row, "评论详情", "comments"))
        data.append({
            "title": title, "url": url,
            "desc": desc_text, "comments_raw": comments_raw, "trend_arr": trend_arr,
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
    cats = set()
    for d in data:
        cats.update(d["cat"])
    return sorted(cats)

def build_packtag_options(data):
    c = Counter()
    for d in data:
        c.update(d["pack"])
    return sorted(c.items(), key=lambda x: (-x[1], x[0]))

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

def gen_row_pretty(d, idx=0):
    mid = _extract_mid(d.get("url", ""))
    L = []
    L.append('            <tr data-row="{}">'.format(idx))
    # 标题（链接，hover 触发预览卡片）
    L.append(
        '                <td class="td-title">'
        '<a href="{url}" target="_blank" class="modpack-link" data-url="{url}" data-mid="{mid}">{title}</a></td>'.format(
            url=esc_attr(d["url"]), mid=mid, title=esc(d["title"]))
    )
    # 总浏览量
    L.append('                <td class="td-num td-views" data-order="{}">{}</td>'.format(
        fmt_order(d["views_n"]), esc(d["views_d"])))
    # 指数评分
    L.append('                <td class="td-num td-score" data-order="{}">{}</td>'.format(
        fmt_order(d["score_n"]), esc(d["score_d"])))

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
        '                <td class="td-trend" data-lat="{lat_n}" data-max="{max_n}" data-avg="{avg_n}" data-days="{days_n}" data-order="{lat_n}" {trend_data_attrs}>'
        '<div class="trend-consolidated-cell" style="display: flex; flex-direction: column; gap: 2px;">'
        '<div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">'
        '<svg class="sparkline-svg" viewBox="0 0 100 24" width="48" height="12" style="opacity: 0.85;">'
        '<path d="{sparkline_closed}" fill="rgba(var(--primary-rgb), 0.1)"></path>'
        '<path d="{sparkline_path}" fill="none" stroke="var(--primary)" stroke-width="2" stroke-linecap="round"></path>'
        '</svg>'
        '<span class="trend-val-lat" title="最新指数" style="font-weight: 700; color: var(--primary-light);">最新: {lat_d}</span>'
        '</div>'
        '<div style="display: flex; justify-content: space-between; font-size: 0.72rem; color: var(--text-muted); gap: 4px;">'
        '<span class="trend-val-max" title="最高指数">高: {max_d}</span>'
        '<span class="trend-val-avg" title="平均指数">平: {avg_d}</span>'
        '<span class="trend-val-days" title="走势天数">{days_d}天</span>'
        '</div>'
        '</div></td>'
    ).format(
        lat_n=fmt_order(d["lat_n"]),
        max_n=fmt_order(d["max_n"]),
        avg_n=fmt_order(d["avg_n"]),
        days_n=fmt_order(d["tc_n"]),
        trend_data_attrs=trend_data_attrs,
        sparkline_closed=sparkline_closed,
        sparkline_path=sparkline_path,
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
    L.append('                <td class="td-num" data-order="{}">{}</td>'.format(
        fmt_order(d["rec_n"]), esc(d["rec_d"])))
    L.append('                <td class="td-num" data-order="{}">{}</td>'.format(
        fmt_order(d["fav_n"]), esc(d["fav_d"])))
    L.append('                <td class="td-num td-comment" data-order="{}" data-mid="{}">{}</td>'.format(
        fmt_order(d["com_n"]), mid, esc(d["com_d"])))
    # 分类标签
    search_cat = esc_attr(" ".join(d["cat"]))
    badges_cat = "".join(
        '<span class="tag-cat">{}</span>'.format(esc(t)) for t in d["cat"]
    )
    L.append('                <td data-search="{}"><div class="tag-wrap">{}</div></td>'.format(
        search_cat, badges_cat if badges_cat else '<span class="tag-empty">—</span>'))
    # 整合包标签
    search_pack = esc_attr(" ".join(d["pack"]))
    badges_pack = "".join(
        '<span class="tag-pack">{}</span>'.format(esc(t)) for t in d["pack"]
    )
    L.append('                <td data-search="{}"><div class="tag-wrap pack-container">{}</div></td>'.format(
        search_pack, badges_pack if badges_pack else '<span class="tag-empty">—</span>'))
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
        "name": "二次元",
        "desc": "烟熏紫褐 · 香槟玻璃",
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
        /* ════════ 主容器 ════════ */
        .main-wrap {{
            max-width: 2400px; margin: 0 auto;
            padding: 0 2rem 3rem;
        }}
        /* ════════ 筛选卡片 ════════ */
        .filter-card {{
            background: var(--glass-bg);
            backdrop-filter: blur(28px); -webkit-backdrop-filter: blur(28px);
            border: 1px solid var(--glass-border);
            border-radius: var(--radius);
            padding: 1.5rem; box-shadow: var(--shadow);
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
        .filter-col-btn {{ flex: 0 0 auto; }}
        .filter-label {{
            display: block; font-size: 0.78rem; font-weight: 700;
            color: var(--text-muted); margin-bottom: 0.4rem;
            text-transform: uppercase; letter-spacing: 0.6px;
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
        .td-title {{ min-width: 200px; }}
        .td-title .modpack-link {{
            color: var(--primary-light); text-decoration: none;
            font-weight: 600; transition: all 0.2s; cursor: pointer;
            display: inline-block; padding: 2px 0;
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
        .td-score {{ color: var(--success) !important; font-weight: 700; font-size: 0.92rem; }}
        .td-views {{ color: var(--secondary) !important; font-weight: 700; }}
        .td-max {{ color: var(--coral) !important; font-weight: 600; }}
        .td-latest {{ color: var(--primary-light) !important; font-weight: 600; }}
        .td-avg {{ color: var(--text) !important; font-weight: 500; }}
        .td-days {{ color: var(--text-muted) !important; font-weight: 500; font-size: 0.78rem; }}
        .td-up {{ color: var(--success) !important; font-weight: 700; }}
        .td-down {{ color: var(--danger) !important; font-weight: 700; }}
        .td-flat {{ color: var(--text-muted) !important; font-weight: 500; }}
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
        .pack-container {{ max-height: 350px; }}
        .tag-cat {{
            display: inline-block;
            background: linear-gradient(135deg, rgba(var(--primary-light-rgb),.15), rgba(var(--primary-rgb),.05));
            color: var(--primary-light);
            border: 1px solid rgba(var(--primary-rgb),.25);
            border-radius: 7px; padding: 2px 9px;
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
            display: inline-block;
            background: rgba(var(--secondary-rgb),.06);
            color: var(--text-secondary);
            border: 1px solid rgba(var(--secondary-rgb),.15);
            border-radius: 7px; padding: 2px 9px;
            font-size: 0.78rem; font-weight: 500; white-space: nowrap;
            cursor: pointer;
            transition: all .2s ease;
        }}
        .tag-pack:hover {{
            background: rgba(var(--secondary-rgb),.12);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(var(--secondary-rgb),.15);
        }}
        .tag-empty {{
            color: var(--text-muted); font-size: 0.78rem; opacity: 0.5;
        }}
        /* 按钮 */
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
            border-radius: 10px !important;
            background: var(--glass-bg-solid) !important;
            border-color: var(--glass-border) !important;
            color: var(--text) !important;
            min-height: 42px;
        }}
        .select2-container--bootstrap-5 .select2-selection--single .select2-selection__rendered {{
            line-height: 40px; color: var(--text) !important;
        }}
        .select2-container--bootstrap-5 .select2-results__option {{
            color: var(--text) !important;
        }}
        .select2-dropdown {{
            background: var(--glass-bg-solid) !important;
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border) !important;
        }}
        .select2-container--bootstrap-5 .select2-results__option--selected {{
            background: rgba(var(--primary-rgb),.1) !important;
        }}
        .select2-container--bootstrap-5 .select2-results__option--highlighted {{
            background: rgba(var(--primary-rgb),.2) !important; color: #fff !important;
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
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: 8px;
            color: var(--text);
            padding: 0.3rem 0.6rem; margin-left: 0.4rem;
        }}
        .dataTables_wrapper .dataTables_filter input:focus {{
            border-color: var(--primary-light);
            box-shadow: 0 0 0 .2rem rgba(var(--primary-light-rgb),.15);
            outline: none;
        }}
        .dataTables_wrapper .dataTables_filter input::placeholder {{ color: var(--text-muted); }}
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
        .pv-actions a, .pv-actions span {{
            display: inline-flex; align-items: center; justify-content: center;
            width: 28px; height: 28px; border-radius: 7px;
            background: rgba(255,255,255,.2); color: #fff;
            cursor: pointer; font-size: 0.85rem;
            transition: background 0.15s; text-decoration: none;
        }}
        .pv-actions a:hover, .pv-actions span:hover {{ background: rgba(255,255,255,.4); }}
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
            pointer-events: none;
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
        .trend-tooltip-title {{
            font-size: 0.9rem; font-weight: 700; color: var(--text);
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
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
            height: auto;
            max-height: min(720px, calc(100vh - 40px)); max-width: calc(100vw - 24px);
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
            display: flex; align-items: center; justify-content: space-between;
            background: linear-gradient(135deg, var(--primary-dark), var(--primary));
            padding: 0.6rem 1rem; color: #fff; font-size: 0.9rem; font-weight: 700;
        }}
        .comment-body {{
            padding: 0.8rem 1.2rem 0.8rem 0.8rem; /* 右边距稍微加大，给滚动条留出安全视觉空间 */
            overflow-y: auto; flex: 1; background: transparent;
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
            margin-bottom: 0.3rem; display: flex; gap: 0.5rem; align-items: center;
        }}
        .comment-floor-head .floor-num {{
            background: var(--primary); color: #fff; padding: 1px 7px; border-radius: 4px; font-size: 0.72rem; font-weight: 600;
        }}
        .comment-floor-text {{ font-size: 0.9rem; color: var(--text) !important; line-height: 1.6; font-weight: 500; }}
        .comment-reply {{
            margin-left: 1.2rem; padding: 0.5rem 0.8rem;
            background: rgba(var(--shadow-rgb), 0.04); border-left: 3px solid var(--primary-light);
            border-radius: 4px; margin-top: 0.4rem;
        }}
        .comment-reply-head {{ font-size: 0.78rem; color: var(--secondary); font-weight: 700; margin-bottom: 0.2rem; }}
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
        .comment-popup {{ width: clamp(620px, 58vw, 900px) !important; }}
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
        .pv-head-title {{
            color: var(--text) !important;
            font-size: 0.98rem !important;
            font-weight: 850 !important;
            letter-spacing: 0 !important;
            text-shadow: none !important;
        }}
        .pv-head-icon {{
            background: rgba(var(--primary-rgb), 0.11) !important;
            color: var(--primary-dark) !important;
            box-shadow: none !important;
        }}
        .pv-actions a, .pv-actions span {{
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
        :root[data-theme="light"] .pv-head-icon {{
            background: #e7f1ff !important;
            color: #0053b3 !important;
        }}
        :root[data-theme="light"] .pv-head-title {{
            color: #0b1220 !important;
        }}
        :root[data-theme="light"] .pv-title,
        :root[data-theme="light"] .comment-title {{
            color: #0b1220 !important;
            text-shadow: none !important;
        }}
        :root[data-theme="light"] .pv-actions a,
        :root[data-theme="light"] .pv-actions span {{
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
            <div class="theme-btn theme-btn-anime" data-theme="anime" title="二次元动漫"><span class="theme-dot" style="background: #8b5cf6;"></span>动漫</div>
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
<div class="notice-wrap">
    <div class="disclaimer-inner" style="margin-bottom:0.8rem;">
        <strong>📋 免责声明</strong><br>
        本页面仅为个人整理与学习交流用途，不涉及任何商业用途。排序、热度等数据均基于公开信息整理或统计，<strong>仅供参考，不代表任何作品或作者的实际质量评价，也不构成排名高低优劣的结论。</strong>如涉及版权、数据使用或其他权益问题，请联系我处理，我会第一时间修改或删除相关内容。本项目与<a href="https://www.mcmod.cn/" target="_blank">MC百科</a>（mcmod.cn）及相关作者无官方关联。
    </div>
    <div class="sort-hint-inner">
        <span style="font-size:1rem;">💡</span>悬停查看详情
        <span><b>排序提示：</b>点击任意表头可按该列排序，再次点击切换 ↑升序 / ↓降序；默认按「指数评分」降序。鼠标悬停整合包名称 0.6 秒弹出 <b>整合包介绍</b>，悬停走势相关数值可查看<b>近 60 天趋势图</b>，悬停评论数可查看<b>评论详情</b>。已启用分页以优化大量数据排序性能，可切换每页 25 / 50 / 100 / 200 条。</span>
    </div>
</div>
<div class="main-wrap">
    <div class="filter-card">
        <div class="filter-row">
            <div class="filter-col">
                <label class="filter-label">📌 分类标签</label>
                <select id="categoryFilter" class="form-select select2-basic">
                    <option value="">全部分类</option>
{cat_opts}
                </select>
            </div>
            <div class="filter-col">
                <label class="filter-label">🏷️ 整合包标签（含频次）</label>
                <select id="packTagFilter" class="form-select select2-basic">
                    <option value="">全部标签</option>
{pack_opts}
                </select>
            </div>
             <div class="filter-col">
                <label class="filter-label">📈 走势周期</label>
                <select id="trendFilter" class="form-select">
                    <option value="">全部</option>
                    <option value="7_in">7天内（刚出新包）</option>
                    <option value="7-14">7-14天（两周内成长包）</option>
                    <option value="14-30">14-30天（半月到满月稳定包）</option>
                    <option value="30_in">30天内（大集合）</option>
                    <option value="30-59">30-59天（成长中期包）</option>
                    <option value="60">至少60天（历史老包）</option>
                </select>
            </div>
            <div class="filter-col-btn">
                <button id="resetFilters" class="btn-reset">重置筛选</button>
            </div>
        </div>
    </div>
    <div class="table-card">
        <div class="table-responsive">
            <table id="modpackTable" class="table table-hover align-middle" style="width:100%">
                <thead>
                    <tr>
                        <th>整合包名称</th>
                        <th>总浏览量</th>
                        <th>指数评分</th>
                        <th class="header-consolidated" style="min-width:140px">
                            <div class="header-sort-switcher" data-col="3">
                                <span class="sort-option active" data-subkey="lat">最新</span>
                                <span class="sort-option" data-subkey="max">最高</span>
                                <span class="sort-option" data-subkey="avg">平均</span>
                                <span class="sort-option" data-subkey="days">天数</span>
                            </div>
                        </th>
                        <th class="header-consolidated" style="min-width:140px">
                            <div class="header-sort-switcher" data-col="4">
                                <span class="sort-option active" data-subkey="t7">7日</span>
                                <span class="sort-option" data-subkey="t30">30日</span>
                                <span class="sort-option" data-subkey="t60">60日</span>
                                <span class="sort-option" data-subkey="tall">总幅</span>
                            </div>
                        </th>
                        <th class="header-consolidated" style="min-width:140px">
                            <div class="header-sort-switcher" data-col="5">
                                <span class="sort-option active" data-subkey="rv">红票</span>
                                <span class="sort-option" data-subkey="rp">红占比</span>
                                <span class="sort-option" data-subkey="bv">黑票</span>
                                <span class="sort-option" data-subkey="bp">黑占比</span>
                            </div>
                        </th>
                        <th>推荐数</th>
                        <th>收藏数</th>
                        <th>评论数</th>
                        <th style="min-width:140px">分类标签</th>
                        <th style="min-width:220px">整合包标签</th>
                    </tr>
                </thead>
                <tbody>
{rows}
                </tbody>
            </table>
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
            <span id="pvClose" title="关闭 ✕">✕</span>
        </div>
    </div>
    <div class="pv-body" id="pvBody"></div>
    <div class="pv-tip" style="line-height:1.6;">
        📋 本页面仅作信息整理预览，不含图片及完整排版 · 详细内容请访问 <a href="https://www.mcmod.cn/" target="_blank" style="color:var(--primary-dark);font-weight:600;">MC百科 mcmod.cn</a> 原页面查看
    </div>
    <div class="mcmod-consent">
        <div class="mcmod-consent-panel">
            <div class="mcmod-consent-brand">MC百科</div>
            <div class="mcmod-consent-title">内容来自 mcmod.cn 公开页面</div>
            <div class="mcmod-consent-text">这里显示的是本地整理预览，可能不含完整排版、图片或最新修订。确认后继续查看介绍内容。</div>
            <button type="button" class="mcmod-consent-ok">知道了</button>
        </div>
    </div>
</div>
<!-- ─── 评论悬浮窗 ─── -->
<div id="commentPopup" class="comment-popup">
    <div class="comment-head">
        <span>💬 评论详情</span>
        <span id="commentCount"></span>
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
        📋 本页面仅作评论整理预览 · 完整上下文与最新内容请访问 <a href="https://www.mcmod.cn/" target="_blank" id="commentModpackLink">MC百科 mcmod.cn</a> 原页面查看
    </div>
    <div class="mcmod-consent">
        <div class="mcmod-consent-panel">
            <div class="mcmod-consent-brand">MC百科</div>
            <div class="mcmod-consent-title">评论来自 mcmod.cn 公开页面</div>
            <div class="mcmod-consent-text">评论仅作本地预览与检索辅助，完整上下文请以 MC百科原页面为准。确认后继续查看评论。</div>
            <button type="button" class="mcmod-consent-ok">知道了</button>
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
        width: '100%'
    }});
    /* ════════ DataTables 初始化（scrollY 固定表头 + 分页优化） ════════ */
    // 🌟 性能优化：将重量级的表格初始化推入下一个事件循环，让 Select2 优先完成重绘，彻底解除页面开启瞬间的 UI 卡死
    setTimeout(function() {{
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
            result.cat = String(data[17] || '').toLowerCase().indexOf(kw) !== -1 || String(data[18] || '').toLowerCase().indexOf(kw) !== -1;
            var mid = $(tr).find('a.modpack-link').data('mid');
            if (mid) {{
                result.desc = textHasKeyword(descData[mid], keyword);
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
        "search": {{
            "smart": false
        }},
        "order": [[2, "desc"]],       // 默认按「指数评分」降序
        "pageLength": 50,             // ★ 每页 50 条
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
            {{ "orderable": true,  "targets": [0,1,2,3,4,5,6,7,8] }},
            {{ "orderable": false, "targets": [9,10] }}
        ],
        "initComplete": function() {{
            var api = this.api();
            /* 将每页条数选择器移到右上角 */
            var $wrapper = $(this.api().table().container());
            var $length = $wrapper.find('.dataTables_length');
            var $filter = $wrapper.find('.dataTables_filter');
            var $info = $wrapper.find('.dataTables_info');
            var $paginate = $wrapper.find('.dataTables_paginate');
            /* 重新排列：搜索框 + 每页条数 → 一行，信息 + 分页 → 一行 */
            $length.css({{ 'display': 'inline-block', 'margin-right': '1rem' }});
            $filter.css({{ 'display': 'inline-block', 'float': 'right' }});
            $info.css({{ 'padding-top': '0.6rem', 'clear': 'both' }});
            $paginate.css({{ 'padding-top': '0.3rem', 'text-align': 'center' }});
            /* ★ 动态注入：全局搜索靶向选择器 */
            var scopeSelect = '<select id="searchScope" class="form-select form-select-sm d-inline-block w-auto me-2" style="background-color: var(--card-bg); color: var(--text-main); border: 1px solid var(--border-color); font-weight: 500;">' +
                              '<option value="all">🔍 穿透搜索 (全部内容)</option>' +
                              '<option value="title">📘 仅搜整合包名称</option>' +
                              '<option value="cat">🏷️ 仅搜分类与标签</option>' +
                              '<option value="desc">📖 仅搜百科长篇介绍</option>' +
                              '<option value="comment">💬 仅搜评论与讨论区</option>' +
                              '</select>';
            $filter.find('label').prepend(scopeSelect);
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
                        highlightCell($tr.children('td').eq(9), keyword);
                        highlightCell($tr.children('td').eq(10), keyword);
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
                if (colIdx < 0 || colIdx > 8) return;
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
                if ($opt.hasClass('active')) return;
                var $switcher = $opt.closest('.header-sort-switcher');
                $switcher.find('.sort-option').removeClass('active');
                $opt.addClass('active');
                var colIdx = parseInt($switcher.attr('data-col'));
                var subKey = $opt.attr('data-subkey');
                api.rows().every(function() {{
                    var cellNode = api.cell(this.index(), colIdx).node();
                    var $cell = $(cellNode);
                    var val = parseFloat($cell.attr('data-' + subKey)) || 0;
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
            /* ★ [v10.0] 点击单元格内标签筛选/取消 */
            $wrapper.on('click', '.tag-cat', function(e) {{
                e.stopPropagation();
                var val = $(this).text().trim();
                var currentVal = $('#categoryFilter').val();
                if (currentVal === val) {{
                    $('#categoryFilter').val("").trigger('change');
                }} else {{
                    if ($('#categoryFilter option[value="' + val.replace(/"/g,'\\"') + '"]').length === 0)
                        $('#categoryFilter').append('<option value="'+val+'">'+val+'</option>');
                    $('#categoryFilter').val(val).trigger('change');
                }}
            }});
            $wrapper.on('click', '.tag-pack', function(e) {{
                e.stopPropagation();
                var val = $(this).text().trim();
                var currentVal = $('#packTagFilter').val();
                if (currentVal === val) {{
                    $('#packTagFilter').val("").trigger('change');
                }} else {{
                    if ($('#packTagFilter option[value="' + val.replace(/"/g,'\\"') + '"]').length === 0)
                        $('#packTagFilter').append('<option value="'+val+'">'+val+'</option>');
                    $('#packTagFilter').val(val).trigger('change');
                }}
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
            var selectedTrend = $('#trendFilter').val();
            // 分类和标签筛选
            var rowCat  = $(table.cell(dataIndex, 9).node()).attr('data-search') || '';
            var rowPack = $(table.cell(dataIndex, 10).node()).attr('data-search') || '';
            if (selectedCat && !rowCat.split(' ').includes(selectedCat)) return false;
            if (selectedPack && !rowPack.split(' ').includes(selectedPack)) return false;
            // 💡 升级：直接从单元格的 data-days 属性中抓取纯数字，避开文本干扰
            var cellNode = table.cell(dataIndex, 3).node();
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
                    if (trendDays !== 60) return false;   // 正好60天：不等于60的历史老包隐藏
                }}
            }}
            return true;
        }}
    );
    $('#categoryFilter, #packTagFilter, #trendFilter').on('change', function() {{
        table.draw();
    }});
    // 表格重绘时，同步更新顶部的总条数统计
    table.on('draw', function() {{
        var info = table.page.info();
        $('#statTotal').text(info.recordsDisplay);
        /* ★ [v10.0] 高亮当前被激活筛选的标签 */
        var $wrap = $('#modpackTable_wrapper');
        $wrap.find('.tag-cat, .tag-pack').removeClass('active-tag');
        var activeCat = $('#categoryFilter').val();
        if (activeCat) {{
            $wrap.find('.tag-cat').filter(function() {{ return $(this).text().trim() === activeCat; }}).addClass('active-tag');
        }}
        var activePack = $('#packTagFilter').val();
        if (activePack) {{
            $wrap.find('.tag-pack').filter(function() {{ return $(this).text().trim() === activePack; }}).addClass('active-tag');
        }}
    }});
    // 一键重置所有筛选条件
    $('#resetFilters').on('click', function() {{
        $('#categoryFilter').val(null).trigger('change');
        $('#packTagFilter').val(null).trigger('change');
        $('#trendFilter').val('').trigger('change'); // 加上走势的重置
        table.search('').draw();
    }});
    /* ═══════ 整合包介绍预览 ═══════ */
    var descData = {desc_json};
    var commentData = {comment_json};
    var $popup = $('#pvPopup');
    var $pvTitle = $('#pvTitle');
    var $pvBody = $('#pvBody');
    var $pvOpen = $('#pvOpen');
    var $cpopup = $('#commentPopup');
    var $cBody = $('#commentBody');
    var $cCount = $('#commentCount');
    var hoverTimer = null;
    var commentHoverTimer = null;
    var HOVER_DELAY = 600;
    $(document).on('click', '.mcmod-consent-ok', function(e) {{
        e.preventDefault();
        e.stopPropagation();
        $(this).closest('.pv-popup, .comment-popup').removeClass('needs-consent');
    }});
    function showDescPopup($link) {{
        var url = $link.attr('href') || '#';
        var title = $link.text();
        var mid = $link.data('mid') || '';
        $pvTitle.text(title);
        $pvOpen.attr('href', url);
        var desc = descData[mid];
        if (desc) {{
            var $filterInput = $('#modpackTable_filter input');
            var keyword = $filterInput.length > 0 ? $filterInput.val().trim() : '';
            if (keyword && desc.toLowerCase().indexOf(keyword.toLowerCase()) !== -1) {{
                $pvBody.html('<div class="pv-para">' + highlightText(desc, keyword) + '</div>');
            }} else {{
                $pvBody.html(escHtml(desc));
            }}
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
            if (firstChar === '-' || firstChar === '*' || firstChar === '•' || /^\d+\.\s/.test(line)) {{
                isList = true;
                listContent = line.replace(/^[-*•\s]+|^\d+\.\s+/, '');
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
        var $filterInput = $('#modpackTable_filter input');
        var keyword = $filterInput.length > 0 ? $filterInput.val().trim() : '';
        var start = (page - 1) * cmtPerPage;
        var end = Math.min(start + cmtPerPage, comments.length);
        var html = '';
        for (var i = start; i < end; i++) {{
            var c = comments[i];
            var isActiveMatch = (cmtSearchMatchPointer >= 0 && i === cmtSearchMatches[cmtSearchMatchPointer]);
            html += '<div class="comment-floor' + (isActiveMatch ? ' matched-active' : '') + '" data-comment-index="' + i + '">';
            html += '<div class="comment-floor-head">';
            if (c.floor) {{
                html += '<span class="floor-num">#' + c.floor + '</span> ';
            }}
            html += highlightText(c.author || '', keyword) + '</div>';
            html += '<div class="comment-floor-text">' + highlightText(c.text || '', keyword) + '</div>';
            if (c.replies && c.replies.length > 0) {{
                c.replies.forEach(function(r) {{
                    html += '<div class="comment-reply">';
                    html += '<div class="comment-reply-head">' + highlightText(r.author || '', keyword) + '</div>';
                    html += '<div class="comment-reply-text">' + highlightText(r.text || '', keyword) + '</div>';
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
            $info.text('第 ' + page + ' / ' + cmtTotalPages + ' 页 · 共 ' + comments.length + ' 楼');
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
        var safeTop = 40;
        var safeBottom = 40;
        var maxHeight = Math.max(400, vh - safeTop - safeBottom);
        $cpopup.css({{
            height: 'auto',
            'max-height': maxHeight + 'px'
        }});
        $cBody.css('max-height', Math.max(260, maxHeight - 130) + 'px');
        var ph = $cpopup.outerHeight();
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
    // 【4. 弹窗主渲染逻辑】：渲染完数据并全部定位成功后，激活检测
    function showCommentPopup($cell) {{
        activeCommentCell = $cell;
        var mid = $cell.data('mid') || '';
        var floorCount = $cell.data('order') || 0;
        var cdata = commentData[mid];
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
        if (cdata && cdata.comments && cdata.comments.length > 0) {{
            var scrapedFloors = cdata.comments.length;
            // 诱饵数据清洗与非逆向计算：直接正向统计回复数
            var scrapedReplies = 0;
            cdata.comments.forEach(function(c) {{
                if (c.replies) scrapedReplies += c.replies.length;
            }});
            // 修正 pageCount 为 max(pageCount, 实际提取数)
            pageCount = Math.max(pageCount, scrapedFloors + scrapedReplies);
            var localTotalPages = Math.max(1, Math.ceil(scrapedFloors / cmtPerPage));
            var totalLabel = '';
            if (localTotalPages > 1) {{
                totalLabel = '共 ' + pageCount + ' 条（' + scrapedFloors + ' 楼 + ' + scrapedReplies + ' 楼中楼）';
            }} else if (pageCount > 0 && pageCount !== (scrapedFloors + scrapedReplies)) {{
                totalLabel = '共 ' + pageCount + ' 条 · 预览（' + scrapedFloors + ' 楼 + ' + scrapedReplies + ' 楼中楼）';
            }} else {{
                totalLabel = '预览（' + scrapedFloors + ' 楼 + ' + scrapedReplies + ' 楼中楼）';
            }}
            $cCount.text(totalLabel);
            cmtCurrentData = cdata;
            /* ★ 自动导航算页算法：打开弹窗时自动跳转到第一个包含搜索词的评论页，提供无缝定位体验 */
            var startPage = 1;
            var $filterInput = $('#modpackTable_filter input');
            var keyword = $filterInput.length > 0 ? $filterInput.val().trim().toLowerCase() : '';
            var url = $cell.closest('tr').find('a.modpack-link').attr('href') || 'https://www.mcmod.cn/';
            $('#commentModpackLink').attr('href', url);
            
            cmtSearchMatches = [];
            cmtSearchMatchPointer = -1;
            if (keyword && cdata.comments && cdata.comments.length > 0) {{
                for (var i = 0; i < cdata.comments.length; i++) {{
                    var c = cdata.comments[i];
                    var match = false;
                    if (c.author && c.author.toLowerCase().indexOf(keyword) !== -1) match = true;
                    if (c.text && c.text.toLowerCase().indexOf(keyword) !== -1) match = true;
                    if (c.replies && c.replies.length > 0) {{
                        for (var j = 0; j < c.replies.length; j++) {{
                            var r = c.replies[j];
                            if (r.author && r.author.toLowerCase().indexOf(keyword) !== -1) match = true;
                            if (r.text && r.text.toLowerCase().indexOf(keyword) !== -1) match = true;
                        }}
                    }}
                    if (match) {{
                        cmtSearchMatches.push(i);
                    }}
                }}
            }}
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
            $('#commentModpackLink').attr('href', url);
            $('#commentSearchNav').hide();
            $cCount.text('共 ' + pageCount + ' 条 · 暂无评论详情');
            $cBody.html('<div class="comment-empty-hint">暂无详细评论预览<br>该整合包共有 ' + pageCount + ' 条评论<br><a href="' + url + '" target="_blank">前往 MC百科 查看完整内容 →</a></div>');
            $('#commentPageBar').hide();
        }}
        $cpopup.addClass('show needs-consent');
        repositionCommentPopup();
        // ✨ 完美的咬合节点：弹窗加载和精准坐标偏置完成后，立刻调取判定
        checkCommentOverflow();
    }}
    function hideCommentPopup() {{
        $cpopup.removeClass('show needs-consent');
        activeCommentCell = null;
        cmtSearchMatches = [];
        cmtSearchMatchPointer = -1;
        // 清除锁定高度和定位样式，便于下次加载时重新计算
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
    // =====================================================================
    // ───── 迷你走势悬浮窗渲染系统 ─────
    var $trendTooltip = $('<div class="trend-tooltip" id="trendTooltip">' +
        '<div class="trend-tooltip-title" id="trendTooltipTitle"></div>' +
        '<div class="trend-tooltip-subtitle" id="trendTooltipSubtitle">近 60 天指数走势历史</div>' +
        '<div class="trend-tooltip-chart-container" id="trendTooltipChartContainer"></div>' +
        '<div class="trend-point-label" id="trendPointLabel"></div>' +
        '<div class="trend-tooltip-footer" id="trendTooltipFooter"></div>' +
        '</div>').appendTo('body');
    var trendHoverTimer = null;
    $(document).on('mouseenter', '.td-trend', function(e) {{
        clearTimeout(trendHoverTimer);
        var $cell = $(this);
        var title = $cell.data('title') || '';
        if ($trendTooltip.hasClass('show') && $trendTooltip.data('active-title') === title) {{
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
        var firstDate = dates[0] || '';
        var lastDate = dates[len - 1] || '';
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
        // 定位悬浮窗
        var rect = this.getBoundingClientRect();
        var tw = $trendTooltip.outerWidth();
        var th = $trendTooltip.outerHeight();
        var left = rect.left + rect.width / 2 - tw / 2;
        var top = rect.top - th - 10;
        if (top < 10) {{
            top = rect.bottom + 10;
        }}
        if (left < 10) left = 10;
        if (left + tw > window.innerWidth - 10) {{
            left = window.innerWidth - tw - 10;
        }}
        $trendTooltip.css({{
            left: left + 'px',
            top: top + 'px'
        }}).addClass('show').data('active-title', title).show();
    }});
    $(document).on('mouseleave', '.td-trend', function() {{
        clearTimeout(trendHoverTimer);
        trendHoverTimer = setTimeout(function() {{
            $('#trendPointLabel').hide();
            $('#trendGuideLine').css('visibility', 'hidden');
            $trendTooltip.removeClass('show').hide();
        }}, 520);
    }});
    $trendTooltip.on('mouseenter', function() {{
        clearTimeout(trendHoverTimer);
    }}).on('mouseleave', function() {{
        clearTimeout(trendHoverTimer);
        trendHoverTimer = setTimeout(function() {{
            $('#trendPointLabel').hide();
            $('#trendGuideLine').css('visibility', 'hidden');
            $trendTooltip.removeClass('show').hide();
        }}, 520);
    }});
    // ────── 悬浮窗智能自适应延迟关闭与滚轮管理系统 ──────
    // =====================================================================
    /* ── 1. 悬停整合包名称 → 显示介绍（带 300ms 延迟及淡入淡出锁死） ── */
    $(document).on('mouseenter', '.modpack-link', function() {{
        var $self = $(this);
        clearTimeout(hoverTimer);
        hoverTimer = setTimeout(function() {{
            showDescPopup($self);
            $('body').css({{ 'overflow': 'hidden', 'height': '100vh' }});
        }}, HOVER_DELAY);
    }});
    $(document).on('mouseleave', '.modpack-link', function() {{
        clearTimeout(hoverTimer);
        hoverTimer = setTimeout(function() {{
            hideDescPopup();
            $('body').css({{ 'overflow': '', 'height': '' }});
        }}, 300);
    }});
    $popup.on('mouseenter', function() {{
        clearTimeout(hoverTimer);
        $('body').css({{ 'overflow': 'hidden', 'height': '100vh' }});
    }}).on('mouseleave', function() {{
        clearTimeout(hoverTimer);
        hoverTimer = setTimeout(function() {{
            hideDescPopup();
            $('body').css({{ 'overflow': '', 'height': '' }});
        }}, 300);
    }});
    /* ── 2. 悬停评论数 → 显示评论详情（彻底消灭翻页闪退 + 背景锁死） ── */
    $(document).on('mouseenter', '.td-comment', function() {{
        var $self = $(this);
        clearTimeout(commentHoverTimer);
        commentHoverTimer = setTimeout(function() {{
            showCommentPopup($self);
            $('body').css({{ 'overflow': 'hidden', 'height': '100vh' }});
        }}, HOVER_DELAY);
    }});
    $(document).on('mouseleave', '.td-comment', function() {{
        clearTimeout(commentHoverTimer);
        commentHoverTimer = setTimeout(function() {{
            hideCommentPopup();
            $('body').css({{ 'overflow': '', 'height': '' }});
        }}, 900); // ★ 防秒退：从 300ms 拉长到 900ms 宽裕防抖
    }});
    $cpopup.on('mouseenter', function() {{
        clearTimeout(commentHoverTimer);
        $('body').css({{ 'overflow': 'hidden', 'height': '100vh' }});
    }}).on('mouseleave', function() {{
        clearTimeout(commentHoverTimer);
        commentHoverTimer = setTimeout(function() {{
            hideCommentPopup();
            $('body').css({{ 'overflow': '', 'height': '' }});
        }}, 900); // ★ 防秒退：从 300ms 拉长到 900ms 宽裕防抖
    }});
    /* ── 3. 关闭/Escape 恢复现场 ── */
    $('#pvClose').on('click', function() {{
        hideDescPopup();
        $('body').css({{ 'overflow': '', 'height': '' }});
    }});
    $(document).on('keydown', function(e) {{
        if (e.key === 'Escape') {{
            hideDescPopup();
            hideCommentPopup();
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
        }}, 300);
    }});
    }}, 10); // 结束延迟初始化
}});
</script>
</body>
</html>'''

def gen_pretty_html(data, theme_name="light"):
    # 直接从爬虫 JSON 行中构建介绍/评论预览数据
    _ill_re = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
    desc_data = {}
    comment_data = {}
    for d in data:
        mid = _extract_mid(d.get("url", ""))
        if not mid:
            continue
        # 介绍：直接从 JSON 的整合包介绍字段读取
        if d.get("desc") and len(d["desc"]) > 5:
            desc_data[mid] = _ill_re.sub('', d["desc"])
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
    comment_json_str = json.dumps(comment_data, ensure_ascii=False)
    cat_opts = "\n".join(
        '                    <option value="{}">{}</option>'.format(esc_attr(c), esc(c))
        for c in build_category_options(data)
    )
    pack_opts = "\n".join(
        '                    <option value="{}">{} ({})</option>'.format(esc_attr(tag), esc(tag), count)
        for tag, count in build_packtag_options(data)
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
        title=title, cat_opts=cat_opts, pack_opts=pack_opts, rows=rows_html,
        total=total, total_views=total_views_str, total_comments=total_comments_str,
        desc_json=desc_json_str, comment_json=comment_json_str,
        theme_warm=THEMES["warm"]["root"],
        theme_dark=THEMES["dark"]["root"],
        theme_light=THEMES["light"]["root"],
        theme_eye=THEMES["eye"]["root"],
        theme_pink=THEMES["pink"]["root"],
        theme_anime=THEMES["anime"]["root"],
        default_theme=theme_name,
    )

# ═══════════════════════ 主程序 ═══════════════════════

def list_themes():
    """列出所有可用主题"""
    print("可用主题：")
    for key, t in THEMES.items():
        print("  {:<10}  {}  -  {}".format(key, t["name"], t["desc"]))

def main():
    import argparse
    parser = argparse.ArgumentParser(description="整合包 JSON 转 HTML 生成器（多主题版）")
    parser.add_argument("-i", "--input", default=None,
                        help="输入 JSONL 文件（默认: 多平台爬虫数据_v1.0.jsonl）")
    parser.add_argument("-o", "--output", default="多平台聚合看板_V1.0.html",
                        help="输出 HTML 文件（默认: 多平台聚合看板_V1.0.html）")
    parser.add_argument("-t", "--theme", default="light",
                        choices=list(THEMES.keys()),
                        help="选择配色主题（默认: light）")
    parser.add_argument("--trend-history-dir", default=TREND_HISTORY_DIR,
                        help="本地长期趋势历史目录（默认: trend_history；不存在则自动跳过）")
    parser.add_argument("-l", "--list", action="store_true",
                        help="列出所有可用主题")
    args = parser.parse_args()
    if args.list:
        list_themes()
        return
    theme = THEMES[args.theme]
    output_html = args.output
    print("=" * 55)
    print("  整合包 JSON 转 HTML 生成器 v10.0  [{}]".format(theme["name"]))
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
    trend_history_applied = apply_local_trend_history(data, args.trend_history_dir)
    if trend_history_applied:
        print("  本地长期趋势: 已增强 {} 条记录（目录: {}）".format(trend_history_applied, args.trend_history_dir))
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
    html_out = gen_pretty_html(data, args.theme)
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_out)
    print("  [OK] 完成（{:,} 字节）".format(len(html_out)))
    print("\n" + "=" * 55)
    print("  生成完毕！[{}] {}".format(theme["name"], theme["desc"]))
    print("  -> {}".format(output_html))
    print("=" * 55)

if __name__ == "__main__":
    main()

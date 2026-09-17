"""
HTML Cell Renderer for MCMod Legacy Dashboard.
Renders c0 through c6 and Sparkline SVGs strictly in memory from structured DB data.
NEVER stored in canonical.db.
"""
from html import escape
from typing import List, Dict, Any, Tuple, Optional

def esc(s: Any) -> str:
    return escape(str(s or ""), quote=False)

def esc_attr(s: Any) -> str:
    return escape(str(s or ""), quote=True)

def compute_trend_stats(sorted_points: List[Tuple[str, float]]) -> Tuple[int, int, float, int, float, float, float, float]:
    """Calculates derived trend statistics from time series points (date, val)."""
    if not sorted_points:
        return 0, 0, 0.0, 0, 0.0, 0.0, 0.0, 0.0
    vals = [p[1] for p in sorted_points]
    n = len(vals)
    lat_n = int(vals[-1])
    max_n = int(max(vals))
    avg_n = round(sum(vals) / n, 1)
    days_n = n

    def growth(lookback: int) -> float:
        if n > lookback:
            base = vals[-1 - lookback]
            return round(((vals[-1] - base) / base) * 100, 1) if base > 0 else 0.0
        return 0.0

    t7_n = growth(7)
    t30_n = growth(30)
    t60_n = growth(60)
    tall_n = round(((vals[-1] - vals[0]) / vals[0]) * 100, 1) if vals[0] > 0 else 0.0
    return lat_n, max_n, avg_n, days_n, t7_n, t30_n, t60_n, tall_n

def generate_sparkline_svg(vals: List[float], width: int = 118, height: int = 34) -> str:
    """Generates compact SVG Sparkline trace."""
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

def build_c0(mid: str, full_title: str, title_cn: str, title_en: str, cover_url: str,
             mold_id: str, type_name: str, views_d: str, latest_ver: str = "", latest_date: str = "") -> str:
    title_en_display = title_en or "&nbsp;"
    if latest_ver:
        tip = f"最新版本: {latest_ver} ({latest_date})" if latest_date else f"最新版本: {latest_ver}"
        ver_badge_html = f'<a class="modpack-version-badge" href="https://www.mcmod.cn/modpack/version/{mid}.html" target="_blank" title="{esc_attr(tip)}">📜 {esc(latest_ver)} ↗</a>'
    else:
        ver_badge_html = f'<a class="modpack-version-badge" href="https://www.mcmod.cn/modpack/version/{mid}.html" target="_blank" title="查看整合包真实版本发布与更新日志">📜 更新日志 ↗</a>'

    return (
        f'<button type="button" class="fav-star" data-mid="{mid}" title="收藏用于对比" aria-label="收藏用于对比">★</button>'
        f'<button type="button" class="modpack-cover-thumb image-thumb" data-image-url="{esc_attr(cover_url)}" title="{esc_attr(full_title)} 封面（悬停 1 秒放大）" aria-label="查看整合包封面">'
        f'<img src="{esc_attr(cover_url)}" alt="{esc_attr(full_title)} 封面" loading="lazy"></button>'
        f'<a href="https://www.mcmod.cn/modpack/{mid}.html" target="_blank" class="modpack-link" data-url="https://www.mcmod.cn/modpack/{mid}.html" data-mid="{mid}" data-full-title="{esc_attr(full_title)}">'
        f'<span class="modpack-title-cn">{esc(title_cn)}</span><span class="modpack-title-en">{title_en_display}</span></a>'
        f'<div class="modpack-meta-row"><a class="modpack-type-badge" href="https://www.mcmod.cn/modpack.html?mold={mold_id}" target="_blank" title="打开 MC百科类型页">{esc(type_name)}</a>'
        f'<span class="modpack-views-badge" title="总浏览量">👁 {esc(views_d)}</span> {ver_badge_html}</div>'
    )

def build_c1(score_n: Optional[int], lat_n: int, max_n: int, avg_n: float, days_n: int, vals: Optional[List[float]] = None) -> str:
    svg_html = generate_sparkline_svg(vals) if vals and len(vals) >= 2 else ""
    hint = "点击看图" if svg_html else "MC百科"
    mid_row = f'{svg_html}<span class="trend-val-lat" title="最新指数" style="font-weight: 700; color: var(--primary-light);">最新: {lat_n}</span><span class="trend-open-hint">{hint}</span>'
    if score_n is not None and score_n > 0:
        score_badge = f'<div class="trend-score-badge" title="官方流行指数评分"><span>流行</span><b>{score_n}</b></div>'
    else:
        score_badge = '<div class="trend-score-badge unrated" title="官方暂无评分"><span>暂无评分</span></div>'
    return (
        f'<div class="trend-consolidated-cell">{score_badge}'
        f'<div class="trend-main-row">{mid_row}</div>'
        f'<div class="trend-meta-row"><span class="trend-val-max" title="最高指数">高: {max_n}</span><span class="trend-val-avg" title="平均指数">平: {avg_n}</span><span class="trend-val-days" title="走势天数">{days_n}天</span></div></div>'
    )

def build_c2(t7_n: float, t30_n: float, t60_n: float, tall_n: float) -> str:
    def fmt_item(label: str, val: float, title: str) -> str:
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

def build_c3(rv_n: int, rp_n: int, bv_n: int, bp_n: int) -> str:
    return (
        '<div class="votes-consolidated-cell" style="display: flex; flex-direction: column; gap: 4px; padding: 4px 0; font-size: 0.76rem;">'
        f'<div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;"><span style="font-weight: 700; color: var(--success); font-size: 0.82rem;">{rv_n + bv_n} 票</span>'
        f'<span style="font-size: 0.72rem; padding: 1px 5px; border-radius: 6px; background: rgba(16, 185, 129, 0.12); color: var(--success); font-weight: 600;">{rp_n}% 红</span></div>'
        f'<div class="vote-ratio-bar" style="width: 100%; height: 5px; border-radius: 3px; background: rgba(128,128,128,0.15); display: flex; overflow: hidden; margin: 2px 0;" title="红占比: {rp_n}% | 黑占比: {bp_n}%">'
        f'<div class="vote-ratio-red" style="height: 100%; width: {rp_n}%; background: var(--success);"></div><div class="vote-ratio-black" style="height: 100%; width: {bp_n}%; background: #6b7280;"></div></div>'
        f'<div style="display: flex; justify-content: space-between; font-size: 0.7rem; color: var(--text-muted);"><span>黑票: {bv_n}</span><span>占比: {bp_n}%</span></div></div>'
    )

def build_c4(rec_n: int, fav_n: int, com_n: int) -> str:
    return (
        f'<div class="engage-cell"><span><b>{rec_n}</b><em>推</em></span><span><b>{fav_n}</b><em>藏</em></span>'
        f'<span class="engage-comment-trigger" role="button" tabindex="0" title="点击评论格打开 / 再点关闭"><b>{com_n}</b><em>评</em><i class="comment-open-dot" aria-hidden="true">⌕</i></span></div>'
    )

def build_c5(cats: List[str]) -> str:
    cat_spans = "".join([
        f'<span class="tag-cat" data-tag="{esc_attr(c)}"><span class="tag-filter-name">{esc(c)}</span></span>'
        for c in cats if c
    ])
    return f'<div class="tag-wrap tag-combo-container"><div class="tag-group-block"><div class="tag-group-label tag-group-label-cat">整合包分类</div><div class="tag-group tag-group-cat">{cat_spans}</div></div></div>'

def build_c6(grouped_mods: List[Dict[str, Any]], total_mods_count: int, preview_limit: int = 8) -> str:
    if not grouped_mods or total_mods_count == 0:
        return '<div class="tag-wrap mod-container"><span class="tag-empty">—</span></div>'

    mod_summary_chips = []
    mod_sections = []
    preview_used = 0
    hidden_mod_count = 0

    for group_idx, group in enumerate(grouped_mods):
        g_name = group.get("name") or "未分类"
        g_url = group.get("url") or ""
        g_mods = group.get("mods") or []
        g_key = f"cat{group_idx}"

        links = []
        for m in g_mods:
            m_name = m.get("name") or m.get("title") or ""
            if not m_name:
                continue
            m_url = m.get("url") or (f"https://www.mcmod.cn/class/{m.get('class_id')}.html" if m.get("class_id") else "#")
            m_ver = m.get("version") or ""
            title_bits = [m_name]
            if m_ver:
                title_bits.append(f"版本: {m_ver}")
            if g_name:
                title_bits.append(f"分类: {g_name}")

            ver_html = f'<span class="tag-mod-version">{esc(m_ver)}</span>' if m_ver else ''
            if preview_used >= preview_limit:
                hidden_mod_count += 1
                continue
            preview_used += 1

            links.append(
                f'<span class="tag-mod" role="button" tabindex="0" title="{esc_attr(" · ".join(title_bits))}" data-mod="{esc_attr(m_name)}" data-mod-cat="{esc_attr(g_name)}" data-mod-url="{esc_attr(m_url)}">'
                f'<span class="tag-mod-name">{esc(m_name)}</span>{ver_html}'
                f'<a class="tag-mod-open" href="{esc_attr(m_url)}" target="_blank" title="打开 MC百科模组页">↗</a></span>'
            )

        cat_label = esc(g_name)
        if g_url:
            cat_head = f'<a class="mod-category-link" href="{esc_attr(g_url)}" target="_blank">{cat_label}</a>'
        else:
            cat_head = f'<span>{cat_label}</span>'

        mod_summary_chips.append(
            f'<button type="button" class="mod-summary-chip" data-mod-cat-key="{g_key}" title="跳到 {esc_attr(g_name)} 分类">{cat_label}<b>{len(g_mods)}</b></button>'
        )

        if links:
            mod_sections.append(
                f'<section class="mod-category-section" data-mod-cat-key="{g_key}"><div class="mod-category-head">{cat_head}<span>{len(g_mods)}</span></div><div class="mod-grid">{"".join(links)}</div></section>'
            )

    more_hint = f'<div class="tag-empty">折叠状态精选预览前 {preview_limit} 个模组；展开抽屉或点击分类可查看全部 {total_mods_count} 款收录模组。</div>' if hidden_mod_count > 0 else ''
    chips_html = "".join(mod_summary_chips)
    sections_html = "".join(mod_sections)

    return (
        '<div class="tag-wrap mod-container">'
        '<details class="mod-details">'
        f'<summary><span class="mod-summary-main">包含模组 <b>{total_mods_count}</b></span><span class="mod-summary-cats">{chips_html}</span></summary>'
        f'<div class="mod-details-body">{sections_html}{more_hint}<div class="mod-full-list" data-loaded="0"></div></div>'
        '</details></div>'
    )

/**
 * MCMod TypeScript Cell Renderers (Architecture V2 — Phase 3B).
 * Pure TypeScript functions rendering DOM strings from structured data.
 * ZERO server-side Python rendering.
 */
import { escHtml, escAttrJs, safeExternalHref } from '../../utils/html';
import { generateSparklineSvg } from './sparkline';
import type { McmodStructuredItem, McmodPreviewModItem } from './types';
import { recordRendererDebug } from '../../debug';
import { renderCoverImage } from '../../utils/coverImage';

export const MCMOD_COVER_FALLBACK = 'data:image/svg+xml;charset=utf-8,%3Csvg xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22 width%3D%22400%22 height%3D%22225%22 viewBox%3D%220 0 400 225%22%3E%3Crect width%3D%22400%22 height%3D%22225%22 fill%3D%22%231e293b%22%2F%3E%3Ctext x%3D%2250%25%22 y%3D%2250%25%22 dominant-baseline%3D%22middle%22 text-anchor%3D%22middle%22 fill%3D%22%2394a3b8%22 font-family%3D%22sans-serif%22 font-size%3D%2215%22%3E%F0%9F%93%A6 MC%E7%99%BE%E7%A7%91%20%E6%9A%82%E6%97%A0%E5%B0%81%E9%9D%A2%3C%2Ftext%3E%3C%2Fsvg%3E';

export function renderTitleCell(pack: McmodStructuredItem): string {
  if (typeof window !== 'undefined') {
    recordRendererDebug('mcmod');
  }
  const mid = String(pack.mid);
  const fullTitle = pack.title || `Modpack ${mid}`;
  const titleCn = pack.chineseName || fullTitle;
  const titleEnDisplay = pack.englishName ? escHtml(pack.englishName) : '&nbsp;';
  const coverUrl = pack.coverUrl || '';
  const typeName = pack.typeName || '原生整合';
  const moldId = pack.moldId || '1';

  const viewsN = pack.views || 0;
  const viewsD = viewsN >= 10000 ? `${(viewsN / 10000).toFixed(2)}万` : String(viewsN);

  const verBadgeHtml = `<a class="modpack-version-badge" href="https://www.mcmod.cn/modpack/version/${mid}.html" target="_blank" title="查看整合包真实版本发布与更新日志">📜 更新日志 ↗</a>`;

  let matchBadgeHtml = '';
  if (typeof window !== 'undefined') {
    const win = window as any;
    if (win.searchCoordinator && win.searchCoordinator.isFiltering('mcmod')) {
      const reasonLabel = win.searchCoordinator.getMatchReasonLabel(pack.mid, 'mcmod');
      if (reasonLabel) {
        matchBadgeHtml = `<div class="search-match-badge" title="匹配原因：${escAttrJs(reasonLabel)}"><span class="search-match-icon">🔎</span> ${escHtml(reasonLabel)}</div>`;
      }
    }
  }

  return (
    `<button type="button" class="fav-star" data-mid="${mid}" title="收藏用于对比" aria-label="收藏用于对比">★</button>` +
    `<button type="button" class="modpack-cover-thumb image-thumb" data-image-url="${escAttrJs(coverUrl)}" title="${escAttrJs(fullTitle)} 封面（悬停 1 秒放大）" aria-label="查看整合包封面">` +
    `<img src="${escAttrJs(coverUrl)}" alt="${escAttrJs(fullTitle)} 封面" loading="lazy"></button>` +
    `<a href="https://www.mcmod.cn/modpack/${mid}.html" target="_blank" class="modpack-link" data-url="https://www.mcmod.cn/modpack/${mid}.html" data-mid="${mid}" data-full-title="${escAttrJs(fullTitle)}">` +
    `<span class="modpack-title-cn">${escHtml(titleCn)}</span><span class="modpack-title-en">${titleEnDisplay}</span></a>` +
    matchBadgeHtml +
    `<div class="modpack-meta-row"><a class="modpack-type-badge" href="https://www.mcmod.cn/modpack.html?mold=${moldId}" target="_blank" title="打开 MC百科类型页">${escHtml(typeName)}</a>` +
    `<span class="modpack-views-badge" title="总浏览量">👁 ${escHtml(viewsD)}</span> ${verBadgeHtml}</div>`
  );
}

export function renderTrendCell(pack: McmodStructuredItem): string {
  const ts = pack.trendStats;
  const score = ts.score;
  const lat = ts.lat || 0;
  const max = ts.max || 0;
  const avg = ts.avg || 0;
  const days = ts.days || 0;

  const vals =
    (pack.trendStats?.history7d && pack.trendStats.history7d.length > 0)
      ? pack.trendStats.history7d
      : (pack.trendPoints || []).map((p) => p.viewsDelta);
  const svgHtml = generateSparklineSvg(vals);
  const hint = svgHtml ? '点击看图' : 'MC百科';

  const midRow = `${svgHtml}<span class="trend-val-lat" title="最新指数" style="font-weight: 700; color: var(--primary-light);">最新: ${lat}</span><span class="trend-open-hint">${hint}</span>`;
  const scoreBadge =
    (score != null && score > 0)
      ? `<div class="trend-score-badge" title="官方流行指数评分"><span>流行</span><b>${score}</b></div>`
      : `<div class="trend-score-badge unrated" title="官方暂无评分"><span>暂无评分</span></div>`;

  return (
    `<div class="trend-consolidated-cell">${scoreBadge}` +
    `<div class="trend-main-row">${midRow}</div>` +
    `<div class="trend-meta-row"><span class="trend-val-max" title="最高指数">高: ${max}</span><span class="trend-val-avg" title="平均指数">平: ${avg}</span><span class="trend-val-days" title="走势天数">${days}天</span></div></div>`
  );
}

export function renderGrowthCell(pack: McmodStructuredItem): string {
  const ts = pack.trendStats;
  function fmtItem(label: string, val: number, title: string): string {
    const cls = val > 0 ? 'td-up' : val < 0 ? 'td-down' : 'td-neutral';
    const sign = val > 0 ? '+' : '';
    return `<span class="growth-val-${label} ${cls}" title="${title}">${label}: ${sign}${val.toFixed(0)}%</span>`;
  }

  const i7 = fmtItem('7日', ts.t7 || 0, '7日涨幅');
  const i30 = fmtItem('30日', ts.t30 || 0, '30日涨幅');
  const i60 = fmtItem('60日', ts.t60 || 0, '60日涨幅');
  const iall = fmtItem('总幅', ts.tall || 0, '总涨幅');

  return (
    `<div class="growth-consolidated-cell" style="display: flex; flex-direction: column; gap: 2px; font-size: 0.76rem;">` +
    `<div style="display: flex; justify-content: space-between; gap: 8px;">${i7}${i30}</div>` +
    `<div style="display: flex; justify-content: space-between; gap: 8px;">${i60}${iall}</div></div>`
  );
}

export function renderVotesCell(pack: McmodStructuredItem): string {
  const v = pack.votes;
  const rv = v.redVotes || 0;
  const bv = v.blackVotes || 0;
  const tot = rv + bv;
  const rp = v.redPercent || 50;
  const bp = v.blackPercent || 50;

  return (
    `<div class="votes-consolidated-cell" style="display: flex; flex-direction: column; gap: 4px; padding: 4px 0; font-size: 0.76rem;">` +
    `<div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;"><span style="font-weight: 700; color: var(--success); font-size: 0.82rem;">${tot} 票</span>` +
    `<span style="font-size: 0.72rem; padding: 1px 5px; border-radius: 6px; background: rgba(16, 185, 129, 0.12); color: var(--success); font-weight: 600;">${rp}% 红</span></div>` +
    `<div class="vote-ratio-bar" style="width: 100%; height: 5px; border-radius: 3px; background: rgba(128,128,128,0.15); display: flex; overflow: hidden; margin: 2px 0;" title="红占比: ${rp}% | 黑占比: ${bp}%">` +
    `<div class="vote-ratio-red" style="height: 100%; width: ${rp}%; background: var(--success);"></div><div class="vote-ratio-black" style="height: 100%; width: ${bp}%; background: #6b7280;"></div></div>` +
    `<div style="display: flex; justify-content: space-between; font-size: 0.7rem; color: var(--text-muted);"><span>黑票: ${bv}</span><span>占比: ${bp}%</span></div></div>`
  );
}

export function renderEngageCell(pack: McmodStructuredItem): string {
  const rec = pack.recommendations || 0;
  const fav = pack.favorites || 0;
  const com = pack.commentsCount || 0;

  return (
    `<div class="engage-cell"><span><b>${rec}</b><em>推</em></span><span><b>${fav}</b><em>藏</em></span>` +
    `<span class="engage-comment-trigger comment-cell" role="button" tabindex="0" title="点击评论格打开 / 再点关闭"><b>${com}</b><em>评</em><i class="comment-open-dot" aria-hidden="true">⌕</i></span></div>`
  );
}

export function renderTagsCell(pack: McmodStructuredItem): string {
  const cats = pack.categories || [];
  const catSpans = cats
    .filter(Boolean)
    .map(
      (c) => `<span class="tag-cat" data-tag="${escAttrJs(c)}"><span class="tag-filter-name">${escHtml(c)}</span></span>`
    )
    .join('');

  return `<div class="tag-wrap tag-combo-container"><div class="tag-group-block"><div class="tag-group-label tag-group-label-cat">整合包分类</div><div class="tag-group tag-group-cat">${catSpans}</div></div></div>`;
}

export function renderModsCell(pack: McmodStructuredItem): string {
  const totalCount = pack.includedModsCount || 0;
  if (totalCount === 0) {
    return '<div class="tag-wrap mod-container"><span class="tag-empty">—</span></div>';
  }

  const modCategories = pack.modCategories || [];
  const previewMods = pack.previewMods || [];

  const modSummaryChips = modCategories.map(
    (c) =>
      `<button type="button" class="mod-summary-chip" data-mod-cat-key="${escAttrJs(c.categoryKey)}" title="跳到 ${escAttrJs(c.categoryName)} 分类">${escHtml(c.categoryName)}<b>${c.count}</b></button>`
  );

  // Group preview mods by categoryKey for the preview sections
  const groupSectionMap: Record<string, McmodPreviewModItem[]> = {};
  for (const m of previewMods) {
    const k = m.categoryKey || 'cat0';
    if (!groupSectionMap[k]) groupSectionMap[k] = [];
    groupSectionMap[k].push(m);
  }

  const modSections: string[] = [];
  for (const c of modCategories) {
    const modsInGroup = groupSectionMap[c.categoryKey];
    if (!modsInGroup || !modsInGroup.length) continue;

    const links = modsInGroup.map((m) => {
      const mName = m.name;
      const mUrl = m.url || '#';
      const mVer = m.version || '';
      const titleBits = [mName];
      if (mVer) titleBits.push(`版本: ${mVer}`);
      if (c.categoryName) titleBits.push(`分类: ${c.categoryName}`);
      const verHtml = mVer ? `<span class="tag-mod-version">${escHtml(mVer)}</span>` : '';

      return (
        `<span class="tag-mod" role="button" tabindex="0" title="${escAttrJs(titleBits.join(' · '))}" data-mod="${escAttrJs(mName)}" data-mod-cat="${escAttrJs(c.categoryName)}" data-mod-url="${escAttrJs(mUrl)}">` +
        `<span class="tag-mod-name">${escHtml(mName)}</span>${verHtml}` +
        `<a class="tag-mod-open" href="${safeExternalHref(mUrl)}" target="_blank" title="打开 MC百科模组页">↗</a></span>`
      );
    });

    const catLabel = escHtml(c.categoryName);
    const catHead = c.categoryUrl
      ? `<a class="mod-category-link" href="${safeExternalHref(c.categoryUrl)}" target="_blank">${catLabel}</a>`
      : `<span>${catLabel}</span>`;

    modSections.push(
      `<section class="mod-category-section" data-mod-cat-key="${escAttrJs(c.categoryKey)}"><div class="mod-category-head">${catHead}<span>${c.count}</span></div><div class="mod-grid">${links.join('')}</div></section>`
    );
  }

  const moreHint =
    totalCount > 8
      ? `<div class="tag-empty">折叠状态精选预览前 8 个模组；<button type="button" class="mod-open-drawer-btn" data-action="open-detail-from-mod" data-mid="${escAttrJs(String(pack.mid || ''))}">展开抽屉查看全部 ${totalCount} 款收录模组 ↗</button></div>`
      : '';

  return (
    '<div class="tag-wrap mod-container">' +
    '<details class="mod-details">' +
    `<summary><span class="mod-summary-main">包含模组 <b>${totalCount}</b></span><span class="mod-summary-cats">${modSummaryChips.join('')}</span></summary>` +
    `<div class="mod-details-body">${modSections.join('')}${moreHint}<div class="mod-full-list" data-loaded="0"></div></div>` +
    '</details></div>'
  );
}

export function renderEnvironmentBadge(pack: McmodStructuredItem): string {
  const claims = pack.environmentClaims || [];
  const server = claims.find((c) => c.side === 'server');
  if (!server) return '';
  if (server.status === 'supported' || server.status === 'required' || server.status === 'optional') {
    return `<span class="modpack-env-badge badge-server-supported" title="${escAttrJs(server.evidenceText || '有服务端运行线索')}">✔ 有服务端运行线索</span>`;
  }
  return '';
}

export function renderMcmodCard(p: McmodStructuredItem): string {
  if (typeof window !== 'undefined') {
    recordRendererDebug('mcmod');
  }
  const mid = String(p.mid || '');
  const fullTitle = p.title || `Modpack ${mid}`;
  const titleCn = p.chineseName || fullTitle;
  const titleEn = p.englishName && p.englishName !== p.chineseName ? p.englishName : '';
  const originalCover = p.coverUrl || '';
  const cover = renderCoverImage({
    url: originalCover,
    fallback: MCMOD_COVER_FALLBACK,
    alt: `${fullTitle}封面`,
    key: `mcmod:${mid}`,
    className: 'mcmod-card-cover-img',
  });
  const viewsN = p.views || 0;
  const viewsStr = viewsN >= 10000 ? `${(viewsN / 10000).toFixed(1)}万` : String(viewsN);
  const score = p.score || p.trendStats?.score || 0;
  const scoreStr = score > 0 ? `${score}★ 流行` : 'MC百科';
  const ver = (p.mcVersions && p.mcVersions[0]) || '';
  const modCount = p.includedModsCount || (p.previewMods ? p.previewMods.length : 0);
  const votes = p.votes || { redVotes: 0, blackVotes: 0, redPercent: 95 };
  const goodPct = votes.redPercent ?? (votes.redVotes > 0 ? Math.round(votes.redVotes / (votes.redVotes + (votes.blackVotes || 0)) * 100) : 95);
  const recN = p.recommendations || 0;
  const favN = p.favorites || 0;
  const comN = p.commentsCount || 0;
  const typeName = p.typeName || '魔改整合';

  let badgesHtml = '';
  if (p.has_server) {
    badgesHtml += '<span class="badge-env badge-env-server" title="含服务端/支持联机开服">🖳 服务端</span>';
  }
  badgesHtml += `<span class="mcmod-badge-type">${escHtml(typeName)}</span>`;
  if (modCount > 0) {
    badgesHtml += `<span class="mcmod-badge-mods js-open-version-modal" data-mid="${escAttrJs(mid)}" style="cursor:pointer;" title="点击查看版本与参数详情">🧩 ${modCount} 款模组</span>`;
  }
  badgesHtml += `<span class="mcmod-badge-score" title="红票 ${votes.redVotes} / 黑票 ${votes.blackVotes || 0}">👍 ${goodPct}% 好评</span>`;
  if (p.categories && Array.isArray(p.categories)) {
    p.categories.slice(0, 3).forEach((c) => {
      badgesHtml += `<span class="mcmod-badge-cat">${escHtml(c)}</span>`;
    });
  }

  const coverOverlay = `<div class="mcmod-card-overlay">
    <span class="mcmod-overlay-views">👁️ ${escHtml(viewsStr)}</span>
    <span class="mcmod-overlay-score">${escHtml(scoreStr)}</span>
  </div>`;
  const verBadge = ver ? `<span class="mcmod-card-ver-badge" title="Minecraft 版本">MC ${escHtml(ver)}</span>` : '';

  return `<div class="mcmod-pack-card platform-pack-card">
    <div class="cover-media cover-media-rich" data-cover-frame data-cover-state="${cover.state}">
      <button type="button" class="mcmod-card-cover-btn image-preview-trigger" data-action="open-image" data-image-url="${escAttrJs(cover.source)}" data-image-title="${escAttrJs(fullTitle)}封面" aria-label="查看${escAttrJs(fullTitle)}封面">
        ${cover.image}
        ${coverOverlay}
        ${verBadge}
      </button>
      ${cover.retryButton}
    </div>
    <div class="mcmod-card-body platform-card-body">
      <a href="https://www.mcmod.cn/modpack/${escAttrJs(mid)}.html" target="_blank" rel="noreferrer" class="mcmod-card-title platform-card-title modpack-link" data-mid="${escAttrJs(mid)}" data-full-title="${escAttrJs(fullTitle)}" title="${escAttrJs(fullTitle)}">
        <span class="mcmod-title-cn">${escHtml(titleCn)}</span>
        ${titleEn ? `<span class="mcmod-title-en">${escHtml(titleEn)}</span>` : ''}
      </a>
      <div class="mcmod-card-badges platform-card-tags">${badgesHtml}</div>
      <div class="mcmod-card-metrics-row platform-card-metrics">
        <span class="mcmod-metric-item" title="推荐数"><span class="metric-icon">👍</span> 推: <b>${recN}</b></span>
        <span class="metric-sep">·</span>
        <span class="mcmod-metric-item" title="收藏数"><span class="metric-icon">⭐</span> 藏: <b>${favN}</b></span>
        <span class="metric-sep">·</span>
        <button type="button" class="mcmod-metric-item mcmod-metric-btn" data-action="open-comment-preview" data-mid="${escAttrJs(mid)}" title="在网页内预览评论详情"><span class="metric-icon">💬</span> 评: <b>${comN}</b></button>
      </div>
      <div class="mcmod-card-foot platform-card-actions">
        <button type="button" class="mcmod-comment-link" data-action="open-in-app-window" data-url="https://www.mcmod.cn/modpack/${escAttrJs(mid)}.html" data-title="${escAttrJs(fullTitle)}">▣ 小窗浏览</button>
        <a class="modpack-diff-link" href="https://www.mcmod.cn/modpack/version/${escAttrJs(mid)}.html" target="_blank" rel="noreferrer" title="在 MC百科 查看真实版本发布与更新日志">📜 更新日志 ↗</a>
        <button type="button" class="mcmod-comment-link js-open-comments" data-mid="${escAttrJs(mid)}" data-action="open-comment-preview" title="在网页内预览此整合包的评论">💬 详情评论</button>
      </div>
    </div>
  </div>`;
}

/**
 * Bilibili Platform Card Renderers (Architecture V2 — Phase 3C).
 */
import type { BilibiliPack } from '../../types/legacy/bilibili';
import { escHtml, safeExternalHref } from '../../utils/html';
import { recordRendererDebug } from '../../debug';
import { renderCoverImage } from '../../utils/coverImage';

export const BILIBILI_COVER_FALLBACK = 'data:image/svg+xml;charset=utf-8,%3Csvg xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22 width%3D%22400%22 height%3D%22225%22 viewBox%3D%220 0 400 225%22%3E%3Crect width%3D%22400%22 height%3D%22225%22 fill%3D%22%23fff0f5%22%2F%3E%3Ctext x%3D%2250%25%22 y%3D%2250%25%22 dominant-baseline%3D%22middle%22 text-anchor%3D%22middle%22 fill%3D%22%23fb7299%22 font-family%3D%22sans-serif%22 font-size%3D%2214%22%3EB%E7%AB%99%20%E6%9A%82%E6%97%A0%E5%B0%81%E9%9D%A2%3C%2Ftext%3E%3C%2Fsvg%3E';

function biliCoverUrl(pic?: string): string {
  const url = pic ? pic.replace('http://', 'https://') : '';
  return !url || url.includes('@') ? url : url + '@480w_300h_1c.webp';
}

function formatStaticDescriptionTime(value: unknown): string {
  const raw = String(value || '').trim();
  // Only convert timestamps with an explicit timezone; source dates retain their meaning.
  if (!/^\d{4}-\d{2}-\d{2}[T ].*(?:Z|[+-]\d{2}:?\d{2})$/i.test(raw)) return raw;
  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) return raw;
  const parts = new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).formatToParts(date);
  const part = (type: Intl.DateTimeFormatPartTypes) => parts.find((item) => item.type === type)?.value || '';
  return part('year') + '-' + part('month') + '-' + part('day') + ' ' + part('hour') + ':' + part('minute') + ' 北京时间';
}

export interface BiliGroup {
  key: string;
  items: BilibiliPack[];
  allVersions: Set<string>;
  allLoaders: Set<string>;
  allCategories: Set<string>;
  allGroups: Set<string>;
  allLinks: Array<{ name?: string; url?: string; type?: string }>;
  totalViews: number;
  totalLikes: number;
  totalCoins: number;
  totalFavs: number;
  totalDanmaku: number;
  totalReply: number;
  totalShare: number;
  latestTimestamp: number;
  latestPubTime: string;
  pic?: string;
  pack_version?: string;
  desc_updated_at?: string;
  has_server?: boolean;
  has_group_version?: boolean;
  group_version_note?: string;
}

export interface BiliCardRenderOptions {
  staticMode?: boolean;
}

export function renderBiliGroupedCard(g: BiliGroup, options: BiliCardRenderOptions = {}): string {
  if (typeof window !== 'undefined') {
    recordRendererDebug('bilibili');
  }
  const latest = g.items[0];
  const isMulti = g.items.length > 1;
  const staticMode = options.staticMode === true;

  const vers = Array.from(g.allVersions);
  const loaders = Array.from(g.allLoaders);
  const cats = Array.from(g.allCategories);
  const groups = Array.from(g.allGroups);

  let tagsHtml = '';
  if (g.has_server || latest.has_server) {
    tagsHtml += '<span class="badge-env badge-env-server" title="有服务端运行线索">🖳 有服务端运行线索</span>';
  }
  if (g.pack_version || latest.pack_version) {
    const packVersion = String(g.pack_version || latest.pack_version).trim();
    const packVersionLabel = /^v?\d/i.test(packVersion) ? 'v' + packVersion.replace(/^v/i, '') : packVersion;
    tagsHtml += '<span class="bili-pack-ver-tag">📦 ' + escHtml(packVersionLabel) + '</span>';
  }
  const descriptionCheckedAt = latest.desc_checked_at || latest.source_html_checked_at;
  const descriptionRecordedAt = g.desc_updated_at || latest.desc_updated_at;
  if (descriptionCheckedAt || descriptionRecordedAt) {
    const descriptionTime = descriptionCheckedAt || descriptionRecordedAt;
    tagsHtml += '<span class="bili-desc-updated-tag" title="聚合记录的核查或记录时间，不代表UP主修改简介或发布新版本">' + (descriptionCheckedAt ? '简介核查: ' : '简介记录: ') + escHtml(formatStaticDescriptionTime(descriptionTime)) + '</span>';

  }
  if (vers.length) {
    tagsHtml += '<span class="bili-tag-mc" title="来自标题或简介的版本线索，未必是 Minecraft 版本">版本线索 ' + vers.slice(0, 2).map((v) => escHtml(v)).join(' / ') + '</span>';
    if (vers.length > 2) tagsHtml += '<details class="card-extra-tags"><summary>+' + (vers.length - 2) + ' 个版本</summary><div>' + vers.slice(2).map((v) => '<span>' + escHtml(v) + '</span>').join('') + '</div></details>';
  }
  loaders.forEach((l) => { tagsHtml += '<span class="bili-tag-loader">' + escHtml(l) + '</span>'; });
  cats.forEach((c) => { tagsHtml += '<span class="bili-tag-cat">' + escHtml(c) + '</span>'; });

  const viewsStr = g.totalViews > 10000 ? (g.totalViews / 10000).toFixed(1) + '万' : String(g.totalViews);
  const likesStr = g.totalLikes > 10000 ? (g.totalLikes / 10000).toFixed(1) + '万' : String(g.totalLikes);
  const coinsStr = g.totalCoins > 10000 ? (g.totalCoins / 10000).toFixed(1) + '万' : String(g.totalCoins);
  const favsStr = g.totalFavs > 10000 ? (g.totalFavs / 10000).toFixed(1) + '万' : String(g.totalFavs);
  const danmakuStr = g.totalDanmaku > 10000 ? (g.totalDanmaku / 10000).toFixed(1) + '万' : String(g.totalDanmaku);
  const replyStr = g.totalReply > 10000 ? (g.totalReply / 10000).toFixed(1) + '万' : String(g.totalReply);
  const shareStr = g.totalShare > 10000 ? (g.totalShare / 10000).toFixed(1) + '万' : String(g.totalShare || 0);

  const originalCover = biliCoverUrl(g.pic || latest.pic);
  const cover = renderCoverImage({ url: originalCover, fallback: BILIBILI_COVER_FALLBACK, alt: latest.title + '封面', key: 'bilibili:' + g.key, className: 'bili-card-img' });
  const coverImg = cover.source;

  let groupVerBannerHtml = '';
  if (g.has_group_version || latest.has_group_version) {
    const gNote = g.group_version_note || latest.group_version_note || 'UP主在简介/置顶评论提示最新版本仅在群内发布，可加入QQ群获取体验！';
    const qGroup = latest.qq_group || (groups.length > 0 ? groups[0] : '');
    groupVerBannerHtml = '<div class="bili-group-ver-banner">👥 <strong>' + (staticMode ? '群内发布线索' : '群内有最新版本') + '</strong>：' + escHtml(gNote) + (qGroup ? (' (Q群: <b>' + escHtml(qGroup) + '</b>)') : '') + '</div>';
  }

  let dlZoneHtml = '<div class="bili-dl-zone platform-card-actions">';
  const dlMap: Record<string, boolean> = {};
  if (!staticMode) g.allLinks.forEach((l) => {
    if (l && l.url && !dlMap[l.url]) {
      dlMap[l.url] = true;
      const panName = (l.name || l.type || '网盘下载').trim();
      const panClass = 'pan-btn-' + (panName.includes('百度') ? 'baidu' : (panName.includes('夸克') ? 'quark' : (panName.includes('蓝奏') ? 'lanzou' : (panName.includes('123') ? 'pan123' : 'other'))));
      dlZoneHtml += '<a href="' + safeExternalHref(l.url) + '" target="_blank" rel="noreferrer" class="bili-pan-btn ' + panClass + '">💾 ' + escHtml(panName) + ' ↗</a>';
    }
  });

  if (!staticMode && latest.extract_code) {
    dlZoneHtml += '<button type="button" class="bili-pan-btn pan-btn-code js-copy-btn" data-text="' + escHtml(latest.extract_code) + '" title="点击复制提取码">🔑 码: ' + escHtml(latest.extract_code) + '</button>';
  }

  groups.forEach((grp) => {
    dlZoneHtml += '<button type="button" class="bili-pan-btn pan-btn-group js-copy-btn" data-text="' + escHtml(grp) + '" title="点击复制群号">👥 群: ' + escHtml(grp) + '</button>';
  });

  const fullDesc = latest.desc || '';
  const pinned = latest.pinned_comment || '';
  if (fullDesc || pinned) {
    const combined = (fullDesc ? '【简介】\n' + fullDesc : '') + (pinned ? '\n\n【置顶评论】\n' + pinned : '');
    dlZoneHtml += '<details class="bili-desc-collapse"><summary class="bili-desc-summary">📄 ' + (staticMode ? '已收录简介与置顶评论' : '最新版本介绍与置顶评论') + '</summary><div class="bili-desc-full">' + escHtml(combined) + '</div></details>';
  }

  if (latest.subtitle_text || latest.subtitle_summary) {
    const subText = latest.subtitle_text || latest.subtitle_summary;
    dlZoneHtml += '<details class="bili-desc-collapse" style="margin-top:6px;"><summary class="bili-desc-summary" style="color:var(--primary); font-weight:700;">📝 ' + (staticMode ? '已收录字幕与摘要' : '视频字幕与口播速读 (AI/官方)') + '</summary><div class="bili-desc-full" style="max-height:160px; overflow-y:auto; line-height:1.6; font-size:12px;">' + escHtml(subText) + '</div></details>';
  }

  if (!staticMode) dlZoneHtml += '<button type="button" class="bili-pan-btn pan-btn-other js-open-bili-group-versions" data-group-key="' + g.key + '" style="font-size:0.75rem; background:color-mix(in srgb,var(--plat-bili) 12%,var(--bg-surface)); color:color-mix(in srgb,var(--plat-bili) 72%,var(--text-primary)); border-color:color-mix(in srgb,var(--plat-bili) 32%,transparent); margin-top:4px;" title="打开版本详情模态窗">📜 历史发布记录 (' + g.items.length + ') ▾</button>';
  dlZoneHtml += '</div>';

  let versionsHtml = '';
  if (isMulti) {
    versionsHtml += '<details class="bili-versions-collapse"><summary class="bili-versions-summary">📜 ' + (staticMode ? '查看 ' + g.items.length + ' 个关联视频' : '查看该整合包历史 ' + g.items.length + ' 个迭代版本与关联视频') + '</summary><div class="bili-versions-list">';
    g.items.forEach((item, idx) => {
      const itemViews = item.views > 10000 ? (item.views / 10000).toFixed(1) + '万' : String(item.views);
      const itemDanmaku = (item.danmaku || 0) > 10000 ? ((item.danmaku || 0) / 10000).toFixed(1) + '万' : String(item.danmaku || 0);
      const itemCoins = item.coins || 0;
      const isLatestBadge = idx === 0 ? '<span class="bili-ver-latest-badge">' + (staticMode ? '最新视频' : '最新发布') + '</span>' : '';
      versionsHtml += '<div class="bili-version-item">' +
        isLatestBadge +
        '<a href="' + safeExternalHref(item.url) + '" target="_blank" rel="noreferrer" class="bili-ver-title" title="' + escHtml(item.title) + '">' + escHtml(item.title) + '</a>' +
        '<div class="bili-ver-meta">' +
        '<span>UP: ' + escHtml(item.author) + '</span> · ' +
        '<span>' + escHtml(item.pub_time) + '</span> · ' +
        '<span>👁️ ' + itemViews + '</span> · ' +
        '<span>📺 ' + itemDanmaku + '</span> · ' +
        '<span>🪙 ' + itemCoins + '</span>' +
        '</div>' +
        '</div>';
    });
    versionsHtml += '</div></details>';
  }

  return '<div class="bili-pack-card platform-pack-card" data-key="' + g.key + '">' +
    '<div class="cover-media cover-media-rich" data-cover-frame data-cover-state="' + cover.state + '">' +
    '<a href="' + safeExternalHref(latest.url) + '" target="_blank" rel="noreferrer" class="bili-card-cover">' +
    cover.image + cover.status +
    (isMulti ? '<span class="bili-multi-badge">📦 ' + g.items.length + (staticMode ? ' 个关联视频' : ' 个关联版本') + '</span>' : '') +
    (latest.duration ? '<span class="bili-card-dur">' + escHtml(latest.duration) + '</span>' : '') +
    (staticMode ? '' : '<div class="bili-card-stats">' +
    '<span>👁️ ' + viewsStr + '</span>' +
    '<span>📺 ' + danmakuStr + '</span>' +
    '</div>') +
    '</a>' + cover.retryButton + '</div>' +
    '<div class="bili-card-body platform-card-body">' +
    '<a href="' + safeExternalHref(latest.url) + '" target="_blank" rel="noreferrer" class="bili-card-title platform-card-title js-open-unified-preview" data-platform="bilibili" data-full-title="' + escHtml(latest.title) + '" data-desc="' + escHtml(fullDesc || pinned || latest.title) + '" data-cover="' + coverImg + '" data-author="' + escHtml(latest.author) + '" data-ver="' + escHtml(vers.join(', ')) + '" data-date="' + escHtml(g.latestPubTime) + '" title="' + escHtml(latest.title) + '">' + escHtml(latest.title) + '</a>' +
    '<div class="bili-card-meta platform-card-meta">' +
    '<span>UP: <b class="bili-author-tag">' + escHtml(latest.author) + '</b></span>' +
    '<span>·</span>' +
    '<span>' + '视频发布: ' + escHtml(g.latestPubTime) + '</span>' +
    '</div>' +
    (tagsHtml ? '<div class="bili-card-tags platform-card-tags">' + tagsHtml + '</div>' : '<div class="platform-card-tags" aria-hidden="true"></div>') +
    groupVerBannerHtml +
    '<div class="bili-metrics-bar">' +
    '<span class="bmb-item" title="总播放量">👁️ <strong>' + viewsStr + '</strong></span>' +
    '<span class="bmb-item" title="总弹幕数">📺 <strong>' + danmakuStr + '</strong></span>' +
    '<span class="bmb-item" title="总点赞数">👍 <strong>' + likesStr + '</strong></span>' +
    '<span class="bmb-item" title="总投币数">🪙 <strong>' + coinsStr + '</strong></span>' +
    '<span class="bmb-item" title="总收藏数">⭐ <strong>' + favsStr + '</strong></span>' +
    '<button type="button" class="bmb-item bmb-comment-btn" data-action="open-comment-preview" data-platform="bilibili" data-source-id="' + escHtml(latest.bvid) + '" title="总评论数 / 点击预览评论区">💬 <strong>' + replyStr + '</strong></button>' +
    (staticMode ? '' : '<button type="button" class="bmb-item bmb-inapp-btn" data-action="open-in-app-window" data-url="' + escHtml(latest.url) + '" data-title="' + escHtml(latest.title) + ' 视频页面" title="软件内小窗浏览视频与讨论">🪟 小窗打开</button>') +
    '<span class="bmb-item" title="总分享数">🔁 <strong>' + shareStr + '</strong></span>' +
    '</div>' +
    '<details class="platform-card-disclosure"><summary>' + (staticMode ? '简介与关联视频' : '下载、简介与关联视频') + '（' + g.items.length + '）</summary>' + dlZoneHtml + versionsHtml + '</details>' +
    '</div>' +
    '</div>';
}

export function renderBiliFlatCard(p: BilibiliPack, options: BiliCardRenderOptions = {}): string {
  if (typeof window !== 'undefined') {
    recordRendererDebug('bilibili');
  }
  const staticMode = options.staticMode === true;
  let tagsHtml = '';
  if (p.has_server) {
    tagsHtml += '<span class="badge-env badge-env-server" title="有服务端运行线索">🖳 有服务端运行线索</span>';
  }
  if (p.pack_version) {
    const packVersion = String(p.pack_version).trim();
    const packVersionLabel = /^v?\d/i.test(packVersion) ? 'v' + packVersion.replace(/^v/i, '') : packVersion;
    tagsHtml += '<span class="bili-pack-ver-tag">📦 ' + escHtml(packVersionLabel) + '</span>';
  }
  const descriptionCheckedAt = p.desc_checked_at || p.source_html_checked_at;
  const descriptionRecordedAt = p.desc_updated_at;
  if (descriptionCheckedAt || descriptionRecordedAt) {
    const descriptionTime = descriptionCheckedAt || descriptionRecordedAt;
    tagsHtml += '<span class="bili-desc-updated-tag" title="聚合记录的核查或记录时间，不代表UP主修改简介或发布新版本">' + (descriptionCheckedAt ? '简介核查: ' : '简介记录: ') + escHtml(formatStaticDescriptionTime(descriptionTime)) + '</span>';

  }
  if (p.mc_version && p.mc_version !== '未知') tagsHtml += '<span class="bili-tag-mc" title="来自标题或简介的版本线索，未必是 Minecraft 版本">🔎 版本线索 ' + escHtml(p.mc_version) + '</span>';
  if (p.loaders && Array.isArray(p.loaders)) {
    p.loaders.forEach((l) => { tagsHtml += '<span class="bili-tag-loader">' + escHtml(l) + '</span>'; });
  }
  if (p.categories && Array.isArray(p.categories)) {
    p.categories.forEach((c) => { tagsHtml += '<span class="bili-tag-cat">' + escHtml(c) + '</span>'; });
  }

  const viewsStr = p.views > 10000 ? (p.views / 10000).toFixed(1) + '万' : String(p.views);
  const danmakuStr = (p.danmaku || 0) > 10000 ? ((p.danmaku || 0) / 10000).toFixed(1) + '万' : String(p.danmaku || 0);
  const likesStr = p.likes > 10000 ? (p.likes / 10000).toFixed(1) + '万' : String(p.likes);
  const coinsStr = p.coins > 10000 ? (p.coins / 10000).toFixed(1) + '万' : String(p.coins || 0);
  const favsStr = (p.favorites || 0) > 10000 ? ((p.favorites || 0) / 10000).toFixed(1) + '万' : String(p.favorites || 0);
  const replyStr = p.reply > 10000 ? (p.reply / 10000).toFixed(1) + '万' : String(p.reply || 0);
  const shareStr = (p.share || 0) > 10000 ? ((p.share || 0) / 10000).toFixed(1) + '万' : String(p.share || 0);

  const originalCover = biliCoverUrl(p.pic);
  const cover = renderCoverImage({ url: originalCover, fallback: BILIBILI_COVER_FALLBACK, alt: p.title + '封面', key: 'bilibili:' + String(p.bvid || p.id || p.url), className: 'bili-card-img' });

  let groupVerBannerHtml = '';
  if (p.has_group_version) {
    const gNote = p.group_version_note || 'UP主在简介/置顶评论提示最新版本仅在群内发布，可加入QQ群获取体验！';
    groupVerBannerHtml = '<div class="bili-group-ver-banner">👥 <strong>' + (staticMode ? '群内发布线索' : '群内有最新版本') + '</strong>：' + escHtml(gNote) + (p.qq_group ? (' (Q群: <b>' + escHtml(p.qq_group) + '</b>)') : '') + '</div>';
  }

  let dlZoneHtml = '<div class="bili-dl-zone platform-card-actions">';
  if (!staticMode && p.download_links && p.download_links.length > 0) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (p.download_links as any[]).forEach((l: any) => {
      if (l && l.url) {
        const panName = (l.name || l.type || '网盘下载').trim();
        const panClass = 'pan-btn-' + (panName.includes('百度') ? 'baidu' : (panName.includes('夸克') ? 'quark' : (panName.includes('蓝奏') ? 'lanzou' : (panName.includes('123') ? 'pan123' : 'other'))));
        dlZoneHtml += '<a href="' + safeExternalHref(l.url) + '" target="_blank" rel="noreferrer" class="bili-pan-btn ' + panClass + '">💾 ' + escHtml(panName) + ' ↗</a>';
      }
    });
  }
  if (!staticMode && p.extract_code) {
    dlZoneHtml += '<button type="button" class="bili-pan-btn pan-btn-code js-copy-btn" data-text="' + escHtml(p.extract_code) + '" title="点击复制提取码">🔑 码: ' + escHtml(p.extract_code) + '</button>';
  }
  if (p.qq_group) {
    dlZoneHtml += '<button type="button" class="bili-pan-btn pan-btn-group js-copy-btn" data-text="' + escHtml(p.qq_group) + '" title="点击复制群号">👥 群: ' + escHtml(p.qq_group) + '</button>';
  }

  const fullDesc = p.desc || '';
  const pinned = p.pinned_comment || '';
  if (fullDesc || pinned) {
    const combined = (fullDesc ? '【简介】\n' + fullDesc : '') + (pinned ? '\n\n【置顶评论】\n' + pinned : '');
    dlZoneHtml += '<details class="bili-desc-collapse"><summary class="bili-desc-summary">📄 详细介绍与置顶评论</summary><div class="bili-desc-full">' + escHtml(combined) + '</div></details>';
  }

  if (p.subtitle_text || p.subtitle_summary) {
    const subText = p.subtitle_text || p.subtitle_summary;
    dlZoneHtml += '<details class="bili-desc-collapse" style="margin-top:6px;"><summary class="bili-desc-summary" style="color:var(--primary); font-weight:700;">📝 ' + (staticMode ? '已收录字幕与摘要' : '视频字幕与口播速读 (AI/官方)') + '</summary><div class="bili-desc-full" style="max-height:160px; overflow-y:auto; line-height:1.6; font-size:12px;">' + escHtml(subText) + '</div></details>';
  }

  dlZoneHtml += '</div>';

  return '<div class="bili-pack-card platform-pack-card">' +
    '<div class="cover-media cover-media-rich" data-cover-frame data-cover-state="' + cover.state + '">' +
    '<a href="' + safeExternalHref(p.url) + '" target="_blank" rel="noreferrer" class="bili-card-cover">' +
    cover.image + cover.status +
    (p.duration ? '<span class="bili-card-dur">' + escHtml(p.duration) + '</span>' : '') +
    (staticMode ? '' : '<div class="bili-card-stats">' +
    '<span>👁️ ' + viewsStr + '</span>' +
    '<span>📺 ' + danmakuStr + '</span>' +
    '</div>') +
    '</a>' + cover.retryButton + '</div>' +
    '<div class="bili-card-body platform-card-body">' +
    '<a href="' + safeExternalHref(p.url) + '" target="_blank" rel="noreferrer" class="bili-card-title platform-card-title" title="' + escHtml(p.title) + '">' + escHtml(p.title) + '</a>' +
    '<div class="bili-card-meta platform-card-meta">' +
    '<span>UP: <b class="bili-author-tag">' + escHtml(p.author) + '</b></span>' +
    '<span>·</span>' +
    '<span>' + '视频发布: ' + escHtml(p.pub_time) + '</span>' +
    '</div>' +
    (tagsHtml ? '<div class="bili-card-tags platform-card-tags">' + tagsHtml + '</div>' : '<div class="platform-card-tags" aria-hidden="true"></div>') +
    groupVerBannerHtml +
    '<div class="bili-metrics-bar">' +
    '<span class="bmb-item" title="播放量">👁️ <strong>' + viewsStr + '</strong></span>' +
    '<span class="bmb-item" title="弹幕数">📺 <strong>' + danmakuStr + '</strong></span>' +
    '<span class="bmb-item" title="点赞数">👍 <strong>' + likesStr + '</strong></span>' +
    '<span class="bmb-item" title="投币数">🪙 <strong>' + coinsStr + '</strong></span>' +
    '<span class="bmb-item" title="收藏数">⭐ <strong>' + favsStr + '</strong></span>' +
    '<button type="button" class="bmb-item bmb-comment-btn" data-action="open-comment-preview" data-platform="bilibili" data-source-id="' + escHtml(p.bvid) + '" title="评论数 / 点击预览评论区">💬 <strong>' + replyStr + '</strong></button>' +
    (staticMode ? '' : '<button type="button" class="bmb-item bmb-inapp-btn" data-action="open-in-app-window" data-url="' + escHtml(p.url) + '" data-title="' + escHtml(p.title) + ' 视频页面" title="软件内小窗浏览视频与讨论">🪟 小窗打开</button>') +
    '<span class="bmb-item" title="分享数">🔁 <strong>' + shareStr + '</strong></span>' +
    '</div>' +
    '<details class="platform-card-disclosure"><summary>' + (staticMode ? '视频简介' : '下载与视频简介') + '</summary>' + dlZoneHtml + '</details>' +
    '</div>' +
    '</div>';
}

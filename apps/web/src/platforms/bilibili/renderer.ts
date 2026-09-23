/**
 * Bilibili Platform Card Renderers (Architecture V2 — Phase 3C).
 */
import type { BilibiliPack } from '../../types/legacy/bilibili';
import { escHtml } from '../../utils/html';
import { recordRendererDebug } from '../../debug';

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

export function renderBiliGroupedCard(g: BiliGroup): string {
  if (typeof window !== 'undefined') {
    recordRendererDebug('bilibili');
  }
  const latest = g.items[0];
  const isMulti = g.items.length > 1;

  const vers = Array.from(g.allVersions);
  const loaders = Array.from(g.allLoaders);
  const cats = Array.from(g.allCategories);
  const groups = Array.from(g.allGroups);

  let tagsHtml = '';
  if (g.has_server || latest.has_server) {
    tagsHtml += '<span class="badge-env badge-env-server" title="有服务端运行线索">🖳 有服务端运行线索</span>';
  }
  if (g.pack_version || latest.pack_version) {
    tagsHtml += '<span class="bili-pack-ver-tag">📦 v' + escHtml(g.pack_version || latest.pack_version) + '</span>';
  }
  if (g.desc_updated_at || latest.desc_updated_at) {
    tagsHtml += '<span class="bili-desc-updated-tag" title="UP主于简介或置顶评论更新版本：' + escHtml(g.desc_updated_at || latest.desc_updated_at) + '">🔄 简介更新: ' + escHtml(g.desc_updated_at || latest.desc_updated_at) + '</span>';
  }
  vers.forEach((v) => { tagsHtml += '<span class="bili-tag-mc">🎮 ' + escHtml(v) + '</span>'; });
  loaders.forEach((l) => { tagsHtml += '<span class="bili-tag-loader">' + escHtml(l) + '</span>'; });
  cats.forEach((c) => { tagsHtml += '<span class="bili-tag-cat">' + escHtml(c) + '</span>'; });

  const viewsStr = g.totalViews > 10000 ? (g.totalViews / 10000).toFixed(1) + '万' : String(g.totalViews);
  const likesStr = g.totalLikes > 10000 ? (g.totalLikes / 10000).toFixed(1) + '万' : String(g.totalLikes);
  const coinsStr = g.totalCoins > 10000 ? (g.totalCoins / 10000).toFixed(1) + '万' : String(g.totalCoins);
  const favsStr = g.totalFavs > 10000 ? (g.totalFavs / 10000).toFixed(1) + '万' : String(g.totalFavs);
  const danmakuStr = g.totalDanmaku > 10000 ? (g.totalDanmaku / 10000).toFixed(1) + '万' : String(g.totalDanmaku);
  const replyStr = g.totalReply > 10000 ? (g.totalReply / 10000).toFixed(1) + '万' : String(g.totalReply);
  const shareStr = g.totalShare > 10000 ? (g.totalShare / 10000).toFixed(1) + '万' : String(g.totalShare || 0);

  const coverImg = g.pic ? (g.pic.replace('http://', 'https://') + '@480w_300h_1c.webp') : '';

  let groupVerBannerHtml = '';
  if (g.has_group_version || latest.has_group_version) {
    const gNote = g.group_version_note || latest.group_version_note || 'UP主在简介/置顶评论提示最新版本仅在群内发布，可加入QQ群获取体验！';
    const qGroup = latest.qq_group || (groups.length > 0 ? groups[0] : '');
    groupVerBannerHtml = '<div class="bili-group-ver-banner">👥 <strong>群内有最新版本</strong>：' + escHtml(gNote) + (qGroup ? (' (Q群: <b>' + escHtml(qGroup) + '</b>)') : '') + '</div>';
  }

  let dlZoneHtml = '<div class="bili-dl-zone">';
  const dlMap: Record<string, boolean> = {};
  g.allLinks.forEach((l) => {
    if (l && l.url && !dlMap[l.url]) {
      dlMap[l.url] = true;
      const panName = (l.name || l.type || '网盘下载').trim();
      const panClass = 'pan-btn-' + (panName.includes('百度') ? 'baidu' : (panName.includes('夸克') ? 'quark' : (panName.includes('蓝奏') ? 'lanzou' : (panName.includes('123') ? 'pan123' : 'other'))));
      dlZoneHtml += '<a href="' + l.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn ' + panClass + '">💾 ' + escHtml(panName) + ' ↗</a>';
    }
  });

  if (latest.extract_code) {
    dlZoneHtml += '<button type="button" class="bili-pan-btn pan-btn-code js-copy-btn" data-text="' + escHtml(latest.extract_code) + '" title="点击复制提取码">🔑 码: ' + escHtml(latest.extract_code) + '</button>';
  }

  groups.forEach((grp) => {
    dlZoneHtml += '<button type="button" class="bili-pan-btn pan-btn-group js-copy-btn" data-text="' + escHtml(grp) + '" title="点击复制群号">👥 群: ' + escHtml(grp) + '</button>';
  });

  const fullDesc = latest.desc || '';
  const pinned = latest.pinned_comment || '';
  if (fullDesc || pinned) {
    const combined = (fullDesc ? '【简介】\n' + fullDesc : '') + (pinned ? '\n\n【置顶评论】\n' + pinned : '');
    dlZoneHtml += '<details class="bili-desc-collapse"><summary class="bili-desc-summary">📄 最新版本介绍与置顶评论</summary><div class="bili-desc-full">' + escHtml(combined) + '</div></details>';
  }

  if (latest.subtitle_text || latest.subtitle_summary) {
    const subText = latest.subtitle_text || latest.subtitle_summary;
    dlZoneHtml += '<details class="bili-desc-collapse" style="margin-top:6px;"><summary class="bili-desc-summary" style="color:var(--primary); font-weight:700;">📝 视频字幕与口播速读 (AI/官方)</summary><div class="bili-desc-full" style="max-height:160px; overflow-y:auto; line-height:1.6; font-size:12px;">' + escHtml(subText) + '</div></details>';
  }

  dlZoneHtml += '<button type="button" class="bili-pan-btn pan-btn-other js-open-bili-group-versions" data-group-key="' + g.key + '" style="font-size:0.75rem; background:color-mix(in srgb,var(--plat-bili) 12%,var(--bg-surface)); color:color-mix(in srgb,var(--plat-bili) 72%,var(--text-primary)); border-color:color-mix(in srgb,var(--plat-bili) 32%,transparent); margin-top:4px;" title="打开版本详情模态窗">📜 历史发布记录 (' + g.items.length + ') ▾</button>';
  dlZoneHtml += '</div>';

  let versionsHtml = '';
  if (isMulti) {
    versionsHtml += '<details class="bili-versions-collapse"><summary class="bili-versions-summary">📜 查看该整合包历史 ' + g.items.length + ' 个迭代版本与关联视频</summary><div class="bili-versions-list">';
    g.items.forEach((item, idx) => {
      const itemViews = item.views > 10000 ? (item.views / 10000).toFixed(1) + '万' : String(item.views);
      const itemDanmaku = (item.danmaku || 0) > 10000 ? ((item.danmaku || 0) / 10000).toFixed(1) + '万' : String(item.danmaku || 0);
      const itemCoins = item.coins || 0;
      const isLatestBadge = idx === 0 ? '<span class="bili-ver-latest-badge">最新发布</span>' : '';
      versionsHtml += '<div class="bili-version-item">' +
        isLatestBadge +
        '<a href="' + item.url + '" target="_blank" rel="noreferrer" class="bili-ver-title" title="' + escHtml(item.title) + '">' + escHtml(item.title) + '</a>' +
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

  return '<div class="bili-pack-card" data-key="' + g.key + '">' +
    '<a href="' + latest.url + '" target="_blank" rel="noreferrer" class="bili-card-cover">' +
    '<img class="bili-card-img" src="' + coverImg + '" alt="' + escHtml(latest.title) + '" loading="lazy" referrerpolicy="no-referrer">' +
    (isMulti ? '<span class="bili-multi-badge">📦 ' + g.items.length + ' 个关联版本</span>' : '') +
    (latest.duration ? '<span class="bili-card-dur">' + escHtml(latest.duration) + '</span>' : '') +
    '<div class="bili-card-stats">' +
    '<span>👁️ ' + viewsStr + '</span>' +
    '<span>📺 ' + danmakuStr + '</span>' +
    '</div>' +
    '</a>' +
    '<div class="bili-card-body">' +
    '<a href="' + latest.url + '" target="_blank" rel="noreferrer" class="bili-card-title js-open-unified-preview" data-platform="bilibili" data-full-title="' + escHtml(latest.title) + '" data-desc="' + escHtml(fullDesc || pinned || latest.title) + '" data-cover="' + coverImg + '" data-author="' + escHtml(latest.author) + '" data-ver="' + escHtml(vers.join(', ')) + '" data-date="' + escHtml(g.latestPubTime) + '" title="' + escHtml(latest.title) + '">' + escHtml(latest.title) + '</a>' +
    '<div class="bili-card-meta">' +
    '<span>UP: <b class="bili-author-tag">' + escHtml(latest.author) + '</b></span>' +
    '<span>·</span>' +
    '<span>最新: ' + escHtml(g.latestPubTime) + '</span>' +
    '</div>' +
    (tagsHtml ? '<div class="bili-card-tags">' + tagsHtml + '</div>' : '') +
    groupVerBannerHtml +
    '<div class="bili-metrics-bar">' +
    '<span class="bmb-item" title="总播放量">👁️ <strong>' + viewsStr + '</strong></span>' +
    '<span class="bmb-item" title="总弹幕数">📺 <strong>' + danmakuStr + '</strong></span>' +
    '<span class="bmb-item" title="总点赞数">👍 <strong>' + likesStr + '</strong></span>' +
    '<span class="bmb-item" title="总投币数">🪙 <strong>' + coinsStr + '</strong></span>' +
    '<span class="bmb-item" title="总收藏数">⭐ <strong>' + favsStr + '</strong></span>' +
    '<span class="bmb-item" title="总评论数">💬 <strong>' + replyStr + '</strong></span>' +
    '<span class="bmb-item" title="总分享数">🔁 <strong>' + shareStr + '</strong></span>' +
    '</div>' +
    dlZoneHtml +
    versionsHtml +
    '</div>' +
    '</div>';
}

export function renderBiliFlatCard(p: BilibiliPack): string {
  if (typeof window !== 'undefined') {
    recordRendererDebug('bilibili');
  }
  let tagsHtml = '';
  if (p.has_server) {
    tagsHtml += '<span class="badge-env badge-env-server" title="有服务端运行线索">🖳 有服务端运行线索</span>';
  }
  if (p.pack_version) {
    tagsHtml += '<span class="bili-pack-ver-tag">📦 v' + escHtml(p.pack_version) + '</span>';
  }
  if (p.desc_updated_at) {
    tagsHtml += '<span class="bili-desc-updated-tag" title="UP主于简介或置顶评论更新版本：' + escHtml(p.desc_updated_at) + '">🔄 简介更新: ' + escHtml(p.desc_updated_at) + '</span>';
  }
  if (p.mc_version && p.mc_version !== '未知') tagsHtml += '<span class="bili-tag-mc">🎮 ' + escHtml(p.mc_version) + '</span>';
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

  const coverImg = p.pic ? (p.pic.replace('http://', 'https://') + '@480w_300h_1c.webp') : '';

  let groupVerBannerHtml = '';
  if (p.has_group_version) {
    const gNote = p.group_version_note || 'UP主在简介/置顶评论提示最新版本仅在群内发布，可加入QQ群获取体验！';
    groupVerBannerHtml = '<div class="bili-group-ver-banner">👥 <strong>群内有最新版本</strong>：' + escHtml(gNote) + (p.qq_group ? (' (Q群: <b>' + escHtml(p.qq_group) + '</b>)') : '') + '</div>';
  }

  let dlZoneHtml = '<div class="bili-dl-zone">';
  if (p.download_links && p.download_links.length > 0) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (p.download_links as any[]).forEach((l: any) => {
      if (l && l.url) {
        const panName = (l.name || l.type || '网盘下载').trim();
        const panClass = 'pan-btn-' + (panName.includes('百度') ? 'baidu' : (panName.includes('夸克') ? 'quark' : (panName.includes('蓝奏') ? 'lanzou' : (panName.includes('123') ? 'pan123' : 'other'))));
        dlZoneHtml += '<a href="' + l.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn ' + panClass + '">💾 ' + escHtml(panName) + ' ↗</a>';
      }
    });
  }
  if (p.extract_code) {
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
    dlZoneHtml += '<details class="bili-desc-collapse" style="margin-top:6px;"><summary class="bili-desc-summary" style="color:var(--primary); font-weight:700;">📝 视频字幕与口播速读 (AI/官方)</summary><div class="bili-desc-full" style="max-height:160px; overflow-y:auto; line-height:1.6; font-size:12px;">' + escHtml(subText) + '</div></details>';
  }

  dlZoneHtml += '</div>';

  return '<div class="bili-pack-card">' +
    '<a href="' + p.url + '" target="_blank" rel="noreferrer" class="bili-card-cover">' +
    '<img class="bili-card-img" src="' + coverImg + '" alt="' + escHtml(p.title) + '" loading="lazy" referrerpolicy="no-referrer">' +
    (p.duration ? '<span class="bili-card-dur">' + escHtml(p.duration) + '</span>' : '') +
    '<div class="bili-card-stats">' +
    '<span>👁️ ' + viewsStr + '</span>' +
    '<span>📺 ' + danmakuStr + '</span>' +
    '</div>' +
    '</a>' +
    '<div class="bili-card-body">' +
    '<a href="' + p.url + '" target="_blank" rel="noreferrer" class="bili-card-title" title="' + escHtml(p.title) + '">' + escHtml(p.title) + '</a>' +
    '<div class="bili-card-meta">' +
    '<span>UP: <b class="bili-author-tag">' + escHtml(p.author) + '</b></span>' +
    '<span>·</span>' +
    '<span>' + escHtml(p.pub_time) + '</span>' +
    '</div>' +
    (tagsHtml ? '<div class="bili-card-tags">' + tagsHtml + '</div>' : '') +
    groupVerBannerHtml +
    '<div class="bili-metrics-bar">' +
    '<span class="bmb-item" title="播放量">👁️ <strong>' + viewsStr + '</strong></span>' +
    '<span class="bmb-item" title="弹幕数">📺 <strong>' + danmakuStr + '</strong></span>' +
    '<span class="bmb-item" title="点赞数">👍 <strong>' + likesStr + '</strong></span>' +
    '<span class="bmb-item" title="投币数">🪙 <strong>' + coinsStr + '</strong></span>' +
    '<span class="bmb-item" title="收藏数">⭐ <strong>' + favsStr + '</strong></span>' +
    '<span class="bmb-item" title="评论数">💬 <strong>' + replyStr + '</strong></span>' +
    '<span class="bmb-item" title="分享数">🔁 <strong>' + shareStr + '</strong></span>' +
    '</div>' +
    dlZoneHtml +
    '</div>' +
    '</div>';
}

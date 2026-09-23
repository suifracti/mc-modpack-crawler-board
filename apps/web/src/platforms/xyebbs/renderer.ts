/**
 * XYEBBS Platform Card Renderer (Architecture V2 — Phase 3C).
 */
import type { XyebbsPack } from '../../types/legacy/xyebbs';
import { escHtml } from '../../utils/html';
import { loaderLabel } from '../../domain/minecraft';
import { BBSMC_COVER_FALLBACK } from '../bbsmc/renderer';
import { recordRendererDebug } from '../../debug';
import { renderCoverImage } from '../../utils/coverImage';

export const XYEBBS_COVER_FALLBACK = BBSMC_COVER_FALLBACK;

export function renderXyebbsCard(p: XyebbsPack): string {
  if (typeof window !== 'undefined') {
    recordRendererDebug('xyebbs');
  }
  const safeTitle = escHtml(p.title || '');
  const safeAuthor = escHtml(p.author || '未知');
  const safeDesc = escHtml(p.description || '');
  const originalCover = p.head_url || p.icon_url || '';
  const cover = renderCoverImage({ url: originalCover, fallback: XYEBBS_COVER_FALLBACK, alt: (p.title || '') + '封面', key: 'xyebbs:' + String(p.url || p.project_id), className: 'xyebbs-card-img' });
  const coverImg = cover.source;
  const dlStr = (p.downloads || 0) > 10000 ? ((p.downloads || 0) / 10000).toFixed(1) + '万' : String(p.downloads || 0);
  const viewStr = (p.views || 0) > 10000 ? ((p.views || 0) / 10000).toFixed(1) + '万' : String(p.views || 0);

  let tagsHtml = '';
  if (p.has_server) {
    tagsHtml += '<span class="badge-env badge-env-server" title="有服务端运行线索">🖳 有服务端运行线索</span>';
  }
  if (p.mc_version && p.mc_version !== '未知') {
    tagsHtml += '<span class="xyebbs-badge-ver">🎮 ' + escHtml(p.mc_version) + '</span>';
  }
  if (p.loaders && Array.isArray(p.loaders)) {
    p.loaders.forEach((l) => { tagsHtml += '<span class="xyebbs-badge-loader">' + escHtml(loaderLabel(l)) + '</span>'; });
  }
  if (p.categories && Array.isArray(p.categories)) {
    p.categories.forEach((c) => { tagsHtml += '<span class="xyebbs-badge-cat">' + escHtml(c) + '</span>'; });
  }

  let dlZoneHtml = '<div class="xyebbs-download-zone">';
  const links = p.download_links || [];
  const seenUrls: Record<string, boolean> = {};
  const uniqueLinks: Array<{ name?: string; url: string; type?: string; code?: string }> = [];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  links.forEach((l: any) => {
    if (l && l.url && !seenUrls[l.url]) {
      seenUrls[l.url] = true;
      uniqueLinks.push(l as { name?: string; url: string; type?: string; code?: string });
    }
  });

  const visibleLinks = uniqueLinks.slice(0, 3);
  const hiddenLinks = uniqueLinks.slice(3);

  if (visibleLinks.length > 0) {
    dlZoneHtml += '<div class="card-dl-chips">';
    visibleLinks.forEach((l) => {
      const lName = (l.name || '直接下载').trim();
      const u = (l.url || '').toLowerCase();
      const t = ((l && l.type) || '').toLowerCase();
      let lClass = 'pan-btn-other';
      if (lName.includes('夸克') || u.includes('pan.quark.cn') || t === 'quark') {
        lClass = 'pan-btn-quark';
      } else if (lName.includes('百度') || u.includes('pan.baidu.com') || t === 'baidu') {
        lClass = 'pan-btn-baidu';
      } else if (lName.includes('123') || u.includes('123pan') || t.includes('123')) {
        lClass = 'pan-btn-pan123';
      } else if (lName.includes('迅雷') || u.includes('pan.xunlei.com') || t === 'xunlei') {
        lClass = 'pan-btn-xunlei';
      } else if (lName.includes('蓝奏') || u.includes('lanzou') || t.includes('lanzou')) {
        lClass = 'pan-btn-lanzou';
      }
      const codeStr = l.code ? (' 提取码: ' + l.code) : '';
      dlZoneHtml += '<a href="' + l.url + '" target="_blank" rel="noreferrer" class="card-dl-btn ' + lClass + '" title="' + escHtml(lName + codeStr, true) + '">💾 ' + escHtml(lName) + ' ↗</a>';
    });
    dlZoneHtml += '</div>';
  }

  if (hiddenLinks.length > 0) {
    dlZoneHtml += '<details class="card-more-details"><summary class="card-more-summary">展开更多网盘下载 (' + hiddenLinks.length + ') ▾</summary><div class="card-more-chips">';
    hiddenLinks.forEach((l) => {
      const lName = (l.name || '直接下载').trim();
      dlZoneHtml += '<a href="' + l.url + '" target="_blank" rel="noreferrer" class="card-dl-btn pan-btn-other" style="font-size:0.73rem;" title="' + escHtml(lName, true) + '">💾 ' + escHtml(lName) + ' ↗</a>';
    });
    dlZoneHtml += '</div></details>';
  }

  dlZoneHtml += '<div class="card-action-bar">' +
    '<button type="button" class="card-action-btn btn-vmodal js-open-plat-version-modal" data-platform="xyebbs" data-vkey="' + escHtml(p.url || '') + '" data-title="' + safeTitle + '" data-ver="' + escHtml(p.mc_version || '') + '" data-date="' + escHtml(p.created_date || '') + '" data-url="' + escHtml(p.url || '') + '" data-author="' + safeAuthor + '" data-downloads="' + dlStr + '">📜 完整版本与更新日志 ↗</button>' +
    '<a href="' + escHtml(p.url || '#') + '" target="_blank" rel="noreferrer" class="card-action-btn">🔗 原帖 ↗</a>' +
    '</div></div>';

  return '<div class="xyebbs-pack-card">' +
    '<div class="cover-media cover-media-rich" data-cover-frame data-cover-state="' + cover.state + '">' +
    '<a href="' + escHtml(p.url || '#') + '" target="_blank" rel="noreferrer" class="xyebbs-card-cover">' +
    cover.image + cover.status +
    '<div class="xyebbs-card-stats">' +
    '<span>📥 ' + dlStr + '</span>' +
    '<span>👁️ ' + viewStr + '</span>' +
    '</div>' +
    (p.mc_version ? '<span class="xyebbs-card-ver-badge">' + escHtml(p.mc_version) + '</span>' : '') +
    '</a>' + cover.retryButton + '</div>' +
    '<div class="xyebbs-card-body">' +
    '<a href="' + escHtml(p.url || '#') + '" target="_blank" rel="noreferrer" class="xyebbs-card-title js-open-unified-preview" data-platform="xyebbs" data-full-title="' + safeTitle + '" data-desc="' + safeDesc + '" data-cover="' + escHtml(coverImg) + '" data-author="' + safeAuthor + '" data-ver="' + escHtml(p.mc_version || '') + '" data-date="' + escHtml(p.created_date || '') + '" title="' + safeTitle + '">' + safeTitle + '</a>' +
    '<div class="xyebbs-card-meta">' +
    '<span>作者: <b class="xyebbs-author-tag">' + safeAuthor + '</b></span>' +
    (p.created_date ? '<span>· 发布: ' + escHtml(p.created_date.substring(0, 10)) + '</span>' : '') +
    '</div>' +
    (safeDesc ? '<div class="xyebbs-card-desc" title="' + safeDesc + '">' + safeDesc + '</div>' : '') +
    (tagsHtml ? '<div class="xyebbs-card-tags">' + tagsHtml + '</div>' : '') +
    dlZoneHtml +
    '</div>' +
    '</div>';
}

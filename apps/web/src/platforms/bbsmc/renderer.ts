/**
 * BBSMC Platform Card Renderer (Architecture V2 — Phase 3C).
 */
import type { BbsmcPack } from '../../types/legacy/bbsmc';
import { escHtml, safeExternalHref } from '../../utils/html';
import { loaderLabel } from '../../domain/minecraft';
import { recordRendererDebug } from '../../debug';
import { renderCoverImage } from '../../utils/coverImage';

export const BBSMC_COVER_FALLBACK = 'data:image/svg+xml;charset=utf-8,%3Csvg xmlns%3D"http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg" width%3D"400" height%3D"225" viewBox%3D"0 0 400 225"%3E%3Crect width%3D"400" height%3D"225" fill%3D"%231e293b"%2F%3E%3Ctext x%3D"50%25" y%3D"50%25" dominant-baseline%3D"middle" text-anchor%3D"middle" fill%3D"%23475569" font-family%3D"sans-serif" font-size%3D"14"%3EBBSMC 暂无封面%3C%2Ftext%3E%3C%2Fsvg%3E';

export function cleanVerChipTag(ver: unknown, packTitle?: string): string {
  if (!ver) return '';
  const v = String(ver).trim();
  if (!v) return '';
  if (packTitle) {
    const pt = String(packTitle).trim().toLowerCase();
    if (v.toLowerCase() === pt || pt.includes(v.toLowerCase()) || v.toLowerCase().includes(pt)) {
      return '';
    }
  }
  if (/^[0-9]/.test(v)) return 'v' + v + ' · ';
  if (/^v[0-9]/i.test(v)) return 'v' + v.replace(/^v/i, '') + ' · ';
  if (v.length <= 16 && !/[：:]/.test(v)) return v + ' · ';
  return '';
}

export function renderBbsmcCard(p: BbsmcPack): string {
  if (typeof window !== 'undefined') {
    recordRendererDebug('bbsmc');
  }
  const safeTitle = escHtml(p.title || '');
  const safeAuthor = escHtml(p.author || '未知');
  const safeDesc = escHtml(p.description || '');
  const originalCover = p.featured_gallery || (p.gallery && p.gallery[0]) || p.icon_url || '';
  const cover = renderCoverImage({ url: originalCover, fallback: BBSMC_COVER_FALLBACK, alt: safeTitle + '封面', key: 'bbsmc:' + String(p.url || p.project_id), className: 'bbsmc-card-img' });
  const coverImg = cover.source;
  const dlStr = (p.downloads || 0) > 10000 ? ((p.downloads || 0) / 10000).toFixed(1) + '万' : String(p.downloads || 0);
  const flStr = (p.followers || 0) > 10000 ? ((p.followers || 0) / 10000).toFixed(1) + '万' : String(p.followers || 0);

  let tagsHtml = '';
  if (p.has_server) {
    tagsHtml += '<span class="badge-env badge-env-server" title="有服务端运行线索">🖳 有服务端运行线索</span>';
  }
  if (p.loaders && Array.isArray(p.loaders)) {
    p.loaders.forEach((l) => { tagsHtml += '<span class="bbsmc-badge-loader">' + escHtml(loaderLabel(l)) + '</span>'; });
  }
  if (p.categories && Array.isArray(p.categories)) {
    p.categories.forEach((c) => { tagsHtml += '<span class="bbsmc-badge-cat">' + escHtml(c) + '</span>'; });
  }

  let galleryHtml = '';
  if (p.gallery && p.gallery.length > 0) {
    galleryHtml += '<div class="bbsmc-gallery-strip">';
    const limitG = Math.min(p.gallery.length, 6);
    for (let gi = 0; gi < limitG; gi++) {
      const gUrl = p.gallery[gi];
      galleryHtml += '<img src="' + escHtml(gUrl) + '" class="bbsmc-gallery-thumb js-bbsmc-lightbox-thumb" data-full="' + escHtml(gUrl) + '" data-title="' + safeTitle + ' 实机截图" alt="截图" loading="lazy" referrerpolicy="no-referrer">';
    }
    galleryHtml += '</div>';
  }

  let dlZoneHtml = '<div class="bbsmc-download-zone platform-card-actions">';
  const links = p.download_links || [];
  const seenUrls: Record<string, boolean> = {};
  const uniqueLinks: Array<{ name?: string; url: string; version?: string }> = [];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  links.forEach((l: any) => {
    if (l && l.url && !seenUrls[l.url]) {
      seenUrls[l.url] = true;
      uniqueLinks.push(l as { name?: string; url: string; version?: string });
    }
  });

  const visibleLinks = uniqueLinks.slice(0, 3);
  const hiddenLinks = uniqueLinks.slice(3);

  if (visibleLinks.length > 0) {
    dlZoneHtml += '<div class="card-dl-chips">';
    visibleLinks.forEach((l) => {
      const lName = (l.name || '直接下载').trim();
      const u = l.url.toLowerCase();
      let lClass = 'pan-btn-other';
      if (lName.includes('modrinth') || u.includes('.mrpack') || u.includes('cdn.bbsmc.net')) {
        lClass = 'pan-btn-modrinth';
      } else if (u.includes('curseforge.com')) {
        lClass = 'pan-btn-curseforge';
      } else if (lName.includes('夸克') || u.includes('pan.quark.cn')) {
        lClass = 'pan-btn-quark';
      } else if (lName.includes('百度') || u.includes('pan.baidu.com')) {
        lClass = 'pan-btn-baidu';
      } else if (lName.includes('123') || u.includes('123pan')) {
        lClass = 'pan-btn-pan123';
      } else if (lName.includes('迅雷') || u.includes('pan.xunlei.com')) {
        lClass = 'pan-btn-xunlei';
      }
      const vTag = cleanVerChipTag(l.version, p.title);
      const displayLabel = '💾 ' + vTag + lName + ' ↗';
      dlZoneHtml += '<a href="' + safeExternalHref(l.url) + '" target="_blank" rel="noreferrer" class="card-dl-btn ' + lClass + '" title="' + escHtml(lName + (l.version ? (' (' + l.version + ')') : ''), true) + '">' + escHtml(displayLabel) + '</a>';
    });
    dlZoneHtml += '</div>';
  }

  if (hiddenLinks.length > 0) {
    dlZoneHtml += '<details class="card-more-details"><summary class="card-more-summary">展开更多历史下载 (' + hiddenLinks.length + ') ▾</summary><div class="card-more-chips">';
    hiddenLinks.forEach((l) => {
      const lName = (l.name || '直接下载').trim();
      const vTag = cleanVerChipTag(l.version, p.title);
      const displayLabel = '💾 ' + vTag + lName + ' ↗';
      dlZoneHtml += '<a href="' + safeExternalHref(l.url) + '" target="_blank" rel="noreferrer" class="card-dl-btn pan-btn-other" style="font-size:0.73rem;" title="' + escHtml(lName, true) + '">' + escHtml(displayLabel) + '</a>';
    });
    dlZoneHtml += '</div></details>';
  }

  dlZoneHtml += '<div class="card-action-bar">' +
    '<button type="button" class="card-action-btn btn-vmodal js-open-plat-version-modal" data-platform="bbsmc" data-vkey="' + escHtml(p.url || '') + '" data-title="' + safeTitle + '" data-ver="' + escHtml(p.mc_version || '') + '" data-date="' + escHtml(p.date_modified || '') + '" data-url="' + escHtml(p.url || '') + '" data-author="' + safeAuthor + '" data-downloads="' + dlStr + '">📜 完整版本与更新日志 ↗</button>' +
    (p.url ? '<button type="button" class="card-action-btn btn-inapp-win" data-action="open-in-app-window" data-url="' + escHtml(p.url) + '" data-title="' + safeTitle + ' 原站页面" title="软件内小窗直接浏览">🪟 小窗浏览</button>' : '') +
    '<a href="' + safeExternalHref(p.url) + '" target="_blank" rel="noreferrer" class="card-action-btn">🔗 原站 ↗</a>' +
    '</div></div>';

  return '<div class="bbsmc-pack-card platform-pack-card">' +
    '<div class="cover-media cover-media-rich" data-cover-frame data-cover-state="' + cover.state + '">' +
    '<a href="' + safeExternalHref(p.url) + '" target="_blank" rel="noreferrer" class="bbsmc-card-cover">' +
    cover.image + cover.status + '</a>' +
    '<div class="bbsmc-card-stats">' +
    '<span>📥 ' + dlStr + '</span>' +
    '<span>⭐ ' + flStr + '</span>' +
    (p.url ? '<button type="button" class="bbsmc-stat-btn bbsmc-comment-btn" data-action="open-comment-preview" data-platform="bbsmc" data-source-id="' + escHtml(p.url) + '" title="在小窗中预览原站讨论与评论">💬 讨论</button>' : '') +
    '</div>' +
    (p.mc_version ? '<span class="bbsmc-card-ver-badge" title="Minecraft 版本；更多支持版本见详情">MC ' + escHtml(p.mc_version) + ((p.mc_versions?.length || 0) > 1 ? ' +' + String((p.mc_versions?.length || 1) - 1) : '') + '</span>' : '') +
    cover.retryButton + '</div>' +
    '<div class="bbsmc-card-body platform-card-body">' +
    '<a href="' + safeExternalHref(p.url) + '" target="_blank" rel="noreferrer" class="bbsmc-card-title platform-card-title js-open-unified-preview" data-platform="bbsmc" data-full-title="' + safeTitle + '" data-desc="' + safeDesc + '" data-cover="' + escHtml(coverImg) + '" data-author="' + safeAuthor + '" data-ver="' + escHtml(p.mc_version || '') + '" data-date="' + escHtml(p.date_modified || '') + '" title="' + safeTitle + '">' + safeTitle + '</a>' +
    '<div class="bbsmc-card-meta platform-card-meta">' +
    '<span>作者: <b class="bbsmc-author-tag">' + safeAuthor + '</b></span>' +
    (p.date_modified ? '<span>· 更新: ' + escHtml(p.date_modified.substring(0, 10)) + '</span>' : '') +
    '</div>' +
    (safeDesc ? '<div class="bbsmc-card-desc platform-card-summary" title="' + safeDesc + '">' + safeDesc + '</div>' : '<div class="platform-card-summary is-empty">暂无简介</div>') +
    (tagsHtml ? '<div class="bbsmc-card-tags platform-card-tags">' + tagsHtml + '</div>' : '<div class="platform-card-tags" aria-hidden="true"></div>') +
    galleryHtml +
    dlZoneHtml +
    '</div>' +
    '</div>';
}

/**
 * Modrinth Platform Card Renderer (Architecture V2 — Phase 3C).
 */
import type { ModrinthPack } from '../../types/legacy/modrinth';
import { escHtml } from '../../utils/html';
import { loaderLabel } from '../../domain/minecraft';
import { getCategoryLabel } from '../../filters/platformFilters';
import { recordRendererDebug } from '../../debug';

export const MODRINTH_COVER_FALLBACK = 'data:image/svg+xml;charset=utf-8,%3Csvg xmlns%3D"http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg" width%3D"400" height%3D"225" viewBox%3D"0 0 400 225"%3E%3Crect width%3D"400" height%3D"225" fill%3D"%23111827"%2F%3E%3Ctext x%3D"50%25" y%3D"50%25" dominant-baseline%3D"middle" text-anchor%3D"middle" fill%3D"%231bd96a" font-family%3D"sans-serif" font-size%3D"14"%3EModrinth 暂无封面%3C%2Ftext%3E%3C%2Fsvg%3E';

export function renderModrinthCard(p: ModrinthPack): string {
  if (typeof window !== 'undefined') {
    recordRendererDebug('modrinth');
  }
  const safeTitle = escHtml(p.title || '');
  const safeAuthor = escHtml(p.author || '未知');
  const safeDesc = escHtml(p.description || '');
  const coverImg = p.icon_url || MODRINTH_COVER_FALLBACK;
  const dlStr = (p.downloads || 0) > 10000 ? ((p.downloads || 0) / 10000).toFixed(1) + '万' : String(p.downloads || 0);
  const flStr = (p.followers || 0) > 10000 ? ((p.followers || 0) / 10000).toFixed(1) + '万' : String(p.followers || 0);

  let tagsHtml = '';
  if (p.env_display) {
    const isBoth = p.env_display.includes('服务端');
    tagsHtml += '<span class="modrinth-badge-env ' + (isBoth ? 'env-both' : 'env-client') + '" title="运行环境: ' + escHtml(p.env_display) + '">🖵 ' + escHtml(p.env_display) + '</span>';
  } else if (p.has_server) {
    tagsHtml += '<span class="badge-env badge-env-server" title="有服务端运行线索">🖳 有服务端运行线索</span>';
  }
  if (p.mc_version && p.mc_version !== '未知') {
    tagsHtml += '<span class="modrinth-badge-ver">🎮 ' + escHtml(p.mc_version) + '</span>';
  }
  if (p.loaders && Array.isArray(p.loaders)) {
    p.loaders.forEach((l) => { tagsHtml += '<span class="modrinth-badge-loader">' + escHtml(loaderLabel(l)) + '</span>'; });
  }
  if (p.categories && Array.isArray(p.categories)) {
    p.categories.slice(0, 4).forEach((c) => { tagsHtml += '<span class="modrinth-badge-cat" title="' + escHtml(c) + '">' + escHtml(getCategoryLabel(c)) + '</span>'; });
  }

  let dlZoneHtml = '<div class="xyebbs-download-zone">';
  const links = p.download_links || [];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  links.forEach((l: any) => {
    if (l && l.url) {
      const lClass = l.type === 'APP_IMPORT' ? 'pan-btn-modrinth' : 'pan-btn-other';
      const icon = l.type === 'APP_IMPORT' ? '🚀' : '🌐';
      dlZoneHtml += '<a href="' + l.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn ' + lClass + '" style="font-size:0.8rem;" title="' + escHtml(l.name || '') + '">' + icon + ' ' + escHtml(l.label || '下载') + ' ↗</a>';
    }
  });
  dlZoneHtml += '<button type="button" class="bili-pan-btn pan-btn-other js-open-plat-version-modal" data-platform="modrinth" data-vkey="' + escHtml(p.url || '') + '" data-title="' + safeTitle + '" data-ver="' + escHtml(p.mc_version || '') + '" data-date="' + escHtml(p.date_modified || '') + '" data-url="' + escHtml(p.url || '#') + '" data-author="' + safeAuthor + '" data-downloads="' + dlStr + '" style="font-size:0.8rem; background:rgba(27,217,106,0.12); color:#1bd96a; border-color:rgba(27,217,106,0.3); margin-top:4px;">📜 版本详情 ↗</button>';
  dlZoneHtml += '</div>';

  return '<div class="modrinth-pack-card">' +
    '<a href="' + escHtml(p.url || '#') + '" target="_blank" rel="noreferrer" class="xyebbs-card-cover">' +
    '<img class="xyebbs-card-img" src="' + escHtml(coverImg) + '" alt="' + safeTitle + '" loading="lazy" referrerpolicy="no-referrer" onerror="this.onerror=null;this.src=window.MODRINTH_COVER_FALLBACK;">' +
    '<div class="xyebbs-card-stats">' +
    '<span>📥 ' + dlStr + '</span>' +
    '<span>⭐ ' + flStr + '</span>' +
    '</div>' +
    (p.mc_version ? '<span class="xyebbs-card-ver-badge" style="background:rgba(27,217,106,0.9);">' + escHtml(p.mc_version) + '</span>' : '') +
    '</a>' +
    '<div class="xyebbs-card-body">' +
    '<a href="' + escHtml(p.url || '#') + '" target="_blank" rel="noreferrer" class="xyebbs-card-title js-open-unified-preview" data-platform="modrinth" data-full-title="' + safeTitle + '" data-desc="' + safeDesc + '" data-cover="' + escHtml(coverImg) + '" data-author="' + safeAuthor + '" data-ver="' + escHtml(p.mc_version || '') + '" data-date="' + escHtml(p.date_modified || '') + '" title="' + safeTitle + '">' + safeTitle + '</a>' +
    '<div class="xyebbs-card-meta">' +
    '<span>作者: <b style="color:#1bd96a;">' + safeAuthor + '</b></span>' +
    (p.date_modified ? '<span>· 更新: ' + escHtml(p.date_modified.substring(0, 10)) + '</span>' : '') +
    '</div>' +
    (safeDesc ? '<div class="xyebbs-card-desc" title="' + safeDesc + '">' + safeDesc + '</div>' : '') +
    (tagsHtml ? '<div class="xyebbs-card-tags">' + tagsHtml + '</div>' : '') +
    dlZoneHtml +
    '</div>' +
    '</div>';
}

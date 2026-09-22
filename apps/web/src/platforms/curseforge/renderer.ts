/**
 * CurseForge Platform Card Renderer (Architecture V2 — Phase 3C).
 */
import type { CurseforgePack } from '../../types/legacy/curseforge';
import { escHtml } from '../../utils/html';
import { loaderLabel } from '../../domain/minecraft';
import { getCategoryLabel } from '../../filters/platformFilters';
import { recordRendererDebug } from '../../debug';
import { stableImageSource } from '../../utils/imageFallback';

export const CURSEFORGE_COVER_FALLBACK = 'data:image/svg+xml;charset=utf-8,%3Csvg xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22 width%3D%22400%22 height%3D%22225%22 viewBox%3D%220 0 400 225%22%3E%3Crect width%3D%22400%22 height%3D%22225%22 fill%3D%22%231c1917%22%2F%3E%3Ctext x%3D%2250%25%22 y%3D%2250%25%22 dominant-baseline%3D%22middle%22 text-anchor%3D%22middle%22 fill%3D%22%23f16436%22 font-family%3D%22sans-serif%22 font-size%3D%2214%22%3ECurseForge%20%E6%9A%82%E6%97%A0%E5%B0%81%E9%9D%A2%3C%2Ftext%3E%3C%2Fsvg%3E';

export function renderCurseforgeCard(p: CurseforgePack): string {
  if (typeof window !== 'undefined') {
    recordRendererDebug('curseforge');
  }
  const safeTitle = escHtml(p.title || '');
  const safeAuthor = escHtml(p.author || '未知');
  const safeDesc = escHtml(p.description || '');
  const originalCover = p.icon_url || '';
  const coverImg = stableImageSource(originalCover, CURSEFORGE_COVER_FALLBACK);
  const fallbackData = originalCover
    ? ' data-original-src="' + escHtml(originalCover) + '" data-fallback-src="' + CURSEFORGE_COVER_FALLBACK + '"'
    : '';
  const dlStr = (p.downloads || 0) > 10000 ? ((p.downloads || 0) / 10000).toFixed(1) + '万' : String(p.downloads || 0);
  const flStr = (p.followers || 0) > 10000 ? ((p.followers || 0) / 10000).toFixed(1) + '万' : String(p.followers || 0);

  let tagsHtml = '';
  if (p.has_server) {
    tagsHtml += '<span class="badge-env badge-env-server" title="有服务端运行线索">🖳 有服务端运行线索</span>';
  }
  if (p.mc_version && p.mc_version !== '未知') {
    tagsHtml += '<span class="curseforge-badge-ver">🎮 ' + escHtml(p.mc_version) + '</span>';
  }
  if (p.loaders && Array.isArray(p.loaders)) {
    p.loaders.forEach((l) => { tagsHtml += '<span class="curseforge-badge-loader">' + escHtml(loaderLabel(l)) + '</span>'; });
  }
  if (p.categories && Array.isArray(p.categories)) {
    p.categories.slice(0, 4).forEach((c) => { tagsHtml += '<span class="curseforge-badge-cat" title="' + escHtml(c) + '">' + escHtml(getCategoryLabel(c)) + '</span>'; });
  }

  let dlZoneHtml = '<div class="xyebbs-download-zone">';
  const links = p.download_links || [];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  links.forEach((l: any) => {
    if (l && l.url) {
      const lClass = l.type === 'APP_IMPORT' ? 'pan-btn-curseforge' : 'pan-btn-other';
      const icon = l.type === 'APP_IMPORT' ? '🔥' : '🔗';
      dlZoneHtml += '<a href="' + l.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn ' + lClass + '" style="font-size:0.8rem;" title="' + escHtml(l.name || '') + '">' + icon + ' ' + escHtml(l.label || '下载') + ' ↗</a>';
    }
  });
  dlZoneHtml += '<button type="button" class="bili-pan-btn pan-btn-other js-open-plat-version-modal" data-platform="curseforge" data-vkey="' + escHtml(p.url || '') + '" data-title="' + safeTitle + '" data-ver="' + escHtml(p.mc_version || '') + '" data-date="' + escHtml(p.date_modified || '') + '" data-url="' + escHtml(p.url || '#') + '" data-author="' + safeAuthor + '" data-downloads="' + dlStr + '" style="font-size:0.8rem; background:rgba(241,100,54,0.12); color:#f16436; border-color:rgba(241,100,54,0.3); margin-top:4px;">📜 版本详情 ↗</button>';
  dlZoneHtml += '</div>';

  return '<div class="curseforge-pack-card">' +
    '<a href="' + escHtml(p.url || '#') + '" target="_blank" rel="noreferrer" class="xyebbs-card-cover">' +
    '<img class="xyebbs-card-img" src="' + escHtml(coverImg) + '"' + fallbackData + ' alt="' + safeTitle + '" loading="lazy" referrerpolicy="no-referrer">' +
    '<div class="xyebbs-card-stats">' +
    '<span>📥 ' + dlStr + '</span>' +
    '<span>👍 ' + flStr + '</span>' +
    '</div>' +
    (p.mc_version ? '<span class="xyebbs-card-ver-badge" style="background:rgba(241,100,54,0.9);">' + escHtml(p.mc_version) + '</span>' : '') +
    '</a>' +
    '<div class="xyebbs-card-body">' +
    '<a href="' + escHtml(p.url || '#') + '" target="_blank" rel="noreferrer" class="xyebbs-card-title js-open-unified-preview" data-platform="curseforge" data-full-title="' + safeTitle + '" data-desc="' + safeDesc + '" data-cover="' + escHtml(coverImg) + '" data-author="' + safeAuthor + '" data-ver="' + escHtml(p.mc_version || '') + '" data-date="' + escHtml(p.date_modified || '') + '" title="' + safeTitle + '">' + safeTitle + '</a>' +
    '<div class="xyebbs-card-meta">' +
    '<span>作者: <b style="color:#f16436;">' + safeAuthor + '</b></span>' +
    (p.date_modified ? '<span>· 更新: ' + escHtml(p.date_modified.substring(0, 10)) + '</span>' : '') +
    '</div>' +
    (safeDesc ? '<div class="xyebbs-card-desc" title="' + safeDesc + '">' + safeDesc + '</div>' : '') +
    (tagsHtml ? '<div class="xyebbs-card-tags">' + tagsHtml + '</div>' : '') +
    dlZoneHtml +
    '</div>' +
    '</div>';
}

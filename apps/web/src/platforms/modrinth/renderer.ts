/**
 * Modrinth Platform Card Renderer (Architecture V2 — Phase 3C).
 */
import type { ModrinthPack } from '../../types/legacy/modrinth';
import { escHtml } from '../../utils/html';
import { loaderLabel } from '../../domain/minecraft';
import { getCategoryLabel } from '../../filters/platformFilters';
import { recordRendererDebug } from '../../debug';
import { renderCoverImage } from '../../utils/coverImage';

export const MODRINTH_COVER_FALLBACK = 'data:image/svg+xml;charset=utf-8,%3Csvg xmlns%3D"http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg" width%3D"400" height%3D"225" viewBox%3D"0 0 400 225"%3E%3Crect width%3D"400" height%3D"225" fill%3D"%23111827"%2F%3E%3Ctext x%3D"50%25" y%3D"50%25" dominant-baseline%3D"middle" text-anchor%3D"middle" fill%3D"%231bd96a" font-family%3D"sans-serif" font-size%3D"14"%3EModrinth 暂无封面%3C%2Ftext%3E%3C%2Fsvg%3E';

export function renderModrinthCard(p: ModrinthPack): string {
  if (typeof window !== 'undefined') {
    recordRendererDebug('modrinth');
  }
  const safeTitle = escHtml(p.title || '');
  const safeAuthor = escHtml(p.author || '未知');
  const safeDesc = escHtml(p.description || '');
  const originalCover = p.icon_url || '';
  const cover = renderCoverImage({ url: originalCover, fallback: MODRINTH_COVER_FALLBACK, alt: (p.title || '') + '封面', key: 'modrinth:' + String(p.url || p.project_id), className: 'xyebbs-card-img' });
  const coverImg = cover.source;
  const dlStr = (p.downloads || 0) > 10000 ? ((p.downloads || 0) / 10000).toFixed(1) + '万' : String(p.downloads || 0);
  const flStr = (p.followers || 0) > 10000 ? ((p.followers || 0) / 10000).toFixed(1) + '万' : String(p.followers || 0);

  let tagsHtml = '';
  if (p.env_display) {
    const isBoth = p.env_display.includes('服务端');
    tagsHtml += '<span class="modrinth-badge-env ' + (isBoth ? 'env-both' : 'env-client') + '" title="运行环境: ' + escHtml(p.env_display) + '">🖵 ' + escHtml(p.env_display) + '</span>';
  } else if (p.has_server) {
    tagsHtml += '<span class="badge-env badge-env-server" title="有服务端运行线索">🖳 有服务端运行线索</span>';
  }
  if (p.loaders && Array.isArray(p.loaders)) {
    p.loaders.forEach((l) => { tagsHtml += '<span class="modrinth-badge-loader">' + escHtml(loaderLabel(l)) + '</span>'; });
  }
  if (p.categories && Array.isArray(p.categories)) {
    p.categories.slice(0, 4).forEach((c) => { tagsHtml += '<span class="modrinth-badge-cat" title="' + escHtml(c) + '">' + escHtml(getCategoryLabel(c)) + '</span>'; });
  }

  let dlZoneHtml = '<div class="xyebbs-download-zone platform-card-actions">';
  const links = p.download_links || [];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  links.forEach((l: any) => {
    if (l && l.url) {
      const lClass = l.type === 'APP_IMPORT' ? 'pan-btn-modrinth' : 'pan-btn-other';
      const icon = l.type === 'APP_IMPORT' ? '🚀' : '🌐';
      dlZoneHtml += '<a href="' + l.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn ' + lClass + '" style="font-size:0.8rem;" title="' + escHtml(l.name || '') + '">' + icon + ' ' + escHtml(l.label || '下载') + ' ↗</a>';
    }
  });
  dlZoneHtml += '<button type="button" class="bili-pan-btn pan-btn-other js-open-plat-version-modal" data-platform="modrinth" data-vkey="' + escHtml(p.url || '') + '" data-title="' + safeTitle + '" data-ver="' + escHtml(p.mc_version || '') + '" data-date="' + escHtml(p.date_modified || '') + '" data-url="' + escHtml(p.url || '#') + '" data-author="' + safeAuthor + '" data-downloads="' + dlStr + '" style="font-size:0.8rem; background:color-mix(in srgb,var(--plat-modrinth) 12%,var(--bg-surface)); color:color-mix(in srgb,var(--plat-modrinth) 72%,var(--text-primary)); border-color:color-mix(in srgb,var(--plat-modrinth) 32%,transparent); margin-top:4px;">📜 版本详情 ↗</button>';
  if (p.url) {
    dlZoneHtml += '<button type="button" class="bili-pan-btn pan-btn-other btn-inapp-win" data-action="open-in-app-window" data-url="' + escHtml(p.url) + '" data-title="' + safeTitle + ' Modrinth页面" style="font-size:0.8rem; margin-top:4px;">🪟 小窗浏览</button>';
  }
  dlZoneHtml += '</div>';

  return '<div class="modrinth-pack-card platform-pack-card">' +
    '<div class="cover-media cover-media-rich" data-cover-frame data-cover-state="' + cover.state + '">' +
    '<a href="' + escHtml(p.url || '#') + '" target="_blank" rel="noreferrer" class="xyebbs-card-cover">' +
    cover.image + cover.status +
    '<div class="xyebbs-card-stats">' +
    '<span>📥 ' + dlStr + '</span>' +
    '<span>⭐ ' + flStr + '</span>' +
    (p.url ? '<button type="button" class="modrinth-comment-btn" data-action="open-comment-preview" data-platform="modrinth" data-source-id="' + escHtml(String(p.project_id || p.slug || p.url || '')) + '" title="在小窗中预览原站与动态" style="cursor:pointer; background:none; border:none; color:inherit; font-size:inherit;">💬 动态</button>' : '') +
    '</div>' +
    (p.mc_version ? '<span class="xyebbs-card-ver-badge" title="Minecraft 版本；更多支持版本见标签或详情" style="background:color-mix(in srgb,var(--plat-modrinth) 78%,var(--text-primary)); color:var(--text-inverse);">MC ' + escHtml(p.mc_version) + ((p.mc_versions?.length || 0) > 1 ? ' +' + String((p.mc_versions?.length || 1) - 1) : '') + '</span>' : '') +
    '</a>' + cover.retryButton + '</div>' +
    '<div class="xyebbs-card-body platform-card-body">' +
    '<a href="' + escHtml(p.url || '#') + '" target="_blank" rel="noreferrer" class="xyebbs-card-title platform-card-title js-open-unified-preview" data-platform="modrinth" data-full-title="' + safeTitle + '" data-desc="' + safeDesc + '" data-cover="' + escHtml(coverImg) + '" data-author="' + safeAuthor + '" data-ver="' + escHtml(p.mc_version || '') + '" data-date="' + escHtml(p.date_modified || '') + '" title="' + safeTitle + '">' + safeTitle + '</a>' +
    '<div class="xyebbs-card-meta platform-card-meta">' +
    '<span>作者: <b style="color:color-mix(in srgb,var(--plat-modrinth) 72%,var(--text-primary));">' + safeAuthor + '</b></span>' +
    (p.date_modified ? '<span>· 更新: ' + escHtml(p.date_modified.substring(0, 10)) + '</span>' : '') +
    '</div>' +
    (safeDesc ? '<div class="xyebbs-card-desc platform-card-summary" title="' + safeDesc + '">' + safeDesc + '</div>' : '<div class="platform-card-summary is-empty">暂无简介</div>') +
    (tagsHtml ? '<div class="xyebbs-card-tags platform-card-tags">' + tagsHtml + '</div>' : '<div class="platform-card-tags" aria-hidden="true"></div>') +
    dlZoneHtml +
    '</div>' +
    '</div>';
}

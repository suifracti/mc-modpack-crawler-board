/**
 * CurseForge Platform Card Renderer (Architecture V2 — Phase 3C).
 */
import type { CurseforgePack } from '../../types/legacy/curseforge';
import { escHtml, safeExternalHref } from '../../utils/html';
import { loaderLabel } from '../../domain/minecraft';
import { getCategoryLabel } from '../../filters/platformFilters';
import { recordRendererDebug } from '../../debug';
import { renderCoverImage } from '../../utils/coverImage';

export const CURSEFORGE_COVER_FALLBACK = 'data:image/svg+xml;charset=utf-8,%3Csvg xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22 width%3D%22400%22 height%3D%22225%22 viewBox%3D%220 0 400 225%22%3E%3Crect width%3D%22400%22 height%3D%22225%22 fill%3D%22%231c1917%22%2F%3E%3Ctext x%3D%2250%25%22 y%3D%2250%25%22 dominant-baseline%3D%22middle%22 text-anchor%3D%22middle%22 fill%3D%22%23f16436%22 font-family%3D%22sans-serif%22 font-size%3D%2214%22%3ECurseForge%20%E6%9A%82%E6%97%A0%E5%B0%81%E9%9D%A2%3C%2Ftext%3E%3C%2Fsvg%3E';

export function renderCurseforgeCard(p: CurseforgePack): string {
  if (typeof window !== 'undefined') {
    recordRendererDebug('curseforge');
  }
  const safeTitle = escHtml(p.title || '');
  const safeAuthor = escHtml(p.author || '未知');
  const safeDesc = escHtml(p.description || '');
  const originalCover = p.icon_url || '';
  const cover = renderCoverImage({ url: originalCover, fallback: CURSEFORGE_COVER_FALLBACK, alt: (p.title || '') + '封面', key: 'curseforge:' + String(p.url || p.project_id), className: 'xyebbs-card-img' });
  const coverImg = cover.source;
  const dlStr = (p.downloads || 0) > 10000 ? ((p.downloads || 0) / 10000).toFixed(1) + '万' : String(p.downloads || 0);
  const flStr = (p.followers || 0) > 10000 ? ((p.followers || 0) / 10000).toFixed(1) + '万' : String(p.followers || 0);

  let tagsHtml = '';
  if (p.has_server) {
    tagsHtml += '<span class="badge-env badge-env-server" title="有服务端运行线索">🖳 有服务端运行线索</span>';
  }
  if (p.loaders && Array.isArray(p.loaders)) {
    p.loaders.forEach((l) => { tagsHtml += '<span class="curseforge-badge-loader">' + escHtml(loaderLabel(l)) + '</span>'; });
  }
  if (p.categories && Array.isArray(p.categories)) {
    p.categories.slice(0, 4).forEach((c) => { tagsHtml += '<span class="curseforge-badge-cat" title="' + escHtml(c) + '">' + escHtml(getCategoryLabel(c)) + '</span>'; });
  }

  let dlZoneHtml = '<div class="xyebbs-download-zone platform-card-actions">';
  const links = p.download_links || [];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  links.forEach((l: any) => {
    const urlStr = String(l?.url || '');
    const href = safeExternalHref(urlStr);
    if (href !== '#') {
      const lClass = 'pan-btn-other';
      const icon = '🔗';
      dlZoneHtml += '<a href="' + href + '" target="_blank" rel="noreferrer" class="bili-pan-btn ' + lClass + '" style="font-size:0.8rem;" title="' + escHtml(l.name || '') + '">' + icon + ' ' + escHtml(l.label || '官网直达') + ' ↗</a>';
    }
  });
  dlZoneHtml += '<button type="button" class="bili-pan-btn pan-btn-other js-open-plat-version-modal" data-platform="curseforge" data-vkey="' + escHtml(p.url || '') + '" data-title="' + safeTitle + '" data-ver="' + escHtml(p.mc_version || '') + '" data-date="' + escHtml(p.date_modified || '') + '" data-url="' + escHtml(p.url || '#') + '" data-author="' + safeAuthor + '" data-downloads="' + dlStr + '" style="font-size:0.8rem; background:color-mix(in srgb,var(--plat-curse) 12%,var(--bg-surface)); color:color-mix(in srgb,var(--plat-curse) 72%,var(--text-primary)); border-color:color-mix(in srgb,var(--plat-curse) 32%,transparent); margin-top:4px;">📜 版本详情 ↗</button>';
  if (p.url) {
    dlZoneHtml += '<button type="button" class="bili-pan-btn pan-btn-other btn-inapp-win" data-action="open-in-app-window" data-url="' + escHtml(p.url) + '" data-title="' + safeTitle + ' CurseForge页面" style="font-size:0.8rem; margin-top:4px;">🪟 小窗浏览</button>';
  }
  dlZoneHtml += '</div>';

  return '<div class="curseforge-pack-card platform-pack-card">' +
    '<div class="cover-media cover-media-rich" data-cover-frame data-cover-state="' + cover.state + '">' +
    '<a href="' + safeExternalHref(p.url) + '" target="_blank" rel="noreferrer" class="xyebbs-card-cover">' +
    cover.image + cover.status +
    '<div class="xyebbs-card-stats">' +
    '<span>📥 ' + dlStr + '</span>' +
    '<span>👍 ' + flStr + '</span>' +
    (p.url ? '<button type="button" class="curseforge-comment-btn" data-action="open-comment-preview" data-platform="curseforge" data-source-id="' + escHtml(String(p.project_id || p.slug || p.url || '')) + '" title="在小窗中预览原站评论" style="cursor:pointer; background:none; border:none; color:inherit; font-size:inherit;">💬 评论</button>' : '') +
    '</div>' +
    (p.mc_version ? '<span class="xyebbs-card-ver-badge" title="Minecraft 版本；更多支持版本见标签或详情" style="background:color-mix(in srgb,var(--plat-curse) 78%,var(--text-primary)); color:var(--text-inverse);">MC ' + escHtml(p.mc_version) + ((p.mc_versions?.length || 0) > 1 ? ' +' + String((p.mc_versions?.length || 1) - 1) : '') + '</span>' : '') +
    '</a>' + cover.retryButton + '</div>' +
    '<div class="xyebbs-card-body platform-card-body">' +
    '<a href="' + safeExternalHref(p.url) + '" target="_blank" rel="noreferrer" class="xyebbs-card-title platform-card-title js-open-unified-preview" data-platform="curseforge" data-full-title="' + safeTitle + '" data-desc="' + safeDesc + '" data-cover="' + escHtml(coverImg) + '" data-author="' + safeAuthor + '" data-ver="' + escHtml(p.mc_version || '') + '" data-date="' + escHtml(p.date_modified || '') + '" title="' + safeTitle + '">' + safeTitle + '</a>' +
    '<div class="xyebbs-card-meta platform-card-meta">' +
    '<span>作者: <b style="color:color-mix(in srgb,var(--plat-curse) 72%,var(--text-primary));">' + safeAuthor + '</b></span>' +
    (p.date_modified ? '<span>· 更新: ' + escHtml(p.date_modified.substring(0, 10)) + '</span>' : '') +
    '</div>' +
    (safeDesc ? '<div class="xyebbs-card-desc platform-card-summary" title="' + safeDesc + '">' + safeDesc + '</div>' : '<div class="platform-card-summary is-empty">暂无简介</div>') +
    (tagsHtml ? '<div class="xyebbs-card-tags platform-card-tags">' + tagsHtml + '</div>' : '<div class="platform-card-tags" aria-hidden="true"></div>') +
    dlZoneHtml +
    '</div>' +
    '</div>';
}

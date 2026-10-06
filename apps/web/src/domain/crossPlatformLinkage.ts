/**
 * Cross-Platform Modpack Linkage & Association Engine (Architecture V2).
 * Connects identical/related modpacks across all 6 platforms:
 * - MCMod (MC百科): Chinese wiki, reviews, mod lists
 * - Bilibili (B站): Chinese video reviews, translated showcase, tutorials
 * - CurseForge & Modrinth: Overseas official origin, author release, downloads
 * - BBSMC & XYEBBS: Domestic forum translations, server packs, Pan/Cloud drive mirrors
 */

import type { Platform } from './types';
import type { DesktopRecord } from '../desktopShell-v2';
import type { BiliGroup } from '../platforms/bilibili/renderer';
import { escHtml } from '../utils/html';
import { safeExternalUrl } from '../utils/url';
import { formatDisplayDate } from '../utils/format';

export interface ModpackFeatures {
  cleanTitle: string;
  chineseKeywords: string[];
  englishKeywords: string[];
  acronyms: string[];
  suggestedSearchQuery: string;
}

export interface CrossPlatformLink {
  platform: Platform;
  title: string;
  url: string;
  sourceId: string;
  packVersion?: string;
  meta: string;
  isOrigin?: boolean;
  rawRecord?: DesktopRecord;
}

export interface CrossPlatformAssociation {
  features: ModpackFeatures;
  totalMatches: number;
  platforms: Platform[];
  links: CrossPlatformLink[];
  biliVideos: Array<{
    bvid: string;
    title: string;
    uploader: string;
    playCount?: number;
    pubDate?: string;
    url: string;
  }>;
  suggestedSearchQuery: string;
}

export type PublicLinkIndex = {
  source?: 'local';
  schema: number;
  catalogCount: number;
  records: Record<string, { platform: Platform; sourceId: string; title: string; url: string; author?: string; packVersion?: string }>;
  links: Record<string, Array<{ id: string; reason: string }>>;
};
let publicIndex: PublicLinkIndex | undefined;
export function clearPublicAssociations(): void { publicIndex = undefined; }
export function installPublicAssociations(index: PublicLinkIndex): void {
  if (index.schema !== 1 || !index.records || !index.links) throw new Error('跨来源索引格式不匹配');
  publicIndex = index;
}
export function publicAssociationScope(): string {
  return publicIndex ? `关联检查覆盖 ${publicIndex.catalogCount.toLocaleString('zh-CN')} 条${publicIndex.source === 'local' ? '本地' : '公开'}记录；同名或原页指向均为线索，版本与作者需到原站核对。` : '关联索引尚未加载，以下仅扫描当前已加载记录。';
}

const GENERIC_CHINESE_WORDS = new Set([
  '整合包', '模组包', '我的世界', '汉化版', '汉化', '发布', '更新', '搬运',
  '自制', '官方', '原版', '客户端', '开黑', '联机', '超难', '低配', '高配',
  '光影', '最新', '修复', '重构', '重置', '重铸', '推荐', '必玩', '生存',
  '冒险', '大型', '魔改', '硬核', '科技', '魔法', '空岛', '系列', '版本',
  '全网', '独家', '测试', '抢先', '正式版', '正式', '测试版', '体验版'
]);

const GENERIC_ENGLISH_WORDS = new Set([
  'minecraft', 'modpack', 'modpacks', 'forge', 'fabric', 'neoforge', 'quilt',
  'version', 'update', 'official', 'unofficial', 'release', 'beta', 'alpha',
  'server', 'client', 'edition', 'pack', 'ultimate', 'custom', 'remastered',
  'reloaded', 'reborn', 'expanded', 'enhanced', 'adventure', 'survival', 'quest'
]);

const STOP_ACRONYMS = new Set(['MC', 'PC', 'MOD', 'ZIP', 'HD', 'API', 'FPS', 'RAM', 'CPU', 'LAN']);

/**
 * Normalizes an English phrase for robust comparison (lowercased, punctuation-free, collapsed spaces).
 */
export function normalizePhrase(text: string): string {
  return String(text || '')
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Extracts salient keywords, acronyms, and English slugs from modpack titles and descriptions.
 */
export function extractPackFeatures(title: string, raw?: Record<string, unknown>): ModpackFeatures {
  const brackets: string[] = [];
  const bracketRegex = /[\[\(\（【]([^\]\)\）】]+)[\]\)\）】]/g;
  let bracketMatch: RegExpExecArray | null;
  while ((bracketMatch = bracketRegex.exec(title)) !== null) {
    brackets.push(bracketMatch[1].trim());
  }

  // Strip brackets from main title for the clean title
  const cleanTitle = title
    .replace(/[\[\(\（【][^\]\)\）】]+[\]\)\）】]/g, ' ')
    .replace(/v?\d+(?:\.\d+)+(?:-[a-zA-Z0-9_.]+)?/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

  const allCandidateSources = [cleanTitle, ...brackets];

  // If slug or english title is present in raw, include it
  if (raw?.slug && typeof raw.slug === 'string') {
    allCandidateSources.push(raw.slug.replace(/[-_]/g, ' '));
  }
  if (raw?.english_name && typeof raw.english_name === 'string') {
    allCandidateSources.push(raw.english_name);
  }

  const acronyms: string[] = [];
  const englishKeywords: string[] = [];
  const chineseKeywords: string[] = [];

  for (const text of allCandidateSources) {
    if (!text) continue;

    // 1. Acronyms (e.g., NFWC, GTNH, ATM9, RLCraft)
    const acroMatches = text.match(/\b[A-Z0-9]{2,8}\b/g) || [];
    for (const a of acroMatches) {
      const upper = a.toUpperCase();
      if (!STOP_ACRONYMS.has(upper) && !/^\d+$/.test(upper)) {
        acronyms.push(upper);
      }
    }

    // 2. English phrases (length >= 3 characters)
    const enMatches = text.match(/[a-zA-Z]{2,}(?:\s+[a-zA-Z]{2,})*/g) || [];
    for (const en of enMatches) {
      const lower = en.toLowerCase().trim();
      const norm = normalizePhrase(lower);
      if (norm.length >= 3 && !GENERIC_ENGLISH_WORDS.has(norm)) {
        englishKeywords.push(norm);
      }
    }

    // 3. Chinese keyword phrases (length >= 2 characters)
    const zhMatches = text.match(/[\u4e00-\u9fa5]{2,}/g) || [];
    for (const zh of zhMatches) {
      if (!GENERIC_CHINESE_WORDS.has(zh) && zh.length >= 2) {
        chineseKeywords.push(zh);
      }
    }
  }

  const uniqueAcro = Array.from(new Set(acronyms));
  const uniqueEn = Array.from(new Set(englishKeywords))
    .sort((a, b) => b.length - a.length);
  const uniqueZh = Array.from(new Set(chineseKeywords))
    .sort((a, b) => b.length - a.length);

  // Suggested search query prefers the most distinctive Chinese keyword, or main English phrase
  let suggested = uniqueZh[0] || uniqueEn[0] || cleanTitle || title;
  if (uniqueZh.length > 0 && uniqueZh[0].length >= 2) {
    suggested = uniqueZh[0];
  } else if (uniqueEn.length > 0) {
    suggested = uniqueEn[0];
  }

  return {
    cleanTitle,
    chineseKeywords: uniqueZh,
    englishKeywords: uniqueEn,
    acronyms: uniqueAcro,
    suggestedSearchQuery: suggested,
  };
}

/**
 * Checks if candidateText matches target features with high confidence.
 */
export function matchFeatures(candidateText: string, features: ModpackFeatures): boolean {
  if (!candidateText) return false;
  const textLower = candidateText.toLowerCase();

  // 1. Check distinct English keywords (e.g. "no flesh within chest", "dawncraft")
  for (const en of features.englishKeywords) {
    if (en.length >= 4 && textLower.includes(en)) {
      return true;
    }
  }

  // 2. Check distinct acronyms surrounded by non-alphanumerics or brackets (e.g. [NFWC], [GTNH])
  for (const acro of features.acronyms) {
    const acroLower = acro.toLowerCase();
    const acroRegex = new RegExp(`(?:\\[|\\(|\\b)${acroLower}(?:\\]|\\)|\\b)`, 'i');
    if (acroRegex.test(candidateText)) {
      return true;
    }
  }

  // 3. Check Chinese core keywords (e.g. "脆骨症", "格雷科技", "破晓之末")
  for (const zh of features.chineseKeywords) {
    if (zh.length >= 2 && candidateText.includes(zh)) {
      return true;
    }
  }

  return false;
}

/**
 * Finds all cross-platform associations for a given record.
 */
export function findCrossPlatformAssociations(
  record: DesktopRecord,
  allRecords: DesktopRecord[],
  biliGroups: BiliGroup[] = [],
): CrossPlatformAssociation {
  const features = extractPackFeatures(record.title, record.raw);
  if (publicIndex) {
    const links: CrossPlatformLink[] = [], biliVideos: CrossPlatformAssociation['biliVideos'] = [];
    for (const match of publicIndex.links[record.id] || []) {
      const row = publicIndex.records[match.id];
      const url = safeExternalUrl(row?.url);
      if (!row || !url || row.platform === record.platform) continue;
      if (row.platform === 'bilibili') biliVideos.push({ bvid: row.sourceId, title: row.title, uploader: row.author || 'UP主未收录', url });
      else links.push({ ...row, url, meta: `${match.reason}${row.author ? ' · ' + row.author : ''}`, isOrigin: row.platform === 'curseforge' || row.platform === 'modrinth' });
    }
    return { features, links, biliVideos, totalMatches: links.length + biliVideos.length, platforms: [...new Set([...links.map(l => l.platform), ...(biliVideos.length ? ['bilibili' as Platform] : [])])], suggestedSearchQuery: features.suggestedSearchQuery };
  }
  const links: CrossPlatformLink[] = [];
  const platformsSeen = new Set<Platform>();

  // Scan other loaded records (excluding current record)
  for (const other of allRecords) {
    if (other.id === record.id) continue;
    if (other.platform === record.platform) continue; // sister platform match

    const candidateFull = `${other.title} ${other.summary || ''} ${other.author || ''}`;
    if (matchFeatures(candidateFull, features)) {
      platformsSeen.add(other.platform);

      let meta = '';
      if (other.platform === 'mcmod') {
        const raw = other.raw || {};
        const mods = raw.includedModsCount ? `${raw.includedModsCount} 模组` : '';
        const votes = (raw.votes as Record<string, unknown>)?.redPercent ? `${(raw.votes as any).redPercent}% 好评` : '';
        meta = [mods, votes, '百科词条'].filter(Boolean).join(' · ');
      } else if (other.platform === 'curseforge' || other.platform === 'modrinth') {
        const dls = other.evidence.find((e) => e.label.includes('下载') || e.label.includes('热度'))?.value || '';
        meta = [dls, other.packVersion ? `版本 ${other.packVersion}` : '', '原站项目线索'].filter(Boolean).join(' · ');
      } else if (other.platform === 'bbsmc' || other.platform === 'xyebbs') {
        meta = [other.author ? `作者: ${other.author}` : '', other.packVersion ? `v${other.packVersion}` : '', '国内论坛与网盘'].filter(Boolean).join(' · ');
      }

      links.push({
        platform: other.platform,
        title: other.title,
        url: safeExternalUrl(other.url) || '',
        sourceId: other.sourceId,
        packVersion: other.packVersion,
        meta: meta || '相关收录',
        isOrigin: other.platform === 'curseforge' || other.platform === 'modrinth',
        rawRecord: other,
      });
    }
  }

  // Scan Bilibili videos
  const biliVideos: Array<{
    bvid: string;
    title: string;
    uploader: string;
    playCount?: number;
    pubDate?: string;
    url: string;
  }> = [];

  for (const group of biliGroups) {
    for (const item of group.items) {
      if (matchFeatures(`${item.title} ${item.desc || ''}`, features)) {
        biliVideos.push({
          bvid: String(item.bvid || item.id || ''),
          title: item.title,
          uploader: item.author || (item as any).uploader || 'UP主',
          playCount: item.views || (item as any).playCount,
          pubDate: formatDisplayDate(item.pub_time || item.published_at),
          url: item.bvid ? `https://www.bilibili.com/video/${item.bvid}` : item.url || '',
        });
        if (biliVideos.length >= 8) break; // keep top 8
      }
    }
    if (biliVideos.length >= 8) break;
  }

  if (biliVideos.length > 0) {
    platformsSeen.add('bilibili');
  }

  return {
    features,
    totalMatches: links.length + biliVideos.length,
    platforms: Array.from(platformsSeen),
    links,
    biliVideos,
    suggestedSearchQuery: features.suggestedSearchQuery,
  };
}

/**
 * Renders an inline linkage badge bar for Modpack Cards.
 */
export function renderCardLinkageCapsule(association: CrossPlatformAssociation, record?: DesktopRecord): string {
  if (association.totalMatches === 0) return '';

  const badges: string[] = [];

  // Bilibili
  if (association.biliVideos.length > 0) {
    badges.push(`<span class="linkage-pill linkage-bili" title="按名称找到 ${association.biliVideos.length} 条相关视频线索">📺 B站 (${association.biliVideos.length})</span>`);
  }

  // MCMod
  const mcmodLink = association.links.find((l) => l.platform === 'mcmod');
  if (mcmodLink) {
    badges.push(`<span class="linkage-pill linkage-mcmod" title="MC百科词条收录：${escHtml(mcmodLink.title)}">📖 百科词条</span>`);
  }

  // Overseas Origin (CurseForge / Modrinth)
  const originLink = association.links.find((l) => l.isOrigin);
  if (originLink) {
    badges.push(`<span class="linkage-pill linkage-origin" title="原站项目线索：${escHtml(originLink.title)}">📦 原站项目</span>`);
  }

  // Domestic Forum (BBSMC / XYEBBS)
  const forumLink = association.links.find((l) => l.platform === 'bbsmc' || l.platform === 'xyebbs');
  if (forumLink) {
    badges.push(`<span class="linkage-pill linkage-forum" title="论坛帖子线索：${escHtml(forumLink.title)}">📜 论坛帖子</span>`);
  }

  if (badges.length === 0) return '';

  return `<div class="card-linkage-row" title="${escHtml(publicIndex ? publicAssociationScope() : '根据已加载记录的名称匹配，打开详情后到原站确认')}">
    ${record ? `<button type="button" class="linkage-pill linkage-open" data-action="open-in-app-window" data-card-window="true" data-in-app-tab="linkage" data-url="${escHtml(safeExternalUrl(record.url) || '')}" data-title="${escHtml(record.title)}" data-record-id="${escHtml(record.id)}">查看其他来源</button>` : '<span class="linkage-label">其他来源</span>'}
    ${badges.join('')}
  </div>`;
}

/**
 * Renders a full cross-platform linkage ecosystem section for Detail Drawer.
 */
export function renderDrawerLinkageSection(
  association: CrossPlatformAssociation,
  _currentRecord: DesktopRecord,
): string {
  const query = escHtml(association.suggestedSearchQuery);
  const searchBtn = `<button type="button" class="linkage-search-btn" data-action="search-modpack-all" data-query="${query}" title="搜索六个来源已收录的记录">🔍 搜索已收录记录：“${query}”</button>`;

  if (association.totalMatches === 0) {
    return `<div class="detail-section linkage-section">
      <div class="dynamics-header">
        <h3>其他来源线索</h3>
      </div>
      <div class="linkage-empty-box">
        <p>${publicIndex ? '公开目录中' : '当前已加载记录中'}未找到可确认名称或原页指向的其他来源线索。可继续搜索已收录的公开记录。</p>
        ${searchBtn}
      </div>
    </div>`;
  }

  const linksHtml = association.links.map((link) => {
    const icon = link.platform === 'mcmod' ? '📖'
      : link.platform === 'curseforge' ? '🔥'
      : link.platform === 'modrinth' ? '🌿'
      : link.platform === 'bbsmc' ? '📜'
      : link.platform === 'xyebbs' ? '💎' : '📦';

    const pName = link.platform === 'mcmod' ? 'MC百科'
      : link.platform === 'curseforge' ? 'CurseForge'
      : link.platform === 'modrinth' ? 'Modrinth'
      : link.platform === 'bbsmc' ? 'BBSMC 论坛'
      : link.platform === 'xyebbs' ? 'XYEBBS 论坛' : link.platform;

    return `<div class="linkage-item-card">
      <div class="linkage-item-head">
        <span class="linkage-item-platform">${icon} ${pName}</span>
        ${link.packVersion ? `<span class="linkage-item-ver">🏷️ v${escHtml(link.packVersion)}</span>` : ''}
      </div>
      <div class="linkage-item-title">${escHtml(link.title)}</div>
      <div class="linkage-item-meta">${escHtml(link.meta)}</div>
      <div class="linkage-item-actions">
        ${link.url ? `<a href="${escHtml(link.url)}" target="_blank" rel="noreferrer" class="linkage-btn linkage-btn-external">打开原网页 ↗</a>` : ''}
        ${link.rawRecord ? `<button type="button" class="linkage-btn linkage-btn-select" data-action="switch-to-record" data-record-id="${escHtml(link.rawRecord.id)}">查看此条目详情</button>` : ''}
      </div>
    </div>`;
  }).join('');

  const biliHtml = association.biliVideos.length > 0
    ? `<div class="linkage-bili-group">
        <h4>📺 Bilibili 相关视频 (${association.biliVideos.length} 条)</h4>
        <div class="linkage-bili-list">
          ${association.biliVideos.map((v) => `
            <a href="${escHtml(v.url)}" target="_blank" rel="noreferrer" class="linkage-bili-card">
              <span class="bili-card-icon">▶</span>
              <div class="bili-card-info">
                <span class="bili-card-title">${escHtml(v.title)}</span>
                <span class="bili-card-sub">${escHtml(v.uploader)}${v.pubDate ? ` · ${escHtml(v.pubDate)}` : ''}${v.playCount ? ` · ${v.playCount} 播放` : ''}</span>
              </div>
            </a>
          `).join('')}
        </div>
      </div>`
    : '';

  return `<div class="detail-section linkage-section">
    <div class="dynamics-header">
      <h3>其他来源线索 <span class="detail-submeta">${association.totalMatches} 条名称匹配，需确认是否为同一整合包</span></h3>
    </div>
    <div class="linkage-cards-grid">
      ${linksHtml}
    </div>
    ${biliHtml}
    <div class="linkage-bottom-bar">
      ${searchBtn}
    </div>
  </div>`;
}

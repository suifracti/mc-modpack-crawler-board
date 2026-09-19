/**
 * Platform Filter Logic & Pipelines (Architecture V2 — Phase 3C).
 */
import type { BilibiliPack } from '../types/legacy/bilibili';
import type { BbsmcPack } from '../types/legacy/bbsmc';
import type { XyebbsPack } from '../types/legacy/xyebbs';
import type { ModrinthPack } from '../types/legacy/modrinth';
import type { CurseforgePack } from '../types/legacy/curseforge';
import type {
  BilibiliFilterCriteria,
  BBSMCFilterCriteria,
  XyebbsFilterCriteria,
  ModrinthFilterCriteria,
  CurseforgeFilterCriteria,
} from './types';
import {
  matchCategories,
  matchVersion,
  matchLoader,
  matchServerOnly,
  matchPan,
  matchDateRange,
} from './predicates';
import { recordFilterDebug } from '../debug';

export const CAT_LABELS: Record<string, string> = {
  // Modrinth
  'multiplayer': '多人游戏',
  'optimization': '性能优化',
  'adventure': '冒险',
  'lightweight': '轻量',
  'combat': '战斗',
  'technology': '科技',
  'challenging': '硬核挑战',
  'magic': '魔法',
  'kitchen-sink': '综合整合',
  'quests': '任务',
  'game-mechanics': '游戏机制',
  'equipment': '装备',
  'decoration': '装饰',
  'worldgen': '世界生成',
  'food': '食物',
  'mobs': '生物',
  'utility': '实用工具',
  'storage': '存储',
  'management': '管理',
  'library': '前置库',
  'transportation': '交通',
  'social': '社交',
  'iris': '光影支持',
  'minecraft': '原版风格',
  'cursed': '搞怪',
  'economy': '经济',
  'datapack': '数据包',
  'modloader': '加载器',
  'minigame': '小游戏',
  // CurseForge
  'Exploration': '探索',
  'Adventure and RPG': '冒险与RPG',
  'Tech': '科技',
  'Multiplayer': '多人游戏',
  'Magic': '魔法',
  'Combat / PvP': '战斗 / PvP',
  'Small / Light': '小型轻量',
  'Vanilla+': '原版增强',
  'Quests': '任务',
  'Hardcore': '硬核',
  'Extra Large': '大型整合',
  'Sci-Fi': '科幻',
  'Horror': '恐怖',
  'Map Based': '地图驱动',
  'Skyblock': '空岛',
  'Mini Game': '小游戏',
  'Expert': '专家模式',
  'FTB Official Pack': 'FTB 官方包',
  'RLCraft': 'RLCraft 系',
};

export function getCategoryLabel(val: string): string {
  return CAT_LABELS[val] || val;
}

export function filterBilibiliPacks(
  packs: BilibiliPack[],
  criteria: BilibiliFilterCriteria,
  excludeCats: boolean = false
): BilibiliPack[] {
  const q = (criteria.searchQuery || '').trim().toLowerCase();
  const nowSec = Math.floor(Date.now() / 1000);
  let refSec = nowSec;
  if (criteria.activeDate) {
    let latestSec = 0;
    for (const item of packs) {
      if ((item.pub_timestamp || 0) > latestSec) latestSec = item.pub_timestamp || 0;
    }
    refSec = Math.max(nowSec, latestSec);
  }

  const result = packs.filter((p) => {
    if (!matchServerOnly(criteria.serverOnly, p.has_server)) return false;
    if (q) {
      const searchTarget = (
        (p.title || '') +
        ' ' +
        (p.author || '') +
        ' ' +
        (p.desc || '') +
        ' ' +
        (p.mc_version || '') +
        ' ' +
        (p.loaders || []).join(' ') +
        ' ' +
        (p.categories || []).join(' ')
      ).toLowerCase();
      if (!searchTarget.includes(q)) return false;
    }
    if (!matchVersion(criteria.version, p.mc_version, p.all_versions)) return false;
    if (!matchLoader(criteria.loader, p.loaders)) return false;
    if (!matchCategories(criteria.activeCategories, p.categories, excludeCats)) return false;
    if (criteria.activePan) {
      if (!matchPan(criteria.activePan, p.download_links)) return false;
    }
    if (criteria.activeDate) {
      if (!matchDateRange(criteria.activeDate, p.pub_timestamp, p.pub_time, refSec)) return false;
    }
    return true;
  });

  if (typeof window !== 'undefined') {
    recordFilterDebug('bilibili', criteria, result.length, result.map((p) => p.bvid || p.id));
  }
  return result;
}

export function filterBbsmcPacks(
  packs: BbsmcPack[],
  criteria: BBSMCFilterCriteria,
  excludeCats: boolean = false
): BbsmcPack[] {
  const q = (criteria.searchQuery || '').trim().toLowerCase();
  const result = packs.filter((p) => {
    if (!matchServerOnly(criteria.serverOnly, p.has_server)) return false;
    if (q) {
      const searchTarget = (
        (p.title || '') +
        ' ' +
        (p.author || '') +
        ' ' +
        (p.description || '') +
        ' ' +
        (p.mc_version || '') +
        ' ' +
        (p.loaders || []).join(' ') +
        ' ' +
        (p.categories || []).join(' ')
      ).toLowerCase();
      if (!searchTarget.includes(q)) return false;
    }
    if (!matchVersion(criteria.version, p.mc_version, p.all_versions)) return false;
    if (!matchLoader(criteria.loader, p.loaders)) return false;
    if (!matchCategories(criteria.activeCategories, p.categories, excludeCats)) return false;
    if (criteria.activePan) {
      if (!matchPan(criteria.activePan, p.download_links)) return false;
    }
    return true;
  });

  if (typeof window !== 'undefined') {
    recordFilterDebug('bbsmc', criteria, result.length, result.map((p) => p.project_id || p.id));
  }
  return result;
}

export function filterXyebbsPacks(
  packs: XyebbsPack[],
  criteria: XyebbsFilterCriteria,
  excludeCats: boolean = false
): XyebbsPack[] {
  const q = (criteria.searchQuery || '').trim().toLowerCase();
  const result = packs.filter((p) => {
    if (!matchServerOnly(criteria.serverOnly, p.has_server)) return false;
    if (q) {
      const searchTarget = (
        (p.title || '') +
        ' ' +
        (p.english_name || '') +
        ' ' +
        (p.author || '') +
        ' ' +
        (p.description || '') +
        ' ' +
        (p.mc_version || '') +
        ' ' +
        (p.loaders || []).join(' ') +
        ' ' +
        (p.categories || []).join(' ')
      ).toLowerCase();
      if (!searchTarget.includes(q)) return false;
    }
    if (!matchVersion(criteria.version, p.mc_version, p.all_versions)) return false;
    if (!matchLoader(criteria.loader, p.loaders)) return false;
    if (!matchCategories(criteria.activeCategories, p.categories, excludeCats)) return false;
    if (criteria.activePan) {
      if (!matchPan(criteria.activePan, p.download_links, p.url)) return false;
    }
    return true;
  });

  if (typeof window !== 'undefined') {
    recordFilterDebug('xyebbs', criteria, result.length, result.map((p) => p.project_id || p.id));
  }
  return result;
}

export function filterModrinthPacks(
  packs: ModrinthPack[],
  criteria: ModrinthFilterCriteria,
  excludeCats: boolean = false
): ModrinthPack[] {
  const q = (criteria.searchQuery || '').trim().toLowerCase();
  const result = packs.filter((p) => {
    if (!matchServerOnly(criteria.serverOnly, p.has_server)) return false;
    if (q) {
      const searchTarget = (
        (p.title || '') +
        ' ' +
        (p.slug || '') +
        ' ' +
        (p.author || '') +
        ' ' +
        (p.description || '') +
        ' ' +
        (p.categories || []).join(' ')
      ).toLowerCase();
      if (!searchTarget.includes(q)) return false;
    }
    if (!matchVersion(criteria.version, p.mc_version, p.all_versions)) return false;
    if (!matchLoader(criteria.loader, p.loaders)) return false;
    if (!matchCategories(criteria.activeCategories, p.categories, excludeCats)) return false;
    return true;
  });

  if (typeof window !== 'undefined') {
    recordFilterDebug('modrinth', criteria, result.length, result.map((p) => p.id));
  }
  return result;
}

export function filterCurseforgePacks(
  packs: CurseforgePack[],
  criteria: CurseforgeFilterCriteria,
  excludeCats: boolean = false
): CurseforgePack[] {
  const q = (criteria.searchQuery || '').trim().toLowerCase();
  const result = packs.filter((p) => {
    if (!matchServerOnly(criteria.serverOnly, p.has_server)) return false;
    if (q) {
      const searchTarget = (
        (p.title || '') +
        ' ' +
        (p.slug || '') +
        ' ' +
        (p.author || '') +
        ' ' +
        (p.description || '') +
        ' ' +
        (p.categories || []).join(' ')
      ).toLowerCase();
      if (!searchTarget.includes(q)) return false;
    }
    if (!matchVersion(criteria.version, p.mc_version, p.all_versions)) return false;
    if (!matchLoader(criteria.loader, p.loaders)) return false;
    if (!matchCategories(criteria.activeCategories, p.categories, excludeCats)) return false;
    return true;
  });

  if (typeof window !== 'undefined') {
    recordFilterDebug('curseforge', criteria, result.length, result.map((p) => p.id));
  }
  return result;
}

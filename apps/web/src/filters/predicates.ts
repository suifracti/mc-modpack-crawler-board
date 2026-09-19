/**
 * Filter Predicates (Architecture V2 — Phase 3C).
 * Pure reusable filter predicate functions across all 6 platforms.
 */

/**
 * Multi-category matching with optional exclusion mode.
 * - Empty selection => passes
 * - exclude=false => passes if item has any selected category (union semantics)
 * - exclude=true => passes if item has none of the selected categories
 */
export function matchCategories(
  selected: string[] | undefined,
  itemCategories: string[] | undefined,
  exclude: boolean = false
): boolean {
  if (!selected || selected.length === 0) return true;
  const cats = itemCategories || [];
  const hit = cats.some((c) => selected.includes(c));
  return exclude ? !hit : hit;
}

/**
 * Version matching: matches if target is substring of primary version
 * or exact member of all_versions array.
 */
export function matchVersion(
  targetVersion: string | undefined,
  primaryVersion: string | undefined,
  allVersions: string[] | undefined
): boolean {
  if (!targetVersion) return true;
  const prim = primaryVersion || '';
  if (prim.includes(targetVersion)) return true;
  if (allVersions && allVersions.includes(targetVersion)) return true;
  return false;
}

/**
 * Loader matching: matches if targetLoader is present in itemLoaders list.
 */
export function matchLoader(
  targetLoader: string | undefined,
  itemLoaders: string[] | undefined
): boolean {
  if (!targetLoader) return true;
  return (itemLoaders || []).includes(targetLoader);
}

/**
 * Server availability matching: matches if item has server support.
 */
export function matchServerOnly(
  serverOnly: boolean | undefined,
  hasServer: boolean | undefined
): boolean {
  if (!serverOnly) return true;
  return Boolean(hasServer);
}

/**
 * Netdisk / pan provider matching.
 */
export interface DownloadLinkCandidate {
  name?: string;
  url?: string;
  filename?: string;
  type?: string;
}

export function matchPan(
  activePan: string | undefined,
  links: DownloadLinkCandidate[] | undefined,
  officialUrl?: string
): boolean {
  if (!activePan) return true;
  const panKey = activePan.toLowerCase();
  const list = links || [];

  if (panKey === 'official') {
    return Boolean(officialUrl);
  }

  return list.some((l) => {
    const n = ((l && l.name) || '').toLowerCase();
    const u = ((l && l.url) || '').toLowerCase();
    const fn = ((l && l.filename) || '').toLowerCase();
    const t = ((l && l.type) || '').toLowerCase();

    if (panKey === 'modrinth') {
      return n.includes('modrinth') || fn.includes('.mrpack') || u.includes('cdn.bbsmc.net');
    }
    if (panKey === 'curseforge') {
      return u.includes('curseforge.com') || n.includes('curseforge');
    }
    if (panKey === '夸克') {
      return n.includes('夸克') || u.includes('pan.quark.cn') || t === 'quark';
    }
    if (panKey === '百度') {
      return n.includes('百度') || u.includes('pan.baidu.com') || t === 'baidu';
    }
    if (panKey === '123') {
      return n.includes('123') || u.includes('123pan') || t.includes('123');
    }
    if (panKey === '迅雷') {
      return n.includes('迅雷') || u.includes('pan.xunlei.com') || t === 'xunlei';
    }
    if (panKey === '蓝奏') {
      return n.includes('蓝奏') || u.includes('lanzou') || t.includes('lanzou');
    }

    return n.includes(panKey) || u.includes(panKey);
  });
}

/**
 * Date range filter for timestamp/publication date.
 */
export function matchDateRange(
  activeDate: string | undefined,
  pubTimestamp: number | undefined,
  pubTime: string | undefined,
  refTimestamp: number = Math.floor(Date.now() / 1000)
): boolean {
  if (!activeDate) return true;

  if (activeDate === '7d') {
    return Boolean(pubTimestamp && refTimestamp - pubTimestamp <= 7 * 86400);
  }
  if (activeDate === '30d') {
    return Boolean(pubTimestamp && refTimestamp - pubTimestamp <= 30 * 86400);
  }
  if (activeDate === '90d') {
    return Boolean(pubTimestamp && refTimestamp - pubTimestamp <= 90 * 86400);
  }
  if (/^\d\d\d\d$/.test(activeDate)) {
    return Boolean(pubTime && pubTime.startsWith(activeDate));
  }
  return Boolean(pubTime && pubTime.startsWith(activeDate));
}

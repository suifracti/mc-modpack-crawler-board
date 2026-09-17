/**
 * MCMod Version Modal Adapter (Architecture V2 — Phase 3C).
 */
import type { McmodStructuredItem } from './types';
import type { VersionModalViewModel } from '../../modals/version/types';

export function adaptMcmodToVersionModal(
  pack?: Partial<McmodStructuredItem> | null,
  extra?: Record<string, unknown>
): VersionModalViewModel {
  const p = pack || {};
  const mcVersions = p.mcVersions || (extra?.mcVersList as string[]) || [];
  const former = p.formerTitles || (extra?.former_titles as string[]) || [];
  const mid = p.mid || (extra?.mid as number) || (extra?.id as number) || 0;
  const title = (extra?.title as string) || p.title || `整合包 #${mid}`;

  const raw = p as any;
  return {
    platform: 'mcmod',
    id: mid,
    title,
    platformName: 'MC百科权威',
    siteShort: 'MC百科',
    latestVersion: (extra?.ver as string) || raw.latest_version || raw.latestVersion || '通用 / 最新',
    lastUpdated: (extra?.date as string) || raw.last_update_date || raw.lastUpdateDate || '暂无记录',
    dateCreated: (extra?.date_created as string) || raw.release_date || raw.releaseDate || undefined,
    versionCount: (extra?.count as number) || raw.version_count || raw.versionCount || 1,
    mcVersionsSummary: mcVersions.length ? mcVersions.join(', ') : '通用 / 未指定',
    mcVersionsList: mcVersions,
    typeName: (extra?.typeName as string) || raw.type_name || raw.typeName || '优质模组包',
    modCountStr: p.includedModsCount ? `${p.includedModsCount} 款` : (raw.mod_count ? `${raw.mod_count} 款` : (extra?.modCount as string) || undefined),
    targetUrl: (extra?.url as string) || `https://www.mcmod.cn/modpack/version/${mid}.html`,
    hasServer: Boolean(p.has_server || extra?.has_server),
    envDisplay: (p.has_server || extra?.has_server) ? '支持联机开服 / 提供专用服务端' : '未提供专用开服端',
    formerTitles: former,
    releases: (extra?.releases as any[]) || [],
  };
}

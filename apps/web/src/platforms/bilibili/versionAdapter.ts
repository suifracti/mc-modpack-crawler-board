/**
 * Bilibili Version Modal Adapter (Architecture V2 — Phase 3C).
 */
import type { BilibiliPack } from '../../types/legacy/bilibili';
import type { VersionModalViewModel, ReleaseItemViewModel, DownloadItemViewModel } from '../../modals/version/types';
import { getVPanClass } from '../../utils/format';

export function adaptBilibiliToVersionModal(
  pack?: Partial<BilibiliPack> | null,
  extra?: Record<string, unknown>
): VersionModalViewModel {
  const p = pack || {};
  const bvid = p.bvid || p.id || (extra?.id as string) || '';
  const mcVer = p.mc_version || '';
  const mcVersList = p.all_versions && p.all_versions.length ? p.all_versions : (mcVer ? [mcVer] : ((extra?.mcVersList as string[]) || []));

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const downloads: DownloadItemViewModel[] = (((p.download_links || extra?.download_links || []) as any[])).map((dl) => ({
    name: dl.name || dl.type || '网盘直达',
    url: dl.url || '',
    panClass: getVPanClass(dl.type || dl.name),
    code: dl.code,
  }));

  const singleRelease: ReleaseItemViewModel = {
    versionId: bvid,
    versionName: p.mc_version ? `MC ${p.mc_version}` : '自制发布版',
    date: p.pub_time || (extra?.date as string) || '',
    changelogMd: p.desc || (extra?.desc as string) || 'UP主未在简介中注明详细版本变更。',
    loaders: p.loaders || (extra?.loaders as string[]) || [],
    gameVersions: mcVersList,
    downloads,
  };

  return {
    platform: 'bilibili',
    id: bvid,
    title: (extra?.title as string) || p.title || '哔哩哔哩整合包',
    platformName: '哔哩哔哩自制',
    siteShort: '哔哩哔哩',
    latestVersion: (extra?.ver as string) || p.mc_version || '最新发布',
    lastUpdated: (extra?.date as string) || p.pub_time || '近期发布',
    dateCreated: (extra?.date_created as string) || p.pub_time || undefined,
    versionCount: (extra?.count as number) || 1,
    mcVersionsSummary: mcVersList.join(', ') || '未指定',
    mcVersionsList: mcVersList,
    typeName: 'B站自制整合',
    targetUrl: `https://www.bilibili.com/video/${bvid}`,
    hasServer: Boolean(p.has_server || extra?.has_server),
    serverStatus: (p.has_server || extra?.has_server) ? 'supported' : 'unknown',
    envDisplay: (p.has_server || extra?.has_server) ? '有服务端运行线索' : '未知（本地数据未提供）',
    hasGroupVersion: Boolean(p.has_group_version || extra?.has_group_version),
    groupVersionNote: p.group_version_note || (extra?.group_version_note as string),
    qqGroup: p.qq_group || (extra?.qq_group as string),
    releases: [singleRelease],
  };
}

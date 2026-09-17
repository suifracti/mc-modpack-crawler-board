/**
 * XYEBBS Version Modal Adapter (Architecture V2 — Phase 3C).
 */
import type { XyebbsPack } from '../../types/legacy/xyebbs';
import type {
  VersionModalViewModel,
  ReleaseItemViewModel,
  DownloadItemViewModel,
} from '../../modals/version/types';
import { getVPanClass } from '../../utils/format';

export function adaptXyebbsToVersionModal(
  pack?: Partial<XyebbsPack> | null,
  extra?: Record<string, unknown>
): VersionModalViewModel {
  const p = pack || {};
  const id = p.id || (p as any).project_id || (extra?.id as string) || '';
  const releasesList = p.releases || (extra?.releases_data as any[]) || [];
  const targetUrl = p.url || (extra?.url as string) || `https://xyebbs.com/thread-${id}-1-1.html`;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const releases: ReleaseItemViewModel[] = releasesList.map((r: any) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const downloads: DownloadItemViewModel[] = (r.links || []).map((l: any) => {
      const lType = (l.type || l.linkType || '').toUpperCase();
      const defaultName =
        lType === 'QUARK'
          ? '夸克网盘'
          : lType === 'BAIDU'
          ? '百度网盘'
          : lType.includes('123')
          ? '123云盘'
          : lType === 'LANZOU'
          ? '蓝奏云'
          : lType === 'XUNLEI'
          ? '迅雷云盘'
          : '极速下载';

      return {
        name: (l.name || defaultName).trim(),
        url: l.url || '',
        panClass: getVPanClass(l.type || l.linkType || l.name),
        code: l.code || l.info,
      };
    });

    return {
      versionId: String(r.id || r.label || ''),
      versionName: r.label || r.name || 'Release',
      date: r.createDate ? String(r.createDate).substring(0, 10) : undefined,
      changelogMd: r.notes || '该版本未提供更新日志说明。',
      downloads,
    };
  });

  const mcVersList = p.all_versions || (p.mc_version ? [p.mc_version] : ((extra?.mcVersList as string[]) || []));

  return {
    platform: 'xyebbs',
    id,
    title: (extra?.title as string) || p.title || 'XYEBBS 整合包',
    platformName: 'XYEBBS社区',
    siteShort: 'XYEBBS',
    latestVersion: (extra?.ver as string) || p.mc_version || '最新版本',
    lastUpdated: (extra?.date as string) || p.modified_date || p.created_date || '暂无记录',
    dateCreated: p.created_date || undefined,
    versionCount: releasesList.length || 1,
    mcVersionsSummary: mcVersList.join(', ') || '未指定',
    mcVersionsList: mcVersList,
    typeName: 'XYEBBS社区整合',
    targetUrl,
    hasServer: Boolean(p.has_server || extra?.has_server),
    envDisplay: (p.has_server || extra?.has_server) ? '支持联机开服 / 提供专用服务端' : '未提供专用开服端',
    releases,
  };
}

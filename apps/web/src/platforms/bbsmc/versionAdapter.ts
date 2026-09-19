/**
 * BBSMC Version Modal Adapter (Architecture V2 — Phase 3C).
 */
import type { BbsmcPack } from '../../types/legacy/bbsmc';
import type {
  VersionModalViewModel,
  ReleaseItemViewModel,
  DownloadItemViewModel,
} from '../../modals/version/types';
import { formatVFileSize } from '../../utils/format';

export function adaptBbsmcToVersionModal(
  pack?: Partial<BbsmcPack> | null,
  extra?: Record<string, unknown>
): VersionModalViewModel {
  const p = pack || {};
  const id = p.id || (p as any).project_id || (extra?.id as string) || '';
  const versions = p.versions || (extra?.versions_data as any[]) || [];
  const targetUrl = p.url || (extra?.url as string) || `https://bbsmc.net/modpack/${id}`;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const releases: ReleaseItemViewModel[] = versions.map((v: any) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const downloads: DownloadItemViewModel[] = (v.files || []).map((f: any) => ({
      name: f.filename || '下载整合包',
      url: f.url || '',
      panClass: 'pan-btn-other',
      sizeStr: formatVFileSize(f.size),
      isOfficial: true,
    }));

    return {
      versionId: v.id || v.version_number || '',
      versionName: v.name || (v.version_number ? `版本 ${v.version_number}` : 'Release'),
      date: v.date_published ? String(v.date_published).substring(0, 10) : undefined,
      changelogMd: v.changelog || '该版本未提供更新日志说明。',
      loaders: v.loaders || [],
      gameVersions: v.game_versions || [],
      downloads,
    };
  });

  const mcVersList = p.all_versions || (p.mc_version ? [p.mc_version] : ((extra?.mcVersList as string[]) || []));

  return {
    platform: 'bbsmc',
    id,
    title: (extra?.title as string) || p.title || 'BBSMC 整合包',
    platformName: 'BBSMC开放资源',
    siteShort: 'BBSMC',
    latestVersion: (extra?.ver as string) || p.mc_version || '最新版本',
    lastUpdated: (extra?.date as string) || p.modified_date || p.created_date || '暂无记录',
    dateCreated: p.created_date || undefined,
    versionCount: versions.length || 1,
    mcVersionsSummary: mcVersList.join(', ') || '未指定',
    mcVersionsList: mcVersList,
    typeName: 'BBSMC社区模组包',
    targetUrl,
    hasServer: Boolean(p.has_server || extra?.has_server),
    serverStatus: (p.has_server || extra?.has_server) ? 'supported' : 'unknown',
    envDisplay: (p.has_server || extra?.has_server) ? '支持联机开服 / 提供专用服务端' : '未声明服务端支持 / 无法确认',
    releases,
  };
}

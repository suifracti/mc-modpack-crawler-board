/**
 * Modrinth Version Modal Adapter (Architecture V2 — Phase 3C).
 */
import type { ModrinthPack } from '../../types/legacy/modrinth';
import type {
  VersionModalViewModel,
  ReleaseItemViewModel,
  DownloadItemViewModel,
} from '../../modals/version/types';
import { formatVFileSize } from '../../utils/format';

export function adaptModrinthToVersionModal(
  pack?: Partial<ModrinthPack> | null,
  extra?: Record<string, unknown>
): VersionModalViewModel {
  const p = pack || {};
  const slug = p.slug || p.id || (p as any).project_id || (extra?.id as string) || '';
  const versionsList = p.versions || (extra?.versions_data as any[]) || [];
  const targetUrl = p.url || (extra?.url as string) || `https://modrinth.com/modpack/${slug}`;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const releases: ReleaseItemViewModel[] = versionsList.map((v: any) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const downloads: DownloadItemViewModel[] = (v.files || []).map((f: any) => ({
      name: f.filename || '下载 mrpack',
      url: f.url || '',
      panClass: 'pan-btn-modrinth',
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
    platform: 'modrinth',
    id: slug,
    title: (extra?.title as string) || p.title || 'Modrinth 模组包',
    platformName: 'Modrinth国际服',
    siteShort: 'Modrinth',
    latestVersion: (extra?.ver as string) || p.mc_version || '最新版本',
    lastUpdated: (extra?.date as string) || p.date_modified || '暂无记录',
    dateCreated: p.date_created || undefined,
    versionCount: versionsList.length || 1,
    mcVersionsSummary: mcVersList.join(', ') || '未指定',
    mcVersionsList: mcVersList,
    typeName: 'Modrinth国际模组包',
    targetUrl,
    hasServer: Boolean(p.has_server || extra?.has_server || (p as any).server_side === 'required' || (p as any).server_side === 'optional'),
    serverStatus: ((p as any).server_side === 'required' || (p as any).server_side === 'optional' || (p as any).server_side === 'unsupported' ? (p as any).server_side : (p.has_server || extra?.has_server ? 'supported' : 'unknown')),
    envDisplay: ((p as any).server_side === 'required' || (p as any).server_side === 'optional' || p.has_server || extra?.has_server)
      ? '支持联机开服 / 提供专用服务端'
      : ((p as any).server_side === 'unsupported' ? '明确不支持开服 / 仅客户端运行' : '未声明服务端支持 / 无法确认'),
    releases,
  };
}

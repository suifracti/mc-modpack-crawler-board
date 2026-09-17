/**
 * CurseForge Version Modal Adapter (Architecture V2 — Phase 3C).
 */
import type { CurseforgePack } from '../../types/legacy/curseforge';
import type {
  VersionModalViewModel,
  ReleaseItemViewModel,
  DownloadItemViewModel,
} from '../../modals/version/types';
import { formatVFileSize } from '../../utils/format';

export function adaptCurseforgeToVersionModal(
  pack?: Partial<CurseforgePack> | null,
  extra?: Record<string, unknown>
): VersionModalViewModel {
  const p = pack || {};
  const slug = p.slug || String(p.id || (p as any).project_id || (extra?.id as string) || '');
  const filesList = ((p as unknown as { files?: Array<Record<string, unknown>> }).files || (extra?.files as any[]) || []);
  const targetUrl = p.url || (extra?.url as string) || `https://www.curseforge.com/minecraft/modpacks/${slug}`;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const releases: ReleaseItemViewModel[] = filesList.map((f: any) => {
    const dls: DownloadItemViewModel[] = f.downloadUrl
      ? [
          {
            name: (f.fileName as string) || (f.displayName as string) || '下载 zip',
            url: f.downloadUrl as string,
            panClass: 'pan-btn-curseforge',
            sizeStr: formatVFileSize(f.fileLength as number),
            isOfficial: true,
          },
        ]
      : [];

    return {
      versionId: String(f.id || ''),
      versionName: (f.displayName as string) || (f.fileName as string) || 'Release',
      date: f.fileDate ? String(f.fileDate).substring(0, 10) : undefined,
      gameVersions: (f.gameVersions as string[]) || [],
      downloads: dls,
    };
  });

  const mcVersList = p.all_versions || (p.mc_version ? [p.mc_version] : ((extra?.mcVersList as string[]) || []));

  return {
    platform: 'curseforge',
    id: slug,
    title: (extra?.title as string) || p.title || 'CurseForge 模组包',
    platformName: 'CurseForge全球服',
    siteShort: 'CurseForge',
    latestVersion: (extra?.ver as string) || p.mc_version || '最新版本',
    lastUpdated: (extra?.date as string) || p.date_modified || '暂无记录',
    dateCreated: p.date_created || undefined,
    versionCount: filesList.length || 1,
    mcVersionsSummary: mcVersList.join(', ') || '未指定',
    mcVersionsList: mcVersList,
    typeName: 'CurseForge全球模组包',
    targetUrl,
    hasServer: Boolean(p.has_server || extra?.has_server),
    serverStatus: (p.has_server || extra?.has_server) ? 'supported' : 'unknown',
    envDisplay: (p.has_server || extra?.has_server) ? '支持联机开服 / 提供专用服务端' : '未声明服务端支持 / 无法确认',
    releases,
  };
}

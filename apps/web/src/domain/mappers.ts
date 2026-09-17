/**
 * Pure mappers converting Legacy Sidecar DTOs into Unified Domain Models.
 */
import type {
  McmodPack,
  BilibiliPack,
  BbsmcPack,
  XyebbsPack,
  ModrinthPack,
  CurseforgePack,
  ReleaseItem,
  DownloadLink,
} from './types';
import type { LegacyMcmodRow } from '../types/legacy/mcmod';
import type { LegacyBilibiliItem } from '../types/legacy/bilibili';
import type { LegacyBbsmcItem } from '../types/legacy/bbsmc';
import type { LegacyXyebbsItem } from '../types/legacy/xyebbs';
import type { LegacyModrinthItem } from '../types/legacy/modrinth';
import type { LegacyCurseforgeItem } from '../types/legacy/curseforge';

export function mapLegacyMcmodToPack(dto: LegacyMcmodRow): McmodPack {
  return {
    id: `mcmod:${dto.mid}`,
    platform: 'mcmod',
    sourceId: String(dto.mid),
    mid: dto.mid,
    title: dto.title || '',
    author: '',
    url: `https://www.mcmod.cn/modpack/${dto.mid}.html`,
    hasServer: Boolean(dto.has_server),
    coverUrl: dto.cover_url,
    views: dto.views_n || 0,
    score: dto.score_n || 0,
    mcVersions: dto.mc_versions || (dto.mc_version ? [dto.mc_version] : []),
    loaders: [],
    categories: dto.category_search ? dto.category_search.split(',').map((s) => s.trim()).filter(Boolean) : [],
  };
}

export function mapLegacyBilibiliToPack(dto: LegacyBilibiliItem): BilibiliPack {
  const downloadLinks: DownloadLink[] = (dto.download_links || []).map((dl) => ({
    panName: dl.pan_name,
    url: dl.url,
    extractCode: dl.extract_code,
    note: dl.note,
    sizeBytes: dl.size_bytes,
  }));

  const releases: ReleaseItem[] = (dto.releases || []).map((r) => ({
    versionId: r.version_id,
    versionNumber: r.version_number,
    releaseDate: r.release_date || r.announced_at,
    mcVersions: r.mc_versions || [],
    loaders: r.loaders || [],
    downloadLinks: (r.download_links || []).map((dl) => ({
      panName: dl.pan_name,
      url: dl.url,
      extractCode: dl.extract_code,
      note: dl.note,
      sizeBytes: dl.size_bytes,
    })),
    changelog: r.changelog,
  }));

  return {
    id: `bilibili:${dto.bvid}`,
    platform: 'bilibili',
    sourceId: dto.bvid,
    bvid: dto.bvid,
    title: dto.title,
    author: dto.author,
    url: dto.url,
    hasServer: Boolean(dto.has_server),
    coverUrl: dto.cover,
    views: dto.views || 0,
    danmaku: dto.danmaku || 0,
    likes: dto.likes || 0,
    pinnedComment: dto.pinned_comment,
    qqGroup: dto.qq_group,
    extractCode: dto.extract_code,
    downloadLinks,
    releases,
    mcVersions: [],
    loaders: [],
    categories: [],
    updatedAt: dto.update_notice_at || dto.published_at,
  };
}

export function mapLegacyBbsmcToPack(dto: LegacyBbsmcItem): BbsmcPack {
  const releases: ReleaseItem[] = (dto.releases || []).map((r) => ({
    versionId: r.version_id || r.version_number,
    versionNumber: r.version_number,
    releaseDate: r.release_date,
    mcVersions: r.mc_versions || [],
    loaders: r.loaders || [],
    downloadLinks: (r.download_links || []).map((dl) => ({
      panName: dl.pan_name,
      url: dl.url,
      extractCode: dl.extract_code,
    })),
    changelog: r.changelog,
  }));

  return {
    id: `bbsmc:${dto.project_id}`,
    platform: 'bbsmc',
    sourceId: String(dto.project_id),
    projectId: dto.project_id,
    title: dto.title,
    author: dto.author,
    url: dto.url,
    hasServer: Boolean(dto.has_server),
    coverUrl: dto.cover,
    downloads: dto.downloads || 0,
    replies: dto.replies || 0,
    views: dto.views || 0,
    mcVersions: dto.mc_versions || [],
    loaders: dto.loaders || [],
    categories: dto.categories || [],
    releases,
  };
}

export function mapLegacyXyebbsToPack(dto: LegacyXyebbsItem): XyebbsPack {
  const releases: ReleaseItem[] = (dto.releases || []).map((r) => ({
    versionId: r.version_id || r.version_number,
    versionNumber: r.version_number,
    releaseDate: r.release_date,
    mcVersions: r.mc_versions || [],
    loaders: r.loaders || [],
    downloadLinks: (r.download_links || []).map((dl) => ({
      panName: dl.pan_name,
      url: dl.url,
      extractCode: dl.extract_code,
    })),
    changelog: r.changelog,
  }));

  return {
    id: `xyebbs:${dto.project_id}`,
    platform: 'xyebbs',
    sourceId: String(dto.project_id),
    projectId: dto.project_id,
    title: dto.title,
    author: dto.author,
    url: dto.url,
    hasServer: Boolean(dto.has_server),
    coverUrl: dto.cover,
    downloads: dto.downloads || 0,
    replies: dto.replies || 0,
    views: dto.views || 0,
    mcVersions: dto.mc_versions || [],
    loaders: dto.loaders || [],
    categories: dto.categories || [],
    releases,
  };
}

export function mapLegacyModrinthToPack(dto: LegacyModrinthItem): ModrinthPack {
  const releases: ReleaseItem[] = (dto.releases || []).map((r) => ({
    versionId: r.version_id || r.version_number,
    versionNumber: r.version_number,
    releaseDate: r.release_date,
    mcVersions: r.mc_versions || [],
    loaders: r.loaders || [],
    downloads: r.downloads,
    downloadLinks: (r.files || []).map((f) => ({
      panName: 'Official',
      url: f.url,
      note: f.filename,
      sizeBytes: f.size,
    })),
    changelog: r.changelog,
  }));

  return {
    id: `modrinth:${dto.project_id}`,
    platform: 'modrinth',
    sourceId: dto.project_id,
    projectId: dto.project_id,
    slug: dto.slug || dto.project_id,
    title: dto.title,
    author: dto.author,
    url: dto.url,
    hasServer: Boolean(dto.has_server),
    coverUrl: dto.icon_url,
    iconUrl: dto.icon_url,
    downloads: dto.downloads || 0,
    followers: dto.followers || 0,
    clientSide: dto.client_side || 'unknown',
    serverSide: dto.server_side || 'unknown',
    mcVersions: dto.mc_versions || [],
    loaders: dto.loaders || [],
    categories: dto.categories || [],
    releases,
  };
}

export function mapLegacyCurseforgeToPack(dto: LegacyCurseforgeItem): CurseforgePack {
  const releases: ReleaseItem[] = (dto.releases || []).map((r) => ({
    versionId: r.version_id || r.version_number,
    versionNumber: r.version_number,
    releaseDate: r.release_date,
    mcVersions: r.mc_versions || [],
    loaders: r.loaders || [],
    downloads: r.downloads,
    downloadLinks: (r.files || []).map((f) => ({
      panName: 'CurseForge File',
      url: f.url,
      note: f.filename,
      sizeBytes: f.size,
    })),
    changelog: r.changelog,
  }));

  return {
    id: `curseforge:${dto.project_id}`,
    platform: 'curseforge',
    sourceId: String(dto.project_id),
    projectId: dto.project_id,
    slug: dto.slug || String(dto.project_id),
    title: dto.title,
    author: dto.author,
    url: dto.url,
    hasServer: Boolean(dto.has_server),
    coverUrl: dto.logo_url,
    logoUrl: dto.logo_url,
    downloads: dto.downloads || 0,
    mcVersions: dto.mc_versions || [],
    loaders: dto.loaders || [],
    categories: dto.categories || [],
    releases,
  };
}

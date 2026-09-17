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
  EnvironmentClaim,
} from './types';
import type { LegacyMcmodRow } from '../types/legacy/mcmod';
import type { LegacyBilibiliItem } from '../types/legacy/bilibili';
import type { LegacyBbsmcItem } from '../types/legacy/bbsmc';
import type { LegacyXyebbsItem } from '../types/legacy/xyebbs';
import type { LegacyModrinthItem } from '../types/legacy/modrinth';
import type { LegacyCurseforgeItem } from '../types/legacy/curseforge';

export function mapLegacyMcmodToPack(dto: LegacyMcmodRow): McmodPack {
  const hasServer = Boolean(dto.has_server);
  const claims: EnvironmentClaim[] = [
    {
      side: 'server',
      status: hasServer ? 'supported' : 'unknown',
      certainty: hasServer ? 'inferred' : 'unknown',
      evidenceType: hasServer ? 'text_rule' : 'no_evidence',
      evidenceText: hasServer ? 'MC百科文本推断' : null,
      sourceField: hasServer ? 'description' : null,
      rawValue: null,
    },
    {
      side: 'client',
      status: 'unknown',
      certainty: 'unknown',
      evidenceType: 'no_evidence',
      evidenceText: null,
      sourceField: null,
      rawValue: null,
    },
  ];

  return {
    id: `mcmod:${dto.mid}`,
    platform: 'mcmod',
    sourceId: String(dto.mid),
    mid: dto.mid,
    title: dto.title || '',
    chineseName: dto.title || '',
    englishName: '',
    formerTitles: [],
    typeName: (dto.type_name as string) || '原生整合',
    author: '',
    url: `https://www.mcmod.cn/modpack/${dto.mid}.html`,
    hasServer,
    environmentClaims: claims,
    serverClaim: claims[0],
    clientClaim: claims[1],
    coverUrl: dto.cover_url,
    views: dto.views_n || 0,
    score: dto.score_n || 0,
    recommendations: 0,
    favorites: 0,
    commentsCount: 0,
    votes: { redVotes: 0, blackVotes: 0, redPercent: 50, blackPercent: 50 },
    trendStats: { lat: 0, max: 0, avg: 0, days: 0, t7: 0, t30: 0, t60: 0, tall: 0, score: dto.score_n || 0 },
    tags: [],
    categories: dto.category_search ? dto.category_search.split(',').map((s) => s.trim()).filter(Boolean) : [],
    mcVersions: dto.mc_versions || (dto.mc_version ? [dto.mc_version] : []),
    loaders: [],
    includedModsCount: 0,
    includedModGroups: [],
    trendPoints: [],
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

  const hasServer = Boolean(dto.has_server);
  const claims: EnvironmentClaim[] = [
    {
      side: 'server',
      status: hasServer ? 'supported' : 'unknown',
      certainty: hasServer ? 'inferred' : 'unknown',
      evidenceType: hasServer ? 'text_rule' : 'no_evidence',
      evidenceText: hasServer ? 'Bilibili 文本规则推断' : null,
      sourceField: hasServer ? 'description' : null,
      rawValue: null,
    },
    {
      side: 'client',
      status: 'unknown',
      certainty: 'unknown',
      evidenceType: 'no_evidence',
      evidenceText: null,
      sourceField: null,
      rawValue: null,
    },
  ];

  return {
    id: `bilibili:${dto.bvid}`,
    platform: 'bilibili',
    sourceId: dto.bvid,
    bvid: dto.bvid,
    title: dto.title,
    author: dto.author,
    url: dto.url,
    hasServer,
    environmentClaims: claims,
    serverClaim: claims[0],
    clientClaim: claims[1],
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

  const hasServer = Boolean(dto.has_server);
  const claims: EnvironmentClaim[] = [
    {
      side: 'server',
      status: hasServer ? 'supported' : 'unknown',
      certainty: hasServer ? 'strong_inferred' : 'unknown',
      evidenceType: hasServer ? 'file_name' : 'no_evidence',
      evidenceText: hasServer ? 'BBSMC 附件文件名推断' : null,
      sourceField: hasServer ? 'download_links[].filename' : null,
      rawValue: null,
    },
    {
      side: 'client',
      status: 'unknown',
      certainty: 'unknown',
      evidenceType: 'no_evidence',
      evidenceText: null,
      sourceField: null,
      rawValue: null,
    },
  ];

  return {
    id: `bbsmc:${dto.project_id}`,
    platform: 'bbsmc',
    sourceId: String(dto.project_id),
    projectId: dto.project_id,
    title: dto.title,
    author: dto.author,
    url: dto.url,
    hasServer,
    environmentClaims: claims,
    serverClaim: claims[0],
    clientClaim: claims[1],
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

  const hasServer = Boolean(dto.has_server);
  const claims: EnvironmentClaim[] = [
    {
      side: 'server',
      status: hasServer ? 'supported' : 'unknown',
      certainty: hasServer ? 'inferred' : 'unknown',
      evidenceType: hasServer ? 'text_rule' : 'no_evidence',
      evidenceText: hasServer ? 'XYEBBS 文本推断' : null,
      sourceField: hasServer ? 'description' : null,
      rawValue: null,
    },
    {
      side: 'client',
      status: 'unknown',
      certainty: 'unknown',
      evidenceType: 'no_evidence',
      evidenceText: null,
      sourceField: null,
      rawValue: null,
    },
  ];

  return {
    id: `xyebbs:${dto.project_id}`,
    platform: 'xyebbs',
    sourceId: String(dto.project_id),
    projectId: dto.project_id,
    title: dto.title,
    author: dto.author,
    url: dto.url,
    hasServer,
    environmentClaims: claims,
    serverClaim: claims[0],
    clientClaim: claims[1],
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

  function parseModrinthEnvStatus(val?: string): 'required' | 'optional' | 'unsupported' | 'unknown' {
    if (val === 'required') return 'required';
    if (val === 'optional') return 'optional';
    if (val === 'unsupported') return 'unsupported';
    return 'unknown';
  }

  const hasServer = Boolean(dto.has_server);
  const serverStatus = parseModrinthEnvStatus(dto.server_side);
  const clientStatus = parseModrinthEnvStatus(dto.client_side);

  const claims: EnvironmentClaim[] = [
    {
      side: 'server',
      status: serverStatus,
      certainty: serverStatus !== 'unknown' ? 'confirmed' : 'unknown',
      evidenceType: serverStatus !== 'unknown' ? 'platform_field' : 'no_evidence',
      evidenceText: serverStatus !== 'unknown' ? `Modrinth 官方 API 字段: server_side=${dto.server_side}` : null,
      sourceField: serverStatus !== 'unknown' ? 'source_meta.server_side' : null,
      rawValue: dto.server_side ?? null,
    },
    {
      side: 'client',
      status: clientStatus,
      certainty: clientStatus !== 'unknown' ? 'confirmed' : 'unknown',
      evidenceType: clientStatus !== 'unknown' ? 'platform_field' : 'no_evidence',
      evidenceText: clientStatus !== 'unknown' ? `Modrinth 官方 API 字段: client_side=${dto.client_side}` : null,
      sourceField: clientStatus !== 'unknown' ? 'source_meta.client_side' : null,
      rawValue: dto.client_side ?? null,
    },
  ];

  return {
    id: `modrinth:${dto.project_id}`,
    platform: 'modrinth',
    sourceId: dto.project_id,
    projectId: dto.project_id,
    slug: dto.slug || dto.project_id,
    title: dto.title,
    author: dto.author,
    url: dto.url,
    hasServer,
    environmentClaims: claims,
    serverClaim: claims[0],
    clientClaim: claims[1],
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

  const hasServer = Boolean(dto.has_server);
  const claims: EnvironmentClaim[] = [
    {
      side: 'server',
      status: hasServer ? 'supported' : 'unknown',
      certainty: hasServer ? 'inferred' : 'unknown',
      evidenceType: hasServer ? 'platform_field' : 'no_evidence',
      evidenceText: hasServer ? 'CurseForge legacy server flag' : null,
      sourceField: hasServer ? 'has_server' : null,
      rawValue: null,
    },
    {
      side: 'client',
      status: 'unknown',
      certainty: 'unknown',
      evidenceType: 'no_evidence',
      evidenceText: null,
      sourceField: null,
      rawValue: null,
    },
  ];

  return {
    id: `curseforge:${dto.project_id}`,
    platform: 'curseforge',
    sourceId: String(dto.project_id),
    projectId: dto.project_id,
    slug: dto.slug || String(dto.project_id),
    title: dto.title,
    author: dto.author,
    url: dto.url,
    hasServer,
    environmentClaims: claims,
    serverClaim: claims[0],
    clientClaim: claims[1],
    coverUrl: dto.logo_url,
    logoUrl: dto.logo_url,
    downloads: dto.downloads || 0,
    mcVersions: dto.mc_versions || [],
    loaders: dto.loaders || [],
    categories: dto.categories || [],
    releases,
  };
}

/**
 * Architecture V2 - Frontend Domain Types.
 * Strictly typed representation of Modpacks, Releases, Environment, and Metrics.
 */

export type Platform =
  | 'mcmod'
  | 'bilibili'
  | 'bbsmc'
  | 'xyebbs'
  | 'modrinth'
  | 'curseforge';

export type EnvironmentStatus =
  | 'required'
  | 'optional'
  | 'unsupported'
  | 'unknown'
  | 'both';

export type EnvironmentCertainty =
  | 'confirmed'
  | 'inferred'
  | 'unknown';

export interface EnvironmentClaim {
  side: 'client' | 'server';
  status: EnvironmentStatus;
  certainty: EnvironmentCertainty;
  evidenceType?: string;
  sourceField?: string;
  rawDeclaration?: string;
}

export interface DownloadLink {
  panName: string;
  url: string;
  extractCode?: string;
  note?: string;
  sizeBytes?: number;
}

export interface ReleaseItem {
  versionId: string;
  versionNumber: string;
  releaseDate?: string;
  mcVersions: string[];
  loaders: string[];
  downloads?: number;
  downloadLinks: DownloadLink[];
  changelog?: string;
}

export interface BasePack {
  id: string;
  platform: Platform;
  sourceId: string;
  title: string;
  author: string;
  url: string;
  hasServer: boolean;
  coverUrl?: string;
  summary?: string;
  mcVersions: string[];
  loaders: string[];
  categories: string[];
  updatedAt?: string;
}

export interface McmodPack extends BasePack {
  platform: 'mcmod';
  mid: number;
  views: number;
  score: number;
  recommendScore?: number;
  commentsCount?: number;
  hasServer: boolean;
}

export interface BilibiliPack extends BasePack {
  platform: 'bilibili';
  bvid: string;
  views: number;
  danmaku: number;
  likes: number;
  pinnedComment?: string;
  qqGroup?: string;
  extractCode?: string;
  downloadLinks: DownloadLink[];
  releases: ReleaseItem[];
}

export interface BbsmcPack extends BasePack {
  platform: 'bbsmc';
  projectId: number;
  downloads: number;
  replies: number;
  views: number;
  releases: ReleaseItem[];
}

export interface XyebbsPack extends BasePack {
  platform: 'xyebbs';
  projectId: number;
  downloads: number;
  replies: number;
  views: number;
  releases: ReleaseItem[];
}

export interface ModrinthPack extends BasePack {
  platform: 'modrinth';
  projectId: string;
  slug: string;
  downloads: number;
  followers: number;
  iconUrl?: string;
  clientSide: string;
  serverSide: string;
  releases: ReleaseItem[];
}

export interface CurseforgePack extends BasePack {
  platform: 'curseforge';
  projectId: number;
  slug: string;
  downloads: number;
  logoUrl?: string;
  releases: ReleaseItem[];
}

export type PlatformPack =
  | McmodPack
  | BilibiliPack
  | BbsmcPack
  | XyebbsPack
  | ModrinthPack
  | CurseforgePack;

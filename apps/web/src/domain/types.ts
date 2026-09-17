/**
 * Architecture V2 - Frontend Domain Types.
 * Strictly typed representation of Modpacks, Releases, Environment Claims, and Metrics.
 */

export type Platform =
  | 'mcmod'
  | 'bilibili'
  | 'bbsmc'
  | 'xyebbs'
  | 'modrinth'
  | 'curseforge';

export type EnvironmentSide = 'client' | 'server';

export type EnvironmentStatus =
  | 'required'
  | 'optional'
  | 'supported'
  | 'unsupported'
  | 'unknown';

export type EnvironmentCertainty =
  | 'confirmed'
  | 'strong_inferred'
  | 'inferred'
  | 'weak_inferred'
  | 'unknown';

export interface EnvironmentClaim {
  side: EnvironmentSide;
  status: EnvironmentStatus;
  certainty: EnvironmentCertainty;
  evidenceType?: string | null;
  evidenceText?: string | null;
  sourceField?: string | null;
  rawValue?: string | null;
}

/**
 * Pure compatibility helper to derive legacy boolean has_server from structured claims.
 * Status 'supported', 'required', or 'optional' translates to true.
 */
export function deriveLegacyHasServer(claims: EnvironmentClaim[] | null | undefined): boolean {
  if (!claims || !claims.length) return false;
  const serverClaim = claims.find((c) => c.side === 'server');
  if (!serverClaim) return false;
  return (
    serverClaim.status === 'supported' ||
    serverClaim.status === 'required' ||
    serverClaim.status === 'optional'
  );
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
  environmentClaims: EnvironmentClaim[];
  serverClaim?: EnvironmentClaim | null;
  clientClaim?: EnvironmentClaim | null;
  hasServer: boolean; // Derived compatibility attribute
  coverUrl?: string;
  summary?: string;
  mcVersions: string[];
  loaders: string[];
  categories: string[];
  updatedAt?: string;
}

export interface McmodTrendStats {
  lat: number;
  max: number;
  avg: number;
  days: number;
  t7: number;
  t30: number;
  t60: number;
  tall: number;
  score: number;
  trendValsStr?: string;
  trendDatesStr?: string;
}

export interface McmodVotes {
  redVotes: number;
  blackVotes: number;
  redPercent: number;
  blackPercent: number;
}

export interface McmodModItem {
  name: string;
  title: string;
  version?: string;
  url: string;
  classId?: string;
}

export interface McmodModGroup {
  categoryKey: string;
  categoryName: string;
  categoryUrl?: string;
  mods: McmodModItem[];
}

export interface McmodTrendPoint {
  date: string;
  viewsDelta: number;
}

export interface McmodPack extends BasePack {
  platform: 'mcmod';
  mid: number;
  chineseName: string;
  englishName: string;
  formerTitles: string[];
  typeName: string;
  moldId?: string;
  views: number;
  score: number;
  trendStats: McmodTrendStats;
  votes: McmodVotes;
  recommendations: number;
  favorites: number;
  commentsCount: number;
  tags: string[];
  includedModsCount: number;
  includedModGroups: McmodModGroup[];
  trendPoints: McmodTrendPoint[];
  tagsSearch?: string;
  categorySearch?: string;
  modsSearch?: string;
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
  | BBSMCPack
  | XYEBBSPack
  | ModrinthPack
  | CurseforgePack;

export type BBSMCPack = BbsmcPack;
export type XYEBBSPack = XyebbsPack;

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

export type EnvironmentEvidenceType =
  | 'platform_field'
  | 'file_name'
  | 'text_rule'
  | 'no_evidence';

export type EnvironmentPresentationConfidence =
  | 'high'
  | 'medium'
  | 'low'
  | 'unknown';

export interface EnvironmentClaim {
  side: EnvironmentSide;
  status: EnvironmentStatus;
  certainty: EnvironmentCertainty;
  evidenceType: EnvironmentEvidenceType;
  evidenceText: string | null;
  sourceField: string | null;
  rawValue: unknown | null;
}

const CERTAINTY_PRIORITY: Record<EnvironmentCertainty, number> = {
  confirmed: 5,
  strong_inferred: 4,
  inferred: 3,
  weak_inferred: 2,
  unknown: 1,
};

/**
 * Deterministically resolves the primary claim for a given side based on canonical certainty precedence:
 * confirmed > strong_inferred > inferred > weak_inferred > unknown.
 */
export function resolvePrimaryClaim(
  claims: EnvironmentClaim[] | null | undefined,
  side: EnvironmentSide
): EnvironmentClaim | null {
  if (!claims || !claims.length) return null;
  const sideClaims = claims.filter((c) => c.side === side);
  if (!sideClaims.length) return null;
  if (sideClaims.length === 1) return sideClaims[0];

  return [...sideClaims].sort(
    (a, b) => (CERTAINTY_PRIORITY[b.certainty] ?? 0) - (CERTAINTY_PRIORITY[a.certainty] ?? 0)
  )[0];
}

/**
 * Pure compatibility helper to derive legacy boolean has_server from structured claims.
 * Status 'supported', 'required', or 'optional' translates to true.
 * 'unsupported', 'unknown', or missing claim translates to false.
 */
export function deriveLegacyHasServer(claims?: EnvironmentClaim[] | null): boolean {
  const serverClaim = resolvePrimaryClaim(claims, 'server');
  if (!serverClaim) return false;
  return (
    serverClaim.status === 'required' ||
    serverClaim.status === 'optional' ||
    serverClaim.status === 'supported'
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
  score?: number | null;
  history7d?: number[];
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
  score?: number | null;
  trendStats: McmodTrendStats;
  votes: McmodVotes;
  recommendations: number;
  favorites: number;
  commentsCount: number;
  tags: string[];
  includedModsCount: number;
  includedModGroups: McmodModGroup[];
  trendPoints?: McmodTrendPoint[];
  tagsSearch?: string;
  categorySearch?: string;
  /**
   * Structured mod-name provenance for Match Reason (Phase 3G-D.1).
   * Exact canonical `included_mods.mod_name` values, never reverse-parsed
   * from a flat search string.
   */
  includedModNames?: string[];
  modSearchText?: string;
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

/**
 * MCMod Structured Data Contracts (Architecture V2 — Phase 3B).
 * Strictly typed DTO for data/mcmod_data.js.
 * ZERO HTML, ZERO c0~c6.
 */
import type {
  EnvironmentClaim,
  McmodTrendStats,
  McmodVotes,
  McmodTrendPoint,
} from '../../domain/types';

export interface McmodModCategoryItem {
  categoryKey: string;
  categoryName: string;
  categoryUrl?: string;
  count: number;
}

export interface McmodPreviewModItem {
  name: string;
  title: string;
  version?: string;
  url: string;
  classId?: string | null;
  categoryKey: string;
  categoryName: string;
}

export interface McmodStructuredItem {
  mid: number;
  title: string;
  chineseName: string;
  englishName: string;
  formerTitles: string[];
  url: string;
  author: string;
  typeName: string;
  moldId: string;
  coverUrl: string;
  views: number;
  score?: number | null;
  recommendations: number;
  favorites: number;
  commentsCount: number;
  votes: McmodVotes;
  trendStats: McmodTrendStats;
  tags: string[];
  categories: string[];
  mcVersions: string[];
  loaders: string[];
  includedModsCount: number;
  modCategories: McmodModCategoryItem[];
  previewMods: McmodPreviewModItem[];
  /**
   * Structured provenance for Match Reason (Phase 3G-D.1).
   *
   * Complete, ordered, and exactly equal to canonical `included_mods.mod_name`.
   * The flat search text used for matching is derived from this array via
   * `joinMcmodModNames()` — never the other way round.
   */
  includedModNames: string[];
  modsSearch?: string;
  modCategorySearch: string;
  trendPoints?: McmodTrendPoint[];
  environmentClaims: EnvironmentClaim[];
  has_server?: boolean;
  publishedAt?: string;
  modifiedAt?: string;
}

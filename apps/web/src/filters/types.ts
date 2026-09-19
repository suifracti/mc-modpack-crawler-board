/**
 * Filter Subsystem Types (Architecture V2 — Phase 3C).
 */

export interface CommonFilterCriteria {
  searchQuery?: string;
  version?: string;
  loader?: string;
  serverOnly?: boolean;
  activeCategories?: string[];
  activePan?: string;
  sort?: string;
}

export interface BilibiliFilterCriteria extends CommonFilterCriteria {
  activeDate?: string;
  groupMode?: 'grouped' | 'flat';
}

export interface BBSMCFilterCriteria extends CommonFilterCriteria {}

export interface XyebbsFilterCriteria extends CommonFilterCriteria {}

export interface ModrinthFilterCriteria extends CommonFilterCriteria {}

export interface CurseforgeFilterCriteria extends CommonFilterCriteria {}

export interface McmodFilterCriteria extends CommonFilterCriteria {
  searchScope?: string;
  tagFilter?: string[];
  categoryFilter?: string[];
  modFilter?: string[];
}

export type FilterPredicate<T> = (item: T, criteria: CommonFilterCriteria) => boolean;

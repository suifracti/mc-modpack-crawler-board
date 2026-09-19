/**
 * Search Subsystem Types (Architecture V2 — Phase 3C).
 */

export type SearchScope = 'all' | 'title' | 'cat' | 'desc' | 'comment' | 'basic';
export type SearchMode = 'legacy_compat' | 'advanced';

export interface ParsedSearchQuery {
  raw: string;
  normalized: string;
  terms: string[];
  negatedTerms?: string[];
  exactPhrases?: string[];
  fieldQueries?: Record<string, string>;
  scope: SearchScope;
  mode: SearchMode;
  isEmpty: boolean;
}

export interface SearchDocument {
  id: string | number;
  platform: string;
  title: string;
  titleLower: string;
  authorLower: string;
  categoriesLower: string;
  tagsLower: string;
  modsLower: string;
  descLower: string;
  commentsLower: string;
  loadersLower: string;
  versionsLower: string;
  allTextLower: string;
  formerTitlesLower?: string[];
  includedModNames?: string[];
}

export type SearchMatchField =
  | 'title'
  | 'former_title'
  | 'author'
  | 'category'
  | 'minecraft_version'
  | 'loader'
  | 'included_mod'
  | 'other';

export interface IncludedModMatchReason {
  field: 'included_mod';
  modName: string;
  matchedTerms: string[];
}

export interface SearchMatchReason {
  matched: boolean;
  fields: SearchMatchField[];
  includedMods: IncludedModMatchReason[];
  termMatches: {
    term: string;
    fields: SearchMatchField[];
  }[];
  primaryReasonLabel: string;
}

export interface SearchMatchResult {
  matches: boolean;
  score: number;
  matchedFields: string[];
  reason?: SearchMatchReason;
}


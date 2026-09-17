/**
 * Search Subsystem Types (Architecture V2 — Phase 3C).
 */

export type SearchScope = 'all' | 'title' | 'cat' | 'desc' | 'comment' | 'basic';

export interface ParsedSearchQuery {
  raw: string;
  normalized: string;
  terms: string[];
  scope: SearchScope;
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
}

export interface SearchMatchResult {
  matches: boolean;
  score: number;
  matchedFields: string[];
}

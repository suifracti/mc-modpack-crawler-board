/**
 * Query parser for search subsystem (Architecture V2 — Phase 3C).
 * Normalizes input, tokenizes query strings, and extracts search terms & scope.
 */
import type { ParsedSearchQuery, SearchScope } from './types';

export function normalizeSearchKeyword(query: string | null | undefined): string {
  if (!query) return '';
  return String(query).trim().toLowerCase();
}

export function parseSearchQuery(
  rawQuery: string | null | undefined,
  defaultScope: SearchScope = 'all'
): ParsedSearchQuery {
  const raw = rawQuery ? String(rawQuery).trim() : '';
  const normalized = raw.toLowerCase();
  if (!normalized) {
    return {
      raw,
      normalized: '',
      terms: [],
      scope: defaultScope,
      isEmpty: true,
    };
  }

  // Tokenize by whitespace
  const terms = normalized.split(/\s+/).filter(Boolean);

  return {
    raw,
    normalized,
    terms,
    scope: defaultScope,
    isEmpty: terms.length === 0,
  };
}

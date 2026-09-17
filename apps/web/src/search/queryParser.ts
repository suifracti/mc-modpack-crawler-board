/**
 * Query parser for search subsystem (Architecture V2 — Phase 3C).
 * Normalizes input, tokenizes query strings, and extracts search terms & scope.
 */
import type { ParsedSearchQuery, SearchScope, SearchMode } from './types';

export function normalizeSearchKeyword(query: string | null | undefined): string {
  if (!query) return '';
  return String(query).trim().toLowerCase();
}

export function parseSearchQuery(
  rawQuery: string | null | undefined,
  defaultScope: SearchScope = 'all',
  mode: SearchMode = 'legacy_compat'
): ParsedSearchQuery {
  const raw = rawQuery ? String(rawQuery).trim() : '';
  const normalized = raw.toLowerCase();
  if (!normalized) {
    return {
      raw,
      normalized: '',
      terms: [],
      scope: defaultScope,
      mode,
      isEmpty: true,
    };
  }

  // Phase 3D Production Default: strictly legacy-compatible whitespace-delimited terms
  if (mode === 'legacy_compat') {
    const terms = normalized.split(/\s+/).filter(Boolean);
    return {
      raw,
      normalized,
      terms,
      scope: defaultScope,
      mode,
      isEmpty: terms.length === 0,
    };
  }

  // Advanced mode (NEW_PREVIEW_ONLY): extracts -term, "quoted phrase", and field:value
  const negatedTerms: string[] = [];
  const exactPhrases: string[] = [];
  const fieldQueries: Record<string, string> = {};
  const terms: string[] = [];

  const remaining = normalized.replace(/"([^"]+)"/g, (_, phrase) => {
    const p = phrase.trim();
    if (p) exactPhrases.push(p);
    return ' ';
  });

  const tokens = remaining.split(/\s+/).filter(Boolean);
  for (const tok of tokens) {
    if (tok.startsWith('-') && tok.length > 1) {
      negatedTerms.push(tok.slice(1));
    } else if (tok.includes(':')) {
      const [fld, val] = tok.split(':', 2);
      if (fld && val) {
        fieldQueries[fld] = val;
      } else {
        terms.push(tok);
      }
    } else {
      terms.push(tok);
    }
  }

  return {
    raw,
    normalized,
    terms,
    negatedTerms,
    exactPhrases,
    fieldQueries,
    scope: defaultScope,
    mode,
    isEmpty:
      terms.length === 0 &&
      exactPhrases.length === 0 &&
      Object.keys(fieldQueries).length === 0,
  };
}

/**
 * Search Engine (Architecture V2 — Phase 3C).
 * Pure in-memory multi-field matching engine with exact legacy fidelity.
 */
import type { SearchDocument, ParsedSearchQuery, SearchMatchResult } from './types';
import { parseSearchQuery } from './queryParser';

export function matchDocument(
  doc: SearchDocument,
  query: ParsedSearchQuery
): SearchMatchResult {
  if (query.isEmpty) {
    return { matches: true, score: 0, matchedFields: [] };
  }

  const matchedFields: string[] = [];
  let totalScore = 0;

  for (const term of query.terms) {
    let termMatched = false;

    // Check scope-specific or global targets
    if (query.scope === 'title') {
      if (doc.titleLower.includes(term)) {
        termMatched = true;
        totalScore += 10;
        matchedFields.push('title');
      }
    } else if (query.scope === 'cat') {
      if (doc.categoriesLower.includes(term) || doc.tagsLower.includes(term)) {
        termMatched = true;
        totalScore += 5;
        matchedFields.push('cat');
      }
    } else if (query.scope === 'desc') {
      if (doc.descLower.includes(term)) {
        termMatched = true;
        totalScore += 2;
        matchedFields.push('desc');
      }
    } else if (query.scope === 'comment') {
      if (doc.commentsLower.includes(term)) {
        termMatched = true;
        totalScore += 2;
        matchedFields.push('comment');
      }
    } else if (query.scope === 'basic') {
      if (
        doc.titleLower.includes(term) ||
        doc.categoriesLower.includes(term) ||
        doc.tagsLower.includes(term) ||
        doc.modsLower.includes(term)
      ) {
        termMatched = true;
        totalScore += 8;
        matchedFields.push('basic');
      }
    } else {
      // 'all' scope
      if (doc.titleLower.includes(term)) {
        termMatched = true;
        totalScore += 10;
        matchedFields.push('title');
      } else if (doc.categoriesLower.includes(term) || doc.tagsLower.includes(term)) {
        termMatched = true;
        totalScore += 5;
        matchedFields.push('cat');
      } else if (doc.modsLower.includes(term)) {
        termMatched = true;
        totalScore += 4;
        matchedFields.push('mods');
      } else if (doc.authorLower.includes(term)) {
        termMatched = true;
        totalScore += 4;
        matchedFields.push('author');
      } else if (doc.descLower.includes(term)) {
        termMatched = true;
        totalScore += 2;
        matchedFields.push('desc');
      } else if (doc.commentsLower.includes(term)) {
        termMatched = true;
        totalScore += 2;
        matchedFields.push('comment');
      } else if (doc.allTextLower.includes(term)) {
        termMatched = true;
        totalScore += 1;
        matchedFields.push('other');
      }
    }

    if (!termMatched) {
      return { matches: false, score: 0, matchedFields: [] };
    }
  }

  return {
    matches: true,
    score: totalScore,
    matchedFields: Array.from(new Set(matchedFields)),
  };
}

export function filterItemsWithSearch<T>(
  items: T[],
  toDoc: (item: T) => SearchDocument,
  query: string | ParsedSearchQuery
): T[] {
  const parsed = typeof query === 'string' ? parseSearchQuery(query) : query;
  if (parsed.isEmpty) return items;

  return items.filter((item) => matchDocument(toDoc(item), parsed).matches);
}

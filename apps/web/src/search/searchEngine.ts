import type {
  SearchDocument,
  ParsedSearchQuery,
  SearchMatchResult,
  SearchMatchField,
  IncludedModMatchReason,
  SearchMatchReason,
} from './types';
import { parseSearchQuery } from './queryParser';

function computePrimaryReasonLabel(
  terms: string[],
  fields: SearchMatchField[],
  termMatches: { term: string; fields: SearchMatchField[] }[],
  includedMods: IncludedModMatchReason[]
): string {
  // Helper: did a field match ALL terms?
  const fieldMatchesAll = (f: SearchMatchField) =>
    termMatches.every((tm) => tm.fields.includes(f));

  // Presentation priority: title / former_title > author / category > loader / version > included_mod
  if (fieldMatchesAll('title')) {
    return '名称匹配';
  }
  if (fieldMatchesAll('former_title')) {
    return '曾用名匹配';
  }
  if (fieldMatchesAll('author')) {
    return '作者匹配';
  }
  if (fieldMatchesAll('category')) {
    return '玩法标签匹配';
  }
  if (fieldMatchesAll('loader')) {
    return 'Loader 匹配';
  }
  if (fieldMatchesAll('minecraft_version')) {
    return '版本匹配';
  }

  // Check if any single included mod matched ALL terms
  const fullMatchMods = includedMods.filter((m) => m.matchedTerms.length === terms.length);
  if (fullMatchMods.length > 0) {
    if (fullMatchMods.length === 1) {
      return `包含模组：${fullMatchMods[0].modName}`;
    }
    if (fullMatchMods.length === 2) {
      return `包含模组：${fullMatchMods[0].modName}、${fullMatchMods[1].modName}`;
    }
    return `包含模组：${fullMatchMods[0].modName}、${fullMatchMods[1].modName} +${fullMatchMods.length - 2}`;
  }

  // Cross-field multi-term matches
  if (fields.includes('title') && fields.includes('included_mod')) {
    return '多字段匹配 (名称 + 包含模组)';
  }
  if (fields.includes('title')) {
    return '名称匹配';
  }
  if (fields.includes('included_mod')) {
    if (includedMods.length === 1) {
      return `包含模组：${includedMods[0].modName}`;
    }
    if (includedMods.length === 2) {
      return `包含模组：${includedMods[0].modName}、${includedMods[1].modName}`;
    }
    if (includedMods.length > 2) {
      return `包含模组：${includedMods[0].modName}、${includedMods[1].modName} +${includedMods.length - 2}`;
    }
  }
  if (fields.includes('author')) {
    return '作者匹配';
  }
  if (fields.includes('category')) {
    return '玩法标签匹配';
  }

  return '多字段匹配';
}

export function matchDocument(
  doc: SearchDocument,
  query: ParsedSearchQuery
): SearchMatchResult {
  if (query.isEmpty) {
    return { matches: true, score: 0, matchedFields: [] };
  }

  // Advanced Mode Features (Inactive by default; only evaluated when mode === 'advanced')
  if (query.mode === 'advanced') {
    if (query.negatedTerms && query.negatedTerms.length > 0) {
      for (const neg of query.negatedTerms) {
        if (doc.allTextLower.includes(neg)) {
          return { matches: false, score: 0, matchedFields: [] };
        }
      }
    }

    if (query.exactPhrases && query.exactPhrases.length > 0) {
      for (const phrase of query.exactPhrases) {
        if (!doc.allTextLower.includes(phrase)) {
          return { matches: false, score: 0, matchedFields: [] };
        }
      }
    }

    if (query.fieldQueries) {
      for (const [field, val] of Object.entries(query.fieldQueries)) {
        if (field === 'author' && !doc.authorLower.includes(val)) return { matches: false, score: 0, matchedFields: [] };
        if (field === 'title' && !doc.titleLower.includes(val)) return { matches: false, score: 0, matchedFields: [] };
        if (field === 'loader' && !doc.loadersLower.includes(val)) return { matches: false, score: 0, matchedFields: [] };
        if (field === 'version' && !doc.versionsLower.includes(val)) return { matches: false, score: 0, matchedFields: [] };
      }
    }
  }

  const modNames = doc.includedModNames || [];
  const modMatchesMap = new Map<string, Set<string>>(); // modName -> Set of matched query terms

  const termMatches: { term: string; fields: SearchMatchField[] }[] = [];
  const allMatchedFieldsSet = new Set<SearchMatchField>();
  let totalScore = 0;

  const canCheckTitle = query.scope === 'all' || query.scope === 'title' || query.scope === 'basic';
  const canCheckAuthor = query.scope === 'all';
  const canCheckCategory = query.scope === 'all' || query.scope === 'cat' || query.scope === 'basic';
  const canCheckLoader = query.scope === 'all';
  const canCheckVersion = query.scope === 'all';
  const canCheckMods = query.scope === 'all' || query.scope === 'basic';
  const canCheckDesc = query.scope === 'all' || query.scope === 'desc';
  const canCheckComment = query.scope === 'all' || query.scope === 'comment';

  for (const term of query.terms) {
    const termFields: SearchMatchField[] = [];

    // 1. Former title vs Main title
    if (canCheckTitle) {
      if (doc.formerTitlesLower && doc.formerTitlesLower.some((ft) => ft.includes(term))) {
        termFields.push('former_title');
        allMatchedFieldsSet.add('former_title');
        totalScore += 9;
      }
      if (doc.titleLower.includes(term)) {
        termFields.push('title');
        allMatchedFieldsSet.add('title');
        totalScore += 10;
      }
    }

    // 2. Author
    if (canCheckAuthor && doc.authorLower.includes(term)) {
      termFields.push('author');
      allMatchedFieldsSet.add('author');
      totalScore += 4;
    }

    // 3. Category / Tags
    if (canCheckCategory && (doc.categoriesLower.includes(term) || doc.tagsLower.includes(term))) {
      termFields.push('category');
      allMatchedFieldsSet.add('category');
      totalScore += 5;
    }

    // 4. Loader
    if (canCheckLoader && doc.loadersLower && doc.loadersLower.includes(term)) {
      termFields.push('loader');
      allMatchedFieldsSet.add('loader');
      totalScore += 3;
    }

    // 5. Version
    if (canCheckVersion && doc.versionsLower && doc.versionsLower.includes(term)) {
      termFields.push('minecraft_version');
      allMatchedFieldsSet.add('minecraft_version');
      totalScore += 3;
    }

    // 6. Included mods
    if (canCheckMods) {
      let modMatched = false;
      if (modNames.length > 0) {
        for (const m of modNames) {
          if (m.toLowerCase().includes(term)) {
            modMatched = true;
            if (!modMatchesMap.has(m)) {
              modMatchesMap.set(m, new Set());
            }
            modMatchesMap.get(m)!.add(term);
          }
        }
      } else if (doc.modsLower.includes(term)) {
        modMatched = true;
      }

      if (modMatched) {
        termFields.push('included_mod');
        allMatchedFieldsSet.add('included_mod');
        totalScore += 4;
      }
    }

    // 7. Desc / Comment (Only when scope is specifically 'desc' or 'comment')
    if (canCheckDesc && doc.descLower && doc.descLower.includes(term)) {
      termFields.push('other');
      allMatchedFieldsSet.add('other');
      totalScore += 2;
    }
    if (canCheckComment && doc.commentsLower && doc.commentsLower.includes(term)) {
      termFields.push('other');
      allMatchedFieldsSet.add('other');
      totalScore += 2;
    }

    // If no field matched this term, then query fails
    if (termFields.length === 0) {
      return { matches: false, score: 0, matchedFields: [] };
    }

    termMatches.push({ term, fields: termFields });
  }

  // All terms matched! Build reason.
  const includedMods: IncludedModMatchReason[] = [];
  for (const [mName, matchedTermSet] of modMatchesMap.entries()) {
    includedMods.push({
      field: 'included_mod',
      modName: mName,
      matchedTerms: Array.from(matchedTermSet),
    });
  }
  // Sort mods by number of matched terms descending, then alphabetical
  includedMods.sort((a, b) => {
    if (b.matchedTerms.length !== a.matchedTerms.length) {
      return b.matchedTerms.length - a.matchedTerms.length;
    }
    return a.modName.localeCompare(b.modName);
  });

  const uniqueFields = Array.from(allMatchedFieldsSet);
  const primaryReasonLabel = computePrimaryReasonLabel(query.terms, uniqueFields, termMatches, includedMods);

  const reason: SearchMatchReason = {
    matched: true,
    fields: uniqueFields,
    includedMods,
    termMatches,
    primaryReasonLabel,
  };

  return {
    matches: true,
    score: totalScore,
    matchedFields: uniqueFields,
    reason,
  };
}

export interface SearchExecutionResult<T> {
  items: T[];
  reasons: Map<string | number, SearchMatchReason>;
}

export function searchItemsWithReasons<T>(
  items: T[],
  toDoc: (item: T) => SearchDocument,
  query: string | ParsedSearchQuery
): SearchExecutionResult<T> {
  const parsed = typeof query === 'string' ? parseSearchQuery(query) : query;
  const matchedItems: T[] = [];
  const reasons = new Map<string | number, SearchMatchReason>();

  if (parsed.isEmpty) {
    return { items, reasons };
  }

  for (const item of items) {
    const doc = toDoc(item);
    const res = matchDocument(doc, parsed);
    if (res.matches) {
      matchedItems.push(item);
      if (res.reason) {
        reasons.set(doc.id, res.reason);
      }
    }
  }

  return { items: matchedItems, reasons };
}

export function filterItemsWithSearch<T>(
  items: T[],
  toDoc: (item: T) => SearchDocument,
  query: string | ParsedSearchQuery
): T[] {
  return searchItemsWithReasons(items, toDoc, query).items;
}


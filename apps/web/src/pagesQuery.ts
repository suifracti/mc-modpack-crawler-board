// @ts-nocheck
// Desktop data-store query contract, reused without disk access.
import { matchesSearchDocument, buildSearchDocument } from '../../shared/search-contract.cjs';
import { publicSearchAliases } from './domain/crossPlatformLinkage';
import { classifyBilibiliContent, bilibiliContentScope } from '../../shared/bilibili-content.cjs';
function parseQueryOptions(queryOrOptions) {
  if (typeof queryOrOptions === 'string' || queryOrOptions === undefined || queryOrOptions === null) {
    return {
      query: String(queryOrOptions || ''),
      version: '',
      loader: '',
      category: '',
      includedMods: [],
      includedModsExclude: false,
      gameplayCategories: [],
      gameplayCategoriesExclude: false,
      pan: '',
      dateRange: '',
      serverOnly: false,
      personalStatus: '',
      sort: '',
      page: 1,
      pageSize: 48,
      bilibiliContent: 'candidates',
    };
  }
  const options = queryOrOptions || {};
  const page = Number.isInteger(Number(options.page)) ? Math.max(1, Number(options.page)) : 1;
  const pageSize = Number.isInteger(Number(options.pageSize)) ? Math.min(2000, Math.max(1, Number(options.pageSize))) : 48;
  return {
    query: String(options.query || ''),
    version: String(options.version || ''),
    loader: String(options.loader || ''),
    category: String(options.category || ''),
    includedMods: stringListOption(options.includedMods),
    includedModsExclude: booleanOption(options.includedModsExclude),
    gameplayCategories: stringListOption(options.gameplayCategories),
    gameplayCategoriesExclude: booleanOption(options.gameplayCategoriesExclude),
    pan: String(options.pan || ''),
    dateRange: String(options.dateRange || ''),
    serverOnly: options.serverOnly === true || options.serverOnly === 1 || String(options.serverOnly || '').toLowerCase() === 'true',
    personalStatus: ['favorite', 'want_to_play', 'played'].includes(String(options.personalStatus || '')) ? String(options.personalStatus) : '',
    sort: String(options.sort || ''),
    page,
    pageSize,
    bilibiliContent: ['all', 'secondary', 'excluded'].includes(options.bilibiliContent) ? options.bilibiliContent : 'candidates',
  };
}

function stringListOption(value) {
  const values = Array.isArray(value) ? value : value === undefined || value === null || value === '' ? [] : [value];
  return [...new Set(values.map((item) => String(item || '').trim()).filter(Boolean))].slice(0, 100);
}

function booleanOption(value) {
  return value === true || value === 1 || String(value || '').toLowerCase() === 'true';
}

function optionValues(records, key) {
  const values = new Set();
  for (const record of records) for (const value of record[key] || []) if (value) values.add(String(value));
  return [...values].sort((a, b) => a.localeCompare(b, 'zh-CN'));
}

function countedOptions(records, valuesForRecord) {
  const counts = new Map();
  for (const record of records) {
    const uniqueValues = new Set(valuesForRecord(record).map((value) => String(value || '').trim()).filter(Boolean));
    for (const value of uniqueValues) counts.set(value, (counts.get(value) || 0) + 1);
  }
  return [...counts.entries()]
    .map(([value, count]) => ({ value, count }))
    .sort((left, right) => right.count - left.count || left.value.localeCompare(right.value, 'zh-CN'));
}

function includedModNames(record) {
  const raw = record?.raw || {};
  const values = raw.includedModNames ?? raw.included_mod_names;
  return Array.isArray(values) ? values.map((value) => String(value || '').trim()).filter(Boolean) : [];
}

function matchesIncludedMods(record, selected, exclude) {
  if (!selected.length) return true;
  const rowText = includedModNames(record).join(' ').toLowerCase();
  const matched = selected.every((value) => rowText.includes(value.toLowerCase()));
  return exclude ? !matched : matched;
}

function matchesGameplayCategories(record, selected, exclude) {
  if (!selected.length) return true;
  const matched = record.categories.some((category) => selected.includes(category));
  return exclude ? !matched : matched;
}

const PAN_FILTERS = ['百度', '夸克', '123', '蓝奏', '迅雷', 'Modrinth', 'CurseForge', 'official'];

function rawDownloadLinks(record) {
  const links = record?.raw?.download_links;
  return Array.isArray(links) ? links.filter((item) => item && typeof item === 'object') : [];
}

function matchesPan(record, selectedPan) {
  const pan = String(selectedPan || '').trim().toLowerCase();
  if (!pan) return true;
  if (pan === 'official') return record.platform === 'xyebbs' && Boolean(record.url);
  return rawDownloadLinks(record).some((link) => {
    const name = String(link.name || '').toLowerCase();
    const url = String(link.url || '').toLowerCase();
    const filename = String(link.filename || '').toLowerCase();
    const type = String(link.type || '').toLowerCase();
    if (pan === 'modrinth') return name.includes('modrinth') || filename.includes('.mrpack') || url.includes('cdn.bbsmc.net');
    if (pan === 'curseforge') return name.includes('curseforge') || url.includes('curseforge.com');
    if (pan === '夸克') return name.includes('夸克') || url.includes('pan.quark.cn') || type === 'quark';
    if (pan === '百度') return name.includes('百度') || url.includes('pan.baidu.com') || type === 'baidu';
    if (pan === '123') return name.includes('123') || url.includes('123pan') || type.includes('123');
    if (pan === '迅雷') return name.includes('迅雷') || url.includes('pan.xunlei.com') || type === 'xunlei';
    if (pan === '蓝奏') return name.includes('蓝奏') || url.includes('lanzou') || type.includes('lanzou');
    return name.includes(pan) || url.includes(pan) || type.includes(pan);
  });
}

function recordTimestamp(record) {
  const raw = record?.raw || {};
  const numeric = [raw.pub_timestamp, raw.modified_timestamp, raw.date_modified_timestamp]
    .map((value) => Number(value))
    .find((value) => Number.isFinite(value) && value > 0);
  if (numeric) return numeric > 10_000_000_000 ? numeric : numeric * 1000;
  const parsed = Date.parse(String(record.updatedAt || ''));
  return Number.isFinite(parsed) ? parsed : 0;
}

function matchesDateRange(record, dateRange, referenceTime) {
  const range = String(dateRange || '').trim();
  if (!range) return true;
  const updatedAt = String(record.updatedAt || '');
  if (/^\d{4}(?:-\d{2})?$/.test(range)) return updatedAt.startsWith(range);
  const days = { '7d': 7, '30d': 30, '90d': 90 }[range];
  if (!days) return true;
  const timestamp = record._timestamp !== undefined ? record._timestamp : recordTimestamp(record);
  return Boolean(timestamp && referenceTime - timestamp <= days * 86_400_000);
}

function hasServerSupport(record) {
  const environment = record?.environment || {};
  if (environment.sourceField && environment.sourceField !== 'has_server') {
    return ['required', 'optional', 'supported'].includes(String(environment.status || '').toLowerCase());
  }
  return record?.raw?.has_server === true;
}

function metricValue(record, keys) {
  for (const key of keys) {
    const value = Number(record?.raw?.[key]);
    if (Number.isFinite(value)) return value;
  }
  return 0;
}

function recordCreatedTimestamp(record) {
  const raw = record?.raw || {};
  const numeric = Number(raw.created_timestamp);
  if (Number.isFinite(numeric) && numeric > 0) return numeric > 10_000_000_000 ? numeric : numeric * 1000;
  const parsed = Date.parse(String(raw.date_created || ''));
  return Number.isFinite(parsed) ? parsed : 0;
}

function sortRecords(records, sort) {
  if (!sort) return records;
  const sorted = [...records];
  sorted.sort((left, right) => {
    if (sort === 'title_asc') return String(left.title).localeCompare(String(right.title), 'zh-CN');
    const keys = sort === 'downloads_desc'
      ? ['downloads']
      : sort === 'followers_desc'
        ? ['followers']
        : sort === 'views_desc'
          ? ['views']
      : sort === 'likes_desc'
        ? ['likes']
        : sort === 'favs_desc'
          ? ['favorites', 'favourites']
          : sort === 'coins_desc'
            ? ['coins']
            : sort === 'share_desc'
              ? ['share', 'shares']
              : sort === 'reply_desc'
                ? ['reply', 'comments']
                : sort === 'danmaku_desc'
                  ? ['danmaku']
          : sort === 'comments_desc'
            ? ['comments', 'commentsCount', 'reply']
              : sort === 'created_desc'
                ? ['created_timestamp', 'date_created']
                : [];
    const leftValue = sort === 'created_desc'
      ? (left._createdTimestamp !== undefined ? left._createdTimestamp : recordCreatedTimestamp(left))
      : (keys.length ? metricValue(left, keys) : (left._timestamp !== undefined ? left._timestamp : recordTimestamp(left)));
    const rightValue = sort === 'created_desc'
      ? (right._createdTimestamp !== undefined ? right._createdTimestamp : recordCreatedTimestamp(right))
      : (keys.length ? metricValue(right, keys) : (right._timestamp !== undefined ? right._timestamp : recordTimestamp(right)));
    if (rightValue !== leftValue) return rightValue - leftValue;
    return String(left.title).localeCompare(String(right.title), 'zh-CN');
  });
  return sorted;
}

function availablePanValues(records) {
  return PAN_FILTERS.filter((pan) => records.some((record) => matchesPan(record, pan)));
}

export async function queryStaticRecords(platform, queryOrOptions, cached, entries) {
    const options = parseQueryOptions(queryOrOptions);
    const result = cached.result;
    if (!cached.normalized) {
      // Private cache records are canonical; public results strip these internal fields.
      cached.normalized = result.records;
      for (const record of cached.normalized) {
        const document = buildSearchDocument(platform, record.raw);
        // Preserve field-wise matching without retaining the unused combined text.
        record.searchDocument = {
          titleLower: document.titleLower,
          formerTitlesLower: document.formerTitlesLower,
          authorLower: document.authorLower,
          categoriesLower: document.categoriesLower,
          tagsLower: document.tagsLower,
          modsLower: document.modsLower,
          descLower: document.descLower,
          commentsLower: document.commentsLower,
          loadersLower: document.loadersLower,
          versionsLower: document.versionsLower,
        };
        record._timestamp = recordTimestamp(record);
        record._createdTimestamp = recordCreatedTimestamp(record);
      }
    }
    if (platform === 'bilibili' && !cached.bilibiliCounts) {
      cached.bilibiliCounts = { all: cached.normalized.length, candidates: 0, secondary: 0, excluded: 0 };
      for (const record of cached.normalized) {
        record.contentDecision = classifyBilibiliContent(record);
        cached.bilibiliCounts[bilibiliContentScope(record.contentDecision)] += 1;
      }
    }
    const normalized = platform === 'bilibili' && options.bilibiliContent !== 'all'
      ? cached.normalized.filter(record => bilibiliContentScope(record.contentDecision) === options.bilibiliContent)
      : cached.normalized;
    cached.facetScopes ||= new Map();
    const facetKey = platform === 'bilibili' ? options.bilibiliContent : 'all';
    if (!cached.facetScopes.has(facetKey)) cached.facetScopes.set(facetKey, {});
    const scopedFacets = cached.facetScopes.get(facetKey);
    if (!scopedFacets.platformFacets) {
      scopedFacets.platformFacets = {
        categories: countedOptions(normalized, (record) => record.categories),
        includedMods: platform === 'mcmod' ? countedOptions(normalized, includedModNames) : [],
        gameplayCategories: platform === 'curseforge' ? countedOptions(normalized, (record) => record.categories) : [],
      };
    }
    if (!scopedFacets.baseFacets) {
      scopedFacets.baseFacets = {
        availableVersions: optionValues(normalized, 'versions'),
        availableLoaders: optionValues(normalized, 'loaders'),
        availableCategories: optionValues(normalized, 'categories'),
        availableIncludedMods: scopedFacets.platformFacets.includedMods,
        availableGameplayCategories: scopedFacets.platformFacets.gameplayCategories,
        availablePans: availablePanValues(normalized),
      };
    }
    if (!cached.baseSorted) {
      cached.baseSorted = new Map();
    }

    const hasQuery = Boolean(options.query.trim());
    const version = options.version.trim().toLocaleLowerCase();
    const loader = options.loader.trim().toLocaleLowerCase();
    const gameplayCategories = platform === 'curseforge'
      ? options.gameplayCategories.length ? options.gameplayCategories : stringListOption(options.category)
      : [];
    const isUnfiltered = !hasQuery
      && !version
      && !loader
      && (platform === 'curseforge' || !options.category)
      && (!options.includedMods || !options.includedMods.length)
      && (!gameplayCategories.length)
      && !options.pan
      && !options.dateRange
      && !options.serverOnly
      && !options.personalStatus;

    let sorted;
    let searched = normalized;
    if (isUnfiltered) {
      const sortKey = options.sort + ':' + (platform === 'bilibili' ? options.bilibiliContent : 'all');
      sorted = cached.baseSorted.get(sortKey);
      if (!sorted) {
        sorted = sortRecords(normalized, options.sort);
        cached.baseSorted.set(sortKey, sorted);
      }
    } else {
      searched = hasQuery
        ? normalized.filter((record) => matchesSearchDocument({...record.searchDocument, aliasesLower: publicSearchAliases(record.id).map(s => s.toLowerCase())}, options.query))
        : normalized;
      let referenceTime = Date.now();
      if (options.dateRange) {
        for (const record of searched) {
          const ts = record._timestamp !== undefined ? record._timestamp : recordTimestamp(record);
          if (ts > referenceTime) referenceTime = ts;
        }
      }
      const filtered = searched.filter((record) => {
        const versionMatch = !version || record.versions.some((item) => item.toLocaleLowerCase() === version);
        const loaderMatch = !loader || record.loaders.some((item) => item.toLocaleLowerCase() === loader);
        const categoryMatch = platform === 'curseforge' || !options.category || record.categories.includes(options.category);
        const includedModsMatch = platform !== 'mcmod' || matchesIncludedMods(record, options.includedMods, options.includedModsExclude);
        const gameplayCategoryMatch = platform !== 'curseforge' || matchesGameplayCategories(record, gameplayCategories, options.gameplayCategoriesExclude);
        const panMatch = matchesPan(record, options.pan);
        const serverMatch = !options.serverOnly || hasServerSupport(record);
        const dateMatch = matchesDateRange(record, options.dateRange, referenceTime);
        const personalMatch = !options.personalStatus || Boolean(entries[`${platform}:${record.sourceId}`]?.[({favorite:'favorite',want_to_play:'wantToPlay',played:'played'})[options.personalStatus]]);
        return versionMatch && loaderMatch && categoryMatch && includedModsMatch && gameplayCategoryMatch && panMatch && serverMatch && dateMatch && personalMatch;
      });
      sorted = sortRecords(filtered, options.sort);
    }

    const offset = (options.page - 1) * options.pageSize;
    const facets = !hasQuery ? scopedFacets.baseFacets : {
      availableVersions: optionValues(searched, 'versions'),
      availableLoaders: optionValues(searched, 'loaders'),
      availableCategories: optionValues(searched, 'categories'),
      availableIncludedMods: scopedFacets.platformFacets.includedMods,
      availableGameplayCategories: scopedFacets.platformFacets.gameplayCategories,
      availablePans: availablePanValues(searched),
    };

    return {
      platform,
      total: sorted.length,
      bilibiliCounts: cached.bilibiliCounts,
      page: options.page,
      pageSize: options.pageSize,
      records: sorted.slice(offset, offset + options.pageSize).map((record) => {
        if (!record.searchDocument && record._timestamp === undefined && record._createdTimestamp === undefined) return record;
        const { searchDocument, _timestamp, _createdTimestamp, ...publicRecord } = record;
        return publicRecord;
      }),
      availableVersions: facets.availableVersions,
      availableLoaders: facets.availableLoaders,
      availableCategories: facets.availableCategories,
      availableCategoryCounts: scopedFacets.platformFacets.categories,
      availableIncludedMods: facets.availableIncludedMods,
      availableGameplayCategories: facets.availableGameplayCategories,
      availablePans: facets.availablePans,
      sourceFile: result.sourceFile,
      error: result.error,
    };
  }


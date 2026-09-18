/**
 * Frontend Debug & Instrumentation Subsystem (Architecture V2 — Phase 3C.1).
 * Used exclusively for Preview runtime verification, integration proofs, and CDP smoke tests.
 * Never shipped to production (converted_output is 100% isolated).
 */
export interface FrontendDebugState {
  searchCalls: number;
  lastSearchQuery: string;
  lastSearchPlatform: string;
  lastSearchMatchedIds: (string | number)[];
  lastSearchMatchReasons?: Record<string | number, unknown>;
  filterCalls: Record<string, number>;
  lastFilterCriteria: Record<string, unknown>;
  lastFilterMatchedCounts: Record<string, number>;
  lastFilterMatchedIds: Record<string, (string | number)[]>;
  navigationCount: number;
  lastRoute: { tab: string; query?: string } | null;
  modalCalls: Record<string, number>;
  lastModalViewModel: unknown;
  rendererCalls: {
    bilibili: number;
    bbsmc: number;
    xyebbs: number;
    modrinth: number;
    curseforge: number;
    mcmod: number;
  };
  /**
   * Phase 3G-F.1-A: explainability surface for Bilibili pack grouping.
   * Lets a runtime gate (or a human in devtools) read WHY a record was grouped
   * where it was, including which candidate anchors the admissibility rules
   * REJECTED and under which rule. Without this the rejection reasons are only
   * reachable by re-running the offline evaluator.
   */
  lastGroupingDecisions?: Record<string, {
    groupKey: string;
    identityKey: string;
    episodeResidue: string;
    groupingReason: string;
    rejectedAnchors?: { anchor: string; reason: string }[];
  }>;
}

declare global {
  interface Window {
    __frontendDebug?: FrontendDebugState;
  }
}

export function initFrontendDebug(): FrontendDebugState {
  if (typeof window === 'undefined') {
    return createDefaultDebugState();
  }

  if (!window.__frontendDebug) {
    window.__frontendDebug = createDefaultDebugState();
  }
  return window.__frontendDebug;
}

export function getFrontendDebug(): FrontendDebugState | undefined {
  if (typeof window !== 'undefined') {
    return window.__frontendDebug;
  }
  return undefined;
}

function createDefaultDebugState(): FrontendDebugState {
  return {
    searchCalls: 0,
    lastSearchQuery: '',
    lastSearchPlatform: '',
    lastSearchMatchedIds: [],
    lastSearchMatchReasons: {},
    filterCalls: {
      mcmod: 0,
      bilibili: 0,
      bbsmc: 0,
      xyebbs: 0,
      modrinth: 0,
      curseforge: 0,
    },
    lastFilterCriteria: {},
    lastFilterMatchedCounts: {},
    lastFilterMatchedIds: {},
    navigationCount: 0,
    lastRoute: null,
    modalCalls: {
      mcmod: 0,
      bilibili: 0,
      bbsmc: 0,
      xyebbs: 0,
      modrinth: 0,
      curseforge: 0,
    },
    lastModalViewModel: null,
    rendererCalls: {
      bilibili: 0,
      bbsmc: 0,
      xyebbs: 0,
      modrinth: 0,
      curseforge: 0,
      mcmod: 0,
    },
  };
}

export function recordSearchDebug(
  platform: string,
  query: string,
  matchedIds: (string | number)[],
  matchReasons?: Record<string | number, unknown>
): void {
  const debug = getFrontendDebug();
  if (debug) {
    debug.searchCalls++;
    debug.lastSearchPlatform = platform;
    debug.lastSearchQuery = query;
    debug.lastSearchMatchedIds = matchedIds;
    debug.lastSearchMatchReasons = matchReasons || {};
  }
}

export function recordFilterDebug(platform: string, criteria: unknown, matchedCount: number, matchedIds: (string | number)[]): void {
  const debug = getFrontendDebug();
  if (debug) {
    debug.filterCalls[platform] = (debug.filterCalls[platform] || 0) + 1;
    debug.lastFilterCriteria[platform] = criteria;
    debug.lastFilterMatchedCounts[platform] = matchedCount;
    debug.lastFilterMatchedIds[platform] = matchedIds;
  }
}

export function recordNavigationDebug(tab: string, query?: string): void {
  const debug = getFrontendDebug();
  if (debug) {
    debug.navigationCount++;
    debug.lastRoute = { tab, query };
  }
}

export function recordModalDebug(platform: string, viewModel: unknown): void {
  const debug = getFrontendDebug();
  if (debug) {
    debug.modalCalls[platform] = (debug.modalCalls[platform] || 0) + 1;
    debug.lastModalViewModel = viewModel;
  }
}

export function recordRendererDebug(platform: 'bilibili' | 'bbsmc' | 'xyebbs' | 'modrinth' | 'curseforge' | 'mcmod'): void {
  const debug = getFrontendDebug();
  if (debug) {
    debug.rendererCalls[platform] = (debug.rendererCalls[platform] || 0) + 1;
  }
}

/**
 * Phase 3G-F.1-A: publish the per-record grouping decisions (including rejected
 * candidate anchors) for runtime inspection. Called by the Bilibili platform
 * renderer path so `window.__frontendDebug.lastGroupingDecisions` is populated
 * whenever grouping actually ran.
 */
export function recordGroupingDecisionsDebug(
  decisions: Record<string, {
    groupKey: string;
    identityKey: string;
    episodeResidue: string;
    groupingReason: string;
    rejectedAnchors?: { anchor: string; reason: string }[];
  }>
): void {
  const debug = getFrontendDebug();
  if (debug) {
    debug.lastGroupingDecisions = decisions;
  }
}

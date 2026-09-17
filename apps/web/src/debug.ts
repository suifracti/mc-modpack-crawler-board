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

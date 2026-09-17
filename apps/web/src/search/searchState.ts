/**
 * Search State Coordinator (Architecture V2 — Phase 3C).
 * Coordinates search terms and active scopes across platform tabs.
 */
import type { SearchScope, ParsedSearchQuery, SearchMode } from './types';
import { parseSearchQuery } from './queryParser';
import type { Platform } from '../domain/types';
import { filterItemsWithSearch } from './searchEngine';
import {
  buildMcmodSearchDocument,
  buildBilibiliSearchDocument,
  buildBbsmcSearchDocument,
  buildXyebbsSearchDocument,
  buildModrinthSearchDocument,
  buildCurseforgeSearchDocument,
} from './searchDocument';
import { recordSearchDebug } from '../debug';

export class SearchStateCoordinator {
  private activeQuery: string = '';
  private activeScope: SearchScope = 'all';
  private searchMode: SearchMode = 'legacy_compat';
  private platformQueries: Map<Platform | 'all', string> = new Map();
  private listeners: Set<(query: string, scope: SearchScope) => void> = new Set();

  public getSearchMode(): SearchMode {
    return this.searchMode;
  }

  public setSearchMode(mode: SearchMode): void {
    this.searchMode = mode;
  }

  public getQuery(platform?: Platform | 'all'): string {
    if (platform) {
      return this.platformQueries.get(platform) || '';
    }
    return this.activeQuery;
  }

  public getScope(): SearchScope {
    return this.activeScope;
  }

  public getParsedQuery(platform?: Platform | 'all'): ParsedSearchQuery {
    const raw = this.getQuery(platform);
    return parseSearchQuery(raw, this.activeScope, this.searchMode);
  }

  public setQuery(query: string, platform?: Platform | 'all'): void {
    const trimmed = (query || '').trim();
    if (platform) {
      this.platformQueries.set(platform, trimmed);
    }
    this.activeQuery = trimmed;

    // Runtime Integration Wiring: run TS SearchEngine on active dataset & record debug
    if (typeof window !== 'undefined') {
      const plat = platform || 'mcmod';
      const parsed = parseSearchQuery(trimmed, this.activeScope, this.searchMode);
      let matchedIds: (string | number)[] = [];
      const win = window as unknown as Record<string, unknown>;

      if (plat === 'mcmod' && Array.isArray(win.mcmodData)) {
        const matches = filterItemsWithSearch(win.mcmodData as any[], buildMcmodSearchDocument, parsed);
        matchedIds = matches.map((m) => m.mid);
      } else if (plat === 'bilibili' && Array.isArray(win.biliModpacksData)) {
        const matches = filterItemsWithSearch(win.biliModpacksData as any[], buildBilibiliSearchDocument, parsed);
        matchedIds = matches.map((m) => m.bvid || m.id);
      } else if (plat === 'bbsmc' && Array.isArray(win.bbsmcModpacksData)) {
        const matches = filterItemsWithSearch(win.bbsmcModpacksData as any[], buildBbsmcSearchDocument, parsed);
        matchedIds = matches.map((m) => m.project_id || m.id);
      } else if (plat === 'xyebbs' && Array.isArray(win.xyebbsModpacksData)) {
        const matches = filterItemsWithSearch(win.xyebbsModpacksData as any[], buildXyebbsSearchDocument, parsed);
        matchedIds = matches.map((m) => m.project_id || m.id);
      } else if (plat === 'modrinth' && Array.isArray(win.modrinthModpacksData)) {
        const matches = filterItemsWithSearch(win.modrinthModpacksData as any[], buildModrinthSearchDocument, parsed);
        matchedIds = matches.map((m) => m.id);
      } else if (plat === 'curseforge' && Array.isArray(win.curseforgeModpacksData)) {
        const matches = filterItemsWithSearch(win.curseforgeModpacksData as any[], buildCurseforgeSearchDocument, parsed);
        matchedIds = matches.map((m) => m.id);
      }

      recordSearchDebug(plat, trimmed, matchedIds);
    }

    this.notify();
  }

  public setScope(scope: SearchScope): void {
    this.activeScope = scope;
    this.notify();
  }

  public clear(platform?: Platform | 'all'): void {
    if (platform) {
      this.platformQueries.set(platform, '');
    } else {
      this.platformQueries.clear();
      this.activeQuery = '';
    }
    this.notify();
  }

  public subscribe(listener: (query: string, scope: SearchScope) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notify(): void {
    for (const l of this.listeners) {
      try {
        l(this.activeQuery, this.activeScope);
      } catch (err) {
        console.error('SearchStateCoordinator listener error:', err);
      }
    }
  }
}

export const searchCoordinator = new SearchStateCoordinator();

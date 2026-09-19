/**
 * Search State Coordinator (Architecture V2 — Phase 3C).
 * Coordinates search terms and active scopes across platform tabs.
 */
import type { SearchScope, ParsedSearchQuery, SearchMode, SearchMatchReason } from './types';
import { parseSearchQuery } from './queryParser';
import type { Platform } from '../domain/types';
import { searchItemsWithReasons } from './searchEngine';
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
  private platformMatchedIds: Map<string, (string | number)[]> = new Map();
  private platformMatchReasons: Map<Platform | 'all', Map<string | number, SearchMatchReason>> = new Map();
  private cachedMatchedSet: Set<number> | null = null;
  private cachedMatchedSetQuery: string = '';

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

  public getMatchedIds(platform: Platform = 'mcmod'): (string | number)[] | null {
    const q = this.getQuery(platform);
    if (!q) return null;
    return this.platformMatchedIds.get(platform) || [];
  }

  public isFiltering(platform: Platform = 'mcmod'): boolean {
    return Boolean(this.getQuery(platform));
  }

  public isMatched(mid: string | number, platform: Platform = 'mcmod'): boolean {
    if (!this.isFiltering(platform)) return true;
    if (platform === 'mcmod') {
      const q = this.getQuery(platform);
      if (this.cachedMatchedSet && this.cachedMatchedSetQuery === q) {
        return this.cachedMatchedSet.has(Number(mid));
      }
      const matched = this.getMatchedIds(platform);
      if (!matched) return true;
      this.cachedMatchedSet = new Set(matched.map(Number));
      this.cachedMatchedSetQuery = q;
      return this.cachedMatchedSet.has(Number(mid));
    }
    const matched = this.getMatchedIds(platform);
    return matched ? matched.includes(mid) : true;
  }

  public getMatchReason(id: string | number, platform: Platform = 'mcmod'): SearchMatchReason | null {
    if (!this.isFiltering(platform)) return null;
    const reasons = this.platformMatchReasons.get(platform);
    if (!reasons) return null;
    return reasons.get(id) || reasons.get(Number(id)) || reasons.get(String(id)) || null;
  }

  public getMatchReasonLabel(id: string | number, platform: Platform = 'mcmod'): string | null {
    const reason = this.getMatchReason(id, platform);
    return reason ? reason.primaryReasonLabel : null;
  }

  public getAllMatchReasons(platform: Platform = 'mcmod'): Record<string | number, SearchMatchReason> {
    const reasons = this.platformMatchReasons.get(platform);
    if (!reasons) return {};
    const out: Record<string | number, SearchMatchReason> = {};
    for (const [k, v] of reasons.entries()) {
      out[k] = v;
    }
    return out;
  }

  public setQuery(query: string, platform?: Platform | 'all'): void {
    const trimmed = (query || '').trim();
    if (platform) {
      this.platformQueries.set(platform, trimmed);
    }
    this.activeQuery = trimmed;

    const plat = platform || 'mcmod';
    if (!trimmed) {
      this.platformMatchedIds.delete(plat);
      this.platformMatchReasons.delete(plat);
      if (plat === 'mcmod' || plat === 'all') {
        this.cachedMatchedSet = null;
        this.cachedMatchedSetQuery = '';
      }
    }

    // Runtime Integration Wiring: run TS SearchEngine on active dataset & record debug
    if (typeof window !== 'undefined') {
      const parsed = parseSearchQuery(trimmed, this.activeScope, this.searchMode);
      let matchedIds: (string | number)[] = [];
      let matchReasonsMap = new Map<string | number, SearchMatchReason>();
      const win = window as unknown as Record<string, unknown>;

      if (plat === 'mcmod' && Array.isArray(win.mcmodData)) {
        const res = searchItemsWithReasons(win.mcmodData as any[], buildMcmodSearchDocument, parsed);
        matchedIds = res.items.map((m) => m.mid);
        matchReasonsMap = res.reasons;
      } else if (plat === 'bilibili' && Array.isArray(win.biliModpacksData)) {
        const res = searchItemsWithReasons(win.biliModpacksData as any[], buildBilibiliSearchDocument, parsed);
        matchedIds = res.items.map((m) => m.bvid || m.id);
        matchReasonsMap = res.reasons;
      } else if (plat === 'bbsmc' && Array.isArray(win.bbsmcModpacksData)) {
        const res = searchItemsWithReasons(win.bbsmcModpacksData as any[], buildBbsmcSearchDocument, parsed);
        matchedIds = res.items.map((m) => m.project_id || m.id);
        matchReasonsMap = res.reasons;
      } else if (plat === 'xyebbs' && Array.isArray(win.xyebbsModpacksData)) {
        const res = searchItemsWithReasons(win.xyebbsModpacksData as any[], buildXyebbsSearchDocument, parsed);
        matchedIds = res.items.map((m) => m.project_id || m.id);
        matchReasonsMap = res.reasons;
      } else if (plat === 'modrinth' && Array.isArray(win.modrinthModpacksData)) {
        const res = searchItemsWithReasons(win.modrinthModpacksData as any[], buildModrinthSearchDocument, parsed);
        matchedIds = res.items.map((m) => m.id);
        matchReasonsMap = res.reasons;
      } else if (plat === 'curseforge' && Array.isArray(win.curseforgeModpacksData)) {
        const res = searchItemsWithReasons(win.curseforgeModpacksData as any[], buildCurseforgeSearchDocument, parsed);
        matchedIds = res.items.map((m) => m.id);
        matchReasonsMap = res.reasons;
      }

      if (trimmed) {
        this.platformMatchedIds.set(plat, matchedIds);
        this.platformMatchReasons.set(plat, matchReasonsMap);
        if (plat === 'mcmod') {
          this.cachedMatchedSet = new Set(matchedIds.map(Number));
          this.cachedMatchedSetQuery = trimmed;
        }
      }

      const matchReasonsObj: Record<string | number, unknown> = {};
      for (const [id, r] of matchReasonsMap.entries()) {
        matchReasonsObj[id] = r;
      }
      recordSearchDebug(plat, trimmed, matchedIds, matchReasonsObj);
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
      this.platformMatchedIds.delete(platform);
      this.platformMatchReasons.delete(platform);
      if (platform === 'mcmod' || platform === 'all') {
        this.cachedMatchedSet = null;
        this.cachedMatchedSetQuery = '';
      }
    } else {
      this.platformQueries.clear();
      this.platformMatchedIds.clear();
      this.platformMatchReasons.clear();
      this.cachedMatchedSet = null;
      this.cachedMatchedSetQuery = '';
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

/**
 * Platform Router (Architecture V2 — Phase 3C).
 * Coordinates active tab state, DOM visibility transitions, and sidecar loading.
 */
import type { PlatformTab, RouteState, RouteChangeListener } from './types';
import { parseHash, updateHash, listenToHashChange } from './urlState';
import { LegacySidecarLoader } from '../data/LegacySidecarLoader';
import type { Platform } from '../domain/types';
import { recordNavigationDebug } from '../debug';

export class PlatformRouter {
  private currentState: RouteState = {
    tab: 'mcmod',
    query: '',
  };
  private listeners: Set<RouteChangeListener> = new Set();
  private initialized: boolean = false;

  public getState(): RouteState {
    return { ...this.currentState };
  }

  public getActiveTab(): PlatformTab {
    return this.currentState.tab;
  }

  public init(initialTab?: PlatformTab): void {
    if (this.initialized) return;
    this.initialized = true;

    const hashState = parseHash();
    const targetTab = initialTab || hashState.tab || 'mcmod';
    const targetQuery = hashState.query || '';

    this.currentState = { tab: targetTab, query: targetQuery };

    listenToHashChange((tab, query) => {
      if (tab !== this.currentState.tab || query !== this.currentState.query) {
        this.navigateTo(tab, query, false);
      }
    });
  }

  public navigateTo(tab: PlatformTab, query?: string, syncHash: boolean = true): void {
    const prevState = { ...this.currentState };
    const newQuery = query !== undefined ? query : this.currentState.query;
    this.currentState = {
      tab,
      query: newQuery,
    };

    if (syncHash) {
      updateHash(tab, newQuery);
    }

    if (typeof window !== 'undefined') {
      recordNavigationDebug(tab, newQuery);
    }

    // Trigger lazy loading for non-all platforms if needed
    if (tab !== 'all' && tab !== 'mcmod') {
      LegacySidecarLoader.load(tab as Platform).catch((err) => {
        console.error(`Failed to load sidecar for platform ${tab}:`, err);
      });
    }

    this.notify(this.currentState, prevState);
  }

  public subscribe(listener: RouteChangeListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notify(newState: RouteState, prevState: RouteState): void {
    for (const l of this.listeners) {
      try {
        l(newState, prevState);
      } catch (err) {
        console.error('PlatformRouter listener error:', err);
      }
    }
  }
}

export const platformRouter = new PlatformRouter();

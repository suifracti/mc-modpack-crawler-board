/**
 * Central Filter State Store (Architecture V2 — Phase 3C).
 * Tracks filter criteria for all 6 platforms and notifies subscribers on changes.
 */
import type { Platform } from '../domain/types';
import type { CommonFilterCriteria } from './types';

export class FilterStore {
  private state: Map<Platform | 'all', CommonFilterCriteria> = new Map();
  private listeners: Set<(platform: Platform | 'all', criteria: CommonFilterCriteria) => void> = new Set();

  public getCriteria(platform: Platform | 'all'): CommonFilterCriteria {
    return this.state.get(platform) || {};
  }

  public setCriteria(
    platform: Platform | 'all',
    update: Partial<CommonFilterCriteria>
  ): void {
    const current = this.getCriteria(platform);
    const updated = { ...current, ...update };
    this.state.set(platform, updated);
    this.notify(platform, updated);
  }

  public reset(platform: Platform | 'all'): void {
    this.state.set(platform, {});
    this.notify(platform, {});
  }

  public subscribe(
    listener: (platform: Platform | 'all', criteria: CommonFilterCriteria) => void
  ): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notify(platform: Platform | 'all', criteria: CommonFilterCriteria): void {
    for (const l of this.listeners) {
      try {
        l(platform, criteria);
      } catch (err) {
        console.error('FilterStore listener error:', err);
      }
    }
  }
}

export const filterStore = new FilterStore();

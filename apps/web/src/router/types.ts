/**
 * Router Subsystem Types (Architecture V2 — Phase 3C).
 */
import type { Platform } from '../domain/types';

export type PlatformTab = Platform | 'all';

export interface RouteState {
  tab: PlatformTab;
  query: string;
  viewMode?: 'table' | 'cards' | 'grouped' | 'flat';
}

export type RouteChangeListener = (newState: RouteState, prevState: RouteState) => void;

/**
 * URL Hash & State Sync (Architecture V2 — Phase 3C).
 */
import type { PlatformTab } from './types';

const VALID_TABS: Set<PlatformTab> = new Set([
  'all',
  'mcmod',
  'bilibili',
  'bbsmc',
  'xyebbs',
  'modrinth',
  'curseforge',
]);

export function parseHash(): { tab: PlatformTab; query: string } {
  if (typeof window === 'undefined') {
    return { tab: 'mcmod', query: '' };
  }

  const rawHash = window.location.hash.replace(/^#\/?/, '').trim();
  if (!rawHash) {
    return { tab: 'mcmod', query: '' };
  }

  const [tabPart, ...queryParts] = rawHash.split('?');
  const normalizedTab = tabPart.toLowerCase() as PlatformTab;
  const tab: PlatformTab = VALID_TABS.has(normalizedTab) ? normalizedTab : 'mcmod';

  let query = '';
  if (queryParts.length > 0) {
    const params = new URLSearchParams(queryParts.join('?'));
    query = params.get('q') || '';
  }

  return { tab, query };
}

export function updateHash(tab: PlatformTab, query?: string): void {
  if (typeof window === 'undefined' || !window.history?.replaceState) return;

  let newHash = `#${tab}`;
  if (query && query.trim()) {
    newHash += `?q=${encodeURIComponent(query.trim())}`;
  }

  if (window.location.hash !== newHash) {
    window.history.replaceState(null, '', newHash);
  }
}

export function listenToHashChange(
  callback: (tab: PlatformTab, query: string) => void
): () => void {
  if (typeof window === 'undefined') return () => {};

  const handler = () => {
    const parsed = parseHash();
    callback(parsed.tab, parsed.query);
  };

  window.addEventListener('hashchange', handler);
  return () => window.removeEventListener('hashchange', handler);
}

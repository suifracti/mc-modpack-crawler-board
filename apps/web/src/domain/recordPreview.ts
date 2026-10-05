import type { Platform } from './types';

/** Public source content from an existing archive; never personal library data. */
export interface RecordPreview {
  platform: Platform;
  sourceId: string;
  sourceUrl: string;
  archivedAt: string;
  description: string;
  images: string[];
  releases: Record<string, unknown>[];
  includedMods?: Record<string, unknown>[];
}

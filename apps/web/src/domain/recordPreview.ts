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

/** Overlay saved public content only when its source identity still agrees. */
export function mergeRecordPreview<T extends {platform: Platform; sourceId: string; url: string; summary: string; releases: Record<string, unknown>[]; raw: Record<string, unknown>}>(record: T, preview: RecordPreview): T {
  if (record.platform !== preview.platform || record.sourceId !== preview.sourceId || record.url !== preview.sourceUrl) return record;
  const current = String(record.raw.description || record.raw.desc || record.summary || '').trim();
  const description = preview.description.length > current.length ? preview.description : current;
  const urls = (value: unknown): string[] => Array.isArray(value) ? value.flatMap(urls)
    : typeof value === 'string' ? [value] : value && typeof value === 'object' ? urls((value as Record<string, unknown>).url || (value as Record<string, unknown>).src) : [];
  const releases = preview.releases.length ? preview.releases : record.releases;
  return {...record, summary: description, releases, raw: {...record.raw, description,
    intro_images: [...new Set([...urls(record.raw.intro_images), ...preview.images])],
    gallery: [...new Set([...urls(record.raw.gallery), ...preview.images])],
    ...(preview.includedMods ? {includedMods: preview.includedMods} : {}),
    releases, previewArchiveAt: preview.archivedAt}};
}

/**
 * Search Document Builders (Architecture V2 — Phase 3C).
 * Maps multi-platform items into unified SearchDocuments for uniform query matching.
 */
import type { SearchDocument } from './types';
import type { McmodStructuredItem } from '../platforms/mcmod/types';
import type { BilibiliPack } from '../types/legacy/bilibili';
import type { BbsmcPack } from '../types/legacy/bbsmc';
import type { XyebbsPack } from '../types/legacy/xyebbs';
import type { ModrinthPack } from '../types/legacy/modrinth';
import type { CurseforgePack } from '../types/legacy/curseforge';
import * as sharedSearchContract from '../../../shared/search-contract.cjs';

export function buildMcmodSearchDocument(
  item: McmodStructuredItem,
  descText?: string,
  commentsText?: string
): SearchDocument {
  return sharedSearchContract.buildMcmodSearchDocument(
    item as unknown as Record<string, unknown>,
    descText,
    commentsText,
  ) as SearchDocument;
}

export function buildBilibiliSearchDocument(p: BilibiliPack): SearchDocument {
  return sharedSearchContract.buildBilibiliSearchDocument(p as unknown as Record<string, unknown>) as SearchDocument;
}

export function buildBbsmcSearchDocument(p: BbsmcPack): SearchDocument {
  return sharedSearchContract.buildBbsmcSearchDocument(p as unknown as Record<string, unknown>) as SearchDocument;
}

export function buildXyebbsSearchDocument(p: XyebbsPack): SearchDocument {
  return sharedSearchContract.buildXyebbsSearchDocument(p as unknown as Record<string, unknown>) as SearchDocument;
}

export function buildModrinthSearchDocument(p: ModrinthPack): SearchDocument {
  return sharedSearchContract.buildModrinthSearchDocument(p as unknown as Record<string, unknown>) as SearchDocument;
}

export function buildCurseforgeSearchDocument(p: CurseforgePack): SearchDocument {
  return sharedSearchContract.buildCurseforgeSearchDocument(p as unknown as Record<string, unknown>) as SearchDocument;
}

/**
 * MCMod Search Document & Selector Utilities (Architecture V2 — Phase 3B).
 * Guarantees search parity (RLCraft = 93) by indexing all structured fields.
 */
import type { McmodStructuredItem } from './types';

/**
 * Flat search text for the included-mods column (Phase 3G-D.1).
 *
 * Derived FORWARD from the structured provenance array. This is byte-identical
 * to the legacy payload value `", ".join(all_mod_names)` for all 1484 packs, so
 * matching behaviour is unchanged — but nothing ever has to reverse-parse an
 * ambiguous flat string back into mod names again.
 */
export function joinMcmodModNames(pack: Pick<McmodStructuredItem, 'includedModNames'>): string {
  return (pack.includedModNames || []).join(', ');
}

export function buildMcmodSearchText(pack: McmodStructuredItem): string {
  const parts: string[] = [];

  if (pack.title) parts.push(pack.title);
  if (pack.chineseName && pack.chineseName !== pack.title) parts.push(pack.chineseName);
  if (pack.englishName) parts.push(pack.englishName);
  if (pack.formerTitles && pack.formerTitles.length) {
    parts.push(pack.formerTitles.join(' '));
  }
  if (pack.author) parts.push(pack.author);
  if (pack.typeName) parts.push(pack.typeName);
  if (pack.categories && pack.categories.length) {
    parts.push(pack.categories.join(' '));
  }
  if (pack.tags && pack.tags.length) {
    parts.push(pack.tags.join(' '));
  }
  if (pack.mcVersions && pack.mcVersions.length) {
    parts.push(pack.mcVersions.join(' '));
  }
  const modNames = joinMcmodModNames(pack);
  if (modNames) parts.push(modNames);
  if (pack.modCategorySearch) parts.push(pack.modCategorySearch);

  return parts.join(' ').toLowerCase();
}

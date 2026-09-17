/**
 * Version Modal ViewModel Builder (Architecture V2 — Phase 3C).
 * Dispatches platform-specific data objects into a unified VersionModalViewModel.
 */
import type { VersionModalViewModel } from './types';
import { adaptMcmodToVersionModal } from '../../platforms/mcmod/versionAdapter';
import { adaptBilibiliToVersionModal } from '../../platforms/bilibili/versionAdapter';
import { adaptBbsmcToVersionModal } from '../../platforms/bbsmc/versionAdapter';
import { adaptXyebbsToVersionModal } from '../../platforms/xyebbs/versionAdapter';
import { adaptModrinthToVersionModal } from '../../platforms/modrinth/versionAdapter';
import { adaptCurseforgeToVersionModal } from '../../platforms/curseforge/versionAdapter';
import type { McmodStructuredItem } from '../../platforms/mcmod/types';
import type { BilibiliPack } from '../../types/legacy/bilibili';
import type { BbsmcPack } from '../../types/legacy/bbsmc';
import type { XyebbsPack } from '../../types/legacy/xyebbs';
import type { ModrinthPack } from '../../types/legacy/modrinth';
import type { CurseforgePack } from '../../types/legacy/curseforge';

export function buildVersionModalViewModel(
  platform: string,
  pack: unknown,
  extra?: Record<string, unknown>
): VersionModalViewModel {
  switch (platform) {
    case 'mcmod':
      return adaptMcmodToVersionModal(pack as McmodStructuredItem, extra);
    case 'bilibili':
      return adaptBilibiliToVersionModal(pack as BilibiliPack, extra);
    case 'bbsmc':
      return adaptBbsmcToVersionModal(pack as BbsmcPack, extra);
    case 'xyebbs':
      return adaptXyebbsToVersionModal(pack as XyebbsPack, extra);
    case 'modrinth':
      return adaptModrinthToVersionModal(pack as ModrinthPack, extra);
    case 'curseforge':
      return adaptCurseforgeToVersionModal(pack as CurseforgePack, extra);
    default:
      return adaptMcmodToVersionModal(pack as McmodStructuredItem, extra);
  }
}

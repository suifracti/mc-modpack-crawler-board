/**
 * Legacy Sidecar Repository implementation of PackRepository.
 * Bridges legacy sidecar arrays (window.xxxData) into unified domain models.
 */
import type { Platform, PlatformPack } from '../domain/types';
import type { PackRepository } from './PackRepository';
import { PLATFORM_CONFIGS } from './platformRegistry';
import { LegacySidecarLoader } from './LegacySidecarLoader';
import {
  mapLegacyMcmodToPack,
  mapLegacyBilibiliToPack,
  mapLegacyBbsmcToPack,
  mapLegacyXyebbsToPack,
  mapLegacyModrinthToPack,
  mapLegacyCurseforgeToPack,
} from '../domain/mappers';
import { mapStructuredMcmodToPack } from '../platforms/mcmod/mappers';
import type { McmodStructuredItem } from '../platforms/mcmod/types';
import type { LegacyMcmodRow } from '../types/legacy/mcmod';
import type { LegacyBilibiliItem } from '../types/legacy/bilibili';
import type { LegacyBbsmcItem } from '../types/legacy/bbsmc';
import type { LegacyXyebbsItem } from '../types/legacy/xyebbs';
import type { LegacyModrinthItem } from '../types/legacy/modrinth';
import type { LegacyCurseforgeItem } from '../types/legacy/curseforge';

export class LegacySidecarRepository implements PackRepository {
  private cache = new Map<Platform, PlatformPack[]>();
  private indexBySourceId = new Map<string, PlatformPack>();

  public isPlatformLoaded(platform: Platform): boolean {
    return this.cache.has(platform) || LegacySidecarLoader.isLoaded(platform);
  }

  public async loadPlatform(platform: Platform): Promise<PlatformPack[]> {
    if (this.cache.has(platform)) {
      return this.cache.get(platform)!;
    }

    await LegacySidecarLoader.load(platform);

    const config = PLATFORM_CONFIGS[platform];
    const rawArray = (
      typeof window !== 'undefined'
        ? (window as unknown as Record<string, unknown[]>)[config.globalVar]
        : []
    ) || [];

    const mapped: PlatformPack[] = [];

    switch (platform) {
      case 'mcmod': {
        const win = typeof window !== 'undefined' ? (window as unknown as { mcmodData?: McmodStructuredItem[] }) : null;
        if (win && win.mcmodData && Array.isArray(win.mcmodData)) {
          for (const item of win.mcmodData) {
            mapped.push(mapStructuredMcmodToPack(item));
          }
        } else {
          for (const row of rawArray as LegacyMcmodRow[]) {
            mapped.push(mapLegacyMcmodToPack(row));
          }
        }
        break;
      }
      case 'bilibili':
        for (const item of rawArray as LegacyBilibiliItem[]) {
          mapped.push(mapLegacyBilibiliToPack(item));
        }
        break;
      case 'bbsmc':
        for (const item of rawArray as LegacyBbsmcItem[]) {
          mapped.push(mapLegacyBbsmcToPack(item));
        }
        break;
      case 'xyebbs':
        for (const item of rawArray as LegacyXyebbsItem[]) {
          mapped.push(mapLegacyXyebbsToPack(item));
        }
        break;
      case 'modrinth':
        for (const item of rawArray as LegacyModrinthItem[]) {
          mapped.push(mapLegacyModrinthToPack(item));
        }
        break;
      case 'curseforge':
        for (const item of rawArray as LegacyCurseforgeItem[]) {
          mapped.push(mapLegacyCurseforgeToPack(item));
        }
        break;
    }

    this.cache.set(platform, mapped);
    for (const p of mapped) {
      this.indexBySourceId.set(`${p.platform}:${p.sourceId}`, p);
    }

    return mapped;
  }

  public async getPack(platform: Platform, sourceId: string): Promise<PlatformPack | null> {
    const key = `${platform}:${sourceId}`;
    if (this.indexBySourceId.has(key)) {
      return this.indexBySourceId.get(key)!;
    }
    await this.loadPlatform(platform);
    return this.indexBySourceId.get(key) || null;
  }
}

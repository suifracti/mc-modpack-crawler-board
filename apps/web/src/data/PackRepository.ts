/**
 * Repository interface for abstracting Modpack data access.
 */
import type { Platform, PlatformPack } from '../domain/types';

export interface PackRepository {
  /**
   * Loads all packs for a given platform.
   */
  loadPlatform(platform: Platform): Promise<PlatformPack[]>;

  /**
   * Retrieves a specific pack by platform and source ID.
   */
  getPack(platform: Platform, sourceId: string): Promise<PlatformPack | null>;

  /**
   * Checks whether the platform sidecar has already been loaded into memory.
   */
  isPlatformLoaded(platform: Platform): boolean;
}

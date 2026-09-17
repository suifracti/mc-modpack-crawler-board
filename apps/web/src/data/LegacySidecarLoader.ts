/**
 * Legacy Sidecar Dynamic Script Loader.
 * Decouples script injection and global variable resolution from UI components.
 */
import type { Platform } from '../domain/types';
import { PLATFORM_CONFIGS } from './platformRegistry';

export class LegacySidecarLoader {
  private static loadingPromises = new Map<Platform, Promise<void>>();
  private static loadedPlatforms = new Set<Platform>();

  /**
   * Checks if a platform's script has already executed and populated its global array.
   */
  public static isLoaded(platform: Platform): boolean {
    if (this.loadedPlatforms.has(platform)) return true;
    if (typeof window === 'undefined') return false;

    const config = PLATFORM_CONFIGS[platform];
    if (!config) return false;

    const globalVal = (window as unknown as Record<string, unknown>)[config.globalVar];
    if (Array.isArray(globalVal) && globalVal.length > 0) {
      this.loadedPlatforms.add(platform);
      return true;
    }
    return false;
  }

  /**
   * Dynamically loads the platform script and resolves when the global variable is ready.
   */
  public static load(platform: Platform): Promise<void> {
    if (this.isLoaded(platform)) {
      return Promise.resolve();
    }

    const existingPromise = this.loadingPromises.get(platform);
    if (existingPromise) {
      return existingPromise;
    }

    const config = PLATFORM_CONFIGS[platform];
    if (!config) {
      return Promise.reject(new Error(`Unknown platform: ${platform}`));
    }

    const promise = new Promise<void>((resolve, reject) => {
      if (typeof document === 'undefined') {
        resolve();
        return;
      }

      const script = document.createElement('script');
      script.src = config.src;
      script.async = true;

      script.onload = () => {
        this.loadedPlatforms.add(platform);
        this.loadingPromises.delete(platform);
        resolve();
      };

      script.onerror = () => {
        this.loadingPromises.delete(platform);
        reject(new Error(`Failed to load sidecar script for ${config.name} from ${config.src}`));
      };

      document.body.appendChild(script);
    });

    this.loadingPromises.set(platform, promise);
    return promise;
  }

  /**
   * Idle background prefetching for remaining platforms.
   */
  public static startIdlePrefetch(): void {
    const queue: Platform[] = ['bilibili', 'bbsmc', 'xyebbs', 'mcmod', 'modrinth', 'curseforge'];

    const step = () => {
      if (!queue.length) return;
      const nextPlat = queue.shift()!;
      if (this.isLoaded(nextPlat) || this.loadingPromises.has(nextPlat)) {
        step();
        return;
      }
      this.load(nextPlat)
        .catch((err) => console.warn(`Idle prefetch failed for ${nextPlat}:`, err))
        .finally(() => {
          setTimeout(step, 150);
        });
    };

    setTimeout(step, 400);
  }
}

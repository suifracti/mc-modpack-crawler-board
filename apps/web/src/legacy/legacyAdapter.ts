/**
 * Legacy Adapter and Global Compatibility Bridge.
 * Binds modern TypeScript utilities, domain logic, repository, and theme state to window
 * to guarantee 100% backward compatibility for existing DOM event handlers and DataTables.
 */
import { escHtml, escAttrJs } from '../utils/html';
import { fmtBigNum, numFmt, formatVFileSize, asArray, getVPanClass } from '../utils/format';
import { extractMcVersion } from '../domain/minecraft';
import { cleanPackKey, BILI_GENRE_BUZZWORDS, BILI_GENERIC_PACK_KEYS } from '../domain/packName';
import { getTheme, setTheme, toggleTheme, bindThemeControls, initTheme } from '../state/theme';
import { LegacySidecarLoader } from '../data/LegacySidecarLoader';
import { LegacySidecarRepository } from '../data/LegacySidecarRepository';
import { PLATFORM_CONFIGS } from '../data/platformRegistry';
import type { Platform } from '../domain/types';

export function setupLegacyBridge(): { repository: LegacySidecarRepository } {
  const repository = new LegacySidecarRepository();

  if (typeof window !== 'undefined') {
    const win = window as unknown as Record<string, unknown>;

    // 1. Pure Utilities
    win.escHtml = escHtml;
    win.escAttrJs = escAttrJs;
    win.fmtBigNum = fmtBigNum;
    win.numFmt = numFmt;
    win.formatVFileSize = formatVFileSize;
    win.asArray = asArray;
    win.getVPanClass = getVPanClass;

    // 2. Domain Recognition & Extraction
    win.extractVersion = extractMcVersion;
    win.cleanPackKey = cleanPackKey;
    win.BILI_GENRE_BUZZWORDS = BILI_GENRE_BUZZWORDS;
    win.BILI_GENERIC_PACK_KEYS = BILI_GENERIC_PACK_KEYS;

    // 3. Central Theme State
    win.getTheme = getTheme;
    win.setTheme = setTheme;
    win.toggleTheme = toggleTheme;

    // 4. Data Repository & Platform Loader
    win.packRepository = repository;

    // Backward-compatible PlatformLoader facade delegating to LegacySidecarLoader
    win.PlatformLoader = {
      ...PLATFORM_CONFIGS,
      load: (platId: Platform, cb?: () => void) => {
        LegacySidecarLoader.load(platId).then(() => {
          if (cb) cb();
        });
      },
    };
  }

  // Initialize theme and event delegation
  initTheme();
  bindThemeControls();

  return { repository };
}

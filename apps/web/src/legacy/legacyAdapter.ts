/**
 * Legacy Adapter and Global Compatibility Bridge.
 * Binds modern TypeScript utilities, domain logic, repository, theme state,
 * modular search, filter, router, modal, and platform card renderers to window
 * to guarantee 100% backward compatibility for existing DOM event handlers and DataTables.
 */
import { escHtml, escAttrJs } from '../utils/html';
import { fmtBigNum, numFmt, formatVFileSize, asArray, getVPanClass } from '../utils/format';
import { extractMcVersion } from '../domain/minecraft';
import { cleanPackKey, BILI_GENRE_BUZZWORDS, BILI_GENERIC_PACK_KEYS } from '../domain/packName';
import { groupBilibiliPacks } from '../domain/bilibiliGrouping';
import type { BilibiliGroupingDecision, BilibiliGroupingInput } from '../domain/bilibiliGrouping';
import { getTheme, setTheme, toggleTheme, bindThemeControls, initTheme } from '../state/theme';
import { LegacySidecarLoader } from '../data/LegacySidecarLoader';
import { LegacySidecarRepository } from '../data/LegacySidecarRepository';
import { PLATFORM_CONFIGS } from '../data/platformRegistry';
import { getMcmodTableColumns, attachMcmodRowAttributes, buildMcmodSearchText } from '../platforms/mcmod';
import type { Platform } from '../domain/types';

// Modular Subsystems (Phase 3C)
import {
  normalizeSearchKeyword,
  parseSearchQuery,
  matchDocument,
  filterItemsWithSearch,
  searchItemsWithReasons,
  searchCoordinator,
} from '../search';
import {
  matchCategories,
  matchVersion,
  matchLoader,
  matchServerOnly,
  matchPan,
  matchDateRange,
  filterStore,
  filterBilibiliPacks,
  filterBbsmcPacks,
  filterXyebbsPacks,
  filterModrinthPacks,
  filterCurseforgePacks,
  CAT_LABELS,
  getCategoryLabel,
} from '../filters';
import { platformRouter, parseHash, updateHash, listenToHashChange } from '../router';
import {
  versionModalController,
  buildVersionModalViewModel,
  buildMcVersionStrip,
  renderSimpleMarkdown,
  renderOverviewPane,
  renderChangelogPane,
  renderDownloadsPane,
  renderDiscussionsPane,
} from '../modals/version';
import { renderBiliGroupedCard, renderBiliFlatCard } from '../platforms/bilibili/renderer';
import { renderBbsmcCard } from '../platforms/bbsmc/renderer';
import { renderXyebbsCard } from '../platforms/xyebbs/renderer';
import { renderModrinthCard } from '../platforms/modrinth/renderer';
import { renderCurseforgeCard } from '../platforms/curseforge/renderer';
import {
  initFrontendDebug,
  recordSearchDebug,
  recordFilterDebug,
  recordNavigationDebug,
  recordModalDebug,
  recordRendererDebug,
  recordGroupingDecisionsDebug,
} from '../debug';

export function setupLegacyBridge(): { repository: LegacySidecarRepository } {
  const repository = new LegacySidecarRepository();

  if (typeof window !== 'undefined') {
    const win = window as unknown as Record<string, unknown>;

    // 0. Runtime Debug Instrumentation (Phase 3C.1)
    initFrontendDebug();
    win.recordSearchDebug = recordSearchDebug;
    win.recordFilterDebug = recordFilterDebug;
    win.recordNavigationDebug = recordNavigationDebug;
    win.recordModalDebug = recordModalDebug;
    win.recordRendererDebug = recordRendererDebug;

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
    // Phase 3G-F: single source of truth for the Bilibili grouping decision.
    // The domain function returns a Map; the legacy aggregator indexes by bvid as
    // a plain object, so expose a keyed object here (a Map indexed with [] would
    // silently yield undefined and quietly disable grouping).
    //
    // Phase 3G-F.1-A: each decision also carries the explainability payload
    // (`identityKey`, `episodeResidue`, `groupingReason`, and `rejectedAnchors` —
    // the candidate anchors the admissibility rules refused and why). The whole
    // decision object is forwarded verbatim so debug tooling can read the
    // rejection reasons without a second code path.
    win.groupBilibiliPacks = (records: BilibiliGroupingInput[]) => {
      const out: Record<string, BilibiliGroupingDecision> = {};
      for (const [bvid, decision] of groupBilibiliPacks(records)) out[bvid] = decision;
      // Phase 3G-F.1-A: publish the explainability payload (identity anchor,
      // residue, and the REJECTED candidate anchors) to the debug surface so a
      // runtime gate can assert on rejection reasons without a second code path.
      recordGroupingDecisionsDebug(out);
      return out;
    };

    // 3. Central Theme State
    win.getTheme = getTheme;
    win.setTheme = setTheme;
    win.toggleTheme = toggleTheme;

    // 4. Data Repository & Platform Loader
    win.packRepository = repository;

    // 5. MCMod Structured Table Columns & TS Renderers
    win.getMcmodTableColumns = getMcmodTableColumns;
    win.attachMcmodRowAttributes = attachMcmodRowAttributes;
    win.buildMcmodSearchText = buildMcmodSearchText;

    // 6. Search Subsystem (Phase 3C)
    win.normalizeSearchKeyword = normalizeSearchKeyword;
    win.parseSearchQuery = parseSearchQuery;
    win.matchDocument = matchDocument;
    win.filterItemsWithSearch = filterItemsWithSearch;
    win.searchItemsWithReasons = searchItemsWithReasons;
    win.searchCoordinator = searchCoordinator;

    // 7. Filter Subsystem (Phase 3C)
    win.matchCategories = matchCategories;
    win.matchVersion = matchVersion;
    win.matchLoader = matchLoader;
    win.matchServerOnly = matchServerOnly;
    win.matchPan = matchPan;
    win.matchDateRange = matchDateRange;
    win.filterStore = filterStore;
    win.filterBilibiliPacks = filterBilibiliPacks;
    win.filterBbsmcPacks = filterBbsmcPacks;
    win.filterXyebbsPacks = filterXyebbsPacks;
    win.filterModrinthPacks = filterModrinthPacks;
    win.filterCurseforgePacks = filterCurseforgePacks;
    win.CAT_LABELS = CAT_LABELS;
    win.getCategoryLabel = getCategoryLabel;

    // 8. Router Subsystem (Phase 3C)
    win.platformRouter = platformRouter;
    win.parseHash = parseHash;
    win.updateHash = updateHash;
    win.listenToHashChange = listenToHashChange;

    // 9. Version Modal Subsystem (Phase 3C)
    win.versionModalController = versionModalController;
    win.buildVersionModalViewModel = buildVersionModalViewModel;
    win.buildMcVersionStrip = buildMcVersionStrip;
    win.renderSimpleMarkdown = renderSimpleMarkdown;
    win.renderOverviewPane = renderOverviewPane;
    win.renderChangelogPane = renderChangelogPane;
    win.renderDownloadsPane = renderDownloadsPane;
    win.renderDiscussionsPane = renderDiscussionsPane;

    // 10. Platform Card Renderers (Phase 3C)
    win.renderBiliGroupedCard = renderBiliGroupedCard;
    win.renderBiliFlatCard = renderBiliFlatCard;
    win.renderBbsmcCard = renderBbsmcCard;
    win.renderXyebbsCard = renderXyebbsCard;
    win.renderModrinthCard = renderModrinthCard;
    win.renderCurseforgeCard = renderCurseforgeCard;

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

  // Initialize router
  platformRouter.init();

  return { repository };
}

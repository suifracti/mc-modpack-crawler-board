import type {PlatformUpdatePlan, UpdateBatchStatus} from './domain/updatePlans';
import type {AuditHistorySummary, AuditPlatformUpdate} from './domain/auditHistory';
import type { PublicLinkIndex } from './domain/crossPlatformLinkage';
import { ALL_PLATFORMS, PLATFORM_CONFIGS } from './data/platformRegistry';
import { groupBilibiliPacks } from './domain/bilibiliGrouping';
import type { Platform } from './domain/types';
import type { RecordPreview } from './domain/recordPreview';
import { getCategoryLabel } from './filters/platformFilters';
import { buildVersionModalViewModel } from './modals/version/buildViewModel';
import { generateSparklineSvg } from './platforms/mcmod/sparkline';
import {
  renderMcmodCard,
  MCMOD_COVER_FALLBACK,
  type McmodStructuredItem,
} from './platforms/mcmod';
import {
  parseMcmodTrendSeries,
  selectMcmodTrendRange,
  summarizeMcmodTrend,
  type McmodTrendPoint,
  type McmodTrendRange,
  type McmodTrendSeries,
} from './platforms/mcmod/trendChart';
import { renderBbsmcCard } from './platforms/bbsmc/renderer';
import { renderBiliFlatCard, renderBiliGroupedCard, type BiliGroup } from './platforms/bilibili/renderer';
import { renderCurseforgeCard } from './platforms/curseforge/renderer';
import { renderModrinthCard } from './platforms/modrinth/renderer';
import { renderXyebbsCard } from './platforms/xyebbs/renderer';
import {
  buildBbsmcSearchDocument,
  buildBilibiliSearchDocument,
  buildCurseforgeSearchDocument,
  buildMcmodSearchDocument,
  buildModrinthSearchDocument,
  buildXyebbsSearchDocument,
} from './search/searchDocument';
import type { BilibiliPack } from './types/legacy/bilibili';
import type { BbsmcPack } from './types/legacy/bbsmc';
import type { CurseforgePack } from './types/legacy/curseforge';
import type { ModrinthPack } from './types/legacy/modrinth';
import type { XyebbsPack } from './types/legacy/xyebbs';
import {
  releaseDetachedCoverImageRequest,
  renderCoverImage,
  startCoverImageRetry,
  type CoverImageState,
} from './utils/coverImage';
import {
  COVER_IMAGE_TIMEOUT_MS,
  finishImageLoad,
  imageRetryDelay,
  rememberFailedImage,
  stableImageSource,
  type ImageRetryTicket,
} from './utils/imageFallback';
import { bindCompositionAwareSearchInput } from './utils/compositionAwareSearch';
import { formatDisplayDate } from './utils/format';

export interface DesktopRecord {
  packVersion?: string;
  fileIndexes?: DesktopCurseforgeFileIndex[];
  mainFileId?: string | number;
  id: string;
  platform: Platform;
  sourceId: string;
  title: string;
  author: string;
  url: string;
  sourceIdOrigin: 'source' | 'index-fallback';
  summary: string;
  versions: string[];
  loaders: string[];
  categories: string[];
  updatedAt: string;
  coverUrl: string;
  environment: { status: string; certainty: string; label: string; sourceField: string | null };
  releases: Array<Record<string, unknown>>;
  raw: Record<string, unknown>;
  searchText: string;
  evidence: Array<{ label: string; value: string }>;
}

export interface DesktopCurseforgeFileIndex {
  fileId: string | number | null;
  filename: string;
  releaseType: string | number | null;
  gameVersion: string;
  modLoader: string | number | null;
}

export interface PersonalStatus {
  reference?: { title?: string; sourceUrl?: string; objectType: 'platform-record' | 'bilibili-video' };
  favorite: boolean;
  wantToPlay: boolean;
  played: boolean;
  rating: number | null;
  note: string;
  updatedAt: string | null;
}

export interface FavoriteUpdateEvent {
  id: string;
  platform: Platform;
  sourceId: string;
  title: string;
  sourceUrl: string;
  kind: 'release' | 'file-index' | 'download-links';
  summary: string;
  previousValues: string[];
  currentValues: string[];
  createdAt: string;
  readAt: string | null;
}

export interface FavoriteUpdateUnknown {
  key: string;
  platform: Platform;
  sourceId: string;
  title: string;
  sourceUrl: string;
  reason: string;
}

export interface FavoriteUpdatesResult {
  events: FavoriteUpdateEvent[];
  unreadCount: number;
  unknown: FavoriteUpdateUnknown[];
}

export type PersonalFilter = '' | 'favorite' | 'want_to_play' | 'played';

export interface DesktopComment {
  author?: string;
  user?: string;
  name?: string;
  text?: string;
  message?: string;
  content?: string;
  body?: string;
  replies?: DesktopComment[];
  [key: string]: unknown;
}

export interface DesktopCommentsResult {
  platform: Platform;
  sourceId: string;
  available: boolean;
  sourceFile: string | null;
  pageCount: number;
  comments: DesktopComment[];
  error?: string;
}

export interface DesktopAuditResult {
  history?: AuditHistorySummary[];
  scope?: string;
  platform_updates?: Record<string,AuditPlatformUpdate>;
  available: boolean;
  message: string | null;
  generated_at: string | null;
  stats: Record<string, unknown> | null;
  added: Array<Record<string, unknown>>;
  updated: Array<Record<string, unknown>>;
  removed: Array<Record<string, unknown>>;
  version_gained: Array<Record<string, unknown>>;
}

export interface DesktopPlatformState {
  id: Platform;
  name: string;
  icon: string;
  count: number;
  sourceFile: string | null;
  error: string | null;
  available: boolean;
}

export interface DesktopDataState {
  hasData: boolean;
  snapshotId: string | null;
  updatedAt: string | null;
  source: string | null;
  canonicalReady: boolean;
  dataRoot?: string;
  platforms: Record<Platform, DesktopPlatformState>;
}

export interface DesktopDataSnapshot {
  snapshotId: string;
  directory: string;
  active: boolean;
  createdAt: string | null;
  updatedAt: string | null;
  source: string;
  updatedPlatforms: string[];
  canonicalReady: boolean;
  platforms: Partial<Record<Platform, number>>;
  total: number;
}

export interface DesktopDataLibrary {
  dataRoot: string;
  activeSnapshotId: string | null;
  snapshots: DesktopDataSnapshot[];
}

export interface DesktopRecordQuery {
  bilibiliContent?: 'candidates' | 'secondary' | 'all' | 'excluded';
  query?: string;
  version?: string;
  loader?: string;
  category?: string;
  includedMods?: string[];
  includedModsExclude?: boolean;
  gameplayCategories?: string[];
  gameplayCategoriesExclude?: boolean;
  pan?: string;
  dateRange?: string;
  serverOnly?: boolean;
  personalStatus?: PersonalFilter;
  sort?: string;
  page?: number;
  pageSize?: number;
}

export interface DesktopFilterOption {
  value: string;
  count: number;
}

export interface DesktopUpdateStatus {
  batch?: UpdateBatchStatus;
  state: 'idle' | 'running' | 'success' | 'failed' | 'cancelled';
  taskId: string | null;
  platform: Platform | null;
  platformName?: string;
  phase: string;
  processed: number;
  total: number | null;
  startedAt?: string;
  endedAt?: string | null;
  error?: string | null;
  result?: { count: number; snapshotId: string; canonicalReady: boolean };
  logs: string[];
}

export interface DesktopApi {
  getRelations?: () => Promise<PublicLinkIndex>;
  getRecordPreview?: (platform: string, sourceId: string) => Promise<{ versions: Record<string, unknown>[]; fetchedAt: string; preview?: RecordPreview; provider?: string; providerLastFetch?: string | null }>;

  getPreviewVersions?: (platform: string, sourceId: string) => Promise<{ versions: Record<string, unknown>[]; fetchedAt: string; preview?: RecordPreview; provider?: string; providerLastFetch?: string | null }>;
  nativeDataDirectoryPicker?: boolean;
  getState: () => Promise<{ data: DesktopDataState; update: DesktopUpdateStatus }>;
  getPersonalLibrary: () => Promise<{ schema: number; entries: Record<string, PersonalStatus> }>;
  getFavoriteUpdates: () => Promise<FavoriteUpdatesResult>;
  markFavoriteUpdateRead: (id: string) => Promise<FavoriteUpdatesResult>;
  getMissingPersonalSources: () => Promise<{ entries: Record<string, PersonalStatus> }>;
  restorePersonalLibrary: (payload: unknown) => Promise<{ restored: number; 'skipped-conflict': number; invalid: number }>;
  updatePersonalStatus: (platform: Platform, sourceId: string, patch: Partial<Pick<PersonalStatus, 'favorite' | 'wantToPlay' | 'played' | 'rating' | 'note'>>) => Promise<{ key: string; status: PersonalStatus }>;
  getAuditDiff: (round?: number | string | null) => Promise<DesktopAuditResult>;
  getSourceRecord?: (platform: Platform, sourceId: string) => Promise<DesktopRecord | null>;
  getPlatformRecords: (platform: Platform, options?: DesktopRecordQuery) => Promise<{ bilibiliCounts?: { all: number; candidates: number; secondary: number; excluded: number }; platform: Platform; total: number; page: number; pageSize: number; records: DesktopRecord[]; availableVersions: string[]; availableLoaders: string[]; availableCategories: string[]; availableCategoryCounts?: DesktopFilterOption[]; availableIncludedMods: DesktopFilterOption[]; availableGameplayCategories: DesktopFilterOption[]; availablePans: string[]; error?: string | null }>;
  getPlatformComments: (platform: Platform, sourceId: string) => Promise<DesktopCommentsResult>;
  getDataLibrary: () => Promise<DesktopDataLibrary>;
  chooseDataDirectory: (path?: string) => Promise<{ cancelled: boolean; data?: DesktopDataState }>;
  activateDataSnapshot: (snapshotId: string) => Promise<{ data: DesktopDataState }>;
  deleteDataSnapshot: (snapshotId: string) => Promise<{ archived: { snapshotId: string; recoverablePath: string }; library: DesktopDataLibrary }>;
  exportActiveData: () => Promise<{ path: string; snapshotId: string; reused: boolean }>;
  openDataDirectory: (snapshotId?: string) => Promise<{ opened: boolean; path: string }>;
  startUpdateBatch?: (plans: PlatformUpdatePlan[]) => Promise<DesktopUpdateStatus>;
  startUpdate: (platform: Platform, options?: UpdateOptions) => Promise<DesktopUpdateStatus>;
  cancelUpdate: () => Promise<{ cancelled: boolean; reason?: string }>;
  openExternal: (url: string) => Promise<{ opened: boolean }>;
  openInAppWindow?: (url: string, title?: string) => Promise<{ opened: boolean }>;
  flushSession?: () => Promise<{ ok: boolean }>;
  onUpdateStatus: (callback: (status: DesktopUpdateStatus) => void) => () => void;
  onUpdateLog: (callback: (line: string) => void) => () => void;
  onDataChanged: (callback: (data: DesktopDataState) => void) => () => void;
}

declare global {
  interface Window {
    desktopApi: DesktopApi;
  }
}

type FilterPlatform = 'all' | Platform;
type DropdownId = 'version' | 'loader' | 'category' | 'pan' | 'date' | 'sort' | 'page-size' | 'personal' | 'update-platform' | 'sticky-sort';
type ViewMode = 'cards' | 'compact' | 'table';
type BiliViewMode = 'grouped' | 'flat';

type UpdateOptions = { limit?: number; mcmodLimit?: number; pages?: number; until?: string; mode?: string; otherMode?: string; coverOffset?: number };

interface UpdateBatchState {
  queue: Platform[];
  total: number;
  completed: number;
  options: UpdateOptions;
  handledTaskId: string;
}

interface InAppWindowState {
  record?: DesktopRecord;
  contentTab?: 'web' | 'overview' | 'versions' | 'gallery';
  id?: string;
  url: string;
  title: string;
  recordId?: string;
  maximized?: boolean;
  minimized?: boolean;
  activeTab?: 'web' | 'changelog';
  showChangelogPane?: boolean;
  sourcePaneTab?: 'source' | 'versions' | 'mods';
  showPersonalPane?: boolean;
  zoom?: string;
}

export type PickerType = 'included-mod' | 'gameplay-category' | 'category';
export type PickerSort = 'count_desc' | 'count_asc' | 'name_asc' | 'name_desc';

export interface PickerModalState {
  type: PickerType;
  search: string;
  limit: number;
  sort?: PickerSort;
}

const UNKNOWN_LOCAL_TEXT = '未知（本地数据未提供）';

export function getDesktopSearchPlaceholder(platform: FilterPlatform): string {
  if (platform === 'all') return '输入名称、版本、作者或平台已有字段…';
  if (platform === 'mcmod') return '输入名称、模组名、版本、作者或当前平台已有字段…';
  return '输入名称、版本、作者或当前平台已有字段…';
}

const PLATFORM_SITE_ICONS: Partial<Record<Platform, string>> = {
  mcmod: 'https://www.mcmod.cn/favicon.ico',
  bilibili: 'https://www.bilibili.com/favicon.ico',
  bbsmc: 'https://bbsmc.net/favicon.ico',
  xyebbs: 'https://www.xyebbs.com/favicon.ico',
  modrinth: 'https://modrinth.com/favicon.ico',
};

const platformItems: Array<{ id: FilterPlatform; name: string }> = [
  { id: 'all', name: '全部平台' },
  ...ALL_PLATFORMS.map((id) => ({ id, name: PLATFORM_CONFIGS[id].name })),
];

const PLATFORM_ACCENTS: Record<Platform, string> = {
  mcmod: '#F59E0B',
  bilibili: '#FB7299',
  bbsmc: '#0284C7',
  xyebbs: '#059669',
  modrinth: '#00AF5C',
  curseforge: '#F97316',
};

const PLATFORM_TAGLINES: Record<Platform, string> = {
  mcmod: '权威词条、版本适配与模组组成',
  bilibili: 'UP 主自制发布、版本流与下载线索',
  bbsmc: '社区资源、作者信息与开源发布',
  xyebbs: '论坛发布、版本标签与渠道信息',
  modrinth: '官方项目、版本与 Loader 契约',
  curseforge: '项目档案、版本发布与文件入口',
};

const PLATFORM_COVER_FALLBACKS: Record<Platform, string> = {
  mcmod: MCMOD_COVER_FALLBACK,
  bilibili: 'data:image/svg+xml;charset=utf-8,%3Csvg xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22 width%3D%22400%22 height%3D%22225%22 viewBox%3D%220 0 400 225%22%3E%3Crect width%3D%22400%22 height%3D%22225%22 fill%3D%22%23fff0f5%22%2F%3E%3Ctext x%3D%2250%25%22 y%3D%2250%25%22 dominant-baseline%3D%22middle%22 text-anchor%3D%22middle%22 fill%3D%22%23fb7299%22 font-family%3D%22sans-serif%22 font-size%3D%2216%22%3EB%E7%AB%99%20%E6%9A%82%E6%97%A0%E5%B0%81%E9%9D%A2%3C%2Ftext%3E%3C%2Fsvg%3E',
  bbsmc: 'data:image/svg+xml;charset=utf-8,%3Csvg xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22 width%3D%22400%22 height%3D%22225%22 viewBox%3D%220 0 400 225%22%3E%3Crect width%3D%22400%22 height%3D%22225%22 fill%3D%22%23eef8ff%22%2F%3E%3Ctext x%3D%2250%25%22 y%3D%2250%25%22 dominant-baseline%3D%22middle%22 text-anchor%3D%22middle%22 fill%3D%22%230284c7%22 font-family%3D%22sans-serif%22 font-size%3D%2216%22%3EBBSMC%20%E6%9A%82%E6%97%A0%E5%B0%81%E9%9D%A2%3C%2Ftext%3E%3C%2Fsvg%3E',
  xyebbs: 'data:image/svg+xml;charset=utf-8,%3Csvg xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22 width%3D%22400%22 height%3D%22225%22 viewBox%3D%220 0 400 225%22%3E%3Crect width%3D%22400%22 height%3D%22225%22 fill%3D%22%23effcf5%22%2F%3E%3Ctext x%3D%2250%25%22 y%3D%2250%25%22 dominant-baseline%3D%22middle%22 text-anchor%3D%22middle%22 fill%3D%22%23059669%22 font-family%3D%22sans-serif%22 font-size%3D%2216%22%3EXYEBBS%20%E6%9A%82%E6%97%A0%E5%B0%81%E9%9D%A2%3C%2Ftext%3E%3C%2Fsvg%3E',
  modrinth: 'data:image/svg+xml;charset=utf-8,%3Csvg xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22 width%3D%22400%22 height%3D%22225%22 viewBox%3D%220 0 400 225%22%3E%3Crect width%3D%22400%22 height%3D%22225%22 fill%3D%22%23ecfdf5%22%2F%3E%3Ctext x%3D%2250%25%22 y%3D%2250%25%22 dominant-baseline%3D%22middle%22 text-anchor%3D%22middle%22 fill%3D%22%2300af5c%22 font-family%3D%22sans-serif%22 font-size%3D%2216%22%3EModrinth%20%E6%9A%82%E6%97%A0%E5%B0%81%E9%9D%A2%3C%2Ftext%3E%3C%2Fsvg%3E',
  curseforge: 'data:image/svg+xml;charset=utf-8,%3Csvg xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22 width%3D%22400%22 height%3D%22225%22 viewBox%3D%220 0 400 225%22%3E%3Crect width%3D%22400%22 height%3D%22225%22 fill%3D%22%23fff4ed%22%2F%3E%3Ctext x%3D%2250%25%22 y%3D%2250%25%22 dominant-baseline%3D%22middle%22 text-anchor%3D%22middle%22 fill%3D%22%23f97316%22 font-family%3D%22sans-serif%22 font-size%3D%2216%22%3ECurseForge%20%E6%9A%82%E6%97%A0%E5%B0%81%E9%9D%A2%3C%2Ftext%3E%3C%2Fsvg%3E',
};

const state = {
  data: null as DesktopDataState | null,
  update: null as DesktopUpdateStatus | null,
  platform: 'all' as FilterPlatform,
  query: '',
  version: '',
  loader: '',
  category: '',
  includedMods: [] as string[],
  includedModsExclude: false,
  includedModSearch: '',
  includedModsExpanded: false,
  gameplayCategories: [] as string[],
  gameplayCategoriesExclude: false,
  gameplayCategoriesExpanded: false,
  pan: '',
  dateRange: '',
  serverOnly: false,
  personalFilter: '' as PersonalFilter,
  moreFiltersOpen: false,
  sort: 'updated_desc',
  stickyFollowMode: true,
  stickyModsExpanded: false,
  stickyModsExpandAll: false,
  stickyCategoriesExpanded: false,
  stickyModSearch: '',
  stickyCatSearch: '',
  viewMode: 'cards' as ViewMode,
  biliViewMode: 'grouped' as BiliViewMode,
  bilibiliContent: 'candidates' as 'candidates' | 'secondary' | 'all' | 'excluded',
  bilibiliCounts: {all:0,candidates:0,secondary:0,excluded:0},
  biliGroups: [] as BiliGroup[],
  records: [] as DesktopRecord[],
  total: 0,
  availableVersions: [] as string[],
  availableLoaders: [] as string[],
  availableCategories: [] as string[],
  availableCategoryCounts: [] as DesktopFilterOption[],
  availableIncludedMods: [] as DesktopFilterOption[],
  availableGameplayCategories: [] as DesktopFilterOption[],
  availablePans: [] as string[],
  page: 1,
  pageSize: 24,
  hasMore: false,
  openDropdown: '' as DropdownId | '',
  updatePlatform: 'bilibili' as Platform,
  updatePlatforms: ['bilibili'] as Platform[],
  updateBatch: null as UpdateBatchState | null,
  mcmodUpdateMode: 'new' as 'new' | 'trend' | 'versions' | 'all',
  mcmodOldLimit: 50,
  otherUpdateMode: 'catalog' as 'catalog' | 'existing',
  updateOtherLimit: '',
  updateBiliPages: 1,
  updateFormError: '',
  updateLogsExpanded: false,
  expandedMcmodTableMods: '' as string,
  selected: null as DesktopRecord | null,
  trendChart: null as { record: DesktopRecord; range: McmodTrendRange } | null,
  imagePreview: null as { url: string; title: string } | null,
  commentPreviewRecord: null as DesktopRecord | null,
  commentPreviewQuery: '',
  commentPreviewTab: 'comments' as 'comments' | 'web',
  inAppWindow: null as InAppWindowState | null,
  inAppWindows: [] as InAppWindowState[],
  inAppWindowPreviousSelected: null as DesktopRecord | null,
  updateOpen: false,
  dataImportOpen: false,
  dataImportPath: '',
  dataLibrary: null as DesktopDataLibrary | null,
  dataLibraryLoading: false,
  dataLibraryError: '',
  dataExportPath: '',
  dataNotice: '',
  audit: null as DesktopAuditResult | null,
  auditOpen: false,
  auditLoading: false,
  auditError: '',
  compareOpen: false,
  compareIds: [] as string[],
  compareRecords: {} as Record<string, DesktopRecord>,
  personalLibrary: {} as Record<string, PersonalStatus>,
  missingPersonalSources: {} as Record<string, PersonalStatus>,
  personalProfileOpen: false,
  favoriteUpdates: null as FavoriteUpdatesResult | null,
  favoriteUpdatesLoading: false,
  favoriteUpdatesError: '',
  comments: { sourceId: '', loading: false, available: false, pageCount: 0, comments: [] as DesktopComment[], sourceFile: null as string | null, error: '' },
  loading: true,
  recordsError: '',
  message: '',
  logs: [] as string[],
  pickerModal: null as PickerModalState | null,
};

function isStaticSite(): boolean {
  return typeof document !== 'undefined' && document.documentElement.dataset.staticSite === 'true';
}

let root: HTMLElement;
let searchTimer: number | undefined;
let mainSearchCompositionInput: HTMLInputElement | null = null;
let mainSearchRenderPending = false;
let detailFocusAfterRender = false;
const personalNoteTimers = new Map<string, number>();
let profileFocusAfterRender: 'close' | 'trigger' | '' = '';
let platformFilterFocusAfterRender: 'included-mod-search' | '' = '';
let pickerFocusAfterRender: 'picker-modal-search' | '' = '';
let stickyFocusAfterRender: 'sticky-mod-search' | 'sticky-cat-search' | '' = '';
let trendFocusAfterRender: 'close' | 'trigger' | '' = '';
let trendReturnRecordId = '';
let mcmodTableFocusRecordId = '';
let activeLoadRequestId = 0;
const pagesLoadProgress = new Map<Platform, { phase: string; completed: number; total: number }>();
function isStaticOverview(): boolean {
  return isStaticSite() && state.platform === 'all' && !state.query.trim()
    && !state.version && !state.loader && !state.category
    && state.includedMods.length === 0 && state.gameplayCategories.length === 0
    && !state.pan && !state.dateRange && !state.serverOnly && !state.personalFilter;
}
function pagesSourceLoadLabel(platform: Platform): string {
  const progress = pagesLoadProgress.get(platform);
  if (!progress) return '未加载';
  if (progress.phase === 'ready') return '已加载';
  if (progress.phase === 'failed') return '加载失败';
  return progress.total ? `加载中 ${progress.completed} / ${progress.total}` : '加载中…';
}
function pagesLoadingMessage(): string {
  const pending = [...pagesLoadProgress.values()].filter((item) => item.phase === 'loading');
  const total = pending.reduce((sum, item) => sum + item.total, 0);
  const completed = pending.reduce((sum, item) => sum + item.completed, 0);
  return total ? `正在加载公开记录：已读取 ${completed} / ${total} 个数据分片…` : '正在准备公开记录…';
}
const mcmodLiveModIndex = new Map<string, Array<{ name: string; url: string; categoryUrl: string }>>();
const mcmodModIndexRequests = new Map<string, Promise<void>>();

function ensureMcmodModIndex(record: DesktopRecord): Promise<void> {
  if (isStaticSite()) return Promise.resolve();
  if (mcmodLiveModIndex.has(record.id) || !/^\d+$/.test(record.sourceId)) return Promise.resolve();
  const existing = mcmodModIndexRequests.get(record.id);
  if (existing) return existing;
  const url = `https://www.mcmod.cn/modpack/${record.sourceId}.html`;
  const request = fetch(`/api/proxy-page?url=${encodeURIComponent(url)}`)
    .then(async (response) => {
      if (!response.ok) return;
      const document = new DOMParser().parseFromString(await response.text(), 'text/html');
      const list = document.querySelector('li.text-area[data-id="2"] .class-relation-list') || document.querySelector('.class-relation-list');
      if (!list) return;
      const entries: Array<{ name: string; url: string; categoryUrl: string }> = [];
      list.querySelectorAll('li.modlist').forEach((group) => {
        const categoryUrl = safeExternalUrl((group.querySelector('a[href*="/class/category/"]') as HTMLAnchorElement | null)?.href);
        group.querySelectorAll('ul li p a[href*="/class/"]').forEach((node) => {
          const link = node as HTMLAnchorElement;
          const name = link.textContent?.trim() || '';
          if (name) entries.push({ name, url: safeExternalUrl(link.href), categoryUrl });
        });
      });
      if (entries.length) mcmodLiveModIndex.set(record.id, entries);
    })
    .catch(() => {})
    .finally(() => { mcmodModIndexRequests.delete(record.id); });
  mcmodModIndexRequests.set(record.id, request);
  return request;
}

interface PlatformCacheEntry {
  bilibiliCounts?: {all:number;candidates:number;secondary:number;excluded:number};
  records: DesktopRecord[];
  biliGroups: BiliGroup[];
  total: number;
  availableVersions: string[];
  availableLoaders: string[];
  availableCategories: string[];
  availableCategoryCounts?: DesktopFilterOption[];
  availableIncludedMods: DesktopFilterOption[];
  availableGameplayCategories: DesktopFilterOption[];
  availablePans: string[];
}

const platformRecordCache = new Map<string, PlatformCacheEntry>();

function isDefaultPlatformFilters(): boolean {
  return state.bilibiliContent === 'candidates' && !state.query
    && !state.version
    && !state.loader
    && !state.category
    && state.includedMods.length === 0
    && state.gameplayCategories.length === 0
    && !state.pan
    && !state.dateRange
    && !state.serverOnly
    && !state.personalFilter;
}

function esc(value: unknown): string {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function textOrUnknown(value: string | null | undefined): string {
  return value && value.trim() ? esc(value) : `<span class="unknown">${UNKNOWN_LOCAL_TEXT}</span>`;
}

function formatTime(value: string | null | undefined): string {
  if (!value || /^0+(?:\.0+)?$/.test(String(value).trim())) return UNKNOWN_LOCAL_TEXT;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? UNKNOWN_LOCAL_TEXT : date.toLocaleString('zh-CN', { dateStyle: 'medium', timeStyle: 'short' });
}

function currentRecords(): DesktopRecord[] {
  return state.records;
}

const EMPTY_PERSONAL_STATUS: PersonalStatus = {
  favorite: false,
  wantToPlay: false,
  played: false,
  rating: null,
  note: '',
  updatedAt: null,
};

function personalKey(record: DesktopRecord): string {
  return `${record.platform}:${record.sourceId}`;
}

function personalStatusForKey(key: string): PersonalStatus {
  return { ...EMPTY_PERSONAL_STATUS, ...(state.personalLibrary[key] || {}) };
}

function personalStatus(record: DesktopRecord): PersonalStatus {
  return personalStatusForKey(personalKey(record));
}

function isPersonalWritable(record: DesktopRecord): boolean {
  return record.sourceIdOrigin !== 'index-fallback';
}

function personalUnavailableReason(record: DesktopRecord): string {
  return record.sourceIdOrigin === 'index-fallback'
    ? '来源缺少稳定 ID，当前标识由数组序号生成，不能保存个人状态'
    : '';
}

function personalTargetAttributes(record: DesktopRecord): string {
  return `data-personal-platform="${esc(record.platform)}" data-personal-source-id="${esc(record.sourceId)}"`;
}

function hasServerRuntimeClue(record: DesktopRecord): boolean {
  if (['required', 'optional', 'supported'].includes(record.environment.status)) return true;
  if (record.environment.status === 'unsupported' || record.environment.status === 'unknown') return false;
  return record.raw?.has_server === true;
}

function environmentDisplay(record: DesktopRecord): string {
  if (record.environment.status === 'unknown') return UNKNOWN_LOCAL_TEXT;
  if (record.environment.status === 'unsupported') return '明确不支持服务端运行线索';
  return `有服务端运行线索（${record.environment.label}）`;
}

function renderRecordDetailsButton(record: DesktopRecord, index: number): string {
  return `<button type="button" class="personal-favorite-button record-detail-button" data-action="select-record" data-index="${index}" aria-label="查看${esc(record.title)}详情">查看详情</button>`;
}

function renderPersonalCardActions(record: DesktopRecord, index: number): string {
  const details = renderRecordDetailsButton(record, index);
  if (!isPersonalWritable(record)) {
    return `<div class="personal-card-actions personal-unavailable" title="${esc(personalUnavailableReason(record))}">${details}<span>个人标记不可保存：缺少稳定来源 ID</span></div>`;
  }
  const status = personalStatus(record);
  const labels = [
    status.wantToPlay ? '<span class="personal-state-chip is-want">想玩</span>' : '',
    status.played ? '<span class="personal-state-chip is-played">玩过</span>' : '',
  ].join('');
  const label = record.platform === 'bilibili'
    ? (status.favorite ? '★ 已收藏当前视频' : '☆ 收藏当前视频')
    : (status.favorite ? '★ 已收藏' : '☆ 收藏');
  const title = record.platform === 'bilibili'
    ? (status.favorite ? '取消当前视频收藏' : '收藏当前视频')
    : (status.favorite ? '取消收藏' : '加入收藏');
  return `<div class="personal-card-actions">${details}<button type="button" class="personal-favorite-button ${status.favorite ? 'is-active' : ''}" data-action="toggle-personal" data-personal-field="favorite" data-index="${index}" ${personalTargetAttributes(record)} aria-pressed="${status.favorite}" title="${title}">${label}</button>${status.rating ? `<span class="personal-rating-mini">★ ${status.rating}/5</span>` : ''}${labels}</div>`;
}

function renderPersonalCardZone(content: string, className = ''): string {
  if (!content) return '';
  return `<footer class="desktop-card-personal-zone ${className}"><span class="desktop-card-personal-label">我的状态</span>${content}</footer>`;
}

function renderPersonalDetail(record: DesktopRecord): string {
  if (!isPersonalWritable(record)) {
    return `<div class="detail-section personal-detail-section personal-unavailable"><h3>我的整合包库</h3><p>${esc(personalUnavailableReason(record))}。请等待来源提供稳定 ID 后再保存。</p></div>`;
  }
  const status = personalStatus(record);
  const ratingButtons = [1, 2, 3, 4, 5].map((rating) => `<button type="button" class="personal-rating-button ${status.rating === rating ? 'is-active' : ''}" data-action="set-personal-rating" data-rating="${rating}" aria-label="${rating} 分">★</button>`).join('');
  const currentVideoLabels = record.platform === 'bilibili'
    ? { favorite: status.favorite ? '★ 已收藏当前视频' : '☆ 收藏当前视频', wantToPlay: status.wantToPlay ? '取消想玩当前视频' : '加入想玩（保存视频线索）' }
    : { favorite: status.favorite ? '★ 已收藏' : '☆ 收藏', wantToPlay: '🎯 想玩' };
  return `<div class="detail-section personal-detail-section"><div class="personal-detail-heading"><div><h3>我的整合包库</h3><span class="detail-submeta">仅保存在本机，不会写入平台采集数据</span></div><button type="button" class="personal-favorite-button ${status.favorite ? 'is-active' : ''}" data-action="toggle-personal" data-personal-field="favorite" data-index="${state.records.indexOf(record)}" ${personalTargetAttributes(record)} aria-pressed="${status.favorite}">${currentVideoLabels.favorite}</button></div><div class="personal-flag-row"><button type="button" class="personal-flag-button ${status.wantToPlay ? 'is-active' : ''}" data-action="set-personal-flag" data-personal-field="wantToPlay" ${personalTargetAttributes(record)} aria-pressed="${status.wantToPlay}">${currentVideoLabels.wantToPlay}</button><button type="button" class="personal-flag-button ${status.played ? 'is-active' : ''}" data-action="set-personal-flag" data-personal-field="played" ${personalTargetAttributes(record)} aria-pressed="${status.played}">✓ 玩过</button></div><div class="personal-rating-row"><span>个人评分</span><div class="personal-rating-buttons">${ratingButtons.replaceAll('data-action="set-personal-rating"', `data-action="set-personal-rating" ${personalTargetAttributes(record)}`)}<button type="button" class="personal-rating-clear" data-action="set-personal-rating" data-rating="0" ${personalTargetAttributes(record)}>清除</button></div></div><label class="personal-note-label" for="personal-note">个人备注</label><textarea id="personal-note" class="personal-note-input" data-personal-note ${personalTargetAttributes(record)} maxlength="20000" placeholder="写下安装、游玩或更新备注…">${esc(status.note)}</textarea><span class="personal-note-hint">${document.documentElement.dataset.staticSite === 'true' ? '输入即保存在此浏览器' : '停止输入后自动保存'}</span></div>`;
}

function existingSearchText(record: DesktopRecord): string {
  const raw = record.raw as never;
  try {
    const document = record.platform === 'mcmod'
      ? buildMcmodSearchDocument(raw as never)
      : record.platform === 'bilibili'
        ? buildBilibiliSearchDocument(raw as never)
        : record.platform === 'bbsmc'
          ? buildBbsmcSearchDocument(raw as never)
          : record.platform === 'xyebbs'
            ? buildXyebbsSearchDocument(raw as never)
            : record.platform === 'modrinth'
              ? buildModrinthSearchDocument(raw as never)
              : buildCurseforgeSearchDocument(raw as never);
    return document.allTextLower || '';
  } catch {
    return record.searchText;
  }
}

function safeExternalUrl(value: unknown): string {
  try {
    const url = new URL(String(value || ''));
    return url.protocol === 'http:' || url.protocol === 'https:' ? url.toString() : '';
  } catch {
    return '';
  }
}

function safeImageUrl(value: unknown): string {
  let text = String(value ?? '').trim();
  if (text.startsWith('//')) text = `https:${text}`;
  if (text.startsWith('data:image/')) return text;
  return safeExternalUrl(text);
}

function imageValueUrls(value: unknown): string[] {
  if (typeof value === 'string') {
    const direct = safeImageUrl(value);
    if (direct) return [direct];
    const embedded = value.match(/data-image-url=["']([^"']+)["']/i)?.[1];
    const embeddedUrl = safeImageUrl(embedded);
    return embeddedUrl ? [embeddedUrl] : [];
  }
  if (Array.isArray(value)) return value.flatMap((item) => imageValueUrls(item));
  if (value && typeof value === 'object') {
    const item = value as Record<string, unknown>;
    return imageValueUrls(item.url ?? item.src ?? item.image ?? item.full ?? item.dataFull);
  }
  return [];
}

function bilibiliCoverUrl(value: unknown): string {
  const url = safeImageUrl(value).replace(/^http:/, 'https:');
  if (!url) return '';
  return url.includes('@') ? url : `${url}@480w_300h_1c.webp`;
}

function recordRealCoverUrl(record: DesktopRecord): string {
  const raw = record.raw || {};
  const galleryFirst = Array.isArray(raw.gallery) ? raw.gallery[0] : undefined;
  const candidate = record.platform === 'bilibili'
    ? bilibiliCoverUrl(raw.pic ?? raw.cover_url ?? raw.coverUrl)
    : record.platform === 'bbsmc'
      ? safeImageUrl(raw.featured_gallery ?? galleryFirst ?? raw.icon_url)
      : record.platform === 'xyebbs'
        ? safeImageUrl(raw.head_url ?? raw.icon_url)
        : safeImageUrl(raw.icon_url ?? raw.logo_url ?? raw.cover_url ?? raw.coverUrl ?? record.coverUrl);
  if (candidate) return candidate;
  if (record.platform === 'mcmod') {
    const c0 = imageValueUrls(raw.c0)[0];
    if (c0) return c0;
  }
  return '';
}

function recordImageUrls(record: DesktopRecord): string[] {
  const raw = record.raw || {};
  const keys = record.platform === 'bbsmc'
    ? ['featured_gallery', 'gallery']
    : record.platform === 'bilibili'
      ? ['pic', 'images', 'gallery']
      : ['gallery', 'images', 'intro_images', 'screenshots', 'cover_url', 'coverUrl', 'icon_url', 'head_url'];
  const urls = keys.flatMap((key) => imageValueUrls(raw[key]));
  const cover = recordRealCoverUrl(record);
  return [...new Set([cover, ...urls].filter(Boolean))];
}

function asNumber(value: unknown): number {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
}

function toBilibiliPack(record: DesktopRecord): BilibiliPack {
  const raw = { ...(record.raw || {}) } as Record<string, unknown>;
  const versions = valueList(raw.all_versions ?? raw.allVersions ?? raw.mc_version ?? record.versions);
  const links = Array.isArray(raw.download_links) ? raw.download_links : [];
  return {
    ...raw,
    bvid: String(raw.bvid || record.sourceId),
    title: String(raw.title || record.title),
    author: String(raw.author || record.author),
    url: String(raw.url || record.url),
    views: asNumber(raw.views),
    danmaku: asNumber(raw.danmaku),
    likes: asNumber(raw.likes),
    favorites: asNumber(raw.favorites),
    reply: asNumber(raw.reply),
    share: asNumber(raw.share),
    has_server: hasServerRuntimeClue(record),
    pic: String(raw.pic || raw.cover || ''),
    pub_time: String(raw.pub_time || raw.published_at || raw.date || record.updatedAt || ''),
    pub_timestamp: asNumber(raw.pub_timestamp),
    mc_version: String(raw.mc_version || versions[0] || ''),
    all_versions: versions,
    loaders: valueList(raw.loaders ?? record.loaders),
    categories: valueList(raw.categories ?? record.categories),
    download_links: links,
  } as BilibiliPack;
}

export function buildBilibiliGroups(records: DesktopRecord[]): BiliGroup[] {
  const packs = records.map(toBilibiliPack);
  const decisions = groupBilibiliPacks(packs.map((pack) => ({ bvid: pack.bvid, title: pack.title, author: pack.author })));
  const groups = new Map<string, BiliGroup>();
  const timestampOf = (pack: BilibiliPack): number => asNumber(pack.pub_timestamp) || Date.parse(String(pack.pub_time || '')) || 0;

  for (const pack of packs) {
    const key = decisions.get(pack.bvid)?.groupKey || `__raw_${pack.bvid}`;
    let group = groups.get(key);
    if (!group) {
      group = {
        key,
        items: [],
        allVersions: new Set<string>(),
        allLoaders: new Set<string>(),
        allCategories: new Set<string>(),
        allGroups: new Set<string>(),
        allLinks: [],
        totalViews: 0,
        totalLikes: 0,
        totalCoins: 0,
        totalFavs: 0,
        totalDanmaku: 0,
        totalReply: 0,
        totalShare: 0,
        latestTimestamp: 0,
        latestPubTime: '',
      };
      groups.set(key, group);
    }
    group.items.push(pack);
    const timestamp = timestampOf(pack);
    if (timestamp >= group.latestTimestamp) {
      group.latestTimestamp = timestamp;
      group.latestPubTime = String(pack.pub_time || '');
      group.pic = String(pack.pic || '');
    }
    for (const version of valueList(pack.mc_version)) if (version !== '未知') group.allVersions.add(version);
    for (const version of valueList(pack.all_versions)) if (version !== '未知') group.allVersions.add(version);
    for (const loader of valueList(pack.loaders)) group.allLoaders.add(loader);
    for (const category of valueList(pack.categories)) group.allCategories.add(category);
    if (pack.qq_group) group.allGroups.add(String(pack.qq_group));
    if (Array.isArray(pack.download_links)) {
      for (const link of pack.download_links) {
        if (!link || typeof link !== 'object') continue;
        const item = link as unknown as Record<string, unknown>;
        group.allLinks.push({ name: String(item.name || item.pan_name || item.type || ''), url: String(item.url || ''), type: String(item.type || '') });
      }
    }
    group.totalViews += asNumber(pack.views);
    group.totalLikes += asNumber(pack.likes);
    group.totalCoins += asNumber(pack.coins);
    group.totalFavs += asNumber(pack.favorites);
    group.totalDanmaku += asNumber(pack.danmaku);
    group.totalReply += asNumber(pack.reply);
    group.totalShare += asNumber(pack.share);
    if (pack.has_server) group.has_server = true;
    if (pack.has_group_version) group.has_group_version = true;
    if (pack.pack_version && !group.pack_version) group.pack_version = String(pack.pack_version);
    if (pack.group_version_note && !group.group_version_note) group.group_version_note = String(pack.group_version_note);
    if (pack.desc_updated_at && !group.desc_updated_at) group.desc_updated_at = String(pack.desc_updated_at);
  }

  for (const group of groups.values()) {
    group.items.sort((left, right) => timestampOf(right) - timestampOf(left));
  }
  return [...groups.values()];
}

function statusFromLibrary(personalLibrary: Record<string, PersonalStatus>, platform: Platform, sourceId: string): PersonalStatus {
  return { ...EMPTY_PERSONAL_STATUS, ...(personalLibrary[`${platform}:${sourceId}`] || {}) };
}

function matchesPersonalStatus(status: PersonalStatus, filter: PersonalFilter): boolean {
  if (filter === 'favorite') return status.favorite;
  if (filter === 'want_to_play') return status.wantToPlay;
  if (filter === 'played') return status.played;
  return true;
}

export function filterBilibiliGroupsByPersonalStatus(
  groups: BiliGroup[],
  personalLibrary: Record<string, PersonalStatus>,
  filter: PersonalFilter,
): BiliGroup[] {
  if (!filter) return groups;
  return groups.filter((group) => group.items.some((item) => matchesPersonalStatus(statusFromLibrary(personalLibrary, 'bilibili', item.bvid), filter)));
}

function hasAnyPersonalStatus(status: PersonalStatus): boolean {
  return status.favorite || status.wantToPlay || status.played || status.rating !== null || Boolean(status.note);
}

function recordForBilibiliPack(pack: BilibiliPack): DesktopRecord | null {
  return state.records.find((record) => record.platform === 'bilibili' && record.sourceId === pack.bvid) || null;
}

function renderBilibiliGroupPersonalActions(group: BiliGroup): string {
  const latest = group.items[0];
  const record = latest ? recordForBilibiliPack(latest) : null;
  if (!record || !latest) return '';
  const index = state.records.indexOf(record);
  const details = index >= 0 ? renderRecordDetailsButton(record, index) : '';
  const status = personalStatus(record);
  const target = personalTargetAttributes(record);
  const targetLabel = `<span class="bili-personal-target" title="${esc(record.title)}">保存至当前视频 · ${esc(record.sourceId)}</span>`;
  if (!isPersonalWritable(record)) {
    return `<div class="bili-personal-actions personal-unavailable">${details}${targetLabel}<span>${esc(personalUnavailableReason(record))}</span></div>`;
  }
  return `<div class="bili-personal-actions">${details}${targetLabel}<button type="button" class="personal-favorite-button ${status.favorite ? 'is-active' : ''}" data-action="toggle-personal" data-personal-field="favorite" ${target} aria-pressed="${status.favorite}">${status.favorite ? '★ 取消收藏当前视频' : '☆ 收藏当前视频'}</button><button type="button" class="personal-flag-button ${status.wantToPlay ? 'is-active' : ''}" data-action="toggle-personal" data-personal-field="wantToPlay" ${target} aria-pressed="${status.wantToPlay}">${status.wantToPlay ? '取消想玩当前视频' : '加入想玩（保存视频线索）'}</button></div>`;
}

function renderBilibiliGroupPersonalSummary(group: BiliGroup): string {
  const marked = group.items
    .map((pack) => ({ pack, status: statusFromLibrary(state.personalLibrary, 'bilibili', pack.bvid) }))
    .filter((item) => hasAnyPersonalStatus(item.status));
  const scope = `本次查询的 ${group.items.length} 个视频成员`;
  const memberButtons = marked.map(({ pack, status }) => {
    const record = recordForBilibiliPack(pack);
    if (!record) return '';
    const labels = [
      status.favorite ? '收藏' : '',
      status.wantToPlay ? '想玩' : '',
      status.played ? '玩过' : '',
      status.rating !== null ? `评分 ${status.rating}/5` : '',
      status.note ? '有备注' : '',
    ].filter(Boolean).join(' · ');
    return `<button type="button" class="bili-personal-member" data-action="select-bili-member" data-bili-bvid="${esc(pack.bvid)}" ${personalTargetAttributes(record)} title="打开该视频详情并编辑状态"><span>${esc(pack.title || record.title)}</span><small>${esc(pack.bvid)} · ${esc(labels)}</small></button>`;
  }).filter(Boolean).join('');
  if (!marked.length) return `<span class="bili-personal-summary-empty" title="${scope}；收藏、评分和备注均按视频保存">${group.items.length} 个关联视频 · 暂无标记</span>`;
  return `<details class="bili-personal-summary"><summary>已标记 ${marked.length}/${group.items.length} 个视频</summary><div class="bili-personal-members">${memberButtons}</div></details>`;
}

function biliSortValue(group: BiliGroup, sort: string): number {
  if (sort === 'views_desc') return group.totalViews;
  if (sort === 'likes_desc') return group.totalLikes;
  if (sort === 'favs_desc') return group.totalFavs;
  if (sort === 'coins_desc') return group.totalCoins;
  if (sort === 'share_desc') return group.totalShare;
  if (sort === 'reply_desc' || sort === 'comments_desc') return group.totalReply;
  if (sort === 'danmaku_desc') return group.totalDanmaku;
  return group.latestTimestamp;
}

function sortBilibiliGroups(groups: BiliGroup[]): BiliGroup[] {
  return [...groups].sort((left, right) => biliSortValue(right, state.sort) - biliSortValue(left, state.sort));
}

function legacyPackBase(record: DesktopRecord): Record<string, unknown> {
  const raw = { ...(record.raw || {}) } as Record<string, unknown>;
  const gallery = recordImageUrls(record);
  const links = Array.isArray(raw.download_links) ? raw.download_links : [];
  return {
    ...raw,
    title: String(raw.title || record.title),
    author: String(raw.author || record.author || '未知'),
    url: String(raw.url || record.url),
    description: String(raw.description || raw.desc || raw.summary || record.summary || ''),
    project_id: Number(raw.project_id || raw.projectId || record.sourceId) || record.sourceId,
    projectId: raw.projectId || raw.project_id || record.sourceId,
    downloads: asNumber(raw.downloads),
    followers: asNumber(raw.followers),
    views: asNumber(raw.views),
    replies: asNumber(raw.replies ?? raw.comments),
    has_server: hasServerRuntimeClue(record),
    categories: valueList(raw.categories ?? record.categories),
    mc_versions: valueList(raw.mc_versions ?? raw.mcVersions ?? record.versions),
    mc_version: String(raw.mc_version || valueList(raw.mcVersions)[0] || record.versions[0] || ''),
    loaders: valueList(raw.loaders ?? record.loaders),
    download_links: links,
    releases: Array.isArray(raw.releases) ? raw.releases : record.releases,
    gallery,
    featured_gallery: gallery[0] || '',
    icon_url: String(raw.icon_url || raw.iconUrl || gallery[0] || ''),
    head_url: String(raw.head_url || gallery[0] || ''),
    logo_url: String(raw.logo_url || raw.logoUrl || gallery[0] || ''),
    date_modified: String(raw.date_modified || raw.modifiedAt || raw.modified_at || record.updatedAt || ''),
    created_date: String(raw.created_date || raw.date_created || raw.createdAt || ''),
    client_side: String(raw.client_side || raw.clientSide || ''),
    server_side: String(raw.server_side || raw.serverSide || ''),
    env_display: environmentDisplay(record),
  };
}

function renderPlatformRichCard(record: DesktopRecord): string {
  const base = legacyPackBase(record);
  if (record.platform === 'mcmod') return renderMcmodCard(base as unknown as McmodStructuredItem);
  if (record.platform === 'bbsmc') return renderBbsmcCard(base as unknown as BbsmcPack);
  if (record.platform === 'xyebbs') return renderXyebbsCard(base as unknown as XyebbsPack);
  if (record.platform === 'modrinth') return renderModrinthCard(base as unknown as ModrinthPack);
  if (record.platform === 'curseforge') return renderCurseforgeCard(base as unknown as CurseforgePack);
  return renderRecord(record, state.records.indexOf(record));
}

function renderImageButton(url: string, title: string, className = '', fallback = ''): string {
  const safeUrl = safeImageUrl(url);
  if (!safeUrl) return '';
  const source = fallback ? stableImageSource(safeUrl, fallback) : safeUrl;
  const fallbackData = fallback ? ` data-original-src="${esc(safeUrl)}" data-fallback-src="${esc(fallback)}"` : '';
  return `<button type="button" class="image-preview-trigger ${className}" data-action="open-image" data-image-url="${esc(source)}" data-image-title="${esc(title)}" title="点击查看${esc(title)}"><img src="${esc(source)}"${fallbackData} alt="${esc(title)}" loading="lazy" referrerpolicy="no-referrer"></button>`;
}

function renderCommentImages(comment: DesktopComment, title: string): string {
  const urls = imageValueUrls(comment.images);
  if (!urls.length) return '';
  return `<div class="comment-image-gallery">${urls.map((url, index) => renderImageButton(url, `${title}图片${index + 1}`, 'comment-image')).join('')}</div>`;
}

function rawText(record: DesktopRecord, keys: string[]): string {
  for (const key of keys) {
    const value = record.raw[key];
    if (value !== undefined && value !== null && String(value).trim()) return String(value);
  }
  return '';
}

function rawList(record: DesktopRecord, keys: string[]): string[] {
  for (const key of keys) {
    const value = record.raw[key];
    if (Array.isArray(value)) return value.filter(Boolean).map(String);
    if (typeof value === 'string' && value.trim()) return value.split(/[,，|/]/).map((item) => item.trim()).filter(Boolean);
  }
  return [];
}

function valueList(value: unknown): string[] {
  if (Array.isArray(value)) return value.filter(Boolean).map(String);
  if (typeof value === 'string' && value.trim()) return value.split(/[,，|/]/).map((item) => item.trim()).filter(Boolean);
  return [];
}

function rawRecords(record: DesktopRecord, keys: string[]): Array<Record<string, unknown>> {
  for (const key of keys) {
    const value = record.raw[key];
    if (Array.isArray(value)) {
      return value.filter(Boolean).map((item) => typeof item === 'object' && item !== null ? item as Record<string, unknown> : { name: String(item) });
    }
  }
  return [];
}

function commentBody(comment: DesktopComment): string {
  const value = comment.text ?? comment.message ?? comment.content ?? comment.body;
  if (typeof value === 'string') return value;
  if (value && typeof value === 'object') {
    const nested = value as Record<string, unknown>;
    return String(nested.message ?? nested.text ?? nested.content ?? '').trim();
  }
  return '';
}

function renderComments(comments: DesktopComment[]): string {
  if (!comments.length) return '<div class="empty-evidence">当前没有可读取的独立评论正文。</div>';
  return `<div class="comment-list">${comments.map((comment, index) => {
    const author = String(comment.author ?? comment.user ?? comment.name ?? `评论 ${index + 1}`);
    const replies = Array.isArray(comment.replies) ? comment.replies : [];
    const replyHtml = replies.length ? `<div class="comment-replies">${replies.map((reply) => `<div class="comment-reply"><strong>${esc(String(reply.author ?? reply.user ?? '回复'))}</strong><span>${textOrUnknown(commentBody(reply))}</span>${renderCommentImages(reply, '回复')}</div>`).join('')}</div>` : '';
    return `<article class="comment-item"><div class="comment-head"><strong>${esc(author)}</strong><span>${esc(String(comment.time ?? comment.date ?? comment.floor ?? ''))}</span></div><p>${textOrUnknown(commentBody(comment))}</p>${renderCommentImages(comment, '评论')}${replyHtml}</article>`;
  }).join('')}</div>`;
}

function renderDropdown(id: DropdownId, selected: string, options: Array<{ value: string; label: string }>, disabled = false): string {
  const selectedOption = options.find((option) => option.value === selected) || options[0];
  const isOpen = state.openDropdown === id;
  const isActive = Boolean(selected);
  return `<div class="ui-dropdown ${isOpen ? 'is-open' : ''}" data-dropdown-root="${id}">
    <button type="button" class="ui-dropdown-trigger ${isActive ? 'is-active' : ''}" data-action="toggle-dropdown" data-dropdown="${id}" aria-haspopup="listbox" aria-expanded="${isOpen}" ${disabled ? 'disabled' : ''}><span>${esc(selectedOption?.label || '')}</span><span class="ui-dropdown-chevron" aria-hidden="true">⌄</span></button>
    <div class="ui-dropdown-menu" id="${id}-menu" role="listbox" aria-label="${esc(selectedOption?.label || '')}">${options.map((option) => `<button type="button" class="ui-dropdown-option ${option.value === selected ? 'is-selected' : ''}" data-action="select-dropdown" data-dropdown="${id}" data-value="${esc(option.value)}" role="option" aria-selected="${option.value === selected}"><span>${esc(option.label)}</span>${option.value === selected ? '<span class="ui-dropdown-check" aria-hidden="true">✓</span>' : ''}</button>`).join('')}</div>
  </div>`;
}

function renderFilterDropdown(id: 'version' | 'loader' | 'category' | 'pan', values: string[], selected: string, emptyLabel: string): string {
  const options = [{ value: '', label: emptyLabel }, ...values.map((value) => ({
    value,
    label: id === 'category' ? getCategoryLabel(value) : value,
  }))];
  const selectedOption = options.find((option) => option.value === selected) || options[0];
  const isOpen = state.openDropdown === id;
  const isActive = Boolean(selected);
  const pickerAction = id === 'category' && values.length > 12
    ? `<button type="button" class="ui-dropdown-picker-action" data-action="open-picker" data-picker="category">弹窗查看全部分类（共 ${values.length} 类）...</button>`
    : '';
  return `<div class="ui-dropdown ${isOpen ? 'is-open' : ''}" data-dropdown-root="${id}">
    <button type="button" class="ui-dropdown-trigger ${isActive ? 'is-active' : ''}" data-action="toggle-dropdown" data-dropdown="${id}" aria-haspopup="listbox" aria-expanded="${isOpen}"><span>${esc(selectedOption?.label || '')}</span><span class="ui-dropdown-chevron" aria-hidden="true">⌄</span></button>
    <div class="ui-dropdown-menu" id="${id}-menu" role="listbox" aria-label="${esc(selectedOption?.label || '')}">
      ${pickerAction}
      ${options.map((option) => {
        const subtext = id === 'category' && option.value && option.label !== option.value ? ` (${esc(option.value)})` : '';
        return `<button type="button" class="ui-dropdown-option ${option.value === selected ? 'is-selected' : ''}" data-action="select-dropdown" data-dropdown="${id}" data-value="${esc(option.value)}" role="option" aria-selected="${option.value === selected}"><span>${esc(option.label)}${subtext}</span>${option.value === selected ? '<span class="ui-dropdown-check" aria-hidden="true">✓</span>' : ''}</button>`;
      }).join('')}
    </div>
  </div>`;
}

function renderSortDropdown(dropdownId: DropdownId = 'sticky-sort'): string {
  const options = state.platform === 'bilibili'
    ? [
      { value: 'updated_desc', label: '最新发布' },
      { value: 'views_desc', label: '播放最多' },
      { value: 'likes_desc', label: '点赞最多' },
      { value: 'favs_desc', label: '收藏最多' },
      { value: 'coins_desc', label: '投币最多' },
      { value: 'share_desc', label: '分享最多' },
      { value: 'reply_desc', label: '评论最多' },
      { value: 'danmaku_desc', label: '弹幕最多' },
    ]
    : [
      { value: 'updated_desc', label: '最近更新' },
      { value: 'downloads_desc', label: '下载最多' },
      { value: 'views_desc', label: '浏览最多' },
      { value: 'followers_desc', label: '关注最多' },
      { value: 'likes_desc', label: '点赞最多' },
      { value: 'comments_desc', label: '评论最多' },
      { value: 'created_desc', label: '创建时间' },
      { value: 'title_asc', label: '名称 A-Z' },
    ];
  return renderDropdown(dropdownId, state.sort, options);
}

function renderPersonalDropdown(): string {
  return renderDropdown('personal', state.personalFilter, [
    { value: '', label: '全部状态' },
    { value: 'favorite', label: '已收藏' },
    { value: 'want_to_play', label: '想玩' },
    { value: 'played', label: '玩过' },
  ]);
}

function panLabel(value: string): string {
  const labels: Record<string, string> = {
    official: '官方原站',
    Modrinth: 'Modrinth',
    CurseForge: 'CurseForge',
  };
  return labels[value] || value;
}


function renderActiveFilters(): string {
  const filters: Array<{ key: string; label: string }> = [];
  if (state.query) filters.push({ key: 'query', label: `关键词：${state.query}` });
  if (state.version) filters.push({ key: 'version', label: `版本：${state.version}` });
  if (state.loader) filters.push({ key: 'loader', label: `Loader：${state.loader}` });
  if (state.category && state.platform !== 'curseforge') filters.push({ key: 'category', label: `分类：${getCategoryLabel(state.category)}` });
  if (state.platform === 'mcmod') state.includedMods.forEach((value) => filters.push({ key: `includedMod:${value}`, label: `${state.includedModsExclude ? '排除组合' : '包含模组'}：${value}` }));
  if (state.platform === 'curseforge') state.gameplayCategories.forEach((value) => filters.push({ key: `gameplayCategory:${value}`, label: `${state.gameplayCategoriesExclude ? '排除玩法' : '玩法分类'}：${getCategoryLabel(value)}` }));
  if (state.pan) filters.push({ key: 'pan', label: `渠道：${panLabel(state.pan)}` });
  if (state.dateRange) filters.push({ key: 'dateRange', label: `时间：${state.dateRange}` });
  if (state.serverOnly) filters.push({ key: 'serverOnly', label: '有服务端运行线索' });
  if (state.personalFilter) filters.push({ key: 'personalStatus', label: state.personalFilter === 'favorite' ? '个人：已收藏' : state.personalFilter === 'want_to_play' ? '个人：想玩' : '个人：玩过' });
  if (!filters.length) return '';
  return `<div class="desktop-active-filters" aria-label="当前筛选条件">${filters.map((filter) => `<button type="button" class="desktop-active-filter" data-action="clear-filter" data-filter="${esc(filter.key)}">${esc(filter.label)} <span aria-hidden="true">×</span></button>`).join('')}<button type="button" class="desktop-active-clear" data-action="clear-filters">清空全部</button></div>`;
}


function renderUpdateModal(): string {
  if (!state.updateOpen) return '';
  const update = state.update;
  const coverageResult = update?.result as (DesktopUpdateStatus['result'] & { coverage?: string; observedCount?: number; newCount?: number; updatedCount?: number; failedCount?: number; failedRequests?: number }) | undefined;
  const running = update?.state === 'running';
  const selectedPlatforms = state.updatePlatforms;
  const batch = state.updateBatch;
  const progress = update && typeof update.total === 'number' && update.total > 0 ? Math.min(100, Math.round((update.processed / update.total) * 100)) : null;
  const logLines = (state.logs.length ? state.logs : update?.logs || []).slice(-80);
  const otherPlatforms = selectedPlatforms.filter((platform) => platform !== 'mcmod');
  const modeText = state.mcmodUpdateMode === 'new'
    ? '只探测新包；每个新包会抓取当时可取得的真实走势与版本记录。'
    : state.mcmodUpdateMode === 'versions'
      ? '补抓所有尚未核实的旧包版本历史与更新正文，不重复抓取走势或封面；已确认无日志的包会跳过。'
    : state.mcmodUpdateMode === 'trend'
      ? '只检查已收录旧包；缝合过期走势、补抓逐版更新正文，并另行检查缺失封面（不会覆盖已有封面）。'
      : '先探测新包，再刷新旧包基础指标、走势、逐版更新正文和缺失封面。旧包工作量较大。';
  const visibleLogs = state.updateLogsExpanded ? logLines : logLines.slice(-3);
  const formatLog = (line: string): string => {
    if (line.startsWith('desktop collector: ')) {
      const platform = line.match(/^desktop collector: (\w+)/)?.[1] as Platform | undefined;
      return `已启动${platform ? PLATFORM_CONFIGS[platform]?.name || platform : '平台'}采集器`;
    }
    if (!line.startsWith('DESKTOP_EVENT ')) return line;
    try {
      const event = JSON.parse(line.slice('DESKTOP_EVENT '.length)) as { platform?: string; phase?: string; processed?: number; total?: number; error?: string };
      return [event.platform ? PLATFORM_CONFIGS[event.platform as Platform]?.name || event.platform : '', event.phase || '', event.total ? `${event.processed || 0}/${event.total}` : '', event.error || ''].filter(Boolean).join(' · ');
    } catch { return line; }
  };
  return `<div class="modal-backdrop update-backdrop" data-action="close-update-panel" role="dialog" aria-modal="true" aria-labelledby="update-title">
    <section class="modal-panel update-modal-panel" onclick="event.stopPropagation()">
      <header class="modal-header">
        <div class="modal-title-wrap">
          <span class="eyebrow">本地快照更新</span>
          <h2 id="update-title">数据更新</h2>
          <p>按所选顺序逐个平台更新；每个平台完成校验后才切换快照。收起面板后任务继续运行，不影响浏览。</p>
        </div>
        <button type="button" class="modal-close update-close" data-action="close-update-panel" aria-label="${running ? '收起更新面板，继续浏览' : '关闭更新面板'}">×</button>
      </header>
      <div class="update-section-head"><div><strong>1 · 更新平台</strong><span>已选 ${selectedPlatforms.length} 个</span></div><div><button type="button" class="button secondary small" data-action="select-all-update-platforms" ${running ? 'disabled' : ''}>全选</button><button type="button" class="button secondary small" data-action="clear-update-platforms" ${running ? 'disabled' : ''}>清空</button></div></div>
      <div class="update-platform-grid" role="group" aria-label="选择要更新的平台">${ALL_PLATFORMS.map((id) => {
        const selected = selectedPlatforms.includes(id);
        return `<button type="button" class="update-platform-choice ${selected ? 'is-selected' : ''}" data-action="toggle-update-platform" data-platform="${id}" aria-pressed="${selected}" ${running ? 'disabled' : ''}><span>${platformIcon(id)} ${esc(PLATFORM_CONFIGS[id].name)}</span><span class="update-platform-check" aria-hidden="true">${selected ? '✓' : '＋'}</span></button>`;
      }).join('')}</div>
      <div class="update-section-head"><div><strong>2 · 更新范围</strong><span>按平台分别生效</span></div></div>
      ${selectedPlatforms.includes('mcmod') ? `<div class="update-scope-card"><label class="field-label" for="update-mode">MC百科 · 新包与旧包</label><select id="update-mode" class="field" ${running ? 'disabled' : ''}><option value="new" ${state.mcmodUpdateMode === 'new' ? 'selected' : ''}>只探测新包（推荐日常使用）</option><option value="versions" ${state.mcmodUpdateMode === 'versions' ? 'selected' : ''}>补抓全部旧包版本历史</option><option value="trend" ${state.mcmodUpdateMode === 'trend' ? 'selected' : ''}>只更新旧包走势、版本与缺失封面</option><option value="all" ${state.mcmodUpdateMode === 'all' ? 'selected' : ''}>新包 + 旧包指标、走势、版本与封面</option></select><p class="update-scope-help">${modeText}</p>${state.mcmodUpdateMode !== 'new' ? `<label class="field-label" for="update-mcmod-limit">本次最多检查多少个旧包</label><input id="update-mcmod-limit" class="field" type="number" min="1" max="100000" step="1" value="${state.mcmodOldLimit}" ${running ? 'disabled' : ''}><p class="update-scope-help">${state.mcmodUpdateMode === 'versions' ? `当前快照已收录 ${formatCount(state.data?.platforms.mcmod.count || 0)} 个 MC百科包；会检查尚未核实的版本页，完成后才切换快照。` : `当前快照已收录 ${formatCount(state.data?.platforms.mcmod.count || 0)} 个 MC百科包。默认最多 50 个走势/版本候选，另检查最多同数的缺失封面候选；近期确认原站无封面的包 30 天内不重复请求。仅新包模式按连续 8 个缺失 ID 自动停止，不受此数量限制。`}</p>` : ''}</div>` : ''}
      ${otherPlatforms.length ? `<div class="update-scope-card"><label class="field-label" for="update-other-mode">其他五站 · 更新内容</label><select id="update-other-mode" class="field" ${running ? 'disabled' : ''}><option value="catalog" ${state.otherUpdateMode === 'catalog' ? 'selected' : ''}>刷新平台列表／B站有限发现</option><option value="existing" ${state.otherUpdateMode === 'existing' ? 'selected' : ''}>复查旧包版本／B站公开页</option></select><label class="field-label" for="update-limit">${state.otherUpdateMode === 'existing' ? '每个平台本次复查旧包数' : '每个平台采集上限'}</label><input id="update-limit" class="field" type="number" min="1" max="100000" step="1" placeholder="${state.otherUpdateMode === 'existing' ? selectedPlatforms.includes('bilibili') ? '留空：B站最多30个，其他站50个' : '留空：每站轮流复查50个' : '留空：沿用各平台默认策略'}" value="${esc(state.updateOtherLimit)}" ${running ? 'disabled' : ''}><p class="update-scope-help">${state.otherUpdateMode === 'existing' ? '按最久未核对优先；其他四站读取项目版本接口。B站仅观察已收录视频的主站公开HTML，更新实际可见字段；未观察到的置顶、字幕和下载线索保留旧值。B站每次最多30页、当天累计最多30个候选；无登录，不调用业务API。失败时保留旧数据。' : '列表模式更新项目概要。B站从已知视频的合集读取候选，再逐页确认，仅代表局部发现。每次最多30页、当天累计最多30个候选；无登录，不调用业务API。'} ${esc(otherPlatforms.map((id) => PLATFORM_CONFIGS[id].name).join('、'))}</p></div>` : ''}
      ${state.updateFormError ? `<p class="update-form-error" role="alert">${esc(state.updateFormError)}</p>` : ''}
      <div class="update-actions"><button class="button primary" data-action="start-update" ${running || !selectedPlatforms.length ? 'disabled' : ''}>${running ? '更新进行中' : `开始更新${selectedPlatforms.length > 1 ? `（${selectedPlatforms.length} 个平台）` : ''}`}</button>${running ? '<button class="button danger" data-action="cancel-update">取消本批任务</button>' : ''}</div>
      <div class="update-section-head"><div><strong>3 · 执行状态</strong><span>${batch ? `批次 ${Math.min(batch.completed + 1, batch.total)}/${batch.total}` : update && update.state !== 'idle' ? '上次任务' : '等待开始'}</span></div></div>
      <div class="update-status ${update?.state || 'idle'}" role="status"><div class="status-line"><strong>${esc(!update?.phase || update.phase === 'idle' ? '等待开始' : update.phase)}</strong><span>${update?.platform ? esc(PLATFORM_CONFIGS[update.platform]?.name || update.platform) : ''}</span></div>${progress === null ? (running ? '<div class="status-meta">处理总量暂未确定</div>' : '') : `<div class="progress-track"><span style="width:${progress}%"></span></div><div class="status-meta">${progress}% · ${update?.processed}/${update?.total}</div>`}${coverageResult?.coverage === 'public-video-html-bounded' ? `<div class="status-meta">B站主站HTML局部覆盖 · 观察 ${Number(coverageResult.observedCount || 0)} 页 · 新增 ${Number(coverageResult.newCount || 0)} 条 · 更新 ${Number(coverageResult.updatedCount || 0)} 条 · 失败 ${Number(coverageResult.failedCount ?? coverageResult.failedRequests ?? 0)} 次</div>` : ''}${update?.error ? `<div class="error-box">${esc(update.error)}</div>` : ''}</div>
      <div class="update-log-head"><strong>${batch || running || !update || update.state === 'idle' ? '任务日志' : '上次任务日志'} <span>${logLines.length} 条</span></strong><button type="button" class="button secondary small" data-action="toggle-update-logs" aria-expanded="${state.updateLogsExpanded}">${state.updateLogsExpanded ? '收起' : '查看全部'}</button></div>
      <div class="update-log-list" role="log" aria-label="数据更新任务日志">${visibleLogs.length ? visibleLogs.map((line) => `<div class="update-log-line ${(line.startsWith('B站主站HTML局部覆盖：') ? /失败 [1-9]\d* 次/.test(line) : /失败|错误|error|failed/i.test(line)) ? 'is-error' : ''}">${esc(formatLog(line))}</div>`).join('') : '<p>开始更新后显示任务进度与日志。</p>'}</div>
    </section>
  </div>`;
}

function refreshUpdateDock(): void {
  const update = state.update;
  const active = update?.state === 'running' || Boolean(state.updateBatch);
  const dock = root.querySelector<HTMLButtonElement>('.update-task-dock');
  if (dock) {
    dock.hidden = !active;
    const platform = update?.platform ? PLATFORM_CONFIGS[update.platform]?.name || update.platform : '数据';
    const phase = update?.state === 'running' ? update.phase || '采集中' : '准备下一平台';
    const progress = update && typeof update.total === 'number' && update.total > 0
      ? Math.min(100, Math.round((update.processed / update.total) * 100)) : null;
    const title = dock.querySelector<HTMLElement>('.update-task-title');
    const detail = dock.querySelector<HTMLElement>('.update-task-detail');
    const bar = dock.querySelector<HTMLElement>('.update-task-track span');
    if (title) title.textContent = `${platform}更新中`;
    if (detail) detail.textContent = `${phase}${progress === null ? '' : ` · ${progress}%`} · 点此查看`;
    if (bar) bar.style.width = `${progress ?? 0}%`;
  }
  const nav = root.querySelector<HTMLButtonElement>('.top-action-btn[data-action="toggle-update"]');
  nav?.classList.toggle('is-running', active);
}

function renderDataImportModal(): string {
  if (!state.dataImportOpen) return '';
  const library = state.dataLibrary;
  const snapshots = library?.snapshots || [];
  const sourceLabel = (source: string): string => source === 'desktop-update' ? '应用更新' : source === 'local-import' ? '外部导入' : '本地快照';
  const snapshotRows = snapshots.map((snapshot) => {
    const platformNames = Object.entries(snapshot.platforms)
      .filter(([, count]) => Number(count) > 0)
      .map(([platform]) => PLATFORM_CONFIGS[platform as Platform]?.name || platform);
    return `<article class="data-snapshot-row ${snapshot.active ? 'is-active' : ''}">
      <div class="data-snapshot-main"><div class="data-snapshot-title"><strong>${snapshot.active ? '当前使用' : sourceLabel(snapshot.source)}</strong>${snapshot.canonicalReady ? '<span class="data-snapshot-badge">Canonical</span>' : ''}</div><code>${esc(snapshot.snapshotId)}</code><p>${esc(formatTime(snapshot.updatedAt || snapshot.createdAt || ''))} · ${formatCount(snapshot.total)} 条 · ${esc(platformNames.join('、') || '未识别平台')}</p></div>
      <div class="data-snapshot-actions"><button type="button" class="button ghost" data-action="open-data-directory" data-snapshot-id="${esc(snapshot.snapshotId)}">打开目录</button><button type="button" class="button ghost data-copy-path" data-action="copy-data-path" data-path="${esc(snapshot.directory)}" title="复制快照目录路径">复制路径</button>${snapshot.active ? '<span class="data-snapshot-current">已选中</span>' : `<button type="button" class="button secondary" data-action="activate-data-snapshot" data-snapshot-id="${esc(snapshot.snapshotId)}">切换到此快照</button><button type="button" class="button danger data-snapshot-delete" data-action="delete-data-snapshot" data-snapshot-id="${esc(snapshot.snapshotId)}">删除</button>`}</div>
    </article>`;
  }).join('');
  return `<div class="modal-backdrop data-import-backdrop" data-action="close-data-import" role="dialog" aria-modal="true" aria-labelledby="data-import-title">
    <section class="modal-panel data-import-panel" onclick="event.stopPropagation()">
      <header class="modal-header">
        <div class="modal-title-wrap"><span class="eyebrow">LOCAL DATA</span><h2 id="data-import-title">本地数据管理</h2><p>快照、导入和导出统一放在应用数据目录。切换只改变当前读取的快照，不删除原数据。</p></div>
        <button type="button" class="modal-close" data-action="close-data-import" aria-label="关闭更换数据面板">×</button>
      </header>
      <section class="data-root-card"><div><span>统一数据目录</span><code>${esc(library?.dataRoot || state.data?.dataRoot || '正在读取…')}</code></div><div class="data-root-actions"><button type="button" class="button secondary" data-action="open-data-directory">浏览目录</button><button type="button" class="button secondary" data-action="copy-data-path" data-path="${esc(library?.dataRoot || state.data?.dataRoot || '')}">复制路径</button><button type="button" class="button secondary" data-action="export-active-data" ${state.data?.hasData ? '' : 'disabled'}>导出当前数据</button></div></section>
      ${state.dataExportPath ? `<div class="notice">已导出到：<code>${esc(state.dataExportPath)}</code></div>` : ''}
      ${state.dataNotice ? `<div class="notice">${esc(state.dataNotice)}</div>` : ''}
      <div class="data-library-heading"><div><strong>可用快照</strong><span>共 ${snapshots.length} 个</span></div><button type="button" class="button ghost" data-action="refresh-data-library">刷新</button></div>
      <div class="data-snapshot-list">${state.dataLibraryLoading ? '<div class="loading-state">正在读取数据快照…</div>' : state.dataLibraryError ? `<div class="error-box">${esc(state.dataLibraryError)}</div>` : snapshotRows || '<div class="empty-evidence">还没有可用快照。</div>'}</div>
      <details class="data-import-details"><summary>导入外部数据包</summary><p>可选择本应用导出的目录，或包含 data、converted_output 数据的旧目录。导入成功后会复制为新快照，不直接在外部目录上运行。</p><div class="data-import-input-row"><input id="data-import-path" class="field data-import-path" value="${esc(state.dataImportPath)}" placeholder="粘贴数据包或 data 目录路径" autocomplete="off" spellcheck="false">${window.desktopApi.nativeDataDirectoryPicker ? '<button type="button" class="button secondary" data-action="browse-data-import">选择目录</button>' : ''}<button type="button" class="button primary" data-action="confirm-data-import">导入并使用</button></div></details>
      ${state.message ? `<div class="error-box">${esc(state.message)}</div>` : ''}
    </section>
  </div>`;
}

function formatMetric(value: unknown): string {
  const number = Number(value);
  if (!Number.isFinite(number)) return '—';
  if (number >= 100_000_000) return `${(number / 100_000_000).toFixed(1).replace(/\.0$/, '')}亿`;
  if (number >= 10_000) return `${(number / 10_000).toFixed(1).replace(/\.0$/, '')}万`;
  return number.toLocaleString('zh-CN');
}

interface DesktopMetricItem {
  label: string;
  text: string;
  isComment?: boolean;
}

function recordMetricItems(record: DesktopRecord): DesktopMetricItem[] {
  const raw = record.raw || {};
  const entries: Array<[string, unknown, boolean?]> = record.platform === 'mcmod'
    ? [['👁 浏览', raw.views], ['💬 评论', raw.commentsCount, true], ['⭐ 收藏', raw.favorites]]
    : record.platform === 'bilibili'
      ? [['▶ 播放', raw.views], ['👍 点赞', raw.likes], ['💬 评论', raw.reply, true]]
      : record.platform === 'bbsmc'
        ? [['⬇ 下载', raw.downloads], ['👁 关注', raw.followers], ['💬 评论', raw.comments, true]]
        : record.platform === 'xyebbs'
          ? [['⬇ 下载', raw.downloads], ['👁 浏览', raw.views], ['💬 评论', raw.comments, true]]
          : [['⬇ 下载', raw.downloads], ['👁 关注', raw.followers], ['👍 点赞', raw.likes]];
  return entries
    .filter(([, value]) => value !== undefined && value !== null && value !== '')
    .map(([label, value, isComment]) => ({
      label,
      text: `${label} ${formatMetric(value)}`,
      isComment: Boolean(isComment),
    }));
}

function renderQuickDownloadLinks(record: DesktopRecord): string {
  const links = rawRecords(record, ['download_links']).filter((item) => safeExternalUrl(item.url));
  if (!links.length) return '';
  const visible = links.slice(0, 3);
  return `<div class="card-downloads">${visible.map((link) => `<a class="card-download-link" href="${esc(safeExternalUrl(link.url))}" target="_blank" rel="noreferrer" data-action="open-source" data-url="${esc(safeExternalUrl(link.url))}">${esc(String(link.name || link.type || '下载'))} ↗</a>`).join('')}${links.length > visible.length ? `<span class="card-download-more">+${links.length - visible.length} 个</span>` : ''}</div>`;
}

function renderRecord(record: DesktopRecord, index: number): string {
  const config = PLATFORM_CONFIGS[record.platform];
  const searchContractText = existingSearchText(record).slice(0, 240);
  const originalCoverUrl = recordRealCoverUrl(record);
  const fallbackUrl = PLATFORM_COVER_FALLBACKS[record.platform];
  const cover = renderCoverImage({ url: originalCoverUrl, fallback: fallbackUrl, alt: `${record.title}封面`, key: record.id, className: 'pack-card-cover-image' });
  const coverMarkup = `<div class="cover-media cover-media-record" data-cover-frame data-cover-state="${cover.state}"><button type="button" class="pack-card-cover image-preview-trigger" data-action="open-image" data-image-url="${esc(cover.source)}" data-image-title="${esc(record.title)}封面" aria-label="查看${esc(record.title)}封面">${cover.image}${cover.status}</button>${cover.retryButton}</div>`;
  const metrics = recordMetricItems(record);
  return `<article class="pack-card platform-pack-card" data-action="select-record" data-index="${index}" data-search-text="${esc(searchContractText)}">
    ${coverMarkup}
    <div class="card-top"><span class="platform-badge">${platformIcon(record.platform)} ${config.name}</span><span class="card-time">${esc(formatTime(record.updatedAt))}</span></div>
    <h3 class="platform-card-title">${esc(record.title)}</h3><p class="author platform-card-meta">${esc(record.author)}</p>
    <p class="summary platform-card-summary">${textOrUnknown(record.summary)}</p>
    <div class="chips platform-card-tags">${record.versions.slice(0, 4).map((value, versionIndex) => `<span>${versionIndex === 0 ? 'MC ' : ''}${esc(value)}</span>`).join('')}${record.loaders.slice(0, 3).map((value) => `<span>${esc(value)}</span>`).join('')}${!record.versions.length && !record.loaders.length ? '<span class="muted-chip">兼容信息未知</span>' : ''}</div>
    ${metrics.length ? `<div class="card-metrics">${metrics.map((m) => m.isComment
      ? `<button type="button" class="card-metric-bubble card-metric-comment" data-action="open-comment-preview" data-index="${index}" title="点击预览此整合包的评论区">${esc(m.text)}</button>`
      : `<span>${esc(m.text)}</span>`
    ).join('')}</div>` : ''}
    ${renderQuickDownloadLinks(record)}
    ${renderPersonalCardZone(renderPersonalCardActions(record, index), 'pack-card-personal-zone')}
    <div class="card-footer platform-card-actions"><button type="button" class="compare-star ${state.compareIds.includes(record.id) ? 'is-selected' : ''}" data-action="toggle-compare" data-index="${index}" title="${state.compareIds.includes(record.id) ? '移出对比' : '加入对比'}">${state.compareIds.includes(record.id) ? '✓' : '＋'} 对比</button></div>
  </article>`;
}

function renderMcmodWindowAction(record: DesktopRecord): string {
  if (record.platform !== 'mcmod') return '';
  const url = safeExternalUrl(record.url) || `https://www.mcmod.cn/modpack/${encodeURIComponent(record.sourceId)}.html`;
  return `<button type="button" class="mcmod-comment-link" data-action="open-in-app-window" data-record-id="${esc(record.id)}" data-url="${esc(url)}" data-title="${esc(record.title)}">${isStaticSite() ? '原站链接 ↗' : '▣ 小窗浏览'}</button>`;
}

function renderCompactRecord(record: DesktopRecord, index: number): string {
  const originalCoverUrl = recordRealCoverUrl(record);
  const fallbackUrl = PLATFORM_COVER_FALLBACKS[record.platform];
  const cover = renderCoverImage({ url: originalCoverUrl, fallback: fallbackUrl, alt: `${record.title}封面`, key: record.id, className: 'compact-record-cover-image' });
  const coverMarkup = `<div class="cover-media cover-media-compact" data-cover-frame data-cover-state="${cover.state}"><button type="button" class="compact-record-cover image-preview-trigger" data-action="open-image" data-image-url="${esc(cover.source)}" data-image-title="${esc(record.title)}封面">${cover.image}</button></div>`;
  const metrics = recordMetricItems(record);
  const authorText = record.author && record.author !== '未知' ? esc(record.author) : '';
  let summaryText = record.summary ? record.summary.trim() : '';
  if (!summaryText || summaryText === '未知' || summaryText.includes('本地数据未提供')) {
    const raw = record.raw || {};
    if (record.platform === 'mcmod') {
      const typeStr = raw.typeName ? String(raw.typeName) : '整合包';
      const modCount = raw.includedModsCount ? `${raw.includedModsCount} 款模组` : '';
      const votes = (raw.votes && typeof raw.votes === 'object' ? raw.votes : {}) as Record<string, unknown>;
      const voteStr = votes.redPercent !== undefined ? `${votes.redPercent}% 好评` : '';
      summaryText = [typeStr, modCount, voteStr].filter(Boolean).join(' · ');
    } else {
      summaryText = record.categories.slice(0, 3).map((c) => getCategoryLabel(c)).join(' / ') || '暂无描述';
    }
  }
  return `<article class="compact-record" data-action="select-record" data-index="${index}">
    ${coverMarkup}
    <div class="compact-record-main">
      <div class="compact-record-head">
        <span class="platform-badge">${platformIcon(record.platform)} ${esc(PLATFORM_CONFIGS[record.platform].name)}</span>
        <span class="card-time">${esc(formatTime(record.updatedAt))}</span>
        ${authorText ? `<span class="compact-record-author">${authorText}</span>` : ''}
      </div>
      <h3 class="compact-record-title">${esc(record.title)}</h3>
      <p class="compact-record-summary">${esc(summaryText)}</p>
      <div class="chips">${record.versions.slice(0, 3).map((value) => `<span>${esc(value)}</span>`).join('')}${record.loaders.slice(0, 2).map((value) => `<span>${esc(value)}</span>`).join('')}</div>
    </div>
    <div class="compact-record-side">
      <div class="compact-record-metrics">${metrics.map((m) => m.isComment
        ? `<button type="button" class="compact-metric-bubble compact-metric-comment" data-action="open-comment-preview" data-index="${index}" title="点击预览此整合包的评论区">${esc(m.text)}</button>`
        : `<span>${esc(m.text)}</span>`
      ).join('')}</div>
      <div class="compact-record-actions">
        ${renderMcmodWindowAction(record)}
        ${renderPersonalCardActions(record, index)}
        <button type="button" class="compare-star compact-compare-star ${state.compareIds.includes(record.id) ? 'is-selected' : ''}" data-action="toggle-compare" data-index="${index}" title="${state.compareIds.includes(record.id) ? '移出对比' : '加入对比'}">${state.compareIds.includes(record.id) ? '✓' : '＋'} 对比</button>
      </div>
    </div>
  </article>`;
}

function mcmodTrendSeries(record: DesktopRecord): McmodTrendSeries {
  if (record.platform !== 'mcmod') return { status: 'missing', points: [], skippedCount: 0 };
  const raw = record.raw || {};
  const rawStats = raw.trendStats ?? raw.trend_stats;
  const trendStats = rawStats && typeof rawStats === 'object' ? rawStats as Record<string, unknown> : {};
  return parseMcmodTrendSeries(trendStats.trendValsStr, trendStats.trendDatesStr);
}

function mcmodTrendStatusText(series: McmodTrendSeries): string {
  if (series.status === 'missing') return '当前数据未提供历史趋势点。';
  if (series.status === 'mismatch') return '日期与数值数量不一致，无法安全配对。';
  if (series.status === 'invalid-order') return '历史日期顺序异常，无法绘制。';
  return `历史数据不足：至少需要两个有效点，当前为 ${series.points.length} 个。`;
}

function renderMcmodTrendTrigger(record: DesktopRecord, series = mcmodTrendSeries(record), compact = false): string {
  const sparkline = series.status === 'ready'
    ? `<span class="mcmod-trend-sparkline" aria-hidden="true">${generateSparklineSvg(series.points.map((point) => point.value), 104, 30)}</span>`
    : '';
  const description = series.status === 'ready' ? `${series.points.length} 个历史点` : mcmodTrendStatusText(series);
  const compactLabel = series.status === 'ready' ? '完整趋势' : series.status === 'missing' ? '无历史' : series.status === 'mismatch' ? '数据不匹配' : series.status === 'invalid-order' ? '日期异常' : '数据不足';
  return `<button type="button" class="mcmod-trend-trigger ${compact ? 'is-compact' : ''}" data-action="open-mcmod-trend" data-record-id="${esc(record.id)}" data-trend-trigger="true" aria-label="查看${esc(record.title)}的趋势图，${esc(description)}" title="${esc(description)}">${sparkline}<span>${compact ? compactLabel : '查看完整走势'}</span></button>`;
}

function renderMcmodTrendDetail(record: DesktopRecord): string {
  if (record.platform !== 'mcmod') return '';
  const series = mcmodTrendSeries(record);
  const summary = series.status === 'ready' ? `当前快照有 ${series.points.length} 个官方流行指数历史点。` : mcmodTrendStatusText(series);
  return `<div class="detail-section mcmod-trend-detail"><h3>历史趋势</h3><p class="detail-summary">${esc(summary)}${series.skippedCount ? ` 已跳过 ${series.skippedCount} 个日期或数值异常的点。` : ''}</p>${renderMcmodTrendTrigger(record, series)}<output class="trend-preview-readout">悬浮曲线查看日期和指数；方向键切换点位</output></div>`;
}

function mcmodTableModInfo(record: DesktopRecord): {
  count: number;
  categories: Array<{ name: string; count: number; url: string }>;
  names: string[];
} {
  const raw = record.raw || {};
  const names = [...new Set([
    ...rawList(record, ['includedModNames', 'included_mod_names']),
    ...rawRecords(record, ['includedMods', 'included_mods', 'previewMods', 'mods'])
      .map((mod) => String(mod.title || mod.name || '').trim()),
  ].filter(Boolean))];
  const reportedCount = Number(raw.includedModsCount ?? raw.included_mods_count ?? raw.modCount ?? raw.mod_count);
  const count = Number.isFinite(reportedCount) && reportedCount > 0 ? Math.max(reportedCount, names.length) : names.length;
  const categories = (Array.isArray(raw.modCategories) ? raw.modCategories : [])
    .filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === 'object')
    .map((item) => ({ name: String(item.categoryName || '').trim(), count: Number(item.count) || 0, url: safeExternalUrl(item.categoryUrl) }))
    .filter((item) => item.name && item.count > 0);
  return { count, categories, names };
}

function renderMcmodFullModList(record: DesktopRecord, context: 'table' | 'window'): string {
  const info = mcmodTableModInfo(record);
  if (!info.names.length) return '<p class="mcmod-mod-drawer-empty">当前快照有模组数量，但未提供可展示的名称清单。</p>';
  const modDetails = new Map<string, { url: string; category: string }>();
  const categoryByPath = new Map(info.categories.filter((item) => item.url).map((item) => [new URL(item.url).pathname, item.name]));
  for (const mod of rawRecords(record, ['includedMods', 'included_mods', 'previewMods', 'mods'])) {
    const name = String(mod.title || mod.name || '').trim();
    const url = safeExternalUrl(mod.url);
    const category = String(mod.categoryName || mod.category_name || '').trim();
    if (name) modDetails.set(name, { url, category });
  }
  for (const mod of mcmodLiveModIndex.get(record.id) || []) {
    const category = mod.categoryUrl ? categoryByPath.get(new URL(mod.categoryUrl).pathname) || '' : '';
    if (mod.name) modDetails.set(mod.name, { url: safeExternalUrl(mod.url), category });
  }
  const groups = new Map<string, Array<{ name: string; index: number; url: string }>>();
  info.names.forEach((name, index) => {
    const detail = modDetails.get(name);
    const category = detail?.category || '未归类（当前资料未逐项标注）';
    if (!groups.has(category)) groups.set(category, []);
    groups.get(category)!.push({ name, index, url: detail?.url || '' });
  });
  const orderedGroups = [...groups.entries()].sort((a, b) => {
    const ai = info.categories.findIndex((item) => item.name === a[0]);
    const bi = info.categories.findIndex((item) => item.name === b[0]);
    return (ai < 0 ? 999 : ai) - (bi < 0 ? 999 : bi);
  });
  return `<div class="mcmod-full-mod-list ${context === 'window' ? 'is-window' : 'is-table'}" data-mod-list>
    <div class="mcmod-full-mod-toolbar"><input type="search" class="js-mcmod-mod-search" placeholder="搜索 ${info.names.length} 款模组…" aria-label="搜索已收录模组" autocomplete="off"><span data-mod-match-count>显示全部 ${info.names.length} 款</span></div>
    <div class="mcmod-full-mod-items" aria-label="完整已收录模组清单">${orderedGroups.map(([category, mods]) => `<section class="mcmod-mod-group"><h4>${esc(category)} <span>${mods.length}</span></h4><div class="mcmod-mod-group-grid">${mods.map(({ name, index, url }) => {
      const label = `<span class="mcmod-mod-index">${index + 1}</span><span class="mcmod-mod-name">${esc(name)}</span>`;
      if (context === 'window') return `<button type="button" class="mcmod-full-mod-item js-focus-in-app-mod" data-mod-name="${esc(name.toLocaleLowerCase())}" data-mod-raw-name="${esc(name)}" title="在中间网页定位 ${esc(name)}">${label}<span class="mcmod-mod-locate">定位 ↘</span></button>`;
      return url ? `<a class="mcmod-full-mod-item" href="${esc(url)}" target="_blank" rel="noreferrer" data-mod-name="${esc(name.toLocaleLowerCase())}">${label}<span aria-hidden="true">↗</span></a>` : `<span class="mcmod-full-mod-item" data-mod-name="${esc(name.toLocaleLowerCase())}">${label}</span>`;
    }).join('')}</div></section>`).join('')}</div>
  </div>`;
}

function renderMcmodTable(records: DesktopRecord[]): string {
  const rows = records.map((record, index) => {
    const raw = record.raw || {};
    const ts = (raw.trendStats && typeof raw.trendStats === 'object' ? raw.trendStats : {}) as Record<string, unknown>;
    const score = ts.score !== undefined && ts.score !== null ? Number(ts.score) : null;
    const lat = ts.lat !== undefined && ts.lat !== null ? formatMetric(ts.lat) : '—';
    const max = ts.max !== undefined && ts.max !== null ? formatMetric(ts.max) : '—';
    const avg = ts.avg !== undefined && ts.avg !== null ? formatMetric(ts.avg) : '—';
    const days = ts.days !== undefined && ts.days !== null ? `${ts.days}天` : '—';
    const trendSeries = mcmodTrendSeries(record);
    const votes = (raw.votes && typeof raw.votes === 'object' ? raw.votes : {}) as Record<string, unknown>;
    const categories = valueList(raw.categories ?? record.categories);
    const originalCoverUrl = recordRealCoverUrl(record);
    const fallbackUrl = PLATFORM_COVER_FALLBACKS[record.platform];
    const cover = renderCoverImage({ url: originalCoverUrl, fallback: fallbackUrl, alt: `${record.title}封面`, key: record.id, className: 'mcmod-table-cover-image' });
    const coverMarkup = `<div class="cover-media cover-media-table" data-cover-frame data-cover-state="${cover.state}"><button type="button" class="mcmod-table-cover image-preview-trigger" data-action="open-image" data-image-url="${esc(cover.source)}" data-image-title="${esc(record.title)}封面" aria-label="查看${esc(record.title)}封面">${cover.image}</button></div>`;

    const svgHtml = trendSeries.status === 'ready'
      ? generateSparklineSvg(trendSeries.points.map((p) => p.value), 118, 30)
      : '';
    const hint = svgHtml ? '看大图 ↗' : '无历史';
    const scoreBadge = score !== null && score > 0
      ? `<div class="trend-score-badge" title="官方流行指数评分"><span>流行</span><b>${score}</b></div>`
      : `<div class="trend-score-badge unrated" title="官方暂无评分"><span>暂无评分</span></div>`;
    const t7Num = asNumber(ts.t7);
    const t30Num = asNumber(ts.t30);
    const t7Label = Number.isFinite(t7Num) && t7Num !== 0 ? `${t7Num > 0 ? '+' : ''}${Math.round(t7Num)}%` : formatMetric(ts.t7);
    const t30Label = Number.isFinite(t30Num) && t30Num !== 0 ? `${t30Num > 0 ? '+' : ''}${Math.round(t30Num)}%` : formatMetric(ts.t30);

    const trendCellHtml = `<div class="trend-consolidated-cell">
      <div class="trend-cell-top">
        ${scoreBadge}
        <div class="trend-growth-pair">
          <span class="trend-growth-item ${t7Num > 0 ? 'is-up' : t7Num < 0 ? 'is-down' : ''}" title="7日涨幅">7日 <strong>${esc(t7Label)}</strong></span>
          <span class="trend-growth-item ${t30Num > 0 ? 'is-up' : t30Num < 0 ? 'is-down' : ''}" title="30日涨幅">30日 <strong>${esc(t30Label)}</strong></span>
        </div>
      </div>
      <button type="button" class="mcmod-trend-trigger is-compact" data-action="open-mcmod-trend" data-record-id="${esc(record.id)}" data-trend-trigger="true" aria-label="查看${esc(record.title)}的趋势图" title="点击查看${esc(record.title)}完整历史走势">
        <div class="trend-main-row">
          ${svgHtml ? `<span class="mcmod-trend-sparkline" data-trend-vals="${trendSeries.points.map((p) => p.value).join(',')}" data-trend-dates="${trendSeries.points.map((p) => p.date).join(',')}">${svgHtml}</span>` : '<span class="trend-no-data">暂无历史走势</span>'}
          <div class="trend-val-group">
            <span class="trend-val-lat" title="最新指数">最新: ${esc(lat)}</span>
            <span class="trend-open-hint">${hint}</span>
          </div>
        </div>
      </button>
      <div class="trend-meta-row">
        <span title="最高指数">高: ${esc(max)}</span>
        <span title="平均指数">平: ${esc(avg)}</span>
        <span title="走势天数">${esc(days)}</span>
      </div>
    </div>`;

    const rv = Number(votes.redVotes) || 0;
    const bv = Number(votes.blackVotes) || 0;
    const rp = votes.redPercent !== undefined ? Number(votes.redPercent) : (rv + bv > 0 ? Math.round(rv / (rv + bv) * 100) : 50);
    const bp = 100 - rp;
    const voteCell = `<div class="votes-consolidated-cell">
      <div class="vote-ratio-text"><span class="vote-positive">👍 ${rv} 红</span> / <span class="vote-negative">👎 ${bv} 黑</span></div>
      <div class="vote-ratio-bar" title="红占比: ${rp}% | 黑占比: ${bp}%"><div class="vote-ratio-red" style="width: ${rp}%;"></div><div class="vote-ratio-black" style="width: ${bp}%;"></div></div>
      <small>${rp}% 好评</small>
    </div>`;

    const com = formatMetric(raw.commentsCount);
    const rec = formatMetric(raw.recommendations);
    const fav = formatMetric(raw.favorites);
    const hasComments = Number(raw.commentsCount) > 0;
    const engageCell = `<div class="mcmod-engage-cell"><button type="button" class="mcmod-comment-btn ${hasComments ? 'has-count' : ''}" data-action="open-comment-preview" data-index="${index}" title="在网页内预览${esc(record.title)}的评论">💬 <strong>${esc(com)}</strong> 评</button><small>👍 ${esc(rec)} 推 · ⭐ ${esc(fav)} 藏</small></div>`;

    const authorMarkup = record.author && record.author !== '未知' ? `<small>${esc(record.author)}</small>` : '';
    const modInfo = mcmodTableModInfo(record);
    const modsExpanded = state.expandedMcmodTableMods === record.id;
    const modPanelId = `mcmod-table-mods-${index}`;
    const categoryPreview = [...modInfo.categories].sort((a, b) => b.count - a.count).slice(0, 2).map((category) => `<span class="mcmod-mod-category" title="${esc(category.name)} ${category.count} 款">${esc(category.name)} <b>${category.count}</b></span>`).join('');
    const modCellHtml = `<div class="mcmod-mod-summary"><div class="mcmod-mod-summary-top"><strong>${modInfo.count ? `${formatCount(modInfo.count)} 款模组` : '模组清单未知'}</strong><button type="button" class="mcmod-mod-toggle" data-action="toggle-mcmod-table-mods" data-record-id="${esc(record.id)}" aria-expanded="${modsExpanded}" aria-controls="${modPanelId}" ${modInfo.count || modInfo.categories.length ? '' : 'disabled'}>${modsExpanded ? '收起' : '查看模组'} <span aria-hidden="true">${modsExpanded ? '▴' : '▾'}</span></button></div>${categoryPreview ? `<div class="mcmod-mod-category-preview">${categoryPreview}${modInfo.categories.length > 2 ? `<span class="mcmod-mod-category-more">另 ${modInfo.categories.length - 2} 类</span>` : ''}</div>` : '<small>当前快照未提供分类</small>'}</div>`;
    const modDrawer = modsExpanded ? `<tr class="mcmod-table-mod-drawer-row"><td colspan="7"><div class="mcmod-table-mod-drawer" id="${modPanelId}"><div class="mcmod-mod-drawer-header"><div><strong>${esc(record.title)} · 已收录模组</strong><span>${modInfo.count ? `来源共 ${formatCount(modInfo.count)} 款` : '清单数量未知'} · 本地可显示 ${modInfo.names.length} 款</span></div></div>${modInfo.categories.length ? `<div class="mcmod-mod-drawer-categories" aria-label="模组分类">${modInfo.categories.map((category) => `<span>${esc(category.name)} <b>${category.count}</b></span>`).join('')}</div>` : ''}${renderMcmodFullModList(record, 'table')}</div></td></tr>` : '';

    return `<tr class="mcmod-table-row" data-action="select-record" data-index="${index}">
      <td class="mcmod-name-cell"><div class="mcmod-name-cell-inner">${coverMarkup}<div class="mcmod-name-content"><strong>${esc(record.title)}</strong>${authorMarkup}<div class="mcmod-table-tags">${categories.slice(0, 4).map((item) => `<span>${esc(getCategoryLabel(item))}</span>`).join('')}${categories.length > 4 ? `<span>+${categories.length - 4}</span>` : ''}</div></div></div></td>
      <td class="mcmod-reach-cell"><div class="mcmod-reach-metrics"><strong>${esc(formatMetric(raw.views))}</strong><span>🔥 ${esc(formatMetric(raw.score))}★ <i aria-hidden="true">·</i> ${esc(formatMetric(raw.recommendations))} 推荐</span></div></td>
      <td class="mcmod-trend-cell">${trendCellHtml}</td>
      <td>${voteCell}</td>
      <td>${engageCell}</td>
      <td class="mcmod-mod-cell">${modCellHtml}</td>
      <td class="mcmod-personal-cell">
        <div class="table-action-cell">
          ${renderMcmodWindowAction(record)}
          ${renderPersonalCardActions(record, index)}
          <button type="button" class="compare-star table-compare-star ${state.compareIds.includes(record.id) ? 'is-selected' : ''}" data-action="toggle-compare" data-index="${index}" title="${state.compareIds.includes(record.id) ? '移出对比' : '加入对比'}">${state.compareIds.includes(record.id) ? '✓' : '＋'} 对比</button>
        </div>
      </td>
    </tr>${modDrawer}`;
  }).join('');
  if (!rows) return '<div class="empty-state compact-empty"><div class="empty-icon">⌕</div><h3>没有匹配的整合包</h3><p>换一个关键词或清除筛选条件。</p><button class="button secondary" data-action="clear-filters">清除筛选</button></div>';
  return `<div class="mcmod-table-wrap"><table class="mcmod-table"><colgroup><col style="width:21%"><col style="width:12%"><col style="width:22%"><col style="width:9%"><col style="width:10%"><col style="width:16%"><col style="width:10%"></colgroup><thead><tr><th>整合包</th><th>浏览 / 热度</th><th>趋势</th><th>投票</th><th>评论 / 收藏</th><th>包含模组</th><th>个人库 / 对比</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}

function renderBilibiliGroupedWorkspace(): string {
  const groups = sortBilibiliGroups(state.biliGroups);
  if (!groups.length) return '<div class="empty-state compact-empty"><div class="empty-icon">⌕</div><h3>没有匹配的整合包</h3><p>换一个关键词或清除筛选条件。</p><button class="button secondary" data-action="clear-filters">清除筛选</button></div>';
  const pageSize = 48;
  const visibleGroups = groups.slice(0, state.page * pageSize);
  const recordIndexBySourceId = new Map<string, number>();
  for (let i = 0; i < state.records.length; i += 1) {
    recordIndexBySourceId.set(state.records[i].sourceId, i);
  }
  const cards = visibleGroups.map((group) => {
    const latest = group.items[0];
    const index = latest ? (recordIndexBySourceId.get(latest.bvid) ?? -1) : -1;
    const personalZone = renderPersonalCardZone(`${renderBilibiliGroupPersonalActions(group)}${renderBilibiliGroupPersonalSummary(group)}`, 'is-bilibili');
    return `<article class="desktop-rich-card" data-action="select-record" data-index="${index}" data-bili-group-key="${esc(group.key)}">${renderBiliGroupedCard(group)}${personalZone}</article>`;
  }).join('');
  const noteCount = visibleGroups.length < groups.length
    ? `已显示 ${formatCount(visibleGroups.length)} / ${formatCount(groups.length)} 款独立整合包 · 关联视频、统计、网盘与历史版本均保留`
    : `${formatCount(groups.length)} 款独立整合包 · 关联视频、统计、网盘与历史版本均保留`;
  return `<div class="bili-legacy-mode-note"><strong>✨ 同名整合包智能聚合</strong><span>${noteCount}</span></div><div class="bili-cards-grid desktop-bili-grid">${cards}</div>`;
}

function renderBilibiliFlatWorkspace(records: DesktopRecord[]): string {
  if (!records.length) return '<div class="empty-state compact-empty"><div class="empty-icon">⌕</div><h3>没有匹配的视频</h3><p>换一个关键词或清除筛选条件。</p><button class="button secondary" data-action="clear-filters">清除筛选</button></div>';
  const cards = records.map((record, index) => `<article class="desktop-rich-card" data-action="select-record" data-index="${index}">${renderBiliFlatCard(toBilibiliPack(record))}${renderPersonalCardZone(renderPersonalCardActions(record, index), 'is-bilibili')}</article>`).join('');
  return `<div class="bili-legacy-mode-note"><strong>视频平铺</strong><span>当前展示 ${formatCount(records.length)} / ${formatCount(state.total)} 条视频，可继续加载</span></div><div class="bili-cards-grid desktop-bili-grid">${cards}</div>`;
}

function platformIcon(platform: Platform): string {
  const src = isStaticSite() ? '' : PLATFORM_SITE_ICONS[platform];
  const short = platform === 'mcmod' ? 'MC' : platform === 'bilibili' ? 'B' : platform === 'bbsmc' ? 'BBS' : platform === 'xyebbs' ? 'XYE' : platform === 'modrinth' ? 'MR' : 'CF';
  if (!src) return `<span class="platform-icon-wrap"><span class="platform-icon-fallback">${short}</span></span>`;
  return `<span class="platform-icon-wrap"><img class="platform-site-icon" src="${esc(src)}" alt="${esc(PLATFORM_CONFIGS[platform].name)}图标" loading="lazy" referrerpolicy="no-referrer" onerror="this.hidden=true;this.nextElementSibling.hidden=false;"><span class="platform-icon-fallback" hidden>${short}</span></span>`;
}

function formatCount(value: number): string {
  return Number(value || 0).toLocaleString('zh-CN');
}

function renderLegacyShowcaseCard(platform: Platform): string {
  const config = PLATFORM_CONFIGS[platform];
  const platformState = state.data?.platforms[platform];
  const records = state.records.filter((record) => record.platform === platform);
  const samples = records.slice(0, 3);
  const count = platformState?.count ?? 0;
  const platformTime = (state.data as (DesktopDataState & { sourceTimes?: Record<string, string> }) | null)?.sourceTimes?.[platform];
  const refresh = (state.data as (DesktopDataState & { sourceRefresh?: Record<string, { status: string; coverage: string; new: number; updated: number; knownUnavailableCount?: number; unverifiedCount?: number; htmlRefresh?: { observedCount: number; newCount: number; updatedCount: number; observedAt: string; newerPublicationCount?: number } }> }) | null)?.sourceRefresh?.[platform];
  const recoveredHistoricalData = refresh?.status === 'recovered-existing-local-snapshot';
  const htmlRefresh = refresh?.htmlRefresh;
  const refreshLabel = recoveredHistoricalData ? htmlRefresh ? '恢复9月28日本地较新数据；官方网页分批局部更新' : '恢复9月28日本地较新数据，本轮未在线刷新' : refresh?.status === 'retained-old' ? '本轮未更新，保留旧完整数据' : refresh?.status === 'partial' ? '本轮局部刷新' : refresh ? '本轮增量范围已验证' : '';
  const refreshCounts = refresh && refresh.status !== 'retained-old' ? `；新增 ${refresh.new}，展示字段更新 ${refresh.updated}` : '';
  const updateTime = isStaticSite() ? `${refreshLabel ? refreshLabel + '；' : ''}${recoveredHistoricalData ? '历史最后检查时间' : refresh && refresh.status !== 'retained-old' ? '刷新验证时间' : '源文件更新时间'}：${formatTime(platformTime || '')}${refreshCounts}${recoveredHistoricalData ? `；${refresh?.knownUnavailableCount || 0}条来源确认不可用，${refresh?.unverifiedCount || 0}条历史未成功检查` : ''}${htmlRefresh ? `；累计HTML分批核验 ${htmlRefresh.observedCount} 条：新增 ${htmlRefresh.newCount} 条（历史漏收 ${htmlRefresh.newCount - (htmlRefresh.newerPublicationCount || 0)}、近期发布介绍视频 ${htmlRefresh.newerPublicationCount || 0}），更新 ${htmlRefresh.updatedCount} 条旧记录；最新核验时间 ${formatTime(htmlRefresh.observedAt)}${htmlRefresh.newerPublicationCount ? "；包首次发布及版本更新未核验" : ""}` : ''}` : platformState?.available && state.data?.updatedAt ? `快照更新时间：${formatTime(state.data.updatedAt)}` : '等待本地快照';
  const tags = [...new Set(samples.flatMap((record) => [...record.versions, ...record.loaders, ...record.categories]).filter(Boolean))].slice(0, 5);
  const sampleHtml = samples.length
    ? samples.map((record, index) => {
      const recordIndex = state.records.indexOf(record);
      return `<button type="button" class="featured-item" data-action="select-record" data-index="${recordIndex}" title="打开 ${esc(record.title)} 详情"><span class="featured-rank">${index + 1}</span><span class="featured-name">${esc(record.title)}</span><span class="featured-meta">${esc(record.author || '作者未知')}</span></button>`;
    }).join('')
    : isStaticSite() && (isStaticOverview() || state.loading)
      ? `<div class="showcase-empty"><span data-pages-source-state="${platform}">${esc(pagesSourceLoadLabel(platform))}</span>。打开此来源后展示代表记录。</div>`
      : '<div class="showcase-empty">当前筛选页没有可展示记录。</div>';
  const tagHtml = tags.length
    ? tags.map((tag) => `<button type="button" class="showcase-tag-chip" data-action="quick-search" data-query="${esc(tag)}">${esc(tag)}</button>`).join('')
    : `<span class="showcase-tag-chip muted-chip">${isStaticSite() && (isStaticOverview() || state.loading) ? '加载记录后显示版本和标签' : '暂无版本或标签'}</span>`;
  return `<article class="platform-showcase-card" style="--card-accent:${PLATFORM_ACCENTS[platform]}; --card-glow:${PLATFORM_ACCENTS[platform]}33;">
    <div class="showcase-header"><div class="showcase-icon" style="background:${PLATFORM_ACCENTS[platform]}22; color:${PLATFORM_ACCENTS[platform]};">${platformIcon(platform)}</div><div><h3 class="showcase-title">${esc(config.name)}数据看板</h3><span class="showcase-badge" style="background:${PLATFORM_ACCENTS[platform]}22; color:${PLATFORM_ACCENTS[platform]};">${esc(PLATFORM_TAGLINES[platform])}</span></div></div>
    <div class="showcase-metrics"><div><div class="smetric-val">${formatCount(count)}</div><div class="smetric-lbl">${isStaticSite() ? '公开采集记录' : '当前快照记录'}</div></div><div><div class="smetric-val">${records.length ? formatCount(records.length) : '—'}</div><div class="smetric-lbl">当前页可浏览</div></div><div><div class="smetric-val">${isStaticSite() ? `<span data-pages-source-state="${platform}">${esc(pagesSourceLoadLabel(platform))}</span>` : platformState?.available ? '已载入' : '未载入'}</div><div class="smetric-lbl">${isStaticSite() ? '记录加载状态' : '本地状态'}</div></div></div>
    <div class="showcase-featured-box"><div class="showcase-box-header"><span>📌 ${isStaticSite() ? '公开记录代表' : '当前快照代表'}</span><span>点击直达</span></div>${sampleHtml}</div>
    <div class="showcase-tags-box">${tagHtml}</div>
    <div class="showcase-source-meta">${esc(updateTime)}</div>
    <button type="button" class="showcase-btn" style="background:linear-gradient(135deg, ${PLATFORM_ACCENTS[platform]}, ${PLATFORM_ACCENTS[platform]}cc);" data-action="set-platform" data-platform="${platform}">浏览全部 ${formatCount(count)} 条${esc(config.name)}记录</button>
  </article>`;
}

function renderCrossSearch(): string {
  const platformPills = ALL_PLATFORMS.map((platform) => `<span class="cplat-pill" style="--cp-c:${PLATFORM_ACCENTS[platform]};">${platformIcon(platform)} ${esc(PLATFORM_CONFIGS[platform].name)}</span>`).join('');
  const versionChips = ['1.20.1', '1.16.5', '1.12.2', '1.7.10', '1.21', '1.19.2'].map((value) => `<button type="button" class="hot-chip chip-ver" data-action="quick-search" data-query="${value}">${value}</button>`).join('');
  const themeChips = ['机械动力', '拔刀剑', '宝可梦', '科技', '魔法', 'Fabulously Optimized', '空岛', 'RLCraft'].map((value) => `<button type="button" class="hot-chip chip-theme" data-action="quick-search" data-query="${esc(value)}">${esc(value)}</button>`).join('');
  return `<section class="cross-search-section" aria-labelledby="cross-search-title">
    <div class="csearch-top-row"><div><h2 id="cross-search-title" class="csearch-heading">跨平台检索总览</h2><p class="csearch-sub">每个平台独立在完整本地数据上搜索、筛选并按平台内规则排序；每轮每个平台最多 12 条。字段覆盖因平台而异，MC百科额外支持模组名检索。</p></div><div class="csearch-platforms-hint">${platformPills}</div></div>
    <div class="cross-search-input-wrap"><span class="cross-search-icon">🔍</span><input id="pack-search" class="cross-search-input js-pack-search" value="${esc(state.query)}" placeholder="${esc(getDesktopSearchPlaceholder('all'))}" autocomplete="off"><div class="cross-search-kbd"><kbd>Ctrl</kbd><kbd>K</kbd></div></div>
    <div class="cross-chips-deck"><div class="chip-deck-row"><span class="deck-row-lbl">🎮 核心版本：</span><div class="deck-chips-group">${versionChips}</div></div><div class="chip-deck-row"><span class="deck-row-lbl">🔥 常用关键词：</span><div class="deck-chips-group">${themeChips}</div></div></div>
    ${renderCrossResults()}
  </section>`;
}

function renderCrossResults(): string {
  if (!state.query.trim()) return '';
  if (isStaticSite() && state.loading) return `<div class="loading-state pages-loading-progress" role="status">${esc(pagesLoadingMessage())}</div>`;
  if (isStaticSite() && state.recordsError && !state.records.length) return '';
  const groups = ALL_PLATFORMS.map((platform) => {
    const records = state.records.filter((record) => record.platform === platform).slice(0, 4);
    if (!records.length) return '';
    return `<section class="cross-result-column"><div class="cross-result-column-head"><span>${platformIcon(platform)} ${esc(PLATFORM_CONFIGS[platform].name)}</span><strong>${records.length} 条当前页结果</strong></div>${records.map((record) => { const index = state.records.indexOf(record); return `<button type="button" class="cross-result-item" data-action="select-record" data-index="${index}"><span>${esc(record.title)}</span><small>${esc(record.author || '未知作者')}</small></button>`; }).join('')}</section>`;
  }).filter(Boolean).join('');
  return groups ? `<div class="cross-results-wrap"><div class="cross-results-heading"><strong>各平台匹配结果</strong><span>按当前筛选条件展示各平台首批结果（每个平台最多 12 条）</span></div><div class="cross-results-grid">${groups}</div></div>` : '<div class="cross-results-wrap cross-results-empty">当前关键词在已载入平台中没有匹配结果。</div>';
}

function auditCount(audit: DesktopAuditResult | null): number {
  const stats = audit?.stats || {};
  return ['added_count', 'updated_count', 'removed_count', 'version_gained_count'].reduce((sum, key) => sum + Number(stats[key] || 0), 0);
}

function auditRows(audit: DesktopAuditResult): string {
  const groups: Array<[string, Array<Record<string, unknown>>]> = [
    ['新增', audit.added],
    ['更新', audit.updated],
    ['新增版本', audit.version_gained],
    ['移除', audit.removed],
  ];
  const rows = groups.flatMap(([label, items]) => items.slice(0, 80).map((item) => `<article class="audit-row"><div><strong>${esc(label)} · ${esc(String(item.title || item.name || item.id || '未命名记录'))}</strong><span>${esc(String(item.platform || '平台未知'))} · ${esc(String(item.author || '作者未知'))}</span></div><a class="detail-link" href="${esc(safeExternalUrl(item.url))}" target="_blank" rel="noreferrer">原站 ↗</a></article>`));
  return rows.length ? rows.join('') : '<div class="empty-evidence">当前快照没有可展示的变动条目。</div>';
}

function auditPanel(): string {
  if (!state.auditOpen) return '';
  const audit = state.audit;
  const stats = audit?.stats || {};
  const body = state.auditLoading
    ? '<div class="loading-state">正在读取当前快照的审计文件…</div>'
    : state.auditError
      ? `<div class="error-state"><div class="empty-icon">!</div><h3>审计请求失败</h3><p>${esc(state.auditError)}</p><button type="button" class="button secondary" data-action="retry-audit">重试审计请求</button></div>`
      : audit
        ? `<p class="audit-meta">${esc(audit.generated_at || '当前快照')} · ${audit.available ? '可用历史对比' : '没有可用历史基线'}</p>${audit.message ? `<div class="notice">${esc(audit.message)}</div>` : ''}<div class="audit-kpis"><div><strong>${formatCount(Number(stats.total_current || 0))}</strong><span>当前范围</span></div><div><strong>${formatCount(Number(stats.added_count || 0))}</strong><span>新增</span></div><div><strong>${formatCount(Number(stats.updated_count || 0))}</strong><span>更新</span></div><div><strong>${formatCount(Number(stats.removed_count || 0))}</strong><span>移除</span></div></div><div class="audit-list">${auditRows(audit)}</div>`
        : '<div class="empty-evidence">当前快照没有可读取的审计信息。</div>';
  return `<div class="modal-backdrop audit-backdrop" data-action="close-audit" role="dialog" aria-modal="true" aria-label="变动审计"><section class="modal-panel audit-panel" onclick="event.stopPropagation()"><header class="modal-header"><div class="modal-title-wrap"><span class="eyebrow">SNAPSHOT AUDIT</span><h2>抓取变动审计</h2></div><button type="button" class="modal-close audit-close" data-action="close-audit" aria-label="关闭审计">×</button></header>${body}</section></div>`;
}

function compareEntries(): DesktopRecord[] {
  return state.compareIds.map((id) => state.compareRecords[id]).filter(Boolean);
}

function renderCompareTray(): string {
  const entries = compareEntries();
  if (!entries.length) return '';
  return `<aside class="compare-tray"><div><strong>待比较整合包</strong><span>${entries.length} 个${state.compareIds.length > entries.length ? `，当前筛选外 ${state.compareIds.length - entries.length} 个` : ''}</span></div><div class="compare-tray-names">${entries.slice(0, 5).map((record) => `<span>${esc(record.title)}</span>`).join('')}</div><button type="button" class="button secondary" data-action="open-compare" ${entries.length < 2 ? 'disabled' : ''}>全面对比</button><button type="button" class="button" data-action="clear-compare">清空</button></aside>`;
}

function renderComparePanel(): string {
  if (!state.compareOpen) return '';
  const entries = compareEntries();
  return `<div class="modal-backdrop compare-backdrop" data-action="close-compare" role="dialog" aria-modal="true" aria-label="整合包全面对比"><section class="modal-panel compare-panel" onclick="event.stopPropagation()"><header class="modal-header"><div class="modal-title-wrap"><span class="eyebrow">MODPACK COMPARISON</span><h2>整合包全面对比</h2></div><button type="button" class="modal-close compare-close" data-action="close-compare" aria-label="关闭比较">×</button></header>${entries.length < 2 ? '<div class="empty-evidence">至少选择两个当前已载入的整合包。</div>' : `<div class="compare-table"><div class="compare-row compare-row-head"><span>字段</span>${entries.map((record) => `<strong>${esc(record.title)}</strong>`).join('')}</div><div class="compare-row"><span>平台</span>${entries.map((record) => `<span>${esc(PLATFORM_CONFIGS[record.platform].name)}</span>`).join('')}</div><div class="compare-row"><span>作者</span>${entries.map((record) => `<span>${esc(record.author)}</span>`).join('')}</div><div class="compare-row"><span>Minecraft</span>${entries.map((record) => `<span>${esc(record.versions.join('、') || UNKNOWN_LOCAL_TEXT)}</span>`).join('')}</div><div class="compare-row"><span>Loader</span>${entries.map((record) => `<span>${esc(record.loaders.join('、') || UNKNOWN_LOCAL_TEXT)}</span>`).join('')}</div><div class="compare-row"><span>分类</span>${entries.map((record) => `<span>${esc(record.categories.map((c) => getCategoryLabel(c)).join('、') || UNKNOWN_LOCAL_TEXT)}</span>`).join('')}</div><div class="compare-row"><span>服务端</span>${entries.map((record) => `<span>${esc(environmentDisplay(record))}</span>`).join('')}</div><div class="compare-row"><span>平台指标</span>${entries.map((record) => `<span>${esc(recordMetricItems(record).map((m) => m.text).join(' · ') || UNKNOWN_LOCAL_TEXT)}</span>`).join('')}</div></div>`}</section></div>`;
}

function renderPlatformHero(platform: Platform): string {
  const config = PLATFORM_CONFIGS[platform];
  const count = state.data?.platforms[platform]?.count ?? 0;
  return `<section class="channel-hero ${platform}-channel-hero"><div class="channel-hero-left"><span class="channel-badge-tag">${platformIcon(platform)} ${esc(config.name)}</span><div class="channel-title">${esc(config.name)}资料看板</div><div class="channel-desc">${esc(PLATFORM_TAGLINES[platform])}。详情页保留版本、模组、评论和原始来源入口。</div></div><div class="channel-quick-stats"><div class="cstat-item"><span class="cs-num">${formatCount(count)}</span><span class="cs-lbl">${isStaticSite() ? '公开采集记录' : '当前快照记录'}</span></div><div class="cstat-item"><span class="cs-num">${state.loading ? '…' : formatCount(state.total)}</span><span class="cs-lbl">当前结果总数</span></div></div></section>`;
}

function getCategoryOptionsWithCounts(): Array<{ value: string; count: number }> {
  if (state.availableCategoryCounts && state.availableCategoryCounts.length > 0) {
    const existingValues = new Set(state.availableCategoryCounts.map((c) => c.value));
    const extra: Array<{ value: string; count: number }> = state.availableCategories
      .filter((cat) => !existingValues.has(cat))
      .map((cat) => ({ value: cat, count: 0 }));
    return [...state.availableCategoryCounts.map((c) => ({ value: c.value, count: c.count ?? 0 })), ...extra];
  }
  const cachedCounts = platformRecordCache.get(state.platform)?.availableCategoryCounts;
  if (cachedCounts && cachedCounts.length > 0) {
    return cachedCounts.map((c) => ({ value: c.value, count: c.count ?? 0 }));
  }
  const countMap = new Map<string, number>();
  for (const record of state.records) {
    for (const cat of record.categories || []) {
      if (cat) {
        countMap.set(cat, (countMap.get(cat) || 0) + 1);
      }
    }
  }
  const allCategories = state.availableCategories;
  const sorted = [...allCategories].sort((a, b) => {
    const countA = countMap.get(a) || 0;
    const countB = countMap.get(b) || 0;
    if (countB !== countA) return countB - countA;
    return getCategoryLabel(a).localeCompare(getCategoryLabel(b), 'zh-Hans-CN');
  });
  return sorted.map((cat) => ({
    value: cat,
    count: countMap.get(cat) || 0,
  }));
}

export function renderStickyFollowBar(): string {
  const isAll = state.platform === 'all';
  const isCurseforge = state.platform === 'curseforge';
  const isMcmod = state.platform === 'mcmod';
  const isBili = state.platform === 'bilibili';

  // 1. Primary Toolbar Row (Row 1):
  // Search + Version + Loader + Status + Sort (if not all) + View Mode Toggle + Reset + Follow + Top
  const searchPlaceholder = getDesktopSearchPlaceholder(state.platform);
  const searchInputHtml = `<div class="sticky-main-search-wrap">
    <span class="sticky-main-search-icon">🔍</span>
    <input id="pack-search" class="sticky-main-search-input js-pack-search" value="${esc(state.query)}" placeholder="${esc(searchPlaceholder)}" autocomplete="off" aria-label="搜索整合包" />
    ${state.query ? `<button type="button" class="sticky-search-clear-btn" data-action="clear-query" aria-label="清空搜索" title="清空搜索">✕</button>` : ''}
  </div>`;

  const versionDropdownHtml = `<div class="sticky-filter-control" title="按 Minecraft 版本筛选">
    <span class="sticky-filter-icon">🏷️</span>
    ${renderFilterDropdown('version', state.availableVersions, state.version, '全部版本')}
  </div>`;

  const loaderDropdownHtml = `<div class="sticky-filter-control" title="按 Mod Loader 筛选">
    <span class="sticky-filter-icon">⚙️</span>
    ${renderFilterDropdown('loader', state.availableLoaders, state.loader, '全部 Loader')}
  </div>`;

  const statusDropdownHtml = `<div class="sticky-filter-control" title="按个人回访状态筛选">
    <span class="sticky-filter-icon">⭐</span>
    ${renderPersonalDropdown()}
  </div>`;

  const sortSelectHtml = isAll ? '' : `<div class="sticky-sort-group">
    <span class="sticky-bar-label">排序</span>
    ${renderSortDropdown('sticky-sort')}
  </div>`;

  const viewButtons = isBili
    ? `<button type="button" class="desktop-view-button ${state.biliViewMode === 'grouped' ? 'is-active' : ''}" data-action="set-bili-view-mode" data-bili-view-mode="grouped">同包聚合</button><button type="button" class="desktop-view-button ${state.biliViewMode === 'flat' ? 'is-active' : ''}" data-action="set-bili-view-mode" data-bili-view-mode="flat">视频平铺</button>`
    : `<button type="button" class="desktop-view-button ${state.viewMode === 'cards' ? 'is-active' : ''}" data-action="set-view-mode" data-view-mode="cards">卡片</button><button type="button" class="desktop-view-button ${state.viewMode === 'compact' ? 'is-active' : ''}" data-action="set-view-mode" data-view-mode="compact">紧凑</button>${isMcmod ? `<button type="button" class="desktop-view-button ${state.viewMode === 'table' ? 'is-active' : ''}" data-action="set-view-mode" data-view-mode="table">表格</button>` : ''}`;

  const hasActiveFilters = Boolean(
    state.category ||
    state.includedMods.length ||
    state.gameplayCategories.length ||
    state.query ||
    state.version ||
    state.loader ||
    state.pan ||
    state.dateRange ||
    state.serverOnly ||
    state.personalFilter
  );
  const activeResetHtml = hasActiveFilters
    ? `<button type="button" class="sticky-reset-btn" data-action="clear-filters" title="清空全部筛选条件">重置</button>`
    : '';

  const followBtnHtml = `<button type="button" class="sticky-tool-btn ${state.stickyFollowMode ? 'is-active' : ''}" data-action="toggle-sticky-follow" title="${state.stickyFollowMode ? '屏幕跟随模式已开启（向下滚动时吸顶常驻），点击可解除吸顶' : '点击开启屏幕跟随模式（向下滚动时吸顶常驻）'}">${state.stickyFollowMode ? '📌 跟随中' : '📌 开启跟随'}</button>`;
  const topBtnHtml = `<button type="button" class="sticky-tool-btn sticky-top-btn" data-action="scroll-to-top" title="返回页面顶部">↑ 顶部</button>`;

  const toolbarRowHtml = `<div class="sticky-bar-row sticky-toolbar-row">
    <div class="sticky-toolbar-left">
      ${searchInputHtml}
      <span class="sticky-separator" aria-hidden="true"></span>
      ${versionDropdownHtml}
      ${loaderDropdownHtml}
      ${statusDropdownHtml}
      ${sortSelectHtml ? `<span class="sticky-separator" aria-hidden="true"></span>${sortSelectHtml}` : ''}
    </div>
    <div class="sticky-toolbar-right">
      <div class="desktop-view-toggle" role="group" aria-label="结果视图">${viewButtons}</div>
      ${activeResetHtml}
      <span class="sticky-separator" aria-hidden="true"></span>
      ${followBtnHtml}
      ${topBtnHtml}
    </div>
  </div>`;

  // 2. Categories (Row 2)
  const categoryOptions = getCategoryOptionsWithCounts();
  let filteredCategoryOptions = categoryOptions;
  if (state.stickyCatSearch.trim()) {
    const q = state.stickyCatSearch.trim().toLowerCase();
    filteredCategoryOptions = categoryOptions.filter((cat) => {
      const label = getCategoryLabel(cat.value).toLowerCase();
      return label.includes(q) || cat.value.toLowerCase().includes(q);
    });
  }
  const categoryLimit = state.stickyCategoriesExpanded ? 999999 : 14;
  let topCategories = state.stickyCatSearch.trim()
    ? filteredCategoryOptions.slice(0, 50)
    : filteredCategoryOptions.slice(0, categoryLimit);
  if (!state.stickyCatSearch.trim() && state.category && !topCategories.some((c) => c.value === state.category)) {
    const selectedCat = categoryOptions.find((c) => c.value === state.category) || { value: state.category, count: 0 };
    topCategories = [selectedCat, ...topCategories];
  }
  const isAllCategoryActive = !state.category;
  const platformTotal = state.platform === 'all'
    ? (state.data ? ALL_PLATFORMS.reduce((sum, p) => sum + (state.data?.platforms[p]?.count || 0), 0) : state.total)
    : (state.data?.platforms[state.platform]?.count ?? state.total);
  const allCatPill = `<button type="button" class="sticky-pill ${isAllCategoryActive ? 'is-active' : ''}" data-action="set-sticky-category" data-category="" title="全部分类 (${formatCount(platformTotal)})">
    <span class="sticky-pill-name">全部</span>
    <span class="sticky-pill-count">${formatCount(platformTotal)}</span>
  </button>`;

  const categoryPillsHtml = topCategories.length > 0
    ? [
      allCatPill,
      ...topCategories.map((cat) => {
        const isActive = state.category === cat.value;
        const label = getCategoryLabel(cat.value);
        const tooltip = label !== cat.value
          ? `${esc(label)} (${esc(cat.value)}) (${formatCount(cat.count)})`
          : `${esc(label)} (${formatCount(cat.count)})`;
        return `<button type="button" class="sticky-pill ${isActive ? 'is-active' : ''}" data-action="set-sticky-category" data-category="${esc(cat.value)}" title="${tooltip}">
          <span class="sticky-pill-name">${esc(label)}</span>
          <span class="sticky-pill-count">${formatCount(cat.count)}</span>
        </button>`;
      }),
    ].join('')
    : `${allCatPill}<span class="sticky-no-match">无匹配分类</span>`;

  const catSearchBox = `<div class="sticky-search-input-wrap">
    <input type="search" id="sticky-cat-search" class="sticky-search-input" placeholder="🔍 搜索分类..." value="${esc(state.stickyCatSearch)}" aria-label="在栏内搜索分类" autocomplete="off" spellcheck="false" />
    ${state.stickyCatSearch ? `<button type="button" class="sticky-search-clear-btn" data-action="clear-sticky-cat-search" aria-label="清空分类搜索">✕</button>` : ''}
  </div>`;

  const canExpandCategories = categoryOptions.length > 12;
  const expandCategoriesBtn = canExpandCategories
    ? `<button type="button" class="sticky-expand-btn ${state.stickyCategoriesExpanded ? 'is-expanded' : ''}" data-action="toggle-sticky-categories-expanded" title="${state.stickyCategoriesExpanded ? '收起分类至常用' : `在栏内展开显示全部分类（共 ${categoryOptions.length} 类）`}">${state.stickyCategoriesExpanded ? '收起分类 ▴' : (categoryOptions.length > 14 ? `展开全部分类 (${categoryOptions.length}) ▾` : '展开分类 ▾')}</button>`
    : '';

  const openAllCategoriesBtn = state.availableCategories.length > 0
    ? `<button type="button" class="sticky-all-btn sticky-picker-trigger" data-action="open-picker" data-picker="category" title="打开全部分类检索独立弹窗（共 ${formatCount(state.availableCategories.length)} 类）"><span class="sticky-btn-icon">📑</span>分类库弹窗 (${formatCount(state.availableCategories.length)}) <span class="sticky-btn-arrow">↗</span></button>`
    : '';

  const categoryRowHtml = `<div class="sticky-bar-row sticky-category-row ${state.stickyCategoriesExpanded ? 'is-expanded' : ''}">
    <div class="sticky-row-left">
      <span class="sticky-bar-label">分类</span>
      ${catSearchBox}
      <div class="sticky-pills-flow">
        ${categoryPillsHtml}
      </div>
    </div>
    <div class="sticky-row-right">
      ${expandCategoriesBtn}
      ${openAllCategoriesBtn}
    </div>
  </div>`;

  // 3. Mods / Gameplay Categories (Row 3, if available)
  const hasMods = isMcmod || (isCurseforge && state.availableGameplayCategories.length > 0);
  let row3Html = '';

  if (hasMods) {
    if (isCurseforge && state.availableGameplayCategories.length > 0) {
      let filteredGameplay = state.availableGameplayCategories;
      if (state.stickyModSearch.trim()) {
        const q = state.stickyModSearch.trim().toLowerCase();
        filteredGameplay = state.availableGameplayCategories.filter((cat) => {
          const label = getCategoryLabel(cat.value).toLowerCase();
          return label.includes(q) || cat.value.toLowerCase().includes(q);
        });
      }
      const topGameplay = state.stickyModSearch.trim() ? filteredGameplay : state.availableGameplayCategories;
      const isAllGameplayActive = state.gameplayCategories.length === 0;
      const allGameplayPill = `<button type="button" class="sticky-pill ${isAllGameplayActive ? 'is-active' : ''}" data-action="clear-gameplay-categories" title="全部玩法">
        <span class="sticky-pill-name">全部</span>
      </button>`;
      const gameplayPills = topGameplay.length > 0
        ? [
          allGameplayPill,
          ...topGameplay.map((cat) => {
            const isActive = state.gameplayCategories.includes(cat.value);
            const label = getCategoryLabel(cat.value);
            const tooltip = label !== cat.value
              ? `${esc(label)} (${esc(cat.value)}) (${formatCount(cat.count)})`
              : `${esc(label)} (${formatCount(cat.count)})`;
            return `<button type="button" class="sticky-pill ${isActive ? 'is-active' : ''}" data-action="toggle-sticky-gameplay-category" data-category="${esc(cat.value)}" title="${tooltip}">
              <span class="sticky-pill-name">${esc(label)}</span>
              <span class="sticky-pill-count">${formatCount(cat.count)}</span>
            </button>`;
          }),
        ].join('')
        : `${allGameplayPill}<span class="sticky-no-match">无匹配玩法</span>`;

      const gameplaySearchBox = `<div class="sticky-search-input-wrap">
        <input type="search" id="sticky-mod-search" class="sticky-search-input" placeholder="🔍 搜索玩法分类..." value="${esc(state.stickyModSearch)}" aria-label="在栏内搜索玩法分类" autocomplete="off" spellcheck="false" />
        ${state.stickyModSearch ? `<button type="button" class="sticky-search-clear-btn" data-action="clear-sticky-mod-search" aria-label="清空玩法搜索">✕</button>` : ''}
      </div>`;

      const canExpandGameplay = state.availableGameplayCategories.length > 8;
      const expandGameplayBtn = canExpandGameplay
        ? `<button type="button" class="sticky-expand-btn ${state.stickyModsExpanded ? 'is-expanded' : ''}" data-action="toggle-sticky-mods-expanded" title="${state.stickyModsExpanded ? '收起玩法至常用' : `在栏内展开显示全部玩法分类（共 ${state.availableGameplayCategories.length} 类）`}">${state.stickyModsExpanded ? '收起玩法 ▴' : `展开全部玩法 (${state.availableGameplayCategories.length}) ▾`}</button>`
        : '';

      const openAllCurseforgeBtn = `<button type="button" class="sticky-all-btn sticky-picker-trigger" data-action="open-picker" data-picker="gameplay-category" title="打开玩法分类独立检索弹窗（共 ${state.availableGameplayCategories.length} 类）"><span class="sticky-btn-icon">🎮</span>玩法库弹窗 (${state.availableGameplayCategories.length}) <span class="sticky-btn-arrow">↗</span></button>`;
      const activeGameplayBadge = state.gameplayCategories.length > 0
        ? `<button type="button" class="sticky-active-badge" data-action="clear-gameplay-categories" title="点击清空已选玩法分类">已选玩法 ${state.gameplayCategories.length} ✕</button>`
        : '';

      row3Html = `<div class="sticky-bar-row sticky-mods-row ${state.stickyModsExpanded ? 'is-expanded' : ''}">
        <div class="sticky-row-left">
          <span class="sticky-bar-label">玩法</span>
          ${gameplaySearchBox}
          <div class="sticky-pills-flow">
            ${gameplayPills}
          </div>
        </div>
        <div class="sticky-row-right">
          ${expandGameplayBtn}
          ${openAllCurseforgeBtn}
          ${activeGameplayBadge}
        </div>
      </div>`;
    } else if (isMcmod) {
      let filteredMods = state.availableIncludedMods;
      if (state.stickyModSearch.trim()) {
        const q = state.stickyModSearch.trim().toLowerCase();
        filteredMods = state.availableIncludedMods.filter((mod) => mod.value.toLowerCase().includes(q));
      }
      const modLimit = state.stickyModsExpandAll
        ? state.availableIncludedMods.length
        : state.stickyModsExpanded
          ? 70
          : 14;
      let topMods = state.stickyModSearch.trim()
        ? filteredMods.slice(0, 100)
        : filteredMods.slice(0, modLimit);
      if (!state.stickyModSearch.trim()) {
        for (const sel of state.includedMods) {
          if (!topMods.some((m) => m.value === sel)) {
            const found = state.availableIncludedMods.find((m) => m.value === sel) || { value: sel, count: 0 };
            topMods.unshift(found);
          }
        }
      }
      const modPillsHtml = topMods.length > 0
        ? topMods.map((mod) => {
          const isActive = state.includedMods.includes(mod.value);
          const label = mod.value;
          return `<button type="button" class="sticky-pill ${isActive ? 'is-active' : ''}" data-action="toggle-included-mod" data-value="${esc(mod.value)}" title="${esc(label)} (${formatCount(mod.count)})">
            <span class="sticky-pill-name">${esc(label)}</span>
            <span class="sticky-pill-count">${formatCount(mod.count)}</span>
          </button>`;
        }).join('')
        : `<span class="sticky-no-match">无匹配模组</span>`;

      const modCountLabel = state.availableIncludedMods.length ? ` (${formatCount(state.availableIncludedMods.length)}款)` : '';
      const modSearchBox = `<div class="sticky-search-input-wrap">
        <input type="search" id="sticky-mod-search" class="sticky-search-input" placeholder="🔍 搜索模组${modCountLabel}..." value="${esc(state.stickyModSearch)}" aria-label="在栏内搜索模组" autocomplete="off" spellcheck="false" />
        ${state.stickyModSearch ? `<button type="button" class="sticky-search-clear-btn" data-action="clear-sticky-mod-search" aria-label="清空模组搜索">✕</button>` : ''}
      </div>`;

      const canExpandMods = state.availableIncludedMods.length > 8;
      const canExpandAllMods = state.availableIncludedMods.length > 70;
      let expandModsControls = '';
      if (canExpandMods) {
        if (state.stickyModsExpandAll) {
          expandModsControls = `<button type="button" class="sticky-expand-btn is-expanded" data-action="toggle-sticky-mods-expand-all" title="收起全部模组至常用">收起全部 ▴</button>`;
        } else if (state.stickyModsExpanded) {
          expandModsControls = `<button type="button" class="sticky-expand-btn is-expanded" data-action="toggle-sticky-mods-expanded" title="收起模组至常用">收起模组 ▴</button>
          ${canExpandAllMods ? `<button type="button" class="sticky-expand-btn sticky-expand-all-btn" data-action="toggle-sticky-mods-expand-all" title="在栏内直接平铺展开全部 ${formatCount(state.availableIncludedMods.length)} 款模组（无需弹窗）">展开全部 (${formatCount(state.availableIncludedMods.length)}) ▾</button>` : ''}`;
        } else {
          expandModsControls = `<button type="button" class="sticky-expand-btn" data-action="toggle-sticky-mods-expanded" title="在栏内展开显示前 70 款热门模组">展开模组 ▾</button>
          ${canExpandAllMods ? `<button type="button" class="sticky-expand-btn sticky-expand-all-btn" data-action="toggle-sticky-mods-expand-all" title="在栏内直接平铺展开全部 ${formatCount(state.availableIncludedMods.length)} 款模组（无需弹窗）">展开全部 ▾</button>` : ''}`;
        }
      }

      const openAllModsBtn = `<button type="button" class="sticky-all-btn sticky-picker-trigger" data-action="open-picker" data-picker="included-mod" title="打开全部收录模组库独立弹窗（共 ${formatCount(state.availableIncludedMods.length)} 款，支持按拼音/中英检索与多选）"><span class="sticky-btn-icon">🧩</span>模组库弹窗 (${formatCount(state.availableIncludedMods.length)}) <span class="sticky-btn-arrow">↗</span></button>`;
      const activeModBadge = state.includedMods.length > 0
        ? `<button type="button" class="sticky-active-badge" data-action="clear-included-mods" title="点击清空已选包含模组">已选模组 ${state.includedMods.length} ✕</button>`
        : '';

      row3Html = `<div class="sticky-bar-row sticky-mods-row ${state.stickyModsExpanded ? 'is-expanded' : ''} ${state.stickyModsExpandAll ? 'is-expanded-all' : ''}">
        <div class="sticky-row-left">
          <span class="sticky-bar-label">模组</span>
          ${modSearchBox}
          <div class="sticky-pills-flow">
            ${modPillsHtml}
          </div>
        </div>
        <div class="sticky-row-right">
          ${expandModsControls}
          ${openAllModsBtn}
          ${activeModBadge}
        </div>
      </div>`;
    }
  }

  // 4. Active filters chips row (if any)
  const activeFiltersHtml = renderActiveFilters();
  const activeFiltersRowHtml = activeFiltersHtml
    ? `<div class="sticky-bar-row sticky-active-filters-row">${activeFiltersHtml}</div>`
    : '';

  return `<nav class="desktop-sticky-bar ${state.stickyFollowMode ? 'is-sticky' : ''}" aria-label="跟随屏幕快捷筛选与排序导航">
    ${toolbarRowHtml}
    ${categoryRowHtml}
    ${row3Html}
    ${activeFiltersRowHtml}
  </nav>`;
}

export function setStickyFollowStateForTest(params: {
  platform?: FilterPlatform;
  category?: string;
  availableCategories?: string[];
  gameplayCategories?: string[];
  availableGameplayCategories?: DesktopFilterOption[];
  availableIncludedMods?: DesktopFilterOption[];
  includedMods?: string[];
  sort?: string;
  stickyFollowMode?: boolean;
  stickyModsExpanded?: boolean;
  stickyModsExpandAll?: boolean;
  stickyCategoriesExpanded?: boolean;
  stickyModSearch?: string;
  stickyCatSearch?: string;
  records?: DesktopRecord[];
}): void {
  if (params.platform) state.platform = params.platform;
  if (params.category !== undefined) state.category = params.category;
  if (params.availableCategories) state.availableCategories = params.availableCategories;
  if (params.gameplayCategories) state.gameplayCategories = params.gameplayCategories;
  if (params.availableGameplayCategories) state.availableGameplayCategories = params.availableGameplayCategories;
  if (params.availableIncludedMods) state.availableIncludedMods = params.availableIncludedMods;
  if (params.includedMods) state.includedMods = params.includedMods;
  if (params.sort) state.sort = params.sort;
  if (params.stickyFollowMode !== undefined) state.stickyFollowMode = params.stickyFollowMode;
  if (params.stickyModsExpanded !== undefined) state.stickyModsExpanded = params.stickyModsExpanded;
  if (params.stickyModsExpandAll !== undefined) state.stickyModsExpandAll = params.stickyModsExpandAll;
  if (params.stickyCategoriesExpanded !== undefined) state.stickyCategoriesExpanded = params.stickyCategoriesExpanded;
  if (params.stickyModSearch !== undefined) state.stickyModSearch = params.stickyModSearch;
  if (params.stickyCatSearch !== undefined) state.stickyCatSearch = params.stickyCatSearch;
  if (params.records) state.records = params.records;
}

function renderBiliContentControls(): string {
  if (state.platform !== 'bilibili') return '';
  return `<section class="notice pages-bili-content-controls" aria-label="B站内容筛选"><div>${([['candidates','发布 / 更新 / 预告'],['secondary','分享 / 推荐 / 介绍'],['excluded','已过滤 / 待核验'],['all','全部存档']] as const).map(([key,label]) => `<button type="button" class="button ${state.bilibiliContent === key ? 'primary' : 'secondary'} small" data-action="set-bili-content" data-content="${key}">${label}${state.bilibiliCounts.all ? ' ' + formatCount(state.bilibiliCounts[key]) : ''}</button>`).join('')}</div><p>默认只看发布、更新与预告线索；分享、推荐、介绍和转载另列，不作为UP主原创发布。明确自制的分享保留在发布线索中；标题不必使用固定格式。下载链接和视频日期不能证明作者归属或新版本。实况、教程、推广及待核验记录另列；全部存档保留。</p></section>`;
}

function renderResultsWorkspace(selectedName: string): string {
  if (isStaticOverview()) {
    return `<section class="notice" data-pages-summary-ready="${Boolean(state.data?.hasData)}"><h2>${state.data?.hasData ? '选择来源，开始浏览' : '正在读取公开目录…'}</h2><p>上方数量与更新时间来自公开目录，记录尚未全部加载。打开一个来源只加载该来源；输入关键词后在六平台完整数据中搜索。代表记录在加载后展示。</p></section>`;
  }
  const records = currentRecords();
  const data = state.data;
  const hasPlatformFilter = state.platform === 'mcmod' ? state.includedMods.length > 0 : state.platform === 'curseforge' ? state.gameplayCategories.length > 0 : false;
  const hasFilter = state.query || state.version || state.loader || (state.platform !== 'curseforge' && state.category) || state.pan || state.dateRange || state.serverOnly || state.personalFilter || hasPlatformFilter;
  const isAllPlatform = state.platform === 'all';
  const isBili = state.platform === 'bilibili';
  const resultBody = isBili
    ? state.biliViewMode === 'grouped' ? renderBilibiliGroupedWorkspace() : renderBilibiliFlatWorkspace(records)
    : records.length
      ? state.viewMode === 'compact'
        ? `<div class="compact-record-list">${records.map(renderCompactRecord).join('')}</div>`
        : state.viewMode === 'table' && state.platform === 'mcmod'
          ? renderMcmodTable(records)
        : state.platform !== 'all'
            ? `<div class="pack-grid legacy-rich-grid">${records.map((record, index) => `<article class="desktop-rich-card" data-action="select-record" data-index="${index}">${renderPlatformRichCard(record)}${renderPersonalCardZone(renderPersonalCardActions(record, index))}</article>`).join('')}</div>`
          : `<div class="pack-grid">${records.map(renderRecord).join('')}</div>`
      : `<div class="empty-state compact-empty"><div class="empty-icon">⌕</div><h3>没有匹配的整合包</h3><p>换一个关键词或清除筛选条件。</p><button class="button secondary" data-action="clear-filters">清除筛选</button></div>`;
  const displayedCount = isBili && state.biliViewMode === 'grouped' ? Math.min(state.page * 48, state.biliGroups.length) : records.length;
  const totalLabel = isBili && state.biliViewMode === 'grouped' ? state.biliGroups.length : state.total;
  const resultHeading = isAllPlatform ? '分平台结果' : state.loading ? '正在读取数据…' : hasFilter ? '筛选结果' : '最近可用数据';
  const resultCount = isAllPlatform ? `${formatCount(displayedCount)} 条已加载 · 每个平台最多 12 条/轮` : `${formatCount(displayedCount)} / ${formatCount(totalLabel)}`;
  const loadMoreLabel = isAllPlatform
    ? `各平台继续加载（当前第 ${state.page} 轮）`
    : isBili && state.biliViewMode === 'grouped'
      ? `加载更多（已显示 ${formatCount(displayedCount)} / ${formatCount(state.biliGroups.length)}）`
      : `加载更多（已显示 ${formatCount(records.length)} / ${formatCount(state.total)}）`;
  const recordsFailure = `<div class="error-state"><div class="empty-icon">!</div><h3>整合包记录加载失败</h3><p>${esc(state.recordsError)}</p><button type="button" class="button secondary" data-action="retry-records">重试加载</button></div>`;
  const recordsBody = !data?.hasData
    ? `<div class="empty-state"><div class="empty-icon">◌</div><h3>还没有本地数据快照</h3><p>选择现有的 <code>converted_output</code>、<code>build/frontend_preview</code> 或其 <code>data</code> 目录。应用不会把空数据伪装成成功。</p><button class="button primary" data-action="choose-data">选择数据目录</button></div>`
    : state.loading
      ? isStaticSite() ? `<div class="loading-state pages-loading-progress" role="status">${esc(pagesLoadingMessage())}</div>` : '<div class="loading-state">正在读取当前快照…</div>'
      : state.recordsError && !records.length
        ? recordsFailure
        : `${state.recordsError ? recordsFailure : ''}${resultBody}${state.hasMore ? `<div class="load-more"><button class="button secondary" data-action="load-more">${loadMoreLabel}</button></div>` : ''}`;
  return `<div class="content-grid"><section class="results-column">${renderStickyFollowBar()}${renderBiliContentControls()}<div class="results-heading"><div><span class="eyebrow">${esc(selectedName)}</span><h2>${state.loading ? '正在读取数据…' : state.recordsError && !records.length ? '加载失败' : resultHeading}</h2></div><span class="result-count">${state.loading || (state.recordsError && !records.length) ? '' : resultCount}</span></div>${state.message ? `<div class="notice">${esc(state.message)}</div>` : ''}${recordsBody}</section></div>`;
}

function renderRelease(release: Record<string, unknown>): string {
  const downloads = Array.isArray(release.downloads) ? release.downloads : Array.isArray(release.download_links) ? release.download_links : Array.isArray(release.files) ? release.files : Array.isArray(release.links) ? release.links : [];
  const links = downloads.map((download) => {
    const item = (download || {}) as Record<string, unknown>;
    const url = safeExternalUrl(item.url);
    const code = item.code || item.info ? ` (${esc(String(item.code || item.info))})` : '';
    return url ? `<a class="detail-link" href="${esc(url)}" target="_blank" rel="noreferrer">${esc(String(item.name || '打开下载'))}${code} ↗</a>` : '';
  }).filter(Boolean).join('');
  const versions = valueList(release.gameVersions ?? release.game_versions ?? release.mc_versions).join('、');
  const loaders = valueList(release.loaders ?? release.loader).join('、');
  const sourceNotes = String(release.changelogMd || release.changelog || release.changelogHtml || release.notes || '').replace(/<\/(?:p|div|li|h[1-6])\s*>|<br\s*\/?>/gi, '\n').replace(/<[^>]*>/g, '').trim();
  const notes = sourceNotes === '该版本未提供更新日志说明。' ? '' : sourceNotes;
  const rawReleaseDate = String(release.date || release.release_date || release.date_published || release.create_date || release.createDate || '').trim();
  const releaseDate = formatDisplayDate(rawReleaseDate) || rawReleaseDate;
  const notesHtml = notes.length > 260
    ? `<details class="release-notes-fold"><summary>查看完整更新说明</summary><p class="release-notes">${esc(notes)}</p></details>`
    : notes ? `<p class="release-notes">${esc(notes)}</p>` : '';
  return `<article class="release-item"><div class="release-head"><strong>${textOrUnknown(String(release.versionName || release.version_number || release.version || release.name || release.label || release.displayName || release.fileName || ''))}</strong><span>${esc(releaseDate || UNKNOWN_LOCAL_TEXT)}</span></div><div class="release-meta">${versions ? `Minecraft：${esc(versions)}` : ''}${loaders ? ` · Loader：${esc(loaders)}` : ''}</div>${notesHtml}${links ? `<div class="release-links">${links}</div>` : ''}</article>`;
}

function getPlatformCommentWebUrl(record: DesktopRecord): string {
  const url = safeExternalUrl(record.url);
  if (record.platform === 'mcmod') {
    return `https://www.mcmod.cn/modpack/${record.sourceId}.html#comment`;
  }
  if (record.platform === 'bilibili') {
    const raw = (record.raw || {}) as Record<string, unknown>;
    const bvid = String(raw.bvid || record.sourceId);
    return `https://www.bilibili.com/video/${bvid}#reply`;
  }
  if (record.platform === 'curseforge') {
    return url ? (url.endsWith('/') ? `${url}comments` : `${url}/comments`) : '';
  }
  if (record.platform === 'bbsmc') {
    return url ? `${url}#reviews` : '';
  }
  if (record.platform === 'xyebbs') {
    return url ? `${url}#post_` : '';
  }
  return url;
}

function renderCommentSection(record: DesktopRecord): string {
  const rawDesc = (rawText(record, ['desc', 'description', 'summary', 'subtitle_summary']) || record.summary || '').trim();
  const hasDesc = Boolean(rawDesc && rawDesc !== '未知' && !rawDesc.includes('本地数据未提供'));
  const descHtml = hasDesc ? `<div class="detail-section"><h3>简介</h3><p class="detail-summary">${esc(rawDesc)}</p></div>` : '';

  const pinned = rawText(record, ['pinned_comment']).trim();
  const commentState = state.comments.sourceId === record.sourceId ? state.comments : null;
  const hasComments = Boolean(pinned || (commentState?.available && commentState.comments?.length) || commentState?.loading || commentState?.error);
  const webCommentUrl = getPlatformCommentWebUrl(record);
  const webCommentAction = webCommentUrl
    ? `<div class="detail-comment-web-entry"><button type="button" class="button secondary wide" data-action="open-comment-preview" data-record-id="${esc(record.id)}">💬 ${isStaticSite() ? '查看已采集评论与来源' : '软件内小窗浏览'}「${esc(PLATFORM_CONFIGS[record.platform]?.name || '')}」原站讨论与评论</button></div>`
    : '';

  if (!hasComments) {
    return descHtml;
  }

  const independentComments = commentState?.available
    ? renderComments(commentState.comments)
    : commentState?.loading
      ? '<div class="loading-state">正在读取独立评论…</div>'
      : commentState?.error
        ? `<div class="error-box">${esc(commentState.error)}</div>`
        : '';
  const pinnedHtml = pinned ? `<article class="comment-item"><div class="comment-head"><strong>来源置顶评论</strong></div><p>${esc(pinned)}</p></article>` : '';
  const meta = commentState?.pageCount ? `<span class="detail-submeta">记录数：${commentState.pageCount}</span>` : '';
  return `${descHtml}<div class="detail-section"><h3>评论 / 讨论 ${meta}</h3>${pinnedHtml}${independentComments}${webCommentAction}</div>`;
}

function renderMediaSection(record: DesktopRecord): string {
  const urls = recordImageUrls(record);
  if (!urls.length) return '';
  return `<div class="detail-section"><h3>图片 <span class="detail-submeta">${urls.length} 张 · 点击放大</span></h3><div class="detail-image-gallery">${urls.map((url, index) => renderImageButton(url, `${record.title}图片${index + 1}`, 'detail-image', PLATFORM_COVER_FALLBACKS[record.platform])).join('')}</div></div>`;
}

function renderDetailFacts(record: DesktopRecord): string {
  const raw = record.raw || {};
  const pairs: Array<[string, string]> = record.platform === 'bilibili'
    ? [['播放', formatMetric(raw.views)], ['点赞', formatMetric(raw.likes)], ['投币', formatMetric(raw.coins)], ['收藏', formatMetric(raw.favorites)], ['评论', formatMetric(raw.reply)], ['弹幕', formatMetric(raw.danmaku)], ['QQ群', raw.qq_group ? String(raw.qq_group) : ''], ['提取码', raw.extract_code ? String(raw.extract_code) : '']]
    : record.platform === 'mcmod'
      ? [['浏览', formatMetric(raw.views)], ['推荐', formatMetric(raw.recommendations)], ['收藏', formatMetric(raw.favorites)], ['评论', formatMetric(raw.commentsCount)], ['模组数', raw.includedModsCount ? `${raw.includedModsCount} 款` : ''], ['类型', raw.typeName ? String(raw.typeName) : '']]
      : [['下载', formatMetric(raw.downloads)], ['关注', formatMetric(raw.followers)], ['点赞', formatMetric(raw.likes)], ['浏览', formatMetric(raw.views)], ['评论', formatMetric(raw.comments)]];
  const valid = pairs.filter(([, value]) => value && value !== '—' && value !== '未知' && !value.includes('本地数据未提供'));
  if (!valid.length) return '';
  return `<div class="detail-facts-row">${valid.map(([label, value]) => `<div class="detail-fact-chip"><span class="detail-fact-label">${esc(label)}</span><strong class="detail-fact-val">${esc(value)}</strong></div>`).join('')}</div>`;
}

function renderDetailDownloadLinks(record: DesktopRecord): string {
  const links = rawRecords(record, ['download_links']).filter((item) => safeExternalUrl(item.url));
  if (!links.length) return '';
  return `<div class="detail-section"><h3>下载与渠道 <span class="detail-submeta">${links.length} 个入口</span></h3><div class="release-links">${links.map((link) => `<a class="detail-link" href="${esc(safeExternalUrl(link.url))}" target="_blank" rel="noreferrer">${esc(String(link.name || link.type || '下载入口'))} ↗</a>`).join('')}</div></div>`;
}

export function renderPackVersionDetail(record: Pick<DesktopRecord, 'platform' | 'packVersion'>): string {
  if (record.platform !== 'mcmod') return '';
  return `<div class="detail-section"><dl><div><dt>整合包版本名</dt><dd>${textOrUnknown(record.packVersion)}</dd></div></dl></div>`;
}

export function renderCurseforgeFileIndexDetail(record: Pick<DesktopRecord, 'platform' | 'fileIndexes' | 'mainFileId'>): string {
  if (record.platform !== 'curseforge') return '';
  const indexes = record.fileIndexes;
  const mainFileId = record.mainFileId;
  const mainFileIdProvided = mainFileId !== undefined && mainFileId !== null && String(mainFileId) !== '';
  const hasMainFile = mainFileIdProvided && Array.isArray(indexes)
    && indexes.some((index) => index.fileId !== null && String(index.fileId) === String(mainFileId));
  const mainFileNote = mainFileIdProvided && !hasMainFile
    ? `<p class="empty-evidence">主文件 ID ${esc(mainFileId)} 未出现在当前文件索引中。</p>`
    : '';
  let indexBody = `<div class="empty-evidence">当前数据未提供文件索引。</div>`;

  if (Array.isArray(indexes)) {
    if (!indexes.length) {
      indexBody = '<div class="empty-evidence">当前来源数据没有文件索引项。</div>';
    } else {
      const groups = new Map<string, { fileId: string | number | null; indexes: DesktopCurseforgeFileIndex[] }>();
      indexes.forEach((index, indexPosition) => {
        const hasId = index.fileId !== null && String(index.fileId) !== '';
        const key = hasId ? `file:${String(index.fileId)}` : `missing:${indexPosition}`;
        const group = groups.get(key) || { fileId: index.fileId, indexes: [] };
        group.indexes.push(index);
        groups.set(key, group);
      });
      const releaseTypeLabel = (value: string | number | null): string => {
        const known: Record<string, string> = { '1': '正式版', '2': 'Beta', '3': 'Alpha' };
        if (value === null || String(value) === '') return UNKNOWN_LOCAL_TEXT;
        return known[String(value)] || `未知发布类型（${String(value)}）`;
      };
      const loaderValueLabel = (value: string | number | null): string => {
        const known: Record<string, string> = {
          '0': '任意 Loader',
          '1': 'Forge',
          '2': 'Cauldron',
          '3': 'LiteLoader',
          '4': 'Fabric',
          '5': 'Quilt',
          '6': 'NeoForge',
        };
        if (value === null || String(value) === '') return UNKNOWN_LOCAL_TEXT;
        return known[String(value)] || `未知 Loader（${String(value)}）`;
      };
      indexBody = `<div class="curseforge-file-index-list">${[...groups.values()].map((group) => {
        const groupHasMain = mainFileIdProvided && group.fileId !== null && String(group.fileId) === String(mainFileId);
        const entries = group.indexes.map((index) => `<li class="curseforge-file-index-entry"><strong>${esc(index.filename || UNKNOWN_LOCAL_TEXT)}</strong><span>类型：${esc(releaseTypeLabel(index.releaseType))} · Minecraft：${esc(index.gameVersion || UNKNOWN_LOCAL_TEXT)} · Loader：${esc(loaderValueLabel(index.modLoader))}</span></li>`).join('');
        return `<section class="curseforge-file-index-group"><h4>文件 ID：${group.fileId === null ? UNKNOWN_LOCAL_TEXT : esc(group.fileId)}${groupHasMain ? '<span class="detail-submeta">主文件</span>' : ''}</h4><ul>${entries}</ul></section>`;
      }).join('')}</div><p class="detail-submeta">${groups.size} 个文件 ID · ${indexes.length} 条索引项</p>`;
    }
  }

  return `<div class="detail-section"><h3>来源提供的文件索引 <span class="detail-submeta">非完整历史</span></h3><p class="detail-summary">这些是来源响应提供的有限索引，不代表完整文件或发布历史。</p>${mainFileNote}${indexBody}</div>`;
}

const MCMOD_TREND_RANGES: Array<{ value: McmodTrendRange; label: string }> = [
  { value: '7d', label: '近 7 天' },
  { value: '30d', label: '近 30 天' },
  { value: '60d', label: '近 60 天' },
  { value: 'all', label: '全部历史' },
];

function formatTrendValue(value: number): string {
  return new Intl.NumberFormat('zh-CN', { maximumFractionDigits: 2 }).format(value);
}

function selectedMcmodTrendPoints(): McmodTrendPoint[] {
  const chart = state.trendChart;
  if (!chart) return [];
  const series = mcmodTrendSeries(chart.record);
  return series.status === 'ready' ? selectMcmodTrendRange(series.points, chart.range) : series.points;
}

function renderMcmodTrendSvg(points: McmodTrendPoint[]): string {
  const width = 760;
  const height = 300;
  const paddingLeft = 58;
  const paddingRight = 22;
  const paddingTop = 24;
  const paddingBottom = 42;
  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;
  const values = points.map((point) => point.value);
  const minimum = values.reduce((current, value) => Math.min(current, value), Number.POSITIVE_INFINITY);
  const maximum = values.reduce((current, value) => Math.max(current, value), Number.NEGATIVE_INFINITY);
  const valueSpan = maximum - minimum || 1;
  const coordinates = points.map((point, index) => ({
    ...point,
    x: paddingLeft + index / (points.length - 1) * chartWidth,
    y: paddingTop + (maximum - point.value) / valueSpan * chartHeight,
  }));
  const linePath = coordinates.map((point, index) => `${index ? 'L' : 'M'} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`).join(' ');
  const areaPath = `${linePath} L ${coordinates[coordinates.length - 1].x.toFixed(2)} ${height - paddingBottom} L ${coordinates[0].x.toFixed(2)} ${height - paddingBottom} Z`;
  const last = coordinates[coordinates.length - 1];
  return `<svg class="mcmod-trend-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="MC百科官方流行指数历史折线图，${points.length} 个有效点">
    <line class="mcmod-trend-grid" x1="${paddingLeft}" y1="${paddingTop}" x2="${width - paddingRight}" y2="${paddingTop}" />
    <line class="mcmod-trend-grid" x1="${paddingLeft}" y1="${height - paddingBottom}" x2="${width - paddingRight}" y2="${height - paddingBottom}" />
    <text class="mcmod-trend-axis-label" x="4" y="${paddingTop + 4}">${formatTrendValue(maximum)}</text>
    <text class="mcmod-trend-axis-label" x="4" y="${height - paddingBottom + 4}">${formatTrendValue(minimum)}</text>
    <path class="mcmod-trend-area" d="${areaPath}" />
    <path class="mcmod-trend-line" d="${linePath}" />
    <g aria-hidden="true">${coordinates.map((point) => `<circle class="mcmod-trend-dot" cx="${point.x.toFixed(2)}" cy="${point.y.toFixed(2)}" r="2.8" />`).join('')}</g>
    <line class="mcmod-trend-guide" data-trend-guide x1="${last.x.toFixed(2)}" y1="${paddingTop}" x2="${last.x.toFixed(2)}" y2="${height - paddingBottom}" />
    <rect class="mcmod-trend-capture" data-trend-capture x="${paddingLeft}" y="${paddingTop}" width="${chartWidth}" height="${chartHeight}" tabindex="0" role="slider" aria-label="浏览历史趋势点，使用左右方向键移动" aria-valuemin="0" aria-valuemax="${points.length - 1}" aria-valuenow="${points.length - 1}" aria-valuetext="${esc(last.date)}，${formatTrendValue(last.value)}" />
    <text class="mcmod-trend-date-label" x="${paddingLeft}" y="${height - 10}" text-anchor="start">${esc(coordinates[0].date)}</text>
    <text class="mcmod-trend-date-label" x="${width - paddingRight}" y="${height - 10}" text-anchor="end">${esc(last.date)}</text>
  </svg>`;
}

function renderMcmodTrendDialog(): string {
  const chart = state.trendChart;
  if (!chart) return '';
  const series = mcmodTrendSeries(chart.record);
  const points = series.status === 'ready' ? selectMcmodTrendRange(series.points, chart.range) : series.points;
  const hasChart = series.status === 'ready' && points.length >= 2;
  const summary = hasChart ? summarizeMcmodTrend(points) : null;
  const point = hasChart ? points[points.length - 1] : null;
  const firstPoint = hasChart ? points[0] : null;
  const rangeDelta = firstPoint && point ? point.value - firstPoint.value : null;
  const rangePercent = firstPoint && rangeDelta !== null && firstPoint.value !== 0
    ? rangeDelta / Math.abs(firstPoint.value) * 100
    : null;
  const signedTrendValue = (value: number): string => `${value > 0 ? '+' : ''}${formatTrendValue(value)}`;
  const trendDirectionClass = rangeDelta === null || rangeDelta === 0 ? '' : rangeDelta > 0 ? 'is-up' : 'is-down';
  const emptyText = series.status !== 'ready'
    ? mcmodTrendStatusText(series)
    : `所选时间范围内只有 ${points.length} 个有效历史点；至少需要两个点才能绘制走势。`;
  const rangeControls = MCMOD_TREND_RANGES.map((range) => `<button type="button" class="mcmod-trend-range ${chart.range === range.value ? 'is-active' : ''}" data-action="set-mcmod-trend-range" data-range="${range.value}" aria-pressed="${chart.range === range.value}" ${series.status === 'ready' ? '' : 'disabled'}>${range.label}</button>`).join('');
  return `<div class="modal-backdrop mcmod-trend-backdrop" data-action="close-mcmod-trend" role="dialog" aria-modal="true" aria-labelledby="mcmod-trend-title">
    <section class="modal-panel mcmod-trend-panel" data-mcmod-trend-panel onclick="event.stopPropagation()">
      <header class="modal-header"><div class="modal-title-wrap"><span class="eyebrow">MCMOD HISTORY</span><h2 id="mcmod-trend-title">${esc(chart.record.title)} · 趋势</h2></div><button type="button" class="modal-close mcmod-trend-close" data-action="close-mcmod-trend" aria-label="关闭趋势图">×</button></header>
      <div class="mcmod-trend-controls"><span class="mcmod-trend-metric">指标：官方流行指数</span><div class="mcmod-trend-ranges" aria-label="趋势时间范围">${rangeControls}</div></div>
      ${hasChart && summary ? `<p class="mcmod-trend-period">${esc(summary.firstDate)} 至 ${esc(summary.lastDate)} · ${summary.count} 个有效历史点</p>
        <div class="mcmod-trend-summary" aria-label="当前范围统计"><div><span>起点</span><strong>${formatTrendValue(firstPoint!.value)}</strong></div><div><span>最新</span><strong>${formatTrendValue(summary.latest)}</strong></div><div><span>区间变化</span><strong class="${trendDirectionClass}">${rangeDelta === null ? '—' : signedTrendValue(rangeDelta)}</strong></div><div><span>区间涨跌</span><strong class="${trendDirectionClass}">${rangePercent === null ? '—' : `${rangePercent > 0 ? '+' : ''}${rangePercent.toFixed(1)}%`}</strong></div><div><span>最低 / 最高</span><strong>${formatTrendValue(summary.minimum)} / ${formatTrendValue(summary.maximum)}</strong></div><div><span>平均</span><strong>${formatTrendValue(summary.average)}</strong></div></div>
        <div class="mcmod-trend-chart-wrap">${renderMcmodTrendSvg(points)}</div>
        <output class="mcmod-trend-readout" data-trend-readout aria-live="polite">最新 · ${esc(point!.date)} · 指数 ${formatTrendValue(point!.value)}</output>
        ${series.skippedCount ? `<p class="mcmod-trend-note">已跳过 ${series.skippedCount} 个日期或数值异常的配对点；其他日期和值仍按原索引配对。</p>` : ''}
      ` : `<div class="mcmod-trend-empty" role="status">${esc(emptyText)}</div>`}
      <p class="mcmod-trend-footnote">当前快照只提供官方流行指数历史序列；7／30／60 天涨幅等汇总不作为独立曲线。图表不以当前值或汇总补造历史。</p>
    </section>
  </div>`;
}

export function setPickerModalForTest(
  picker: PickerModalState | null,
  context?: {
    platform?: FilterPlatform;
    includedMods?: string[];
    availableIncludedMods?: DesktopFilterOption[];
    gameplayCategories?: string[];
    availableGameplayCategories?: DesktopFilterOption[];
    category?: string;
    availableCategories?: string[];
  },
): void {
  state.pickerModal = picker;
  if (context?.platform) state.platform = context.platform;
  if (context?.includedMods) state.includedMods = context.includedMods;
  if (context?.availableIncludedMods) state.availableIncludedMods = context.availableIncludedMods;
  if (context?.gameplayCategories) state.gameplayCategories = context.gameplayCategories;
  if (context?.availableGameplayCategories) state.availableGameplayCategories = context.availableGameplayCategories;
  if (context?.category !== undefined) state.category = context.category;
  if (context?.availableCategories) state.availableCategories = context.availableCategories;
}

export function setInAppWindowStateForTest(
  inAppWindow: { url: string; title: string; recordId?: string; maximized?: boolean; activeTab?: 'web' | 'changelog' } | null,
  selected: DesktopRecord | null,
  previousSelected: DesktopRecord | null,
): void {
  state.inAppWindow = inAppWindow;
  state.inAppWindows = inAppWindow ? [inAppWindow] : [];
  state.selected = selected;
  state.inAppWindowPreviousSelected = previousSelected;
}

export function getInAppWindowStateForTest(): {
  inAppWindow: { url: string; title: string; recordId?: string; maximized?: boolean; activeTab?: 'web' | 'changelog' } | null;
  selected: DesktopRecord | null;
  previousSelected: DesktopRecord | null;
} {
  return {
    inAppWindow: state.inAppWindow,
    selected: state.selected,
    previousSelected: state.inAppWindowPreviousSelected,
  };
}

export function renderPickerModal(): string {
  const picker = state.pickerModal;
  if (!picker) return '';

  let title = '';
  let eyebrow = '';
  let ruleHint = '';
  let allItems: Array<{ value: string; count?: number }> = [];
  let selectedValues: string[] = [];

  if (picker.type === 'included-mod') {
    eyebrow = 'MOD DISCOVERY · 包含模组发现';
    title = `全部收录模组（${formatCount(state.availableIncludedMods.length)} 款）`;
    ruleHint = '筛选包含指定模组的整合包 · 点击可多选（再次点击取消） · 按整合包收录数量排序';
    allItems = state.availableIncludedMods;
    selectedValues = state.includedMods;
  } else if (picker.type === 'gameplay-category') {
    eyebrow = 'GAMEPLAY DISCOVERY · 玩法分类发现';
    title = `CurseForge 玩法分类（${state.availableGameplayCategories.length} 类）`;
    ruleHint = '筛选包含指定玩法分类的整合包 · 点击可多选（再次点击取消） · 按整合包收录数量排序';
    allItems = state.availableGameplayCategories;
    selectedValues = state.gameplayCategories;
  } else if (picker.type === 'category') {
    const platName = state.platform === 'all' ? '全平台' : (PLATFORM_CONFIGS[state.platform]?.name || '');
    eyebrow = 'CATEGORY DISCOVERY · 分类发现';
    title = `${platName} 全部分类与标签（${state.availableCategories.length} 类）`;
    ruleHint = '按分类标签精准筛选 · 点击选择单项分类（再次点击清除）';
    allItems = getCategoryOptionsWithCounts();
    selectedValues = state.category ? [state.category] : [];
  }

  const isCatOrGameplay = picker.type === 'category' || picker.type === 'gameplay-category';
  const sortMode: PickerSort = picker.sort || 'count_desc';

  const query = picker.search.trim().toLowerCase();
  const matched = query
    ? allItems.filter((item) => {
        const valLower = item.value.toLowerCase();
        if (valLower.includes(query)) return true;
        if (isCatOrGameplay) {
          const label = getCategoryLabel(item.value).toLowerCase();
          if (label.includes(query)) return true;
        }
        return false;
      })
    : allItems;

  const filtered = [...matched].sort((a, b) => {
    const countA = a.count ?? 0;
    const countB = b.count ?? 0;
    const labelA = isCatOrGameplay ? getCategoryLabel(a.value) : a.value;
    const labelB = isCatOrGameplay ? getCategoryLabel(b.value) : b.value;
    if (sortMode === 'count_desc') {
      if (countB !== countA) return countB - countA;
      return labelA.localeCompare(labelB, 'zh-Hans-CN');
    }
    if (sortMode === 'count_asc') {
      if (countA !== countB) return countA - countB;
      return labelA.localeCompare(labelB, 'zh-Hans-CN');
    }
    if (sortMode === 'name_asc') {
      return labelA.localeCompare(labelB, 'zh-Hans-CN');
    }
    if (sortMode === 'name_desc') {
      return labelB.localeCompare(labelA, 'zh-Hans-CN');
    }
    return 0;
  });

  const displayItems = filtered.slice(0, picker.limit);
  const remaining = filtered.length - displayItems.length;

  return `<div class="modal-backdrop picker-modal-backdrop" data-action="close-picker-modal" role="dialog" aria-modal="true" aria-labelledby="picker-modal-title">
    <section class="modal-panel picker-modal-panel" onclick="event.stopPropagation()">
      <header class="modal-header">
        <div class="modal-title-wrap">
          <span class="eyebrow">${esc(eyebrow)}</span>
          <h2 id="picker-modal-title">${esc(title)}</h2>
          <p>${esc(ruleHint)}</p>
        </div>
        <button type="button" class="modal-close picker-close" data-action="close-picker-modal" aria-label="关闭选择弹窗">×</button>
      </header>
      <div class="picker-toolbar">
        <div class="facet-search-box picker-search-box">
          <span class="facet-search-icon">🔍</span>
          <input id="picker-modal-search" class="facet-search-input" type="search" placeholder="输入名称实时模糊搜索（支持中英文，如 JEI, Create, 冒险）..." value="${esc(picker.search)}" autocomplete="off" aria-label="弹窗内实时搜索">
          ${picker.search ? '<button type="button" class="facet-search-clear-btn" data-action="clear-picker-search" title="清空搜索词">✕</button>' : ''}
        </div>
        <div class="picker-toolbar-controls">
          <div class="picker-sort-group">
            <label class="picker-sort-label" for="picker-modal-sort">排序</label>
            <select id="picker-modal-sort" class="picker-sort-select" data-action="set-picker-sort" aria-label="选择排序方式">
              <option value="count_desc" ${sortMode === 'count_desc' ? 'selected' : ''}>收录最多（热度）</option>
              <option value="count_asc" ${sortMode === 'count_asc' ? 'selected' : ''}>收录最少（小众）</option>
              <option value="name_asc" ${sortMode === 'name_asc' ? 'selected' : ''}>名称 A → Z</option>
              <option value="name_desc" ${sortMode === 'name_desc' ? 'selected' : ''}>名称 Z → A</option>
            </select>
          </div>
          <div class="picker-toolbar-stats">
            <span>已选 <strong class="counter-num">${selectedValues.length}</strong> 项</span>
            <span class="stat-divider">·</span>
            <span>匹配 <strong class="counter-num">${formatCount(filtered.length)}</strong> 项</span>
          </div>
        </div>
      </div>
      <div class="picker-grid-wrap">
        <div class="picker-grid" id="picker-modal-grid" role="listbox" aria-label="候选列表">
          ${displayItems.length ? displayItems.map((item) => {
            const isActive = selectedValues.includes(item.value);
            const countStr = typeof item.count === 'number' && item.count > 0 ? `<b class="picker-count">${formatCount(item.count)}</b>` : '';
            const label = isCatOrGameplay ? getCategoryLabel(item.value) : item.value;
            const hasTranslation = isCatOrGameplay && label !== item.value;
            const nameHtml = hasTranslation
              ? `${esc(label)} <span class="picker-option-sub">(${esc(item.value)})</span>`
              : esc(item.value);
            const tooltip = hasTranslation ? `${esc(label)} (${esc(item.value)})` : esc(item.value);
            return `<button type="button" class="picker-option ${isActive ? 'is-active' : ''}" data-action="toggle-picker-item" data-value="${esc(item.value)}" role="option" aria-selected="${isActive}" title="${tooltip}">
              <span class="picker-option-name">${nameHtml}</span>
              ${countStr}
              ${isActive ? '<span class="picker-check-badge" aria-hidden="true">✓</span>' : ''}
            </button>`;
          }).join('') : '<div class="picker-empty-state">🔍 没有找到匹配项，请尝试其他关键词</div>'}
        </div>
        ${remaining > 0 ? `<div class="picker-more-bar">
          <div class="picker-more-actions">
            <button type="button" class="picker-load-more-btn" data-action="picker-load-more">📥 加载更多 300 项（剩余 ${formatCount(remaining)} 项）▾</button>
            <button type="button" class="picker-load-all-btn" data-action="picker-load-all" title="一次性展示当前匹配的全部 ${formatCount(filtered.length)} 项">⚡ 一次展示完（全部 ${formatCount(filtered.length)} 项）</button>
          </div>
        </div>` : (picker.limit > 300 && filtered.length > 300 ? `<div class="picker-more-bar">
          <div class="picker-more-actions">
            <button type="button" class="picker-collapse-btn" data-action="picker-reset-limit" title="收起列表至前 300 项">⤴ 收起为前 300 项</button>
          </div>
        </div>` : '')}
      </div>
      <footer class="picker-footer">
        <span class="picker-footer-summary">已选 ${selectedValues.length} 项 · 共匹配 ${formatCount(filtered.length)} 项${remaining > 0 ? `（已呈现前 ${formatCount(displayItems.length)} 项）` : '（已全部呈现）'}</span>
        <div class="picker-footer-actions">
          ${selectedValues.length ? '<button type="button" class="button picker-clear-btn" data-action="picker-clear-selected">清空已选</button>' : ''}
          <button type="button" class="button primary picker-done-btn" data-action="close-picker-modal">完成 / 应用筛选</button>
        </div>
      </footer>
    </section>
  </div>`;
}

export function renderDetailSourceDynamics(
  record: DesktopRecord,
  vm: ReturnType<typeof buildVersionModalViewModel>,
  biliGroups: BiliGroup[] = state.biliGroups,
): string {
  const releases = vm.releases?.length ? vm.releases : rawRecords(record, ['releases', 'versions_data', 'version_history']);
  const releaseHtml = releases.length
    ? `<div class="detail-section dynamics-section">
        <div class="dynamics-header">
          <h3>${record.platform === 'bilibili' ? '视频发布与版本动态' : record.platform === 'modrinth' ? '版本发布与变更记录' : record.platform === 'xyebbs' ? '原帖更新日志与版本' : record.platform === 'curseforge' ? 'CurseForge 全部发布文件与直链下载' : '更新日志与版本历史'} <span class="detail-submeta">共 ${releases.length} 条记录</span></h3>
        </div>
        <div class="release-list">${releases.map((release) => renderRelease(release as unknown as Record<string, unknown>)).join('')}</div>
      </div>`
    : '';

  const sourceUrl = safeExternalUrl(record.url);
  const emptyDynamicsBox = (title: string, desc: string, btnText: string) => {
    if (!sourceUrl) return '';
    return `<div class="empty-dyn-box">
      <div class="empty-dyn-title"><span>${esc(title)}</span></div>
      <p>${esc(desc)}</p>
      <button type="button" class="empty-dyn-btn" data-action="open-in-app-window" data-url="${esc(sourceUrl)}" data-title="${esc(record.title)}">${esc(btnText)}</button>
    </div>`;
  };

  // 1. MCMod (MC百科)
  if (record.platform === 'mcmod') {
    const hasPackVersion = Boolean(record.packVersion && record.packVersion.trim() && record.packVersion !== '未知' && !record.packVersion.includes('本地数据未提供'));
    const packVersionHtml = hasPackVersion ? renderPackVersionDetail(record) : '';
    const emptyBox = !releases.length && sourceUrl
      ? emptyDynamicsBox('📋 来源更新日志', '本地快照暂未收录更新日志，点击下方可在软件内小窗直接翻看原站', '🪟 软件内查看原站更新')
      : '';
    return releaseHtml ? `${packVersionHtml}${releaseHtml}` : `${packVersionHtml}${emptyBox}`;
  }

  // 2. CurseForge
  if (record.platform === 'curseforge') {
    const live = previewVersionCache.get(record.id);
    let liveActionHtml = '';
    if (live?.loading) {
      liveActionHtml = '<div class="notice" role="status" style="margin-bottom:10px;">⚡ 正在通过 API 查询完整历史文件与直链下载…</div>';
    } else if (live?.error) {
      liveActionHtml = `<div class="notice error" style="margin-bottom:10px;">在线查询失败：${esc(live.error)} <button type="button" class="button secondary small" data-action="fetch-live-versions" data-record-id="${esc(record.id)}" style="margin-left:8px;">重试查询</button></div>`;
    } else if (live?.versions?.length) {
      liveActionHtml = `<div class="notice" style="color:var(--accent-green);font-size:12px;margin-bottom:10px;">⚡ 已通过 API 载入全部 ${live.versions.length} 个历史文件与直链下载 <button type="button" class="button secondary small" data-action="fetch-live-versions" data-record-id="${esc(record.id)}" style="margin-left:8px;">刷新</button></div>`;
    } else {
      liveActionHtml = `<div style="margin-bottom:10px;"><button type="button" class="button secondary small" data-action="fetch-live-versions" data-record-id="${esc(record.id)}">⚡ 在线查询全部历史版本与直链下载</button></div>`;
    }

    const hasFileIndexes = Array.isArray(record.fileIndexes) && record.fileIndexes.length > 0;
    const fileIndexHtml = (!live?.versions?.length && hasFileIndexes) ? renderCurseforgeFileIndexDetail(record) : '';
    const emptyBox = (!releases.length && !hasFileIndexes && sourceUrl)
      ? emptyDynamicsBox('📦 来源文件与版本', '本地快照暂未收录文件索引与更新记录，点击下方可在软件内小窗直接翻看原站', '🪟 软件内查看原站文件')
      : '';
    return `${liveActionHtml}${(fileIndexHtml || releaseHtml) ? `${fileIndexHtml}${releaseHtml}` : emptyBox}`;
  }

  // 3. Modrinth
  if (record.platform === 'modrinth') {
    return releaseHtml || (!releases.length && sourceUrl
      ? emptyDynamicsBox('🧩 Modrinth 版本发布', '本地快照暂未收录版本发布记录，点击下方可在软件内小窗直接翻看原站', '🪟 软件内查看原站版本')
      : '');
  }

  // 4. Bilibili
  if (record.platform === 'bilibili') {
    const raw = (record.raw || {}) as Record<string, unknown>;
    const matchingGroup = biliGroups.find((g) => g.items.some((item) => String(item.bvid) === String(record.sourceId) || String(item.id) === String(record.sourceId)));
    const relatedItems = matchingGroup ? matchingGroup.items : [];
    let groupHtml = '';
    if (relatedItems.length > 1) {
      groupHtml = `<div class="detail-section dynamics-section">
        <div class="dynamics-header">
          <h3>关联视频与版本动态</h3>
          <span class="detail-submeta">同系列共 ${relatedItems.length} 期视频</span>
        </div>
        <div class="bili-related-videos-list">
          ${relatedItems.map((item) => {
            const isCurrent = String(item.bvid) === String(record.sourceId);
            const itemUrl = item.bvid ? `https://www.bilibili.com/video/${item.bvid}` : (item.url || '');
            const itemDate = item.pub_time || (item as any).date || '';
            const itemViews = item.views ? formatMetric(item.views) : '';
            return `<div class="bili-related-video-item ${isCurrent ? 'is-current' : ''}">
              <div class="bili-related-video-info">
                <strong>${isCurrent ? '<span class="current-indicator">▶ 当前</span> ' : ''}${esc(item.title)}</strong>
                <span class="detail-submeta">${itemDate ? `发布：${esc(itemDate)}` : ''}${itemViews ? ` · 播放：${itemViews}` : ''}</span>
              </div>
              <div class="bili-related-video-actions">
                ${itemUrl ? `<button type="button" class="button secondary small" data-action="open-in-app-window" data-record-id="${esc(record.id)}" data-url="${esc(itemUrl)}" data-title="${esc(item.title)} 视频页面">${isStaticSite() ? '打开原站 ↗' : '🪟 小窗浏览'}</button>` : ''}
              </div>
            </div>`;
          }).join('')}
        </div>
      </div>`;
    }

    const descUpdated = raw.desc_updated_at ? `<div class="bili-dyn-notice">🔄 <strong>简介更新时间：</strong>${esc(String(raw.desc_updated_at))}</div>` : '';
    const groupVer = raw.has_group_version ? `<div class="bili-dyn-notice bili-group-notice">👥 <strong>群内版本提示：</strong>${esc(String(raw.group_version_note || 'UP主提示最新版本在交流群内发布'))}</div>` : '';

    if (groupHtml) {
      return `${descUpdated}${groupVer}${groupHtml}`;
    }
    if (descUpdated || groupVer) {
      return `${descUpdated}${groupVer}`;
    }

    return '';
  }

  // 5. BBSMC
  if (record.platform === 'bbsmc') {
    return releaseHtml || (!releases.length && sourceUrl
      ? emptyDynamicsBox('📜 BBSMC 原帖动态', '本地快照暂未收录更新记录，点击下方可在软件内小窗直接翻看原帖', '🪟 软件内查看原帖动态')
      : '');
  }

  // 6. XYEBBS
  if (record.platform === 'xyebbs') {
    const live = previewVersionCache.get(record.id);
    let liveActionHtml = '';
    if (live?.loading) {
      liveActionHtml = '<div class="notice" role="status" style="margin-bottom:10px;">⚡ 正在通过 API 查询最新版本发布与网盘直链…</div>';
    } else if (live?.error) {
      liveActionHtml = `<div class="notice error" style="margin-bottom:10px;">在线查询失败：${esc(live.error)} <button type="button" class="button secondary small" data-action="fetch-live-versions" data-record-id="${esc(record.id)}" style="margin-left:8px;">重试查询</button></div>`;
    } else if (live?.versions?.length) {
      liveActionHtml = `<div class="notice" style="color:var(--accent-green);font-size:12px;margin-bottom:10px;">⚡ 已通过官方 API 载入全部 ${live.versions.length} 个版本与网盘直链 <button type="button" class="button secondary small" data-action="fetch-live-versions" data-record-id="${esc(record.id)}" style="margin-left:8px;">刷新</button></div>`;
    } else {
      liveActionHtml = `<div style="margin-bottom:10px;"><button type="button" class="button secondary small" data-action="fetch-live-versions" data-record-id="${esc(record.id)}">⚡ 在线查询最新版本与网盘直链</button></div>`;
    }
    const emptyBox = (!releases.length && sourceUrl)
      ? emptyDynamicsBox('📌 星域论坛 原帖动态', '本地快照暂未收录更新日志，点击下方可在软件内小窗直接翻看原帖', '🪟 软件内查看原帖更新')
      : '';
    return `${liveActionHtml}${(releaseHtml || emptyBox)}`;
  }

  return releaseHtml;
}

function detailPanel(): string {
  const record = state.selected;
  if (!record) return '';
  const liveVersions = previewVersionCache.get(record.id)?.versions;
  const activeRecord = liveVersions?.length
    ? { ...record, releases: liveVersions, raw: { ...record.raw, releases: liveVersions, files: liveVersions, versions: liveVersions, versions_data: liveVersions } }
    : record;
  const vm = buildVersionModalViewModel(activeRecord.platform, activeRecord.raw as never, activeRecord.raw);
  const modNames = rawList(activeRecord, ['includedModNames', 'included_mod_names']);
  const modsByName = new Map<string, Record<string, unknown>>();
  for (const mod of rawRecords(activeRecord, ['includedMods', 'included_mods', 'previewMods', 'mods'])) {
    const name = String(mod.title || mod.name || '').trim();
    if (name && !modsByName.has(name)) modsByName.set(name, mod);
  }
  for (const name of modNames) if (!modsByName.has(name)) modsByName.set(name, { name });
  const mods = [...modsByName.values()];
  const sourceUrl = safeExternalUrl(activeRecord.url);
  const modHtml = mods.length
    ? `<div class="detail-section"><h3>已收录模组</h3><details class="detail-expand"><summary>已收录模组（共 ${mods.length} 款，点击展开）▾</summary><div class="mod-list">${mods.map((mod) => {
        const url = safeExternalUrl(mod.url);
        return url
          ? `<a class="mod-chip" href="${esc(url)}" target="_blank" rel="noreferrer">${esc(String(mod.title || mod.name || '未知模组'))} ↗</a>`
          : `<span class="mod-chip">${esc(String(mod.title || mod.name || '未知模组'))}</span>`;
      }).join('')}</div></details></div>`
    : '';

  const hasAuthor = Boolean(activeRecord.author && activeRecord.author.trim() !== '' && activeRecord.author.trim() !== '未知' && !activeRecord.author.includes('未知'));
  const authorHtml = hasAuthor ? `<p class="detail-author">作者：${esc(activeRecord.author)}</p>` : '';
  const categories = Array.isArray(activeRecord.categories) ? activeRecord.categories.filter((c) => c && c.trim() && c !== '全部') : [];
  const mcVer = (vm.mcVersionsList.length ? vm.mcVersionsList.join('、') : activeRecord.versions.join('、')).trim();
  const loaders = activeRecord.loaders.filter((l) => l && l !== '未知' && !l.includes('本地数据未提供')).join('、');

  const metaChips: string[] = [];
  if (mcVer && mcVer !== '未知' && !mcVer.includes('本地数据未提供')) metaChips.push(`MC ${mcVer}`);
  if (loaders) metaChips.push(loaders);
  metaChips.push(...categories);
  const tagsHtml = metaChips.length ? `<div class="detail-tags-row">${metaChips.map((c) => `<span class="detail-tag-chip">${esc(c)}</span>`).join('')}</div>` : '';

  const evidenceHtml = activeRecord.evidence?.length
    ? `<details class="detail-evidence-collapsible"><summary>来源原始核验记录（共 ${activeRecord.evidence.length} 项，点击展开）▾</summary><div class="evidence-list">${activeRecord.evidence.map((item) => `<div class="evidence-item"><span>${esc(item.label)}</span><strong>${textOrUnknown(item.value)}</strong></div>`).join('')}</div></details>`
    : '';

  const sourceDynamicsHtml = renderDetailSourceDynamics(activeRecord, vm, state.biliGroups);

  return `<div class="detail-backdrop" data-action="close-detail"><aside class="detail-panel" data-detail-panel onclick="event.stopPropagation()">
    <button type="button" class="modal-close close-detail" data-action="close-detail" aria-label="关闭详情">×</button>
    <header class="detail-header-block">
      <span class="eyebrow">${esc(PLATFORM_CONFIGS[record.platform].name)} · 原始来源</span>
      <h2>${esc(record.title)}</h2>
      ${authorHtml}
      ${tagsHtml}
      ${renderMediaSection(record)}
      ${renderDetailFacts(record)}
    </header>
    <div class="detail-columns-layout">
      <div class="detail-col-source">
        <details class="detail-source-fold"><summary>版本与来源动态</summary>${sourceDynamicsHtml}</details>
        ${renderDetailDownloadLinks(record)}
        ${renderCommentSection(record)}
        ${modHtml}
        ${evidenceHtml}
      </div>
      <div class="detail-col-personal">
        ${renderMcmodTrendDetail(record)}
        ${renderPersonalDetail(record)}
        <div class="detail-actions">${sourceUrl ? `<button class="button primary wide" data-action="open-in-app-window" data-record-id="${esc(record.id)}" data-url="${esc(sourceUrl)}" data-title="${esc(record.title)} 原站页面">${isStaticSite() ? '打开原站 ↗' : '🪟 软件内小窗浏览'}</button><button class="button secondary wide" data-action="open-source" data-url="${esc(sourceUrl)}">外部浏览器打开 ↗</button>` : '<div class="unknown-action">原站链接未知</div>'}</div>
      </div>
    </div>
  </aside></div>`;
}

function imagePreviewPanel(): string {
  const preview = state.imagePreview;
  if (!preview) return '';
  return `<div class="modal-backdrop image-lightbox" data-action="close-image" role="dialog" aria-modal="true" aria-label="图片预览"><div class="modal-panel image-lightbox-panel" onclick="event.stopPropagation()"><button type="button" class="modal-close image-lightbox-close" data-action="close-image" aria-label="关闭图片预览">×</button><img src="${esc(preview.url)}" alt="${esc(preview.title)}" referrerpolicy="no-referrer"><div class="image-lightbox-title">${esc(preview.title)}</div><a class="button secondary" href="${esc(preview.url)}" target="_blank" rel="noreferrer">在新标签页打开原图 ↗</a></div></div>`;
}

function safeHost(url: string): string {
  try {
    return new URL(url).hostname;
  } catch {
    return '';
  }
}

function renderCommentPreviewModal(): string {
  const record = state.commentPreviewRecord;
  if (!record) return '';
  const commentState = state.comments.sourceId === record.sourceId ? state.comments : null;
  const isLoading = commentState?.loading;
  const error = commentState?.error;
  const comments = commentState?.comments || [];
  const query = state.commentPreviewQuery.trim().toLowerCase();
  const filtered = query
    ? comments.filter((c) => {
        const author = String(c.author ?? c.user ?? c.name ?? '').toLowerCase();
        const text = String(commentBody(c)).toLowerCase();
        return author.includes(query) || text.includes(query);
      })
    : comments;

  const raw = (record.raw || {}) as Record<string, unknown>;
  const metaCount = Number(raw.commentsCount ?? raw.reply ?? raw.comments ?? 0);
  const countBadge = commentState?.pageCount
    ? `共 ${commentState.pageCount} 条评论`
    : comments.length
      ? `共 ${comments.length} 条评论`
      : metaCount > 0
        ? `原站约 ${metaCount} 条评论`
        : '评论详情';

  const sourceUrl = getPlatformCommentWebUrl(record) || safeExternalUrl(record.url);

  let bodyHtml = '';
  if (isLoading) {
    bodyHtml = '<div class="loading-state"><span class="pulse-indicator"></span>正在读取评论数据…</div>';
  } else if (error) {
    bodyHtml = `<div class="error-box">${esc(error)}</div>`;
  } else if (!comments.length) {
    bodyHtml = `<div class="empty-evidence comment-empty-state">
      <div class="comment-empty-icon">💬</div>
      <div class="comment-empty-title">暂无本地存档评论</div>
      <p class="comment-empty-desc">
        ${record.platform === 'mcmod'
          ? '当前快照未收录此整合包的独立评论数据文件。'
          : `当前本地快照未归档「${esc(PLATFORM_CONFIGS[record.platform]?.name || record.platform)}」的独立评论文本。`}
      </p>
      <div class="comment-empty-actions">
        ${sourceUrl ? `<a class="button" href="${esc(sourceUrl)}" target="_blank" rel="noreferrer">外部浏览器打开 ↗</a>` : ''}
      </div>
    </div>`;
  } else if (!filtered.length) {
    bodyHtml = `<div class="empty-evidence">没有找到匹配关键词 “${esc(query)}” 的评论。</div>`;
  } else {
    bodyHtml = renderComments(filtered);
  }

  const toolbarHtml = `<div class="comment-preview-toolbar">
        <input type="search" class="comment-preview-search js-comment-preview-search" placeholder="在当前整合包评论中实时搜索…" value="${esc(state.commentPreviewQuery)}" autocomplete="off">
        ${sourceUrl ? `<a class="button secondary comment-open-source-btn" href="${esc(sourceUrl)}" target="_blank" rel="noreferrer">外部打开 ↗</a>` : ''}
      </div>`;

  return `<div class="modal-backdrop comment-preview-backdrop" data-action="close-comment-preview" role="dialog" aria-modal="true" aria-label="评论预览">
    <section class="modal-panel comment-preview-panel" onclick="event.stopPropagation()">
      <header class="modal-header comment-preview-header">
        <div class="modal-title-wrap">
          <span class="eyebrow">${esc(PLATFORM_CONFIGS[record.platform].name)} · 评论预览</span>
          <h2>${esc(record.title)} <span class="comment-preview-badge">${esc(countBadge)}</span></h2>
        </div>
        <button type="button" class="modal-close" data-action="close-comment-preview" aria-label="关闭评论预览">×</button>
      </header>
      ${toolbarHtml}
      <div class="comment-preview-body">
        ${bodyHtml}
      </div>
      <footer class="modal-footer comment-preview-footer">
        <span class="js-comment-count-text">${isLoading ? '正在获取评论…' : query ? `筛选出 ${filtered.length} / ${comments.length} 条评论` : comments.length ? `已展示全部 ${comments.length} 条本地评论` : '本地暂无存档评论'}</span>
        <button type="button" class="button secondary" data-action="close-comment-preview">关闭</button>
      </footer>
    </section>
  </div>`;
}

function renderInAppSourceTools(record: DesktopRecord): string {
  return `<section class="in-app-source-tools"><h3>来源资料</h3>
    ${renderDetailDownloadLinks(record)}
    <details><summary>简介与分类</summary><p>${esc(record.summary || '当前快照未收录简介')}</p><p>${(record.categories || []).map((value) => esc(value)).join(' · ')}</p></details>
    ${record.platform === 'mcmod' ? `<a class="detail-link" href="https://www.mcmod.cn/modpack/version/${encodeURIComponent(record.sourceId)}.html" target="_blank" rel="noreferrer">原站版本历史 ↗</a>` : ''}
  </section>`;
}

export function renderInAppChangelogView(record: DesktopRecord): string {
  const liveVersions = previewVersionCache.get(record.id)?.versions;
  if (liveVersions?.length) record = { ...record, releases: liveVersions, raw: { ...record.raw, releases: liveVersions, files: liveVersions, versions: liveVersions, versions_data: liveVersions } };
  const vm = buildVersionModalViewModel(record.platform, record.raw as never, record.raw);
  const releases = vm.releases?.length ? vm.releases : (record.releases?.length ? record.releases : rawRecords(record, ['releases', 'versions_data', 'version_history']));
  const fileIndexes = record.fileIndexes || [];
  const visibleLimit = inAppVersionLimits.get(record.id) || 30;
  const rawPackVersion = (record.packVersion && record.packVersion.trim() && record.packVersion !== '未知' && !record.packVersion.includes('本地数据未提供'))
    ? record.packVersion.trim()
    : (record.platform === 'mcmod' && vm.latestVersion && vm.latestVersion.trim() && vm.latestVersion !== '未知' && vm.latestVersion !== '最新版本' && !vm.latestVersion.includes('本地数据未提供') ? vm.latestVersion.trim() : '');
  const packVersion = rawPackVersion && rawPackVersion !== '最新版本' ? rawPackVersion : '';

  const matchingGroup = record.platform === 'bilibili' ? state.biliGroups.find((g) => g.items.some((item) => String(item.bvid) === String(record.sourceId) || String(item.id) === String(record.sourceId))) : null;
  const relatedVideos = matchingGroup ? matchingGroup.items : [];
  const hasReleaseNotes = releases.some((release) => {
    const item = release as Record<string, unknown>;
    const note = String(item.changelogMd || item.changelog || item.changelogHtml || '').trim();
    return Boolean(note && note !== '该版本未提供更新日志说明。');
  });

  const hasData = releases.length > 0 || fileIndexes.length > 0 || Boolean(packVersion) || relatedVideos.length > 1;

  if (!hasData) {
    return `<div class="in-app-changelog-empty-compact">
      <span class="empty-dyn-icon">📋</span>
      <h4>当前本地快照暂无收录结构化更新日志</h4>
      <p>【更新日志状态】：<strong>没有</strong>（快照暂未收录该整合包历史版本与日志）</p>
      <small style="color:var(--text-muted);font-size:12px;margin-top:6px;display:block;">当前快照未收录结构化版本；可在中间网页核对原站，或切到“来源资料”查看其他内容。</small>
      ${record.platform === 'mcmod' ? `<button type="button" class="button secondary small" data-action="switch-in-app-url" data-url="https://www.mcmod.cn/modpack/version/${encodeURIComponent(record.sourceId)}.html" data-title="${esc(record.title)} 更新日志" style="margin-top:10px;">🌐 在中间网页查看原站版本</button>` : record.platform === 'curseforge' ? `<button type="button" class="button primary small" data-action="fetch-live-versions" data-record-id="${esc(record.id)}" style="margin-top:10px;">⚡ 在线查询原站全部文件与直链</button>` : `<button type="button" class="button secondary small" data-action="set-in-app-window-tab" data-tab="web" style="margin-top:10px;">🌐 浏览原站网页</button>`}
      ${record.platform === 'xyebbs' ? `<button type="button" class="button primary small" data-action="fetch-live-versions" data-record-id="${esc(record.id)}" style="margin-top:6px;">⚡ 在线查询原站最新版本与下载</button>` : ''}
    </div>`;
  }

  let contentHtml = '';

  if (packVersion) {
    contentHtml += `<div class="in-app-log-banner">
      <span class="in-app-log-badge">当前版本摘要</span>
      <strong>${esc(packVersion)}</strong>
    </div>`;
  }

  if (!releases.length) {
    const cfPrompt = (['curseforge', 'xyebbs'].includes(record.platform) && !liveVersions?.length)
      ? ` <button type="button" class="button secondary small" data-action="fetch-live-versions" data-record-id="${esc(record.id)}">⚡ 在线查询全部历史版本与直链下载</button>`
      : '';
    contentHtml += `<p class="in-app-version-limited">当前快照仅有版本摘要，尚无可逐条展示的历史版本与更新正文。${record.platform === 'mcmod' ? `<button type="button" class="button secondary small" data-action="switch-in-app-url" data-url="https://www.mcmod.cn/modpack/version/${encodeURIComponent(record.sourceId)}.html" data-title="${esc(record.title)} 更新日志">在中间网页查看原站历史 ↗</button>` : ''}${cfPrompt}</p>`;
  }

  if (fileIndexes.length > 0 && !liveVersions?.length) {
    contentHtml += `<div class="in-app-log-section">
      <div class="in-app-log-head">
        <h4>CurseForge 文件索引快照</h4>
        <span class="in-app-log-count">共 ${fileIndexes.length} 个文件</span>
      </div>
      <div style="margin: 6px 0 10px 0;"><button type="button" class="button secondary small" data-action="fetch-live-versions" data-record-id="${esc(record.id)}">⚡ 在线查询全部历史版本与直链下载</button></div>
      <div class="in-app-files-table-wrap">
        <table class="in-app-files-table">
          <thead><tr><th>文件名</th><th>游戏版本</th><th>Loader</th><th>类型</th></tr></thead>
          <tbody>
            ${fileIndexes.slice(0, visibleLimit).map((file) => `<tr>
              <td class="file-name-cell" title="${esc(file.filename)}">${file.fileId && /^\d+$/.test(String(file.fileId)) && safeExternalUrl(record.url) ? `<a href="${esc(`${record.url.replace(/\/$/, '')}/files/${file.fileId}`)}" target="_blank" rel="noreferrer">📄 ${esc(file.filename)} ↗</a>` : `📄 ${esc(file.filename)}`}</td>
              <td>${esc(file.gameVersion || '—')}</td>
              <td>${esc(String(file.modLoader || '—'))}</td>
              <td><span class="release-type-badge">${esc(String(file.releaseType === 1 ? 'Release' : file.releaseType === 2 ? 'Beta' : file.releaseType === 3 ? 'Alpha' : file.releaseType || '—'))}</span></td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
      ${fileIndexes.length > visibleLimit ? `<button type="button" class="button secondary small" data-action="more-in-app-versions" data-record-id="${esc(record.id)}">再看 30 个文件（已显示 ${visibleLimit} / ${fileIndexes.length}）</button>` : ''}
    </div>`;
  }

  if (releases.length > 0) {
    const live = previewVersionCache.get(record.id);
    const releaseHeading = record.platform === 'bilibili'
      ? '视频发布记录'
      : record.platform === 'modrinth'
        ? (hasReleaseNotes ? 'Modrinth 版本与更新说明' : 'Modrinth 版本记录')
        : record.platform === 'xyebbs'
          ? (hasReleaseNotes ? '原帖版本与更新说明' : '原帖版本记录')
          : record.platform === 'curseforge'
            ? 'CurseForge 全部发布文件与直链下载'
            : hasReleaseNotes ? '版本与更新说明' : '版本历史记录';
    const liveBanner = (record.platform === 'xyebbs' && live?.versions?.length)
      ? `<div style="margin: 4px 0 10px 0;"><span class="notice" style="color:var(--accent-green);font-size:12px;">⚡ 已通过官方 API 载入最新发布版本与网盘直链</span></div>`
      : '';
    contentHtml += `<div class="in-app-log-section">
      <div class="in-app-log-head">
        <h4>${releaseHeading}</h4>
        <span class="in-app-log-count">共 ${releases.length} 条</span>
      </div>
      ${liveBanner}
      <div class="in-app-release-list">
        ${releases.slice(0, visibleLimit).map((rel) => renderRelease(rel as unknown as Record<string, unknown>)).join('')}
      </div>
      ${releases.length > visibleLimit ? `<button type="button" class="button secondary small" data-action="more-in-app-versions" data-record-id="${esc(record.id)}">再看 30 个版本（已显示 ${visibleLimit} / ${releases.length}）</button>` : ''}
    </div>`;
  }

  if (relatedVideos.length > 1) {
    contentHtml += `<div class="in-app-log-section">
      <div class="in-app-log-head">
        <h4>同系列关联视频</h4>
        <span class="in-app-log-count">共 ${relatedVideos.length} 期</span>
      </div>
      <div class="in-app-video-series-list">
        ${relatedVideos.map((item) => {
          const isCurrent = String(item.bvid) === String(record.sourceId);
          const itemUrl = item.bvid ? `https://www.bilibili.com/video/${item.bvid}` : (item.url || '');
          const itemDate = item.pub_time || (item as any).date || '';
          return `<div class="in-app-video-item ${isCurrent ? 'is-current' : ''}">
            <div class="in-app-video-meta">
              <strong>${isCurrent ? '▶ [当前播放] ' : ''}${esc(item.title)}</strong>
              <span>${itemDate ? `发布：${esc(itemDate)}` : ''}</span>
            </div>
            ${itemUrl ? `<button type="button" class="button secondary small in-app-video-switch" data-action="switch-in-app-url" data-url="${esc(itemUrl)}" data-title="${esc(item.title)} 视频页面">在中间网页打开</button>` : ''}
          </div>`;
        }).join('')}
      </div>
    </div>`;
  }

  return `<div class="in-app-changelog-wrap">${contentHtml}</div>`;
}

export function renderInAppSideContent(record: DesktopRecord): string {
  const versions = record.versions?.filter(Boolean) || [];
  const loaders = record.loaders?.filter(Boolean) || [];
  return `<div class="in-app-side-header">
    <div class="in-app-side-plat-row">
      <div class="in-app-side-plat">
        <span class="in-app-side-badge" style="--plat-accent:${PLATFORM_ACCENTS[record.platform]};">${platformIcon(record.platform)} ${esc(PLATFORM_CONFIGS[record.platform].name)}</span>
      </div>
      <button type="button" class="in-app-pane-close-btn" data-action="toggle-in-app-personal" title="收起右侧个人区面板" aria-label="收起右侧个人区面板">▸</button>
    </div>
    <h3 class="in-app-side-title" title="${esc(record.title)}">${esc(record.title)}</h3>
    ${record.author ? `<div class="in-app-side-author">作者：${esc(record.author)}</div>` : ''}
    ${(versions.length || loaders.length) ? `
    <div class="in-app-side-tags">
      ${versions.slice(0, 3).map((v) => `<span class="in-app-side-tag tag-ver">${esc(v)}</span>`).join('')}
      ${loaders.slice(0, 2).map((l) => `<span class="in-app-side-tag tag-ldr">${esc(l)}</span>`).join('')}
    </div>` : ''}
  </div>
  <div class="in-app-side-scroll">
    <div class="in-app-side-content">
      ${renderPersonalDetail(record)}
      ${record.platform === 'mcmod' ? renderMcmodTrendDetail(record) : ''}
    </div>
  </div>`;
}

function inAppWindowId(win: InAppWindowState): string {
  if (!win.id) win.id = `web-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
  return win.id;
}

function recordForInAppWindow(win: InAppWindowState): DesktopRecord | null {
  return win.record || (win.recordId ? state.records.find((record) => record.id === win.recordId) : null)
    || state.records.find((record) => record.url === win.url || (record.sourceId && win.url.includes(record.sourceId)))
    || null;
}

function inAppFrameConfig(win: InAppWindowState, record: DesktopRecord | null): { restricted: boolean; frameUrl: string; sandbox: string; proxy: boolean; note: string } {
  // Route by the actual destination: a window can outlive the current
  // platform's record list or navigate to a different associated video.
  const host = safeHost(win.url).toLowerCase();
  const isHost = (domain: string) => host === domain || host.endsWith(`.${domain}`);
  const platform = isHost('bilibili.com') ? 'bilibili'
    : isHost('xyebbs.com') ? 'xyebbs'
    : isHost('curseforge.com') ? 'curseforge' : record?.platform;
  if (typeof window !== 'undefined' && !window.desktopApi?.openInAppWindow && platform === 'mcmod' && isHost('mcmod.cn') && /^\/modpack\/\d+\.html$/.test(new URL(win.url).pathname)) return {
    restricted: false,
    frameUrl: `/api/proxy-page?url=${encodeURIComponent(win.url)}`,
    sandbox: 'allow-scripts allow-popups allow-popups-to-escape-sandbox',
    proxy: true,
    note: 'MC百科原站只读预览；左侧模组清单可定位到页面对应条目。',
  };
  const browserEntry = typeof window !== 'undefined' && !window.desktopApi?.openInAppWindow;
  if (!browserEntry) return {
    restricted: false,
    frameUrl: win.url,
    sandbox: 'allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox allow-downloads allow-modals allow-top-navigation-by-user-activation allow-storage-access-by-user-activation',
    proxy: false,
    note: '原站可能限制内嵌或第三方登录。页面空白时可用“浏览器打开”。',
  };
  if (platform === 'curseforge') return {
    restricted: true,
    frameUrl: '',
    sandbox: '',
    proxy: false,
    note: 'CurseForge 当前要求 Cloudflare 浏览器验证，软件内只读代理不能完成该验证。',
  };
  if (platform === 'bilibili') {
    const bvid = win.url.match(/\/video\/(BV[0-9A-Za-z]+)/i)?.[1]
      || (/^BV[0-9A-Za-z]+$/.test(record?.sourceId || '') ? record!.sourceId : '');
    if (bvid) return {
      restricted: false,
      frameUrl: `https://player.bilibili.com/player.html?bvid=${encodeURIComponent(bvid)}&page=1&autoplay=0&danmaku=0`,
      sandbox: 'allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox allow-presentation',
      proxy: false,
      note: '⚠ B站站内打开存在已知问题，可能一直空白或等待加载。建议使用右上角“浏览器打开”。',
    };
  }

  if (platform === 'xyebbs') return {
    restricted: false,
    frameUrl: `/api/proxy-page?static=1&url=${encodeURIComponent(win.url)}`,
    sandbox: 'allow-scripts allow-popups allow-popups-to-escape-sandbox',
    proxy: true,
    note: 'XYEBBS 使用隔离只读预览，已停用会在本地域名报错的原站应用脚本。',
  };
  return {
    restricted: false,
    frameUrl: `/api/proxy-page?url=${encodeURIComponent(win.url)}`,
    sandbox: 'allow-scripts allow-popups allow-popups-to-escape-sandbox',
    proxy: true,
    note: '浏览器入口使用隔离只读预览；登录、提交或下载请用“浏览器打开”。',
  };
}

const previewVersionCache = new Map<string, { versions?: Record<string, unknown>[]; error?: string; loading?: boolean }>();
const inAppVersionLimits = new Map<string, number>();

async function loadPreviewVersions(record: DesktopRecord): Promise<void> {
  if (!['mcmod', 'bbsmc', 'modrinth', 'curseforge', 'xyebbs'].includes(record.platform) || !window.desktopApi?.getPreviewVersions || previewVersionCache.has(record.id)) return;
  const entry: { versions?: Record<string, unknown>[]; error?: string; loading?: boolean } = { loading: true };
  previewVersionCache.set(record.id, entry);
  try { entry.versions = (await window.desktopApi.getPreviewVersions(record.platform, record.sourceId)).versions; }
  catch (error) { entry.error = error instanceof Error ? error.message : String(error); }
  finally { entry.loading = false; render(); }
}

function renderInAppWebPane(win: InAppWindowState, record: DesktopRecord | null): string {
  const tab = win.contentTab || 'web';
  const tabs = record ? `<nav class="in-app-content-tabs" aria-label="小窗内容">${([['overview', '资料'], ['versions', '版本历史'], ['gallery', '图片'], ['web', record.platform === 'bilibili' ? '尝试播放' : '原站网页']] as const).map(([key, label]) => `<button class="button ${tab === key ? 'primary' : 'secondary'} small" data-action="in-app-content-tab" data-tab="${key}">${label}</button>`).join('')}</nav>` : '';
  let body = '';
  if (!record || tab === 'web') body = renderInAppRemotePane(win, record);
  else if (tab === 'versions') {
    const live = previewVersionCache.get(record.id);
    body = `<div class="in-app-reader">${live?.loading ? '<p role="status">正在查询原站版本，本地记录仍可查看…</p>' : ''}${live?.error ? `<p>在线版本暂不可用：${esc(live.error)}。以下保留本地记录。</p><button class="button secondary small" data-action="retry-preview-versions">重试查询</button>` : ''}${renderInAppChangelogView(record)}</div>`;
  } else if (tab === 'gallery') body = `<div class="in-app-reader">${renderMediaSection(record) || '<p>当前快照没有收录图片。</p>'}</div>`;
  else {
    const raw = record.raw as Record<string, unknown>;
    const description = String(raw.description || raw.desc || record.summary || '当前快照没有收录简介。');
    body = `<div class="in-app-reader"><h2>${esc(record.title)}</h2><p>${esc(PLATFORM_CONFIGS[record.platform].name)} · ${esc(record.author || '作者未收录')}</p>${record.platform === 'bilibili' ? '<p class="in-app-version-limited">B站内嵌播放器存在兼容问题；可以尝试播放，空白时请用右上角“浏览器打开”。</p>' : ''}${renderDetailFacts(record)}<h3>简介</h3><div class="in-app-reader-description">${esc(description)}</div>${renderDetailDownloadLinks(record)}${raw.pinned_comment ? `<h3>置顶评论</h3><div class="in-app-reader-description">${esc(String(raw.pinned_comment))}</div>` : ''}</div>`;
  }
  return `<section class="in-app-content-shell">${tabs}${body}</section>`;
}

function renderInAppRemotePane(win: InAppWindowState, record: DesktopRecord | null): string {
  const config = inAppFrameConfig(win, record);
  if (config.restricted) return `<div class="in-app-web-pane in-app-restricted-pane"><div class="in-app-restricted-state"><span class="in-app-restricted-icon">🛡️</span><h3>CurseForge 需要浏览器验证</h3><p>当前请求收到 Cloudflare 403 challenge。应用不会把验证页或空白页当作加载成功。</p><a class="button primary" href="${esc(win.url)}" target="_blank" rel="noreferrer">在浏览器中打开 ↗</a></div></div>`;
  const id = inAppWindowId(win);
  return `<div class="in-app-web-pane">
    <div class="in-app-web-toolbar"><span class="js-in-app-loader" role="status">正在请求原站…</span><label>网页缩放 <select class="js-in-app-zoom" aria-label="网页缩放"><option value="auto">自动（保持可读）</option><option value="1">100%</option><option value="0.9">90%</option><option value="0.75">75%</option><option value="0.5">50%</option></select></label></div>
    <div class="in-app-web-viewport"><iframe class="in-app-window-frame js-in-app-frame" data-frame-key="${esc(`${id}:${config.frameUrl}`)}" src="${esc(config.frameUrl)}" sandbox="${config.sandbox}" allow="${config.proxy ? 'fullscreen' : 'fullscreen; clipboard-read; clipboard-write'}" title="${esc(win.title)}原站网页"></iframe></div>
  </div>`;
}

function renderInAppWindowDock(windows: InAppWindowState[]): string {
  const minimized = windows.filter((win) => win.minimized);
  if (!minimized.length) return '';
  return `<aside class="in-app-window-dock" aria-label="已收起的小窗">${minimized.map((win) => `<button type="button" class="in-app-dock-item" data-action="restore-in-app-window" data-window-id="${esc(inAppWindowId(win))}" title="展开 ${esc(win.title)}"><span>🪟</span><span>${esc(win.title)}</span></button>`).join('')}</aside>`;
}

function renderInAppSplitWorkspace(windows: InAppWindowState[], dock: string): string {
  return `<div class="modal-backdrop in-app-window-backdrop in-app-workspace-backdrop" data-action="minimize-all-in-app-windows" role="dialog" aria-modal="true" aria-label="多窗口分屏浏览">
    <section class="in-app-workspace-panel" onclick="event.stopPropagation()">
      <header class="in-app-workspace-header"><div><strong>分屏浏览</strong><span>${windows.length} 个页面 · 分屏时隐藏资料侧栏以保证可读性</span></div><button type="button" class="button secondary" data-action="minimize-all-in-app-windows">全部收起</button></header>
      <div class="in-app-workspace-grid ${windows.length >= 3 ? 'is-many' : ''}">${windows.map((win) => {
        const id = inAppWindowId(win);
        const record = recordForInAppWindow(win);
        return `<article class="in-app-split-window" data-window-id="${esc(id)}">
          <header class="in-app-split-header"><div><strong title="${esc(win.title)}">${esc(win.title)}</strong><span>${esc(safeHost(win.url))}</span></div><div><button type="button" data-action="reload-in-app-window" title="刷新">↻</button><button type="button" data-action="minimize-in-app-window" title="收起到右侧">—</button><a href="${esc(win.url)}" target="_blank" rel="noreferrer" title="浏览器打开">↗</a><button type="button" data-action="close-in-app-window" title="关闭">×</button></div></header>
          ${renderInAppWebPane(win, record)}
        </article>`;
      }).join('')}</div>
    </section>
  </div>${dock}`;
}

function renderInAppWindowModal(): string {
  const windows = state.inAppWindows.length ? state.inAppWindows : (state.inAppWindow ? [state.inAppWindow] : []);
  if (!windows.length) return '';
  windows.forEach(inAppWindowId);
  const dock = renderInAppWindowDock(windows);
  const visible = windows.filter((win) => !win.minimized);
  if (!visible.length) return dock;
  if (visible.length > 1) return renderInAppSplitWorkspace(visible, dock);
  const win = visible[0];
  state.inAppWindow = win;
  const parsedHost = safeHost(win.url);
  const isMaximized = Boolean(win.maximized);
  const record = recordForInAppWindow(win)
    || state.inAppWindowPreviousSelected
    || null;
  const frameConfig = inAppFrameConfig(win, record);

  let logBadgeText = '无';
  if (record) {
    const vm = buildVersionModalViewModel(record.platform, record.raw as never, record.raw);
    const releases = vm.releases?.length ? vm.releases : (record.releases?.length ? record.releases : rawRecords(record, ['releases', 'versions_data', 'version_history']));
    const fileIndexes = record.fileIndexes || [];
    const matchingGroup = record.platform === 'bilibili' ? state.biliGroups.find((g) => g.items.some((item) => String(item.bvid) === String(record.sourceId) || String(item.id) === String(record.sourceId))) : null;
    const relatedVideos = matchingGroup ? matchingGroup.items : [];
    const packVersion = (record.packVersion && record.packVersion.trim() && record.packVersion !== '未知' && !record.packVersion.includes('本地数据未提供'))
      ? record.packVersion.trim()
      : (record.platform === 'mcmod' && vm.latestVersion && vm.latestVersion.trim() && vm.latestVersion !== '未知' && !vm.latestVersion.includes('本地数据未提供') ? vm.latestVersion.trim() : '');
    const logCount = releases.length || fileIndexes.length || (relatedVideos.length > 1 ? relatedVideos.length : 0);
    logBadgeText = logCount > 0 ? `${logCount}条` : (packVersion ? `v${packVersion}` : '无');
  }

  const isChangelogOpen = Boolean(record && (win.showChangelogPane !== undefined ? win.showChangelogPane : true));
  const isPersonalOpen = Boolean(record && (win.showPersonalPane !== false));
  const sourcePaneTab = win.sourcePaneTab === 'source' || win.sourcePaneTab === 'versions' || (record?.platform === 'mcmod' && win.sourcePaneTab === 'mods') ? win.sourcePaneTab : 'versions';
  const modInfo = record?.platform === 'mcmod' ? mcmodTableModInfo(record) : null;

  return `<div class="modal-backdrop in-app-window-backdrop" data-action="minimize-in-app-window" data-window-id="${esc(inAppWindowId(win))}" role="dialog" aria-modal="true" aria-label="软件内网页小窗">
    <section class="modal-panel in-app-window-panel ${isMaximized ? 'is-maximized' : ''}" data-window-id="${esc(inAppWindowId(win))}" onclick="event.stopPropagation()">
      <header class="modal-header in-app-window-header">
        <div class="in-app-window-info">
          <span class="in-app-window-icon">🪟</span>
          <strong class="in-app-window-title" title="${esc(win.title)}">${esc(win.title)}</strong>
          ${parsedHost ? `<span class="in-app-window-host">${esc(parsedHost)}</span>` : ''}

        </div>
        <div class="in-app-window-url-bar" title="${esc(win.url)}">
          <span class="url-lock">🔒</span>
          <span class="url-text">${esc(win.url)}</span>
        </div>
        ${record ? `
        <div class="in-app-pane-toggles" role="group" aria-label="小窗栏位展开控制">
          <button type="button" class="in-app-pane-toggle-btn ${isChangelogOpen ? 'is-active' : ''}" data-action="toggle-in-app-changelog" title="${isChangelogOpen ? '收起左侧资料面板' : '展开左侧资料面板'}">
            <span>📋 资料与版本</span>
            <span class="in-app-toggle-count">${esc(logBadgeText)}</span>
          </button>
          <button type="button" class="in-app-pane-toggle-btn ${isPersonalOpen ? 'is-active' : ''}" data-action="toggle-in-app-personal" title="${isPersonalOpen ? '收起右侧个人区面板' : '展开右侧个人区面板'}">
            <span>👤 个人区</span>
          </button>
        </div>
        ` : ''}
        <div class="in-app-window-ctrls">
          <button type="button" class="in-app-ctrl-btn" data-action="reload-in-app-window" title="重新载入页面">🔄 刷新</button>
          <button type="button" class="in-app-ctrl-btn" data-action="minimize-in-app-window" title="收起到右侧悬浮栏">— 收起</button>
          <button type="button" class="in-app-ctrl-btn" data-action="toggle-maximize-in-app-window" title="${isMaximized ? '还原窗口' : '最大化窗口'}">${isMaximized ? '❐ 还原' : '⛶ 最大化'}</button>
          ${typeof window !== 'undefined' && window.desktopApi?.openInAppWindow ? `<button type="button" class="in-app-ctrl-btn" data-action="open-native-subwindow" data-url="${esc(win.url)}" data-title="${esc(win.title)}" title="在独立窗口中打开">🗗 独立窗口</button>` : ''}
          <a class="in-app-ctrl-btn external-open-btn" href="${esc(win.url)}" target="_blank" rel="noreferrer" title="在系统外部浏览器中打开此网页">浏览器打开 ↗</a>
          <button type="button" class="modal-close in-app-close-btn" data-action="close-in-app-window" aria-label="关闭小窗">✕</button>
        </div>
      </header>

      <div class="in-app-window-body in-app-split-body ${isPersonalOpen ? 'has-side-pane' : 'no-side-pane'}">
        ${record && isChangelogOpen ? `
        <aside class="in-app-changelog-pane" aria-label="资料与模组面板">
          <div class="in-app-pane-header">
            <div class="in-app-pane-title">
              <span class="js-in-app-source-title">${sourcePaneTab === 'mods' ? '🧩 已收录模组' : sourcePaneTab === 'source' ? '📄 来源资料' : '📋 版本历史'}</span>
              <span class="in-app-pane-badge js-in-app-source-count">${sourcePaneTab === 'mods' ? modInfo?.count || 0 : sourcePaneTab === 'source' ? '资料' : esc(logBadgeText)}</span>
            </div>
            <button type="button" class="in-app-pane-close-btn" data-action="toggle-in-app-changelog" title="收起左侧资料面板" aria-label="收起左侧资料面板">◂</button>
          </div>
          <div class="in-app-source-tabs ${modInfo ? 'has-mods' : ''}" role="tablist" aria-label="左栏内容">
            <button type="button" role="tab" data-action="switch-in-app-source-pane" data-source-tab="source" data-count="资料" aria-selected="${sourcePaneTab === 'source'}" class="${sourcePaneTab === 'source' ? 'is-active' : ''}">来源资料</button>
            <button type="button" role="tab" data-action="switch-in-app-source-pane" data-source-tab="versions" data-count="${esc(logBadgeText)}" aria-selected="${sourcePaneTab === 'versions'}" class="${sourcePaneTab === 'versions' ? 'is-active' : ''}">版本历史</button>
            ${modInfo ? `<button type="button" role="tab" data-action="switch-in-app-source-pane" data-source-tab="mods" data-count="${modInfo.count}" aria-selected="${sourcePaneTab === 'mods'}" class="${sourcePaneTab === 'mods' ? 'is-active' : ''}">包含模组 <span>${modInfo.count}</span></button>` : ''}
          </div>
          <div class="in-app-changelog-scroll" data-source-panel="source" ${sourcePaneTab !== 'source' ? 'hidden' : ''}>${renderInAppSourceTools(record)}</div>
          <div class="in-app-changelog-scroll" data-source-panel="versions" ${sourcePaneTab !== 'versions' ? 'hidden' : ''}>${renderInAppChangelogView(record)}</div>
          ${modInfo ? `<div class="in-app-changelog-scroll in-app-mods-scroll" data-source-panel="mods" ${sourcePaneTab !== 'mods' ? 'hidden' : ''}><div class="in-app-mods-intro"><strong>完整模组清单</strong><span>本地收录 ${modInfo.names.length} / 来源标记 ${modInfo.count} 款</span></div>${renderMcmodFullModList(record, 'window')}</div>` : ''}
        </aside>
        ` : ''}

        ${renderInAppWebPane(win, record)}

        ${record && isPersonalOpen ? `
        <aside class="in-app-side-pane" aria-label="个人标记与来源">
          ${renderInAppSideContent(record)}
        </aside>
        ` : ''}
      </div>

      <footer class="modal-footer in-app-window-footer">
        <span class="in-app-footer-tip">${esc(frameConfig.note)}</span>
        <button type="button" class="button secondary" data-action="close-in-app-window">关闭小窗</button>
      </footer>
    </section>
  </div>${dock}`;
}

export function renderPersonalBackup(entries: Record<string, PersonalStatus>): string {
  const missingSources = Object.entries(entries);
  return `<div class="personal-profile-content">
    <section class="personal-profile-section" aria-labelledby="personal-backup-title">
      <div class="personal-profile-section-heading"><div><h3 id="personal-backup-title">资料备份</h3><p>收藏、想玩、玩过、评分、备注及保存时的来源线索仅保存在本机。</p></div></div>
      <div class="personal-profile-actions">
        <a class="detail-link" href="/api/library/export" download="personal-library.json">导出个人资料 JSON</a>
        <label class="detail-link personal-profile-restore" for="personal-restore-file">选择备份并恢复</label>
        <input id="personal-restore-file" class="personal-profile-file-input" type="file" accept="application/json,.json">
        <span class="personal-profile-file-note">仅支持本应用导出的 JSON</span>
      </div>
      <p class="personal-profile-help">恢复前完整校验；已有 key 保留当前资料，备份冲突项跳过。备份不包含平台快照。</p>
    </section>
    <section class="personal-profile-section" aria-labelledby="personal-missing-title">
      <details class="personal-missing-details" ${missingSources.length ? '' : 'open'}>
        <summary><span id="personal-missing-title">缺源回访</span><span class="personal-profile-count">${missingSources.length} 条</span></summary>
        <div class="missing-source-list">
    ${missingSources.map(([key, status]) => {
      const url = safeExternalUrl(status.reference?.sourceUrl);
      return `<article class="missing-source-entry"><h4>${esc(status.reference?.title || '标题未知（本地数据未提供）')}</h4><p>当前数据未包含此来源</p><p>保存时记录的来源信息（非实时源站数据） · ${esc(key)} · ${status.reference?.objectType === 'bilibili-video' ? 'B站视频' : status.reference?.objectType === 'platform-record' ? '平台来源记录' : '对象类型未知'}</p>
        <p>收藏：${status.favorite ? '是' : '否'} · 想玩：${status.wantToPlay ? '是' : '否'} · 玩过：${status.played ? '是' : '否'} · 评分：${status.rating ?? '未评分'}</p><pre>${esc(status.note || '无备注')}</pre>
        ${url ? `<a class="detail-link" href="${esc(url)}" target="_blank" rel="noopener noreferrer">打开保存时的来源链接 ↗</a>` : '<p>来源 URL 未知（本地数据未提供）</p>'}</article>`;
    }).join('') || '<p class="personal-profile-empty">暂无缺源个人记录。</p>'}
        </div>
      </details>
    </section>
  </div>`;
}

function renderPersonalProfilePanel(): string {
  if (!state.personalProfileOpen) return '';
  return `<div class="modal-backdrop personal-profile-backdrop" data-action="close-personal-profile" role="dialog" aria-modal="true" aria-labelledby="personal-profile-title">
    <section class="modal-panel personal-profile-panel" id="personal-profile-dialog" onclick="event.stopPropagation()">
      <header class="modal-header personal-profile-header"><div class="modal-title-wrap"><span class="eyebrow">LOCAL PERSONAL DATA</span><h2 id="personal-profile-title">个人资料</h2><p>查看收藏更新提醒、管理本机个人标记备份，并回访当前快照中缺失的来源。</p></div><button type="button" class="modal-close personal-profile-close" data-action="close-personal-profile" aria-label="关闭个人资料">×</button></header>
      ${state.message ? `<div class="notice personal-profile-notice" role="status">${esc(state.message)}</div>` : ''}
      ${renderFavoriteUpdatesPanel()}
      ${renderPersonalBackup(state.missingPersonalSources)}
    </section>
  </div>`;
}

function renderFavoriteUpdatesPanel(): string {
  const result = state.favoriteUpdates;
  const events = result?.events || [];
  const unknown = result?.unknown || [];
  const eventRows = events.map((item) => {
    const sourceUrl = safeExternalUrl(item.sourceUrl);
    const kindName = item.kind === 'file-index' ? '来源文件索引' : item.kind === 'download-links' ? '下载链接' : '发布信息';
    const changedLinks = item.kind === 'download-links'
      ? item.currentValues.slice(0, 5).map((url) => {
        const safeUrl = safeExternalUrl(url);
        return safeUrl ? `<button type="button" class="detail-link" data-action="open-source" data-url="${esc(safeUrl)}">打开更新后的下载链接 ↗</button>` : '';
      }).join('')
      : '';
    return `<article class="favorite-update-entry ${item.readAt ? 'is-read' : 'is-unread'}">
      <div class="favorite-update-heading"><strong>${esc(item.title)}</strong><span>${esc(PLATFORM_CONFIGS[item.platform].name)} · ${esc(kindName)}</span></div>
      <p>${esc(item.summary)}</p><small>检测于 ${esc(formatTime(item.createdAt))} · ${esc(item.sourceId)}</small>
      ${changedLinks ? `<div class="favorite-update-links">${changedLinks}</div>` : ''}
      <div class="favorite-update-actions">${sourceUrl ? `<button type="button" class="detail-link" data-action="open-source" data-url="${esc(sourceUrl)}">打开原记录 ↗</button>` : '<span>原记录链接未知（本地数据未提供）</span>'}
      ${item.readAt ? '<span class="favorite-update-read-state">已读</span>' : `<button type="button" class="favorite-update-mark-read" data-action="mark-favorite-update-read" data-event-id="${esc(item.id)}">标记已读</button>`}</div>
    </article>`;
  }).join('') || '<p class="personal-profile-empty">暂无已检测到的收藏更新。</p>';
  const unknownRows = unknown.map((item) => {
    const sourceUrl = safeExternalUrl(item.sourceUrl);
    return `<article class="favorite-update-entry favorite-update-unknown"><div class="favorite-update-heading"><strong>${esc(item.title)}</strong><span>${esc(PLATFORM_CONFIGS[item.platform].name)} · ${esc(item.sourceId)}</span></div><p>暂不可判断：${esc(item.reason)}</p>${sourceUrl ? `<div class="favorite-update-actions"><button type="button" class="detail-link" data-action="open-source" data-url="${esc(sourceUrl)}">打开原记录 ↗</button></div>` : ''}</article>`;
  }).join('') || '<p class="favorite-update-note">当前收藏均有可比较的来源字段，或尚未积累需要说明的条目。</p>';
  return `<section class="personal-profile-section favorite-updates-section" aria-labelledby="favorite-updates-title">
    <div class="personal-profile-section-heading"><div><h3 id="favorite-updates-title">收藏更新 · ${result?.unreadCount || 0} 条未读</h3><p>仅在应用运行期间完成对应平台更新并切换快照后检查；不做后台轮询或实时推送。</p></div></div>
    ${state.favoriteUpdatesLoading ? '<div class="loading-state">正在读取收藏更新…</div>' : ''}
    ${state.favoriteUpdatesError ? `<div class="notice" role="alert">${esc(state.favoriteUpdatesError)}</div>` : ''}
    <div class="favorite-update-list">${eventRows}</div>
    <div class="favorite-update-unknown-heading"><h3>暂不可判断 · ${unknown.length} 条</h3><p>来源缺少稳定发布字段、当前快照缺少记录或数据不足时，不会生成更新提醒。</p></div>
    <div class="favorite-update-list">${unknownRows}</div>
  </section>`;
}

function replaceRootHtmlPreservingCoverImages(markup: string): void {
  disposeInAppFrame();
  const previousImages = new Map<string, HTMLImageElement[]>();
  root.querySelectorAll<HTMLImageElement>('img[data-cover-image]').forEach((image) => {
    const key = `${image.dataset.coverKey || ''}\u0000${image.dataset.originalSrc || ''}`;
    const matching = previousImages.get(key) || [];
    matching.push(image);
    previousImages.set(key, matching);
  });

  const previousFrames = new Map<string, HTMLIFrameElement>();
  root.querySelectorAll<HTMLIFrameElement>('iframe.js-in-app-frame').forEach((frame) => {
    const key = frame.dataset.frameKey || frame.src;
    previousFrames.set(key, frame);
  });

  const template = document.createElement('template');
  template.innerHTML = markup;
  template.content.querySelectorAll<HTMLImageElement>('img[data-cover-image]').forEach((nextImage) => {
    const key = `${nextImage.dataset.coverKey || ''}\u0000${nextImage.dataset.originalSrc || ''}`;
    const previous = previousImages.get(key)?.shift();
    if (!previous) return;
    Array.from(nextImage.attributes).forEach((attribute) => {
      if (attribute.name !== 'src' && attribute.name !== 'data-cover-state') previous.setAttribute(attribute.name, attribute.value);
    });
    nextImage.replaceWith(previous);
  });

  const retainedFrames: Array<{ frame: HTMLIFrameElement; placeholder: Comment }> = [];
  template.content.querySelectorAll<HTMLIFrameElement>('iframe.js-in-app-frame').forEach((nextFrame) => {
    const key = nextFrame.dataset.frameKey || nextFrame.src;
    const previousFrame = previousFrames.get(key);
    if (!previousFrame) return;
    // Moving an iframe through a detached template destroys its browsing context.
    // Keep it connected until its destination is connected too, then use the
    // state-preserving DOM move where supported.
    const placeholder = document.createComment('retained web window');
    nextFrame.replaceWith(placeholder);
    retainedFrames.push({ frame: previousFrame, placeholder });
  });

  const removedImages = [...previousImages.values()].flat();
  const previousChildren = Array.from(root.childNodes);
  root.append(template.content);
  retainedFrames.forEach(({ frame, placeholder }) => {
    const parent = placeholder.parentElement! as HTMLElement & {
      moveBefore?: (node: Node, child: Node | null) => void;
    };
    if (parent.moveBefore) {
      parent.moveBefore(frame, placeholder);
    } else {
      // Older engines reload on reparenting; never carry a stale success flag.
      delete frame.dataset.loaded;
      delete frame.dataset.requestStarted;
      parent.insertBefore(frame, placeholder);
    }
    placeholder.remove();
  });
  previousChildren.forEach((child) => child.remove());
  removedImages.forEach((image) => releaseDetachedCoverImage(image));
  initializeCoverImages();
}

function coverStatusText(state: CoverImageState): string {
  if (state === 'loading') return '封面加载中…';
  if (state === 'error') return '封面加载失败';
  if (state === 'timeout') return '封面加载超时';
  if (state === 'missing') return '来源未提供封面';
  return '';
}

function setCoverPresentation(image: HTMLImageElement, state: CoverImageState): void {
  image.dataset.coverState = state;
  const frame = image.closest<HTMLElement>('[data-cover-frame]');
  if (!frame) return;
  frame.dataset.coverState = state;
  const status = frame.querySelector<HTMLElement>('.cover-image-status');
  if (status) status.textContent = coverStatusText(state);
  const retry = frame.querySelector<HTMLButtonElement>('[data-action="retry-cover"]');
  if (retry) {
    const retryDelay = imageRetryDelay(image.dataset.originalSrc || '');
    const canRetry = (state === 'error' || state === 'timeout') && retryDelay === 0;
    retry.hidden = state !== 'error' && state !== 'timeout';
    retry.disabled = !canRetry;
    retry.textContent = canRetry ? '重试封面' : `封面失败 · ${Math.max(1, Math.ceil(retryDelay / 1000))} 秒后可重试`;
  }
  const trigger = frame.querySelector<HTMLElement>('.image-preview-trigger');
  if (trigger) {
    trigger.dataset.imageUrl = state === 'fallback' || state === 'error' || state === 'timeout' || state === 'missing'
      ? image.dataset.fallbackSrc || ''
      : image.dataset.originalSrc || image.dataset.fallbackSrc || '';
  }
}

const coverLoadTimers = new WeakMap<HTMLImageElement, number>();
const coverRetryTimers = new WeakMap<HTMLImageElement, number>();
const coverRetryTickets = new WeakMap<HTMLImageElement, ImageRetryTicket>();
const observedCoverImages = new WeakSet<HTMLImageElement>();
let coverObserver: IntersectionObserver | null = null;

function clearCoverTimer(image: HTMLImageElement): void {
  const timer = coverLoadTimers.get(image);
  if (timer !== undefined) window.clearTimeout(timer);
  coverLoadTimers.delete(image);
}

function releaseDetachedCoverImage(image: HTMLImageElement): void {
  if (image.isConnected) return;
  clearCoverTimer(image);
  const retryTimer = coverRetryTimers.get(image);
  if (retryTimer !== undefined) window.clearTimeout(retryTimer);
  coverRetryTimers.delete(image);
  coverObserver?.unobserve(image);
  observedCoverImages.delete(image);
  const ticket = coverRetryTickets.get(image);
  releaseDetachedCoverImageRequest(image, ticket);
  coverRetryTickets.delete(image);
}

function startCoverLoadTimer(image: HTMLImageElement): void {
  clearCoverTimer(image);
  if (!image.isConnected || image.dataset.coverState !== 'loading') return;
  coverLoadTimers.set(image, window.setTimeout(() => {
    if (!image.isConnected) {
      releaseDetachedCoverImage(image);
      return;
    }
    if (image.dataset.coverState !== 'loading') return;
    const original = safeImageUrl(image.dataset.originalSrc);
    const fallback = safeImageUrl(image.dataset.fallbackSrc);
    if (!original || !fallback) return;
    coverRetryTickets.delete(image);
    rememberFailedImage(original, 'timeout');
    image.src = fallback;
    setCoverPresentation(image, 'timeout');
    scheduleCoverRetry(image);
  }, COVER_IMAGE_TIMEOUT_MS));
}

function scheduleCoverRetry(image: HTMLImageElement): void {
  const previousTimer = coverRetryTimers.get(image);
  if (previousTimer !== undefined) window.clearTimeout(previousTimer);
  const delay = imageRetryDelay(image.dataset.originalSrc || '');
  if (!delay) return;
  coverRetryTimers.set(image, window.setTimeout(() => {
    coverRetryTimers.delete(image);
    if (!image.isConnected) return;
    const state = image.dataset.coverState;
    if (state === 'error' || state === 'timeout') setCoverPresentation(image, state);
  }, delay + 5));
}

function initializeCoverImages(): void {
  root.querySelectorAll<HTMLImageElement>('img[data-cover-image]').forEach((image) => {
    const currentState = (image.dataset.coverState || 'loading') as CoverImageState;
    setCoverPresentation(image, currentState);

    const original = safeImageUrl(image.dataset.originalSrc);
    if (!original) {
      clearCoverTimer(image);
      const fallback = safeImageUrl(image.dataset.fallbackSrc);
      if (fallback && safeImageUrl(image.currentSrc || image.src) !== fallback) image.src = fallback;
      setCoverPresentation(image, 'missing');
      return;
    }

    // Reused and cached images can finish before the delegated load/error
    // listeners see an event. Reconcile the DOM's real state here so an
    // already visible cover cannot retain a stale failure overlay.
    if (image.naturalWidth > 0) {
      handleCoverImageLoad(image);
      return;
    }
    if (image.complete && currentState === 'loading') {
      handleCoverImageFailure(image, 'error');
      return;
    }

    if (currentState !== 'loading' || !image.dataset.originalSrc) {
      scheduleCoverRetry(image);
      return;
    }
    if (typeof IntersectionObserver === 'undefined') {
      startCoverLoadTimer(image);
      return;
    }
    if (!coverObserver) {
      coverObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const target = entry.target as HTMLImageElement;
          coverObserver?.unobserve(target);
          startCoverLoadTimer(target);
        });
      }, { rootMargin: '240px' });
    }
    if (!observedCoverImages.has(image)) {
      observedCoverImages.add(image);
      coverObserver.observe(image);
    }
  });
}

function handleCoverImageLoad(image: HTMLImageElement): void {
  const currentState = image.dataset.coverState as CoverImageState;
  if (currentState !== 'loading' && currentState !== 'error' && currentState !== 'timeout') return;
  clearCoverTimer(image);
  coverRetryTickets.delete(image);
  const original = safeImageUrl(image.dataset.originalSrc);
  const fallback = safeImageUrl(image.dataset.fallbackSrc);
  const current = safeImageUrl(image.currentSrc || image.src);
  if (fallback && current === fallback) {
    setCoverPresentation(image, 'fallback');
    return;
  }
  finishImageLoad(original);
  setCoverPresentation(image, 'loaded');
}

function handleCoverImageFailure(image: HTMLImageElement, kind: 'error' | 'timeout'): void {
  if (image.dataset.coverState !== 'loading') return;
  // Some remote servers finish the decodable image before closing the
  // response. The browser can already paint it while `complete` remains
  // false, so a timer/error at that point must not replace a usable cover.
  if (image.naturalWidth > 0) {
    handleCoverImageLoad(image);
    return;
  }
  clearCoverTimer(image);
  coverRetryTickets.delete(image);
  const original = safeImageUrl(image.dataset.originalSrc);
  const fallback = safeImageUrl(image.dataset.fallbackSrc);
  if (!original || !fallback) {
    setCoverPresentation(image, 'missing');
    return;
  }
  rememberFailedImage(original, kind);
  image.src = fallback;
  setCoverPresentation(image, kind);
  scheduleCoverRetry(image);
}

function retryCoverImage(button: HTMLButtonElement): void {
  const image = button.closest<HTMLElement>('[data-cover-frame]')?.querySelector<HTMLImageElement>('img[data-cover-image]');
  if (!image) return;
  const ticket = startCoverImageRetry(image);
  if (!ticket) {
    setCoverPresentation(image, image.dataset.coverState as CoverImageState);
    scheduleCoverRetry(image);
    return;
  }
  coverRetryTickets.set(image, ticket);
  const retryTimer = coverRetryTimers.get(image);
  if (retryTimer !== undefined) window.clearTimeout(retryTimer);
  coverRetryTimers.delete(image);
  setCoverPresentation(image, 'loading');
  startCoverLoadTimer(image);
}

function render(): void {
  if (mainSearchCompositionInput?.isConnected) {
    mainSearchRenderPending = true;
    return;
  }
  const active = document.activeElement;
  const searchFocus = active instanceof HTMLInputElement && active.matches('#pack-search, .js-pack-search')
    ? { start: active.selectionStart, end: active.selectionEnd, direction: active.selectionDirection } : null;
  const detailFocus = active instanceof HTMLElement && active.closest('.detail-panel')
    ? { action: active.dataset.action, rating: active.dataset.rating, id: active.id,
        value: active instanceof HTMLTextAreaElement ? active.value : null,
        start: active instanceof HTMLTextAreaElement ? active.selectionStart : null,
        end: active instanceof HTMLTextAreaElement ? active.selectionEnd : null,
        recordId: state.selected?.id } : null;
  const data = state.data;
  const availableCount = data ? Object.values(data.platforms).filter((item) => item.available).length : 0;
  const publicTimes = (data as (DesktopDataState & { sourceTimes?: Record<string, string> }) | null)?.sourceTimes;
  const publicTimeMarkup = publicTimes ? `<details><summary>各平台数据时间</summary>${Object.entries(publicTimes).map(([platform, time]) => `<div>${esc(PLATFORM_CONFIGS[platform as Platform]?.name || platform)}：${esc(formatTime(time))}</div>`).join('')}<small>各平台并非同批抓取。刷新成功仅覆盖本轮增量范围；保留旧数据的来源仍显示原文件时间。</small></details>` : '';
  const selectedName = state.platform === 'all' ? '全部平台' : PLATFORM_CONFIGS[state.platform].name;
  const totalCount = data ? ALL_PLATFORMS.reduce((sum, platform) => sum + (data.platforms[platform]?.count || 0), 0) : 0;
  const theme = document.documentElement.dataset.theme || 'light';
  const topNav = platformItems.map((item) => {
    const count = item.id === 'all' ? totalCount : data?.platforms[item.id]?.count || 0;
    const icon = item.id === 'all' ? '<span class="platform-icon-wrap platform-all-icon"><span class="platform-icon-fallback">全</span></span>' : platformIcon(item.id);
    return `<button type="button" class="top-plat-btn ${state.platform === item.id ? 'active' : ''}" data-tab="${item.id}" data-action="set-platform" data-platform="${item.id}" aria-current="${state.platform === item.id ? 'page' : 'false'}"><span class="platform-nav-icon">${icon}</span><span class="platform-nav-label">${esc(item.name)}</span><span class="pnav-badge">${count ? formatCount(count) : '—'}</span></button>`;
  }).join('');
  const themeButtons = [['dark', '🌙'], ['light', '☀️'], ['eye', '🌿'], ['warm', '☕'], ['pink', '🌸']].map(([id, icon]) => `<button type="button" class="top-tdot ${theme === id ? 'active' : ''}" data-action="set-theme" data-theme="${id}" title="切换${id}主题">${icon}</button>`).join('');
  const missingPersonalCount = Object.keys(state.missingPersonalSources).length;
  const unreadFavoriteUpdates = state.favoriteUpdates?.unreadCount || 0;
  const personalBadges = [
    unreadFavoriteUpdates ? `<span class="personal-profile-count">更新 ${unreadFavoriteUpdates}</span>` : '',
    missingPersonalCount ? `<span class="personal-profile-count">缺源 ${missingPersonalCount}</span>` : '',
  ].filter(Boolean).join('');
  const personalProfileAction = `<button type="button" class="top-action-btn personal-profile-trigger" data-action="open-personal-profile" aria-haspopup="dialog" aria-label="打开个人资料${unreadFavoriteUpdates ? `，${unreadFavoriteUpdates} 条收藏更新未读` : ''}${missingPersonalCount ? `，${missingPersonalCount} 条缺源回访` : ''}">个人资料${personalBadges}</button>`;
  const body = (state.platform === 'all'
    ? `${renderCrossSearch()}<section class="all-platforms-grid" aria-label="六平台数据看板">${ALL_PLATFORMS.map(renderLegacyShowcaseCard).join('')}</section><div class="desktop-section-heading"><span class="eyebrow">LIVE SNAPSHOT</span><h2>${isStaticSite() ? '公开数据浏览' : '当前快照浏览'}</h2><p>${isStaticSite() ? '浏览已抓取的六平台公开数据；收藏、评分和备注仅保存在当前浏览器。' : '卡片、版本筛选与详情入口均来自本地快照；需要更多结果时可继续加载。'}</p></div>${renderResultsWorkspace(selectedName)}`
    : `${renderPlatformHero(state.platform)}${renderResultsWorkspace(selectedName)}`);
  const snapshotStatusLabel = isStaticSite() ? '静态展示' : data?.hasData ? '快照' : '等待数据';
  const snapshotStatusDescription = data?.hasData ? `当前快照：${data.snapshotId || '已载入'}` : '等待数据';
  const isUpdating = state.update?.state === 'running';
  const updateAction = `<button type="button" class="top-action-btn ${isUpdating ? 'is-running' : ''}" data-action="toggle-update" aria-label="数据更新" aria-expanded="${state.updateOpen}">${isUpdating ? '<span class="pulse-indicator"></span>' : ''}数据更新</button>`;
  const gridWrap = root?.querySelector<HTMLElement>('.picker-grid-wrap');
  const savedGridScrollTop = gridWrap ? gridWrap.scrollTop : 0;
  const savedUpdateScrollTop = root?.querySelector<HTMLElement>('.update-modal-panel')?.scrollTop || 0;
  const savedLogScrollTop = root?.querySelector<HTMLElement>('.update-log-list')?.scrollTop || 0;
  replaceRootHtmlPreservingCoverImages(`<div class="desktop-app legacy-shell"><div class="bg-layer" aria-hidden="true"></div>
    <header class="topbar"><div class="topbar-inner"><div class="topbar-left"><button type="button" class="topbar-brand" data-action="set-platform" data-platform="all" title="返回全平台总览"><span class="brand-cube">⛏️</span><span class="brand-title">我的世界整合包聚合</span><span class="brand-badge">${totalCount ? `${formatCount(totalCount)} 条${isStaticSite() ? '公开记录' : '本地记录'}` : isStaticSite() ? '正在读取公开目录…' : '本地快照工作台'}</span></button></div><div class="topbar-center"><nav class="topbar-platform-nav" aria-label="全端聚合多平台导航">${topNav}</nav><nav class="topbar-platform-flyout" aria-label="完整平台导航">${topNav}</nav></div><div class="topbar-actions"><button type="button" class="top-action-btn" data-action="toggle-audit">变动审计${auditCount(state.audit) ? ` <span class="audit-count-badge">${auditCount(state.audit)}</span>` : ''}</button>${updateAction}<button type="button" class="top-action-btn" data-action="choose-data">${data?.hasData ? '更换数据' : '选择数据'}</button>${personalProfileAction}<span class="data-status ${data?.hasData ? 'ready' : 'empty'}" title="${esc(snapshotStatusDescription)}" aria-label="${esc(snapshotStatusDescription)}"><i aria-hidden="true"></i>${snapshotStatusLabel}</span><div class="top-theme-pills" role="radiogroup" aria-label="切换主题">${themeButtons}</div></div></div></header>
    <main class="main-content">${body}<footer class="workspace-footer">${publicTimeMarkup}<span>${availableCount ? `${availableCount}/6 个平台已有数据` : '数据来源未知'}</span><span>${data?.updatedAt ? `快照更新时间：${esc(formatTime(data.updatedAt))}` : '数据不会自动编造'}</span>${data?.canonicalReady ? '<span class="canonical-ok">Canonical 已校验</span>' : isStaticSite() ? '<span>静态站不采集、不管理服务；各平台数据时间见说明</span>' : '<span>局部导入或原始数据不足，Canonical 状态未知</span>'}</footer></main><button type="button" class="update-task-dock" data-action="toggle-update" hidden><span class="pulse-indicator" aria-hidden="true"></span><span class="update-task-copy"><strong class="update-task-title"></strong><small class="update-task-detail"></small></span><span class="update-task-track" aria-hidden="true"><span></span></span></button>${renderCompareTray()}${detailPanel()}${imagePreviewPanel()}${renderCommentPreviewModal()}${auditPanel()}${renderComparePanel()}${renderPersonalProfilePanel()}${renderMcmodTrendDialog()}${renderUpdateModal()}${renderDataImportModal()}${renderPickerModal()}${renderInAppWindowModal()}</div>`);
  if (savedGridScrollTop > 0) {
    const nextGridWrap = root?.querySelector<HTMLElement>('.picker-grid-wrap');
    if (nextGridWrap) nextGridWrap.scrollTop = savedGridScrollTop;
  }
  const nextUpdatePanel = root?.querySelector<HTMLElement>('.update-modal-panel');
  if (nextUpdatePanel && savedUpdateScrollTop > 0) nextUpdatePanel.scrollTop = savedUpdateScrollTop;
  const nextLogList = root?.querySelector<HTMLElement>('.update-log-list');
  if (nextLogList && savedLogScrollTop > 0) nextLogList.scrollTop = savedLogScrollTop;
  bindEvents();
  if (searchFocus) {
    const search = root.querySelector<HTMLInputElement>('#pack-search');
    search?.focus({ preventScroll: true });
    if (search && searchFocus.start !== null && searchFocus.end !== null) {
      search.setSelectionRange(searchFocus.start, searchFocus.end, searchFocus.direction || 'none');
    }
  }
  if (detailFocusAfterRender) {
    root.querySelector<HTMLButtonElement>('.detail-panel [data-action="close-detail"]')?.focus({ preventScroll: true });
    detailFocusAfterRender = false;
  } else if (detailFocus && detailFocus.recordId === state.selected?.id) {
    const selector = detailFocus.id ? `#${CSS.escape(detailFocus.id)}` : detailFocus.action
      ? `[data-action="${CSS.escape(detailFocus.action)}"]${detailFocus.rating ? `[data-rating="${CSS.escape(detailFocus.rating)}"]` : ''}` : '';
    const control = selector ? root.querySelector<HTMLElement>(`.detail-panel ${selector}`) : null;
    if (control instanceof HTMLTextAreaElement && detailFocus.value !== null) {
      control.value = detailFocus.value;
      control.setSelectionRange(detailFocus.start, detailFocus.end);
    }
    control?.focus({ preventScroll: true });
  }
  refreshUpdateDock();
  const focusTarget = profileFocusAfterRender;
  profileFocusAfterRender = '';
  if (focusTarget === 'close') root.querySelector<HTMLButtonElement>('.personal-profile-close')?.focus();
  if (focusTarget === 'trigger') root.querySelector<HTMLButtonElement>('.personal-profile-trigger')?.focus();
  const trendFocusTarget = trendFocusAfterRender;
  trendFocusAfterRender = '';
  if (trendFocusTarget === 'close') root.querySelector<HTMLButtonElement>('.mcmod-trend-close')?.focus();
  if (trendFocusTarget === 'trigger') {
    const trigger = [...root.querySelectorAll<HTMLButtonElement>('[data-trend-trigger]')]
      .find((element) => element.dataset.recordId === trendReturnRecordId);
    trigger?.focus();
    trendReturnRecordId = '';
  }
  if (platformFilterFocusAfterRender === 'included-mod-search') {
    const search = root.querySelector<HTMLInputElement>('#included-mod-search');
    search?.focus();
    search?.setSelectionRange(search.value.length, search.value.length);
  }
  platformFilterFocusAfterRender = '';
  if (pickerFocusAfterRender === 'picker-modal-search') {
    const search = root.querySelector<HTMLInputElement>('#picker-modal-search');
    search?.focus();
    search?.setSelectionRange(search.value.length, search.value.length);
  }
  pickerFocusAfterRender = '';
  if (stickyFocusAfterRender === 'sticky-mod-search') {
    const search = root.querySelector<HTMLInputElement>('#sticky-mod-search');
    search?.focus();
    search?.setSelectionRange(search.value.length, search.value.length);
  } else if (stickyFocusAfterRender === 'sticky-cat-search') {
    const search = root.querySelector<HTMLInputElement>('#sticky-cat-search');
    search?.focus();
    search?.setSelectionRange(search.value.length, search.value.length);
  }
  stickyFocusAfterRender = '';
}

let disposeInAppFrame = (): void => {};
function bindMcmodModList(list: HTMLElement): void {
  const input = list.querySelector<HTMLInputElement>('.js-mcmod-mod-search');
  input?.addEventListener('input', () => {
    const query = input.value.trim().toLocaleLowerCase();
    let count = 0;
    list.querySelectorAll<HTMLElement>('.mcmod-mod-group').forEach((group) => {
      let groupCount = 0;
      group.querySelectorAll<HTMLElement>('.mcmod-full-mod-item').forEach((item) => {
        const match = !query || (item.dataset.modName || '').includes(query);
        item.hidden = !match;
        if (match) { count += 1; groupCount += 1; }
      });
      group.hidden = groupCount === 0;
    });
    const output = list.querySelector<HTMLElement>('[data-mod-match-count]');
    if (output) output.textContent = query ? `找到 ${count} 款` : `显示全部 ${count} 款`;
  });
  list.querySelectorAll<HTMLButtonElement>('.js-focus-in-app-mod').forEach((button) => {
    button.addEventListener('click', () => {
      const frame = button.closest<HTMLElement>('.in-app-window-panel')?.querySelector<HTMLIFrameElement>('.js-in-app-frame');
      const label = button.querySelector<HTMLElement>('.mcmod-mod-locate');
      if (!frame?.contentWindow) { if (label) label.textContent = '原站不可定位'; return; }
      button.classList.add('is-locating');
      if (label) label.textContent = frame.dataset.loaded ? '定位中…' : '等待网页…';
      const send = () => frame.contentWindow?.postMessage({ type: 'mcmod-focus-mod', name: button.dataset.modRawName || '' }, '*');
      if (frame.dataset.loaded) send();
      else frame.addEventListener('load', send, { once: true });
    });
  });
}

function bindInAppFrame(): void {
  disposeInAppFrame();
  const disposers: Array<() => void> = [];
  root.querySelectorAll<HTMLIFrameElement>('.js-in-app-frame').forEach((frame) => {
    const container = frame.closest<HTMLElement>('[data-window-id]');
    const viewport = frame.closest<HTMLElement>('.in-app-web-viewport');
    const pane = frame.closest<HTMLElement>('.in-app-web-pane');
    const status = pane?.querySelector<HTMLElement>('.js-in-app-loader');
    const zoom = pane?.querySelector<HTMLSelectElement>('.js-in-app-zoom');
    if (!viewport || !status || !zoom) return;
    const windowId = container?.dataset.windowId || '';
    const windows = state.inAppWindows.length ? state.inAppWindows : (state.inAppWindow ? [state.inAppWindow] : []);
    const win = windows.find((item) => inAppWindowId(item) === windowId) || state.inAppWindow;
    zoom.value = win?.zoom || 'auto';
    const resize = () => {
      const viewportWidth = Math.max(1, viewport.clientWidth);
      const viewportHeight = Math.max(1, viewport.clientHeight);
      const scale = zoom.value === 'auto'
        ? Math.max(0.85, Math.min(1, viewportWidth / 1100))
        : Number(zoom.value);
      const contentWidth = Math.max(1100, viewportWidth / scale);
      frame.style.width = `${contentWidth}px`;
      frame.style.height = `${viewportHeight / scale}px`;
      frame.style.transform = `scale(${scale})`;
      frame.dataset.effectiveScale = scale.toFixed(3);
      viewport.style.overflowX = contentWidth * scale <= viewportWidth + 1 ? 'hidden' : 'auto';
      viewport.style.overflowY = 'hidden';
    };
    const changed = () => { if (win) win.zoom = zoom.value; resize(); };
    let timer: ReturnType<typeof setTimeout>;
    const loaded = () => { clearTimeout(timer); frame.dataset.loaded = 'true'; if (frame.dataset.failed !== 'true') status.textContent = '页面已返回；若空白请切换上方资料或版本历史'; };
    const failed = () => { clearTimeout(timer); status.textContent = '载入失败，请刷新或用浏览器打开'; };
    if (!frame.dataset.requestStarted) frame.dataset.requestStarted = String(Date.now());
    if (frame.dataset.loaded) loaded();
    else timer = setTimeout(() => { status.textContent = '等待较久：原站可能限制内嵌或网络较慢'; }, Math.max(0, 12000 - (Date.now() - Number(frame.dataset.requestStarted))));
    frame.addEventListener('load', loaded);
    frame.addEventListener('error', failed);
    const onMessage = (message: MessageEvent) => {
      if (message.source !== frame.contentWindow || !win) return;
      const data = message.data as { type?: unknown; entries?: unknown; name?: unknown; found?: unknown; ok?: boolean; url?: string } | null;
      if (!data || typeof data !== 'object') return;
      if (data.type === 'in-app-page-state') {
        clearTimeout(timer);
        frame.dataset.failed = data.ok === false ? 'true' : 'false';
        status.textContent = data.ok === true ? '只读网页已载入 · 版本与图片可在上方切换' : data.ok === false ? '原站请求失败，请切换资料或版本历史' : '正在打开链接…';
        return;
      }
      if (data.type === 'mcmod-mod-index' && Array.isArray(data.entries)) {
        const record = recordForInAppWindow(win);
        if (record?.platform !== 'mcmod') return;
        const entries = data.entries.slice(0, 5000).filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === 'object')
          .map((item) => ({ name: String(item.name || '').slice(0, 500), url: safeExternalUrl(item.url), categoryUrl: safeExternalUrl(item.categoryUrl) }))
          .filter((item) => item.name);
        mcmodLiveModIndex.set(record.id, entries);
        const oldList = container?.querySelector<HTMLElement>('.mcmod-full-mod-list.is-window');
        if (!oldList) return;
        const template = document.createElement('template');
        template.innerHTML = renderMcmodFullModList(record, 'window');
        const nextList = template.content.firstElementChild as HTMLElement | null;
        if (nextList) { oldList.replaceWith(nextList); bindMcmodModList(nextList); }
      } else if (data.type === 'mcmod-focus-result') {
        const name = String(data.name || '');
        const button = [...(container?.querySelectorAll<HTMLButtonElement>('.js-focus-in-app-mod.is-locating') || [])]
          .find((item) => item.dataset.modRawName === name);
        const label = button?.querySelector<HTMLElement>('.mcmod-mod-locate');
        if (label) label.textContent = data.found === true ? '已定位 ✓' : '原站未找到';
        button?.classList.remove('is-locating');
      }
    };
    window.addEventListener('message', onMessage);
    zoom.addEventListener('change', changed);
    const observer = new ResizeObserver(resize);
    observer.observe(viewport);
    resize();
    disposers.push(() => { clearTimeout(timer); observer.disconnect(); frame.removeEventListener('load', loaded); frame.removeEventListener('error', failed); zoom.removeEventListener('change', changed); window.removeEventListener('message', onMessage); });
  });
  disposeInAppFrame = () => { disposers.forEach((dispose) => dispose()); };
}

function bindTrendPreviews(): void {
  root.querySelectorAll<HTMLElement>('.mcmod-trend-detail').forEach((container) => {
    const trigger = container.querySelector<HTMLElement>('[data-trend-trigger]');
    const graph = trigger?.querySelector<HTMLElement>('.mcmod-trend-sparkline');
    const output = container.querySelector<HTMLOutputElement>('output');
    const record = state.records.find((item) => item.id === trigger?.dataset.recordId) || state.selected || state.inAppWindowPreviousSelected;
    if (!trigger || !graph || !output || !record) return;
    const series = mcmodTrendSeries(record);
    if (series.status !== 'ready') return;
    let index = series.points.length - 1;
    const show = () => { const point = series.points[index]; output.textContent = `${point.date} · 官方流行指数 ${point.value}`; };
    graph.addEventListener('pointermove', (event) => { const box = graph.getBoundingClientRect(); index = Math.max(0, Math.min(series.points.length - 1, Math.round((event.clientX - box.left) / box.width * (series.points.length - 1)))); show(); });
    trigger.addEventListener('keydown', (event) => { if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return; event.preventDefault(); index = Math.max(0, Math.min(series.points.length - 1, index + (event.key === 'ArrowRight' ? 1 : -1))); show(); });
  });
}

function bindEvents(): void {
  bindInAppFrame();
  bindTrendPreviews();
  root.querySelectorAll<HTMLDetailsElement>('[data-more-filters]').forEach((details) => details.addEventListener('toggle', () => {
    state.moreFiltersOpen = details.open;
  }));
  root.querySelector<HTMLInputElement>('#personal-restore-file')?.addEventListener('change', async (event) => {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;
    try {
      if (file.size > 16 * 1024 * 1024) throw new Error('备份不能超过 16 MiB');
      const result = await window.desktopApi.restorePersonalLibrary(JSON.parse(await file.text()));
      await loadPersonalLibrary();
      await loadRecords(true);
      state.message = `恢复结果：restored=${result.restored}，skipped-conflict=${result['skipped-conflict']}，invalid=${result.invalid}`;
    } catch (error) { state.message = `恢复未确认成功，请核对当前资料：${error instanceof Error ? error.message : String(error)}`; }
    render();
  });
  root.querySelectorAll<HTMLElement>('[data-action]').forEach((element) => {
    const host = safeHost(element.dataset.url || '').toLowerCase();
    if (element.dataset.action === 'open-in-app-window' && (host === 'bilibili.com' || host.endsWith('.bilibili.com'))) {
      element.textContent = '⚠ B站小窗（已知问题）';
      element.title = 'B站站内打开有问题，可能空白或一直等待，建议使用浏览器打开';
    }
    element.addEventListener('click', (event) => void handleAction(element, event));
  });
  const trendPanel = root.querySelector<HTMLElement>('[data-mcmod-trend-panel]');
  trendPanel?.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      event.preventDefault();
      event.stopPropagation();
      closeMcmodTrendChart();
    }
  });
  const trendCapture = root.querySelector<SVGRectElement>('[data-trend-capture]');
  const currentTrendPoints = selectedMcmodTrendPoints();
  if (trendCapture && currentTrendPoints.length >= 2) {
    const svg = trendCapture.ownerSVGElement;
    const viewBoxWidth = Number(svg?.getAttribute('viewBox')?.split(/\s+/)[2]) || 760;
    const plotLeft = Number(trendCapture.getAttribute('x')) || 0;
    const plotWidth = Number(trendCapture.getAttribute('width')) || 1;
    const guide = svg?.querySelector<SVGLineElement>('[data-trend-guide]');
    const readout = root.querySelector<HTMLOutputElement>('[data-trend-readout]');
    const showTrendPoint = (index: number) => {
      const selectedIndex = Math.max(0, Math.min(currentTrendPoints.length - 1, index));
      const point = currentTrendPoints[selectedIndex];
      const x = plotLeft + (selectedIndex / (currentTrendPoints.length - 1)) * plotWidth;
      guide?.setAttribute('x1', String(x));
      guide?.setAttribute('x2', String(x));
      if (readout) readout.textContent = `${selectedIndex === currentTrendPoints.length - 1 ? '最新' : selectedIndex === 0 ? '最早' : '历史点'} · ${point.date} · 指数 ${formatTrendValue(point.value)}`;
      trendCapture.setAttribute('aria-valuenow', String(selectedIndex));
      trendCapture.setAttribute('aria-valuetext', `${point.date}，${formatTrendValue(point.value)}`);
    };
    const pointIndexFromPointer = (clientX: number): number => {
      const bounds = svg?.getBoundingClientRect();
      if (!bounds?.width) return currentTrendPoints.length - 1;
      const chartX = (clientX - bounds.left) * viewBoxWidth / bounds.width;
      const ratio = Math.max(0, Math.min(1, (chartX - plotLeft) / plotWidth));
      return Math.round(ratio * (currentTrendPoints.length - 1));
    };
    trendCapture.addEventListener('pointermove', (event) => showTrendPoint(pointIndexFromPointer(event.clientX)));
    trendCapture.addEventListener('click', (event) => showTrendPoint(pointIndexFromPointer(event.clientX)));
    trendCapture.addEventListener('keydown', (event) => {
      const selectedIndex = Number(trendCapture.getAttribute('aria-valuenow') || currentTrendPoints.length - 1);
      if (event.key === 'ArrowLeft') showTrendPoint(selectedIndex - 1);
      else if (event.key === 'ArrowRight') showTrendPoint(selectedIndex + 1);
      else if (event.key === 'Home') showTrendPoint(0);
      else if (event.key === 'End') showTrendPoint(currentTrendPoints.length - 1);
      else return;
      event.preventDefault();
    });
  }
  root.querySelectorAll<HTMLElement>('.js-copy-btn').forEach((element) => element.addEventListener('click', (event) => {
    event.preventDefault();
    event.stopPropagation();
    const text = element.dataset.text || '';
    if (!text) return;
    const copy = navigator.clipboard?.writeText(text) || Promise.resolve();
    void copy.then(() => {
      state.message = '已复制到剪贴板';
      render();
    });
  }));
  root.querySelectorAll<HTMLElement>('.js-open-bili-group-versions').forEach((element) => element.addEventListener('click', (event) => {
    event.preventDefault();
    event.stopPropagation();
    const key = element.dataset.groupKey || '';
    const group = state.biliGroups.find((item) => item.key === key);
    const latest = group?.items[0];
    const record = latest ? state.records.find((item) => item.sourceId === latest.bvid) : null;
    if (!record) return;
    state.selected = record;
    state.imagePreview = null;
    void loadComments(record);
  }));
  root.querySelectorAll<HTMLElement>('.js-bbsmc-lightbox-thumb').forEach((element) => element.addEventListener('click', (event) => {
    event.preventDefault();
    event.stopPropagation();
    const url = safeImageUrl(element.dataset.full || element.getAttribute('src') || '');
    if (!url) return;
    state.imagePreview = { url, title: element.dataset.title || '图片预览' };
    render();
  }));
  root.querySelectorAll<HTMLElement>('.js-open-plat-version-modal').forEach((element) => element.addEventListener('click', (event) => {
    event.preventDefault();
    event.stopPropagation();
    const card = element.closest<HTMLElement>('.desktop-rich-card');
    const index = Number(card?.dataset.index || '-1');
    const record = state.records[index];
    if (!record) return;
    state.selected = record;
    state.imagePreview = null;
    void loadComments(record);
  }));
  root.querySelectorAll<HTMLElement>('.mcmod-trend-sparkline').forEach((sparkline) => {
    sparkline.addEventListener('mousemove', (event) => {
      const valsStr = sparkline.dataset.trendVals || '';
      const datesStr = sparkline.dataset.trendDates || '';
      if (!valsStr) return;
      const vals = valsStr.split(',').map(Number).filter((v) => !isNaN(v));
      const dates = datesStr ? datesStr.split(',') : [];
      if (vals.length < 2) return;
      const rect = sparkline.getBoundingClientRect();
      let ratio = (event.clientX - rect.left) / rect.width;
      if (ratio < 0) ratio = 0;
      if (ratio > 1) ratio = 1;
      const idx = Math.min(vals.length - 1, Math.max(0, Math.round(ratio * (vals.length - 1))));
      const val = vals[idx];
      const date = dates[idx] || '';

      const cell = sparkline.closest<HTMLElement>('.mcmod-trend-cell');
      if (!cell) return;
      let probe = cell.querySelector<HTMLElement>('.trend-inline-probe');
      if (!probe) {
        probe = document.createElement('div');
        probe.className = 'trend-inline-probe';
        cell.appendChild(probe);
      }
      const cellRect = cell.getBoundingClientRect();
      let left = event.clientX - cellRect.left + 10;
      let top = event.clientY - cellRect.top - 44;
      if (left > cellRect.width - 104) left = Math.max(6, cellRect.width - 104);
      if (top < 6) top = event.clientY - cellRect.top + 16;
      probe.innerHTML = `<b>${val.toLocaleString()}</b>${date ? `<span>${date}</span>` : ''}`;
      probe.style.left = `${left}px`;
      probe.style.top = `${top}px`;
      probe.style.display = 'block';
    });
    sparkline.addEventListener('mouseleave', () => {
      const cell = sparkline.closest<HTMLElement>('.mcmod-trend-cell');
      const probe = cell?.querySelector<HTMLElement>('.trend-inline-probe');
      if (probe) probe.style.display = 'none';
    });
  });
  root.querySelectorAll<HTMLElement>('.mcmod-mod-cell').forEach((cell) => {
    cell.addEventListener('click', (event) => {
      event.stopPropagation();
    });
  });
  root.querySelectorAll<HTMLButtonElement>('.mod-summary-chip').forEach((btn) => {
    btn.addEventListener('click', (event) => {
      event.preventDefault();
      event.stopPropagation();
      const catKey = btn.dataset.modCatKey;
      if (!catKey) return;
      const details = btn.closest<HTMLDetailsElement>('.mod-details');
      if (details) details.open = true;
      const section = details?.querySelector<HTMLElement>(`.mod-category-section[data-mod-cat-key="${catKey}"]`);
      if (section) {
        section.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        section.classList.add('is-highlighted');
        setTimeout(() => section.classList.remove('is-highlighted'), 1500);
      }
    });
  });
  root.querySelectorAll<HTMLElement>('.tag-mod').forEach((tag) => {
    tag.addEventListener('click', (event) => {
      if ((event.target as HTMLElement).closest('.tag-mod-open')) {
        event.stopPropagation();
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      const modName = tag.dataset.mod;
      if (modName) {
        state.query = modName;
        void loadRecords(true);
      }
    });
  });
  root.querySelector<HTMLInputElement>('.js-comment-preview-search')?.addEventListener('input', (event) => {
    state.commentPreviewQuery = (event.target as HTMLInputElement).value;
    const record = state.commentPreviewRecord;
    if (!record) return;
    const bodyEl = root.querySelector<HTMLElement>('.comment-preview-body');
    const footerCountEl = root.querySelector<HTMLElement>('.js-comment-count-text');
    if (bodyEl) {
      const commentState = state.comments.sourceId === record.sourceId ? state.comments : null;
      const comments = commentState?.comments || [];
      const query = state.commentPreviewQuery.trim().toLowerCase();
      const filtered = query
        ? comments.filter((c) => {
            const author = String(c.author ?? c.user ?? c.name ?? '').toLowerCase();
            const text = String(commentBody(c)).toLowerCase();
            return author.includes(query) || text.includes(query);
          })
        : comments;
      if (!comments.length) {
        const sourceUrl = record.platform === 'mcmod'
          ? `https://www.mcmod.cn/modpack/${record.sourceId}.html#comment`
          : safeExternalUrl(record.url);
        bodyEl.innerHTML = `<div class="empty-evidence comment-empty-state">
          <div class="comment-empty-icon">💬</div>
          <div class="comment-empty-title">暂无本地存档评论</div>
          <p class="comment-empty-desc">${record.platform === 'mcmod' ? '当前快照未收录此整合包的独立评论数据文件。' : `当前本地快照未归档「${esc(PLATFORM_CONFIGS[record.platform]?.name || record.platform)}」的独立评论文本。`}</p>
          ${sourceUrl ? `<a class="button primary" href="${esc(sourceUrl)}" target="_blank" rel="noreferrer">前往原站查看最新评论 ↗</a>` : ''}
        </div>`;
      } else if (!filtered.length) {
        bodyEl.innerHTML = `<div class="empty-evidence">没有找到匹配关键词 “${esc(query)}” 的评论。</div>`;
      } else {
        bodyEl.innerHTML = renderComments(filtered);
      }
      if (footerCountEl) {
        footerCountEl.textContent = query
          ? `筛选出 ${filtered.length} / ${comments.length} 条评论`
          : `已展示全部 ${comments.length} 条本地评论`;
      }
    }
  });
  root.querySelector<HTMLInputElement>('#server-only-toggle')?.addEventListener('change', (event) => {
    state.serverOnly = (event.target as HTMLInputElement).checked;
    void loadRecords(true);
  });
  root.querySelector<HTMLInputElement>('#included-mod-exclude')?.addEventListener('change', (event) => {
    state.includedModsExclude = (event.target as HTMLInputElement).checked;
    void loadRecords(true);
  });
  root.querySelector<HTMLInputElement>('#gameplay-category-exclude')?.addEventListener('change', (event) => {
    state.gameplayCategoriesExclude = (event.target as HTMLInputElement).checked;
    void loadRecords(true);
  });
  root.querySelector<HTMLSelectElement>('#update-mode')?.addEventListener('change', (event) => {
    const value = (event.target as HTMLSelectElement).value;
    if (value === 'new' || value === 'trend' || value === 'versions' || value === 'all') {
      state.mcmodUpdateMode = value;
      if (value === 'versions' && state.mcmodOldLimit === 50) state.mcmodOldLimit = state.data?.platforms.mcmod.count || 1484;
      state.updateFormError = '';
      render();
    }
  });
  root.querySelectorAll<HTMLElement>('[data-mod-list]').forEach(bindMcmodModList);
  root.querySelector<HTMLInputElement>('#update-mcmod-limit')?.addEventListener('input', (event) => {
    state.mcmodOldLimit = Number((event.target as HTMLInputElement).value);
  });
  root.querySelector<HTMLInputElement>('#update-limit')?.addEventListener('input', (event) => {
    state.updateOtherLimit = (event.target as HTMLInputElement).value;
  });
  root.querySelector<HTMLSelectElement>('#update-other-mode')?.addEventListener('change', (event) => {
    state.otherUpdateMode = (event.target as HTMLSelectElement).value === 'existing' ? 'existing' : 'catalog';
    state.updateFormError = '';
    render();
  });
  root.querySelector<HTMLInputElement>('#update-pages')?.addEventListener('input', (event) => {
    state.updateBiliPages = Number((event.target as HTMLInputElement).value);
  });
  const includedModSearch = root.querySelector<HTMLInputElement>('#included-mod-search');
  if (includedModSearch) {
    bindCompositionAwareSearchInput(includedModSearch, (value) => {
      state.includedModSearch = value;
    }, () => {
      platformFilterFocusAfterRender = 'included-mod-search';
      render();
    });
    includedModSearch.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && state.includedModSearch) {
        event.preventDefault();
        event.stopPropagation();
        state.includedModSearch = '';
        platformFilterFocusAfterRender = 'included-mod-search';
        render();
      }
    });
  }
  const pickerSearch = root.querySelector<HTMLInputElement>('#picker-modal-search');
  if (pickerSearch) {
    bindCompositionAwareSearchInput(pickerSearch, (value) => {
      if (state.pickerModal) {
        state.pickerModal.search = value;
        state.pickerModal.limit = value ? 500 : 300;
      }
    }, () => {
      pickerFocusAfterRender = 'picker-modal-search';
      render();
    });
    pickerSearch.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && state.pickerModal?.search) {
        event.preventDefault();
        event.stopPropagation();
        state.pickerModal.search = '';
        pickerFocusAfterRender = 'picker-modal-search';
        render();
      }
    });
  }
  root.querySelector<HTMLSelectElement>('#picker-modal-sort')?.addEventListener('change', (event) => {
    const val = (event.target as HTMLSelectElement).value as PickerSort;
    if (state.pickerModal) {
      state.pickerModal.sort = val;
      render();
    }
  });
  const stickyModSearch = root.querySelector<HTMLInputElement>('#sticky-mod-search');
  if (stickyModSearch) {
    bindCompositionAwareSearchInput(stickyModSearch, (value) => {
      state.stickyModSearch = value;
    }, () => {
      stickyFocusAfterRender = 'sticky-mod-search';
      render();
    });
    stickyModSearch.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && state.stickyModSearch) {
        event.preventDefault();
        event.stopPropagation();
        state.stickyModSearch = '';
        stickyFocusAfterRender = 'sticky-mod-search';
        render();
      }
    });
  }
  const stickyCatSearch = root.querySelector<HTMLInputElement>('#sticky-cat-search');
  if (stickyCatSearch) {
    bindCompositionAwareSearchInput(stickyCatSearch, (value) => {
      state.stickyCatSearch = value;
    }, () => {
      stickyFocusAfterRender = 'sticky-cat-search';
      render();
    });
    stickyCatSearch.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && state.stickyCatSearch) {
        event.preventDefault();
        event.stopPropagation();
        state.stickyCatSearch = '';
        stickyFocusAfterRender = 'sticky-cat-search';
        render();
      }
    });
  }
  root.querySelectorAll<HTMLInputElement>('#pack-search, .js-pack-search').forEach((input) => {
    input.addEventListener('compositionstart', () => {
      mainSearchCompositionInput = input;
      window.clearTimeout(searchTimer);
    });
    bindCompositionAwareSearchInput(input, (value) => {
      state.query = value;
    }, () => {
      window.clearTimeout(searchTimer);
      searchTimer = window.setTimeout(() => void loadRecords(), 180);
    });
    input.addEventListener('compositionend', () => {
      if (mainSearchCompositionInput === input) mainSearchCompositionInput = null;
      if (mainSearchRenderPending) {
        mainSearchRenderPending = false;
        render();
      }
    });
  });
  root.querySelectorAll<HTMLTextAreaElement>('[data-personal-note]').forEach((textarea) => {
    textarea.addEventListener('input', (event) => {
      const el = event.target as HTMLTextAreaElement;
      const targetRecord = recordForPersonalTarget(el) || state.selected;
      if (!targetRecord || !isPersonalWritable(targetRecord)) return;
      const key = personalKey(targetRecord);
      const note = el.value;
      window.clearTimeout(personalNoteTimers.get(key));
      if (document.documentElement.dataset.staticSite === 'true') {
        // Pages persists localStorage synchronously before its API promise returns.
        void savePersonalPatch(targetRecord, { note }, false);
        return;
      }
      personalNoteTimers.set(key, window.setTimeout(() => {
        personalNoteTimers.delete(key);
        void savePersonalPatch(targetRecord, { note }, false);
      }, 350));
    });
  });
}

async function loadComments(record: DesktopRecord): Promise<void> {
  state.comments = { sourceId: record.sourceId, loading: true, available: false, pageCount: 0, comments: [], sourceFile: null, error: '' };
  render();
  try {
    const result = await window.desktopApi.getPlatformComments(record.platform, record.sourceId);
    const isTarget = state.selected?.id === record.id || state.commentPreviewRecord?.id === record.id;
    if (!isTarget) return;

    let comments = result.comments || [];
    let pageCount = result.pageCount;
    let available = result.available;

    if ((!comments || comments.length === 0) && record.raw) {
      const raw = record.raw as Record<string, unknown>;
      if (typeof raw.pinned_comment === 'string' && raw.pinned_comment.trim()) {
        comments = [{
          author: `${record.author || 'UP主'}（置顶说明）`,
          text: raw.pinned_comment.trim(),
          date: String(raw.pub_time || raw.pubTime || record.updatedAt || ''),
          likes: 0,
        }];
        pageCount = Math.max(pageCount, 1);
        available = true;
      } else if (Array.isArray(raw.comments) && raw.comments.length > 0) {
        comments = raw.comments as DesktopComment[];
        pageCount = Math.max(pageCount, comments.length);
        available = true;
      }
    }

    state.comments = {
      sourceId: result.sourceId || record.sourceId,
      loading: false,
      available,
      pageCount,
      comments,
      sourceFile: result.sourceFile,
      error: result.error || '',
    };
  } catch (error) {
    const isTarget = state.selected?.id === record.id || state.commentPreviewRecord?.id === record.id;
    if (!isTarget) return;
    state.comments = {
      sourceId: record.sourceId,
      loading: false,
      available: false,
      pageCount: 0,
      comments: [],
      sourceFile: null,
      error: error instanceof Error ? error.message : String(error),
    };
  }
  render();
}

type PersonalPatch = Partial<Pick<PersonalStatus, 'favorite' | 'wantToPlay' | 'played' | 'rating' | 'note'>>;

export function resolvePersonalTargetRecord(
  records: DesktopRecord[],
  platform: Platform | undefined,
  sourceId: string | undefined,
  fallbackIndex: number,
): DesktopRecord | null {
  if (platform && sourceId !== undefined && ALL_PLATFORMS.includes(platform)) {
    return records.find((record) => record.platform === platform && record.sourceId === sourceId) || null;
  }
  return records[fallbackIndex] || null;
}

function recordForPersonalTarget(element: HTMLElement): DesktopRecord | null {
  return resolvePersonalTargetRecord(
    state.records,
    element.dataset.personalPlatform as Platform | undefined,
    element.dataset.personalSourceId,
    Number(element.dataset.index || '-1'),
  );
}

async function savePersonalPatch(record: DesktopRecord, patch: PersonalPatch, rerender = true): Promise<void> {
  if (!isPersonalWritable(record)) {
    state.message = personalUnavailableReason(record);
    if (rerender) render();
    return;
  }
  const key = personalKey(record);
  const previous = personalStatus(record);
  state.personalLibrary[key] = { ...previous, ...patch, updatedAt: new Date().toISOString() };
  if (rerender) render();
  try {
    const result = await window.desktopApi.updatePersonalStatus(record.platform, record.sourceId, patch);
    state.personalLibrary[key] = result.status;
    await loadFavoriteUpdates(false);
    if (state.personalFilter) await loadRecords(true);
    else if (rerender) render();
  } catch (error) {
    state.personalLibrary[key] = previous;
    state.message = error instanceof Error ? error.message : String(error);
    render();
  }
}

async function loadPersonalLibrary(): Promise<void> {
  try {
    const result = await window.desktopApi.getPersonalLibrary();
    state.personalLibrary = result.entries || {};
    state.missingPersonalSources = (await window.desktopApi.getMissingPersonalSources()).entries;
  } catch (error) {
    state.personalLibrary = {};
    state.message = error instanceof Error ? error.message : String(error);
  }
}

async function loadFavoriteUpdates(renderAfter = false): Promise<void> {
  state.favoriteUpdatesLoading = true;
  state.favoriteUpdatesError = '';
  try {
    state.favoriteUpdates = await window.desktopApi.getFavoriteUpdates();
  } catch (error) {
    state.favoriteUpdatesError = error instanceof Error ? error.message : String(error);
  } finally {
    state.favoriteUpdatesLoading = false;
    if (renderAfter) render();
  }
}

async function loadAudit(): Promise<void> {
  state.auditLoading = true;
  state.auditError = '';
  render();
  try {
    state.audit = await window.desktopApi.getAuditDiff();
  } catch (error) {
    state.audit = null;
    state.auditError = error instanceof Error ? error.message : String(error);
  } finally {
    state.auditLoading = false;
    render();
  }
}

function closeMcmodTrendChart(): void {
  if (!state.trendChart) return;
  trendReturnRecordId = state.trendChart.record.id;
  state.trendChart = null;
  trendFocusAfterRender = 'trigger';
  render();
}

async function loadDataLibrary(): Promise<void> {
  state.dataLibraryLoading = true;
  state.dataLibraryError = '';
  render();
  try {
    state.dataLibrary = await window.desktopApi.getDataLibrary();
  } catch (error) {
    state.dataLibraryError = error instanceof Error ? error.message : String(error);
  } finally {
    state.dataLibraryLoading = false;
    render();
  }
  if (mcmodTableFocusRecordId) {
    const trigger = [...root.querySelectorAll<HTMLButtonElement>('[data-action="toggle-mcmod-table-mods"]')]
      .find((element) => element.dataset.recordId === mcmodTableFocusRecordId);
    trigger?.focus({ preventScroll: true });
    mcmodTableFocusRecordId = '';
  }
}

async function copyLocalPath(value: string): Promise<void> {
  if (!value) throw new Error('当前没有可复制的目录路径');
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(value);
    return;
  }
  const input = document.createElement('textarea');
  input.value = value;
  input.setAttribute('readonly', '');
  input.style.position = 'fixed';
  input.style.opacity = '0';
  document.body.appendChild(input);
  input.select();
  const copied = document.execCommand('copy');
  input.remove();
  if (!copied) throw new Error('浏览器拒绝了剪贴板写入');
}

async function loadSelectedDataDirectory(path?: string): Promise<void> {
  state.message = '正在读取所选目录…';
  render();
  try {
    const result = await window.desktopApi.chooseDataDirectory(path);
    if (!result.cancelled && result.data) {
      platformRecordCache.clear();
      state.data = result.data;
      state.dataImportOpen = false;
      state.dataImportPath = '';
      state.message = '';
      await loadRecords(true);
      await loadDataLibrary();
    } else {
      state.message = '';
      render();
    }
  } catch (error) {
    state.message = error instanceof Error ? error.message : String(error);
    render();
  }
}

function optionsForUpdatePlatform(platform: Platform, options: UpdateOptions): UpdateOptions {
  return {
    limit: platform === 'mcmod' ? options.mcmodLimit : options.limit,
    pages: undefined,
    mode: platform === 'mcmod' ? options.mode : options.otherMode,
  };
}

async function startUpdateBatchPlatform(platform: Platform): Promise<void> {
  const batch = state.updateBatch;
  if (!batch) return;
  state.updatePlatform = platform;
  try {
    await window.desktopApi.startUpdate(platform, optionsForUpdatePlatform(platform, batch.options));
  } catch (error) {
    state.updateBatch = null;
    state.message = error instanceof Error ? error.message : String(error);
    render();
  }
}

function inAppWindowForAction(element: HTMLElement): InAppWindowState | null {
  const windowId = element.dataset.windowId || element.closest<HTMLElement>('[data-window-id]')?.dataset.windowId || '';
  const windows = state.inAppWindows.length ? state.inAppWindows : (state.inAppWindow ? [state.inAppWindow] : []);
  return windows.find((win) => inAppWindowId(win) === windowId) || state.inAppWindow;
}

function closeInAppWindow(win: InAppWindowState | null): void {
  if (!win) return;
  const id = inAppWindowId(win);
  state.inAppWindows = state.inAppWindows.filter((item) => inAppWindowId(item) !== id);
  state.inAppWindow = state.inAppWindows.find((item) => !item.minimized) || state.inAppWindows[0] || null;
  if (!state.inAppWindows.length && state.inAppWindowPreviousSelected) {
    state.selected = state.inAppWindowPreviousSelected;
    state.inAppWindowPreviousSelected = null;
  }
}

async function handleAction(element: HTMLElement, event?: Event): Promise<void> {
  const action = element.dataset.action;
  if (isStaticSite() && ['open-in-app-window', 'open-native-subwindow'].includes(action || '')) {
    event?.preventDefault(); event?.stopPropagation();
    const url = element.dataset.url;
    if (url) await window.desktopApi.openExternal(url);
    return;
  }
  if (action === 'retry-cover') {
    event?.preventDefault();
    event?.stopPropagation();
    retryCoverImage(element as HTMLButtonElement);
  } else if (action === 'open-mcmod-trend') {
    event?.preventDefault();
    event?.stopPropagation();
    const recordId = element.dataset.recordId || '';
    const record = state.records.find((item) => item.id === recordId)
      || (state.selected?.id === recordId ? state.selected : null);
    if (!record || record.platform !== 'mcmod') return;
    state.trendChart = { record, range: 'all' };
    trendFocusAfterRender = 'close';
    render();
  } else if (action === 'set-mcmod-trend-range') {
    event?.preventDefault();
    event?.stopPropagation();
    const range = element.dataset.range;
    if (state.trendChart && MCMOD_TREND_RANGES.some((item) => item.value === range)) {
      state.trendChart.range = range as McmodTrendRange;
      render();
    }
  } else if (action === 'close-mcmod-trend') {
    if (element.classList.contains('mcmod-trend-backdrop') && event && event.target !== element) return;
    event?.preventDefault();
    event?.stopPropagation();
    closeMcmodTrendChart();
  } else if (action === 'open-personal-profile') {
    state.personalProfileOpen = true;
    profileFocusAfterRender = 'close';
    render();
    await loadFavoriteUpdates(true);
  } else if (action === 'mark-favorite-update-read') {
    const id = element.dataset.eventId;
    if (!id) return;
    try {
      state.favoriteUpdates = await window.desktopApi.markFavoriteUpdateRead(id);
      state.favoriteUpdatesError = '';
    } catch (error) {
      state.favoriteUpdatesError = error instanceof Error ? error.message : String(error);
    }
    render();
  } else if (action === 'close-personal-profile') {
    if (element.classList.contains('personal-profile-backdrop') && event && event.target !== element) return;
    state.personalProfileOpen = false;
    profileFocusAfterRender = 'trigger';
    render();
  } else if (action === 'toggle-update') {
    event?.preventDefault();
    event?.stopPropagation();
    state.updateOpen = !state.updateOpen;
    render();
  } else if (action === 'close-update-panel') {
    if (element.classList.contains('update-backdrop') && event && event.target !== element) return;
    event?.stopPropagation();
    state.updateOpen = false;
    render();
  } else if (action === 'close-data-import') {
    if (element.classList.contains('data-import-backdrop') && event && event.target !== element) return;
    state.dataImportOpen = false;
    state.dataImportPath = '';
    state.dataNotice = '';
    render();
  } else if (action === 'refresh-data-library') {
    await loadDataLibrary();
  } else if (action === 'open-data-directory') {
    try {
      const result = await window.desktopApi.openDataDirectory(element.dataset.snapshotId || undefined);
      state.message = result.opened ? '' : '无法打开数据目录。';
      state.dataNotice = result.opened ? `系统已接受打开请求：${result.path}` : '';
    } catch (error) {
      state.message = error instanceof Error ? error.message : String(error);
      state.dataNotice = '';
    }
    render();
  } else if (action === 'copy-data-path') {
    try {
      const value = element.dataset.path || '';
      await copyLocalPath(value);
      state.message = '';
      state.dataNotice = `已复制路径：${value}`;
    } catch (error) {
      state.message = error instanceof Error ? error.message : String(error);
      state.dataNotice = '';
    }
    render();
  } else if (action === 'export-active-data') {
    try {
      const result = await window.desktopApi.exportActiveData();
      state.dataExportPath = result.path;
      state.message = '';
    } catch (error) {
      state.message = error instanceof Error ? error.message : String(error);
    }
    render();
  } else if (action === 'activate-data-snapshot') {
    const snapshotId = element.dataset.snapshotId || '';
    if (!snapshotId || snapshotId === state.data?.snapshotId) return;
    state.message = '正在切换快照…';
    render();
    try {
      const result = await window.desktopApi.activateDataSnapshot(snapshotId);
      platformRecordCache.clear();
      state.data = result.data;
      state.message = '';
      await loadRecords(true);
      await loadDataLibrary();
    } catch (error) {
      state.message = error instanceof Error ? error.message : String(error);
      render();
    }
  } else if (action === 'delete-data-snapshot') {
    const snapshotId = element.dataset.snapshotId || '';
    if (!snapshotId || snapshotId === state.data?.snapshotId) return;
    if (!window.confirm(`删除快照 ${snapshotId}？\n\n它会被移到应用数据目录下的 trash 回收区，不会立即永久删除。`)) return;
    try {
      const result = await window.desktopApi.deleteDataSnapshot(snapshotId);
      state.dataLibrary = result.library;
      state.message = '';
      state.dataNotice = `已移到回收区：${result.archived.recoverablePath}`;
    } catch (error) {
      state.message = error instanceof Error ? error.message : String(error);
    }
    render();
  } else if (action === 'browse-data-import') {
    await loadSelectedDataDirectory();
  } else if (action === 'confirm-data-import') {
    const input = root.querySelector<HTMLInputElement>('#data-import-path');
    state.dataImportPath = input?.value.trim() || '';
    if (!state.dataImportPath) {
      state.message = '请先输入本地数据目录。';
      render();
      return;
    }
    await loadSelectedDataDirectory(state.dataImportPath);
  } else if (action === 'toggle-audit') {
    state.auditOpen = !state.auditOpen;
    if (state.auditOpen && !state.audit) await loadAudit();
    else render();
  } else if (action === 'retry-audit') {
    await loadAudit();
  } else if (action === 'close-audit') {
    if (element.classList.contains('audit-backdrop') && event && event.target !== element) return;
    state.auditOpen = false;
    render();
  } else if (action === 'open-compare') {
    if (compareEntries().length >= 2) {
      state.compareOpen = true;
      render();
    }
  } else if (action === 'close-compare') {
    if (element.classList.contains('compare-backdrop') && event && event.target !== element) return;
    state.compareOpen = false;
    render();
  } else if (action === 'clear-compare') {
    state.compareIds = [];
    state.compareOpen = false;
    render();
  } else if (action === 'retry-records') {
    await loadRecords(true);
  } else if (action === 'toggle-included-mod' && state.platform === 'mcmod') {
    const value = element.dataset.value || '';
    if (!value) return;
    state.includedMods = state.includedMods.includes(value) ? state.includedMods.filter((item) => item !== value) : [...state.includedMods, value];
    if (!state.includedMods.length) state.includedModsExclude = false;
    await loadRecords(true);
  } else if (action === 'toggle-included-mods-expanded' && state.platform === 'mcmod') {
    state.includedModsExpanded = !state.includedModsExpanded;
    render();
  } else if (action === 'clear-included-mod-search') {
    state.includedModSearch = '';
    platformFilterFocusAfterRender = 'included-mod-search';
    render();
  } else if (action === 'toggle-gameplay-category' && state.platform === 'curseforge') {
    const value = element.dataset.value || '';
    if (!value) return;
    state.gameplayCategories = state.gameplayCategories.includes(value) ? state.gameplayCategories.filter((item) => item !== value) : [...state.gameplayCategories, value];
    if (!state.gameplayCategories.length) state.gameplayCategoriesExclude = false;
    await loadRecords(true);
  } else if (action === 'toggle-gameplay-expanded' && state.platform === 'curseforge') {
    state.gameplayCategoriesExpanded = !state.gameplayCategoriesExpanded;
    render();
  } else if (action === 'clear-platform-facet') {
    if (state.platform === 'mcmod') {
      state.includedMods = [];
      state.includedModsExclude = false;
    } else if (state.platform === 'curseforge') {
      state.gameplayCategories = [];
      state.gameplayCategoriesExclude = false;
    } else return;
    await loadRecords(true);
  } else if (action === 'open-picker') {
    const pickerType = (element.dataset.picker || 'included-mod') as PickerType;
    state.openDropdown = '';
    state.pickerModal = {
      type: pickerType,
      search: '',
      limit: 300,
      sort: 'count_desc',
    };
    pickerFocusAfterRender = 'picker-modal-search';
    render();
  } else if (action === 'close-picker-modal') {
    if (element.classList.contains('picker-modal-backdrop') && event && event.target !== element) return;
    state.pickerModal = null;
    render();
    await loadRecords(true);
  } else if (action === 'clear-picker-search') {
    if (state.pickerModal) {
      state.pickerModal.search = '';
      pickerFocusAfterRender = 'picker-modal-search';
      render();
    }
  } else if (action === 'toggle-picker-item') {
    if (!state.pickerModal) return;
    const value = element.dataset.value || '';
    if (!value) return;
    if (state.pickerModal.type === 'included-mod') {
      state.includedMods = state.includedMods.includes(value)
        ? state.includedMods.filter((v) => v !== value)
        : [...state.includedMods, value];
      if (!state.includedMods.length) state.includedModsExclude = false;
    } else if (state.pickerModal.type === 'gameplay-category') {
      state.gameplayCategories = state.gameplayCategories.includes(value)
        ? state.gameplayCategories.filter((v) => v !== value)
        : [...state.gameplayCategories, value];
      if (!state.gameplayCategories.length) state.gameplayCategoriesExclude = false;
    } else if (state.pickerModal.type === 'category') {
      state.category = state.category === value ? '' : value;
    }
    render();
  } else if (action === 'picker-load-more') {
    if (state.pickerModal) {
      state.pickerModal.limit += 300;
      render();
    }
  } else if (action === 'picker-load-all') {
    if (state.pickerModal) {
      state.pickerModal.limit = 999999;
      render();
    }
  } else if (action === 'picker-reset-limit') {
    if (state.pickerModal) {
      state.pickerModal.limit = 300;
      render();
    }
  } else if (action === 'set-picker-sort') {
    if (state.pickerModal && element instanceof HTMLSelectElement) {
      state.pickerModal.sort = element.value as PickerSort;
      render();
    }
  } else if (action === 'picker-clear-selected') {
    if (!state.pickerModal) return;
    if (state.pickerModal.type === 'included-mod') {
      state.includedMods = [];
      state.includedModsExclude = false;
    } else if (state.pickerModal.type === 'gameplay-category') {
      state.gameplayCategories = [];
      state.gameplayCategoriesExclude = false;
    } else if (state.pickerModal.type === 'category') {
      state.category = '';
    }
    render();
  } else if (action === 'set-sticky-category') {
    const cat = element.dataset.category || '';
    if (state.category !== cat) {
      state.category = cat;
      void loadRecords(true);
    } else if (cat) {
      state.category = '';
      void loadRecords(true);
    }
  } else if (action === 'toggle-sticky-gameplay-category') {
    const cat = element.dataset.category || '';
    if (!cat) {
      state.gameplayCategories = [];
      state.gameplayCategoriesExclude = false;
    } else {
      state.gameplayCategories = state.gameplayCategories.includes(cat)
        ? state.gameplayCategories.filter((c) => c !== cat)
        : [...state.gameplayCategories, cat];
      if (!state.gameplayCategories.length) state.gameplayCategoriesExclude = false;
    }
    void loadRecords(true);
  } else if (action === 'clear-gameplay-categories') {
    state.gameplayCategories = [];
    state.gameplayCategoriesExclude = false;
    void loadRecords(true);
  } else if (action === 'clear-included-mods') {
    event?.stopPropagation();
    state.includedMods = [];
    state.includedModsExclude = false;
    void loadRecords(true);
  } else if (action === 'toggle-sticky-follow') {
    state.stickyFollowMode = !state.stickyFollowMode;
    render();
  } else if (action === 'toggle-sticky-mods-expanded') {
    state.stickyModsExpanded = !state.stickyModsExpanded;
    if (!state.stickyModsExpanded) {
      state.stickyModsExpandAll = false;
    }
    render();
  } else if (action === 'toggle-sticky-mods-expand-all') {
    state.stickyModsExpandAll = !state.stickyModsExpandAll;
    state.stickyModsExpanded = state.stickyModsExpandAll;
    render();
  } else if (action === 'toggle-sticky-categories-expanded') {
    state.stickyCategoriesExpanded = !state.stickyCategoriesExpanded;
    render();
  } else if (action === 'clear-sticky-mod-search') {
    state.stickyModSearch = '';
    stickyFocusAfterRender = 'sticky-mod-search';
    render();
  } else if (action === 'clear-sticky-cat-search') {
    state.stickyCatSearch = '';
    stickyFocusAfterRender = 'sticky-cat-search';
    render();
  } else if (action === 'scroll-to-top') {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  } else if (action === 'toggle-compare') {
    event?.stopPropagation();
    const index = Number(element.dataset.index || '-1');
    const record = state.records[index];
    if (!record) return;
    state.compareRecords[record.id] = record;
    state.compareIds = state.compareIds.includes(record.id) ? state.compareIds.filter((id) => id !== record.id) : [...state.compareIds, record.id];
    render();
  } else if (action === 'set-platform') {
    const nextPlatform = (element.dataset.platform || 'all') as FilterPlatform;
    if (state.platform === nextPlatform) return;
    state.platform = nextPlatform;
    state.expandedMcmodTableMods = '';
    state.stickyModsExpanded = false;
    state.stickyModsExpandAll = false;
    state.stickyCategoriesExpanded = false;
    state.stickyModSearch = '';
    state.stickyCatSearch = '';
    state.availableIncludedMods = [];
    state.availableGameplayCategories = [];
    state.pickerModal = null;
    if (state.platform !== 'all' && state.update?.state !== 'running') {
      state.updatePlatform = state.platform;
      state.updatePlatforms = [state.platform];
    }
    if (state.platform === 'all') state.sort = 'updated_desc';
    if (state.platform === 'bilibili' && !['updated_desc', 'views_desc', 'likes_desc', 'favs_desc', 'coins_desc', 'share_desc', 'reply_desc', 'danmaku_desc'].includes(state.sort)) state.sort = 'updated_desc';
    if (state.platform !== 'mcmod' && state.viewMode === 'table') state.viewMode = 'cards';
    state.selected = null;
    state.inAppWindowPreviousSelected = null;
    state.trendChart = null;
    state.imagePreview = null;
    state.compareOpen = false;
    state.comments = { sourceId: '', loading: false, available: false, pageCount: 0, comments: [], sourceFile: null, error: '' };

    const cached = !isStaticOverview() && isDefaultPlatformFilters() ? platformRecordCache.get(nextPlatform) : undefined;
    if (cached) {
      if (cached.bilibiliCounts) state.bilibiliCounts = cached.bilibiliCounts;
      state.records = [...cached.records];
      state.biliGroups = [...cached.biliGroups];
      state.total = cached.total;
      state.page = 1;
      const groupedBili = nextPlatform === 'bilibili' && state.biliViewMode === 'grouped';
      state.hasMore = groupedBili ? state.page * 48 < state.biliGroups.length : state.records.length < state.total;
      state.availableVersions = cached.availableVersions;
      state.availableLoaders = cached.availableLoaders;
      state.availableCategories = cached.availableCategories;
      state.availableCategoryCounts = cached.availableCategoryCounts || [];
      state.availableIncludedMods = cached.availableIncludedMods;
      state.availableGameplayCategories = cached.availableGameplayCategories;
      state.availablePans = cached.availablePans;
      state.loading = false;
      render();
    } else {
      await loadRecords(true);
    }
  } else if (action === 'choose-data') {
    state.dataImportOpen = true;
    state.dataImportPath = '';
    state.dataExportPath = '';
    state.dataNotice = '';
    state.message = '';
    render();
    await loadDataLibrary();
  } else if (action === 'toggle-dropdown') {
    const dropdown = element.dataset.dropdown as DropdownId | undefined;
    if (dropdown) state.openDropdown = state.openDropdown === dropdown ? '' : dropdown;
    render();
  } else if (action === 'select-dropdown') {
    const dropdown = element.dataset.dropdown as DropdownId | undefined;
    const value = element.dataset.value || '';
    state.openDropdown = '';
    if (dropdown === 'version') {
      state.version = value;
      await loadRecords(true);
    } else if (dropdown === 'loader') {
      state.loader = value;
      await loadRecords(true);
    } else if (dropdown === 'category') {
      state.category = value;
      await loadRecords(true);
    } else if (dropdown === 'pan') {
      state.pan = value;
      await loadRecords(true);
    } else if (dropdown === 'date') {
      state.dateRange = value;
      await loadRecords(true);
    } else if ((dropdown === 'sort' || dropdown === 'sticky-sort') && state.platform !== 'all') {
      state.sort = value;
      await loadRecords(true);
    } else if (dropdown === 'page-size' && state.platform !== 'all') {
      const pageSize = Number(value);
      if ([24, 48, 100].includes(pageSize)) {
        state.pageSize = pageSize;
        await loadRecords(true);
      }
    } else if (dropdown === 'personal') {
      state.personalFilter = value as PersonalFilter;
      await loadRecords(true);
    } else if (dropdown === 'update-platform' && ALL_PLATFORMS.includes(value as Platform)) {
      state.updatePlatform = value as Platform;
      render();
    }
  } else if (action === 'toggle-update-platform') {
    const platform = element.dataset.platform as Platform | undefined;
    if (!platform || !ALL_PLATFORMS.includes(platform) || state.update?.state === 'running') return;
    state.updatePlatforms = state.updatePlatforms.includes(platform)
      ? state.updatePlatforms.filter((item) => item !== platform)
      : [...state.updatePlatforms, platform];
    if (state.updatePlatforms.length) state.updatePlatform = state.updatePlatforms[0];
    render();
  } else if (action === 'select-all-update-platforms' && state.update?.state !== 'running') {
    state.updatePlatforms = [...ALL_PLATFORMS];
    render();
  } else if (action === 'clear-update-platforms' && state.update?.state !== 'running') {
    state.updatePlatforms = [];
    render();
  } else if (action === 'toggle-update-logs') {
    state.updateLogsExpanded = !state.updateLogsExpanded;
    render();
  } else if (action === 'start-update') {
    const platforms = [...state.updatePlatforms];
    if (!platforms.length) return;
    const validPositive = (value: string): boolean => /^\d+$/.test(value) && Number(value) >= 1 && Number(value) <= 100000;
    const oldMode = platforms.includes('mcmod') && state.mcmodUpdateMode !== 'new';
    const oldLimit = String(state.mcmodOldLimit);
    const otherLimit = state.updateOtherLimit.trim();
    state.updateFormError = oldMode && !validPositive(oldLimit) ? 'MC百科旧包数量须为 1–100000 的整数。'
      : platforms.some((platform) => platform !== 'mcmod') && otherLimit && !validPositive(otherLimit) ? '其他平台采集上限须为 1–100000 的整数。' : '';
    if (state.updateFormError) { render(); return; }
    state.logs = [];
    state.updateOpen = true;
    state.updateBatch = {
      queue: platforms.slice(1),
      total: platforms.length,
      completed: 0,
      options: {
        limit: otherLimit ? Number(otherLimit) : undefined,
        mcmodLimit: oldMode ? state.mcmodOldLimit : undefined,
        mode: state.mcmodUpdateMode,
        // Preserve the selected non-MC百科 mode. Dropping `catalog` here
        // silently turned a requested B站/CF catalog pass into the worker's
        // default `new` mode and its much smaller request budget.
        otherMode: state.otherUpdateMode,
      },
      handledTaskId: '',
    };
    render();
    await startUpdateBatchPlatform(platforms[0]);
    if (state.updateBatch) {
      state.updateOpen = false;
      render();
    }
  } else if (action === 'cancel-update') {
    if (state.updateBatch) state.updateBatch.queue = [];
    await window.desktopApi.cancelUpdate();
  } else if (action === 'load-more') {
    if (state.platform === 'bilibili' && state.biliViewMode === 'grouped') {
      state.page += 1;
      state.hasMore = state.page * 48 < state.biliGroups.length;
      render();
    } else {
      await loadRecords(false);
    }
  } else if (action === 'select-bili-member') {
    event?.stopPropagation();
    const record = recordForPersonalTarget(element);
    if (!record || record.platform !== 'bilibili') return;
    state.selected = record;
    state.imagePreview = null;
    state.comments = { sourceId: record.sourceId, loading: false, available: false, pageCount: 0, comments: [], sourceFile: null, error: '' };
    render();
    await loadComments(record);
  } else if (action === 'toggle-personal') {
    event?.stopPropagation();
    const record = recordForPersonalTarget(element);
    const field = element.dataset.personalField;
    if (!record || (field !== 'favorite' && field !== 'wantToPlay')) return;
    await savePersonalPatch(record, { [field]: !personalStatus(record)[field] } as PersonalPatch);
  } else if (action === 'set-personal-flag') {
    event?.stopPropagation();
    const record = recordForPersonalTarget(element) || state.selected;
    const field = element.dataset.personalField;
    if (!record || (field !== 'wantToPlay' && field !== 'played')) return;
    await savePersonalPatch(record, { [field]: !personalStatus(record)[field] } as PersonalPatch);
  } else if (action === 'set-personal-rating') {
    event?.stopPropagation();
    const record = recordForPersonalTarget(element) || state.selected;
    if (!record) return;
    const rating = Number(element.dataset.rating || '0');
    await savePersonalPatch(record, { rating: rating >= 1 && rating <= 5 ? rating : null });
  } else if (action === 'open-comment-preview') {
    event?.preventDefault();
    event?.stopPropagation();
    let record: DesktopRecord | null = null;
    const indexStr = element.dataset.index;
    if (indexStr !== undefined && indexStr !== '') {
      const idx = Number(indexStr);
      if (Number.isFinite(idx)) record = state.records[idx] || null;
    }
    if (!record && element.dataset.mid) {
      const mid = String(element.dataset.mid);
      record = state.records.find((r) => r.sourceId === mid || String((r.raw as { mid?: unknown })?.mid) === mid) || null;
    }
    if (!record && element.dataset.recordId) {
      record = state.records.find((r) => r.id === element.dataset.recordId) || null;
    }
    if (!record && element.dataset.sourceId && element.dataset.platform) {
      record = state.records.find((r) => r.platform === element.dataset.platform && r.sourceId === element.dataset.sourceId) || null;
    }
    if (!record && element.dataset.sourceId) {
      const sid = String(element.dataset.sourceId);
      record = state.records.find((r) => r.sourceId === sid || String((r.raw as { mid?: unknown; bvid?: unknown; project_id?: unknown; slug?: unknown })?.bvid) === sid || String((r.raw as { project_id?: unknown })?.project_id) === sid || String((r.raw as { slug?: unknown })?.slug) === sid) || null;
    }
    if (!record) {
      const card = element.closest<HTMLElement>('[data-index]');
      if (card && card.dataset.index !== undefined && card.dataset.index !== '') {
        const idx = Number(card.dataset.index);
        if (Number.isFinite(idx)) record = state.records[idx] || null;
      }
    }
    if (!record) record = state.selected;
    if (!record) return;
    state.commentPreviewRecord = record;
    state.commentPreviewQuery = '';
    state.commentPreviewTab = 'comments';
    render();
    await loadComments(record);
  } else if (action === 'open-in-app-window') {
    event?.preventDefault();
    event?.stopPropagation();
    const url = element.dataset.url;
    const title = element.dataset.title || '网页小窗';
    const recordId = element.dataset.recordId || '';
    const foundRecord = (recordId ? state.records.find((r) => r.id === recordId) : null)
      || state.selected
      || (url ? state.records.find((r) => r.url === url || (r.sourceId && url.includes(r.sourceId))) : null)
      || null;
    if (url) {
      if (!state.inAppWindows.length && state.inAppWindow) state.inAppWindows = [state.inAppWindow];
      if (!state.inAppWindows.length) state.inAppWindowPreviousSelected = state.selected || foundRecord;
      state.selected = null;
      state.trendChart = null;
      state.commentPreviewRecord = null;
      const viewportWidth = typeof window !== 'undefined' ? window.innerWidth : 1920;
      const existing = state.inAppWindows.find((win) => win.url === url && win.recordId === foundRecord?.id);
      const nextWindow: InAppWindowState = existing || {
        id: `web-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
        url,
        title,
        recordId: foundRecord?.id,
        record: foundRecord || undefined,
        contentTab: foundRecord && ['bilibili', 'curseforge', 'xyebbs'].includes(foundRecord.platform) ? 'overview' : 'web',
        maximized: false,
        activeTab: 'web',
        showChangelogPane: viewportWidth >= 1420,
        showPersonalPane: viewportWidth >= 1680,
      };
      nextWindow.minimized = false;
      if (!existing) state.inAppWindows.push(nextWindow);
      state.inAppWindow = nextWindow;
      if (foundRecord && ['mcmod', 'bbsmc', 'modrinth', 'curseforge', 'xyebbs'].includes(foundRecord.platform)) void loadPreviewVersions(foundRecord);
      render();
    }
  } else if (action === 'set-in-app-window-tab') {
    event?.preventDefault();
    event?.stopPropagation();
    const tab = element.dataset.tab as 'web' | 'changelog';
    if (state.inAppWindow && tab) {
      state.inAppWindow.activeTab = tab;
      state.inAppWindow.contentTab = tab === 'changelog' ? 'versions' : 'web';
      render();
    }
  } else if (action === 'in-app-content-tab' || action === 'retry-preview-versions') {
    event?.preventDefault();
    event?.stopPropagation();
    const win = inAppWindowForAction(element);
    const tab = action === 'retry-preview-versions' ? 'versions' : element.dataset.tab;
    if (win && (tab === 'overview' || tab === 'versions' || tab === 'gallery' || tab === 'web')) {
      win.contentTab = tab;
      const record = recordForInAppWindow(win);
      if (record && tab === 'versions') {
        if (action === 'retry-preview-versions') previewVersionCache.delete(record.id);
        void loadPreviewVersions(record);
      }
      render();
    }
  } else if (action === 'fetch-live-versions') {
    event?.preventDefault();
    event?.stopPropagation();
    const recordId = element.dataset.recordId;
    const targetRecord = (recordId && state.selected?.id === recordId)
      ? state.selected
      : (recordId ? (state.records.find((r) => r.id === recordId) || state.inAppWindows.find((w) => w.record?.id === recordId)?.record) : state.selected);
    if (targetRecord) {
      previewVersionCache.delete(targetRecord.id);
      void loadPreviewVersions(targetRecord);
      render();
    }
  } else if (action === 'more-in-app-versions') {
    event?.preventDefault();
    event?.stopPropagation();
    const recordId = element.dataset.recordId || '';
    if (recordId) {
      inAppVersionLimits.set(recordId, (inAppVersionLimits.get(recordId) || 30) + 30);
      render();
    }
  } else if (action === 'toggle-in-app-changelog') {
    event?.preventDefault();
    event?.stopPropagation();
    const win = inAppWindowForAction(element);
    if (win) {
      const current = win.showChangelogPane !== false;
      win.showChangelogPane = !current;
      render();
    }
  } else if (action === 'switch-in-app-source-pane') {
    event?.preventDefault();
    event?.stopPropagation();
    const win = inAppWindowForAction(element);
    const tab = element.dataset.sourceTab;
    const pane = element.closest<HTMLElement>('.in-app-changelog-pane');
    if (win && pane && (tab === 'source' || tab === 'versions' || (tab === 'mods' && recordForInAppWindow(win)?.platform === 'mcmod'))) {
      win.sourcePaneTab = tab;
      pane.querySelectorAll<HTMLElement>('[data-source-panel]').forEach((panel) => panel.toggleAttribute('hidden', panel.dataset.sourcePanel !== tab));
      pane.querySelectorAll<HTMLButtonElement>('.in-app-source-tabs button').forEach((button) => {
        const selected = button.dataset.sourceTab === tab;
        button.classList.toggle('is-active', selected);
        button.setAttribute('aria-selected', String(selected));
      });
      const title = pane.querySelector<HTMLElement>('.js-in-app-source-title');
      if (title) title.textContent = tab === 'mods' ? '🧩 已收录模组' : tab === 'source' ? '📄 来源资料' : '📋 版本历史';
      const count = pane.querySelector<HTMLElement>('.js-in-app-source-count');
      if (count) count.textContent = pane.querySelector<HTMLElement>(`.in-app-source-tabs [data-source-tab="${tab}"]`)?.dataset.count || '';
    }
  } else if (action === 'toggle-in-app-personal') {
    event?.preventDefault();
    event?.stopPropagation();
    const win = inAppWindowForAction(element);
    if (win) {
      const current = win.showPersonalPane !== false;
      win.showPersonalPane = !current;
      render();
    }
  } else if (action === 'switch-in-app-url') {
    event?.preventDefault();
    event?.stopPropagation();
    const url = element.dataset.url;
    const win = inAppWindowForAction(element);
    const title = element.dataset.title || win?.title || '网页小窗';
    if (url && win) {
      win.url = url;
      win.title = title;
      win.activeTab = 'web';
      win.contentTab = 'web';
      render();
    }
  } else if (action === 'minimize-in-app-window') {
    event?.preventDefault();
    event?.stopPropagation();
    const win = inAppWindowForAction(element);
    if (win) {
      win.minimized = true;
      state.inAppWindow = state.inAppWindows.find((item) => !item.minimized) || win;
      render();
    }
  } else if (action === 'restore-in-app-window') {
    event?.preventDefault();
    event?.stopPropagation();
    const win = inAppWindowForAction(element);
    if (win) {
      win.minimized = false;
      state.inAppWindow = win;
      render();
    }
  } else if (action === 'minimize-all-in-app-windows') {
    event?.preventDefault();
    event?.stopPropagation();
    state.inAppWindows.forEach((win) => { win.minimized = true; });
    render();
  } else if (action === 'close-in-app-window') {
    event?.preventDefault();
    event?.stopPropagation();
    if (event && event.target !== element && !element.classList.contains('in-app-close-btn') && !element.classList.contains('button') && !element.classList.contains('modal-backdrop')) return;
    closeInAppWindow(inAppWindowForAction(element));
    render();
    if (typeof window !== 'undefined' && window.desktopApi?.flushSession) {
      window.desktopApi.flushSession().catch(() => {});
    }
  } else if (action === 'open-native-subwindow') {
    event?.preventDefault();
    event?.stopPropagation();
    const win = inAppWindowForAction(element);
    const url = element.dataset.url || win?.url;
    const title = element.dataset.title || win?.title || '原站小窗';
    if (url && typeof window !== 'undefined' && window.desktopApi?.openInAppWindow) {
      window.desktopApi.openInAppWindow(url, title).catch(() => {});
    }
  } else if (action === 'toggle-maximize-in-app-window') {
    event?.preventDefault();
    event?.stopPropagation();
    const win = inAppWindowForAction(element);
    if (win) {
      win.maximized = !win.maximized;
      render();
    }
  } else if (action === 'reload-in-app-window') {
    event?.preventDefault();
    event?.stopPropagation();
    const container = element.closest<HTMLElement>('[data-window-id]');
    const frame = container?.querySelector<HTMLIFrameElement>('.js-in-app-frame') || root.querySelector<HTMLIFrameElement>('.js-in-app-frame');
    if (frame) {
      delete frame.dataset.requestStarted;
      delete frame.dataset.loaded;
      frame.src = frame.src;
      bindInAppFrame();
    }
  } else if (action === 'close-comment-preview') {
    if (event && event.target !== element && !element.classList.contains('modal-close') && !element.classList.contains('button')) return;
    state.commentPreviewRecord = null;
    state.commentPreviewQuery = '';
    state.commentPreviewTab = 'comments';
    render();
  } else if (action === 'open-detail-from-mod') {
    event?.stopPropagation();
    const mid = element.dataset.mid;
    const record = state.records.find((r) => r.sourceId === mid || String((r.raw as { mid?: unknown })?.mid) === mid);
    if (record) {
      state.selected = record;
      state.inAppWindowPreviousSelected = null;
      render();
      await loadComments(record);
    }
  } else if (action === 'toggle-mcmod-table-mods') {
    event?.preventDefault();
    event?.stopPropagation();
    const recordId = element.dataset.recordId || '';
    if (!recordId) return;
    state.expandedMcmodTableMods = state.expandedMcmodTableMods === recordId ? '' : recordId;
    mcmodTableFocusRecordId = recordId;
    render();
    if (state.expandedMcmodTableMods === recordId) {
      const record = state.records.find((item) => item.id === recordId);
      if (record?.platform === 'mcmod') {
        void ensureMcmodModIndex(record).then(() => {
          if (state.expandedMcmodTableMods !== recordId || !mcmodLiveModIndex.has(recordId)) return;
          const drawer = root.querySelector<HTMLElement>('.mcmod-table-mod-drawer');
          const oldList = drawer?.querySelector<HTMLElement>('.mcmod-full-mod-list.is-table');
          if (!oldList) return;
          const template = document.createElement('template');
          template.innerHTML = renderMcmodFullModList(record, 'table');
          const nextList = template.content.firstElementChild as HTMLElement | null;
          if (nextList) { oldList.replaceWith(nextList); bindMcmodModList(nextList); }
        });
      }
    }
  } else if (action === 'select-record') {
    const target = event?.target instanceof Element ? event.target : null;
    if (target && target !== element && target.closest('a,button,details,summary,.tag-mod,.mcmod-mod-cell,.mcmod-trend-trigger,.mcmod-comment-btn,.card-metric-comment,.compact-metric-comment,.bmb-comment-btn,.xyebbs-comment-btn')) return;
    const index = Number(element.dataset.index || '-1');
    state.selected = state.records[index] || null;
    detailFocusAfterRender = Boolean(state.selected);
    state.inAppWindowPreviousSelected = null;
    state.trendChart = null;
    state.imagePreview = null;
    state.comments = { sourceId: state.selected?.sourceId || '', loading: false, available: false, pageCount: 0, comments: [], sourceFile: null, error: '' };
    render();
    if (state.selected) await loadComments(state.selected);
  } else if (action === 'close-detail') {
    event?.preventDefault();
    event?.stopPropagation();
    if (element.classList.contains('detail-backdrop') && event && event.target !== element) return;
    state.selected = null;
    state.inAppWindowPreviousSelected = null;
    state.trendChart = null;
    state.imagePreview = null;
    state.comments = { sourceId: '', loading: false, available: false, pageCount: 0, comments: [], sourceFile: null, error: '' };
    render();
  } else if (action === 'open-image') {
    event?.stopPropagation();
    const url = safeImageUrl(element.dataset.imageUrl);
    if (!url) return;
    state.imagePreview = { url, title: element.dataset.imageTitle || '图片预览' };
    render();
  } else if (action === 'close-image') {
    if (element.classList.contains('image-lightbox') && event && event.target !== element) return;
    state.imagePreview = null;
    render();
  } else if (action === 'open-source') {
    event?.preventDefault();
    event?.stopPropagation();
    const url = element.dataset.url;
    if (url) await window.desktopApi.openExternal(url);
  } else if (action === 'quick-search') {
    state.query = element.dataset.query || '';
    await loadRecords(true);
  } else if (action === 'set-theme') {
    const next = element.dataset.theme;
    if (next === 'dark' || next === 'light' || next === 'eye' || next === 'warm' || next === 'pink') {
      document.documentElement.dataset.theme = next;
      localStorage.setItem('mcmod-desktop-theme', next);
      render();
    }
  } else if (action === 'toggle-theme') {
    const next = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
    document.documentElement.dataset.theme = next;
    localStorage.setItem('mcmod-desktop-theme', next);
    render();
  } else if (action === 'clear-query') {
    state.query = '';
    await loadRecords(true);
  } else if (action === 'clear-filters') {
    state.query = ''; state.version = ''; state.loader = ''; state.category = ''; state.includedMods = []; state.includedModsExclude = false; state.includedModSearch = ''; state.includedModsExpanded = false; state.gameplayCategories = []; state.gameplayCategoriesExclude = false; state.gameplayCategoriesExpanded = false; state.pan = ''; state.dateRange = ''; state.serverOnly = false; state.personalFilter = ''; state.sort = 'updated_desc'; await loadRecords(true);
  } else if (action === 'clear-filter') {
    const filter = element.dataset.filter;
    if (filter === 'query') state.query = '';
    if (filter === 'version') state.version = '';
    if (filter === 'loader') state.loader = '';
    if (filter === 'category') state.category = '';
    if (filter === 'pan') state.pan = '';
    if (filter === 'dateRange') state.dateRange = '';
    if (filter === 'serverOnly') state.serverOnly = false;
    if (filter === 'personalStatus') state.personalFilter = '';
    if (filter?.startsWith('includedMod:')) {
      state.includedMods = state.includedMods.filter((value) => value !== filter.slice('includedMod:'.length));
      if (!state.includedMods.length) state.includedModsExclude = false;
    }
    if (filter?.startsWith('gameplayCategory:')) {
      state.gameplayCategories = state.gameplayCategories.filter((value) => value !== filter.slice('gameplayCategory:'.length));
      if (!state.gameplayCategories.length) state.gameplayCategoriesExclude = false;
    }
    await loadRecords(true);
  } else if (action === 'set-view-mode') {
    const viewMode = element.dataset.viewMode;
    if (viewMode === 'cards' || viewMode === 'compact' || (viewMode === 'table' && state.platform === 'mcmod')) {
      state.viewMode = viewMode;
      if (viewMode !== 'table') state.expandedMcmodTableMods = '';
      render();
    }
  } else if (action === 'set-bili-content') {
    const mode = element.dataset.content;
    if (mode === 'all' || mode === 'excluded' || mode === 'candidates' || mode === 'secondary') {
      state.bilibiliContent = mode;
      await loadRecords(true);
    }
  } else if (action === 'set-bili-view-mode') {
    const viewMode = element.dataset.biliViewMode;
    if (viewMode === 'grouped' || viewMode === 'flat') {
      state.biliViewMode = viewMode;
      await loadRecords(true);
    }
  }
}

async function loadRecords(reset = true, backgroundRevalidate = false): Promise<void> {
  const requestId = ++activeLoadRequestId;
  if (isStaticOverview()) {
    state.page = 1;
    state.records = [];
    state.biliGroups = [];
    state.total = ALL_PLATFORMS.reduce((sum, platform) => sum + (state.data?.platforms[platform]?.count || 0), 0);
    state.hasMore = false;
    state.loading = false;
    state.recordsError = '';
    state.availableVersions = [];
    state.availableLoaders = [];
    state.availableCategories = [];
    state.availableCategoryCounts = [];
    state.availableIncludedMods = [];
    state.availableGameplayCategories = [];
    state.availablePans = [];
    render();
    return;
  }
  if (reset) {
    state.page = 1;
    if (!backgroundRevalidate) {
      state.records = [];
      state.biliGroups = [];
    }
  } else {
    state.page += 1;
  }
  if (!backgroundRevalidate) {
    state.loading = true;
    state.recordsError = '';
    render();
  }
  const platforms = state.platform === 'all' ? ALL_PLATFORMS : [state.platform];
  const groupedBili = state.platform === 'bilibili' && state.biliViewMode === 'grouped';
  const requestPageSize = groupedBili ? 2000 : state.platform === 'all' ? 12 : state.pageSize;
  try {
    const getOptions = (page: number) => ({
      query: state.query,
      version: state.version,
      loader: state.loader,
      category: state.platform === 'curseforge' ? '' : state.category,
      includedMods: state.platform === 'mcmod' ? state.includedMods : [],
      includedModsExclude: state.platform === 'mcmod' && state.includedModsExclude,
      gameplayCategories: state.platform === 'curseforge' ? state.gameplayCategories : [],
      gameplayCategoriesExclude: state.platform === 'curseforge' && state.gameplayCategoriesExclude,
      pan: state.pan,
      dateRange: state.dateRange,
      serverOnly: state.serverOnly,
      personalStatus: groupedBili ? '' : state.personalFilter,
      bilibiliContent: state.bilibiliContent,
      sort: state.platform === 'all' ? 'updated_desc' : state.sort,
      page,
      pageSize: requestPageSize,
    });
    const requestPlatform = async (platform: Platform, page: number) => {
      const result = await window.desktopApi.getPlatformRecords(platform, getOptions(page));
      if (result.error) throw new Error(result.error);
      return result;
    };
    let results: Awaited<ReturnType<typeof window.desktopApi.getPlatformRecords>>[];
    if (groupedBili) {
      const first = await requestPlatform('bilibili', 1);
      results = [first];
      const pageCount = Math.ceil(first.total / Math.max(first.pageSize, 1));
      if (pageCount > 1) {
        const remaining = Array.from({ length: pageCount - 1 }, (_, i) => i + 2);
        const more = await Promise.all(remaining.map((page) => requestPlatform('bilibili', page)));
        results.push(...more);
      }
    } else {
      const settled = await Promise.allSettled(platforms.map((platform) => requestPlatform(platform, state.page)));
      const failures = settled.flatMap((result, index) => result.status === 'rejected'
        ? [`${PLATFORM_CONFIGS[platforms[index]].name}：${result.reason instanceof Error ? result.reason.message : String(result.reason)}`]
        : []);
      results = settled.flatMap((result) => result.status === 'fulfilled' ? [result.value] : []);
      if (!results.length) throw new Error(failures.join('；') || '所有平台请求均失败');
      if (failures.length) state.recordsError = `部分平台加载失败；已保留其他平台结果。${failures.join('；')}`;
    }
    if (requestId !== activeLoadRequestId) return;
    const counts = results.find(result => result.bilibiliCounts)?.bilibiliCounts;
    if (counts) state.bilibiliCounts = counts;
    const nextRecords = results.flatMap((result) => result.records);
    state.records = reset ? nextRecords : [...state.records, ...nextRecords];
    for (const record of nextRecords) state.compareRecords[record.id] = record;
    const groupedResults = groupedBili ? buildBilibiliGroups(state.records) : [];
    state.biliGroups = groupedBili
      ? filterBilibiliGroupsByPersonalStatus(groupedResults, state.personalLibrary, state.personalFilter)
      : [];
    state.total = groupedBili ? (results[0]?.total || 0) : results.reduce((sum, result) => sum + result.total, 0);
    state.availableVersions = [...new Set(results.flatMap((result) => result.availableVersions || []))].sort((a, b) => a.localeCompare(b, 'zh-CN'));
    state.availableLoaders = [...new Set(results.flatMap((result) => result.availableLoaders || []))].sort((a, b) => a.localeCompare(b, 'zh-CN'));
    state.availableCategories = [...new Set(results.flatMap((result) => result.availableCategories || []))].sort((a, b) => a.localeCompare(b, 'zh-CN'));
    const catCountMap = new Map<string, number>();
    for (const result of results) {
      for (const item of (result.availableCategoryCounts || [])) {
        catCountMap.set(item.value, (catCountMap.get(item.value) || 0) + (item.count ?? 0));
      }
    }
    if (catCountMap.size > 0) {
      state.availableCategoryCounts = [...catCountMap.entries()]
        .map(([value, count]) => ({ value, count }))
        .sort((a, b) => b.count - a.count || a.value.localeCompare(b.value, 'zh-CN'));
    }
    state.availableIncludedMods = state.platform === 'mcmod' ? (results[0]?.availableIncludedMods || []) : [];
    state.availableGameplayCategories = state.platform === 'curseforge' ? (results[0]?.availableGameplayCategories || []) : [];
    state.availablePans = [...new Set(results.flatMap((result) => result.availablePans || []))];
    state.hasMore = !state.recordsError && (groupedBili ? state.page * 48 < state.biliGroups.length : state.records.length < state.total);
    state.loading = false;

    if (reset && isDefaultPlatformFilters()) {
      platformRecordCache.set(state.platform, {
        bilibiliCounts: state.bilibiliCounts,
        records: state.records,
        biliGroups: state.biliGroups,
        total: state.total,
        availableVersions: state.availableVersions,
        availableLoaders: state.availableLoaders,
        availableCategories: state.availableCategories,
        availableCategoryCounts: state.availableCategoryCounts,
        availableIncludedMods: state.availableIncludedMods,
        availableGameplayCategories: state.availableGameplayCategories,
        availablePans: state.availablePans,
      });
    }
    render();
  } catch (error) {
    if (requestId !== activeLoadRequestId) return;
    state.loading = false;
    state.hasMore = false;
    state.recordsError = error instanceof Error ? error.message : String(error);
    render();
  }
}

let documentEventsBound = false;

function bindDocumentEvents(): void {
  if (documentEventsBound) return;
  documentEventsBound = true;
  if (isStaticSite()) document.addEventListener('mc-pages-load-progress', (event) => {
    const detail = (event as CustomEvent<{ platform: Platform; phase: string; completed: number; total: number }>).detail;
    if (!detail || !ALL_PLATFORMS.includes(detail.platform)) return;
    pagesLoadProgress.set(detail.platform, detail);
    root.querySelectorAll<HTMLElement>(`[data-pages-source-state="${detail.platform}"]`).forEach((element) => { element.textContent = pagesSourceLoadLabel(detail.platform); });
    root.querySelectorAll<HTMLElement>('.pages-loading-progress').forEach((element) => { element.textContent = pagesLoadingMessage(); });
  });
  document.addEventListener('load', (event) => {
    const image = event.target instanceof HTMLImageElement ? event.target : null;
    if (!image || image.dataset.coverImage !== 'true') return;
    handleCoverImageLoad(image);
  }, true);
  document.addEventListener('error', (event) => {
    const image = event.target instanceof HTMLImageElement ? event.target : null;
    if (!image) return;
    if (image.dataset.coverImage === 'true') {
      handleCoverImageFailure(image, 'error');
      return;
    }
    const original = safeImageUrl(image.dataset.originalSrc);
    const fallback = safeImageUrl(image.dataset.fallbackSrc);
    if (!original || !fallback) return;
    rememberFailedImage(original);
    if (image.getAttribute('src') === fallback) return;
    image.setAttribute('src', fallback);
    image.closest<HTMLElement>('.image-preview-trigger')?.setAttribute('data-image-url', fallback);
  }, true);
  document.addEventListener('click', (event) => {
    if (!state.openDropdown) return;
    const target = event.target instanceof Element ? event.target : null;
    if (!target?.closest('.ui-dropdown')) {
      state.openDropdown = '';
      render();
    }
  });
  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    if (state.trendChart) {
      closeMcmodTrendChart();
    } else if (state.inAppWindows.some((win) => !win.minimized) || (state.inAppWindow && !state.inAppWindow.minimized)) {
      const visible = state.inAppWindows.filter((win) => !win.minimized);
      if (visible.length) visible.forEach((win) => { win.minimized = true; });
      else if (state.inAppWindow) state.inAppWindow.minimized = true;
      render();
    } else if (state.commentPreviewRecord) {
      state.commentPreviewRecord = null;
      state.commentPreviewTab = 'comments';
      render();
    } else if (state.imagePreview) {
      state.imagePreview = null;
      render();
    } else if (state.trendChart) {
      state.trendChart = null;
      trendFocusAfterRender = 'trigger';
      render();
    } else if (state.pickerModal) {
      state.pickerModal = null;
      render();
      void loadRecords(true);
    } else if (state.updateOpen) {
      state.updateOpen = false;
      render();
    } else if (state.dataImportOpen) {
      state.dataImportOpen = false;
      state.dataImportPath = '';
      render();
    } else if (state.auditOpen) {
      state.auditOpen = false;
      render();
    } else if (state.compareOpen) {
      state.compareOpen = false;
      render();
    } else if (state.personalProfileOpen) {
      state.personalProfileOpen = false;
      profileFocusAfterRender = 'trigger';
      render();
    } else if (state.selected) {
      state.selected = null;
      render();
    } else if (state.openDropdown) {
      state.openDropdown = '';
      render();
    }
  });
  window.addEventListener('scroll', () => {
    const bar = document.querySelector('.desktop-sticky-bar');
    if (!bar) return;
    const isScrolled = window.scrollY > 30;
    if (isScrolled !== bar.classList.contains('is-scrolled')) {
      bar.classList.toggle('is-scrolled', isScrolled);
    }
  }, { passive: true });
}

async function warmupPlatformCache(): Promise<void> {
  if (isStaticSite()) return;
  const currentSnapshotId = state.data?.snapshotId;
  for (const platform of ALL_PLATFORMS) {
    if (platformRecordCache.has(platform)) continue;
    if (state.data?.snapshotId !== currentSnapshotId) return;
    try {
      const groupedBili = platform === 'bilibili' && state.biliViewMode === 'grouped';
      const requestPageSize = groupedBili ? 2000 : state.pageSize;
      const result = await window.desktopApi.getPlatformRecords(platform, {
        query: '',
        version: '',
        loader: '',
        category: '',
        includedMods: [],
        includedModsExclude: false,
        gameplayCategories: [],
        gameplayCategoriesExclude: false,
        pan: '',
        dateRange: '',
        serverOnly: false,
        personalStatus: '',
        bilibiliContent: 'candidates',
        sort: 'updated_desc',
        page: 1,
        pageSize: requestPageSize,
      });
      if (result.records && !result.error && state.data?.snapshotId === currentSnapshotId) {
        const biliGroups = groupedBili ? buildBilibiliGroups(result.records) : [];
        platformRecordCache.set(platform, {
          bilibiliCounts: result.bilibiliCounts,
          records: result.records,
          biliGroups,
          total: result.total,
          availableVersions: result.availableVersions || [],
          availableLoaders: result.availableLoaders || [],
          availableCategories: result.availableCategories || [],
          availableCategoryCounts: result.availableCategoryCounts || [],
          availableIncludedMods: result.availableIncludedMods || [],
          availableGameplayCategories: result.availableGameplayCategories || [],
          availablePans: result.availablePans || [],
        });
      }
    } catch {}
  }
}

export async function initDesktopShell(): Promise<void> {
  root = document.querySelector<HTMLElement>('#desktop-root')!;
  bindDocumentEvents();
  const savedTheme = localStorage.getItem('mcmod-desktop-theme');
  if (savedTheme === 'light' || savedTheme === 'dark' || savedTheme === 'eye' || savedTheme === 'warm' || savedTheme === 'pink') document.documentElement.dataset.theme = savedTheme;
  else document.documentElement.dataset.theme = 'light';
  render();
  try {
    const initial = await window.desktopApi.getState();
    state.data = initial.data;
    state.update = initial.update;
    await loadPersonalLibrary();
    await loadFavoriteUpdates(false);
    await loadRecords();
    void warmupPlatformCache();
  } catch (error) {
    state.loading = false;
    state.message = error instanceof Error ? error.message : String(error);
    render();
  }
  window.desktopApi.onUpdateStatus((update) => {
    state.update = update;
    if (update.platform) state.updatePlatform = update.platform;
    state.logs = update.logs || state.logs;
    if (state.updateOpen) render();
    else refreshUpdateDock();
    if (update.state === 'success') {
      let nextPlatform: Platform | undefined;
      const batch = state.updateBatch;
      if (batch && update.taskId && batch.handledTaskId !== update.taskId) {
        batch.handledTaskId = update.taskId;
        batch.completed += 1;
        nextPlatform = batch.queue.shift();
        if (!nextPlatform) state.updateBatch = null;
      }
      platformRecordCache.clear();
      void window.desktopApi.getState().then(async (next) => {
        state.data = next.data;
        await loadPersonalLibrary();
        await loadFavoriteUpdates(false);
        await loadRecords(true);
        void warmupPlatformCache();
      });
      if (nextPlatform) window.setTimeout(() => void startUpdateBatchPlatform(nextPlatform!), 0);
    } else if ((update.state === 'failed' || update.state === 'cancelled') && state.updateBatch) {
      state.updateBatch = null;
      if (state.updateOpen) render();
    }
    refreshUpdateDock();
  });
  window.desktopApi.onUpdateLog((line) => {
    state.logs = [...state.logs, line].slice(-200);
    if (state.updateOpen) render();
  });
  window.desktopApi.onDataChanged((data) => {
    platformRecordCache.clear();
    state.data = data;
    void loadPersonalLibrary().then(async () => {
      await loadFavoriteUpdates(false);
      await loadRecords(true);
      void warmupPlatformCache();
    });
  });
}

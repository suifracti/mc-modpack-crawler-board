import { ALL_PLATFORMS, PLATFORM_CONFIGS } from './data/platformRegistry';
import { groupBilibiliPacks } from './domain/bilibiliGrouping';
import type { Platform } from './domain/types';
import { buildVersionModalViewModel } from './modals/version/buildViewModel';
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

export interface DesktopRecord {
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

export interface PersonalStatus {
  favorite: boolean;
  wantToPlay: boolean;
  played: boolean;
  rating: number | null;
  note: string;
  updatedAt: string | null;
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
  platforms: Record<Platform, DesktopPlatformState>;
}

export interface DesktopRecordQuery {
  query?: string;
  version?: string;
  loader?: string;
  category?: string;
  pan?: string;
  dateRange?: string;
  serverOnly?: boolean;
  personalStatus?: PersonalFilter;
  sort?: string;
  page?: number;
  pageSize?: number;
}

export interface DesktopUpdateStatus {
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
  getState: () => Promise<{ data: DesktopDataState; update: DesktopUpdateStatus }>;
  getPersonalLibrary: () => Promise<{ schema: number; entries: Record<string, PersonalStatus> }>;
  updatePersonalStatus: (platform: Platform, sourceId: string, patch: Partial<Pick<PersonalStatus, 'favorite' | 'wantToPlay' | 'played' | 'rating' | 'note'>>) => Promise<{ key: string; status: PersonalStatus }>;
  getAuditDiff: () => Promise<DesktopAuditResult>;
  getPlatformRecords: (platform: Platform, options?: DesktopRecordQuery) => Promise<{ platform: Platform; total: number; page: number; pageSize: number; records: DesktopRecord[]; availableVersions: string[]; availableLoaders: string[]; availableCategories: string[]; availablePans: string[]; error?: string | null }>;
  getPlatformComments: (platform: Platform, sourceId: string) => Promise<DesktopCommentsResult>;
  chooseDataDirectory: () => Promise<{ cancelled: boolean; data?: DesktopDataState }>;
  startUpdate: (platform: Platform, options?: { limit?: number; pages?: number; until?: string }) => Promise<DesktopUpdateStatus>;
  cancelUpdate: () => Promise<{ cancelled: boolean; reason?: string }>;
  openExternal: (url: string) => Promise<{ opened: boolean }>;
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
type DropdownId = 'version' | 'loader' | 'category' | 'pan' | 'date' | 'sort' | 'page-size' | 'personal' | 'update-platform';
type ViewMode = 'cards' | 'compact' | 'table';
type BiliViewMode = 'grouped' | 'flat';

const UNKNOWN_LOCAL_TEXT = '未知（本地数据未提供）';

export function getDesktopSearchPlaceholder(platform: FilterPlatform): string {
  if (platform === 'all') return '输入名称、版本、作者或平台已有字段…';
  if (platform === 'mcmod') return '输入名称、模组名、版本、作者或当前平台已有字段…';
  return '输入名称、版本、作者或当前平台已有字段…';
}

const PLATFORM_SITE_ICONS: Record<Platform, string> = {
  mcmod: 'https://www.mcmod.cn/favicon.ico',
  bilibili: 'https://www.bilibili.com/favicon.ico',
  bbsmc: 'https://bbsmc.net/favicon.ico',
  xyebbs: 'https://www.xyebbs.com/favicon.ico',
  modrinth: 'https://modrinth.com/favicon.ico',
  curseforge: 'https://www.curseforge.com/favicon.ico',
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
  mcmod: 'data:image/svg+xml;charset=utf-8,%3Csvg xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22 width%3D%22400%22 height%3D%22225%22 viewBox%3D%220 0 400 225%22%3E%3Crect width%3D%22400%22 height%3D%22225%22 fill%3D%22%23fff7e6%22%2F%3E%3Ctext x%3D%2250%25%22 y%3D%2250%25%22 dominant-baseline%3D%22middle%22 text-anchor%3D%22middle%22 fill%3D%22%23b66c2a%22 font-family%3D%22sans-serif%22 font-size%3D%2216%22%3EMC%E7%99%BE%E7%A7%91%20%E6%9A%82%E6%97%A0%E5%B0%81%E9%9D%A2%3C%2Ftext%3E%3C%2Fsvg%3E',
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
  pan: '',
  dateRange: '',
  serverOnly: false,
  personalFilter: '' as PersonalFilter,
  sort: 'updated_desc',
  viewMode: 'cards' as ViewMode,
  biliViewMode: 'grouped' as BiliViewMode,
  biliGroups: [] as BiliGroup[],
  records: [] as DesktopRecord[],
  total: 0,
  availableVersions: [] as string[],
  availableLoaders: [] as string[],
  availableCategories: [] as string[],
  availablePans: [] as string[],
  page: 1,
  pageSize: 24,
  hasMore: false,
  openDropdown: '' as DropdownId | '',
  updatePlatform: 'bilibili' as Platform,
  selected: null as DesktopRecord | null,
  imagePreview: null as { url: string; title: string } | null,
  audit: null as DesktopAuditResult | null,
  auditOpen: false,
  compareOpen: false,
  compareIds: [] as string[],
  compareRecords: {} as Record<string, DesktopRecord>,
  personalLibrary: {} as Record<string, PersonalStatus>,
  comments: { sourceId: '', loading: false, available: false, pageCount: 0, comments: [] as DesktopComment[], sourceFile: null as string | null, error: '' },
  loading: true,
  message: '',
  logs: [] as string[],
};

let root: HTMLElement;
let searchTimer: number | undefined;
let personalNoteTimer: number | undefined;

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

function renderPersonalCardActions(record: DesktopRecord, index: number): string {
  if (!isPersonalWritable(record)) {
    return `<div class="personal-card-actions personal-unavailable" title="${esc(personalUnavailableReason(record))}"><span>个人标记不可保存：缺少稳定来源 ID</span></div>`;
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
  return `<div class="personal-card-actions"><button type="button" class="personal-favorite-button ${status.favorite ? 'is-active' : ''}" data-action="toggle-personal" data-personal-field="favorite" data-index="${index}" ${personalTargetAttributes(record)} aria-pressed="${status.favorite}" title="${title}">${label}</button>${status.rating ? `<span class="personal-rating-mini">★ ${status.rating}/5</span>` : ''}${labels}</div>`;
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
  return `<div class="detail-section personal-detail-section"><div class="personal-detail-heading"><div><h3>我的整合包库</h3><span class="detail-submeta">仅保存在本机，不会写入平台采集数据</span></div><button type="button" class="personal-favorite-button ${status.favorite ? 'is-active' : ''}" data-action="toggle-personal" data-personal-field="favorite" data-index="${state.records.indexOf(record)}" ${personalTargetAttributes(record)} aria-pressed="${status.favorite}">${currentVideoLabels.favorite}</button></div><div class="personal-flag-row"><button type="button" class="personal-flag-button ${status.wantToPlay ? 'is-active' : ''}" data-action="set-personal-flag" data-personal-field="wantToPlay" ${personalTargetAttributes(record)} aria-pressed="${status.wantToPlay}">${currentVideoLabels.wantToPlay}</button><button type="button" class="personal-flag-button ${status.played ? 'is-active' : ''}" data-action="set-personal-flag" data-personal-field="played" ${personalTargetAttributes(record)} aria-pressed="${status.played}">✓ 玩过</button></div><div class="personal-rating-row"><span>个人评分</span><div class="personal-rating-buttons">${ratingButtons.replaceAll('data-action="set-personal-rating"', `data-action="set-personal-rating" ${personalTargetAttributes(record)}`)}<button type="button" class="personal-rating-clear" data-action="set-personal-rating" data-rating="0" ${personalTargetAttributes(record)}>清除</button></div></div><label class="personal-note-label" for="personal-note">个人备注</label><textarea id="personal-note" class="personal-note-input" data-personal-note ${personalTargetAttributes(record)} maxlength="20000" placeholder="写下安装、游玩或更新备注…">${esc(status.note)}</textarea><span class="personal-note-hint">停止输入后自动保存</span></div>`;
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
  const text = String(value ?? '').trim();
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

function recordCoverUrl(record: DesktopRecord): string {
  return recordRealCoverUrl(record) || PLATFORM_COVER_FALLBACKS[record.platform];
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
  const status = personalStatus(record);
  const target = personalTargetAttributes(record);
  const targetLabel = `<span class="bili-personal-target">当前视频：${esc(record.title)} · BVID ${esc(record.sourceId)}</span>`;
  if (!isPersonalWritable(record)) {
    return `<div class="bili-personal-actions personal-unavailable">${targetLabel}<span>${esc(personalUnavailableReason(record))}</span></div>`;
  }
  return `<div class="bili-personal-actions">${targetLabel}<button type="button" class="personal-favorite-button ${status.favorite ? 'is-active' : ''}" data-action="toggle-personal" data-personal-field="favorite" ${target} aria-pressed="${status.favorite}">${status.favorite ? '★ 取消收藏当前视频' : '☆ 收藏当前视频'}</button><button type="button" class="personal-flag-button ${status.wantToPlay ? 'is-active' : ''}" data-action="toggle-personal" data-personal-field="wantToPlay" ${target} aria-pressed="${status.wantToPlay}">${status.wantToPlay ? '取消想玩当前视频' : '加入想玩（保存视频线索）'}</button></div>`;
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
  return `<div class="bili-personal-summary"><div class="bili-personal-summary-head"><strong>个人状态摘要</strong><span>${marked.length ? `已标记 ${marked.length}/${group.items.length} 个成员` : `暂无成员标记`} · 范围：${scope}</span></div>${memberButtons ? `<div class="bili-personal-members">${memberButtons}</div>` : '<span class="bili-personal-summary-empty">组状态按视频保存；评分和备注不会折叠为组值。</span>'}</div>`;
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
  if (record.platform === 'bbsmc') return renderBbsmcCard(base as unknown as BbsmcPack);
  if (record.platform === 'xyebbs') return renderXyebbsCard(base as unknown as XyebbsPack);
  if (record.platform === 'modrinth') return renderModrinthCard(base as unknown as ModrinthPack);
  if (record.platform === 'curseforge') return renderCurseforgeCard(base as unknown as CurseforgePack);
  return renderRecord(record, state.records.indexOf(record));
}

function renderImageButton(url: string, title: string, className = ''): string {
  const safeUrl = safeImageUrl(url);
  if (!safeUrl) return '';
  return `<button type="button" class="image-preview-trigger ${className}" data-action="open-image" data-image-url="${esc(safeUrl)}" data-image-title="${esc(title)}" title="点击查看${esc(title)}"><img src="${esc(safeUrl)}" alt="${esc(title)}" loading="lazy" referrerpolicy="no-referrer"></button>`;
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
  return `<div class="ui-dropdown ${isOpen ? 'is-open' : ''}" data-dropdown-root="${id}">
    <button type="button" class="ui-dropdown-trigger" data-action="toggle-dropdown" data-dropdown="${id}" aria-haspopup="listbox" aria-expanded="${isOpen}" ${disabled ? 'disabled' : ''}><span>${esc(selectedOption?.label || '')}</span><span class="ui-dropdown-chevron" aria-hidden="true">⌄</span></button>
    <div class="ui-dropdown-menu" id="${id}-menu" role="listbox" aria-label="${esc(selectedOption?.label || '')}">${options.map((option) => `<button type="button" class="ui-dropdown-option ${option.value === selected ? 'is-selected' : ''}" data-action="select-dropdown" data-dropdown="${id}" data-value="${esc(option.value)}" role="option" aria-selected="${option.value === selected}">${esc(option.label)}</button>`).join('')}</div>
  </div>`;
}

function renderFilterDropdown(id: 'version' | 'loader' | 'category' | 'pan', values: string[], selected: string, emptyLabel: string): string {
  return renderDropdown(id, selected, [{ value: '', label: emptyLabel }, ...values.map((value) => ({ value, label: value }))]);
}

function renderSortDropdown(): string {
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
  return renderDropdown('sort', state.sort, options);
}

function renderDateDropdown(): string {
  return renderDropdown('date', state.dateRange, [
    { value: '', label: '全部时间' },
    { value: '7d', label: '近 7 天' },
    { value: '30d', label: '近 30 天' },
    { value: '90d', label: '近 90 天' },
  ]);
}

function renderPersonalDropdown(): string {
  return renderDropdown('personal', state.personalFilter, [
    { value: '', label: '全部个人状态' },
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
  if (state.category) filters.push({ key: 'category', label: `分类：${state.category}` });
  if (state.pan) filters.push({ key: 'pan', label: `渠道：${panLabel(state.pan)}` });
  if (state.dateRange) filters.push({ key: 'dateRange', label: `时间：${state.dateRange}` });
  if (state.serverOnly) filters.push({ key: 'serverOnly', label: '有服务端运行线索' });
  if (state.personalFilter) filters.push({ key: 'personalStatus', label: state.personalFilter === 'favorite' ? '个人：已收藏' : state.personalFilter === 'want_to_play' ? '个人：想玩' : '个人：玩过' });
  if (!filters.length) return '';
  return `<div class="desktop-active-filters" aria-label="当前筛选条件">${filters.map((filter) => `<button type="button" class="desktop-active-filter" data-action="clear-filter" data-filter="${esc(filter.key)}">${esc(filter.label)} <span aria-hidden="true">×</span></button>`).join('')}<button type="button" class="desktop-active-clear" data-action="clear-filters">清空全部</button></div>`;
}

function renderFilterControls(includeDataButton = false): string {
  const isAllPlatform = state.platform === 'all';
  const viewButtons = state.platform === 'bilibili'
    ? `<button type="button" class="desktop-view-button ${state.biliViewMode === 'grouped' ? 'is-active' : ''}" data-action="set-bili-view-mode" data-bili-view-mode="grouped">同包聚合</button><button type="button" class="desktop-view-button ${state.biliViewMode === 'flat' ? 'is-active' : ''}" data-action="set-bili-view-mode" data-bili-view-mode="flat">视频平铺</button>`
    : `<button type="button" class="desktop-view-button ${state.viewMode === 'cards' ? 'is-active' : ''}" data-action="set-view-mode" data-view-mode="cards">卡片</button><button type="button" class="desktop-view-button ${state.viewMode === 'compact' ? 'is-active' : ''}" data-action="set-view-mode" data-view-mode="compact">紧凑</button>${state.platform === 'mcmod' ? `<button type="button" class="desktop-view-button ${state.viewMode === 'table' ? 'is-active' : ''}" data-action="set-view-mode" data-view-mode="table">表格</button>` : ''}`;
  return `<div class="desktop-filter-dock desktop-filter-dock-rich">
    <span class="filter-label">版本</span>${renderFilterDropdown('version', state.availableVersions, state.version, '全部版本')}
    <span class="filter-label">Loader</span>${renderFilterDropdown('loader', state.availableLoaders, state.loader, '全部 Loader')}
    <span class="filter-label">分类</span>${renderFilterDropdown('category', state.availableCategories, state.category, '全部分类')}
    <span class="filter-label">渠道</span>${renderFilterDropdown('pan', state.availablePans, state.pan, '全部渠道')}
    <span class="filter-label">时间</span>${renderDateDropdown()}
    <span class="filter-label">个人库</span>${renderPersonalDropdown()}
    ${isAllPlatform ? '' : `<span class="filter-label">排序</span>${renderSortDropdown()}<span class="filter-label">每页</span>${renderDropdown('page-size', String(state.pageSize), [{ value: '24', label: '24 条' }, { value: '48', label: '48 条' }, { value: '100', label: '100 条' }])}`}
    <label class="desktop-check"><input id="server-only-toggle" type="checkbox" ${state.serverOnly ? 'checked' : ''}> <span>有服务端运行线索</span></label>
    <div class="desktop-view-toggle" role="group" aria-label="结果视图">${viewButtons}</div>
    <button type="button" class="hub-reset-btn" data-action="clear-filters">重置筛选</button>${includeDataButton ? `<button type="button" class="top-action-btn" data-action="choose-data">${state.data?.hasData ? '更换数据目录' : '选择已有数据'}</button>` : ''}
  </div>${renderActiveFilters()}`;
}

function updatePanel(): string {
  const update = state.update;
  const running = update?.state === 'running';
  const platform = update?.platform || state.updatePlatform;
  const progress = update && typeof update.total === 'number' && update.total > 0 ? Math.min(100, Math.round((update.processed / update.total) * 100)) : null;
  const logLines = (state.logs.length ? state.logs : update?.logs || []).slice(-80);
  return `<section class="update-panel" aria-labelledby="update-title">
    <div class="panel-heading"><div><span class="eyebrow">DATA REFRESH</span><h2 id="update-title">更新数据</h2></div><span class="panel-dot ${running ? 'is-running' : ''}"></span></div>
    <p class="panel-copy">选择一个平台，采集将在隔离目录完成。成功后才切换新快照，失败或取消不会覆盖当前可用数据。</p>
    <label class="field-label" for="update-platform">更新平台</label>
    ${renderDropdown('update-platform', platform, ALL_PLATFORMS.map((id) => ({ value: id, label: PLATFORM_CONFIGS[id].name })), running)}
    <div class="field-row"><div><label class="field-label" for="update-limit">采集上限</label><input id="update-limit" class="field" inputmode="numeric" placeholder="默认平台策略" value="" ${running ? 'disabled' : ''}></div><div><label class="field-label" for="update-pages">B站页数</label><input id="update-pages" class="field" inputmode="numeric" placeholder="1" value="1" ${running ? 'disabled' : ''}></div></div>
    <div class="update-actions"><button class="button primary" data-action="start-update" ${running ? 'disabled' : ''}>${running ? '更新进行中' : '开始更新'}</button>${running ? '<button class="button danger" data-action="cancel-update">取消任务</button>' : ''}</div>
    <div class="update-status ${update?.state || 'idle'}"><div class="status-line"><strong>${esc(update?.phase || '等待操作')}</strong><span>${update?.processed ? `已处理 ${update.processed} 条` : ''}</span></div>${progress === null ? (running ? '<div class="status-meta">总量未知，按实际处理结果更新</div>' : '') : `<div class="progress-track"><span style="width:${progress}%"></span></div><div class="status-meta">${progress}% · ${update?.processed}/${update?.total}</div>`}${update?.error ? `<div class="error-box">${esc(update.error)}</div>` : ''}</div>
    <details class="log-details" ${running || logLines.length ? 'open' : ''}><summary>任务日志${logLines.length ? ` · ${logLines.length} 条` : ''}</summary><pre>${esc(logLines.join('\n') || '暂无日志')}</pre></details>
  </section>`;
}

function formatMetric(value: unknown): string {
  const number = Number(value);
  if (!Number.isFinite(number)) return '—';
  if (number >= 100_000_000) return `${(number / 100_000_000).toFixed(1).replace(/\.0$/, '')}亿`;
  if (number >= 10_000) return `${(number / 10_000).toFixed(1).replace(/\.0$/, '')}万`;
  return number.toLocaleString('zh-CN');
}

function recordMetricItems(record: DesktopRecord): string[] {
  const raw = record.raw || {};
  const entries: Array<[string, unknown]> = record.platform === 'mcmod'
    ? [['浏览', raw.views], ['评论', raw.commentsCount], ['收藏', raw.favorites]]
    : record.platform === 'bilibili'
      ? [['播放', raw.views], ['点赞', raw.likes], ['评论', raw.reply]]
      : record.platform === 'bbsmc'
        ? [['下载', raw.downloads], ['关注', raw.followers], ['评论', raw.comments]]
        : record.platform === 'xyebbs'
          ? [['下载', raw.downloads], ['浏览', raw.views], ['评论', raw.comments]]
          : [['下载', raw.downloads], ['关注', raw.followers], ['点赞', raw.likes]];
  return entries.filter(([, value]) => value !== undefined && value !== null && value !== '').map(([label, value]) => `${label} ${formatMetric(value)}`);
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
  const coverUrl = recordCoverUrl(record);
  const fallbackUrl = PLATFORM_COVER_FALLBACKS[record.platform];
  const metrics = recordMetricItems(record);
  return `<article class="pack-card" data-action="select-record" data-index="${index}" data-search-text="${esc(searchContractText)}">
    <button type="button" class="pack-card-cover image-preview-trigger" data-action="open-image" data-image-url="${esc(coverUrl)}" data-image-title="${esc(record.title)}封面" aria-label="查看${esc(record.title)}封面"><img src="${esc(coverUrl)}" alt="${esc(record.title)}封面" loading="lazy" referrerpolicy="no-referrer" onerror="this.onerror=null;this.src='${esc(fallbackUrl)}'"></button>
    <div class="card-top"><span class="platform-badge">${platformIcon(record.platform)} ${config.name}</span><span class="card-time">${esc(formatTime(record.updatedAt))}</span></div>
    ${renderPersonalCardActions(record, index)}
    <h3>${esc(record.title)}</h3><p class="author">${esc(record.author)}</p>
    <p class="summary">${textOrUnknown(record.summary)}</p>
    <div class="chips">${record.versions.slice(0, 4).map((value) => `<span>${esc(value)}</span>`).join('')}${record.loaders.slice(0, 3).map((value) => `<span>${esc(value)}</span>`).join('')}${!record.versions.length && !record.loaders.length ? '<span class="muted-chip">兼容信息未知</span>' : ''}</div>
    ${metrics.length ? `<div class="card-metrics">${metrics.map((metric) => `<span>${esc(metric)}</span>`).join('')}</div>` : ''}
    ${renderQuickDownloadLinks(record)}
    <div class="card-footer"><span>查看详情与来源证据</span><button type="button" class="compare-star ${state.compareIds.includes(record.id) ? 'is-selected' : ''}" data-action="toggle-compare" data-index="${index}" title="${state.compareIds.includes(record.id) ? '移出对比' : '加入对比'}">${state.compareIds.includes(record.id) ? '✓' : '＋'} 对比</button></div>
  </article>`;
}

function renderCompactRecord(record: DesktopRecord, index: number): string {
  const coverUrl = recordCoverUrl(record);
  const fallbackUrl = PLATFORM_COVER_FALLBACKS[record.platform];
  const metrics = recordMetricItems(record);
  return `<article class="compact-record" data-action="select-record" data-index="${index}"><button type="button" class="compact-record-cover image-preview-trigger" data-action="open-image" data-image-url="${esc(coverUrl)}" data-image-title="${esc(record.title)}封面"><img src="${esc(coverUrl)}" alt="${esc(record.title)}封面" loading="lazy" referrerpolicy="no-referrer" onerror="this.onerror=null;this.src='${esc(fallbackUrl)}'"></button><div class="compact-record-main"><div class="compact-record-head"><span class="platform-badge">${platformIcon(record.platform)} ${esc(PLATFORM_CONFIGS[record.platform].name)}</span><span class="card-time">${esc(formatTime(record.updatedAt))}</span></div>${renderPersonalCardActions(record, index)}<h3>${esc(record.title)}</h3><p>${esc(record.author)} · ${textOrUnknown(record.summary)}</p><div class="chips">${record.versions.slice(0, 3).map((value) => `<span>${esc(value)}</span>`).join('')}${record.loaders.slice(0, 2).map((value) => `<span>${esc(value)}</span>`).join('')}</div></div><div class="compact-record-metrics">${metrics.map((metric) => `<span>${esc(metric)}</span>`).join('')}<button type="button" class="compare-star ${state.compareIds.includes(record.id) ? 'is-selected' : ''}" data-action="toggle-compare" data-index="${index}">${state.compareIds.includes(record.id) ? '✓' : '＋'} 对比</button></div></article>`;
}

function renderMcmodTable(records: DesktopRecord[]): string {
  const rows = records.map((record, index) => {
    const raw = record.raw || {};
    const trend = (raw.trendStats && typeof raw.trendStats === 'object' ? raw.trendStats : {}) as Record<string, unknown>;
    const votes = (raw.votes && typeof raw.votes === 'object' ? raw.votes : {}) as Record<string, unknown>;
    const categories = valueList(raw.categories ?? record.categories);
    const mods = valueList(raw.includedModNames ?? raw.included_mod_names);
    return `<tr class="mcmod-table-row" data-action="select-record" data-index="${index}">
      <td class="mcmod-name-cell"><strong>${esc(record.title)}</strong><small>${esc(record.author || '作者未知')}</small><div class="mcmod-table-tags">${categories.slice(0, 4).map((item) => `<span>${esc(item)}</span>`).join('')}${categories.length > 4 ? `<span>+${categories.length - 4}</span>` : ''}</div></td>
      <td>${esc(formatMetric(raw.views))}</td>
      <td><strong>${esc(formatMetric(raw.score))}</strong><small>推荐 ${esc(formatMetric(raw.recommendations))}</small></td>
      <td><span class="trend-number ${asNumber(trend.t7) >= 0 ? 'is-up' : 'is-down'}">${esc(formatMetric(trend.t7))}</span><small>7日 · 30日 ${esc(formatMetric(trend.t30))}</small></td>
      <td><span class="vote-positive">${esc(formatMetric(votes.redVotes))}</span> / <span class="vote-negative">${esc(formatMetric(votes.blackVotes))}</span><small>红 / 黑</small></td>
      <td>${esc(formatMetric(raw.commentsCount))}<small>推荐 ${esc(formatMetric(raw.recommendations))} · 收藏 ${esc(formatMetric(raw.favorites))}</small></td>
      <td class="mcmod-mod-cell">${mods.slice(0, 3).map((item) => `<span>${esc(item)}</span>`).join('')}${mods.length > 3 ? `<small>另有 ${mods.length - 3} 款模组</small>` : ''}</td><td class="mcmod-personal-cell">${renderPersonalCardActions(record, index)}</td>
    </tr>`;
  }).join('');
  if (!rows) return '<div class="empty-state compact-empty"><div class="empty-icon">⌕</div><h3>没有匹配的整合包</h3><p>换一个关键词或清除筛选条件。</p><button class="button secondary" data-action="clear-filters">清除筛选</button></div>';
  return `<div class="mcmod-table-wrap"><table class="mcmod-table"><thead><tr><th>整合包</th><th>浏览</th><th>热度 / 推荐</th><th>趋势</th><th>投票</th><th>评论 / 收藏</th><th>包含模组</th><th>个人库</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}

function renderBilibiliGroupedWorkspace(): string {
  const groups = sortBilibiliGroups(state.biliGroups);
  if (!groups.length) return '<div class="empty-state compact-empty"><div class="empty-icon">⌕</div><h3>没有匹配的整合包</h3><p>换一个关键词或清除筛选条件。</p><button class="button secondary" data-action="clear-filters">清除筛选</button></div>';
  const cards = groups.map((group) => {
    const latest = group.items[0];
    const index = latest ? state.records.findIndex((record) => record.sourceId === latest.bvid) : -1;
    return `<article class="desktop-rich-card" data-action="select-record" data-index="${index}" data-bili-group-key="${esc(group.key)}">${renderBilibiliGroupPersonalActions(group)}${renderBilibiliGroupPersonalSummary(group)}${renderBiliGroupedCard(group)}</article>`;
  }).join('');
  return `<div class="bili-legacy-mode-note"><strong>✨ 同名整合包智能聚合</strong><span>${formatCount(groups.length)} 款独立整合包 · 关联视频、统计、网盘与历史版本均保留</span></div><div class="bili-cards-grid desktop-bili-grid">${cards}</div>`;
}

function renderBilibiliFlatWorkspace(records: DesktopRecord[]): string {
  if (!records.length) return '<div class="empty-state compact-empty"><div class="empty-icon">⌕</div><h3>没有匹配的视频</h3><p>换一个关键词或清除筛选条件。</p><button class="button secondary" data-action="clear-filters">清除筛选</button></div>';
  const cards = records.map((record, index) => `<article class="desktop-rich-card" data-action="select-record" data-index="${index}">${renderPersonalCardActions(record, index)}${renderBiliFlatCard(toBilibiliPack(record))}</article>`).join('');
  return `<div class="bili-legacy-mode-note"><strong>视频平铺</strong><span>当前展示 ${formatCount(records.length)} / ${formatCount(state.total)} 条视频，可继续加载</span></div><div class="bili-cards-grid desktop-bili-grid">${cards}</div>`;
}

function platformIcon(platform: Platform): string {
  const src = PLATFORM_SITE_ICONS[platform];
  const short = platform === 'mcmod' ? 'MC' : platform === 'bilibili' ? 'B' : platform === 'bbsmc' ? 'BBS' : platform === 'xyebbs' ? 'XYE' : platform === 'modrinth' ? 'MR' : 'CF';
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
  const updateTime = platformState?.available && state.data?.updatedAt ? `快照更新时间：${formatTime(state.data.updatedAt)}` : '等待本地快照';
  const tags = [...new Set(samples.flatMap((record) => [...record.versions, ...record.loaders, ...record.categories]).filter(Boolean))].slice(0, 5);
  const sampleHtml = samples.length
    ? samples.map((record, index) => {
      const recordIndex = state.records.indexOf(record);
      return `<button type="button" class="featured-item" data-action="select-record" data-index="${recordIndex}" title="打开 ${esc(record.title)} 详情"><span class="featured-rank">${index + 1}</span><span class="featured-name">${esc(record.title)}</span><span class="featured-meta">${esc(record.author || '作者未知')}</span></button>`;
    }).join('')
    : '<div class="showcase-empty">当前筛选页没有可展示记录。</div>';
  const tagHtml = tags.length
    ? tags.map((tag) => `<button type="button" class="showcase-tag-chip" data-action="quick-search" data-query="${esc(tag)}">${esc(tag)}</button>`).join('')
    : '<span class="showcase-tag-chip muted-chip">暂无版本或标签</span>';
  return `<article class="platform-showcase-card" style="--card-accent:${PLATFORM_ACCENTS[platform]}; --card-glow:${PLATFORM_ACCENTS[platform]}33;">
    <div class="showcase-header"><div class="showcase-icon" style="background:${PLATFORM_ACCENTS[platform]}22; color:${PLATFORM_ACCENTS[platform]};">${platformIcon(platform)}</div><div><h3 class="showcase-title">${esc(config.name)}数据看板</h3><span class="showcase-badge" style="background:${PLATFORM_ACCENTS[platform]}22; color:${PLATFORM_ACCENTS[platform]};">${esc(PLATFORM_TAGLINES[platform])}</span></div></div>
    <div class="showcase-metrics"><div><div class="smetric-val">${formatCount(count)}</div><div class="smetric-lbl">当前快照记录</div></div><div><div class="smetric-val">${records.length ? formatCount(records.length) : '—'}</div><div class="smetric-lbl">当前页可浏览</div></div><div><div class="smetric-val">${platformState?.available ? '已载入' : '未载入'}</div><div class="smetric-lbl">本地状态</div></div></div>
    <div class="showcase-featured-box"><div class="showcase-box-header"><span>📌 当前快照代表</span><span>点击直达</span></div>${sampleHtml}</div>
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
    <div class="cross-search-input-wrap"><span class="cross-search-icon">🔍</span><input id="pack-search" class="cross-search-input" value="${esc(state.query)}" placeholder="${esc(getDesktopSearchPlaceholder('all'))}" autocomplete="off"><div class="cross-search-kbd"><kbd>Ctrl</kbd><kbd>K</kbd></div></div>
    <div class="cross-chips-deck"><div class="chip-deck-row"><span class="deck-row-lbl">🎮 核心版本：</span><div class="deck-chips-group">${versionChips}</div></div><div class="chip-deck-row"><span class="deck-row-lbl">🔥 常用关键词：</span><div class="deck-chips-group">${themeChips}</div></div></div>
    ${renderFilterControls(true)}
    ${renderCrossResults()}
  </section>`;
}

function renderCrossResults(): string {
  if (!state.query.trim()) return '';
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
  return `<div class="audit-backdrop" data-action="close-audit" role="dialog" aria-modal="true" aria-label="变动审计"><section class="audit-panel"><button type="button" class="icon-button audit-close" data-action="close-audit" aria-label="关闭审计">×</button><div class="eyebrow">SNAPSHOT AUDIT</div><h2>抓取变动审计</h2>${audit ? `<p class="audit-meta">${esc(audit.generated_at || '当前快照')} · ${audit.available ? '可用历史对比' : '没有可用历史基线'}</p>${audit.message ? `<div class="notice">${esc(audit.message)}</div>` : ''}<div class="audit-kpis"><div><strong>${formatCount(Number(stats.total_current || 0))}</strong><span>当前范围</span></div><div><strong>${formatCount(Number(stats.added_count || 0))}</strong><span>新增</span></div><div><strong>${formatCount(Number(stats.updated_count || 0))}</strong><span>更新</span></div><div><strong>${formatCount(Number(stats.removed_count || 0))}</strong><span>移除</span></div></div><div class="audit-list">${auditRows(audit)}</div>` : '<div class="loading-state">正在读取当前快照的审计文件…</div>'}</section></div>`;
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
  return `<div class="compare-backdrop" data-action="close-compare"><section class="compare-panel"><button type="button" class="icon-button compare-close" data-action="close-compare" aria-label="关闭比较">×</button><div class="eyebrow">MODPACK COMPARISON</div><h2>整合包全面对比</h2>${entries.length < 2 ? '<div class="empty-evidence">至少选择两个当前已载入的整合包。</div>' : `<div class="compare-table"><div class="compare-row compare-row-head"><span>字段</span>${entries.map((record) => `<strong>${esc(record.title)}</strong>`).join('')}</div><div class="compare-row"><span>平台</span>${entries.map((record) => `<span>${esc(PLATFORM_CONFIGS[record.platform].name)}</span>`).join('')}</div><div class="compare-row"><span>作者</span>${entries.map((record) => `<span>${esc(record.author)}</span>`).join('')}</div><div class="compare-row"><span>Minecraft</span>${entries.map((record) => `<span>${esc(record.versions.join('、') || UNKNOWN_LOCAL_TEXT)}</span>`).join('')}</div><div class="compare-row"><span>Loader</span>${entries.map((record) => `<span>${esc(record.loaders.join('、') || UNKNOWN_LOCAL_TEXT)}</span>`).join('')}</div><div class="compare-row"><span>分类</span>${entries.map((record) => `<span>${esc(record.categories.join('、') || UNKNOWN_LOCAL_TEXT)}</span>`).join('')}</div><div class="compare-row"><span>服务端</span>${entries.map((record) => `<span>${esc(environmentDisplay(record))}</span>`).join('')}</div><div class="compare-row"><span>平台指标</span>${entries.map((record) => `<span>${esc(recordMetricItems(record).join(' · ') || UNKNOWN_LOCAL_TEXT)}</span>`).join('')}</div></div>`}</section></div>`;
}

function renderPlatformHero(platform: Platform): string {
  const config = PLATFORM_CONFIGS[platform];
  const count = state.data?.platforms[platform]?.count ?? 0;
  return `<section class="channel-hero ${platform}-channel-hero"><div class="channel-hero-left"><span class="channel-badge-tag">${platformIcon(platform)} ${esc(config.name)}</span><div class="channel-title">${esc(config.name)}资料看板</div><div class="channel-desc">${esc(PLATFORM_TAGLINES[platform])}。详情页保留版本、模组、评论和原始来源入口。</div></div><div class="channel-quick-stats"><div class="cstat-item"><span class="cs-num">${formatCount(count)}</span><span class="cs-lbl">当前快照记录</span></div><div class="cstat-item"><span class="cs-num">${state.loading ? '…' : formatCount(state.total)}</span><span class="cs-lbl">当前结果总数</span></div></div></section>
   <section class="central-hub"><div class="hub-tier-search"><div class="hub-stat-badge">当前平台 <strong>${esc(config.name)}</strong></div><div class="hub-search-box"><span class="hub-search-icon">🔍</span><input id="pack-search" class="hub-search-input" value="${esc(state.query)}" placeholder="${esc(getDesktopSearchPlaceholder(platform))}" autocomplete="off"></div></div>${renderFilterControls()}</section>`;
}

function renderResultsWorkspace(selectedName: string): string {
  const records = currentRecords();
  const data = state.data;
  const hasFilter = state.query || state.version || state.loader || state.category || state.pan || state.dateRange || state.serverOnly || state.personalFilter;
  const isAllPlatform = state.platform === 'all';
  const isBili = state.platform === 'bilibili';
  const resultBody = isBili
    ? state.biliViewMode === 'grouped' ? renderBilibiliGroupedWorkspace() : renderBilibiliFlatWorkspace(records)
    : records.length
      ? state.viewMode === 'compact'
        ? `<div class="compact-record-list">${records.map(renderCompactRecord).join('')}</div>`
        : state.viewMode === 'table' && state.platform === 'mcmod'
          ? renderMcmodTable(records)
          : state.platform !== 'all' && state.platform !== 'mcmod'
            ? `<div class="pack-grid legacy-rich-grid">${records.map((record, index) => `<article class="desktop-rich-card" data-action="select-record" data-index="${index}">${renderPersonalCardActions(record, index)}${renderPlatformRichCard(record)}</article>`).join('')}</div>`
          : `<div class="pack-grid">${records.map(renderRecord).join('')}</div>`
      : `<div class="empty-state compact-empty"><div class="empty-icon">⌕</div><h3>没有匹配的整合包</h3><p>换一个关键词或清除筛选条件。</p><button class="button secondary" data-action="clear-filters">清除筛选</button></div>`;
  const displayedCount = isBili && state.biliViewMode === 'grouped' ? state.biliGroups.length : records.length;
  const totalLabel = isBili && state.biliViewMode === 'grouped' ? displayedCount : state.total;
  const resultHeading = isAllPlatform ? '分平台结果' : state.loading ? '正在读取数据…' : hasFilter ? '筛选结果' : '最近可用数据';
  const resultCount = isAllPlatform ? `${formatCount(displayedCount)} 条已加载 · 每个平台最多 12 条/轮` : `${formatCount(displayedCount)} / ${formatCount(totalLabel)}`;
  const loadMoreLabel = isAllPlatform ? `各平台继续加载（当前第 ${state.page} 轮）` : `加载更多（已显示 ${formatCount(records.length)} / ${formatCount(state.total)}）`;
  return `<div class="content-grid"><section class="results-column"><div class="results-heading"><div><span class="eyebrow">${esc(selectedName)}</span><h2>${state.loading ? '正在读取数据…' : resultHeading}</h2></div><span class="result-count">${state.loading ? '' : resultCount}</span></div>${state.message ? `<div class="notice">${esc(state.message)}</div>` : ''}${!data?.hasData ? `<div class="empty-state"><div class="empty-icon">◌</div><h3>还没有本地数据快照</h3><p>选择现有的 <code>converted_output</code>、<code>build/frontend_preview</code> 或其 <code>data</code> 目录。应用不会把空数据伪装成成功。</p><button class="button primary" data-action="choose-data">选择数据目录</button></div>` : state.loading ? '<div class="loading-state">正在读取当前快照…</div>' : `${resultBody}${state.hasMore ? `<div class="load-more"><button class="button secondary" data-action="load-more">${loadMoreLabel}</button></div>` : ''}`}</section>${updatePanel()}</div>`;
}

function renderRelease(release: Record<string, unknown>): string {
  const downloads = Array.isArray(release.downloads) ? release.downloads : Array.isArray(release.download_links) ? release.download_links : Array.isArray(release.files) ? release.files : [];
  const links = downloads.map((download) => {
    const item = (download || {}) as Record<string, unknown>;
    const url = safeExternalUrl(item.url);
    return url ? `<a class="detail-link" href="${esc(url)}" target="_blank" rel="noreferrer">${esc(String(item.name || '打开下载'))} ↗</a>` : '';
  }).filter(Boolean).join('');
  const versions = valueList(release.gameVersions ?? release.game_versions ?? release.mc_versions).join('、');
  const loaders = valueList(release.loaders ?? release.loader).join('、');
  const notes = String(release.changelogMd || release.changelog || '').trim();
  const releaseDate = String(release.date || release.release_date || '').trim();
  return `<article class="release-item"><div class="release-head"><strong>${textOrUnknown(String(release.versionName || release.version_number || ''))}</strong><span>${esc(releaseDate || UNKNOWN_LOCAL_TEXT)}</span></div><div class="release-meta">${versions ? `Minecraft：${esc(versions)}` : ''}${loaders ? ` · Loader：${esc(loaders)}` : ''}</div>${notes ? `<p>${esc(notes)}</p>` : ''}${links ? `<div class="release-links">${links}</div>` : ''}</article>`;
}

function renderCommentSection(record: DesktopRecord): string {
  const description = rawText(record, ['desc', 'description', 'summary', 'subtitle_summary']) || record.summary;
  const pinned = rawText(record, ['pinned_comment']);
  const commentState = state.comments.sourceId === record.sourceId ? state.comments : null;
  const independentComments = commentState?.available ? renderComments(commentState.comments) : commentState?.loading ? '<div class="loading-state">正在读取独立评论…</div>' : commentState?.error ? `<div class="error-box">${esc(commentState.error)}</div>` : '<div class="empty-evidence">当前快照没有独立评论文件。</div>';
  const pinnedHtml = pinned ? `<article class="comment-item"><div class="comment-head"><strong>来源置顶评论</strong></div><p>${esc(pinned)}</p></article>` : '';
  const meta = commentState?.pageCount ? `<span class="detail-submeta">记录数：${commentState.pageCount}</span>` : '';
  return `<div class="detail-section"><h3>简介</h3><p class="detail-summary">${textOrUnknown(description)}</p></div><div class="detail-section"><h3>评论 / 讨论 ${meta}</h3>${pinnedHtml}${independentComments}</div>`;
}

function renderMediaSection(record: DesktopRecord): string {
  const urls = recordImageUrls(record);
  if (!urls.length) return `<div class="detail-section"><h3>图片</h3><div class="empty-evidence">${UNKNOWN_LOCAL_TEXT}；列表继续使用现有封面占位图。</div></div>`;
  return `<div class="detail-section"><h3>图片 <span class="detail-submeta">${urls.length} 张 · 点击放大</span></h3><div class="detail-image-gallery">${urls.map((url, index) => renderImageButton(url, `${record.title}图片${index + 1}`, 'detail-image')).join('')}</div></div>`;
}

function renderDetailFacts(record: DesktopRecord): string {
  const raw = record.raw || {};
  const pairs: Array<[string, string]> = record.platform === 'bilibili'
    ? [['播放', formatMetric(raw.views)], ['点赞', formatMetric(raw.likes)], ['投币', formatMetric(raw.coins)], ['收藏', formatMetric(raw.favorites)], ['评论', formatMetric(raw.reply)], ['弹幕', formatMetric(raw.danmaku)], ['QQ群', raw.qq_group ? String(raw.qq_group) : '未知'], ['提取码', raw.extract_code ? String(raw.extract_code) : '未知']]
    : record.platform === 'mcmod'
      ? [['浏览', formatMetric(raw.views)], ['推荐', formatMetric(raw.recommendations)], ['收藏', formatMetric(raw.favorites)], ['评论', formatMetric(raw.commentsCount)], ['模组数', raw.includedModsCount ? `${raw.includedModsCount} 款` : '未知'], ['类型', raw.typeName ? String(raw.typeName) : '未知']]
      : [['下载', formatMetric(raw.downloads)], ['关注', formatMetric(raw.followers)], ['点赞', formatMetric(raw.likes)], ['浏览', formatMetric(raw.views)], ['评论', formatMetric(raw.comments)]];
  const valid = pairs.filter(([, value]) => value && value !== '—');
  if (!valid.length) return '';
  return `<div class="detail-section"><h3>平台数据</h3><dl class="detail-facts">${valid.map(([label, value]) => `<div><dt>${esc(label)}</dt><dd>${esc(value)}</dd></div>`).join('')}</dl></div>`;
}

function renderDetailDownloadLinks(record: DesktopRecord): string {
  const links = rawRecords(record, ['download_links']).filter((item) => safeExternalUrl(item.url));
  if (!links.length) {
    return record.platform === 'mcmod'
      ? `<div class="detail-section"><h3>下载入口</h3><div class="empty-evidence">${UNKNOWN_LOCAL_TEXT}；可打开 MC百科原站继续判断。</div></div>`
      : '';
  }
  return `<div class="detail-section"><h3>下载与渠道 <span class="detail-submeta">${links.length} 个入口</span></h3><div class="release-links">${links.map((link) => `<a class="detail-link" href="${esc(safeExternalUrl(link.url))}" target="_blank" rel="noreferrer">${esc(String(link.name || link.type || '下载入口'))} ↗</a>`).join('')}</div></div>`;
}

function detailPanel(): string {
  const record = state.selected;
  if (!record) return '';
  const vm = buildVersionModalViewModel(record.platform, record.raw as never, record.raw);
  const modNames = rawList(record, ['includedModNames', 'included_mod_names']);
  const modsByName = new Map<string, Record<string, unknown>>();
  for (const mod of rawRecords(record, ['includedMods', 'included_mods', 'previewMods', 'mods'])) {
    const name = String(mod.title || mod.name || '').trim();
    if (name && !modsByName.has(name)) modsByName.set(name, mod);
  }
  for (const name of modNames) if (!modsByName.has(name)) modsByName.set(name, { name });
  const mods = [...modsByName.values()];
  const releases = vm.releases?.length ? vm.releases : rawRecords(record, ['releases', 'versions_data', 'version_history']);
  const releaseHtml = releases.length ? releases.map((release) => renderRelease(release as unknown as Record<string, unknown>)).join('') : '<div class="empty-evidence">当前数据没有版本发布明细；可从下方版本详情入口查看原站记录。</div>';
  const versionUrl = safeExternalUrl(vm.targetUrl);
  const sourceUrl = safeExternalUrl(record.url);
  const modHtml = mods.length ? `<details class="detail-expand" open><summary>共 ${mods.length} 款</summary><div class="mod-list">${mods.map((mod) => { const url = safeExternalUrl(mod.url); return url ? `<a class="mod-chip" href="${esc(url)}" target="_blank" rel="noreferrer">${esc(String(mod.title || mod.name || '未知模组'))} ↗</a>` : `<span class="mod-chip">${esc(String(mod.title || mod.name || '未知模组'))}</span>`; }).join('')}</div></details>` : '<div class="empty-evidence">当前数据没有模组清单。</div>';
  return `<div class="detail-backdrop" data-action="close-detail"><aside class="detail-panel" data-detail-panel>
    <button class="icon-button close-detail" data-action="close-detail" aria-label="关闭详情">×</button>
    <span class="eyebrow">${esc(PLATFORM_CONFIGS[record.platform].name)} · 原始来源</span><h2>${esc(record.title)}</h2><p class="detail-author">${esc(record.author)}</p>
    ${renderMediaSection(record)}
    <div class="detail-section"><h3>适配摘要</h3><dl><div><dt>Minecraft</dt><dd>${textOrUnknown(vm.mcVersionsList.join('、'))}</dd></div><div><dt>Loader</dt><dd>${textOrUnknown(record.loaders.join('、'))}</dd></div><div><dt>更新时间</dt><dd>${esc(formatTime(record.updatedAt))}</dd></div><div><dt>服务端</dt><dd>${esc(environmentDisplay(record))}</dd></div></dl></div>
    <div class="detail-section"><h3>来源证据</h3><div class="evidence-list">${record.evidence.length ? record.evidence.map((item) => `<div class="evidence-item"><span>${esc(item.label)}</span><strong>${textOrUnknown(item.value)}</strong></div>`).join('') : '<div class="empty-evidence">当前数据没有提供可核对的来源字段。</div>'}</div></div>
    ${renderDetailFacts(record)}
    ${renderPersonalDetail(record)}
    ${renderDetailDownloadLinks(record)}
    ${renderCommentSection(record)}
    <div class="detail-section"><h3>版本详情 <span class="detail-submeta">${releases.length ? `记录数：${releases.length}` : ''}</span></h3><div class="release-list">${releaseHtml}</div></div>
    <div class="detail-section"><h3>已收录模组</h3>${modHtml}</div>
    <div class="detail-actions">${sourceUrl ? `<button class="button primary wide" data-action="open-source" data-url="${esc(sourceUrl)}">打开原站</button>` : '<div class="unknown-action">原站链接未知</div>'}${versionUrl && versionUrl !== sourceUrl ? `<button class="button secondary wide" data-action="open-source" data-url="${esc(versionUrl)}">打开版本详情</button>` : ''}</div>
  </aside></div>`;
}

function imagePreviewPanel(): string {
  const preview = state.imagePreview;
  if (!preview) return '';
  return `<div class="image-lightbox" data-action="close-image" role="dialog" aria-modal="true" aria-label="图片预览"><div class="image-lightbox-panel"><button type="button" class="icon-button image-lightbox-close" data-action="close-image" aria-label="关闭图片预览">×</button><img src="${esc(preview.url)}" alt="${esc(preview.title)}" referrerpolicy="no-referrer"><div class="image-lightbox-title">${esc(preview.title)}</div><a class="button secondary" href="${esc(preview.url)}" target="_blank" rel="noreferrer">在新标签页打开原图 ↗</a></div></div>`;
}

function render(): void {
  const data = state.data;
  const availableCount = data ? Object.values(data.platforms).filter((item) => item.available).length : 0;
  const selectedName = state.platform === 'all' ? '全部平台' : PLATFORM_CONFIGS[state.platform].name;
  const totalCount = data ? ALL_PLATFORMS.reduce((sum, platform) => sum + (data.platforms[platform]?.count || 0), 0) : 0;
  const theme = document.documentElement.dataset.theme || 'light';
  const topNav = platformItems.map((item) => {
    const count = item.id === 'all' ? totalCount : data?.platforms[item.id]?.count || 0;
    const icon = item.id === 'all' ? '<span class="platform-icon-wrap platform-all-icon"><span class="platform-icon-fallback">全</span></span>' : platformIcon(item.id);
    return `<button type="button" class="top-plat-btn ${state.platform === item.id ? 'active' : ''}" data-tab="${item.id}" data-action="set-platform" data-platform="${item.id}" aria-current="${state.platform === item.id ? 'page' : 'false'}"><span class="platform-nav-icon">${icon}</span><span class="platform-nav-label">${esc(item.name)}</span><span class="pnav-badge">${count ? formatCount(count) : '—'}</span></button>`;
  }).join('');
  const themeButtons = [['dark', '🌙'], ['light', '☀️'], ['eye', '🌿'], ['warm', '☕'], ['pink', '🌸']].map(([id, icon]) => `<button type="button" class="top-tdot ${theme === id ? 'active' : ''}" data-action="set-theme" data-theme="${id}" title="切换${id}主题">${icon}</button>`).join('');
  const body = state.platform === 'all'
    ? `${renderCrossSearch()}<section class="all-platforms-grid" aria-label="六平台数据看板">${ALL_PLATFORMS.map(renderLegacyShowcaseCard).join('')}</section><div class="desktop-section-heading"><span class="eyebrow">LIVE SNAPSHOT</span><h2>当前快照浏览</h2><p>卡片、版本筛选与详情入口均来自本地快照；需要更多结果时可继续加载。</p></div>${renderResultsWorkspace(selectedName)}`
    : `${renderPlatformHero(state.platform)}${renderResultsWorkspace(selectedName)}`;
  root.innerHTML = `<div class="desktop-app legacy-shell"><div class="bg-layer" aria-hidden="true"></div>
    <header class="topbar"><div class="topbar-inner"><div class="topbar-left"><button type="button" class="topbar-brand" data-action="set-platform" data-platform="all" title="返回全平台总览"><span class="brand-cube">⛏️</span><span class="brand-title">我的世界整合包聚合</span><span class="brand-badge">${totalCount ? `${formatCount(totalCount)} 条本地记录` : '本地快照工作台'}</span></button></div><div class="topbar-center"><nav class="topbar-platform-nav" aria-label="全端聚合多平台导航">${topNav}</nav></div><div class="topbar-actions"><button type="button" class="top-action-btn" data-action="toggle-audit">变动审计${auditCount(state.audit) ? ` <span class="audit-count-badge">${auditCount(state.audit)}</span>` : ''}</button><span class="data-status ${data?.hasData ? 'ready' : 'empty'}"><i></i>${data?.hasData ? `快照 ${esc(data.snapshotId || '已载入')}` : '等待数据'}</span><button type="button" class="top-action-btn" data-action="choose-data">${data?.hasData ? '更换数据' : '选择数据'}</button><div class="top-theme-pills" role="radiogroup" aria-label="切换主题">${themeButtons}</div></div></div></header>
    <main class="main-content">${body}<footer class="workspace-footer"><span>${availableCount ? `${availableCount}/6 个平台已有数据` : '数据来源未知'}</span><span>${data?.updatedAt ? `快照更新时间：${esc(formatTime(data.updatedAt))}` : '数据不会自动编造'}</span>${data?.canonicalReady ? '<span class="canonical-ok">Canonical 已校验</span>' : '<span>局部导入或原始数据不足，Canonical 状态未知</span>'}</footer></main>${renderCompareTray()}${detailPanel()}${imagePreviewPanel()}${auditPanel()}${renderComparePanel()}</div>`;
  bindEvents();
}

function bindEvents(): void {
  root.querySelectorAll<HTMLElement>('[data-action]').forEach((element) => element.addEventListener('click', (event) => void handleAction(element, event)));
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
  root.querySelector<HTMLInputElement>('#server-only-toggle')?.addEventListener('change', (event) => {
    state.serverOnly = (event.target as HTMLInputElement).checked;
    void loadRecords(true);
  });
  root.querySelector<HTMLInputElement>('#pack-search')?.addEventListener('input', (event) => {
    state.query = (event.target as HTMLInputElement).value;
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(() => void loadRecords(), 180);
  });
  root.querySelector<HTMLTextAreaElement>('[data-personal-note]')?.addEventListener('input', (event) => {
    const textarea = event.target as HTMLTextAreaElement;
    const targetRecord = state.selected;
    if (!targetRecord || !isPersonalWritable(targetRecord)) return;
    window.clearTimeout(personalNoteTimer);
    personalNoteTimer = window.setTimeout(() => {
      void savePersonalPatch(targetRecord, { note: textarea.value }, false);
    }, 350);
  });
}

async function loadComments(record: DesktopRecord): Promise<void> {
  state.comments = { sourceId: record.sourceId, loading: true, available: false, pageCount: 0, comments: [], sourceFile: null, error: '' };
  render();
  try {
    const result = await window.desktopApi.getPlatformComments(record.platform, record.sourceId);
    if (state.selected?.id !== record.id) return;
    state.comments = {
      sourceId: result.sourceId,
      loading: false,
      available: result.available,
      pageCount: result.pageCount,
      comments: result.comments || [],
      sourceFile: result.sourceFile,
      error: result.error || '',
    };
  } catch (error) {
    if (state.selected?.id !== record.id) return;
    state.comments = { sourceId: record.sourceId, loading: false, available: false, pageCount: 0, comments: [], sourceFile: null, error: error instanceof Error ? error.message : String(error) };
  }
  render();
}

type PersonalPatch = Partial<Pick<PersonalStatus, 'favorite' | 'wantToPlay' | 'played' | 'rating' | 'note'>>;

function recordAtIndex(index: number): DesktopRecord | null {
  return state.records[index] || null;
}

function recordForPersonalTarget(element: HTMLElement): DesktopRecord | null {
  const platform = element.dataset.personalPlatform as Platform | undefined;
  const sourceId = element.dataset.personalSourceId;
  if (platform && sourceId !== undefined && ALL_PLATFORMS.includes(platform)) {
    return state.records.find((record) => record.platform === platform && record.sourceId === sourceId) || null;
  }
  return recordAtIndex(Number(element.dataset.index || '-1'));
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
  } catch (error) {
    state.personalLibrary = {};
    state.message = error instanceof Error ? error.message : String(error);
  }
}

async function handleAction(element: HTMLElement, event?: Event): Promise<void> {
  const action = element.dataset.action;
  if (action === 'toggle-audit') {
    state.auditOpen = !state.auditOpen;
    if (state.auditOpen && !state.audit) {
      render();
      try {
        state.audit = await window.desktopApi.getAuditDiff();
      } catch (error) {
        state.audit = { available: false, message: error instanceof Error ? error.message : String(error), generated_at: null, stats: null, added: [], updated: [], removed: [], version_gained: [] };
      }
    }
    render();
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
  } else if (action === 'toggle-compare') {
    event?.stopPropagation();
    const index = Number(element.dataset.index || '-1');
    const record = state.records[index];
    if (!record) return;
    state.compareRecords[record.id] = record;
    state.compareIds = state.compareIds.includes(record.id) ? state.compareIds.filter((id) => id !== record.id) : [...state.compareIds, record.id];
    render();
  } else if (action === 'set-platform') {
    state.platform = (element.dataset.platform || 'all') as FilterPlatform;
    if (state.platform !== 'all') state.updatePlatform = state.platform;
    if (state.platform === 'all') state.sort = 'updated_desc';
    if (state.platform === 'bilibili' && !['updated_desc', 'views_desc', 'likes_desc', 'favs_desc', 'coins_desc', 'share_desc', 'reply_desc', 'danmaku_desc'].includes(state.sort)) state.sort = 'updated_desc';
    if (state.platform !== 'mcmod' && state.viewMode === 'table') state.viewMode = 'cards';
    state.selected = null;
    state.imagePreview = null;
    state.compareOpen = false;
    state.comments = { sourceId: '', loading: false, available: false, pageCount: 0, comments: [], sourceFile: null, error: '' };
    await loadRecords(true);
  } else if (action === 'choose-data') {
    state.message = '正在读取所选目录…';
    render();
    try {
      const result = await window.desktopApi.chooseDataDirectory();
      if (!result.cancelled && result.data) {
        state.data = result.data;
        state.message = '';
        await loadRecords(true);
      } else {
        state.message = '';
        render();
      }
    } catch (error) {
      state.message = error instanceof Error ? error.message : String(error);
      render();
    }
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
    } else if (dropdown === 'sort' && state.platform !== 'all') {
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
  } else if (action === 'start-update') {
    const platform = state.updatePlatform;
    const limitValue = root.querySelector<HTMLInputElement>('#update-limit')?.value.trim() || '';
    const pagesValue = root.querySelector<HTMLInputElement>('#update-pages')?.value.trim() || '';
    state.logs = [];
    try {
      await window.desktopApi.startUpdate(platform || 'bilibili', { limit: limitValue ? Number(limitValue) : undefined, pages: pagesValue ? Number(pagesValue) : undefined });
    } catch (error) {
      state.message = error instanceof Error ? error.message : String(error);
      render();
    }
  } else if (action === 'cancel-update') {
    await window.desktopApi.cancelUpdate();
  } else if (action === 'load-more') {
    await loadRecords(false);
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
  } else if (action === 'select-record') {
    const target = event?.target instanceof Element ? event.target : null;
    if (target && target !== element && target.closest('a,button,details,summary')) return;
    const index = Number(element.dataset.index || '-1');
    state.selected = state.records[index] || null;
    state.imagePreview = null;
    state.comments = { sourceId: state.selected?.sourceId || '', loading: false, available: false, pageCount: 0, comments: [], sourceFile: null, error: '' };
    render();
    if (state.selected) await loadComments(state.selected);
  } else if (action === 'close-detail') {
    if (event && event.target !== element) return;
    state.selected = null;
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
  } else if (action === 'clear-filters') {
    state.query = ''; state.version = ''; state.loader = ''; state.category = ''; state.pan = ''; state.dateRange = ''; state.serverOnly = false; state.personalFilter = ''; state.sort = 'updated_desc'; await loadRecords(true);
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
    await loadRecords(true);
  } else if (action === 'set-view-mode') {
    const viewMode = element.dataset.viewMode;
    if (viewMode === 'cards' || viewMode === 'compact' || (viewMode === 'table' && state.platform === 'mcmod')) {
      state.viewMode = viewMode;
      render();
    }
  } else if (action === 'set-bili-view-mode') {
    const viewMode = element.dataset.biliViewMode;
    if (viewMode === 'grouped' || viewMode === 'flat') {
      state.biliViewMode = viewMode;
      await loadRecords(true);
    }
  }
}

async function loadRecords(reset = true): Promise<void> {
  if (reset) {
    state.page = 1;
    state.records = [];
    state.biliGroups = [];
  } else {
    state.page += 1;
  }
  state.loading = true;
  render();
  const platforms = state.platform === 'all' ? ALL_PLATFORMS : [state.platform];
  const groupedBili = state.platform === 'bilibili' && state.biliViewMode === 'grouped';
  const requestPageSize = groupedBili ? 500 : state.platform === 'all' ? 12 : state.pageSize;
  try {
    const getOptions = (page: number) => ({
      query: state.query,
      version: state.version,
      loader: state.loader,
      category: state.category,
      pan: state.pan,
      dateRange: state.dateRange,
      serverOnly: state.serverOnly,
      // Grouped Bilibili mode must receive the complete non-personal result set.
      // Personal matching happens after all members have been grouped so an old
      // marked video cannot disappear behind a newer unmarked representative.
      personalStatus: groupedBili ? '' : state.personalFilter,
      sort: state.platform === 'all' ? 'updated_desc' : state.sort,
      page,
      pageSize: requestPageSize,
    });
    let results: Awaited<ReturnType<typeof window.desktopApi.getPlatformRecords>>[];
    if (groupedBili) {
      const first = await window.desktopApi.getPlatformRecords('bilibili', getOptions(1));
      results = [first];
      const pageCount = Math.ceil(first.total / Math.max(first.pageSize, 1));
      for (let page = 2; page <= pageCount; page += 1) {
        results.push(await window.desktopApi.getPlatformRecords('bilibili', getOptions(page)));
      }
    } else {
      results = await Promise.all(platforms.map((platform) => window.desktopApi.getPlatformRecords(platform, getOptions(state.page))));
    }
    const nextRecords = results.flatMap((result) => result.records);
    state.records = reset ? nextRecords : [...state.records, ...nextRecords];
    for (const record of nextRecords) state.compareRecords[record.id] = record;
    const groupedResults = groupedBili ? buildBilibiliGroups(state.records) : [];
    state.biliGroups = groupedBili
      ? filterBilibiliGroupsByPersonalStatus(groupedResults, state.personalLibrary, state.personalFilter)
      : [];
    state.total = results.reduce((sum, result) => sum + result.total, 0);
    state.availableVersions = [...new Set(results.flatMap((result) => result.availableVersions || []))].sort((a, b) => a.localeCompare(b, 'zh-CN'));
    state.availableLoaders = [...new Set(results.flatMap((result) => result.availableLoaders || []))].sort((a, b) => a.localeCompare(b, 'zh-CN'));
    state.availableCategories = [...new Set(results.flatMap((result) => result.availableCategories || []))].sort((a, b) => a.localeCompare(b, 'zh-CN'));
    state.availablePans = [...new Set(results.flatMap((result) => result.availablePans || []))];
    state.hasMore = groupedBili ? false : state.records.length < state.total;
    state.loading = false;
    render();
  } catch (error) {
    state.loading = false;
    state.message = error instanceof Error ? error.message : String(error);
    render();
  }
}

let documentEventsBound = false;

function bindDocumentEvents(): void {
  if (documentEventsBound) return;
  documentEventsBound = true;
  document.addEventListener('click', (event) => {
    if (!state.openDropdown) return;
    const target = event.target instanceof Element ? event.target : null;
    if (!target?.closest('.ui-dropdown')) {
      state.openDropdown = '';
      render();
    }
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && state.openDropdown) {
      state.openDropdown = '';
      render();
    }
  });
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
    await loadRecords();
  } catch (error) {
    state.loading = false;
    state.message = error instanceof Error ? error.message : String(error);
    render();
  }
  window.desktopApi.onUpdateStatus((update) => {
    state.update = update;
    if (update.platform) state.updatePlatform = update.platform;
    state.logs = update.logs || state.logs;
    render();
    if (update.state === 'success') {
      void window.desktopApi.getState().then(async (next) => { state.data = next.data; await loadRecords(true); });
    }
  });
  window.desktopApi.onUpdateLog((line) => {
    state.logs = [...state.logs, line].slice(-200);
    render();
  });
  window.desktopApi.onDataChanged((data) => {
    state.data = data;
    void loadRecords(true);
  });
}

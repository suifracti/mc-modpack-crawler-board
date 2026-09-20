import { ALL_PLATFORMS, PLATFORM_CONFIGS } from './data/platformRegistry';
import type { Platform } from './domain/types';
import { buildVersionModalViewModel } from './modals/version/buildViewModel';
import {
  buildBbsmcSearchDocument,
  buildBilibiliSearchDocument,
  buildCurseforgeSearchDocument,
  buildMcmodSearchDocument,
  buildModrinthSearchDocument,
  buildXyebbsSearchDocument,
} from './search/searchDocument';

interface DesktopRecord {
  id: string;
  platform: Platform;
  sourceId: string;
  title: string;
  author: string;
  url: string;
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

interface DesktopComment {
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

interface DesktopCommentsResult {
  platform: Platform;
  sourceId: string;
  available: boolean;
  sourceFile: string | null;
  pageCount: number;
  comments: DesktopComment[];
  error?: string;
}

interface DesktopPlatformState {
  id: Platform;
  name: string;
  icon: string;
  count: number;
  sourceFile: string | null;
  error: string | null;
  available: boolean;
}

interface DesktopDataState {
  hasData: boolean;
  snapshotId: string | null;
  updatedAt: string | null;
  source: string | null;
  canonicalReady: boolean;
  platforms: Record<Platform, DesktopPlatformState>;
}

interface DesktopUpdateStatus {
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

interface DesktopApi {
  getState: () => Promise<{ data: DesktopDataState; update: DesktopUpdateStatus }>;
  getPlatformRecords: (platform: Platform, options?: { query?: string; version?: string; loader?: string; page?: number; pageSize?: number }) => Promise<{ platform: Platform; total: number; page: number; pageSize: number; records: DesktopRecord[]; availableVersions: string[]; availableLoaders: string[]; error?: string | null }>;
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

const platformItems: Array<{ id: FilterPlatform; name: string; icon: string }> = [
  { id: 'all', name: '全部平台', icon: '✦' },
  ...ALL_PLATFORMS.map((id) => ({ id, name: PLATFORM_CONFIGS[id].name, icon: id === 'mcmod' ? '📦' : id === 'bilibili' ? '📺' : id === 'bbsmc' ? '💎' : id === 'xyebbs' ? '🍃' : id === 'modrinth' ? '🌐' : '🔥' })),
];

const state = {
  data: null as DesktopDataState | null,
  update: null as DesktopUpdateStatus | null,
  platform: 'all' as FilterPlatform,
  query: '',
  version: '',
  loader: '',
  records: [] as DesktopRecord[],
  total: 0,
  availableVersions: [] as string[],
  availableLoaders: [] as string[],
  page: 1,
  pageSize: 48,
  hasMore: false,
  selected: null as DesktopRecord | null,
  comments: { sourceId: '', loading: false, available: false, pageCount: 0, comments: [] as DesktopComment[], sourceFile: null as string | null, error: '' },
  loading: true,
  message: '',
  logs: [] as string[],
};

let root: HTMLElement;
let searchTimer: number | undefined;

function esc(value: unknown): string {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function textOrUnknown(value: string | null | undefined): string {
  return value && value.trim() ? esc(value) : '<span class="unknown">未知</span>';
}

function formatTime(value: string | null | undefined): string {
  if (!value) return '未提供更新时间';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('zh-CN', { dateStyle: 'medium', timeStyle: 'short' });
}

function currentRecords(): DesktopRecord[] {
  return state.records;
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
    const replyHtml = replies.length ? `<div class="comment-replies">${replies.map((reply) => `<div class="comment-reply"><strong>${esc(String(reply.author ?? reply.user ?? '回复'))}</strong><span>${textOrUnknown(commentBody(reply))}</span></div>`).join('')}</div>` : '';
    return `<article class="comment-item"><div class="comment-head"><strong>${esc(author)}</strong><span>${esc(String(comment.time ?? comment.date ?? comment.floor ?? ''))}</span></div><p>${textOrUnknown(commentBody(comment))}</p>${replyHtml}</article>`;
  }).join('')}</div>`;
}

function renderOptions(values: string[], selected: string, emptyLabel: string): string {
  return [`<option value="">${emptyLabel}</option>`, ...values.map((value) => `<option value="${esc(value)}"${value === selected ? ' selected' : ''}>${esc(value)}</option>`)].join('');
}

function updatePanel(): string {
  const update = state.update;
  const running = update?.state === 'running';
  const platform = update?.platform || (state.platform === 'all' ? 'bilibili' : state.platform);
  const progress = update && typeof update.total === 'number' && update.total > 0 ? Math.min(100, Math.round((update.processed / update.total) * 100)) : null;
  const logLines = (state.logs.length ? state.logs : update?.logs || []).slice(-80);
  return `<section class="update-panel" aria-labelledby="update-title">
    <div class="panel-heading"><div><span class="eyebrow">DATA REFRESH</span><h2 id="update-title">更新数据</h2></div><span class="panel-dot ${running ? 'is-running' : ''}"></span></div>
    <p class="panel-copy">选择一个平台，采集将在隔离目录完成。成功后才切换新快照，失败或取消不会覆盖当前可用数据。</p>
    <label class="field-label" for="update-platform">更新平台</label>
    <select id="update-platform" class="field" ${running ? 'disabled' : ''}>${ALL_PLATFORMS.map((id) => `<option value="${id}"${id === platform ? ' selected' : ''}>${PLATFORM_CONFIGS[id].name}</option>`).join('')}</select>
    <div class="field-row"><div><label class="field-label" for="update-limit">采集上限</label><input id="update-limit" class="field" inputmode="numeric" placeholder="默认平台策略" value="" ${running ? 'disabled' : ''}></div><div><label class="field-label" for="update-pages">B站页数</label><input id="update-pages" class="field" inputmode="numeric" placeholder="1" value="1" ${running ? 'disabled' : ''}></div></div>
    <div class="update-actions"><button class="button primary" data-action="start-update" ${running ? 'disabled' : ''}>${running ? '更新进行中' : '开始更新'}</button>${running ? '<button class="button danger" data-action="cancel-update">取消任务</button>' : ''}</div>
    <div class="update-status ${update?.state || 'idle'}"><div class="status-line"><strong>${esc(update?.phase || '等待操作')}</strong><span>${update?.processed ? `已处理 ${update.processed} 条` : ''}</span></div>${progress === null ? (running ? '<div class="status-meta">总量未知，按实际处理结果更新</div>' : '') : `<div class="progress-track"><span style="width:${progress}%"></span></div><div class="status-meta">${progress}% · ${update?.processed}/${update?.total}</div>`}${update?.error ? `<div class="error-box">${esc(update.error)}</div>` : ''}</div>
    <details class="log-details" ${running || logLines.length ? 'open' : ''}><summary>任务日志${logLines.length ? ` · ${logLines.length} 条` : ''}</summary><pre>${esc(logLines.join('\n') || '暂无日志')}</pre></details>
  </section>`;
}

function renderRecord(record: DesktopRecord, index: number): string {
  const config = PLATFORM_CONFIGS[record.platform];
  const searchContractText = existingSearchText(record).slice(0, 240);
  return `<article class="pack-card" data-action="select-record" data-index="${index}" data-search-text="${esc(searchContractText)}">
    <div class="card-top"><span class="platform-badge">${config.name}</span><span class="card-time">${esc(record.updatedAt || '更新时间未知')}</span></div>
    <h3>${esc(record.title)}</h3><p class="author">${esc(record.author)}</p>
    <p class="summary">${textOrUnknown(record.summary)}</p>
    <div class="chips">${record.versions.slice(0, 4).map((value) => `<span>${esc(value)}</span>`).join('')}${record.loaders.slice(0, 3).map((value) => `<span>${esc(value)}</span>`).join('')}${!record.versions.length && !record.loaders.length ? '<span class="muted-chip">兼容信息未知</span>' : ''}</div>
    <div class="card-footer"><span>查看来源证据</span><span class="arrow">↗</span></div>
  </article>`;
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
  return `<article class="release-item"><div class="release-head"><strong>${textOrUnknown(String(release.versionName || release.version_number || ''))}</strong><span>${esc(String(release.date || release.release_date || ''))}</span></div><div class="release-meta">${versions ? `Minecraft：${esc(versions)}` : ''}${loaders ? ` · Loader：${esc(loaders)}` : ''}</div>${notes ? `<p>${esc(notes)}</p>` : ''}${links ? `<div class="release-links">${links}</div>` : ''}</article>`;
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
    <div class="detail-section"><h3>适配摘要</h3><dl><div><dt>Minecraft</dt><dd>${vm.mcVersionsList.length ? esc(vm.mcVersionsList.join('、')) : '<span class="unknown">未知</span>'}</dd></div><div><dt>Loader</dt><dd>${record.loaders.length ? esc(record.loaders.join('、')) : '<span class="unknown">未知</span>'}</dd></div><div><dt>更新时间</dt><dd>${esc(formatTime(record.updatedAt))}</dd></div><div><dt>服务端</dt><dd>${esc(vm.envDisplay || `${record.environment.label}（${record.environment.certainty}）`)}</dd></div></dl></div>
    <div class="detail-section"><h3>来源证据</h3><div class="evidence-list">${record.evidence.length ? record.evidence.map((item) => `<div class="evidence-item"><span>${esc(item.label)}</span><strong>${textOrUnknown(item.value)}</strong></div>`).join('') : '<div class="empty-evidence">当前数据没有提供可核对的来源字段。</div>'}</div></div>
    ${renderCommentSection(record)}
    <div class="detail-section"><h3>版本详情 <span class="detail-submeta">${releases.length ? `记录数：${releases.length}` : ''}</span></h3><div class="release-list">${releaseHtml}</div></div>
    <div class="detail-section"><h3>已收录模组</h3>${modHtml}</div>
    <div class="detail-actions">${sourceUrl ? `<button class="button primary wide" data-action="open-source" data-url="${esc(sourceUrl)}">打开原站</button>` : '<div class="unknown-action">原站链接未知</div>'}${versionUrl && versionUrl !== sourceUrl ? `<button class="button secondary wide" data-action="open-source" data-url="${esc(versionUrl)}">打开版本详情</button>` : ''}</div>
  </aside></div>`;
}

function render(): void {
  const records = currentRecords();
  const versions = state.availableVersions;
  const loaders = state.availableLoaders;
  const data = state.data;
  const availableCount = data ? Object.values(data.platforms).filter((item) => item.available).length : 0;
  const selectedName = state.platform === 'all' ? '全部平台' : PLATFORM_CONFIGS[state.platform].name;
  root.innerHTML = `<div class="desktop-app">
    <header class="topbar"><div class="brand"><div class="brand-mark">✦</div><div><div class="brand-name">整合包工作台</div><div class="brand-caption">找包 · 判断适配 · 回到原站</div></div></div><div class="top-actions"><span class="data-status ${data?.hasData ? 'ready' : 'empty'}"><i></i>${data?.hasData ? `快照 ${esc(data.snapshotId || '')}` : '等待数据'}</span><button class="icon-button" data-action="toggle-theme" aria-label="切换主题">☼</button></div></header>
    <main class="workspace"><section class="hero"><div><span class="eyebrow">LOCAL DISCOVERY DESK</span><h1>从一个名字开始，找到适合你的整合包。</h1><p>搜索本地快照中的整合包，逐步查看版本、Loader、服务端和原始来源。缺少数据时，导入已有看板目录即可开始。</p></div><div class="hero-actions"><button class="button secondary" data-action="choose-data">${data?.hasData ? '更换数据目录' : '选择已有数据'}</button></div></section>
    <section class="search-panel"><div class="search-wrap"><span>⌕</span><input id="pack-search" value="${esc(state.query)}" placeholder="搜索整合包名称、作者或关键词" autocomplete="off"></div><select id="version-filter" class="field compact">${renderOptions(versions, state.version, 'Minecraft 版本')}</select><select id="loader-filter" class="field compact">${renderOptions(loaders, state.loader, 'Loader')}</select></section>
    <nav class="platform-nav" aria-label="平台筛选">${platformItems.map((item) => `<button class="platform-tab ${state.platform === item.id ? 'active' : ''}" data-action="set-platform" data-platform="${item.id}"><span>${item.icon}</span>${item.name}${item.id !== 'all' && data ? `<em>${data.platforms[item.id].count.toLocaleString('zh-CN')}</em>` : ''}</button>`).join('')}</nav>
    <div class="content-grid"><section class="results-column"><div class="results-heading"><div><span class="eyebrow">${esc(selectedName)}</span><h2>${state.loading ? '正在读取数据…' : state.query || state.version || state.loader ? '筛选结果' : '最近可用数据'}</h2></div><span class="result-count">${state.loading ? '' : `${records.length.toLocaleString('zh-CN')} / ${state.total.toLocaleString('zh-CN')}`}</span></div>${state.message ? `<div class="notice">${esc(state.message)}</div>` : ''}${!data?.hasData ? `<div class="empty-state"><div class="empty-icon">◌</div><h3>还没有本地数据快照</h3><p>选择现有的 <code>converted_output</code>、<code>build/frontend_preview</code> 或其 <code>data</code> 目录。应用不会把空数据伪装成成功。</p><button class="button primary" data-action="choose-data">选择数据目录</button></div>` : state.loading ? '<div class="loading-state">正在读取当前快照…</div>' : records.length ? `<div class="pack-grid">${records.map(renderRecord).join('')}</div>${state.hasMore ? `<div class="load-more"><button class="button secondary" data-action="load-more">加载更多（已显示 ${records.length.toLocaleString('zh-CN')} / ${state.total.toLocaleString('zh-CN')}）</button></div>` : ''}` : `<div class="empty-state compact-empty"><div class="empty-icon">⌕</div><h3>没有匹配的整合包</h3><p>换一个关键词或清除筛选条件。</p><button class="button secondary" data-action="clear-filters">清除筛选</button></div>`}</section>${updatePanel()}</div>
    <footer class="workspace-footer"><span>${availableCount ? `${availableCount}/6 个平台已有数据` : '数据来源未知'}</span><span>${data?.updatedAt ? `快照更新时间：${esc(formatTime(data.updatedAt))}` : '数据不会自动编造'}</span>${data?.canonicalReady ? '<span class="canonical-ok">Canonical 已校验</span>' : '<span>局部导入或原始数据不足，Canonical 状态未知</span>'}</footer></main>${detailPanel()}</div>`;
  bindEvents();
}

function bindEvents(): void {
  root.querySelectorAll<HTMLElement>('[data-action]').forEach((element) => element.addEventListener('click', (event) => void handleAction(element, event)));
  root.querySelector<HTMLInputElement>('#pack-search')?.addEventListener('input', (event) => {
    state.query = (event.target as HTMLInputElement).value;
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(() => void loadRecords(), 180);
  });
  root.querySelector<HTMLSelectElement>('#version-filter')?.addEventListener('change', (event) => { state.version = (event.target as HTMLSelectElement).value; void loadRecords(true); });
  root.querySelector<HTMLSelectElement>('#loader-filter')?.addEventListener('change', (event) => { state.loader = (event.target as HTMLSelectElement).value; void loadRecords(true); });
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

async function handleAction(element: HTMLElement, event?: Event): Promise<void> {
  const action = element.dataset.action;
  if (action === 'set-platform') {
    state.platform = (element.dataset.platform || 'all') as FilterPlatform;
    state.selected = null;
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
  } else if (action === 'start-update') {
    const platform = root.querySelector<HTMLSelectElement>('#update-platform')?.value as Platform | undefined;
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
  } else if (action === 'select-record') {
    const index = Number(element.dataset.index || '-1');
    state.selected = state.records[index] || null;
    state.comments = { sourceId: state.selected?.sourceId || '', loading: false, available: false, pageCount: 0, comments: [], sourceFile: null, error: '' };
    render();
    if (state.selected) await loadComments(state.selected);
  } else if (action === 'close-detail') {
    if (event && event.target !== element) return;
    state.selected = null;
    state.comments = { sourceId: '', loading: false, available: false, pageCount: 0, comments: [], sourceFile: null, error: '' };
    render();
  } else if (action === 'open-source') {
    const url = element.dataset.url;
    if (url) await window.desktopApi.openExternal(url);
  } else if (action === 'toggle-theme') {
    const next = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
    document.documentElement.dataset.theme = next;
    localStorage.setItem('mcmod-desktop-theme', next);
  } else if (action === 'clear-filters') {
    state.query = ''; state.version = ''; state.loader = ''; await loadRecords(true);
  }
}

async function loadRecords(reset = true): Promise<void> {
  if (reset) {
    state.page = 1;
    state.records = [];
  } else {
    state.page += 1;
  }
  state.loading = true;
  render();
  const platforms = state.platform === 'all' ? ALL_PLATFORMS : [state.platform];
  try {
    const results = await Promise.all(platforms.map((platform) => window.desktopApi.getPlatformRecords(platform, {
      query: state.query,
      version: state.version,
      loader: state.loader,
      page: state.page,
      pageSize: state.pageSize,
    })));
    const nextRecords = results.flatMap((result) => result.records);
    state.records = reset ? nextRecords : [...state.records, ...nextRecords];
    state.total = results.reduce((sum, result) => sum + result.total, 0);
    state.availableVersions = [...new Set(results.flatMap((result) => result.availableVersions || []))].sort((a, b) => a.localeCompare(b, 'zh-CN'));
    state.availableLoaders = [...new Set(results.flatMap((result) => result.availableLoaders || []))].sort((a, b) => a.localeCompare(b, 'zh-CN'));
    state.hasMore = state.records.length < state.total;
    state.loading = false;
    render();
  } catch (error) {
    state.loading = false;
    state.message = error instanceof Error ? error.message : String(error);
    render();
  }
}

export async function initDesktopShell(): Promise<void> {
  root = document.querySelector<HTMLElement>('#desktop-root')!;
  const savedTheme = localStorage.getItem('mcmod-desktop-theme');
  if (savedTheme === 'light' || savedTheme === 'dark') document.documentElement.dataset.theme = savedTheme;
  render();
  try {
    const initial = await window.desktopApi.getState();
    state.data = initial.data;
    state.update = initial.update;
    await loadRecords();
  } catch (error) {
    state.loading = false;
    state.message = error instanceof Error ? error.message : String(error);
    render();
  }
  window.desktopApi.onUpdateStatus((update) => {
    state.update = update;
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

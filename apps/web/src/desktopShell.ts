import { ALL_PLATFORMS, PLATFORM_CONFIGS } from './data/platformRegistry';
import type { Platform } from './domain/types';

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
  evidence: Array<{ label: string; value: string }>;
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
  getPlatformRecords: (platform: Platform, query?: string) => Promise<{ platform: Platform; total: number; records: DesktopRecord[]; error?: string | null }>;
  chooseDataDirectory: () => Promise<{ cancelled: boolean; data?: DesktopDataState }>;
  startUpdate: (platform: Platform, options?: { limit?: number; pages?: number; until?: string }) => Promise<DesktopUpdateStatus>;
  cancelUpdate: () => Promise<{ cancelled: boolean }>;
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
  selected: null as DesktopRecord | null,
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
  const version = state.version.toLocaleLowerCase();
  const loader = state.loader.toLocaleLowerCase();
  return state.records.filter((record) => {
    const versionMatch = !version || record.versions.some((item) => item.toLocaleLowerCase() === version);
    const loaderMatch = !loader || record.loaders.some((item) => item.toLocaleLowerCase() === loader);
    return versionMatch && loaderMatch;
  });
}

function filterOptions(records: DesktopRecord[], selector: 'versions' | 'loaders'): string[] {
  const values = new Set<string>();
  for (const record of records) for (const value of record[selector]) if (value) values.add(value);
  return [...values].sort((a, b) => a.localeCompare(b, 'zh-CN')).slice(0, 80);
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
  return `<article class="pack-card" data-action="select-record" data-index="${index}">
    <div class="card-top"><span class="platform-badge">${config.name}</span><span class="card-time">${esc(record.updatedAt || '更新时间未知')}</span></div>
    <h3>${esc(record.title)}</h3><p class="author">${esc(record.author)}</p>
    <p class="summary">${textOrUnknown(record.summary)}</p>
    <div class="chips">${record.versions.slice(0, 4).map((value) => `<span>${esc(value)}</span>`).join('')}${record.loaders.slice(0, 3).map((value) => `<span>${esc(value)}</span>`).join('')}${!record.versions.length && !record.loaders.length ? '<span class="muted-chip">兼容信息未知</span>' : ''}</div>
    <div class="card-footer"><span>查看来源证据</span><span class="arrow">↗</span></div>
  </article>`;
}

function detailPanel(): string {
  const record = state.selected;
  if (!record) return '';
  return `<div class="detail-backdrop" data-action="close-detail"><aside class="detail-panel" data-detail-panel>
    <button class="icon-button close-detail" data-action="close-detail" aria-label="关闭详情">×</button>
    <span class="eyebrow">${esc(PLATFORM_CONFIGS[record.platform].name)} · 原始来源</span><h2>${esc(record.title)}</h2><p class="detail-author">${esc(record.author)}</p>
    <div class="detail-section"><h3>适配摘要</h3><dl><div><dt>Minecraft</dt><dd>${record.versions.length ? esc(record.versions.join('、')) : '<span class="unknown">未知</span>'}</dd></div><div><dt>Loader</dt><dd>${record.loaders.length ? esc(record.loaders.join('、')) : '<span class="unknown">未知</span>'}</dd></div><div><dt>更新时间</dt><dd>${esc(formatTime(record.updatedAt))}</dd></div></dl></div>
    <div class="detail-section"><h3>来源证据</h3><div class="evidence-list">${record.evidence.length ? record.evidence.map((item) => `<div class="evidence-item"><span>${esc(item.label)}</span><strong>${textOrUnknown(item.value)}</strong></div>`).join('') : '<div class="empty-evidence">当前数据没有提供可核对的来源字段。</div>'}</div></div>
    <div class="detail-section"><h3>简介</h3><p class="detail-summary">${textOrUnknown(record.summary)}</p></div>
    ${record.url ? `<button class="button primary wide" data-action="open-source" data-url="${esc(record.url)}">打开原站</button>` : '<div class="unknown-action">原站链接未知</div>'}
  </aside></div>`;
}

function render(): void {
  const records = currentRecords();
  const versions = filterOptions(state.records, 'versions');
  const loaders = filterOptions(state.records, 'loaders');
  const data = state.data;
  const availableCount = data ? Object.values(data.platforms).filter((item) => item.available).length : 0;
  const selectedName = state.platform === 'all' ? '全部平台' : PLATFORM_CONFIGS[state.platform].name;
  root.innerHTML = `<div class="desktop-app">
    <header class="topbar"><div class="brand"><div class="brand-mark">✦</div><div><div class="brand-name">整合包工作台</div><div class="brand-caption">找包 · 判断适配 · 回到原站</div></div></div><div class="top-actions"><span class="data-status ${data?.hasData ? 'ready' : 'empty'}"><i></i>${data?.hasData ? `快照 ${esc(data.snapshotId || '')}` : '等待数据'}</span><button class="icon-button" data-action="toggle-theme" aria-label="切换主题">☼</button></div></header>
    <main class="workspace"><section class="hero"><div><span class="eyebrow">LOCAL DISCOVERY DESK</span><h1>从一个名字开始，找到适合你的整合包。</h1><p>搜索本地快照中的整合包，逐步查看版本、Loader、服务端和原始来源。缺少数据时，导入已有看板目录即可开始。</p></div><div class="hero-actions"><button class="button secondary" data-action="choose-data">${data?.hasData ? '更换数据目录' : '选择已有数据'}</button></div></section>
    <section class="search-panel"><div class="search-wrap"><span>⌕</span><input id="pack-search" value="${esc(state.query)}" placeholder="搜索整合包名称、作者或关键词" autocomplete="off"></div><select id="version-filter" class="field compact">${renderOptions(versions, state.version, 'Minecraft 版本')}</select><select id="loader-filter" class="field compact">${renderOptions(loaders, state.loader, 'Loader')}</select></section>
    <nav class="platform-nav" aria-label="平台筛选">${platformItems.map((item) => `<button class="platform-tab ${state.platform === item.id ? 'active' : ''}" data-action="set-platform" data-platform="${item.id}"><span>${item.icon}</span>${item.name}${item.id !== 'all' && data ? `<em>${data.platforms[item.id].count.toLocaleString('zh-CN')}</em>` : ''}</button>`).join('')}</nav>
    <div class="content-grid"><section class="results-column"><div class="results-heading"><div><span class="eyebrow">${esc(selectedName)}</span><h2>${state.loading ? '正在读取数据…' : state.query || state.version || state.loader ? '筛选结果' : '最近可用数据'}</h2></div><span class="result-count">${state.loading ? '' : `${records.length.toLocaleString('zh-CN')} / ${state.total.toLocaleString('zh-CN')}`}</span></div>${state.message ? `<div class="notice">${esc(state.message)}</div>` : ''}${!data?.hasData ? `<div class="empty-state"><div class="empty-icon">◌</div><h3>还没有本地数据快照</h3><p>选择现有的 <code>converted_output</code>、<code>build/frontend_preview</code> 或其 <code>data</code> 目录。应用不会把空数据伪装成成功。</p><button class="button primary" data-action="choose-data">选择数据目录</button></div>` : state.loading ? '<div class="loading-state">正在读取当前快照…</div>' : records.length ? `<div class="pack-grid">${records.map(renderRecord).join('')}</div>` : `<div class="empty-state compact-empty"><div class="empty-icon">⌕</div><h3>没有匹配的整合包</h3><p>换一个关键词或清除筛选条件。</p><button class="button secondary" data-action="clear-filters">清除筛选</button></div>`}</section>${updatePanel()}</div>
    <footer class="workspace-footer"><span>${availableCount ? `${availableCount}/6 个平台已有数据` : '数据来源未知'}</span><span>${data?.updatedAt ? `快照更新时间：${esc(formatTime(data.updatedAt))}` : '数据不会自动编造'}</span>${data?.canonicalReady ? '<span class="canonical-ok">Canonical 已校验</span>' : '<span>局部导入或原始数据不足，Canonical 状态未知</span>'}</footer></main>${detailPanel()}</div>`;
  bindEvents();
}

function bindEvents(): void {
  root.querySelectorAll<HTMLElement>('[data-action]').forEach((element) => element.addEventListener('click', () => void handleAction(element)));
  root.querySelector<HTMLInputElement>('#pack-search')?.addEventListener('input', (event) => {
    state.query = (event.target as HTMLInputElement).value;
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(() => void loadRecords(), 180);
  });
  root.querySelector<HTMLSelectElement>('#version-filter')?.addEventListener('change', (event) => { state.version = (event.target as HTMLSelectElement).value; render(); });
  root.querySelector<HTMLSelectElement>('#loader-filter')?.addEventListener('change', (event) => { state.loader = (event.target as HTMLSelectElement).value; render(); });
}

async function handleAction(element: HTMLElement): Promise<void> {
  const action = element.dataset.action;
  if (action === 'set-platform') {
    state.platform = (element.dataset.platform || 'all') as FilterPlatform;
    state.selected = null;
    await loadRecords();
  } else if (action === 'choose-data') {
    state.message = '正在读取所选目录…';
    render();
    try {
      const result = await window.desktopApi.chooseDataDirectory();
      if (!result.cancelled && result.data) {
        state.data = result.data;
        state.message = '';
        await loadRecords();
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
  } else if (action === 'select-record') {
    const index = Number(element.dataset.index || '-1');
    state.selected = currentRecords()[index] || null;
    render();
  } else if (action === 'close-detail') {
    if (element.hasAttribute('data-detail-panel')) return;
    state.selected = null;
    render();
  } else if (action === 'open-source') {
    const url = element.dataset.url;
    if (url) await window.desktopApi.openExternal(url);
  } else if (action === 'toggle-theme') {
    const next = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
    document.documentElement.dataset.theme = next;
    localStorage.setItem('mcmod-desktop-theme', next);
  } else if (action === 'clear-filters') {
    state.query = ''; state.version = ''; state.loader = ''; await loadRecords();
  }
}

async function loadRecords(): Promise<void> {
  state.loading = true;
  render();
  const platforms = state.platform === 'all' ? ALL_PLATFORMS : [state.platform];
  try {
    const results = await Promise.all(platforms.map((platform) => window.desktopApi.getPlatformRecords(platform, state.query)));
    state.records = results.flatMap((result) => result.records);
    state.total = results.reduce((sum, result) => sum + result.total, 0);
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
      void window.desktopApi.getState().then(async (next) => { state.data = next.data; await loadRecords(); });
    }
  });
  window.desktopApi.onUpdateLog((line) => {
    state.logs = [...state.logs, line].slice(-200);
    render();
  });
  window.desktopApi.onDataChanged((data) => {
    state.data = data;
    void loadRecords();
  });
}

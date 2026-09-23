import type { Platform } from './domain/types';
import type { DesktopApi, DesktopDataState, DesktopCommentsResult, DesktopUpdateStatus, DesktopAuditResult, PersonalStatus } from './desktopShell';

async function request<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  const method = init?.method || 'GET';
  const target = String(input);
  let response: Response;
  try {
    response = await fetch(input, { ...init, headers: { 'content-type': 'application/json', ...(init?.headers || {}) } });
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    throw new Error(`无法连接本地浏览服务（${method} ${target}）：${detail}`);
  }
  let text: string;
  try {
    text = await response.text();
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    throw new Error(`读取本地浏览服务响应失败（${method} ${target}）：${detail}`);
  }
  let payload: unknown = null;
  try { payload = text ? JSON.parse(text) : null; } catch { payload = text; }
  if (!response.ok) {
    const message = payload && typeof payload === 'object' && 'error' in payload ? String(payload.error) : `${response.status} ${response.statusText}`;
    throw new Error(message);
  }
  return payload as T;
}

let events: EventSource | null = null;
const statusListeners = new Set<(status: DesktopUpdateStatus) => void>();
const logListeners = new Set<(line: string) => void>();
const dataListeners = new Set<(data: DesktopDataState) => void>();

function ensureEvents(): void {
  if (events) return;
  events = new EventSource('/api/events');
  events.addEventListener('status', (event) => {
    const status = JSON.parse((event as MessageEvent).data);
    for (const listener of statusListeners) listener(status);
  });
  events.addEventListener('log', (event) => {
    const line = JSON.parse((event as MessageEvent).data);
    for (const listener of logListeners) listener(String(line));
  });
  events.addEventListener('data', (event) => {
    const data = JSON.parse((event as MessageEvent).data);
    for (const listener of dataListeners) listener(data);
  });
}

function subscribe<T>(listeners: Set<(value: T) => void>, callback: (value: T) => void): () => void {
  ensureEvents();
  listeners.add(callback);
  return () => listeners.delete(callback);
}

export function installBrowserApi(): void {
  if (window.desktopApi) return;
  const api: DesktopApi = {
    getState: () => request<{ data: DesktopDataState; update: DesktopUpdateStatus }>('/api/state'),
    getPersonalLibrary: () => request<{ schema: number; entries: Record<string, PersonalStatus> }>('/api/library'),
    getMissingPersonalSources: () => request<{ entries: Record<string, PersonalStatus> }>('/api/library/missing'),
    restorePersonalLibrary: (payload) => request<{ restored: number; 'skipped-conflict': number; invalid: number }>('/api/library/restore', { method: 'POST', body: JSON.stringify(payload) }),
    updatePersonalStatus: (platform, sourceId, patch) => request<{ key: string; status: PersonalStatus }>(`/api/library/${encodeURIComponent(platform)}/${encodeURIComponent(sourceId)}`, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    }),
    getAuditDiff: () => request<DesktopAuditResult>('/api/audit'),
    getPlatformRecords: (platform, options = {}) => {
      const params = new URLSearchParams({
        query: options.query || '',
        version: options.version || '',
        loader: options.loader || '',
        category: options.category || '',
        pan: options.pan || '',
        dateRange: options.dateRange || '',
        serverOnly: options.serverOnly ? 'true' : 'false',
        personalStatus: options.personalStatus || '',
        sort: options.sort || '',
        page: String(options.page || 1),
        pageSize: String(options.pageSize || 48),
      });
      for (const mod of options.includedMods || []) params.append('includedMod', mod);
      if (options.includedModsExclude) params.set('includedModsExclude', 'true');
      for (const category of options.gameplayCategories || []) params.append('gameplayCategory', category);
      if (options.gameplayCategoriesExclude) params.set('gameplayCategoriesExclude', 'true');
      return request<Awaited<ReturnType<DesktopApi['getPlatformRecords']>>>(`/api/platforms/${encodeURIComponent(platform)}/records?${params.toString()}`);
    },
    getPlatformComments: (platform, sourceId) => request<DesktopCommentsResult>(`/api/platforms/${encodeURIComponent(platform)}/comments/${encodeURIComponent(sourceId)}`),
    chooseDataDirectory: async () => {
      const selected = window.prompt('输入本地看板数据目录路径（可选 data、converted_output 或 build/frontend_preview）');
      if (!selected?.trim()) return { cancelled: true };
      const result = await request<{ cancelled: boolean; data?: DesktopDataState }>('/api/data/import', {
        method: 'POST',
        body: JSON.stringify({ path: selected.trim() }),
      });
      return result;
    },
    startUpdate: (platform: Platform, options = {}) => request<DesktopUpdateStatus>('/api/updates', { method: 'POST', body: JSON.stringify({ platform, options }) }),
    cancelUpdate: () => request<{ cancelled: boolean; reason?: string }>('/api/updates/cancel', { method: 'POST', body: '{}' }),
    openExternal: async (url) => {
      const parsed = new URL(url);
      if (!['http:', 'https:'].includes(parsed.protocol)) throw new Error('只允许打开 http/https 原站链接');
      const opened = window.open(parsed.toString(), '_blank', 'noopener,noreferrer');
      return { opened: Boolean(opened) };
    },
    onUpdateStatus: (callback) => subscribe(statusListeners, callback),
    onUpdateLog: (callback) => subscribe(logListeners, callback),
    onDataChanged: (callback) => subscribe(dataListeners, callback),
  };
  window.desktopApi = api;
}

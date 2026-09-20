import type { Platform } from './domain/types';
import type { DesktopApi, DesktopDataState, DesktopCommentsResult, DesktopUpdateStatus } from './desktopShell';

async function request<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  const response = await fetch(input, { ...init, headers: { 'content-type': 'application/json', ...(init?.headers || {}) } });
  const text = await response.text();
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
    getPlatformRecords: (platform, options = {}) => {
      const params = new URLSearchParams({
        query: options.query || '',
        version: options.version || '',
        loader: options.loader || '',
        page: String(options.page || 1),
        pageSize: String(options.pageSize || 48),
      });
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

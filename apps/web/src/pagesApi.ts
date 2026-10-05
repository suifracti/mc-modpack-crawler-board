import type { DesktopApi, DesktopRecord, PersonalStatus, DesktopDataState } from './desktopShell';
import type { Platform } from './domain/types';
import type { RecordPreview } from './domain/recordPreview';
import { queryStaticRecords } from './pagesQuery';
import { installPublicAssociations } from './domain/crossPlatformLinkage';

const storageKey = 'mc-pages-personal-v1';
function entries(): Record<string, PersonalStatus> {
  try { return JSON.parse(localStorage.getItem(storageKey) || '{}'); } catch { return {}; }
}
const caches = new Map<string, Promise<{ result: { records: DesktopRecord[]; sourceFile: null; error: null } }>>();
type PreviewIndex = { schema: number; platforms: Partial<Record<Platform, Record<string, string>>> };
let previewIndex: Promise<PreviewIndex> | undefined;
const previewFiles = new Map<string, Promise<Record<string, RecordPreview>>>();
async function loadPreview(platform: Platform, sourceId: string): Promise<RecordPreview | undefined> {
  if (!previewIndex) {
    previewIndex = fetch(new URL('data/previews.json', document.baseURI)).then(async response => {
      if (!response.ok) throw new Error(`正文存档索引加载失败（${response.status}）`);
      const index = await response.json() as PreviewIndex;
      if (index.schema !== 1 || !index.platforms) throw new Error('正文存档索引格式不匹配');
      return index;
    });
    previewIndex.catch(() => { previewIndex = undefined; });
  }
  const file = (await previewIndex).platforms[platform]?.[sourceId];
  if (!file) return undefined;
  if (!new RegExp(`^preview-${platform}-\\d+\\.json\\.gz$`).test(file)) throw new Error('正文存档文件路径无效');
  let pending = previewFiles.get(file);
  if (!pending) {
    pending = fetch(new URL(`data/${file}`, document.baseURI)).then(async response => {
      if (!response.ok) throw new Error(`正文存档加载失败（${response.status}）`);
      const bytes = new Uint8Array(await response.arrayBuffer());
      const blob = new Blob([bytes]);
      const stream = bytes[0] === 0x1f && bytes[1] === 0x8b ? blob.stream().pipeThrough(new DecompressionStream('gzip')) : blob.stream();
      return new Response(stream).json() as Promise<Record<string, RecordPreview>>;
    });
    previewFiles.set(file, pending);
    pending.catch(() => { previewFiles.delete(file); });
  }
  const preview = (await pending)[sourceId];
  if (preview && (preview.platform !== platform || preview.sourceId !== sourceId)) throw new Error('正文存档来源不匹配');
  return preview;
}
async function load(platform: Platform) {
  let pending = caches.get(platform);
  if (!pending) {
    let completed = 0;
    let total = 0;
    let failed = false;
    const progress = (phase: 'loading' | 'ready' | 'failed') => {
      if (failed && phase !== 'failed') return;
      document.dispatchEvent(new CustomEvent('mc-pages-load-progress', { detail: { platform, phase, completed, total } }));
    };
    progress('loading');
    pending = fetch(new URL(`data/${platform}.json`, document.baseURI)).then(async response => {
      if (!response.ok) throw new Error(`公开数据加载失败：${platform}（${response.status}）`);
      const index = await response.json() as { files: string[] };
      total = index.files.length;
      progress('loading');
      const chunks = await Promise.all(index.files.map(async file => {
        const chunk = await fetch(new URL(`data/${file}`, document.baseURI));
        if (!chunk.ok) throw new Error(`公开数据分片加载失败：${file}`);
        if (!file.endsWith('.gz')) {
          const records = await chunk.json() as DesktopRecord[];
          completed += 1; progress('loading');
          return records;
        }
        const bytes = new Uint8Array(await chunk.arrayBuffer());
        const blob = new Blob([bytes]);
        const body = bytes[0] === 0x1f && bytes[1] === 0x8b
          ? blob.stream().pipeThrough(new DecompressionStream('gzip')) : blob.stream();
        const records = await new Response(body).json() as DesktopRecord[];
        completed += 1; progress('loading');
        return records;
      }));
      progress('ready');
      return { result: { records: chunks.flat(), sourceFile: null, error: null } };
    });
    caches.set(platform, pending);
    pending.catch(() => {
      failed = true;
      caches.delete(platform);
      progress('failed');
    });
  }
  return pending;
}
const unsupported = async (): Promise<never> => { throw new Error('静态站不提供采集、服务和快照管理，请使用桌面应用。'); };
const emptyUpdates = () => ({ events: [], unreadCount: 0, unknown: [] });
export function installPagesApi(): void {
  document.documentElement.dataset.staticSite = 'true';
  const api: DesktopApi & { staticMode: boolean } = {
    staticMode: true,
    getState: async () => {
      const relations = fetch(new URL('data/relations.json.gz', document.baseURI)).then(async response => {
        if (!response.ok) throw new Error(`关联索引加载失败（${response.status}）`);
        const bytes = new Uint8Array(await response.arrayBuffer());
        const blob = new Blob([bytes]);
        const stream = bytes[0] === 31 && bytes[1] === 139 ? blob.stream().pipeThrough(new DecompressionStream('gzip')) : blob.stream();
        installPublicAssociations(await new Response(stream).json());
      });
      const response = await fetch(new URL('data/manifest.json', document.baseURI));
      if (!response.ok) throw new Error('公开数据清单加载失败');
      const data = await response.json() as DesktopDataState;
      await relations.catch(() => { /* Browsing remains available; UI states the narrower loaded-record scope. */ });
      return { data, update: { state: 'idle', taskId: null, platform: null, phase: '', processed: 0, total: null, logs: [] } };
    },
    getPersonalLibrary: async () => ({ schema: 1, entries: entries() }),
    getMissingPersonalSources: async () => ({ entries: {} }),
    getFavoriteUpdates: async () => emptyUpdates(),
    markFavoriteUpdateRead: async () => emptyUpdates(),
    restorePersonalLibrary: unsupported,
    updatePersonalStatus: async (platform, sourceId, patch) => {
      const key = `${platform}:${sourceId}`, library = entries();
      const previous: Partial<PersonalStatus> = library[key] || {};
      const status = { favorite: false, wantToPlay: false, played: false, rating: null, note: '', ...previous, ...patch, updatedAt: new Date().toISOString() };
      library[key] = status;
      localStorage.setItem(storageKey, JSON.stringify(library));
      return { key, status };
    },
    getAuditDiff: async () => ({ available: false, message: '静态站展示当前公开数据，不发布本地运行审计。', generated_at: null, stats: null, added: [], updated: [], removed: [], version_gained: [] }),
    getPlatformRecords: async (platform, options) => queryStaticRecords(platform, options, await load(platform), entries()),
    getPlatformComments: async (platform, sourceId) => {
      const record = (await load(platform)).result.records.find(item => item.sourceId === sourceId);
      const raw = record?.raw || {};
      const comments = Array.isArray(raw.comments) ? raw.comments : typeof raw.pinned_comment === 'string' ? [{ text: raw.pinned_comment }] : [];
      return { platform, sourceId, available: comments.length > 0, sourceFile: null, pageCount: comments.length, comments };
    },
    getPreviewVersions: async (platform, sourceId) => {
      const record = (await load(platform as Platform)).result.records.find(item => item.sourceId === sourceId);
      const preview = await loadPreview(platform as Platform, sourceId);
      if (preview && preview.sourceUrl !== record?.url) throw new Error('正文存档链接与当前记录不匹配');
      // Current releases take priority; append archived versions without changing catalog metadata.
      const versions = [...(record?.releases || [])];
      const versionKey = (item: Record<string, unknown>) => String(item.versionName || item.version_number || item.version || item.name || '') + ':' + String(item.date || item.date_published || '');
      const existing = new Set(versions.map(versionKey));
      for (const release of preview?.releases || []) if (!existing.has(versionKey(release))) { versions.push(release); existing.add(versionKey(release)); }
      return { versions, fetchedAt: preview?.archivedAt || '', preview };
    },
    getDataLibrary: unsupported, chooseDataDirectory: unsupported, activateDataSnapshot: unsupported,
    deleteDataSnapshot: unsupported, exportActiveData: unsupported, openDataDirectory: unsupported,
    startUpdate: unsupported, cancelUpdate: unsupported,
    openExternal: async url => {
      const parsed = new URL(url);
      if (!['http:', 'https:'].includes(parsed.protocol)) throw new Error('只支持公开网页链接');
      window.open(parsed.href, '_blank', 'noopener,noreferrer'); return { opened: true };
    },
    onUpdateStatus: () => () => {}, onUpdateLog: () => () => {}, onDataChanged: () => () => {},
  };
  window.desktopApi = api;
}

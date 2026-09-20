const fs = require('node:fs');
const fsp = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');
const os = require('node:os');
const {
  ALL_PLATFORMS,
  COMMON_DATA_FILES,
  PLATFORM_CONFIGS,
  assertPlatform,
  findSidecar,
  readPlatformRecords,
  normaliseRecord,
  matchesSearchDocument,
} = require('./platforms.cjs');

const SNAPSHOT_SCHEMA = 1;
const SAFE_DATA_FILE = /^[a-zA-Z0-9_.-]+\.(?:js|json|jsonl)$/;

function nowIso() {
  return new Date().toISOString();
}

async function exists(filePath) {
  try {
    await fsp.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function writeJsonAtomic(filePath, value) {
  const tempPath = `${filePath}.${process.pid}.${crypto.randomBytes(4).toString('hex')}.tmp`;
  await fsp.writeFile(tempPath, JSON.stringify(value, null, 2), 'utf8');
  await fsp.rename(tempPath, filePath);
}

async function copyIfExists(source, destination) {
  if (await exists(source)) {
    await fsp.mkdir(path.dirname(destination), { recursive: true });
    await fsp.copyFile(source, destination);
    return true;
  }
  return false;
}

function parseQueryOptions(queryOrOptions) {
  if (typeof queryOrOptions === 'string' || queryOrOptions === undefined || queryOrOptions === null) {
    return { query: String(queryOrOptions || ''), version: '', loader: '', page: 1, pageSize: 48 };
  }
  const options = queryOrOptions || {};
  const page = Number.isInteger(Number(options.page)) ? Math.max(1, Number(options.page)) : 1;
  const pageSize = Number.isInteger(Number(options.pageSize)) ? Math.min(500, Math.max(1, Number(options.pageSize))) : 48;
  return {
    query: String(options.query || ''),
    version: String(options.version || ''),
    loader: String(options.loader || ''),
    page,
    pageSize,
  };
}

function optionValues(records, key) {
  const values = new Set();
  for (const record of records) for (const value of record[key] || []) if (value) values.add(String(value));
  return [...values].sort((a, b) => a.localeCompare(b, 'zh-CN'));
}

async function readMcmodComments(dataDir, sourceId) {
  if (!/^\d+$/.test(String(sourceId || ''))) return { available: false, sourceFile: null, pageCount: 0, comments: [] };
  const base = path.join(dataDir, 'comments', String(sourceId));
  const candidates = [`${base}.js`, `${base}.json`];
  for (const candidate of candidates) {
    if (!(await exists(candidate))) continue;
    try {
      const source = await fsp.readFile(candidate, 'utf8');
      let payload;
      if (candidate.endsWith('.json')) {
        payload = JSON.parse(source);
      } else {
        const match = source.match(/window\.__registerCommentData\(\s*["']?\d+["']?\s*,\s*([\s\S]+)\)\s*;?\s*$/);
        if (!match) throw new Error('评论 sidecar 格式无法识别');
        payload = JSON.parse(match[1]);
      }
      const comments = Array.isArray(payload) ? payload : Array.isArray(payload?.comments) ? payload.comments : [];
      const pageCount = Number(payload?.page_count ?? payload?.pageCount ?? payload?.count ?? comments.length) || comments.length;
      return { available: true, sourceFile: path.relative(dataDir, candidate), pageCount, comments };
    } catch (error) {
      return { available: false, sourceFile: path.relative(dataDir, candidate), pageCount: 0, comments: [], error: error instanceof Error ? error.message : String(error) };
    }
  }
  return { available: false, sourceFile: null, pageCount: 0, comments: [] };
}

async function copyDirectoryContents(sourceDir, destinationDir, predicate = () => true) {
  if (!(await exists(sourceDir))) return 0;
  await fsp.mkdir(destinationDir, { recursive: true });
  let copied = 0;
  for (const entry of await fsp.readdir(sourceDir, { withFileTypes: true })) {
    const source = path.join(sourceDir, entry.name);
    const destination = path.join(destinationDir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === 'vendor' || entry.name === '.git') continue;
      copied += await copyDirectoryContents(source, destination, predicate);
    } else if (predicate(entry.name)) {
      await fsp.copyFile(source, destination);
      copied += 1;
    }
  }
  return copied;
}

class DataStore {
  constructor(rootDir) {
    this.rootDir = path.resolve(rootDir);
    this.snapshotsDir = path.join(this.rootDir, 'snapshots');
    this.incomingDir = path.join(this.rootDir, 'incoming');
    this.activePointer = path.join(this.rootDir, 'active.json');
    // Active snapshots are immutable after the pointer switch. Keep the
    // parsed sidecars so every browser request does not repeat the same
    // multi-megabyte parse and normalisation work.
    this.platformCache = new Map();
  }

  async init() {
    await fsp.mkdir(this.snapshotsDir, { recursive: true });
    await fsp.mkdir(this.incomingDir, { recursive: true });
    const pointer = await this.readActivePointer();
    if (pointer && !(await exists(this.snapshotDataDir(pointer.snapshotId)))) {
      await fsp.rm(this.activePointer, { force: true });
    }
    return this.getState();
  }

  async readActivePointer() {
    try {
      const parsed = JSON.parse(await fsp.readFile(this.activePointer, 'utf8'));
      if (!parsed || typeof parsed.snapshotId !== 'string') return null;
      return parsed;
    } catch {
      return null;
    }
  }

  snapshotDataDir(snapshotId) {
    return path.join(this.snapshotsDir, snapshotId, 'data');
  }

  snapshotRawDir(snapshotId) {
    return path.join(this.snapshotsDir, snapshotId, 'crawler_output');
  }

  readCachedPlatform(snapshotId, platform) {
    const dataDir = this.snapshotDataDir(snapshotId);
    const sidecar = findSidecar(dataDir, platform);
    let signature = 'missing';
    if (sidecar) {
      try {
        const stat = fs.statSync(sidecar);
        signature = `${sidecar}:${stat.size}:${stat.mtimeMs}`;
      } catch {
        signature = `${sidecar}:unreadable`;
      }
    }
    const key = `${snapshotId}:${platform}`;
    const cached = this.platformCache.get(key);
    if (cached && cached.signature === signature) return cached;
    const result = readPlatformRecords(dataDir, platform);
    const entry = { signature, result, normalized: null };
    this.platformCache.set(key, entry);
    return entry;
  }

  async getActiveSnapshot() {
    const pointer = await this.readActivePointer();
    if (!pointer) return null;
    try {
      const manifest = JSON.parse(await fsp.readFile(path.join(this.snapshotsDir, pointer.snapshotId, 'manifest.json'), 'utf8'));
      return { ...manifest, snapshotId: pointer.snapshotId };
    } catch {
      return { snapshotId: pointer.snapshotId };
    }
  }

  async getState() {
    const active = await this.getActiveSnapshot();
    const platforms = {};
    for (const platform of ALL_PLATFORMS) {
      const result = active ? this.readCachedPlatform(active.snapshotId, platform).result : { records: [], sourceFile: null, error: null };
      platforms[platform] = {
        ...PLATFORM_CONFIGS[platform],
        count: result.records.length,
        sourceFile: result.sourceFile,
        error: result.error,
        available: Boolean(result.sourceFile && !result.error),
      };
    }
    return {
      schema: SNAPSHOT_SCHEMA,
      hasData: Boolean(active),
      snapshotId: active?.snapshotId || null,
      updatedAt: active?.updatedAt || null,
      source: active?.source || null,
      canonicalReady: active?.canonicalReady ?? false,
      dataRoot: this.rootDir,
      platforms,
    };
  }

  async getPlatformRecords(platform, queryOrOptions = '') {
    assertPlatform(platform);
    const options = parseQueryOptions(queryOrOptions);
    const active = await this.getActiveSnapshot();
    if (!active) return { platform, total: 0, records: [], sourceFile: null, page: options.page, pageSize: options.pageSize, availableVersions: [], availableLoaders: [] };
    const cached = this.readCachedPlatform(active.snapshotId, platform);
    const result = cached.result;
    if (!cached.normalized) cached.normalized = result.records.map((record, index) => normaliseRecord(platform, record, index));
    const normalized = cached.normalized;
    const searched = options.query.trim()
      ? normalized.filter((record) => matchesSearchDocument(record.searchDocument, options.query))
      : normalized;
    const version = options.version.trim().toLocaleLowerCase();
    const loader = options.loader.trim().toLocaleLowerCase();
    const filtered = searched.filter((record) => {
      const versionMatch = !version || record.versions.some((item) => item.toLocaleLowerCase() === version);
      const loaderMatch = !loader || record.loaders.some((item) => item.toLocaleLowerCase() === loader);
      return versionMatch && loaderMatch;
    });
    const offset = (options.page - 1) * options.pageSize;
    return {
      platform,
      total: filtered.length,
      page: options.page,
      pageSize: options.pageSize,
      records: filtered.slice(offset, offset + options.pageSize),
      availableVersions: optionValues(searched, 'versions'),
      availableLoaders: optionValues(searched, 'loaders'),
      sourceFile: result.sourceFile,
      error: result.error,
    };
  }

  async getPlatformComments(platform, sourceId) {
    assertPlatform(platform);
    const active = await this.getActiveSnapshot();
    if (!active) return { platform, sourceId: String(sourceId || ''), available: false, sourceFile: null, pageCount: 0, comments: [] };
    if (platform !== 'mcmod') return { platform, sourceId: String(sourceId || ''), available: false, sourceFile: null, pageCount: 0, comments: [] };
    return {
      platform,
      sourceId: String(sourceId || ''),
      ...(await readMcmodComments(this.snapshotDataDir(active.snapshotId), sourceId)),
    };
  }

  async prepareUpdateWorkspace(platform) {
    assertPlatform(platform);
    const jobId = `${Date.now()}-${crypto.randomUUID()}`;
    const workspace = path.join(this.incomingDir, jobId);
    await fsp.mkdir(path.join(workspace, 'crawler_output'), { recursive: true });
    await fsp.mkdir(path.join(workspace, 'converted_output', 'data'), { recursive: true });
    await fsp.mkdir(path.join(workspace, 'build'), { recursive: true });
    const active = await this.getActiveSnapshot();
    if (active) {
      const rawDir = this.snapshotRawDir(active.snapshotId);
      await copyDirectoryContents(rawDir, path.join(workspace, 'crawler_output'), (name) => name.endsWith('.json'));
      await copyDirectoryContents(this.snapshotDataDir(active.snapshotId), path.join(workspace, 'converted_output', 'data'), (name) => SAFE_DATA_FILE.test(name));
      const canonical = path.join(this.snapshotsDir, active.snapshotId, 'canonical.db');
      await copyIfExists(canonical, path.join(workspace, 'build', 'canonical.db'));
    }
    return { jobId, workspace, activeSnapshotId: active?.snapshotId || null };
  }

  async validateStage(workspace, platform) {
    assertPlatform(platform);
    const dataDir = path.join(workspace, 'converted_output', 'data');
    const contractPath = path.join(workspace, 'build', 'desktop_update_result.json');
    let contract;
    try {
      contract = JSON.parse(await fsp.readFile(contractPath, 'utf8'));
    } catch {
      throw new Error(`${PLATFORM_CONFIGS[platform].name} 缺少本轮采集结果合同，拒绝复用旧 sidecar`);
    }
    if (contract.platform !== platform || !['success_update', 'success_no_change'].includes(contract.outcome)) {
      throw new Error(`${PLATFORM_CONFIGS[platform].name} 本轮采集未形成可提交结果`);
    }
    if (!contract.collectionResultTouched || !contract.crawlerResult || !['success', 'success_no_change'].includes(contract.crawlerResult.status)) {
      throw new Error(`${PLATFORM_CONFIGS[platform].name} 缺少 crawler 对本轮请求完整性的确认`);
    }
    if (contract.crawlerResult.status !== 'success_no_change' && (!contract.rawTouched || !contract.sidecarTouched)) {
      throw new Error(`${PLATFORM_CONFIGS[platform].name} 本轮未同时生成原始 JSON 与现代 sidecar`);
    }
    const expectedSidecar = path.join(dataDir, contract.sidecarFile || PLATFORM_CONFIGS[platform].sidecars[0]);
    const sidecar = await exists(expectedSidecar) ? expectedSidecar : findSidecar(dataDir, platform);
    if (!sidecar || path.basename(sidecar) !== path.basename(expectedSidecar)) throw new Error(`${PLATFORM_CONFIGS[platform].name} 更新未生成本轮现代数据文件`);
    const parsed = readPlatformRecords(dataDir, platform);
    if (parsed.error) throw new Error(`更新数据校验失败: ${parsed.error}`);
    if (!parsed.records.length) throw new Error(`${PLATFORM_CONFIGS[platform].name} 更新结果为空，保留旧数据`);
    const rawPath = path.join(workspace, 'crawler_output', PLATFORM_CONFIGS[platform].rawFile);
    const rawExists = await exists(rawPath);
    if (!rawExists) throw new Error(`本轮缺少原始快照: ${PLATFORM_CONFIGS[platform].rawFile}`);
    const raw = JSON.parse(await fsp.readFile(rawPath, 'utf8'));
    if (!Array.isArray(raw) || !raw.length) throw new Error(`本轮原始快照为空或不是数组: ${PLATFORM_CONFIGS[platform].rawFile}`);
    return {
      sidecar: path.basename(sidecar),
      count: parsed.records.length,
      rawExists: true,
      rawCount: raw.length,
      outcome: contract.outcome,
      changed: Boolean(contract.changed),
      contract,
    };
  }

  async commitUpdate(workspace, platform, validation, metadata = {}, control = {}) {
    const active = await this.getActiveSnapshot();
    const snapshotId = `${new Date().toISOString().replace(/[-:.TZ]/g, '')}-${crypto.randomBytes(3).toString('hex')}`;
    const tempSnapshot = path.join(this.snapshotsDir, `.incoming-${snapshotId}`);
    const finalSnapshot = path.join(this.snapshotsDir, snapshotId);
    const tempData = path.join(tempSnapshot, 'data');
    const tempRaw = path.join(tempSnapshot, 'crawler_output');
    await fsp.mkdir(tempData, { recursive: true });
    await fsp.mkdir(tempRaw, { recursive: true });

    if (active) {
      await copyDirectoryContents(this.snapshotDataDir(active.snapshotId), tempData, (name) => SAFE_DATA_FILE.test(name));
      await copyDirectoryContents(this.snapshotRawDir(active.snapshotId), tempRaw, (name) => name.endsWith('.json'));
      await copyIfExists(path.join(this.snapshotsDir, active.snapshotId, 'canonical.db'), path.join(tempSnapshot, 'canonical.db'));
    }
    await copyDirectoryContents(path.join(workspace, 'converted_output', 'data'), tempData, (name) => SAFE_DATA_FILE.test(name));
    await copyDirectoryContents(path.join(workspace, 'crawler_output'), tempRaw, (name) => name.endsWith('.json'));
    await copyIfExists(path.join(workspace, 'build', 'canonical.db'), path.join(tempSnapshot, 'canonical.db'));
    await copyIfExists(path.join(workspace, 'build', 'desktop_snapshot_manifest.json'), path.join(tempSnapshot, 'desktop_snapshot_manifest.json'));
    await copyIfExists(path.join(workspace, 'build', 'desktop_update_result.json'), path.join(tempSnapshot, 'desktop_update_result.json'));

    const state = readPlatformRecords(tempData, platform);
    const manifest = {
      schema: SNAPSHOT_SCHEMA,
      snapshotId,
      createdAt: nowIso(),
      updatedAt: nowIso(),
      source: 'desktop-update',
      updatedPlatforms: [platform],
      canonicalReady: Boolean(await exists(path.join(tempSnapshot, 'canonical.db'))),
      platform: {
        id: platform,
        name: PLATFORM_CONFIGS[platform].name,
        sidecar: validation.sidecar,
        count: state.records.length,
        rawFile: validation.rawExists ? PLATFORM_CONFIGS[platform].rawFile : null,
        rawCount: validation.rawCount,
        outcome: validation.outcome,
        changed: validation.changed,
      },
      options: metadata.options || {},
    };
    await writeJsonAtomic(path.join(tempSnapshot, 'manifest.json'), manifest);
    await fsp.rename(tempSnapshot, finalSnapshot);
    let pointerSwitched = false;
    try {
      control.beforePointerCommit?.();
      await writeJsonAtomic(this.activePointer, { schema: SNAPSHOT_SCHEMA, snapshotId, updatedAt: manifest.updatedAt });
      this.platformCache.clear();
      pointerSwitched = true;
      return { ...manifest, snapshotId };
    } catch (error) {
      if (!pointerSwitched) await fsp.rm(finalSnapshot, { recursive: true, force: true }).catch(() => {});
      throw error;
    }
  }

  async importDirectory(sourceDirectory) {
    const source = path.resolve(sourceDirectory);
    const dataDir = await this.resolveDataDirectory(source);
    if (!dataDir) throw new Error('所选目录中没有可识别的数据目录（需要 platform_data.js 或 table_rows.js）');
    const staging = await this.prepareUpdateWorkspace('bilibili');
    await fsp.rm(path.join(staging.workspace, 'converted_output', 'data'), { recursive: true, force: true });
    await fsp.mkdir(path.join(staging.workspace, 'converted_output', 'data'), { recursive: true });
    await copyDirectoryContents(dataDir, path.join(staging.workspace, 'converted_output', 'data'), (name) => SAFE_DATA_FILE.test(name));
    const rawCandidate = path.basename(dataDir) === 'data' ? path.join(path.dirname(dataDir), '..', 'crawler_output') : path.join(source, 'crawler_output');
    await copyDirectoryContents(rawCandidate, path.join(staging.workspace, 'crawler_output'), (name) => name.endsWith('.json'));
    const available = ALL_PLATFORMS.filter((platform) => {
      const result = readPlatformRecords(path.join(staging.workspace, 'converted_output', 'data'), platform);
      return !result.error && result.records.length > 0;
    });
    if (!available.length) {
      await this.cleanupWorkspace(staging.workspace);
      throw new Error('未找到可读取的整合包数据');
    }
    const snapshotId = `${new Date().toISOString().replace(/[-:.TZ]/g, '')}-${crypto.randomBytes(3).toString('hex')}`;
    const tempSnapshot = path.join(this.snapshotsDir, `.incoming-${snapshotId}`);
    const finalSnapshot = path.join(this.snapshotsDir, snapshotId);
    await fsp.mkdir(path.join(tempSnapshot, 'data'), { recursive: true });
    await fsp.mkdir(path.join(tempSnapshot, 'crawler_output'), { recursive: true });
    await copyDirectoryContents(path.join(staging.workspace, 'converted_output', 'data'), path.join(tempSnapshot, 'data'), (name) => SAFE_DATA_FILE.test(name));
    await copyDirectoryContents(path.join(staging.workspace, 'crawler_output'), path.join(tempSnapshot, 'crawler_output'), (name) => name.endsWith('.json'));
    const manifest = {
      schema: SNAPSHOT_SCHEMA,
      snapshotId,
      createdAt: nowIso(),
      updatedAt: nowIso(),
      source: 'local-import',
      updatedPlatforms: available,
      canonicalReady: false,
      importedFrom: path.basename(source),
      platforms: Object.fromEntries(available.map((platform) => [platform, { count: readPlatformRecords(path.join(tempSnapshot, 'data'), platform).records.length }])),
    };
    await writeJsonAtomic(path.join(tempSnapshot, 'manifest.json'), manifest);
    await fsp.rename(tempSnapshot, finalSnapshot);
    await writeJsonAtomic(this.activePointer, { schema: SNAPSHOT_SCHEMA, snapshotId, updatedAt: manifest.updatedAt });
    this.platformCache.clear();
    await this.cleanupWorkspace(staging.workspace);
    return this.getState();
  }

  async resolveDataDirectory(source) {
    const candidates = [
      path.join(source, 'data'),
      source,
      path.join(source, 'converted_output', 'data'),
      path.join(source, 'build', 'frontend_preview', 'data'),
    ];
    for (const candidate of candidates) {
      if (await exists(candidate) && ALL_PLATFORMS.some((platform) => findSidecar(candidate, platform))) return candidate;
    }
    return null;
  }

  async cleanupWorkspace(workspace) {
    const resolved = path.resolve(workspace);
    const incomingRoot = path.resolve(this.incomingDir);
    if (resolved === incomingRoot || !resolved.startsWith(`${incomingRoot}${path.sep}`)) {
      throw new Error('拒绝清理工作目录之外的路径');
    }
    await fsp.rm(resolved, { recursive: true, force: true });
  }

  async getActiveDataDirectory() {
    const active = await this.getActiveSnapshot();
    return active ? this.snapshotDataDir(active.snapshotId) : null;
  }
}

function defaultUserDataRoot(appName = 'MCModpackBoard') {
  const base = process.env.APPDATA
    || (process.platform === 'darwin'
      ? path.join(os.homedir(), 'Library', 'Application Support')
      : process.platform === 'win32'
        ? path.join(os.homedir(), 'AppData', 'Roaming')
        : process.env.XDG_DATA_HOME || path.join(os.homedir(), '.local', 'share'));
  return path.join(base, appName, 'data');
}

module.exports = { DataStore, defaultUserDataRoot, SNAPSHOT_SCHEMA };

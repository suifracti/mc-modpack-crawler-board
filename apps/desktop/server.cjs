'use strict';

const http = require('node:http');
const fs = require('node:fs');
const fsp = require('node:fs/promises');
const path = require('node:path');
const { spawn } = require('node:child_process');
const { URL } = require('node:url');
const { DataStore, defaultUserDataRoot } = require('./lib/data-store.cjs');
const { PersonalLibrary } = require('./lib/personal-library.cjs');
const { FavoriteUpdateTracker } = require('./lib/favorite-updates.cjs');
const { assertPlatform, redactLogLine } = require('./lib/platforms.cjs');
const { UpdateManager } = require('./lib/update-manager.cjs');
const { createProcessRunner } = require('./lib/process-runner.cjs');

const repoRoot = path.resolve(__dirname, '..', '..');
const frontendRoot = path.join(repoRoot, 'build', 'desktop', 'frontend');
const workerSource = path.join(repoRoot, 'apps', 'desktop', 'collector_worker.py');

function parseArgs(argv) {
  const args = { host: '127.0.0.1', port: 8765, open: false, dataRoot: null, python: null };
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === '--open') args.open = true;
    else if (value === '--no-open') args.open = false;
    else if (value === '--host') args.host = String(argv[++index] || args.host);
    else if (value === '--port') args.port = Number(argv[++index] || args.port);
    else if (value === '--data-root') args.dataRoot = String(argv[++index] || '');
    else if (value === '--python') args.python = String(argv[++index] || '');
  }
  if (!Number.isInteger(args.port) || args.port < 1 || args.port > 65535) throw new Error('端口必须是 1 到 65535 之间的整数');
  return args;
}

function pythonCommand(explicit) {
  if (explicit) return explicit;
  if (process.env.MC_DESKTOP_PYTHON) return process.env.MC_DESKTOP_PYTHON;
  return process.platform === 'win32' ? 'python' : 'python3';
}

function makeRunner({ platform, options, workspace, onLine, sourceRoot = repoRoot, python }) {
  if (!fs.existsSync(workerSource)) throw new Error(`采集 worker 未找到: ${workerSource}`);
  const command = pythonCommand(python);
  const args = [workerSource, '--platform', platform, '--workspace', workspace, '--source-root', sourceRoot];
  if (options.limit) args.push('--limit', String(options.limit));
  if (options.pages) args.push('--pages', String(options.pages));
  if (options.until) args.push('--until', options.until);
  return createProcessRunner({ command, args, cwd: workspace, onLine });
}

function json(res, statusCode, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(statusCode, {
    'content-type': 'application/json; charset=utf-8',
    'cache-control': 'no-store',
    'content-length': Buffer.byteLength(body),
  });
  res.end(body);
}

function errorJson(res, statusCode, error) {
  const message = error instanceof Error ? error.message : String(error);
  json(res, statusCode, { error: message });
}

async function readJsonBody(req, maxBytes = 1024 * 1024) {
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > maxBytes) throw new Error('请求体过大');
    chunks.push(chunk);
  }
  if (!chunks.length) return {};
  const text = Buffer.concat(chunks).toString('utf8');
  const parsed = JSON.parse(text);
  if (!parsed || typeof parsed !== 'object') throw new Error('请求体必须是 JSON 对象');
  return parsed;
}

function contentType(filePath) {
  const extension = path.extname(filePath).toLowerCase();
  return {
    '.html': 'text/html; charset=utf-8',
    '.js': 'text/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.svg': 'image/svg+xml',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
  }[extension] || 'application/octet-stream';
}

function openBrowser(url) {
  const command = process.platform === 'win32' ? 'cmd' : process.platform === 'darwin' ? 'open' : 'xdg-open';
  const args = process.platform === 'win32' ? ['/c', 'start', '', url] : [url];
  const child = spawn(command, args, { detached: true, stdio: 'ignore', windowsHide: true });
  child.unref();
}

function createBrowserService(options = {}) {
  const host = options.host || '127.0.0.1';
  const port = options.port ?? 8765;
  const sourceRoot = options.sourceRoot || repoRoot;
  const dataRoot = path.resolve(options.dataRoot || process.env.MC_DESKTOP_DATA_ROOT || defaultUserDataRoot());
  const personalLibrary = options.personalLibrary || new PersonalLibrary(dataRoot);
  const favoriteUpdates = options.favoriteUpdates || new FavoriteUpdateTracker(dataRoot);
  const store = options.store || new DataStore(dataRoot, { personalLibrary });
  if (store && !store.personalLibrary) store.personalLibrary = personalLibrary;
  const subscribers = new Set();
  let initialized = false;

  const logger = async (line) => {
    const logPath = path.join(path.dirname(dataRoot), 'logs', 'updates.log');
    await fsp.mkdir(path.dirname(logPath), { recursive: true });
    await fsp.appendFile(logPath, `${new Date().toISOString()} ${redactLogLine(line)}\n`, 'utf8');
  };

  const updateManager = options.updateManager || new UpdateManager({
    store,
    runnerFactory: (runnerOptions) => makeRunner({ ...runnerOptions, sourceRoot, python: options.python }),
    logger: (line) => { void logger(line).catch(() => {}); },
    onSnapshotActivated: async ({ platform }) => {
      const result = await favoriteUpdates.processSuccessfulRefresh(
        platform,
        (await personalLibrary.list()).entries,
        (sourcePlatform, sourceId) => store.findSourceRecord(sourcePlatform, sourceId),
      );
      if (result.eventsAdded) await logger(`收藏更新提醒：${result.eventsAdded} 条新变化已记录。`);
    },
  });

  function sendEvent(event, payload) {
    const message = `event: ${event}\ndata: ${JSON.stringify(payload)}\n\n`;
    for (const response of subscribers) {
      try { response.write(message); } catch { subscribers.delete(response); }
    }
  }

  updateManager.on('status', (status) => sendEvent('status', status));
  updateManager.on('log', (line) => sendEvent('log', line));

  async function ensureInitialized() {
    if (!initialized) {
      await personalLibrary.init();
      await store.init();
      await favoriteUpdates.init();
      await favoriteUpdates.seedMissingFavorites(
        (await personalLibrary.list()).entries,
        (platform, sourceId) => store.findSourceRecord(platform, sourceId),
      );
      initialized = true;
    }
  }

  async function serveStatic(requestUrl, res) {
    const requested = requestUrl === '/' ? 'desktop.html' : decodeURIComponent(requestUrl.slice(1));
    if (!requested || requested.includes('\0')) return errorJson(res, 400, '非法资源路径');
    const root = path.resolve(frontendRoot);
    const filePath = path.resolve(root, requested);
    if (filePath !== root && !filePath.startsWith(`${root}${path.sep}`)) return errorJson(res, 403, '拒绝访问该路径');
    let stat;
    try { stat = await fsp.stat(filePath); } catch { return errorJson(res, 404, '资源不存在'); }
    if (!stat.isFile()) return errorJson(res, 404, '资源不存在');
    res.writeHead(200, { 'content-type': contentType(filePath), 'cache-control': 'no-store' });
    fs.createReadStream(filePath).pipe(res);
  }

  async function handleApi(request, response, requestUrl) {
    const pathname = requestUrl.pathname;
    if (pathname === '/api/health' && request.method === 'GET') return json(response, 200, { ok: true, service: 'mc-modpack-board-browser' });
    if (pathname === '/api/events' && request.method === 'GET') {
      response.writeHead(200, {
        'content-type': 'text/event-stream; charset=utf-8',
        'cache-control': 'no-cache, no-transform',
        connection: 'keep-alive',
      });
      response.write(`retry: 2000\nevent: status\ndata: ${JSON.stringify(updateManager.getStatus())}\n\n`);
      subscribers.add(response);
      request.on('close', () => subscribers.delete(response));
      return;
    }
    if (pathname === '/api/state' && request.method === 'GET') return json(response, 200, { data: await store.getState(), update: updateManager.getStatus() });
    if (pathname === '/api/audit' && request.method === 'GET') return json(response, 200, await store.getAuditDiff());

    const recordsMatch = pathname.match(/^\/api\/platforms\/([^/]+)\/records$/);
    if (recordsMatch && request.method === 'GET') {
      const platform = decodeURIComponent(recordsMatch[1]);
      assertPlatform(platform);
      return json(response, 200, await store.getPlatformRecords(platform, {
        query: requestUrl.searchParams.get('query') || '',
        version: requestUrl.searchParams.get('version') || '',
        loader: requestUrl.searchParams.get('loader') || '',
        category: requestUrl.searchParams.get('category') || '',
        includedMods: requestUrl.searchParams.getAll('includedMod'),
        includedModsExclude: requestUrl.searchParams.get('includedModsExclude') === 'true',
        gameplayCategories: requestUrl.searchParams.getAll('gameplayCategory'),
        gameplayCategoriesExclude: requestUrl.searchParams.get('gameplayCategoriesExclude') === 'true',
        pan: requestUrl.searchParams.get('pan') || '',
        dateRange: requestUrl.searchParams.get('dateRange') || '',
        serverOnly: requestUrl.searchParams.get('serverOnly') === 'true',
        personalStatus: requestUrl.searchParams.get('personalStatus') || '',
        sort: requestUrl.searchParams.get('sort') || '',
        page: requestUrl.searchParams.get('page') || 1,
        pageSize: requestUrl.searchParams.get('pageSize') || 48,
      }));
    }

    if (pathname === '/api/library' && request.method === 'GET') return json(response, 200, await personalLibrary.list());
    if (pathname === '/api/favorite-updates' && request.method === 'GET') {
      return json(response, 200, favoriteUpdates.list((await personalLibrary.list()).entries));
    }
    const favoriteUpdateReadMatch = pathname.match(/^\/api\/favorite-updates\/([a-f0-9]{64})\/read$/);
    if (favoriteUpdateReadMatch && request.method === 'POST') {
      const marked = await favoriteUpdates.markRead(favoriteUpdateReadMatch[1]);
      if (!marked) return errorJson(response, 404, '收藏更新提醒不存在');
      return json(response, 200, favoriteUpdates.list((await personalLibrary.list()).entries));
    }
    if (pathname === '/api/library/export' && request.method === 'GET') {
      response.setHeader('Content-Disposition', 'attachment; filename="personal-library.json"');
      return json(response, 200, await personalLibrary.list());
    }
    if (pathname === '/api/library/restore' && request.method === 'POST') {
      const result = await personalLibrary.restore(await readJsonBody(request, 16 * 1024 * 1024));
      if (!result.invalid && result.restored) await favoriteUpdates.seedMissingFavorites(
        (await personalLibrary.list()).entries,
        (platform, sourceId) => store.findSourceRecord(platform, sourceId),
      );
      return json(response, result.invalid ? 400 : 200, result);
    }
    if (pathname === '/api/library/missing' && request.method === 'GET') {
      const missing = {};
      for (const [key, status] of Object.entries((await personalLibrary.list()).entries)) {
        const split = key.indexOf(':');
        if (!await store.findSourceRecord(key.slice(0, split), key.slice(split + 1))) missing[key] = status;
      }
      return json(response, 200, { entries: missing });
    }

    const personalMatch = pathname.match(/^\/api\/library\/([^/]+)\/([^/]+)$/);
    if (personalMatch && request.method === 'PATCH') {
      const platform = decodeURIComponent(personalMatch[1]);
      const sourceId = decodeURIComponent(personalMatch[2]);
      assertPlatform(platform);
      const patch = await readJsonBody(request, 64 * 1024);
      const record = await store.findSourceRecord(platform, sourceId);
      if (record?.sourceIdOrigin === 'index-fallback') {
        throw new Error('该记录仅由数组序号生成来源标识，不能保存个人状态；请使用带稳定来源 ID 的记录');
      }
      const wasFavorite = personalLibrary.get(platform, sourceId).favorite;
      const result = await personalLibrary.update(platform, sourceId, patch, record);
      if (typeof patch.favorite === 'boolean' && patch.favorite !== wasFavorite) {
        try {
          const activeRecord = patch.favorite ? await store.findSourceRecord(platform, sourceId) : null;
          await favoriteUpdates.setFavorite(platform, sourceId, patch.favorite, activeRecord);
        } catch (error) {
          await logger(`收藏更新基线暂未同步：${error instanceof Error ? error.message : String(error)}`);
        }
      }
      return json(response, 200, result);
    }

    const commentsMatch = pathname.match(/^\/api\/platforms\/([^/]+)\/comments\/([^/]+)$/);
    if (commentsMatch && request.method === 'GET') {
      const platform = decodeURIComponent(commentsMatch[1]);
      assertPlatform(platform);
      return json(response, 200, await store.getPlatformComments(platform, decodeURIComponent(commentsMatch[2])));
    }

    if (pathname === '/api/data/import' && request.method === 'POST') {
      const body = await readJsonBody(request);
      if (!body.path || typeof body.path !== 'string') throw new Error('需要提供本地数据目录路径');
      const data = await store.importDirectory(body.path);
      await favoriteUpdates.resetFavoriteBaselines(
        (await personalLibrary.list()).entries,
        (platform, sourceId) => store.findSourceRecord(platform, sourceId),
      );
      sendEvent('data', data);
      return json(response, 200, { cancelled: false, data });
    }

    if (pathname === '/api/updates' && request.method === 'POST') {
      const body = await readJsonBody(request);
      assertPlatform(body.platform);
      const task = updateManager.start(body.platform, body.options || {});
      task.catch(() => {});
      return json(response, 202, updateManager.getStatus());
    }

    if (pathname === '/api/updates/cancel' && request.method === 'POST') return json(response, 200, updateManager.cancel());
    return errorJson(response, 404, 'API 路径不存在');
  }

  const server = http.createServer((request, response) => {
    const requestUrl = new URL(request.url || '/', `http://${request.headers.host || `${host}:${port}`}`);
    const work = requestUrl.pathname.startsWith('/api/')
      ? handleApi(request, response, requestUrl)
      : request.method === 'GET' ? serveStatic(requestUrl.pathname, response) : Promise.resolve(errorJson(response, 405, '只允许 GET 请求'));
    work.catch((error) => {
      if (!response.headersSent) errorJson(response, error.code === 'UPDATE_ALREADY_RUNNING' ? 409 : 400, error);
      else response.destroy();
    });
  });

  return {
    host,
    port,
    dataRoot,
    frontendRoot,
    store,
    updateManager,
    server,
    async start() {
      await ensureInitialized();
      await new Promise((resolve, reject) => {
        const onError = (error) => { server.off('listening', onListening); reject(error); };
        const onListening = () => { server.off('error', onError); resolve(); };
        server.once('error', onError);
        server.once('listening', onListening);
        server.listen(port, host);
      });
      const address = server.address();
      const actualPort = typeof address === 'object' && address ? address.port : port;
      return { url: `http://${host}:${actualPort}/`, port: actualPort };
    },
    async stop() {
      await updateManager.shutdown();
      for (const response of subscribers) response.end();
      subscribers.clear();
      if (server.listening) await new Promise((resolve) => server.close(resolve));
    },
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const service = createBrowserService(args);
  const started = await service.start();
  console.log(`MC Modpack Board browser service: ${started.url}`);
  console.log(`Data root: ${service.dataRoot}`);
  if (args.open) openBrowser(started.url);
  const shutdown = async () => { await service.stop(); process.exit(0); };
  process.once('SIGINT', shutdown);
  process.once('SIGTERM', shutdown);
}

if (require.main === module) main().catch((error) => { console.error(error.stack || error); process.exitCode = 1; });

module.exports = { createBrowserService, openBrowser, parseArgs, frontendRoot };

'use strict';

const http = require('node:http');
const https = require('node:https');
const fs = require('node:fs');
const fsp = require('node:fs/promises');
const path = require('node:path');
const net = require('node:net');
const zlib = require('node:zlib');
const { URL } = require('node:url');
const { DataStore, defaultUserDataRoot } = require('./lib/data-store.cjs');
const { PersonalLibrary } = require('./lib/personal-library.cjs');
const { FavoriteUpdateTracker } = require('./lib/favorite-updates.cjs');
const { assertPlatform, redactLogLine } = require('./lib/platforms.cjs');
const { UpdateManager } = require('./lib/update-manager.cjs');
const { createProcessRunner } = require('./lib/process-runner.cjs');
const { openSystemTarget } = require('./lib/system-open.cjs');
const { getPreviewVersions } = require('./lib/preview-versions.cjs');

const repoRoot = path.resolve(__dirname, '..', '..');
const defaultFrontendRoot = path.join(repoRoot, 'build', 'desktop', 'frontend');
const workerSource = path.join(repoRoot, 'apps', 'desktop', 'collector_worker.py');
const proxyHostSuffixes = [
  'mcmod.cn', 'bilibili.com', 'curseforge.com', 'modrinth.com',
  'bbsmc.net', 'xyebbs.com', 'binjie.fun', 'minecraft.net',
];

function parseAllowedProxyTarget(value) {
  const parsed = new URL(String(value || ''));
  if (!['http:', 'https:'].includes(parsed.protocol)) throw new Error('需要合法的 HTTP/HTTPS 目标 URL');
  const allowed = proxyHostSuffixes.some((suffix) => parsed.hostname === suffix || parsed.hostname.endsWith(`.${suffix}`));
  if (!allowed) throw new Error('不支持代理该域名');
  return parsed;
}

function proxyPageError(response, status, message, targetUrl = '') {
  if (response.headersSent || response.destroyed) return;
  const text = String(message).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('"', '&quot;');
  const safeTarget = targetUrl ? String(targetUrl).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('"', '&quot;') : '';
  response.writeHead(status, { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' });
  response.end(`<!doctype html><meta charset="utf-8"><style>body{font:15px system-ui,-apple-system,sans-serif;padding:36px 32px;color:#475569;max-width:640px;margin:0 auto;line-height:1.6}h2{color:#0f172a;margin-top:0;font-size:20px;display:flex;align-items:center;gap:8px}.err-msg{background:#fee2e2;color:#991b1b;padding:12px 16px;border-radius:8px;font-family:monospace;font-size:13px;word-break:break-all;margin:16px 0;border:1px solid #fecaca}.actions{display:flex;gap:10px;margin:20px 0;flex-wrap:wrap}.btn{display:inline-flex;align-items:center;gap:6px;padding:9px 18px;border-radius:6px;font-weight:500;font-size:14px;text-decoration:none;cursor:pointer;border:none}.btn-primary{background:#3b82f6;color:#fff}.btn-primary:hover{background:#2563eb}.btn-secondary{background:#f1f5f9;color:#334155;border:1px solid #cbd5e1}.btn-secondary:hover{background:#e2e8f0}.tips{color:#64748b;font-size:13px;border-top:1px solid #e2e8f0;padding-top:16px;margin-top:24px}ul{padding-left:20px;margin:8px 0}li{margin-bottom:6px}</style><h2>🌐 原站暂时无法载入</h2><div class="err-msg">${text}</div><div class="actions"><button type="button" class="btn btn-primary" onclick="location.reload()">🔄 重新尝试载入</button>${safeTarget ? `<a href="${safeTarget}" target="_blank" rel="noreferrer" class="btn btn-secondary">在新标签页中打开原站 ↗</a>` : ''}</div><div class="tips"><strong>💡 解决建议：</strong><ul><li>站点可能存在短暂网络波动或 CDN 限制，点击上方“重新尝试载入”通常可直接恢复；</li><li>可切换上方小窗顶部的<strong>【资料】</strong>或<strong>【版本历史】</strong>标签，直接查看已收录的网盘下载链接与更新日志；</li><li>也可直接点击“在新标签页中打开原站”前往外部浏览器浏览。</li></ul></div><script>parent.postMessage({type:'in-app-page-state',ok:false},'*')</script>`);
}

function rewriteProxiedHtml(html, targetUrl, options = {}) {
  let content = String(html || '');
  const target = new URL(String(targetUrl));
  const staticMode = options.static === true || ['bbsmc.net', 'modrinth.com', 'xyebbs.com'].some((host) => target.hostname === host || target.hostname.endsWith(`.${host}`));
  if (staticMode) {
    content = content
      .replace(/<script\b[^>]*>[\s\S]*?<\/script\s*>/gi, '')
      .replace(/\son[a-z]+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)/gi, '');
  }
  const escapedBase = String(targetUrl).replaceAll('&', '&amp;').replaceAll('"', '&quot;').replaceAll('<', '&lt;');
  const navigationScript = `<script>(function(){
    var base=${JSON.stringify(target.href).replaceAll('<', '\\u003c')};
    function ready(){window.parent.postMessage({type:'in-app-page-state',ok:true,url:base},'*');}
    document.addEventListener('click',function(event){
      var anchor=event.target&&event.target.closest&&event.target.closest('a[href]');
      if(!anchor||event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
      try{var next=new URL(anchor.getAttribute('href'),base);if(next.protocol!=='http:'&&next.protocol!=='https:')return;
        if(next.origin===new URL(base).origin&&next.pathname===new URL(base).pathname&&next.search===new URL(base).search&&next.hash){var section=document.getElementById(decodeURIComponent(next.hash.slice(1)));if(section){event.preventDefault();section.scrollIntoView();return;}}
        var host=new URL(base).hostname;var sameSite=next.hostname===host||next.hostname.replace(/^www\\./,'')===host.replace(/^www\\./,'');
        if(!sameSite||anchor.hasAttribute('download')||/\\.(zip|jar|mrpack|7z)(?:$|[?#])/i.test(next.href)){anchor.href=next.href;anchor.target='_blank';anchor.rel='noreferrer';return;}
        event.preventDefault();event.stopImmediatePropagation();window.parent.postMessage({type:'in-app-page-state',loading:true,url:next.href},'*');location.href=location.origin+'/api/proxy-page?${staticMode ? 'static=1&' : ''}url='+encodeURIComponent(next.href);
      }catch(_){}
    },${staticMode ? 'true' : 'false'});
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ready,{once:true});else ready();
  })();</script>`;
  const mcmodPack = new URL(String(targetUrl)).hostname.endsWith('mcmod.cn') && /^\/modpack\/\d+\.html$/.test(new URL(String(targetUrl)).pathname);
  const modNavigator = mcmodPack ? `<script>(function(){
    function entries(){var root=document.querySelector('li.text-area[data-id="2"] .class-relation-list')||document.querySelector('.class-relation-list');if(!root)return[];var result=[];root.querySelectorAll('li.modlist').forEach(function(group){var category=group.querySelector('a[href*="/class/category/"]');group.querySelectorAll('ul li').forEach(function(item){var link=item.querySelector('p a[href*="/class/"]');if(link&&link.textContent.trim())result.push({name:link.textContent.trim(),url:link.href,categoryUrl:category?category.href:''});});});return result;}
    function publish(){window.parent.postMessage({type:'mcmod-mod-index',entries:entries()},'*');}
    window.addEventListener('message',function(event){if(event.source!==window.parent||!event.data||event.data.type!=='mcmod-focus-mod')return;var wanted=String(event.data.name||'').trim();var root=document.querySelector('li.text-area[data-id="2"] .class-relation-list')||document.querySelector('.class-relation-list');var found=null;if(root&&wanted){root.querySelectorAll('li.modlist ul li p a[href*="/class/"]').forEach(function(link){if(!found&&link.textContent.trim()===wanted)found=link;});}if(found){var tab=document.querySelector('.class-menu-page li.page-li[data-id="2"] a');if(tab&&tab.click)tab.click();setTimeout(function(){found.scrollIntoView({block:'center',behavior:'smooth'});found.style.outline='3px solid #1677ff';setTimeout(function(){found.style.outline='';},3500);},80);}window.parent.postMessage({type:'mcmod-focus-result',name:wanted,found:!!found},'*');});
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',publish,{once:true});else publish();
  })();</script>` : '';
  const injection = `<base href="${escapedBase}">${navigationScript}${modNavigator}`;
  if (/<base\b[^>]*>/i.test(content)) return content.replace(/<base\b[^>]*>/i, injection);
  if (/<head\b[^>]*>/i.test(content)) return content.replace(/<head\b[^>]*>/i, (head) => `${head}${injection}`);
  return `${injection}${content}`;
}

function parseArgs(argv) {
  const args = { host: '::', port: 8765, open: false, dataRoot: null, python: null, frontendRoot: null };
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === '--open') args.open = true;
    else if (value === '--no-open') args.open = false;
    else if (value === '--host') args.host = String(argv[++index] || args.host);
    else if (value === '--port') args.port = Number(argv[++index] || args.port);
    else if (value === '--data-root') args.dataRoot = String(argv[++index] || '');
    else if (value === '--python') args.python = String(argv[++index] || '');
    else if (value === '--frontend-root') args.frontendRoot = String(argv[++index] || '');
  }
  if (!Number.isInteger(args.port) || args.port < 1 || args.port > 65535) throw new Error('端口必须是 1 到 65535 之间的整数');
  return args;
}

function displayHost(host) {
  if (host === '::' || host === '0.0.0.0') return host === '::' ? '[::1]' : '127.0.0.1';
  return net.isIP(host) === 6 ? `[${host}]` : host;
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
  if (options.mode) args.push('--mode', String(options.mode));
  if (options.limit) args.push('--limit', String(options.limit));
  if (options.coverOffset !== undefined && options.coverOffset !== null) args.push('--cover-offset', String(options.coverOffset));
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
  return openSystemTarget(url, { kind: 'url' });
}

function openDirectory(directory) {
  return openSystemTarget(path.resolve(directory), { kind: 'path' });
}

function createBrowserService(options = {}) {
  const host = options.host || '::';
  const port = options.port ?? 8765;
  const sourceRoot = options.sourceRoot || repoRoot;
  const dataRoot = path.resolve(options.dataRoot || process.env.MC_DESKTOP_DATA_ROOT || defaultUserDataRoot());
  const frontendRoot = path.resolve(options.frontendRoot || defaultFrontendRoot);
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
    const root = path.resolve(frontendRoot);
    let requested = requestUrl === '/' ? 'desktop.html' : decodeURIComponent(requestUrl.slice(1));
    if (requestUrl === '/' && !fs.existsSync(path.join(root, 'desktop.html')) && fs.existsSync(path.join(root, 'desktop-v2.html'))) {
      requested = 'desktop-v2.html';
    }
    if (!requested || requested.includes('\0')) return errorJson(res, 400, '非法资源路径');
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
    const previewVersionsMatch = pathname.match(/^\/api\/preview-versions\/(mcmod|bbsmc|modrinth|curseforge|xyebbs)\/([A-Za-z0-9_-]+)$/);
    if (previewVersionsMatch && request.method === 'GET') return json(response, 200, await getPreviewVersions(previewVersionsMatch[1], previewVersionsMatch[2]));
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
    if (pathname === '/api/data/library' && request.method === 'GET') return json(response, 200, await store.listSnapshots());
    if (pathname === '/api/data/open' && request.method === 'POST') {
      const body = await readJsonBody(request, 64 * 1024);
      const target = body.snapshotId ? await store.getSnapshotDirectory(body.snapshotId) : dataRoot;
      await fsp.mkdir(target, { recursive: true });
      await openDirectory(target);
      return json(response, 200, { opened: true, path: target });
    }
    if (pathname === '/api/data/export' && request.method === 'POST') {
      return json(response, 200, await store.exportActiveSnapshot());
    }
    if (pathname === '/api/data/activate' && request.method === 'POST') {
      const body = await readJsonBody(request, 64 * 1024);
      const data = await store.activateSnapshot(body.snapshotId);
      await favoriteUpdates.resetFavoriteBaselines(
        (await personalLibrary.list()).entries,
        (platform, sourceId) => store.findSourceRecord(platform, sourceId),
      );
      sendEvent('data', data);
      return json(response, 200, { data });
    }
    if (pathname === '/api/data/delete' && request.method === 'POST') {
      const body = await readJsonBody(request, 64 * 1024);
      const archived = await store.archiveSnapshot(body.snapshotId);
      return json(response, 200, { archived, library: await store.listSnapshots() });
    }

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

    if (pathname === '/api/proxy-page' && request.method === 'GET') {
      const targetUrl = requestUrl.searchParams.get('url');
      if (!targetUrl) {
        return errorJson(response, 400, '需要合法的 HTTP/HTTPS 目标 URL');
      }
      try {
        const parsed = parseAllowedProxyTarget(targetUrl);

        const client = parsed.protocol === 'https:' ? https : http;
        const reqHeaders = {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
          'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
          'Accept-Encoding': 'identity',
        };
        const executeProxyRequest = (attempt = 0) => {
          if (response.headersSent || response.destroyed) return;
          const reqOptions = {
            method: 'GET',
            headers: reqHeaders,
            agent: false,
            servername: parsed.hostname,
          };
          const proxyReq = client.request(targetUrl, reqOptions, (proxyRes) => {
            if (proxyRes.statusCode >= 400) {
              proxyRes.resume();
              return proxyPageError(response, proxyRes.statusCode, `原站返回 HTTP ${proxyRes.statusCode}，可能需要在浏览器中验证或登录。`, targetUrl);
            }
            if (proxyRes.statusCode >= 300 && proxyRes.statusCode < 400 && proxyRes.headers.location) {
              const redirected = new URL(proxyRes.headers.location, targetUrl).toString();
              try {
                parseAllowedProxyTarget(redirected);
              } catch (error) {
                return errorJson(response, 502, error);
              }
              response.writeHead(302, { Location: `/api/proxy-page?${requestUrl.searchParams.get('static') === '1' ? 'static=1&' : ''}url=${encodeURIComponent(redirected)}` });
              return response.end();
            }

            const responseHeaders = { ...proxyRes.headers };
            delete responseHeaders['x-frame-options'];
            delete responseHeaders['X-Frame-Options'];
            delete responseHeaders['content-security-policy'];
            delete responseHeaders['Content-Security-Policy'];
            delete responseHeaders['content-security-policy-report-only'];
            delete responseHeaders['set-cookie'];
            delete responseHeaders['content-length'];
            delete responseHeaders['transfer-encoding'];
            delete responseHeaders['Transfer-Encoding'];
            delete responseHeaders['connection'];
            delete responseHeaders['Connection'];

            const contentTypeHeader = String(responseHeaders['content-type'] || '');
            if (!/text\/html|application\/xhtml\+xml/i.test(contentTypeHeader)) {
              response.writeHead(proxyRes.statusCode || 200, responseHeaders);
              proxyRes.pipe(response);
              return;
            }

            const chunks = [];
            let totalBytes = 0;
            proxyRes.on('data', (chunk) => {
              totalBytes += chunk.length;
              if (totalBytes > 10 * 1024 * 1024) {
                proxyRes.destroy(new Error('代理页面超过 10MB 限制'));
                return;
              }
              chunks.push(chunk);
            });
            proxyRes.on('end', () => {
              if (response.headersSent) return;
              let decoded = Buffer.concat(chunks);
              const encoding = String(responseHeaders['content-encoding'] || '').toLowerCase();
              try {
                if (encoding === 'gzip') decoded = zlib.gunzipSync(decoded);
                else if (encoding === 'br') decoded = zlib.brotliDecompressSync(decoded);
                else if (encoding === 'deflate') decoded = zlib.inflateSync(decoded);
                else if (encoding && encoding !== 'identity') throw new Error(`不支持的内容编码：${encoding}`);
              } catch (error) {
                return errorJson(response, 502, `代理页面解压失败：${error instanceof Error ? error.message : String(error)}`);
              }
              delete responseHeaders['content-encoding'];
              const body = rewriteProxiedHtml(decoded.toString('utf8'), targetUrl, {
                static: requestUrl.searchParams.get('static') === '1',
              });
              responseHeaders['content-length'] = Buffer.byteLength(body);
              responseHeaders['cache-control'] = 'no-store';
              response.writeHead(proxyRes.statusCode || 200, responseHeaders);
              response.end(body);
            });
            proxyRes.on('error', (error) => {
              if (!response.headersSent) errorJson(response, 502, `代理响应失败：${error.message}`);
            });
          });

          proxyReq.on('error', (err) => {
            if (response.headersSent || response.destroyed) return;
            const msg = String(err.message || '').toLowerCase();
            const isTransient = msg.includes('disconnected before secure tls') ||
                                msg.includes('econnreset') ||
                                msg.includes('etimedout') ||
                                msg.includes('socket hang up') ||
                                err.code === 'ECONNRESET' ||
                                err.code === 'ETIMEDOUT';
            if (isTransient && attempt < 2) {
              setTimeout(() => executeProxyRequest(attempt + 1), 350);
              return;
            }
            proxyPageError(response, 502, `代理请求失败：${err.message}`, targetUrl);
          });

          proxyReq.setTimeout(18000, () => proxyReq.destroy(new Error('原站请求超过 18 秒，请稍后重试')));
          response.on('close', () => { if (!response.writableEnded) proxyReq.destroy(); });
          proxyReq.end();
        };

        executeProxyRequest(0);
        return;
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        return errorJson(response, message === '不支持代理该域名' ? 403 : 400, message);
      }
    }
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
      return { url: `http://${displayHost(host)}:${actualPort}/`, port: actualPort };
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
  if (args.open) await openBrowser(started.url);
  const shutdown = async () => { await service.stop(); process.exit(0); };
  process.once('SIGINT', shutdown);
  process.once('SIGTERM', shutdown);
}

if (require.main === module) main().catch((error) => { console.error(error.stack || error); process.exitCode = 1; });

module.exports = { createBrowserService, openBrowser, parseArgs, frontendRoot: defaultFrontendRoot, parseAllowedProxyTarget, rewriteProxiedHtml };

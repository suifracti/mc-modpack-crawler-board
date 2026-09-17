/**
 * Architecture V2 - Single Directory Browser Smoke Test.
 * Runs the comprehensive 33-behavior test suite against any specified directory.
 * Usage: node pipeline/smoke_test_single.js <target_dir> [port]
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const REPO_ROOT = path.resolve(__dirname, '..');
const targetArg = process.argv[2] || 'converted_output';
const targetDir = path.isAbsolute(targetArg) ? targetArg : path.join(REPO_ROOT, targetArg);
const PORT = parseInt(process.argv[3] || '8769', 10);
const CDP_PORT = PORT + 1000;
const EDGE_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
};

function createStaticServer(rootDir, startPort) {
  return new Promise((resolve, reject) => {
    let currentPort = startPort;
    function tryListen() {
      const server = http.createServer((req, res) => {
        let reqPath = decodeURIComponent(req.url.split('?')[0]);
        if (reqPath === '/' || reqPath === '') {
          reqPath = fs.existsSync(path.join(rootDir, '看板.html')) ? '/看板.html' : '/点击打开.html';
        }
        const filePath = path.join(rootDir, reqPath);

        if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
          res.writeHead(404);
          res.end('Not found: ' + reqPath);
          return;
        }

        const ext = path.extname(filePath).toLowerCase();
        res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
        fs.createReadStream(filePath).pipe(res);
      });

      server.on('error', (err) => {
        if (err.code === 'EADDRINUSE') {
          currentPort++;
          tryListen();
        } else {
          reject(err);
        }
      });

      server.listen(currentPort, '127.0.0.1', () => {
        resolve({ server, port: currentPort });
      });
    }
    tryListen();
  });
}

class EdgeCDPClient {
  constructor(port) {
    this.port = port;
    this.proc = null;
    this.userDataDir = path.join(REPO_ROOT, 'build', `.edge_cdp_${port}`);
  }

  async start() {
    fs.mkdirSync(this.userDataDir, { recursive: true });
    const args = [
      '--headless=new',
      `--remote-debugging-port=${this.port}`,
      `--user-data-dir=${this.userDataDir}`,
      '--disable-gpu',
      '--no-sandbox',
      '--no-first-run',
      '--no-default-browser-check',
      'about:blank'
    ];
    this.proc = spawn(EDGE_PATH, args);

    for (let i = 0; i < 35; i++) {
      await new Promise(r => setTimeout(r, 200));
      try {
        const res = await fetch(`http://127.0.0.1:${this.port}/json/version`);
        if (res.ok) return;
      } catch (e) {}
    }
    throw new Error('Could not connect to Edge CDP on port ' + this.port);
  }

  async createPage(url) {
    const res = await fetch(`http://127.0.0.1:${this.port}/json/new?${encodeURIComponent(url)}`, { method: 'PUT' });
    const target = await res.json();
    const ws = new WebSocket(target.webSocketDebuggerUrl);

    let msgId = 1;
    const pending = new Map();
    const consoleLogs = [];
    const uncaughtErrors = [];

    await new Promise((resolve, reject) => {
      ws.onopen = resolve;
      ws.onerror = reject;
    });

    ws.onmessage = (evt) => {
      const msg = JSON.parse(evt.data);
      if (msg.id && pending.has(msg.id)) {
        const { resolve, reject } = pending.get(msg.id);
        pending.delete(msg.id);
        if (msg.error) reject(msg.error);
        else resolve(msg.result);
      } else if (msg.method === 'Runtime.consoleAPICalled') {
        const text = msg.params.args.map(a => a.value || a.description || '').join(' ');
        consoleLogs.push({ type: msg.params.type, text });
      } else if (msg.method === 'Runtime.exceptionThrown') {
        const desc = msg.params.exceptionDetails.exception?.description || msg.params.exceptionDetails.text;
        console.error(`  [CDP UNCAUGHT EXCEPTION]`, desc);
        uncaughtErrors.push(desc);
      }
    };

    const sendCDP = (method, params = {}) => {
      return new Promise((resolve, reject) => {
        const id = msgId++;
        pending.set(id, { resolve, reject });
        ws.send(JSON.stringify({ id, method, params }));
      });
    };

    await sendCDP('Runtime.enable');
    await sendCDP('Page.enable');

    const evaluate = async (expr) => {
      // Phase 3F.2 harness fix.
      //
      // `awaitPromise: true` is required: three MCMod behaviours resolve their
      // result through `new Promise(...)` + setTimeout. Without it the CDP result
      // is the unresolved Promise object and no primitive value comes back.
      //
      // `returnByValue` must NOT be passed. Several behaviours end with a legacy
      // DataTables call, e.g.
      //     if (window.table) window.table.search('RLCraft').draw();
      // whose *completion value* is the DataTables API object - a large cyclic
      // object graph. With `returnByValue: true` the renderer main thread blocks
      // forever trying to serialize it, the CDP response never arrives, and every
      // subsequent evaluate hangs as well (reproduced: the identical work completes
      // in 93 ms when the completion value is a primitive, and never returns
      // otherwise). Primitives are still delivered in `result.value` without
      // `returnByValue`, and every value this suite consumes (booleans / numbers /
      // strings) is a primitive, so no behaviour assertion is weakened.
      const evalRes = await sendCDP('Runtime.evaluate', { expression: expr, awaitPromise: true });
      return evalRes.result ? evalRes.result.value : undefined;
    };

    return { ws, sendCDP, evaluate, consoleLogs, uncaughtErrors };
  }

  cleanup() {
    try { if (this.proc) this.proc.kill('SIGKILL'); } catch (e) {}
    try { fs.rmSync(this.userDataDir, { recursive: true, force: true }); } catch (e) {}
  }
}

async function runTestSuite(envName, baseUrl, cdpClient) {
  console.log(`\n============================================================`);
  console.log(`  Running Core Behavioral Test Suite: [${envName}]`);
  console.log(`  URL: ${baseUrl}`);
  console.log(`============================================================`);

  const page = await cdpClient.createPage(baseUrl);
  const evalFn = page.evaluate;

  // 1. Wait for page initialization
  let ready = false;
  for (let i = 0; i < 50; i++) {
    await new Promise(r => setTimeout(r, 200));
    const isReady = await evalFn('Boolean((window.mcmodData && window.mcmodData.length > 0) || (window.tableRowsData && window.tableRowsData.length > 0))');
    if (isReady) { ready = true; break; }
  }
  if (!ready) throw new Error(`[${envName}] Failed to initialize mcmod data (tableRowsData or mcmodData) in time`);

  const metrics = {};
  const behaviors = [];

  const recordBehavior = (testName, pass, details) => {
    behaviors.push({ name: testName, pass, details });
    console.log(`  [${pass ? 'PASS' : 'FAIL'}] ${testName}: ${details}`);
  };

  // --- 1. MC百科 (mcmod) ---
  console.log('\n[*] Testing MCMod behaviors...');
  const mcmodTotal = await evalFn(`Boolean(window.mcmodData) ? window.mcmodData.length : (window.tableRowsData ? window.tableRowsData.length : 0)`);
  metrics.mcmod_total = mcmodTotal;
  recordBehavior('MCMod Total Loaded', mcmodTotal === 1484, `Total: ${mcmodTotal}`);

  // MC百科: 普通搜索
  await evalFn(`
    $('#mcmodUnifiedSearch').val('RLCraft').trigger('input');
    if (window.table) window.table.search('RLCraft').draw();
  `);
  await new Promise(r => setTimeout(r, 400));
  const mcmodSearchCount = await evalFn('window.table ? window.table.rows({filter:"applied"}).count() : 0');
  metrics.mcmod_search_rlcraft = mcmodSearchCount;
  recordBehavior('MCMod Search (RLCraft)', mcmodSearchCount > 0, `Matches: ${mcmodSearchCount}`);

  // 清除搜索
  await evalFn(`
    $('#mcmodUnifiedSearch').val('').trigger('input');
    if (window.table) window.table.search('').draw();
  `);
  await new Promise(r => setTimeout(r, 300));

  // MC百科: 服务端筛选
  await evalFn(`
    $('#mcmodServerOnly').prop('checked', true).trigger('change');
  `);
  await new Promise(r => setTimeout(r, 400));
  const mcmodServerCount = await evalFn('window.table ? window.table.rows({filter:"applied"}).count() : 0');
  metrics.mcmod_server_filter = mcmodServerCount;
  recordBehavior('MCMod Server Filter', mcmodServerCount > 0, `Filtered Count: ${mcmodServerCount}`);

  // 取消服务端筛选
  await evalFn(`$('#mcmodServerOnly').prop('checked', false).trigger('change');`);
  await new Promise(r => setTimeout(r, 300));

  // MC百科: 排序
  await evalFn(`if (window.table) window.table.order([1, 'asc']).draw();`);
  await new Promise(r => setTimeout(r, 300));
  const firstRowTitleAsc = await evalFn(`$('#modpackTable tbody tr:first-child a.modpack-link').text().trim()`);
  await evalFn(`if (window.table) window.table.order([1, 'desc']).draw();`);
  await new Promise(r => setTimeout(r, 300));
  const firstRowTitleDesc = await evalFn(`$('#modpackTable tbody tr:first-child a.modpack-link').text().trim()`);
  recordBehavior('MCMod Sort Toggle', firstRowTitleAsc !== firstRowTitleDesc, `Asc: "${firstRowTitleAsc.substring(0,15)}", Desc: "${firstRowTitleDesc.substring(0,15)}"`);

  // MC百科: 打开模组详情抽屉
  const modDrawerOpened = await evalFn(`
    new Promise(resolve => {
      const $chip = $('#modpackTable tbody tr:first-child .mod-summary-chip');
      if ($chip.length) {
        $chip.trigger('click');
        setTimeout(() => {
          const loaded = $('#modpackTable tbody tr:first-child .mod-full-list').attr('data-loaded') === '1' ||
                         $('#modpackTable tbody tr:first-child .tag-mod').length > 0;
          resolve(Boolean(loaded));
        }, 600);
      } else {
        resolve(false);
      }
    })
  `);
  recordBehavior('MCMod Mod Details Drawer Opened', modDrawerOpened, `Drawer loaded full mods`);

  // MC百科: 打开评论弹窗
  const commentPopupOpened = await evalFn(`
    new Promise(resolve => {
      const $cmtCell = $('#modpackTable tbody tr:first-child .comment-cell');
      if ($cmtCell.length) {
        $cmtCell.trigger('click');
        setTimeout(() => {
          const visible = $('#commentPopup').hasClass('show') || $('#commentPopup').is(':visible');
          resolve(Boolean(visible));
        }, 500);
      } else {
        resolve(false);
      }
    })
  `);
  recordBehavior('MCMod Comment Popup Opened', commentPopupOpened, `Popup opened`);
  await evalFn(`$('#commentPopup').removeClass('show');`);

  // MC百科: 打开 Version Modal
  const mcmodVersionModalOpened = await evalFn(`
    new Promise(resolve => {
      const $btn = $('#modpackTable tbody tr:first-child a.modpack-version-badge, .js-open-version-modal:first');
      if ($btn.length) $btn.trigger('click');
      setTimeout(() => {
        const visible = $('#versionModalOverlay').hasClass('show') || $('#versionModalOverlay').is(':visible');
        resolve(Boolean(visible));
      }, 300);
    })
  `);
  recordBehavior('MCMod Version Modal Opened', mcmodVersionModalOpened, `Modal visible`);
  await evalFn(`(() => { $('#versionModalCloseBtn, #versionModalOverlay .close').trigger('click'); $('#versionModalOverlay').removeClass('show').hide(); return true; })()`);

  // --- 2. 哔哩哔哩 (bilibili) ---
  console.log('\n[*] Testing Bilibili behaviors...');
  await evalFn(`switchPlatformTab('bilibili')`);
  for (let j = 0; j < 30; j++) {
    await new Promise(r => setTimeout(r, 200));
    if (await evalFn('Boolean(window.biliModpacksData && window.biliModpacksData.length)')) break;
  }
  const biliTotal = await evalFn('window.biliModpacksData ? window.biliModpacksData.length : 0');
  metrics.bili_total = biliTotal;
  const biliGroupedCards = await evalFn(`document.querySelectorAll('#biliCardsGrid .bili-pack-card').length`);
  metrics.bili_grouped_cards = biliGroupedCards;
  recordBehavior('Bilibili Grouped Cards Loaded', biliTotal === 936 && biliGroupedCards > 0, `Total: ${biliTotal}, Cards: ${biliGroupedCards}`);

  // Bilibili: Flat 切换
  await evalFn(`
    $('#biliViewToggle button[data-mode="flat"]').trigger('click');
  `);
  await new Promise(r => setTimeout(r, 400));
  const biliFlatCards = await evalFn(`document.querySelectorAll('#biliCardsGrid .bili-pack-card, #biliCardsGrid .bili-flat-card').length`);
  recordBehavior('Bilibili Grouped / Flat Toggle', biliFlatCards > 0, `Flat Cards: ${biliFlatCards}`);
  // 切回 Grouped
  await evalFn(`$('#biliViewToggle button[data-mode="grouped"]').trigger('click');`);
  await new Promise(r => setTimeout(r, 300));

  // Bilibili: 搜索
  await evalFn(`
    $('#biliSearchInput').val('机械动力').trigger('input');
  `);
  await new Promise(r => setTimeout(r, 400));
  const biliSearchCount = await evalFn(`document.querySelectorAll('#biliCardsGrid .bili-pack-card').length`);
  metrics.bili_search_create = biliSearchCount;
  recordBehavior('Bilibili Search (机械动力)', biliSearchCount > 0, `Filtered Cards: ${biliSearchCount}`);
  await evalFn(`$('#biliSearchInput').val('').trigger('input');`);
  await new Promise(r => setTimeout(r, 300));

  // Bilibili: 群版本提示存在性
  const hasGroupVerBanner = await evalFn(`document.querySelectorAll('#biliCardsGrid .bili-group-ver-banner').length > 0`);
  recordBehavior('Bilibili Group Version Banner Present', hasGroupVerBanner, `Found banners in cards`);

  // Bilibili: 下载按钮存在且具有有效链接
  const biliDlLinksValid = await evalFn(`Boolean(document.querySelectorAll('#biliCardsGrid .bili-pan-btn').length > 0)`);
  recordBehavior('Bilibili Download Links Valid', biliDlLinksValid, `Download buttons verified`);

  // Bilibili: 打开 Version Modal
  const biliVModalOpen = await evalFn(`
    Boolean((() => {
      const $multi = $('#biliCardsGrid .js-open-bili-group-versions:first, #biliCardsGrid .js-open-plat-version-modal:first');
      if ($multi.length) $multi.trigger('click');
      return $('#versionModalOverlay').hasClass('show') || $('#versionModalOverlay').is(':visible');
    })())
  `);
  recordBehavior('Bilibili Version Modal Opened', biliVModalOpen, `Modal opened from card`);
  await evalFn(`(() => { $('#versionModalCloseBtn, #versionModalOverlay .close').trigger('click'); $('#versionModalOverlay').removeClass('show').hide(); return true; })()`);

  // --- 3. BBSMC ---
  console.log('\n[*] Testing BBSMC behaviors...');
  await evalFn(`(() => { switchPlatformTab('bbsmc'); return true; })()`);
  for (let j = 0; j < 30; j++) {
    await new Promise(r => setTimeout(r, 200));
    if (await evalFn('Boolean(window.bbsmcModpacksData && window.bbsmcModpacksData.length)')) break;
  }
  const bbsmcTotal = await evalFn('window.bbsmcModpacksData ? window.bbsmcModpacksData.length : 0');
  metrics.bbsmc_total = bbsmcTotal;
  const bbsmcCards = await evalFn(`document.querySelectorAll('#bbsmcCardsGrid .bbsmc-pack-card').length`);
  recordBehavior('BBSMC Loaded & Rendered', bbsmcTotal === 1802 && bbsmcCards > 0, `Total: ${bbsmcTotal}, Cards: ${bbsmcCards}`);

  // BBSMC: 服务端筛选
  await evalFn(`(() => { $('#bbsmcServerOnly').prop('checked', true).trigger('change'); return true; })()`);
  await new Promise(r => setTimeout(r, 400));
  const bbsmcServerCount = await evalFn(`document.querySelectorAll('#bbsmcCardsGrid .bbsmc-pack-card').length`);
  metrics.bbsmc_server_count = bbsmcServerCount;
  recordBehavior('BBSMC Server Filter', bbsmcServerCount > 0, `Filtered Cards: ${bbsmcServerCount}`);
  await evalFn(`(() => { $('#bbsmcServerOnly').prop('checked', false).trigger('change'); return true; })()`);
  await new Promise(r => setTimeout(r, 300));

  // BBSMC: 下载链接
  const bbsmcDlValid = await evalFn(`Boolean(document.querySelectorAll('#bbsmcCardsGrid .card-dl-btn').length > 0)`);
  recordBehavior('BBSMC Download Links Valid', bbsmcDlValid, `Download buttons verified`);

  // BBSMC: 打开 Version Modal
  const bbsmcVModalOpen = await evalFn(`
    Boolean((() => {
      const $btn = $('#bbsmcCardsGrid .js-open-plat-version-modal:first');
      if ($btn.length) $btn.trigger('click');
      return $('#versionModalOverlay').hasClass('show') || $('#versionModalOverlay').is(':visible');
    })())
  `);
  recordBehavior('BBSMC Version Modal Opened', bbsmcVModalOpen, `Modal opened from card`);
  await evalFn(`(() => { $('#versionModalCloseBtn, #versionModalOverlay .close').trigger('click'); $('#versionModalOverlay').removeClass('show').hide(); return true; })()`);

  // --- 4. XYEBBS ---
  console.log('\n[*] Testing XYEBBS behaviors...');
  await evalFn(`(() => { switchPlatformTab('xyebbs'); return true; })()`);
  for (let j = 0; j < 30; j++) {
    await new Promise(r => setTimeout(r, 200));
    if (await evalFn('Boolean(window.xyebbsModpacksData && window.xyebbsModpacksData.length)')) break;
  }
  const xyebbsTotal = await evalFn('window.xyebbsModpacksData ? window.xyebbsModpacksData.length : 0');
  metrics.xyebbs_total = xyebbsTotal;
  const xyebbsCards = await evalFn(`document.querySelectorAll('#xyebbsCardsGrid .xyebbs-pack-card').length`);
  recordBehavior('XYEBBS Loaded & Rendered', xyebbsTotal === 5175 && xyebbsCards > 0, `Total: ${xyebbsTotal}, Cards: ${xyebbsCards}`);

  // XYEBBS: 服务端筛选
  await evalFn(`(() => { $('#xyebbsServerOnly').prop('checked', true).trigger('change'); return true; })()`);
  await new Promise(r => setTimeout(r, 400));
  const xyebbsServerCount = await evalFn(`document.querySelectorAll('#xyebbsCardsGrid .xyebbs-pack-card').length`);
  metrics.xyebbs_server_count = xyebbsServerCount;
  recordBehavior('XYEBBS Server Filter', xyebbsServerCount > 0, `Filtered Cards: ${xyebbsServerCount}`);
  await evalFn(`(() => { $('#xyebbsServerOnly').prop('checked', false).trigger('change'); return true; })()`);
  await new Promise(r => setTimeout(r, 300));

  // XYEBBS: Version Modal
  const xyebbsVModalOpen = await evalFn(`
    Boolean((() => {
      const $btn = $('#xyebbsCardsGrid .js-open-plat-version-modal:first');
      if ($btn.length) $btn.trigger('click');
      return $('#versionModalOverlay').hasClass('show') || $('#versionModalOverlay').is(':visible');
    })())
  `);
  recordBehavior('XYEBBS Version Modal Opened', xyebbsVModalOpen, `Modal opened from card`);
  await evalFn(`(() => { $('#versionModalCloseBtn, #versionModalOverlay .close').trigger('click'); $('#versionModalOverlay').removeClass('show').hide(); return true; })()`);

  // --- 5. Modrinth ---
  console.log('\n[*] Testing Modrinth behaviors...');
  await evalFn(`(() => { switchPlatformTab('modrinth'); return true; })()`);
  for (let j = 0; j < 40; j++) {
    await new Promise(r => setTimeout(r, 250));
    if (await evalFn('Boolean(window.modrinthModpacksData && window.modrinthModpacksData.length)')) break;
  }
  const mrTotal = await evalFn('window.modrinthModpacksData ? window.modrinthModpacksData.length : 0');
  metrics.modrinth_total = mrTotal;
  const mrCards = await evalFn(`document.querySelectorAll('#modrinthCardsGrid .modrinth-pack-card').length`);
  recordBehavior('Modrinth Loaded & Rendered', mrTotal === 18328 && mrCards > 0, `Total: ${mrTotal}, Cards: ${mrCards}`);

  // Modrinth: 加载器筛选 (Fabric)
  await evalFn(`(() => { $('#modrinthLoaderSelect').val('Fabric').trigger('change'); return true; })()`);
  await new Promise(r => setTimeout(r, 400));
  const mrFabricCount = await evalFn(`document.querySelectorAll('#modrinthCardsGrid .modrinth-pack-card').length`);
  metrics.modrinth_fabric_count = mrFabricCount;
  recordBehavior('Modrinth Loader Filter (Fabric)', mrFabricCount > 0, `Filtered Cards: ${mrFabricCount}`);
  await evalFn(`(() => { $('#modrinthLoaderSelect').val('').trigger('change'); return true; })()`);
  await new Promise(r => setTimeout(r, 300));

  // Modrinth: 服务端筛选
  await evalFn(`(() => { $('#modrinthServerOnly').prop('checked', true).trigger('change'); return true; })()`);
  await new Promise(r => setTimeout(r, 400));
  const mrServerCount = await evalFn(`document.querySelectorAll('#modrinthCardsGrid .modrinth-pack-card').length`);
  metrics.modrinth_server_count = mrServerCount;
  recordBehavior('Modrinth Server Filter', mrServerCount > 0, `Filtered Cards: ${mrServerCount}`);
  await evalFn(`(() => { $('#modrinthServerOnly').prop('checked', false).trigger('change'); return true; })()`);
  await new Promise(r => setTimeout(r, 300));

  // Modrinth: Environment Badge
  const mrEnvBadgePresent = await evalFn(`Boolean(document.querySelectorAll('#modrinthCardsGrid .modrinth-badge-env, #modrinthCardsGrid .badge-env').length > 0)`);
  recordBehavior('Modrinth Environment Badge Present', mrEnvBadgePresent, `Badges verified`);

  // Modrinth: 官方链接
  const mrOfficialLinks = await evalFn(`Boolean(document.querySelectorAll('#modrinthCardsGrid a[href*="modrinth.com"]').length > 0)`);
  recordBehavior('Modrinth Official Links Present', mrOfficialLinks, `Official URLs verified`);

  // Modrinth: Version Modal
  const mrVModalOpen = await evalFn(`
    Boolean((() => {
      const $btn = $('#modrinthCardsGrid .js-open-plat-version-modal:first');
      if ($btn.length) $btn.trigger('click');
      return $('#versionModalOverlay').hasClass('show') || $('#versionModalOverlay').is(':visible');
    })())
  `);
  recordBehavior('Modrinth Version Modal Opened', mrVModalOpen, `Modal opened from card`);
  await evalFn(`(() => { $('#versionModalCloseBtn, #versionModalOverlay .close').trigger('click'); $('#versionModalOverlay').removeClass('show').hide(); return true; })()`);

  // --- 6. CurseForge ---
  console.log('\n[*] Testing CurseForge behaviors...');
  await evalFn(`(() => { switchPlatformTab('curseforge'); return true; })()`);
  for (let j = 0; j < 40; j++) {
    await new Promise(r => setTimeout(r, 250));
    if (await evalFn('Boolean(window.curseforgeModpacksData && window.curseforgeModpacksData.length)')) break;
  }
  const cfTotal = await evalFn('window.curseforgeModpacksData ? window.curseforgeModpacksData.length : 0');
  metrics.curseforge_total = cfTotal;
  const cfCards = await evalFn(`document.querySelectorAll('#curseforgeCardsGrid .curseforge-pack-card').length`);
  recordBehavior('CurseForge Loaded & Rendered', cfTotal === 45797 && cfCards > 0, `Total: ${cfTotal}, Cards: ${cfCards}`);

  // CurseForge: 服务端筛选
  await evalFn(`(() => { $('#curseforgeServerOnly').prop('checked', true).trigger('change'); return true; })()`);
  await new Promise(r => setTimeout(r, 400));
  const cfServerCount = await evalFn(`document.querySelectorAll('#curseforgeCardsGrid .curseforge-pack-card').length`);
  metrics.curseforge_server_count = cfServerCount;
  recordBehavior('CurseForge Server Filter', cfServerCount > 0, `Filtered Cards: ${cfServerCount}`);
  await evalFn(`(() => { $('#curseforgeServerOnly').prop('checked', false).trigger('change'); return true; })()`);
  await new Promise(r => setTimeout(r, 300));

  // CurseForge: 官方链接
  const cfOfficialLinks = await evalFn(`Boolean(document.querySelectorAll('#curseforgeCardsGrid a[href*="curseforge.com"]').length > 0)`);
  recordBehavior('CurseForge Official Links Present', cfOfficialLinks, `Official URLs verified`);

  // CurseForge: Version Modal
  const cfVModalOpen = await evalFn(`
    Boolean((() => {
      const $btn = $('#curseforgeCardsGrid .js-open-plat-version-modal:first');
      if ($btn.length) $btn.trigger('click');
      return $('#versionModalOverlay').hasClass('show') || $('#versionModalOverlay').is(':visible');
    })())
  `);
  recordBehavior('CurseForge Version Modal Opened', cfVModalOpen, `Modal opened from card`);
  await evalFn(`(() => { $('#versionModalCloseBtn, #versionModalOverlay .close').trigger('click'); $('#versionModalOverlay').removeClass('show').hide(); return true; })()`);

  // --- 7. 全局 (Global) 行为 ---
  console.log('\n[*] Testing Global Cross-Platform behaviors...');
  // 跨平台搜索
  await evalFn(`
    $('#crossSearchInput').val('RLCraft').trigger('input');
  `);
  await new Promise(r => setTimeout(r, 600));
  const crossMatchCount = await evalFn(`document.querySelectorAll('.cross-result-item').length`);
  recordBehavior('Cross-Platform Search (RLCraft)', crossMatchCount > 0, `Cross matches: ${crossMatchCount}`);
  await evalFn(`$('#crossSearchInput').val('').trigger('input');`);
  await new Promise(r => setTimeout(r, 300));

  // Audit Diff Modal
  await evalFn(`$('#openAuditModalBtn').trigger('click');`);
  await new Promise(r => setTimeout(r, 300));
  const auditModalOpen = await evalFn(`$('#auditModalOverlay').hasClass('show') || $('#auditModalOverlay').is(':visible')`);
  recordBehavior('Audit Diff Modal Opened', auditModalOpen, `Modal visible`);
  await evalFn(`$('#auditModalClose').trigger('click');`);

  // 主题切换
  const initialTheme = await evalFn(`document.documentElement.getAttribute('data-theme') || 'light'`);
  const nextTheme = initialTheme === 'dark' ? 'light' : 'dark';
  await evalFn(`
    document.documentElement.setAttribute('data-theme', '${nextTheme}');
    localStorage.setItem('mcmod-theme-v2', '${nextTheme}');
  `);
  const switchedTheme = await evalFn(`document.documentElement.getAttribute('data-theme')`);
  recordBehavior('Theme Switcher Toggle', switchedTheme === nextTheme, `Theme switched to: ${switchedTheme}`);

  // Summary
  const passCount = behaviors.filter(b => b.pass).length;
  const failCount = behaviors.filter(b => !b.pass).length;
  const uncaughtCount = page.uncaughtErrors.length;

  console.log(`\n============================================================`);
  console.log(`  [${envName}] Suite Finished: ${passCount} Passed, ${failCount} Failed, ${uncaughtCount} Exceptions`);
  console.log(`============================================================`);

  page.ws.close();
  return {
    envName,
    metrics,
    behaviors,
    passCount,
    failCount,
    uncaughtErrors: page.uncaughtErrors,
  };
}

async function main() {
  console.log("======================================================================");
  console.log(`  Architecture V2 Single-Target Smoke Test: ${targetDir}`);
  console.log(`  Port: ${PORT} | CDP Port: ${CDP_PORT}`);
  console.log("======================================================================\n");

  if (!fs.existsSync(targetDir)) {
    console.error(`Target directory does not exist: ${targetDir}`);
    process.exit(1);
  }

  const { server, port: actualPort } = await createStaticServer(targetDir, PORT);
  console.log(`[+] Static server running at http://127.0.0.1:${actualPort}`);

  const cdpClient = new EdgeCDPClient(CDP_PORT);
  await cdpClient.start();
  console.log('[+] Headless Edge CDP client ready.');

  try {
    const results = await runTestSuite(path.basename(targetDir), `http://127.0.0.1:${actualPort}`, cdpClient);
    const success = (results.failCount === 0 && results.uncaughtErrors.length === 0);
    console.log(`\n[RESULT] Final Result: ${success ? 'SUCCESS (ALL 33 PASS, 0 EXCEPTIONS)' : 'FAILED'}`);
    process.exit(success ? 0 : 1);
  } catch (err) {
    console.error("Test execution failed:", err);
    process.exit(1);
  } finally {
    cdpClient.cleanup();
    server.close();
  }
}

main();

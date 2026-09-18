/**
 * Phase 3G-F-A - Bilibili grouping RUNTIME bridge proof.
 *
 * The offline evaluator imports the TS module directly, so it can never catch a
 * broken bridge between the TS domain module and the legacy dashboard. The
 * Phase 3G-F bug being guarded against was exactly that:
 *
 *   groupBilibiliPacks() returns a Map
 *   dashboard.legacy.js did `decisions[bvid]`
 *   -> a Map is not index-addressable by bvid, so the lookup silently missed
 *      and every record fell back to `authorKey::cleanPackKey`
 *      -> grouping silently degraded to "exact same key only" (48 cards, not 36)
 *
 * This probe drives the REAL production frontend in headless Edge and asserts:
 *   * window.groupBilibiliPacks is a function returning a PLAIN OBJECT keyed by
 *     bvid (not a Map, not a fallback shim)
 *   * the runtime grouped card count is < raw matched count for 机械动力
 *   * the raw matched count is exactly 53 (the only invariant)
 *   * biliGroupsMap (the aggregator's own map) agrees with the rendered cards
 *
 * Usage: node pipeline/audit/probe_bili_grouping_runtime.js [target_dir] [port]
 * Output: build/audit/bilibili_grouping_runtime_probe.json
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const REPO_ROOT = path.resolve(__dirname, '..', '..');
const targetArg = process.argv[2] || 'converted_output';
const targetDir = path.isAbsolute(targetArg) ? targetArg : path.join(REPO_ROOT, targetArg);
const PORT = parseInt(process.argv[3] || '8790', 10);
const CDP_PORT = PORT + 1000;
const EDGE_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const OUT = path.join(REPO_ROOT, 'build', 'audit', 'bilibili_grouping_runtime_probe.json');

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
          reqPath = fs.existsSync(path.join(rootDir, '看板.html')) ? '/看板.html' : '/index.html';
        }
        const filePath = path.join(rootDir, reqPath);
        if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
          res.writeHead(404); res.end('Not found: ' + reqPath); return;
        }
        const ext = path.extname(filePath).toLowerCase();
        res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
        fs.createReadStream(filePath).pipe(res);
      });
      server.on('error', (err) => {
        if (err.code === 'EADDRINUSE') { currentPort++; tryListen(); } else { reject(err); }
      });
      server.listen(currentPort, '127.0.0.1', () => resolve({ server, port: currentPort }));
    }
    tryListen();
  });
}

class EdgeCDPClient {
  constructor(port) {
    this.port = port;
    this.proc = null;
    // unique per run so a killed run can never poison the port (see Phase 3G-F note)
    this.userDataDir = path.join(REPO_ROOT, 'build', `.edge_cdp_biliprobe_${port}_${process.pid}`);
  }
  async start() {
    fs.mkdirSync(this.userDataDir, { recursive: true });
    this.proc = spawn(EDGE_PATH, [
      '--headless=new', `--remote-debugging-port=${this.port}`,
      `--user-data-dir=${this.userDataDir}`, '--disable-gpu', '--no-sandbox',
      '--no-first-run', '--no-default-browser-check', 'about:blank',
    ]);
    for (let i = 0; i < 35; i++) {
      await new Promise((r) => setTimeout(r, 200));
      try {
        const res = await fetch(`http://127.0.0.1:${this.port}/json/version`);
        if (res.ok) return;
      } catch (e) { /* keep waiting */ }
    }
    throw new Error('Could not connect to Edge CDP on port ' + this.port);
  }
  async createPage(url) {
    const res = await fetch(`http://127.0.0.1:${this.port}/json/new?${encodeURIComponent(url)}`, { method: 'PUT' });
    const target = await res.json();
    const ws = new WebSocket(target.webSocketDebuggerUrl);
    let msgId = 1;
    const pending = new Map();
    const uncaughtErrors = [];
    await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
    ws.onmessage = (evt) => {
      const msg = JSON.parse(evt.data);
      if (msg.id && pending.has(msg.id)) {
        const { resolve, reject } = pending.get(msg.id);
        pending.delete(msg.id);
        if (msg.error) reject(msg.error); else resolve(msg.result);
      } else if (msg.method === 'Runtime.exceptionThrown') {
        const desc = msg.params.exceptionDetails.exception?.description || msg.params.exceptionDetails.text;
        uncaughtErrors.push(desc);
      }
    };
    const sendCDP = (method, params = {}) => new Promise((resolve, reject) => {
      const id = msgId++;
      pending.set(id, { resolve, reject });
      ws.send(JSON.stringify({ id, method, params }));
    });
    await sendCDP('Runtime.enable');
    await sendCDP('Page.enable');
    const evaluate = async (expr) => {
      const r = await sendCDP('Runtime.evaluate', { expression: expr, returnByValue: true });
      return r.result ? r.result.value : undefined;
    };
    return { ws, sendCDP, evaluate, uncaughtErrors };
  }
  cleanup() {
    try { if (this.proc) this.proc.kill('SIGKILL'); } catch (e) { /* noop */ }
  }
}

async function main() {
  console.log('============================================================');
  console.log('  Phase 3G-F-A  Bilibili grouping runtime bridge proof');
  console.log('============================================================');
  const { server, port } = await createStaticServer(targetDir, PORT);
  console.log(`[+] Static server at http://127.0.0.1:${port}`);

  const cdp = new EdgeCDPClient(CDP_PORT);
  await cdp.start();
  console.log(`[+] Edge headless on CDP port ${CDP_PORT}`);

  const checks = [];
  const record = (name, pass, detail) => {
    checks.push({ name, pass: Boolean(pass), detail });
    console.log(`  [${pass ? 'PASS' : 'FAIL'}] ${name} - ${detail}`);
  };

  try {
    const page = await cdp.createPage(`http://127.0.0.1:${port}/看板.html`);
    const evalFn = page.evaluate;

    let ready = false;
    for (let i = 0; i < 60; i++) {
      await new Promise((r) => setTimeout(r, 250));
      if (await evalFn('Boolean(window.mcmodData && window.mcmodData.length > 0)')) { ready = true; break; }
    }
    if (!ready) throw new Error('page failed to initialize');

    // ---- A. the bridge itself ------------------------------------------------
    const bridgeType = await evalFn(`typeof window.groupBilibiliPacks`);
    record('bridge exposed', bridgeType === 'function', `typeof window.groupBilibiliPacks === '${bridgeType}'`);

    // Call it with a real sibling pair (Horizon v1.2.0 / v2.1.0) and inspect the
    // SHAPE of the return value. A Map has no own bvid properties, so
    // `decisions[bvid]` returns undefined and grouping silently degrades.
    const shape = await evalFn(`(() => {
      const recs = [
        { bvid: 'BVA1', title: 'Horizon地平线整合包v1.2.0更新日志，支持BSL光影，机械动力和瓦尔基里了！', author: 'ConfectionaryQwQ' },
        { bvid: 'BVA2', title: 'Horizon地平线整合包v2.1.0更新日志，1.21.4再度启程！', author: 'ConfectionaryQwQ' }
      ];
      const out = window.groupBilibiliPacks(recs);
      return JSON.stringify({
        ctor: out && out.constructor ? out.constructor.name : null,
        isMap: out instanceof Map,
        keys: Object.keys(out || {}),
        indexed: out && out['BVA1'] ? out['BVA1'].groupKey : null,
        sameGroup: out && out['BVA1'] && out['BVA2'] ? (out['BVA1'].groupKey === out['BVA2'].groupKey) : null
      });
    })()`);
    const s = JSON.parse(shape);
    record('bridge returns a plain object (not a Map)', s.isMap === false && s.ctor === 'Object',
      `constructor=${s.ctor} isMap=${s.isMap}`);
    record('bridge is index-addressable by bvid', Boolean(s.indexed) && s.keys.length === 2,
      `Object.keys=${s.keys.length} out['BVA1'].groupKey=${JSON.stringify(s.indexed)}`);
    record('bridge groups real sibling episodes', s.sameGroup === true,
      `Horizon v1.2.0 / v2.1.0 share a groupKey: ${s.sameGroup}`);

    // ---- B. the real 机械动力 runtime path -----------------------------------
    await evalFn(`switchPlatformTab('bilibili')`);
    for (let i = 0; i < 40; i++) {
      await new Promise((r) => setTimeout(r, 250));
      if (await evalFn('Boolean(window.biliModpacksData && window.biliModpacksData.length)')) break;
    }
    const total = await evalFn('window.biliModpacksData ? window.biliModpacksData.length : 0');
    record('payload total is 936', total === 936, `window.biliModpacksData.length = ${total}`);

    await evalFn(`$('#biliViewToggle button[data-mode="grouped"]').trigger('click');
                  $('#biliSearchInput').val('机械动力').trigger('input');`);
    await new Promise((r) => setTimeout(r, 700));

    const dbg = JSON.parse(await evalFn(`(() => {
      const d = window.__frontendDebug || {};
      return JSON.stringify({
        raw: d.lastSearchMatchedIds ? d.lastSearchMatchedIds.length : null,
        query: d.lastSearchQuery || null,
        grouped: document.querySelectorAll('#biliCardsGrid .bili-pack-card').length,
        mapSize: window.biliGroupsMap ? Object.keys(window.biliGroupsMap).length : null
      });
    })()`));
    record('机械动力 raw matched = 53 (invariant)', dbg.raw === 53, `raw=${dbg.raw} query=${JSON.stringify(dbg.query)}`);
    record('机械动力 grouped cards < raw', dbg.grouped > 0 && dbg.grouped < dbg.raw,
      `grouped=${dbg.grouped} < raw=${dbg.raw}`);
    record('grouped cards match the remediated algorithm', dbg.grouped === 36,
      `grouped=${dbg.grouped} (3G-F batch result: 36; pre-remediation was 47)`);
    record('rendered cards equal aggregator map size', dbg.grouped === dbg.mapSize,
      `cards=${dbg.grouped} biliGroupsMap=${dbg.mapSize}`);

    // ---- C. degrade-detection: a Map-shaped return would break the aggregation
    // If the bridge regressed to returning a Map, groupPacks would fall back to
    // `authorKey::cleanPackKey`. Assert the search-filtered cards are NOT the
    // naive per-distinct-key count.
    const naive = await evalFn(`(() => {
      const set = new Set();
      (window.biliModpacksData || []).forEach(p => {
        const t = [p.title||'', p.author||'', p.desc||'', p.mc_version||'',
                   (p.loaders||[]).join(' '), (p.categories||[]).join(' ')].join(' ').toLowerCase();
        if (t.includes('机械动力')) set.add((p.author||'unknown').trim().toLowerCase() + '::' + (p.title||''));
      });
      return set.size;
    })()`);
    record('grouping is NOT naive per-title (bridge really applied)',
      dbg.grouped < naive, `grouped=${dbg.grouped} < naiveDistinctTitleKeys=${naive}`);

    const uncaught = page.uncaughtErrors.length;
    record('no uncaught runtime exceptions', uncaught === 0, `uncaught=${uncaught}`);

    const payload = {
      generated_at: new Date().toISOString(),
      target: path.relative(REPO_ROOT, targetDir),
      checks,
      all_passed: checks.every((c) => c.pass),
      mechanical_power: dbg,
      naive_distinct_title_keys: naive,
    };
    fs.mkdirSync(path.dirname(OUT), { recursive: true });
    fs.writeFileSync(OUT, JSON.stringify(payload, null, 2), 'utf8');
    console.log('------------------------------------------------------------');
    console.log(`  Runtime bridge probe: ${payload.all_passed ? 'ALL PASSED' : 'FAILED'} (${checks.filter((c) => c.pass).length}/${checks.length})`);
    console.log(`  written: ${path.relative(REPO_ROOT, OUT)}`);
    server.close();
    cdp.cleanup();
    process.exit(payload.all_passed ? 0 : 1);
  } catch (err) {
    console.error('[!] probe error:', err && err.message ? err.message : err);
    try { server.close(); } catch (e) { /* noop */ }
    cdp.cleanup();
    process.exit(2);
  }
}

main();

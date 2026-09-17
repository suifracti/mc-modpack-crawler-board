const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const REPO_ROOT = path.resolve(__dirname, '..', '..');
const targetDir = path.join(REPO_ROOT, 'converted_output');
const PORT = 8892;
const CDP_PORT = 9892;
const EDGE_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
};

function createStaticServer(rootDir, port) {
  return new Promise((resolve, reject) => {
    const server = http.createServer((req, res) => {
      let reqPath = decodeURIComponent(req.url.split('?')[0]);
      if (reqPath === '/' || reqPath === '') {
        reqPath = fs.existsSync(path.join(rootDir, '看板.html')) ? '/看板.html' : '/index.html';
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
    server.on('error', reject);
    server.listen(port, '127.0.0.1', () => resolve(server));
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
      'about:blank',
    ];
    this.proc = spawn(EDGE_PATH, args);

    for (let i = 0; i < 35; i++) {
      await new Promise((r) => setTimeout(r, 200));
      try {
        const res = await fetch(`http://127.0.0.1:${this.port}/json/version`);
        if (res.ok) return;
      } catch (e) {}
    }
    throw new Error('Could not connect to Edge CDP on port ' + this.port);
  }

  async createPage(url) {
    const res = await fetch(`http://127.0.0.1:${this.port}/json/new?${encodeURIComponent(url)}`, {
      method: 'PUT',
    });
    const target = await res.json();
    const ws = new WebSocket(target.webSocketDebuggerUrl);

    let msgId = 1;
    const pending = new Map();

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
      const evalRes = await sendCDP('Runtime.evaluate', { expression: expr, awaitPromise: true });
      return evalRes.result ? evalRes.result.value : undefined;
    };

    return { ws, sendCDP, evaluate };
  }

  cleanup() {
    if (this.proc) {
      try {
        this.proc.kill();
      } catch (e) {}
    }
  }
}

const QUERIES = [
  // Pack Identity
  { query: 'RLCraft', group: 'Pack Identity' },
  { query: 'GreedyCraft', group: 'Pack Identity' },
  { query: 'Age of Fate', group: 'Pack Identity' },
  { query: 'Enigmatica', group: 'Pack Identity' },
  { query: 'DawnCraft', group: 'Pack Identity' },
  // Core-theme Mod
  { query: 'Create', group: 'Core-theme Mod' },
  { query: 'Cobblemon', group: 'Core-theme Mod' },
  { query: 'GregTech', group: 'Core-theme Mod' },
  { query: 'Mekanism', group: 'Core-theme Mod' },
  { query: 'Botania', group: 'Core-theme Mod' },
  // Utility / Library
  { query: 'JEI', group: 'Utility / Library' },
  { query: 'Architectury', group: 'Utility / Library' },
  { query: 'Cloth Config', group: 'Utility / Library' },
  { query: 'Fabric API', group: 'Utility / Library' },
  { query: 'Mouse Tweaks', group: 'Utility / Library' },
  // Ambiguous Mod
  { query: 'Twilight Forest', group: 'Ambiguous' },
  { query: 'Applied Energistics', group: 'Ambiguous' },
  { query: 'Ice and Fire', group: 'Ambiguous' },
  { query: 'Thermal', group: 'Ambiguous' },
  { query: 'Avaritia', group: 'Ambiguous' },
];

async function main() {
  console.log('[+] Starting static server on port', PORT);
  const server = await createStaticServer(targetDir, PORT);

  const cdp = new EdgeCDPClient(CDP_PORT);
  console.log('[+] Starting Edge CDP on port', CDP_PORT);
  await cdp.start();

  console.log('[+] Opening page...');
  const page = await cdp.createPage(`http://127.0.0.1:${PORT}`);

  console.log('[+] Waiting for MCMod data & DataTables ready...');
  for (let i = 0; i < 40; i++) {
    await new Promise((r) => setTimeout(r, 250));
    const loaded = await page.evaluate(
      `Boolean(window.mcmodData && window.mcmodData.length === 1484 && window.table && window.table.rows().count() === 1484)`
    );
    if (loaded) break;
  }

  console.log('[+] Ready! Executing 20 queries against Production Browser Runtime...');

  const results = [];

  for (const item of QUERIES) {
    const q = item.query;
    // Set query in input and trigger search
    await page.evaluate(`(() => {
      $('#mcmodUnifiedSearch').val(${JSON.stringify(q)}).trigger('input');
      if (window.table) window.table.search(${JSON.stringify(q)}).draw();
      return true;
    })()`);

    // wait for debounce & draw
    await new Promise((r) => setTimeout(r, 350));

    const rawJsonStr = await page.evaluate(`(() => {
      const dbg = window.__frontendDebug || {};
      const tsIds = (dbg.lastSearchMatchedIds || []).map(Number);
      tsIds.sort((a, b) => a - b);

      let dtIds = [];
      if (window.table) {
        dtIds = window.table.rows({ filter: 'applied' }).data().toArray().map(r => Number(r.mid));
        dtIds.sort((a, b) => a - b);
      }

      const reasons = dbg.lastSearchMatchReasons || {};
      const sampleReasons = {};
      for (const id of tsIds.slice(0, 5)) {
        if (reasons[id]) {
          sampleReasons[id] = {
            primaryReasonLabel: reasons[id].primaryReasonLabel,
            fields: reasons[id].fields,
          };
        }
      }

      return JSON.stringify({
        query: ${JSON.stringify(q)},
        tsMatchedCount: tsIds.length,
        tsMatchedIds: tsIds,
        dtMatchedCount: dtIds.length,
        dtMatchedIds: dtIds,
        reasonsCount: Object.keys(reasons).length,
        sampleReasons,
        searchCalls: dbg.searchCalls || 0
      });
    })()`);

    const parsedData = JSON.parse(rawJsonStr || '{}');

    results.push({
      ...item,
      runtime: parsedData,
    });

    console.log(
      `Query: "${q.padEnd(20)}" | TS Engine: ${String(parsedData.tsMatchedCount).padStart(4)} | DataTable: ${String(parsedData.dtMatchedCount).padStart(4)} | Equal?: ${parsedData.tsMatchedCount === parsedData.dtMatchedCount}`
    );
  }

  // Clear search at end
  await page.evaluate(`(() => {
    $('#mcmodUnifiedSearch').val('').trigger('input');
    if (window.table) window.table.search('').draw();
    return true;
  })()`);

  page.ws.close();
  cdp.cleanup();
  server.close();

  const outPath = path.join(REPO_ROOT, 'build', 'audit', 'mcmod_runtime_search_20.json');
  fs.writeFileSync(outPath, JSON.stringify(results, null, 2), 'utf8');
  console.log('[+] Saved runtime search results to', outPath);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

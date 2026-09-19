const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const REPO_ROOT = path.resolve(__dirname, '..', '..');
// Phase 3G-D.1R.1: allow auditing any target directory (e.g. the rolled-back
// `converted_output`), not just the legacy fallback staging bundle.
const legacyDir = process.argv[2]
  ? path.resolve(REPO_ROOT, process.argv[2])
  : path.join(REPO_ROOT, 'build', 'frontend_legacy_current_data');
const targetLabel = process.argv[2] ? process.argv[2] : 'frontend_legacy_current_data';
const PORT = 8894;
const CDP_PORT = 9894;
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
  'RLCraft',
  'Age of Fate',
  'Cloth Config',
  'Fabric API',
  'Mouse Tweaks',
  'Applied Energistics',
  'Ice and Fire',
];

async function main() {
  console.log('[+] Starting legacy static server on port', PORT);
  const server = await createStaticServer(legacyDir, PORT);

  const cdp = new EdgeCDPClient(CDP_PORT);
  console.log('[+] Starting Edge CDP on port', CDP_PORT);
  await cdp.start();

  console.log('[+] Opening legacy page...');
  const page = await cdp.createPage(`http://127.0.0.1:${PORT}`);

  console.log('[+] Waiting for legacy DataTables ready...');
  for (let i = 0; i < 40; i++) {
    await new Promise((r) => setTimeout(r, 300));
    const ready = await page.evaluate(
      `Boolean(window.table && window.table.rows().count() === 1484)`
    );
    if (ready) break;
  }

  console.log('[+] Legacy DataTables is ready! Running queries...');

  const results = {};

  for (const q of QUERIES) {
    await page.evaluate(`(() => {
      $('#mcmodUnifiedSearch').val(${JSON.stringify(q)}).trigger('input');
      if (window.table) window.table.search(${JSON.stringify(q)}).draw();
      return true;
    })()`);

    await new Promise((r) => setTimeout(r, 400));

    const rawJson = await page.evaluate(`(() => {
      let matchedCount = 0;
      let matchedIds = [];
      if (window.table) {
        matchedCount = window.table.rows({ filter: 'applied' }).count();
        // In legacy, mid was in data-mid attribute on tr or in rowData
        const rows = window.table.rows({ filter: 'applied' }).nodes().toArray();
        matchedIds = rows.map(tr => $(tr).attr('data-mid') || $(tr).data('mid')).filter(Boolean).map(Number);
      }
      return JSON.stringify({
        query: ${JSON.stringify(q)},
        matchedCount,
        matchedIds
      });
    })()`);

    const data = JSON.parse(rawJson || '{}');
    results[q] = data;
    console.log(`Legacy Query: "${q.padEnd(20)}" | Matches: ${data.matchedCount}`);
  }

  // Specifically check RLCraft for MID 255, 413, 1231
  const rlData = results['RLCraft'];
  console.log('\n--- RLCraft Golden Check on Legacy ---');
  console.log('Total RLCraft legacy matches:', rlData.matchedCount);
  for (const mid of [255, 413, 1231]) {
    // Check if table has row for mid
    const hasRow = await page.evaluate(`(() => {
      // search row in full table
      let found = false;
      window.table.rows({ filter: 'applied' }).every(function(rowIdx, tableLoop, rowLoop) {
        const node = this.node();
        const mid = $(node).attr('data-mid') || $(node).data('mid');
        if (Number(mid) === ${mid}) found = true;
      });
      return found;
    })()`);
    console.log(`  MID ${mid} matched in legacy?: ${hasRow}`);
  }

  page.ws.close();
  cdp.cleanup();
  server.close();

  const outPath = path.join(REPO_ROOT, 'build', 'audit', `legacy_search_results_${targetLabel.replace(/[\\/]/g, '_')}.json`);
  fs.writeFileSync(outPath, JSON.stringify({ target: targetLabel, results }, null, 2), 'utf8');
  console.log('[+] Saved legacy search results to', outPath);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const REPO_ROOT = path.resolve(__dirname, '..');
const targetDir = path.join(REPO_ROOT, 'build', 'frontend_preview');
const PORT = 8775;
const CDP_PORT = 9775;
const EDGE_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
};

function createStaticServer(rootDir, port) {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      let reqPath = decodeURIComponent(req.url.split('?')[0]);
      if (reqPath === '/' || reqPath === '') reqPath = '/看板.html';
      const filePath = path.join(rootDir, reqPath);
      if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
        res.writeHead(404);
        res.end('Not found');
        return;
      }
      const ext = path.extname(filePath).toLowerCase();
      res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
      fs.createReadStream(filePath).pipe(res);
    });
    server.listen(port, '127.0.0.1', () => resolve(server));
  });
}

class EdgeCDPClient {
  constructor(port) {
    this.port = port;
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
    throw new Error('Could not connect to Edge CDP');
  }

  async createPage(url) {
    const res = await fetch(`http://127.0.0.1:${this.port}/json/new?${encodeURIComponent(url)}`, { method: 'PUT' });
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
      const evalRes = await sendCDP('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
      return evalRes.result ? evalRes.result.value : undefined;
    };

    return { evaluate };
  }

  cleanup() {
    try { if (this.proc) this.proc.kill('SIGKILL'); } catch (e) {}
    try { fs.rmSync(this.userDataDir, { recursive: true, force: true }); } catch (e) {}
  }
}

async function main() {
  const server = await createStaticServer(targetDir, PORT);
  const cdp = new EdgeCDPClient(CDP_PORT);
  await cdp.start();
  const page = await cdp.createPage(`http://127.0.0.1:${PORT}/看板.html`);

  // Wait for init
  for (let i = 0; i < 50; i++) {
    await new Promise(r => setTimeout(r, 200));
    const ready = await page.evaluate('Boolean(window.mcmodData && window.mcmodData.length > 0)');
    if (ready) break;
  }

  // Switch to bilibili
  await page.evaluate(`switchPlatformTab('bilibili')`);
  for (let i = 0; i < 30; i++) {
    await new Promise(r => setTimeout(r, 200));
    const biliReady = await page.evaluate('Boolean(window.biliModpacksData && window.biliModpacksData.length > 0)');
    if (biliReady) break;
  }

  const result = await page.evaluate(`
    (async () => {
      const rawPacks = window.biliModpacksData || [];
      const q = '机械动力';
      const rawMatches = rawPacks.filter(p => {
        const s = ((p.title || '') + ' ' + (p.author || '') + ' ' + (p.desc || '') + ' ' + (p.mc_version || '') + ' ' + (p.loaders || []).join(' ') + ' ' + (p.categories || []).join(' ')).toLowerCase();
        return s.indexOf(q) !== -1;
      });

      // Type into search box
      $('#biliSearchInput').val('机械动力').trigger('input');
      await new Promise(r => setTimeout(r, 400));

      const groupedCards = document.querySelectorAll('#biliCardsGrid .bili-pack-card').length;
      const groupedModeText = $('#biliCurrentModeText').text();
      const groupsMap = window.biliGroupsMap || {};
      const groupKeys = Object.keys(groupsMap);
      const multiGroups = [];
      for (const k of groupKeys) {
        const g = groupsMap[k];
        if (g && g.items && g.items.length > 1) {
          multiGroups.push({
            key: k,
            count: g.items.length,
            bvids: g.items.map(x => x.bvid)
          });
        }
      }

      // Switch to flat
      $('#biliViewToggle button[data-mode="flat"]').trigger('click');
      await new Promise(r => setTimeout(r, 400));

      const flatCards = document.querySelectorAll('#biliCardsGrid .bili-pack-card, #biliCardsGrid .bili-flat-card').length;
      const flatModeText = $('#biliCurrentModeText').text();

      return {
        totalBili: rawPacks.length,
        rawMatchesCount: rawMatches.length,
        rawBvids: rawMatches.map(x => x.bvid),
        groupedCardsCount: groupedCards,
        groupedModeText: groupedModeText,
        totalGroupKeysCount: groupKeys.length,
        multiGroups: multiGroups,
        flatCardsCount: flatCards,
        flatModeText: flatModeText
      };
    })()
  `);

  console.log('=== Bilibili Investigation Result ===');
  console.log(JSON.stringify(result, null, 2));

  cdp.cleanup();
  server.close();
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});

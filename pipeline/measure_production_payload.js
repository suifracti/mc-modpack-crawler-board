const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const REPO_ROOT = path.resolve(__dirname, '..');
const targetDir = path.join(REPO_ROOT, 'converted_output');
const PORT = 8792;
const CDP_PORT = 9792;
const EDGE_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
};

const server = http.createServer((req, res) => {
  let reqPath = decodeURIComponent(req.url.split('?')[0]);
  if (reqPath === '/' || reqPath === '') reqPath = '/看板.html';
  const filePath = path.join(targetDir, reqPath);
  if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
    res.writeHead(404); res.end(); return;
  }
  const ext = path.extname(filePath).toLowerCase();
  res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
  fs.createReadStream(filePath).pipe(res);
});

server.listen(PORT, async () => {
  const edge = spawn(EDGE_PATH, [
    '--headless=new',
    '--remote-debugging-port=' + CDP_PORT,
    '--disable-gpu',
    '--no-sandbox',
    'http://127.0.0.1:' + PORT + '/看板.html'
  ]);

  await new Promise(r => setTimeout(r, 2500));
  const tabsRes = await fetch('http://127.0.0.1:' + CDP_PORT + '/json');
  const tabs = await tabsRes.json();
  const pageTab = tabs.find(t => t.type === 'page');

  const ws = new WebSocket(pageTab.webSocketDebuggerUrl);
  await new Promise(r => { ws.onopen = r; });

  let msgId = 1;
  function send(method, params = {}) {
    return new Promise(resolve => {
      const id = msgId++;
      const handler = (evt) => {
        const msg = JSON.parse(evt.data);
        if (msg.id === id) {
          ws.removeEventListener('message', handler);
          resolve(msg.result);
        }
      };
      ws.addEventListener('message', handler);
      ws.send(JSON.stringify({ id, method, params }));
    });
  }

  await new Promise(r => setTimeout(r, 3500));

  const perfData = await send('Runtime.evaluate', {
    expression: `(() => {
      const entries = performance.getEntriesByType('resource');
      const mcmodDataEntry = entries.find(r => r.name.includes('mcmod_data.js'));
      const jsEntries = entries.filter(r => r.name.endsWith('.js'));
      const cssEntries = entries.filter(r => r.name.endsWith('.css'));
      const trendsEntries = entries.filter(r => r.name.includes('mcmod_trends.js'));
      return JSON.stringify({
        initialResourceCount: entries.length,
        mcmodDataEncodedBytes: mcmodDataEntry ? (mcmodDataEntry.encodedBodySize || mcmodDataEntry.decodedBodySize || 0) : 0,
        mcmodTrendsRequestCount: trendsEntries.length,
        resources: entries.map(r => ({
          name: r.name.split('/').pop().split('?')[0],
          encodedSize: r.encodedBodySize || 0,
          decodedSize: r.decodedBodySize || 0,
          transferSize: r.transferSize || 0
        }))
      });
    })()`,
    returnByValue: true
  });

  const parsed = JSON.parse(perfData.result.value);

  // File size on disk for key artifacts in converted_output
  const mcmodDataFile = path.join(targetDir, 'data', 'mcmod_data.js');
  const indexJsFile = path.join(targetDir, 'assets', 'index.js');
  const dashboardCssFile = path.join(targetDir, 'assets', 'css', 'dashboard.css');

  const onDiskSizes = {
    'data/mcmod_data.js': fs.existsSync(mcmodDataFile) ? fs.statSync(mcmodDataFile).size : 0,
    'assets/index.js (Vite Bundle)': fs.existsSync(indexJsFile) ? fs.statSync(indexJsFile).size : 0,
    'assets/css/dashboard.css': fs.existsSync(dashboardCssFile) ? fs.statSync(dashboardCssFile).size : 0,
  };

  parsed.onDiskSizes = onDiskSizes;
  console.log(JSON.stringify(parsed, null, 2));

  ws.close();
  edge.kill();
  server.close();
  process.exit(0);
});

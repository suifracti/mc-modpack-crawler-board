const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const PORT = 8765;
const PREVIEW_DIR = path.resolve(__dirname, '..', 'build', 'legacy_preview');

// 1. Static file server
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
  const filePath = path.join(PREVIEW_DIR, reqPath);

  if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
    res.writeHead(404);
    res.end('Not found: ' + reqPath);
    return;
  }

  const ext = path.extname(filePath).toLowerCase();
  res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
  fs.createReadStream(filePath).pipe(res);
});

async function runTest() {
  await new Promise((resolve) => server.listen(PORT, '127.0.0.1', resolve));
  console.log(`[+] Static server listening at http://127.0.0.1:${PORT}`);

  const edgePath = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
  const userDataDir = path.join(__dirname, '..', 'build', '.edge_user_data');
  fs.mkdirSync(userDataDir, { recursive: true });

  const CDP_PORT = 9555;
  const edgeArgs = [
    '--headless=new',
    `--remote-debugging-port=${CDP_PORT}`,
    `--user-data-dir=${userDataDir}`,
    '--disable-gpu',
    '--no-sandbox',
    '--no-first-run',
    '--no-default-browser-check',
    'about:blank'
  ];

  console.log('[+] Spawning headless Edge...');
  const edgeProc = spawn(edgePath, edgeArgs);

  const cleanup = () => {
    try { edgeProc.kill('SIGKILL'); } catch (e) {}
    try { server.close(); } catch (e) {}
  };

  process.on('exit', cleanup);
  process.on('SIGINT', cleanup);

  // Wait for remote debugging to be ready
  let versionData = null;
  for (let i = 0; i < 30; i++) {
    await new Promise(r => setTimeout(r, 200));
    try {
      const res = await fetch(`http://127.0.0.1:${CDP_PORT}/json/version`);
      if (res.ok) {
        versionData = await res.json();
        break;
      }
    } catch (e) {}
  }

  if (!versionData) {
    cleanup();
    throw new Error(`Failed to connect to Edge DevTools port ${CDP_PORT}`);
  }

  console.log('[+] Connected to Edge CDP:', versionData.Browser);

  // Create new target / page
  const targetRes = await fetch(`http://127.0.0.1:${CDP_PORT}/json/new?http://127.0.0.1:` + PORT + '/看板.html', { method: 'PUT' });
  const target = await targetRes.json();
  const wsUrl = target.webSocketDebuggerUrl;

  console.log('[+] Connecting to Page WebSocket:', wsUrl);
  const ws = new WebSocket(wsUrl);

  let msgId = 1;
  const pendingRequests = new Map();
  const consoleMessages = [];
  const pageErrors = [];

  const sendCDP = (method, params = {}) => {
    return new Promise((resolve, reject) => {
      const id = msgId++;
      pendingRequests.set(id, { resolve, reject });
      ws.send(JSON.stringify({ id, method, params }));
    });
  };

  await new Promise((resolve, reject) => {
    ws.onopen = resolve;
    ws.onerror = reject;
  });

  ws.onmessage = (evt) => {
    const data = JSON.parse(evt.data);
    if (data.id && pendingRequests.has(data.id)) {
      const { resolve, reject } = pendingRequests.get(data.id);
      pendingRequests.delete(data.id);
      if (data.error) reject(data.error);
      else resolve(data.result);
    } else if (data.method === 'Runtime.consoleAPICalled') {
      const text = data.params.args.map(a => a.value || a.description || '').join(' ');
      consoleMessages.push({ type: data.params.type, text });
    } else if (data.method === 'Runtime.exceptionThrown') {
      const desc = data.params.exceptionDetails.exception?.description || data.params.exceptionDetails.text;
      pageErrors.push(desc);
      console.error('  [!] Page Exception:', desc);
    }
  };

  // Enable Runtime and Page
  await sendCDP('Runtime.enable');
  await sendCDP('Page.enable');

  console.log('[+] Navigating and waiting for DOMContentLoaded...');
  // Wait up to 10 seconds for initial load
  let pageReady = false;
  for (let i = 0; i < 50; i++) {
    await new Promise(r => setTimeout(r, 200));
    try {
      const evalRes = await sendCDP('Runtime.evaluate', {
        expression: 'Boolean(window.tableRowsData && window.tableRowsData.length > 0)',
        returnByValue: true
      });
      if (evalRes.result && evalRes.result.value === true) {
        pageReady = true;
        break;
      }
    } catch (e) {}
  }

  if (!pageReady) {
    console.error('[-] Page failed to initialize tableRowsData in time');
  } else {
    console.log('[+] Page successfully loaded initial MCMod tableRowsData');
  }

  // Helper evaluate
  const evaluate = async (expr) => {
    const res = await sendCDP('Runtime.evaluate', { expression: expr, returnByValue: true });
    return res.result ? res.result.value : undefined;
  };

  // Run test suite
  const testResults = [];

  // 1. Check Data Variables loaded
  const mcmodCount = await evaluate('window.tableRowsData ? window.tableRowsData.length : 0');
  testResults.push({ name: 'MCMod Rows Loaded', pass: mcmodCount === 1484, details: `Count: ${mcmodCount}` });

  const appDataCount = await evaluate('window.compareData ? Object.keys(window.compareData).length : 0');
  testResults.push({ name: 'AppData Loaded', pass: appDataCount === 1484, details: `Count: ${appDataCount}` });

  const descDataCount = await evaluate('window.descData ? Object.keys(window.descData).length : 0');
  testResults.push({ name: 'DescData Loaded', pass: descDataCount === 1484, details: `Count: ${descDataCount}` });

  // 2. Test Tab Switching
  const platforms = [
    { id: 'bilibili', varName: 'biliModpacksData', expectedCount: 936, cardSelector: '#biliCardsGrid .bili-pack-card' },
    { id: 'bbsmc', varName: 'bbsmcModpacksData', expectedCount: 1802, cardSelector: '#bbsmcCardsGrid .bbsmc-pack-card' },
    { id: 'xyebbs', varName: 'xyebbsModpacksData', expectedCount: 5175, cardSelector: '#xyebbsCardsGrid .xyebbs-pack-card' },
    { id: 'modrinth', varName: 'modrinthModpacksData', expectedCount: 18328, cardSelector: '#modrinthCardsGrid .modrinth-pack-card' },
    { id: 'curseforge', varName: 'curseforgeModpacksData', expectedCount: 45797, cardSelector: '#curseforgeCardsGrid .curseforge-pack-card' }
  ];

  for (const plat of platforms) {
    console.log(`[*] Testing tab switch to: ${plat.id}...`);
    await evaluate(`switchPlatformTab('${plat.id}')`);
    // Wait for async sidecar load
    let count = 0;
    for (let j = 0; j < 40; j++) {
      await new Promise(r => setTimeout(r, 250));
      count = await evaluate(`window.${plat.varName} ? window.${plat.varName}.length : 0`);
      if (count > 0) break;
    }
    await new Promise(r => setTimeout(r, 1000));
    const visibleCards = await evaluate(`document.querySelectorAll('${plat.cardSelector}').length`);
    if (visibleCards === 0) {
      const gridId = plat.cardSelector.split(' ')[0];
      const gridHtml = await evaluate(`document.querySelector('${gridId}') ? document.querySelector('${gridId}').innerHTML.substring(0, 300) : 'NOT FOUND'`);
      console.log(`  [-] Debug grid for ${plat.id} (${gridId}): ${gridHtml}`);
    }
    testResults.push({
      name: `Tab [${plat.id}] Lazy Loaded & Rendered`,
      pass: count === plat.expectedCount && visibleCards > 0,
      details: `Records: ${count}/${plat.expectedCount}, Rendered Cards: ${visibleCards}`
    });
  }

  // 3. Test Mod Detail Sidecar loading
  console.log('[*] Testing mod detail lazy sidecar for mid=1...');
  const modSidecarLoaded = await evaluate(`new Promise(resolve => {
    const s = document.createElement('script');
    s.src = 'data/mods/1.js';
    s.onload = () => resolve(true);
    s.onerror = () => resolve(false);
    document.head.appendChild(s);
  })`);
  testResults.push({ name: 'Mod Detail Sidecar (data/mods/1.js)', pass: Boolean(modSidecarLoaded), details: `HTTP 200 & Executed: ${modSidecarLoaded}` });

  // 4. Test Comments Sidecar loading
  console.log('[*] Testing comments lazy sidecar for mid=1...');
  const commentSidecarLoaded = await evaluate(`new Promise(resolve => {
    const s = document.createElement('script');
    s.src = 'data/comments/1.js';
    s.onload = () => resolve(true);
    s.onerror = () => resolve(false);
    document.head.appendChild(s);
  })`);
  testResults.push({ name: 'Comment Sidecar (data/comments/1.js)', pass: Boolean(commentSidecarLoaded), details: `HTTP 200 & Executed: ${commentSidecarLoaded}` });

  // 5. Test Server Filter
  console.log('[*] Testing server filter toggles...');
  await evaluate(`switchPlatformTab('mcmod')`);
  await evaluate(`$('#serverFilter').val('yes').trigger('change')`);
  await new Promise(r => setTimeout(r, 300));
  const serverFilteredCount = await evaluate(`$('#modpackTable tbody tr').length`);
  testResults.push({
    name: 'Server Filter (MCMod)',
    pass: serverFilteredCount > 0,
    details: `Filtered Visible Rows: ${serverFilteredCount}`
  });

  // Summary
  console.log('\n' + '='.repeat(60));
  console.log('  Browser Smoke Test Summary (Headless Edge)');
  console.log('='.repeat(60));
  let allPass = true;
  for (const t of testResults) {
    const status = t.pass ? '[PASS]' : '[FAIL]';
    if (!t.pass) allPass = false;
    console.log(`  ${status} ${t.name}: ${t.details}`);
  }

  console.log(`\n  Uncaught JS Exceptions: ${pageErrors.length}`);
  if (pageErrors.length > 0) {
    allPass = false;
    pageErrors.forEach(err => console.log(`    - ${err}`));
  }
  console.log('='.repeat(60));
  console.log(`  Final Browser Test Status: ${allPass ? 'ALL TESTS PASSED' : 'SOME TESTS FAILED'}`);
  console.log('='.repeat(60));

  ws.close();
  cleanup();
  process.exit(allPass ? 0 : 1);
}

runTest().catch((err) => {
  console.error('Fatal Test Runner Error:', err);
  process.exit(1);
});

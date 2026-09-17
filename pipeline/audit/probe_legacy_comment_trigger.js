/**
 * Phase 3G-D.1R - Legacy fallback comment-popup trigger probe.
 *
 * `pipeline/smoke_test_single.js` probes the MCMod comment popup through
 * `.comment-cell`, which is a MODERN-only markup hook emitted by
 * `apps/web/src/platforms/mcmod/renderer.ts`. The legacy bundle renders its
 * trigger as `.td-comment` instead, so the shared suite reports 32/33 against
 * the legacy fallback even though the behavior works.
 *
 * This probe proves the legacy popup is functional by clicking the legacy
 * trigger. Expected output:
 *   ".comment-cell"      -> 0 occurrences
 *   ".td-comment"        -> >=1 in the first row
 *   legacy popup         -> opened: true, class "comment-popup show"
 *   uncaught exceptions  -> 0
 *
 * Usage: node pipeline/audit/probe_legacy_comment_trigger.js
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const REPO_ROOT = path.resolve(__dirname, '..', '..');
const targetDir = path.join(REPO_ROOT, 'build', 'frontend_legacy_current_data');
const PORT = 8896;
const CDP_PORT = 9896;
const EDGE_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';

const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'application/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8' };

function createStaticServer(rootDir, port) {
  return new Promise((resolve, reject) => {
    const server = http.createServer((req, res) => {
      let reqPath = decodeURIComponent(req.url.split('?')[0]);
      if (reqPath === '/' || reqPath === '') reqPath = '/看板.html';
      const filePath = path.join(rootDir, reqPath);
      if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) { res.writeHead(404); res.end('nf'); return; }
      res.writeHead(200, { 'Content-Type': MIME[path.extname(filePath).toLowerCase()] || 'application/octet-stream' });
      fs.createReadStream(filePath).pipe(res);
    });
    server.on('error', reject);
    server.listen(port, '127.0.0.1', () => resolve(server));
  });
}

async function main() {
  const server = await createStaticServer(targetDir, PORT);
  const proc = spawn(EDGE_PATH, [
    `--remote-debugging-port=${CDP_PORT}`,
    `--user-data-dir=${path.join(REPO_ROOT, 'build', '.edge_probe_comment')}`,
    '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
    `http://127.0.0.1:${PORT}/`
  ], { stdio: 'ignore' });

  let target = null;
  for (let i = 0; i < 30; i++) {
    try {
      const res = await fetch(`http://127.0.0.1:${CDP_PORT}/json/list`);
      const list = await res.json();
      target = list.find(t => t.type === 'page' && t.webSocketDebuggerUrl);
      if (target) break;
    } catch (e) {}
    await new Promise(r => setTimeout(r, 500));
  }
  if (!target) { console.error('no CDP page target'); process.exit(1); }

  const ws = new WebSocket(target.webSocketDebuggerUrl);
  let msgId = 1;
  const pending = new Map();
  const uncaught = [];
  await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
  ws.onmessage = (evt) => {
    const msg = JSON.parse(evt.data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) reject(new Error(JSON.stringify(msg.error)));
      else resolve(msg.result);
    } else if (msg.method === 'Runtime.exceptionThrown') {
      uncaught.push(msg.params.exceptionDetails.exception?.description || msg.params.exceptionDetails.text);
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
    const r = await sendCDP('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
    if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails).slice(0, 300));
    return r.result.value;
  };

  for (let i = 0; i < 40; i++) {
    if (await evaluate(`Boolean(window.table && document.querySelectorAll('#modpackTable tbody tr').length)`)) break;
    await new Promise(r => setTimeout(r, 500));
  }

  const presence = await evaluate(`(() => {
    const row = document.querySelector('#modpackTable tbody tr');
    const sel = ['.comment-cell', '.td-comment', '.show-comment-btn', '#commentOpen'];
    const out = {};
    for (const s of sel) out[s] = { inRow: row ? row.querySelectorAll(s).length : -1, inDoc: document.querySelectorAll(s).length };
    return { out, hasPopupEl: Boolean(document.querySelector('#commentPopup')) };
  })()`);
  console.log('selector presence:', JSON.stringify(presence, null, 2));

  const res = await evaluate(`new Promise(resolve => {
    const row = document.querySelector('#modpackTable tbody tr');
    const trigger = (row && row.querySelector('.td-comment')) || (row && row.querySelector('.show-comment-btn')) || document.querySelector('.td-comment') || document.querySelector('.show-comment-btn');
    if (!trigger) { resolve({ opened: false, reason: 'no legacy trigger' }); return; }
    trigger.click();
    setTimeout(() => {
      const el = document.querySelector('#commentPopup');
      resolve({ opened: Boolean(el && (el.classList.contains('show') || el.offsetParent !== null)), cls: el ? el.className : null, triggerClass: trigger.className });
    }, 800);
  })`);
  console.log('legacy popup via legacy trigger:', JSON.stringify(res));
  console.log('uncaught JS exceptions:', uncaught.length, uncaught.slice(0, 3));

  ws.close(); proc.kill(); server.close();
  process.exit(0);
}

main().catch(e => { console.error(e); process.exit(1); });

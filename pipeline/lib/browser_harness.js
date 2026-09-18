/**
 * Architecture V2 - Phase 3G-F-B browser harness.
 *
 * Shared process-lifecycle layer for the browser gates (smoke_test_single.js,
 * smoke_test_wiring.js). It exists because the previous gates could leave the
 * machine in exactly the state that made a hang look like a poisoned port:
 *
 *   "port listening, msedge main process = 0, only a stale/crash profile"
 *
 * Three independent defects produced that state:
 *
 * 1. `smoke_test_single.js` called `process.exit()` from inside its `try`
 *    block. Node does NOT unwind the stack for `process.exit()` - the `finally`
 *    block never runs, so `cdpClient.cleanup()` and `server.close()` were both
 *    skipped on every single run. Every run orphaned its Edge process and left
 *    its profile directory behind. (Verified: a `try { process.exit(0) } finally
 *    { ... }` probe never reaches the finally, and not even the `exit` hook runs.)
 *
 * 2. Edge was launched *outside* the try/finally in smoke_test_wiring.js, so a
 *    failed launch leaked the static server and the port stayed LISTENING.
 *
 * 3. Nothing checked whether the CDP port it was about to use was already owned
 *    by a foreign browser. A stale Edge answering on the port made `start()`
 *    "succeed" against a browser this run did not own, after which every
 *    evaluate() waits on a page that will never load.
 *
 * This module fixes all three: unique per-run profiles under
 * build/.edge_cdp/<suite>/<run-id>, a hard ownership guard on the CDP port,
 * whole-process-tree teardown, force-closed static servers, and exit/signal
 * hooks so cleanup runs even when the process is terminated from outside.
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn, spawnSync } = require('child_process');

const REPO_ROOT = path.resolve(__dirname, '..', '..');
const EDGE_PATH = process.env.MC_EDGE_PATH
  || 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
};

const PROFILE_ROOT = path.join(REPO_ROOT, 'build', '.edge_cdp');

let runCounter = 0;

/** Deterministic, collision-free run id: timestamp + pid + counter. */
function makeRunId() {
  runCounter += 1;
  const d = new Date();
  const pad = (n, w = 2) => String(n).padStart(w, '0');
  const ts = `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}`
    + `_${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
  return `${ts}_${process.pid}_${runCounter}`;
}

function profileDirFor(suite, runId) {
  return path.join(PROFILE_ROOT, suite, runId);
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/** Ask the CDP endpoint who it is. Returns null when nothing answers. */
async function probeCdp(port, timeoutMs = 800) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(`http://127.0.0.1:${port}/json/version`, { signal: ctrl.signal });
    if (!res.ok) return null;
    return await res.json();
  } catch (e) {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

/** PIDs listening on a TCP port, via netstat. Windows only, best effort. */
function portOwnerPids(port) {
  try {
    const res = spawnSync('netstat', ['-ano', '-p', 'tcp'], {
      encoding: 'utf8', errors: 'replace', timeout: 20000, windowsHide: true,
    });
    if (!res.stdout) return [];
    const pids = new Set();
    for (const line of res.stdout.split(/\r?\n/)) {
      const parts = line.trim().split(/\s+/);
      if (parts.length < 5) continue;
      const local = parts[1];
      if (!local || !local.endsWith(`:${port}`)) continue;
      if (!/LISTENING/i.test(parts[3])) continue;
      const pid = parseInt(parts[4], 10);
      if (Number.isFinite(pid) && pid > 0) pids.add(pid);
    }
    return [...pids];
  } catch (e) {
    return [];
  }
}

/** Kill a PID and its whole process tree. Synchronous: safe in exit hooks. */
function killTree(pid) {
  if (!pid) return;
  try {
    spawnSync('taskkill', ['/F', '/T', '/PID', String(pid)], {
      encoding: 'utf8', errors: 'replace', timeout: 30000, windowsHide: true,
    });
  } catch (e) { /* best effort */ }
}

/**
 * Create a static file server that can actually be torn down.
 *
 * `server.close()` alone waits for existing keep-alive connections to finish,
 * which is how a "closed" gate can leave its port LISTENING.
 */
function createStaticServer(rootDir, startPort) {
  return new Promise((resolve, reject) => {
    const sockets = new Set();
    let currentPort = startPort;

    function tryListen() {
      const server = http.createServer((req, res) => {
        let reqPath = decodeURIComponent(req.url.split('?')[0]);
        if (reqPath === '/' || reqPath === '') {
          const kanban = path.join(rootDir, '看板.html');
          reqPath = fs.existsSync(kanban) ? '/看板.html' : '/点击打开.html';
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

      server.on('connection', (socket) => {
        sockets.add(socket);
        socket.on('close', () => sockets.delete(socket));
      });
      server.keepAliveTimeout = 1000;

      server.on('error', (err) => {
        if (err.code === 'EADDRINUSE') {
          currentPort++;
          tryListen();
        } else {
          reject(err);
        }
      });

      server.listen(currentPort, '127.0.0.1', () => {
        resolve({
          server,
          port: currentPort,
          close() {
            try {
              if (typeof server.closeAllConnections === 'function') {
                server.closeAllConnections();
              }
              for (const s of sockets) { try { s.destroy(); } catch (e) {} }
              server.close();
            } catch (e) { /* best effort */ }
          },
        });
      });
    }
    tryListen();
  });
}

class EdgeCDPClient {
  /**
   * @param {number} port CDP port
   * @param {object} [opts] { suite, runId, launchTimeoutMs }
   */
  constructor(port, opts = {}) {
    this.port = port;
    this.suite = opts.suite || 'default';
    this.runId = opts.runId || makeRunId();
    this.userDataDir = profileDirFor(this.suite, this.runId);
    this.launchTimeoutMs = opts.launchTimeoutMs || 30000;
    this.proc = null;
    this.pages = [];
    this._cleaned = false;
  }

  async start() {
    // --- Ownership guard -------------------------------------------------
    // Never attach to a browser this run did not start. A stale Edge holding
    // the port makes `fetch(/json/version)` succeed and silently hands us the
    // wrong browser, whose page will never finish loading.
    const foreign = await probeCdp(this.port);
    if (foreign) {
      const pids = portOwnerPids(this.port);
      console.log(`[!] CDP port ${this.port} is already served by a foreign browser `
        + `(${foreign.Browser || 'unknown'}, pid(s) ${pids.join(',') || 'unknown'})`);
      console.log(`[!] Reclaiming the port before launching our own Edge.`);
      for (const pid of pids) killTree(pid);
      await sleep(700);
      const still = await probeCdp(this.port);
      if (still) {
        throw new Error(
          `CDP port ${this.port} is still owned by a foreign browser after cleanup `
          + `(${still.Browser || 'unknown'}). Refusing to attach to a browser this run `
          + `does not own - that is the failure mode that hangs the gate.`);
      }
    }

    fs.mkdirSync(this.userDataDir, { recursive: true });
    const args = [
      '--headless=new',
      `--remote-debugging-port=${this.port}`,
      `--user-data-dir=${this.userDataDir}`,
      '--disable-gpu',
      '--no-sandbox',
      '--no-first-run',
      '--no-default-browser-check',
      '--disable-crash-reporter',
      'about:blank',
    ];
    // stdio 'ignore': an unread stdout/stderr pipe would block Edge once the
    // 64 KB pipe buffer fills, which looks exactly like a dead browser.
    this.proc = spawn(EDGE_PATH, args, { stdio: 'ignore', windowsHide: true });
    this.proc.on('error', (err) => {
      console.error(`[!] Edge failed to spawn: ${err.message}`);
    });

    const deadline = Date.now() + this.launchTimeoutMs;
    while (Date.now() < deadline) {
      await sleep(200);
      if (this.proc.exitCode !== null) {
        throw new Error(
          `Edge exited immediately (code ${this.proc.exitCode}) while launching on `
          + `CDP port ${this.port}. Profile: ${this.userDataDir}`);
      }
      const info = await probeCdp(this.port);
      if (info) {
        console.log(`[+] Edge ${info.Browser || ''} ready on CDP port ${this.port} `
          + `(profile ${path.relative(REPO_ROOT, this.userDataDir)})`);
        return;
      }
    }
    throw new Error(`Could not connect to Edge CDP on port ${this.port} within `
      + `${this.launchTimeoutMs} ms`);
  }

  async createPage(url, opts = {}) {
    const res = await fetch(
      `http://127.0.0.1:${this.port}/json/new?${encodeURIComponent(url)}`,
      { method: 'PUT' });
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
        const desc = msg.params.exceptionDetails.exception?.description
          || msg.params.exceptionDetails.text;
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

    const evalParams = {};
    if (opts.returnByValue) evalParams.returnByValue = true;
    if (opts.awaitPromise) evalParams.awaitPromise = true;

    const evaluate = async (expr) => {
      const evalRes = await sendCDP('Runtime.evaluate',
        { expression: expr, ...evalParams });
      return evalRes.result ? evalRes.result.value : undefined;
    };

    const page = { ws, sendCDP, evaluate, consoleLogs, uncaughtErrors };
    this.pages.push(page);
    return page;
  }

  /** Idempotent, synchronous-safe teardown. */
  cleanup() {
    if (this._cleaned) return;
    this._cleaned = true;
    for (const page of this.pages) {
      try { page.ws.close(); } catch (e) {}
    }
    if (this.proc && this.proc.pid) {
      killTree(this.proc.pid);
    }
    try { fs.rmSync(this.userDataDir, { recursive: true, force: true }); } catch (e) {}
  }
}

/**
 * Install cleanup hooks so a gate killed from outside still tears down its
 * Edge processes, static servers and profile directories.
 */
function installExitHooks({ clients = [], servers = [] } = {}) {
  const teardown = () => {
    for (const s of servers) { try { s.close(); } catch (e) {} }
    for (const c of clients) { try { c.cleanup(); } catch (e) {} }
  };
  process.on('exit', teardown);
  for (const sig of ['SIGINT', 'SIGTERM', 'SIGHUP']) {
    process.on(sig, () => { teardown(); process.exit(130); });
  }
  process.on('uncaughtException', (err) => {
    console.error('Uncaught exception:', err);
    teardown();
    process.exit(1);
  });
  process.on('unhandledRejection', (err) => {
    console.error('Unhandled rejection:', err);
    teardown();
    process.exit(1);
  });
  return teardown;
}

module.exports = {
  REPO_ROOT,
  EDGE_PATH,
  PROFILE_ROOT,
  MIME,
  makeRunId,
  profileDirFor,
  probeCdp,
  portOwnerPids,
  killTree,
  createStaticServer,
  EdgeCDPClient,
  installExitHooks,
};

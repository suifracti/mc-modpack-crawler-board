const { spawn } = require('node:child_process');
const { redactLogLine } = require('./platforms.cjs');

function killProcessTree(child) {
  if (!child || !child.pid) return;
  if (process.platform === 'win32') {
    spawn('taskkill', ['/pid', String(child.pid), '/t', '/f'], { windowsHide: true, stdio: 'ignore' });
  } else {
    try { process.kill(-child.pid, 'SIGTERM'); } catch { try { child.kill('SIGTERM'); } catch { /* already gone */ } }
  }
}

function createProcessRunner({ command, args, cwd, env, onLine }) {
  const child = spawn(command, args, {
    cwd,
    env: { ...process.env, ...env },
    windowsHide: true,
    detached: process.platform !== 'win32',
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  let buffer = '';
  const handle = (chunk) => {
    buffer += chunk.toString('utf8');
    const lines = buffer.split(/\r?\n/);
    buffer = lines.pop() || '';
    for (const line of lines) {
      if (line.trim()) onLine(redactLogLine(line));
    }
  };
  child.stdout.on('data', handle);
  child.stderr.on('data', handle);
  const promise = new Promise((resolve, reject) => {
    child.once('error', reject);
    child.once('close', (code, signal) => {
      if (buffer.trim()) onLine(redactLogLine(buffer));
      resolve({ code: code ?? 1, signal: signal || null });
    });
  });
  return { child, promise, cancel: () => killProcessTree(child) };
}

module.exports = { createProcessRunner, killProcessTree };

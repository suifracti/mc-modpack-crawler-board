const { spawn } = require('node:child_process');
const { StringDecoder } = require('node:string_decoder');
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
    env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1', PYTHONUNBUFFERED: '1', ...env },
    windowsHide: true,
    detached: process.platform !== 'win32',
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  const streams = [child.stdout, child.stderr].map((stream) => {
    const decoder = new StringDecoder('utf8');
    let buffer = '';
    stream.on('data', (chunk) => {
      buffer += decoder.write(chunk);
      const lines = buffer.split(/\r?\n/);
      buffer = lines.pop() || '';
      for (const line of lines) if (line.trim()) onLine(redactLogLine(line));
    });
    return () => {
      buffer += decoder.end();
      if (buffer.trim()) onLine(redactLogLine(buffer));
    };
  });
  const promise = new Promise((resolve, reject) => {
    child.once('error', reject);
    child.once('close', (code, signal) => {
      streams.forEach((flush) => flush());
      resolve({ code: code ?? 1, signal: signal || null });
    });
  });
  return { child, promise, cancel: () => killProcessTree(child) };
}

module.exports = { createProcessRunner, killProcessTree };

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const { createBrowserService } = require('../server.cjs');

async function tempDir() {
  return fs.mkdtemp(path.join(os.tmpdir(), 'mcmod-browser-service-'));
}

function request(url, options = {}) {
  return new Promise((resolve, reject) => {
    const requestUrl = new URL(url);
    const request = http.request({
      hostname: requestUrl.hostname,
      port: requestUrl.port,
      path: `${requestUrl.pathname}${requestUrl.search}`,
      method: options.method || 'GET',
      headers: { ...(options.body ? { 'content-type': 'application/json' } : {}), ...(options.headers || {}) },
    }, (response) => {
      const chunks = [];
      response.on('data', (chunk) => chunks.push(chunk));
      response.on('end', () => resolve({ status: response.statusCode, headers: response.headers, body: Buffer.concat(chunks).toString('utf8') }));
    });
    request.on('error', reject);
    if (options.body) request.write(JSON.stringify(options.body));
    request.end();
  });
}

test('serves same-origin health, state and imported records over HTTP', async () => {
  const root = await tempDir();
  const source = path.join(root, 'source', 'data');
  await fs.mkdir(source, { recursive: true });
  await fs.writeFile(path.join(source, 'bili_data.js'), 'window.biliModpacksData = [{"bvid":"BV-browser","title":"浏览器服务测试包","url":"https://example.com/browser"}];\n', 'utf8');

  const service = createBrowserService({ host: '127.0.0.1', port: 0, dataRoot: path.join(root, 'user-data') });
  const started = await service.start();
  try {
    const health = await request(`${started.url}api/health`);
    assert.equal(health.status, 200);
    assert.deepEqual(JSON.parse(health.body), { ok: true, service: 'mc-modpack-board-browser' });

    const emptyState = await request(`${started.url}api/state`);
    assert.equal(emptyState.status, 200);
    assert.equal(JSON.parse(emptyState.body).data.hasData, false);

    const imported = await request(`${started.url}api/data/import`, { method: 'POST', body: { path: path.join(root, 'source') } });
    assert.equal(imported.status, 200);
    assert.equal(JSON.parse(imported.body).data.hasData, true);

    const records = await request(`${started.url}api/platforms/bilibili/records?query=${encodeURIComponent('浏览器服务')}`);
    assert.equal(records.status, 200);
    const payload = JSON.parse(records.body);
    assert.equal(payload.total, 1);
    assert.equal(payload.records[0].title, '浏览器服务测试包');
  } finally {
    await service.stop();
  }
});

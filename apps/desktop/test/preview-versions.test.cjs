const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const { getPreviewVersions } = require('../lib/preview-versions.cjs');
const { createBrowserService } = require('../server.cjs');

function request(url) {
  return new Promise((resolve, reject) => {
    const requestUrl = new URL(url);
    const req = http.request({
      hostname: requestUrl.hostname,
      port: requestUrl.port,
      path: `${requestUrl.pathname}${requestUrl.search}`,
      method: 'GET',
    }, (response) => {
      const chunks = [];
      response.on('data', (chunk) => chunks.push(chunk));
      response.on('end', () => resolve({ status: response.statusCode, body: Buffer.concat(chunks).toString('utf8') }));
    });
    req.on('error', reject);
    req.end();
  });
}

test('getPreviewVersions validates platform and sourceId', async () => {
  await assert.rejects(() => getPreviewVersions('unsupported', '123'), /该来源不支持在线版本读取/);
  await assert.rejects(() => getPreviewVersions('curseforge', 'invalid/id'), /该来源不支持在线版本读取/);
  await assert.rejects(() => getPreviewVersions('curseforge', 'notanumber'), /CurseForge 项目编号无效/);
});

test('server routes /api/preview-versions for curseforge', async () => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'mcmod-preview-test-'));
  const dataRoot = path.join(root, 'data');
  await fs.mkdir(dataRoot, { recursive: true });
  const service = createBrowserService({ host: '127.0.0.1', port: 0, dataRoot });
  const started = await service.start();
  try {
    // Non-numeric curseforge id fails with 400 error from handler, confirming route matches
    const res = await request(`${started.url}api/preview-versions/curseforge/invalid_id`);
    assert.equal(res.status, 400);
    const json = JSON.parse(res.body);
    assert.match(json.error, /CurseForge 项目编号无效/);
  } finally {
    await service.stop();
    await fs.rm(root, { recursive: true, force: true });
  }
});

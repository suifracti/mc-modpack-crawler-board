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

  const dataRoot = path.join(root, 'user-data');
  let service = createBrowserService({ host: '127.0.0.1', port: 0, dataRoot });
  let started = await service.start();
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

    const initialLibrary = await request(`${started.url}api/library`);
    assert.equal(initialLibrary.status, 200);
    assert.deepEqual(JSON.parse(initialLibrary.body).entries, {});

    const saved = await request(`${started.url}api/library/bilibili/BV-browser`, {
      method: 'PATCH',
      body: { favorite: true, wantToPlay: true, played: true, rating: 4, note: '先测试备注' },
    });
    assert.equal(saved.status, 200);
    assert.equal(JSON.parse(saved.body).status.rating, 4);

    const personalRecords = await request(`${started.url}api/platforms/bilibili/records?personalStatus=favorite`);
    assert.equal(personalRecords.status, 200);
    assert.equal(JSON.parse(personalRecords.body).total, 1);

    const nextSource = path.join(root, 'source-next', 'data');
    await fs.mkdir(nextSource, { recursive: true });
    await fs.writeFile(path.join(nextSource, 'bili_data.js'), 'window.biliModpacksData = [{"bvid":"BV-browser","title":"浏览器服务测试包（新快照）","url":"https://example.com/browser"}];\n', 'utf8');
    const switched = await request(`${started.url}api/data/import`, { method: 'POST', body: { path: path.join(root, 'source-next') } });
    assert.equal(switched.status, 200);
    const switchedRecords = await request(`${started.url}api/platforms/bilibili/records?personalStatus=favorite`);
    assert.equal(switchedRecords.status, 200);
    assert.equal(JSON.parse(switchedRecords.body).records[0].title, '浏览器服务测试包（新快照）');

    await service.stop();
    service = createBrowserService({ host: '127.0.0.1', port: 0, dataRoot });
    started = await service.start();
    const restartedLibrary = await request(`${started.url}api/library`);
    const restartedStatus = JSON.parse(restartedLibrary.body).entries['bilibili:BV-browser'];
    assert.equal(restartedStatus.wantToPlay, true);
    assert.equal(restartedStatus.played, true);
    assert.equal(restartedStatus.note, '先测试备注');

    const edited = await request(`${started.url}api/library/bilibili/BV-browser`, {
      method: 'PATCH',
      body: { favorite: false, note: '已修改备注' },
    });
    assert.equal(edited.status, 200);
    const editedStatus = JSON.parse(edited.body).status;
    assert.equal(editedStatus.favorite, false);
    assert.equal(editedStatus.note, '已修改备注');
  } finally {
    await service.stop();
  }
});

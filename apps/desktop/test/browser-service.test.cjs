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

test('personal backup migrates on write, preserves missing sources and restores atomically without overwriting', async () => {
  const root = await tempDir();
  const dataRoot = path.join(root, 'old');
  await fs.mkdir(dataRoot);
  const old = { favorite: true, wantToPlay: true, played: true, rating: 4, note: '旧备注', updatedAt: null };
  const file = path.join(dataRoot, 'personal-library.json');
  await fs.writeFile(file, JSON.stringify({ schema: 1, entries: { 'mcmod:123': old } }));
  let service = createBrowserService({ host: '127.0.0.1', port: 0, dataRoot });
  let started = await service.start();
  const api = async (route, body, method = 'POST') => {
    const response = await request(`${started.url}api/${route}`, body === undefined ? {} : { method, body });
    return { status: response.status, data: JSON.parse(response.body) };
  };
  try {
    assert.deepEqual((await api('library')).data.entries['mcmod:123'], old);
    assert.equal(JSON.parse(await fs.readFile(file, 'utf8')).schema, 1);
    assert.deepEqual((await api('library/missing')).data.entries['mcmod:123'], old);
    await api('library/mcmod/123', { note: '旧备注更新' }, 'PATCH');
    assert.equal(JSON.parse(await fs.readFile(file, 'utf8')).schema, 2);
    const source = path.join(root, 'source', 'data');
    await fs.mkdir(source, { recursive: true });
    await fs.writeFile(path.join(source, 'bili_data.js'), 'window.biliModpacksData = [{"bvid":"BV-A","title":"历史标题 A","url":"https://example.com/A"}];');
    await api('data/import', { path: path.dirname(source) });
    assert.equal((await api('library/bilibili/BV-A', { favorite: true }, 'PATCH')).status, 200);
    await api('library/bilibili/BV-A', { rating: 5, note: 'A 备注' }, 'PATCH');
    const saved = JSON.parse(await fs.readFile(file, 'utf8')).entries['bilibili:BV-A'];
    assert.deepEqual(saved.reference, { title: '历史标题 A', sourceUrl: 'https://example.com/A', objectType: 'bilibili-video' });
    assert.equal(saved.rating, 5);
    const next = path.join(root, 'next', 'data');
    await fs.mkdir(next, { recursive: true });
    await fs.writeFile(path.join(next, 'bili_data.js'), 'window.biliModpacksData = [{"bvid":"BV-B","title":"B"}];');
    await api('data/import', { path: path.dirname(next) });
    assert.deepEqual((await api('library/missing')).data.entries['bilibili:BV-A'], saved);
    const beforeExport = await fs.readFile(file, 'utf8');
    const backup = (await api('library/export')).data;
    assert.deepEqual(Object.keys(backup).sort(), ['entries', 'schema']);
    assert.equal(backup.schema, 2);
    assert.deepEqual(backup.entries['bilibili:BV-A'], saved);
    assert.equal(await fs.readFile(file, 'utf8'), beforeExport);
    await service.stop();
    const fresh = path.join(root, 'fresh');
    service = createBrowserService({ host: '127.0.0.1', port: 0, dataRoot: fresh });
    started = await service.start();
    assert.deepEqual((await api('library/restore', backup)).data, { restored: 2, 'skipped-conflict': 0, invalid: 0 });
    await api('library/bilibili/BV-A', { note: '当前值保留' }, 'PATCH');
    assert.deepEqual((await api('library/restore', backup)).data, { restored: 0, 'skipped-conflict': 2, invalid: 0 });
    const freshFile = path.join(fresh, 'personal-library.json');
    const preserved = await fs.readFile(freshFile, 'utf8');
    const invalidBackups = [
      { ...backup, schema: 99 },
      { schema: 2, entries: { 'bad:123': old } },
      ...[{ rating: 6 }, { rating: '5' }, { note: 'x'.repeat(20001) }, { reference: { objectType: 'bilibili-video', sourceUrl: 'javascript:alert(1)' } }, { reference: { objectType: 'bilibili-video', title: 42 } }, { favorite: 'yes' }, { unexpected: true }].map((patch) => ({ schema: 2, entries: { 'mcmod:456': old, 'bilibili:invalid': { ...saved, ...patch } } })),
    ];
    for (const bad of invalidBackups) {
      const result = await api('library/restore', bad);
      assert.equal(result.status, 400);
      assert.equal(result.data.invalid, 1);
      assert.equal(result.data.restored, 0);
      assert.equal(await fs.readFile(freshFile, 'utf8'), preserved);
      assert.equal((await api('library')).data.entries['mcmod:456'], undefined);
    }
    await service.stop();
    service = createBrowserService({ host: '127.0.0.1', port: 0, dataRoot: fresh });
    started = await service.start();
    const restored = (await api('library/missing')).data.entries;
    assert.equal(restored['bilibili:BV-A'].note, '当前值保留');
    assert.deepEqual(restored['bilibili:BV-A'].reference, saved.reference);
    assert.equal(restored['mcmod:123'].played, true);
  } finally { await service.stop(); }
});

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

    const reminders = await request(`${started.url}api/favorite-updates`);
    assert.equal(reminders.status, 200);
    const reminderSummary = JSON.parse(reminders.body);
    assert.equal(reminderSummary.unreadCount, 0);
    assert.ok(reminderSummary.unknown.some((item) => item.key === 'bilibili:BV-browser'));

    const personalRecords = await request(`${started.url}api/platforms/bilibili/records?personalStatus=favorite`);
    assert.equal(personalRecords.status, 200);
    assert.equal(JSON.parse(personalRecords.body).total, 1);

    const nextSource = path.join(root, 'source-next', 'data');
    await fs.mkdir(nextSource, { recursive: true });
    await fs.writeFile(path.join(nextSource, 'bili_data.js'), 'window.biliModpacksData = [{"bvid":"BV-browser","title":"浏览器服务测试包（新快照）","url":"https://example.com/browser"},{"bvid":"BV-browser-new","title":"浏览器服务测试包 2.0","author":"测试作者","url":"https://example.com/browser-new"}];\n', 'utf8');
    const switched = await request(`${started.url}api/data/import`, { method: 'POST', body: { path: path.join(root, 'source-next') } });
    assert.equal(switched.status, 200);
    const allNextRecords = await request(`${started.url}api/platforms/bilibili/records`);
    assert.equal(JSON.parse(allNextRecords.body).total, 2);
    const switchedRecords = await request(`${started.url}api/platforms/bilibili/records?personalStatus=favorite`);
    assert.equal(switchedRecords.status, 200);
    const switchedPayload = JSON.parse(switchedRecords.body);
    assert.equal(switchedPayload.total, 1);
    assert.equal(switchedPayload.records[0].sourceId, 'BV-browser');
    assert.equal(switchedPayload.records[0].title, '浏览器服务测试包（新快照）');

    const savedNewVideo = await request(`${started.url}api/library/bilibili/BV-browser-new`, {
      method: 'PATCH',
      body: { favorite: true },
    });
    assert.equal(savedNewVideo.status, 200);
    const cancelledNewVideo = await request(`${started.url}api/library/bilibili/BV-browser-new`, {
      method: 'PATCH',
      body: { favorite: false },
    });
    assert.equal(cancelledNewVideo.status, 200);
    const afterNewVideoCancel = JSON.parse((await request(`${started.url}api/library`)).body).entries;
    assert.equal(afterNewVideoCancel['bilibili:BV-browser'].favorite, true);
    assert.equal(afterNewVideoCancel['bilibili:BV-browser-new'], undefined);

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

test('does not persist index fallback identities and accepts a numeric source ID', async () => {
  const root = await tempDir();
  const fallbackSource = path.join(root, 'fallback-source', 'data');
  await fs.mkdir(fallbackSource, { recursive: true });
  await fs.writeFile(path.join(fallbackSource, 'bili_data.js'), 'window.biliModpacksData = [{"title":"没有稳定来源 ID","url":"https://example.com/fallback"}];\n', 'utf8');

  const dataRoot = path.join(root, 'user-data');
  const service = createBrowserService({ host: '127.0.0.1', port: 0, dataRoot });
  const started = await service.start();
  try {
    const imported = await request(`${started.url}api/data/import`, { method: 'POST', body: { path: path.join(root, 'fallback-source') } });
    assert.equal(imported.status, 200);
    const fallbackRecords = JSON.parse((await request(`${started.url}api/platforms/bilibili/records`)).body);
    assert.equal(fallbackRecords.records[0].sourceId, 'bilibili-1');
    assert.equal(fallbackRecords.records[0].sourceIdOrigin, 'index-fallback');

    const rejected = await request(`${started.url}api/library/bilibili/bilibili-1`, {
      method: 'PATCH',
      body: { favorite: true },
    });
    assert.equal(rejected.status, 400);
    assert.match(rejected.body, /数组序号生成/);
    assert.deepEqual(JSON.parse((await request(`${started.url}api/library`)).body).entries, {});

    const numericSource = path.join(root, 'numeric-source', 'data');
    await fs.mkdir(numericSource, { recursive: true });
    await fs.writeFile(path.join(numericSource, 'bili_data.js'), 'window.biliModpacksData = [{"bvid":123,"title":"合法数字来源 ID","url":"https://example.com/numeric"}];\n', 'utf8');
    const switched = await request(`${started.url}api/data/import`, { method: 'POST', body: { path: path.join(root, 'numeric-source') } });
    assert.equal(switched.status, 200);
    const numericRecords = JSON.parse((await request(`${started.url}api/platforms/bilibili/records`)).body);
    assert.equal(numericRecords.records[0].sourceId, '123');
    assert.equal(numericRecords.records[0].sourceIdOrigin, 'source');
    const savedNumeric = await request(`${started.url}api/library/bilibili/123`, {
      method: 'PATCH',
      body: { favorite: true },
    });
    assert.equal(savedNumeric.status, 200);
    assert.equal(JSON.parse((await request(`${started.url}api/library`)).body).entries['bilibili:123'].favorite, true);
  } finally {
    await service.stop();
  }
});

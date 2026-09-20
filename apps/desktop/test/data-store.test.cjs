const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { DataStore } = require('../lib/data-store.cjs');

async function tempDir() {
  return fs.mkdtemp(path.join(os.tmpdir(), 'mcmod-desktop-store-'));
}

async function writeSidecar(dir, name, value, globalName) {
  await fs.mkdir(dir, { recursive: true });
  await fs.writeFile(path.join(dir, name), `window.${globalName} = ${JSON.stringify(value)};\n`, 'utf8');
}

test('imports a local data folder and reports platform counts without executing JavaScript', async () => {
  const root = await tempDir();
  const source = path.join(root, 'source', 'data');
  await writeSidecar(source, 'bili_data.js', [{ bvid: 'BV1', title: '测试整合包', author: '作者', url: 'https://example.com/p' }], 'biliModpacksData');
  const store = new DataStore(path.join(root, 'user-data'));
  await store.init();
  const state = await store.importDirectory(path.join(root, 'source'));
  assert.equal(state.hasData, true);
  assert.equal(state.platforms.bilibili.count, 1);
  const records = await store.getPlatformRecords('bilibili', '测试');
  assert.equal(records.total, 1);
  assert.equal(records.records[0].title, '测试整合包');
});

test('failed validation does not replace the active snapshot', async () => {
  const root = await tempDir();
  const source = path.join(root, 'source', 'data');
  await writeSidecar(source, 'bili_data.js', [{ bvid: 'BV1', title: '旧快照' }], 'biliModpacksData');
  const store = new DataStore(path.join(root, 'user-data'));
  await store.init();
  await store.importDirectory(path.join(root, 'source'));
  const prepared = await store.prepareUpdateWorkspace('bilibili');
  await fs.writeFile(path.join(prepared.workspace, 'converted_output', 'data', 'bili_data.js'), 'window.biliModpacksData = [];\n', 'utf8');
  await assert.rejects(() => store.validateStage(prepared.workspace, 'bilibili'), /更新结果为空/);
  await store.cleanupWorkspace(prepared.workspace);
  const records = await store.getPlatformRecords('bilibili');
  assert.equal(records.records[0].title, '旧快照');
});

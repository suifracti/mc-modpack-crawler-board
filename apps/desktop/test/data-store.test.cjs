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
  await assert.rejects(() => store.validateStage(prepared.workspace, 'bilibili'), /本轮采集结果合同/);
  await store.cleanupWorkspace(prepared.workspace);
  const records = await store.getPlatformRecords('bilibili');
  assert.equal(records.records[0].title, '旧快照');
});

test('filters the complete dataset before pagination and preserves modern fields', async () => {
  const root = await tempDir();
  const source = path.join(root, 'source', 'data');
  const mcmod = [{
    mid: 1,
    title: 'MC百科测试包',
    author: '测试作者',
    url: 'https://www.mcmod.cn/modpack/1.html',
    mcVersions: ['1.7.10'],
    loaders: ['Forge'],
    includedModNames: ['Fixture Mod'],
    englishName: 'Desktop Fixture',
    formerTitles: ['旧测试包'],
    environmentClaims: [{ side: 'server', status: 'unknown', certainty: 'unknown', evidenceText: null }],
  }];
  const bili = Array.from({ length: 301 }, (_, index) => ({
    bvid: `BV${index}`,
    title: index === 300 ? '第301条唯一版本' : `测试视频${index}`,
    author: '测试作者',
    url: `https://www.bilibili.com/video/BV${index}`,
    desc: index === 300 ? '正文描述也可搜索' : '',
    pub_time: '2026-09-20 12:00',
    all_versions: index === 300 ? ['9.9.9'] : ['1.20.1'],
  }));
  await writeSidecar(source, 'mcmod_data.js', mcmod, 'mcmodData');
  await fs.mkdir(path.join(source, 'comments'), { recursive: true });
  await fs.writeFile(path.join(source, 'comments', '1.js'), 'window.__registerCommentData("1",' + JSON.stringify({ page_count: 2, comments: [{ author: "玩家", text: "独立评论正文" }] }) + ');\n', 'utf8');
  await writeSidecar(source, 'bili_data.js', bili, 'biliModpacksData');
  const store = new DataStore(path.join(root, 'user-data'));
  await store.init();
  await store.importDirectory(path.join(root, 'source'));

  const firstPage = await store.getPlatformRecords('bilibili', { page: 1, pageSize: 300 });
  assert.equal(firstPage.total, 301);
  assert.equal(firstPage.records.length, 300);
  assert.ok(firstPage.availableVersions.includes('9.9.9'));
  const secondPage = await store.getPlatformRecords('bilibili', { page: 2, pageSize: 300 });
  assert.equal(secondPage.records.length, 1);
  assert.equal(secondPage.records[0].title, '第301条唯一版本');
  const filtered = await store.getPlatformRecords('bilibili', { version: '9.9.9', page: 1, pageSize: 48 });
  assert.equal(filtered.total, 1);
  assert.equal(filtered.records[0].summary, '正文描述也可搜索');
  assert.equal(filtered.records[0].updatedAt, '2026-09-20 12:00');
  const descriptionSearch = await store.getPlatformRecords('bilibili', { query: '正文 描述', page: 1, pageSize: 48 });
  assert.equal(descriptionSearch.total, 1);

  const mcmodRecords = await store.getPlatformRecords('mcmod', { page: 1, pageSize: 48 });
  assert.deepEqual(mcmodRecords.records[0].versions, ['1.7.10']);
  assert.equal(mcmodRecords.records[0].raw.mid, 1);
  const mcmodSearch = await store.getPlatformRecords('mcmod', { query: '旧测试包 Fixture Mod', page: 1, pageSize: 48 });
  assert.equal(mcmodSearch.total, 1);
  const comments = await store.getPlatformComments('mcmod', '1');
  assert.equal(comments.available, true);
  assert.equal(comments.pageCount, 2);
  assert.equal(comments.comments[0].text, '独立评论正文');
});

test('server filter uses structured runtime evidence and excludes unknown dates', async () => {
  const root = await tempDir();
  const source = path.join(root, 'source', 'data');
  const recent = new Date(Date.now() - 2 * 86_400_000).toISOString();
  const thirtyOneDaysAgo = new Date(Date.now() - 31 * 86_400_000).toISOString();
  const ninetyOneDaysAgo = new Date(Date.now() - 91 * 86_400_000).toISOString();
  const old = new Date(Date.now() - 120 * 86_400_000).toISOString();
  const serverClaim = (status) => ({ side: 'server', status, certainty: 'confirmed', evidenceText: `fixture:${status}`, sourceField: 'fixture', rawValue: status });
  const records = [
    { bvid: 'BV-required', title: 'required', pub_time: recent, environmentClaims: [serverClaim('required')] },
    { bvid: 'BV-optional', title: 'optional', pub_time: recent, environmentClaims: [serverClaim('optional')] },
    { bvid: 'BV-supported', title: 'supported', pub_time: recent, environmentClaims: [serverClaim('supported')] },
    { bvid: 'BV-unsupported', title: 'unsupported', pub_time: recent, has_server: true, environmentClaims: [serverClaim('unsupported')] },
    { bvid: 'BV-unknown', title: 'unknown', pub_time: recent, has_server: true, environmentClaims: [serverClaim('unknown')] },
    { bvid: 'BV-legacy', title: 'legacy', pub_time: recent, has_server: true },
    { bvid: 'BV-31d', title: '31 days', pub_time: thirtyOneDaysAgo },
    { bvid: 'BV-91d', title: '91 days', pub_time: ninetyOneDaysAgo },
    { bvid: 'BV-old', title: 'old', pub_time: old },
    { bvid: 'BV-no-date', title: 'no date', created_timestamp: Math.floor(Date.now() / 1000) },
  ];
  await writeSidecar(source, 'bili_data.js', records, 'biliModpacksData');
  const store = new DataStore(path.join(root, 'user-data'));
  await store.init();
  await store.importDirectory(path.join(root, 'source'));

  const serverOnly = await store.getPlatformRecords('bilibili', { serverOnly: true, page: 1, pageSize: 20 });
  assert.deepEqual(serverOnly.records.map((record) => record.sourceId).sort(), ['BV-legacy', 'BV-optional', 'BV-required', 'BV-supported']);
  assert.equal(serverOnly.records.find((record) => record.sourceId === 'BV-unsupported'), undefined);
  assert.equal(serverOnly.records.find((record) => record.sourceId === 'BV-unknown'), undefined);

  const allRecords = await store.getPlatformRecords('bilibili', { page: 1, pageSize: 20 });
  assert.equal(allRecords.records.find((record) => record.sourceId === 'BV-no-date')?.updatedAt, '');

  const recentOnly = await store.getPlatformRecords('bilibili', { dateRange: '7d', page: 1, pageSize: 20 });
  assert.equal(recentOnly.records.some((record) => record.sourceId === 'BV-no-date'), false);
  assert.equal(recentOnly.records.some((record) => record.sourceId === 'BV-old'), false);
  assert.equal(recentOnly.records.some((record) => record.sourceId === 'BV-required'), true);

  const thirtyDayOnly = await store.getPlatformRecords('bilibili', { dateRange: '30d', page: 1, pageSize: 20 });
  assert.equal(thirtyDayOnly.records.some((record) => record.sourceId === 'BV-31d'), false);
  assert.equal(thirtyDayOnly.records.some((record) => record.sourceId === 'BV-required'), true);
  const ninetyDayOnly = await store.getPlatformRecords('bilibili', { dateRange: '90d', page: 1, pageSize: 20 });
  assert.equal(ninetyDayOnly.records.some((record) => record.sourceId === 'BV-31d'), true);
  assert.equal(ninetyDayOnly.records.some((record) => record.sourceId === 'BV-91d'), false);
});

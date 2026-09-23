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

test('applies restored MC百科 mod and CurseForge gameplay filters before pagination', async () => {
  const root = await tempDir();
  const source = path.join(root, 'source', 'data');
  const mcmod = [
    { mid: 1, title: 'MC AB', loaders: ['Forge'], mcVersions: ['1.20.1'], includedModNames: ['Mod A', 'Mod B'] },
    { mid: 2, title: 'MC A', loaders: ['Fabric'], mcVersions: ['1.20.1'], includedModNames: ['Mod A'] },
    { mid: 3, title: 'MC B', loaders: ['Forge'], mcVersions: ['1.19.2'], includedModNames: ['Mod B'] },
    { mid: 4, title: 'MC neither', loaders: ['Forge'], mcVersions: ['1.20.1'], includedModNames: ['Mod C'] },
    { mid: 5, title: 'MC unknown', loaders: ['Forge'], mcVersions: ['1.20.1'] },
  ];
  const curseforge = [
    { project_id: 11, title: 'CF AB', loaders: ['Forge'], categories: ['Category A', 'Category B'] },
    { project_id: 12, title: 'CF A', loaders: ['Fabric'], categories: ['Category A'] },
    { project_id: 13, title: 'CF B', loaders: ['Forge'], categories: ['Category B'] },
    { project_id: 14, title: 'CF neither', loaders: ['Forge'], categories: ['Category C'] },
    { project_id: 15, title: 'CF unknown', loaders: ['Forge'] },
  ];
  await writeSidecar(source, 'mcmod_data.js', mcmod, 'mcmodData');
  await writeSidecar(source, 'curseforge_data.js', curseforge, 'curseforgeModpacksData');
  const store = new DataStore(path.join(root, 'user-data'));
  await store.init();
  await store.importDirectory(path.join(root, 'source'));

  const mcmodEmpty = await store.getPlatformRecords('mcmod', { includedMods: [], page: 1, pageSize: 2 });
  assert.equal(mcmodEmpty.total, 5);
  const mcmodAnd = await store.getPlatformRecords('mcmod', { includedMods: ['Mod A', 'Mod B'], page: 1, pageSize: 1 });
  assert.equal(mcmodAnd.total, 1);
  assert.deepEqual(mcmodAnd.records.map((record) => record.sourceId), ['1']);
  const mcmodExcludeCombination = await store.getPlatformRecords('mcmod', { includedMods: ['mod a', 'MOD B'], includedModsExclude: true, page: 1, pageSize: 10 });
  assert.equal(mcmodExcludeCombination.total, 4);
  assert.deepEqual(mcmodExcludeCombination.records.map((record) => record.sourceId), ['2', '3', '4', '5']);
  const mcmodCombined = await store.getPlatformRecords('mcmod', { includedMods: ['Mod A'], loader: 'Forge', page: 1, pageSize: 10 });
  assert.equal(mcmodCombined.total, 1);
  assert.deepEqual(mcmodCombined.records.map((record) => record.sourceId), ['1']);
  const mcmodSecondPage = await store.getPlatformRecords('mcmod', { includedMods: ['Mod A'], page: 2, pageSize: 1 });
  assert.equal(mcmodSecondPage.total, 2);
  assert.deepEqual(mcmodSecondPage.records.map((record) => record.sourceId), ['2']);
  assert.deepEqual(Object.fromEntries(mcmodAnd.availableIncludedMods.map((option) => [option.value, option.count])), { 'Mod A': 2, 'Mod B': 2, 'Mod C': 1 });
  const mcmodSearched = await store.getPlatformRecords('mcmod', { query: 'neither', page: 1, pageSize: 1 });
  assert.equal(mcmodSearched.total, 1);
  assert.equal(mcmodSearched.availableIncludedMods.some((option) => option.value === 'Mod A' && option.count === 2), true);

  const cfEmpty = await store.getPlatformRecords('curseforge', { gameplayCategories: [], page: 1, pageSize: 2 });
  assert.equal(cfEmpty.total, 5);
  const cfOr = await store.getPlatformRecords('curseforge', { gameplayCategories: ['Category A', 'Category B'], page: 1, pageSize: 2 });
  assert.equal(cfOr.total, 3);
  assert.deepEqual(cfOr.records.map((record) => record.sourceId), ['11', '12']);
  const cfExcludeAny = await store.getPlatformRecords('curseforge', { gameplayCategories: ['Category A', 'Category B'], gameplayCategoriesExclude: true, page: 1, pageSize: 10 });
  assert.equal(cfExcludeAny.total, 2);
  assert.deepEqual(cfExcludeAny.records.map((record) => record.sourceId), ['14', '15']);
  const cfCombined = await store.getPlatformRecords('curseforge', { gameplayCategories: ['Category A', 'Category B'], loader: 'Forge', page: 1, pageSize: 10 });
  assert.equal(cfCombined.total, 2);
  assert.deepEqual(cfCombined.records.map((record) => record.sourceId), ['11', '13']);
  const cfSecondPage = await store.getPlatformRecords('curseforge', { gameplayCategories: ['Category B'], page: 2, pageSize: 1 });
  assert.equal(cfSecondPage.total, 2);
  assert.deepEqual(cfSecondPage.records.map((record) => record.sourceId), ['13']);
  assert.deepEqual(Object.fromEntries(cfOr.availableGameplayCategories.map((option) => [option.value, option.count])), { 'Category A': 2, 'Category B': 2, 'Category C': 1 });
});

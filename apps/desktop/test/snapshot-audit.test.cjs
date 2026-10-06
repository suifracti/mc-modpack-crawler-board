const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { DataStore } = require('../lib/data-store.cjs');

async function setup(t, platforms) {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'mc-snapshot-audit-'));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  const source = path.join(root, 'source');
  await fs.mkdir(source);
  for (const [file, records] of Object.entries(platforms)) {
    await fs.writeFile(path.join(source, file), `window.fixture = ${JSON.stringify(records)};`);
  }
  // Reproduce the migrated, stale audit carried into every update.
  await fs.writeFile(path.join(source, 'audit_diff.js'), 'window.auditDiffData = {"is_available":false,"generated_at":"2026-09-17","stats":{"total_current":73522}};');
  const store = new DataStore(path.join(root, 'data'));
  await store.init();
  await store.importDirectory(source);
  return store;
}

async function update(store, platform, file, records) {
  const { workspace } = await store.prepareUpdateWorkspace(platform);
  await fs.writeFile(path.join(workspace, 'converted_output', 'data', file), `window.fixture = ${JSON.stringify(records)};`);
  return store.commitUpdate(workspace, platform, {
    sidecar: file, rawExists: false, rawCount: 0, count: records.length,
    changed: true, outcome: 'success_update',
  });
}

test('serial platform updates expose both deltas instead of the stale imported audit', async (t) => {
  const store = await setup(t, {
    'mcmod_data.js': [{ mid: 1, title: '包一', mcVersions: ['1.20.1'] }],
    'bili_data.js': [{ bvid: 'BV1', title: '旧标题' }],
  });
  await update(store, 'mcmod', 'mcmod_data.js', [
    { mid: 1, title: '包一', mcVersions: ['1.20.1', '1.21.1'] },
    { mid: 2, title: '新增包' },
  ]);
  await update(store, 'bilibili', 'bili_data.js', [
    { bvid: 'BV1', title: '新标题' }, { bvid: 'BV2', title: '新增视频' },
  ]);
  const audit = await store.getAuditDiff();
  assert.equal(audit.available, true);
  assert.deepEqual(audit.stats, { total_current: 4, total_prev: 2, added_count: 2, updated_count: 1, removed_count: 0, version_gained_count: 1 });
  assert.deepEqual(audit.added.map((r) => r.id).sort(), ['bilibili:BV2', 'mcmod:2']);
  assert.equal(audit.updated[0].title, '新标题');
  assert.equal(audit.version_gained[0].id, 'mcmod:1');
  assert.notEqual(audit.generated_at, '2026-09-17');
  // Reading an archived update must not pick changes from a future snapshot.
  await store.activateSnapshot(audit.platform_updates.mcmod.snapshotId);
  const archived = await store.getAuditDiff();
  assert.deepEqual(archived.added.map((r) => r.id), ['mcmod:2']);
});

test('a newer no-change observation replaces only that platform delta and ignores fetch timestamps', async (t) => {
  const store = await setup(t, { 'bili_data.js': [{ bvid: 'BV1', title: '同一包', observed_at: 'old' }] });
  await update(store, 'bilibili', 'bili_data.js', [{ bvid: 'BV1', title: '同一包', observed_at: 'today' }]);
  const audit = await store.getAuditDiff();
  assert.equal(audit.available, true);
  assert.equal(audit.updated.length, 0);
  assert.equal(audit.added.length, 0);
});

test('a new release download is version completion and actual absent IDs are removals', async (t) => {
  const store = await setup(t, { 'bbsmc_data.js': [
    { project_id: 'p1', title: '包一', releases: [{ id: 'r1', version_number: '1.0', files: [] }] },
    { project_id: 'p2', title: '已移除包' },
  ] });
  await update(store, 'bbsmc', 'bbsmc_data.js', [
    { project_id: 'p1', title: '包一', releases: [{ id: 'r1', version_number: '1.0', files: [{ url: 'https://example.com/pack.zip' }] }] },
  ]);
  const audit = await store.getAuditDiff();
  assert.equal(audit.version_gained.length, 1);
  assert.equal(audit.version_gained[0].id, 'bbsmc:p1');
  assert.equal(audit.removed.length, 1);
  assert.equal(audit.removed[0].id, 'bbsmc:p2');
});

test('missing predecessor is unavailable rather than treating every existing record as new', async (t) => {
  const store = await setup(t, { 'bili_data.js': [{ bvid: 'BV1', title: '已有包' }] });
  const previous = await store.getActiveSnapshot();
  await update(store, 'bilibili', 'bili_data.js', [{ bvid: 'BV1', title: '已有包' }, { bvid: 'BV2', title: '新包' }]);
  await fs.rm(path.join(store.snapshotsDir, previous.snapshotId), { recursive: true, force: true });
  const audit = await store.getAuditDiff();
  assert.equal(audit.available, false);
  assert.equal(audit.added.length, 0);
  assert.equal(audit.stats.total_current, 2);
});

test('pagination duplicates do not disable audit or count one source twice', async (t) => {
  const store = await setup(t, { 'modrinth_data.js': [
    { project_id: 'old', title: '原有包' }, { project_id: 'old', title: '原有包' },
  ] });
  await update(store, 'modrinth', 'modrinth_data.js', [
    { project_id: 'old', title: '原有包' },
    { project_id: 'new', title: '新包' }, { project_id: 'new', title: '新包' },
  ]);
  const audit = await store.getAuditDiff();
  assert.equal(audit.available, true);
  assert.equal(audit.added.length, 1);
  assert.equal(audit.added[0].id, 'modrinth:new');
  assert.equal(audit.updated.length, 0);
});

test('three historical tasks keep separate deltas, platforms and collection times', async (t) => {
  const store = await setup(t, {'bili_data.js': [{bvid:'BV1',title:'初始'}]});
  const snapshots=[];
  for (const title of ['第一次','第二次','第三次']) snapshots.push(await update(store,'bilibili','bili_data.js',[{bvid:'BV1',title}]));
  for (let i=0;i<snapshots.length;i++) await fs.writeFile(path.join(store.snapshotsDir,snapshots[i].snapshotId,'desktop_update_result.json'),JSON.stringify({startedAt:`2026-10-0${i+1}T01:00:00Z`,finishedAt:`2026-10-0${i+1}T01:02:00Z`,outcome:'success_update'}));
  const latest=await store.getAuditDiff();
  assert.equal(latest.history.length,3);
  assert.deepEqual(latest.history.map(x=>x.snapshotId),snapshots.toReversed().map(x=>x.snapshotId));
  for(let i=0;i<3;i++) {
    const audit=await store.getAuditDiff(i);
    assert.equal(audit.scope,'task');
    assert.equal(audit.updated[0].title,['第三次','第二次','第一次'][i]);
    assert.equal(audit.stats.updated_count,1);
    assert.equal(audit.platform_updates.bilibili.startedAt,`2026-10-0${3-i}T01:00:00Z`);
    assert.equal(audit.platform_updates.bilibili.finishedAt,`2026-10-0${3-i}T01:02:00Z`);
  }
  await assert.rejects(()=>store.getAuditDiff(-1),/审计轮次/);
});

test('every saved update remains selectable after new updates and a service restart', async (t) => {
  const store = await setup(t, {'bili_data.js': [{bvid:'BV1',title:'初始',view:10}]});
  const snapshots=[];
  for (let i=1;i<=5;i++) snapshots.push(await update(store,'bilibili','bili_data.js',[{bvid:'BV1',title:`第${i}次`,view:10+i}]));
  const audit=await store.getAuditDiff(0);
  assert.equal(audit.history.length,5);
  const first=await store.getAuditDiff(snapshots[0].snapshotId);
  assert.equal(first.baselineSnapshotId, audit.history.at(-1).baselineSnapshotId);
  assert.deepEqual(first.updated[0].changes.title, {before:'初始',after:'第1次'});
  assert.deepEqual(first.updated[0].changes.view, {before:'10',after:'11'});
  await update(store,'bilibili','bili_data.js',[{bvid:'BV1',title:'第6次',view:16}]);
  const restarted=new DataStore(store.rootDir); await restarted.init();
  const latest=await restarted.getAuditDiff(0);
  assert.equal(latest.history.length,6);
  assert.equal(latest.updated[0].changes.title.before,'第5次');
  assert.equal((await restarted.getAuditDiff(5)).updated[0].title,'第1次');
  assert.deepEqual((await restarted.getAuditDiff(snapshots[0].snapshotId)).updated,first.updated);
});

test('version changes include previous and current evidence instead of only a count', async (t) => {
  const store=await setup(t, {'mcmod_data.js':[{mid:1,title:'包',mcVersions:['1.20.1']}]});
  await update(store,'mcmod','mcmod_data.js',[{mid:1,title:'包',mcVersions:['1.20.1','1.21.1']}]);
  const audit=await store.getAuditDiff(0);
  assert.deepEqual(audit.version_gained[0].changes.versions, {before:['minecraft:1.20.1'],after:['minecraft:1.20.1','minecraft:1.21.1']});
});

test('a requested absent historical round is unavailable, never latest data relabelled',async(t)=>{
 const store=await setup(t,{'bili_data.js':[{bvid:'BV1',title:'初始'}]});
 await update(store,'bilibili','bili_data.js',[{bvid:'BV1',title:'更新'}]);
 const audit=await store.getAuditDiff(2); assert.equal(audit.available,false);assert.equal(audit.history.length,1);assert.equal(audit.updated.length,0);
});

test('an imported legacy audit cannot impersonate a requested task round', async (t) => {
  const store = await setup(t, { 'bili_data.js': [{ bvid: 'BV1', title: '历史包' }] });
  const active = await store.getActiveSnapshot();
  await fs.writeFile(path.join(store.snapshotDataDir(active.snapshotId), 'audit_diff.js'),
    'window.auditDiffData = {"is_available":true,"stats":{"added_count":42},"added":[{"id":"legacy"}]};');
  assert.equal((await store.getAuditDiff()).stats.added_count, 42);
  const round = await store.getAuditDiff(0);
  assert.equal(round.available, false);
  assert.deepEqual(round.history, []);
  assert.equal(round.added.length, 0);
});

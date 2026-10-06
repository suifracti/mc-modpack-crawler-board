const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { DataStore } = require('../lib/data-store.cjs');
const { UpdateManager } = require('../lib/update-manager.cjs');

async function setupStore() {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'mcmod-desktop-update-'));
  const sourceData = path.join(root, 'initial', 'data');
  await fs.mkdir(sourceData, { recursive: true });
  await fs.writeFile(path.join(sourceData, 'bili_data.js'), 'window.biliModpacksData = [{"bvid":"old","title":"旧数据","url":"https://example.com/old"}];\n', 'utf8');
  const store = new DataStore(path.join(root, 'user-data'));
  await store.init();
  await store.importDirectory(path.join(root, 'initial'));
  return { root, store };
}

function fakeRunnerFactory(mode = 'success') {
  return ({ workspace, onLine }) => {
    let resolvePromise;
    let rejectPromise;
    const promise = new Promise((resolve, reject) => { resolvePromise = resolve; rejectPromise = reject; });
    const runner = { promise, cancel: () => { resolvePromise({ code: 130, signal: 'SIGTERM' }); } };
    setImmediate(async () => {
      if (mode === 'cancel') { resolvePromise({ code: 130, signal: 'SIGTERM' }); return; }
      if (mode === 'fail') { onLine('network unavailable'); resolvePromise({ code: 1, signal: null }); return; }
      await fs.writeFile(path.join(workspace, 'converted_output', 'data', 'bili_data.js'), 'window.biliModpacksData = [{"bvid":"new","title":"新数据","url":"https://example.com/new"}];\n', 'utf8');
      await fs.writeFile(path.join(workspace, 'crawler_output', 'bilibili_modpacks.json'), '[{"bvid":"new","title":"新数据"}]', 'utf8');
      await fs.writeFile(path.join(workspace, 'build', 'desktop_update_result.json'), JSON.stringify({
        platform: 'bilibili',
        outcome: 'success_update',
        rawTouched: true,
        sidecarTouched: true,
        collectionResultTouched: true,
        crawlerResult: { status: 'success', requestCompleted: true, fetchedCount: 1, failedRequests: 0, truncated: false },
        changed: true,
      }), 'utf8');
      onLine('DESKTOP_EVENT {"phase":"采集完成","processed":1,"total":1}');
      resolvePromise({ code: 0, signal: null });
    });
    return runner;
  };
}

function deferred() {
  let resolve;
  const promise = new Promise((done) => { resolve = done; });
  return { promise, resolve };
}

function nextTurn() {
  return new Promise((resolve) => setImmediate(resolve));
}

test('only one update task can run and success switches the snapshot', async () => {
  const { store } = await setupStore();
  const manager = new UpdateManager({ store, runnerFactory: fakeRunnerFactory('success') });
  const running = manager.start('bilibili', { limit: 1 });
  assert.throws(() => manager.start('mcmod'), /已有更新任务正在运行/);
  const result = await running;
  assert.equal(result.state, 'success');
  const records = await store.getPlatformRecords('bilibili');
  assert.equal(records.records[0].title, '新数据');
});

test('failure keeps the previous snapshot and cancellation does not commit', async () => {
  const { store } = await setupStore();
  const failed = new UpdateManager({ store, runnerFactory: fakeRunnerFactory('fail') });
  const failedResult = await failed.start('bilibili');
  assert.equal(failedResult.state, 'failed');
  assert.equal((await store.getPlatformRecords('bilibili')).records[0].title, '旧数据');

  const cancelled = new UpdateManager({ store, runnerFactory: fakeRunnerFactory('cancel') });
  const pending = cancelled.start('bilibili');
  cancelled.cancel();
  const cancelledResult = await pending;
  assert.equal(cancelledResult.state, 'cancelled');
  assert.equal((await store.getPlatformRecords('bilibili')).records[0].title, '旧数据');
});

test('cancelled old-pack refresh keeps its isolated checkpoint for recovery', async () => {
  const { store } = await setupStore();
  const manager = new UpdateManager({ store, runnerFactory: fakeRunnerFactory('cancel') });
  const pending = manager.start('bilibili', { mode: 'existing' });
  manager.cancel();
  const result = await pending;
  assert.equal(result.state, 'cancelled');
  const workspaces = await fs.readdir(store.incomingDir);
  assert.equal(workspaces.length, 1);
  assert.equal((await store.getPlatformRecords('bilibili')).records[0].title, '旧数据');
});

test('cancellation during preparation prevents the runner and shutdown waits for the task', async () => {
  const { store } = await setupStore();
  const preparation = deferred();
  const originalPrepare = store.prepareUpdateWorkspace.bind(store);
  store.prepareUpdateWorkspace = async (...args) => {
    await preparation.promise;
    return originalPrepare(...args);
  };
  let runnerStarted = false;
  const manager = new UpdateManager({
    store,
    runnerFactory: () => { runnerStarted = true; return fakeRunnerFactory('success')({ workspace: '', onLine: () => {} }); },
  });
  const pending = manager.start('bilibili');
  await nextTurn();
  assert.deepEqual(manager.cancel(), { cancelled: true });
  let shutdownDone = false;
  const shutdown = manager.shutdown().then(() => { shutdownDone = true; });
  await nextTurn();
  assert.equal(shutdownDone, false);
  preparation.resolve();
  const result = await pending;
  await shutdown;
  assert.equal(result.state, 'cancelled');
  assert.equal(runnerStarted, false);
  assert.equal((await store.getPlatformRecords('bilibili')).records[0].title, '旧数据');
});

test('cancellation during validation preserves the active pointer', async () => {
  const { store } = await setupStore();
  const validation = deferred();
  const entered = deferred();
  const originalValidate = store.validateStage.bind(store);
  store.validateStage = async (...args) => {
    entered.resolve();
    await validation.promise;
    return originalValidate(...args);
  };
  const manager = new UpdateManager({ store, runnerFactory: fakeRunnerFactory('success') });
  const pending = manager.start('bilibili');
  await entered.promise;
  assert.deepEqual(manager.cancel(), { cancelled: true });
  validation.resolve();
  const result = await pending;
  assert.equal(result.state, 'cancelled');
  assert.equal((await store.getPlatformRecords('bilibili')).records[0].title, '旧数据');
});

test('cancellation after the pointer commit point is refused and the result is successful', async () => {
  const { store } = await setupStore();
  const originalCommit = store.commitUpdate.bind(store);
  let cancelResult;
  store.commitUpdate = async (workspace, platform, validation, metadata, control) => originalCommit(
    workspace,
    platform,
    validation,
    metadata,
    {
      beforePointerCommit: () => {
        control.beforePointerCommit();
        queueMicrotask(() => { cancelResult = manager.cancel(); });
      },
    },
  );
  const manager = new UpdateManager({ store, runnerFactory: fakeRunnerFactory('success') });
  const result = await manager.start('bilibili');
  await nextTurn();
  assert.deepEqual(cancelResult, { cancelled: false, reason: 'commit_started' });
  assert.equal(result.state, 'success');
  assert.equal((await store.getPlatformRecords('bilibili')).records[0].title, '新数据');
});

test('preserves mode and coverOffset options for runner', async () => {
  const { store } = await setupStore();
  let capturedOptions = null;
  const runnerFactory = ({ platform, options, workspace, onLine }) => {
    capturedOptions = options;
    return fakeRunnerFactory('cancel')({ workspace, onLine });
  };
  const manager = new UpdateManager({ store, runnerFactory });
  await manager.start('mcmod', { mode: 'covers', coverOffset: 40, limit: 10 });
  assert.equal(capturedOptions?.mode, 'covers');
  assert.equal(capturedOptions?.coverOffset, 40);
  assert.equal(capturedOptions?.limit, 10);
});

test('a server batch survives one source failure and reports every source independently',async()=>{
 const calls=[];
 const store={prepareUpdateWorkspace:async(p)=>({workspace:p}),validateStage:async()=>({outcome:'partial_update',count:7,contract:{crawlerResult:{failedRequests:0,details:{provider:'modpacks-ch',coverage:'third-party-catalog',observedCount:100,pagesObserved:2,fullRefresh:false}}}}),commitUpdate:async()=>({snapshotId:'new',canonicalReady:false}),cleanupWorkspace:async()=>{}};
 const manager=new UpdateManager({store,runnerFactory:({platform,onLine})=>{calls.push(platform);if(platform==='bilibili')onLine('DESKTOP_EVENT '+JSON.stringify({phase:'失败',error:'connection unavailable'}));return {promise:Promise.resolve({code:platform==='bilibili'?1:0})};}});
 const status=await manager.startBatch([{platform:'bilibili',options:{mode:'existing',limit:30}},{platform:'curseforge',options:{mode:'recent',pages:2}},{platform:'modrinth',options:{limit:100}}]);
 assert.deepEqual(calls,['bilibili','curseforge','modrinth']);
 assert.equal(status.batch.completed,3);assert.equal(status.batch.state,'completed');
 assert.deepEqual(status.batch.results.map(r=>r.state),['failed','success','success']);
 assert.equal(status.batch.results[0].error,'connection unavailable');
 assert.equal(status.batch.results[1].result.provider,'modpacks-ch');
 assert.equal(status.batch.results[1].result.observedCount,100);
});

test('batch cancellation stops remaining sources and direct starts cannot interleave',async()=>{
 const {store}=await setupStore();const entered=deferred(),finish=deferred();let count=0;
 const manager=new UpdateManager({store,runnerFactory:()=>{count++;entered.resolve();return {promise:finish.promise,cancel:()=>finish.resolve({code:130})};}});
 const pending=manager.startBatch([{platform:'bilibili'},{platform:'curseforge'}]);await entered.promise;
 assert.throws(()=>manager.start('mcmod'),/已有更新任务/);
 assert.deepEqual(manager.cancel(),{cancelled:true});
 const result=await pending;assert.equal(count,1);assert.equal(result.batch.state,'cancelled');assert.equal(result.batch.results[0].state,'cancelled');
});

test('invalid batch inputs fail before any platform starts',()=>{
 let count=0;const manager=new UpdateManager({store:{},runnerFactory:()=>{count++;}});
 for(const items of [[],[{platform:'unknown'}],[{platform:'bilibili'},{platform:'bilibili'}],[{platform:'bilibili'},{platform:'curseforge',options:{limit:-1}}]])assert.throws(()=>manager.startBatch(items));
 assert.equal(count,0);assert.equal(manager.getStatus().state,'idle');
});

test('completed batch results remain available after restarting the service',async()=>{
 const {store}=await setupStore();const manager=new UpdateManager({store,runnerFactory:fakeRunnerFactory('fail')});
 await manager.startBatch([{platform:'bilibili'},{platform:'curseforge'}]);
 const restored=new UpdateManager({store,runnerFactory:()=>{throw new Error('must not restart network jobs');}});
 await restored.restoreBatchHistory();
 assert.equal(restored.getStatus().batch.state,'completed');assert.equal(restored.getStatus().batch.completed,2);
 assert.deepEqual(restored.getStatus().batch.platforms,['bilibili','curseforge']);
 assert.deepEqual(restored.getStatus().batch.results.map(r=>r.state),['failed','failed']);
});

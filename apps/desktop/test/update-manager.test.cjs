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

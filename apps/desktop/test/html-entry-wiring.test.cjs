const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { createRequire } = require('node:module');
const { UpdateManager } = require('../lib/update-manager.cjs');

const desktopRoot = path.resolve(__dirname, '..');
const repoRoot = path.resolve(desktopRoot, '..', '..');
const fixtureDataRoot = path.join(repoRoot, 'test-fixture-user-data');
const expectedState = path.join(fixtureDataRoot, 'collector-state', 'bilibili-public-html-state.json');

function loadBrowserServiceWithFakeProcess() {
  const file = path.join(desktopRoot, 'server.cjs');
  const sourceRequire = createRequire(file);
  const captured = [];
  const module = { exports: {} };
  const fakeRequire = (name) => name === './lib/process-runner.cjs'
    ? { createProcessRunner: (options) => { captured.push(options); return { promise: Promise.resolve({ code: 1 }), cancel() {} }; } }
    : sourceRequire(name);
  vm.runInNewContext(fs.readFileSync(file, 'utf8'), {
    require: fakeRequire, module, exports: module.exports, __dirname: desktopRoot,
    process, Buffer, URL, console, setTimeout, clearTimeout,
  }, { filename: file });
  return { createBrowserService: module.exports.createBrowserService, captured };
}

test('browser jobs share a persistent HTML state path outside job workspaces', () => {
  const { createBrowserService, captured } = loadBrowserServiceWithFakeProcess();
  const service = createBrowserService({ dataRoot: fixtureDataRoot, store: {}, personalLibrary: {}, favoriteUpdates: {} });
  for (const job of ['one', 'two']) {
    service.updateManager.runnerFactory({ platform: 'bilibili', options: { mode: 'existing', limit: 2 },
      workspace: path.join(fixtureDataRoot, 'incoming', job), onLine() {} });
  }
  for (const runner of captured) {
    assert.equal(runner.args[runner.args.indexOf('--html-state') + 1], expectedState);
    assert.equal(runner.args[runner.args.indexOf('--mode') + 1], 'existing');
    assert.equal(runner.args[runner.args.indexOf('--limit') + 1], '2');
    assert.equal(runner.args.includes('--login'), false);
    assert.equal(expectedState.startsWith(`${runner.cwd}${path.sep}`), false);
  }
  service.updateManager.runnerFactory({ platform: 'mcmod', options: {}, workspace: path.join(fixtureDataRoot, 'incoming', 'three'), onLine() {} });
  assert.equal(captured[2].args.includes('--html-state'), false);
});

test('Electron runner shares the same state file for successive Bilibili jobs', () => {
  const file = path.join(desktopRoot, 'main.cjs');
  const source = fs.readFileSync(file, 'utf8');
  const start = source.indexOf('function makeRunner(');
  const end = source.indexOf('const updateManager =', start);
  assert.ok(start >= 0 && end > start);
  const captured = [];
  const makeRunner = vm.runInNewContext(`${source.slice(start, end)}\nmakeRunner;`, {
    path, dataRoot: fixtureDataRoot, fs: { existsSync: () => true },
    pythonCommand: () => 'fake-python', workerScript: () => path.join(desktopRoot, 'collector_worker.py'),
    sourceRoot: () => repoRoot,
    createProcessRunner: (options) => { captured.push(options); return {}; },
  }, { filename: file });
  for (const job of ['one', 'two']) {
    makeRunner({ platform: 'bilibili', options: { mode: 'existing' },
      workspace: path.join(fixtureDataRoot, 'incoming', job), onLine() {} });
  }
  assert.equal(captured[0].args[captured[0].args.indexOf('--html-state') + 1], expectedState);
  assert.equal(captured[1].args[captured[1].args.indexOf('--html-state') + 1], expectedState);
});

function fakeStore(contract) {
  return {
    async prepareUpdateWorkspace() { return { workspace: path.join(fixtureDataRoot, 'incoming', 'fake-job') }; },
    async validateStage() { return { outcome: 'partial_update', count: 7, contract }; },
    async commitUpdate(_workspace, _platform, _validation, _metadata, control) {
      control.beforePointerCommit();
      return { snapshotId: 'fake-snapshot', canonicalReady: false };
    },
    async cleanupWorkspace() {},
  };
}

test('bounded HTML coverage remains partial and reports true observation counts without invented request failures', async () => {
  const details = { coverage: 'public-video-html-bounded', observedCount: 3, newCount: 1,
    updatedCount: 2, failedCount: 0, requestBudget: { dailyLimit: 30 }, stopped: false, apiBusinessRequests: 0 };
  const manager = new UpdateManager({
    store: fakeStore({ crawlerResult: { status: 'partial', failedRequests: 0, details } }),
    runnerFactory: () => ({ promise: Promise.resolve({ code: 0, signal: null }) }),
  });
  const status = await manager.start('bilibili', { limit: 3 });
  assert.equal(status.state, 'success');
  assert.equal(status.result.outcome, 'partial_update');
  assert.equal(status.result.coverage, details.coverage);
  assert.equal(status.result.observedCount, 3);
  assert.equal(status.result.newCount, 1);
  assert.equal(status.result.updatedCount, 2);
  assert.equal(status.result.failedCount, 0);
  assert.match(status.phase, /HTML局部覆盖/);
  assert.match(status.logs.at(-1), /观察 3 页，新增 1 条，更新 2 条，失败 0 次/);
  assert.match(status.logs.at(-1), /API业务请求 0/);
  assert.doesNotMatch(status.phase, /请求失败/);
});

test('bounded HTML access stop and actual failures are kept in the result', async () => {
  const details = { coverage: 'public-video-html-bounded', observedCount: 1, newCount: 0,
    updatedCount: 1, failedCount: 1, stopped: true, apiBusinessRequests: 0 };
  const manager = new UpdateManager({
    store: fakeStore({ crawlerResult: { status: 'partial', failedRequests: 1, details } }),
    runnerFactory: () => ({ promise: Promise.resolve({ code: 0, signal: null }) }),
  });
  const status = await manager.start('bilibili');
  assert.equal(status.result.failedRequests, 1);
  assert.equal(status.result.stopped, true);
  assert.match(status.logs.at(-1), /失败 1 次/);
  assert.match(status.logs.at(-1), /已停止访问/);
});

test('other partial coverage does not invent an upstream request failure', async () => {
  const manager = new UpdateManager({
    store: fakeStore({ crawlerResult: { status: 'partial', failedRequests: 0 } }),
    runnerFactory: () => ({ promise: Promise.resolve({ code: 0, signal: null }) }),
  });
  const status = await manager.start('curseforge');
  assert.equal(status.result.outcome, 'partial_update');
  assert.match(status.phase, /局部覆盖/);
  assert.doesNotMatch(status.phase, /请求失败/);
  assert.doesNotMatch(status.logs.at(-1), /原站请求失败/);
});


test('failed runner preserves the current HTML refusal reason and never validates or commits', async () => {
  const reportedErrors = [
    'robots.txt 拒绝公开视频路径，已持久停止自动访问',
    '公开页出现 captcha 验证码，已持久停止自动访问',
    null,
  ];
  let run = 0;
  let validationCalls = 0;
  let commitCalls = 0;
  const store = fakeStore({});
  store.validateStage = async () => { validationCalls += 1; throw new Error('unexpected validation'); };
  store.commitUpdate = async () => { commitCalls += 1; throw new Error('unexpected commit'); };
  const manager = new UpdateManager({
    store,
    runnerFactory: ({ onLine }) => {
      const error = reportedErrors[run++];
      if (error) onLine('DESKTOP_EVENT ' + JSON.stringify({ platform: 'bilibili', phase: '失败', error }));
      return { promise: Promise.resolve({ code: 1, signal: null }) };
    },
  });
  for (const error of reportedErrors) {
    const status = await manager.start('bilibili', { mode: 'existing' });
    assert.equal(status.state, 'failed');
    assert.equal(status.error, error || '采集进程退出码 1');
    if (error) {
      assert.doesNotMatch(status.error, /采集进程退出码/);
      assert.ok(status.logs.includes(`更新失败：${error}`));
    }
  }
  assert.equal(validationCalls, 0);
  assert.equal(commitCalls, 0);
});

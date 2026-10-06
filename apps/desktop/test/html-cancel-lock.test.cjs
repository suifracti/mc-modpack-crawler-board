const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { UpdateManager } = require('../lib/update-manager.cjs');

for (const scenario of [
  { name: 'closed owned worker', owner: '12345', closed: true, platform: 'bilibili', removed: true },
  { name: 'different lock owner', owner: '54321', closed: true, platform: 'bilibili', removed: false },
  { name: 'worker not confirmed exited', owner: '12345', closed: false, platform: 'bilibili', removed: false },
  { name: 'another platform task', owner: '12345', closed: true, platform: 'curseforge', removed: false },
]) {
  test(`cancellation preserves the ledger and only releases a closed owned HTML lock: ${scenario.name}`, async () => {
    const rootDir = await fs.mkdtemp(path.join(os.tmpdir(), 'mc-cancel-lock-test-'));
    const stateDir = path.join(rootDir, 'collector-state');
    await fs.mkdir(stateDir);
    const ledgerPath = path.join(stateDir, 'bilibili-public-html-state.json');
    const ledger = JSON.stringify({ days: { fixture: { attempted: ['BVfixture'] } }, stopped: { httpStatus: 403 } });
    await fs.writeFile(ledgerPath, ledger);
    const lockPath = `${ledgerPath}.lock`;
    await fs.writeFile(lockPath, scenario.owner);
    let preparedResolve; const ready = new Promise(resolve => { preparedResolve = resolve; });
    let closeResolve; const workerPromise = new Promise(resolve => { closeResolve = resolve; });
    let commits = 0; let validations = 0;
    const child = { pid: 12345, exitCode: null, signalCode: null };
    const manager = new UpdateManager({
      store: { rootDir,
        async prepareUpdateWorkspace() { return { workspace: path.join(rootDir, 'incoming', 'fixture') }; },
        async validateStage() { validations++; throw Error('Cancelled job must not validate'); },
        async commitUpdate() { commits++; throw Error('Cancelled job must not commit'); },
        async cleanupWorkspace() {},
      },
      runnerFactory: () => { preparedResolve(); return { child, promise: workerPromise, cancel() {} }; },
    });
    const running = manager.start(scenario.platform, { mode: 'existing' });
    await ready;
    assert.equal(manager.cancel().cancelled, true);
    if (scenario.closed) child.exitCode = 1;
    closeResolve({ code: 1, signal: null });
    const status = await running;
    assert.equal(status.state, 'cancelled');
    assert.equal(manager.active, null);
    assert.equal(commits, 0); assert.equal(validations, 0);
    assert.equal(await fs.readFile(ledgerPath, 'utf8'), ledger);
    assert.equal(await fs.stat(lockPath).then(() => false, e => { assert.equal(e.code, 'ENOENT'); return true; }), scenario.removed);
    if (!scenario.removed) assert.equal(await fs.readFile(lockPath, 'utf8'), scenario.owner);
  });
}

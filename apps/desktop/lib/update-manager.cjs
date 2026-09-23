const { EventEmitter } = require('node:events');
const { assertPlatform, PLATFORM_CONFIGS, redactLogLine } = require('./platforms.cjs');

function validLimit(value) {
  if (value === undefined || value === null || value === '') return null;
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < 1 || parsed > 100000) throw new Error('采集上限必须是 1 到 100000 之间的整数');
  return parsed;
}

class CancelledBeforeCommit extends Error {
  constructor() {
    super('任务已取消，未替换当前数据');
    this.name = 'CancelledBeforeCommit';
  }
}

class UpdateManager extends EventEmitter {
  constructor({ store, runnerFactory, logger = () => {}, now = () => new Date().toISOString(), onSnapshotActivated = async () => {} }) {
    super();
    this.store = store;
    this.runnerFactory = runnerFactory;
    this.logger = logger;
    this.now = now;
    this.onSnapshotActivated = onSnapshotActivated;
    this.active = null;
    this.taskPromise = null;
    this.status = { state: 'idle', taskId: null, platform: null, phase: 'idle', processed: 0, total: null, logs: [] };
  }

  getStatus() {
    return JSON.parse(JSON.stringify(this.status));
  }

  setStatus(patch) {
    this.status = { ...this.status, ...patch };
    this.emit('status', this.getStatus());
  }

  appendLog(message) {
    const safe = redactLogLine(message).slice(0, 2000);
    this.status.logs = [...this.status.logs, safe].slice(-200);
    this.logger(safe);
    this.emit('log', safe);
    this.emit('status', this.getStatus());
    const event = safe.match(/^DESKTOP_EVENT\s+(\{.*\})$/);
    if (event) {
      try {
        const parsed = JSON.parse(event[1]);
        this.setStatus({ ...parsed, phase: parsed.phase || this.status.phase });
      } catch { /* ordinary log */ }
    }
  }

  start(platform, options = {}) {
    assertPlatform(platform);
    if (this.active) {
      const error = new Error('已有更新任务正在运行');
      error.code = 'UPDATE_ALREADY_RUNNING';
      throw error;
    }
    const normalizedOptions = {
      limit: validLimit(options.limit),
      pages: validLimit(options.pages),
      until: options.until ? String(options.until).slice(0, 32) : null,
    };
    const taskId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const active = { taskId, platform, workspace: null, runner: null, cancelled: false };
    this.active = active;
    this.status = {
      state: 'running',
      taskId,
      platform,
      platformName: PLATFORM_CONFIGS[platform].name,
      phase: '准备隔离目录',
      processed: 0,
      total: null,
      startedAt: this.now(),
      endedAt: null,
      error: null,
      logs: [],
    };
    this.emit('status', this.getStatus());
    this.appendLog(`开始更新 ${PLATFORM_CONFIGS[platform].name}，仅在隔离目录执行。`);
    this.taskPromise = this.runTask(active, normalizedOptions);
    active.promise = this.taskPromise;
    return this.taskPromise;
  }

  assertNotCancelled(active) {
    if (active.cancelled && !active.commitStarted) throw new CancelledBeforeCommit();
  }

  async runTask(active, normalizedOptions) {
    let prepared = null;
    try {
      this.assertNotCancelled(active);
      prepared = await this.store.prepareUpdateWorkspace(active.platform);
      active.workspace = prepared.workspace;
      this.assertNotCancelled(active);
      active.runner = this.runnerFactory({
        platform: active.platform,
        options: normalizedOptions,
        workspace: prepared.workspace,
        onLine: (line) => this.appendLog(line),
      });
      this.assertNotCancelled(active);
      const result = await active.runner.promise;
      this.assertNotCancelled(active);
      if (result.code !== 0) throw new Error(`采集进程退出码 ${result.code}${result.signal ? ` (${result.signal})` : ''}`);
      this.setStatus({ phase: '完整性检查' });
      const validation = await this.store.validateStage(prepared.workspace, active.platform);
      this.assertNotCancelled(active);
      const manifest = await this.store.commitUpdate(
        prepared.workspace,
        active.platform,
        validation,
        { options: normalizedOptions },
        {
          beforePointerCommit: () => {
            this.assertNotCancelled(active);
            active.commitStarted = true;
          },
        },
      );
      active.committed = true;
      try {
        await this.onSnapshotActivated({
          platform: active.platform,
          snapshotId: manifest.snapshotId,
          outcome: validation.outcome,
          count: validation.count,
        });
      } catch (error) {
        this.appendLog(`快照已切换；收藏更新提醒暂未处理：${error instanceof Error ? error.message : String(error)}`);
      }
      this.setStatus({
        state: 'success',
        phase: '已完成并切换数据快照',
        processed: validation.count,
        total: validation.count,
        endedAt: this.now(),
        result: { count: validation.count, snapshotId: manifest.snapshotId, canonicalReady: manifest.canonicalReady },
      });
      this.appendLog(`更新成功：${validation.count} 条数据已切换；上一份快照仍保留。`);
      return this.getStatus();
    } catch (error) {
      const cancelled = error instanceof CancelledBeforeCommit || (active.cancelled && !active.commitStarted);
      this.setStatus({
        state: cancelled ? 'cancelled' : 'failed',
        phase: cancelled ? '已取消' : '失败，旧数据已保留',
        endedAt: this.now(),
        error: error instanceof Error ? error.message : String(error),
      });
      this.appendLog(cancelled ? '任务已取消，未替换当前数据。' : `更新失败：${this.status.error}`);
      return this.getStatus();
    } finally {
      if (prepared) await this.store.cleanupWorkspace(prepared.workspace).catch(() => {});
      if (this.active === active) this.active = null;
      if (this.taskPromise && this.taskPromise === active.promise) this.taskPromise = null;
    }
  }

  cancel() {
    if (!this.active) return { cancelled: false, reason: 'idle' };
    if (this.active.commitStarted) return { cancelled: false, reason: 'commit_started' };
    if (this.active.cancelled) return { cancelled: false, reason: 'already_requested' };
    this.active.cancelled = true;
    this.setStatus({ phase: '正在取消' });
    this.appendLog('收到取消请求，正在结束本任务的进程树。');
    this.active.runner?.cancel?.();
    return { cancelled: true };
  }

  async shutdown() {
    this.cancel();
    if (this.taskPromise) await this.taskPromise.catch(() => {});
  }
}

module.exports = { UpdateManager, validLimit };

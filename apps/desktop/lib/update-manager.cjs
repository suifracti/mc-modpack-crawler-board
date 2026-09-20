const { EventEmitter } = require('node:events');
const { assertPlatform, PLATFORM_CONFIGS, redactLogLine } = require('./platforms.cjs');

function validLimit(value) {
  if (value === undefined || value === null || value === '') return null;
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < 1 || parsed > 100000) throw new Error('采集上限必须是 1 到 100000 之间的整数');
  return parsed;
}

class UpdateManager extends EventEmitter {
  constructor({ store, runnerFactory, logger = () => {}, now = () => new Date().toISOString() }) {
    super();
    this.store = store;
    this.runnerFactory = runnerFactory;
    this.logger = logger;
    this.now = now;
    this.active = null;
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

  async start(platform, options = {}) {
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
    let prepared = null;
    try {
      prepared = await this.store.prepareUpdateWorkspace(platform);
      active.workspace = prepared.workspace;
      active.runner = this.runnerFactory({
        platform,
        options: normalizedOptions,
        workspace: prepared.workspace,
        onLine: (line) => this.appendLog(line),
      });
      const result = await active.runner.promise;
      if (active.cancelled) {
        this.setStatus({ state: 'cancelled', phase: '已取消', endedAt: this.now(), error: null });
        return this.getStatus();
      }
      if (result.code !== 0) throw new Error(`采集进程退出码 ${result.code}${result.signal ? ` (${result.signal})` : ''}`);
      this.setStatus({ phase: '完整性检查' });
      const validation = await this.store.validateStage(prepared.workspace, platform);
      const manifest = await this.store.commitUpdate(prepared.workspace, platform, validation, { options: normalizedOptions });
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
      const cancelled = active.cancelled;
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
      this.active = null;
    }
  }

  cancel() {
    if (!this.active) return false;
    this.active.cancelled = true;
    this.setStatus({ phase: '正在取消' });
    this.appendLog('收到取消请求，正在结束本任务的进程树。');
    this.active.runner?.cancel?.();
    return true;
  }

  async shutdown() {
    this.cancel();
    if (this.active?.runner?.promise) await this.active.runner.promise.catch(() => {});
  }
}

module.exports = { UpdateManager, validLimit };

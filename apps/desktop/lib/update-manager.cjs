const { EventEmitter } = require('node:events');
const fs = require('node:fs/promises');
const path = require('node:path');
const { assertPlatform, PLATFORM_CONFIGS, redactLogLine } = require('./platforms.cjs');

function validLimit(value) {
  if (value === undefined || value === null || value === '') return null;
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < 1 || parsed > 100000) throw new Error('采集上限必须是 1 到 100000 之间的整数');
  return parsed;
}

function normalizeOptions(options = {}) {
  return {limit:validLimit(options.limit),pages:validLimit(options.pages),
    until:options.until?String(options.until).slice(0,32):null,mode:options.mode?String(options.mode).slice(0,32):null,
    coverOffset:options.coverOffset!==undefined&&options.coverOffset!==null?validLimit(options.coverOffset)||0:null};
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
    return JSON.parse(JSON.stringify({...this.status,...(this.batch?{batch:this.batch}:{})}));
  }

  async saveBatchHistory() {
    if(!this.store.rootDir)return;
    const file=path.join(this.store.rootDir,'update-batch-history.json');
    const temp=`${file}.${process.pid}.tmp`;
    try {await fs.writeFile(temp,JSON.stringify({schema:1,status:this.getStatus()}));await fs.rename(temp,file);}
    catch(error){this.appendLog(`批次记录未保存：${error.message}`);}
  }

  async restoreBatchHistory() {
    if(!this.store.rootDir)return;
    try {
      const saved=JSON.parse(await fs.readFile(path.join(this.store.rootDir,'update-batch-history.json'),'utf8'));
      const batch=saved.status?.batch;
      if(saved.schema!==1||!batch||!Array.isArray(batch.results)||!Array.isArray(batch.platforms)||batch.total<1||batch.total>6)return;
      for(const platform of batch.platforms)assertPlatform(platform);
      this.batch=batch;this.status=saved.status;delete this.status.batch;
      if(batch.state==='running') {
        this.batch.state='cancelled';this.batch.cancelled=true;
        this.status={...this.status,state:'cancelled',phase:'服务已重启，未完成批次停止；旧数据保留'};
      }
    } catch { /* No usable previous batch: keep the service idle. */ }
  }

  startBatch(plans) {
    if(this.active || this.batch?.state==='running') {
      const error=new Error('已有更新任务正在运行');error.code='UPDATE_ALREADY_RUNNING';throw error;
    }
    if(!Array.isArray(plans)||plans.length<1||plans.length>6)throw new Error('批次须选择1到6个平台');
    const platforms=new Set();
    const validated=plans.map(plan=>{
      assertPlatform(plan?.platform);
      if(platforms.has(plan.platform))throw new Error('批次平台不能重复');
      platforms.add(plan.platform);return {platform:plan.platform,options:normalizeOptions(plan.options)};
    });
    this.batch={state:'running',total:validated.length,completed:0,results:[],cancelled:false,platforms:validated.map(p=>p.platform)};
    this.setStatus({state:'running',phase:'准备批次',taskId:null,platform:null,error:null,result:undefined,processed:0,total:null});
    this.batchPromise=this.runBatch(validated);
    return this.batchPromise;
  }

  async runBatch(plans) {
    try {
      await this.saveBatchHistory();
      for(const plan of plans) {
        if(this.batch.cancelled)break;
        const status=await this.start(plan.platform,plan.options,true);
        this.batch.results.push({platform:plan.platform,state:status.state,error:status.error,endedAt:status.endedAt,result:status.result});
        this.batch.completed++;
        await this.saveBatchHistory();
        this.emit('status',this.getStatus());
      }
    } finally {
      const failed=this.batch.results.filter(r=>r.state==='failed').length;
      const succeeded=this.batch.results.filter(r=>r.state==='success').length;
      this.batch.state=this.batch.cancelled?'cancelled':'completed';
      this.setStatus({state:this.batch.cancelled?'cancelled':failed&& !succeeded?'failed':'success',
        phase:this.batch.cancelled?'批次已取消':`批次完成：${succeeded}站已保存，${failed}站失败`,endedAt:this.now(),error:null});
      await this.saveBatchHistory();
    }
    return this.getStatus();
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

  start(platform, options = {}, fromBatch = false) {
    assertPlatform(platform);
    if (this.active || (this.batch?.state==='running' && !fromBatch)) {
      const error = new Error('已有更新任务正在运行');
      error.code = 'UPDATE_ALREADY_RUNNING';
      throw error;
    }
    const normalizedOptions = normalizeOptions(options);
    if(!fromBatch)this.batch=null;
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

  async releaseCancelledHtmlLock(active) {
    const child = active.runner?.child;
    if (active.platform !== 'bilibili' || !active.cancelled || !active.runnerClosed
        || !Number.isInteger(child?.pid) || child.pid < 1 || typeof this.store.rootDir !== 'string'
        || !(Number.isInteger(child.exitCode) || (typeof child.signalCode === 'string' && child.signalCode))) return;
    const lockPath = path.join(this.store.rootDir, 'collector-state', 'bilibili-public-html-state.json.lock');
    try {
      const stat = await fs.lstat(lockPath);
      if (!stat.isFile() || stat.isSymbolicLink()) return;
      if ((await fs.readFile(lockPath, 'utf8')).trim() !== String(child.pid)) return;
      await fs.unlink(lockPath);
      this.appendLog('已清理本次已退出采集进程的锁；采集记录与访问停止状态保留。');
    } catch (error) {
      if (error.code !== 'ENOENT') this.appendLog(`本次采集锁未能清理：${error.message}`);
    }
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
      active.runnerClosed = true;
      this.assertNotCancelled(active);
      if (result.code !== 0) {
        const reportedError = this.status.taskId === active.taskId && typeof this.status.error === 'string'
          ? this.status.error.trim() : '';
        throw new Error(reportedError || `采集进程退出码 ${result.code}${result.signal ? ` (${result.signal})` : ''}`);
      }
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
      const crawlerResult = validation.contract?.crawlerResult || {};
      const coverageDetails = crawlerResult.details || {};
      const htmlCoverage = active.platform === 'bilibili' && coverageDetails.coverage === 'public-video-html-bounded';
      const failedRequests = Number(crawlerResult.failedRequests || 0);
      const coverageSummary = htmlCoverage
        ? `B站主站HTML局部覆盖：观察 ${Number(coverageDetails.observedCount || 0)} 页，新增 ${Number(coverageDetails.newCount || 0)} 条，更新 ${Number(coverageDetails.updatedCount || 0)} 条，失败 ${Number(coverageDetails.failedCount ?? failedRequests)} 次；API业务请求 ${Number(coverageDetails.apiBusinessRequests || 0)}`
        : null;
      this.setStatus({
        state: 'success',
        phase: htmlCoverage ? 'B站主站HTML局部覆盖已切换'
          : validation.outcome === 'partial_update' ? failedRequests > 0 ? '部分更新已切换（原站有请求失败）' : '局部覆盖已切换'
            : '已完成并切换数据快照',
        processed: validation.count,
        total: validation.count,
        endedAt: this.now(),
        result: { count: validation.count, snapshotId: manifest.snapshotId, canonicalReady: manifest.canonicalReady,
          outcome: validation.outcome, failedRequests,
          provider:coverageDetails.provider,coverage:coverageDetails.coverage,observedCount:coverageDetails.observedCount,
          pagesObserved:coverageDetails.pagesObserved,providerPages:coverageDetails.providerPages,
          providerPagesCompleted:coverageDetails.providerPagesCompleted,fullRefresh:coverageDetails.fullRefresh,
          knownCatalogCompleted:coverageDetails.knownCatalogCompleted,sourceStop:coverageDetails.sourceStop,
          unverifiedQueuedCount:coverageDetails.unverifiedQueuedCount,pendingTransportFailureCount:coverageDetails.pendingTransportFailureCount,
          ...(htmlCoverage ? { coverage: coverageDetails.coverage, observedCount: coverageDetails.observedCount,
            newCount: coverageDetails.newCount, updatedCount: coverageDetails.updatedCount,
            failedCount: coverageDetails.failedCount, requestBudget: coverageDetails.requestBudget,
            stopped: coverageDetails.stopped, apiBusinessRequests: coverageDetails.apiBusinessRequests } : {}) },
      });
      this.appendLog(htmlCoverage
        ? `${coverageSummary}；旧记录全部保留，未观察范围需后续核对。${coverageDetails.stopped ? '本次已停止访问，请查看共享采集状态。' : ''}`
        : validation.outcome === 'partial_update'
          ? `部分更新已切换：${validation.count} 条记录${failedRequests > 0 ? `，${failedRequests} 个原站请求失败` : '，本轮为局部覆盖'}；旧记录全部保留，未完成范围需后续补抓。`
          : `更新成功：${validation.count} 条数据已切换；上一份快照仍保留。`);
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
      await this.releaseCancelledHtmlLock(active);
      if (prepared && (['versions', 'existing'].includes(normalizedOptions.mode)
          || (active.platform === 'mcmod' && ['new', 'trend', 'metrics', 'all'].includes(normalizedOptions.mode)))
          && !active.committed) {
        this.appendLog(`旧包复查未提交；已保留中途结果：${prepared.workspace}。重试前请先核对该目录。`);
      } else if (prepared) {
        await this.store.cleanupWorkspace(prepared.workspace).catch(() => {});
      }
      if (this.active === active) this.active = null;
      if (this.taskPromise && this.taskPromise === active.promise) this.taskPromise = null;
    }
  }

  cancel() {
    const batchRunning=this.batch?.state==='running';
    if(batchRunning)this.batch.cancelled=true;
    if (!this.active) return { cancelled: Boolean(batchRunning), reason: batchRunning?'remaining_batch':'idle' };
    if (this.active.commitStarted) return batchRunning?{cancelled:true,reason:'after_current_commit'}:{ cancelled: false, reason: 'commit_started' };
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
    if(this.batchPromise)await this.batchPromise.catch(()=>{});
  }
}

module.exports = { UpdateManager, validLimit };

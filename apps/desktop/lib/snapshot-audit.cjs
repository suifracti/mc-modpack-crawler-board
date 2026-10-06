const fs = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');
const { ALL_PLATFORMS, readPlatformRecords, normaliseRecord } = require('./platforms.cjs');

const list = (values) => [...new Set((values || []).map(String))].sort();

function versionEvidence(record) {
  const tokens = record.versions.map((value) => `minecraft:${value}`);
  if (record.modpackVersion) tokens.push(`pack:${record.modpackVersion}`);
  const visit = (value) => {
    if (Array.isArray(value)) return value.forEach(visit);
    if (!value || typeof value !== 'object') return;
    for (const [key, item] of Object.entries(value)) {
      if (['id', 'file_id', 'fileId', 'version_number', 'versionName', 'label', 'filename'].includes(key)
          && ['string', 'number'].includes(typeof item) && String(item)) tokens.push(`${key}:${item}`);
      if (['url', 'download_url', 'downloadUrl', 'link'].includes(key)
          && typeof item === 'string' && /^https?:\/\//.test(item)) tokens.push(`link:${item}`);
      if (item && typeof item === 'object') visit(item);
    }
  };
  visit(record.releases);
  visit(record.fileIndexes);
  if (record.mainFileId) tokens.push(`mainFileId:${record.mainFileId}`);
  return list(tokens);
}

function indexRecords(platform, records) {
  const result = new Map();
  records.forEach((raw, index) => {
    const record = normaliseRecord(platform, raw, index);
    if (record.sourceIdOrigin !== 'source') {
      throw new Error(`${platform} 存在缺失的来源ID，无法可靠审计`);
    }
    // The live catalog can move while offset pages are read. Match the first
    // record shown by the workspace; repeated source IDs are not new projects.
    if (result.has(record.id)) return;
    const content = {};
    for (const key of ['title', 'author', 'url', 'summary', 'updatedAt', 'coverUrl']) content[key] = record[key];
    for (const key of ['loaders', 'categories']) content[key] = list(record[key]);
    content.serverStatus = record.environment.status;
    for (const key of ['downloads', 'download_count', 'views', 'view', 'likes', 'favorites', 'follows']) {
      if (raw[key] !== undefined) content[key] = String(raw[key]);
    }
    result.set(record.id, {
      entry: { id: record.id, source_id: record.sourceId, platform, title: record.title, author: record.author, url: record.url },
      content, versions: versionEvidence(record),
    });
  });
  return result;
}

async function buildSnapshotAudit(snapshotsDir, active) {
  const manifests = new Map();
  for (const entry of await fs.readdir(snapshotsDir, { withFileTypes: true })) {
    if (!entry.isDirectory() || entry.name.startsWith('.')) continue;
    try {
      const manifest = JSON.parse(await fs.readFile(path.join(snapshotsDir, entry.name, 'manifest.json'), 'utf8'));
      manifests.set(entry.name, { ...manifest, snapshotId: entry.name });
    } catch { /* An unreadable snapshot is not usable history. */ }
  }
  // Old desktop snapshots predate explicit parent pointers. Their IDs contain
  // creation timestamps; infer only the immediate earlier snapshot, never a
  // newer one. New snapshots always follow their recorded parent instead.
  const ordered = [...manifests.keys()].sort();
  const pairs = new Map();
  const tasks = [];
  const seen = new Set();
  let cursor = active;
  while (cursor?.source === 'desktop-update' && !seen.has(cursor.snapshotId)) {
    seen.add(cursor.snapshotId);
    const explicit = Object.hasOwn(cursor, 'previousSnapshotId');
    const parentId = explicit ? cursor.previousSnapshotId : ordered[ordered.indexOf(cursor.snapshotId) - 1];
    const parent = manifests.get(parentId);
    if (!parent) break;
    const platforms = (cursor.updatedPlatforms || []).filter(p => ALL_PLATFORMS.includes(p));
    tasks.push({ before: parent, after: cursor, platforms });
    for (const platform of cursor.updatedPlatforms || []) {
      if (ALL_PLATFORMS.includes(platform) && !pairs.has(platform)) pairs.set(platform, { before: parent, after: cursor });
    }
    cursor = parent;
  }
  const overview = await auditPairs(snapshotsDir, active, pairs);
  // Persist derived comparisons separately from original snapshots. Keep only
  // their summaries in memory; an unlimited history must not retain every
  // full catalog/diff in the server heap or recompare it on every restart.
  const cacheDir = path.join(path.dirname(snapshotsDir), 'audit-history');
  await fs.mkdir(cacheDir, { recursive: true });
  const loadTask = async (task) => {
    const dependencies = [];
    for (const snapshot of [task.before, task.after]) {
      const dir = path.join(snapshotsDir, snapshot.snapshotId);
      const names = ['manifest.json', 'desktop_update_result.json'];
      for (const name of await fs.readdir(path.join(dir, 'data'))) {
        if (name.endsWith('.js')) names.push(path.join('data', name));
      }
      for (const name of names.sort()) {
        try { const stat = await fs.stat(path.join(dir, name)); dependencies.push([snapshot.snapshotId, name, stat.size, stat.mtimeMs]); }
        catch { dependencies.push([snapshot.snapshotId, name, null]); }
      }
    }
    const fingerprint = crypto.createHash('sha256').update(JSON.stringify({schema:2, platforms:task.platforms, dependencies})).digest('hex');
    const cachePath = path.join(cacheDir, `${task.after.snapshotId}.json`);
    try {
      const cached = JSON.parse(await fs.readFile(cachePath, 'utf8'));
      if (cached.fingerprint === fingerprint && cached.audit?.snapshotId === task.after.snapshotId
          && cached.audit.baselineSnapshotId === task.before.snapshotId) return cached.audit;
    } catch { /* Missing/obsolete cache is rebuilt from original evidence. */ }
    const taskPairs = new Map(task.platforms.map(p => [p, task]));
    const round = await auditPairs(snapshotsDir, task.after, taskPairs, true);
    round.snapshotId = task.after.snapshotId;
    round.baselineSnapshotId = task.before.snapshotId;
    round.scope = 'task';
    const tempPath = `${cachePath}.${crypto.randomUUID()}.tmp`;
    await fs.writeFile(tempPath, JSON.stringify({fingerprint, audit:round}));
    await fs.rename(tempPath, cachePath);
    return round;
  };
  overview.history = [];
  for (const task of tasks) {
    const {added, updated, removed, version_gained, ...summary} = await loadTask(task);
    overview.history.push(summary);
  }
  Object.defineProperty(overview, 'getRound', {value: async (selection) => {
    const task = typeof selection === 'string' ? tasks.find(t => t.after.snapshotId === selection) : tasks[selection];
    return task ? loadTask(task) : null;
  }});
  return overview;
}

async function auditPairs(snapshotsDir, active, pairs, taskOnly = false) {
  const audit = {
    available: pairs.size > 0,
    message: pairs.size ? (taskOnly ? '仅统计该次任务更新的平台，与它紧邻的前置快照对比。' : '对比各平台最近一次更新前后的本地快照。') + '旧记录保留不等于原站下架，采集时间变化不计为内容更新。'
      : '缺少可读取的历史基线快照，不能计算真实变动。',
    generated_at: active.updatedAt || active.createdAt || null,
    scope: taskOnly ? 'task' : 'latest-per-platform',
    stats: { total_current: 0, total_prev: pairs.size ? 0 : null, added_count: 0, updated_count: 0, removed_count: 0, version_gained_count: 0 },
    added: [], updated: [], removed: [], version_gained: [], platform_updates: {}, duplicate_source_ids: {},
  };
  for (const platform of ALL_PLATFORMS) {
    if (taskOnly && !pairs.has(platform)) continue;
    const current = readPlatformRecords(path.join(snapshotsDir, active.snapshotId, 'data'), platform);
    if (current.error) throw new Error(current.error);
    audit.stats.total_current += current.records.length;
    const pair = pairs.get(platform);
    if (!pair) {
      if (audit.stats.total_prev !== null) audit.stats.total_prev += current.records.length;
      continue;
    }
    const before = readPlatformRecords(path.join(snapshotsDir, pair.before.snapshotId, 'data'), platform);
    const after = readPlatformRecords(path.join(snapshotsDir, pair.after.snapshotId, 'data'), platform);
    if (before.error || after.error || !before.sourceFile || !after.sourceFile) {
      // A missing platform input is not evidence of additions or removals.
      throw new Error(`${platform} 的历史或当前来源文件缺失/不可读，不能计算真实变动`);
    }
    audit.stats.total_prev += before.records.length;
    let collection = {};
    try { collection = JSON.parse(await fs.readFile(path.join(snapshotsDir, pair.after.snapshotId, 'desktop_update_result.json'), 'utf8')); } catch { /* Historical runs may not include worker times. */ }
    audit.platform_updates[platform] = {
      snapshotId: pair.after.snapshotId, baselineSnapshotId: pair.before.snapshotId,
      baselineAt: pair.before.updatedAt || pair.before.createdAt || null,
      updatedAt: pair.after.updatedAt || pair.after.createdAt || null,
      startedAt: collection.startedAt || null, finishedAt: collection.finishedAt || null,
      outcome: collection.outcome || pair.after.platform?.outcome || null,
      coverage: collection.crawlerResult?.details?.coverage || null,
    };
    const addedBefore = audit.added.length, updatedBefore = audit.updated.length;
    const removedBefore = audit.removed.length, gainedBefore = audit.version_gained.length;
    const oldRecords = indexRecords(platform, before.records);
    const newRecords = indexRecords(platform, after.records);
    if (oldRecords.size < before.records.length || newRecords.size < after.records.length) {
      audit.duplicate_source_ids[platform] = { before: before.records.length - oldRecords.size, after: after.records.length - newRecords.size };
    }
    for (const [id, record] of newRecords) {
      const old = oldRecords.get(id);
      if (!old) { audit.added.push(record.entry); continue; }
      const changedFields = Object.keys({ ...old.content, ...record.content })
        .filter((key) => JSON.stringify(old.content[key]) !== JSON.stringify(record.content[key]));
      const changes = Object.fromEntries(changedFields.map(key => [key, {before:old.content[key] ?? null, after:record.content[key] ?? null}]));
      if (JSON.stringify(old.versions) !== JSON.stringify(record.versions)) {
        changes.versions = {before:old.versions, after:record.versions};
      }
      const gained = record.versions.filter((value) => !old.versions.includes(value));
      if (gained.length) audit.version_gained.push({ ...record.entry, changedFields, changes, gained });
      else if (changedFields.length || JSON.stringify(old.versions) !== JSON.stringify(record.versions)) {
        audit.updated.push({ ...record.entry, changedFields, changes });
      }
    }
    for (const [id, record] of oldRecords) if (!newRecords.has(id)) audit.removed.push(record.entry);
    audit.platform_updates[platform].stats = {
      total_current: after.records.length, total_prev: before.records.length,
      added_count: audit.added.length - addedBefore, updated_count: audit.updated.length - updatedBefore,
      removed_count: audit.removed.length - removedBefore, version_gained_count: audit.version_gained.length - gainedBefore,
    };
    // Allow other local HTTP requests to run between platforms.
    await new Promise((resolve) => setImmediate(resolve));
  }
  for (const category of ['added', 'updated', 'removed', 'version_gained']) audit.stats[`${category}_count`] = audit[category].length;
  if (Object.keys(audit.duplicate_source_ids).length) audit.message += ' 变动按来源ID去重，当前范围总数仍按原始记录计数。';
  return audit;
}

module.exports = { buildSnapshotAudit };

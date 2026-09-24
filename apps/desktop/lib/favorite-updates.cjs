const fsp = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');
const { assertPlatform } = require('./platforms.cjs');

const FAVORITE_UPDATES_FILE = 'favorite-updates.json';
const SCHEMA = 1;

function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function sourceRecord(record) {
  return isObject(record?.raw) ? record.raw : isObject(record) ? record : {};
}

function text(value) {
  return typeof value === 'string' || typeof value === 'number' ? String(value).trim() : '';
}

function stableId(value) {
  const result = text(value);
  return result && result !== '0' ? result : '';
}

function safeHttpUrl(value) {
  if (typeof value !== 'string' || !value.trim()) return '';
  try {
    const url = new URL(value.trim());
    if (!['http:', 'https:'].includes(url.protocol)) return '';
    return url.toString();
  } catch {
    return '';
  }
}

function releaseSignal(platform, record) {
  const raw = sourceRecord(record);
  if (platform === 'mcmod') {
    const packVersion = text(raw.packVersion);
    return packVersion ? { mode: 'scalar', kind: 'release', entries: [{ key: packVersion, label: packVersion }] } : null;
  }

  if (platform === 'curseforge') {
    const indexes = raw.file_indexes ?? raw.fileIndexes;
    if (!Array.isArray(indexes) || !indexes.length) return null;
    const entries = [];
    for (const item of indexes) {
      if (!isObject(item)) return null;
      const id = stableId(item.file_id ?? item.fileId);
      if (!id) return null;
      const filename = text(item.filename);
      entries.push({ key: id, label: filename ? `#${id} · ${filename}` : `#${id}` });
    }
    return { mode: 'set', kind: 'file-index', entries: uniqueEntries(entries) };
  }

  if (platform === 'bbsmc') {
    const releases = raw.versions_data;
    if (!Array.isArray(releases) || !releases.length) return null;
    const entries = [];
    for (const item of releases) {
      if (!isObject(item)) return null;
      const version = text(item.version_number);
      if (!version) return null;
      entries.push({ key: version, label: version });
    }
    return { mode: 'set', kind: 'release', entries: uniqueEntries(entries) };
  }

  if (platform === 'xyebbs') {
    const releases = raw.releases_data;
    if (!Array.isArray(releases) || !releases.length) return null;
    const entries = [];
    for (const item of releases) {
      if (!isObject(item)) return null;
      const label = text(item.label);
      const createdAt = text(item.create_date ?? item.createDate);
      if (!label || !createdAt || !Number.isFinite(Date.parse(createdAt))) return null;
      entries.push({ key: JSON.stringify([label, createdAt]), label: `${label} · ${createdAt}` });
    }
    return { mode: 'set', kind: 'release', entries: uniqueEntries(entries) };
  }

  // Modrinth's current collector exports project metadata and install links,
  // not a package release list. Bilibili records are keyed by BVID; their
  // changing titles/upload times are not package-version evidence.
  return null;
}

function uniqueEntries(entries) {
  const seen = new Set();
  return entries.filter((item) => {
    if (seen.has(item.key)) return false;
    seen.add(item.key);
    return true;
  });
}

function linkSignal(platform, record) {
  if (!['bilibili', 'bbsmc', 'xyebbs'].includes(platform)) return null;
  const raw = sourceRecord(record);
  if (!Array.isArray(raw.download_links)) return null;
  if (!raw.download_links.length) {
    return platform === 'bilibili' && raw.download_links_observed === true ? [] : null;
  }
  if (platform === 'bilibili' && raw.download_links_observed === false) return null;
  const sourceUrl = safeHttpUrl(text(record?.url) || text(raw.url));
  const urls = [];
  for (const item of raw.download_links) {
    if (!isObject(item)) return null;
    const type = text(item.type).toUpperCase();
    if (type === 'OFFICIAL' || type === 'APP_IMPORT') continue;
    const url = safeHttpUrl(text(item.url));
    if (!url) return null;
    if (url === sourceUrl || url.startsWith('modrinth://')) continue;
    urls.push(url);
  }
  const unique = [...new Set(urls)].sort();
  return unique.length ? unique : null;
}

function splitPersonalKey(key) {
  const split = key.indexOf(':');
  if (split < 1) return null;
  const platform = key.slice(0, split);
  const sourceId = key.slice(split + 1);
  try { assertPlatform(platform); } catch { return null; }
  return sourceId ? { platform, sourceId } : null;
}

function snapshotFor(platform, record) {
  const release = releaseSignal(platform, record);
  const links = linkSignal(platform, record);
  return {
    title: text(record?.title) || '标题未知（本地数据未提供）',
    sourceUrl: safeHttpUrl(text(record?.url) || text(sourceRecord(record).url)),
    release,
    links,
    capabilityKnown: Boolean(release || links),
    reason: release || links ? '' : '来源记录没有可识别的发布版本、文件索引或下载链接字段',
    sampledAt: new Date().toISOString(),
  };
}

function baselineFrom(snapshot) {
  return {
    title: snapshot.title,
    sourceUrl: snapshot.sourceUrl,
    release: snapshot.release ? {
      mode: snapshot.release.mode,
      kind: snapshot.release.kind,
      seen: snapshot.release.entries.map((item) => item.key).sort(),
      lastValue: snapshot.release.mode === 'scalar' ? snapshot.release.entries[0].key : null,
      labels: Object.fromEntries(snapshot.release.entries.map((item) => [item.key, item.label])),
    } : null,
    links: snapshot.links ? [...snapshot.links] : null,
    capabilityKnown: snapshot.capabilityKnown,
    reason: snapshot.reason,
    sampledAt: snapshot.sampledAt,
  };
}

function eventId(platform, sourceId, kind, previousValues, currentValues) {
  const canonical = JSON.stringify([platform, sourceId, kind, previousValues, currentValues]);
  return crypto.createHash('sha256').update(canonical).digest('hex');
}

function makeEvent(platform, sourceId, baseline, kind, previousValues, currentValues, now) {
  let summary;
  if (kind === 'release' && previousValues.length === 1 && currentValues.length === 1 && platform === 'mcmod') {
    summary = `包版本从 ${previousValues[0]} 变为 ${currentValues[0]}`;
  } else if (kind === 'file-index') {
    summary = `发现 ${currentValues.length} 条新的来源文件索引：${currentValues.slice(0, 3).join('；')}`;
  } else if (kind === 'release') {
    summary = `发现 ${currentValues.length} 条新发布记录：${currentValues.slice(0, 3).join('；')}`;
  } else {
    summary = `可识别的下载链接出现变化（当前 ${currentValues.length} 条）`;
  }
  return {
    id: eventId(platform, sourceId, kind, previousValues, currentValues),
    platform,
    sourceId,
    title: baseline.title,
    sourceUrl: baseline.sourceUrl,
    kind,
    summary,
    previousValues,
    currentValues,
    createdAt: now,
    readAt: null,
  };
}

async function writeJsonAtomic(filePath, value) {
  const tempPath = `${filePath}.${process.pid}.${crypto.randomBytes(4).toString('hex')}.tmp`;
  await fsp.writeFile(tempPath, JSON.stringify(value, null, 2), 'utf8');
  await fsp.rename(tempPath, filePath);
}

class FavoriteUpdateTracker {
  constructor(rootDir, { now = () => new Date().toISOString() } = {}) {
    this.rootDir = path.resolve(rootDir);
    this.filePath = path.join(this.rootDir, FAVORITE_UPDATES_FILE);
    this.now = now;
    this.state = { schema: SCHEMA, baselines: {}, events: [] };
    this.writeQueue = Promise.resolve();
  }

  async init() {
    await fsp.mkdir(this.rootDir, { recursive: true });
    try {
      const value = JSON.parse(await fsp.readFile(this.filePath, 'utf8'));
      if (!isObject(value) || value.schema !== SCHEMA || !isObject(value.baselines) || !Array.isArray(value.events)) {
        throw new Error('提醒状态结构无效');
      }
      this.state = { schema: SCHEMA, baselines: value.baselines, events: value.events };
    } catch (error) {
      if (error?.code !== 'ENOENT') throw new Error(`收藏更新提醒读取失败：${error instanceof Error ? error.message : String(error)}`);
    }
    return this.list();
  }

  async mutate(callback) {
    const operation = this.writeQueue.then(async () => {
      const draft = {
        schema: SCHEMA,
        baselines: structuredClone(this.state.baselines),
        events: structuredClone(this.state.events),
      };
      const result = callback(draft);
      await writeJsonAtomic(this.filePath, draft);
      this.state = draft;
      return result;
    });
    this.writeQueue = operation.catch(() => {});
    return operation;
  }

  async seedMissingFavorites(entries, findRecord) {
    const candidates = [];
    for (const [key, status] of Object.entries(entries || {})) {
      if (status?.favorite !== true) continue;
      const identity = splitPersonalKey(key);
      if (!identity) continue;
      const record = await findRecord(identity.platform, identity.sourceId);
      candidates.push({ key, ...identity, record });
    }
    if (!candidates.length) return 0;
    return this.mutate((draft) => {
      let seeded = 0;
      for (const candidate of candidates) {
        if (draft.baselines[candidate.key]) continue;
        if (candidate.record?.sourceIdOrigin === 'index-fallback') continue;
        const snapshot = candidate.record ? snapshotFor(candidate.platform, candidate.record) : {
          title: '标题未知（本地数据未提供）', sourceUrl: '', release: null, links: null,
          capabilityKnown: false, reason: '当前快照未找到此来源记录', sampledAt: this.now(),
        };
        draft.baselines[candidate.key] = baselineFrom({ ...snapshot, sampledAt: this.now() });
        seeded++;
      }
      return seeded;
    });
  }

  async resetFavoriteBaselines(entries, findRecord) {
    const candidates = [];
    for (const [key, status] of Object.entries(entries || {})) {
      if (status?.favorite !== true) continue;
      const identity = splitPersonalKey(key);
      if (!identity) continue;
      const record = await findRecord(identity.platform, identity.sourceId);
      candidates.push({ key, ...identity, record });
    }
    return this.mutate((draft) => {
      const baselines = {};
      for (const candidate of candidates) {
        if (candidate.record?.sourceIdOrigin === 'index-fallback') continue;
        const snapshot = candidate.record ? snapshotFor(candidate.platform, candidate.record) : {
          title: '标题未知（本地数据未提供）', sourceUrl: '', release: null, links: null,
          capabilityKnown: false, reason: '当前快照未找到此来源记录', sampledAt: this.now(),
        };
        baselines[candidate.key] = baselineFrom({ ...snapshot, sampledAt: this.now() });
      }
      draft.baselines = baselines;
      return candidates.length;
    });
  }

  async setFavorite(platform, sourceId, isFavorite, record) {
    const key = `${platform}:${sourceId}`;
    assertPlatform(platform);
    return this.mutate((draft) => {
      if (!isFavorite) {
        delete draft.baselines[key];
        return { seeded: false };
      }
      if (draft.baselines[key]) return { seeded: false };
      if (record?.sourceIdOrigin === 'index-fallback') return { seeded: false };
      const snapshot = record ? snapshotFor(platform, record) : {
        title: '标题未知（本地数据未提供）', sourceUrl: '', release: null, links: null,
        capabilityKnown: false, reason: '当前快照未找到此来源记录', sampledAt: this.now(),
      };
      draft.baselines[key] = baselineFrom({ ...snapshot, sampledAt: this.now() });
      return { seeded: true };
    });
  }

  async processSuccessfulRefresh(platform, entries, findRecord) {
    assertPlatform(platform);
    const candidates = [];
    for (const [key, status] of Object.entries(entries || {})) {
      const identity = splitPersonalKey(key);
      if (!identity || identity.platform !== platform || status?.favorite !== true) continue;
      const record = await findRecord(platform, identity.sourceId);
      candidates.push({ key, ...identity, record });
    }
    if (!candidates.length) return { observed: 0, eventsAdded: 0 };

    return this.mutate((draft) => {
      let eventsAdded = 0;
      for (const candidate of candidates) {
        if (candidate.record?.sourceIdOrigin === 'index-fallback') continue;
        const now = this.now();
        const previous = draft.baselines[candidate.key];
        if (!candidate.record) {
          const prior = previous || baselineFrom({ title: '标题未知（本地数据未提供）', sourceUrl: '', release: null, links: null, capabilityKnown: false, reason: '', sampledAt: now });
          draft.baselines[candidate.key] = { ...prior, capabilityKnown: false, reason: '当前快照未找到此来源记录', sampledAt: now };
          continue;
        }
        const current = snapshotFor(platform, candidate.record);
        if (!previous) {
          draft.baselines[candidate.key] = baselineFrom({ ...current, sampledAt: now });
          continue;
        }

        const next = { ...previous, title: current.title, sourceUrl: current.sourceUrl || previous.sourceUrl, sampledAt: now };
        let comparable = false;
        if (current.release) {
          if (!previous.release || previous.release.mode !== current.release.mode || previous.release.kind !== current.release.kind) {
            next.release = baselineFrom({ ...current, sampledAt: now }).release;
          } else if (current.release.mode === 'scalar') {
            const currentValue = current.release.entries[0]?.key || '';
            const previousValue = previous.release.lastValue || '';
            if (previousValue && currentValue && previousValue !== currentValue) {
              const event = makeEvent(platform, candidate.sourceId, next, current.release.kind, [previousValue], [currentValue], now);
              if (!draft.events.some((item) => item.id === event.id)) { draft.events.push(event); eventsAdded++; }
            }
            next.release = { ...previous.release, lastValue: currentValue, seen: [...new Set([...(previous.release.seen || []), currentValue])].filter(Boolean).sort(), labels: Object.fromEntries(current.release.entries.map((item) => [item.key, item.label])) };
            comparable = true;
          } else {
            const priorSeen = new Set(previous.release.seen || []);
            const added = current.release.entries.filter((item) => !priorSeen.has(item.key));
            const displayAdded = added.map((item) => item.label);
            if (added.length) {
              const event = makeEvent(platform, candidate.sourceId, next, current.release.kind, [], displayAdded, now);
              if (!draft.events.some((item) => item.id === event.id)) { draft.events.push(event); eventsAdded++; }
            }
            next.release = {
              ...previous.release,
              seen: [...new Set([...(previous.release.seen || []), ...current.release.entries.map((item) => item.key)])].sort(),
              labels: { ...(previous.release.labels || {}), ...Object.fromEntries(current.release.entries.map((item) => [item.key, item.label])) },
            };
            comparable = true;
          }
        }

        if (current.links) {
          if (!previous.links) next.links = [...current.links];
          else {
            const priorLinks = [...previous.links].sort();
            const currentLinks = [...current.links].sort();
            if (JSON.stringify(priorLinks) !== JSON.stringify(currentLinks)) {
              const event = makeEvent(platform, candidate.sourceId, next, 'download-links', priorLinks, currentLinks, now);
              if (!draft.events.some((item) => item.id === event.id)) { draft.events.push(event); eventsAdded++; }
            }
            next.links = currentLinks;
            comparable = true;
          }
        }

        next.capabilityKnown = comparable || Boolean(current.release || current.links);
        next.reason = next.capabilityKnown ? '' : current.reason;
        draft.baselines[candidate.key] = next;
      }
      return { observed: candidates.length, eventsAdded };
    });
  }

  async markRead(id) {
    if (typeof id !== 'string' || !/^[a-f0-9]{64}$/.test(id)) return false;
    return this.mutate((draft) => {
      const event = draft.events.find((item) => item.id === id);
      if (!event) return false;
      if (!event.readAt) event.readAt = this.now();
      return true;
    });
  }

  list(entries = {}) {
    const events = [...this.state.events].sort((a, b) => String(b.createdAt).localeCompare(String(a.createdAt)));
    const unknown = [];
    for (const [key, status] of Object.entries(entries)) {
      if (status?.favorite !== true) continue;
      const identity = splitPersonalKey(key);
      if (!identity) continue;
      const baseline = this.state.baselines[key];
      if (baseline?.capabilityKnown) continue;
      unknown.push({
        key,
        platform: identity.platform,
        sourceId: identity.sourceId,
        title: baseline?.title || status.reference?.title || '标题未知（本地数据未提供）',
        sourceUrl: safeHttpUrl(baseline?.sourceUrl || status.reference?.sourceUrl || ''),
        reason: baseline?.reason || '等待一次成功刷新建立基线；当前尚无可识别的发布或下载链接字段',
      });
    }
    return {
      events,
      unreadCount: events.filter((item) => !item.readAt).length,
      unknown,
    };
  }
}

module.exports = {
  FAVORITE_UPDATES_FILE,
  FavoriteUpdateTracker,
  releaseSignal,
  linkSignal,
};

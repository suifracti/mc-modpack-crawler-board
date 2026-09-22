const fsp = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');
const { assertPlatform } = require('./platforms.cjs');

const PERSONAL_LIBRARY_SCHEMA = 2;
const PERSONAL_LIBRARY_FILE = 'personal-library.json';
const MAX_NOTE_LENGTH = 20_000;

function defaultPersonalStatus() {
  return {
    favorite: false,
    wantToPlay: false,
    played: false,
    rating: null,
    note: '',
    updatedAt: null,
  };
}

function personalKey(platform, sourceId) {
  assertPlatform(platform);
  const value = String(sourceId ?? '').trim();
  if (!value || value.length > 256 || value.includes('/') || value.includes('\\') || value.includes('\0')) {
    throw new Error('来源记录标识无效');
  }
  return `${platform}:${value}`;
}

function normaliseStatus(value) {
  const input = value && typeof value === 'object' ? value : {};
  const rating = input.rating === null || input.rating === undefined || input.rating === '' ? null : Number(input.rating);
  return {
    favorite: input.favorite === true,
    wantToPlay: input.wantToPlay === true,
    played: input.played === true,
    rating: Number.isInteger(rating) && rating >= 1 && rating <= 5 ? rating : null,
    note: typeof input.note === 'string' ? input.note.slice(0, MAX_NOTE_LENGTH) : '',
    updatedAt: typeof input.updatedAt === 'string' ? input.updatedAt : null,
    ...(input.reference ? { reference: { ...input.reference } } : {}),
  };
}

function validateBackup(payload) {
  const object = (value) => value !== null && typeof value === 'object' && !Array.isArray(value);
  if (!object(payload) || ![1, 2].includes(payload.schema) || Object.keys(payload).some((key) => !['schema', 'entries'].includes(key)) || !object(payload.entries)) throw new Error('个人资料 schema 或结构无效');
  const entries = new Map();
  for (const [key, value] of Object.entries(payload.entries)) {
    const split = key.indexOf(':');
    const platform = key.slice(0, split);
    const sourceId = key.slice(split + 1);
    if (split < 1 || personalKey(platform, sourceId) !== key) throw new Error('来源 key 无效');
    if (!object(value) || Object.keys(value).some((field) => !['favorite', 'wantToPlay', 'played', 'rating', 'note', 'updatedAt', ...(payload.schema === 2 ? ['reference'] : [])].includes(field))) throw new Error('个人资料包含非法字段');
    for (const field of ['favorite', 'wantToPlay', 'played']) if (typeof value[field] !== 'boolean') throw new Error(`${field} 类型无效`);
    if (value.rating !== null && (!Number.isInteger(value.rating) || value.rating < 1 || value.rating > 5)) throw new Error('rating 无效');
    if (typeof value.note !== 'string' || value.note.length > MAX_NOTE_LENGTH) throw new Error('note 无效');
    if (value.updatedAt !== null && (typeof value.updatedAt !== 'string' || !Number.isFinite(Date.parse(value.updatedAt)))) throw new Error('updatedAt 无效');
    if (value.reference !== undefined) {
      const ref = value.reference;
      if (!object(ref) || Object.keys(ref).some((field) => !['title', 'sourceUrl', 'objectType'].includes(field))) throw new Error('引用字段无效');
      if (ref.title !== undefined && typeof ref.title !== 'string') throw new Error('引用标题无效');
      if (ref.sourceUrl !== undefined && (typeof ref.sourceUrl !== 'string' || !safeSourceUrl(ref.sourceUrl))) throw new Error('引用 URL 无效');
      if (ref.objectType !== (platform === 'bilibili' ? 'bilibili-video' : 'platform-record')) throw new Error('引用对象类型无效');
    }
    entries.set(key, normaliseStatus(value));
  }
  return entries;
}

function safeSourceUrl(value) {
  if (typeof value !== 'string' || !value.trim()) return false;
  try { return ['http:', 'https:'].includes(new URL(value).protocol); } catch { return false; }
}

function validatePatch(patch) {
  if (!patch || typeof patch !== 'object' || Array.isArray(patch)) throw new Error('个人状态必须是 JSON 对象');
  const allowed = new Set(['favorite', 'wantToPlay', 'played', 'rating', 'note']);
  for (const key of Object.keys(patch)) if (!allowed.has(key)) throw new Error(`不支持的个人状态字段: ${key}`);
  if (!Object.keys(patch).length) throw new Error('至少提供一个个人状态字段');
  if ('favorite' in patch && typeof patch.favorite !== 'boolean') throw new Error('favorite 必须是布尔值');
  if ('wantToPlay' in patch && typeof patch.wantToPlay !== 'boolean') throw new Error('wantToPlay 必须是布尔值');
  if ('played' in patch && typeof patch.played !== 'boolean') throw new Error('played 必须是布尔值');
  if ('rating' in patch && patch.rating !== null && (!Number.isInteger(Number(patch.rating)) || Number(patch.rating) < 1 || Number(patch.rating) > 5)) {
    throw new Error('rating 必须是 1 到 5 的整数或 null');
  }
  if ('note' in patch && (typeof patch.note !== 'string' || patch.note.length > MAX_NOTE_LENGTH)) throw new Error(`note 必须是文本且不超过 ${MAX_NOTE_LENGTH} 个字符`);
}

async function writeJsonAtomic(filePath, value) {
  const tempPath = `${filePath}.${process.pid}.${crypto.randomBytes(4).toString('hex')}.tmp`;
  await fsp.writeFile(tempPath, JSON.stringify(value, null, 2), 'utf8');
  await fsp.rename(tempPath, filePath);
}

class PersonalLibrary {
  constructor(rootDir) {
    this.rootDir = path.resolve(rootDir);
    this.filePath = path.join(this.rootDir, PERSONAL_LIBRARY_FILE);
    this.entries = new Map();
    this.writeQueue = Promise.resolve();
  }

  async init() {
    await fsp.mkdir(this.rootDir, { recursive: true });
    try {
      const payload = JSON.parse(await fsp.readFile(this.filePath, 'utf8'));
      this.entries = validateBackup(payload);
    } catch (error) {
      if (error?.code !== 'ENOENT') throw new Error(`个人库读取失败：${error instanceof Error ? error.message : String(error)}`);
    }
    return this.list();
  }

  get(platform, sourceId) {
    return { ...defaultPersonalStatus(), ...(this.entries.get(personalKey(platform, sourceId)) || {}) };
  }

  matches(platform, sourceId, filter) {
    const status = this.get(platform, sourceId);
    if (filter === 'favorite') return status.favorite;
    if (filter === 'want_to_play') return status.wantToPlay;
    if (filter === 'played') return status.played;
    return true;
  }

  async list() {
    const entries = {};
    for (const [key, value] of this.entries) entries[key] = normaliseStatus(value);
    return { schema: PERSONAL_LIBRARY_SCHEMA, entries };
  }

  async restore(payload) {
    let incoming;
    try { incoming = validateBackup(payload); } catch (error) {
      return { restored: 0, 'skipped-conflict': 0, invalid: 1, error: error.message };
    }
    const operation = this.writeQueue.then(async () => {
      const merged = new Map(this.entries);
      let restored = 0;
      let skipped = 0;
      for (const [key, value] of incoming) {
        if (merged.has(key)) skipped++;
        else { merged.set(key, value); restored++; }
      }
      if (restored) {
        await writeJsonAtomic(this.filePath, { schema: PERSONAL_LIBRARY_SCHEMA, entries: Object.fromEntries(merged) });
        this.entries = merged;
      }
      return { restored, 'skipped-conflict': skipped, invalid: 0 };
    });
    this.writeQueue = operation.catch(() => {});
    return operation;
  }

  async update(platform, sourceId, patch, record) {
    const key = personalKey(platform, sourceId);
    validatePatch(patch);
    const operation = this.writeQueue.then(async () => {
      const merged = new Map(this.entries);
      const current = this.get(platform, sourceId);
      const next = normaliseStatus({ ...current, ...patch, updatedAt: new Date().toISOString() });
      if (record) next.reference = {
        ...(typeof record.title === 'string' && record.title.trim() ? { title: record.title } : {}),
        ...(safeSourceUrl(record.url) ? { sourceUrl: record.url } : {}),
        objectType: platform === 'bilibili' ? 'bilibili-video' : 'platform-record',
      };
      if (!next.favorite && !next.wantToPlay && !next.played && next.rating === null && !next.note) {
        merged.delete(key);
      } else {
        merged.set(key, next);
      }
      await writeJsonAtomic(this.filePath, { schema: PERSONAL_LIBRARY_SCHEMA, entries: Object.fromEntries(merged) });
      this.entries = merged;
      return { key, status: this.get(platform, sourceId) };
    });
    this.writeQueue = operation.catch(() => {});
    return operation;
  }
}

module.exports = {
  PERSONAL_LIBRARY_FILE,
  PERSONAL_LIBRARY_SCHEMA,
  PersonalLibrary,
  defaultPersonalStatus,
  personalKey,
};

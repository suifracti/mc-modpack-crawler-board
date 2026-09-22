const fsp = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');
const { assertPlatform } = require('./platforms.cjs');

const PERSONAL_LIBRARY_SCHEMA = 1;
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
  };
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
      const rawEntries = payload && typeof payload === 'object' && payload.entries && typeof payload.entries === 'object' ? payload.entries : {};
      for (const [key, value] of Object.entries(rawEntries)) {
        if (typeof key === 'string' && key.length <= 300) this.entries.set(key, normaliseStatus(value));
      }
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
    for (const [key, value] of this.entries) entries[key] = { ...value };
    return { schema: PERSONAL_LIBRARY_SCHEMA, entries };
  }

  async update(platform, sourceId, patch) {
    const key = personalKey(platform, sourceId);
    validatePatch(patch);
    const operation = this.writeQueue.then(async () => {
      const hadPrevious = this.entries.has(key);
      const previous = this.entries.get(key);
      const current = this.get(platform, sourceId);
      const next = normaliseStatus({ ...current, ...patch, updatedAt: new Date().toISOString() });
      try {
        if (!next.favorite && !next.wantToPlay && !next.played && next.rating === null && !next.note) {
          this.entries.delete(key);
        } else {
          this.entries.set(key, next);
        }
        const payload = await this.list();
        await writeJsonAtomic(this.filePath, payload);
        return { key, status: this.get(platform, sourceId) };
      } catch (error) {
        if (hadPrevious) this.entries.set(key, previous);
        else this.entries.delete(key);
        throw error;
      }
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

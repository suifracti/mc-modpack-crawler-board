const fs = require('node:fs');
const path = require('node:path');

const PLATFORM_CONFIGS = Object.freeze({
  mcmod: {
    id: 'mcmod',
    name: 'MC百科',
    icon: '📦',
    rawFile: 'mcmod_modpacks.json',
    sidecars: ['mcmod_data.js', 'table_rows.js', 'app_data.js'],
  },
  bilibili: {
    id: 'bilibili',
    name: '哔哩哔哩',
    icon: '📺',
    rawFile: 'bilibili_modpacks.json',
    sidecars: ['bili_data.js'],
  },
  bbsmc: {
    id: 'bbsmc',
    name: 'BBSMC',
    icon: '💎',
    rawFile: 'bbsmc_modpacks.json',
    sidecars: ['bbsmc_data.js'],
  },
  xyebbs: {
    id: 'xyebbs',
    name: 'XYEBBS',
    icon: '🍃',
    rawFile: 'xyebbs_modpacks.json',
    sidecars: ['xyebbs_data.js'],
  },
  modrinth: {
    id: 'modrinth',
    name: 'Modrinth',
    icon: '🌐',
    rawFile: 'modrinth_modpacks.json',
    sidecars: ['modrinth_data.js'],
  },
  curseforge: {
    id: 'curseforge',
    name: 'CurseForge',
    icon: '🔥',
    rawFile: 'curseforge_modpacks.json',
    sidecars: ['curseforge_data.js'],
  },
});

const ALL_PLATFORMS = Object.freeze(Object.keys(PLATFORM_CONFIGS));
const COMMON_DATA_FILES = Object.freeze([
  'desc_data.js',
  'audit_diff.js',
]);

function assertPlatform(platform) {
  if (!Object.prototype.hasOwnProperty.call(PLATFORM_CONFIGS, platform)) {
    throw new Error(`不支持的平台: ${String(platform)}`);
  }
  return platform;
}

function findSidecar(dataDir, platform) {
  assertPlatform(platform);
  const config = PLATFORM_CONFIGS[platform];
  for (const filename of config.sidecars) {
    const candidate = path.join(dataDir, filename);
    if (fs.existsSync(candidate)) return candidate;
  }
  return null;
}

function stripJsonAssignment(text) {
  const source = String(text || '').replace(/^\uFEFF/, '').trim();
  const assignment = source.indexOf('=');
  if (assignment < 0) throw new Error('sidecar 缺少 JSON 赋值');
  let json = source.slice(assignment + 1).trim();
  if (json.endsWith(';')) json = json.slice(0, -1).trim();
  return json;
}

function parseSidecarFile(filePath) {
  const stat = fs.statSync(filePath);
  if (stat.size > 256 * 1024 * 1024) {
    throw new Error(`sidecar 过大，拒绝读取: ${path.basename(filePath)}`);
  }
  const json = stripJsonAssignment(fs.readFileSync(filePath, 'utf8'));
  const parsed = JSON.parse(json);
  if (!Array.isArray(parsed) && (parsed === null || typeof parsed !== 'object')) {
    throw new Error(`sidecar 顶层不是数组或对象: ${path.basename(filePath)}`);
  }
  return parsed;
}

function readPlatformRecords(dataDir, platform) {
  const sidecar = findSidecar(dataDir, platform);
  if (!sidecar) return { records: [], sourceFile: null, error: null };
  try {
    const parsed = parseSidecarFile(sidecar);
    const records = Array.isArray(parsed) ? parsed : Object.values(parsed);
    return { records, sourceFile: path.basename(sidecar), error: null };
  } catch (error) {
    return {
      records: [],
      sourceFile: path.basename(sidecar),
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

function firstValue(record, keys) {
  for (const key of keys) {
    const value = record && record[key];
    if (value !== undefined && value !== null && value !== '') return value;
  }
  return null;
}

function asText(value) {
  if (Array.isArray(value)) return value.filter(Boolean).map(String).join('、');
  if (value === undefined || value === null) return '';
  return String(value).trim();
}

function asList(value) {
  if (Array.isArray(value)) return value.filter(Boolean).map(String);
  if (typeof value === 'string' && value.trim()) return value.split(/[,，|/]/).map((item) => item.trim()).filter(Boolean);
  return value ? [String(value)] : [];
}

function normaliseRecord(platform, record, index) {
  const title = asText(firstValue(record, ['title', 'name', 'preferred_title', 'chinese_name', 'project_title'])) || '未命名整合包';
  const author = asText(firstValue(record, ['author', 'uploader', 'creator', 'owner'])) || '未知作者';
  const url = asText(firstValue(record, ['url', 'source_url', 'link', 'homepage']));
  const sourceId = asText(firstValue(record, ['bvid', 'project_id', 'mid', 'id', 'slug', 'source_id'])) || `${platform}-${index + 1}`;
  const versions = asList(firstValue(record, ['all_versions', 'versions', 'mc_versions', 'mc_version']));
  const loaders = asList(firstValue(record, ['loaders', 'loader']));
  const categories = asList(firstValue(record, ['categories', 'tags']));
  const summary = asText(firstValue(record, ['description', 'summary', 'intro', 'pinned_comment']));
  const updatedAt = asText(firstValue(record, ['date_modified', 'modified_at', 'updated_at', 'pubdate', 'published_at', 'date_created']));
  const serverSide = asText(firstValue(record, ['server_side', 'server_support', 'has_server']));
  const evidence = [];
  if (url) evidence.push({ label: '原始来源', value: url });
  if (versions.length) evidence.push({ label: 'Minecraft 版本', value: versions.join('、') });
  if (loaders.length) evidence.push({ label: 'Loader', value: loaders.join('、') });
  if (serverSide) evidence.push({ label: '服务端事实', value: serverSide });
  const sourceMeta = record && record.source_meta;
  if (sourceMeta && typeof sourceMeta === 'object') {
    for (const [key, value] of Object.entries(sourceMeta)) {
      if (value !== undefined && value !== null && value !== '') {
        evidence.push({ label: `来源字段 · ${key}`, value: asText(value) });
      }
    }
  }
  return {
    id: `${platform}:${sourceId}`,
    platform,
    sourceId,
    title,
    author,
    url,
    summary,
    versions,
    loaders,
    categories,
    updatedAt,
    evidence,
  };
}

function isHttpUrl(value) {
  try {
    const parsed = new URL(String(value));
    return parsed.protocol === 'http:' || parsed.protocol === 'https:';
  } catch {
    return false;
  }
}

function redactLogLine(line) {
  return String(line || '')
    .replace(/(cookie|token|authorization|\bSESSDATA\b)\s*[:=]\s*[^\s,;]+/gi, '$1=[已隐藏]')
    .replace(/https?:\/\/[^\s]*[?&](?:token|access_token|auth|cookie)=[^\s&]+/gi, '[已隐藏的受限链接]');
}

module.exports = {
  ALL_PLATFORMS,
  COMMON_DATA_FILES,
  PLATFORM_CONFIGS,
  assertPlatform,
  findSidecar,
  parseSidecarFile,
  readPlatformRecords,
  normaliseRecord,
  isHttpUrl,
  redactLogLine,
};

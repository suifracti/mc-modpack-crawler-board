const https = require('node:https');
const path = require('node:path');
const { execFile } = require('node:child_process');
const { promisify } = require('node:util');

const origins = { bbsmc: 'https://api.bbsmc.net/v2', modrinth: 'https://api.modrinth.com/v2' };
const cache = new Map();
const execFileAsync = promisify(execFile);

async function getMcmodVersions(sourceId) {
  if (!/^\d{1,8}$/.test(String(sourceId))) throw new Error('MC百科整合包编号无效');
  const python = process.env.MC_DESKTOP_PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
  const script = path.join(__dirname, 'read-mcmod-versions.py');
  const { stdout } = await execFileAsync(python, [script, String(sourceId)], {
    cwd: path.resolve(__dirname, '..', '..', '..'),
    windowsHide: true,
    timeout: 18000,
    maxBuffer: 4 * 1024 * 1024,
  });
  const result = JSON.parse(stdout);
  if (!result.checked) throw new Error('MC百科版本页本次未能读取，请稍后重试');
  return { versions: result.versions, fetchedAt: new Date().toISOString() };
}

async function getCurseforgeVersions(sourceId) {
  if (!/^\d+$/.test(String(sourceId))) throw new Error('CurseForge 项目编号无效');
  return new Promise((resolve, reject) => {
    const url = `https://api.curse.tools/v1/mods/${encodeURIComponent(sourceId)}/files?pageSize=50`;
    const request = https.get(url, { headers: { 'User-Agent': 'MCModpackBoard/0.1 (local project reader)', Accept: 'application/json' } }, (response) => {
      if (response.statusCode !== 200) { response.resume(); reject(new Error(`CurseForge 接口返回 HTTP ${response.statusCode}`)); return; }
      const chunks = [];
      let bytes = 0;
      response.on('data', (chunk) => {
        bytes += chunk.length;
        if (bytes > 8 * 1024 * 1024) { response.destroy(new Error('版本资料过大，请在原站查看')); return; }
        chunks.push(chunk);
      });
      response.on('error', reject);
      response.on('end', () => {
        try {
          const payload = JSON.parse(Buffer.concat(chunks).toString('utf8'));
          const files = Array.isArray(payload?.data) ? payload.data : [];
          const versions = files.map((file) => ({
            id: file.id,
            displayName: file.displayName || file.fileName || 'Release',
            fileName: file.fileName || '',
            fileDate: file.fileDate ? String(file.fileDate).slice(0, 10) : '',
            fileLength: file.fileLength || 0,
            releaseType: file.releaseType,
            gameVersions: Array.isArray(file.gameVersions) ? file.gameVersions : [],
            downloadUrl: file.downloadUrl || '',
          }));
          resolve({ versions, fetchedAt: new Date().toISOString() });
        } catch (error) { reject(error); }
      });
    });
    request.setTimeout(12000, () => request.destroy(new Error('CurseForge 在线文件读取超时，请稍后重试')));
    request.on('error', reject);
  });
}

async function getXyebbsVersions(sourceId) {
  if (!/^\d+$/.test(String(sourceId))) throw new Error('XYEBBS 项目编号无效');
  return new Promise((resolve, reject) => {
    const url = `https://resource-api.xyeidc.com/client/resources/${encodeURIComponent(sourceId)}/releases?includes=links`;
    const request = https.get(url, { headers: { 'User-Agent': 'MCModpackBoard/0.1 (local project reader)', Accept: 'application/json' } }, (response) => {
      if (response.statusCode !== 200) { response.resume(); reject(new Error(`XYEBBS 接口返回 HTTP ${response.statusCode}`)); return; }
      const chunks = [];
      let bytes = 0;
      response.on('data', (chunk) => {
        bytes += chunk.length;
        if (bytes > 8 * 1024 * 1024) { response.destroy(new Error('版本资料过大，请在原站查看')); return; }
        chunks.push(chunk);
      });
      response.on('error', reject);
      response.on('end', () => {
        try {
          const payload = JSON.parse(Buffer.concat(chunks).toString('utf8'));
          const inner = payload?.data;
          const releases = Array.isArray(inner) ? inner : (Array.isArray(inner?.data) ? inner.data : []);
          const versions = releases.map((item) => {
            const rawLinks = Array.isArray(item.links) ? item.links : [];
            const downloads = rawLinks.map((link) => {
              const lType = String(link.linkType || link.type || '').toUpperCase();
              const u = String(link.url || '').toLowerCase();
              const defaultName =
                lType.includes('QUARK') || u.includes('quark.cn') ? '夸克网盘' :
                lType.includes('BAIDU') || u.includes('baidu.com') ? '百度网盘' :
                lType.includes('123') || u.includes('123pan') || u.includes('123684') ? '123云盘' :
                lType.includes('LANZOU') || u.includes('lanzou') ? '蓝奏云' :
                lType.includes('XUNLEI') || lType.includes('XUN_LEI') || u.includes('xunlei.com') ? '迅雷网盘' :
                '网盘下载';
              const rawName = String(link.name || '').trim();
              const explicitName = rawName && rawName !== '下载' ? rawName : defaultName;
              return {
                name: explicitName.trim(),
                url: link.url || '',
                code: link.info || link.code || '',
              };
            });
            const vName = item.label || item.name || 'Release';
            const vDate = item.createDate ? String(item.createDate).slice(0, 10) : '';
            return {
              id: item.id,
              label: vName,
              versionName: vName,
              version_number: vName,
              createDate: vDate,
              date: vDate,
              date_published: vDate,
              notes: item.notes || '',
              changelog: item.notes || '',
              changelogMd: item.notes || '',
              downloads,
              links: downloads,
              files: downloads,
            };
          });
          resolve({ versions, fetchedAt: new Date().toISOString() });
        } catch (error) { reject(error); }
      });
    });
    request.setTimeout(12000, () => request.destroy(new Error('XYEBBS 在线版本读取超时，请稍后重试')));
    request.on('error', reject);
  });
}

async function getPreviewVersions(platform, sourceId) {
  if ((!origins[platform] && platform !== 'mcmod' && platform !== 'curseforge' && platform !== 'xyebbs') || !/^[A-Za-z0-9_-]+$/.test(String(sourceId))) throw new Error('该来源不支持在线版本读取');
  const key = `${platform}:${sourceId}`;
  const cached = cache.get(key);
  if (cached && Date.now() - cached.time < 5 * 60 * 1000) return cached.promise;
  const promise = platform === 'mcmod'
    ? getMcmodVersions(sourceId)
    : platform === 'curseforge'
      ? getCurseforgeVersions(sourceId)
      : platform === 'xyebbs'
        ? getXyebbsVersions(sourceId)
        : new Promise((resolve, reject) => {
    const url = `${origins[platform]}/project/${encodeURIComponent(sourceId)}/version`;
    const request = https.get(url, { headers: { 'User-Agent': 'MCModpackBoard/0.1 (local project reader)', Accept: 'application/json' } }, (response) => {
      if (response.statusCode !== 200) { response.resume(); reject(new Error(`版本接口返回 HTTP ${response.statusCode}`)); return; }
      const chunks = [];
      let bytes = 0;
      response.on('data', (chunk) => {
        bytes += chunk.length;
        if (bytes > 8 * 1024 * 1024) { response.destroy(new Error('版本资料过大，请在原站查看')); return; }
        chunks.push(chunk);
      });
      response.on('error', reject);
      response.on('end', () => {
        try {
          const versions = JSON.parse(Buffer.concat(chunks).toString('utf8'));
          if (!Array.isArray(versions)) throw new Error('版本接口未返回列表');
          resolve({ versions, fetchedAt: new Date().toISOString() });
        } catch (error) { reject(error); }
      });
    });
    request.setTimeout(12000, () => request.destroy(new Error('在线版本读取超时，可继续查看本地资料')));
    request.on('error', reject);
  });
  cache.set(key, { time: Date.now(), promise });
  if (cache.size > 100) cache.delete(cache.keys().next().value);
  try { return await promise; } catch (error) { cache.delete(key); throw error; }
}

module.exports = { getPreviewVersions };

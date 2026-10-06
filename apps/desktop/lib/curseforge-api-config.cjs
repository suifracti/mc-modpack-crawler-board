const fs = require('node:fs');

function readCurseforgeApiKey() {
  let key = process.env.CURSEFORGE_API_KEY || process.env.CF_API_KEY || '';
  if (!key && process.env.CURSEFORGE_API_KEY_FILE) {
    let fd;
    try {
      fd = fs.openSync(process.env.CURSEFORGE_API_KEY_FILE, 'r');
      const buffer = Buffer.alloc(4097);
      const size = fs.readSync(fd, buffer, 0, buffer.length, 0);
      if (size > 4096) throw new Error('Key file size limit');
      key = buffer.subarray(0, size).toString('utf8').replace(/^\uFEFF/, '').trim();
    } catch {
      throw new Error('CurseForge API Key文件无法读取或格式无效');
    } finally {
      if (fd !== undefined) fs.closeSync(fd);
    }
  }
  if (!key) throw new Error('CurseForge官方API需要你自己的已获批Key；请配置CURSEFORGE_API_KEY或CURSEFORGE_API_KEY_FILE后重新启动服务。未发起请求。');
  if (!/^[\x21-\x7e]{1,4096}$/.test(key)) throw new Error('CurseForge API Key格式无效');
  return key;
}

function getCurseforgeMetadataProvider() {
  const explicit = (process.env.CURSEFORGE_PROVIDER || '').trim().toLowerCase();
  if (explicit && !['official','cfwidget'].includes(explicit)) throw new Error('CURSEFORGE_PROVIDER必须是official或cfwidget');
  return explicit || (['CURSEFORGE_API_KEY','CF_API_KEY','CURSEFORGE_API_KEY_FILE'].some(name=>process.env[name]) ? 'official' : 'cfwidget');
}

module.exports = { readCurseforgeApiKey, getCurseforgeMetadataProvider };

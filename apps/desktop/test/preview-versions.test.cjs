const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const { getPreviewVersions } = require('../lib/preview-versions.cjs');
const { createBrowserService } = require('../server.cjs');
const https = require('node:https');
const { EventEmitter } = require('node:events');

function request(url) {
  return new Promise((resolve, reject) => {
    const requestUrl = new URL(url);
    const req = http.request({
      hostname: requestUrl.hostname,
      port: requestUrl.port,
      path: `${requestUrl.pathname}${requestUrl.search}`,
      method: 'GET',
    }, (response) => {
      const chunks = [];
      response.on('data', (chunk) => chunks.push(chunk));
      response.on('end', () => resolve({ status: response.statusCode, body: Buffer.concat(chunks).toString('utf8') }));
    });
    req.on('error', reject);
    req.end();
  });
}

test('getPreviewVersions validates platform and sourceId', async () => {
  await assert.rejects(() => getPreviewVersions('unsupported', '123'), /该来源不支持在线版本读取/);
  await assert.rejects(() => getPreviewVersions('curseforge', 'invalid/id'), /该来源不支持在线版本读取/);
  await assert.rejects(() => getPreviewVersions('curseforge', 'notanumber'), /CurseForge 项目编号无效/);
});

test('server routes /api/preview-versions for curseforge', async () => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'mcmod-preview-test-'));
  const dataRoot = path.join(root, 'data');
  await fs.mkdir(dataRoot, { recursive: true });
  const service = createBrowserService({ host: '127.0.0.1', port: 0, dataRoot });
  const started = await service.start();
  try {
    // Non-numeric curseforge id fails with 400 error from handler, confirming route matches
    const res = await request(`${started.url}api/preview-versions/curseforge/invalid_id`);
    assert.equal(res.status, 400);
    const json = JSON.parse(res.body);
    assert.match(json.error, /CurseForge 项目编号无效/);
  } finally {
    await service.stop();
    await fs.rm(root, { recursive: true, force: true });
  }
});

test('CF官方版本读取缺Key不请求，Key仅发官方地址，拒绝后停止', async () => {
  const names=['CURSEFORGE_API_KEY','CF_API_KEY','CURSEFORGE_API_KEY_FILE','CURSEFORGE_PROVIDER'];
  const previous=Object.fromEntries(names.map(name=>[name,process.env[name]]));
  const original=https.get;let calls=0;
  const root=await fs.mkdtemp(path.join(os.tmpdir(),'cf-key-fixture-'));const keyfile=path.join(root,'key.txt');
  try {
    for(const name of names)delete process.env[name];
    process.env.CURSEFORGE_PROVIDER='official';
    https.get=()=>{throw new Error('Unexpected network request');};
    await assert.rejects(()=>getPreviewVersions('curseforge','990001'),/需要你自己的已获批Key/);
    await fs.writeFile(keyfile,'fixture-local-key\n');process.env.CURSEFORGE_API_KEY_FILE=keyfile;
    https.get=(url,options,callback)=>{
      calls++;assert.equal(new URL(url).origin,'https://api.curseforge.com');
      assert.equal(options.headers['x-api-key'],'fixture-local-key');assert(!url.includes('fixture-local-key'));
      const request=new EventEmitter();request.setTimeout=()=>{};
      process.nextTick(()=>{
        const response=new EventEmitter();response.statusCode=calls===1?200:403;response.resume=()=>{};callback(response);
        if(response.statusCode===200){response.emit('data',Buffer.from(JSON.stringify({data:[{id:7,displayName:'Known release',fileDate:'2026-09-01T00:00:00Z',gameVersions:['1.20.1']}]})));response.emit('end');}
      });return request;
    };
    const result=await getPreviewVersions('curseforge','990002');assert.equal(result.versions[0].displayName,'Known release');assert.equal(result.versions[0].fileDate,'2026-09-01');
    await assert.rejects(()=>getPreviewVersions('curseforge','990003'),/HTTP 403/);
    await assert.rejects(()=>getPreviewVersions('curseforge','990004'),/已停止该来源/);
    assert.equal(calls,2);
  } finally {
    https.get=original;for(const name of names){if(previous[name]===undefined)delete process.env[name];else process.env[name]=previous[name];}
    await fs.unlink(keyfile).catch(()=>{});await fs.rmdir(root);
  }
});

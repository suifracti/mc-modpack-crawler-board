const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const zlib = require('node:zlib');
const {execFileSync} = require('node:child_process');

test('Pages export reads the explicitly selected public sidecars and records its source commit', async () => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'mc-pages-export-'));
  const out = path.join(root, 'out'), data = path.join(root, 'source'), archive=path.join(root,'archive');
  await fs.mkdir(out); await fs.mkdir(data);
  await fs.mkdir(path.join(archive,'crawler_output'),{recursive:true});
  await fs.writeFile(path.join(archive,'manifest.json'),JSON.stringify({snapshotId:'fixture',createdAt:'2026-10-06T09:00:00Z'}));
  await fs.writeFile(path.join(archive,'crawler_output/mcmod_details_cache.json'),'{}');
  await fs.writeFile(path.join(out, 'pages.html'), '<!doctype html><title>fixture</title>');
  await fs.writeFile(path.join(data, 'mcmod_data.js'), 'window.mcmodData = [{"mid":"1","title":"fixture","trend_days":["2026-10-05","2026-10-06"],"trend_vals":[10,20]}];');
  const sources = {};
  for (const platform of ['mcmod','bilibili','bbsmc','xyebbs','modrinth','curseforge']) {
    const input = path.join(root, platform+'.json');
    const rows=[{project_id:'1',mid:'1',bvid:'BV1234567890',title:platform+' fixture',url:'https://example.com/'+platform,desc:'正文 /Users/example/notes.txt 公开说明',releases:[{version:'1',changelog:'路径 C:\\Users\\example\\save.zip 公开变更'}]}];
    await fs.writeFile(input, JSON.stringify(rows));
    await fs.writeFile(path.join(archive,'crawler_output',platform+'_modpacks.json'),JSON.stringify(rows));
    sources[platform] = {inputPath:input,status:'partial',finalCount:1,validatedAt:'2026-10-06T09:00:00Z'};
  }
  const report = path.join(root,'refresh.json'); await fs.writeFile(report,JSON.stringify({sources}));
  const sha = 'a'.repeat(40);
  execFileSync(process.execPath,[path.resolve(__dirname,'../../web/scripts/export-pages.cjs')],{env:{...process.env,MC_PAGES_OUT:out,MC_PAGES_REFRESH_REPORT:report,MC_PAGES_SOURCE_DATA_DIR:data,MC_PAGES_SOURCE_COMMIT:sha},stdio:'pipe'});
  const index=JSON.parse(await fs.readFile(path.join(out,'data/mcmod.json')));
  const records=JSON.parse(zlib.gunzipSync(await fs.readFile(path.join(out,'data',index.files[0]))));
  assert.deepEqual(records[0].raw.trend_vals,[10,20]);
  assert.doesNotMatch(records[0].summary,/\/Users\/example/);
  assert.match(records[0].summary,/公开说明/);
  assert.equal(JSON.parse(await fs.readFile(path.join(out,'data/manifest.json'))).sourceCodeSha,sha);
  assert.match(await fs.readFile(path.join(out,'DATA_SCOPE.md'),'utf8'),new RegExp(sha));
  require('../../web/scripts/export-pages-preview.cjs').exportPreviews(out,archive);
  const previews=JSON.parse(await fs.readFile(path.join(out,'data/previews.json')));
  const file=previews.platforms.modrinth['1'];
  const rows=JSON.parse(zlib.gunzipSync(await fs.readFile(path.join(out,'data',file))));
  assert.doesNotMatch(rows['1'].releases[0].changelog,/C:\\Users/);
  assert.match(rows['1'].releases[0].changelog,/公开变更/);
});

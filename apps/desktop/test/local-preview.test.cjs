const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const { DataStore } = require('../lib/data-store.cjs');
const { readLocalPreview } = require('../lib/local-preview.cjs');

test('preview includes source Markdown and HTML images without executing content or losing the stored gallery', async () => {
 const record={platform:'curseforge',sourceId:'2',url:'https://www.curseforge.com/minecraft/modpacks/example',raw:{gallery:['https://media.forgecdn.net/old.png'],description:'正文 ![](https://media.forgecdn.net/new.png){width=500}\n![重复](https://media.forgecdn.net/old.png)\n![恶意](javascript:alert)\n<img src="https://media.forgecdn.net/html.png"><script>throw Error("never execute")</script>'},releases:[]};
 const result=await readLocalPreview('/unused',{},record);
 assert.deepEqual(result.preview.images,['https://media.forgecdn.net/old.png','https://media.forgecdn.net/new.png','https://media.forgecdn.net/html.png']);
 assert.equal(result.preview.description,record.raw.description);
});

test('local preview restores MC text and nine images omitted by sidecar without contacting origin', async t => {
 const root = await fs.mkdtemp(path.join(os.tmpdir(), 'mc-local-preview-'));
 t.after(() => fs.rm(root,{recursive:true,force:true}));
 const source = path.join(root,'source'); await fs.mkdir(source);
 await fs.writeFile(path.join(source,'mcmod_data.js'), 'window.fixture = [{"mid":1261,"title":"虚饰作品","url":"https://www.mcmod.cn/modpack/1261.html"}];');
 const store = new DataStore(path.join(root,'store')); await store.init(); await store.importDirectory(source);
 const active = await store.getActiveSnapshot(); const raw = path.join(store.snapshotsDir, active.snapshotId,'crawler_output');await fs.mkdir(raw,{recursive:true});
 await fs.writeFile(path.join(raw,'mcmod_details_cache.json'),JSON.stringify({'1261':{text:'完整的本地正文',images:Array.from({length:9},(_,i)=>`https://i.mcmod.cn/${i}.webp`)}}));
 assert.equal(typeof store.getRecordPreview,'function','the desktop needs a local archive reader');
 const result = await store.getRecordPreview('mcmod','1261');
 assert.equal(result.preview.description,'完整的本地正文');assert.equal(result.preview.images.length,9);
 assert.equal(result.preview.sourceUrl,'https://www.mcmod.cn/modpack/1261.html');assert.equal(result.provider,'local-snapshot');
 await assert.rejects(()=>store.getRecordPreview('mcmod','../1261'));
});

test('full catalog associations work for other-platform records outside the current UI page and exclude personal fields',()=>{
 const { buildRelations } = require('../../web/scripts/export-pages-relations.cjs');
 assert.equal(typeof buildRelations,'function','relations must be reusable without exporting a website');
 const records=[{id:'mcmod:1',sourceId:'1',platform:'mcmod',title:'虚饰作品 (Fictional)',url:'https://www.mcmod.cn/modpack/1.html',raw:{}},
 {id:'modrinth:far-away',sourceId:'far-away',platform:'modrinth',title:'Fictional',url:'https://modrinth.com/modpack/fictional',raw:{note:'PRIVATE'},personalLibrary:{favorite:true}}];
 const result=buildRelations(records,'2026-10-06');
 assert.equal(result.catalogCount,2);assert.equal(result.links['mcmod:1'][0].id,'modrinth:far-away');
 assert.equal(JSON.stringify(result).includes('PRIVATE'),false);assert.equal(JSON.stringify(result).includes('personalLibrary'),false);
});

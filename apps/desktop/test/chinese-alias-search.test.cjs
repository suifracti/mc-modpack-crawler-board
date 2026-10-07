const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs/promises'),os=require('node:os'),path=require('node:path');
const {DataStore}=require('../lib/data-store.cjs');
const {buildRelations}=require('../../web/scripts/export-pages-relations.cjs');
const rows=[{id:'mcmod:1096',platform:'mcmod',title:'[TF]愚者 (The Fool)',raw:{chinese_name:'[TF]愚者',english_name:'The Fool'}},{id:'curseforge:1265501',platform:'curseforge',title:'The Fool',raw:{slug:'the-fool'}},{id:'curseforge:2',platform:'curseforge',title:'FoolCraft 3',raw:{slug:'foolcraft-3'}}];
test('bilingual aliases include short Chinese names without linking a different English name',()=>{
 const index=buildRelations(rows,'2026-10-06');assert.deepEqual(index.searchAliases['curseforge:1265501'],['愚者']);assert.equal(index.searchAliases['curseforge:2'],undefined);
});
test('local query can search foreign pack by a Chinese name recorded by Chinese sources',async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'mc-alias-'));try{
 const source=path.join(root,'source/data');await fs.mkdir(source,{recursive:true});
 await fs.writeFile(path.join(source,'mcmod_data.js'),'window.mcmodData = '+JSON.stringify([{mid:1096,title:rows[0].title,chineseName:'[TF]愚者',englishName:'The Fool'}])+';');
 await fs.writeFile(path.join(source,'curseforge_data.js'),'window.curseforgeModpacksData = '+JSON.stringify([{project_id:1265501,title:'The Fool',slug:'the-fool'},{project_id:2,title:'FoolCraft 3'}])+';');
 const store=new DataStore(path.join(root,'user'));await store.init();await store.importDirectory(path.join(root,'source'));
 const result=await store.getPlatformRecords('curseforge','愚者');assert.equal(result.total,1);assert.equal(result.records[0].sourceId,'1265501');
 }finally{await fs.rm(root,{recursive:true,force:true});}
});
test('local Bilibili candidates exclude current acquisition bait while retaining complete archives',async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'mc-bili-filter-'));try{
 const source=path.join(root,'source/data');await fs.mkdir(source,{recursive:true});
 const rows=[{bvid:'BV1234567890',title:'MC整合包发布：永生',author:'fixture'},{bvid:'BV0987654321',title:'我的世界怪物大乱斗整合包分享',description_excerpt_observed:true,description_excerpt:'三连+关注后自动发送更多整合包！！！'}];
 await fs.writeFile(path.join(source,'bili_data.js'),'window.biliModpacksData = '+JSON.stringify(rows)+';');
 const store=new DataStore(path.join(root,'user'));await store.init();await store.importDirectory(path.join(root,'source'));
 const candidates=await store.getPlatformRecords('bilibili',{bilibiliContent:'candidates'});assert.equal(candidates.total,1);assert.equal(candidates.records[0].sourceId,rows[0].bvid);
 assert.equal((await store.getPlatformRecords('bilibili',{bilibiliContent:'excluded'})).total,1);assert.equal((await store.getPlatformRecords('bilibili',{bilibiliContent:'all'})).total,2);
 }finally{await fs.rm(root,{recursive:true,force:true});}
});
test('mentioning use in many modpacks does not turn a single mod introduction into a pack recommendation',()=>{
 const {classifyBilibiliContent}=require('../../shared/bilibili-content.cjs');
 const row={title:'各大整合包都加的mod？怎么玩，为什么厉害？我的世界精妙背包mod介绍',raw:{source_tags:['我的世界'],content_policy_schema:7,content_candidate:true}};
 assert.equal(classifyBilibiliContent(row).candidate,false);
});
test('Bilibili release scope separates sharing and reposts before pagination without losing archives',async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'mc-bili-scopes-'));try{
 const source=path.join(root,'source/data');await fs.mkdir(source,{recursive:true});
 const rows=[
  {bvid:'release',title:'MC整合包发布：永生'},
  {bvid:'preview',title:'MC整合包更新预告：永生'},
  {bvid:'sharing',title:'我的世界怪物大乱斗整合包分享 支持手机版',desc:'https://www.mcmod.cn/modpack/123.html'},
  {bvid:'repost',title:'转载 MC整合包发布：星港',desc:'https://www.mcmod.cn/modpack/123.html'},
  {bvid:'recommend',title:'我的世界国外整合包推荐 The Fool',desc:'https://www.curseforge.com/minecraft/modpacks/the-fool'},
  {bvid:'own',title:'MC 我制作的整合包分享：星港'},
  {bvid:'gameplay',title:'MC整合包实况 第2期'},
 ];
 await fs.writeFile(path.join(source,'bili_data.js'),'window.biliModpacksData = '+JSON.stringify(rows)+';');
 const store=new DataStore(path.join(root,'user'));await store.init();await store.importDirectory(path.join(root,'source'));
 const primary=await store.getPlatformRecords('bilibili',{bilibiliContent:'candidates',pageSize:1});
 assert.equal(primary.total,3);assert.equal(primary.records.length,1);
 const secondary=await store.getPlatformRecords('bilibili',{bilibiliContent:'secondary',pageSize:100});
 assert.deepEqual(new Set(secondary.records.map(r=>r.sourceId)),new Set(['sharing','repost','recommend']));
 assert.deepEqual(primary.bilibiliCounts,{all:7,candidates:3,secondary:3,excluded:1});
 assert.equal((await store.getPlatformRecords('bilibili',{bilibiliContent:'all'})).total,7);
 }finally{await fs.rm(root,{recursive:true,force:true});}
});

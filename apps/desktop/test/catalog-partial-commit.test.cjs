const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs/promises'),os=require('node:os'),path=require('node:path');
const {DataStore}=require('../lib/data-store.cjs');
test('complete catalogue partial releases can be committed, but a forged old-ID preservation flag cannot',async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'mc-catalog-partial-'));
 try{
  const source=path.join(root,'source','data');await fs.mkdir(source,{recursive:true});
  await fs.writeFile(path.join(source,'modrinth_data.js'),'window.modrinthModpacksData = [{"project_id":"old","title":"old"}];');
  const store=new DataStore(path.join(root,'user'));await store.init();await store.importDirectory(path.dirname(source));
  const {workspace}=await store.prepareUpdateWorkspace('modrinth');
  const contract={platform:'modrinth',outcome:'partial_update',partialScope:'catalog',previousIdsPreserved:true,collectionResultTouched:true,rawTouched:true,sidecarTouched:true,changed:true,sidecarFile:'modrinth_data.js',crawlerResult:{status:'partial',fetchedCount:2,truncated:false,details:{catalogCompleted:true,versionsChecked:1,sourceStopped:false,versionParseFailures:0}}};
  async function write(rows){await fs.mkdir(path.join(workspace,'build'),{recursive:true});await fs.writeFile(path.join(workspace,'build','desktop_update_result.json'),JSON.stringify(contract));await fs.writeFile(path.join(workspace,'crawler_output','modrinth_modpacks.json'),JSON.stringify(rows));await fs.writeFile(path.join(workspace,'converted_output','data','modrinth_data.js'),'window.modrinthModpacksData = '+JSON.stringify(rows)+';');}
  await write([{project_id:'old',title:'old',latest_version:'0.3'},{project_id:'new',title:'new'}]);
  const validation=await store.validateStage(workspace,'modrinth');assert.equal(validation.outcome,'partial_update');
  contract.crawlerResult.details.sourceStopped=true;await write([{project_id:'old'},{project_id:'new'}]);await assert.rejects(store.validateStage(workspace,'modrinth'),/部分采集/);
  contract.crawlerResult.details.sourceStopped=false;await write([{project_id:'new'},{project_id:'replacement'}]);await assert.rejects(store.validateStage(workspace,'modrinth'),/旧 ID/);
  await write([{project_id:'old',title:'old',latest_version:'0.3'},{project_id:'new',title:'new'}]);await store.commitUpdate(workspace,'modrinth',await store.validateStage(workspace,'modrinth'));assert.equal((await store.findSourceRecord('modrinth','old')).packVersion,'0.3');
 }finally{await fs.rm(root,{recursive:true,force:true});}
});

test('catalogue ID parity rejects empty, duplicate, and differing IDs with a private bounded diagnostic',async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'mc-catalog-id-diagnostic-'));
 try{
  const source=path.join(root,'source','data');await fs.mkdir(source,{recursive:true});
  await fs.writeFile(path.join(source,'modrinth_data.js'),'window.modrinthModpacksData = [{"project_id":"old","title":"old"}];');
  const userRoot=path.join(root,'user'),store=new DataStore(userRoot);await store.init();await store.importDirectory(path.dirname(source));
  const cases=[
   {name:'null-row',raw:[{project_id:'old'},null],sidecar:[{project_id:'old'},null],check:d=>{assert.equal(d.rawFile.emptyIdCount,1);assert.equal(d.sidecarFile.emptyIdCount,1);assert.deepEqual(d.rawFile.emptyRowIndexSamples,[1]);}},
   {name:'empty-id',raw:[{project_id:'old'},{title:'missing'}],sidecar:[{project_id:'old'},{title:'missing'}],check:d=>{assert.equal(d.rawFile.emptyIdCount,1);assert.equal(d.sidecarFile.emptyIdCount,1);}},
   {name:'duplicate-id',raw:[{project_id:'old'},{project_id:'dup'},{project_id:'dup'}],sidecar:[{project_id:'old'},{project_id:'dup'},{project_id:'dup'}],check:d=>{assert.equal(d.rawFile.duplicateRecordCount,1);assert.deepEqual(d.rawFile.duplicateIds,[{id:'dup',count:2}]);}},
   {name:'different-id',raw:[{project_id:'old'},{project_id:'raw-only',title:'PRIVATE_PAGE_TEXT_SENTINEL'}],sidecar:[{project_id:'old'},{project_id:'sidecar-only',description:'PRIVATE_PAGE_TEXT_SENTINEL'}],check:d=>{assert.deepEqual(d.rawOnlyIds,['raw-only']);assert.deepEqual(d.sidecarOnlyIds,['sidecar-only']);}},
  ];
  const diagnostics=path.join(userRoot,'collector-state','update-results');
  for(const item of cases){
   const {workspace}=await store.prepareUpdateWorkspace('modrinth');await fs.mkdir(path.join(workspace,'build'),{recursive:true});
   const contract={platform:'modrinth',outcome:'partial_update',partialScope:'catalog',previousIdsPreserved:true,collectionResultTouched:true,rawTouched:true,sidecarTouched:true,changed:true,sidecarFile:'modrinth_data.js',crawlerResult:{status:'partial',fetchedCount:item.raw.length,truncated:false,details:{catalogCompleted:true,versionsChecked:1,sourceStopped:false,versionParseFailures:0}}};
   await fs.writeFile(path.join(workspace,'build','desktop_update_result.json'),JSON.stringify(contract));
   await fs.writeFile(path.join(workspace,'crawler_output','modrinth_modpacks.json'),JSON.stringify(item.raw));
   await fs.writeFile(path.join(workspace,'converted_output','data','modrinth_data.js'),'window.modrinthModpacksData = '+JSON.stringify(item.sidecar)+';');
   await assert.rejects(store.validateStage(workspace,'modrinth'),/目录局部结果的原始记录与展示记录 ID 不一致/);
   const names=await fs.readdir(diagnostics);assert.equal(names.length,cases.indexOf(item)+1);
   const diagnostic=JSON.parse(await fs.readFile(path.join(diagnostics,names.at(-1)),'utf8'));
   const diagnosticText=JSON.stringify(diagnostic);assert.doesNotMatch(diagnosticText,/PRIVATE_PAGE_TEXT_SENTINEL|description|title|download_links|password|cookie/i);
   assert.equal(diagnostic.phase,'catalog-partial-id-parity');assert.equal(diagnostic.platform,'modrinth');assert.equal(diagnostic.workspaceId,path.basename(workspace));
   assert.equal(diagnostic.rawFile.recordCount,item.raw.length);assert.equal(diagnostic.sidecarFile.recordCount,item.sidecar.length);
   item.check(diagnostic);const mode=(await fs.stat(path.join(diagnostics,names.at(-1)))).mode&0o777;assert.equal(mode,0o600);
  }

  const {workspace}=await store.prepareUpdateWorkspace('modrinth');await fs.mkdir(path.join(workspace,'build'),{recursive:true});
  const contract={platform:'modrinth',outcome:'partial_update',partialScope:'catalog',previousIdsPreserved:true,collectionResultTouched:true,rawTouched:true,sidecarTouched:true,changed:true,sidecarFile:'modrinth_data.js',crawlerResult:{status:'partial',fetchedCount:2,truncated:false,details:{catalogCompleted:true,versionsChecked:1,sourceStopped:false,versionParseFailures:0}}};
  await fs.writeFile(path.join(workspace,'build','desktop_update_result.json'),JSON.stringify(contract));
  await fs.writeFile(path.join(workspace,'crawler_output','modrinth_modpacks.json'),JSON.stringify([{project_id:'old'},{project_id:2}]));
  await fs.writeFile(path.join(workspace,'converted_output','data','modrinth_data.js'),'window.modrinthModpacksData = '+JSON.stringify([{project_id:'old'},{project_id:'2'}])+';');
  assert.equal((await store.validateStage(workspace,'modrinth')).outcome,'partial_update');
 }finally{await fs.rm(root,{recursive:true,force:true});}
});

test('catalogue ID rejection remains primary when private diagnostics cannot be written',async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'mc-catalog-id-diagnostic-blocked-'));
 try{
  const source=path.join(root,'source','data');await fs.mkdir(source,{recursive:true});
  await fs.writeFile(path.join(source,'modrinth_data.js'),'window.modrinthModpacksData = [{"project_id":"old"}];');
  const userRoot=path.join(root,'user'),store=new DataStore(userRoot);await store.init();await store.importDirectory(path.dirname(source));
  const blockedDir=path.join(userRoot,'collector-state','update-results');await fs.mkdir(path.dirname(blockedDir),{recursive:true});await fs.writeFile(blockedDir,'blocked');
  const {workspace}=await store.prepareUpdateWorkspace('modrinth');await fs.mkdir(path.join(workspace,'build'),{recursive:true});
  const contract={platform:'modrinth',outcome:'partial_update',partialScope:'catalog',previousIdsPreserved:true,collectionResultTouched:true,rawTouched:true,sidecarTouched:true,changed:true,sidecarFile:'modrinth_data.js',crawlerResult:{status:'partial',fetchedCount:2,truncated:false,details:{catalogCompleted:true,versionsChecked:1,sourceStopped:false,versionParseFailures:0}}};
  await fs.writeFile(path.join(workspace,'build','desktop_update_result.json'),JSON.stringify(contract));
  await fs.writeFile(path.join(workspace,'crawler_output','modrinth_modpacks.json'),JSON.stringify([{project_id:'old'},{project_id:'raw-only',title:'PRIVATE_PAGE_TEXT_SENTINEL'}]));
  await fs.writeFile(path.join(workspace,'converted_output','data','modrinth_data.js'),'window.modrinthModpacksData = '+JSON.stringify([{project_id:'old'},{project_id:'sidecar-only',description:'PRIVATE_PAGE_TEXT_SENTINEL'}])+';');
  await assert.rejects(store.validateStage(workspace,'modrinth'),error=>error.message==='目录局部结果的原始记录与展示记录 ID 不一致');
  assert.equal((await fs.stat(blockedDir)).isFile(),true);
 }finally{await fs.rm(root,{recursive:true,force:true});}
});

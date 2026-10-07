const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs/promises'),os=require('node:os'),path=require('node:path');
const {saveBrowserCandidates}=require('../lib/bilibili-discovery.cjs');
test('browser candidates survive deduplicated queue updates and require canonical video identity',async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'mc-discovery-'));try{
 const first=await saveBrowserCandidates(root,{text:'https://www.bilibili.com/video/BV1uSYA6GEKi/'});assert.equal(first.total,1);
 const second=await saveBrowserCandidates(root,{text:'BV1uSYA6GEKi\nBV1vDpw6xEDA'});assert.equal(second.total,2);assert.equal(second.added,1);
 const rows=JSON.parse(await fs.readFile(path.join(root,'collector-state/bilibili-browser-discovery.json'),'utf8'));assert.equal(rows.candidates[0].sourceUrl,'https://www.bilibili.com/video/BV1uSYA6GEKi/');
 await assert.rejects(saveBrowserCandidates(root,{text:'https://evil.invalid/video/BV1234567890/'}),/官方/);
 }finally{await fs.rm(root,{recursive:true,force:true});}
});

const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs/promises'),os=require('node:os'),path=require('node:path');
const {createBrowserService}=require('../server.cjs');
test('Bilibili entry opens the fixed official search in the system browser, not an embedded popup',async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'mc-bili-browser-'));const opened=[];
 const service=createBrowserService({host:'127.0.0.1',port:0,dataRoot:root,openBrowser:async url=>{opened.push(url);return {opened:true};}});
 try {const {url}=await service.start();const response=await fetch(url+'api/bilibili/browser',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({url:'https://evil.invalid'})});
 assert.equal(response.status,200);assert.equal((await response.json()).opened,true);assert.deepEqual(opened,['https://search.bilibili.com/all?keyword=MC%E6%95%B4%E5%90%88%E5%8C%85&order=pubdate']);
 }finally{await service.stop();await fs.rm(root,{recursive:true,force:true});}
});

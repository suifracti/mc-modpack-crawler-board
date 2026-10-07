const fs=require('node:fs/promises'),path=require('node:path');
async function saveBrowserCandidates(root, input) {
 const text=String(input?.text || '').trim();if(!text || text.length>64000)throw Error('请粘贴B站官方视频链接或BVID，最多64KB');
 const ids=new Set();
 for(const token of text.split(/\s+/)) {
  if(/^https?:\/\//.test(token)) {
   const url=new URL(token);const match=url.pathname.match(/^\/video\/(BV[0-9A-Za-z]{10})\/?$/);
   if(url.protocol!=='https:' || url.hostname!=='www.bilibili.com' || !match)throw Error('仅接受B站官方公开视频链接或BVID');ids.add(match[1]);
  } else if(/^BV[0-9A-Za-z]{10}$/.test(token))ids.add(token);
 }
 if(!ids.size || ids.size>1000)throw Error('没有有效BVID，或本次超过1000个候选');
 const folder=path.join(root,'collector-state'),file=path.join(folder,'bilibili-browser-discovery.json');await fs.mkdir(folder,{recursive:true});
 const lock=await fs.open(file+'.lock','wx',0o600);
 try {
  let previous={schema:1,candidates:[]};try{previous=JSON.parse(await fs.readFile(file,'utf8'));}catch(error){if(error.code!=='ENOENT')throw error;}
  if(previous.schema!==1 || !Array.isArray(previous.candidates))throw Error('发现队列格式异常，原记录已保留');
  const candidates=new Map(previous.candidates.map(x=>[x.bvid,x]));let added=0;
  for(const bvid of ids)if(!candidates.has(bvid)){candidates.set(bvid,{bvid,sourceUrl:`https://www.bilibili.com/video/${bvid}/`,observedAt:new Date().toISOString(),discoveryKind:'user-official-browser-link'});added++;}
  if(candidates.size>5000)throw Error('发现队列超过5000条；先核验已有候选');
  const temporary=file+'.tmp';await fs.writeFile(temporary,JSON.stringify({schema:1,candidates:[...candidates.values()]},null,2),{mode:0o600});await fs.rename(temporary,file);
  return {added,total:candidates.size,globalDiscoveryAvailable:false};
 }finally{await lock.close();await fs.unlink(file+'.lock');}
}
module.exports={saveBrowserCandidates};

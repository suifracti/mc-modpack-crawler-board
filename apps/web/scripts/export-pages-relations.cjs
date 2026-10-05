// Connect existing public source records. Never merge identities or fetch an external page.
const fs = require('node:fs'), path = require('node:path'), zlib = require('node:zlib');
const { classifyBilibiliContent } = require('../../shared/bilibili-content.cjs');
const platforms = ['mcmod','bilibili','bbsmc','xyebbs','modrinth','curseforge'];
const read = p => JSON.parse(fs.readFileSync(p, 'utf8').replace(/^\uFEFF/, ''));
const normalize = s => String(s || '').normalize('NFKC').toLowerCase().replace(/[^\p{L}\p{N}]/gu, '');
const generic = /^(?:minecraft|modpack|forge|fabric|neoforge|quilt|整合包|我的世界|科技|魔法|生存|冒险|空岛|服务器|汉化|官方|发布|更新|原创|自制|rpg|mc|pvp|rpg整合包|科技整合包|vanilla|lite|extended|survival|adventure|official|notofficial|unofficial|server|client|beta|alpha|hardcore|remastered|reloaded|reborn|汉化版|测试版|正式版|非官方|魔改整合包)$/i;
function aliases(record) {
  const raw = record.raw || {};
  const title = String(record.title || '').replace(/^\[[A-Z0-9]{2,8}\]\s*/, '');
  const values = [title, title.replace(/[（(][^）)]+[）)]/g, '').trim(), raw.english_name, raw.chinese_name];
  // A slug alone is insufficient: unrelated uploads can reuse another pack's slug.
  if (raw.slug && normalize(title).includes(normalize(raw.slug))) values.push(raw.slug.replace(/[-_]/g, ' '));
  if (/\p{Script=Han}/u.test(title)) values.push(...title.split(/\s[-–—]\s/).filter(v=>/[a-z]{3}/i.test(v)));
  for (const match of title.matchAll(/[（(]([^）)]+)[）)]/g)) values.push(match[1]);
  const commonMods = new Set(['tacz','create','机械动力','冰火传说','宝可梦','cobblemon','pixelmon','ftb']);
  return [...new Set(values.filter(v => typeof v === 'string').map(normalize).filter(v => v.length >= (/\p{Script=Han}/u.test(v) ? 3 : 4) && !generic.test(v) && !commonMods.has(v) && !/^[0-9]+$/.test(v)))];
}
function exportRelations(out) {
  const records = platforms.flatMap(platform => read(path.join(out,'data',platform+'.json')).files.flatMap(file => {
    const bytes = fs.readFileSync(path.join(out,'data',file));
    return JSON.parse(bytes[0] === 31 && bytes[1] === 139 ? zlib.gunzipSync(bytes) : bytes);
  }));
  const byId = new Map(records.map(row => [row.id,row]));
  const aliasMap = new Map(), edges = new Map(), reasons = new Map();
  const add = (a,b,reason) => {
    if (a === b || byId.get(a).platform === byId.get(b).platform) return;
    for (const [from,to] of [[a,b],[b,a]]) { if (!edges.has(from)) edges.set(from,new Set()); edges.get(from).add(to); reasons.set(from+'|'+to,reason); }
  };
  for (const row of records.filter(r=>r.platform!=='bilibili')) for (const name of aliases(row)) {
    if (!aliasMap.has(name)) aliasMap.set(name,[]); aliasMap.get(name).push(row.id);
  }
  for (const [alias, ids] of aliasMap) if (ids.length <= 40) for (let i=0;i<ids.length;i++) for(let j=i+1;j<ids.length;j++) add(ids[i],ids[j], '完整名称或收录别名相同：'+alias);
  const sourceUrls = new Map(records.filter(r=>r.platform!=='bilibili').map(r=>[String(r.url).replace(/\/$/,''),r.id]));
  const biliCounts = {};
  for (const row of records.filter(r=>r.platform==='bilibili')) {
    const quality=classifyBilibiliContent(row); biliCounts[quality.kind]=(biliCounts[quality.kind]||0)+1;
    if(!quality.candidate) continue;
    const title=normalize(row.title);
    for (const [alias,ids] of aliasMap) {
      if (ids.length>40 || !title.includes(alias)) continue;
      const at=title.indexOf(alias), before=title[at-1]||'', after=title[at+alias.length]||'';
      if (!/\p{Script=Han}/u.test(alias) && (/[a-z0-9]/i.test(before) || /[a-z0-9]/i.test(after))) continue;
      if (/\d$/.test(alias) && /\d/.test(after)) continue;
      for (const id of ids) add(row.id,id,'发布/介绍视频标题包含收录名称：'+alias);
    }
    for (const url of String(row.raw?.desc || row.summary || '').match(/https?:\/\/[^\s<>"'，。；）】]+/g)||[]) {
      const id=sourceUrls.get(url.replace(/\/$/,''));if(id) add(row.id,id,'公开简介指向该原站条目');
    }
  }
  const index={schema:1, catalogCount:records.length, dataTime:read(path.join(out,'data/manifest.json')).updatedAt, records:{}, links:{}};
  for (const [id,targets] of edges) {
    index.links[id]=[...targets].sort().slice(0,80).map(target=>({id:target,reason:reasons.get(id+'|'+target)}));
    for (const target of [id,...targets]) if (!index.records[target]) {
      const row=byId.get(target); index.records[target]={id:row.id,platform:row.platform,sourceId:row.sourceId,title:row.title,url:row.url,author:row.author,packVersion:row.packVersion};
    }
  }
  const files=['data/relations.json.gz'];
  fs.writeFileSync(path.join(out,files[0]),zlib.gzipSync(JSON.stringify(index),{level:9}));
  const report={files,catalogCount:records.length,linkedRecords:edges.size,links:[...edges.values()].reduce((n,s)=>n+s.size,0)/2,biliCounts};
  fs.writeFileSync(path.join(out,'relations-export.json'),JSON.stringify(report,null,2));return report;
}
module.exports={exportRelations,aliases,normalize};
if(require.main===module){if(!process.env.MC_PAGES_OUT)throw Error('MC_PAGES_OUT required');console.log(JSON.stringify(exportRelations(process.env.MC_PAGES_OUT)));}

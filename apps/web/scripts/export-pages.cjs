// Read public crawler outputs only; never instantiate DataStore or read user library/config.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {scrubLocalText}=require('./public-data-redaction.cjs');
const repo=path.resolve(__dirname,'../../..');
const out=path.resolve(process.env.MC_PAGES_OUT || path.join(repo,'build/pages'));
const sourceCommit=process.env.MC_PAGES_SOURCE_COMMIT || null;
if(sourceCommit && !/^[0-9a-f]{40}$/.test(sourceCommit))throw Error('Invalid source commit');
const refresh=process.env.MC_PAGES_REFRESH_REPORT ? JSON.parse(fs.readFileSync(process.env.MC_PAGES_REFRESH_REPORT,'utf8')) : null;
// Explicit public cover metadata supplements missing fields without opening a DataStore.
const mcCovers=new Map();
if(process.env.MC_PAGES_MCMOD_COVERS){
  const covers=JSON.parse(fs.readFileSync(process.env.MC_PAGES_MCMOD_COVERS,'utf8'));
  if(!Array.isArray(covers))throw Error('MC cover supplement must be an array');
  for(const item of covers){
    const id=String(item.mid || ''),cover=String(item.cover_url || '').trim();
    const url=new URL(cover);
    if(!/^\d+$/.test(id)||mcCovers.has(id)||!['https:','http:'].includes(url.protocol)||url.hostname!=='i.mcmod.cn'||!/^\/(?:modpack|class)\/cover\//.test(url.pathname))throw Error('Invalid public MC cover supplement');
    mcCovers.set(id,cover);
  }
}
const {normaliseRecord,readPlatformRecords,ALL_PLATFORMS,PLATFORM_CONFIGS}=require(path.join(repo,'apps/desktop/lib/platforms.cjs'));
const allowed=new Set(`id mid project_id source_id slug title title_cn title_en name author uploader creator owner url source_url link homepage description summary intro desc pinned_comment all_versions allVersions mc_versions mcVersions mc_version versions loaders loader categories tags coverUrl cover cover_url icon_url logo_url pic head_url has_server client_side server_side clientSide serverSide modifiedAt date_modified modified_at updated_at publishedAt published_at pubdate pub_time pub_timestamp modified_timestamp date_modified_timestamp date_created created_timestamp updatedAt published_at release_date last_update_date pack_version latest_version download_links downloads followers views likes coins favorites favourite favorites share reply danmaku comments commentsCount score recommend red_votes red_percent black_votes black_percent votes recommendations releases versions_data releases_data file_indexes main_file_id gallery featured_gallery mod_count modCount mods includedModsCount included_mods_count includedModNames included_mod_names modCategories includedMods type_name typeName formerTitles former_titles trend_dates trend_days trend_latest trend_vals trendStats trend_stats bvid aid cid duration extract_code qq_group subtitle_summary subtitle_text has_subtitle has_group_version group_version_note desc_updated_at desc_checked_at source_html_checked_at source_kind source_html_sha256 source_html_observed_fields description_download_links_observed description_excerpt description_excerpt_truncated description_excerpt_observed description_source_sha256 source_observed_at source_field_provenance source_tags classification_basis content_category content_candidate content_reason content_policy_schema catalogue_entry_kind pack_first_release_verified publication_time_provenance acquisition_note desc_observed pinned_comment_observed subtitle_observed download_links_observed source_unavailable preferred_title chinese_name project_title c0`.split(/\s+/));
allowed.add('english_name'); // Existing XYEBBS names are needed by the V2 association engine.
const forbidden=/^(?:password|passwd|secret|cookie|token|access_token|authorization|session|sessdata|credential|api_?key|private_?key|user_?notes|personal|dataRoot|sourceFile|local_?path|file_?path|directory|source_meta|sourceMeta)$/i;
let redactions=0;
function decodePublicTitle(value){
  return typeof value !== 'string' ? value : value.replace(/&(?:#x([0-9a-f]+)|#([0-9]+)|(amp|quot|apos|lt|gt));/gi, (entity,hex,decimal,named)=>{
    if(named)return {amp:'&',quot:'"',apos:"'",lt:'<',gt:'>'}[named.toLowerCase()];
    const code=parseInt(hex || decimal,hex ? 16 : 10);
    return Number.isFinite(code) && code>0 && code<=0x10ffff ? String.fromCodePoint(code) : entity;
  });
}
function clean(value){
  if(typeof value==='string'){
    const scrubbed=scrubLocalText(value);
    if(scrubbed!==value){redactions++;value=scrubbed;}
    if(/(?:(?:^|[\s"'(])[A-Za-z]:[\\/]|file:\/\/|(?:https?:\/\/)?(?:localhost|127\.0\.0\.1)(?::|\/)|[?&](?:token|access_token|auth|authorization|signature|api_key|credential)=)/i.test(value)){redactions++;return '';}
    return value;
  }
  if(Array.isArray(value))return value.map(clean);
  if(value && typeof value==='object')return Object.fromEntries(Object.entries(value).filter(([key])=>!forbidden.test(key)).map(([key,v])=>[key,clean(v)]));
  return value;
}
fs.mkdirSync(path.join(out,'data'),{recursive:true});
const manifest={hasData:true,snapshotId:'public-crawler-export',sourceCodeSha:sourceCommit,updatedAt:null,source:'static-public',canonicalReady:false,platforms:{},sourceTimes:{},sourceRefresh:{},recordCount:0};
const mcDetails=readPlatformRecords(path.resolve(process.env.MC_PAGES_SOURCE_DATA_DIR || path.join(repo,'converted_output','data')),'mcmod').records;
const mcById=new Map(mcDetails.map(v=>[String(v.mid||v.id||v.project_id),v]));
for(const platform of ALL_PLATFORMS){
  const result=refresh?.sources?.[platform];
  const input=result?.inputPath || path.join(repo,'crawler_output',PLATFORM_CONFIGS[platform].rawFile);
  if(result && !['success','partial','retained-old','recovered-existing-local-snapshot'].includes(result.status))throw Error(`Unvalidated refresh: ${platform}`);
  if(result?.dataSha256 && crypto.createHash('sha256').update(fs.readFileSync(input)).digest('hex')!==result.dataSha256)throw Error(`Refresh input changed: ${platform}`);
  const source=JSON.parse(fs.readFileSync(input,'utf8'));
  if(!Array.isArray(source)||!source.length)throw Error(`Incomplete platform: ${platform}`);
  if(result && source.length!==result.finalCount)throw Error(`Refresh count mismatch: ${platform}`);
  const records=source.map((raw,index)=>{
    // MC structured display fields supplement raw source; original raw fields win.
    const combined=platform==='mcmod'?{...mcById.get(String(raw.mid||raw.project_id)),...raw}:raw;
    const displayExtras=new Set(['chineseName','englishName','previewMods','environmentClaims','trendPoints','modCategorySearch','moldId','packVersion','version_count']);
    const publicRaw=clean(Object.fromEntries(Object.entries(combined).filter(([key])=>allowed.has(key)||displayExtras.has(key))));
    if(platform==='mcmod' && !['coverUrl','cover','icon_url','logo_url','cover_url'].some(key=>String(publicRaw[key] || '').trim())){
      const cover=mcCovers.get(String(raw.mid || raw.project_id));
      if(cover)publicRaw.cover_url=cover;
    }
    if(publicRaw.title)publicRaw.title=decodePublicTitle(publicRaw.title);
    const derivedBiliSource=platform==='bilibili' && !publicRaw.url && /^BV[A-Za-z0-9]{10}$/.test(String(publicRaw.bvid || ''));
    if(platform==='bilibili'){
      publicRaw.cover_url=publicRaw.pic;
      if(derivedBiliSource)publicRaw.url=`https://www.bilibili.com/video/${publicRaw.bvid}`;
    }
    const record=normaliseRecord(platform,publicRaw,index);
    if(derivedBiliSource)record.evidence.push({label:'来源链接依据',value:'由已抓取的来源 BVID 构造；未联网核验'});
    if(platform==='bilibili' && !record.summary && publicRaw.description_excerpt){
      record.summary=`简介摘录${publicRaw.description_excerpt_truncated ? '（已截断，非完整简介）' : '（仅保留短文，非完整简介）'}：${publicRaw.description_excerpt}`;
    }
    if(platform==='bilibili' && publicRaw.pack_first_release_verified===false){
      record.evidence.push({label:'发布含义',value:'此日期为官方视频发布日期；包本体首次发布时间及是否新版本尚未核验'});
      if(publicRaw.source_observed_at)record.evidence.push({label:'官方网页核查时间',value:String(publicRaw.source_observed_at)});
    }
    delete record.searchDocument;
    return clean(record);
  });
  const files=[];
  for(let offset=0;offset<records.length;offset+=3000){
    const filename=`${platform}-${Math.floor(offset/3000)+1}.json`;
    fs.writeFileSync(path.join(out,'data',filename+'.gz'),require('node:zlib').gzipSync(JSON.stringify(records.slice(offset,offset+3000)),{level:9}));
    files.push(filename+'.gz');
  }
  fs.writeFileSync(path.join(out,'data',`${platform}.json`),JSON.stringify({files}));
  const date=result ? (result.status==='retained-old' ? result.baseSourceFileTime : result.validatedAt) : fs.statSync(input).mtime.toISOString();
  if(result)manifest.sourceRefresh[platform]={status:result.status,coverage:result.coverage,new:result.new,updated:result.updated,failedRequests:result.failedRequests,validationFailures:result.validationFailures || 0,baseSourceFileTime:result.baseSourceFileTime,checkedAt:result.finishedAt,reason:result.reason || null,...(result.status==='recovered-existing-local-snapshot' ? {knownUnavailableCount:result.knownUnavailableCount,unverifiedCount:result.unverifiedCount,lastObservedAt:result.validatedAt,...(result.htmlRefresh ? {htmlRefresh:result.htmlRefresh} : {})} : {})};
  if(result?.htmlRefresh)manifest.sourceRefresh[platform].htmlRefresh=clean(result.htmlRefresh);
  if(result && platform==='bilibili'){
    manifest.sourceRefresh[platform].historicalSourceTime=result.historicalSourceTime || result.baseSourceFileTime;
    for(const key of ['currentBatchDateLocal','apiBusinessRequests','dailyCandidatesUsed'])if(result[key]!==undefined)manifest.sourceRefresh[platform][key]=result[key];
  }
  manifest.sourceTimes[platform]=date;
  manifest.platforms[platform]={id:platform,name:PLATFORM_CONFIGS[platform].name,icon:PLATFORM_CONFIGS[platform].icon,count:records.length,sourceFile:null,error:null,available:true};
  manifest.recordCount+=records.length;
  if(!manifest.updatedAt||date>manifest.updatedAt)manifest.updatedAt=date;
}
fs.writeFileSync(path.join(out,'data/manifest.json'),JSON.stringify(manifest));
fs.writeFileSync(path.join(out,'.nojekyll'),'');
fs.writeFileSync(path.join(out,'DATA_SCOPE.md'),`# 公开采集数据\n\n最新桌面界面 ${sourceCommit || 'unknown'}，六平台 ${manifest.recordCount} 条。\n\n${Object.entries(manifest.sourceTimes).map(([p,t])=>`- ${p}: 源文件更新时间 ${t}`).join('\n')}\n\n${refresh ? '本轮为隔离增量刷新；成功源显示验证时间，保留旧源仍显示原文件时间。更新计数为展示字段发生变化，不代表整合包版本发布。' : '时间来自现有采集文件的修改时间，不保证同一批次或即时数据。'}${refresh ? '\n\n'+Object.entries(manifest.sourceRefresh).map(([p,v])=>`- ${p}: ${v.status}; 范围 ${v.coverage}; 新增 ${v.new}; 展示字段更新 ${v.updated}; 请求失败 ${v.failedRequests}; 范围验证失败 ${v.validationFailures}; 原数据时间 ${v.baseSourceFileTime}`).join('\n') : ''}仅公开来源展示字段；不包含个人资料、配置、凭据、session、日志、本地路径和运行快照。个人收藏仅在访问者自己的浏览器保存。静态站不执行爬虫、服务、代理和快照管理；原站小窗转为外链打开。\n`);
fs.writeFileSync(path.join(out,'data-report.json'),JSON.stringify({manifest,redactedValues:redactions,dataBytes:fs.readdirSync(path.join(out,'data')).reduce((n,f)=>n+fs.statSync(path.join(out,'data',f)).size,0)},null,2));
console.log(JSON.stringify({records:manifest.recordCount,platforms:Object.fromEntries(Object.entries(manifest.platforms).map(([p,v])=>[p,v.count])),sourceTimes:manifest.sourceTimes,redactedValues:redactions}));

fs.copyFileSync(path.join(out,'pages.html'),path.join(out,'index.html'));
const html=fs.readFileSync(path.join(out,'index.html'),'utf8');
const viteManifestPath=path.join(out,'.vite','manifest.json');
const viteAssets=fs.existsSync(viteManifestPath) ? Object.values(JSON.parse(fs.readFileSync(viteManifestPath,'utf8'))).flatMap(entry=>[entry.file,...(entry.css || []),...(entry.assets || [])]) : [];
const assets=[...new Set([...html.matchAll(/(?:src|href)="\.\/(assets\/[^"\s]+)"/g)].map(match=>match[1]).concat(viteAssets.filter(name=>/^assets\/[^/]+\.(?:js|css|svg|ico|png)$/.test(name))))];
const dataFiles=['data/manifest.json',...ALL_PLATFORMS.flatMap(p=>[
  `data/${p}.json`,...JSON.parse(fs.readFileSync(path.join(out,'data',`${p}.json`),'utf8')).files.map(f=>`data/${f}`)
])];
let previewFiles;
if(process.env.MC_PAGES_PREVIEW_ARCHIVE_ROOT){
  previewFiles=require('./export-pages-preview.cjs').exportPreviews(out,process.env.MC_PAGES_PREVIEW_ARCHIVE_ROOT).files;
}else{
  fs.writeFileSync(path.join(out,'data','previews.json'),JSON.stringify({schema:1,platforms:{}}));
  previewFiles=['data/previews.json'];
}
const relationFiles=require('./export-pages-relations.cjs').exportRelations(out).files;
const files=['index.html','.nojekyll','DATA_SCOPE.md',...assets,...dataFiles,...previewFiles,...relationFiles].map(name=>{
  const file=path.join(out,name),stat=fs.lstatSync(file);
  if(!stat.isFile()||stat.isSymbolicLink())throw Error('Unsafe publication file');
  return {path:name,bytes:stat.size,sha256:crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')};
});
fs.writeFileSync(path.join(out,'publication-manifest.json'),JSON.stringify({repository:'suifracti/mc-modpack-crawler-board',branch:'gh-pages',files,bytes:files.reduce((n,f)=>n+f.bytes,0)},null,2));

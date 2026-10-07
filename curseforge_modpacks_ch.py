"""Public third-party CurseForge modpack catalogue. No keys, downloads or fallback.

A completed walk means the provider's returned pages, not all CurseForge projects.
Existing IDs and richer original-source data always survive a bounded observation.
"""
import copy,hashlib,json,os,re,tempfile,time,urllib.request,urllib.error,urllib.robotparser
from html import unescape
from datetime import datetime,timezone
from pathlib import Path
from desktop_collection_contract import write_collection_result
from verified_tls import create_verified_context
ORIGIN='https://api.modpacks.ch'
UA='MCModpackCrawlerDashboard/1.0'
MAX_BYTES=8*1024*1024
class CatalogRefusal(RuntimeError):pass
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args):raise CatalogRefusal('Public catalogue redirect refused')
class PublicCatalogTransport:
 def __init__(self):self.opener=urllib.request.build_opener(NoRedirect(),urllib.request.HTTPSHandler(context=create_verified_context()));self.policy=None;self.last=0;self.stopped=None;self.request_count=0
 def read(self,route):
  if self.stopped:raise CatalogRefusal(self.stopped)
  time.sleep(max(0,1-(time.monotonic()-self.last)));self.last=time.monotonic()
  self.request_count+=1
  req=urllib.request.Request(ORIGIN+route,headers={'User-Agent':UA,'Accept':'application/json' if route!='/robots.txt' else 'text/plain'})
  try:
   with self.opener.open(req,timeout=20) as r:status,body=r.status,r.read(MAX_BYTES+1)
  except urllib.error.HTTPError as e:
   status,body=e.code,e.read(MAX_BYTES+1);e.close()
  if len(body)>MAX_BYTES:raise CatalogRefusal('Public catalogue response too large')
  if status in (401,403,412,429) or 300<=status<400:raise CatalogRefusal(f'Public catalogue HTTP {status}; stopped without retry')
  return status,body
 def get(self,route):
  if not re.fullmatch(r'/public/curseforge/(?:browse/updated(?:/\d+)?|\d+)',route):raise ValueError('Outside public catalogue metadata scope')
  try:
   if self.policy is None:
    status,body=self.read('/robots.txt')
    if status not in (200,404,410):raise CatalogRefusal('Unverifiable public catalogue robots')
    self.policy=urllib.robotparser.RobotFileParser()
    if status==200 and (b'<html' in body.lower() or b'user-agent:' not in body.lower()):raise CatalogRefusal('Unverifiable robots response')
    self.policy.parse(body.decode('utf-8-sig').splitlines() if status==200 else [])
   if not self.policy.can_fetch(UA,ORIGIN+route):raise CatalogRefusal('Public catalogue robots denied')
   status,body=self.read(route)
   if status!=200:raise CatalogRefusal(f'Public catalogue HTTP {status}; source stopped')
   if body.lstrip().startswith(b'<'):raise CatalogRefusal('Public catalogue returned HTML/access gate')
   value=json.loads(body)
   if not isinstance(value,dict) or value.get('status')!='success':raise CatalogRefusal('Public catalogue invalid status')
   return value,{'provider':'modpacks-ch','sourceUrl':ORIGIN+route,'observedAt':datetime.now(timezone.utc).isoformat(),'providerRefreshedAt':value.get('refreshed'),'sha256':hashlib.sha256(body).hexdigest()}
  except (CatalogRefusal,ValueError,OSError) as e:self.stopped=str(e);raise CatalogRefusal(self.stopped) from None

def stamp(value):
 if type(value) not in (int,float) or value<=0:return None
 return datetime.fromtimestamp(value,timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
def merge_pack(pack,old,observation):
 if (not isinstance(pack,dict) or pack.get('provider')!='curseforge' or type(pack.get('id')) is not int or pack['id']<1 or not isinstance(pack.get('name'),str) or not pack['name'].strip()):raise ValueError('Third-party identity/provider mismatch')
 ident=str(pack['id']);row=copy.deepcopy(old or {'platform':'curseforge','project_id':ident,'releases':[],'gallery':[],'loaders':[],'all_versions':[]})
 if old and str(old.get('project_id'))!=ident:raise ValueError('Existing identity mismatch')
 original=next((x.get('link') for x in pack.get('links') or [] if isinstance(x,dict) and re.fullmatch(r'https://www\.curseforge\.com/minecraft/modpacks/[A-Za-z0-9_-]+/?',str(x.get('link') or ''))),None)
 if not row.get('url') and not original:raise ValueError('New ID lacks verified original project URL')
 row['url']=row.get('url') or original
 newer=not row.get('date_modified') or (stamp(pack.get('updated')) or '')>=str(row.get('date_modified'))
 if newer:
  row['title']=pack['name'];row['author']=', '.join(str(x['name']) for x in pack.get('authors') or [] if isinstance(x,dict) and x.get('name')) or row.get('author','未知')
  if stamp(pack.get('updated')):row['date_modified']=stamp(pack['updated'])
 prior=(old or {}).get('catalog_observation',{})
 detail_description=pack.get('description') if isinstance(pack.get('description'),str) else ''
 owned_body=bool(prior.get('descriptionSha256') and prior['descriptionSha256']==hashlib.sha256(str(row.get('description') or '').encode()).hexdigest())
 if not row.get('description') or (detail_description and (owned_body or row.get('description')==prior.get('synopsis'))):
  row['description']=detail_description or pack.get('synopsis') or ''
 row['downloads']=max(int(row.get('downloads') or 0),int(pack.get('installs') or 0))
 arts=[a.get('url') for a in pack.get('art') or [] if isinstance(a,dict) and re.match(r'^https://',str(a.get('url') or ''))]
 if not row.get('icon_url') and arts:row['icon_url']=arts[0]
 tags=[str(t['name']) for t in pack.get('tags') or [] if isinstance(t,dict) and t.get('name')]
 row['all_versions']=list(dict.fromkeys((row.get('all_versions') or [])+[t for t in tags if re.fullmatch(r'\d+\.\d+(?:\.\d+)?',t)]))
 targets=[target for v in pack.get('versions') or [] if isinstance(v,dict) for target in v.get('targets') or [] if isinstance(target,dict)]
 row['all_versions']=list(dict.fromkeys(row['all_versions']+[t['version'] for t in targets if t.get('type')=='game' and t.get('name')=='minecraft' and isinstance(t.get('version'),str)]))
 loader_names={'forge':'Forge','fabric':'Fabric','neoforge':'NeoForge','quilt':'Quilt'}
 row['loaders']=list(dict.fromkeys((row.get('loaders') or [])+[loader_names[t['name']] for t in targets if t.get('type')=='modloader' and t.get('name') in loader_names]))
 if detail_description and not row.get('gallery'):
  source_images=[unescape(x) for x in re.findall(r'<img\b[^>]*\bsrc=[\"\']([^\"\']+)',detail_description,re.I)]
  row['gallery']=list(dict.fromkeys(u for u in source_images if re.match(r'^https://',u)))
 row['categories']=list(dict.fromkeys((row.get('categories') or [])+[t for t in tags if not re.fullmatch(r'\d+\.\d+(?:\.\d+)?',t)]))
 if not old:
  row['slug']=row['url'].rstrip('/').rsplit('/',1)[-1]
  row['download_links']=[{'name':'CurseForge 官方页面','url':row['url'],'type':'OFFICIAL'}]
 # Catalogue version summaries are not file-download contracts. Preserve original release dates and file history.
 summaries=[v for v in pack.get('versions') or [] if isinstance(v,dict) and v.get('private') is not True and isinstance(v.get('name'),str) and v['name'].strip() and stamp(v.get('updated'))]
 if summaries:
  latest=max(summaries,key=lambda v:v['updated'])
  row['catalog_latest_version']={'id':latest.get('id'),'name':latest['name'],'updatedAt':stamp(latest['updated']),'provider':'modpacks-ch','observedAt':observation.get('observedAt')}
 same_version=prior.get('providerUpdated')==pack.get('updated')
 row['catalog_observation']={**observation,'provider':'modpacks-ch','projectId':ident,'providerUpdated':pack.get('updated'),'synopsis':pack.get('synopsis'),'versionSummaries':pack.get('versions') or [],'detailsLoaded':bool(detail_description) or (same_version and bool(prior.get('detailsLoaded')))}
 if detail_description and row.get('description')==detail_description:
  row['catalog_observation']['descriptionSha256']=hashlib.sha256(detail_description.encode()).hexdigest()
 elif owned_body:row['catalog_observation']['descriptionSha256']=prior['descriptionSha256']
 return row

def atomic(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+f'.{os.getpid()}.tmp');tmp.write_text(value,encoding='utf-8');tmp.replace(path)

def atomic_private_json(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True,mode=0o700);os.chmod(path.parent,0o700)
 fd,tmp=tempfile.mkstemp(prefix='.cf-catalog-',suffix='.tmp',dir=path.parent)
 try:
  with os.fdopen(fd,'w',encoding='utf-8') as handle:json.dump(value,handle,ensure_ascii=False,separators=(',',':'));handle.write('\n')
  os.chmod(tmp,0o600);os.replace(tmp,path)
 except BaseException:
  try:os.unlink(tmp)
  except OSError:pass
  raise

def mark_checkpoint_run(checkpoint_path,manifest,status,error=None):
 if not checkpoint_path or not manifest:return
 now=datetime.now(timezone.utc).isoformat()
 manifest['runStatus']=status
 manifest['endedAt']=None if status=='running' else now
 if status=='running':
  manifest['runStartedAt']=now;manifest['completedAt']=None;manifest.pop('lastError',None)
 elif status=='finished':
  manifest['runFinishedAt']=now;manifest.pop('lastError',None)
 else:
  message=str(error) if error is not None else 'Unknown collection failure'
  manifest.update(complete=False,completedAt=None,runFinishedAt=now,lastError=message)
  manifest['coverageValidation']={'complete':False,'status':'failed','error':message}
 atomic_private_json(checkpoint_path,manifest)

def reset_catalog_checkpoint_pages(page_dir):
 page_dir=Path(page_dir)
 if not page_dir.exists():return
 if page_dir.is_symlink() or not page_dir.is_dir():raise CatalogRefusal('Unsafe public catalogue checkpoint directory')
 for child in page_dir.iterdir():
  if not re.fullmatch(r'page-\d{4}\.json',child.name):continue
  if child.is_symlink() or not child.is_file():raise CatalogRefusal('Unsafe public catalogue checkpoint page')
  child.unlink()

def checkpoint_page_path(page_dir,page):return Path(page_dir)/f'page-{int(page):04d}.json'

def normalize_catalog_refresh_token(value):
 if type(value)is int and value>=0:return str(value)
 if isinstance(value,str) and value.strip():return value.strip()
 return None

def page_directory_for_run(checkpoint_path):
 checkpoint_path=Path(checkpoint_path);stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');base=f'curseforge-public-catalog-pages-{stamp}-{os.getpid()}';candidate=checkpoint_path.parent/base;suffix=0
 while candidate.exists():suffix+=1;candidate=checkpoint_path.parent/f'{base}-{suffix}'
 candidate.mkdir(parents=True,mode=0o700);os.chmod(candidate,0o700);return candidate

def read_catalog_checkpoint(checkpoint_path,max_pages):
 checkpoint_path=Path(checkpoint_path)
 if not checkpoint_path.exists():return None,None
 if checkpoint_path.is_symlink() or not checkpoint_path.is_file():raise CatalogRefusal('Unsafe public catalogue checkpoint manifest')
 try:manifest=json.loads(checkpoint_path.read_text(encoding='utf-8'))
 except (OSError,UnicodeError,ValueError):raise CatalogRefusal('Invalid public catalogue checkpoint manifest') from None
 # Schema 1 stored transformed rows but not the source's full page response.
 # Leave it intact as historical evidence and start a schema-2 run alongside it.
 if not isinstance(manifest,dict) or manifest.get('provider')!='modpacks-ch':raise CatalogRefusal('Invalid public catalogue checkpoint manifest')
 if manifest.get('schema')!=2 or manifest.get('complete') is True:return None,None
 last=manifest.get('lastCompletedPage');pages=manifest.get('providerPages');digests=manifest.get('pageDigests');page_name=manifest.get('pageDirectory')
 requested=manifest.get('requestedPages')
 if (type(last)is not int or last<1 or last>max_pages or type(pages)is not int or pages<last
     or type(requested)is not int or requested>max_pages or not isinstance(digests,dict)
     or not isinstance(page_name,str) or Path(page_name).name!=page_name
     or not re.fullmatch(r'curseforge-public-catalog-pages-[A-Za-z0-9T-]+Z-\d+(?:-\d+)?',page_name)):
  return None,None
 page_dir=checkpoint_path.parent/page_name
 if page_dir.is_symlink() or not page_dir.is_dir():raise CatalogRefusal('Public catalogue checkpoint pages are missing')
 for page in range(1,last+1):
  path=checkpoint_page_path(page_dir,page);expected=digests.get(str(page))
  if (path.is_symlink() or not path.is_file() or not isinstance(expected,str)
      or hashlib.sha256(path.read_bytes()).hexdigest()!=expected):raise CatalogRefusal('Public catalogue checkpoint page hash mismatch')
  try:journal=json.loads(path.read_text(encoding='utf-8'))
  except (OSError,UnicodeError,ValueError):raise CatalogRefusal('Invalid public catalogue checkpoint page') from None
  if (journal.get('schema')!=2 or journal.get('page')!=page
      or not isinstance(journal.get('providerResponse'),dict)
      or not isinstance(journal.get('items'),list)):
   raise CatalogRefusal('Checkpoint lacks the full provider page response')
 return manifest,page_dir

def validate_catalog_page(data,page):
 if not isinstance(data,dict) or data.get('status')!='success':raise CatalogRefusal('Invalid catalogue status')
 try:response_page=int(data.get('page'));page_count=int(data.get('pages'))
 except (TypeError,ValueError):raise CatalogRefusal('Invalid catalogue pagination metadata') from None
 packs=data.get('packs')
 if response_page!=page or page_count<page or not isinstance(packs,list) or not packs:
  raise CatalogRefusal('Invalid/empty catalogue pagination; old IDs retained')
 ids=[]
 for pack in packs:
  if not isinstance(pack,dict) or pack.get('provider')!='curseforge' or type(pack.get('id')) is not int or pack['id']<1:
   raise CatalogRefusal('Catalogue page contains foreign or invalid identity')
  ids.append(str(pack['id']))
 return page_count,ids

def id_overlap_ratio(left,right):
 a=set(left or []);b=set(right or [])
 return len(a&b)/max(len(a),len(b),1)

def refresh_project_details(raw_path,sidecar_path,limit=0,transport=None):
 raw_path=Path(raw_path);transport=transport or PublicCatalogTransport()
 old=json.loads(raw_path.read_text(encoding='utf-8'))
 if not isinstance(old,list) or any(not isinstance(r,dict) or not re.fullmatch(r'\d+',str(r.get('project_id',''))) for r in old):raise ValueError('Invalid prior catalogue, retained without requests')
 rows={str(r['project_id']):r for r in old}
 if len(rows)!=len(old):raise ValueError('Duplicate source IDs in prior catalogue')
 selected=[r for i,r in rows.items() if r.get('catalog_observation',{}).get('provider')=='modpacks-ch' and r['catalog_observation'].get('sourceUrl')==ORIGIN+'/public/curseforge/'+i and not r['catalog_observation'].get('detailsLoaded')]
 if limit:selected=selected[:max(0,int(limit))]
 fetched=0;errors=[]
 for row in selected:
  try:
   ident=str(row['project_id']);detail,obs=transport.get('/public/curseforge/'+ident)
   if str(detail.get('id'))!=ident or detail.get('provider')!='curseforge':raise CatalogRefusal('Project detail identity mismatch')
   rows[ident]=merge_pack(detail,row,obs);rows[ident]['catalog_observation']['detailsLoaded']=True;fetched+=1
   print('DESKTOP_EVENT '+json.dumps({'phase':'CF新增项目资料补充','processed':fetched,'total':len(selected)},ensure_ascii=False),flush=True)
  except (ValueError,OSError,CatalogRefusal) as e:errors.append(str(e));break
 if fetched:
  result=list(rows.values());atomic(raw_path,json.dumps(result,ensure_ascii=False));atomic(sidecar_path,'window.curseforgeModpacksData = '+json.dumps(result,ensure_ascii=False)+';\n')
 return write_collection_result('curseforge',request_completed=bool(selected) and fetched==len(selected),fetched_count=fetched,pages_completed=fetched,pages_expected=len(selected),failed_requests=len(errors),errors=errors,status='partial' if fetched else 'failed',details={'provider':'modpacks-ch','coverage':'third-party-details','fullRefresh':False,'observedCount':fetched,'plannedProjectCount':len(selected),'originalFileHistoryPreserved':True,'sourceStop':errors[-1] if errors else None})

def refresh_catalog(raw_path,sidecar_path,limit=0,recent_pages=0,transport=None,checkpoint_path=None):
 raw_path=Path(raw_path);transport=transport or PublicCatalogTransport()
 old=json.loads(raw_path.read_text(encoding='utf-8')) if raw_path.exists() else []
 if not isinstance(old,list) or any(not isinstance(r,dict) or not re.fullmatch(r'\d+',str(r.get('project_id',''))) for r in old):raise ValueError('Invalid prior catalogue, retained without requests')
 rows={str(r['project_id']):copy.deepcopy(r) for r in old}
 if len(rows)!=len(old):raise ValueError('Duplicate source IDs in prior catalogue')
 pages=pages_seen=fetched=new=updated=failed=details_seen=duplicate_count=0;errors=[];seen=set();complete=False
 browse_calls=detail_calls=0;resumed_from=0;restart_reason=None;source_refreshed=None;first_response=None
 started_at=datetime.now(timezone.utc).isoformat();page_ids_by_page={};pagination_drift=[];refresh_tokens={};coverage_validation={'complete':False,'status':'not-run'}
 max_pages=min(200,recent_pages or ((int(limit)+49)//50 if limit else 200));limit=max(0,int(limit))
 checkpoint_path=Path(checkpoint_path) if checkpoint_path else None
 page_dir=None
 manifest=None
 try:
  if checkpoint_path:
   checkpoint_path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
   manifest,page_dir=read_catalog_checkpoint(checkpoint_path,max_pages)
   if manifest:
    # A resumed manifest can carry a terminal timestamp from its prior run.
    # Clear it before the first verification request so an in-flight resume
    # cannot look finished, even if that request stalls or fails.
    mark_checkpoint_run(checkpoint_path,manifest,'running')
    verify_data,verify_obs=transport.get('/public/curseforge/browse/updated');browse_calls+=1
    verify_count,verify_ids=validate_catalog_page(verify_data,1)
    first_journal=json.loads(checkpoint_page_path(page_dir,1).read_text(encoding='utf-8'))
    head_overlap=id_overlap_ratio(first_journal.get('pageIds'),verify_ids)
    if head_overlap>=0.8:
     resumed_from=int(manifest['lastCompletedPage']);pages=max(int(manifest['providerPages']),verify_count)
     manifest['requestedPages']=max_pages
     source_refreshed=manifest.get('providerRefreshedAt');fetched=int(manifest.get('observedCount') or 0)
     new=int(manifest.get('newCount') or 0);updated=int(manifest.get('updatedCount') or 0)
     details_seen=int(manifest.get('detailsObserved') or 0);duplicate_count=int(manifest.get('duplicateCount') or 0);pages_seen=resumed_from
     if verify_count!=int(manifest['providerPages']):pagination_drift.append({'stage':'resume-head','checkpointPages':manifest['providerPages'],'reportedPages':verify_count,'page':1})
     manifest.setdefault('resumeChecks',[]).append({'at':verify_obs.get('observedAt'),'headPageOverlap':head_overlap,'providerPages':verify_count,'refreshed':verify_data.get('refreshed')})
     pagination_drift.extend(manifest.get('paginationDrift') or [])
     refresh_tokens.update(manifest.get('providerRefreshTokensByPage') or {})
     for page in range(1,resumed_from+1):
      journal=json.loads(checkpoint_page_path(page_dir,page).read_text(encoding='utf-8'))
      if journal.get('schema')!=2 or journal.get('page')!=page or not isinstance(journal.get('items'),list):raise CatalogRefusal('Invalid public catalogue checkpoint page')
      page_ids_by_page[page]=journal.get('pageIds') or []
      refresh_tokens[str(page)]=journal.get('metadata',{}).get('refreshed')
      for item in journal['items']:
       pack=item.get('pack');obs=item.get('observation')
       if not isinstance(pack,dict) or type(pack.get('id')) is not int or not isinstance(obs,dict):raise CatalogRefusal('Invalid item in public catalogue checkpoint')
       ident=str(pack['id']);before=rows.get(ident);rows[ident]=merge_pack(pack,before,obs);seen.add(ident)
    else:
     restarts=int(manifest.get('restartCount') or 0)
     if restarts>=1:raise CatalogRefusal(f'Checkpoint head overlap {head_overlap:.3f} remained below 0.800 after one bounded restart; preserved old rows and checkpoint')
     restart_reason=f'checkpoint head overlap {head_overlap:.3f} below 0.800; bounded restart from page 1'
     manifest=None;page_dir=None;first_response=(verify_data,verify_obs);restart_count=restarts+1
   else:restart_count=0
  else:restart_count=0
  start_page=resumed_from+1 if resumed_from else 1
  page=start_page
  while page<=min(max(pages,1),max_pages):
   route='/public/curseforge/browse/updated'+(f'/{page}' if page>1 else '')
   if page==1 and first_response:data,obs=first_response;first_response=None
   else:data,obs=transport.get(route);browse_calls+=1
   page_count,raw_page_ids=validate_catalog_page(data,page)
   if page==1:
    pages=page_count;source_refreshed=normalize_catalog_refresh_token(data.get('refreshed'))
    if checkpoint_path and not manifest:
     page_dir=page_directory_for_run(checkpoint_path)
     manifest={'schema':2,'provider':'modpacks-ch','requestedPages':max_pages,'providerPages':pages,'initialProviderPages':pages,'providerRefreshedAt':source_refreshed,'providerRefreshTokensByPage':{},'lastCompletedPage':0,'complete':False,'runStatus':'running','endedAt':None,'runStartedAt':started_at,'startedAt':started_at,'pageDirectory':page_dir.name,'pageDigests':{},'observedCount':0,'newCount':0,'updatedCount':0,'detailsObserved':0,'duplicateCount':0,'browseRequests':0,'detailRequests':0,'paginationDrift':[],'resumeChecks':[],'restartCount':restart_count}
   else:
    if page_count!=pages:
     drift={'stage':'page-walk','page':page,'previousTargetPages':pages,'reportedPages':page_count,'at':obs.get('observedAt')}
     pagination_drift.append(drift)
     if manifest:manifest.setdefault('paginationDrift',[]).append(drift)
     pages=max(pages,page_count)
   page_items=[];page_ids=set();page_updates={};page_new=page_updated=page_details=page_duplicates=0;limit_reached=False
   for pack in data['packs']:
    ident=str(pack['id'])
    if ident in seen or ident in page_ids:duplicate_count+=1;page_duplicates+=1;continue
    if limit and fetched+len(page_ids)>=limit:limit_reached=True;break
    before=page_updates.get(ident,rows.get(ident));prior=(before or {}).get('catalog_observation',{})
    need_detail=before is None or (prior.get('provider')=='modpacks-ch' and
       (prior.get('providerUpdated')!=pack.get('updated') or (not prior.get('detailsLoaded') and (not before.get('description') or before.get('description')==prior.get('synopsis')))))
    if need_detail:
     detail,detail_obs=transport.get('/public/curseforge/'+ident);detail_calls+=1
     if detail.get('id')!=pack['id']:raise CatalogRefusal('Project detail identity mismatch')
     pack={**pack,**detail};obs_for_record=detail_obs;page_details+=1
    else:obs_for_record=obs
    row=merge_pack(pack,before,obs_for_record);page_updates[ident]=row;page_ids.add(ident)
    page_new+=int(before is None);page_updated+=int(before is not None and before!=row)
    page_items.append({'pack':pack,'observation':obs_for_record})
   rows.update(page_updates);seen.update(page_ids);fetched+=len(page_ids);new+=page_new;updated+=page_updated;details_seen+=page_details
   if limit_reached:break
   pages_seen+=1
   page_ids_by_page[page]=list(dict.fromkeys(raw_page_ids))
   page_refresh=normalize_catalog_refresh_token(data.get('refreshed'))
   refresh_tokens[str(page)]=page_refresh
   if checkpoint_path and manifest:
    page_meta={'page':page,'pages':page_count,'refreshed':page_refresh,'rawRefreshed':data.get('refreshed'),'observedAt':obs.get('observedAt'),'sourceUrl':obs.get('sourceUrl'),'sha256':obs.get('sha256'),'uniqueIds':list(dict.fromkeys(raw_page_ids)),'duplicateIdsInResponse':len(raw_page_ids)-len(set(raw_page_ids))}
    journal={'schema':2,'page':page,'providerResponse':data,'observation':obs,'metadata':page_meta,'pageIds':list(dict.fromkeys(raw_page_ids)),'items':page_items,'newCount':page_new,'updatedCount':page_updated,'detailsObserved':page_details,'duplicateCount':page_duplicates}
    page_path=checkpoint_page_path(page_dir,page);atomic_private_json(page_path,journal)
    manifest['pageDigests'][str(page)]=hashlib.sha256(page_path.read_bytes()).hexdigest();manifest['providerRefreshTokensByPage'][str(page)]=page_refresh
    manifest.update(providerPages=pages,lastCompletedPage=page,observedCount=fetched,newCount=new,updatedCount=updated,detailsObserved=details_seen,duplicateCount=duplicate_count,browseRequests=int(manifest.get('browseRequests') or 0)+1,detailRequests=int(manifest.get('detailRequests') or 0)+page_details,paginationDrift=list(pagination_drift))
    atomic_private_json(checkpoint_path,manifest)
   print('DESKTOP_EVENT '+json.dumps({'phase':'CF第三方目录核对','page':page,'pages':pages,'processed':fetched,'uniqueIds':len(seen),'duplicates':duplicate_count,'total':min(pages,max_pages)*50},ensure_ascii=False),flush=True)
   page+=1
  scan_complete=pages_seen>=pages and pages<=max_pages and not errors and not limit_reached
  if scan_complete:
   try:
    head_data,head_obs=transport.get('/public/curseforge/browse/updated');browse_calls+=1;head_count,head_ids=validate_catalog_page(head_data,1)
    tail_route='/public/curseforge/browse/updated'+(f'/{pages}' if pages>1 else '')
    tail_data,tail_obs=transport.get(tail_route);browse_calls+=1;tail_count,tail_ids=validate_catalog_page(tail_data,pages)
    head_overlap=id_overlap_ratio(page_ids_by_page.get(1),head_ids);tail_overlap=id_overlap_ratio(page_ids_by_page.get(pages),tail_ids)
    if checkpoint_path and manifest and page_dir:
     atomic_private_json(page_dir/'validation-head.json',{'response':head_data,'observation':head_obs,'ids':head_ids})
     atomic_private_json(page_dir/'validation-tail.json',{'response':tail_data,'observation':tail_obs,'ids':tail_ids})
    coverage_validation={'complete':False,'status':'validated','headPage':1,'tailPage':pages,'headPagesReported':head_count,'tailPagesReported':tail_count,'headIdOverlap':head_overlap,'tailIdOverlap':tail_overlap,'minimumOverlap':0.8,'headRefreshed':normalize_catalog_refresh_token(head_data.get('refreshed')),'tailRefreshed':normalize_catalog_refresh_token(tail_data.get('refreshed'))}
    stable_pages=head_count==pages and tail_count==pages
    adequate_overlap=head_overlap>=0.8 and tail_overlap>=0.8
    complete=stable_pages and adequate_overlap and not pagination_drift and duplicate_count==0
    coverage_validation.update(complete=complete,stablePageCount=stable_pages,adequateHeadTailOverlap=adequate_overlap,paginationDriftObserved=bool(pagination_drift),duplicateIdsObserved=duplicate_count)
    if not complete:coverage_validation['status']='uncertain'
   except (ValueError,OSError,CatalogRefusal,TypeError) as e:
    failed+=1;errors.append('Final head/tail coverage validation failed: '+str(e));coverage_validation={'complete':False,'status':'failed','error':str(e)}
  if checkpoint_path and manifest:
   manifest.update(complete=complete,completedAt=datetime.now(timezone.utc).isoformat() if complete else None,coverageValidation=coverage_validation,paginationDrift=list(pagination_drift),providerRefreshTokensByPage=refresh_tokens)
   mark_checkpoint_run(checkpoint_path,manifest,'finished')
 except Exception as e:
  failed+=1;errors.append(str(e))
  if checkpoint_path and manifest:
   try:mark_checkpoint_run(checkpoint_path,manifest,'failed',e)
   except Exception as checkpoint_error:errors.append('Checkpoint terminal status could not be saved: '+str(checkpoint_error))
  if not isinstance(e,(ValueError,OSError,CatalogRefusal,TypeError)):raise
 if fetched:
  result=list(rows.values());atomic(raw_path,json.dumps(result,ensure_ascii=False));atomic(sidecar_path,'window.curseforgeModpacksData = '+json.dumps(result,ensure_ascii=False)+';\n')
 http_requests=getattr(transport,'request_count',None)
 range_pages=min(pages,max_pages) if pages else max_pages
 return write_collection_result('curseforge',request_completed=complete,fetched_count=fetched,pages_completed=pages_seen,pages_expected=range_pages or None,failed_requests=failed,errors=errors,status='partial' if fetched else 'failed',truncated=not complete,details={'provider':'modpacks-ch','coverage':'third-party-catalog-visible-window','fullRefresh':False,'providerPagesCompleted':complete,'pagesObserved':pages_seen,'providerPages':pages,'requestedPageLimit':max_pages,'pageSize':50,'visibleProjectSlots':range_pages*50,'observedCount':fetched,'uniqueIdsObserved':len(seen),'duplicateCount':duplicate_count,'detailsObserved':details_seen,'newCount':new,'updatedCount':updated,'browseRequests':browse_calls,'detailRequests':detail_calls,'httpRequestsThisRun':http_requests if isinstance(http_requests,int) else browse_calls+detail_calls,'resumedFromPage':resumed_from,'checkpointEnabled':bool(checkpoint_path),'checkpointPage':pages_seen if checkpoint_path else None,'checkpointSchema':2 if checkpoint_path else None,'checkpointPageDirectory':page_dir.name if page_dir else None,'fullPageResponsesSaved':bool(checkpoint_path and page_dir and manifest),'providerRefreshTokensByPage':refresh_tokens,'paginationDrift':pagination_drift,'coverageValidation':coverage_validation,'sourceRefreshedAt':source_refreshed,'startedAt':started_at,'endedAt':datetime.now(timezone.utc).isoformat(),'restartReason':restart_reason,'oldIdsRetained':True,'outputCount':len(rows),'originalFileHistoryPreserved':True,'sourceStop':errors[-1] if errors else None})

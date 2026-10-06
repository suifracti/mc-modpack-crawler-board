"""Public third-party CurseForge modpack catalogue. No keys, downloads or fallback.

A completed walk means the provider's returned pages, not all CurseForge projects.
Existing IDs and richer original-source data always survive a bounded observation.
"""
import copy,hashlib,json,os,re,time,urllib.request,urllib.error,urllib.robotparser
from html import unescape
from datetime import datetime,timezone
from pathlib import Path
from desktop_collection_contract import write_collection_result
ORIGIN='https://api.modpacks.ch'
UA='MCModpackCrawlerDashboard/1.0'
MAX_BYTES=8*1024*1024
class CatalogRefusal(RuntimeError):pass
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args):raise CatalogRefusal('Public catalogue redirect refused')
class PublicCatalogTransport:
 def __init__(self):self.opener=urllib.request.build_opener(NoRedirect());self.policy=None;self.last=0;self.stopped=None
 def read(self,route):
  if self.stopped:raise CatalogRefusal(self.stopped)
  time.sleep(max(0,1-(time.monotonic()-self.last)));self.last=time.monotonic()
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
 same_version=prior.get('providerUpdated')==pack.get('updated')
 row['catalog_observation']={**observation,'provider':'modpacks-ch','projectId':ident,'providerUpdated':pack.get('updated'),'synopsis':pack.get('synopsis'),'versionSummaries':pack.get('versions') or [],'detailsLoaded':bool(detail_description) or (same_version and bool(prior.get('detailsLoaded')))}
 if detail_description and row.get('description')==detail_description:
  row['catalog_observation']['descriptionSha256']=hashlib.sha256(detail_description.encode()).hexdigest()
 elif owned_body:row['catalog_observation']['descriptionSha256']=prior['descriptionSha256']
 return row

def atomic(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+f'.{os.getpid()}.tmp');tmp.write_text(value,encoding='utf-8');tmp.replace(path)

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

def refresh_catalog(raw_path,sidecar_path,limit=0,recent_pages=0,transport=None):
 raw_path=Path(raw_path);transport=transport or PublicCatalogTransport()
 old=json.loads(raw_path.read_text(encoding='utf-8')) if raw_path.exists() else []
 if not isinstance(old,list) or any(not isinstance(r,dict) or not re.fullmatch(r'\d+',str(r.get('project_id',''))) for r in old):raise ValueError('Invalid prior catalogue, retained without requests')
 rows={str(r['project_id']):copy.deepcopy(r) for r in old}
 if len(rows)!=len(old):raise ValueError('Duplicate source IDs in prior catalogue')
 pages=pages_seen=fetched=new=updated=failed=details_seen=0;errors=[];seen=set();complete=False
 max_pages=min(200,recent_pages or ((int(limit)+49)//50 if limit else 200));limit=max(0,int(limit))
 try:
  for page in range(1,max_pages+1):
   route='/public/curseforge/browse/updated'+(f'/{page}' if page>1 else '')
   data,obs=transport.get(route);pages=int(data.get('pages') or 0)
   if str(data.get('page'))!=str(page) or pages<page or not isinstance(data.get('packs'),list) or not data['packs']:raise CatalogRefusal('Invalid/empty catalogue pagination; old IDs retained')
   # Validate the entire page before accepting any item from it.
   for p in data['packs']:
    if p.get('provider')!='curseforge' or type(p.get('id')) is not int:raise CatalogRefusal('Catalogue page contains foreign or invalid identity')
   for pack in data['packs']:
    ident=str(pack['id'])
    if ident in seen:continue
    if limit and fetched>=limit:break
    before=rows.get(ident);prior=(before or {}).get('catalog_observation',{})
    need_detail=before is None or (prior.get('provider')=='modpacks-ch' and
       (prior.get('providerUpdated')!=pack.get('updated') or (not prior.get('detailsLoaded') and (not before.get('description') or before.get('description')==prior.get('synopsis')))))
    if need_detail:
     detail,detail_obs=transport.get('/public/curseforge/'+ident)
     if detail.get('id')!=pack['id']:raise CatalogRefusal('Project detail identity mismatch')
     pack={**pack,**detail};obs_for_record=detail_obs;details_seen+=1
    else:obs_for_record=obs
    row=merge_pack(pack,before,obs_for_record);rows[ident]=row;seen.add(ident);fetched+=1;new+=int(before is None);updated+=int(before is not None and before!=row)
   pages_seen+=1
   print('DESKTOP_EVENT '+json.dumps({'phase':'CF第三方目录核对','processed':fetched,'total':min(pages,max_pages)*50},ensure_ascii=False),flush=True)
   if page>=pages:complete=True;break
   if limit and fetched>=limit:break
 except (ValueError,OSError,CatalogRefusal) as e:failed+=1;errors.append(str(e))
 if fetched:
  result=list(rows.values());atomic(raw_path,json.dumps(result,ensure_ascii=False));atomic(sidecar_path,'window.curseforgeModpacksData = '+json.dumps(result,ensure_ascii=False)+';\n')
 return write_collection_result('curseforge',request_completed=complete,fetched_count=fetched,pages_completed=pages_seen,pages_expected=pages or None,failed_requests=failed,errors=errors,status='partial' if fetched else 'failed',truncated=not complete,details={'provider':'modpacks-ch','coverage':'third-party-catalog','fullRefresh':False,'providerPagesCompleted':complete,'pagesObserved':pages_seen,'providerPages':pages,'observedCount':fetched,'detailsObserved':details_seen,'newCount':new,'updatedCount':updated,'oldIdsRetained':True,'outputCount':len(rows),'originalFileHistoryPreserved':True,'sourceStop':errors[-1] if errors else None})

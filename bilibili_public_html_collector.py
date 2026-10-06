"""Bounded, explicit public HTML observations for the desktop collector contract.

Never imports the legacy API/login collector. Old full descriptions, auxiliary
observations and derived release fields survive a metadata observation unchanged.
"""
from __future__ import annotations
import argparse,copy,gzip,hashlib,io,json,os,re,ssl,tempfile,time
import urllib.request,urllib.error,urllib.parse,urllib.robotparser
from datetime import datetime,timezone,timedelta
from pathlib import Path
from bilibili_html_adapter import parse_public_video,make_public_record,UnavailablePublicVideo
from desktop_collection_contract import write_collection_result

UA='MCModpackCrawlerDashboard/1.0'
MAX_PAGES=30
MAX_CATALOG_PAGES=5000
MIN_INTERVAL=2
TRANSPORT_COOLDOWN_SECONDS=300
META_FIELDS=('title','author','pub_timestamp','pub_time','duration','aid','cid','pic','views','likes','coins','favorites','share','reply','danmaku')
OBS_FIELDS=('source_tags','source_kind','source_url','source_observed_at','source_html_sha256','source_field_provenance','classification_basis','description_excerpt','description_excerpt_truncated','description_excerpt_observed','description_source_sha256','description_download_links_observed','acquisition_note','content_category','content_candidate','content_reason','content_policy_schema')

class Refusal(RuntimeError):pass
def utc():return datetime.now(timezone.utc).isoformat()
def valid_bvid(value):return isinstance(value,str) and bool(re.fullmatch(r'BV[0-9A-Za-z]{10}',value))
def close_http_error(error):
 if isinstance(error,urllib.error.HTTPError):error.close()
def atomic_json(path,value):
 path.parent.mkdir(parents=True,exist_ok=True)
 fd,name=tempfile.mkstemp(prefix='.html-observation-',suffix='.tmp',dir=path.parent)
 with os.fdopen(fd,'w',encoding='utf-8') as h:json.dump(value,h,ensure_ascii=False,indent=2);h.write('\n')
 os.replace(name,path)

def save_html_evidence(state_path,bvid,body):
 digest=hashlib.sha256(body.encode()).hexdigest()
 folder=Path(state_path).parent/'bilibili-html-evidence';folder.mkdir(parents=True,exist_ok=True)
 target=folder/f'{bvid}-{digest}.html'
 if not target.exists():
  fd,tmp=tempfile.mkstemp(prefix='.public-html-',suffix='.tmp',dir=folder)
  with os.fdopen(fd,'w',encoding='utf-8') as h:h.write(body)
  os.replace(tmp,target)
 return {'path':str(target),'sha256':digest,'sourceUrl':f'https://www.bilibili.com/video/{bvid}/'}

def unavailable_entry(bvid,body,at,true_code=-404):
 return {'at':at,'bvid':bvid,'reason':'official-video-unavailable','httpStatus':200,'initialStateCode':404,'initialStateTrueCode':true_code,'sourceUrl':f'https://www.bilibili.com/video/{bvid}/','htmlSha256':hashlib.sha256(body.encode()).hexdigest(),'oldRecordRetained':True}

def resolve_unavailable_stop(state_path,bvid,body):
 """Resolve only the legacy parse error proved by a saved official 404 page."""
 try:parse_public_video(body,bvid)
 except UnavailablePublicVideo as exc:true_code=exc.true_code
 else:raise ValueError('Saved HTML does not prove an unavailable video')
 state_path=Path(state_path);lock_path=state_path.with_suffix(state_path.suffix+'.lock')
 fd=os.open(lock_path,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
 try:
  state=json.loads(state_path.read_text(encoding='utf-8'))
  stop=state.get('stopped')
  if (state.get('schema')!=1 or not isinstance(state.get('days'),dict) or not isinstance(stop,dict)
      or stop.get('bvid')!=bvid or stop.get('httpStatus') is not None or stop.get('error')!='Missing or error initial state'):
   raise Refusal('Persistent stop is not the evidenced legacy unavailable-video error')
  unavailable=state.setdefault('unavailable',{});history=state.setdefault('stopHistory',[])
  if not isinstance(unavailable,dict) or not isinstance(history,list):raise ValueError('Invalid persistent HTML history')
  entry=unavailable_entry(bvid,body,utc(),true_code)
  entry['htmlEvidence']=save_html_evidence(state_path,bvid,body)
  history.append({'stopped':copy.deepcopy(stop),'resolvedAt':entry['at'],'resolution':'single-video-unavailable','evidenceSha256':entry['htmlSha256']})
  unavailable[bvid]=entry;state['stopped']=None;atomic_json(state_path,state)
  return entry
 finally:os.close(fd);lock_path.unlink()

def is_tls_eof(error):
 """A typed connection interruption is not evidence about video availability."""
 reason=error.reason if isinstance(error,urllib.error.URLError) and not isinstance(error,urllib.error.HTTPError) else error
 return isinstance(reason,ssl.SSLEOFError)

def resume_transport_state(state):
 """A new user-requested task may recheck a cooled-off connection interruption.

 No content retry, no HTTP/HTML/certificate refusal reset. Original stop and
 attempts survive in history. A failed recheck records a fresh interruption.
 """
 stop=state.get('stopped')
 if not isinstance(stop,dict):return False
 eof_text=re.fullmatch(r'<urlopen error \[SSL: UNEXPECTED_EOF_WHILE_READING\] EOF occurred in violation of protocol \(_ssl\.c:\d+\)>',str(stop.get('error','')))
 typed=(stop.get('stopKind')=='transport' and stop.get('reason')=='tls-eof-unverified'
        and (stop.get('transportErrorType')=='SSLEOFError' or eof_text))
 legacy=(not stop.get('stopKind') and eof_text)
 if not (typed or legacy) or stop.get('httpStatus') is not None or 'htmlEvidence' in stop:return False
 try:
  at=datetime.fromisoformat(stop['at']);now=datetime.fromisoformat(utc())
  if at.tzinfo is None or now.tzinfo is None or (now-at).total_seconds()<TRANSPORT_COOLDOWN_SECONDS:return False
 except (KeyError,ValueError,TypeError):return False
 if stop.get('bvid') and (not valid_bvid(stop['bvid']) or not any(stop['bvid'] in ids for ids in state['days'].values() if isinstance(ids,list))):return False
 history=state.setdefault('stopHistory',[])
 if not isinstance(history,list):raise ValueError('Invalid persistent stop history')
 history.append({'stopped':copy.deepcopy(stop),'resolvedAt':utc(),'resolution':'transport-cooldown-public-recheck','contentRetried':False})
 state['stopped']=None;state['transportFailureStreak']=0
 return True

def resolve_transport_stop(state_path):
 """Migrate only an old, recorded TLS EOF; retain its attempt and do not retry it."""
 state_path=Path(state_path);lock_path=state_path.with_suffix(state_path.suffix+'.lock')
 fd=os.open(lock_path,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
 try:
  state=json.loads(state_path.read_text(encoding='utf-8'));stop=state.get('stopped')
  if (state.get('schema')!=1 or not isinstance(state.get('days'),dict) or not isinstance(stop,dict)
      or not valid_bvid(stop.get('bvid')) or stop.get('httpStatus') is not None
      or 'htmlEvidence' in stop or stop.get('transportFailureCircuitOpen')
      or not re.fullmatch(r'<urlopen error \[SSL: UNEXPECTED_EOF_WHILE_READING\] EOF occurred in violation of protocol \(_ssl\.c:\d+\)>',stop.get('error',''))
      or not any(isinstance(v,list) and stop['bvid'] in v for v in state['days'].values())):
   raise Refusal('Persistent stop is not an attempted legacy TLS EOF')
  failures=state.setdefault('transportFailures',{});history=state.setdefault('stopHistory',[])
  if not isinstance(failures,dict) or not isinstance(history,list):raise ValueError('Invalid persistent transport history')
  failures[stop['bvid']]={**copy.deepcopy(stop),'reason':'tls-eof-unverified','oldRecordRetained':True,'retried':False}
  history.append({'stopped':copy.deepcopy(stop),'resolvedAt':utc(),'resolution':'tls-eof-deferred-without-retry'})
  state['transportFailureStreak']=1;state['stopped']=None;atomic_json(state_path,state)
  return failures[stop['bvid']]
 finally:os.close(fd);lock_path.unlink()

class RedirectGuard(urllib.request.HTTPRedirectHandler):
 expected=''
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  if newurl.rstrip('/')!=self.expected.rstrip('/'):raise Refusal('Redirect left the exact approved public URL')
  return super().redirect_request(req,fp,code,msg,headers,newurl)

class PublicTransport:
 def __init__(self):
  self.guard=RedirectGuard();self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),self.guard)
  self.last_request=0.0;self.requests=[]
 def fetch(self,url,limit):
  part=urllib.parse.urlsplit(url)
  robots=part.path=='/robots.txt' and part.hostname in {'www.bilibili.com','api.bilibili.com','search.bilibili.com'}
  video=part.hostname=='www.bilibili.com' and bool(re.fullmatch(r'/video/BV[0-9A-Za-z]{10}/',part.path))
  if part.scheme!='https' or part.query or part.fragment or not (robots or video):raise Refusal('Request outside public HTML/robots scope')
  wait=MIN_INTERVAL-(time.monotonic()-self.last_request)
  if wait>0:time.sleep(wait)
  self.last_request=time.monotonic();self.guard.expected=url;self.requests.append(url)
  request=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,text/plain;q=0.8'})
  with self.opener.open(request,timeout=15) as response:
   if response.status!=200:raise Refusal(f'HTTP {response.status}')
   if response.geturl().rstrip('/')!=url.rstrip('/'):raise Refusal('Unexpected final URL')
   data=response.read(limit+1)
   if len(data)>limit:raise Refusal('Response-size limit exceeded')
   encoding=response.headers.get('Content-Encoding','')
   if encoding=='gzip':
    with gzip.GzipFile(fileobj=io.BytesIO(data)) as compressed:data=compressed.read(limit+1)
   elif encoding not in ('','identity'):raise Refusal('Unverifiable response encoding')
   if len(data)>limit:raise Refusal('Decoded response-size limit exceeded')
   return data.decode('utf-8','replace')

def robots_policy(body):
 if '<html' in body.lower() or not re.search(r'^\s*User-agent\s*:',body,re.I|re.M):raise Refusal('Unverifiable robots response')
 policy=urllib.robotparser.RobotFileParser();policy.parse(body.splitlines());return policy

def metadata_patch(video,tags,body,observed_at):
 record,decision=make_public_record(video,tags,body,observed_at)
 if record is None:
  # A formerly known publication may be reclassified. Preserve its ID and only
  # update official identity/statistics, never remove it based on one observation.
  record={'bvid':video['bvid'],'title':video['title'],'author':video['owner']['name'],'pub_timestamp':video['pubdate'],'pub_time':datetime.fromtimestamp(video['pubdate'],timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M'),'source_tags':tags,'source_kind':'official-public-video-html','source_url':f"https://www.bilibili.com/video/{video['bvid']}/",'source_observed_at':observed_at,'source_html_sha256':hashlib.sha256(body.encode()).hexdigest(),'classification_basis':decision['basis']}
  for k in ('aid','cid','pic'):
   if k in video:record[k]=video[k]
  for k,source in [('views','view'),('likes','like'),('coins','coin'),('favorites','favorite'),('share','share'),('reply','reply'),('danmaku','danmaku')]:
   value=video.get('stat',{}).get(source)
   if type(value)is int and value>=0:record[k]=value
 record['source_html_checked_at']=observed_at
 record.update(content_category=decision['contentCategory'],content_candidate=decision['accepted'],content_reason=decision['contentReason'] if decision['accepted'] else decision['basis'],content_policy_schema=decision['contentPolicySchema'])
 record['source_html_observed_fields']=[k for k in META_FIELDS if k in record]+[k for k in OBS_FIELDS if k in record]
 record['pack_first_release_verified']=False
 return record,decision

def merge_observation(old,observed):
 if old is None:return copy.deepcopy(observed)
 result=copy.deepcopy(old)
 for k in META_FIELDS+OBS_FIELDS+('source_html_checked_at','source_html_observed_fields'):
  if k in observed:result[k]=copy.deepcopy(observed[k])
 # No raw.desc or historical observed flag/date is changed by a short excerpt.
 return result

def season_candidates(video):
 result=[]
 season=video.get('ugc_season') or {}
 if not isinstance(season,dict):return result
 for section in season.get('sections',[]):
  if not isinstance(section,dict):continue
  for episode in section.get('episodes',[]):
   if not isinstance(episode,dict):continue
   arc=episode.get('arc') or {};bvid=episode.get('bvid') or (arc.get('bvid') if isinstance(arc,dict) else None)
   if valid_bvid(bvid) and bvid not in result:result.append(bvid)
 return result

def collect(workspace,state_path,*,mode='existing',limit=3,bvid=None,until=None,transport=None):
 workspace=Path(workspace);state_path=Path(state_path)
 if mode not in {'existing','new','catalog'}:raise ValueError('Invalid HTML collection mode')
 daily_budget=MAX_CATALOG_PAGES if mode=='catalog' else MAX_PAGES
 limit=max(1,min(int(limit),daily_budget));transport=transport or PublicTransport()
 raw_path=workspace/'crawler_output/bilibili_modpacks.json';sidecar=workspace/'converted_output/data/bili_data.js'
 observations=[];new_count=updated_count=0;errors=[];failed_count=0
 details={'mode':mode,'coverage':'public-video-html-bounded','fullRefresh':False,'observedCount':0,'newCount':0,'updatedCount':0,'failedCount':0,'requestBudget':limit,'dailyBudget':daily_budget,'knownCatalogRefresh':mode=='catalog','apiBusinessRequests':0,'cookiesUsed':False,'scriptsExecuted':False,'contentRetries':0,'minimumIntervalSeconds':2,'restrictedRobots':{},'stopped':None,'discoveredCandidates':[]}
 state={'schema':1,'days':{},'stopped':None};lock_fd=None;lock_path=state_path.with_suffix(state_path.suffix+'.lock')
 try:
  previous=json.loads(raw_path.read_text(encoding='utf-8')) if raw_path.exists() else []
  if not isinstance(previous,list) or any(not isinstance(v,dict) or not valid_bvid(v.get('bvid')) for v in previous):raise ValueError('Existing Bilibili input contains invalid BVIDs; retained without changes')
  ids=[v['bvid'] for v in previous]
  if len(ids)!=len(set(ids)):raise ValueError('Duplicate BVIDs in existing input; retained without changes')
  records={v['bvid']:copy.deepcopy(v) for v in previous};initial=copy.deepcopy(records)
  if bvid and not valid_bvid(bvid):raise ValueError('Invalid explicit BVID')
  seeds=[bvid] if bvid else [v['bvid'] for v in sorted(previous,key=lambda v:(v.get('source_html_checked_at') or '',-(v.get('pub_timestamp') or 0)))]
  if not seeds:raise ValueError('No known public BVID seed: import existing data or use --bv; full-site API/search is unavailable')
  state_path.parent.mkdir(parents=True,exist_ok=True)
  lock_fd=os.open(lock_path,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
  os.write(lock_fd,str(os.getpid()).encode())
  if state_path.exists():
   state=json.loads(state_path.read_text(encoding='utf-8'))
   if state.get('schema')!=1 or not isinstance(state.get('days'),dict):raise ValueError('Invalid persistent HTML state; no requests made')
  if state.get('stopped'):
   if resume_transport_state(state):atomic_json(state_path,state)
   else:raise Refusal('Previous HTML refusal or transport cooldown persists; no further requests permitted: '+str(state['stopped']))
  day=utc()[:10];attempted=state['days'].setdefault(day,[])
  if not isinstance(attempted,list) or any(not valid_bvid(x) for x in attempted):raise ValueError('Invalid daily HTML ledger')
  unavailable=state.setdefault('unavailable',{})
  if not isinstance(unavailable,dict) or any(not valid_bvid(x) for x in unavailable):raise ValueError('Invalid unavailable-video ledger')
  transport_failures=state.setdefault('transportFailures',{})
  if not isinstance(transport_failures,dict) or any(not valid_bvid(x) for x in transport_failures):raise ValueError('Invalid transport-failure ledger')
  seeds=[x for x in seeds if x not in attempted and x not in unavailable]
  details['knownCandidateCount']=len(seeds)
  if not seeds or len(attempted)>=daily_budget:raise ValueError('Daily candidate budget exhausted or selected BVID already observed today; no repeat requests')
  seeds=seeds[:limit if mode in {'existing','catalog'} else min(3,limit)]
  details['plannedCandidateCount']=len(seeds)
  policy=robots_policy(transport.fetch('https://www.bilibili.com/robots.txt',1024*1024))
  details['publicRobotsCheckedAt']=utc()
  for host in ('api.bilibili.com','search.bilibili.com'):
   try:
    restricted=robots_policy(transport.fetch('https://'+host+'/robots.txt',1024*1024))
    details['restrictedRobots'][host]={'checkedAt':utc(),'rootDenied':not restricted.can_fetch(UA,'https://'+host+'/'),'businessRequests':0,'routeEnabled':False}
   except Exception as exc:
    details['restrictedRobots'][host]={'checkedAt':utc(),'error':str(exc),'businessRequests':0,'routeEnabled':False}
    close_http_error(exc)
  queue=seeds[:];seen=set(attempted)|set(unavailable);attempt_count=0
  cutoff=datetime.fromisoformat(until).replace(tzinfo=timezone.utc).timestamp() if until else None
  while queue and attempt_count<limit and len(attempted)<daily_budget:
   ident=queue.pop(0)
   if ident in seen:continue
   url=f'https://www.bilibili.com/video/{ident}/'
   if not policy.can_fetch(UA,url):raise Refusal('Public video URL is denied by robots')
   attempted.append(ident);seen.add(ident);attempt_count+=1;atomic_json(state_path,state)
   body=None
   try:
    body=transport.fetch(url,8*1024*1024)
    title=re.search(r'<title[^>]*>(.*?)</title>',body,re.I|re.S)
    if title and re.search(r'验证码|访问被拒绝|安全验证|Forbidden|Access Denied|Precondition Failed|请先登录',title.group(1),re.I):raise Refusal('HTTP200 access-gate title')
    video,tags=parse_public_video(body,ident);at=utc();patch,decision=metadata_patch(video,tags,body,at)
    state['transportFailureStreak']=0;transport_failures.pop(ident,None);atomic_json(state_path,state)
    known=ident in records;accepted=decision['accepted']
    observations.append({'bvid':ident,'observedAt':at,'publishedAtUTC':datetime.fromtimestamp(video['pubdate'],timezone.utc).isoformat(),'accepted':accepted,'basis':decision['basis'],'known':known,'htmlSha256':patch['source_html_sha256']})
    if known:
     merged=merge_observation(records[ident],patch);updated_count+=int(merged!=records[ident]);records[ident]=merged
    elif accepted and (cutoff is None or video['pubdate']>=cutoff):records[ident]=merge_observation(None,patch);new_count+=1
    if mode=='new':
     candidates=[x for x in season_candidates(video) if x not in records and x not in seen and x not in queue]
     details['discoveredCandidates'].extend(candidates);queue=candidates[:MAX_PAGES]+queue
    print('DESKTOP_EVENT '+json.dumps({'phase':'已有视频目录核验' if mode=='catalog' else 'HTML局部核验','processed':attempt_count,'total':len(seeds) if mode=='catalog' else limit},ensure_ascii=False),flush=True)
   except UnavailablePublicVideo as exc:
    failed_count+=1;state['transportFailureStreak']=0;transport_failures.pop(ident,None);unavailable[ident]={**unavailable_entry(ident,body,utc(),exc.true_code),'htmlEvidence':save_html_evidence(state_path,ident,body)};atomic_json(state_path,state);errors.append(f'{ident}: {exc}')
   except Exception as exc:
    failed_count+=1;failure={'at':utc(),'bvid':ident,'error':str(exc),'httpStatus':getattr(exc,'code',None)}
    if body is None and is_tls_eof(exc):
     transport_failures[ident]={**failure,'reason':'tls-eof-unverified','oldRecordRetained':True,'retried':False}
     state['transportFailureStreak']=int(state.get('transportFailureStreak') or 0)+1;errors.append(f'{ident}: TLS EOF; unverified, no retry')
     print('DESKTOP_EVENT '+json.dumps({'phase':'网络中断记录（不重试）','processed':attempt_count,'total':len(seeds) if mode=='catalog' else limit},ensure_ascii=False),flush=True)
     if state['transportFailureStreak']<3:atomic_json(state_path,state);continue
     failure['transportFailureCircuitOpen']=True
     failure.update(stopKind='transport',reason='tls-eof-unverified',transportErrorType='SSLEOFError',stage='video',retryAfter=(datetime.fromisoformat(utc())+timedelta(seconds=TRANSPORT_COOLDOWN_SECONDS)).isoformat())
    state['stopped']=failure
    if isinstance(body,str):state['stopped']['htmlEvidence']=save_html_evidence(state_path,ident,body)
    atomic_json(state_path,state);errors.append(str(exc));close_http_error(exc);break
  details['dailyCandidatesUsed']=len(attempted);details['unverifiedQueuedCount']=max(0,details['knownCandidateCount']-attempt_count) if mode=='catalog' else len(queue)
  details['pendingTransportFailureCount']=len(transport_failures)
  details['knownCatalogCompleted']=mode=='catalog' and not details['unverifiedQueuedCount'] and not state.get('stopped') and not transport_failures
 except FileExistsError:errors.append('HTML state is locked by another task or an interrupted task; no requests made')
 except Exception as exc:
  errors.append(str(exc))
  if is_tls_eof(exc) and not state.get('stopped'):
   failed_count+=1
   state['stopped']={'at':utc(),'error':str(exc),'httpStatus':None,'stopKind':'transport','reason':'tls-eof-unverified','transportErrorType':'SSLEOFError','stage':'robots','retryAfter':(datetime.fromisoformat(utc())+timedelta(seconds=TRANSPORT_COOLDOWN_SECONDS)).isoformat()};atomic_json(state_path,state)
  elif isinstance(exc,Refusal) and not state.get('stopped'):
   state['stopped']={'at':utc(),'error':str(exc),'httpStatus':getattr(exc,'code',None)};atomic_json(state_path,state)
  elif isinstance(exc,(urllib.error.URLError,urllib.error.HTTPError)):
   state['stopped']={'at':utc(),'error':str(exc),'httpStatus':getattr(exc,'code',None)};atomic_json(state_path,state)
  close_http_error(exc)
 finally:
  if lock_fd is not None:os.close(lock_fd);lock_path.unlink()
 details.update(observedCount=len(observations),newCount=new_count,updatedCount=updated_count,failedCount=failed_count,stopped=state.get('stopped'),knownUnavailableCount=len(state.get('unavailable') or {}),observations=observations,requests=getattr(transport,'requests',[]))
 if observations:
  atomic_json(raw_path,list(records.values()))
  sidecar.parent.mkdir(parents=True,exist_ok=True)
  sidecar.write_text('window.biliModpacksData = '+json.dumps(list(records.values()),ensure_ascii=False)+';\n',encoding='utf-8')
 result=write_collection_result('bilibili',request_completed=False,fetched_count=len(observations),pages_completed=len(observations),pages_expected=limit,failed_requests=failed_count,errors=errors,status='partial' if observations else 'failed',details=details)
 return result

def main():
 cli=argparse.ArgumentParser(description='Bounded public Bilibili HTML; no API/search/login/full refresh')
 cli.add_argument('--mode',choices=['existing','new','catalog'],default='existing');cli.add_argument('--limit',type=int,default=3);cli.add_argument('--bv');cli.add_argument('--until');cli.add_argument('--html-state',required=True)
 args=cli.parse_args();workspace=Path(os.environ.get('MC_DESKTOP_WORKSPACE') or Path.cwd())
 result=collect(workspace,args.html_state,mode=args.mode,limit=args.limit,bvid=args.bv,until=args.until)
 print(json.dumps({'status':result['status'],'details':result['details'],'errors':result['errors']},ensure_ascii=False),flush=True)
 return 0 if result['fetchedCount'] else 1

if __name__=='__main__':raise SystemExit(main())

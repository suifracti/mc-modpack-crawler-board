import unittest,tempfile,json,sys,urllib.error,urllib.request,os,subprocess,ssl
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
import curseforge_modpacks_ch as catalog

def pack(i=1):return {'id':i,'provider':'curseforge','name':'新标题','updated':1791267000,'synopsis':'简短摘要','installs':150,'authors':[{'name':'作者'}],'art':[],'tags':[]}
class Transport:
 def __init__(self,fail=None):self.calls=[];self.fail=fail
 def get(self,route):
  self.calls.append(route)
  if self.fail and route.endswith('/2'):raise catalog.CatalogRefusal('HTTP 403')
  if '/browse/' in route:return {'status':'success','page':'2' if route.endswith('/2') else '1','pages':2,'packs':[pack(2 if route.endswith('/2') else 1)]},{'sha256':'fixture'}
  return {**pack(2),'status':'success','links':[{'link':'https://www.curseforge.com/minecraft/modpacks/new-pack'}],'versions':[]},{'sha256':'fixture'}
class Tests(unittest.TestCase):
 def test_catalog_keeps_current_version_summary_separate_from_original_file_history(self):
  detail={**pack(1),'versions':[{'id':123,'name':'Pack v0.3.0','updated':1790724600,'private':False}]}
  old={'project_id':'1','url':'https://www.curseforge.com/minecraft/modpacks/a','releases':[{'id':99,'displayName':'Pack v0.2.0','fileDate':'2026-02-16'}]}
  row=catalog.merge_pack(detail,old,{'observedAt':'2026-10-06T11:00:00Z'})
  self.assertEqual(row['releases'],old['releases'])
  self.assertEqual(row['catalog_latest_version']['name'],'Pack v0.3.0')
  self.assertEqual(row['catalog_latest_version']['provider'],'modpacks-ch')
  self.assertNotIn('downloadUrl',row['catalog_latest_version'])

 def test_daily_worker_uses_public_catalog_without_manual_mode_override(self):
  sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
  from collector_worker import build_script_args
  args=SimpleNamespace(mode=None,limit=None,pages=2,source_root=str(Path(__file__).resolve().parents[3]))
  with patch.dict(os.environ,{'CURSEFORGE_PROVIDER':'cfwidget'}):
   actual=build_script_args('curseforge',args)
  self.assertIn('--public-catalog',actual);self.assertIn('--recent-pages',actual)
 def test_explicit_catalog_mode_requests_the_full_provider_visible_page_cap(self):
  sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
  from collector_worker import build_script_args
  args=SimpleNamespace(mode='catalog',limit=None,pages=200,source_root=str(Path(__file__).resolve().parents[3]))
  with patch.dict(os.environ,{'CURSEFORGE_PROVIDER':'cfwidget'}):actual=build_script_args('curseforge',args)
  self.assertEqual(actual,['--max','0','--recent-pages','200','--public-catalog'])

 def test_catalog_mode_defaults_to_full_page_cap_when_pages_were_not_supplied(self):
  sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
  from collector_worker import build_script_args,parse_args
  with patch.object(sys,'argv',['collector_worker.py','--platform','curseforge','--workspace','/tmp/cf-workspace','--source-root',str(Path(__file__).resolve().parents[3]),'--mode','catalog']):args=parse_args()
  with patch.dict(os.environ,{'CURSEFORGE_PROVIDER':'cfwidget'}):actual=build_script_args('curseforge',args)
  self.assertEqual(actual,['--max','0','--recent-pages','200','--public-catalog'])

 def test_catalog_resumes_from_saved_page_when_page_cap_is_expanded(self):
  class Full(Transport):
   def get(self,route):
    self.calls.append(route)
    if '/browse/' in route:
     page=2 if route.endswith('/2') else 1
     return {'status':'success','page':str(page),'pages':2,'refreshed':1791290528,'packs':[pack(page)]},{'sha256':'fixture'}
    ident=int(route.rsplit('/',1)[-1])
    return {**pack(ident),'description':'detail-'+str(ident),'links':[{'link':f'https://www.curseforge.com/minecraft/modpacks/pack-{ident}'}],'versions':[],'status':'success'},{'sha256':'fixture-detail'}
  with tempfile.TemporaryDirectory() as temp:
   raw=Path(temp)/'raw.json';side=Path(temp)/'data.js';checkpoint=Path(temp)/'state'/'checkpoint.json';raw.write_text('[]')
   first=Full();partial=catalog.refresh_catalog(raw,side,recent_pages=1,transport=first,checkpoint_path=checkpoint)
   self.assertEqual(partial['details']['pagesObserved'],1);self.assertFalse(partial['requestCompleted'])
   resumed=catalog.refresh_catalog(raw,side,recent_pages=2,transport=Full(),checkpoint_path=checkpoint)
   self.assertEqual(resumed['details']['resumedFromPage'],1)
   self.assertEqual(resumed['details']['pagesObserved'],2)
   self.assertTrue(resumed['requestCompleted'])
   self.assertTrue(json.loads(checkpoint.read_text())['complete'])

 def test_resumed_catalog_clears_stale_end_time_and_persists_request_failure(self):
  class SnapshotTransport:
   def __init__(self,checkpoint=None,fail_page=None):self.calls=[];self.checkpoint=checkpoint;self.fail_page=fail_page;self.state_at_first_request=None
   def get(self,route):
    self.calls.append(route)
    if self.checkpoint and self.state_at_first_request is None:
     state=json.loads(self.checkpoint.read_text());self.state_at_first_request=(state.get('runStatus'),state.get('endedAt'))
    if '/browse/' in route:
     page=int(route.rsplit('/',1)[-1]) if route.rsplit('/',1)[-1].isdigit() else 1
     if self.fail_page==page:raise catalog.CatalogRefusal('HTTP 503 fixture')
     return {'status':'success','page':str(page),'pages':2,'packs':[pack(page)]},{'sourceUrl':catalog.ORIGIN+route,'observedAt':'2026-10-06T13:00:00Z'}
    ident=int(route.rsplit('/',1)[-1])
    return {**pack(ident),'description':'detail-'+str(ident),'links':[{'link':f'https://www.curseforge.com/minecraft/modpacks/pack-{ident}'}],'versions':[],'status':'success'},{'sourceUrl':catalog.ORIGIN+route,'observedAt':'2026-10-06T13:00:01Z'}
  with tempfile.TemporaryDirectory() as d:
   raw=Path(d)/'raw.json';side=Path(d)/'data.js';checkpoint=Path(d)/'state'/'checkpoint.json';raw.write_text('[]')
   first=catalog.refresh_catalog(raw,side,recent_pages=1,transport=SnapshotTransport(),checkpoint_path=checkpoint)
   previous=json.loads(checkpoint.read_text());previous_end=previous['endedAt']
   self.assertEqual(previous['runStatus'],'finished')
   self.assertEqual(first['details']['pagesObserved'],1)
   resumed_transport=SnapshotTransport(checkpoint=checkpoint,fail_page=2)
   result=catalog.refresh_catalog(raw,side,recent_pages=2,transport=resumed_transport,checkpoint_path=checkpoint)
   after=json.loads(checkpoint.read_text())
   self.assertEqual(resumed_transport.state_at_first_request,('running',None))
   self.assertNotEqual(after['endedAt'],previous_end)
   self.assertEqual(after['runStatus'],'failed')
   self.assertIn('HTTP 503 fixture',after['lastError'])
   self.assertFalse(after['complete'])
   self.assertFalse(result['requestCompleted'])

 def test_unexpected_resumed_catalog_exception_is_recorded_before_propagating(self):
  class StableTransport:
   def get(self,route):
    if '/browse/' in route:
     page=int(route.rsplit('/',1)[-1]) if route.rsplit('/',1)[-1].isdigit() else 1
     return {'status':'success','page':str(page),'pages':2,'packs':[pack(page)]},{'sourceUrl':catalog.ORIGIN+route,'observedAt':'2026-10-06T13:00:00Z'}
    ident=int(route.rsplit('/',1)[-1])
    return {**pack(ident),'description':'detail-'+str(ident),'links':[{'link':f'https://www.curseforge.com/minecraft/modpacks/pack-{ident}'}],'versions':[],'status':'success'},{'sourceUrl':catalog.ORIGIN+route,'observedAt':'2026-10-06T13:00:01Z'}
  class CrashAtPageTwo(StableTransport):
   def get(self,route):
    if '/browse/' in route and route.endswith('/2'):raise RuntimeError('fixture programming failure')
    return super().get(route)
  with tempfile.TemporaryDirectory() as d:
   raw=Path(d)/'raw.json';side=Path(d)/'data.js';checkpoint=Path(d)/'state'/'checkpoint.json';raw.write_text('[]')
   catalog.refresh_catalog(raw,side,recent_pages=1,transport=StableTransport(),checkpoint_path=checkpoint)
   with self.assertRaisesRegex(RuntimeError,'fixture programming failure'):
    catalog.refresh_catalog(raw,side,recent_pages=2,transport=CrashAtPageTwo(),checkpoint_path=checkpoint)
   after=json.loads(checkpoint.read_text())
   self.assertEqual(after['runStatus'],'failed')
   self.assertIn('fixture programming failure',after['lastError'])
   self.assertFalse(after['complete'])

 def test_catalog_hydrates_new_and_changed_provider_projects_in_the_same_task(self):
  class Full(Transport):
   def get(self,route):
    data,obs=super().get(route)
    if '/browse/' not in route:
     ident=int(route.rsplit('/',1)[-1]);data={**data,'id':ident,'description':'完整正文-'+str(ident),'versions':[{'targets':[{'type':'modloader','name':'fabric'},{'type':'game','name':'minecraft','version':'1.20.1'}]}]}
    return data,obs
  with tempfile.TemporaryDirectory() as d:
   raw=Path(d)/'raw.json';side=Path(d)/'data.js';old={'project_id':'1','url':'https://www.curseforge.com/minecraft/modpacks/old-pack','description':'旧摘要','releases':[{'id':99}],'catalog_observation':{'provider':'modpacks-ch','providerUpdated':1,'synopsis':'旧摘要'}};raw.write_text(json.dumps([old]));t=Full()
   with patch.dict(os.environ,{'MC_DESKTOP_COLLECTION_RESULT':str(Path(d)/'result.json')}):r=catalog.refresh_catalog(raw,side,transport=t)
   rows=json.loads(raw.read_text());self.assertEqual(rows[0]['description'],'完整正文-1');self.assertEqual(rows[1]['description'],'完整正文-2');self.assertEqual(rows[1]['loaders'],['Fabric']);self.assertEqual(rows[0]['releases'],[{'id':99}]);self.assertIn('/public/curseforge/1',t.calls)
   self.assertEqual(r['details']['detailsObserved'],2)

 def test_browse_observation_preserves_loaded_detail_evidence_on_unchanged_projects(self):
  detail={**pack(1),'description':'完整正文','links':[{'link':'https://www.curseforge.com/minecraft/modpacks/a'}]}
  old=catalog.merge_pack(detail,None,{'sourceUrl':catalog.ORIGIN+'/public/curseforge/1'})
  current=catalog.merge_pack(pack(1),old,{'sourceUrl':catalog.ORIGIN+'/public/curseforge/browse/updated'})
  self.assertTrue(current['catalog_observation']['detailsLoaded']);self.assertEqual(current['description'],'完整正文')

 def test_project_details_restore_full_body_and_explicit_loader_targets(self):
  detail={**pack(2),'description':'<p>完整正文</p><img src="https://media.forgecdn.net/a.jpg">','links':[{'link':'https://www.curseforge.com/minecraft/modpacks/new-pack'}],'versions':[{'id':3,'targets':[{'type':'modloader','name':'neoforge','version':'21.1.1'},{'type':'game','name':'minecraft','version':'1.21.1'}]}]}
  row=catalog.merge_pack(detail,None,{'sourceUrl':catalog.ORIGIN+'/public/curseforge/2'})
  self.assertEqual(row['description'],detail['description']);self.assertEqual(row['loaders'],['NeoForge']);self.assertIn('1.21.1',row['all_versions']);self.assertIn('https://media.forgecdn.net/a.jpg',row['gallery']);self.assertEqual(row['releases'],[])
 def test_details_backfill_only_observed_new_projects_and_preserves_file_history(self):
  with tempfile.TemporaryDirectory() as d:
   raw=Path(d)/'raw.json';side=Path(d)/'data.js';rows=[{'project_id':'1','url':'https://www.curseforge.com/minecraft/modpacks/old-pack','description':'保留完整正文','releases':[{'id':99}]},{'project_id':'2','url':'https://www.curseforge.com/minecraft/modpacks/new-pack','description':'简短摘要','releases':[],'catalog_observation':{'provider':'modpacks-ch','sourceUrl':catalog.ORIGIN+'/public/curseforge/2','synopsis':'简短摘要'}}];raw.write_text(json.dumps(rows));t=Transport()
   with patch.dict(os.environ,{'MC_DESKTOP_COLLECTION_RESULT':str(Path(d)/'result.json')}):result=catalog.refresh_project_details(raw,side,transport=t)
   actual=json.loads(raw.read_text());self.assertEqual(t.calls,['/public/curseforge/2']);self.assertEqual(actual[0],rows[0]);self.assertEqual(actual[1]['releases'],[]);self.assertTrue(actual[1]['catalog_observation']['detailsLoaded']);self.assertEqual(result['details']['coverage'],'third-party-details')
 def test_pagination_adds_verified_new_id_without_losing_old_rich_data(self):
  with tempfile.TemporaryDirectory() as d:
   raw=Path(d)/'raw.json';side=Path(d)/'data.js';old={'project_id':'1','title':'旧标题','url':'https://www.curseforge.com/minecraft/modpacks/old-pack','downloads':200,'description':'原站完整正文比摘要更长','date_modified':'2026-10-06 16:00:00','releases':[{'file_id':99,'changelog':'retain'}],'gallery':['https://example.com/a.jpg']};raw.write_text(json.dumps([old]));t=Transport()
   with patch.dict('os.environ',{'MC_DESKTOP_COLLECTION_RESULT':str(Path(d)/'result.json')}):r=catalog.refresh_catalog(raw,side,transport=t)
   rows=json.loads(raw.read_text());self.assertEqual([x['project_id'] for x in rows],['1','2']);self.assertEqual(rows[0]['description'],old['description']);self.assertEqual(rows[0]['downloads'],200);self.assertEqual(rows[0]['releases'],old['releases']);self.assertEqual(rows[0]['date_modified'],old['date_modified']);self.assertEqual(rows[1]['url'],'https://www.curseforge.com/minecraft/modpacks/new-pack');self.assertEqual(r['details']['pagesObserved'],2);self.assertFalse(r['details']['fullRefresh']);self.assertEqual(r['status'],'partial')

 def test_public_catalog_scan_resumes_after_last_verified_page_and_keeps_old_ids(self):
  class SnapshotTransport:
   def __init__(self,fail_page=None):self.calls=[];self.fail_page=fail_page
   def get(self,route):
    self.calls.append(route)
    if '/browse/' in route:
     page=int(route.rsplit('/',1)[-1]) if route.rsplit('/',1)[-1].isdigit() else 1
     if self.fail_page==page:raise catalog.CatalogRefusal('HTTP 503 fixture')
     refreshed=1791290528 if page==1 else '1791290528'
     return {'status':'success','page':str(page),'pages':2,'refreshed':refreshed,'packs':[pack(page)]},{'sourceUrl':catalog.ORIGIN+route,'observedAt':'2026-10-06T13:00:00Z','sha256':'fixture'}
    ident=int(route.rsplit('/',1)[-1])
    return {**pack(ident),'description':'detail-'+str(ident),'links':[{'link':f'https://www.curseforge.com/minecraft/modpacks/pack-{ident}'}],'versions':[],'status':'success'},{'sourceUrl':catalog.ORIGIN+route,'observedAt':'2026-10-06T13:00:01Z','sha256':'fixture-detail'}
  with tempfile.TemporaryDirectory() as d:
   raw=Path(d)/'raw.json';side=Path(d)/'data.js';checkpoint=Path(d)/'collector-state'/'cf-checkpoint.json'
   raw.write_text(json.dumps([{'project_id':'99','url':'https://www.curseforge.com/minecraft/modpacks/old','releases':[{'id':990}]}]))
   first=SnapshotTransport(fail_page=2);partial=catalog.refresh_catalog(raw,side,transport=first,checkpoint_path=checkpoint)
   self.assertEqual(partial['details']['pagesObserved'],1);self.assertFalse(partial['requestCompleted']);self.assertEqual(partial['details']['checkpointPage'],1)
   second=SnapshotTransport();complete=catalog.refresh_catalog(raw,side,transport=second,checkpoint_path=checkpoint)
   self.assertEqual(second.calls,['/public/curseforge/browse/updated','/public/curseforge/browse/updated/2','/public/curseforge/2','/public/curseforge/browse/updated','/public/curseforge/browse/updated/2'])
   rows=json.loads(raw.read_text());self.assertEqual({row['project_id'] for row in rows},{'99','1','2'});self.assertEqual(rows[0]['releases'],[{'id':990}])
   self.assertEqual(complete['details']['pagesObserved'],2);self.assertEqual(complete['details']['observedCount'],2);self.assertEqual(complete['details']['newCount'],2)
   self.assertEqual(complete['details']['resumedFromPage'],1);self.assertTrue(complete['requestCompleted']);self.assertEqual(complete['details']['duplicateCount'],0)
 def test_public_catalog_treats_refresh_tokens_as_per_page_metadata_and_saves_responses(self):
  class ChangedSnapshotTransport:
   def __init__(self):self.calls=[]
   def get(self,route):
    self.calls.append(route)
    if '/browse/' in route:
     page=int(route.rsplit('/',1)[-1]) if route.rsplit('/',1)[-1].isdigit() else 1
     refreshed=1791290528 if page==1 else '1791290588'
     return {'status':'success','page':str(page),'pages':2,'refreshed':refreshed,'packs':[pack(page)]},{'sourceUrl':catalog.ORIGIN+route,'observedAt':'2026-10-06T13:00:00Z','sha256':'fixture'}
    ident=int(route.rsplit('/',1)[-1])
    return {**pack(ident),'description':'detail-'+str(ident),'links':[{'link':f'https://www.curseforge.com/minecraft/modpacks/pack-{ident}'}],'versions':[],'status':'success'},{'sourceUrl':catalog.ORIGIN+route,'observedAt':'2026-10-06T13:00:01Z','sha256':'fixture-detail'}
  with tempfile.TemporaryDirectory() as d:
   raw=Path(d)/'raw.json';side=Path(d)/'data.js';checkpoint=Path(d)/'collector-state'/'cf-checkpoint.json';raw.write_text('[]');t=ChangedSnapshotTransport()
   result=catalog.refresh_catalog(raw,side,recent_pages=2,transport=t,checkpoint_path=checkpoint)
   self.assertEqual(result['details']['pagesObserved'],2);self.assertTrue(result['requestCompleted'])
   self.assertEqual(result['details']['providerRefreshTokensByPage'],{'1':'1791290528','2':'1791290588'})
   self.assertTrue(result['details']['coverageValidation']['complete'])
   self.assertTrue(result['details']['fullPageResponsesSaved'])
   manifest=json.loads(checkpoint.read_text());page1=json.loads((checkpoint.parent/manifest['pageDirectory']/'page-0001.json').read_text())
   self.assertEqual(page1['providerResponse']['packs'][0]['id'],1)

 def test_public_catalog_records_page_count_drift_and_keeps_visible_window_partial(self):
  class DriftingTransport:
   def __init__(self):self.calls=[]
   def get(self,route):
    self.calls.append(route)
    if '/browse/' in route:
     page=int(route.rsplit('/',1)[-1]) if route.rsplit('/',1)[-1].isdigit() else 1
     count=2 if page==1 and len(self.calls)==1 else 3
     return {'status':'success','page':str(page),'pages':count,'refreshed':1791290528+page,'packs':[pack(page)]},{'sourceUrl':catalog.ORIGIN+route,'observedAt':'2026-10-06T13:00:00Z','sha256':'fixture'}
    ident=int(route.rsplit('/',1)[-1])
    return {**pack(ident),'description':'detail-'+str(ident),'links':[{'link':f'https://www.curseforge.com/minecraft/modpacks/pack-{ident}'}],'versions':[],'status':'success'},{'sourceUrl':catalog.ORIGIN+route,'observedAt':'2026-10-06T13:00:01Z','sha256':'fixture-detail'}
  with tempfile.TemporaryDirectory() as d:
   raw=Path(d)/'raw.json';side=Path(d)/'data.js';raw.write_text('[]');transport=DriftingTransport()
   result=catalog.refresh_catalog(raw,side,recent_pages=3,transport=transport,checkpoint_path=Path(d)/'state'/'checkpoint.json')
   self.assertEqual(result['details']['pagesObserved'],3)
   self.assertTrue(result['details']['paginationDrift'])
   self.assertFalse(result['requestCompleted']);self.assertTrue(result['truncated'])
   self.assertEqual(result['details']['uniqueIdsObserved'],3)
 def test_refusal_stops_without_provider_switch_or_deleting_old_ids(self):
  with tempfile.TemporaryDirectory() as d:
   raw=Path(d)/'raw.json';side=Path(d)/'data.js';raw.write_text(json.dumps([{'project_id':'1','url':'https://www.curseforge.com/minecraft/modpacks/p','releases':[{'id':99}]}]));t=Transport(fail=True)
   with patch.dict('os.environ',{'MC_DESKTOP_COLLECTION_RESULT':str(Path(d)/'result.json')}):r=catalog.refresh_catalog(raw,side,transport=t)
   self.assertEqual(r['failedRequests'],1);self.assertEqual(len(t.calls),2);self.assertEqual(json.loads(raw.read_text())[0]['releases'],[{'id':99}])
 def test_wrong_provider_or_url_cannot_become_curseforge_record(self):
  with self.assertRaises(ValueError):catalog.merge_pack({**pack(),'provider':'modrinth'},None,{})
  with self.assertRaises(ValueError):catalog.merge_pack({**pack(),'links':[{'link':'https://evil.invalid/p'}]},None,{})
 def test_transport_rejects_unapproved_host_paths_and_never_sends_credentials(self):
  t=catalog.PublicCatalogTransport()
  handler=next(h for h in t.opener.handlers if isinstance(h,urllib.request.HTTPSHandler))
  self.assertTrue(handler._context.check_hostname);self.assertEqual(handler._context.verify_mode,ssl.CERT_REQUIRED);self.assertGreater(handler._context.cert_store_stats()['x509_ca'],0)
  for route in ['/public/curseforge/import/test','/public/curseforge/1/2/server/linux','https://api.curseforge.com/v1/mods/1']:
   with self.assertRaises(ValueError):t.get(route)

 def test_explicit_catalog_worker_builds_current_outputs_and_partial_contract(self):
  sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
  from collector_worker import run_selected_collector
  root=Path(__file__).resolve().parents[3]
  with tempfile.TemporaryDirectory() as d:
   workspace=Path(d);raw=workspace/'crawler_output/curseforge_modpacks.json';raw.parent.mkdir();raw.write_text(json.dumps([{'project_id':'1','title':'旧标题','url':'https://www.curseforge.com/minecraft/modpacks/old-pack','releases':[{'id':99}]}]))
   args=SimpleNamespace(platform='curseforge',workspace=d,source_root=str(root),limit=100,pages=None,mode='catalog',until=None)
   with patch.dict(os.environ,{'CURSEFORGE_PROVIDER':'cfwidget'}),patch.object(catalog,'PublicCatalogTransport',return_value=Transport()):run_selected_collector(args)
   contract=json.loads((workspace/'build/desktop_update_result.json').read_text())
   self.assertEqual(contract['outcome'],'partial_update');self.assertEqual(contract['crawlerResult']['details']['provider'],'modpacks-ch');self.assertTrue(contract['previousIdsPreserved']);self.assertEqual(contract['rawCount'],2);self.assertTrue((workspace/'build/desktop_snapshot_manifest.json').exists());self.assertEqual(len(json.loads((workspace/'crawler_output/curseforge_modpacks.json').read_text())),2)

 def test_daily_recent_window_preserves_the_full_catalog_checkpoint(self):
  sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
  from collector_worker import run_selected_collector
  root=Path(__file__).resolve().parents[3]
  class RecentTransport(Transport):
   def get(self,route):
    if '/browse/' in route:return super().get(route)
    ident=int(route.rsplit('/',1)[-1]);self.calls.append(route)
    return {**pack(ident),'status':'success','description':'Fixture detail','links':[{'link':f'https://www.curseforge.com/minecraft/modpacks/pack-{ident}'}]},{'sha256':'fixture'}
  with tempfile.TemporaryDirectory() as d:
   data_root=Path(d);workspace=data_root/'incoming/daily-job';raw=workspace/'crawler_output/curseforge_modpacks.json';raw.parent.mkdir(parents=True);raw.write_text(json.dumps([{'project_id':'1','title':'Old','url':'https://www.curseforge.com/minecraft/modpacks/old-pack','releases':[{'id':99}]}]))
   checkpoint=data_root/'collector-state/curseforge-public-catalog-v2/checkpoint.json';checkpoint.parent.mkdir(parents=True)
   checkpoint.write_text(json.dumps({'schema':2,'provider':'modpacks-ch','requestedPages':200,'providerPages':200,'lastCompletedPage':124,'complete':False,'pageDigests':{},'pageDirectory':'curseforge-public-catalog-pages-20261007T090750450509Z-52053'}));before=checkpoint.read_bytes()
   args=SimpleNamespace(platform='curseforge',workspace=str(workspace),source_root=str(root),limit=None,pages=2,mode='recent',until=None)
   with patch.dict(os.environ,{'CURSEFORGE_PROVIDER':'cfwidget'}),patch.object(catalog,'PublicCatalogTransport',return_value=RecentTransport()):run_selected_collector(args)
   self.assertEqual(checkpoint.read_bytes(),before)
   recent=data_root/'collector-state/curseforge-public-catalog-recent-v2/daily-job-checkpoint.json'
   self.assertTrue(recent.exists());self.assertEqual(json.loads(recent.read_text())['requestedPages'],2)

 def test_cli_resolves_configuration_before_starting_requests(self):
  root=Path(__file__).resolve().parents[3]
  with tempfile.TemporaryDirectory() as d:
   result=subprocess.run([sys.executable,'-I',str(root/'apps/desktop/collector_worker.py'),'--platform','curseforge','--source-root',str(root),'--workspace',d,'--mode','catalog'],env={**os.environ,'CURSEFORGE_PROVIDER':'invalid'},capture_output=True,text=True)
   self.assertNotEqual(result.returncode,0);self.assertIn('CURSEFORGE_PROVIDER must be',result.stdout+result.stderr);self.assertNotIn('No module named',result.stdout+result.stderr)

 def test_metadata_worker_uses_only_detail_routes_and_current_snapshot_pipeline(self):
  sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
  from collector_worker import run_selected_collector
  root=Path(__file__).resolve().parents[3]
  with tempfile.TemporaryDirectory() as d:
   workspace=Path(d);raw=workspace/'crawler_output/curseforge_modpacks.json';raw.parent.mkdir();raw.write_text(json.dumps([{'project_id':'2','url':'https://www.curseforge.com/minecraft/modpacks/new-pack','description':'简短摘要','releases':[],'catalog_observation':{'provider':'modpacks-ch','sourceUrl':catalog.ORIGIN+'/public/curseforge/2','synopsis':'简短摘要'}}]))
   args=SimpleNamespace(platform='curseforge',workspace=d,source_root=str(root),limit=None,pages=None,mode='metadata',until=None);t=Transport()
   with patch.dict(os.environ,{'CURSEFORGE_PROVIDER':'cfwidget'}),patch.object(catalog,'PublicCatalogTransport',return_value=t):run_selected_collector(args)
   contract=json.loads((workspace/'build/desktop_update_result.json').read_text());self.assertEqual(t.calls,['/public/curseforge/2']);self.assertEqual(contract['outcome'],'partial_update');self.assertTrue(contract['previousIdsPreserved']);self.assertTrue((workspace/'build/desktop_snapshot_manifest.json').exists())

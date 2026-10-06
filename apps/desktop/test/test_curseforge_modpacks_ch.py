import unittest,tempfile,json,sys,urllib.error,os,subprocess
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
 def test_daily_worker_uses_public_catalog_without_manual_mode_override(self):
  sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
  from collector_worker import build_script_args
  args=SimpleNamespace(mode=None,limit=None,pages=2,source_root=str(Path(__file__).resolve().parents[3]))
  with patch.dict(os.environ,{'CURSEFORGE_PROVIDER':'cfwidget'}):
   actual=build_script_args('curseforge',args)
  self.assertIn('--public-catalog',actual);self.assertIn('--recent-pages',actual)

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

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from collector_worker import merge_catalog_with_existing, build_script_args
from types import SimpleNamespace


class CatalogReleaseRefresh(unittest.TestCase):
    def test_failed_empty_catalog_preserves_ids_and_reports_source_failure(self):
        from collector_worker import collect_output_contract
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for folder in ['build','crawler_output','converted_output/data']:(root/folder).mkdir(parents=True)
            raw=root/'crawler_output/modrinth_modpacks.json'
            sidecar=root/'converted_output/data/modrinth_data.js'
            raw.write_text('[]');sidecar.write_text('window.modrinthModpacksData = [];')
            old={'project_id':'old1','title':'Retained source','latest_version':'0.3'}
            result={'platform':'modrinth','status':'failed','requestCompleted':False,'fetchedCount':0,'failedRequests':1,'errors':['offset=0: certificate verify failed']}
            (root/'build/desktop_collection_result.json').write_text(json.dumps(result))
            merge_catalog_with_existing(root,'modrinth',[old])
            self.assertEqual(json.loads(raw.read_text()),[old])
            self.assertEqual(json.loads(sidecar.read_text().split('=',1)[1].rstrip(';\n')),[old])
            contract=collect_output_contract(root,'modrinth',0,{'raw':{'sha256':None},'sidecar':{'sha256':None}})
            self.assertEqual(contract['outcome'],'failed')
            self.assertIn('certificate verify failed',contract['error'])

    def test_fresh_catalog_history_replaces_stale_release_priority_and_keeps_older_entries(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw = root / 'crawler_output/bbsmc_modpacks.json'
            modern = root / 'converted_output/data/bbsmc_data.js'
            raw.parent.mkdir(parents=True)
            modern.parent.mkdir(parents=True)
            new = {'project_id': 'fool', 'title': '愚者 - The Fool',
                   'versions_data': [{'version_number': '0.3.0', 'date_published': '2026-09-30'}]}
            old = {'project_id': 'fool', 'latest_version': '0.2.0',
                   'releases': [{'version_number': '0.2.0', 'date_published': '2026-02-16'}]}
            raw.write_text(json.dumps([new]))
            modern.write_text('window.bbsmcModpacksData = '+json.dumps([new])+';')
            merge_catalog_with_existing(root, 'bbsmc', [old])
            actual = json.loads(raw.read_text())[0]
            self.assertEqual(actual['latest_version'], '0.3.0')
            self.assertEqual([x['version_number'] for x in actual['releases']], ['0.3.0', '0.2.0'])
            self.assertEqual(json.loads(modern.read_text().split('=', 1)[1].rstrip(';\n'))[0]['latest_version'], '0.3.0')


class FullCatalogScope(unittest.TestCase):
    def test_daily_catalog_requests_all_metadata_with_incremental_version_checks(self):
        args=SimpleNamespace(limit=None,mode='daily')
        for platform in ('bbsmc','xyebbs','modrinth'):
            values=build_script_args(platform,args)
            self.assertIn('--daily',values)
            self.assertEqual(values[values.index('--max')+1],'0')
    def test_full_catalog_enriches_all_records_instead_of_first_hundred(self):
        args=SimpleNamespace(limit=None, mode='catalog')
        for platform in ('bbsmc','xyebbs'):
            values=build_script_args(platform,args)
            self.assertEqual(values[values.index('--max')+1],'0')
            self.assertEqual(values[values.index('--enrich')+1],'100000')


class PartialCatalogContract(unittest.TestCase):
 def test_completed_catalog_keeps_successful_versions_but_rejects_denial_or_incomplete_pages(self):
  from collector_worker import collect_output_contract
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp)
   for folder in ['build','crawler_output','converted_output/data']:(root/folder).mkdir(parents=True)
   (root/'crawler_output/bbsmc_modpacks.json').write_text('[{"project_id":"fool"}]')
   (root/'converted_output/data/bbsmc_data.js').write_text('window.bbsmcModpacksData = [{"project_id":"fool"}];')
   result={'platform':'bbsmc','status':'partial','requestCompleted':False,'fetchedCount':1,'failedRequests':1,'details':{'catalogCompleted':True,'versionsChecked':1,'sourceStopped':False,'versionParseFailures':0}}
   before={'raw':{'sha256':None},'sidecar':{'sha256':None}}
   def check():
    (root/'build/desktop_collection_result.json').write_text(json.dumps(result))
    return collect_output_contract(root,'bbsmc',0,before)['outcome']
   self.assertEqual(check(),'partial_update')
   result['details']['sourceStopped']=True
   self.assertEqual(check(),'failed')
   result['details']['sourceStopped']=False;result['details']['catalogCompleted']=False
   self.assertEqual(check(),'failed')

if __name__ == '__main__':
    unittest.main()

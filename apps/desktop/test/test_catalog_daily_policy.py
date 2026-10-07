import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import contextlib
import io
import os

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
import catalog_refresh_policy as policy


class DailyPolicy(unittest.TestCase):
    def test_all_changed_and_new_projects_plus_oldest_unchanged_rotation(self):
        prior=[{'project_id':str(i),'date_modified':'same','version_attempted_at':f'2026-10-{i:02d}'} for i in range(1,5)]
        current=[dict(p) for p in prior]+[{'project_id':'new','date_modified':'now'}]
        current[3]['date_modified']='changed'
        chosen=policy.select_daily_versions(current,prior,lambda row:row,rotation=1)
        self.assertEqual({r['project_id'] for r in chosen},{'new','4','1'})
        self.assertEqual(len(current),5)

    def test_missing_dates_are_bounded_and_rotate_by_attempt_instead_of_repeating(self):
        prior=[{'project_id':str(i),'version_attempted_at':str(i)} for i in range(5)]
        chosen=policy.select_daily_versions(prior,prior,lambda row:row,rotation=2)
        self.assertEqual([r['project_id'] for r in chosen],['0','1'])

    def test_fresh_version_data_wins_while_unchanged_history_links_and_times_are_preserved(self):
        old={'project_id':'x','latest_version':'0.3','releases':[{'version_number':'0.3'}],'download_links':[{'url':'https://pan.quark.cn/s/evidence'}],'version_checked_at':'old-time','version_attempted_at':'old-attempt'}
        current={'project_id':'x','title':'Fresh title','date_modified':'fresh','download_links':[{'url':'https://example.com/official'}]}
        policy.retain_cached_versions(current,old)
        self.assertEqual(current['latest_version'],'0.3');self.assertEqual(current['title'],'Fresh title')
        self.assertEqual(current['download_links'],old['download_links']);self.assertEqual(current['version_checked_at'],'old-time')
        fresh={'project_id':'x','versions_data':[{'version_number':'0.3.1'}],'download_links':[{'url':'https://example.com/new'}]}
        policy.retain_cached_versions(fresh,old)
        self.assertNotIn('releases',fresh);self.assertNotIn('latest_version',fresh)
        self.assertEqual(fresh['download_links'][0]['url'],'https://example.com/new')

    def test_invalid_prior_snapshot_is_reported_instead_of_silently_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'prior.json';p.write_text('{}')
            with self.assertRaises(ValueError):policy.load_previous(p)

    def test_changed_catalog_release_id_is_selected_even_if_source_date_did_not_change(self):
        prior=[{'project_id':'x','date_modified':'same','catalog_version_id':'v1'}]
        current=[dict(prior[0],catalog_version_id='v2')]
        self.assertEqual(policy.select_daily_versions(current,prior,lambda row:row,rotation=0),current)

    def test_failed_version_detail_is_requeued_even_after_catalog_date_was_adopted(self):
        prior=[{'project_id':'x','date_modified':'today','version_refresh_pending':True}]
        current=[{'project_id':'x','date_modified':'today'}]
        self.assertEqual(policy.select_daily_versions(current,prior,lambda row:row,rotation=0),current)


class RealDailyCollectors(unittest.TestCase):
    def test_both_catalogs_keep_all_ids_but_rotate_only_fifty_unchanged_versions(self):
        import bbsmc_crawler as b,xyebbs_crawler as x
        for platform,module,cls,raw_row,search,version,run in [
            ('bbsmc',b,b.BbsmcCrawler,lambda i:{'project_id':str(i),'title':f'Pack {i}','date_modified':'2026-10-01T00:00:00Z'},'search_all_projects','fetch_project_versions',b.crawl_bbsmc),
            ('xyebbs',x,x.XyebbsCrawler,lambda i:{'id':i,'name':f'Pack {i}','updateDate':'2026-10-01T00:00:00Z'},'fetch_all_resources','fetch_resource_releases',x.crawl_xyebbs),
        ]:
            with self.subTest(platform=platform),tempfile.TemporaryDirectory() as d:
                root=Path(d);(root/'crawler_output').mkdir()
                raw=[raw_row(i) for i in range(1,101)]
                prior=[dict(module.standardize_pack(item),releases=[{'version_number':'0.3'}],version_checked_at='2026-10-01',download_links=[{'url':'https://pan.quark.cn/s/retained'}]) for item in raw]
                path=root/'crawler_output'/f'{platform}_modpacks.json';path.write_text(json.dumps(prior))
                def directory(self,*args,**kwargs):self.catalog_completed=True;return [dict(item) for item in raw]
                env={'MC_DESKTOP_WORKSPACE':d,'MC_DESKTOP_COLLECTION_RESULT':str(root/'result.json')}
                with patch.dict(os.environ,env),patch.object(cls,search,directory),patch.object(cls,version,return_value=[]) as versions,contextlib.redirect_stdout(io.StringIO()):
                    run(daily=True)
                    first={str(call.args[0]) for call in versions.call_args_list}
                    self.assertEqual(len(first),50)
                    versions.reset_mock();run(daily=True)
                    second={str(call.args[0]) for call in versions.call_args_list}
                    self.assertEqual(len(second),50);self.assertFalse(first & second)
                current=json.loads(path.read_text())
                self.assertEqual({p['project_id'] for p in current},{p['project_id'] for p in prior})
                self.assertTrue(all(p['releases'][0]['version_number']=='0.3' for p in current))
                self.assertTrue(all(p['download_links'][0]['url']=='https://pan.quark.cn/s/retained' for p in current))

    def test_modrinth_reuses_exact_id_only_and_preserves_real_observation_time(self):
        import modrinth_crawler as m
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);raw=root/'crawler_output/modrinth_modpacks.json';raw.parent.mkdir()
            raw.write_text(json.dumps([{'project_id':'p1','releases':[{'id':'v1','project_id':'p1','version_number':'0.3'}],'version_checked_at':'real-old-time'}]))
            hits=[{'project_id':'p1','title':'Same','latest_version':'v1'},{'project_id':'p2','title':'New','latest_version':'v2'}]
            fresh={'v2':{'id':'v2','project_id':'p2','version_number':'0.3.1'}}
            with patch.object(m,'OUTPUT_JSON',str(raw)),patch.object(m,'OUTPUT_JS',str(root/'converted_output/data/modrinth_data.js')),patch.object(m,'fetch_page',return_value={'hits':hits,'total_hits':2}),patch.object(m,'fetch_versions',return_value=fresh) as versions,patch.object(m,'write_collection_result') as contract,contextlib.redirect_stdout(io.StringIO()):
                m.main(daily=True)
            versions.assert_called_once_with(['v2'])
            rows=json.loads(raw.read_text())
            self.assertEqual(rows[0]['version_checked_at'],'real-old-time')
            self.assertEqual(rows[1]['latest_version'],'0.3.1')
            self.assertEqual(contract.call_args.kwargs['details']['versionsReused'],1)

if __name__=='__main__':unittest.main()

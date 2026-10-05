import json
import io
from contextlib import redirect_stdout
import os
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path
from unittest.mock import patch


DESKTOP_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = DESKTOP_ROOT.parents[1]
if str(DESKTOP_ROOT) not in sys.path:
    sys.path.insert(0, str(DESKTOP_ROOT))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from collector_worker import PLATFORMS, build_script_args, collect_output_contract, file_state, run_selected_collector  # noqa: E402
import curseforge_full_crawler  # noqa: E402
import mcmod_full_crawler  # noqa: E402


class StubResponse:
    def __init__(self, payload, status=200):
        self.status = status
        self._payload = payload if isinstance(payload, bytes) else json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def read(self, limit=-1):
        return self._payload if limit < 0 else self._payload[:limit]

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class StubOpener:
    def __init__(self, urlopen):
        self.urlopen = urlopen

    def open(self, request, timeout=None):
        return self.urlopen(request, timeout=timeout)


class ControlledRequests:
    def __call__(self, request, timeout=None):
        url = request.full_url if hasattr(request, "full_url") else str(request)
        if "mcmod.cn/modpack/" in url:
            return StubResponse({}, status=404)
        if "api.modrinth.com/v2/search" in url:
            return StubResponse({
                "total_hits": 1,
                "hits": [{
                    "project_id": "mr-test",
                    "slug": "desktop-test-pack",
                    "title": "Desktop Test Pack",
                    "author": "fixture",
                    "description": "controlled Modrinth response",
                    "downloads": 7,
                    "follows": 2,
                    "versions": ["1.20.1"],
                    "categories": ["fabric", "adventure"],
                    "client_side": "required",
                    "server_side": "optional",
                }],
            })
        if "api.curseforge.com/v1/mods/search" in url:
            return StubResponse({
                "data": [{
                    "id": 42,
                    "slug": "curse-desktop-test",
                    "name": "Curse Desktop Test",
                    "summary": "controlled CurseForge response",
                    "downloadCount": 9,
                    "authors": [{"name": "fixture"}],
                    "links": {"websiteUrl": "https://www.curseforge.com/minecraft/modpacks/curse-desktop-test"},
                    "latestFilesIndexes": [{"gameVersion": "1.20.1", "modLoader": 4}],
                }],
                "pagination": {"totalCount": 1},
            })
        if "api.bbsmc.net/v2/search" in url:
            return StubResponse({
                "total_hits": 1,
                "hits": [{
                    "project_id": "bbs-test",
                    "slug": "bbs-test",
                    "project_type": "modpack",
                    "title": "BBSMC Desktop Test",
                    "author": "fixture",
                    "description": "controlled BBSMC response",
                    "versions": ["1.20.1"],
                    "categories": ["forge"],
                }],
            })
        if "resource-api.xyeidc.com/client/resources" in url:
            return StubResponse({
                "data": {
                    "count": 1,
                    "totalPages": 1,
                    "data": [{
                        "id": 73,
                        "identify": "xye-test",
                        "name": "XYE Desktop Test",
                        "description": "controlled XYEBBS response",
                        "versions": [{"name": "1.20.1"}],
                        "cores": [{"name": "Fabric"}],
                        "owner": {"username": "fixture"},
                        "stat": {"downloadCount": 3, "viewCount": 4},
                    }],
                },
            })
        if "api.bilibili.com/x/web-interface/nav" in url:
            return StubResponse({"code": 0, "data": {"isLogin": False, "wbi_img": {
                "img_url": "https://i.example.test/img.png",
                "sub_url": "https://i.example.test/sub.png",
            }}})
        if "api.bilibili.com/x/web-interface/wbi/search/type" in url:
            return StubResponse({"code": 0, "data": {"result": [{
                "bvid": "BVdesktop1",
                "title": "测试整合包发布 1.20.1",
                "author": "fixture",
                "pic": "https://i.example.test/cover.jpg",
                "pubdate": 1700000000,
            }]}})
        if "api.bilibili.com/x/web-interface/view" in url:
            return StubResponse({"code": 0, "data": {
                "aid": 101,
                "cid": 202,
                "desc": "Forge 版本发布说明",
                "stat": {"view": 10, "like": 2, "coin": 1, "favorite": 1, "share": 0, "reply": 0, "danmaku": 0},
                "duration": 60,
            }})
        if "api.bilibili.com/x/v2/reply/main" in url:
            return StubResponse({"code": 0, "data": {}})
        if "api.bilibili.com/x/player/wbi/v2" in url or "api.bilibili.com/x/player/v2" in url:
            return StubResponse({"code": 0, "data": {"subtitle": {"subtitles": []}}})
        raise AssertionError(f"unexpected controlled request: {url}")


def write_sidecar(path: Path, global_name: str, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"window.{global_name} = {json.dumps(value, ensure_ascii=False)};\n", encoding="utf-8")


class CollectorWorkerIntegrationTest(unittest.TestCase):
    def test_cfwidget_known_pack_cache_preserves_newer_history_and_stops_on_refusal(self):
        import curseforge_cfwidget as widget
        from curseforge_api_config import metadata_provider
        import existing_version_crawler as existing
        project={'id':42,'game':'minecraft','type':'Modpacks','title':'Cached title',
            'urls':{'curseforge':'https://www.curseforge.com/minecraft/modpacks/known-pack'},
            'downloads':{'total':150},'files':[{'id':7,'display':'Older known release',
                'uploaded_at':'2026-09-01T00:00:00Z','versions':['1.20.1','Forge']}]}
        latest={'version_number':'Newer stored release','date_published':'2026-10-03T00:00:00Z','changelog':'Keep details'}
        old={'project_id':'42','url':project['urls']['curseforge'],'title':'Known title','downloads':200,
             'date_modified':'2026-10-03 00:00:00','releases':[latest]}
        observation={'provider':'cfwidget','fetchedAt':'2026-10-04T00:00:00Z','providerLastFetch':None,'sha256':'fixture'}
        with patch.dict(os.environ,{'CURSEFORGE_API_KEY':'','CF_API_KEY':'','CURSEFORGE_API_KEY_FILE':'','CURSEFORGE_PROVIDER':''}):
            self.assertEqual(metadata_provider(),'cfwidget')
            with patch.object(existing,'get_widget_project',return_value=(project,observation)),patch.object(existing,'request_cf_json') as official:
                releases=existing.fetch_releases('curseforge','42');official.assert_not_called()
            self.assertEqual(releases[0]['files'][0]['url'],project['urls']['curseforge']+'/files/7')
            self.assertEqual(releases[0]['game_versions'],['1.20.1'])
        updated=widget.merge_project(old,project,observation)
        self.assertEqual(updated['downloads'],200);self.assertEqual(updated['title'],'Known title')
        self.assertEqual(updated['date_modified'],old['date_modified']);self.assertEqual(updated['releases'][0],latest)
        self.assertEqual(len(updated['releases']),2);self.assertIn('未提供',updated['acquisition_note'])
        for wrong in ({**project,'id':99},{**project,'game':'wow'},{**project,'type':'Mods'}):
            with self.assertRaises(ValueError):widget.merge_project(old,wrong,observation)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);raw=root/'raw.json';sidecar=root/'data.js'
            raw.write_text(json.dumps([old,{'project_id':'99','title':'Retain'}]),encoding='utf-8');sidecar.write_bytes(b'keep original sidecar')
            original=(raw.read_bytes(),sidecar.read_bytes())
            responses=[subprocess.CompletedProcess([],0,b'User-agent: *\nAllow: /\n__CFW_STATUS__:200',b''),subprocess.CompletedProcess([],0,b'\n__CFW_STATUS__:403',b'')]
            with patch.object(widget,'STOP',None),patch.object(widget,'ROBOTS',None),patch.object(widget,'LAST_REQUEST',0),patch.object(widget.shutil,'which',return_value='fixture-curl'),patch.object(widget.subprocess,'run',side_effect=responses) as request,patch.object(widget.time,'sleep'),patch.dict(os.environ,{'MC_DESKTOP_COLLECTION_RESULT':str(root/'result.json')}),redirect_stdout(io.StringIO()):
                result=widget.refresh_known(raw,sidecar,2)
                with self.assertRaises(widget.WidgetRefusal):widget.get_project('99')
                self.assertEqual(request.call_count,2)
                self.assertTrue(all('x-api-key' not in ' '.join(call.args[0]).lower() for call in request.call_args_list))
            self.assertEqual(result['fetchedCount'],0);self.assertEqual((raw.read_bytes(),sidecar.read_bytes()),original)

    def test_curseforge_refusal_stops_source_and_keeps_cached_bytes(self):
        cf = curseforge_full_crawler
        for code, body in ((302,b''),(401,b''),(403,b''),(412,b''),(200,b'<html><title>Security verification</title></html>')):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                raw = root / 'raw.json';sidecar = root / 'data.js'
                raw.write_bytes(b'[{"project_id":"old","title":"keep","downloads":1}]')
                sidecar.write_bytes(b'window.curseforgeModpacksData = [{"project_id":"old","title":"keep","downloads":1}];')
                original = (raw.read_bytes(),sidecar.read_bytes())
                result = subprocess.CompletedProcess([],0,body+b'\n__CF_STATUS__:'+str(code).encode(),b'')
                with patch.object(cf,'OUTPUT_JSON',str(raw)),patch.object(cf,'OUTPUT_JS',str(sidecar)),patch.object(cf,'CURL_BIN','fixture-curl'),patch.object(cf,'ACCESS_STOP',None),patch.object(cf,'REQUEST_STATS',{'requests':0,'successful':0,'failed':0,'errors':[]}),patch.object(cf.subprocess,'run',return_value=result) as request,patch.dict(os.environ,{'CURSEFORGE_API_KEY':'fixture-api-key','MC_DESKTOP_COLLECTION_RESULT':str(root/'result.json')}),redirect_stdout(io.StringIO()):
                    cf.main(recent_pages=1)
                    cf.fetch_slice_page(50)
                    self.assertEqual(request.call_count,1)
                    self.assertEqual(cf.REQUEST_STATS['requests'],1)
                    self.assertEqual(cf.REQUEST_STATS['failed'],1)
                    self.assertTrue(cf.ACCESS_STOP)
                self.assertEqual((raw.read_bytes(),sidecar.read_bytes()),original)
        payload={'data':[{'id':42,'summary':'A pack explaining captcha blocks and <html> examples'}]}
        response=subprocess.CompletedProcess([],0,json.dumps(payload).encode()+b'\n__CF_STATUS__:200',b'')
        with patch.object(cf,'CURL_BIN','fixture-curl'),patch.object(cf,'ACCESS_STOP',None),patch.object(cf.subprocess,'run',return_value=response),patch.dict(os.environ,{'CURSEFORGE_API_KEY':'fixture-api-key'}):
            self.assertEqual(cf.request_api_json('https://api.curseforge.com/v1/mods/search'),payload)

    def test_curseforge_official_configuration_and_metadata_preserve_history(self):
        cf=curseforge_full_crawler
        for url, key in (('https://api.curseforge.com/v1/mods/search',''),('https://api.curse.tools/v1/cf/mods/search','fixture-api-key')):
            with patch.dict(os.environ,{'CURSEFORGE_API_KEY':key,'CF_API_KEY':'','CURSEFORGE_API_KEY_FILE':''}),patch.object(cf,'ACCESS_STOP',None),patch.object(cf.subprocess,'run') as request:
                with self.assertRaises(cf.AccessRefusal):cf.request_api_json(url)
                request.assert_not_called()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);raw=root/'raw.json';sidecar=root/'sidecar.js';keyfile=root/'key.txt'
            old=[{'project_id':'42','title':'old','downloads':0,'releases':[{'version_number':'old release','date_published':'2026-09-01'}],'version_checked_at':'2026-09-30'},{'project_id':'99','title':'retain other pack','downloads':0}]
            raw.write_text(json.dumps(old),encoding='utf-8');keyfile.write_text('fixture-local-key\n',encoding='utf-8')
            payload={'data':[{'id':42,'name':'Updated pack','slug':'updated-pack','downloadCount':12,'gameId':432,'classId':4471,'dateCreated':'2026-09-01T00:00:00Z','dateModified':'2026-10-04T00:00:00Z'}],'pagination':{'totalCount':1}}
            response=subprocess.CompletedProcess([],0,json.dumps(payload).encode()+b'\n__CF_STATUS__:200',b'')
            with patch.dict(os.environ,{'CURSEFORGE_API_KEY':'','CF_API_KEY':'','CURSEFORGE_API_KEY_FILE':str(keyfile),'MC_DESKTOP_COLLECTION_RESULT':str(root/'result.json')}),patch.object(cf,'ACCESS_STOP',None),patch.object(cf,'OUTPUT_JSON',str(raw)),patch.object(cf,'OUTPUT_JS',str(sidecar)),patch.object(cf,'CURL_BIN','fixture-curl'),patch.object(cf,'REQUEST_STATS',{'requests':0,'successful':0,'failed':0,'errors':[]}),patch.object(cf.subprocess,'run',return_value=response) as request,redirect_stdout(io.StringIO()):
                cf.main(recent_pages=1)
                args,kwargs=request.call_args
                self.assertNotIn('fixture-local-key',' '.join(args[0]))
                self.assertEqual(kwargs['input'],b'x-api-key: fixture-local-key\n')
                self.assertTrue(args[0][-1].startswith('https://api.curseforge.com/v1/mods/search?'))
            rows={row['project_id']:row for row in json.loads(raw.read_text(encoding='utf-8'))}
            self.assertEqual(rows['42']['title'],'Updated pack');self.assertEqual(rows['42']['releases'],old[0]['releases']);self.assertEqual(rows['42']['version_checked_at'],'2026-09-30');self.assertEqual(rows['99'],old[1])

    def test_curseforge_existing_files_use_official_offset_pagination(self):
        import existing_version_crawler as existing
        responses=[{'data':[{'id':i,'displayName':f'Release {i}','fileDate':'2026-09-01T00:00:00Z'} for i in range(50)],'pagination':{'totalCount':51}},{'data':[{'id':50,'displayName':'Last release','fileDate':'2026-10-04T00:00:00Z'}],'pagination':{'totalCount':51}}]
        with patch.object(existing,'metadata_provider',return_value='official'), patch.object(existing,'request_cf_json',side_effect=responses) as request:
            releases=existing.fetch_releases('curseforge','42')
        self.assertEqual([call.args[0] for call in request.call_args_list],['https://api.curseforge.com/v1/mods/42/files?index=0&pageSize=50','https://api.curseforge.com/v1/mods/42/files?index=50&pageSize=50'])
        self.assertEqual(len(releases),51);self.assertEqual(releases[-1]['date_published'],'2026-10-04T00:00:00Z')

    def test_curseforge_existing_refusal_does_not_rewrite_or_try_next_pack(self):
        import existing_version_crawler as existing
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);raw=root/'crawler_output/curseforge_modpacks.json';sidecar=root/'converted_output/data/curseforge_data.js'
            raw.parent.mkdir();sidecar.parent.mkdir(parents=True)
            rows=[{'project_id':'42','title':'keep'},{'project_id':'99','title':'retain'}]
            raw.write_text(json.dumps(rows),encoding='utf-8');sidecar.write_text('window.curseforgeModpacksData = '+json.dumps(rows)+';',encoding='utf-8')
            before=(raw.read_bytes(),sidecar.read_bytes())
            with patch.object(sys,'argv',['existing','--platform','curseforge','--limit','2']),patch.object(existing,'metadata_provider',return_value='official'),patch.dict(os.environ,{'MC_DESKTOP_WORKSPACE':temp,'MC_DESKTOP_COLLECTION_RESULT':str(root/'result.json')}),patch.object(existing,'request_cf_json',side_effect=curseforge_full_crawler.AccessRefusal('HTTP 403')) as request,redirect_stdout(io.StringIO()):
                existing.main()
                self.assertEqual(request.call_count,1)
            self.assertEqual((raw.read_bytes(),sidecar.read_bytes()),before)

    def test_curseforge_file_indexes_flow_from_producer_sidecar_to_desktop_api(self):
        expected_categories = [f"Fixture category {index}" for index in range(10)]
        expected_versions = [f"1.20.{minor}" for minor in range(1, 16)]
        source_indexes = [
            {"fileId": 7101, "filename": "Arcadia 3.2.1.zip", "releaseType": 1, "gameVersion": "1.20.1", "modLoader": 4},
            {"fileId": 7101, "filename": "Arcadia 3.2.1.zip", "releaseType": 1, "gameVersion": "1.20.2", "modLoader": 6},
            {"fileId": 7102, "filename": "Arcadia unknown.zip", "releaseType": 87, "gameVersion": "1.20.3", "modLoader": 77},
        ]
        source_indexes.extend(
            {"fileId": 7103 + offset, "filename": f"Arcadia {version}.zip", "releaseType": 2, "gameVersion": version, "modLoader": 1}
            for offset, version in enumerate(expected_versions[3:])
        )
        expected_sidecar_first_indexes = [
            {"file_id": 7101, "filename": "Arcadia 3.2.1.zip", "release_type": 1, "game_version": "1.20.1", "mod_loader": 4},
            {"file_id": 7101, "filename": "Arcadia 3.2.1.zip", "release_type": 1, "game_version": "1.20.2", "mod_loader": 6},
            {"file_id": 7102, "filename": "Arcadia unknown.zip", "release_type": 87, "game_version": "1.20.3", "mod_loader": 77},
        ]
        expected_api_first_indexes = [
            {"fileId": 7101, "filename": "Arcadia 3.2.1.zip", "releaseType": 1, "gameVersion": "1.20.1", "modLoader": 4},
            {"fileId": 7101, "filename": "Arcadia 3.2.1.zip", "releaseType": 1, "gameVersion": "1.20.2", "modLoader": 6},
            {"fileId": 7102, "filename": "Arcadia unknown.zip", "releaseType": 87, "gameVersion": "1.20.3", "modLoader": 77},
        ]
        source = {
            "id": 7001,
            "slug": "fixture-curseforge-pack",
            "name": "CurseForge file index fixture",
            "summary": "offline producer-consumer fixture",
            "downloadCount": 30,
            "authors": [{"name": "fixture"}],
            "categories": [{"name": "Minecraft"}, {"name": "Modpacks"}] + [{"name": value} for value in expected_categories],
            "latestFilesIndexes": source_indexes,
            "mainFileId": 9999,
        }
        unknown_loader_only = curseforge_full_crawler.standardize_pack({
            "id": 7002,
            "latestFilesIndexes": [{"fileId": 7201, "filename": "Unknown loader.zip", "releaseType": 42, "gameVersion": "1.20.16", "modLoader": 77}],
        })
        self.assertEqual(unknown_loader_only["loaders"], [])
        legacy_record = {
            "project_id": "legacy-fixture",
            "title": "Old sidecar fixture",
            "author": "fixture",
            "source_meta": {"main_file_id": 8888},
        }

        with tempfile.TemporaryDirectory(prefix="curseforge-index-flow-") as temp:
            root = Path(temp)
            raw_path = root / "crawler_output" / "curseforge_modpacks.json"
            sidecar_path = root / "converted_output" / "data" / "curseforge_data.js"
            raw_path.parent.mkdir(parents=True)
            sidecar_path.parent.mkdir(parents=True)
            produced = curseforge_full_crawler.standardize_pack(source)
            with patch.object(curseforge_full_crawler, "OUTPUT_JSON", str(raw_path)), \
                 patch.object(curseforge_full_crawler, "OUTPUT_JS", str(sidecar_path)):
                curseforge_full_crawler.save_current_state({
                    produced["project_id"]: produced,
                    "legacy-fixture": legacy_record,
                })

            sidecar_text = sidecar_path.read_text(encoding="utf-8")
            self.assertTrue(sidecar_text.startswith("window.curseforgeModpacksData = "))
            sidecar = json.loads(sidecar_text.split("=", 1)[1].strip().rstrip(";"))
            source_record = next(record for record in sidecar if record["project_id"] == "7001")
            self.assertEqual(source_record["categories"], expected_categories)
            self.assertEqual(source_record["all_versions"], expected_versions)
            self.assertEqual(source_record["main_file_id"], 9999)
            self.assertEqual(len(source_record["file_indexes"]), 15)
            self.assertEqual(source_record["file_indexes"][:3], expected_sidecar_first_indexes)
            self.assertEqual([row["game_version"] for row in source_record["file_indexes"]], expected_versions)

            node_script = r"""
const [storeModule, userData, sourceDirectory] = process.argv.slice(1);
const { DataStore } = require(storeModule);
(async () => {
  const store = new DataStore(userData);
  await store.init();
  await store.importDirectory(sourceDirectory);
  const all = await store.getPlatformRecords('curseforge', { page: 1, pageSize: 20 });
  const lastCategory = await store.getPlatformRecords('curseforge', { category: 'Fixture category 9', page: 1, pageSize: 20 });
  const lastVersion = await store.getPlatformRecords('curseforge', { version: '1.20.15', page: 1, pageSize: 20 });
  process.stdout.write(JSON.stringify({ all, lastCategory: lastCategory.total, lastVersion: lastVersion.total }));
})().catch((error) => { console.error(error); process.exitCode = 1; });
"""
            api_result = subprocess.run(
                ["node", "-e", node_script, str(DESKTOP_ROOT / "lib" / "data-store.cjs"), str(root / "user-data"), str(root)],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(api_result.returncode, 0, api_result.stderr)
            api = json.loads(api_result.stdout)
            self.assertEqual(api["lastCategory"], 1)
            self.assertEqual(api["lastVersion"], 1)
            current = next(record for record in api["all"]["records"] if record["sourceId"] == "7001")
            self.assertEqual(current["categories"], expected_categories)
            self.assertEqual(current["versions"], expected_versions)
            self.assertEqual(current["mainFileId"], 9999)
            self.assertEqual(len(current["fileIndexes"]), 15)
            self.assertEqual(current["fileIndexes"][:3], expected_api_first_indexes)
            self.assertEqual([row["gameVersion"] for row in current["fileIndexes"]], expected_versions)
            legacy = next(record for record in api["all"]["records"] if record["sourceId"] == "legacy-fixture")
            self.assertNotIn("fileIndexes", legacy)
            self.assertEqual(legacy["mainFileId"], 8888)

    def test_explicit_no_change_can_reuse_untouched_cache(self):
        with tempfile.TemporaryDirectory(prefix="desktop-collector-no-change-") as temp:
            workspace = Path(temp)
            raw_path = workspace / "crawler_output" / PLATFORMS["curseforge"]["raw"]
            sidecar_path = workspace / "converted_output" / "data" / PLATFORMS["curseforge"]["sidecar"]
            result_path = workspace / "build" / PLATFORMS["curseforge"]["result"]
            raw_path.parent.mkdir(parents=True)
            sidecar_path.parent.mkdir(parents=True)
            result_path.parent.mkdir(parents=True)
            old = [{"project_id": "old", "title": "unchanged cache"}]
            raw_path.write_text(json.dumps(old), encoding="utf-8")
            write_sidecar(sidecar_path, "curseforgeModpacksData", old)
            started_ns = time.time_ns()
            old_ns = started_ns - 1_000_000
            os.utime(raw_path, ns=(old_ns, old_ns))
            os.utime(sidecar_path, ns=(old_ns, old_ns))
            before = {
                "raw": file_state(raw_path),
                "sidecar": file_state(sidecar_path),
                "result": file_state(result_path),
            }
            result_path.write_text(json.dumps({
                "schema": 1,
                "platform": "curseforge",
                "status": "success_no_change",
                "requestCompleted": True,
                "fetchedCount": 0,
                "pagesCompleted": 1,
                "truncated": False,
                "failedRequests": 0,
                "errors": [],
                "noChangeConfirmed": True,
            }), encoding="utf-8")
            contract = collect_output_contract(workspace, "curseforge", started_ns, before)
            self.assertEqual(contract["outcome"], "success_no_change")
            self.assertFalse(contract["rawTouched"])
            self.assertFalse(contract["sidecarTouched"])

    def test_all_platforms_write_current_workspace_outputs_and_mcmod_modern_sidecar(self):
        stub = ControlledRequests()
        with tempfile.TemporaryDirectory(prefix="desktop-collector-contract-") as temp:
            root = Path(temp)
            for platform, config in PLATFORMS.items():
                workspace = root / platform
                (workspace / "crawler_output").mkdir(parents=True)
                (workspace / "converted_output" / "data").mkdir(parents=True)
                if platform == "mcmod":
                    write_sidecar(workspace / "converted_output" / "data" / "table_rows.js", "tableRowsData", [{
                        "mid": 100,
                        "title": "本轮 MC百科 现代输出",
                        "views_n": 1,
                        "score_n": 1,
                        "mc_version": "1.7.10",
                    }])
                    write_sidecar(workspace / "converted_output" / "data" / "app_data.js", "compareData", {"100": {
                        "mid": "100", "title": "本轮 MC百科 现代输出", "title_cn": "本轮 MC百科 现代输出",
                        "mc_versions": ["1.7.10"], "mods": ["Fixture Mod"],
                    }})
                if platform == "curseforge":
                    old = [{"project_id": "old", "title": "旧 CurseForge 输入", "downloads": 1}]
                    (workspace / "crawler_output" / config["raw"]).write_text(json.dumps(old), encoding="utf-8")
                args = type("Args", (), {
                    "platform": platform,
                    "workspace": str(workspace),
                    "source_root": str(PROJECT_ROOT),
                    "limit": 1,
                    "pages": 1,
                    "until": None,
                })()
                with patch.object(urllib.request, "urlopen", side_effect=stub), \
                     patch.object(urllib.request, "build_opener", side_effect=lambda *args, **kwargs: StubOpener(stub)), \
                     patch("time.sleep", return_value=None):
                    run_selected_collector(args)
                raw_path = workspace / "crawler_output" / config["raw"]
                sidecar_path = workspace / "converted_output" / "data" / config["sidecar"]
                self.assertTrue(raw_path.exists(), platform)
                self.assertTrue(sidecar_path.exists(), platform)
                contract = json.loads((workspace / "build" / "desktop_update_result.json").read_text(encoding="utf-8"))
                self.assertIn(contract["outcome"], {"success_update", "success_no_change"}, platform)
                self.assertTrue(contract["rawTouched"], platform)
                self.assertTrue(contract["sidecarTouched"], platform)

                if platform == "mcmod":
                    text = sidecar_path.read_text(encoding="utf-8")
                    self.assertTrue(text.startswith("window.mcmodData = "))
                    modern = json.loads(text.split("=", 1)[1].strip().rstrip(";"))
                    self.assertEqual(modern[0]["title"], "本轮 MC百科 现代输出")
                    self.assertEqual(modern[0]["mcVersions"], ["1.7.10"])
                if platform == "curseforge":
                    self.assertEqual(json.loads(raw_path.read_text(encoding="utf-8"))[0]["title"], "旧 CurseForge 输入")

    def test_cached_curseforge_is_rejected_when_requests_are_empty_or_failed(self):
        for mode in ("empty", "error"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory(prefix="desktop-collector-cache-guard-") as temp:
                root = Path(temp)
                workspace = root / "curseforge"
                data_dir = workspace / "converted_output" / "data"
                raw_dir = workspace / "crawler_output"
                data_dir.mkdir(parents=True)
                raw_dir.mkdir(parents=True)
                old = [{"project_id": "old", "title": "Cached old record", "downloads": 1}]
                (raw_dir / PLATFORMS["curseforge"]["raw"]).write_text(json.dumps(old), encoding="utf-8")
                write_sidecar(data_dir / PLATFORMS["curseforge"]["sidecar"], "curseforgeModpacksData", old)
                args = type("Args", (), {
                    "platform": "curseforge",
                    "workspace": str(workspace),
                    "source_root": str(PROJECT_ROOT),
                    "limit": 1,
                    "pages": 1,
                    "until": None,
                })()

                def empty_or_error(request, timeout=None):
                    if mode == "error":
                        raise OSError("controlled network failure")
                    return StubResponse({"data": [], "pagination": {"totalCount": 0}})

                with patch.object(urllib.request, "urlopen", side_effect=empty_or_error), \
                     patch("time.sleep", return_value=None):
                    with self.assertRaises(RuntimeError):
                        run_selected_collector(args)

                contract = json.loads((workspace / "build" / "desktop_update_result.json").read_text(encoding="utf-8"))
                self.assertEqual(contract["outcome"], "failed")
                self.assertIn(contract["crawlerResult"]["status"], {"empty", "failed"})
                self.assertEqual(json.loads((raw_dir / PLATFORMS["curseforge"]["raw"]).read_text(encoding="utf-8"))[0]["title"], "Cached old record")

    def test_mcmod_build_script_args_modes(self):
        args_default = type("Args", (), {"limit": None, "pages": 1, "until": None})()
        self.assertEqual(build_script_args("mcmod", args_default), ["--mode", "new"])

        args_trend = type("Args", (), {"limit": 50, "pages": 1, "until": None, "mode": "trend", "cover_offset": None})()
        self.assertEqual(build_script_args("mcmod", args_trend), ["--mode", "trend", "--limit", "50"])

        args_all = type("Args", (), {"limit": 50, "pages": 1, "until": None, "mode": "all", "cover_offset": None})()
        self.assertEqual(build_script_args("mcmod", args_all), ["--mode", "all", "--limit", "50"])

        args_covers = type("Args", (), {"limit": None, "pages": 1, "until": None, "mode": "covers", "cover_offset": None})()
        self.assertEqual(build_script_args("mcmod", args_covers), ["--mode", "covers", "--limit", "20"])

        args_covers_custom = type("Args", (), {"limit": 50, "pages": 1, "until": None, "mode": "covers", "cover_offset": 100})()
        self.assertEqual(build_script_args("mcmod", args_covers_custom), ["--mode", "covers", "--limit", "50", "--cover-offset", "100"])

    def test_mcmod_existing_pack_trend_result_is_committable(self):
        with tempfile.TemporaryDirectory(prefix="mcmod-trend-contract-") as temp:
            result_path = Path(temp) / "result.json"
            rows = [{"mid": 16, "trend_dates": "2026-09-24", "trend_vals": "10"}]
            def refresh_existing(rows_arg, _compare, **_kwargs):
                rows_arg[0]["trend_dates"] = "2026-09-24,2026-09-25"
                rows_arg[0]["trend_vals"] = "10,14"
                return 1, 0
            with patch.dict(os.environ, {"MC_DESKTOP_COLLECTION_RESULT": str(result_path)}), \
                 patch.object(sys, "argv", ["mcmod_full_crawler.py", "--mode", "trend", "--limit", "1"]), \
                 patch.object(mcmod_full_crawler, "init_network"), \
                 patch.object(mcmod_full_crawler, "load_data", return_value=(rows, {})), \
                 patch.object(mcmod_full_crawler, "save_all_outputs"), \
                 patch.object(mcmod_full_crawler, "refresh_trend_and_versions", side_effect=refresh_existing), \
                 patch.object(mcmod_full_crawler, "COLLECTION_STATS", {"requests": 1, "successful": 1, "not_found": 0, "failed": 0, "errors": []}), \
                 patch.object(mcmod_full_crawler, "IS_BANNED", False):
                mcmod_full_crawler.main()
            result = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["fetchedCount"], 1)
            self.assertTrue(result["requestCompleted"])
            self.assertEqual(rows[0]["trend_dates"], "2026-09-24,2026-09-25")


if __name__ == "__main__":
    unittest.main()

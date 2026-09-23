import json
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

from collector_worker import PLATFORMS, collect_output_contract, file_state, run_selected_collector  # noqa: E402
import curseforge_full_crawler  # noqa: E402


class StubResponse:
    def __init__(self, payload, status=200):
        self.status = status
        self._payload = payload if isinstance(payload, bytes) else json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def read(self):
        return self._payload

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
        if "api.curse.tools/v1/cf/mods/search" in url:
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


if __name__ == "__main__":
    unittest.main()

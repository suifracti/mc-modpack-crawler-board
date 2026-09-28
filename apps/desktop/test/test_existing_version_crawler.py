"""Observable recovery behavior for a long CurseForge release refresh."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import existing_version_crawler


class CurseForgeReleaseResumeTest(unittest.TestCase):
    def test_successful_project_is_replayed_without_another_request(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_dir = root / "crawler_output"
            sidecar_dir = root / "converted_output" / "data"
            build_dir = root / "build"
            for directory in (raw_dir, sidecar_dir, build_dir):
                directory.mkdir(parents=True)
            records = [
                {"project_id": "a", "date_modified": "2026-09-28"},
                {"project_id": "b", "date_modified": "2026-09-27"},
            ]
            raw_path = raw_dir / "curseforge_modpacks.json"
            sidecar_path = sidecar_dir / "curseforge_data.js"
            raw_path.write_text(json.dumps(records), encoding="utf-8")
            sidecar_path.write_text("window.curseforgeModpacksData = " + json.dumps(records) + ";\n", encoding="utf-8")
            env = {"MC_DESKTOP_WORKSPACE": str(root),
                   "MC_DESKTOP_COLLECTION_RESULT": str(build_dir / "desktop_collection_result.json")}
            argv = ["existing_version_crawler.py", "--platform", "curseforge", "--limit", "2"]
            first_calls = []

            def interrupted_fetch(platform, ident):
                first_calls.append(ident)
                if ident == "b":
                    raise KeyboardInterrupt
                return [{"version_number": "a-1"}]

            with patch.dict(os.environ, env), patch.object(sys, "argv", argv), \
                    patch.object(existing_version_crawler.time, "sleep", return_value=None), \
                    patch.object(existing_version_crawler, "fetch_releases", side_effect=interrupted_fetch):
                with self.assertRaises(KeyboardInterrupt):
                    existing_version_crawler.main()
            self.assertEqual(first_calls, ["a", "b"])
            self.assertNotIn("version_checked_at", json.loads(raw_path.read_text(encoding="utf-8"))[0])

            resumed_calls = []

            def resumed_fetch(platform, ident):
                resumed_calls.append(ident)
                return [{"version_number": "b-1"}]

            with patch.dict(os.environ, env), patch.object(sys, "argv", argv), \
                    patch.object(existing_version_crawler.time, "sleep", return_value=None), \
                    patch.object(existing_version_crawler, "fetch_releases", side_effect=resumed_fetch):
                existing_version_crawler.main()

            self.assertEqual(resumed_calls, ["b"])
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8").split("=", 1)[1].rstrip(";\n"))
            self.assertEqual({item["project_id"]: item["latest_version"] for item in raw},
                             {"a": "a-1", "b": "b-1"})
            self.assertEqual([item["project_id"] for item in sidecar], ["a", "b"])
            self.assertEqual(json.loads((build_dir / "desktop_collection_result.json").read_text(encoding="utf-8"))["fetchedCount"], 2)


if __name__ == "__main__":
    unittest.main()

"""Offline production/consumer contract for the optional MCMod pack version."""
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import mcmod_full_crawler as crawler
from pipeline.adapters.mcmod import MCModAdapter
from pipeline.db.connection import init_db
from pipeline.exporters.structured_mcmod_exporter import StructuredMCModExporter


def read_sidecar(path):
    return json.loads(path.read_text(encoding="utf-8").split("=", 1)[1].strip().rstrip(";"))


class PackVersionContract(unittest.TestCase):
    def test_producers_and_desktop_consumer_preserve_only_explicit_version(self):
        with tempfile.TemporaryDirectory(prefix="mcmod-pack-version-") as temp:
            workspace = Path(temp)
            data = workspace / "converted_output" / "data"
            data.mkdir(parents=True)
            rows = [{"mid": 1, "title": "Fixture A", "latest_version": "1.2.3"},
                    {"mid": 2, "title": "Fixture B"},
                    {"mid": 3, "title": "Fixture empty", "latest_version": "   "}]
            app = {str(i): {"mc_versions": ["1.20.1"]} for i in (1, 2, 3)}
            with patch.multiple(crawler, REPO_ROOT=str(workspace),
                                TABLE_ROWS_PATH=str(data / "table_rows.js"),
                                APP_DATA_PATH=str(data / "app_data.js"),
                                RAW_OUTPUT_DIR=str(workspace / "crawler_output"),
                                RAW_JSON_PATH=str(workspace / "crawler_output/mcmod_modpacks.json")):
                crawler.save_all_outputs(rows, app)
            raw = json.loads((workspace / "crawler_output/mcmod_modpacks.json").read_text(encoding="utf-8"))
            self.assertEqual(raw[0]["latest_version"], "1.2.3")
            modern = read_sidecar(data / "mcmod_data.js")
            self.assertEqual(modern[0]["packVersion"], "1.2.3")
            for item in modern[1:]:
                self.assertNotIn("packVersion", item)

            # Feed the actual produced sidecar through DataStore, in a temporary root.
            script = """
const assert = require('node:assert/strict');
const { DataStore } = require('./apps/desktop/lib/data-store.cjs');
(async () => {
  const store = new DataStore(process.argv[2]);
  await store.init();
  await store.importDirectory(process.argv[1]);
  const all = await store.getPlatformRecords('mcmod');
  const a = all.records.find(r => r.sourceId === '1');
  const b = all.records.find(r => r.sourceId === '2');
  assert.equal(a.packVersion, '1.2.3');
  assert.equal(b.packVersion, undefined);
  assert.deepEqual(a.versions, ['1.20.1']);
  assert.deepEqual(all.availableVersions, ['1.20.1']);
  assert.deepEqual(a.loaders, b.loaders);
  assert.equal(a.updatedAt, b.updatedAt);
  assert.deepEqual(a.environment, b.environment);
  assert.equal((await store.getPlatformRecords('mcmod', {version:'1.2.3'})).total, 0);
  assert.equal((await store.getPlatformRecords('mcmod', {query:'1.2.3'})).total, 0);
  assert.equal(all.records.length, 3); // Missing-field old sidecars still load.
})().catch(e => { console.error(e); process.exit(1); });
"""
            subprocess.run(["node", "-e", script, str(data), str(workspace / "user-data")],
                           cwd=ROOT, check=True)

            # Offline exporter uses the same explicit value via extra_json, never release defaults.
            db = workspace / "canonical.db"
            conn = sqlite3.connect(db)
            init_db(conn)
            conn.executescript((ROOT / "pipeline/db/migrations/002_runtime_enrichment.sql").read_text(encoding="utf-8"))
            adapter = MCModAdapter(str(workspace))
            for index, item in enumerate(raw):
                bundle = adapter.adapt_item(item, index)
                for table, model in (("packs", bundle.pack), ("source_items", bundle.source_item)):
                    fields = asdict(model)
                    conn.execute(f"INSERT INTO {table} ({','.join(fields)}) VALUES ({','.join('?' for _ in fields)})", list(fields.values()))
            conn.commit()
            conn.close()
            out = workspace / "exported"
            StructuredMCModExporter(str(db), str(out)).export()
            exported = read_sidecar(out / "mcmod_data.js")
            self.assertEqual(exported[0]["packVersion"], "1.2.3")
            for item in exported[1:]:
                self.assertNotIn("packVersion", item)

    def test_sampled_cover_refresh_preserves_unknowns_and_reaches_desktop_reader(self):
        fixture_dir = ROOT / "tests" / "fixtures"
        covered_page = (fixture_dir / "mcmod_cover_page_16_excerpt.html").read_text(encoding="utf-8")
        no_cover_page = (fixture_dir / "mcmod_cover_no_main_excerpt.html").read_text(encoding="utf-8")
        expected_cover = "https://i.mcmod.cn/modpack/cover/20201007/1602069892_10167_rkTL.jpg@480x300.jpg"

        self.assertEqual(crawler.extract_mcmod_pack_cover("16", covered_page), expected_cover)
        self.assertEqual(crawler.parse_mcmod_pack("16", covered_page)["cover_url"], expected_cover)
        self.assertEqual(crawler.extract_mcmod_pack_cover("999999", no_cover_page), "")
        lazy_cover_page = (
            '<div class="class-cover-image"><img src="/pages/class/images/none.jpg" '
            'data-src="/modpack/cover/lazy-cover.webp"></div>'
        )
        self.assertEqual(
            crawler.extract_mcmod_pack_cover("16", lazy_cover_page),
            "https://i.mcmod.cn/modpack/cover/lazy-cover.webp",
        )

        with tempfile.TemporaryDirectory(prefix="mcmod-cover-pipeline-") as temp:
            workspace = Path(temp)
            raw_dir = workspace / "crawler_output"
            data_dir = workspace / "converted_output" / "data"
            raw_dir.mkdir(parents=True)
            data_dir.mkdir(parents=True)
            raw_path = raw_dir / "mcmod_modpacks.json"
            sidecar_path = data_dir / "mcmod_data.js"
            raw_before = [
                {
                    "platform": "mcmod",
                    "project_id": "16",
                    "mid": "16",
                    "url": "https://www.mcmod.cn/modpack/16.html",
                    "title": "RLCraft",
                    "cover_url": "",
                    "categories": ["生存"],
                    "description": "preserve raw description",
                },
                {
                    "platform": "mcmod",
                    "project_id": "999999",
                    "mid": "999999",
                    "url": "https://www.mcmod.cn/modpack/999999.html",
                    "title": "No source cover",
                    "cover_url": "",
                    "categories": ["冒险"],
                    "description": "also preserved",
                },
            ]
            sidecar_before = [
                {"mid": 16, "title": "RLCraft", "coverUrl": "", "categories": ["生存"], "author": "keep"},
                {"mid": 999999, "title": "No source cover", "coverUrl": "", "categories": ["冒险"], "author": "keep"},
            ]
            raw_path.write_text(json.dumps(raw_before, ensure_ascii=False, indent=2), encoding="utf-8")
            sidecar_path.write_text(
                "window.mcmodData = " + json.dumps(sidecar_before, ensure_ascii=False, separators=(",", ":")) + ";\n",
                encoding="utf-8",
            )
            pages = {
                "https://www.mcmod.cn/modpack/16.html": covered_page,
                "https://www.mcmod.cn/modpack/999999.html": no_cover_page,
            }
            with patch.multiple(crawler, RAW_JSON_PATH=str(raw_path), MCMOD_DATA_PATH=str(sidecar_path)):
                result = crawler.refresh_missing_mcmod_covers(
                    limit=2, page_fetcher=lambda url: pages[url]
                )

            self.assertEqual(
                {key: result[key] for key in ("requests", "updated", "noCover", "failed", "blocked")},
                {"requests": 2, "updated": 1, "noCover": 1, "failed": 0, "blocked": ""},
            )
            raw_after = json.loads(raw_path.read_text(encoding="utf-8"))
            sidecar_after = read_sidecar(sidecar_path)
            self.assertEqual(raw_after[0]["cover_url"], expected_cover)
            self.assertEqual(sidecar_after[0]["coverUrl"], expected_cover)
            self.assertEqual(raw_after[1]["cover_url"], "")
            self.assertEqual(sidecar_after[1]["coverUrl"], "")
            for before, after in zip(raw_before, raw_after):
                self.assertEqual({k: v for k, v in before.items() if k != "cover_url"},
                                 {k: v for k, v in after.items() if k != "cover_url"})
            for before, after in zip(sidecar_before, sidecar_after):
                self.assertEqual({k: v for k, v in before.items() if k != "coverUrl"},
                                 {k: v for k, v in after.items() if k != "coverUrl"})

            script = """
const assert = require('node:assert/strict');
const { DataStore } = require('./apps/desktop/lib/data-store.cjs');
(async () => {
  const store = new DataStore(process.argv[2]);
  await store.init();
  await store.importDirectory(process.argv[1]);
  const result = await store.getPlatformRecords('mcmod');
  assert.equal(result.records.find(r => r.sourceId === '16').coverUrl, process.argv[3]);
  assert.equal(result.records.find(r => r.sourceId === '999999').coverUrl, '');
})().catch(error => { console.error(error); process.exit(1); });
"""
            subprocess.run(
                ["node", "-e", script, str(data_dir), str(workspace / "user-data"), expected_cover],
                cwd=ROOT,
                check=True,
            )


if __name__ == "__main__":
    unittest.main()

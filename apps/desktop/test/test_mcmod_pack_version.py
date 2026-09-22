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


if __name__ == "__main__":
    unittest.main()

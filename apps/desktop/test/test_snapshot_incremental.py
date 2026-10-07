"""Real SQLite fixtures protect snapshot reuse and the five untouched platforms."""
import contextlib
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'apps/desktop'))
from pipeline import build_canonical_db as builder
import snapshot_pipeline


@contextlib.contextmanager
def database(path):
    with contextlib.closing(sqlite3.connect(path)) as conn:
        with conn:yield conn


class SnapshotIncremental(unittest.TestCase):
    def setup_workspace(self,root):
        (root/'crawler_output').mkdir();(root/'converted_output/data').mkdir(parents=True);(root/'build').mkdir()
        records={
            'mcmod':[{'mid':'1','title':'MC fixture'}],
            'bilibili':[{'bvid':'BV1234567890','title':'Before','pub_timestamp':1790502559}],
            'bbsmc':[{'project_id':'bb1','title':'BBS fixture'}],
            'xyebbs':[{'project_id':'xy1','title':'XY fixture'}],
            'modrinth':[{'project_id':'mod1','title':'Mod fixture'}],
            'curseforge':[{'project_id':'cf1','title':'CF fixture'}],
        }
        for platform,rows in records.items():self.write_rows(root,platform,rows)
        with patch.object(builder,'PROJECT_ROOT',str(root)),contextlib.redirect_stdout(io.StringIO()):
            builder.build_canonical_db(str(root/'build/canonical.db'))
        (root/'build/desktop_update_result.json').write_text(json.dumps({'platform':'bilibili','outcome':'success_update','rawTouched':True,'sidecarTouched':True,'crawlerResult':{'status':'success'}}))

    def write_rows(self,root,platform,rows):
        raw,sidecars=snapshot_pipeline.PLATFORMS[platform]
        (root/'crawler_output'/raw).write_text(json.dumps(rows))
        (root/'converted_output/data'/sidecars[0]).write_text('window.fixture = '+json.dumps(rows)+';')

    def run_snapshot(self,root):
        with patch.object(sys,'argv',['snapshot_pipeline.py','--workspace',str(root),'--platform','bilibili','--source-root',str(ROOT)]),contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(snapshot_pipeline.main(),0)

    def test_only_changed_platform_is_rebuilt_and_prior_provenance_and_fts_survive(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.setup_workspace(root)
            with database(root/'build/canonical.db') as c:
                untouched=c.execute("SELECT * FROM source_items WHERE platform != 'bilibili' ORDER BY id").fetchall()
            self.write_rows(root,'bilibili',[{'bvid':'BV1234567890','title':'After','pub_timestamp':1790502559},{'bvid':'BV0987654321','title':'Brandnew','pub_timestamp':1790502559}])
            self.run_snapshot(root);self.run_snapshot(root)
            with database(root/'build/canonical.db') as c:
                self.assertEqual(c.execute("SELECT * FROM source_items WHERE platform != 'bilibili' ORDER BY id").fetchall(),untouched)
                self.assertEqual(c.execute('SELECT COUNT(*) FROM ingest_runs').fetchone()[0],3)
                self.assertEqual(c.execute("SELECT COUNT(*) FROM raw_snapshot_refs WHERE platform='modrinth'").fetchone()[0],1)
                self.assertEqual(c.execute("SELECT COUNT(*) FROM source_items WHERE platform='bilibili'").fetchone()[0],2)
                self.assertEqual(c.execute("SELECT COUNT(*) FROM pack_fts WHERE pack_fts MATCH 'Before'").fetchone()[0],0)
                self.assertEqual(c.execute("SELECT COUNT(*) FROM pack_fts WHERE pack_fts MATCH 'After'").fetchone()[0],1)
                self.assertEqual(c.execute('SELECT COUNT(*) FROM pack_fts').fetchone()[0],7)
                self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])
                self.assertEqual(c.execute('PRAGMA quick_check').fetchone()[0],'ok')

    def test_changed_other_input_requires_full_rebuild_instead_of_reusing_stale_platform(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.setup_workspace(root)
            self.write_rows(root,'modrinth',[{'project_id':'mod1','title':'Fresh foreign source'}])
            self.run_snapshot(root)
            with database(root/'build/canonical.db') as c:
                self.assertEqual(c.execute("SELECT title FROM source_items WHERE platform='modrinth'").fetchone()[0],'Fresh foreign source')

    def test_missing_baseline_provenance_never_qualifies_for_reuse(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.setup_workspace(root)
            with database(root/'build/canonical.db') as c:c.execute("DELETE FROM raw_snapshot_refs WHERE platform='modrinth'")
            self.run_snapshot(root)
            with database(root/'build/canonical.db') as c:
                self.assertEqual(c.execute("SELECT COUNT(*) FROM raw_snapshot_refs WHERE platform='modrinth'").fetchone()[0],1)

    def test_old_or_mismatched_pipeline_metadata_forces_a_full_rebuild(self):
        for mismatch in (True,False):
            with self.subTest(mismatch=mismatch),tempfile.TemporaryDirectory() as d:
                root=Path(d);self.setup_workspace(root)
                with database(root/'build/canonical.db') as c:
                    if mismatch:c.execute("UPDATE canonical_build_meta SET value='old-code' WHERE key='pipelineFingerprint'")
                    else:c.execute('DROP TABLE canonical_build_meta')
                self.run_snapshot(root)
                with database(root/'build/canonical.db') as c:
                    self.assertEqual(c.execute('SELECT COUNT(*) FROM ingest_runs').fetchone()[0],1)
                    self.assertEqual(c.execute("SELECT value FROM canonical_build_meta WHERE key='pipelineFingerprint'").fetchone()[0],builder.pipeline_fingerprint())

    def test_missing_other_source_id_cannot_be_hidden_by_matching_raw_hashes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.setup_workspace(root)
            with database(root/'build/canonical.db') as c:c.execute("DELETE FROM source_items WHERE platform='modrinth'")
            self.run_snapshot(root)
            with database(root/'build/canonical.db') as c:
                self.assertEqual(c.execute("SELECT source_id FROM source_items WHERE platform='modrinth'").fetchone()[0],'mod1')
                self.assertEqual(c.execute('SELECT COUNT(*) FROM ingest_runs').fetchone()[0],1)

if __name__=='__main__':unittest.main()

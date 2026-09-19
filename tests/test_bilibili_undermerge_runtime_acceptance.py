"""Dynamic Phase 3G-F.3-A acceptance-harness tests.

The tests deliberately use temporary output/modules.  They never regenerate or
restore the frozen evidence files, and they never accept a stale JSON report as
proof that the current runtime passed.
"""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NODE = "node"
SCRIPT = ROOT / "pipeline" / "audit" / "phase3gf_runtime_acceptance.js"
FIXTURE = ROOT / "pipeline" / "audit" / "fixtures" / "phase3gf_runtime_acceptance.json"
ESBUILD = ROOT / "apps" / "web" / "node_modules" / ".bin" / (
    "esbuild.cmd" if os.name == "nt" else "esbuild"
)


def run_acceptance(module, fixture=FIXTURE, output=None):
    cmd = [NODE, str(SCRIPT), "--current-module", str(module), "--fixture", str(fixture)]
    if output is not None:
        cmd.extend(["--out", str(output)])
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


class TestBilibiliUndermergeRuntimeAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="phase3gf-acceptance-")
        cls.tmp_path = Path(cls.tmp.name)
        cls.current_module = cls.tmp_path / "current.js"
        r = subprocess.run([
            str(ESBUILD), "apps/web/src/domain/bilibiliGrouping.ts", "--bundle",
            "--format=cjs", "--platform=node", "--outfile=" + str(cls.current_module),
            "--log-level=warning",
        ], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode:
            raise AssertionError(f"esbuild failed: {r.stdout}\n{r.stderr}")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_fixture_validates_without_reading_a_mutable_selection(self):
        r = subprocess.run([NODE, str(SCRIPT), "--validate-only", "--fixture", str(FIXTURE)],
                           cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('"status": "VALID"', r.stdout)

    def test_fixture_hash_or_member_drift_fails_closed(self):
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        data["cases"][0]["groups"][0]["members"] = []
        bad = self.tmp_path / "fixture-empty-member.json"
        bad.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        r = subprocess.run([NODE, str(SCRIPT), "--validate-only", "--fixture", str(bad)],
                           cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("empty/incomplete group", r.stdout + r.stderr)

    def test_fixture_evidence_mapping_drift_fails_closed(self):
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        data["source_artifacts"]["population"]["sha256"] = "0" * 64
        bad = self.tmp_path / "fixture-input-hash-drift.json"
        bad.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        r = subprocess.run([NODE, str(SCRIPT), "--validate-only", "--fixture", str(bad)],
                           cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("fixture provenance hash mismatch", r.stdout + r.stderr)

    def test_changed_current_runtime_cannot_reuse_a_stale_pass_report(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        target = next(c for c in fixture["cases"] if c["case_type"] == "gate")["bvids"][0]
        wrapper = self.tmp_path / "tampered-current.js"
        base = json.dumps(str(self.current_module).replace("\\", "/"))
        target_json = json.dumps(target)
        wrapper.write_text(
            "const base=require(" + base + ");\n"
            "const target=" + target_json + ";\n"
            "exports.groupBilibiliPacks=(records)=>{const out=base.groupBilibiliPacks(records);"
            "const d=out.get(target); d.groupKey='tampered::'+target; return out;};\n",
            encoding="utf-8",
        )
        output = self.tmp_path / "tampered-result.json"
        r = run_acceptance(wrapper, output=output)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertNotEqual(report["status"], "PASS")
        self.assertTrue(any(report_case["result"] == "FAIL"
                            for report_case in report["gate_cases"]))

    def test_negative_absorption_is_detected_by_member_partition(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        target_case = next(c for c in fixture["cases"]
                           if c["case_type"] == "protected"
                           and c["verdict"] == "DIFFERENT_PACKS"
                           and c["relations"]["cannot_link"])
        left, right = target_case["relations"]["cannot_link"][0]
        wrapper = self.tmp_path / "negative-absorption.js"
        base = json.dumps(str(self.current_module).replace("\\", "/"))
        left_json = json.dumps(left)
        right_json = json.dumps(right)
        wrapper.write_text(
            "const base=require(" + base + ");\n"
            "exports.groupBilibiliPacks=(records)=>{const out=base.groupBilibiliPacks(records);"
            "out.get(" + right_json + ").groupKey=out.get(" + left_json + ").groupKey; return out;};\n",
            encoding="utf-8",
        )
        output = self.tmp_path / "negative-result.json"
        r = run_acceptance(wrapper, output=output)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        report = json.loads(output.read_text(encoding="utf-8"))
        failures = [x for x in report["protected_cases"] if x["result"] == "FAIL"]
        self.assertTrue(any("cannot-link violation" in reason
                            for x in failures for reason in x["failure_reasons"]))

    def test_unknown_member_merge_is_not_a_safe_pass(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        target_case = next(c for c in fixture["cases"]
                           if c["case_type"] == "protected"
                           and c["verdict"] == "DIFFERENT_PACKS"
                           and c["relations"]["unknown_pairs"])
        left, right = target_case["relations"]["unknown_pairs"][0]
        wrapper = self.tmp_path / "unknown-merge.js"
        base = json.dumps(str(self.current_module).replace("\\", "/"))
        left_json = json.dumps(left)
        right_json = json.dumps(right)
        wrapper.write_text(
            "const base=require(" + base + ");\n"
            "exports.groupBilibiliPacks=(records)=>{const out=base.groupBilibiliPacks(records);"
            "out.get(" + right_json + ").groupKey=out.get(" + left_json + ").groupKey; return out;};\n",
            encoding="utf-8",
        )
        output = self.tmp_path / "unknown-merge-result.json"
        r = run_acceptance(wrapper, output=output)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        report = json.loads(output.read_text(encoding="utf-8"))
        failures = [x for x in report["protected_cases"] if x["result"] == "FAIL"]
        self.assertTrue(any("unknown relation merged" in reason
                            for x in failures for reason in x["failure_reasons"]))

    def test_group_key_rename_preserves_member_relations(self):
        wrapper = self.tmp_path / "renamed-keys.js"
        base = json.dumps(str(self.current_module).replace("\\", "/"))
        wrapper.write_text(
            "const base=require(" + base + ");\n"
            "exports.groupBilibiliPacks=(records)=>{const out=base.groupBilibiliPacks(records);"
            "for(const d of out.values()) d.groupKey='renamed::'+d.groupKey; return out;};\n",
            encoding="utf-8",
        )
        output = self.tmp_path / "renamed-keys-result.json"
        r = run_acceptance(wrapper, output=output)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "PASS")

    def test_real_current_runtime_is_invoked_and_result_matches_exit_code(self):
        output = self.tmp_path / "current-result.json"
        r = run_acceptance(self.current_module, output=output)
        self.assertIn(r.returncode, (0, 2), r.stdout + r.stderr)
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "PASS" if r.returncode == 0 else "BLOCKED")
        self.assertEqual(report["baselines"]["candidate_runtime"]["bundle_sha256"],
                         __import__("hashlib").sha256(self.current_module.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main(verbosity=2)

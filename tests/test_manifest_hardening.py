"""
Manifest Hardening Tests (Architecture V2 - Phase 3G-F-B).

Locks down the reliability contract that the cutover's final manifest step
depends on:

  M1  deterministic file list: two runs produce byte-identical (path, sha256)
      sets, ordered by relative path
  M2  backward compatibility: a manifest written by the pre-3G-F-B code (only
      `path` / `size_bytes` / `sha256`) still verifies
  M3  verification detects modified / missing / extra files
  M4  no production file is silently dropped: anything the walker refuses to
      hash is reported in `skipped_entries` with a reason
  M5  directory reparse points (junctions / directory symlinks) are NOT
      descended into, so a junction pointing at an ancestor cannot make the
      walk unbounded
  M6  file-level links are hashed but marked in the manifest
  M7  the stall watchdog hard-exits with STALL_EXIT_CODE instead of blocking
      forever, and writes an attributable diagnostic
  M8  `get_git_commit` can never hang the cutover (bounded, stdin closed)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from pipeline.manifest import (  # noqa: E402
    STALL_EXIT_CODE,
    collect_files,
    compute_sha256,
    generate_manifest,
    get_git_commit,
    verify_manifest,
)

PRODUCTION_MANIFEST = os.path.join(
    REPO_ROOT, "build", "manifests", "frontend_modern_production.sha256.json")
CONVERTED_OUTPUT = os.path.join(REPO_ROOT, "converted_output")


def _make_tree(root):
    """A small tree with nested dirs, a link, and a junction to its own parent."""
    os.makedirs(os.path.join(root, "a", "b"), exist_ok=True)
    os.makedirs(os.path.join(root, "c"), exist_ok=True)
    with open(os.path.join(root, "a", "one.txt"), "w", encoding="utf-8") as fp:
        fp.write("one")
    with open(os.path.join(root, "a", "b", "two.txt"), "w", encoding="utf-8") as fp:
        fp.write("two")
    with open(os.path.join(root, "c", "three.txt"), "w", encoding="utf-8") as fp:
        fp.write("three")


class ManifestDeterminismTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="mf_hard_")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_m1_two_runs_identical_and_sorted(self):
        _make_tree(self.tmp)
        out = tempfile.mkdtemp(prefix="mf_out_")
        self.addCleanup(shutil.rmtree, out, True)
        m1 = generate_manifest(self.tmp, os.path.join(out, "_m1.json"))
        m2 = generate_manifest(self.tmp, os.path.join(out, "_m2.json"))
        f1 = [(e["path"], e["sha256"]) for e in m1["files"]]
        f2 = [(e["path"], e["sha256"]) for e in m2["files"]]
        self.assertEqual(f1, f2, "manifest file list is not deterministic")
        paths = [e["path"] for e in m1["files"]]
        self.assertEqual(paths, sorted(paths), "manifest paths are not sorted")
        self.assertEqual(m1["total_files"], 3)

    def test_m1_production_manifest_matches_checked_in_digests(self):
        """The new walker must reproduce the production manifest exactly."""
        if not os.path.exists(PRODUCTION_MANIFEST):
            self.skipTest("production manifest not present")
        with open(PRODUCTION_MANIFEST, "r", encoding="utf-8") as fp:
            old = json.load(fp)
        old_map = {e["path"]: e["sha256"] for e in old["files"]}
        entries, skipped = collect_files(CONVERTED_OUTPUT)
        self.assertEqual(skipped, [], "production tree must have no skipped entries")
        new_map = {}
        for e in entries:
            new_map[e["path"]] = compute_sha256(e["abs_path"])
        self.assertEqual(set(old_map), set(new_map), "path set drifted")
        self.assertEqual(old_map, new_map, "digests drifted")


class ManifestCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="mf_compat_")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        _make_tree(self.tmp)
        # The manifest must live OUTSIDE the directory under test, otherwise it
        # shows up as an extra file.
        self.out = tempfile.mkdtemp(prefix="mf_compat_out_")
        self.addCleanup(shutil.rmtree, self.out, True)
        self.manifest = os.path.join(self.out, "_m.json")

    def _legacy_manifest(self):
        """A manifest in the pre-3G-F-B schema (three keys per entry)."""
        return {
            "generated_at": "2026-01-01 00:00:00 UTC",
            "target_directory": os.path.basename(self.tmp),
            "source_commit": "deadbeef",
            "total_files": 3,
            "files": [
                {"path": "a/b/two.txt", "size_bytes": 3,
                 "sha256": compute_sha256(os.path.join(self.tmp, "a", "b", "two.txt"))},
                {"path": "a/one.txt", "size_bytes": 3,
                 "sha256": compute_sha256(os.path.join(self.tmp, "a", "one.txt"))},
                {"path": "c/three.txt", "size_bytes": 5,
                 "sha256": compute_sha256(os.path.join(self.tmp, "c", "three.txt"))},
            ],
        }

    def test_m2_legacy_schema_still_verifies(self):
        with open(self.manifest, "w", encoding="utf-8") as fp:
            json.dump(self._legacy_manifest(), fp)
        ok, details = verify_manifest(self.tmp, self.manifest)
        self.assertTrue(ok, details)
        self.assertEqual(details["target_total_files"], 3)

    def test_m3_detects_modified_missing_and_extra(self):
        with open(self.manifest, "w", encoding="utf-8") as fp:
            json.dump(self._legacy_manifest(), fp)

        with open(os.path.join(self.tmp, "a", "one.txt"), "w", encoding="utf-8") as fp:
            fp.write("ONE")
        ok, details = verify_manifest(self.tmp, self.manifest)
        self.assertFalse(ok)
        self.assertEqual(details["modified_count"], 1)
        self.assertEqual(details["modified"][0]["reason"], "sha256_mismatch")

        os.remove(os.path.join(self.tmp, "c", "three.txt"))
        ok, details = verify_manifest(self.tmp, self.manifest)
        self.assertFalse(ok)
        self.assertEqual(details["missing_count"], 1)

        with open(os.path.join(self.tmp, "c", "extra.txt"), "w", encoding="utf-8") as fp:
            fp.write("extra")
        ok, details = verify_manifest(self.tmp, self.manifest)
        self.assertFalse(ok)
        self.assertEqual(details["extra_count"], 1)

    def test_m3_ignore_extra_still_supported(self):
        with open(self.manifest, "w", encoding="utf-8") as fp:
            json.dump(self._legacy_manifest(), fp)
        with open(os.path.join(self.tmp, "metadata.json"), "w", encoding="utf-8") as fp:
            fp.write("{}")
        ok, details = verify_manifest(self.tmp, self.manifest, ignore_extra=["metadata.json"])
        self.assertTrue(ok, details)


class ManifestLinkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="mf_link_")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        _make_tree(self.tmp)

    def _mklink(self, link, target, kind):
        """kind: 'junction' | 'symlink' | 'hardlink'."""
        flag = {"junction": "/J", "symlink": None, "hardlink": "/H"}[kind]
        cmd = ["cmd", "/c", "mklink"] + ([flag] if flag else []) + [link, target]
        res = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8",
            errors="replace", stdin=subprocess.DEVNULL, timeout=60)
        return res.returncode == 0

    def test_m4_m5_junction_not_descended_and_reported(self):
        """A junction back to an ancestor must be reported, not walked into."""
        junction = os.path.join(self.tmp, "a", "loop")
        if not self._mklink(junction, self.tmp, "junction"):
            self.skipTest("cannot create a junction in this environment")

        entries, skipped = collect_files(self.tmp)
        paths = [e["path"] for e in entries]
        self.assertEqual(len(entries), 3, f"junction was descended into: {paths}")
        self.assertTrue(
            any(s["path"] == "a/loop" and "reparse_point" in s["reason"]
                for s in skipped),
            f"junction not reported in skipped_entries: {skipped}")

        out = tempfile.mkdtemp(prefix="mf_out_")
        self.addCleanup(shutil.rmtree, out, True)
        m = generate_manifest(self.tmp, os.path.join(out, "_m.json"))
        self.assertEqual(m["total_files"], 3)
        self.assertEqual(m.get("skipped_count"), len(skipped))
        self.assertTrue(m.get("skipped_entries"))

    def test_m6_file_symlink_hashed_and_marked(self):
        target = os.path.join(self.tmp, "a", "one.txt")
        link = os.path.join(self.tmp, "c", "link.txt")
        if not self._mklink(link, target, "symlink") or not os.path.islink(link):
            self.skipTest("cannot create a file symlink in this environment")

        out = tempfile.mkdtemp(prefix="mf_out_")
        self.addCleanup(shutil.rmtree, out, True)
        m = generate_manifest(self.tmp, os.path.join(out, "_m.json"))
        entry = next(e for e in m["files"] if e["path"] == "c/link.txt")
        self.assertEqual(entry["sha256"], compute_sha256(target))
        self.assertIn("link", entry)
        # Windows readlink returns an extended-length path (\\?\C:\...).
        self.assertEqual(
            entry["link_target"].lstrip("\\?") .replace("\\\\?", ""),
            target)

    def test_m6b_hardlink_is_a_regular_file(self):
        """A hard link must NOT be reported as a link entry: it is a real file."""
        target = os.path.join(self.tmp, "a", "one.txt")
        link = os.path.join(self.tmp, "c", "hard.txt")
        if not self._mklink(link, target, "hardlink") or os.path.islink(link):
            self.skipTest("cannot create a hard link in this environment")

        entries, skipped = collect_files(self.tmp)
        self.assertEqual(skipped, [])
        self.assertIn("c/hard.txt", [e["path"] for e in entries])
        self.assertEqual(compute_sha256(link), compute_sha256(target))


class ManifestWatchdogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="mf_wd_")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_m7_watchdog_hard_exits_with_diagnostic(self):
        """A stalled operation must fail fast, naming the operation and path."""
        script = os.path.join(self.tmp, "stall.py")
        audit_dir = os.path.join(REPO_ROOT, "build", "audit")
        os.makedirs(audit_dir, exist_ok=True)
        before = set(os.listdir(audit_dir))
        with open(script, "w", encoding="utf-8") as fp:
            fp.write(
                "import os, sys, time\n"
                f"sys.path.insert(0, {REPO_ROOT!r})\n"
                "from pipeline.manifest import Progress\n"
                "p = Progress(label='watchdog-test', stall_timeout=1.0,\n"
                "             per_file_timeout=1.0)\n"
                "p.start_watchdog()\n"
                "p.begin('hash_file', 'a/b/pretend_blocked_file.js')\n"
                "time.sleep(600)\n"
            )
        res = subprocess.run(
            [sys.executable, script],
            capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=120)
        self.assertEqual(res.returncode, STALL_EXIT_CODE,
                         f"expected exit {STALL_EXIT_CODE}, got {res.returncode}\n"
                         f"{res.stdout}\n{res.stderr}")
        self.assertIn("MANIFEST STALL", res.stdout + res.stderr)
        self.assertIn("pretend_blocked_file.js", res.stdout + res.stderr)

        after = set(os.listdir(audit_dir)) - before
        diags = [f for f in after if f.startswith("manifest_stall_pid")]
        self.assertTrue(diags, "no stall diagnostic was written")
        with open(os.path.join(audit_dir, diags[0]), "r", encoding="utf-8") as fp:
            diag = json.load(fp)
        self.assertEqual(diag["operation"], "hash_file")
        self.assertEqual(diag["path"], "a/b/pretend_blocked_file.js")
        for f in diags:
            os.remove(os.path.join(audit_dir, f))

    def test_m7b_watchdog_does_not_fire_on_healthy_run(self):
        _make_tree(self.tmp)
        m = generate_manifest(self.tmp, os.path.join(self.tmp, "_m.json"),
                              stall_timeout=30.0, per_file_timeout=30.0)
        self.assertEqual(m["total_files"], 3)


class GitCommitTests(unittest.TestCase):
    def test_m8_git_commit_is_bounded_and_never_raises(self):
        commit = get_git_commit(REPO_ROOT, timeout=10)
        self.assertTrue(
            commit == "unknown" or (len(commit) == 40 and
                                    all(c in "0123456789abcdef" for c in commit)),
            f"unexpected commit value: {commit!r}")

    def test_m8b_git_commit_on_bogus_dir_returns_unknown(self):
        tmp = tempfile.mkdtemp(prefix="mf_git_")
        self.addCleanup(shutil.rmtree, tmp, True)
        self.assertEqual(get_git_commit(tmp, timeout=10), "unknown")


if __name__ == "__main__":
    unittest.main(verbosity=2)

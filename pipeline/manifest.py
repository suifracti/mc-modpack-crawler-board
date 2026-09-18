"""
Architecture V2 - SHA-256 Manifest Utility.

Generates and verifies cryptographic manifests for production, staging, and
backup directories. Uses portable relative paths and deterministic sorting.

Phase 3G-F-B hardening
----------------------
The cutover was previously observed to stall for ~38 minutes between the
staging manifest and the production manifest, with the Python process showing
0% CPU, a tiny working set and no child process. That symptom cannot be
explained by Python bytecode, and the old implementation offered no way to tell
*which file* and *which syscall* was stuck - the only available report was
"Windows filesystem flaky".

This module now provides the missing attribution:

* deterministic two-phase walk (collect + sort, then hash) so the manifest file
  list is stable regardless of directory iteration order;
* explicit classification of every entry (regular file / symlink / junction /
  other) and an explicit ``skipped`` report - production files are never
  silently dropped;
* a daemon watchdog thread that records the exact operation and path in flight
  and *hard-exits* with a diagnostic instead of blocking forever;
* per-file and per-chunk progress so a stall names a concrete file.

All instrumentation is off by default and enabled with ``MANIFEST_DEBUG=1``.
"""
import os
import sys
import json
import time
import errno
import hashlib
import stat as stat_mod
import threading
import subprocess
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Exit code used when the watchdog trips. Distinct from 1 (normal failure) so a
# stalled run is unambiguously identifiable in the cutover journal.
STALL_EXIT_CODE = 86

DEBUG = os.environ.get("MANIFEST_DEBUG", "") == "1"

# A single file must finish within this budget (stat + open + full hash).
DEFAULT_PER_FILE_TIMEOUT = float(os.environ.get("MANIFEST_PER_FILE_TIMEOUT", "300"))
# No progress at all (no new file, no new chunk) within this budget = stall.
DEFAULT_STALL_TIMEOUT = float(os.environ.get("MANIFEST_STALL_TIMEOUT", "600"))

FILE_ATTRIBUTE_REPARSE_POINT = getattr(stat_mod, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


class ManifestStallError(RuntimeError):
    """Raised when a manifest operation exceeds its stall budget."""

    def __init__(self, operation: str, path: str, elapsed: float, extra: str = ""):
        self.operation = operation
        self.path = path
        self.elapsed = elapsed
        self.extra = extra
        super().__init__(
            f"Manifest stall: operation={operation} path={path} "
            f"elapsed={elapsed:.1f}s {extra}".strip()
        )


# --------------------------------------------------------------------------
# Progress / watchdog
# --------------------------------------------------------------------------

class Progress:
    """Tracks the operation currently in flight so a stall can be attributed."""

    def __init__(self, label: str = "", debug: Optional[bool] = None,
                 stall_timeout: float = DEFAULT_STALL_TIMEOUT,
                 per_file_timeout: float = DEFAULT_PER_FILE_TIMEOUT):
        self.label = label
        self.debug = DEBUG if debug is None else debug
        self.stall_timeout = stall_timeout
        self.per_file_timeout = per_file_timeout
        self.operation = "init"
        self.path = ""
        self.files_done = 0
        self.files_total = 0
        self.bytes_done = 0
        self._file_started = time.time()
        self._last_advance = time.time()
        self._t0 = time.time()
        self._lock = threading.Lock()
        self._watchdog = None
        self._stop = threading.Event()

    # -- state transitions -------------------------------------------------
    def begin(self, operation: str, path: str = "") -> None:
        with self._lock:
            self.operation = operation
            self.path = path
            if operation == "hash_file":
                self._file_started = time.time()

    def advance(self, nbytes: int = 0) -> None:
        with self._lock:
            self.bytes_done += nbytes
            self._last_advance = time.time()

    def file_done(self, size: int) -> None:
        with self._lock:
            self.files_done += 1
            self._last_advance = time.time()
            if self.debug:
                elapsed = time.time() - self._t0
                print(f"    [manifest] {self.files_done}/{self.files_total} "
                      f"{self.path} ({size} B) t={elapsed:.1f}s", flush=True)

    def set_total(self, n: int) -> None:
        with self._lock:
            self.files_total = n
            self._last_advance = time.time()

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            now = time.time()
            return {
                "label": self.label,
                "operation": self.operation,
                "path": self.path,
                "files_done": self.files_done,
                "files_total": self.files_total,
                "bytes_done": self.bytes_done,
                "elapsed_total": round(now - self._t0, 2),
                "elapsed_in_operation": round(now - self._last_advance, 2),
                "elapsed_in_file": round(now - self._file_started, 2),
            }

    # -- watchdog ----------------------------------------------------------
    def start_watchdog(self) -> None:
        if self._watchdog is not None:
            return
        self._watchdog = threading.Thread(target=self._watch, daemon=True)
        self._watchdog.start()

    def stop_watchdog(self) -> None:
        self._stop.set()

    def _watch(self) -> None:
        interval = max(0.25, min(2.0, self.stall_timeout / 20.0))
        while not self._stop.wait(interval):
            snap = self.snapshot()
            in_op = snap["elapsed_in_operation"]
            in_file = snap["elapsed_in_file"]
            stalled = in_op > self.stall_timeout
            file_over = (self.operation == "hash_file"
                         and in_file > self.per_file_timeout)
            if not (stalled or file_over):
                continue
            reason = "no_progress" if stalled else "per_file_timeout"
            self._trip(reason, snap)

    def _trip(self, reason: str, snap: Dict[str, Any]) -> None:
        diag = {
            "reason": reason,
            "detected_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "pid": os.getpid(),
            "stall_timeout_s": self.stall_timeout,
            "per_file_timeout_s": self.per_file_timeout,
        }
        diag.update(snap)
        out_dir = os.path.join(REPO_ROOT, "build", "audit")
        try:
            os.makedirs(out_dir, exist_ok=True)
            diag_path = os.path.join(
                out_dir,
                f"manifest_stall_pid{os.getpid()}_{int(time.time())}.json"
            )
            with open(diag_path, "w", encoding="utf-8") as fp:
                json.dump(diag, fp, indent=2, ensure_ascii=False)
        except Exception:
            diag_path = "<could not write diagnostic>"

        msg = (
            "\n" + "=" * 68 + "\n"
            f"[MANIFEST STALL] {reason}\n"
            f"  operation : {snap['operation']}\n"
            f"  path      : {snap['path']}\n"
            f"  in-op     : {snap['elapsed_in_operation']:.1f}s "
            f"(budget {self.stall_timeout:.0f}s)\n"
            f"  in-file   : {snap['elapsed_in_file']:.1f}s "
            f"(budget {self.per_file_timeout:.0f}s)\n"
            f"  progress  : {snap['files_done']}/{snap['files_total']} files, "
            f"{snap['bytes_done']} bytes, total {snap['elapsed_total']:.1f}s\n"
            f"  diagnostic: {diag_path}\n"
            "  Action: failing fast instead of blocking indefinitely.\n"
            + "=" * 68
        )
        print(msg, flush=True)
        try:
            sys.stderr.write(msg + "\n")
            sys.stderr.flush()
        except Exception:
            pass
        # os._exit is deliberate: the main thread may be blocked inside a
        # filesystem syscall that no Python-level timeout can interrupt.
        os._exit(STALL_EXIT_CODE)


# --------------------------------------------------------------------------
# Hashing
# --------------------------------------------------------------------------

def compute_sha256(filepath: str, progress: Optional[Progress] = None,
                   chunk_size: int = 65536) -> str:
    h = hashlib.sha256()
    if progress is not None:
        progress.begin("open_file", filepath)
    with open(filepath, "rb") as f:
        if progress is not None:
            progress.begin("hash_file", filepath)
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
            if progress is not None:
                progress.advance(len(chunk))
    return h.hexdigest()


def get_git_commit(cwd: str = REPO_ROOT, timeout: float = 30.0) -> str:
    """Best-effort HEAD lookup.

    ``stdin`` is explicitly closed: a git invocation that decides to prompt
    (credential helper, pager) would otherwise block forever while the parent
    waits at 0% CPU, which is indistinguishable from a filesystem hang.
    """
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
            stdin=subprocess.DEVNULL,
            timeout=timeout,
        )
        return res.stdout.strip()
    except Exception:
        return "unknown"


# --------------------------------------------------------------------------
# Deterministic file collection
# --------------------------------------------------------------------------

def classify_entry(abs_path: str, st: Optional[os.stat_result] = None) -> str:
    """Return 'file', 'symlink', 'junction', 'dir' or 'other'."""
    if st is None:
        try:
            st = os.lstat(abs_path)
        except OSError as exc:
            return f"stat_error:{exc.errno}"
    if stat_mod.S_ISLNK(st.st_mode):
        return "symlink"
    if stat_mod.S_ISDIR(st.st_mode):
        if getattr(st, "st_file_attributes", 0) & FILE_ATTRIBUTE_REPARSE_POINT:
            return "junction"
        return "dir"
    if stat_mod.S_ISREG(st.st_mode):
        return "file"
    return "other"


def collect_files(target_dir: str, progress: Optional[Progress] = None,
                  follow_dir_links: bool = False
                  ) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    """Collect a deterministic, sorted list of regular files to hash.

    Returns ``(entries, skipped)``. ``skipped`` is always reported explicitly so
    a production file can never be dropped silently.

    Directory reparse points (junctions / directory symlinks) are NOT descended
    into by default: a junction pointing at an ancestor would make the walk
    unbounded, and one pointing outside the tree would silently import foreign
    files into the manifest. Both cases are recorded in ``skipped``.
    """
    if progress is not None:
        progress.begin("walk", target_dir)

    entries: List[Dict[str, Any]] = []
    skipped: List[Dict[str, str]] = []
    stack: List[Tuple[str, str]] = [(target_dir, "")]

    while stack:
        abs_dir, rel_dir = stack.pop()
        try:
            with os.scandir(abs_dir) as it:
                children = list(it)
        except OSError as exc:
            skipped.append({
                "path": rel_dir or ".",
                "reason": f"scandir_failed:{errno.errorcode.get(exc.errno, exc.errno)}",
            })
            continue

        subdirs = []
        for entry in children:
            rel = f"{rel_dir}/{entry.name}" if rel_dir else entry.name
            try:
                st = entry.stat(follow_symlinks=False)
            except OSError as exc:
                skipped.append({
                    "path": rel,
                    "reason": f"stat_failed:{errno.errorcode.get(exc.errno, exc.errno)}",
                })
                continue

            kind = classify_entry(entry.path, st)
            if kind == "dir":
                subdirs.append((entry.path, rel))
            elif kind == "file":
                entries.append({
                    "path": rel,
                    "abs_path": entry.path,
                    "size_bytes": st.st_size,
                })
            elif kind in ("symlink", "junction"):
                try:
                    link_target = os.readlink(entry.path)
                except OSError:
                    link_target = "<unreadable>"
                is_dir_link = False
                try:
                    is_dir_link = os.path.isdir(entry.path)
                except OSError:
                    pass
                if is_dir_link and follow_dir_links:
                    subdirs.append((entry.path, rel))
                elif is_dir_link:
                    skipped.append({
                        "path": rel,
                        "reason": f"directory_reparse_point_not_followed:{kind}",
                        "target": link_target,
                    })
                else:
                    # File-level link: hash the target content exactly as open()
                    # would, but record the fact in the manifest.
                    try:
                        tst = os.stat(entry.path)
                    except OSError as exc:
                        skipped.append({
                            "path": rel,
                            "reason": f"link_target_unreadable:{errno.errorcode.get(exc.errno, exc.errno)}",
                            "target": link_target,
                        })
                        continue
                    entries.append({
                        "path": rel,
                        "abs_path": entry.path,
                        "size_bytes": tst.st_size,
                        "link": kind,
                        "link_target": link_target,
                    })
            else:
                skipped.append({
                    "path": rel,
                    "reason": f"non_regular_file:{stat_mod.filemode(st.st_mode)}",
                })

        # Deterministic depth-first order.
        subdirs.sort(key=lambda p: p[1])
        stack.extend(reversed(subdirs))

    entries.sort(key=lambda e: e["path"])
    skipped.sort(key=lambda s: s["path"])
    if progress is not None:
        progress.set_total(len(entries))
    return entries, skipped


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------

def generate_manifest(
    target_dir: str,
    output_manifest_path: str,
    extra_metadata: Optional[Dict[str, Any]] = None,
    progress: Optional[Progress] = None,
    stall_timeout: float = DEFAULT_STALL_TIMEOUT,
    per_file_timeout: float = DEFAULT_PER_FILE_TIMEOUT,
) -> Dict[str, Any]:
    """Generates a deterministic SHA-256 manifest for a target directory."""
    if not os.path.exists(target_dir):
        raise FileNotFoundError(f"Target directory does not exist: {target_dir}")

    os.makedirs(os.path.dirname(output_manifest_path), exist_ok=True)

    own_progress = progress is None
    if own_progress:
        progress = Progress(
            label=f"generate:{os.path.basename(os.path.normpath(target_dir))}",
            stall_timeout=stall_timeout,
            per_file_timeout=per_file_timeout,
        )
    progress.start_watchdog()

    t0 = time.time()
    files: List[Dict[str, Any]] = []
    total_bytes = 0
    try:
        entries, skipped = collect_files(target_dir, progress)
        if skipped and DEBUG:
            for s in skipped:
                print(f"    [manifest] SKIPPED {s['path']} ({s['reason']})",
                      flush=True)

        progress.begin("hash_files", target_dir)
        for e in entries:
            progress.begin("stat_file", e["abs_path"])
            try:
                sz = os.path.getsize(e["abs_path"])
            except OSError as exc:
                skipped.append({
                    "path": e["path"],
                    "reason": f"getsize_failed:{errno.errorcode.get(exc.errno, exc.errno)}",
                })
                continue
            sha = compute_sha256(e["abs_path"], progress)
            total_bytes += sz
            entry = {"path": e["path"], "size_bytes": sz, "sha256": sha}
            if e.get("link"):
                entry["link"] = e["link"]
                entry["link_target"] = e.get("link_target", "")
            files.append(entry)
            progress.file_done(sz)
    finally:
        progress.stop_watchdog()

    manifest = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "target_directory": os.path.basename(os.path.normpath(target_dir)),
        "source_commit": get_git_commit(),
        "total_files": len(files),
        "total_size_bytes": total_bytes,
        "total_size_mb": round(total_bytes / (1024 * 1024), 2),
    }

    if extra_metadata:
        manifest.update(extra_metadata)

    if skipped:
        # Explicit, never silent: callers can assert on this.
        manifest["skipped_entries"] = skipped
        manifest["skipped_count"] = len(skipped)

    manifest["files"] = files

    progress.begin("write_manifest", output_manifest_path)
    with open(output_manifest_path, "w", encoding="utf-8") as fp:
        json.dump(manifest, fp, indent=2, ensure_ascii=False)

    elapsed = time.time() - t0
    manifest["elapsed_seconds"] = round(elapsed, 2)
    return manifest


def verify_manifest(
    target_dir: str,
    manifest_path: str,
    ignore_extra: Optional[List[str]] = None,
    progress: Optional[Progress] = None,
    stall_timeout: float = DEFAULT_STALL_TIMEOUT,
    per_file_timeout: float = DEFAULT_PER_FILE_TIMEOUT,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Verifies a target directory against a SHA-256 manifest.
    Returns (is_match, details_dict).
    """
    if not os.path.exists(target_dir):
        return False, {"error": f"Target directory not found: {target_dir}"}
    if not os.path.exists(manifest_path):
        return False, {"error": f"Manifest file not found: {manifest_path}"}

    with open(manifest_path, "r", encoding="utf-8") as fp:
        manifest = json.load(fp)

    manifest_map = {entry["path"]: entry for entry in manifest.get("files", [])}
    found_paths = set()
    missing: List[str] = []
    modified: List[Dict[str, Any]] = []
    extra: List[str] = []
    ignore_set = set(ignore_extra or [])

    own_progress = progress is None
    if own_progress:
        progress = Progress(
            label=f"verify:{os.path.basename(os.path.normpath(target_dir))}",
            stall_timeout=stall_timeout,
            per_file_timeout=per_file_timeout,
        )
    progress.start_watchdog()

    try:
        entries, _skipped = collect_files(target_dir, progress)
        progress.begin("verify_files", target_dir)
        for e in entries:
            rel_p = e["path"]
            if rel_p in ignore_set:
                continue
            found_paths.add(rel_p)
            abs_p = e["abs_path"]

            if rel_p not in manifest_map:
                extra.append(rel_p)
                continue

            expected = manifest_map[rel_p]
            progress.begin("stat_file", abs_p)
            actual_sz = os.path.getsize(abs_p)
            if actual_sz != expected["size_bytes"]:
                modified.append({
                    "path": rel_p,
                    "reason": "size_mismatch",
                    "expected": expected["size_bytes"],
                    "actual": actual_sz,
                })
            else:
                actual_sha = compute_sha256(abs_p, progress)
                if actual_sha != expected["sha256"]:
                    modified.append({
                        "path": rel_p,
                        "reason": "sha256_mismatch",
                        "expected": expected["sha256"],
                        "actual": actual_sha,
                    })
            progress.file_done(actual_sz)
    finally:
        progress.stop_watchdog()

    for p in manifest_map:
        if p not in found_paths and p not in ignore_set:
            missing.append(p)

    is_match = (len(missing) == 0 and len(modified) == 0 and len(extra) == 0)
    details = {
        "is_match": is_match,
        "manifest_total_files": len(manifest_map),
        "target_total_files": len(found_paths),
        "missing_count": len(missing),
        "modified_count": len(modified),
        "extra_count": len(extra),
        "missing": missing[:50],
        "modified": modified[:50],
        "extra": extra[:50],
    }
    return is_match, details

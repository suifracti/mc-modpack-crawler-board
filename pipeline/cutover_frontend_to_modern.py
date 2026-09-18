"""
Architecture V2 - Phase 3D: Modern Frontend Production Cutover.

Switches the verified Modern Frontend (TypeScript + Vite) into Production
(converted_output/) with complete rollback guarantees and strict gate
verification.

Phase 3G-F-B reliability hardening
----------------------------------
A previous full cutover completed the swap (``converted_output`` was byte
identical to ``build/frontend_preview``) but the driving process then appeared
to stall for over an hour at 0% CPU, ~13 MB working set, with no child process.
It had to be killed by hand, and because nothing durable recorded how far the
run had progressed, the remaining steps were completed manually.

Two things made that undiagnosable and unrecoverable, and both are fixed here:

1. **No durable progress.** Progress existed only as block-buffered ``print()``
   lines on a captured pipe, so the last visible line was not a reliable
   indicator of the real stage. Every stage is now timed, journaled to
   ``build/cutover_transaction.json`` *before* it starts and *after* it
   finishes, and mirrored to a flushed log file.

2. **No timeouts and no idempotent resume.** Every child process now runs with
   ``stdin=DEVNULL`` and a hard timeout (a child that waits on input while the
   parent waits on the child is indistinguishable from a hang), is killed as a
   whole process tree on timeout, and streams its output live. The transaction
   journal makes the run resumable: if the swap is already complete and
   production still matches the recorded staging manifest, the run resumes at
   post-swap verification instead of re-copying ~2924 files.

Usage
-----
    python pipeline/cutover_frontend_to_modern.py                # full run
    python pipeline/cutover_frontend_to_modern.py --dry-run      # all gates, no swap
    python pipeline/cutover_frontend_to_modern.py --resume       # continue a killed run
    python pipeline/cutover_frontend_to_modern.py --no-resume    # force a fresh run
    python pipeline/cutover_frontend_to_modern.py --only-cutover # skip preflight gates
"""
import os
import sys
import json
import time
import shutil
import argparse
import hashlib
import subprocess
import threading
from typing import Optional

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from pipeline.manifest import (  # noqa: E402
    compute_sha256,
    generate_manifest,
    verify_manifest,
    get_git_commit,
    Progress,
    STALL_EXIT_CODE,
)

CONVERTED_OUTPUT_DIR = os.path.join(REPO_ROOT, "converted_output")
FRONTEND_PREVIEW_DIR = os.path.join(REPO_ROOT, "build", "frontend_preview")
STAGING_TEMP_DIR = os.path.join(REPO_ROOT, "build", "modern_staging_temp")
SWAP_TEMP_DIR = os.path.join(REPO_ROOT, "build", "legacy_pre_cutover_swap")
BACKUPS_DIR = os.path.join(REPO_ROOT, "build", "backups")
MANIFESTS_DIR = os.path.join(REPO_ROOT, "build", "manifests")
CANONICAL_DB = os.path.join(REPO_ROOT, "build", "canonical.db")
PRODUCTION_STATE_PATH = os.path.join(REPO_ROOT, "build", "production_state.json")
LOGS_DIR = os.path.join(REPO_ROOT, "build", "logs")
TRANSACTION_PATH = os.path.join(REPO_ROOT, "build", "cutover_transaction.json")

LEGACY_MANIFEST_PATH = os.path.join(MANIFESTS_DIR, "frontend_legacy_production.sha256.json")
MODERN_STAGING_MANIFEST_PATH = os.path.join(MANIFESTS_DIR, "frontend_modern_staging.sha256.json")
MODERN_PRODUCTION_MANIFEST_PATH = os.path.join(MANIFESTS_DIR, "frontend_modern_production.sha256.json")

# Ordered stage names, in the order the run actually performs them. `plan_resume`
# uses these to decide what may be skipped, so the order must match execution:
# the state file is written at the end of execute_cutover(), and the acceptance
# browser gates run afterwards in post_cutover_verification().
STAGES = [
    "prepared",
    "legacy_manifested",
    "legacy_backed_up",
    "staging_manifested",
    "swapped",
    "post_swap_verified",
    "state_written",
    "browser_verified",
    "complete",
]

DEFAULT_GATE_TIMEOUT = float(os.environ.get("CUTOVER_GATE_TIMEOUT", "1800"))
DEFAULT_NPM_TIMEOUT = float(os.environ.get("CUTOVER_NPM_TIMEOUT", "1800"))

# Browser-gate ports. Overridable so two cutover runs (e.g. two parallel
# worktrees) cannot fight over the same CDP port - the harness reclaims a port
# it finds occupied, which would otherwise kill the other run's browser.
WIRING_PORT = os.environ.get("CUTOVER_WIRING_PORT", "8780")
LEGACY_PORT = os.environ.get("CUTOVER_LEGACY_PORT", "8768")
PREVIEW_PORT = os.environ.get("CUTOVER_PREVIEW_PORT", "8770")

_LOG_FILE = None
_LOG_LOCK = threading.Lock()
_TIMINGS = {}


# --------------------------------------------------------------------------
# Logging / timing
# --------------------------------------------------------------------------

def log(msg: str) -> None:
    """Print and mirror to the durable cutover log, always flushed.

    Flushing matters: when stdout is a captured pipe Python block-buffers it,
    so an unflushed run looks stalled at a stage it already passed.
    """
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with _LOG_LOCK:
        if _LOG_FILE is not None:
            try:
                _LOG_FILE.write(line + "\n")
                _LOG_FILE.flush()
            except Exception:
                pass


def banner(msg: str) -> None:
    log("")
    log("=" * 68)
    log(f"  {msg}")
    log("=" * 68)


def stage_start(name: str) -> float:
    log(f"[stage] >>> {name}")
    return time.time()


def stage_end(name: str, t0: float, extra: str = "") -> float:
    dt = time.time() - t0
    _TIMINGS[name] = round(_TIMINGS.get(name, 0.0) + dt, 2)
    log(f"[stage] <<< {name} done in {dt:.2f}s {extra}".rstrip())
    return dt


# --------------------------------------------------------------------------
# Transaction journal
# --------------------------------------------------------------------------

def read_transaction() -> dict:
    if not os.path.exists(TRANSACTION_PATH):
        return {}
    try:
        with open(TRANSACTION_PATH, "r", encoding="utf-8") as fp:
            return json.load(fp) or {}
    except (json.JSONDecodeError, OSError):
        return {}


def write_transaction(txn: dict) -> None:
    txn["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    txn["pid"] = os.getpid()
    txn["timings"] = dict(_TIMINGS)
    tmp = TRANSACTION_PATH + ".tmp"
    os.makedirs(os.path.dirname(TRANSACTION_PATH), exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as fp:
        json.dump(txn, fp, indent=2, ensure_ascii=False)
        fp.flush()
        os.fsync(fp.fileno())
    os.replace(tmp, TRANSACTION_PATH)


def advance(txn: dict, stage: str) -> None:
    """Record that `stage` completed. Called immediately after each stage."""
    completed = txn.setdefault("completed_stages", [])
    if stage not in completed:
        completed.append(stage)
    txn["stage"] = stage
    write_transaction(txn)


def stage_index(stage: str) -> int:
    try:
        return STAGES.index(stage)
    except ValueError:
        return -1


def needs_browser_gates(txn: dict) -> bool:
    """Whether the post-cutover acceptance gates still have to run.

    Regression guard: this must be True when the journal stops at
    ``state_written``. An earlier revision compared against a stage list whose
    order did not match execution and silently skipped the acceptance gates on a
    complete fresh run.
    """
    return stage_index(txn.get("stage", "")) < stage_index("browser_verified")


def rollup_digest(manifest: dict) -> str:
    """Order-independent digest of a manifest's (path, sha256) pairs."""
    h = hashlib.sha256()
    for entry in sorted(manifest.get("files", []), key=lambda e: e["path"]):
        h.update(entry["path"].encode("utf-8"))
        h.update(b"\0")
        h.update(entry["sha256"].encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()


# --------------------------------------------------------------------------
# Child process handling
# --------------------------------------------------------------------------

def kill_tree(pid: int) -> None:
    """Kill a process and all of its descendants."""
    if not pid:
        return
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                capture_output=True, stdin=subprocess.DEVNULL, timeout=60,
            )
        else:
            os.killpg(os.getpgid(pid), 9)
    except Exception:
        pass


def run_cmd(cmd: list, desc: str, timeout: float = DEFAULT_GATE_TIMEOUT,
            cwd: str = None, env: dict = None) -> None:
    """Run a child, streaming its output live, with a hard timeout.

    Output is streamed rather than captured so that a stalled child still leaves
    the partial evidence that identifies where it stalled. stdin is /dev/null so
    a child can never sit waiting for input while the parent waits for it.
    """
    exec_cmd = list(cmd)
    if sys.platform == "win32" and exec_cmd[0] == "npm":
        exec_cmd[0] = "npm.cmd"
    log(f"[*] Running {desc}: {' '.join(exec_cmd)} (timeout {timeout:.0f}s)")
    t0 = time.time()
    proc = subprocess.Popen(
        exec_cmd,
        cwd=cwd or REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        bufsize=1,
    )

    def pump():
        try:
            for line in proc.stdout:
                line = line.rstrip("\n")
                if line:
                    log(f"    | {line}")
        except Exception:
            pass

    reader = threading.Thread(target=pump, daemon=True)
    reader.start()

    timed_out = False
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        log(f"[-] TIMEOUT after {timeout:.0f}s in '{desc}' (pid {proc.pid}) "
            f"- killing process tree")
        kill_tree(proc.pid)
        try:
            proc.wait(timeout=60)
        except subprocess.TimeoutExpired:
            pass
    finally:
        reader.join(timeout=10)
        try:
            if proc.stdout:
                proc.stdout.close()
        except Exception:
            pass

    elapsed = time.time() - t0
    if timed_out:
        raise RuntimeError(
            f"Step '{desc}' exceeded its {timeout:.0f}s budget and was killed. "
            f"The child was still running after {elapsed:.1f}s."
        )
    if proc.returncode != 0:
        if proc.returncode == STALL_EXIT_CODE:
            raise RuntimeError(
                f"Step '{desc}' tripped the manifest stall watchdog "
                f"(exit {STALL_EXIT_CODE}). See build/audit/manifest_stall_*.json "
                f"for the exact operation and path."
            )
        raise RuntimeError(f"Step '{desc}' failed with exit code {proc.returncode}")
    log(f"[+] PASSED: {desc} ({elapsed:.2f}s)")


# --------------------------------------------------------------------------
# Directory helpers
# --------------------------------------------------------------------------

def get_dir_size(path: str) -> int:
    if not os.path.exists(path):
        return 0
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def count_files(path: str) -> int:
    if not os.path.exists(path):
        return 0
    count = 0
    for _, _, files in os.walk(path):
        count += len(files)
    return count


def copy_tree_progressed(src: str, dst: str, label: str,
                         stall_timeout: float = 900.0) -> None:
    """copytree with a progress watchdog.

    ``shutil.copytree`` on this tree has been measured at a ~20x wall/CPU ratio
    (47.96s wall vs 2.39s of Python CPU for 2924 files), i.e. the wall time is
    dominated by work charged to another component (filesystem filter driver /
    antivirus), not to Python. That is precisely the shape of stall that looks
    like "0% CPU" in the Python process, so it gets an explicit watchdog that
    names the file being copied.
    """
    progress = Progress(label=label, stall_timeout=stall_timeout)
    progress.start_watchdog()
    t0 = time.time()
    try:
        os.makedirs(dst, exist_ok=True)
        for root, dirs, files in os.walk(src):
            dirs.sort()
            rel_root = os.path.relpath(root, src)
            target_root = dst if rel_root == "." else os.path.join(dst, rel_root)
            os.makedirs(target_root, exist_ok=True)
            for f in sorted(files):
                s = os.path.join(root, f)
                d = os.path.join(target_root, f)
                progress.begin("copy_file", s)
                shutil.copy2(s, d)
                try:
                    progress.advance(os.path.getsize(d))
                except OSError:
                    pass
    finally:
        progress.stop_watchdog()
    log(f"    copied {count_files(dst)} files in {time.time() - t0:.2f}s")


# --------------------------------------------------------------------------
# Gates
# --------------------------------------------------------------------------

def preflight_disk_space() -> None:
    t0 = stage_start("preflight_disk_space")
    total, used, free = shutil.disk_usage(REPO_ROOT)
    legacy_size = get_dir_size(CONVERTED_OUTPUT_DIR)
    modern_size = get_dir_size(FRONTEND_PREVIEW_DIR)
    margin = max(1024 * 1024 * 1024, int(0.20 * (legacy_size + modern_size)))
    required_space = legacy_size + modern_size + margin

    log(f"  Legacy Production Size: {legacy_size / (1024*1024):.2f} MB")
    log(f"  Modern Staging Size   : {modern_size / (1024*1024):.2f} MB")
    log(f"  Safety Margin         : {margin / (1024*1024):.2f} MB")
    log(f"  Required Free Space   : {required_space / (1024*1024):.2f} MB")
    log(f"  Actual Free Space     : {free / (1024*1024):.2f} MB")

    if free < required_space:
        raise RuntimeError(
            f"Disk space preflight failed! Available {free / (1024*1024):.2f} MB "
            f"< Required {required_space / (1024*1024):.2f} MB"
        )
    log("  [GATE PASSED] Sufficient disk space verified.")
    stage_end("preflight_disk_space", t0)


def preflight_quality_gates() -> None:
    t0 = stage_start("preflight_quality_gates")
    run_cmd(["npm", "--prefix", "apps/web", "run", "typecheck"],
            "TypeScript Typecheck (tsc --noEmit)", timeout=DEFAULT_NPM_TIMEOUT)
    run_cmd(["npm", "--prefix", "apps/web", "test"],
            "Vitest Unit Tests (vitest run)", timeout=DEFAULT_NPM_TIMEOUT)
    run_cmd([sys.executable, "tests/test_structured_mcmod_contract.py"],
            "MCMod Structured Data Contract")
    run_cmd([sys.executable, "tests/test_search_golden.py"], "Search Golden Tests")
    run_cmd([sys.executable, "tests/test_filter_golden.py"], "Filter Golden Tests")
    run_cmd([sys.executable, "tests/test_bili_grouping_explanation.py"],
            "Bilibili Grouping Invariant (53 raw preserved + evidence-backed merges)")
    run_cmd([sys.executable, "tests/test_correctness_regressions.py"],
            "Correctness Regressions Test Suite (9 P0 Items)")
    run_cmd([sys.executable, "tests/test_release_date_semantics.py"],
            "Release-Date Semantics Contract (Phase 3F.2)")
    run_cmd([sys.executable, "tests/test_mcmod_match_reason_source_integrity.py"],
            "Match-Reason Structured Source Integrity (Phase 3G-D.1)")
    run_cmd([sys.executable, "tests/test_manifest_hardening.py"],
            "Manifest Determinism / Stall-Guard / Backward-Compat")
    run_cmd([sys.executable, "tests/test_cutover_transaction.py"],
            "Cutover Transaction / Resume / Torn-Swap Recovery")
    log("  [GATE PASSED] All code quality and contract tests passed.")
    stage_end("preflight_quality_gates", t0)


def preflight_stage_preview() -> None:
    t0 = stage_start("preflight_stage_preview")
    run_cmd([sys.executable, "pipeline/stage_frontend_preview.py"],
            "Stage Frontend Preview", timeout=DEFAULT_NPM_TIMEOUT)
    log("  [GATE PASSED] Frontend preview staged.")
    stage_end("preflight_stage_preview", t0)


def preflight_wiring_and_browsers() -> None:
    t0 = stage_start("preflight_browser_gates")
    run_cmd(["node", "pipeline/smoke_test_wiring.js", "build/frontend_preview", WIRING_PORT],
            "Preview Integration Wiring Test (18/18)")
    run_cmd(["node", "pipeline/smoke_test_single.js", "converted_output", LEGACY_PORT],
            "Legacy Production Browser Test (33/33)")
    run_cmd(["node", "pipeline/smoke_test_single.js", "build/frontend_preview", PREVIEW_PORT],
            "Preview Browser Test (33/33)")
    log("  [GATE PASSED] All preflight browser and wiring gates passed.")
    stage_end("preflight_browser_gates", t0)


# --------------------------------------------------------------------------
# Cutover
# --------------------------------------------------------------------------

def _load_manifest(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fp:
        return json.load(fp)


def plan_resume(txn: dict, allow_resume: bool) -> dict:
    """Decide which stages can be skipped, refusing anything unsafe.

    Returns a dict with the resolved ``resume_stage`` and a human-readable
    reason. Safety rule: we only skip work that is *provably already done*.
    """
    decision = {"resume_stage": None, "reason": "fresh run"}
    if not allow_resume:
        decision["reason"] = "resume disabled by --no-resume"
        return decision
    if not txn:
        decision["reason"] = "no transaction journal"
        return decision

    recorded = txn.get("stage", "")
    idx = stage_index(recorded)
    if idx < 0:
        decision["reason"] = f"journal has unknown stage '{recorded}'"
        return decision
    if recorded == "complete":
        decision["reason"] = "journal says the previous run completed"
        return decision

    if idx >= stage_index("swapped"):
        staging_manifest_path = txn.get("staging_manifest_path", MODERN_STAGING_MANIFEST_PATH)
        if not os.path.exists(staging_manifest_path):
            decision["reason"] = "swap recorded but the staging manifest is gone; refusing to guess"
            return decision
        expected = txn.get("staging_rollup")
        actual_manifest = _load_manifest(staging_manifest_path)
        actual_rollup = rollup_digest(actual_manifest)
        if expected and actual_rollup != expected:
            decision["reason"] = ("staging manifest content changed since the journal was "
                                  "written; refusing to resume")
            return decision
        is_match, details = verify_manifest(CONVERTED_OUTPUT_DIR, staging_manifest_path)
        if not is_match:
            # Production was modified after the swap. Never silently repair.
            raise RuntimeError(
                "Refusing to resume: the journal records a completed swap but "
                "converted_output no longer matches the staged modern manifest "
                f"(missing={details.get('missing_count')}, "
                f"modified={details.get('modified_count')}, "
                f"extra={details.get('extra_count')}). "
                "Production would be overwritten, so this needs a human decision."
            )
        decision["resume_stage"] = recorded
        decision["reason"] = (
            f"swap already complete and converted_output matches the staged modern "
            f"manifest ({details.get('target_total_files')} files); skipping "
            f"re-copy and re-swap"
        )
        return decision

    decision["reason"] = (f"journal stage '{recorded}' is before the swap; "
                          f"production was never touched, safe to redo from the start")
    return decision


def recover_torn_swap(txn: dict) -> Optional[str]:
    """Repair the only non-atomic window in the cutover.

    The swap is two renames:

        converted_output  -> build/legacy_pre_cutover_swap
        build/modern_staging_temp -> converted_output

    A kill between them leaves ``converted_output`` *missing*. Without this
    recovery a resumed run would either crash on a non-existent production
    directory or - worse - try to manifest an empty tree and call it success.

    Returns the stage the run should resume from, or None if nothing was torn.
    """
    if os.path.exists(CONVERTED_OUTPUT_DIR):
        return None

    log("[!] converted_output is missing: a previous run died mid-swap.")
    staging_ok = False
    if os.path.exists(STAGING_TEMP_DIR) and os.path.exists(MODERN_STAGING_MANIFEST_PATH):
        staging_ok, sdetails = verify_manifest(STAGING_TEMP_DIR, MODERN_STAGING_MANIFEST_PATH)
        log(f"    staged modern tree present and verified against its manifest: {staging_ok}")
        if not staging_ok:
            log(f"    staging temp detail: {sdetails}")

    if staging_ok:
        log("[*] Completing the interrupted swap (modern staging -> converted_output).")
        shutil.move(STAGING_TEMP_DIR, CONVERTED_OUTPUT_DIR)
        advance(txn, "swapped")
        log("[+] Interrupted swap completed; production is now the staged modern frontend.")
        return "swapped"

    if os.path.exists(SWAP_TEMP_DIR):
        log("[*] Staged tree unusable; rolling back to the parked legacy production.")
        shutil.move(SWAP_TEMP_DIR, CONVERTED_OUTPUT_DIR)
        log("[+] Rolled back; production is the legacy frontend again.")
        return None

    raise RuntimeError(
        "converted_output is missing and neither the staged modern tree "
        "(build/modern_staging_temp) nor the parked legacy tree "
        "(build/legacy_pre_cutover_swap) is available. Refusing to continue - "
        "this needs a human decision."
    )


def execute_cutover(txn: dict, resume_stage: str = None,
                    dry_run: bool = False) -> str:
    banner("Executing Production Frontend Cutover (Legacy -> Modern)")
    os.makedirs(MANIFESTS_DIR, exist_ok=True)
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    commit = get_git_commit(REPO_ROOT)
    resume_idx = stage_index(resume_stage) if resume_stage else -1

    # ---------------------------------------------------------------- Step 1
    if resume_idx < stage_index("legacy_manifested"):
        t0 = stage_start("step1_legacy_manifest")
        legacy_files = count_files(CONVERTED_OUTPUT_DIR)
        legacy_bytes = get_dir_size(CONVERTED_OUTPUT_DIR)
        legacy_manifest = generate_manifest(
            target_dir=CONVERTED_OUTPUT_DIR,
            output_manifest_path=LEGACY_MANIFEST_PATH,
            extra_metadata={
                "frontend_type": "legacy",
                "source_commit": commit,
                "file_count": legacy_files,
                "total_size": legacy_bytes,
            },
        )
        is_match, details = verify_manifest(CONVERTED_OUTPUT_DIR, LEGACY_MANIFEST_PATH)
        if not is_match:
            raise RuntimeError(f"Legacy Production manifest verification failed: {details}")
        log(f"  [+] Legacy Production manifest created & verified "
            f"({legacy_manifest['total_files']} files, {legacy_manifest['total_size_mb']} MB).")
        txn["legacy_manifest_path"] = LEGACY_MANIFEST_PATH
        txn["legacy_rollup"] = rollup_digest(legacy_manifest)
        advance(txn, "legacy_manifested")
        stage_end("step1_legacy_manifest", t0)
    else:
        log("[skip] Step 1 legacy manifest (already done)")

    # ---------------------------------------------------------------- Step 2
    if resume_idx < stage_index("legacy_backed_up"):
        t0 = stage_start("step2_legacy_backup")
        ts = time.strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(BACKUPS_DIR, f"frontend-legacy-{ts}")
        log(f"  Backing up Legacy Production -> {backup_dir}")
        copy_tree_progressed(CONVERTED_OUTPUT_DIR, backup_dir, "legacy_backup")
        with open(os.path.join(backup_dir, "metadata.json"), "w", encoding="utf-8") as fp:
            json.dump({
                "backed_up_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "source_commit": commit,
                "manifest_path": os.path.relpath(LEGACY_MANIFEST_PATH, REPO_ROOT).replace("\\", "/"),
                "frontend_type": "legacy",
            }, fp, indent=2, ensure_ascii=False)
        is_backup_valid, bdetails = verify_manifest(
            backup_dir, LEGACY_MANIFEST_PATH, ignore_extra=["metadata.json"])
        if not is_backup_valid:
            raise RuntimeError(f"Legacy backup verification failed against manifest: {bdetails}")
        log("  [+] Legacy backup verified 100% against manifest.")
        txn["backup_dir"] = os.path.relpath(backup_dir, REPO_ROOT).replace("\\", "/")
        advance(txn, "legacy_backed_up")
        stage_end("step2_legacy_backup", t0)
    else:
        backup_dir = os.path.join(REPO_ROOT, txn.get("backup_dir", "")) \
            if txn.get("backup_dir") else None
        log(f"[skip] Step 2 legacy backup (already done: {txn.get('backup_dir')})")

    # ---------------------------------------------------------------- Step 3
    if resume_idx < stage_index("staging_manifested"):
        t0 = stage_start("step3_staging_manifest")
        staging_manifest = generate_manifest(
            target_dir=FRONTEND_PREVIEW_DIR,
            output_manifest_path=MODERN_STAGING_MANIFEST_PATH,
            extra_metadata={"frontend_type": "modern-vite", "source_commit": commit},
        )
        is_staging_valid, sdetails = verify_manifest(
            FRONTEND_PREVIEW_DIR, MODERN_STAGING_MANIFEST_PATH)
        if not is_staging_valid:
            raise RuntimeError(f"Modern Staging manifest verification failed: {sdetails}")
        log(f"  [+] Modern Staging manifest verified "
            f"({staging_manifest['total_files']} files, {staging_manifest['total_size_mb']} MB).")
        txn["staging_manifest_path"] = MODERN_STAGING_MANIFEST_PATH
        txn["staging_file_count"] = staging_manifest["total_files"]
        txn["staging_total_size_bytes"] = staging_manifest["total_size_bytes"]
        txn["staging_rollup"] = rollup_digest(staging_manifest)
        advance(txn, "staging_manifested")
        stage_end("step3_staging_manifest", t0)
    else:
        log("[skip] Step 3 staging manifest (already done)")

    if dry_run:
        log("[dry-run] stopping before the swap; production untouched.")
        txn["dry_run"] = True
        write_transaction(txn)
        return txn.get("backup_dir", "")

    # ---------------------------------------------------------------- Step 4
    if resume_idx < stage_index("swapped"):
        t0 = stage_start("step4_swap")
        if os.path.exists(STAGING_TEMP_DIR):
            log("  Removing leftover staging temp dir")
            shutil.rmtree(STAGING_TEMP_DIR, ignore_errors=True)
        if os.path.exists(SWAP_TEMP_DIR):
            log("  Removing leftover swap temp dir")
            shutil.rmtree(SWAP_TEMP_DIR, ignore_errors=True)

        log("  Copying staging preview -> staging temp (watchdogged)")
        copy_tree_progressed(FRONTEND_PREVIEW_DIR, STAGING_TEMP_DIR, "staging_temp_copy")
        is_temp_valid, tdetails = verify_manifest(STAGING_TEMP_DIR, MODERN_STAGING_MANIFEST_PATH)
        if not is_temp_valid:
            shutil.rmtree(STAGING_TEMP_DIR, ignore_errors=True)
            raise RuntimeError(f"Staging temp copy failed verification before swap: {tdetails}")

        # Journal the intent *before* touching production so a kill between the
        # two renames is still recoverable from the journal.
        txn["swap_intent"] = {
            "from": os.path.relpath(CONVERTED_OUTPUT_DIR, REPO_ROOT).replace("\\", "/"),
            "to": os.path.relpath(SWAP_TEMP_DIR, REPO_ROOT).replace("\\", "/"),
            "staged_from": os.path.relpath(STAGING_TEMP_DIR, REPO_ROOT).replace("\\", "/"),
        }
        write_transaction(txn)

        try:
            shutil.move(CONVERTED_OUTPUT_DIR, SWAP_TEMP_DIR)
            shutil.move(STAGING_TEMP_DIR, CONVERTED_OUTPUT_DIR)
        except Exception as swap_err:
            log(f"[-] CRITICAL ERROR during swap: {swap_err}")
            log("[*] Initiating self-healing rollback...")
            if os.path.exists(SWAP_TEMP_DIR) and not os.path.exists(CONVERTED_OUTPUT_DIR):
                shutil.move(SWAP_TEMP_DIR, CONVERTED_OUTPUT_DIR)
            elif not os.path.exists(CONVERTED_OUTPUT_DIR) and txn.get("backup_dir"):
                shutil.copytree(os.path.join(REPO_ROOT, txn["backup_dir"]), CONVERTED_OUTPUT_DIR)
            raise RuntimeError(f"Cutover failed during swap: {swap_err}. Self-healing executed.")

        advance(txn, "swapped")
        stage_end("step4_swap", t0)

        t1 = stage_start("step4b_cleanup_legacy_swap")
        shutil.rmtree(SWAP_TEMP_DIR, ignore_errors=True)
        stage_end("step4b_cleanup_legacy_swap", t1)
    else:
        log(f"[skip] Step 4 swap (already done; {resume_stage})")

    # ---------------------------------------------------------------- Step 5
    if resume_idx < stage_index("post_swap_verified"):
        t0 = stage_start("step5_post_swap_manifest")
        prod_manifest = generate_manifest(
            target_dir=CONVERTED_OUTPUT_DIR,
            output_manifest_path=MODERN_PRODUCTION_MANIFEST_PATH,
            extra_metadata={
                "frontend_type": "modern-vite",
                "source_commit": commit,
                "backup_legacy_path": txn.get("backup_dir", ""),
            },
        )
        is_prod_valid, pdetails = verify_manifest(
            CONVERTED_OUTPUT_DIR, MODERN_PRODUCTION_MANIFEST_PATH)
        if not is_prod_valid:
            log(f"[-] Modern Production verification failed: {pdetails}")
            log("[*] Rolling back to legacy backup...")
            shutil.rmtree(CONVERTED_OUTPUT_DIR, ignore_errors=True)
            if txn.get("backup_dir"):
                shutil.copytree(os.path.join(REPO_ROOT, txn["backup_dir"]), CONVERTED_OUTPUT_DIR)
            raise RuntimeError("Modern Production manifest mismatch! Rolled back to legacy.")
        log(f"  [+] Modern Production verified 100% match "
            f"({prod_manifest['total_files']} files, {prod_manifest['total_size_mb']} MB).")

        # Cross-check: production must equal staging byte for byte.
        staging_manifest = _load_manifest(MODERN_STAGING_MANIFEST_PATH)
        prod_rollup = rollup_digest(prod_manifest)
        staging_rollup = rollup_digest(staging_manifest)
        if prod_rollup != staging_rollup:
            raise RuntimeError(
                "Post-swap rollup mismatch: production does not match the staged "
                f"modern manifest (prod={prod_rollup[:16]} staging={staging_rollup[:16]})"
            )
        txn["production_rollup"] = prod_rollup
        advance(txn, "post_swap_verified")
        stage_end("step5_post_swap_manifest", t0)
    else:
        log("[skip] Step 5 post-swap manifest (already done)")

    # ---------------------------------------------------------------- Step 6
    if resume_idx < stage_index("state_written"):
        t0 = stage_start("step6_state_write")
        db_hash = compute_sha256(CANONICAL_DB) if os.path.exists(CANONICAL_DB) else "unknown"

        state = {}
        if os.path.exists(PRODUCTION_STATE_PATH):
            try:
                with open(PRODUCTION_STATE_PATH, "r", encoding="utf-8") as fp:
                    state = json.load(fp) or {}
            except (json.JSONDecodeError, OSError):
                state = {}

        state.update({
            "active_pipeline": "v2",
            "active_frontend": "modern-vite",
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "frontend_source_commit": commit,
            "frontend_code_commit": commit,
            "production_build_commit": commit,
            "frontend_manifest": os.path.relpath(MODERN_PRODUCTION_MANIFEST_PATH, REPO_ROOT).replace("\\", "/"),
            "production_manifest": os.path.relpath(MODERN_PRODUCTION_MANIFEST_PATH, REPO_ROOT).replace("\\", "/"),
            "legacy_frontend_backup": txn.get("backup_dir") or state.get("legacy_frontend_backup", ""),
            "legacy_frontend_manifest": os.path.relpath(LEGACY_MANIFEST_PATH, REPO_ROOT).replace("\\", "/"),
            "legacy_fallback_staging": "build/frontend_legacy_current_data",
            "canonical_db_hash": db_hash,
            "record_count": 73522,
            "cutover_transaction": os.path.relpath(TRANSACTION_PATH, REPO_ROOT).replace("\\", "/"),
        })
        with open(PRODUCTION_STATE_PATH, "w", encoding="utf-8") as fp:
            json.dump(state, fp, indent=2, ensure_ascii=False)
        log("  [+] production_state.json updated successfully.")
        advance(txn, "state_written")
        stage_end("step6_state_write", t0)
    else:
        log("[skip] Step 6 state write (already done)")

    return txn.get("backup_dir", "")


def post_cutover_verification() -> None:
    t0 = stage_start("post_cutover_browser_gates")
    run_cmd(["node", "pipeline/smoke_test_single.js", "converted_output", LEGACY_PORT],
            "Modern Production Browser Test (33/33)")
    run_cmd(["node", "pipeline/smoke_test_wiring.js", "converted_output", WIRING_PORT],
            "Modern Production Wiring Test (18/18)")
    log("  [GATE PASSED] Modern Production accepted with 0 regressions.")
    stage_end("post_cutover_browser_gates", t0)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def parse_args(argv):
    ap = argparse.ArgumentParser(description="Modern frontend production cutover")
    ap.add_argument("--dry-run", action="store_true",
                    help="run every gate and prepare the swap, but never touch production")
    ap.add_argument("--resume", action="store_true",
                    help="continue a previous run recorded in build/cutover_transaction.json")
    ap.add_argument("--no-resume", action="store_true",
                    help="ignore the journal and force a fresh run")
    ap.add_argument("--only-cutover", action="store_true",
                    help="skip the preflight gates and go straight to the cutover")
    ap.add_argument("--gate-timeout", type=float, default=DEFAULT_GATE_TIMEOUT,
                    help="per-child-process timeout in seconds")
    ap.add_argument("--no-browser-gates", action="store_true",
                    help="skip the post-cutover browser gates")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    global _LOG_FILE
    args = parse_args(argv if argv is not None else sys.argv[1:])

    os.makedirs(LOGS_DIR, exist_ok=True)
    log_name = f"cutover_{time.strftime('%Y%m%d_%H%M%S')}.log"
    _LOG_FILE = open(os.path.join(LOGS_DIR, log_name), "a", encoding="utf-8")

    banner("Architecture V2 - Phase 3D Frontend Cutover Process")
    t_start = time.time()
    log(f"  log file      : build/logs/{log_name}")
    log(f"  python        : {sys.version.split()[0]}")
    log(f"  args          : dry_run={args.dry_run} resume={args.resume} "
        f"no_resume={args.no_resume} only_cutover={args.only_cutover}")

    previous = read_transaction()
    try:
        if args.no_resume:
            decision = {"resume_stage": None, "reason": "resume disabled by --no-resume"}
        else:
            decision = plan_resume(previous, allow_resume=True)
    except Exception as exc:
        # An unsafe resume (production changed after a recorded swap) must stop
        # the run with a clear message rather than a traceback.
        log(f"[-] REFUSING TO RUN: {exc}")
        return 1
    resume_stage = decision["resume_stage"]
    log(f"  resume plan   : {decision['reason']}")
    if resume_stage:
        log(f"  resuming from : {resume_stage}")

    txn = {
        "transaction_id": time.strftime("%Y%m%d_%H%M%S") + f"-{os.getpid()}",
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "source_commit": get_git_commit(REPO_ROOT),
        "target_dir": "converted_output",
        "resumed_from": resume_stage,
        "resume_reason": decision["reason"],
        "dry_run": bool(args.dry_run),
        "stage": previous.get("stage", "") if resume_stage else "",
        "completed_stages": list(previous.get("completed_stages", [])) if resume_stage else [],
    }
    # Carry forward the recorded artifacts so a resumed run can reuse them.
    for key in ("legacy_manifest_path", "legacy_rollup", "backup_dir",
                "staging_manifest_path", "staging_file_count",
                "staging_total_size_bytes", "staging_rollup", "production_rollup"):
        if key in previous and key not in txn:
            txn[key] = previous[key]
    advance(txn, "prepared")

    try:
        torn_stage = recover_torn_swap(txn)
        if torn_stage:
            resume_stage = torn_stage

        if not args.only_cutover:
            preflight_disk_space()
            preflight_quality_gates()
            preflight_stage_preview()
            preflight_wiring_and_browsers()

        backup_dir = execute_cutover(txn, resume_stage=resume_stage, dry_run=args.dry_run)

        if not args.dry_run and not args.no_browser_gates:
            if needs_browser_gates(txn):
                post_cutover_verification()
                advance(txn, "browser_verified")
            else:
                log("[skip] post-cutover browser gates (already done)")

        if not args.dry_run:
            advance(txn, "complete")
    except Exception as exc:
        txn["failed_at"] = txn.get("stage", "")
        txn["failure"] = f"{exc.__class__.__name__}: {exc}"
        write_transaction(txn)
        log(f"[-] CUTOVER FAILED at stage '{txn.get('failed_at')}': {exc}")
        log(f"[-] Journal preserved at build/cutover_transaction.json "
            f"(resume with --resume)")
        log(f"[-] Total elapsed: {time.time() - t_start:.2f}s")
        return 1

    total = time.time() - t_start
    banner("PHASE 3D PRODUCTION CUTOVER SUCCESSFUL!")
    log("  Active Frontend       : modern-vite")
    log(f"  Legacy Backup Path    : {backup_dir}")
    log(f"  Total Cutover Duration: {total:.2f}s")
    log("")
    log("--- per-stage timings (seconds) ---")
    for name in sorted(_TIMINGS, key=lambda n: -_TIMINGS[n]):
        log(f"  {name:34s} {_TIMINGS[name]:10.2f}")
    log(f"  {'TOTAL (measured stages)':34s} {sum(_TIMINGS.values()):10.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

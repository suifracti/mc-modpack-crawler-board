"""
Phase 3G-F-B: minimal repro for the cutover final-manifest hang.

Runs manifest generation / verification against an arbitrary directory with a
per-file watchdog log so a stall can be attributed to one concrete file and one
concrete syscall, instead of "Windows filesystem flaky".

Usage:
    python pipeline/audit/repro_manifest_hang.py <mode> <target_dir> [label]

    mode = gen | verify | both
"""
import os
import sys
import json
import time
import hashlib
import traceback

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from pipeline.manifest import compute_sha256, generate_manifest, verify_manifest

LOG_PATH = os.path.join(REPO_ROOT, "build", "audit", "repro_manifest_hang.log")


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as fp:
        fp.write(line + "\n")


def classify(path: str) -> str:
    """Report what kind of filesystem object a path is."""
    try:
        st = os.lstat(path)
    except OSError as exc:
        return f"LSTAT_ERROR:{exc.__class__.__name__}"
    import stat as stat_mod
    kind = "file" if stat_mod.S_ISREG(st.st_mode) else (
        "dir" if stat_mod.S_ISDIR(st.st_mode) else "other")
    flags = []
    if os.path.islink(path):
        flags.append("symlink")
    if hasattr(os.path, "isjunction") and os.path.isjunction(path):
        flags.append("junction")
    if getattr(st, "st_file_attributes", 0) & getattr(stat_mod, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
        flags.append("reparse_point")
    if flags:
        kind += "[" + ",".join(flags) + "]"
    return kind


def walk_report(target_dir: str) -> None:
    """Enumerate the target with per-entry timing; surface reparse points."""
    log(f"WALK start: {target_dir}")
    t0 = time.time()
    n_dirs = n_files = n_special = 0
    specials = []
    slowest = []
    for root, dirs, files in os.walk(target_dir):
        n_dirs += 1
        for f in files:
            n_files += 1
            abs_p = os.path.join(root, f)
            rel = os.path.relpath(abs_p, target_dir)
            k = classify(abs_p)
            if "[" in k:
                n_special += 1
                specials.append((rel, k))
            t1 = time.time()
            try:
                os.lstat(abs_p)
            except OSError:
                pass
            dt = time.time() - t1
            slowest.append((dt, rel))
    walk_elapsed = time.time() - t0
    log(f"WALK done: dirs={n_dirs} files={n_files} special={n_special} "
        f"elapsed={walk_elapsed:.3f}s")
    for rel, k in specials[:50]:
        log(f"  SPECIAL: {rel} -> {k}")
    slowest.sort(reverse=True)
    for dt, rel in slowest[:10]:
        log(f"  SLOWEST_LSTAT: {dt*1000:.2f}ms {rel}")
    # directory-level reparse points (junctions that os.walk may descend into)
    log("DIR_REPARSE scan start")
    t0 = time.time()
    dir_specials = []
    for root, dirs, files in os.walk(target_dir):
        for d in dirs:
            p = os.path.join(root, d)
            k = classify(p)
            if "[" in k:
                dir_specials.append((os.path.relpath(p, target_dir), k))
    log(f"DIR_REPARSE done: {len(dir_specials)} in {time.time()-t0:.3f}s")
    for rel, k in dir_specials[:50]:
        log(f"  DIR_SPECIAL: {rel} -> {k}")


def timed_hash_sweep(target_dir: str) -> None:
    """Hash every file with per-file watchdog logging (the core hang probe)."""
    log(f"HASH_SWEEP start: {target_dir}")
    t_start = time.time()
    files = []
    for root, dirs, files_ in os.walk(target_dir):
        for f in files_:
            files.append(os.path.relpath(os.path.join(root, f), target_dir))
    log(f"HASH_SWEEP collected {len(files)} paths in {time.time()-t_start:.3f}s")
    files.sort()
    total = 0
    slow = []
    for i, rel in enumerate(files):
        abs_p = os.path.join(target_dir, rel)
        t0 = time.time()
        try:
            sz = os.path.getsize(abs_p)
            t_stat = time.time() - t0
            t1 = time.time()
            h = compute_sha256(abs_p)
            t_hash = time.time() - t1
        except OSError as exc:
            log(f"HASH_SWEEP ERROR at [{i}] {rel}: {exc}")
            continue
        total += sz
        dt = t_stat + t_hash
        slow.append((dt, t_stat, t_hash, rel))
        if i % 200 == 0:
            log(f"  progress {i}/{len(files)} elapsed={time.time()-t_start:.2f}s "
                f"bytes={total}")
    slow.sort(reverse=True)
    log(f"HASH_SWEEP done: {len(files)} files, {total} bytes, "
        f"elapsed={time.time()-t_start:.3f}s")
    for dt, ts, th, rel in slow[:10]:
        log(f"  SLOWEST_FILE: total={dt*1000:.2f}ms stat={ts*1000:.2f}ms "
            f"hash={th*1000:.2f}ms {rel}")


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "both"
    target = sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO_ROOT, "converted_output")
    label = sys.argv[3] if len(sys.argv) > 3 else os.path.basename(os.path.normpath(target))
    target = target if os.path.isabs(target) else os.path.join(REPO_ROOT, target)

    out_dir = os.path.join(REPO_ROOT, "build", "audit")
    os.makedirs(out_dir, exist_ok=True)
    manifest_path = os.path.join(out_dir, f"repro_manifest_{label}.sha256.json")

    log(f"=== repro_manifest_hang mode={mode} target={target} label={label} ===")
    log(f"python={sys.version.split()[0]} platform={sys.platform}")

    if mode in ("walk", "both"):
        walk_report(target)
    if mode in ("hash", "both"):
        timed_hash_sweep(target)

    if mode in ("gen", "both"):
        t0 = time.time()
        log("GEN start")
        try:
            m = generate_manifest(target, manifest_path)
            log(f"GEN done: {m['total_files']} files {m['total_size_mb']} MB "
                f"in {time.time()-t0:.3f}s")
        except Exception:
            log("GEN FAILED:\n" + traceback.format_exc())
            return 1

    if mode in ("verify", "both"):
        t0 = time.time()
        log("VERIFY start")
        try:
            ok, details = verify_manifest(target, manifest_path)
            log(f"VERIFY done: match={ok} files={details.get('target_total_files')} "
                f"missing={details.get('missing_count')} "
                f"modified={details.get('modified_count')} "
                f"extra={details.get('extra_count')} in {time.time()-t0:.3f}s")
        except Exception:
            log("VERIFY FAILED:\n" + traceback.format_exc())
            return 1

    log("=== repro done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())

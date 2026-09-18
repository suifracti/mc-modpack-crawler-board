"""
Phase 3G-F-B: attribute the cutover Step-4 stall to a concrete syscall.

The reported hang showed 0% CPU and a tiny working set in the Python process,
which means the time was NOT spent executing Python bytecode. This probe
separates wall-clock time from Python process-CPU time for each Step-4
primitive (copytree / rmtree / move / hash) and samples the CPU consumed by
external services (Defender MsMpEng.exe) at the same time.

If wall >> process_cpu, the cost is billed to a *different* process, which is
exactly why the Python process looked idle. That establishes WHAT class of
component is responsible (an out-of-process filter/scanner), not WHICH one.

Attribution honesty (Phase 3G-F.1): Defender (MsMpEng.exe) is only one of the
processes sampled below. A rising MsMpEng CPU counter is consistent with
Defender being involved, but it does NOT uniquely prove Defender is the cause -
other filter drivers, the search indexer, and the volume's own IO stack are
sampled too and are not ruled out. Do not report Defender as the proven root
cause; report "blocking occurred in the OS/filesystem copy path".
"""
import os
import sys
import shutil
import time
import subprocess

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONVERTED = os.path.join(REPO_ROOT, "converted_output")
PROBE_DIR = os.path.join(REPO_ROOT, "build", "_step4_probe")


def cpu_snapshot():
    """Return {image: cumulative_cpu_seconds} for interesting processes."""
    out = {}
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-Process | Where-Object { $_.ProcessName -match "
             "'MsMpEng|MsSense|python|msedge|node|SearchIndexer' } | "
             "ForEach-Object { \"$($_.ProcessName) $($_.Id) $($_.CPU)\" }"],
            capture_output=True, text=True, timeout=60)
        for line in res.stdout.splitlines():
            parts = line.split()
            if len(parts) == 3:
                name, pid, cpu = parts
                try:
                    out[f"{name}:{pid}"] = float(cpu)
                except ValueError:
                    pass
    except Exception as exc:
        out[f"<error:{exc.__class__.__name__}>"] = 0.0
    return out


def timed(label, fn):
    c0 = cpu_snapshot()
    p0 = time.process_time()
    w0 = time.time()
    err = None
    try:
        fn()
    except Exception as exc:
        err = f"{exc.__class__.__name__}: {exc}"
    wall = time.time() - w0
    pcpu = time.process_time() - p0
    c1 = cpu_snapshot()
    external = []
    for k, v in c1.items():
        if k in c0 and not k.startswith("<"):
            delta = v - c0[k]
            if delta > 0.5:
                external.append(f"{k}=+{delta:.1f}s")
    print(f"  {label}")
    print(f"    wall={wall:.2f}s  process_cpu={pcpu:.2f}s  "
          f"ratio={wall / pcpu if pcpu > 0.01 else float('inf'):.1f}x")
    if external:
        print(f"    external_cpu: {', '.join(external)}")
    if err:
        print(f"    ERROR: {err}")
    return wall, pcpu


def count_tree(p):
    n = 0
    b = 0
    for root, dirs, files in os.walk(p):
        for f in files:
            n += 1
            try:
                b += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return n, b


def main():
    if os.path.exists(PROBE_DIR):
        shutil.rmtree(PROBE_DIR, ignore_errors=True)
    n, b = count_tree(CONVERTED)
    print(f"=== Step-4 IO attribution probe ===")
    print(f"source tree: {n} files / {b / (1024*1024):.1f} MB")
    print(f"python: {sys.version.split()[0]}  cwd={REPO_ROOT}")

    results = {}
    results["copytree"] = timed("copytree (2924 files)", lambda: shutil.copytree(CONVERTED, PROBE_DIR))
    results["rmtree"] = timed("rmtree (2924 files)", lambda: shutil.rmtree(PROBE_DIR, ignore_errors=True))

    # move semantics: rename within the same volume
    if os.path.exists(PROBE_DIR):
        shutil.rmtree(PROBE_DIR, ignore_errors=True)
    shutil.copytree(CONVERTED, PROBE_DIR)
    swap_target = PROBE_DIR + "_swap"
    if os.path.exists(swap_target):
        shutil.rmtree(swap_target, ignore_errors=True)
    results["move"] = timed("move dir (rename)", lambda: shutil.move(PROBE_DIR, swap_target))
    results["rmtree_after_move"] = timed("rmtree after move", lambda: shutil.rmtree(swap_target, ignore_errors=True))

    print("\n=== summary ===")
    total = sum(v[0] for v in results.values())
    for k, (wall, pcpu) in results.items():
        print(f"  {k:20s} wall={wall:8.2f}s cpu={pcpu:7.2f}s")
    print(f"  {'TOTAL':20s} wall={total:8.2f}s")
    print(f"  observed cutover Step4 gap was ~2318s (38m38s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

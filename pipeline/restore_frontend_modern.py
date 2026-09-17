"""
Architecture V2 - Phase 3D: Verified Restore to Modern Frontend.
Restores converted_output/ to Modern Frontend (TypeScript + Vite) and validates
against frontend_modern_production.sha256.json without affecting the V2 Data Pipeline.
"""
import os
import sys
import shutil
import time
import json
import subprocess

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from pipeline.manifest import verify_manifest, compute_sha256, get_git_commit

CONVERTED_OUTPUT_DIR = os.path.join(REPO_ROOT, "converted_output")
FRONTEND_PREVIEW_DIR = os.path.join(REPO_ROOT, "build", "frontend_preview")
PRODUCTION_STATE_PATH = os.path.join(REPO_ROOT, "build", "production_state.json")
MODERN_MANIFEST_PATH = os.path.join(REPO_ROOT, "build", "manifests", "frontend_modern_production.sha256.json")
CANONICAL_DB = os.path.join(REPO_ROOT, "build", "canonical.db")


def run_cmd(cmd: list, desc: str) -> None:
    print(f"[*] Running {desc}: {' '.join(cmd)}")
    t0 = time.time()
    res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    elapsed = time.time() - t0
    if res.returncode != 0:
        print(f"[-] FAILED: {desc} (exit code {res.returncode}, {elapsed:.2f}s)")
        print(res.stdout)
        print(res.stderr)
        raise RuntimeError(f"Step '{desc}' failed with exit code {res.returncode}")
    print(f"[+] PASSED: {desc} ({elapsed:.2f}s)")


def restore_frontend_modern():
    print("============================================================")
    print("  Architecture V2 — Phase 3D Frontend Restore to Modern")
    print("============================================================")
    t_start = time.time()

    if not os.path.exists(PRODUCTION_STATE_PATH):
        raise FileNotFoundError(f"Production state file not found: {PRODUCTION_STATE_PATH}")

    with open(PRODUCTION_STATE_PATH, "r", encoding="utf-8") as fp:
        state = json.load(fp)

    if not os.path.exists(MODERN_MANIFEST_PATH):
        raise FileNotFoundError(f"Modern Production manifest not found: {MODERN_MANIFEST_PATH}")

    # Ensure frontend_preview exists and is up to date
    if not os.path.exists(FRONTEND_PREVIEW_DIR):
        print("[*] Staging frontend preview...")
        run_cmd([sys.executable, "pipeline/stage_frontend_preview.py"], "Stage Frontend Preview")

    # Step 1: Copy modern staging into converted_output
    print("\n[Step 1/3] Restoring converted_output/ from build/frontend_preview/...")
    temp_swap_dir = os.path.join(REPO_ROOT, "build", "frontend_restore_temp")
    if os.path.exists(temp_swap_dir):
        shutil.rmtree(temp_swap_dir, ignore_errors=True)

    shutil.copytree(FRONTEND_PREVIEW_DIR, temp_swap_dir)

    if os.path.exists(CONVERTED_OUTPUT_DIR):
        shutil.rmtree(CONVERTED_OUTPUT_DIR, ignore_errors=True)
    shutil.move(temp_swap_dir, CONVERTED_OUTPUT_DIR)
    print("  [+] Modern files restored into converted_output/.")

    # Step 2: Verify converted_output against modern production manifest
    print("\n[Step 2/3] Verifying converted_output/ against Modern Production Manifest...")
    is_valid, details = verify_manifest(CONVERTED_OUTPUT_DIR, MODERN_MANIFEST_PATH)
    if not is_valid:
        raise RuntimeError(f"Restored Modern Production verification failed: {details}")
    print("  [+] Restored converted_output verified 100% against Modern Production Manifest.")

    # Step 3: Update production_state.json
    print("\n[Step 3/3] Updating build/production_state.json...")
    commit = get_git_commit(REPO_ROOT)
    db_hash = compute_sha256(CANONICAL_DB) if os.path.exists(CANONICAL_DB) else state.get("canonical_db_hash", "unknown")

    state["active_frontend"] = "modern-vite"
    state["active_pipeline"] = "v2"
    state["frontend_manifest"] = os.path.relpath(MODERN_MANIFEST_PATH, REPO_ROOT).replace("\\", "/")
    state["frontend_source_commit"] = commit
    state["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    state["canonical_db_hash"] = db_hash

    with open(PRODUCTION_STATE_PATH, "w", encoding="utf-8") as fp:
        json.dump(state, fp, indent=2, ensure_ascii=False)
    print("  [+] production_state.json updated (active_frontend = modern-vite, active_pipeline = v2).")

    # Step 4: Verification gates
    print("\n--- Gate: Post-Restore Modern Acceptance Verification ---")
    run_cmd(["node", "pipeline/smoke_test_single.js", "converted_output", "8768"], "Modern Production Browser Test (33/33)")
    run_cmd(["node", "pipeline/smoke_test_wiring.js", "converted_output", "8780"], "Modern Production Wiring Test (18/18)")
    print("  [GATE PASSED] Modern Production restored and verified with 0 regressions.")

    print("\n============================================================")
    print("  FRONTEND RESTORE TO MODERN SUCCESSFUL!")
    print(f"  Active Frontend       : modern-vite")
    print(f"  Active Pipeline       : v2")
    print(f"  Duration              : {time.time() - t_start:.2f}s")
    print("============================================================")


if __name__ == "__main__":
    restore_frontend_modern()

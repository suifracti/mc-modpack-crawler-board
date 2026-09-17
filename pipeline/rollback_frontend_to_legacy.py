"""
Architecture V2 - Phase 3D: Verified Rollback to Legacy Frontend.
Restores converted_output/ from the verified Legacy Frontend backup and validates
against frontend_legacy_production.sha256.json without affecting the V2 Data Pipeline.
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

from pipeline.manifest import verify_manifest, compute_sha256

CONVERTED_OUTPUT_DIR = os.path.join(REPO_ROOT, "converted_output")
PRODUCTION_STATE_PATH = os.path.join(REPO_ROOT, "build", "production_state.json")
MANIFESTS_DIR = os.path.join(REPO_ROOT, "build", "manifests")
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


def rollback_frontend_to_legacy():
    print("============================================================")
    print("  Architecture V2 — Phase 3D Frontend Rollback to Legacy")
    print("============================================================")
    t_start = time.time()

    if not os.path.exists(PRODUCTION_STATE_PATH):
        raise FileNotFoundError(f"Production state file not found: {PRODUCTION_STATE_PATH}")

    with open(PRODUCTION_STATE_PATH, "r", encoding="utf-8") as fp:
        state = json.load(fp)

    legacy_backup_rel = state.get("legacy_frontend_backup")
    legacy_manifest_rel = state.get("legacy_frontend_manifest")

    if not legacy_backup_rel:
        raise ValueError("production_state.json is missing 'legacy_frontend_backup' path")
    if not legacy_manifest_rel:
        legacy_manifest_rel = "build/manifests/frontend_legacy_production.sha256.json"

    legacy_backup_dir = os.path.join(REPO_ROOT, legacy_backup_rel)
    legacy_manifest_path = os.path.join(REPO_ROOT, legacy_manifest_rel)

    print(f"  Legacy Backup Source  : {legacy_backup_dir}")
    print(f"  Legacy Manifest Path  : {legacy_manifest_path}")

    if not os.path.exists(legacy_backup_dir):
        raise FileNotFoundError(f"Legacy backup directory not found: {legacy_backup_dir}")
    if not os.path.exists(legacy_manifest_path):
        raise FileNotFoundError(f"Legacy manifest not found: {legacy_manifest_path}")

    # Step 1: Verify backup integrity
    print("\n[Step 1/4] Verifying Legacy Backup integrity against manifest...")
    # Ignore backup's own metadata.json if present
    is_valid, details = verify_manifest(legacy_backup_dir, legacy_manifest_path, ignore_extra=["metadata.json"])
    if not is_valid:
        raise RuntimeError(f"Legacy backup verification failed against manifest: {details}")
    print("  [+] Legacy backup integrity verified 100%.")

    # Step 2: Replace converted_output with legacy backup
    print("\n[Step 2/4] Restoring converted_output/ from Legacy Backup...")
    temp_swap_dir = os.path.join(REPO_ROOT, "build", "frontend_rollback_temp")
    if os.path.exists(temp_swap_dir):
        shutil.rmtree(temp_swap_dir, ignore_errors=True)

    # Copy backup to temp first
    shutil.copytree(legacy_backup_dir, temp_swap_dir)
    # Remove metadata.json from restored output if copied
    temp_meta = os.path.join(temp_swap_dir, "metadata.json")
    if os.path.exists(temp_meta):
        os.remove(temp_meta)

    # Swap into converted_output
    if os.path.exists(CONVERTED_OUTPUT_DIR):
        shutil.rmtree(CONVERTED_OUTPUT_DIR, ignore_errors=True)
    shutil.move(temp_swap_dir, CONVERTED_OUTPUT_DIR)
    print("  [+] Legacy files restored into converted_output/.")

    # Step 3: Verify restored converted_output
    print("\n[Step 3/4] Verifying restored converted_output/ against Legacy Manifest...")
    is_prod_valid, prod_details = verify_manifest(CONVERTED_OUTPUT_DIR, legacy_manifest_path)
    if not is_prod_valid:
        raise RuntimeError(f"Restored legacy production verification failed: {prod_details}")
    print("  [+] Restored converted_output verified 100% against legacy manifest.")

    # Step 4: Update production_state.json
    print("\n[Step 4/4] Updating build/production_state.json...")
    db_hash = compute_sha256(CANONICAL_DB) if os.path.exists(CANONICAL_DB) else state.get("canonical_db_hash", "unknown")
    state["active_frontend"] = "legacy"
    state["active_pipeline"] = "v2"  # Data Pipeline strictly preserved as V2!
    state["frontend_manifest"] = legacy_manifest_rel
    state["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    state["canonical_db_hash"] = db_hash

    with open(PRODUCTION_STATE_PATH, "w", encoding="utf-8") as fp:
        json.dump(state, fp, indent=2, ensure_ascii=False)
    print("  [+] production_state.json updated (active_frontend = legacy, active_pipeline = v2).")

    # Step 5: Post-rollback browser verification
    print("\n--- Gate: Post-Rollback Legacy Browser Verification ---")
    run_cmd(["node", "pipeline/smoke_test_single.js", "converted_output", "8768"], "Legacy Production Browser Test (33/33)")
    print("  [GATE PASSED] Legacy Production verified with 0 regressions.")

    print("\n============================================================")
    print("  FRONTEND ROLLBACK TO LEGACY SUCCESSFUL!")
    print(f"  Active Frontend       : legacy")
    print(f"  Active Pipeline       : v2")
    print(f"  Duration              : {time.time() - t_start:.2f}s")
    print("============================================================")


if __name__ == "__main__":
    rollback_frontend_to_legacy()

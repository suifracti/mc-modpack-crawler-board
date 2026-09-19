"""
Architecture V2 - Phase 2B: Verified Production Rollback to V1.
Rolls back active production `converted_output/` from V2 to V1.
Preserves the current V2 production into `build/backups/v2-production-<timestamp>/`.
Restores V1 from the latest `build/backups/v1-production-<timestamp>/`.
Verifies SHA-256 integrity 100% against `build/manifests/v1_production.sha256.json`.
Executes single browser smoke test and records production state.
"""
import os
import sys
import json
import time
import shutil
import subprocess

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from pipeline.manifest import compute_sha256, generate_manifest, verify_manifest, get_git_commit

CONVERTED_OUTPUT_DIR = os.path.join(REPO_ROOT, "converted_output")
BACKUPS_DIR = os.path.join(REPO_ROOT, "build", "backups")
MANIFESTS_DIR = os.path.join(REPO_ROOT, "build", "manifests")
V1_MANIFEST_PATH = os.path.join(MANIFESTS_DIR, "v1_production.sha256.json")
PRODUCTION_STATE_PATH = os.path.join(REPO_ROOT, "build", "production_state.json")


def find_latest_v1_backup() -> str:
    if not os.path.exists(BACKUPS_DIR):
        raise FileNotFoundError(f"Backups directory does not exist: {BACKUPS_DIR}")
    v1_backups = []
    for d in os.listdir(BACKUPS_DIR):
        if d.startswith("v1-production-"):
            full_p = os.path.join(BACKUPS_DIR, d)
            if os.path.isdir(full_p):
                v1_backups.append(full_p)
    if not v1_backups:
        raise FileNotFoundError("No V1 backup directory found under build/backups/")
    v1_backups.sort()
    return v1_backups[-1]


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


def rollback_to_v1():
    print("======================================================================")
    print("  Architecture V2 - Phase 2B: Rollback Production to V1")
    print("======================================================================\n")

    t_start = time.time()

    # 1. Locate V1 backup
    v1_backup = find_latest_v1_backup()
    print(f"[+] Selected latest V1 backup: {v1_backup}")

    # 2. Verify V1 backup integrity before making changes
    print("[*] Verifying V1 backup integrity against V1 manifest...")
    is_match, details = verify_manifest(v1_backup, V1_MANIFEST_PATH, ignore_extra=["metadata.json"])
    if not is_match:
        raise RuntimeError(f"V1 backup directory corrupted or mismatch: {details}")
    print("[+] V1 backup integrity verified 100%.")

    # 3. Archive current V2 production
    ts = time.strftime("%Y%m%d_%H%M%S")
    v2_backup = os.path.join(BACKUPS_DIR, f"v2-production-{ts}")
    if os.path.exists(CONVERTED_OUTPUT_DIR):
        print(f"[*] Archiving current V2 production to {v2_backup}...")
        shutil.move(CONVERTED_OUTPUT_DIR, v2_backup)
        # Write metadata
        metadata = {
            "backed_up_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "source_commit": get_git_commit(REPO_ROOT),
            "type": "v2_production_before_rollback"
        }
        with open(os.path.join(v2_backup, "metadata.json"), "w", encoding="utf-8") as fp:
            json.dump(metadata, fp, indent=2, ensure_ascii=False)
        print("[+] Current V2 production archived.")

    # 4. Restore V1 from backup
    print(f"[*] Restoring V1 from {v1_backup} -> {CONVERTED_OUTPUT_DIR}...")
    try:
        shutil.copytree(v1_backup, CONVERTED_OUTPUT_DIR, ignore=shutil.ignore_patterns("metadata.json"))
        print("[+] V1 production restored.")
    except Exception as e:
        print(f"[-] ERROR restoring V1: {e}")
        if os.path.exists(v2_backup):
            print("[*] Reverting back to V2 backup...")
            shutil.move(v2_backup, CONVERTED_OUTPUT_DIR)
        raise

    # 5. Post-rollback SHA-256 verification
    print("[*] Verifying restored converted_output/ against V1 manifest...")
    is_match, details = verify_manifest(CONVERTED_OUTPUT_DIR, V1_MANIFEST_PATH)
    if not is_match:
        raise RuntimeError(f"Restored V1 does not match V1 manifest: {details}")
    print(f"[+] Restored V1 SHA-256 matched 100% ({details['target_total_files']} files).")

    # 6. Run browser smoke test on restored V1
    print("[*] Running browser smoke test on restored V1 production (Port 8768)...")
    run_cmd(["node", "pipeline/smoke_test_single.js", "converted_output", "8768"], "Restored V1 Browser Smoke Test")
    print("[+] Browser smoke test on restored V1 passed with 0 exceptions.")

    # 7. Update production state
    commit = get_git_commit(REPO_ROOT)
    prod_state = {
        "active_pipeline": "v1",
        "rolled_back_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "commit": commit,
        "restored_from_backup": os.path.relpath(v1_backup, REPO_ROOT).replace("\\", "/"),
        "archived_v2_backup": os.path.relpath(v2_backup, REPO_ROOT).replace("\\", "/"),
        "manifest_path": os.path.relpath(V1_MANIFEST_PATH, REPO_ROOT).replace("\\", "/"),
        "total_records": 73522
    }
    with open(PRODUCTION_STATE_PATH, "w", encoding="utf-8") as fp:
        json.dump(prod_state, fp, indent=2, ensure_ascii=False)
    print(f"[+] Production state recorded as V1 active:\n{json.dumps(prod_state, indent=2)}")

    print("\n======================================================================")
    print(f"  V1 ROLLBACK COMPLETED SUCCESSFULLY in {time.time() - t_start:.2f}s")
    print("  Active Production Pipeline: V1 (Legacy Converter)")
    print("======================================================================\n")


if __name__ == "__main__":
    rollback_to_v1()

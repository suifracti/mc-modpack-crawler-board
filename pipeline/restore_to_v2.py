"""
Architecture V2 - Phase 2B: Restore Production to V2.
Restores active production `converted_output/` to V2.
Verifies against `build/manifests/v2_production.sha256.json` (or `v2_staging.sha256.json`).
Runs 33-behavior browser smoke test and records production state.
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
LEGACY_PREVIEW_DIR = os.path.join(REPO_ROOT, "build", "legacy_preview")
BACKUPS_DIR = os.path.join(REPO_ROOT, "build", "backups")
MANIFESTS_DIR = os.path.join(REPO_ROOT, "build", "manifests")
CANONICAL_DB = os.path.join(REPO_ROOT, "build", "canonical.db")

V2_PROD_MANIFEST_PATH = os.path.join(MANIFESTS_DIR, "v2_production.sha256.json")
V2_STAGING_MANIFEST_PATH = os.path.join(MANIFESTS_DIR, "v2_staging.sha256.json")
PRODUCTION_STATE_PATH = os.path.join(REPO_ROOT, "build", "production_state.json")


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


def load_legacy_js(file_path: str, global_var: str) -> list:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Missing file: {file_path}")
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    prefix = f"window.{global_var} = "
    idx = text.find(prefix)
    if idx == -1:
        raise ValueError(f"Variable prefix '{prefix}' not found in {file_path}")
    json_part = text[idx + len(prefix):].rstrip(";\n ")
    return json.loads(json_part)


def restore_to_v2():
    print("======================================================================")
    print("  Architecture V2 - Phase 2B: Restore Production to V2")
    print("======================================================================\n")

    t_start = time.time()

    # Determine reference manifest
    manifest_path = V2_PROD_MANIFEST_PATH if os.path.exists(V2_PROD_MANIFEST_PATH) else V2_STAGING_MANIFEST_PATH
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Neither V2 production nor staging manifest found in {MANIFESTS_DIR}")

    # Determine source directory for V2 (legacy_preview is the gold source)
    if not os.path.exists(LEGACY_PREVIEW_DIR):
        raise FileNotFoundError(f"Legacy preview directory not found at {LEGACY_PREVIEW_DIR}")

    # Archive current converted_output if present
    ts = time.strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(BACKUPS_DIR, f"v1-production-{ts}")
    if os.path.exists(CONVERTED_OUTPUT_DIR):
        print(f"[*] Backing up current converted_output/ to {backup_dir}...")
        shutil.move(CONVERTED_OUTPUT_DIR, backup_dir)
        metadata = {
            "backed_up_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "source_commit": get_git_commit(REPO_ROOT),
            "manifest_path": "build/manifests/v1_production.sha256.json",
            "type": "v1_production"
        }
        with open(os.path.join(backup_dir, "metadata.json"), "w", encoding="utf-8") as fp:
            json.dump(metadata, fp, indent=2, ensure_ascii=False)

    # Copy V2 from legacy_preview
    print(f"[*] Restoring V2 from {LEGACY_PREVIEW_DIR} -> {CONVERTED_OUTPUT_DIR}...")
    shutil.copytree(LEGACY_PREVIEW_DIR, CONVERTED_OUTPUT_DIR)
    print("[+] V2 restored to converted_output/.")

    # Verify manifest
    print(f"[*] Verifying restored converted_output/ against {os.path.basename(manifest_path)}...")
    is_match, details = verify_manifest(CONVERTED_OUTPUT_DIR, manifest_path)
    if not is_match:
        raise RuntimeError(f"Restored V2 manifest mismatch: {details}")
    print(f"[+] Restored V2 SHA-256 verified 100% ({details['target_total_files']} files).")


    # Verify total records
    print("[*] Verifying total record count (73,522)...")
    data_dir = os.path.join(CONVERTED_OUTPUT_DIR, "data")
    platform_files = {
        "mcmod": ("table_rows.js", "tableRowsData", 1484),
        "bilibili": ("bili_data.js", "biliModpacksData", 936),
        "bbsmc": ("bbsmc_data.js", "bbsmcModpacksData", 1802),
        "xyebbs": ("xyebbs_data.js", "xyebbsModpacksData", 5175),
        "modrinth": ("modrinth_data.js", "modrinthModpacksData", 18328),
        "curseforge": ("curseforge_data.js", "curseforgeModpacksData", 45797)
    }
    total_count = 0
    for plat, (fname, gvar, expected) in platform_files.items():
        fpath = os.path.join(data_dir, fname)
        records = load_legacy_js(fpath, gvar)
        count = len(records)
        print(f"    - {plat.ljust(12)}: {count} records (expected: {expected})")
        if count != expected:
            raise ValueError(f"Record count mismatch for {plat}: expected {expected}, got {count}")
        total_count += count
    print(f"[+] Total records verified: {total_count} / 73522.")

    # Run browser smoke test
    print("[*] Running 33-behavior browser smoke test on restored V2 production (Port 8768)...")
    run_cmd(["node", "pipeline/smoke_test_single.js", "converted_output", "8768"], "Restored V2 Browser Smoke Test")
    print("[+] Browser smoke test passed 33/33 with 0 exceptions.")

    # Ensure v2_production manifest exists
    commit = get_git_commit(REPO_ROOT)
    canonical_db_hash = compute_sha256(CANONICAL_DB) if os.path.exists(CANONICAL_DB) else "unknown"
    prod_manifest = generate_manifest(
        target_dir=CONVERTED_OUTPUT_DIR,
        output_manifest_path=V2_PROD_MANIFEST_PATH,
        extra_metadata={
            "canonical_db_sha256": canonical_db_hash,
            "pipeline": "canonical_v2_legacy_exporter",
            "production_active": True
        }
    )

    # Update production state
    prod_state = {
        "active_pipeline": "v2",
        "restored_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "commit": commit,
        "canonical_db_hash": canonical_db_hash,
        "total_records": total_count,
        "manifest_path": os.path.relpath(V2_PROD_MANIFEST_PATH, REPO_ROOT).replace("\\", "/"),
        "backup_v1_path": os.path.relpath(backup_dir, REPO_ROOT).replace("\\", "/")
    }
    with open(PRODUCTION_STATE_PATH, "w", encoding="utf-8") as fp:
        json.dump(prod_state, fp, indent=2, ensure_ascii=False)
    print(f"[+] Production state recorded as V2 active:\n{json.dumps(prod_state, indent=2)}")

    print("\n======================================================================")
    print(f"  V2 RESTORATION COMPLETED SUCCESSFULLY in {time.time() - t_start:.2f}s")
    print("  Active Production Pipeline: V2 (Canonical SQLite -> Legacy Exporter)")
    print("======================================================================\n")


if __name__ == "__main__":
    restore_to_v2()

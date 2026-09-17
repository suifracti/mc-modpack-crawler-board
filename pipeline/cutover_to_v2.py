"""
Architecture V2 - Phase 2B: Automated Production Cutover to V2.
Transitions production `converted_output/` from V1 pipeline to Canonical SQLite -> V2 Legacy Exporter.
Enforces strict preflight gates (Disk Space, V1 Integrity, V2 Staging Integrity, V2 Data, V2 Browser 33/33).
Executes a short transactional cutover with verified rollback.
Performs postflight verification and generates production state and manifest.
"""
import os
import sys
import json
import time
import shutil
import subprocess
from typing import Dict, Any

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
STAGING_DIR = os.path.join(REPO_ROOT, "converted_output.v2_staging")
BACKUPS_DIR = os.path.join(REPO_ROOT, "build", "backups")
MANIFESTS_DIR = os.path.join(REPO_ROOT, "build", "manifests")
CANONICAL_DB = os.path.join(REPO_ROOT, "build", "canonical.db")

V1_MANIFEST_PATH = os.path.join(MANIFESTS_DIR, "v1_production.sha256.json")
V2_STAGING_MANIFEST_PATH = os.path.join(MANIFESTS_DIR, "v2_staging.sha256.json")
V2_PRODUCTION_MANIFEST_PATH = os.path.join(MANIFESTS_DIR, "v2_production.sha256.json")
PRODUCTION_STATE_PATH = os.path.join(REPO_ROOT, "build", "production_state.json")


def get_dir_size(path: str) -> int:
    if not os.path.exists(path):
        return 0
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            total += os.path.getsize(os.path.join(root, f))
    return total


def count_files(path: str) -> int:
    if not os.path.exists(path):
        return 0
    count = 0
    for _, _, files in os.walk(path):
        count += len(files)
    return count


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


def preflight_disk_space() -> None:
    print("\n--- Gate 1: Disk Space Preflight ---")
    total, used, free = shutil.disk_usage(REPO_ROOT)
    v1_size = get_dir_size(CONVERTED_OUTPUT_DIR)
    v2_size = get_dir_size(LEGACY_PREVIEW_DIR)
    # Required: v1 backup size + v2 size + max(1GB, 20% of data)
    margin = max(1024 * 1024 * 1024, int(0.20 * (v1_size + v2_size)))
    required_space = v1_size + v2_size + margin

    print(f"  V1 Production Size : {v1_size / (1024*1024):.2f} MB")
    print(f"  V2 Staging Size    : {v2_size / (1024*1024):.2f} MB")
    print(f"  Safety Margin      : {margin / (1024*1024):.2f} MB")
    print(f"  Required Free Space: {required_space / (1024*1024):.2f} MB ({required_space / (1024*1024*1024):.2f} GB)")
    print(f"  Actual Free Space  : {free / (1024*1024):.2f} MB ({free / (1024*1024*1024):.2f} GB)")

    if free < required_space:
        raise RuntimeError(
            f"Disk space preflight failed! Available {free / (1024*1024):.2f} MB < Required {required_space / (1024*1024):.2f} MB"
        )
    print("  [GATE PASSED] Sufficient disk space verified.")


def preflight_v1_production() -> None:
    print("\n--- Gate 2: V1 Production Integrity Preflight ---")
    if not os.path.exists(V1_MANIFEST_PATH):
        raise FileNotFoundError(f"V1 manifest not found at {V1_MANIFEST_PATH}")
    is_match, details = verify_manifest(CONVERTED_OUTPUT_DIR, V1_MANIFEST_PATH)
    if not is_match:
        raise RuntimeError(
            f"V1 Production integrity check failed! Missing: {details['missing_count']}, "
            f"Modified: {details['modified_count']}, Extra: {details['extra_count']}"
        )
    print(f"  [GATE PASSED] V1 production matches manifest 100% ({details['target_total_files']} files).")


def preflight_v2_staging() -> str:
    print("\n--- Gate 3: V2 Staging Integrity Preflight ---")
    if not os.path.exists(LEGACY_PREVIEW_DIR):
        raise FileNotFoundError(f"V2 preview directory not found at {LEGACY_PREVIEW_DIR}")
    if not os.path.exists(CANONICAL_DB):
        raise FileNotFoundError(f"Canonical DB not found at {CANONICAL_DB}")

    canonical_db_hash = compute_sha256(CANONICAL_DB)
    commit = get_git_commit(REPO_ROOT)
    print(f"  Canonical DB SHA-256 : {canonical_db_hash}")
    print(f"  Source Git Commit    : {commit}")

    manifest = generate_manifest(
        target_dir=LEGACY_PREVIEW_DIR,
        output_manifest_path=V2_STAGING_MANIFEST_PATH,
        extra_metadata={
            "canonical_db_sha256": canonical_db_hash,
            "pipeline": "canonical_v2_legacy_exporter",
            "source_preview_dir": "build/legacy_preview"
        }
    )
    is_match, details = verify_manifest(LEGACY_PREVIEW_DIR, V2_STAGING_MANIFEST_PATH)
    if not is_match:
        raise RuntimeError(f"V2 Staging manifest verification failed: {details}")
    print(f"  [GATE PASSED] V2 staging manifest created & verified ({manifest['total_files']} files, {manifest['total_size_mb']} MB).")
    return canonical_db_hash


def preflight_v2_data() -> None:
    print("\n--- Gate 4: V2 Data Validation Preflight ---")
    run_cmd([sys.executable, "pipeline/validate_canonical_db.py"], "Validate Canonical SQLite DB")
    run_cmd([sys.executable, "pipeline/verify_legacy_export.py"], "Verify Legacy Preview Export Parity")
    print("  [GATE PASSED] Canonical DB and Export Parity verified 100%.")


def preflight_v2_browser() -> None:
    print("\n--- Gate 5: V2 Browser Smoke Test Preflight ---")
    run_cmd(["node", "pipeline/smoke_test_single.js", "build/legacy_preview", "8767"], "33-Behavior Browser Test (Preview)")
    print("  [GATE PASSED] V2 Preview Browser Smoke Test passed 33/33 with 0 exceptions.")


def execute_transactional_cutover() -> str:
    print("\n============================================================")
    print("  Executing Short Transactional Cutover with Verified Rollback")
    print("============================================================\n")

    # Step A: Clean up any old staging directory
    if os.path.exists(STAGING_DIR):
        print(f"[*] Removing preexisting staging directory: {STAGING_DIR}")
        shutil.rmtree(STAGING_DIR)

    # Step B: Copy legacy_preview -> converted_output.v2_staging
    print(f"[*] Staging V2 files to temporary transition directory: {STAGING_DIR}...")
    t0 = time.time()
    shutil.copytree(LEGACY_PREVIEW_DIR, STAGING_DIR)
    print(f"[+] Staging copied in {time.time() - t0:.2f}s.")

    # Step C: Verify staging directory against manifest
    print("[*] Verifying staging directory integrity against V2 staging manifest...")
    is_match, details = verify_manifest(STAGING_DIR, V2_STAGING_MANIFEST_PATH)
    if not is_match:
        shutil.rmtree(STAGING_DIR, ignore_errors=True)
        raise RuntimeError(f"Staging directory integrity check failed: {details}")
    print("[+] Staging directory verified 100% against manifest.")

    # Step D: Move current converted_output to timestamped backup
    ts = time.strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(BACKUPS_DIR, f"v1-production-{ts}")
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    v1_files = count_files(CONVERTED_OUTPUT_DIR)
    v1_bytes = get_dir_size(CONVERTED_OUTPUT_DIR)

    print(f"[*] Moving active production V1 to backup: {backup_dir}...")
    try:
        shutil.move(CONVERTED_OUTPUT_DIR, backup_dir)
    except Exception as e:
        shutil.rmtree(STAGING_DIR, ignore_errors=True)
        raise RuntimeError(f"Failed to backup V1 production to {backup_dir}: {e}. Production remains untouched.")

    # Write backup metadata
    metadata = {
        "backed_up_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "source_commit": get_git_commit(REPO_ROOT),
        "manifest_path": "build/manifests/v1_production.sha256.json",
        "total_files": v1_files,
        "total_size_bytes": v1_bytes,
        "total_size_mb": round(v1_bytes / (1024 * 1024), 2),
        "type": "v1_production"
    }
    with open(os.path.join(backup_dir, "metadata.json"), "w", encoding="utf-8") as fp:
        json.dump(metadata, fp, indent=2, ensure_ascii=False)
    print(f"[+] V1 production successfully moved to backup ({v1_files} files).")

    # Step E: Move staging to active production converted_output
    print(f"[*] Moving staging directory {STAGING_DIR} -> {CONVERTED_OUTPUT_DIR}...")
    try:
        shutil.move(STAGING_DIR, CONVERTED_OUTPUT_DIR)
        print("[+] V2 staging directory successfully activated as converted_output/.")
    except Exception as e:
        print(f"[-] CRITICAL ERROR during cutover move: {e}")
        print(f"[*] Triggering automatic self-healing: restoring {backup_dir} -> {CONVERTED_OUTPUT_DIR}...")
        try:
            shutil.move(backup_dir, CONVERTED_OUTPUT_DIR)
            print("[+] Self-healing complete: V1 production fully restored.")
        except Exception as restore_err:
            print(f"[-] CATASTROPHIC ERROR: Self-healing restore failed: {restore_err}")
            print(f"[-] Manual intervention required: move {backup_dir} back to {CONVERTED_OUTPUT_DIR}")
        raise RuntimeError(f"Cutover failed during staging rename: {e}")

    return backup_dir


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


def postflight_verification(backup_dir: str, canonical_db_hash: str) -> None:
    print("\n============================================================")
    print("  Postflight Verification of Activated V2 Production")
    print("============================================================\n")

    # 1. SHA-256 Manifest check
    print("[*] 1. Checking SHA-256 parity with V2 staging manifest...")
    is_match, details = verify_manifest(CONVERTED_OUTPUT_DIR, V2_STAGING_MANIFEST_PATH)
    if not is_match:
        raise RuntimeError(f"Postflight manifest check failed on activated converted_output/: {details}")
    print(f"[+] SHA-256 100% matched ({details['target_total_files']} files).")

    # 2. Check total records across platforms = 73522
    print("[*] 2. Checking total record count across active production data files...")
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

    if total_count != 73522:
        raise ValueError(f"Total active records mismatch: expected 73522, got {total_count}")
    print(f"[+] Total records verified: {total_count} / 73522.")

    # 3. Check auxiliary sidecars
    print("[*] 3. Checking auxiliary lazy sidecars...")
    mods_sample = os.path.join(data_dir, "mods", "1.js")
    comments_sample = os.path.join(data_dir, "comments", "1.js")
    if not os.path.exists(mods_sample):
        raise FileNotFoundError(f"Mod sidecar missing: {mods_sample}")
    if not os.path.exists(comments_sample):
        raise FileNotFoundError(f"Comment sidecar missing: {comments_sample}")
    print(f"[+] Auxiliary sidecars present and readable.")

    # 4. Production browser smoke test
    print("[*] 4. Running 33-behavior browser smoke test on active converted_output/ (Port 8768)...")
    run_cmd(["node", "pipeline/smoke_test_single.js", "converted_output", "8768"], "Production Browser Smoke Test")
    print("[+] Browser smoke test passed 33/33 with 0 exceptions.")

    # 5. Generate production manifest
    print("[*] 5. Generating V2 production SHA-256 manifest...")
    commit = get_git_commit(REPO_ROOT)
    prod_manifest = generate_manifest(
        target_dir=CONVERTED_OUTPUT_DIR,
        output_manifest_path=V2_PRODUCTION_MANIFEST_PATH,
        extra_metadata={
            "canonical_db_sha256": canonical_db_hash,
            "pipeline": "canonical_v2_legacy_exporter",
            "production_active": True,
            "source_backup_v1": os.path.relpath(backup_dir, REPO_ROOT).replace("\\", "/")
        }
    )
    print(f"[+] V2 Production manifest written to {V2_PRODUCTION_MANIFEST_PATH} ({prod_manifest['total_files']} files).")

    # 6. Write production state
    print("[*] 6. Updating production state file: build/production_state.json...")
    prod_state = {
        "active_pipeline": "v2",
        "cutover_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "pipeline_code_commit": commit,
        "cutover_base_commit": "a8cc46ea839ea64d64468d3aba22766015729686",
        "canonical_db_hash": canonical_db_hash,
        "total_records": total_count,
        "manifest_path": os.path.relpath(V2_PRODUCTION_MANIFEST_PATH, REPO_ROOT).replace("\\", "/"),
        "backup_v1_path": os.path.relpath(backup_dir, REPO_ROOT).replace("\\", "/")
    }
    with open(PRODUCTION_STATE_PATH, "w", encoding="utf-8") as fp:
        json.dump(prod_state, fp, indent=2, ensure_ascii=False)
    print(f"[+] Production state recorded:\n{json.dumps(prod_state, indent=2)}")


def main():
    print("======================================================================")
    print("  Architecture V2 - Phase 2B: Automated Production Cutover")
    print("======================================================================\n")

    t_start = time.time()
    # 1. Preflight Gates
    preflight_disk_space()
    preflight_v1_production()
    canonical_db_hash = preflight_v2_staging()
    preflight_v2_data()
    preflight_v2_browser()

    # 2. Transactional Cutover
    backup_dir = execute_transactional_cutover()

    # 3. Postflight Verification
    postflight_verification(backup_dir, canonical_db_hash)

    print("\n======================================================================")
    print(f"  PHASE 2B CUTOVER COMPLETED SUCCESSFULLY in {time.time() - t_start:.2f}s")
    print("  Active Production Pipeline: V2 (Canonical SQLite -> Legacy Exporter)")
    print("======================================================================\n")


if __name__ == "__main__":
    main()

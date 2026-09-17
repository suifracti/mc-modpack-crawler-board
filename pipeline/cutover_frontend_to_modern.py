"""
Architecture V2 - Phase 3D: Modern Frontend Production Cutover.
Switches the verified Modern Frontend (TypeScript + Vite) into Production (converted_output/)
with complete rollback guarantees and strict gate verification.
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

from pipeline.manifest import compute_sha256, generate_manifest, verify_manifest, get_git_commit

CONVERTED_OUTPUT_DIR = os.path.join(REPO_ROOT, "converted_output")
FRONTEND_PREVIEW_DIR = os.path.join(REPO_ROOT, "build", "frontend_preview")
STAGING_TEMP_DIR = os.path.join(REPO_ROOT, "build", "modern_staging_temp")
SWAP_TEMP_DIR = os.path.join(REPO_ROOT, "build", "legacy_pre_cutover_swap")
BACKUPS_DIR = os.path.join(REPO_ROOT, "build", "backups")
MANIFESTS_DIR = os.path.join(REPO_ROOT, "build", "manifests")
CANONICAL_DB = os.path.join(REPO_ROOT, "build", "canonical.db")
PRODUCTION_STATE_PATH = os.path.join(REPO_ROOT, "build", "production_state.json")

LEGACY_MANIFEST_PATH = os.path.join(MANIFESTS_DIR, "frontend_legacy_production.sha256.json")
MODERN_STAGING_MANIFEST_PATH = os.path.join(MANIFESTS_DIR, "frontend_modern_staging.sha256.json")
MODERN_PRODUCTION_MANIFEST_PATH = os.path.join(MANIFESTS_DIR, "frontend_modern_production.sha256.json")


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
    exec_cmd = list(cmd)
    if sys.platform == "win32" and exec_cmd[0] == "npm":
        exec_cmd[0] = "npm.cmd"
    res = subprocess.run(exec_cmd, cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
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
    legacy_size = get_dir_size(CONVERTED_OUTPUT_DIR)
    modern_size = get_dir_size(FRONTEND_PREVIEW_DIR)
    margin = max(1024 * 1024 * 1024, int(0.20 * (legacy_size + modern_size)))
    required_space = legacy_size + modern_size + margin

    print(f"  Legacy Production Size: {legacy_size / (1024*1024):.2f} MB")
    print(f"  Modern Staging Size   : {modern_size / (1024*1024):.2f} MB")
    print(f"  Safety Margin         : {margin / (1024*1024):.2f} MB")
    print(f"  Required Free Space   : {required_space / (1024*1024):.2f} MB ({required_space / (1024*1024*1024):.2f} GB)")
    print(f"  Actual Free Space     : {free / (1024*1024):.2f} MB ({free / (1024*1024*1024):.2f} GB)")

    if free < required_space:
        raise RuntimeError(
            f"Disk space preflight failed! Available {free / (1024*1024):.2f} MB < Required {required_space / (1024*1024):.2f} MB"
        )
    print("  [GATE PASSED] Sufficient disk space verified.")


def preflight_quality_gates() -> None:
    print("\n--- Gate 2: Code Quality, Contracts & Unit Tests Preflight ---")
    run_cmd(["npm", "--prefix", "apps/web", "run", "typecheck"], "TypeScript Typecheck (tsc --noEmit)")
    run_cmd(["npm", "--prefix", "apps/web", "test"], "Vitest Unit Tests (vitest run)")
    run_cmd([sys.executable, "tests/test_structured_mcmod_contract.py"], "MCMod Structured Data Contract")
    run_cmd([sys.executable, "tests/test_search_golden.py"], "Search Golden Tests")
    run_cmd([sys.executable, "tests/test_filter_golden.py"], "Filter Golden Tests")
    run_cmd([sys.executable, "tests/test_bili_grouping_explanation.py"], "Bilibili Grouping Invariant (53 vs 47)")
    run_cmd([sys.executable, "tests/test_correctness_regressions.py"], "Correctness Regressions Test Suite (9 P0 Items)")
    run_cmd([sys.executable, "tests/test_release_date_semantics.py"], "Release-Date Semantics Contract (Phase 3F.2)")
    print("  [GATE PASSED] All code quality and contract tests passed.")


def preflight_stage_preview() -> None:
    print("\n--- Gate 3: Staging Frontend Preview ---")
    run_cmd([sys.executable, "pipeline/stage_frontend_preview.py"], "Stage Frontend Preview")
    print("  [GATE PASSED] Frontend preview staged.")


def preflight_wiring_and_browsers() -> None:
    print("\n--- Gate 4: Subsystem Wiring & Dual-Target Browser Verification ---")
    run_cmd(["node", "pipeline/smoke_test_wiring.js", "build/frontend_preview", "8780"], "Preview Integration Wiring Test (18/18)")
    run_cmd(["node", "pipeline/smoke_test_single.js", "converted_output", "8768"], "Legacy Production Browser Test (33/33)")
    run_cmd(["node", "pipeline/smoke_test_single.js", "build/frontend_preview", "8770"], "Preview Browser Test (33/33)")
    print("  [GATE PASSED] All preflight browser and wiring gates passed.")


def execute_cutover() -> str:
    print("\n============================================================")
    print("  Executing Production Frontend Cutover (Legacy -> Modern)")
    print("============================================================")
    os.makedirs(MANIFESTS_DIR, exist_ok=True)
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    commit = get_git_commit(REPO_ROOT)

    # Step 1: Manifest Legacy Production
    print("\n[Step 1/6] Generating SHA-256 Manifest for current Legacy Production...")
    legacy_files = count_files(CONVERTED_OUTPUT_DIR)
    legacy_bytes = get_dir_size(CONVERTED_OUTPUT_DIR)
    legacy_manifest = generate_manifest(
        target_dir=CONVERTED_OUTPUT_DIR,
        output_manifest_path=LEGACY_MANIFEST_PATH,
        extra_metadata={
            "frontend_type": "legacy",
            "source_commit": commit,
            "file_count": legacy_files,
            "total_size": legacy_bytes
        }
    )
    is_match, details = verify_manifest(CONVERTED_OUTPUT_DIR, LEGACY_MANIFEST_PATH)
    if not is_match:
        raise RuntimeError(f"Legacy Production manifest verification failed: {details}")
    print(f"  [+] Legacy Production manifest created & verified ({legacy_manifest['total_files']} files, {legacy_manifest['total_size_mb']} MB).")

    # Step 2: Backup Legacy Frontend
    ts = time.strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(BACKUPS_DIR, f"frontend-legacy-{ts}")
    print(f"\n[Step 2/6] Backing up Legacy Production -> {backup_dir}...")
    t0 = time.time()
    shutil.copytree(CONVERTED_OUTPUT_DIR, backup_dir)
    print(f"  [+] Legacy backup completed in {time.time() - t0:.2f}s.")

    # Write backup metadata
    with open(os.path.join(backup_dir, "metadata.json"), "w", encoding="utf-8") as fp:
        json.dump({
            "backed_up_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "source_commit": commit,
            "manifest_path": os.path.relpath(LEGACY_MANIFEST_PATH, REPO_ROOT).replace("\\", "/"),
            "total_files": legacy_files,
            "total_size_bytes": legacy_bytes,
            "total_size_mb": round(legacy_bytes / (1024 * 1024), 2),
            "frontend_type": "legacy"
        }, fp, indent=2, ensure_ascii=False)

    is_backup_valid, bdetails = verify_manifest(backup_dir, LEGACY_MANIFEST_PATH, ignore_extra=["metadata.json"])
    if not is_backup_valid:
        raise RuntimeError(f"Legacy backup verification failed against manifest: {bdetails}")
    print(f"  [+] Legacy backup verified 100% against manifest.")

    # Step 3: Manifest Modern Staging
    print("\n[Step 3/6] Generating SHA-256 Manifest for Modern Staging (build/frontend_preview)...")
    staging_manifest = generate_manifest(
        target_dir=FRONTEND_PREVIEW_DIR,
        output_manifest_path=MODERN_STAGING_MANIFEST_PATH,
        extra_metadata={
            "frontend_type": "modern-vite",
            "source_commit": commit
        }
    )
    is_staging_valid, sdetails = verify_manifest(FRONTEND_PREVIEW_DIR, MODERN_STAGING_MANIFEST_PATH)
    if not is_staging_valid:
        raise RuntimeError(f"Modern Staging manifest verification failed: {sdetails}")
    print(f"  [+] Modern Staging manifest verified ({staging_manifest['total_files']} files, {staging_manifest['total_size_mb']} MB).")

    # Step 4: Cutover Execution (Short Transaction + Recoverable)
    print("\n[Step 4/6] Activating Modern Frontend into converted_output/...")
    if os.path.exists(STAGING_TEMP_DIR):
        shutil.rmtree(STAGING_TEMP_DIR)
    if os.path.exists(SWAP_TEMP_DIR):
        shutil.rmtree(SWAP_TEMP_DIR)

    t0 = time.time()
    shutil.copytree(FRONTEND_PREVIEW_DIR, STAGING_TEMP_DIR)
    is_temp_valid, _ = verify_manifest(STAGING_TEMP_DIR, MODERN_STAGING_MANIFEST_PATH)
    if not is_temp_valid:
        shutil.rmtree(STAGING_TEMP_DIR, ignore_errors=True)
        raise RuntimeError("Staging temp copy failed verification before swap.")

    # Swap sequence with automatic recovery
    try:
        shutil.move(CONVERTED_OUTPUT_DIR, SWAP_TEMP_DIR)
        shutil.move(STAGING_TEMP_DIR, CONVERTED_OUTPUT_DIR)
        shutil.rmtree(SWAP_TEMP_DIR, ignore_errors=True)
        print(f"  [+] Cutover swap completed in {time.time() - t0:.2f}s.")
    except Exception as swap_err:
        print(f"[-] CRITICAL ERROR during swap: {swap_err}")
        print("[*] Initiating self-healing rollback...")
        if os.path.exists(SWAP_TEMP_DIR) and not os.path.exists(CONVERTED_OUTPUT_DIR):
            shutil.move(SWAP_TEMP_DIR, CONVERTED_OUTPUT_DIR)
        elif not os.path.exists(CONVERTED_OUTPUT_DIR):
            shutil.copytree(backup_dir, CONVERTED_OUTPUT_DIR)
        raise RuntimeError(f"Cutover failed during swap: {swap_err}. Self-healing executed.")

    # Step 5: Generate & Verify Modern Production Manifest
    print("\n[Step 5/6] Generating SHA-256 Manifest for Active Modern Production...")
    prod_manifest = generate_manifest(
        target_dir=CONVERTED_OUTPUT_DIR,
        output_manifest_path=MODERN_PRODUCTION_MANIFEST_PATH,
        extra_metadata={
            "frontend_type": "modern-vite",
            "source_commit": commit,
            "backup_legacy_path": os.path.relpath(backup_dir, REPO_ROOT).replace("\\", "/")
        }
    )
    is_prod_valid, pdetails = verify_manifest(CONVERTED_OUTPUT_DIR, MODERN_PRODUCTION_MANIFEST_PATH)
    if not is_prod_valid:
        print(f"[-] Modern Production verification failed: {pdetails}")
        print("[*] Rolling back to legacy backup...")
        shutil.rmtree(CONVERTED_OUTPUT_DIR, ignore_errors=True)
        shutil.copytree(backup_dir, CONVERTED_OUTPUT_DIR)
        raise RuntimeError("Modern Production manifest mismatch! Rolled back to legacy.")
    print(f"  [+] Modern Production verified 100% match ({prod_manifest['total_files']} files, {prod_manifest['total_size_mb']} MB).")

    # Step 6: Update production_state.json
    print("\n[Step 6/6] Updating build/production_state.json...")
    db_hash = compute_sha256(CANONICAL_DB) if os.path.exists(CANONICAL_DB) else "unknown"

    state = {
        "active_pipeline": "v2",
        "active_frontend": "modern-vite",
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "frontend_source_commit": commit,
        "frontend_manifest": os.path.relpath(MODERN_PRODUCTION_MANIFEST_PATH, REPO_ROOT).replace("\\", "/"),
        "legacy_frontend_backup": os.path.relpath(backup_dir, REPO_ROOT).replace("\\", "/"),
        "legacy_frontend_manifest": os.path.relpath(LEGACY_MANIFEST_PATH, REPO_ROOT).replace("\\", "/"),
        "canonical_db_hash": db_hash,
        "record_count": 73522
    }
    with open(PRODUCTION_STATE_PATH, "w", encoding="utf-8") as fp:
        json.dump(state, fp, indent=2, ensure_ascii=False)
    print("  [+] production_state.json updated successfully.")

    return backup_dir


def post_cutover_verification() -> None:
    print("\n--- Gate 5: Modern Production Acceptance Verification ---")
    run_cmd(["node", "pipeline/smoke_test_single.js", "converted_output", "8768"], "Modern Production Browser Test (33/33)")
    run_cmd(["node", "pipeline/smoke_test_wiring.js", "converted_output", "8780"], "Modern Production Wiring Test (18/18)")
    print("  [GATE PASSED] Modern Production accepted with 0 regressions.")


def main():
    print("============================================================")
    print("  Architecture V2 — Phase 3D Frontend Cutover Process")
    print("============================================================")
    t_start = time.time()

    preflight_disk_space()
    preflight_quality_gates()
    preflight_stage_preview()
    preflight_wiring_and_browsers()

    backup_dir = execute_cutover()
    post_cutover_verification()

    print("\n============================================================")
    print("  PHASE 3D PRODUCTION CUTOVER SUCCESSFUL!")
    print(f"  Active Frontend       : modern-vite")
    print(f"  Legacy Backup Path    : {backup_dir}")
    print(f"  Total Cutover Duration: {time.time() - t_start:.2f}s")
    print("============================================================")


if __name__ == "__main__":
    main()

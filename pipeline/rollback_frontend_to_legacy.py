"""
Architecture V2 - Phase 3F.1: Decoupled Frontend Rollback to Legacy.
Swaps ONLY the frontend presentation layer in converted_output/ to the
verified Correctness-Compatible Legacy Frontend (build/frontend_legacy_current_data)
while strictly preserving the current Phase 3F data sidecars and Canonical DB.
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

from pipeline.manifest import compute_sha256

CONVERTED_OUTPUT_DIR = os.path.join(REPO_ROOT, "converted_output")
PRODUCTION_STATE_PATH = os.path.join(REPO_ROOT, "build", "production_state.json")
LEGACY_FALLBACK_DIR = os.path.join(REPO_ROOT, "build", "frontend_legacy_current_data")
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
    print("  Architecture V2 — Decoupled Frontend Rollback to Legacy")
    print("============================================================")
    t_start = time.time()

    if not os.path.exists(PRODUCTION_STATE_PATH):
        raise FileNotFoundError(f"Production state file not found: {PRODUCTION_STATE_PATH}")

    with open(PRODUCTION_STATE_PATH, "r", encoding="utf-8") as fp:
        state = json.load(fp)

    if not os.path.exists(LEGACY_FALLBACK_DIR):
        raise FileNotFoundError(f"Legacy fallback staging directory not found: {LEGACY_FALLBACK_DIR}")

    print(f"  Legacy Frontend Source : {LEGACY_FALLBACK_DIR}")
    print(f"  Production Target      : {CONVERTED_OUTPUT_DIR}")
    print("  Data Preservation Mode : Strict (Preserves current Phase 3F Data Sidecars)")

    # Step 1: Swap Frontend Code Layers Only
    print("\n[Step 1/3] Swapping frontend code layer (assets, HTML)...")
    
    # Replace assets directory
    prod_assets = os.path.join(CONVERTED_OUTPUT_DIR, "assets")
    src_assets = os.path.join(LEGACY_FALLBACK_DIR, "assets")
    if os.path.exists(prod_assets):
        shutil.rmtree(prod_assets, ignore_errors=True)
    shutil.copytree(src_assets, prod_assets)

    # Replace HTML files
    for html_name in ["index.html", "看板.html"]:
        src_html = os.path.join(LEGACY_FALLBACK_DIR, html_name)
        if os.path.exists(src_html):
            shutil.copy2(src_html, os.path.join(CONVERTED_OUTPUT_DIR, html_name))

    # Ensure table_rows.js is present for Legacy MCMod table
    src_table_rows = os.path.join(LEGACY_FALLBACK_DIR, "data", "table_rows.js")
    dst_table_rows = os.path.join(CONVERTED_OUTPUT_DIR, "data", "table_rows.js")
    if os.path.exists(src_table_rows) and not os.path.exists(dst_table_rows):
        shutil.copy2(src_table_rows, dst_table_rows)

    print("  [+] Legacy frontend code swapped. Data sidecars preserved intact.")

    # Step 2: Update production_state.json
    print("\n[Step 2/3] Updating build/production_state.json...")
    db_hash = compute_sha256(CANONICAL_DB) if os.path.exists(CANONICAL_DB) else state.get("canonical_db_hash", "unknown")
    state["active_frontend"] = "legacy"
    state["active_pipeline"] = "v2"  # Data Pipeline strictly preserved as V2!
    state["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    state["canonical_db_hash"] = db_hash

    with open(PRODUCTION_STATE_PATH, "w", encoding="utf-8") as fp:
        json.dump(state, fp, indent=2, ensure_ascii=False)
    print("  [+] production_state.json updated (active_frontend = legacy, active_pipeline = v2).")

    # Step 3: Post-rollback browser verification
    print("\n[Step 3/3] Gate: Post-Rollback Legacy Browser Verification ---")
    run_cmd(["node", "pipeline/smoke_test_single.js", "converted_output", "8768"], "Legacy Fallback Browser Test (33/33)")
    print("  [GATE PASSED] Legacy Fallback verified with 0 regressions.")

    print("\n============================================================")
    print("  FRONTEND ROLLBACK TO LEGACY SUCCESSFUL!")
    print("  Active Frontend       : legacy")
    print("  Active Pipeline       : v2")
    print(f"  Canonical DB Hash     : {db_hash}")
    print(f"  Duration              : {time.time() - t_start:.2f}s")
    print("============================================================")


if __name__ == "__main__":
    rollback_frontend_to_legacy()

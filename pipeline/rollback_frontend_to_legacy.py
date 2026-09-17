"""
Architecture V2 - Phase 3F.1: Decoupled Frontend Rollback to Legacy.
Swaps ONLY the frontend presentation layer in converted_output/ to the
verified Correctness-Compatible Legacy Frontend (build/frontend_legacy_current_data)
while strictly preserving the current Phase 3F data sidecars and Canonical DB.

Phase 3G-D.1R.1 — Frontend/Data Rollback Contract Finalization:
The legacy MCMod row model (`window.tableRowsData`) is a FRONTEND compatibility
artifact, not production data. It is now emitted into the frontend code layer at
`assets/legacy-compat/table_rows.js` instead of `data/table_rows.js`, so a
frontend-only rollback leaves `converted_output/data/` byte-identical
(file set + rollup digest). This script asserts that contract before and after
the swap and fails loudly if the data layer was touched.
"""
import os
import sys
import shutil
import time
import json
import subprocess
import tempfile

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
from pipeline.audit.digest_data_dir import digest_dir
from pipeline.exporters.legacy.mcmod import MCModExporter

CONVERTED_OUTPUT_DIR = os.path.join(REPO_ROOT, "converted_output")
PRODUCTION_DATA_DIR = os.path.join(CONVERTED_OUTPUT_DIR, "data")
PRODUCTION_STATE_PATH = os.path.join(REPO_ROOT, "build", "production_state.json")
LEGACY_FALLBACK_DIR = os.path.join(REPO_ROOT, "build", "frontend_legacy_current_data")
CANONICAL_DB = os.path.join(REPO_ROOT, "build", "canonical.db")

# Frontend-layer location of the legacy compatibility artifact (NOT the data layer).
LEGACY_COMPAT_REL_DIR = os.path.join("assets", "legacy-compat")
LEGACY_COMPAT_FILENAME = "table_rows.js"


def build_legacy_compat_artifact(dest_dir: str) -> str:
    """Regenerate the legacy row model from the CURRENT canonical DB.

    Written into the frontend code layer so the production data directory is
    never mutated by a frontend-only rollback. Regenerating (rather than copying
    a staged snapshot) guarantees the artifact always matches canonical.
    """
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, LEGACY_COMPAT_FILENAME)
    with tempfile.TemporaryDirectory(prefix="legacy_compat_") as tmp:
        exporter = MCModExporter(CANONICAL_DB, os.path.join(tmp, "data"))
        result = exporter.export_all()
        src = os.path.join(tmp, "data", LEGACY_COMPAT_FILENAME)
        if not os.path.exists(src):
            raise RuntimeError(f"Legacy exporter did not produce {LEGACY_COMPAT_FILENAME}")
        shutil.copy2(src, dest_path)
        rows = result.get("table_rows_count") if isinstance(result, dict) else None
    print(f"  [+] Legacy compat artifact rebuilt from canonical ({rows} rows) -> "
          f"{os.path.relpath(dest_path, REPO_ROOT).replace(os.sep, '/')}")
    return dest_path


def assert_data_layer_unchanged(before: dict, after: dict, stage: str) -> None:
    """Hard contract: a frontend-only rollback must not change converted_output/data/."""
    if before["rollup_sha256"] == after["rollup_sha256"]:
        print(f"  [GATE PASSED] Data layer byte-identical {stage} "
              f"({after['file_count']} files, {after['rollup_sha256'][:16]}…)")
        return
    before_map = {e["path"]: e["sha256"] for e in before["files"]}
    after_map = {e["path"]: e["sha256"] for e in after["files"]}
    added = sorted(set(after_map) - set(before_map))
    removed = sorted(set(before_map) - set(after_map))
    modified = sorted(p for p in set(before_map) & set(after_map)
                      if before_map[p] != after_map[p])
    raise RuntimeError(
        "FRONTEND/DATA CONTRACT VIOLATION: converted_output/data/ changed "
        f"{stage}. added={added[:5]} removed={removed[:5]} modified={modified[:5]}"
    )


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
    print("  Data Preservation Mode : Strict (frontend-only; data/ must stay byte-identical)")

    # Baseline the production data layer before touching anything.
    print("\n[Step 0/3] Baselining production data layer (converted_output/data)...")
    data_before = digest_dir(PRODUCTION_DATA_DIR)
    print(f"  data/ baseline : {data_before['file_count']} files, "
          f"rollup {data_before['rollup_sha256'][:16]}…")

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
    # Phase 3G-D.1R.1: emitted into the FRONTEND layer, never into data/.
    compat_dir = os.path.join(CONVERTED_OUTPUT_DIR, LEGACY_COMPAT_REL_DIR)
    build_legacy_compat_artifact(compat_dir)

    print("  [+] Legacy frontend code swapped. Data sidecars preserved intact.")

    # Hard contract gate: the production data layer must be untouched.
    data_after_swap = digest_dir(PRODUCTION_DATA_DIR)
    assert_data_layer_unchanged(data_before, data_after_swap, "after frontend swap")

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
    print(f"  Data layer            : UNCHANGED ({data_before['file_count']} files, "
          f"{data_before['rollup_sha256'][:16]}…)")
    print(f"  Legacy compat artifact: {LEGACY_COMPAT_REL_DIR.replace(os.sep, '/')}/{LEGACY_COMPAT_FILENAME}")
    print(f"  Duration              : {time.time() - t_start:.2f}s")
    print("============================================================")


if __name__ == "__main__":
    rollback_frontend_to_legacy()

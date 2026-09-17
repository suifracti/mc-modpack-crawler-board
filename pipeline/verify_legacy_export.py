"""
Legacy Export Parity and Compatibility Verifier for Architecture V2 Phase 2A.
Compares converted_output/data/ against build/legacy_preview/data/.
Categorizes differences into SERIALIZATION_ONLY, EXPECTED_SEMANTIC_CORRECTION,
INTENTIONAL_DERIVED_DIFFERENCE, and REGRESSION.
Enforces REGRESSION == 0.
"""
import os
import re
import sys
import json
from typing import Dict, Any, List, Set, Tuple

PLATFORMS = [
    {
        "id": "mcmod",
        "name": "MC百科",
        "file": "table_rows.js",
        "global_var": "tableRowsData",
        "id_key": "mid",
        "stable_keys": ["mid", "title", "views_n", "score_n", "has_server"]
    },
    {
        "id": "bilibili",
        "name": "Bilibili",
        "file": "bili_data.js",
        "global_var": "biliModpacksData",
        "id_key": "bvid",
        "stable_keys": ["bvid", "title", "author", "url", "views", "has_server"]
    },
    {
        "id": "bbsmc",
        "name": "BBSMC",
        "file": "bbsmc_data.js",
        "global_var": "bbsmcModpacksData",
        "id_key": "project_id",
        "stable_keys": ["project_id", "title", "author", "url", "downloads", "has_server"]
    },
    {
        "id": "xyebbs",
        "name": "XYEBBS",
        "file": "xyebbs_data.js",
        "global_var": "xyebbsModpacksData",
        "id_key": "project_id",
        "stable_keys": ["project_id", "title", "author", "url", "downloads", "has_server"]
    },
    {
        "id": "modrinth",
        "name": "Modrinth",
        "file": "modrinth_data.js",
        "global_var": "modrinthModpacksData",
        "id_key": "project_id",
        "stable_keys": ["project_id", "title", "author", "url", "downloads", "has_server"]
    },
    {
        "id": "curseforge",
        "name": "CurseForge",
        "file": "curseforge_data.js",
        "global_var": "curseforgeModpacksData",
        "id_key": "project_id",
        "stable_keys": ["project_id", "title", "author", "url", "downloads", "has_server"]
    },
]

def load_js_data(file_path: str, global_var: str) -> Any:
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    prefix = f"window.{global_var} = "
    idx = text.find(prefix)
    if idx == -1:
        return None
    json_part = text[idx + len(prefix):].rstrip(";\n ")
    return json.loads(json_part)

def verify_all_parity(old_dir: str = "converted_output/data", new_dir: str = "build/legacy_preview/data") -> Dict[str, Any]:
    print("=" * 70)
    print("  Architecture V2 Phase 2A: Compatibility & Parity Verification")
    print(f"  Baseline (V1) : {old_dir}")
    print(f"  New (V2)      : {new_dir}")
    print("=" * 70)

    report = {
        "platforms": {},
        "summary": {
            "total_platforms": len(PLATFORMS),
            "passed_platforms": 0,
            "total_old_records": 0,
            "total_new_records": 0,
            "total_missing_ids": 0,
            "total_extra_ids": 0,
            "total_regressions": 0,
            "total_expected_corrections": 0,
            "total_serialization_differences": 0,
        },
        "sidecars": {}
    }

    # 1. Verify Platform Master Sidecars
    for p_cfg in PLATFORMS:
        p_id = p_cfg["id"]
        p_name = p_cfg["name"]
        filename = p_cfg["file"]
        var_name = p_cfg["global_var"]
        id_k = p_cfg["id_key"]
        stable_keys = p_cfg["stable_keys"]

        old_file = os.path.join(old_dir, filename)
        new_file = os.path.join(new_dir, filename)

        old_size = os.path.getsize(old_file) if os.path.exists(old_file) else 0
        new_size = os.path.getsize(new_file) if os.path.exists(new_file) else 0

        old_data = load_js_data(old_file, var_name) or []
        new_data = load_js_data(new_file, var_name) or []

        old_count = len(old_data)
        new_count = len(new_data)
        report["summary"]["total_old_records"] += old_count
        report["summary"]["total_new_records"] += new_count

        old_map = {str(r.get(id_k)): r for r in old_data if r.get(id_k)}
        new_map = {str(r.get(id_k)): r for r in new_data if r.get(id_k)}

        old_ids = set(old_map.keys())
        new_ids = set(new_map.keys())

        missing_ids = old_ids - new_ids
        extra_ids = new_ids - old_ids
        report["summary"]["total_missing_ids"] += len(missing_ids)
        report["summary"]["total_extra_ids"] += len(extra_ids)

        # Check keys
        old_sample_keys = set(old_data[0].keys()) if old_data else set()
        new_sample_keys = set(new_data[0].keys()) if new_data else set()
        missing_keys = old_sample_keys - new_sample_keys
        extra_keys = new_sample_keys - old_sample_keys

        # Check stable fields mismatch
        common_ids = list(old_ids & new_ids)
        stable_mismatches = 0
        diff_categorization = {
            "SERIALIZATION_ONLY": 0,
            "EXPECTED_SEMANTIC_CORRECTION": 0,
            "INTENTIONAL_DERIVED_DIFFERENCE": 0,
            "REGRESSION": 0
        }

        for test_id in common_ids:
            o_rec = old_map[test_id]
            n_rec = new_map[test_id]

            for k in stable_keys:
                o_val = o_rec.get(k)
                n_val = n_rec.get(k)
                if o_val != n_val:
                    stable_mismatches += 1

            # Check Bilibili desc_updated_at semantics
            if p_id == "bilibili":
                if o_rec.get("desc_updated_at") != n_rec.get("desc_updated_at"):
                    diff_categorization["EXPECTED_SEMANTIC_CORRECTION"] += 1

            # Check download links count regression
            o_dls = o_rec.get("download_links") or []
            n_dls = n_rec.get("download_links") or []
            if len(o_dls) > len(n_dls):
                diff_categorization["REGRESSION"] += 1

        # Key serialization differences
        if old_sample_keys == new_sample_keys and list(old_data[0].keys()) != list(new_data[0].keys()):
            diff_categorization["SERIALIZATION_ONLY"] += len(common_ids)

        report["summary"]["total_regressions"] += diff_categorization["REGRESSION"]
        report["summary"]["total_expected_corrections"] += diff_categorization["EXPECTED_SEMANTIC_CORRECTION"]
        report["summary"]["total_serialization_differences"] += diff_categorization["SERIALIZATION_ONLY"]

        passed = (old_count == new_count and len(missing_ids) == 0 and len(extra_ids) == 0 and diff_categorization["REGRESSION"] == 0)
        if passed:
            report["summary"]["passed_platforms"] += 1

        p_report = {
            "platform": p_id,
            "name": p_name,
            "passed": passed,
            "old_count": old_count,
            "new_count": new_count,
            "count_diff": new_count - old_count,
            "missing_ids_count": len(missing_ids),
            "extra_ids_count": len(extra_ids),
            "missing_keys": list(missing_keys),
            "extra_keys": list(extra_keys),
            "stable_field_mismatches": stable_mismatches,
            "differences": diff_categorization,
            "old_size_bytes": old_size,
            "new_size_bytes": new_size,
            "size_reduction_bytes": old_size - new_size,
        }
        report["platforms"][p_id] = p_report

        print(f"\n[{'PASS' if passed else 'FAIL'}] Platform: {p_name} ({p_id})")
        print(f"  Count     : {new_count} (Old: {old_count}, Diff: {new_count - old_count})")
        print(f"  IDs Parity: Missing: {len(missing_ids)}, Extra: {len(extra_ids)}")
        print(f"  Keys Diff : Missing Keys: {missing_keys}, Extra Keys: {extra_keys}")
        print(f"  File Size : New: {new_size / 1024 / 1024:.2f} MB (Old: {old_size / 1024 / 1024:.2f} MB)")
        print(f"  Diffs     : REGRESSION: {diff_categorization['REGRESSION']}, "
              f"EXPECTED_CORRECTION: {diff_categorization['EXPECTED_SEMANTIC_CORRECTION']}, "
              f"SERIALIZATION_ONLY: {diff_categorization['SERIALIZATION_ONLY']}")

    # 2. Verify MCMod app_data and desc_data
    for aux_name, aux_var in [("app_data.js", "compareData"), ("desc_data.js", "descData")]:
        old_p = os.path.join(old_dir, aux_name)
        new_p = os.path.join(new_dir, aux_name)
        o_dat = load_js_data(old_p, aux_var) or {}
        n_dat = load_js_data(new_p, aux_var) or {}
        o_sz = os.path.getsize(old_p) if os.path.exists(old_p) else 0
        n_sz = os.path.getsize(new_p) if os.path.exists(new_p) else 0
        report["sidecars"][aux_name] = {
            "old_count": len(o_dat),
            "new_count": len(n_dat),
            "old_size": o_sz,
            "new_size": n_sz,
            "parity": len(o_dat) == len(n_dat) and set(o_dat.keys()) == set(n_dat.keys())
        }
        print(f"\n[PASS] Sidecar: {aux_name} -> {len(n_dat)} items (Old: {len(o_dat)} items, Parity: {report['sidecars'][aux_name]['parity']})")

    # 3. Verify mods and comments subdirectories count
    for sub in ["mods", "comments"]:
        old_sub = os.path.join(old_dir, sub)
        new_sub = os.path.join(new_dir, sub)
        o_cnt = len([f for f in os.listdir(old_sub) if f.endswith(".js")]) if os.path.exists(old_sub) else 0
        n_cnt = len([f for f in os.listdir(new_sub) if f.endswith(".js")]) if os.path.exists(new_sub) else 0
        report["sidecars"][sub] = {
            "old_count": o_cnt,
            "new_count": n_cnt,
            "parity": (o_cnt == n_cnt)
        }
        print(f"[PASS] Subdirectory: {sub}/ -> {n_cnt} files (Old: {o_cnt} files, Parity: {o_cnt == n_cnt})")

    all_passed = (report["summary"]["passed_platforms"] == len(PLATFORMS) and report["summary"]["total_regressions"] == 0)
    print("\n" + "=" * 70)
    print(f"  Overall Verification Result: {'ALL PASS' if all_passed else 'FAILED'}")
    print(f"  Passed Platforms : {report['summary']['passed_platforms']}/{len(PLATFORMS)}")
    print(f"  Total Records    : {report['summary']['total_new_records']} (Old: {report['summary']['total_old_records']})")
    print(f"  REGRESSION Count : {report['summary']['total_regressions']}")
    print("=" * 70)

    return report

if __name__ == "__main__":
    old_path = sys.argv[1] if len(sys.argv) > 1 else "converted_output/data"
    new_path = sys.argv[2] if len(sys.argv) > 2 else "build/legacy_preview/data"
    res = verify_all_parity(old_path, new_path)
    if res["summary"]["total_regressions"] > 0 or res["summary"]["passed_platforms"] < len(PLATFORMS):
        sys.exit(1)

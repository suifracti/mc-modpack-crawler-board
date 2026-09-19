"""
Legacy / Portable Exporter Orchestrator for Architecture V2 Phase 2A.
Generates build/legacy_preview/ from build/canonical.db.
STRICT RULE: Never touches crawler_output/*.json.
"""
import os
import sys
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import time
import shutil
import argparse
from typing import Dict, Any

from pipeline.exporters.legacy.mcmod import MCModExporter
from pipeline.exporters.legacy.bilibili import BilibiliExporter
from pipeline.exporters.legacy.bbsmc import BBSMCExporter
from pipeline.exporters.legacy.xyebbs import XYEBBSExporter
from pipeline.exporters.legacy.modrinth import ModrinthExporter
from pipeline.exporters.legacy.curseforge import CurseForgeExporter
from pipeline.exporters.legacy.audit import AuditExporter

def export_legacy_preview(db_path: str = "build/canonical.db", preview_dir: str = "build/legacy_preview") -> Dict[str, Any]:
    start_total = time.time()
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    abs_db = os.path.abspath(os.path.join(repo_root, db_path))
    abs_preview = os.path.abspath(os.path.join(repo_root, preview_dir))
    data_dir = os.path.join(abs_preview, "data")

    if not os.path.exists(abs_db):
        raise FileNotFoundError(f"Canonical database not found: {abs_db}")

    print("=" * 65)
    print("  Architecture V2: Legacy / Portable Exporter (Phase 2A)")
    print(f"  Source Database : {abs_db}")
    print(f"  Target Preview  : {abs_preview}")
    print("=" * 65)

    os.makedirs(data_dir, exist_ok=True)

    # 1. Synchronize static frontend assets, vendor libraries, and dashboard HTML
    web_dir = os.path.join(repo_root, "web")
    assets_src = os.path.join(web_dir, "assets")
    assets_dst = os.path.join(abs_preview, "assets")
    if os.path.exists(assets_src):
        shutil.copytree(assets_src, assets_dst, dirs_exist_ok=True)
        print("  [+] Assets synchronized to: build/legacy_preview/assets/")

    vendor_src = os.path.join(repo_root, "converted_output", "data", "vendor")
    vendor_dst = os.path.join(data_dir, "vendor")
    if os.path.exists(vendor_src):
        shutil.copytree(vendor_src, vendor_dst, dirs_exist_ok=True)
        print("  [+] Vendor libraries synchronized to: build/legacy_preview/data/vendor/")

    rendered_html_src = os.path.join(repo_root, "converted_output", "点击打开.html")
    template_src = os.path.join(web_dir, "template.html")
    html_dst = os.path.join(abs_preview, "看板.html")
    if os.path.exists(rendered_html_src):
        shutil.copy2(rendered_html_src, html_dst)
        print("  [+] Dashboard HTML copied to: build/legacy_preview/看板.html")
    elif os.path.exists(template_src):
        shutil.copy2(template_src, html_dst)
        print("  [+] Dashboard template copied to: build/legacy_preview/看板.html")

    results = {}
    timings = {}

    # 2. Run MCMod Exporter
    t0 = time.time()
    print("\n[*] Exporting MCMod sidecars (table_rows.js, app_data.js, desc_data.js, mods, comments)...")
    mc_exp = MCModExporter(abs_db, data_dir)
    results["mcmod"] = mc_exp.export_all()
    timings["mcmod"] = time.time() - t0
    print(f"  [+] MCMod completed in {timings['mcmod']:.2f}s: {results['mcmod']['table_rows_count']} rows, "
          f"{results['mcmod']['mods_sidecars_count']} mod sidecars, {results['mcmod']['comments_sidecars_count']} comment sidecars")

    # 3. Run Bilibili Exporter
    t0 = time.time()
    print("\n[*] Exporting Bilibili sidecar (bili_data.js)...")
    bili_exp = BilibiliExporter(abs_db, data_dir)
    results["bilibili"] = bili_exp.export_all()
    timings["bilibili"] = time.time() - t0
    print(f"  [+] Bilibili completed in {timings['bilibili']:.2f}s: {results['bilibili']['count']} records")

    # 4. Run BBSMC Exporter
    t0 = time.time()
    print("\n[*] Exporting BBSMC sidecar (bbsmc_data.js)...")
    bbsmc_exp = BBSMCExporter(abs_db, data_dir)
    results["bbsmc"] = bbsmc_exp.export_all()
    timings["bbsmc"] = time.time() - t0
    print(f"  [+] BBSMC completed in {timings['bbsmc']:.2f}s: {results['bbsmc']['count']} records")

    # 5. Run XYEBBS Exporter
    t0 = time.time()
    print("\n[*] Exporting XYEBBS sidecar (xyebbs_data.js)...")
    xyebbs_exp = XYEBBSExporter(abs_db, data_dir)
    results["xyebbs"] = xyebbs_exp.export_all()
    timings["xyebbs"] = time.time() - t0
    print(f"  [+] XYEBBS completed in {timings['xyebbs']:.2f}s: {results['xyebbs']['count']} records")

    # 6. Run Modrinth Exporter
    t0 = time.time()
    print("\n[*] Exporting Modrinth sidecar (modrinth_data.js)...")
    mr_exp = ModrinthExporter(abs_db, data_dir)
    results["modrinth"] = mr_exp.export_all()
    timings["modrinth"] = time.time() - t0
    print(f"  [+] Modrinth completed in {timings['modrinth']:.2f}s: {results['modrinth']['count']} records")

    # 7. Run CurseForge Exporter
    t0 = time.time()
    print("\n[*] Exporting CurseForge sidecar (curseforge_data.js)...")
    cf_exp = CurseForgeExporter(abs_db, data_dir)
    results["curseforge"] = cf_exp.export_all()
    timings["curseforge"] = time.time() - t0
    print(f"  [+] CurseForge completed in {timings['curseforge']:.2f}s: {results['curseforge']['count']} records")

    # 8. Run Audit Exporter
    t0 = time.time()
    print("\n[*] Exporting audit_diff.js...")
    audit_exp = AuditExporter(abs_db, data_dir)
    results["audit"] = audit_exp.export_all()
    timings["audit"] = time.time() - t0
    print(f"  [+] Audit completed in {timings['audit']:.2f}s")

    total_time = time.time() - start_total

    # Measure output sizes
    sizes = {}
    total_bytes = 0
    for root, dirs, files in os.walk(data_dir):
        for f in files:
            p = os.path.join(root, f)
            sz = os.path.getsize(p)
            rel = os.path.relpath(p, data_dir).replace("\\", "/")
            sizes[rel] = sz
            total_bytes += sz

    print("\n" + "=" * 65)
    print(f"  Export Complete! Total Runtime: {total_time:.2f} seconds")
    print(f"  Total Data Size: {total_bytes / 1024 / 1024:.2f} MB")
    print("=" * 65)

    return {
        "results": results,
        "timings": timings,
        "total_time": total_time,
        "total_bytes": total_bytes,
        "sizes": sizes,
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export Legacy Dashboard Preview from Canonical SQLite DB")
    parser.add_argument("--db", default="build/canonical.db", help="Path to canonical.db")
    parser.add_argument("--output-dir", default="build/legacy_preview", help="Target output directory")
    args = parser.parse_args()

    export_legacy_preview(args.db, args.output_dir)

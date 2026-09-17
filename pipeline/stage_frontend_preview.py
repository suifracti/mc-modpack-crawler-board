"""
Stage Frontend Preview for verification (Architecture V2 — Phase 3B).
Builds apps/web, exports structured mcmod_data.js, syncs other sidecars,
and guarantees complete isolation from converted_output/.
"""
import os
import shutil
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

APPS_WEB = os.path.join(REPO_ROOT, 'apps', 'web')
PREVIEW_DIR = os.path.join(REPO_ROOT, 'build', 'frontend_preview')
CONVERTED_DIR = os.path.join(REPO_ROOT, 'converted_output')
CANONICAL_DB = os.path.join(REPO_ROOT, 'build', 'canonical.db')

from pipeline.exporters.structured_mcmod_exporter import StructuredMCModExporter

def main():
    print("[1/5] Exporting structured MCMod data (data/mcmod_data.js)...")
    dst_data_dir = os.path.join(PREVIEW_DIR, 'data')
    os.makedirs(dst_data_dir, exist_ok=True)
    exporter = StructuredMCModExporter(CANONICAL_DB, dst_data_dir)
    res = exporter.export()
    print(f"  Exported {res['count']} structured items ({res['size_bytes'] / 1024:.1f} KB)")

    print("[2/5] Syncing other 5 platforms sidecars & vendor dependencies...")
    src_data_dir = os.path.join(CONVERTED_DIR, 'data')

    # Copy vendor directory
    src_vendor = os.path.join(src_data_dir, 'vendor')
    dst_vendor = os.path.join(dst_data_dir, 'vendor')
    if os.path.exists(src_vendor) and not os.path.exists(dst_vendor):
        shutil.copytree(src_vendor, dst_vendor)

    # Copy other 5 platforms and common sidecars (EXCLUDING table_rows.js!)
    sidecars = [
        'bili_data.js',
        'bbsmc_data.js',
        'xyebbs_data.js',
        'modrinth_data.js',
        'curseforge_data.js',
        'app_data.js',
        'desc_data.js',
        'audit_diff.js',
    ]
    for s in sidecars:
        s_src = os.path.join(src_data_dir, s)
        s_dst = os.path.join(dst_data_dir, s)
        if os.path.exists(s_src):
            shutil.copy2(s_src, s_dst)

    # Sync mods and comments subdirectories if present as real directories
    for sub in ['mods', 'comments']:
        sub_src = os.path.join(src_data_dir, sub)
        sub_dst = os.path.join(dst_data_dir, sub)
        if os.path.exists(sub_src):
            if os.path.exists(sub_dst):
                try:
                    if os.path.islink(sub_dst):
                        os.unlink(sub_dst)
                    else:
                        shutil.rmtree(sub_dst)
                except Exception:
                    pass
            if not os.path.exists(sub_dst):
                shutil.copytree(sub_src, sub_dst)

    # Ensure table_rows.js is NOT present in preview data directory!
    preview_table_rows = os.path.join(dst_data_dir, 'table_rows.js')
    if os.path.exists(preview_table_rows):
        os.remove(preview_table_rows)

    print("[3/5] Building TypeScript + Vite bundle...")
    subprocess.run(["npm", "run", "build"], cwd=APPS_WEB, shell=True, check=True)

    print("[4/5] Syncing CSS assets...")
    dst_css_dir = os.path.join(PREVIEW_DIR, 'assets', 'css')
    os.makedirs(dst_css_dir, exist_ok=True)
    src_css = os.path.join(CONVERTED_DIR, 'assets', 'css', 'dashboard.css')
    if not os.path.exists(src_css):
        src_css = os.path.join(REPO_ROOT, 'web', 'assets', 'css', 'dashboard.css')
    shutil.copy2(src_css, os.path.join(dst_css_dir, 'dashboard.css'))

    print("[5/5] Creating 看板.html link/copy...")
    src_index = os.path.join(PREVIEW_DIR, 'index.html')
    dst_kanban = os.path.join(PREVIEW_DIR, '看板.html')
    shutil.copy2(src_index, dst_kanban)

    print("Frontend preview staging complete!")

if __name__ == '__main__':
    main()

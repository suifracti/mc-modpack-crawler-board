"""
Stage Frontend Preview for verification.
Builds apps/web, syncs data sidecars and CSS, and ensures 看板.html is present.
"""
import os
import shutil
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS_WEB = os.path.join(REPO_ROOT, 'apps', 'web')
PREVIEW_DIR = os.path.join(REPO_ROOT, 'build', 'frontend_preview')
CONVERTED_DIR = os.path.join(REPO_ROOT, 'converted_output')

def main():
    print("[1/4] Building TypeScript + Vite bundle...")
    subprocess.run(["npm", "run", "build"], cwd=APPS_WEB, shell=True, check=True)

    print("[2/4] Syncing CSS assets...")
    dst_css_dir = os.path.join(PREVIEW_DIR, 'assets', 'css')
    os.makedirs(dst_css_dir, exist_ok=True)
    src_css = os.path.join(CONVERTED_DIR, 'assets', 'css', 'dashboard.css')
    if not os.path.exists(src_css):
        src_css = os.path.join(REPO_ROOT, 'web', 'assets', 'css', 'dashboard.css')
    shutil.copy2(src_css, os.path.join(dst_css_dir, 'dashboard.css'))

    print("[3/4] Syncing data sidecars & vendor dependencies...")
    dst_data_dir = os.path.join(PREVIEW_DIR, 'data')
    src_data_dir = os.path.join(CONVERTED_DIR, 'data')
    if not os.path.exists(dst_data_dir):
        # On Windows, try junction if possible, otherwise copy
        try:
            import _winapi
            _winapi.CreateJunction(src_data_dir, dst_data_dir)
            print("  Created junction for data directory.")
        except Exception:
            shutil.copytree(src_data_dir, dst_data_dir)
            print("  Copied data directory.")
    else:
        print("  Data directory already present.")

    print("[4/4] Creating 看板.html link/copy...")
    src_index = os.path.join(PREVIEW_DIR, 'index.html')
    dst_kanban = os.path.join(PREVIEW_DIR, '看板.html')
    shutil.copy2(src_index, dst_kanban)

    print("Frontend preview staging complete!")

if __name__ == '__main__':
    main()

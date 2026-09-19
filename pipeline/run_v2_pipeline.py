"""
Architecture V2 - Phase 2B: V2 Pipeline Runner.
Orchestrates Canonical SQLite -> V2 Legacy Exporter.

Modes:
  --staging     (default) Generates build/legacy_preview/ and validates data integrity.
  --production  Generates staging preview, validates all gates, and executes transactional cutover to converted_output/.
  --build-db    Rebuilds data/canonical.db and build/canonical.db from crawler_output/ before export.
"""
import os
import sys
import argparse
import subprocess

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)


def main():
    parser = argparse.ArgumentParser(description="Architecture V2 Pipeline Runner")
    parser.add_argument(
        "--mode",
        choices=["staging", "production"],
        default="staging",
        help="Target environment mode: 'staging' (build/legacy_preview) or 'production' (cutover to converted_output)"
    )
    parser.add_argument(
        "--staging",
        dest="mode",
        action="store_const",
        const="staging",
        help="Alias for --mode staging"
    )
    parser.add_argument(
        "--production",
        dest="mode",
        action="store_const",
        const="production",
        help="Alias for --mode production"
    )
    parser.add_argument(
        "--build-db",
        action="store_true",
        help="Rebuild Canonical SQLite database before export"
    )
    args = parser.parse_args()

    print("======================================================================")
    print(f"  Architecture V2 Pipeline Runner (Mode: {args.mode.upper()})")
    print("======================================================================\n")

    # Step 1: Rebuild Canonical DB if requested or missing
    canonical_db_build = os.path.join(REPO_ROOT, "build", "canonical.db")
    if args.build_db or not os.path.exists(canonical_db_build):
        print("[*] Building Canonical SQLite database...")
        res = subprocess.run([sys.executable, "pipeline/build_canonical_db.py"], cwd=REPO_ROOT)
        if res.returncode != 0:
            print("[-] Canonical DB build failed.")
            sys.exit(res.returncode)

    # Step 2: Run V2 Legacy Exporter -> build/legacy_preview/
    print("[*] Running V2 Legacy Exporter to build/legacy_preview/...")
    from pipeline.exporters.export_legacy import export_legacy_preview
    export_legacy_preview(db_path="build/canonical.db", preview_dir="build/legacy_preview")

    # Step 3: If production mode, invoke cutover script
    if args.mode == "production":
        print("\n[*] Invoking automated production cutover...")
        res = subprocess.run([sys.executable, "pipeline/cutover_to_v2.py"], cwd=REPO_ROOT)
        if res.returncode != 0:
            print("[-] Production cutover failed.")
            sys.exit(res.returncode)
    else:
        print("\n[+] Staging pipeline completed. Preview ready at build/legacy_preview/.")


if __name__ == "__main__":
    main()

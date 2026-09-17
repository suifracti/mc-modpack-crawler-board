"""
Architecture Unified Pipeline Runner.
Provides a single entry point to execute either V1 (legacy) or V2 (canonical SQLite) pipelines.

Usage:
  python pipeline/run_pipeline.py --pipeline v2 [--staging | --production] [--build-db]
  python pipeline/run_pipeline.py --pipeline v1
"""
import os
import sys
import argparse
import subprocess

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    parser = argparse.ArgumentParser(description="Unified Modpack Pipeline Runner")
    parser.add_argument(
        "--pipeline",
        choices=["v1", "v2"],
        default="v2",
        help="Pipeline version: 'v2' (Canonical SQLite -> Legacy Exporter, default) or 'v1' (Legacy monolithic converter)"
    )
    # Forward other arguments to v2 runner
    parser.add_argument(
        "--mode",
        choices=["staging", "production"],
        default="staging",
        help="V2 mode: 'staging' (build/legacy_preview) or 'production' (cutover to converted_output)"
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
        help="Rebuild Canonical SQLite database (V2 only)"
    )

    args, unknown = parser.parse_known_args()

    print("======================================================================")
    print(f"  Unified Pipeline Runner: Executing Pipeline [{args.pipeline.upper()}]")
    print("======================================================================\n")

    if args.pipeline == "v1":
        print("[*] Launching V1 Pipeline (多平台聚合转换器_v1.0.py)...")
        v1_script = os.path.join(REPO_ROOT, "多平台聚合转换器_v1.0.py")
        if not os.path.exists(v1_script):
            print(f"[-] Error: V1 script not found at {v1_script}")
            sys.exit(1)
        res = subprocess.run([sys.executable, v1_script], cwd=REPO_ROOT)
        sys.exit(res.returncode)

    elif args.pipeline == "v2":
        v2_runner = os.path.join(REPO_ROOT, "pipeline", "run_v2_pipeline.py")
        cmd = [sys.executable, v2_runner, "--mode", args.mode]
        if args.build_db:
            cmd.append("--build-db")
        res = subprocess.run(cmd, cwd=REPO_ROOT)
        sys.exit(res.returncode)


if __name__ == "__main__":
    main()

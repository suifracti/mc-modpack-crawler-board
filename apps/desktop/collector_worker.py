"""Run one existing collector inside an isolated desktop update workspace.

The worker deliberately executes a single explicit platform. It never invokes the
monolithic crawler with ``--auto-convert`` and writes only below ``workspace``.
"""
from __future__ import annotations

import argparse
import json
import os
import runpy
import shutil
import sys
from pathlib import Path


PLATFORMS = {
    "mcmod": {"script": "mcmod_full_crawler.py", "raw": "mcmod_modpacks.json"},
    "bilibili": {"script": "bilibili_crawler.py", "raw": "bilibili_modpacks.json"},
    "bbsmc": {"script": "bbsmc_crawler.py", "raw": "bbsmc_modpacks.json"},
    "xyebbs": {"script": "xyebbs_crawler.py", "raw": "xyebbs_modpacks.json"},
    "modrinth": {"script": "modrinth_crawler.py", "raw": "modrinth_modpacks.json"},
    "curseforge": {"script": "curseforge_full_crawler.py", "raw": "curseforge_modpacks.json"},
}


def emit(**payload: object) -> None:
    print("DESKTOP_EVENT " + json.dumps(payload, ensure_ascii=False), flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MCMod desktop isolated collector worker")
    parser.add_argument("--platform", choices=sorted(PLATFORMS), required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--until", default=None)
    return parser.parse_args()


def build_script_args(platform: str, args: argparse.Namespace) -> list[str]:
    limit = args.limit
    if platform == "bilibili":
        result = ["--mode", "crawl", "--pages", str(args.pages), "--max", str(limit or 20)]
        if args.until:
            result.extend(["--until", args.until])
        return result
    if platform == "mcmod":
        result = ["--mode", "new"]
        if limit:
            result.extend(["--limit", str(limit)])
        return result
    if platform == "bbsmc":
        return ["--type", "modpack", "--max", str(limit or 0), "--enrich", "0"]
    if platform == "xyebbs":
        return ["--max", str(limit or 0), "--enrich", "0"]
    if platform == "modrinth":
        return ["--max", str(limit or 0)]
    if platform == "curseforge":
        return ["--max", str(limit or 0)]
    raise ValueError(platform)


def ensure_stage_dirs(workspace: Path) -> None:
    (workspace / "crawler_output").mkdir(parents=True, exist_ok=True)
    (workspace / "converted_output" / "data").mkdir(parents=True, exist_ok=True)
    (workspace / "build").mkdir(parents=True, exist_ok=True)


def run_selected_collector(args: argparse.Namespace) -> None:
    workspace = Path(args.workspace).resolve()
    source_root = Path(args.source_root).resolve()
    config = PLATFORMS[args.platform]
    source_script = source_root / config["script"]
    if not source_script.exists():
        raise FileNotFoundError(f"collector source not found: {source_script}")

    ensure_stage_dirs(workspace)
    isolated_script = workspace / "_collector" / config["script"]
    isolated_script.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_script, isolated_script)

    script_args = build_script_args(args.platform, args)
    emit(platform=args.platform, phase="采集", processed=0, total=None)
    print(f"desktop collector: {args.platform} args={script_args}", flush=True)

    previous_cwd = Path.cwd()
    previous_argv = sys.argv[:]
    previous_path = sys.path[:]
    try:
        os.chdir(workspace)
        sys.path.insert(0, str(isolated_script.parent))
        sys.argv = [str(isolated_script), *script_args]
        runpy.run_path(str(isolated_script), run_name="__main__")
    finally:
        sys.argv = previous_argv
        sys.path[:] = previous_path
        os.chdir(previous_cwd)

    raw_path = workspace / "crawler_output" / config["raw"]
    count = 0
    if raw_path.exists():
        with raw_path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        count = len(raw) if isinstance(raw, list) else 0
    emit(platform=args.platform, phase="采集完成，准备完整性检查", processed=count, total=count)

    snapshot_script = Path(__file__).with_name("snapshot_pipeline.py")
    if snapshot_script.exists():
        previous_argv = sys.argv[:]
        try:
            sys.argv = [str(snapshot_script), "--workspace", str(workspace), "--platform", args.platform, "--source-root", str(source_root)]
            runpy.run_path(str(snapshot_script), run_name="__main__")
        finally:
            sys.argv = previous_argv


def main() -> int:
    args = parse_args()
    try:
        run_selected_collector(args)
        return 0
    except KeyboardInterrupt:
        emit(phase="已取消")
        return 130
    except Exception as error:  # noqa: BLE001 - process boundary must report the real reason
        print(f"desktop collector error: {error}", file=sys.stderr, flush=True)
        emit(phase="失败", error=str(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

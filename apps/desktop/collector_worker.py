"""Run one existing collector inside an isolated desktop update workspace.

The worker deliberately executes a single explicit platform. It never invokes the
monolithic crawler with ``--auto-convert`` and writes only below ``workspace``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import runpy
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


PLATFORMS = {
    "mcmod": {"script": "mcmod_full_crawler.py", "raw": "mcmod_modpacks.json", "sidecar": "mcmod_data.js", "result": "desktop_collection_result.json"},
    "bilibili": {"script": "bilibili_crawler.py", "raw": "bilibili_modpacks.json", "sidecar": "bili_data.js", "result": "desktop_collection_result.json"},
    "bbsmc": {"script": "bbsmc_crawler.py", "raw": "bbsmc_modpacks.json", "sidecar": "bbsmc_data.js", "result": "desktop_collection_result.json"},
    "xyebbs": {"script": "xyebbs_crawler.py", "raw": "xyebbs_modpacks.json", "sidecar": "xyebbs_data.js", "result": "desktop_collection_result.json"},
    "modrinth": {"script": "modrinth_crawler.py", "raw": "modrinth_modpacks.json", "sidecar": "modrinth_data.js", "result": "desktop_collection_result.json"},
    "curseforge": {"script": "curseforge_full_crawler.py", "raw": "curseforge_modpacks.json", "sidecar": "curseforge_data.js", "result": "desktop_collection_result.json"},
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


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_state(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"exists": False, "size": 0, "mtimeNs": None, "sha256": None}
    stat = path.stat()
    return {"exists": True, "size": stat.st_size, "mtimeNs": stat.st_mtime_ns, "sha256": sha256(path)}


def parse_sidecar(path: Path) -> list[object]:
    text = path.read_text(encoding="utf-8-sig").strip()
    if "=" not in text:
        raise ValueError(f"sidecar assignment missing: {path.name}")
    payload = text.split("=", 1)[1].strip()
    if payload.endswith(";"):
        payload = payload[:-1].strip()
    value = json.loads(payload)
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return list(value.values())
    raise ValueError(f"sidecar 顶层不是数组或对象: {path.name}")


def read_collection_result(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("crawler result 顶层不是对象")
    return value


def write_update_contract(workspace: Path, contract: dict[str, object]) -> None:
    path = workspace / "build" / "desktop_update_result.json"
    temp = path.with_suffix(f".{os.getpid()}.tmp")
    temp.write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def collect_output_contract(
    workspace: Path,
    platform: str,
    started_ns: int,
    before: dict[str, dict[str, object]],
    crawler_error: str | None = None,
) -> dict[str, object]:
    config = PLATFORMS[platform]
    raw_path = workspace / "crawler_output" / config["raw"]
    sidecar_path = workspace / "converted_output" / "data" / config["sidecar"]
    result_path = workspace / "build" / config["result"]
    raw_state = file_state(raw_path)
    sidecar_state = file_state(sidecar_path)
    result_state = file_state(result_path)
    raw_touched = bool(raw_state["exists"] and int(raw_state["mtimeNs"] or 0) >= started_ns)
    sidecar_touched = bool(sidecar_state["exists"] and int(sidecar_state["mtimeNs"] or 0) >= started_ns)
    result_touched = bool(result_state["exists"] and int(result_state["mtimeNs"] or 0) >= started_ns)
    raw_count = 0
    sidecar_count = 0
    crawler_result: dict[str, object] | None = None
    failure_reason = None
    try:
        if crawler_error:
            raise ValueError(f"crawler 执行失败: {crawler_error}")
        if not result_state["exists"] or not result_touched:
            raise ValueError("本轮没有生成 crawler 采集结果合同")
        crawler_result = read_collection_result(result_path)
        if crawler_result.get("platform") != platform:
            raise ValueError("crawler 采集结果合同的平台不匹配")
        if crawler_result.get("status") not in {"success", "success_no_change"}:
            raise ValueError(f"crawler 报告本轮结果为 {crawler_result.get('status') or 'unknown'}")
        if not crawler_result.get("requestCompleted"):
            raise ValueError("crawler 未确认请求/分页完整完成")
        if crawler_result.get("truncated"):
            raise ValueError("crawler 报告本轮分页被截断")
        if int(crawler_result.get("failedRequests") or 0) > 0:
            raise ValueError("crawler 报告存在失败请求")
        fetched_count = int(crawler_result.get("fetchedCount") or 0)
        if fetched_count <= 0 and not crawler_result.get("noChangeConfirmed"):
            raise ValueError("crawler 未获取到当前结果，也未确认有效无变化")
        if not raw_state["exists"]:
            raise ValueError("本轮没有生成原始 JSON")
        raw_value = json.loads(raw_path.read_text(encoding="utf-8"))
        if not isinstance(raw_value, list):
            raise ValueError("本轮原始 JSON 不是数组")
        raw_count = len(raw_value)
        if not raw_count:
            raise ValueError("本轮原始 JSON 为空")
        if not sidecar_state["exists"]:
            raise ValueError("本轮没有生成现代 sidecar")
        sidecar_count = len(parse_sidecar(sidecar_path))
        if not sidecar_count:
            raise ValueError("本轮现代 sidecar 为空")
        if crawler_result.get("status") != "success_no_change" and (not raw_touched or not sidecar_touched):
            raise ValueError("原始 JSON 或现代 sidecar 未在本轮采集期间写入")
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        failure_reason = str(error)

    changed = any(before[name].get("sha256") != after.get("sha256") for name, after in {"raw": raw_state, "sidecar": sidecar_state}.items())
    outcome = "success_update" if not failure_reason and changed else "success_no_change" if not failure_reason else "failed"
    return {
        "schema": 1,
        "platform": platform,
        "startedAt": datetime.fromtimestamp(started_ns / 1_000_000_000, timezone.utc).isoformat(),
        "finishedAt": datetime.now(timezone.utc).isoformat(),
        "rawFile": config["raw"],
        "sidecarFile": config["sidecar"],
        "raw": raw_state,
        "sidecar": sidecar_state,
        "collectionResult": result_state,
        "crawlerResult": crawler_result,
        "rawTouched": raw_touched,
        "sidecarTouched": sidecar_touched,
        "collectionResultTouched": result_touched,
        "rawCount": raw_count,
        "sidecarCount": sidecar_count,
        "changed": changed,
        "outcome": outcome,
        "error": failure_reason,
    }


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
    helper_source = source_root / "desktop_collection_contract.py"
    if not helper_source.exists():
        raise FileNotFoundError(f"collector contract helper not found: {helper_source}")
    shutil.copy2(helper_source, isolated_script.parent / helper_source.name)

    script_args = build_script_args(args.platform, args)
    emit(platform=args.platform, phase="采集", processed=0, total=None)
    print(f"desktop collector: {args.platform} args={script_args}", flush=True)

    output_paths = {
        "raw": workspace / "crawler_output" / config["raw"],
        "sidecar": workspace / "converted_output" / "data" / config["sidecar"],
        "result": workspace / "build" / config["result"],
    }
    before = {name: file_state(path) for name, path in output_paths.items()}
    started_ns = time.time_ns()

    previous_cwd = Path.cwd()
    previous_argv = sys.argv[:]
    previous_path = sys.path[:]
    previous_workspace = os.environ.get("MC_DESKTOP_WORKSPACE")
    previous_result_path = os.environ.get("MC_DESKTOP_COLLECTION_RESULT")
    crawler_error = None
    try:
        os.chdir(workspace)
        sys.path.insert(0, str(isolated_script.parent))
        sys.argv = [str(isolated_script), *script_args]
        os.environ["MC_DESKTOP_WORKSPACE"] = str(workspace)
        os.environ["MC_DESKTOP_COLLECTION_RESULT"] = str(workspace / "build" / config["result"])
        try:
            runpy.run_path(str(isolated_script), run_name="__main__")
        except SystemExit as error:
            if error.code not in (None, 0):
                crawler_error = f"SystemExit({error.code})"
        except Exception as error:  # noqa: BLE001 - report the crawler boundary
            crawler_error = str(error)
    finally:
        sys.argv = previous_argv
        sys.path[:] = previous_path
        os.chdir(previous_cwd)
        if previous_workspace is None:
            os.environ.pop("MC_DESKTOP_WORKSPACE", None)
        else:
            os.environ["MC_DESKTOP_WORKSPACE"] = previous_workspace
        if previous_result_path is None:
            os.environ.pop("MC_DESKTOP_COLLECTION_RESULT", None)
        else:
            os.environ["MC_DESKTOP_COLLECTION_RESULT"] = previous_result_path

    contract = collect_output_contract(workspace, args.platform, started_ns, before, crawler_error)
    write_update_contract(workspace, contract)
    if contract["outcome"] == "failed":
        emit(platform=args.platform, phase="失败", processed=contract["rawCount"], total=contract["rawCount"], error=contract["error"])
        raise RuntimeError(str(contract["error"]))

    count = int(contract["rawCount"])
    emit(platform=args.platform, phase="采集完成，准备完整性检查", processed=count, total=count, outcome=contract["outcome"])

    snapshot_script = Path(__file__).with_name("snapshot_pipeline.py")
    if snapshot_script.exists():
        previous_argv = sys.argv[:]
        try:
            sys.argv = [str(snapshot_script), "--workspace", str(workspace), "--platform", args.platform, "--source-root", str(source_root)]
            try:
                runpy.run_path(str(snapshot_script), run_name="__main__")
            except SystemExit as error:
                if error.code not in (None, 0):
                    raise
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

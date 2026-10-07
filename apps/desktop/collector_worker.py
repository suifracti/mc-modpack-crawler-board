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
    # Leave unset unless the caller explicitly limits pages. Platform modes
    # choose their own safe defaults (including the 200-page CF catalog cap).
    parser.add_argument("--pages", type=int, default=None)
    parser.add_argument("--until", default=None)
    parser.add_argument("--mode", default=None)
    parser.add_argument("--cover-offset", type=int, default=None)
    parser.add_argument("--bv", default=None)
    parser.add_argument("--html-state", default=None)
    return parser.parse_args()


def build_script_args(platform: str, args: argparse.Namespace) -> list[str]:
    limit = args.limit
    if platform == "bilibili":
        mode = getattr(args,"mode",None)
        result = ["--mode", "catalog" if mode=="catalog" else "existing" if mode=="existing" else "new",
                  "--limit", str(min(limit or (5000 if mode=="catalog" else 3), 5000 if mode=="catalog" else 30)), "--html-state", str(args.html_state)]
        if getattr(args, "bv", None):
            result.extend(["--bv", args.bv])
        if getattr(args, "until", None):
            result.extend(["--until", args.until])
        return result
    if getattr(args, "mode", None) == "existing" and platform != "mcmod":
        return ["--platform", platform, "--limit", str(limit or 50)]
    if platform == "mcmod":
        mode = getattr(args, "mode", None) or "new"
        result = ["--mode", mode]
        if limit:
            result.extend(["--limit", str(limit)])
        elif mode == "covers":
            result.extend(["--limit", "20"])
        if mode == "covers":
            result.append("--force")
        cover_offset = getattr(args, "cover_offset", None)
        if cover_offset is not None and mode == "covers":
            result.extend(["--cover-offset", str(cover_offset)])
        return result
    if platform == "bbsmc":
        return ["--type", "modpack", "--max", str(limit or 0), "--enrich", str(limit or 100000)] + (["--daily"] if getattr(args,"mode",None)=="daily" else [])
    if platform == "xyebbs":
        return ["--max", str(limit or 0), "--enrich", str(limit or 100000)] + (["--daily"] if getattr(args,"mode",None)=="daily" else [])
    if platform == "modrinth":
        return ["--max", str(limit or 0)] + (["--daily"] if getattr(args,"mode",None)=="daily" else [])
    if platform == "curseforge":
        config_root = str(Path(getattr(args, "source_root", Path(__file__).resolve().parents[2])).resolve())
        sys.path.insert(0, config_root)
        try:
            from curseforge_api_config import metadata_provider
            provider = metadata_provider()
        finally:
            sys.path.pop(0)
        if getattr(args,"mode",None)=="metadata":
            if provider!="cfwidget":raise ValueError('Public project details require the explicitly selected no-key provider')
            return ["--max",str(limit or 0),"--public-details"]
        mode=getattr(args,"mode",None)
        public = ["--public-catalog"] if provider == "cfwidget" and mode in {None,"new","catalog","recent"} else []
        if mode in {None,"new"}:
            return ["--max","0","--recent-pages",str(args.pages or 2)]+public
        if getattr(args, "mode", None) == "recent":
            return ["--max", "0", "--recent-pages", str(args.pages or 20)] + public
        if mode == "catalog":
            return ["--max", str(limit or 0), "--recent-pages", str(args.pages or 200)] + public
        return ["--max", str(limit or 0)] + public
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


def merge_catalog_with_existing(workspace: Path, platform: str, previous: list[dict]) -> None:
    """A list refresh must not erase release details or drop previously known IDs."""
    config = PLATFORMS[platform]
    raw_path = workspace / "crawler_output" / config["raw"]
    sidecar_path = workspace / "converted_output" / "data" / config["sidecar"]
    with raw_path.open(encoding="utf-8") as handle:
        current = json.load(handle)
    if not isinstance(current, list):
        return
    key = "bvid" if platform == "bilibili" else "project_id"
    old_by_id = {str(item.get(key)): item for item in previous if isinstance(item, dict) and item.get(key)}
    seen = set()
    keep_fields = (
        "releases", "versions_data", "releases_data", "version_checked_at", "latest_version",
        "desc_checked_at", "source_unavailable", "pack_version", "group_version_note",
    )
    for item in current:
        ident = str(item.get(key) or "")
        seen.add(ident)
        old = old_by_id.get(ident)
        if not old:
            continue
        history_fields = ("releases", "versions_data", "releases_data")
        fresh_history = next((item[field] for field in history_fields
                              if isinstance(item.get(field), list) and item[field]), None)
        if fresh_history:
            # The catalog producers use different history field names. Never
            # let a retained old `releases`/latest_version hide fresh versions.
            old_history = next((old[field] for field in history_fields
                                if isinstance(old.get(field), list) and old[field]), [])
            def release_name(release):
                return str(next((release.get(k) for k in ("version_number", "versionName", "label", "name")
                                 if release.get(k)), ""))
            fresh_names = {release_name(release) for release in fresh_history}
            item["releases"] = fresh_history + [release for release in old_history
                                               if release_name(release) not in fresh_names]
            latest = release_name(fresh_history[0])
            if latest:
                item["latest_version"] = latest
        for field in keep_fields:
            if fresh_history and field in (*history_fields, "latest_version", "pack_version", "version_checked_at"):
                continue
            if old.get(field) and not item.get(field):
                item[field] = old[field]
        if platform == "bilibili":
            for field, observed in (("desc", "desc_observed"), ("pinned_comment", "pinned_comment_observed")):
                if old.get(field) and not item.get(observed):
                    item[field] = old[field]
    retained = [item for ident, item in old_by_id.items() if ident not in seen]
    if retained:
        print(f"desktop merge: {platform} kept {len(retained)} older records absent from this listing", flush=True)
        current.extend(retained)
    sidecar_text = sidecar_path.read_text(encoding="utf-8").strip()
    if "=" not in sidecar_text:
        raise ValueError("平台 sidecar 缺少赋值前缀，拒绝合并")
    prefix = sidecar_text.split("=", 1)[0] + "= "
    for path, content in (
        (raw_path, json.dumps(current, ensure_ascii=False, indent=2) + "\n"),
        (sidecar_path, prefix + json.dumps(current, ensure_ascii=False, separators=(",", ":")) + ";\n"),
    ):
        temp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
        temp.write_text(content, encoding="utf-8")
        temp.replace(path)


def collect_output_contract(
    workspace: Path,
    platform: str,
    started_ns: int,
    before: dict[str, dict[str, object]],
    crawler_error: str | None = None,
    allow_existing_partial: bool = False,
    allow_mcmod_partial: bool = False,
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
            if platform == "bilibili" and result_state["exists"] and result_touched:
                attempted = read_collection_result(result_path)
                if (attempted.get("details") or {}).get("coverage") == "public-video-html-bounded":
                    crawler_result = attempted
                    reasons = attempted.get("errors") or []
                    raise ValueError("HTML局部更新未完成：" + "; ".join(str(value) for value in reasons or [crawler_error]))
            raise ValueError(f"crawler 执行失败: {crawler_error}")
        if not result_state["exists"] or not result_touched:
            raise ValueError("本轮没有生成 crawler 采集结果合同")
        crawler_result = read_collection_result(result_path)
        if crawler_result.get("platform") != platform:
            raise ValueError("crawler 采集结果合同的平台不匹配")
        truncated_catalog_allowed = platform == "curseforge" and not allow_existing_partial and not allow_mcmod_partial
        details = crawler_result.get("details") or {}
        verified_catalog_partial = (platform in {"bbsmc", "xyebbs", "modrinth"}
                                    and details.get("catalogCompleted") is True
                                    and int(details.get("versionsChecked") or 0) > 0
                                    and not details.get("sourceStopped")
                                    and int(details.get("versionParseFailures") or 0) == 0)
        partial_allowed = ((verified_catalog_partial or platform in {"bilibili", "curseforge"} or allow_existing_partial or allow_mcmod_partial)
                           and crawler_result.get("status") == "partial"
                           and int(crawler_result.get("fetchedCount") or 0) > 0
                           and (not crawler_result.get("truncated") or truncated_catalog_allowed))
        if crawler_result.get("status") not in {"success", "success_no_change"} and not partial_allowed:
            raise ValueError(f"crawler 报告本轮结果为 {crawler_result.get('status') or 'unknown'}；" + "; ".join(str(value) for value in (crawler_result.get("errors") or [])[:3]))
        if not crawler_result.get("requestCompleted") and not partial_allowed:
            raise ValueError("crawler 未确认请求/分页完整完成")
        if crawler_result.get("truncated") and not truncated_catalog_allowed:
            raise ValueError("crawler 报告本轮分页被截断")
        if int(crawler_result.get("failedRequests") or 0) > 0 and not partial_allowed:
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
    html_partial = bool(platform == "bilibili" and crawler_result and
                        (crawler_result.get("details") or {}).get("coverage") == "public-video-html-bounded")
    outcome = ("partial_update" if not failure_reason and (changed or html_partial) and crawler_result and crawler_result.get("status") == "partial"
               else "success_update" if not failure_reason and changed else "success_no_change" if not failure_reason else "failed")
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
        "partialScope": ("public-video-html-bounded" if html_partial else "mcmod_refresh" if allow_mcmod_partial else "existing" if allow_existing_partial else "catalog") if outcome == "partial_update" else None,
        "error": failure_reason,
    }


def run_selected_collector(args: argparse.Namespace) -> None:
    workspace = Path(args.workspace).resolve()
    source_root = Path(args.source_root).resolve()
    config = PLATFORMS[args.platform]
    source_name = "existing_version_crawler.py" if args.mode == "existing" and args.platform not in ("mcmod", "bilibili") else config["script"]
    if args.platform == "bilibili":
        source_name = "bilibili_public_html_collector.py"
        if not getattr(args, "html_state", None):
            args.html_state = str(workspace.parent.parent / "collector-state" / "bilibili-public-html-state.json")
    source_script = source_root / source_name
    if not source_script.exists():
        raise FileNotFoundError(f"collector source not found: {source_script}")

    ensure_stage_dirs(workspace)
    isolated_script = workspace / "_collector" / source_name
    isolated_script.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_script, isolated_script)
    helper_source = source_root / "desktop_collection_contract.py"
    if not helper_source.exists():
        raise FileNotFoundError(f"collector contract helper not found: {helper_source}")
    shutil.copy2(helper_source, isolated_script.parent / helper_source.name)
    if source_name == "existing_version_crawler.py":
        # Existing-version CF requests share the source-wide refusal guard.
        shutil.copy2(source_root / "curseforge_full_crawler.py", isolated_script.parent / "curseforge_full_crawler.py")
    if source_name in {"existing_version_crawler.py", "curseforge_full_crawler.py"}:
        shutil.copy2(source_root / "curseforge_api_config.py", isolated_script.parent / "curseforge_api_config.py")
        shutil.copy2(source_root / "curseforge_cfwidget.py", isolated_script.parent / "curseforge_cfwidget.py")
        shutil.copy2(source_root / "curseforge_modpacks_ch.py", isolated_script.parent / "curseforge_modpacks_ch.py")
        shutil.copy2(source_root / "verified_tls.py", isolated_script.parent / "verified_tls.py")

    if args.platform in {"bbsmc", "xyebbs"}:
        shutil.copy2(source_root / "public_api_transport.py", isolated_script.parent / "public_api_transport.py")
    if args.platform in {"bbsmc", "xyebbs", "modrinth"}:
        shutil.copy2(source_root / "verified_tls.py", isolated_script.parent / "verified_tls.py")
        shutil.copy2(source_root / "catalog_refresh_policy.py", isolated_script.parent / "catalog_refresh_policy.py")

    if args.platform == "bilibili":
        for helper in ("bilibili_html_adapter.py", "bilibili_html_extract.py", "verified_tls.py"):
            shutil.copy2(source_root / helper, isolated_script.parent / helper)
        # Keep the same content policy in the isolated HTML worker as public browsing.
        rules = source_root / "bilibili-content-rules.json"
        if not rules.is_file():
            rules = source_root / "apps" / "shared" / "bilibili-content-rules.json"
        shutil.copy2(rules, isolated_script.parent / "bilibili-content-rules.json")

    script_args = build_script_args(args.platform, args)
    emit(platform=args.platform, phase="采集", processed=0, total=None)
    print(f"desktop collector: {args.platform} args={script_args}", flush=True)

    output_paths = {
        "raw": workspace / "crawler_output" / config["raw"],
        "sidecar": workspace / "converted_output" / "data" / config["sidecar"],
        "result": workspace / "build" / config["result"],
    }
    before = {name: file_state(path) for name, path in output_paths.items()}
    old_records = []
    if output_paths["raw"].exists():
        with output_paths["raw"].open(encoding="utf-8") as handle:
            old_records = json.load(handle)
    started_ns = time.time_ns()

    previous_cwd = Path.cwd()
    previous_argv = sys.argv[:]
    previous_path = sys.path[:]
    previous_workspace = os.environ.get("MC_DESKTOP_WORKSPACE")
    previous_result_path = os.environ.get("MC_DESKTOP_COLLECTION_RESULT")
    previous_cf_checkpoint = os.environ.get("MC_CF_PUBLIC_CATALOG_CHECKPOINT")
    previous_bili_proof_dir = os.environ.get("MC_BILIBILI_TLS_STOP_PROOF_DIR")
    crawler_error = None
    try:
        os.chdir(workspace)
        sys.path.insert(0, str(isolated_script.parent))
        sys.argv = [str(isolated_script), *script_args]
        os.environ["MC_DESKTOP_WORKSPACE"] = str(workspace)
        os.environ["MC_DESKTOP_COLLECTION_RESULT"] = str(workspace / "build" / config["result"])
        if args.platform == "curseforge" and "--public-catalog" in script_args:
            data_root = workspace.parent.parent if workspace.parent.name == "incoming" else workspace
            checkpoint = (data_root / "collector-state" / "curseforge-public-catalog-v2" / "checkpoint.json"
                          if args.mode == "catalog" else data_root / "collector-state" /
                          "curseforge-public-catalog-recent-v2" / f"{workspace.name}-checkpoint.json")
            os.environ["MC_CF_PUBLIC_CATALOG_CHECKPOINT"] = str(
                checkpoint
            )
        if args.platform == "bilibili":
            data_root = workspace.parent.parent if workspace.parent.name == "incoming" else workspace
            os.environ["MC_BILIBILI_TLS_STOP_PROOF_DIR"] = str(
                data_root / "collector-state" / "update-results"
            )
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
        if previous_cf_checkpoint is None:
            os.environ.pop("MC_CF_PUBLIC_CATALOG_CHECKPOINT", None)
        else:
            os.environ["MC_CF_PUBLIC_CATALOG_CHECKPOINT"] = previous_cf_checkpoint
        if previous_bili_proof_dir is None:
            os.environ.pop("MC_BILIBILI_TLS_STOP_PROOF_DIR", None)
        else:
            os.environ["MC_BILIBILI_TLS_STOP_PROOF_DIR"] = previous_bili_proof_dir

    if crawler_error is None and old_records and args.mode != "existing" and args.platform not in {"mcmod", "bilibili"}:
        merge_catalog_with_existing(workspace, args.platform, old_records)
    previous_ids_preserved = not old_records
    if old_records:
        key = "bvid" if args.platform == "bilibili" else "project_id"
        with output_paths["raw"].open(encoding="utf-8") as handle:
            merged = json.load(handle)
        old_ids = {str(item.get(key)) for item in old_records if item.get(key)}
        new_ids = {str(item.get(key)) for item in merged if item.get(key)}
        previous_ids_preserved = old_ids.issubset(new_ids)
        if not previous_ids_preserved:
            raise ValueError(f"{args.platform} 合并后遗失旧 ID，拒绝提交")
    contract = collect_output_contract(workspace, args.platform, started_ns, before, crawler_error,
                                       allow_existing_partial=args.mode == "existing" and args.platform != "mcmod",
                                       allow_mcmod_partial=args.platform == "mcmod" and args.mode in {"all", "metrics", "trend", "covers", "versions"})
    contract["previousIdsPreserved"] = previous_ids_preserved
    write_update_contract(workspace, contract)
    if contract["outcome"] == "failed":
        # The runner removes its temporary stage. Retain the small result
        # contract so a rejected update can still be diagnosed afterwards.
        diagnostic_dir = workspace.parent.parent / "collector-state" / "update-results"
        diagnostic_dir.mkdir(parents=True, exist_ok=True)
        diagnostic_path = diagnostic_dir / f"{workspace.name}.json"
        with os.fdopen(os.open(diagnostic_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w", encoding="utf-8") as handle:
            json.dump(contract, handle, ensure_ascii=False, indent=2)
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
    # Both desktop runners decode stdout as UTF-8, independent of Windows locale.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
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

"""Small, packaging-friendly snapshot integrity step for the desktop app.

The desktop update path never calls a production cutover. When all six raw
snapshots are present, this module also builds a canonical SQLite copy in the
isolated workspace. With a partial local import, it records why canonical data
is unavailable while preserving the valid sidecars and the previous snapshot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


PLATFORMS = {
    "mcmod": ("mcmod_modpacks.json", ("mcmod_data.js", "table_rows.js", "app_data.js")),
    "bilibili": ("bilibili_modpacks.json", ("bili_data.js",)),
    "bbsmc": ("bbsmc_modpacks.json", ("bbsmc_data.js",)),
    "xyebbs": ("xyebbs_modpacks.json", ("xyebbs_data.js",)),
    "modrinth": ("modrinth_modpacks.json", ("modrinth_data.js",)),
    "curseforge": ("curseforge_modpacks.json", ("curseforge_data.js",)),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_sidecar(path: Path) -> list[object]:
    text = path.read_text(encoding="utf-8-sig").strip()
    if "=" not in text:
        raise ValueError(f"sidecar assignment missing: {path.name}")
    payload = text.split("=", 1)[1].strip()
    if payload.endswith(";"):
        payload = payload[:-1].strip()
    parsed = json.loads(payload)
    return parsed if isinstance(parsed, list) else list(parsed.values())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--platform", choices=sorted(PLATFORMS), required=True)
    parser.add_argument("--source-root", default="")
    args = parser.parse_args()
    workspace = Path(args.workspace).resolve()
    raw_dir = workspace / "crawler_output"
    data_dir = workspace / "converted_output" / "data"
    result_path = workspace / "build" / "desktop_update_result.json"
    if not result_path.exists():
        raise ValueError("缺少本轮采集结果合同，拒绝把旧 sidecar 视为成功")
    update_result = json.loads(result_path.read_text(encoding="utf-8"))
    if update_result.get("platform") != args.platform:
        raise ValueError("本轮采集结果合同的平台不匹配")
    if update_result.get("outcome") not in {"success_update", "success_no_change"}:
        raise ValueError("本轮采集未形成成功结果，拒绝生成快照")
    crawler_result = update_result.get("crawlerResult") or {}
    if crawler_result.get("status") != "success_no_change" and (
        not update_result.get("rawTouched") or not update_result.get("sidecarTouched")
    ):
        raise ValueError("本轮原始 JSON 或现代 sidecar 未实际写入")
    raw_meta: dict[str, object] = {}
    all_raw = True
    for platform, (raw_name, sidecars) in PLATFORMS.items():
        raw_path = raw_dir / raw_name
        sidecar = next((data_dir / name for name in sidecars if (data_dir / name).exists()), None)
        if not raw_path.exists():
            all_raw = False
            raw_meta[platform] = {"raw": False, "sidecar": bool(sidecar)}
            continue
        raw_value = json.loads(raw_path.read_text(encoding="utf-8"))
        if not isinstance(raw_value, list):
            raise ValueError(f"raw snapshot must be a list: {raw_name}")
        if sidecar is None:
            raise ValueError(f"raw snapshot has no sidecar: {platform}")
        sidecar_value = parse_sidecar(sidecar)
        raw_meta[platform] = {
            "raw": True,
            "rawCount": len(raw_value),
            "sidecar": sidecar.name,
            "sidecarCount": len(sidecar_value),
            "rawSha256": sha256(raw_path),
            "sidecarSha256": sha256(sidecar),
        }

    canonical_ready = False
    canonical_reason = "partial raw inputs; sidecar snapshot remains valid"
    if all_raw:
        source_root = Path(args.source_root).resolve() if args.source_root else Path(__file__).resolve().parents[2]
        sys.path.insert(0, str(source_root))
        try:
            import pipeline.build_canonical_db as canonical_builder

            # The existing builder derives adapter paths from PROJECT_ROOT. Point
            # that one module-level root at the isolated workspace before calling
            # it; no repository or production output is touched.
            canonical_builder.PROJECT_ROOT = str(workspace)
            canonical_builder.build_canonical_db(str(workspace / "build" / "canonical.db"), recreate=True)
            canonical_ready = True
            canonical_reason = "all six raw inputs validated and canonical SQLite built in isolation"
        except Exception as error:  # noqa: BLE001 - preserve the actual integrity failure
            raise RuntimeError(f"canonical build failed in isolated workspace: {error}") from error

    manifest = {
        "schema": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "platform": args.platform,
        "canonicalReady": canonical_ready,
        "canonicalReason": canonical_reason,
        "updateResult": update_result,
        "platforms": raw_meta,
    }
    output = workspace / "build" / "desktop_snapshot_manifest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("DESKTOP_EVENT " + json.dumps({"phase": "完整性检查完成", "processed": raw_meta.get(args.platform, {}).get("rawCount", 0), "total": raw_meta.get(args.platform, {}).get("rawCount", 0)}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

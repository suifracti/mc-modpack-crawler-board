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
import sqlite3
from contextlib import closing
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


def can_reuse_canonical(db_path, raw_meta, changed_platform, builder):
    """Reuse only verified provenance; old schema/code or other input drift rebuilds."""
    if not db_path.is_file():
        return False
    try:
        with closing(sqlite3.connect(db_path.as_uri() + '?mode=ro', uri=True)) as conn:
            row = conn.execute("SELECT value FROM canonical_build_meta WHERE key='pipelineFingerprint'").fetchone()
            if not row or row[0] != builder.pipeline_fingerprint():
                return False
            if conn.execute('PRAGMA quick_check').fetchone()[0] != 'ok' or conn.execute('PRAGMA foreign_key_check').fetchone():
                return False
            for platform, meta in raw_meta.items():
                if platform == changed_platform:
                    continue
                prior = conn.execute('''SELECT r.content_hash, r.record_count FROM raw_snapshot_refs r
                    JOIN ingest_runs i ON i.run_id=r.run_id WHERE r.platform=? AND i.status='completed'
                    ORDER BY r.id DESC LIMIT 1''', (platform,)).fetchone()
                ids = conn.execute('SELECT value FROM canonical_build_meta WHERE key=?', ('sourceIds:' + platform,)).fetchone()
                if not prior or prior != (meta['rawSha256'], meta['rawCount']) or not ids or ids[0] != builder.source_id_fingerprint(conn, platform):
                    return False
            return True
    except sqlite3.Error:
        return False


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
    if update_result.get("outcome") not in {"success_update", "success_no_change", "partial_update"}:
        raise ValueError("本轮采集未形成成功结果，拒绝生成快照")
    crawler_result = update_result.get("crawlerResult") or {}
    if crawler_result.get("status") != "success_no_change" and (
        not update_result.get("rawTouched") or not update_result.get("sidecarTouched")
    ):
        raise ValueError("本轮原始 JSON 或现代 sidecar 未实际写入")
    raw_meta: dict[str, object] = {}
    prior_manifest = workspace / 'build/desktop_snapshot_manifest.json'
    prior_meta = {}
    if prior_manifest.is_file():
        try:
            prior = json.loads(prior_manifest.read_text(encoding='utf-8'))
            if prior.get('canonicalReady') is True:
                prior_meta = prior.get('platforms') or {}
        except (ValueError, TypeError):
            pass
    all_raw = True
    for platform, (raw_name, sidecars) in PLATFORMS.items():
        raw_path = raw_dir / raw_name
        sidecar = next((data_dir / name for name in sidecars if (data_dir / name).exists()), None)
        if not raw_path.exists():
            all_raw = False
            raw_meta[platform] = {"raw": False, "sidecar": bool(sidecar)}
            continue
        if sidecar is None:
            raise ValueError(f"raw snapshot has no sidecar: {platform}")
        raw_hash = sha256(raw_path)
        sidecar_hash = sha256(sidecar)
        cached = prior_meta.get(platform) or {}
        unchanged = (platform != args.platform and cached.get('rawSha256') == raw_hash
                     and cached.get('sidecarSha256') == sidecar_hash
                     and type(cached.get('rawCount')) is int and cached['rawCount'] > 0
                     and type(cached.get('sidecarCount')) is int and cached['sidecarCount'] > 0)
        if unchanged:
            raw_count, sidecar_count = cached['rawCount'], cached['sidecarCount']
        else:
            raw_value = json.loads(raw_path.read_text(encoding="utf-8"))
            if not isinstance(raw_value, list):
                raise ValueError(f"raw snapshot must be a list: {raw_name}")
            raw_count = len(raw_value)
            sidecar_count = len(parse_sidecar(sidecar))
        raw_meta[platform] = {
            "raw": True,
            "rawCount": raw_count,
            "sidecar": sidecar.name,
            "sidecarCount": sidecar_count,
            "rawSha256": raw_hash,
            "sidecarSha256": sidecar_hash,
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
            db_path = workspace / 'build/canonical.db'
            reuse = can_reuse_canonical(db_path, raw_meta, args.platform, canonical_builder)
            canonical_builder.build_canonical_db(str(db_path), recreate=not reuse,
                                                  platforms=[args.platform] if reuse else None)
            canonical_ready = True
            canonical_reason = ("all six inputs validated; unchanged platforms reused, selected platform rebuilt in isolation"
                                if reuse else "all six raw inputs validated and canonical SQLite built in isolation")
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

"""Bounded, resumable release refresh for already-collected non-MCMod packs."""
import argparse
import json
import os
import sqlite3
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from desktop_collection_contract import write_collection_result
from verified_tls import get_verified_context
from curseforge_full_crawler import request_api_json as request_cf_json, AccessRefusal
from curseforge_api_config import api_url as cf_api_url, metadata_provider
from curseforge_cfwidget import get_project as get_widget_project, project_releases, merge_releases, WidgetRefusal


CONFIG = {
    "bbsmc": ("bbsmc_modpacks.json", "bbsmc_data.js", "window.bbsmcModpacksData = "),
    "xyebbs": ("xyebbs_modpacks.json", "xyebbs_data.js", "window.xyebbsModpacksData = "),
    "modrinth": ("modrinth_modpacks.json", "modrinth_data.js", "window.modrinthModpacksData = "),
    "curseforge": ("curseforge_modpacks.json", "curseforge_data.js", "window.curseforgeModpacksData = "),
}
HEADERS = {"User-Agent": "MCModpackBoard/0.1 (local release refresh)", "Accept": "application/json"}


def request_json(url):
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=15, context=get_verified_context()) as response:
                if response.status != 200:
                    raise ValueError(f"HTTP {response.status}")
                return json.load(response)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(1.5 * (attempt + 1))


def fetch_releases(platform, project_id):
    ident = urllib.parse.quote(str(project_id), safe="")
    if platform == "bbsmc":
        data = request_json(f"https://api.bbsmc.net/v2/project/{ident}/version")
        if not isinstance(data, list):
            raise ValueError("BBSMC 版本接口未返回列表")
        return [{"version_number": item.get("version_number") or item.get("name") or "",
                 "date_published": item.get("date_published") or "",
                 "changelog": item.get("changelog") or "",
                 "game_versions": item.get("game_versions") or [],
                 "loaders": item.get("loaders") or [],
                 "files": [{"name": file.get("filename") or "下载", "url": file.get("url")}
                           for file in item.get("files") or [] if file.get("url")]}
                for item in data]
    if platform == "xyebbs":
        data = request_json(f"https://resource-api.xyeidc.com/client/resources/{ident}/releases?includes=links")
        inner = data.get("data") if isinstance(data, dict) else None
        releases = inner.get("data") if isinstance(inner, dict) else inner
        if not isinstance(releases, list):
            raise ValueError("XYEBBS 版本接口未返回列表")

        def _xyebbs_pan_name(l):
            lt = (l.get("linkType") or l.get("type") or "").upper()
            u = (l.get("url") or "").lower()
            if "QUARK" in lt or "quark.cn" in u: return "夸克网盘"
            if "BAIDU" in lt or "baidu.com" in u: return "百度网盘"
            if "123" in lt or "123pan" in u or "123684" in u: return "123云盘"
            if "LANZOU" in lt or "lanzou" in u: return "蓝奏云"
            if "XUNLEI" in lt or "xunlei.com" in u: return "迅雷网盘"
            raw = (l.get("name") or "").strip()
            return raw if raw and raw != "下载" else "网盘下载"

        def _format_xyebbs_release(item):
            v_name = item.get("label") or item.get("name") or "Release"
            raw_date = item.get("createDate") or ""
            date_str = str(raw_date)[:10] if raw_date else ""
            notes = (item.get("notes") or "").strip()
            links = [{
                "name": _xyebbs_pan_name(lk),
                "url": lk.get("url"),
                "type": lk.get("linkType"),
                "code": lk.get("info") or lk.get("code") or ""
            } for lk in item.get("links") or [] if lk.get("url")]
            return {
                "id": item.get("id"),
                "label": v_name,
                "name": v_name,
                "version_number": v_name,
                "createDate": raw_date,
                "date_published": raw_date,
                "date": date_str,
                "notes": notes,
                "changelog": notes,
                "downloads": item.get("downloadCount") or 0,
                "links": links,
                "files": links,
            }

        return [_format_xyebbs_release(item) for item in releases]
    if platform == "modrinth":
        data = request_json(f"https://api.modrinth.com/v2/project/{ident}/version")
        if not isinstance(data, list):
            raise ValueError("Modrinth 版本接口未返回列表")
        return [{"version_number": item.get("version_number") or item.get("name") or "",
                 "date_published": item.get("date_published") or "", "changelog": item.get("changelog") or "",
                 "game_versions": item.get("game_versions") or [], "loaders": item.get("loaders") or [],
                 "files": [{"name": file.get("filename") or "下载", "url": file.get("url")}
                           for file in item.get("files") or [] if file.get("url")]}
                for item in data]
    releases = []
    if metadata_provider() == 'cfwidget':
        project, observation = get_widget_project(project_id)
        return [{**release, 'provider_fetched_at': observation['fetchedAt'],
                 'provider_last_fetch': observation.get('providerLastFetch')}
                for release in project_releases(project)]
    page = 0
    while True:
        data = request_cf_json(cf_api_url(f'/v1/mods/{ident}/files', {'index':page * 50,'pageSize':50}), headers=HEADERS)
        files = data.get("data") if isinstance(data, dict) else None
        if not isinstance(files, list):
            raise ValueError("CurseForge 文件接口未返回列表")
        for item in files:
            releases.append({"version_number": item.get("displayName") or item.get("fileName") or "",
                             "date_published": item.get("fileDate") or "", "changelog": "",
                             "game_versions": item.get("gameVersions") or [],
                             "files": [{"name": item.get("fileName") or "下载", "url": item.get("downloadUrl")}] if item.get("downloadUrl") else []})
        pagination = data.get("pagination") or {}
        if len(files) < 50 or (pagination.get("totalCount") is not None and (page + 1) * 50 >= pagination["totalCount"]):
            break
        page += 1
    return releases


def atomic_json(path, content):
    temp = f"{path}.{os.getpid()}.tmp"
    with open(temp, "w", encoding="utf-8") as handle:
        handle.write(content)
    os.replace(temp, path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=sorted(CONFIG), required=True)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("旧包复查数量必须大于 0")
    root = os.environ.get("MC_DESKTOP_WORKSPACE")
    if not root or not os.environ.get("MC_DESKTOP_COLLECTION_RESULT"):
        parser.error("只能在桌面隔离工作区内执行旧包复查")
    raw_name, sidecar_name, prefix = CONFIG[args.platform]
    raw_path = os.path.join(root, "crawler_output", raw_name)
    sidecar_path = os.path.join(root, "converted_output", "data", sidecar_name)
    with open(raw_path, encoding="utf-8") as handle:
        raw = json.load(handle)
    with open(sidecar_path, encoding="utf-8") as handle:
        text = handle.read().strip()
    if not text.startswith(prefix):
        raise ValueError("旧包数据文件格式不符，拒绝覆写")
    sidecar = json.loads(text[len(prefix):].rstrip(";\n "))
    by_id = {str(item.get("project_id")): item for item in sidecar}
    if not raw or len(raw) != len(sidecar) or {str(item.get("project_id")) for item in raw} != set(by_id):
        raise ValueError("旧包原始记录与前端数据 ID 不一致，拒绝覆写")
    # Modrinth and CurseForge have large catalogs. Rewriting their entire
    # raw JSON and sidecar every 20 requests makes a full refresh impractical.
    # Keep successful details in a durable per-project journal and materialize
    # the two large files once, after the requested range finishes.
    journal = None
    replayed = 0
    journal_ids = set()
    if args.platform in {"modrinth", "curseforge"}:
        journal_path = os.path.join(root, "build", f"{args.platform}_release_progress.sqlite3")
        os.makedirs(os.path.dirname(journal_path), exist_ok=True)
        journal = sqlite3.connect(journal_path)
        journal.execute("CREATE TABLE IF NOT EXISTS completed (project_id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        raw_by_id = {str(item.get("project_id")): item for item in raw}
        for ident, payload_text in journal.execute("SELECT project_id, payload FROM completed"):
            target = by_id.get(ident)
            raw_target = raw_by_id.get(ident)
            if target is None or raw_target is None:
                continue
            payload = json.loads(payload_text)
            for item in (target, raw_target):
                item.update(payload)
            journal_ids.add(ident)
            replayed += 1
        if replayed:
            print(f"[{args.platform} 旧包版本] 从隔离检查点恢复 {replayed} 条成功记录", flush=True)
    candidates = sorted((item for item in raw if item.get("project_id")
                         and str(item["project_id"]) not in journal_ids
                         and (not journal_ids or not item.get("version_checked_at"))),
                        key=lambda item: str(item.get("date_modified") or ""), reverse=True)
    # Unchecked records first; among equally unchecked records, review recently
    # modified projects first so a bounded run catches likely new releases.
    candidates.sort(key=lambda item: item.get("version_checked_at") or "")
    free_cf = args.platform == 'curseforge' and metadata_provider() == 'cfwidget'
    candidates = candidates[:min(args.limit, 50) if free_cf else args.limit]
    checked = 0
    with_history = 0
    errors = []
    def checkpoint():
        if journal is not None:
            journal.commit()
            return
        atomic_json(raw_path, json.dumps(raw, ensure_ascii=False, indent=2) + "\n")
        atomic_json(sidecar_path, prefix + json.dumps(sidecar, ensure_ascii=False, separators=(",", ":")) + ";\n")
    try:
        for index, item in enumerate(candidates, 1):
            ident = str(item["project_id"])
            try:
                releases = fetch_releases(args.platform, ident)
                stamp = datetime.now(timezone.utc).isoformat()
                for target in (item, by_id[ident]):
                    if releases or not target.get("releases"):
                        target["releases"] = (merge_releases(target.get('releases'), releases)
                            if args.platform == 'curseforge' and metadata_provider() == 'cfwidget' else releases)
                    target["version_checked_at"] = stamp
                    if target.get('releases'):
                        target["latest_version"] = target['releases'][0]["version_number"]
                if journal is not None:
                    payload = {key: item[key] for key in ("releases", "version_checked_at", "latest_version") if key in item}
                    journal.execute("INSERT OR REPLACE INTO completed (project_id, payload) VALUES (?, ?)",
                                    (ident, json.dumps(payload, ensure_ascii=False, separators=(",", ":"))))
                checked += 1
                if releases:
                    with_history += 1
            except sqlite3.Error:
                raise
            except (AccessRefusal, WidgetRefusal) as error:
                errors.append(f"{ident}: {error}")
                break
            except Exception as error:
                errors.append(f"{ident}: {error}")
            if index % 20 == 0 or index == len(candidates):
                print(f"[{args.platform} 旧包版本] {index}/{len(candidates)} · 成功 {checked} · 有历史 {with_history} · 失败 {len(errors)}", flush=True)
                checkpoint()
            time.sleep(0.25)
        complete = not errors and checked == len(candidates)
        if journal is not None and checked + replayed:
            checkpoint()
            atomic_json(raw_path, json.dumps(raw, ensure_ascii=False, indent=2) + "\n")
            atomic_json(sidecar_path, prefix + json.dumps(sidecar, ensure_ascii=False, separators=(",", ":")) + ";\n")
        write_collection_result(args.platform, request_completed=complete, fetched_count=checked + replayed,
                                pages_completed=checked, failed_requests=len(errors), errors=errors[:20],
                                status="success" if complete and checked + replayed else "success_no_change" if complete else "partial",
                                no_change_confirmed=complete and checked + replayed == 0,
                                details={"mode": "existing", "targets": len(candidates), "withHistory": with_history,
                                         "replayedFromCheckpoint": replayed,
                                         **({'apiProvider': 'cfwidget', 'coverage': 'known-project-cached-metadata-only',
                                             'newDiscoveryCount': 0} if free_cf else {})})
    finally:
        checkpoint()
        if journal is not None:
            journal.close()


if __name__ == "__main__":
    main()

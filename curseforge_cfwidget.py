"""Free public cached metadata for known Minecraft modpacks, never discovery."""
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path

from desktop_collection_contract import write_collection_result

ORIGIN = 'https://api.cfwidget.com'
USER_AGENT = 'MCModpackCrawlerDashboard/1.0'
MAX_BYTES = 8 * 1024 * 1024
STOP = None
ROBOTS = None
LAST_REQUEST = 0
STATS = {'requests': 0, 'robotsRequests': 0, 'failed': 0}


class WidgetRefusal(RuntimeError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise WidgetRefusal(f'CFWidget HTTP {code}: redirect not followed')


def _get(path, *, robots=False):
    global STOP, LAST_REQUEST
    if STOP:
        raise WidgetRefusal(STOP)
    if not (path == '/robots.txt' or re.fullmatch(r'/\d+', path)):
        raise ValueError('CFWidget supports numeric known project IDs only')
    # One request at a time, at most one per second; no automatic retries.
    time.sleep(max(0, 1 - (time.monotonic() - LAST_REQUEST)))
    LAST_REQUEST = time.monotonic()
    STATS['robotsRequests' if robots else 'requests'] += 1
    curl = shutil.which('curl.exe') if os.name == 'nt' else None
    try:
        if curl:
            result = subprocess.run([curl, '--silent', '--show-error', '--max-time', '12',
                '--max-filesize', str(MAX_BYTES), '--user-agent', USER_AGENT,
                '--header', 'Accept: application/json' if not robots else 'Accept: text/plain',
                '--write-out', '\n__CFW_STATUS__:%{http_code}', ORIGIN + path],
                capture_output=True, timeout=15, check=False)
            if result.returncode:
                raise WidgetRefusal(f'CFWidget transport failed (curl {result.returncode}); source stopped')
            body, marker, code = result.stdout.rpartition(b'\n__CFW_STATUS__:')
            status = int(code.strip()) if marker and code.strip().isdigit() else 0
        else:
            request = urllib.request.Request(ORIGIN + path, headers={'User-Agent': USER_AGENT})
            try:
                with urllib.request.build_opener(NoRedirect()).open(request, timeout=12) as response:
                    status, body = response.status, response.read(MAX_BYTES + 1)
            except urllib.error.HTTPError as error:
                status, body = error.code, error.read(MAX_BYTES + 1)
                error.close()
        if 300 <= status < 400 or status in (401, 403, 412, 429):
            raise WidgetRefusal(f'CFWidget HTTP {status}: source stopped without redirect or retry')
        if len(body) > MAX_BYTES:
            raise WidgetRefusal('CFWidget response exceeds bounded size')
        return status, body
    except (WidgetRefusal, OSError, subprocess.TimeoutExpired) as error:
        STOP = str(error)
        STATS['failed'] += 1
        raise WidgetRefusal(STOP) from None


def validate_project(value, ident):
    if (not isinstance(value, dict) or str(value.get('id')) != str(ident)
            or value.get('game') != 'minecraft' or value.get('type') != 'Modpacks'):
        raise ValueError('CFWidget identity/game/type mismatch; old record retained')
    url = (value.get('urls') or {}).get('curseforge') or ''
    if not re.fullmatch(r'https://www\.curseforge\.com/minecraft/modpacks/[A-Za-z0-9_-]+/?', url):
        raise ValueError('CFWidget original modpack page missing or invalid')
    if not isinstance(value.get('files'), list):
        raise ValueError('CFWidget file metadata list missing')
    return value


def get_project(ident):
    global ROBOTS, STOP
    ident = str(ident)
    if not re.fullmatch(r'\d+', ident):
        raise ValueError('CurseForge project ID must be numeric')
    if ROBOTS is None:
        status, body = _get('/robots.txt', robots=True)
        if status not in (200, 404, 410):
            STOP = f'CFWidget robots unavailable (HTTP {status}); source stopped'
            raise WidgetRefusal(STOP)
        ROBOTS = urllib.robotparser.RobotFileParser()
        ROBOTS.parse(body.decode('utf-8-sig').splitlines() if status == 200 else [])
    if not ROBOTS.can_fetch(USER_AGENT, ORIGIN + '/' + ident):
        STOP = 'CFWidget robots disallows project metadata; source stopped'
        raise WidgetRefusal(STOP)
    status, body = _get('/' + ident)
    if status != 200:
        STATS['failed'] += 1
        raise ValueError(f'CFWidget HTTP {status}; record retained, no retry')
    text = body.decode('utf-8-sig')
    if re.match(r'\s*<(?:!doctype\s+html|html|head|body)\b', text, re.I):
        STOP = 'CFWidget returned HTML/access gate; source stopped'
        STATS['failed'] += 1
        raise WidgetRefusal(STOP)
    value = json.loads(text)
    if re.search(r'captcha|验证码|安全验证|Access Denied', ' '.join(str(value.get(k) or '')
            for k in ('message', 'error', 'msg')) if isinstance(value, dict) else '', re.I):
        STOP = 'CFWidget access challenge; source stopped'
        STATS['failed'] += 1
        raise WidgetRefusal(STOP)
    validate_project(value, ident)
    return value, {'provider': 'cfwidget', 'fetchedAt': datetime.now(timezone.utc).isoformat(),
        'providerLastFetch': value.get('last_fetch'), 'sha256': hashlib.sha256(body).hexdigest()}


def project_releases(project):
    base = project['urls']['curseforge'].rstrip('/')
    releases = []
    for item in project['files']:
        if not isinstance(item, dict) or not re.fullmatch(r'\d+', str(item.get('id', ''))):
            continue
        versions = item.get('versions') if isinstance(item.get('versions'), list) else []
        releases.append({'id': str(item['id']), 'version_number': item.get('display') or item.get('name') or '',
            'date_published': item.get('uploaded_at') or '', 'changelog': '',
            'game_versions': [v for v in versions if isinstance(v, str) and re.fullmatch(r'\d+\.\d+(?:\.\d+)?', v)],
            'loaders': [v for v in versions if v in ('Forge', 'Fabric', 'NeoForge', 'Quilt')],
            'files': [{'name': 'CurseForge 原始发布页', 'url': f'{base}/files/{item["id"]}'}],
            'source_provider': 'cfwidget'})
    return sorted(releases, key=lambda row: row['date_published'], reverse=True)


def merge_releases(old, observed):
    # The cache can be older/incomplete. Never replace or remove stored history.
    result = list(old or [])
    seen = {(r.get('date_published'), r.get('version_number')) for r in result}
    ids = {str(r['id']) for r in result if r.get('id') is not None}
    for row in observed:
        key = (row.get('date_published'), row.get('version_number'))
        if key not in seen and str(row.get('id')) not in ids:
            result.append(row); seen.add(key); ids.add(str(row.get('id')))
    return sorted(result, key=lambda row: row.get('date_published') or '', reverse=True)


def merge_project(old, project, observation):
    validate_project(project, old['project_id'])
    if old.get('url') and old['url'].rstrip('/') != project['urls']['curseforge'].rstrip('/'):
        raise ValueError('CFWidget original page differs from known record; manual review required')
    result = {**old}
    # Unknown upstream freshness: fill missing text only; no project-date guesses.
    for key, value in [('title', project.get('title')), ('description', project.get('summary')),
            ('icon_url', project.get('thumbnail'))]:
        if not result.get(key) and value:
            result[key] = value
    downloads = (project.get('downloads') or {}).get('total')
    if isinstance(downloads, int) and downloads >= (old.get('downloads') or 0):
        result['downloads'] = downloads
    result['releases'] = merge_releases(old.get('releases'), project_releases(project))
    result['source_observed_at'] = observation['fetchedAt']
    result['acquisition_note'] = ('CFWidget公开缓存，按已知ID核查；上游抓取时间' +
        (str(observation['providerLastFetch']) if observation.get('providerLastFetch') else '未提供') +
        '。原项目更新时间及旧版本历史保留；不代表CF全站实时刷新。')
    result['source_meta'] = {**(old.get('source_meta') or {}), 'cfwidget': observation}
    return result


def refresh_known(raw_path, sidecar_path, limit=20):
    raw_path, sidecar_path = Path(raw_path), Path(sidecar_path)
    rows = json.loads(raw_path.read_text('utf-8-sig')) if raw_path.exists() else []
    targets = sorted((row for row in rows if re.fullmatch(r'\d+', str(row.get('project_id', '')))),
        key=lambda row: str(row.get('date_modified') or ''), reverse=True)[:min(max(limit, 1), 50)]
    observed, errors = [], []
    by_id = {str(row.get('project_id')): index for index, row in enumerate(rows)}
    for target in targets:
        ident = str(target['project_id'])
        try:
            project, observation = get_project(ident)
            rows[by_id[ident]] = merge_project(target, project, observation)
            observed.append(ident)
        except Exception as error:
            errors.append(f'{ident}: {error}')
            if isinstance(error, WidgetRefusal):
                break
    if observed:
        for file, content in [(raw_path, json.dumps(rows, ensure_ascii=False, indent=2)),
                (sidecar_path, 'window.curseforgeModpacksData = ' + json.dumps(rows, ensure_ascii=False) + ';\n')]:
            file.parent.mkdir(parents=True, exist_ok=True)
            temp = file.with_suffix(file.suffix + '.tmp')
            temp.write_text(content, 'utf-8'); temp.replace(file)
    print(f'[CFWidget缓存核查] 已知包 {len(observed)}/{len(targets)}；新增发现0；旧记录全部保留。', flush=True)
    return write_collection_result('curseforge', request_completed=not errors and bool(targets),
        fetched_count=len(observed), pages_completed=len(observed), pages_expected=len(targets),
        failed_requests=len(errors), errors=errors or ([] if targets else ['没有已有CF数字ID；CFWidget不提供全站发现']),
        status='partial' if observed else 'failed',
        details={'apiProvider': 'cfwidget', 'coverage': 'known-project-cached-metadata-only',
            'observedIds': observed, 'newDiscoveryCount': 0, 'knownLimit': len(targets),
            'uniqueOutputCount': len(rows), 'sourceStop': STOP, 'requests': STATS['requests'],
            'robotsRequests': STATS['robotsRequests'], 'upstreamFreshness': 'unknown unless last_fetch provided'})

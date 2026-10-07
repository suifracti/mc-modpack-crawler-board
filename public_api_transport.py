"""Read public JSON, retaining TLS verification when Python sees TLS EOF."""
import json
import ssl
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from verified_tls import get_verified_context

SYSTEM_TLS_ORIGINS = set()
MAX_BYTES = 8 * 1024 * 1024
ALLOWED_HOSTS = {'api.bbsmc.net', 'resource-api.xyeidc.com'}


def read_public_api_json(url, headers, timeout=10):
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != 'https' or parsed.hostname not in ALLOWED_HOSTS
            or parsed.username or parsed.password):
        raise ValueError('Unsupported public API origin')
    if any(key.lower() in {'authorization', 'cookie', 'x-api-key'} for key in headers):
        raise ValueError('Public metadata transport cannot send credentials')
    if parsed.hostname not in SYSTEM_TLS_ORIGINS:
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=timeout, context=get_verified_context()) as response:
                data = response.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                raise ValueError('Public API response too large')
            return json.loads(data)
        except urllib.error.URLError as error:
            if not isinstance(error.reason, ssl.SSLEOFError):
                raise
            SYSTEM_TLS_ORIGINS.add(parsed.hostname)
            print('[网络连接] Python TLS EOF；同一公开API改用系统TLS，保留证书校验。', flush=True)

    # Same URL and public headers; certificate errors, redirects and access
    # denials are never worked around. Only the TLS implementation changes.
    command = ['/usr/bin/curl', '--silent', '--show-error', '--max-time', str(timeout),
               '--proto', '=https', '--max-filesize', str(MAX_BYTES),
               '--write-out', '\n__PUBLIC_STATUS__:%{http_code}']
    for key, value in headers.items():
        command.extend(['--header', f'{key}: {value}'])
    command.append(url)
    result = subprocess.run(command, capture_output=True, timeout=timeout + 3, check=False)
    if result.returncode:
        raise OSError(f'System TLS request failed (curl {result.returncode})')
    body, marker, status = result.stdout.rpartition(b'\n__PUBLIC_STATUS__:')
    if not marker or len(body) > MAX_BYTES:
        raise ValueError('Invalid public API response')
    code = int(status)
    if code != 200:
        raise urllib.error.HTTPError(url, code, 'Public API response', {}, None)
    return json.loads(body)

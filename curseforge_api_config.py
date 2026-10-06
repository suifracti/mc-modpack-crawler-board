"""Official CurseForge metadata API configuration; credentials stay local."""
import os
import re
import urllib.parse
from pathlib import Path

API_ORIGIN = 'https://api.curseforge.com'


def metadata_provider():
    """Select before any request; never switch providers after a refusal."""
    configured = os.environ.get('CURSEFORGE_PROVIDER', '').strip().lower()
    if configured:
        if configured not in {'official', 'cfwidget'}:
            raise ApiConfigurationError('CURSEFORGE_PROVIDER must be official or cfwidget')
        return configured
    return 'official' if any(os.environ.get(name) for name in
        ('CURSEFORGE_API_KEY', 'CF_API_KEY', 'CURSEFORGE_API_KEY_FILE')) else 'cfwidget'


class ApiConfigurationError(ValueError):
    pass


def api_url(path, params=None):
    if not re.fullmatch(r'/v1/mods/(?:search|\d+(?:/files)?)', path):
        raise ApiConfigurationError('CurseForge endpoint is outside metadata scope')
    return API_ORIGIN + path + ('?' + urllib.parse.urlencode(params) if params else '')


def validate_api_url(url):
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != 'https' or parsed.netloc != 'api.curseforge.com' or parsed.fragment
            or not re.fullmatch(r'/v1/mods/(?:search|\d+(?:/files)?)', parsed.path)):
        raise ApiConfigurationError('CurseForge credentials may only be sent to the official metadata API')


def read_api_key():
    key = os.environ.get('CURSEFORGE_API_KEY') or os.environ.get('CF_API_KEY') or ''
    filename = os.environ.get('CURSEFORGE_API_KEY_FILE')
    if not key and filename:
        try:
            with Path(filename).open('rb') as handle:
                content = handle.read(4097)
            if len(content) > 4096:
                raise ApiConfigurationError('CurseForge API Key file exceeds size limit')
            key = content.decode('utf-8-sig').strip()
        except (OSError, UnicodeError):
            raise ApiConfigurationError('CurseForge API Key file cannot be read') from None
    if not key:
        raise ApiConfigurationError('CurseForge官方API需要你自己的已获批Key；请配置CURSEFORGE_API_KEY或CURSEFORGE_API_KEY_FILE后重新启动服务。未发起请求。')
    if not re.fullmatch(r'[\x21-\x7e]{1,4096}', key):
        raise ApiConfigurationError('CurseForge API Key contains invalid header characters')
    return key

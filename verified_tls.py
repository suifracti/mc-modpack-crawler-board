"""Create HTTPS contexts only when a trusted root CA bundle is available."""
from pathlib import Path
from functools import lru_cache
import ssl
import sys


def _system_ca_paths(platform_name):
    if platform_name == "darwin":
        return ("/etc/ssl/cert.pem",)
    if platform_name.startswith("linux"):
        return ("/etc/ssl/certs/ca-certificates.crt", "/etc/pki/tls/certs/ca-bundle.crt")
    return ()


def _has_trusted_roots(context):
    try:
        return int(context.cert_store_stats().get("x509_ca") or 0) > 0
    except (AttributeError, TypeError, ValueError):
        return False


def create_verified_context(*, context_factory=None, platform_name=None, ca_paths=None):
    """Use Python's configured roots, then the OS CA bundle; never disable TLS checks."""
    factory = context_factory or ssl.create_default_context
    context = factory()
    if _has_trusted_roots(context):
        return context
    candidates = _system_ca_paths(platform_name or sys.platform) if ca_paths is None else ca_paths
    for candidate in candidates:
        path = Path(candidate)
        if not path.is_file():
            continue
        try:
            context = factory(cafile=str(path))
        except (OSError, ssl.SSLError):
            continue
        if _has_trusted_roots(context):
            return context
    raise ssl.SSLError("No trusted CA certificates available; refusing HTTPS without verification")


@lru_cache(maxsize=1)
def get_verified_context():
    """Load trusted roots once per worker, retaining hostname and chain checks."""
    return create_verified_context()

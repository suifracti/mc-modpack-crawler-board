"""Small, dependency-free result contract shared by desktop crawlers.

The desktop worker must be able to distinguish a successful request cycle from
an old cache that a crawler merely rewrote.  Each crawler writes this report
after it knows whether its request/page walk completed.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def _result_path() -> Path:
    configured = os.environ.get("MC_DESKTOP_COLLECTION_RESULT")
    if not configured:
        raise RuntimeError("MC_DESKTOP_COLLECTION_RESULT 未配置")
    return Path(configured).resolve()


def write_collection_result(
    platform: str,
    *,
    request_completed: bool,
    fetched_count: int,
    pages_completed: int = 0,
    pages_expected: int | None = None,
    truncated: bool = False,
    failed_requests: int = 0,
    errors: Iterable[str] | None = None,
    status: str | None = None,
    no_change_confirmed: bool = False,
    details: dict[str, object] | None = None,
) -> dict[str, object]:
    errors_list = [str(item) for item in (errors or []) if str(item).strip()]
    if status is None:
        if not request_completed or failed_requests or errors_list:
            status = "failed"
        elif truncated:
            status = "partial"
        elif fetched_count > 0:
            status = "success"
        else:
            status = "empty"

    payload: dict[str, object] = {
        "schema": 1,
        "platform": platform,
        "status": status,
        "requestCompleted": bool(request_completed),
        "fetchedCount": int(fetched_count),
        "pagesCompleted": int(pages_completed),
        "pagesExpected": pages_expected,
        "truncated": bool(truncated),
        "failedRequests": int(failed_requests),
        "errors": errors_list,
        "noChangeConfirmed": bool(no_change_confirmed),
        "startedAt": datetime.now(timezone.utc).isoformat(),
        "finishedAt": datetime.now(timezone.utc).isoformat(),
    }
    if details:
        payload["details"] = details

    path = _result_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".desktop-collection-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return payload

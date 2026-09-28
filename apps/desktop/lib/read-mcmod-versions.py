"""Read one MC百科 pack's release history with the crawler's shared parser."""

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)

from mcmod_full_crawler import fetch_version_data  # noqa: E402


if __name__ == "__main__":
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        raise SystemExit("MC百科整合包编号无效")
    result = fetch_version_data(sys.argv[1], retries=1, timeout=12)
    print(json.dumps({"checked": result["checked"], "versions": result["versions"]}, ensure_ascii=False))

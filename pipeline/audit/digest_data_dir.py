"""
Phase 3G-D.1R - Release Integrity helper.
Computes a deterministic SHA-256 digest manifest for converted_output/data/
so the Modern -> Legacy frontend rollback can be proven data-neutral.

Usage:
    python pipeline/audit/digest_data_dir.py <label> [target_dir]

Writes build/audit/data_digest_<label>.json and prints the rollup digest.
"""
import hashlib
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_TARGET = os.path.join(REPO_ROOT, "converted_output", "data")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 16):
            h.update(chunk)
    return h.hexdigest()


def digest_dir(target_dir):
    entries = []
    for root, dirs, files in os.walk(target_dir):
        dirs.sort()
        for name in sorted(files):
            abs_p = os.path.join(root, name)
            rel_p = os.path.relpath(abs_p, target_dir).replace("\\", "/")
            entries.append({
                "path": rel_p,
                "size_bytes": os.path.getsize(abs_p),
                "sha256": sha256_file(abs_p),
            })
    entries.sort(key=lambda e: e["path"])
    rollup = hashlib.sha256()
    for e in entries:
        rollup.update(f'{e["path"]}\n{e["sha256"]}\n'.encode("utf-8"))
    return {
        "target_directory": target_dir.replace("\\", "/"),
        "file_count": len(entries),
        "total_size_bytes": sum(e["size_bytes"] for e in entries),
        "rollup_sha256": rollup.hexdigest(),
        "files": entries,
    }


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "current"
    target = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_TARGET
    if not os.path.isdir(target):
        print(f"[-] Target directory not found: {target}")
        return 1
    result = digest_dir(target)
    out_dir = os.path.join(REPO_ROOT, "build", "audit")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"data_digest_{label}.json")
    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(result, fp, indent=2, ensure_ascii=False)
    print(f"[+] label                : {label}")
    print(f"[+] target               : {result['target_directory']}")
    print(f"[+] file_count           : {result['file_count']}")
    print(f"[+] total_size_bytes     : {result['total_size_bytes']}")
    print(f"[+] rollup_sha256        : {result['rollup_sha256']}")
    print(f"[+] artifact             : {os.path.relpath(out_path, REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
Architecture V2 - SHA-256 Manifest Utility.
Generates and verifies cryptographic manifests for production, staging, and backup directories.
Uses portable relative paths and deterministic sorting.
"""
import os
import hashlib
import json
import time
import subprocess
from typing import Dict, Any, List, Tuple, Optional

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def get_git_commit(cwd: str = REPO_ROOT) -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True
        )
        return res.stdout.strip()
    except Exception:
        return "unknown"


def generate_manifest(
    target_dir: str,
    output_manifest_path: str,
    extra_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Generates a deterministic SHA-256 manifest for a target directory."""
    if not os.path.exists(target_dir):
        raise FileNotFoundError(f"Target directory does not exist: {target_dir}")

    os.makedirs(os.path.dirname(output_manifest_path), exist_ok=True)
    t0 = time.time()
    entries = []
    total_bytes = 0

    for root, dirs, files in os.walk(target_dir):
        dirs.sort()
        for f in sorted(files):
            abs_p = os.path.join(root, f)
            rel_p = os.path.relpath(abs_p, target_dir).replace("\\", "/")
            sz = os.path.getsize(abs_p)
            sha = compute_sha256(abs_p)
            total_bytes += sz
            entries.append({
                "path": rel_p,
                "size_bytes": sz,
                "sha256": sha
            })

    manifest = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "target_directory": os.path.basename(os.path.normpath(target_dir)),
        "source_commit": get_git_commit(),
        "total_files": len(entries),
        "total_size_bytes": total_bytes,
        "total_size_mb": round(total_bytes / (1024 * 1024), 2),
    }

    if extra_metadata:
        manifest.update(extra_metadata)

    manifest["files"] = entries

    with open(output_manifest_path, "w", encoding="utf-8") as fp:
        json.dump(manifest, fp, indent=2, ensure_ascii=False)

    elapsed = time.time() - t0
    manifest["elapsed_seconds"] = round(elapsed, 2)
    return manifest


def verify_manifest(
    target_dir: str,
    manifest_path: str,
    ignore_extra: Optional[List[str]] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Verifies a target directory against a SHA-256 manifest.
    Returns (is_match, details_dict).
    """
    if not os.path.exists(target_dir):
        return False, {"error": f"Target directory not found: {target_dir}"}
    if not os.path.exists(manifest_path):
        return False, {"error": f"Manifest file not found: {manifest_path}"}

    with open(manifest_path, "r", encoding="utf-8") as fp:
        manifest = json.load(fp)

    manifest_map = {entry["path"]: entry for entry in manifest.get("files", [])}
    found_paths = set()
    missing = []
    modified = []
    extra = []
    ignore_set = set(ignore_extra or [])

    for root, dirs, files in os.walk(target_dir):
        dirs.sort()
        for f in sorted(files):
            abs_p = os.path.join(root, f)
            rel_p = os.path.relpath(abs_p, target_dir).replace("\\", "/")
            if rel_p in ignore_set:
                continue
            found_paths.add(rel_p)

            if rel_p not in manifest_map:
                extra.append(rel_p)
            else:
                expected = manifest_map[rel_p]
                actual_sz = os.path.getsize(abs_p)
                if actual_sz != expected["size_bytes"]:
                    modified.append({
                        "path": rel_p,
                        "reason": "size_mismatch",
                        "expected": expected["size_bytes"],
                        "actual": actual_sz
                    })
                else:
                    actual_sha = compute_sha256(abs_p)
                    if actual_sha != expected["sha256"]:
                        modified.append({
                            "path": rel_p,
                            "reason": "sha256_mismatch",
                            "expected": expected["sha256"],
                            "actual": actual_sha
                        })

    for p in manifest_map:
        if p not in found_paths:
            missing.append(p)

    is_match = (len(missing) == 0 and len(modified) == 0 and len(extra) == 0)
    details = {
        "is_match": is_match,
        "manifest_total_files": len(manifest_map),
        "target_total_files": len(found_paths),
        "missing_count": len(missing),
        "modified_count": len(modified),
        "extra_count": len(extra),
        "missing": missing,
        "modified": modified,
        "extra": extra
    }
    return is_match, details

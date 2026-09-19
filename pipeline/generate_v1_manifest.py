"""
Generates a deterministic SHA-256 manifest for converted_output/.
Provides an immutable cryptographic baseline for integrity and rollback verification.
"""
import os
import hashlib
import json
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET_DIR = os.path.join(REPO_ROOT, "converted_output")
MANIFEST_DIR = os.path.join(REPO_ROOT, "build", "manifests")
MANIFEST_FILE = os.path.join(MANIFEST_DIR, "v1_production.sha256.json")

def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def generate_manifest():
    if not os.path.exists(TARGET_DIR):
        raise FileNotFoundError(f"Directory not found: {TARGET_DIR}")

    os.makedirs(MANIFEST_DIR, exist_ok=True)
    t0 = time.time()
    manifest_entries = []
    total_bytes = 0

    print(f"[*] Hashing all files in: {TARGET_DIR}...")
    for root, dirs, files in os.walk(TARGET_DIR):
        dirs.sort()
        for f in sorted(files):
            abs_p = os.path.join(root, f)
            rel_p = os.path.relpath(abs_p, TARGET_DIR).replace("\\", "/")
            sz = os.path.getsize(abs_p)
            sha = compute_sha256(abs_p)
            total_bytes += sz
            manifest_entries.append({
                "path": rel_p,
                "size_bytes": sz,
                "sha256": sha
            })

    summary = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "target_directory": "converted_output",
        "total_files": len(manifest_entries),
        "total_size_bytes": total_bytes,
        "total_size_mb": round(total_bytes / (1024 * 1024), 2),
        "files": manifest_entries
    }

    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    elapsed = time.time() - t0
    print(f"[+] Manifest generated successfully in {elapsed:.2f}s!")
    print(f"    Total Files     : {len(manifest_entries):,}")
    print(f"    Total Size      : {summary['total_size_mb']} MB")
    print(f"    Manifest Saved  : {MANIFEST_FILE}")

if __name__ == "__main__":
    generate_manifest()

"""
Compares V1 (converted_output/data) vs V2 (build/legacy_preview/data) sidecar sizes.
Calculates byte delta, percentage, directory totals, and explains growth factors.
"""
import os
import sys

def dir_size(path):
    if not os.path.exists(path):
        return 0
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            total += os.path.getsize(os.path.join(root, f))
    return total

def compare_sizes():
    v1_dir = "converted_output/data"
    v2_dir = "build/legacy_preview/data"

    files_to_check = [
        "table_rows.js",
        "app_data.js",
        "desc_data.js",
        "bili_data.js",
        "bbsmc_data.js",
        "xyebbs_data.js",
        "modrinth_data.js",
        "curseforge_data.js",
        "audit_diff.js",
    ]

    dirs_to_check = [
        "mods",
        "comments",
    ]

    print(f"{'File / Directory':<24} | {'V1 Bytes':<14} | {'V2 Bytes':<14} | {'Delta Bytes':<14} | {'Delta %':<10}")
    print("-" * 86)

    total_v1_specific = 0
    total_v2_specific = 0

    for f in files_to_check:
        p1 = os.path.join(v1_dir, f)
        p2 = os.path.join(v2_dir, f)
        sz1 = os.path.getsize(p1) if os.path.exists(p1) else 0
        sz2 = os.path.getsize(p2) if os.path.exists(p2) else 0
        delta = sz2 - sz1
        pct = (delta / sz1 * 100) if sz1 > 0 else 0
        total_v1_specific += sz1
        total_v2_specific += sz2
        print(f"{f:<24} | {sz1:<14,d} | {sz2:<14,d} | {delta:<+14,d} | {pct:<+9.2f}%")

    for d in dirs_to_check:
        p1 = os.path.join(v1_dir, d)
        p2 = os.path.join(v2_dir, d)
        sz1 = dir_size(p1)
        sz2 = dir_size(p2)
        delta = sz2 - sz1
        pct = (delta / sz1 * 100) if sz1 > 0 else 0
        total_v1_specific += sz1
        total_v2_specific += sz2
        print(f"{d + '/':<24} | {sz1:<14,d} | {sz2:<14,d} | {delta:<+14,d} | {pct:<+9.2f}%")

    print("-" * 86)
    # Total data directory sizes
    total_v1_all = dir_size(v1_dir)
    total_v2_all = dir_size(v2_dir)
    delta_all = total_v2_all - total_v1_all
    pct_all = (delta_all / total_v1_all * 100) if total_v1_all > 0 else 0

    print(f"{'TOTAL DATA DIR':<24} | {total_v1_all:<14,d} | {total_v2_all:<14,d} | {delta_all:<+14,d} | {pct_all:<+9.2f}%")
    print(f"  V1 Data Total : {total_v1_all / (1024 * 1024):.2f} MB")
    print(f"  V2 Data Total : {total_v2_all / (1024 * 1024):.2f} MB")
    print(f"  Net Difference: {delta_all / (1024 * 1024):+.2f} MB ({pct_all:+.2f}%)")

if __name__ == "__main__":
    compare_sizes()

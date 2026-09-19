"""
Architecture V2 - Phase 3F.2: Release-Date Semantic Equivalence Gate.

Exports the FULL set of per-release `release_date` differences between the
Migrated DB (build/canonical.db) and the Fresh Rebuilt DB
(build/canonical_fresh_verify.db).

Output: build/audit/release_date_migrated_vs_fresh_diff.json

Categories:
  A = migrated NULL      / fresh non-NULL   (fresh fabricated a date)
  B = migrated non-NULL  / fresh NULL       (fresh dropped a date)
  C = both non-NULL but different values
"""
import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_MIGRATED = os.path.join(ROOT, "build", "canonical.db")
DEFAULT_FRESH = os.path.join(ROOT, "build", "canonical_fresh_verify.db")
DEFAULT_OUT = os.path.join(ROOT, "build", "audit", "release_date_migrated_vs_fresh_diff.json")

QUERY = """
SELECT r.id            AS release_id,
       r.release_date  AS release_date,
       r.source_item_id AS source_item_id,
       s.platform      AS platform,
       s.source_id     AS source_id,
       s.published_at  AS source_published_at,
       s.modified_at   AS source_modified_at,
       r.version_name  AS version_name,
       r.version_type  AS version_type,
       r.is_latest     AS is_latest,
       r.downloads_count AS download_count
FROM releases r
LEFT JOIN source_items s ON r.source_item_id = s.id
ORDER BY r.id
"""


def load(db_path):
    conn = sqlite3.connect(db_path)
    try:
        return {row[0]: row for row in conn.execute(QUERY)}
    finally:
        conn.close()


def classify(migrated_date, fresh_date):
    if migrated_date == fresh_date:
        return "SAME"
    if migrated_date is None:
        return "A_migrated_null_fresh_nonnull"
    if fresh_date is None:
        return "B_migrated_nonnull_fresh_null"
    return "C_both_nonnull_different"


def build_report(db_migrated=DEFAULT_MIGRATED, db_fresh=DEFAULT_FRESH, out_path=DEFAULT_OUT,
                 captured_state="PRE_FIX", write_diff_file=True):
    migrated = load(db_migrated)
    fresh = load(db_fresh)

    if set(migrated) != set(fresh):
        raise SystemExit(
            "release id sets differ between DBs: "
            f"only_migrated={len(set(migrated) - set(fresh))} only_fresh={len(set(fresh) - set(migrated))}"
        )

    diffs = []
    counts = {
        "total_release_rows": len(migrated),
        "same_release_date_rows": 0,
        "different_release_date_rows": 0,
        "migrated_null_fresh_nonnull": 0,
        "migrated_nonnull_fresh_null": 0,
        "both_nonnull_but_different": 0,
    }
    per_platform = {}

    for rid in sorted(migrated):
        m = migrated[rid]
        f = fresh[rid]
        cat = classify(m[1], f[1])
        if cat == "SAME":
            counts["same_release_date_rows"] += 1
            continue

        counts["different_release_date_rows"] += 1
        if cat.startswith("A"):
            counts["migrated_null_fresh_nonnull"] += 1
        elif cat.startswith("B"):
            counts["migrated_nonnull_fresh_null"] += 1
        else:
            counts["both_nonnull_but_different"] += 1

        platform = m[3]
        per_platform.setdefault(platform, {})
        per_platform[platform][cat] = per_platform[platform].get(cat, 0) + 1

        diffs.append({
            "release_id": m[0],
            "platform": platform,
            "source_item_id": m[2],
            "source_id": m[4],
            "version_name": m[7],
            "version_type": m[8],
            "migrated_release_date": m[1],
            "fresh_release_date": f[1],
            "source_published_at": m[5],
            "source_modified_at": m[6],
            "difference_class": cat,
            "fresh_equals_source_published_at": f[1] is not None and f[1] == m[5],
            "fresh_equals_source_modified_at": f[1] is not None and f[1] == m[6],
        })

    report = {
        "phase": "Architecture V2 - Phase 3F.2 Release-Date Semantic Equivalence Gate",
        "captured_state": captured_state,
        "base_commit": "391a516",
        "migrated_db": os.path.relpath(db_migrated, ROOT).replace("\\", "/"),
        "fresh_db": os.path.relpath(db_fresh, ROOT).replace("\\", "/"),
        "summary": counts,
        "per_platform_difference_counts": per_platform,
        "differences": diffs,
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if write_diff_file:
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=1)

    print("=" * 70)
    print("  Release-Date Diff Export (Migrated vs Fresh)")
    print("=" * 70)
    print(f"  total release rows                 : {counts['total_release_rows']}")
    print(f"  same release_date rows             : {counts['same_release_date_rows']}")
    print(f"  different release_date rows        : {counts['different_release_date_rows']}")
    print(f"    A migrated NULL / fresh non-NULL : {counts['migrated_null_fresh_nonnull']}")
    print(f"    B migrated non-NULL / fresh NULL : {counts['migrated_nonnull_fresh_null']}")
    print(f"    C both non-NULL but different    : {counts['both_nonnull_but_different']}")
    print(f"  per-platform                       : {json.dumps(per_platform, ensure_ascii=False)}")
    print(f"  written -> {out_path}")
    return report


def build_post_fix_report(out_path=None):
    """Writes the POST-FIX equivalence state (0 differing rows expected)."""
    out_path = out_path or os.path.join(ROOT, "build", "audit", "release_date_post_fix_equivalence.json")
    report = build_report(captured_state="POST_FIX", write_diff_file=False)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump({k: v for k, v in report.items() if k != "differences"}, fh,
                  ensure_ascii=False, indent=1)
    print(f"  post-fix equivalence written -> {out_path}")
    return report


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--post-fix" in args:
        build_post_fix_report()
    else:
        def _opt(flag, default):
            return args[args.index(flag) + 1] if flag in args else default

        build_report(
            db_migrated=_opt("--migrated", DEFAULT_MIGRATED),
            db_fresh=_opt("--fresh", DEFAULT_FRESH),
            out_path=_opt("--out", DEFAULT_OUT),
            captured_state=_opt("--state", "PRE_FIX"),
        )

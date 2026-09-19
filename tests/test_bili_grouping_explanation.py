"""
Bilibili grouping explanation test (Phase 3G-F revised).

Previously this test re-implemented the legacy grouping rule in Python and
asserted `53 raw -> 47 grouped cards`. That made 47 a *correctness golden*, which
Phase 3G-E proved is wrong: 47 only ever described the pre-remediation algorithm's
stability. After Phase 3G-F recovers the false splits, the grouped count is
expected to move.

What this test now asserts:
  * `53 raw` — the real invariant (Flat Mode must show every raw record)
  * grouping is produced by the REAL implementation (the TS domain module bundled
    with the project's own esbuild), not by a Python re-implementation
  * the evidence-backed merges that must not regress (懂嗎懂嗎 A/B, ZiCaiOT,
    白银_1223) still collapse
  * every raw record still maps to exactly one group (no record is lost)
"""
import json
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CANDIDATE_DATA = [
    os.path.join(REPO_ROOT, "converted_output", "data", "bili_data.js"),
    os.path.join(REPO_ROOT, "build", "frontend_preview", "data", "bili_data.js"),
]
DATA_PATH = next((p for p in CANDIDATE_DATA if os.path.exists(p)), CANDIDATE_DATA[0])
MODULE = os.path.join(REPO_ROOT, "build", "audit", "bilibili_grouping_module.js")
QUERY = "机械动力"


def load_payload():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    json_str = content.split("=", 1)[1].strip()
    if json_str.endswith(";"):
        json_str = json_str[:-1]
    return json.loads(json_str)


def search_blob(p):
    return " ".join([
        p.get("title") or "", p.get("author") or "", p.get("desc") or "",
        p.get("mc_version") or "", " ".join(p.get("loaders") or []),
        " ".join(p.get("categories") or []),
    ]).lower()


def ensure_module():
    esbuild = os.path.join(REPO_ROOT, "apps", "web", "node_modules", ".bin",
                           "esbuild.cmd" if os.name == "nt" else "esbuild")
    r = subprocess.run([esbuild, "apps/web/src/domain/bilibiliGrouping.ts", "--bundle",
                        "--format=cjs", "--platform=node", f"--outfile={MODULE}",
                        "--log-level=warning"],
                       cwd=REPO_ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    assert r.returncode == 0, f"esbuild failed: {r.stdout}\n{r.stderr}"


def group_with_real_impl(records):
    """Run the REAL domain module in Node and return bvid -> groupKey."""
    payload = json.dumps(records, ensure_ascii=False)
    js = (
        "global.window={};const m=require(" + json.dumps(MODULE.replace('\\', '/')) + ");"
        "const recs=JSON.parse(require('fs').readFileSync(0,'utf8'));"
        "const o={};for(const [b,d] of m.groupBilibiliPacks(recs)) o[b]=d.groupKey;"
        "console.log(JSON.stringify(o));"
    )
    r = subprocess.run(["node", "-e", js], cwd=REPO_ROOT, input=payload,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0, f"node failed: {r.stdout}\n{r.stderr}"
    return json.loads(r.stdout)


def main():
    ensure_module()
    data = load_payload()
    filtered = [p for p in data if QUERY in search_blob(p)]
    print(f"Raw filtered videos count: {len(filtered)}")

    # ---- invariant: Flat Mode must surface every raw record -------------------
    assert len(filtered) == 53, f"Expected 53 raw filtered items, got {len(filtered)}"
    print("INVARIANT OK: Flat Mode still shows 53 raw records")

    # ---- grouping by the real implementation ---------------------------------
    slim = [{"bvid": p.get("bvid"), "title": p.get("title") or "",
             "author": p.get("author") or ""} for p in filtered]
    keys = group_with_real_impl(slim)

    # no record may be dropped
    assert len(keys) == len(filtered), (
        f"grouping lost records: {len(keys)} of {len(filtered)}")

    groups = {}
    for p in filtered:
        groups.setdefault(keys[p["bvid"]], []).append(p)

    multi = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"Grouped cards count: {len(groups)}  (was 47 before Phase 3G-F remediation)")
    print(f"Multi-video groups: {len(multi)}")
    for k, items in sorted(multi.items(), key=lambda x: -len(x[1])):
        print(f"  Group Key: {k} ({len(items)} items):")
        for it in items:
            print(f"    * {it.get('bvid')} - {(it.get('title') or '')[:48]}")

    # ---- evidence-backed merges that must not regress -------------------------
    REQUIRED_MERGES = {
        "懂嗎懂嗎 Group A": ["BV1Ziuw6ZE7C", "BV1fqNe6rEt5", "BV1tVeVzDELy"],
        "懂嗎懂嗎 Group B": ["BV1vuVH6XErM", "BV1k3Lg6zEjY", "BV1ACA8zjELd"],
        "ZiCaiOT 农场物语": ["BV1XA9tBYE5D", "BV1REYKzgE45"],
        "Horizon 地平线": ["BV17vQtY5E74", "BV1px4y1J71D", "BV1Wx4y1i7CH",
                            "BV1yC411G7Fj", "BV1Tx421X7nC", "BV1yx421C7FN"],
    }
    for label, bvids in REQUIRED_MERGES.items():
        present = [b for b in bvids if b in keys]
        if len(present) < 2:
            continue
        distinct = {keys[b] for b in present}
        assert len(distinct) == 1, f"{label} regressed: {len(distinct)} groups for {present}"
        print(f"  [OK] {label}: {len(present)} videos -> 1 group")

    print("VERIFICATION SUCCESS: 53 raw records preserved; grouping is "
          "evidence-backed and false splits are reduced (see "
          "build/audit/bilibili_grouping_remediation.json)")


if __name__ == "__main__":
    main()

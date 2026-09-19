"""
Architecture V2 - Phase 3C: Search Golden Corpus Tests.
Validates search fidelity, term matching, and Top-N ID invariants across platform payloads.
"""
import json
import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "build", "frontend_preview", "data")


def load_mcmod_data():
    path = os.path.join(DATA_DIR, "mcmod_data.js")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    json_str = content.split("window.mcmodData = ")[1].rsplit(";", 1)[0]
    return json.loads(json_str)


def test_mcmod_search_rlcraft_golden():
    """Verify MCMod RLCraft search matches exactly 93 items and invariant Top-N IDs."""
    data = load_mcmod_data()
    matches = []
    for row in data:
        target = " ".join([
            row.get("title") or "",
            row.get("typeName") or "",
            " ".join(row.get("formerTitles") or []),
            " ".join(row.get("categories") or []),
            ", ".join(row.get("includedModNames") or [])
        ]).lower()
        if "rlcraft" in target:
            matches.append(row["mid"])

    assert len(matches) == 93, f"Expected 93 RLCraft matches, got {len(matches)}"

    # Top 10 sorted MIDs
    top_10 = sorted(matches)[:10]
    expected_top_10 = [16, 57, 198, 221, 304, 305, 339, 360, 370, 399]
    assert top_10 == expected_top_10, f"Expected {expected_top_10}, got {top_10}"


def test_mcmod_search_create_golden():
    """Verify MCMod '机械动力' (Create) search results."""
    data = load_mcmod_data()
    matches = []
    for row in data:
        target = " ".join([
            row.get("title") or "",
            row.get("typeName") or "",
            " ".join(row.get("formerTitles") or []),
            " ".join(row.get("categories") or []),
            ", ".join(row.get("includedModNames") or [])
        ]).lower()
        if "机械动力" in target:
            matches.append(row["mid"])

    assert len(matches) == 415, f"Expected 415 机械动力 matches, got {len(matches)}"
    top_10 = sorted(matches)[:10]
    expected_top_10 = [10, 47, 149, 164, 167, 168, 170, 172, 189, 198]
    assert top_10 == expected_top_10, f"Expected {expected_top_10}, got {top_10}"


def test_bilibili_search_create_golden():
    """Verify Bilibili search '机械动力' matches."""
    path = os.path.join(DATA_DIR, "bili_data.js")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    data = json.loads(content.split("=", 1)[1].rsplit(";", 1)[0])

    matches = []
    for p in data:
        target = (
            (p.get("title") or "") + " " +
            (p.get("author") or "") + " " +
            (p.get("desc") or "") + " " +
            (p.get("mc_version") or "") + " " +
            " ".join(p.get("loaders") or []) + " " +
            " ".join(p.get("categories") or [])
        ).lower()
        if "机械动力" in target:
            matches.append(p.get("bvid") or p.get("id"))

    assert len(matches) >= 40, f"Expected >=40 Bili 机械动力 matches, got {len(matches)}"


if __name__ == "__main__":
    test_mcmod_search_rlcraft_golden()
    test_mcmod_search_create_golden()
    test_bilibili_search_create_golden()
    print("All search golden tests passed!")

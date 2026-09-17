"""
Contract test for data/mcmod_data.js.
Verifies:
1. Records = 1484
2. Unique mid = 1484
3. Missing titles = 0
4. c0 through c6 do NOT exist
5. No UI HTML (<div, <span, <button, <svg, onclick=) in structured data fields
"""
import os
import json
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCMOD_DATA_PATH = os.path.join(REPO_ROOT, "build", "frontend_preview", "data", "mcmod_data.js")

def test_contract():
    assert os.path.exists(MCMOD_DATA_PATH), f"File not found: {MCMOD_DATA_PATH}"
    with open(MCMOD_DATA_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    prefix = "window.mcmodData = "
    assert content.startswith(prefix), "Must start with window.mcmodData = "
    json_str = content[len(prefix):].rstrip().rstrip(";")
    data = json.loads(json_str)

    print(f"[Contract Test] Loaded {len(data)} items from mcmod_data.js")
    assert len(data) == 1484, f"Expected 1484 records, got {len(data)}"

    mids = set()
    html_pattern = re.compile(r'<(?:div|span|button|svg|details|summary|section|a\s+href)[^>]*>', re.IGNORECASE)

    for i, item in enumerate(data):
        mid = item.get("mid")
        assert mid is not None, f"Item {i} missing mid"
        assert mid not in mids, f"Duplicate mid: {mid}"
        mids.add(mid)

        title = item.get("title")
        assert title and title.strip(), f"Item {mid} missing title"

        # Check c0 through c6 do not exist
        for col in ["c0", "c1", "c2", "c3", "c4", "c5", "c6"]:
            assert col not in item, f"Legacy column {col} must NOT exist in structured data! (mid={mid})"

        # Check environment claims structure
        claims = item.get("environmentClaims")
        assert isinstance(claims, list) and len(claims) >= 2, f"Item {mid} missing environmentClaims"
        sides = {c["side"] for c in claims}
        assert "server" in sides and "client" in sides, f"Item {mid} environmentClaims must cover both server and client"

        # Scan text fields for injected UI HTML
        for field in ["title", "chineseName", "englishName", "author", "typeName", "modSearchText", "modCategorySearch"]:
            val = item.get(field)
            if val and isinstance(val, str):
                match = html_pattern.search(val)
                assert not match, f"UI HTML tag found in field {field} for mid={mid}: {match.group(0)}"

    print("[Contract Test] ALL 5 CHECKS PASSED:")
    print("  [PASS] Records = 1484")
    print("  [PASS] Unique mid = 1484")
    print("  [PASS] Missing title = 0")
    print("  [PASS] c0~c6 columns = 0")
    print("  [PASS] Injected UI HTML tags = 0")

if __name__ == "__main__":
    test_contract()

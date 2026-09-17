"""
Contract test for data/mcmod_data.js and Frontend Provenance Alignment.
Verifies:
1. Records = 1484, Unique mid = 1484, Missing titles = 0
2. Legacy c0~c6 do NOT exist, 0 UI HTML injected
3. Canonical Enum Parity (Frontend TS contract covers all DISTINCT values in canonical.db)
4. Golden Claims Preservation (status, certainty, evidenceType, sourceField, rawValue preserved without loss)
"""
import os
import json
import re
import sqlite3

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCMOD_DATA_PATH = os.path.join(REPO_ROOT, "build", "frontend_preview", "data", "mcmod_data.js")
DB_PATH = os.path.join(REPO_ROOT, "build", "canonical.db")
TS_TYPES_PATH = os.path.join(REPO_ROOT, "apps", "web", "src", "domain", "types.ts")

def extract_ts_union_literals(content: str, type_name: str) -> set:
    """Extract string literal union values from a TypeScript type definition."""
    match = re.search(rf'export\s+type\s+{type_name}\s*=\s*([^;]+);', content, re.MULTILINE | re.DOTALL)
    if not match:
        raise ValueError(f"Type {type_name} not found in TypeScript definitions")
    body = match.group(1)
    return set(re.findall(r"'([^']+)'", body))

def test_canonical_enum_parity():
    """Verify Frontend TS contracts and exported mcmod_data.js are in 100% parity with Canonical DB."""
    assert os.path.exists(DB_PATH), f"Canonical DB not found: {DB_PATH}"
    assert os.path.exists(TS_TYPES_PATH), f"TS types file not found: {TS_TYPES_PATH}"

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    db_statuses = {r[0] for r in c.execute("SELECT DISTINCT status FROM environment_claims")}
    db_certainties = {r[0] for r in c.execute("SELECT DISTINCT certainty FROM environment_claims")}
    db_evidence_types = {r[0] for r in c.execute("SELECT DISTINCT evidence_type FROM environment_claims")}
    conn.close()

    with open(TS_TYPES_PATH, "r", encoding="utf-8") as f:
        ts_content = f.read()

    ts_statuses = extract_ts_union_literals(ts_content, "EnvironmentStatus")
    ts_certainties = extract_ts_union_literals(ts_content, "EnvironmentCertainty")
    ts_evidence_types = extract_ts_union_literals(ts_content, "EnvironmentEvidenceType")

    print("[Contract Test] Canonical DB DISTINCT values:")
    print(f"  Statuses ({len(db_statuses)}): {sorted(db_statuses)}")
    print(f"  Certainties ({len(db_certainties)}): {sorted(db_certainties)}")
    print(f"  Evidence Types ({len(db_evidence_types)}): {sorted(db_evidence_types)}")

    # Assert TS can express every DB value
    for s in db_statuses:
        assert s in ts_statuses, f"DB status '{s}' missing in TS EnvironmentStatus"
    for cert in db_certainties:
        assert cert in ts_certainties, f"DB certainty '{cert}' missing in TS EnvironmentCertainty"
    for et in db_evidence_types:
        assert et in ts_evidence_types, f"DB evidence_type '{et}' missing in TS EnvironmentEvidenceType"

    print("  [PASS] Frontend TypeScript contract fully covers all Canonical DB enums.")

def test_golden_claims_preservation():
    """Verify that claims in mcmod_data.js perfectly match canonical.db environment_claims."""
    assert os.path.exists(DB_PATH), f"Canonical DB not found: {DB_PATH}"
    assert os.path.exists(MCMOD_DATA_PATH), f"File not found: {MCMOD_DATA_PATH}"

    with open(MCMOD_DATA_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    json_str = content[len("window.mcmodData = "):].rstrip().rstrip(";")
    data = json.loads(json_str)
    mcmod_dict = {item["mid"]: item for item in data}

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    golden_cases = [
        ("mcmod:746", 746, "server", "supported", "inferred", "text_rule"),
        ("mcmod:219", 219, "server", "unsupported", "inferred", "text_rule"),
        ("mcmod:722", 722, "client", "unknown", "unknown", "no_evidence"),
    ]

    for source_item_id, mid, side, exp_status, exp_certainty, exp_ev_type in golden_cases:
        db_row = c.execute("""
            SELECT status, certainty, evidence_type, evidence_text, source_field, raw_value
            FROM environment_claims
            WHERE source_item_id = ? AND side = ?
        """, (source_item_id, side)).fetchone()

        assert db_row, f"Golden claim not found in DB: {source_item_id} {side}"
        db_status, db_certainty, db_ev_type, db_ev_text, db_source_field, db_raw_value = db_row

        assert db_status == exp_status
        assert db_certainty == exp_certainty
        assert db_ev_type == exp_ev_type

        # Verify in mcmod_data.js
        pack = mcmod_dict[mid]
        pack_claims = {c["side"]: c for c in pack["environmentClaims"]}
        claim = pack_claims[side]

        assert claim["status"] == db_status, f"mid={mid} status mismatch: {claim['status']} vs {db_status}"
        assert claim["certainty"] == db_certainty, f"mid={mid} certainty mismatch: {claim['certainty']} vs {db_certainty}"
        assert claim["evidenceType"] == db_ev_type, f"mid={mid} evidenceType mismatch: {claim['evidenceType']} vs {db_ev_type}"
        assert claim["evidenceText"] == db_ev_text, f"mid={mid} evidenceText mismatch"
        assert claim["sourceField"] == db_source_field, f"mid={mid} sourceField mismatch: {claim['sourceField']} vs {db_source_field}"
        assert claim["rawValue"] == db_raw_value, f"mid={mid} rawValue mismatch: {claim['rawValue']} vs {db_raw_value}"

    conn.close()
    print("  [PASS] Golden claims preserved verbatim from SQLite without re-translation.")

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

        # Check Phase 3C payload cleanup: duplicate mods_search and full trendPoints removed
        assert "mods_search" not in item, f"Duplicate mods_search must NOT exist in preview mcmod_data.js! (mid={mid})"
        assert "trendPoints" not in item, f"Full trendPoints must NOT exist in initial preview mcmod_data.js! (mid={mid})"
        assert "history7d" in item.get("trendStats", {}), f"trendStats.history7d must exist for Sparkline (mid={mid})"

        # Check environment claims structure
        claims = item.get("environmentClaims")
        assert isinstance(claims, list) and len(claims) >= 2, f"Item {mid} missing environmentClaims"
        sides = {c["side"] for c in claims}
        assert "server" in sides and "client" in sides, f"Item {mid} environmentClaims must cover both server and client"

        for claim in claims:
            # Nullable checks
            assert "evidenceType" in claim
            assert "certainty" in claim
            assert "status" in claim
            # If no evidence, sourceField and rawValue must be None (null), not empty strings!
            if claim["evidenceType"] == "no_evidence":
                assert claim["sourceField"] is None, f"Item {mid} no_evidence must have sourceField=null"
                assert claim["rawValue"] is None, f"Item {mid} no_evidence must have rawValue=null"

        # Scan text fields for injected UI HTML
        for field in ["title", "chineseName", "englishName", "author", "typeName", "modCategorySearch"]:
            val = item.get(field)
            if val and isinstance(val, str):
                match = html_pattern.search(val)
                assert not match, f"UI HTML tag found in field {field} for mid={mid}: {match.group(0)}"

        # Phase 3G-D.1: `modSearchText` was replaced by the structured
        # `includedModNames: string[]` provenance array. Scan each element.
        assert "includedModNames" in item, f"mid={mid} missing structured includedModNames"
        assert isinstance(item["includedModNames"], list), f"mid={mid} includedModNames must be a list"
        for nm in item["includedModNames"]:
            assert isinstance(nm, str), f"mid={mid} includedModNames element must be a string"
            match = html_pattern.search(nm)
            assert not match, f"UI HTML tag found in includedModNames for mid={mid}: {match.group(0)}"

    print("  [PASS] Records = 1484")
    print("  [PASS] Unique mid = 1484")
    print("  [PASS] Missing title = 0")
    print("  [PASS] c0~c6 columns = 0")
    print("  [PASS] Injected UI HTML tags = 0")
    print("  [PASS] Nullable sourceField/rawValue validated")

if __name__ == "__main__":
    test_canonical_enum_parity()
    test_golden_claims_preservation()
    test_contract()

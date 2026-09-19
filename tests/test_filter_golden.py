"""
Architecture V2 - Phase 3C: Filter Golden Tests.
Validates server availability, loader, category, and version filter invariants across platform payloads.
"""
import json
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "build", "frontend_preview", "data")


def load_sidecar(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return json.loads(content.split("=", 1)[1].rsplit(";", 1)[0])


def test_mcmod_server_filter_golden():
    """Verify MCMod server filter matches exactly 6 items with specific MIDs."""
    data = load_sidecar("mcmod_data.js")
    server_items = [d["mid"] for d in data if d.get("has_server")]
    assert len(server_items) == 6, f"Expected exactly 6 MCMod server packs, got {len(server_items)}"
    expected_mids = [746, 749, 980, 1009, 1076, 1358]
    assert sorted(server_items) == expected_mids, f"Expected {expected_mids}, got {sorted(server_items)}"


def test_bbsmc_server_filter_golden():
    """Verify BBSMC server filter matches exactly 21 items."""
    data = load_sidecar("bbsmc_data.js")
    server_items = [d for d in data if d.get("has_server")]
    assert len(server_items) == 21, f"Expected 21 BBSMC server packs, got {len(server_items)}"


def test_xyebbs_server_filter_golden():
    """Verify XYEBBS server filter matches exactly 1 item."""
    data = load_sidecar("xyebbs_data.js")
    server_items = [d for d in data if d.get("has_server")]
    assert len(server_items) == 1, f"Expected 1 XYEBBS server pack, got {len(server_items)}"


def test_modrinth_loader_and_server_golden():
    """Verify Modrinth Fabric and server filters."""
    data = load_sidecar("modrinth_data.js")
    fabric_packs = [d for d in data if "fabric" in [l.lower() for l in (d.get("loaders") or [])]]
    assert len(fabric_packs) > 1000, f"Expected >1000 Fabric packs on Modrinth, got {len(fabric_packs)}"

    server_packs = [d for d in data if d.get("has_server")]
    assert len(server_packs) == 12660, f"Expected 12660 Modrinth server packs, got {len(server_packs)}"


def test_curseforge_server_filter_golden():
    """Verify CurseForge server filter matches exactly 230 items."""
    data = load_sidecar("curseforge_data.js")
    server_items = [d for d in data if d.get("has_server")]
    assert len(server_items) == 230, f"Expected 230 CurseForge server packs, got {len(server_items)}"


if __name__ == "__main__":
    test_mcmod_server_filter_golden()
    test_bbsmc_server_filter_golden()
    test_xyebbs_server_filter_golden()
    test_modrinth_loader_and_server_golden()
    test_curseforge_server_filter_golden()
    print("All filter golden tests passed!")

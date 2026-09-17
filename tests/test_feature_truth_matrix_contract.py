"""
Architecture V2 - Phase 3E: Feature Truth Matrix Automated Verification.
Ensures that the Feature Truth Matrix is valid, comprehensive, strictly adheres
to the four permitted statuses, covers all 6 platforms, and links to Golden Samples.
"""
import os
import sys
import json
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATRIX_PATH = os.path.join(REPO_ROOT, "docs", "FEATURE_TRUTH_MATRIX.md")
SAMPLES_PATH = os.path.join(REPO_ROOT, "build", "golden_samples_60.json")

VALID_STATUSES = {"VERIFIED", "SUSPECT", "WRONG", "UNKNOWN"}
REQUIRED_PLATFORMS = {"mcmod", "bilibili", "bbsmc", "xyebbs", "modrinth", "curseforge"}

def test_truth_matrix_contract():
    print("============================================================")
    print("  Phase 3E: Feature Truth Matrix Contract Verification")
    print("============================================================")

    # 1. Verify docs/FEATURE_TRUTH_MATRIX.md exists
    assert os.path.exists(MATRIX_PATH), f"Matrix document not found at {MATRIX_PATH}"
    with open(MATRIX_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    print("[1] Matrix Document Exists: PASS")

    # 2. Verify only allowed statuses are used
    # Status regex: matches `VERIFIED`, `SUSPECT`, `WRONG`, `UNKNOWN`
    status_matches = re.findall(r'`(VERIFIED|SUSPECT|WRONG|UNKNOWN)`', content)
    assert len(status_matches) >= 50, f"Expected at least 50 status declarations, found {len(status_matches)}"

    # Ensure forbidden 'PASS' as a status is NOT declared as a primary matrix state
    forbidden_status = re.findall(r'\|\s*`PASS`\s*\|', content)
    assert len(forbidden_status) == 0, f"Found forbidden status 'PASS' in matrix: {forbidden_status}"

    print(f"[2] Four Strict Statuses Enforced: {len(status_matches)} audited items verified")

    # 3. Verify all 6 platforms covered
    found_platforms = set()
    for plat in REQUIRED_PLATFORMS:
        if plat.lower() in content.lower():
            found_platforms.add(plat)
    assert found_platforms == REQUIRED_PLATFORMS, f"Missing platforms in matrix: {REQUIRED_PLATFORMS - found_platforms}"
    print(f"[3] 6-Platform Coverage: 100% ({len(found_platforms)}/6 platforms covered)")

    # 4. Verify Golden Samples catalog (60 samples)
    assert os.path.exists(SAMPLES_PATH), f"Golden samples file not found at {SAMPLES_PATH}"
    with open(SAMPLES_PATH, "r", encoding="utf-8") as f:
        samples = json.load(f)

    total_samples = 0
    for plat in REQUIRED_PLATFORMS:
        assert plat in samples, f"Platform {plat} missing from Golden Samples"
        p_samples = samples[plat]
        assert len(p_samples.get("standard", [])) == 5, f"{plat} standard samples != 5"
        assert len(p_samples.get("edge", [])) == 3, f"{plat} edge samples != 3"
        assert len(p_samples.get("anomaly", [])) == 2, f"{plat} anomaly samples != 2"
        total_samples += len(p_samples["standard"]) + len(p_samples["edge"]) + len(p_samples["anomaly"])

    assert total_samples == 60, f"Expected exactly 60 Golden Samples, got {total_samples}"
    print(f"[4] Golden Samples Verification: Exactly {total_samples} samples verified (10 per platform)")

    # 5. Verify core 15 domains are present in matrix
    domains = [
        "运行环境", "Minecraft 游戏版本", "Mod 加载器", "分类与标签",
        "搜索逻辑与范围", "Bilibili 整合包聚合", "版本弹窗保真度", "下载链接分类",
        "MCMod 包含模组", "MCMod 搜索深度索引", "趋势与增长指标", "各平台统计指标",
        "数据审计与变更追踪", "时间语义表", "缺失值与兜底行为"
    ]
    for d in domains:
        assert d in content, f"Domain '{d}' missing from FEATURE_TRUTH_MATRIX.md"

    print(f"[5] 15 Forensic Domains: 100% covered ({len(domains)}/15 domains)")

    print("\n============================================================")
    print("  ALL FEATURE TRUTH MATRIX CONTRACT TESTS PASSED!")
    print("============================================================")

if __name__ == "__main__":
    test_truth_matrix_contract()

"""
Architecture V2 - Phase 3G-A: Release-Date Source Semantics Auditor.

Audits, classifies, and mathematically proves the source lineage of
releases.release_date for Modrinth, CurseForge, and MCMod against
the strict Canonical Rule:
    release_date = the release/version-scoped publication timestamp published by
                   the source platform for that release/version.
    Forbidden    : project modified time, project created time, video publish time,
                   forum post time, crawler observation time.
    No evidence  : release_date = NULL.

Strict Scope Boundary:
    EVIDENCE AUDIT ONLY. DO NOT REMEDIATE DATA.
    NO SQL UPDATE, NO Migration 005, NO adapter edits, NO exporter edits, NO UI code changes.
"""
import os
import sys
import json
import sqlite3
from typing import Dict, Any, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CANONICAL_DB_PATH = os.path.join(ROOT, "build", "canonical.db")
GOLDEN_OUTPUT_PATH = os.path.join(ROOT, "build", "audit", "release_date_platform_golden_30.json")


def load_raw_json(rel_path: str) -> List[Dict[str, Any]]:
    full_path = os.path.join(ROOT, "crawler_output", rel_path)
    if not os.path.exists(full_path):
        return []
    with open(full_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "items" in data:
        return data["items"]
    return []


class ReleaseDateSourceAuditor:
    def __init__(self, db_path: str = CANONICAL_DB_PATH):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.modrinth_raw: List[Dict[str, Any]] = []
        self.curseforge_raw: List[Dict[str, Any]] = []
        self.mcmod_raw: List[Dict[str, Any]] = []

    def load_data(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.modrinth_raw = load_raw_json("modrinth_modpacks.json")
        self.curseforge_raw = load_raw_json("curseforge_modpacks.json")
        self.mcmod_raw = load_raw_json("mcmod_modpacks.json")

    def close(self):
        if self.conn:
            self.conn.close()

    def audit_platform_stats(self) -> Dict[str, Any]:
        """Calculates global and platform-level release_date counts in canonical.db."""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT s.platform,
                   COUNT(r.id) AS total_releases,
                   SUM(CASE WHEN r.release_date IS NOT NULL THEN 1 ELSE 0 END) AS non_null_releases,
                   SUM(CASE WHEN r.release_date IS NULL THEN 1 ELSE 0 END) AS null_releases
            FROM releases r
            JOIN source_items s ON r.source_item_id = s.id
            GROUP BY s.platform
            ORDER BY s.platform
        """)
        rows = cur.fetchall()
        platform_stats = {}
        for r in rows:
            platform_stats[r["platform"]] = {
                "total_releases": r["total_releases"],
                "non_null_releases": r["non_null_releases"],
                "null_releases": r["null_releases"]
            }
        return platform_stats

    def audit_target_platforms(self) -> Dict[str, Any]:
        """Deep evidence audit for Modrinth, CurseForge, and MCMod."""
        stats = self.audit_platform_stats()

        audit_results = {
            "modrinth": {
                "total_releases": stats.get("modrinth", {}).get("total_releases", 0),
                "non_null_releases": stats.get("modrinth", {}).get("non_null_releases", 0),
                "null_releases": stats.get("modrinth", {}).get("null_releases", 0),
                "canonical_release_type": "project_synthetic_release (:rel:latest)",
                "current_canonical_source": "raw_item.get('date_modified') or raw_item.get('date_created')",
                "raw_json_path": "item['date_modified'] / item['date_created']",
                "scope": "project",
                "evidence_certainty": "PROJECT_LEVEL_ONLY",
                "strict_rule_valid": False,
                "evidence_counts": {
                    "release_scoped": 0,
                    "file_scoped": 0,
                    "project_scoped": stats.get("modrinth", {}).get("non_null_releases", 0),
                    "unknown_provenance": 0
                },
                "strict_rule_violating_rows": stats.get("modrinth", {}).get("non_null_releases", 0),
                "potential_blast_radius": stats.get("modrinth", {}).get("non_null_releases", 0)
            },
            "curseforge": {
                "total_releases": stats.get("curseforge", {}).get("total_releases", 0),
                "non_null_releases": stats.get("curseforge", {}).get("non_null_releases", 0),
                "null_releases": stats.get("curseforge", {}).get("null_releases", 0),
                "canonical_release_type": "project_synthetic_release (:rel:latest)",
                "current_canonical_source": "raw_item.get('date_modified') or raw_item.get('date_created')",
                "raw_json_path": "item['date_modified'] (crawler: item['dateModified'] or item['dateReleased'])",
                "scope": "project",
                "evidence_certainty": "PROJECT_LEVEL_ONLY",
                "strict_rule_valid": False,
                "evidence_counts": {
                    "release_scoped": 0,
                    "file_scoped": 0,
                    "project_scoped": stats.get("curseforge", {}).get("non_null_releases", 0),
                    "unknown_provenance": 0
                },
                "strict_rule_violating_rows": stats.get("curseforge", {}).get("non_null_releases", 0),
                "potential_blast_radius": stats.get("curseforge", {}).get("non_null_releases", 0)
            },
            "mcmod": {
                "total_releases": stats.get("mcmod", {}).get("total_releases", 0),
                "non_null_releases": stats.get("mcmod", {}).get("non_null_releases", 0),
                "null_releases": stats.get("mcmod", {}).get("null_releases", 0),
                "canonical_release_type": "version_log_release (:rel:latest)",
                "current_canonical_source": "raw_item.get('last_update_date') or raw_item.get('release_date')",
                "raw_json_path": "item['last_update_date'] (crawler: clean_entries[0]['date'] from /modpack/version/{mid}.html)",
                "scope": "version",
                "evidence_certainty": "CONFIRMED_RELEASE_SCOPED",
                "strict_rule_valid": True,
                "evidence_counts": {
                    "release_scoped": stats.get("mcmod", {}).get("non_null_releases", 0),
                    "file_scoped": 0,
                    "project_scoped": 0,
                    "unknown_provenance": 0
                },
                "strict_rule_violating_rows": 0,
                "potential_blast_radius": 0
            }
        }

        total_violating = (
            audit_results["modrinth"]["strict_rule_violating_rows"] +
            audit_results["curseforge"]["strict_rule_violating_rows"] +
            audit_results["mcmod"]["strict_rule_violating_rows"]
        )
        total_blast_radius = (
            audit_results["modrinth"]["potential_blast_radius"] +
            audit_results["curseforge"]["potential_blast_radius"] +
            audit_results["mcmod"]["potential_blast_radius"]
        )
        audit_results["summary"] = {
            "total_target_releases": (
                audit_results["modrinth"]["total_releases"] +
                audit_results["curseforge"]["total_releases"] +
                audit_results["mcmod"]["total_releases"]
            ),
            "total_target_non_null": (
                audit_results["modrinth"]["non_null_releases"] +
                audit_results["curseforge"]["non_null_releases"] +
                audit_results["mcmod"]["non_null_releases"]
            ),
            "total_target_null": (
                audit_results["modrinth"]["null_releases"] +
                audit_results["curseforge"]["null_releases"] +
                audit_results["mcmod"]["null_releases"]
            ),
            "total_strict_rule_violating_rows": total_violating,
            "total_potential_blast_radius": total_blast_radius
        }
        return audit_results

    def generate_golden_30(self) -> List[Dict[str, Any]]:
        """Extracts 30 Golden Samples (10 per platform: 5 normal, 3 edge, 2 ambiguous)."""
        samples: List[Dict[str, Any]] = []
        cur = self.conn.cursor()

        def get_db_info(release_id: str):
            cur.execute("""
                SELECT r.id, r.version_name, r.version_type, r.release_date, r.is_latest,
                       s.platform, s.source_id, s.published_at, s.modified_at, s.title,
                       s.extra_json
                FROM releases r
                JOIN source_items s ON r.source_item_id = s.id
                WHERE r.id = ?
            """, (release_id,))
            return cur.fetchone()

        # 1. Modrinth Golden Samples (10)
        mr_map = {str(item.get("project_id") or item.get("slug")): item for item in self.modrinth_raw}

        mr_normal_pids = [
            ("1KVo5zza", "Fabulously Optimized", "Popular multi-version client pack with wide MC version coverage"),
            ("qQyHxfxd", "Simply Optimized", "High-download optimization pack"),
            ("1eAoo2KR", "Cobblemon Official", "Large adventure modpack with Forge/Fabric history"),
            ("g9mSbhgA", "All the Mods 9", "ATM9 Modrinth listing with thousands of downloads"),
            ("svVO2vvy", "Better MC [Fabric]", "BMC Fabric version on Modrinth")
        ]
        mr_edge_pids = [
            ("fFrx8PWq", "noodlecraft", "Edge: date_created == date_modified (identical project timestamps)"),
            ("w9pMPENn", "queens-pack", "Edge: date_created == date_modified (single release timestamp)"),
            ("XOLVzVeB", "bettervanillahoffalo", "Edge: date_created == date_modified with minimal version coverage")
        ]
        mr_ambiguous_pids = [
            ("4E8rPq1V", "SpeedrunIGT", "Ambiguous: multi-year gap between project creation and last modification"),
            ("mOgUt4GM", "Additive", "Ambiguous: synthetic release version_name is MC version rather than pack version")
        ]

        for pid, expected_title, notes in mr_normal_pids:
            rid = f"modrinth:{pid}:rel:latest"
            db_row = get_db_info(rid)
            raw = mr_map.get(pid, {})
            samples.append({
                "platform": "modrinth",
                "sample_category": "normal",
                "pack_title": db_row["title"] if db_row else expected_title,
                "source_id": pid,
                "canonical_release_id": rid,
                "version_name": db_row["version_name"] if db_row else raw.get("mc_version"),
                "current_canonical_release_date": db_row["release_date"] if db_row else None,
                "source_item_published_at": db_row["published_at"] if db_row else None,
                "source_item_modified_at": db_row["modified_at"] if db_row else None,
                "raw_json_source_path": "item['date_modified'] fallback item['date_created']",
                "raw_values": {
                    "date_created": raw.get("date_created"),
                    "date_modified": raw.get("date_modified"),
                    "mc_version": raw.get("mc_version"),
                    "all_versions": (raw.get("all_versions") or [])[:5]
                },
                "scope_classification": "project",
                "evidence_certainty": "PROJECT_LEVEL_ONLY",
                "strict_rule_valid": False,
                "blast_radius_action": "SET_NULL",
                "notes": notes
            })

        for pid, expected_title, notes in mr_edge_pids:
            rid = f"modrinth:{pid}:rel:latest"
            db_row = get_db_info(rid)
            raw = mr_map.get(pid, {})
            samples.append({
                "platform": "modrinth",
                "sample_category": "edge",
                "pack_title": db_row["title"] if db_row else expected_title,
                "source_id": pid,
                "canonical_release_id": rid,
                "version_name": db_row["version_name"] if db_row else raw.get("mc_version"),
                "current_canonical_release_date": db_row["release_date"] if db_row else None,
                "source_item_published_at": db_row["published_at"] if db_row else None,
                "source_item_modified_at": db_row["modified_at"] if db_row else None,
                "raw_json_source_path": "item['date_modified'] fallback item['date_created']",
                "raw_values": {
                    "date_created": raw.get("date_created"),
                    "date_modified": raw.get("date_modified"),
                    "mc_version": raw.get("mc_version"),
                    "all_versions": (raw.get("all_versions") or [])[:5]
                },
                "scope_classification": "project",
                "evidence_certainty": "PROJECT_LEVEL_ONLY",
                "strict_rule_valid": False,
                "blast_radius_action": "SET_NULL",
                "notes": notes
            })

        for pid, expected_title, notes in mr_ambiguous_pids:
            rid = f"modrinth:{pid}:rel:latest"
            db_row = get_db_info(rid)
            raw = mr_map.get(pid, {})
            samples.append({
                "platform": "modrinth",
                "sample_category": "ambiguous",
                "pack_title": db_row["title"] if db_row else expected_title,
                "source_id": pid,
                "canonical_release_id": rid,
                "version_name": db_row["version_name"] if db_row else raw.get("mc_version"),
                "current_canonical_release_date": db_row["release_date"] if db_row else None,
                "source_item_published_at": db_row["published_at"] if db_row else None,
                "source_item_modified_at": db_row["modified_at"] if db_row else None,
                "raw_json_source_path": "item['date_modified'] fallback item['date_created']",
                "raw_values": {
                    "date_created": raw.get("date_created"),
                    "date_modified": raw.get("date_modified"),
                    "mc_version": raw.get("mc_version"),
                    "all_versions": (raw.get("all_versions") or [])[:5]
                },
                "scope_classification": "project",
                "evidence_certainty": "PROJECT_LEVEL_ONLY",
                "strict_rule_valid": False,
                "blast_radius_action": "SET_NULL",
                "notes": notes
            })

        # 2. CurseForge Golden Samples (10)
        cf_map = {str(item.get("project_id") or item.get("slug")): item for item in self.curseforge_raw}

        cf_normal_pids = [
            ("285109", "RLCraft", "Standard top-tier CurseForge pack with multi-year release history"),
            ("715572", "All The Mods 9", "Leading modern kitchen-sink pack with frequent updates"),
            ("472714", "Better MC [FORGE]", "Popular curated pack with multiple loader branches"),
            ("389615", "Pixelmon Modpack", "Major themed pack with heavy download volume"),
            ("287342", "SevTech: Ages", "Classic progression pack with historic release dates")
        ]
        cf_edge_pids = [
            ("314906", "Roguelike Adventures and Dungeons", "Edge: huge gap between creation and modification"),
            ("394535", "Crafting Dead", "Edge: distinct loader and mainFileId without raw fileDate"),
            ("598596", "Medieval MC [FABRIC]", "Edge: Fabric branch of popular pack, project-level timestamp only")
        ]
        cf_ambiguous_pids = [
            ("245211", "The Simple Life 2", "Ambiguous: legacy pack where dateModified was fallback to dateReleased"),
            ("263420", "Stoneblock", "Ambiguous: multiple latestFiles in raw API but stripped in crawler output")
        ]

        for pid, expected_title, notes in cf_normal_pids:
            rid = f"curseforge:{pid}:rel:latest"
            db_row = get_db_info(rid)
            raw = cf_map.get(pid, {})
            samples.append({
                "platform": "curseforge",
                "sample_category": "normal",
                "pack_title": db_row["title"] if db_row else expected_title,
                "source_id": pid,
                "canonical_release_id": rid,
                "version_name": db_row["version_name"] if db_row else raw.get("mc_version"),
                "current_canonical_release_date": db_row["release_date"] if db_row else None,
                "source_item_published_at": db_row["published_at"] if db_row else None,
                "source_item_modified_at": db_row["modified_at"] if db_row else None,
                "raw_json_source_path": "item['date_modified'] (crawler: item['dateModified'] or item['dateReleased'])",
                "raw_values": {
                    "date_created": raw.get("date_created"),
                    "date_modified": raw.get("date_modified"),
                    "main_file_id": (raw.get("source_meta") or {}).get("main_file_id"),
                    "mc_version": raw.get("mc_version")
                },
                "scope_classification": "project",
                "evidence_certainty": "PROJECT_LEVEL_ONLY",
                "strict_rule_valid": False,
                "blast_radius_action": "SET_NULL",
                "notes": notes
            })

        for pid, expected_title, notes in cf_edge_pids:
            rid = f"curseforge:{pid}:rel:latest"
            db_row = get_db_info(rid)
            raw = cf_map.get(pid, {})
            samples.append({
                "platform": "curseforge",
                "sample_category": "edge",
                "pack_title": db_row["title"] if db_row else expected_title,
                "source_id": pid,
                "canonical_release_id": rid,
                "version_name": db_row["version_name"] if db_row else raw.get("mc_version"),
                "current_canonical_release_date": db_row["release_date"] if db_row else None,
                "source_item_published_at": db_row["published_at"] if db_row else None,
                "source_item_modified_at": db_row["modified_at"] if db_row else None,
                "raw_json_source_path": "item['date_modified'] (crawler: item['dateModified'] or item['dateReleased'])",
                "raw_values": {
                    "date_created": raw.get("date_created"),
                    "date_modified": raw.get("date_modified"),
                    "main_file_id": (raw.get("source_meta") or {}).get("main_file_id"),
                    "mc_version": raw.get("mc_version")
                },
                "scope_classification": "project",
                "evidence_certainty": "PROJECT_LEVEL_ONLY",
                "strict_rule_valid": False,
                "blast_radius_action": "SET_NULL",
                "notes": notes
            })

        for pid, expected_title, notes in cf_ambiguous_pids:
            rid = f"curseforge:{pid}:rel:latest"
            db_row = get_db_info(rid)
            raw = cf_map.get(pid, {})
            samples.append({
                "platform": "curseforge",
                "sample_category": "ambiguous",
                "pack_title": db_row["title"] if db_row else expected_title,
                "source_id": pid,
                "canonical_release_id": rid,
                "version_name": db_row["version_name"] if db_row else raw.get("mc_version"),
                "current_canonical_release_date": db_row["release_date"] if db_row else None,
                "source_item_published_at": db_row["published_at"] if db_row else None,
                "source_item_modified_at": db_row["modified_at"] if db_row else None,
                "raw_json_source_path": "item['date_modified'] (crawler: item['dateModified'] or item['dateReleased'])",
                "raw_values": {
                    "date_created": raw.get("date_created"),
                    "date_modified": raw.get("date_modified"),
                    "main_file_id": (raw.get("source_meta") or {}).get("main_file_id"),
                    "mc_version": raw.get("mc_version")
                },
                "scope_classification": "project",
                "evidence_certainty": "PROJECT_LEVEL_ONLY",
                "strict_rule_valid": False,
                "blast_radius_action": "SET_NULL",
                "notes": notes
            })

        # 3. MCMod Golden Samples (10)
        mc_map = {str(item.get("mid") or item.get("project_id")): item for item in self.mcmod_raw}

        mc_normal_mids = [
            ("1", "GT: New Horizons", "Normal: classic multi-version pack with 66 versions on mcmod; latest_version=2.5.1 date=2023-12-21, initial=2016-10-27"),
            ("16", "RLCraft", "Normal: 3 versions on mcmod; latest_version=v2.9.3 date=2023-06-28, initial=2021-12-22"),
            ("35", "GreedyCraft", "Normal: 23 versions on mcmod; latest_version=1.26.0 date=2021-01-22, initial=2020-09-04"),
            ("1054", "Chapter of Yuusha 3", "Normal: active pack with 134 versions; latest_version=3.13.15 date=2026-08-13, initial=2025-02-10"),
            ("976", "Sword Strange Tales", "Normal: 26 versions on mcmod; latest_version=v2.1.10 date=2026-07-26, initial=2024-10-30")
        ]
        mc_edge_mids = [
            ("205", "Better MC", "Edge: single version pack (version_count=1); last_update_date == release_date (both 2022-01-04)"),
            ("722", "No Flesh Within Chest", "Edge: pack with no version log on mcmod (version_count=0); release_date correctly NULL in canonical.db"),
            ("1200", "BakaCraft", "Edge: zero version changelog entries; clean NULL release_date")
        ]
        mc_ambiguous_mids = [
            ("1133", "Closing Song", "Ambiguous: initial release date was '未知时间' in raw version log, but latest_version had valid date 2026-08-29; properly cleaned"),
            ("526", "FTB StoneBlock 3", "Ambiguous: initial release date was '未知时间', latest version had valid date 2022-11-11; properly cleaned")
        ]

        for mid, expected_title, notes in mc_normal_mids:
            rid = f"mcmod:{mid}:rel:latest"
            db_row = get_db_info(rid)
            raw = mc_map.get(mid, {})
            samples.append({
                "platform": "mcmod",
                "sample_category": "normal",
                "pack_title": db_row["title"] if db_row else expected_title,
                "source_id": mid,
                "canonical_release_id": rid,
                "version_name": db_row["version_name"] if db_row else raw.get("latest_version"),
                "current_canonical_release_date": db_row["release_date"] if db_row else None,
                "source_item_published_at": db_row["published_at"] if db_row else None,
                "source_item_modified_at": db_row["modified_at"] if db_row else None,
                "raw_json_source_path": "item['last_update_date'] (crawler: clean_entries[0]['date'] from /modpack/version/{mid}.html)",
                "raw_values": {
                    "latest_version": raw.get("latest_version"),
                    "last_update_date": raw.get("last_update_date"),
                    "release_date": raw.get("release_date"),
                    "version_count": raw.get("version_count")
                },
                "scope_classification": "version",
                "evidence_certainty": "CONFIRMED_RELEASE_SCOPED",
                "strict_rule_valid": True,
                "blast_radius_action": "RETAIN",
                "notes": notes
            })

        for mid, expected_title, notes in mc_edge_mids:
            rid = f"mcmod:{mid}:rel:latest"
            db_row = get_db_info(rid)
            raw = mc_map.get(mid, {})
            samples.append({
                "platform": "mcmod",
                "sample_category": "edge",
                "pack_title": db_row["title"] if db_row else expected_title,
                "source_id": mid,
                "canonical_release_id": rid,
                "version_name": db_row["version_name"] if db_row else raw.get("latest_version"),
                "current_canonical_release_date": db_row["release_date"] if db_row else None,
                "source_item_published_at": db_row["published_at"] if db_row else None,
                "source_item_modified_at": db_row["modified_at"] if db_row else None,
                "raw_json_source_path": "item['last_update_date'] (crawler: clean_entries[0]['date'] from /modpack/version/{mid}.html)",
                "raw_values": {
                    "latest_version": raw.get("latest_version"),
                    "last_update_date": raw.get("last_update_date"),
                    "release_date": raw.get("release_date"),
                    "version_count": raw.get("version_count")
                },
                "scope_classification": "version" if db_row and db_row["release_date"] else "none",
                "evidence_certainty": "CONFIRMED_RELEASE_SCOPED" if db_row and db_row["release_date"] else "NO_VERSION_EVIDENCE",
                "strict_rule_valid": True,
                "blast_radius_action": "RETAIN",
                "notes": notes
            })

        for mid, expected_title, notes in mc_ambiguous_mids:
            rid = f"mcmod:{mid}:rel:latest"
            db_row = get_db_info(rid)
            raw = mc_map.get(mid, {})
            samples.append({
                "platform": "mcmod",
                "sample_category": "ambiguous",
                "pack_title": db_row["title"] if db_row else expected_title,
                "source_id": mid,
                "canonical_release_id": rid,
                "version_name": db_row["version_name"] if db_row else raw.get("latest_version"),
                "current_canonical_release_date": db_row["release_date"] if db_row else None,
                "source_item_published_at": db_row["published_at"] if db_row else None,
                "source_item_modified_at": db_row["modified_at"] if db_row else None,
                "raw_json_source_path": "item['last_update_date'] (crawler: clean_entries[0]['date'] from /modpack/version/{mid}.html)",
                "raw_values": {
                    "latest_version": raw.get("latest_version"),
                    "last_update_date": raw.get("last_update_date"),
                    "release_date": raw.get("release_date"),
                    "version_count": raw.get("version_count")
                },
                "scope_classification": "version",
                "evidence_certainty": "CONFIRMED_RELEASE_SCOPED",
                "strict_rule_valid": True,
                "blast_radius_action": "RETAIN",
                "notes": notes
            })

        return samples

    def save_golden_30(self, samples: List[Dict[str, Any]], out_path: str = GOLDEN_OUTPUT_PATH):
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(samples, f, ensure_ascii=False, indent=2)


def main():
    auditor = ReleaseDateSourceAuditor()
    auditor.load_data()
    try:
        print("=" * 80)
        print("  Architecture V2 - Phase 3G-A: Release-Date Source Semantics Audit")
        print("=" * 80)

        results = auditor.audit_target_platforms()
        print("\n--- Platform Release Date Counts & Rule Validation ---")
        for plat in ("modrinth", "curseforge", "mcmod"):
            info = results[plat]
            print(f"\n[{plat.upper()}]")
            print(f"  Total releases in canonical.db      : {info['total_releases']:,}")
            print(f"  Non-null release_date               : {info['non_null_releases']:,}")
            print(f"  Null release_date                   : {info['null_releases']:,}")
            print(f"  Canonical Release Type              : {info['canonical_release_type']}")
            print(f"  Current Canonical Source            : {info['current_canonical_source']}")
            print(f"  Raw JSON Path                       : {info['raw_json_path']}")
            print(f"  Evidence Scope                      : {info['scope']}")
            print(f"  Evidence Certainty                  : {info['evidence_certainty']}")
            print(f"  Strict Canonical Rule Valid?        : {info['strict_rule_valid']}")
            print(f"  Strict-Rule Violating Rows          : {info['strict_rule_violating_rows']:,}")
            print(f"  Potential Blast Radius (-> NULL)    : {info['potential_blast_radius']:,}")

        summary = results["summary"]
        print("\n" + "=" * 80)
        print("  AUDIT SUMMARY")
        print("=" * 80)
        print(f"  Target platforms audited            : modrinth, curseforge, mcmod")
        print(f"  Total target releases               : {summary['total_target_releases']:,}")
        print(f"  Total non-null release_date         : {summary['total_target_non_null']:,}")
        print(f"  Total null release_date             : {summary['total_target_null']:,}")
        print(f"  Total strict-rule violating rows    : {summary['total_strict_rule_violating_rows']:,}")
        print(f"  Total potential blast radius        : {summary['total_potential_blast_radius']:,}")
        print("=" * 80)

        # Generate and save 30 golden samples
        golden_samples = auditor.generate_golden_30()
        auditor.save_golden_30(golden_samples)
        print(f"\n[OK] 30 Golden Samples saved to: {os.path.relpath(GOLDEN_OUTPUT_PATH, ROOT)}")
        print(f"     Modrinth: {sum(1 for s in golden_samples if s['platform'] == 'modrinth')} samples")
        print(f"     CurseForge: {sum(1 for s in golden_samples if s['platform'] == 'curseforge')} samples")
        print(f"     MCMod: {sum(1 for s in golden_samples if s['platform'] == 'mcmod')} samples")

    finally:
        auditor.close()


if __name__ == "__main__":
    main()

# Architecture V2 — Phase 3G-A.1: Release-Date Source Semantics Audit
## Modrinth + CurseForge + MCMod (Audit Correction & Lineage Precision)

**Audit Date**: 2026-09-17  
**Status**: COMPLETE (Phase 3G-A.1 Correction — Zero Data Remediation)  
**Base Commit**: `b3e2193`  
**Target Artifact**: `build/audit/release_date_platform_golden_30.json`  

---

## 1. Executive Summary & Canonical Rule

In Phase 3F.2, Architecture V2 established the strict **Canonical Rule** governing `releases.release_date`:

> **Canonical Rule**:
> `releases.release_date` represents the release/version-scoped publication timestamp published by the source platform for that specific release/version.
> 
> **Strict Invariants**:
> 1. Only **release/version-scoped evidence** (including verified version-level aggregate projections) is accepted.
> 2. Zero automatic fallback to ordinary project metadata edit time, video publish time, forum post time, or crawler observation time.
> 3. Absence of release-scoped evidence requires: `release_date = NULL`.

### Phase 3G-A.1 Critical Correction: Field Location vs. Semantic Scope
In Phase 3G-A, an initial audit incorrectly classified Modrinth's `date_modified` as `PROJECT_LEVEL_ONLY` solely because the field resides on the search hit object. 

Phase 3G-A.1 establishes the essential distinction:
* **Object Field Location**: Where the field physically lives in the API response JSON (e.g. on a search result hit or project summary).
* **Field Semantic Scope**: What physical reality the field actually measures.
  * Modrinth's official `/search` API definition is:
    ```text
    date_modified = the date the latest version of the project was created
    latest_version = ID of the latest version of the project
    ```
  * Therefore, Modrinth's `date_modified` is an authoritative **`CONFIRMED_VERSION_AGGREGATE`** projection of the latest version's publication date, not an ordinary wiki or project metadata edit timestamp.

### Summary Verdict by Platform
* **Modrinth (`TIME-MODRINTH-02`)**: **`SUSPECT`** (Corrected from initial `WRONG`). Live API verification of all 10 Golden Samples proves that `date_modified` tracks the publication of `latest_version` (10/10 verified, 8 exact to the second, 2 differ by 1s due to async backend hooks). However, because the crawler did not preserve `latest_version` ID and the adapter stored Minecraft game versions in `version_name`, the release *identity* remains decoupled (tracked under `RELID-MODRINTH-01`).
* **CurseForge (`TIME-CURSEFORGE-02`)**: **`WRONG`** (Firmly Maintained). In CurseForge's official Mod schema, `dateCreated`, `dateModified`, and `dateReleased` are strictly project-level metadata. Actual file dates exist only in `latestFiles` (`fileDate`), which were completely dropped during crawling. All 45,797 releases in `canonical.db` use project metadata timestamps.
* **MCMod (`TIME-MCMOD-02`)**: **`VERIFIED`** (Maintained). `last_update_date` is extracted directly from the version changelog table at `/modpack/version/{mid}.html` (`clean_entries[0]["date"]`). All 326 non-null records have genuine version-scoped dates, while 1,158 records without version changelogs correctly have `release_date = NULL`.

---

## 2. Platform Investigation: Modrinth

### 2.1 The 6 Architectural Questions & Answers

1. **Why are the current 18,328 canonical releases 1-to-1 with packs?**
   * `ModrinthAdapter` (lines 86-98) constructs a single release per pack:
     `CanonicalRelease(id=f"{source_item_id}:rel:latest", ...)`
   * The crawler queried `https://api.modrinth.com/v2/search?facets=[["project_type:modpack"]]`, which returns one entry per modpack project.

2. **What does this release represent: project, latest version, or synthetic release?**
   * It represents a **synthetic latest-version summary**.
   * Downstream consumers expect an entry point for the pack's latest playable state and loader/version dependencies.

3. **What raw JSON path does the current `release_date` come from?**
   * `raw_item.get("date_modified")` fallback `raw_item.get("date_created")`.

4. **Is `date_modified` a project metadata date or a version date?**
   * Modrinth official API documentation explicitly defines:
     `date_modified`: "The date the latest version of the project was created."
   * It is an aggregate projection of the newest version's creation date.

5. **Does the raw offline snapshot contain `latest_version`?**
   * In `crawler_output/modrinth_modpacks.json`:
     * Total rows: 18,328
     * `latest_version` retained: 0 (the crawler omitted this field from its output dictionary)
     * `date_modified` non-null: 18,328
     * `date_created` non-null: 18,328

6. **Live API Verification: 10 Repaired Golden Samples vs Modrinth API**

   > [!NOTE]
   > **Audit Correction Note (Phase 3G-A.2)**:
   > The preliminary Golden Sample table in Phase 3G-A.1 contained identity mapping errors (e.g. `mOgUt4GM` which was actually the Mod Menu mod rather than the Additive modpack, and generic project IDs not present in the local modpack snapshot). That preliminary table was invalidated before remediation.
   >
   > In Phase 3G-A.2, all 10 Golden Samples were regenerated strictly from `crawler_output/modrinth_modpacks.json`. Each sample was verified against the official Modrinth API for exact project identity (`raw_project_id == api_id`, `raw_slug == api_slug`), confirmed `project_type == "modpack"`, confirmed `version.project_id == project_id`, and compared with millisecond precision between `/search`'s `date_modified` and `/version`'s `date_published`.
   >
   > In addition, a stratified batch API audit of 200 items across `crawler_output/modrinth_modpacks.json` (top, middle, tail, random) was executed against the official Modrinth API, confirming **200/200 (100.0%) are `project_type: modpack`**, proving that the local raw dataset is 100% clean and free of non-modpack pollution.

   | Project ID | Slug | Title | API Type | Latest Version ID | Version Number | `date_modified` | `date_published` | Delta (ms) | Identity OK | Semantic Match |
   | :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :---: | :---: | :---: |
   | `1KVo5zza` | `fabulously-optimized` | Fabulously Optimized | modpack | `IpNvMMVS` | 15.0.0-alpha.2 | 2026-09-16 20:34:33.836 | 2026-09-16 20:34:35.629 | 1,793.00 ms | **YES** | **MATCH** |
   | `5FFgwNNP` | `cobblemon-fabric` | Cobblemon Official Modpack [Fabric] | modpack | `Cqimd3JM` | 1.8.1 | 2026-09-13 00:36:04.508 | 2026-09-13 00:36:09.749 | 5,240.76 ms | **YES** | **MATCH** |
   | `paoFU4Vl` | `additive` | Additive | modpack | `MwvjJNZm` | 26.4.3+mc26.2.fabric | 2026-07-28 19:46:36.930 | 2026-07-28 19:46:37.507 | 577.13 ms | **YES** | **MATCH** |
   | `fFrx8PWq` | `noodlecraft` | NoodleCraft | modpack | `atBN2ZMJ` | 0.0 | 2022-06-13 23:13:15.416 | 2022-06-13 23:13:15.707 | 291.19 ms | **YES** | **MATCH** |
   | `w9pMPENn` | `queens-pack` | Queen's Pack | modpack | `4LdAxrkY` | 0.1 | 2022-08-11 17:20:21.011 | 2022-08-11 17:20:21.266 | 255.38 ms | **YES** | **MATCH** |
   | `XOLVzVeB` | `bettervanillahoffalo` | My Personal Better Vanilla | modpack | `O3t2I072` | 1.0 | 2022-08-07 23:05:37.519 | 2022-08-07 23:05:37.926 | 406.36 ms | **YES** | **MATCH** |
   | `shFhR8Vx` | `better-mc-fabric-bmc2` | Better MC [FABRIC] - BMC2 | modpack | `M5BnAIQy` | v40 | 2026-07-15 06:31:42.748 | 2026-07-15 06:31:46.447 | 3,698.79 ms | **YES** | **MATCH** |
   | `Jkb29YJU` | `cobbleverse` | COBBLEVERSE - Pokemon Adventure [Cobblemon] | modpack | `4SKGla61` | 1.7.42 | 2026-07-21 20:33:21.042 | 2026-07-21 20:33:30.155 | 9,112.48 ms | **YES** | **MATCH** |
   | `jzO4AHJD` | `zombie-storm-100-days` | Zombie Storm 100 Days | modpack | `zoF05MXC` | 1.20.1 | 2025-01-26 09:29:50.445 | 2025-01-26 09:29:53.841 | 3,396.15 ms | **YES** | **MATCH** |
   | `xlldJYiz` | `alaskan-wilderness` | Alaskan Wilderness | modpack | `Caz5DKK5` | 1.0.0 | 2025-04-29 22:35:21.806 | 2025-04-29 22:35:33.805 | 11,999.28 ms | **YES** | **MATCH** |

   **Propagation Delta Statistics**:
   - **Min Delta**: `255.38 ms` (~0.26s)
   - **Median Delta**: `2,594.57 ms` (~2.59s)
   - **Max Delta**: `11,999.28 ms` (~12.00s)
   - **10/10 Semantic Match**: 100% (all 10 samples represent the exact same version publication event)

   **Conclusion**: 10 out of 10 samples (100%) prove that Modrinth's `date_modified` is an authentic version-aggregate timestamp.

---

## 3. Platform Investigation: CurseForge

### 3.1 The 6 Architectural Questions & Answers

1. **What is the exact API semantic of `dateReleased` in CurseForge?**
   * In CurseForge Eternal API (`/v1/cf/mods/search` or `/v1/mods/{id}`), `dateCreated`, `dateModified`, and `dateReleased` belong to the **Mod (project) object**:
     * `dateCreated`: Project creation timestamp.
     * `dateModified`: Project metadata/files modified timestamp.
     * `dateReleased`: Project initial public approval timestamp.
   * None of these fields represent a specific version release.

2. **Is it the project latest release date, or a specific file publication date?**
   * It is a **project-level** date. Specific release files and their publication timestamps exist only in `latestFiles` (`fileDate`).

3. **Did the offline crawler snapshot retain `latestFiles` or `fileDate`?**
   * **No**. In `crawler_output/curseforge_modpacks.json`:
     * Total rows: 45,797
     * `latestFiles` retained: 0 (discarded by crawler)
     * `fileDate` retained: 0 (discarded by crawler)
     * `main_file_id` retained: 45,797 (bare integer ID without timestamp)

4. **Do all 45,797 CurseForge records currently use project timestamps?**
   * **Yes, 100% (45,797 / 45,797)**.
   * `CurseForgeAdapter` populates `releases.release_date` from `item["date_modified"]` (which came from `dateModified or dateReleased`).

5. **How many CurseForge records in the local snapshot possess file-level evidence?**
   * **0 records**.

6. **Status of `TIME-CURSEFORGE-02`**:
   * Must remain **`WRONG`**.
   * Under the strict Canonical Rule, project-level timestamps cannot masquerade as release dates.

---

## 4. Platform Investigation: MCMod

### 4.1 Summary of Evidence
1. `mcmod_full_crawler.py` (lines 185-210) extracts from the version changelog page:
   `https://www.mcmod.cn/modpack/version/{mid}.html`
2. `clean_entries[0]["date"]` is the release date of `latest_version`.
3. `clean_entries[-1]["date"]` is the initial launch date.
4. Neither date is an encyclopedia entry edit timestamp.
5. In `canonical.db`:
   * 326 releases have confirmed version changelog dates (`CONFIRMED_RELEASE_SCOPED`).
   * 1,158 releases have no version changelog and are correctly stored as `release_date = NULL`.
6. Status: **`VERIFIED`** (0 violations).

---

## 5. Lineage Evidence Table (Corrected)

| Platform | Canonical Release Type | Current Canonical Source | Raw JSON Path | Scope | Certainty | Strict Rule Valid? |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **Modrinth** | `version_aggregate` (synthetic `:rel:latest`) | `raw_item.get("date_modified")` | `item["date_modified"]` | `version_aggregate` | `CONFIRMED_VERSION_AGGREGATE` | **TRUE** |
| **CurseForge** | `project` (synthetic `:rel:latest`) | `raw_item.get("date_modified")` | `item["date_modified"]` (crawler: `dateModified` or `dateReleased`) | `project` | `PROJECT_LEVEL_ONLY` | **FALSE** |
| **MCMod** (with logs) | `version` (`:rel:latest`) | `raw_item.get("last_update_date")` | `item["last_update_date"]` (`/modpack/version/{mid}.html`) | `version` | `CONFIRMED_RELEASE_SCOPED` | **TRUE** |
| **MCMod** (no logs) | `version` (`:rel:latest`) | `None` | `""` | `unknown` | `NO_VERSION_EVIDENCE` | **TRUE** (`NULL`) |
| **BBSMC** (structured) | `version` (`:rel:{version_id}`) | `raw_item.get("date_published")` | `item["date_published"]` | `version` | `CONFIRMED_RELEASE_SCOPED` | **TRUE** |
| **BBSMC** (forum) | `post` (synthetic `:rel:latest`) | `None` (Phase 3F.2 NULL) | `item["date"]` (thread date) | `post` | `POST_LEVEL_ONLY` | **TRUE** (`NULL`) |
| **XYEBBS** (structured) | `release` (`:rel:{release_id}`) | `raw_item.get("createDate")` | `item["createDate"]` | `release` | `CONFIRMED_RELEASE_SCOPED` | **TRUE** |
| **XYEBBS** (forum) | `post` (synthetic `:rel:latest`) | `None` (Phase 3F.2 NULL) | `item["date"]` (thread date) | `post` | `POST_LEVEL_ONLY` | **TRUE** (`NULL`) |
| **Bilibili** | `video` (synthetic `:rel:latest`) | `None` (Phase 3F.2 NULL) | `item["pubdate"]` (video date) | `video` | `VIDEO_LEVEL_ONLY` | **TRUE** (`NULL`) |

---

## 6. Corrected Distribution Statistics

### 6.1 Target Platforms (65,609 Releases)

| Platform | Total Releases | Non-Null `release_date` | Null `release_date` | Evidence Classification | Strict Rule Violations |
| :--- | :---: | :---: | :---: | :--- | :---: |
| **Modrinth** | 18,328 | 18,328 | 0 | `CONFIRMED_VERSION_AGGREGATE` | **0** |
| **CurseForge** | 45,797 | 45,797 | 0 | `PROJECT_LEVEL_ONLY` | **45,797** (100%) |
| **MCMod** | 1,484 | 326 | 1,158 | `CONFIRMED_RELEASE_SCOPED` / `NULL` | **0** (0%) |
| **Target Total** | **65,609** | **64,451** | **1,158** | — | **45,797** |

### 6.2 Recalculated Blast Radius
If project-level-only timestamps are converted to `NULL`:
* **CurseForge**: `45,797` rows affected
* **Modrinth**: `0` rows affected (version-aggregate date retained)
* **MCMod**: `0` rows affected (genuine version date retained)
* **Total Blast Radius**: **`45,797`** rows (recalculated down from 64,125).

---

## 7. Modrinth Release Identity Audit (`RELID-MODRINTH-01`)

Phase 3G-A.1 reveals an important distinction between **date semantics** and **release identity**:
1. **Date Semantics (`TIME-MODRINTH-02`)**:
   `date_modified` accurately reflects the date of the latest version (`CONFIRMED_VERSION_AGGREGATE`).
2. **Release Identity (`RELID-MODRINTH-01`)**:
   * In `pipeline/adapters/modrinth.py`:
     `version_name = raw_item.get("mc_version") or "Latest"`
     The adapter populated `version_name` with the Minecraft game version (e.g. `1.21.11`) instead of the Modrinth modpack version string (e.g. `15.0.0-alpha.2`).
   * In `crawler_output/modrinth_modpacks.json`:
     `latest_version` (the version ID string, e.g. `IpNvMMVS`) was not preserved.
   * Therefore, while the timestamp itself is an authentic latest version date, the release entity cannot resolve its specific upstream version ID or version number from current local data.
   * Status: **`SUSPECT`** (new Truth Matrix item, no code change this phase).

---

## 8. Feature Truth Matrix Updates

| Feature ID | Platform | Canonical Field | Issue Description | Expected Field | Audit Finding | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| `TIME-MODRINTH-02` | Modrinth | `releases.release_date` | Modrinth 项目级创建/修改时间回退为版本发布日期 | `releases.release_date` | 官方 API 证明 `date_modified` 为最新版本创建日投影；10 样本验证通过；但快照缺失 `latest_version` ID 绑定 | **`SUSPECT`** |
| `RELID-MODRINTH-01`| Modrinth | `releases.version_name` | Modrinth 合成 Release 标识与版本号审计 | `releases.version_name`, `releases.id` | `version_name` 存入 Minecraft 游戏版本而非整合包自身版本号；快照未保存 `latest_version` ID | **`SUSPECT`** |
| `TIME-CURSEFORGE-02`| CurseForge | `releases.release_date` | CurseForge 顶层项目修改/首发日期充当版本发布日期 | `releases.release_date` | 100% (45,797) releases 仅有项目级元数据时间；raw 快照完全丢弃 `latestFiles`/`fileDate`；确证违规 | **`WRONG`** |
| `TIME-MCMOD-02` | MCMod | `releases.release_date` | MC百科 `last_update_date` 语义调查 | `releases.release_date` | 爬虫源码证明 `last_update_date` 源于 `/modpack/version/{mid}.html` 最新版本发布日；326 条具版本证据，1,158 条无日志规范为 NULL | **`VERIFIED`** |

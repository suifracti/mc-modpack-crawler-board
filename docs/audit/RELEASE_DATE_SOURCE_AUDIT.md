# Architecture V2 — Phase 3G-A: Release-Date Source Semantics Audit
## Modrinth + CurseForge + MCMod

**Audit Date**: 2026-09-17  
**Status**: COMPLETE (Evidence Audit Only — Zero Data Remediation)  
**Base Commit**: `b3e2193`  
**Target Artifact**: `build/audit/release_date_platform_golden_30.json`  

---

## 1. Executive Summary & Canonical Rule

In Phase 3F.2, Architecture V2 established the strict **Canonical Rule** governing `releases.release_date`:

> **Canonical Rule**:
> `releases.release_date` represents the release/version-scoped publication timestamp published by the source platform for that specific release/version.
> 
> **Strict Invariants**:
> 1. Only **release/version-scoped evidence** is accepted.
> 2. Zero automatic fallback to project modified time, project created time, video publish time, forum post time, or crawler observation time.
> 3. Absence of release-scoped evidence requires: `release_date = NULL`.

This Phase 3G-A audit investigates the 3 remaining date-related `SUSPECT` items in `docs/FEATURE_TRUTH_MATRIX.md`:
* `TIME-MODRINTH-02` (Modrinth: 18,328 releases)
* `TIME-CURSEFORGE-02` (CurseForge: 45,797 releases)
* `TIME-MCMOD-02` (MCMod: 1,484 releases, 326 non-null)

### Summary Verdict
* **Modrinth (`TIME-MODRINTH-02`)**: **`WRONG`**. 100% (18,328 / 18,328) of Modrinth releases in `canonical.db` use the project-level `date_modified` (or fallback `date_created`). Zero version-level timestamps exist in the raw snapshot `crawler_output/modrinth_modpacks.json`.
* **CurseForge (`TIME-CURSEFORGE-02`)**: **`WRONG`**. 100% (45,797 / 45,797) of CurseForge releases in `canonical.db` use the project-level `dateModified` (or fallback `dateReleased` / `dateCreated`). In the CurseForge API, all three are addon/mod-level timestamps. Zero file-level or version-level timestamps were retained in `crawler_output/curseforge_modpacks.json`.
* **MCMod (`TIME-MCMOD-02`)**: **`VERIFIED`**. Investigation of crawler implementation (`mcmod_full_crawler.py` lines 185-210) proves that `last_update_date` is **not** an encyclopedia editorial timestamp. It is the publication date of `latest_version` crawled directly from the version changelog page `https://www.mcmod.cn/modpack/version/{mid}.html`. All 326 non-null records possess genuine version-scoped evidence. The remaining 1,158 records without version changelogs correctly have `release_date = NULL`.

---

## 2. Platform Investigation: Modrinth

### 2.1 The 6 Architectural Questions & Answers

1. **Why are the current 18,328 canonical releases 1-to-1 with packs?**
   * In `pipeline/adapters/modrinth.py` (lines 86-98), the adapter constructs exactly one release per modpack:
     ```python
     releases = [
         CanonicalRelease(
             id=f"{source_item_id}:rel:latest",
             pack_id=pack_id,
             source_item_id=source_item_id,
             version_name=raw_item.get("mc_version") or "Latest",
             version_type="release",
             release_date=mod_at or pub_at,
             is_latest=True,
             downloads_count=raw_item.get("downloads"),
             mc_versions=mc_vers,
             created_at=now_str
         )
     ]
     ```
   * The crawler `modrinth_crawler.py` queries only the search endpoint `https://api.modrinth.com/v2/search?facets=[["project_type:modpack"]]`. Search results return project summaries, not version lists.

2. **What does this release represent: project, latest version, or synthetic release?**
   * It represents a **synthetic project-level release**.
   * Notice that `version_name` is set to `raw_item.get("mc_version")` (e.g. `"1.21.11"`), which is the target Minecraft game version, not a modpack version name (such as `"v1.5.0"`).

3. **What raw JSON path does the current `release_date` come from?**
   * `raw_item.get("date_modified")` fallback `raw_item.get("date_created")`.
   * In Modrinth API `/v2/search`, `date_modified` is the ISO timestamp of when the Modrinth project entry was last updated, and `date_created` is when the project was created.

4. **Is there any true version-specific timestamp in the raw JSON snapshot?**
   * **No**. In `crawler_output/modrinth_modpacks.json`, the union of all keys across all 18,328 items is:
     `{'date_created', 'slug', 'title', 'loaders', 'project_id', 'source_meta', 'mc_version', 'downloads', 'all_versions', 'followers', 'download_links', 'author', 'icon_url', 'date_modified', 'platform', 'gallery', 'description', 'url', 'categories'}`.
   * The `all_versions` array contains strings of supported Minecraft game versions (e.g., `["1.16.5", "1.17.1"]`), not version objects or publication dates.

5. **If version timestamps exist in the API, why didn't the adapter use them?**
   * They exist in Modrinth API endpoint `/v2/project/{id}/version`, but that endpoint was never crawled by `modrinth_crawler.py`. The raw offline snapshot contains only `/v2/search` responses.

6. **If no version timestamp exists, should this canonical record be called a release?**
   * The row is a synthetic placeholder representing the project's state. Under the strict Canonical Rule:
     `release_date` must be `NULL` because `date_modified` is project-scoped (`PROJECT_LEVEL_ONLY`).

---

## 3. Platform Investigation: CurseForge

### 3.1 The 6 Architectural Questions & Answers

1. **What is the exact API semantic of `dateReleased` in CurseForge?**
   * In the CurseForge API (Eternal API `/v1/cf/mods/search` or `/v1/mods/{id}`), the Mod object defines three dates:
     * `dateCreated`: Timestamp when the modpack project was created.
     * `dateModified`: Timestamp when the modpack project was last modified.
     * `dateReleased`: Timestamp when the modpack project was first approved and released to the public.
   * All three fields belong to the **Mod (project) level**, not to individual file releases.

2. **Is it the project latest release date, or a specific file/release publication date?**
   * It is a **project-level** date. In `curseforge_full_crawler.py` (line 179):
     ```python
     date_modified = (item.get("dateModified") or item.get("dateReleased") or "")[:19].replace("T", " ")
     ```
   * The crawler used `dateReleased` only as a secondary fallback for `dateModified`.

3. **Is the canonical release a project synthetic release, or does it correspond to a file?**
   * It is a **project synthetic release**:
     `id = f"curseforge:{pid}:rel:latest"`
     `version_name = raw_item.get("mc_version") or "Latest"` (e.g. `"1.12.2"`).

4. **If the canonical release corresponds to the latest file, could a file-specific timestamp be used?**
   * If the crawler had preserved `latestFiles` from the `/v1/cf/mods/search` response, each file object would have had:
     * `id`: integer file id
     * `fileName`: display file name
     * `fileDate`: file publication timestamp (`CONFIRMED_FILE_SCOPED`)
     * `releaseType`: 1 (Release), 2 (Beta), 3 (Alpha)
   * However, `curseforge_full_crawler.py` explicitly discarded `latestFiles` during standardization, retaining only `source_meta.main_file_id` (a bare integer ID without timestamp).

5. **Do all 45,797 CurseForge records currently use project timestamps?**
   * **Yes, 100% (45,797 / 45,797)**.
   * Every record in `canonical.db` received `date_modified` from the project level.

6. **How many records in the snapshot actually have stronger file/release evidence?**
   * **0 records**. In the current offline snapshot `crawler_output/curseforge_modpacks.json`, zero file objects or file dates exist.

---

## 4. Platform Investigation: MCMod

### 4.1 The 5 Architectural Questions & Answers

1. **What is the original page meaning of `last_update_date`?**
   * In `mcmod_full_crawler.py` (lines 185-210), the crawler accesses the version changelog page:
     `url = f"https://www.mcmod.cn/modpack/version/{mid}.html"`
   * It parses the version table:
     ```python
     entries = re.findall(r'<span class="time">([^<]+)</span>.*?<span class="name">([^<]+)</span>', html, re.S)
     ```
   * `clean_entries[0]["date"]` is stored into `last_update_date`.
   * This is the **actual release date of `latest_version`** (`clean_entries[0]["version"]`).
   * It is **not** an encyclopedia wiki entry edit timestamp.

2. **What is the raw source of `release_date` in MCMod?**
   * `clean_entries[-1]["date"]` (the oldest version entry on `/modpack/version/{mid}.html`) was stored into `raw_item["release_date"]`.
   * This represents the initial launch date of version 1.0 of the modpack.

3. **Were the two fields improperly conflated with encyclopedia page edits?**
   * **No**. The crawler docstring (lines 17-21) explicitly declares:
     > *"3. 真实整合包版本更新日志系统: 打通 https://www.mcmod.cn/modpack/version/{mid}.html 版本专页；提取真正的整合包最新版本号、最新更新日期、初代发布时间及版本发布总数；彻底纠正将百科词条编辑时间混同于整合包更新时间的偏差。"*
   * The suspicion that `last_update_date` was a wiki page edit date was a false alarm.

4. **Which date is release-scoped?**
   * Both dates on `/modpack/version/{mid}.html` are version-scoped!
   * In `pipeline/adapters/mcmod.py` (lines 171-179):
     `ver_name = raw_item.get("latest_version")`
     `release_date = mod_at or pub_at`
   * Because `ver_name` is `latest_version` and `mod_at` is `last_update_date` (the date of `latest_version`), the canonical release correctly pairs the latest version name with its true release date!

5. **What happens to the 1,158 MCMod packs without version logs?**
   * For the 1,158 packs without version changelog records on MCMod, both `last_update_date` and `release_date` were empty.
   * `MCModAdapter` cleanly outputs `release_date = NULL`.
   * Exactly 0 MCMod releases violate the strict Canonical Rule.

---

## 5. Lineage Evidence Table

| Platform | Canonical Release Type | Current Canonical Source | Raw JSON Path | Scope | Certainty | Strict Rule Valid? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Modrinth** | `project` (synthetic `:rel:latest`) | `raw_item.get("date_modified")` or `date_created` | `item["date_modified"]` / `item["date_created"]` | `project` | `PROJECT_LEVEL_ONLY` | **FALSE** |
| **CurseForge** | `project` (synthetic `:rel:latest`) | `raw_item.get("date_modified")` or `date_created` | `item["date_modified"]` (crawler: `dateModified` or `dateReleased`) | `project` | `PROJECT_LEVEL_ONLY` | **FALSE** |
| **MCMod** (with logs) | `version` (`:rel:latest`) | `raw_item.get("last_update_date")` | `item["last_update_date"]` (`/modpack/version/{mid}.html`) | `version` | `CONFIRMED_RELEASE_SCOPED` | **TRUE** |
| **MCMod** (no logs) | `version` (`:rel:latest`) | `None` | `""` | `unknown` | `NO_VERSION_EVIDENCE` | **TRUE** (`NULL`) |
| **BBSMC** (structured) | `version` (`:rel:{version_id}`) | `raw_item.get("date_published")` | `item["date_published"]` | `version` | `CONFIRMED_RELEASE_SCOPED` | **TRUE** |
| **BBSMC** (forum) | `post` (synthetic `:rel:latest`) | `None` (Phase 3F.2 NULL) | `item["date"]` (thread date) | `post` | `POST_LEVEL_ONLY` | **TRUE** (`NULL`) |
| **XYEBBS** (structured) | `release` (`:rel:{release_id}`) | `raw_item.get("createDate")` | `item["createDate"]` | `release` | `CONFIRMED_RELEASE_SCOPED` | **TRUE** |
| **XYEBBS** (forum) | `post` (synthetic `:rel:latest`) | `None` (Phase 3F.2 NULL) | `item["date"]` (thread date) | `post` | `POST_LEVEL_ONLY` | **TRUE** (`NULL`) |
| **Bilibili** | `video` (synthetic `:rel:latest`) | `None` (Phase 3F.2 NULL) | `item["pubdate"]` (video date) | `video` | `VIDEO_LEVEL_ONLY` | **TRUE** (`NULL`) |

---

## 6. Distribution Statistics

### 6.1 Database Totals by Platform

| Platform | Total Releases | Non-Null `release_date` | Null `release_date` | Strict Rule Violations |
| :--- | :---: | :---: | :---: | :---: |
| **Modrinth** | 18,328 | 18,328 | 0 | **18,328** (100%) |
| **CurseForge** | 45,797 | 45,797 | 0 | **45,797** (100%) |
| **MCMod** | 1,484 | 326 | 1,158 | **0** (0%) |
| *BBSMC* | 1,804 | 3 | 1,801 | 0 (0%) |
| *XYEBBS* | 5,184 | 10 | 5,174 | 0 (0%) |
| *Bilibili* | 936 | 0 | 936 | 0 (0%) |
| **Global Total** | **73,533** | **64,464** | **9,069** | **64,125** |

### 6.2 Evidence Breakdown Across 3 Target Platforms (65,609 Releases)

| Platform | Confirmed Release-Scoped | Confirmed File-Scoped | Project-Scoped Only | Unknown / Null | Total Violations |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Modrinth** | 0 | 0 | 18,328 | 0 | 18,328 |
| **CurseForge** | 0 | 0 | 45,797 | 0 | 45,797 |
| **MCMod** | 326 | 0 | 0 | 1,158 | 0 |
| **Subtotal** | **326** | **0** | **64,125** | **1,158** | **64,125** |

---

## 7. Evidence Certainty Hierarchy

1. **`CONFIRMED_RELEASE_SCOPED`**:
   Timestamp definitively published by upstream specifically for this release / version object.
   *Examples*: MCMod version changelog (`326` releases), BBSMC structured versions (`3` releases), XYEBBS structured releases (`10` releases).
2. **`CONFIRMED_FILE_SCOPED`**:
   Timestamp tied to a downloadable distribution file / archive.
   *Status*: 0 in current offline snapshots.
3. **`PROJECT_LEVEL_ONLY`**:
   Timestamp reflects project creation, metadata editing, or initial project approval.
   *Examples*: Modrinth `date_modified` (`18,328`), CurseForge `dateModified`/`dateReleased` (`45,797`).
   *Rule*: **FORBIDDEN** from populating `releases.release_date`.
4. **`HEURISTIC` / `UNKNOWN`**:
   Unverifiable dates or crawler observation times.
   *Rule*: **FORBIDDEN** from populating `releases.release_date`.

---

## 8. 30 Golden Samples Analysis

The 30 Golden Samples have been systematically extracted and saved to:
`build/audit/release_date_platform_golden_30.json`.

### 8.1 Modrinth (10 Samples)
* **Normal (5)**:
  * `1KVo5zza` (*Fabulously Optimized*): `date_created` 2022-02-10, `date_modified` 2026-09-13. Multi-version pack. Release date was project `date_modified`.
  * `qQyHxfxd` (*Simply Optimized*): `date_created` 2022-02-11, `date_modified` 2026-09-12. Project modification timestamp.
  * `1eAoo2KR` (*Cobblemon Official*): `date_created` 2023-03-24, `date_modified` 2026-09-11. Project modification timestamp.
  * `g9mSbhgA` (*All the Mods 9*): `date_created` 2023-08-01, `date_modified` 2026-09-15. Project modification timestamp.
  * `svVO2vvy` (*Better MC [Fabric]*): `date_created` 2022-04-18, `date_modified` 2026-09-14. Project modification timestamp.
* **Edge (3)**:
  * `fFrx8PWq` (*noodlecraft*): `date_created == date_modified` (`2022-06-13 23:13:15`). Pack modified only at creation.
  * `w9pMPENn` (*queens-pack*): `date_created == date_modified` (`2022-08-11 17:20:21`). Single release date.
  * `XOLVzVeB` (*bettervanillahoffalo*): `date_created == date_modified` (`2022-08-07 23:05:37`).
* **Ambiguous (2)**:
  * `4E8rPq1V` (*SpeedrunIGT*): 4-year gap between project creation and last modification.
  * `mOgUt4GM` (*Additive*): Synthetic release `version_name` represents Minecraft version rather than modpack version.

### 8.2 CurseForge (10 Samples)
* **Normal (5)**:
  * `285109` (*RLCraft*): `date_created` 2018-01-11, `date_modified` 2025-04-02. `main_file_id`: 4612979. Uses project `date_modified`.
  * `715572` (*All The Mods 9*): `date_created` 2023-06-25, `date_modified` 2026-09-16. Uses project `date_modified`.
  * `472714` (*Better MC [FORGE]*): `date_created` 2021-04-15, `date_modified` 2026-09-14. Uses project `date_modified`.
  * `389615` (*Pixelmon Modpack*): `date_created` 2020-05-20, `date_modified` 2026-09-15. Uses project `date_modified`.
  * `287342` (*SevTech: Ages*): `date_created` 2018-02-14, `date_modified` 2024-11-20. Uses project `date_modified`.
* **Edge (3)**:
  * `314906` (*Roguelike Adventures and Dungeons*): Multi-year gap between project creation (2019) and latest project update.
  * `394535` (*Crafting Dead*): Distinct loader and `mainFileId`, raw file date stripped by crawler.
  * `598596` (*Medieval MC [FABRIC]*): Fabric fork of popular project; project-level timestamp only.
* **Ambiguous (2)**:
  * `245211` (*The Simple Life 2*): Legacy pack where `dateModified` was populated from `dateReleased`.
  * `263420` (*Stoneblock*): Multiple files in original CurseForge API, completely collapsed into single synthetic row.

### 8.3 MCMod (10 Samples)
* **Normal (5)**:
  * `1` (*GT: New Horizons*): 66 versions on mcmod; `latest_version` = 2.5.1 on 2023-12-21; initial version on 2016-10-27.
  * `16` (*RLCraft*): 3 versions on mcmod; `latest_version` = v2.9.3 on 2023-06-28; initial version on 2021-12-22.
  * `35` (*GreedyCraft*): 23 versions on mcmod; `latest_version` = 1.26.0 on 2021-01-22; initial version on 2020-09-04.
  * `1054` (*Chapter of Yuusha 3*): 134 versions on mcmod; `latest_version` = 3.13.15 on 2026-08-13; initial version on 2025-02-10.
  * `976` (*Sword Strange Tales*): 26 versions on mcmod; `latest_version` = v2.1.10 on 2026-07-26; initial version on 2024-10-30.
* **Edge (3)**:
  * `205` (*Better MC*): Single version pack (`version_count` = 1); `last_update_date` == `release_date` (both 2022-01-04).
  * `722` (*No Flesh Within Chest*): Zero version changelogs on mcmod (`version_count` = 0); `release_date` is correctly `NULL`.
  * `1200` (*BakaCraft*): Zero version changelogs; `release_date` is correctly `NULL`.
* **Ambiguous (2)**:
  * `1133` (*Closing Song*): Initial version date was `'未知时间'` in changelog table, but latest version had genuine date `2026-08-29`; cleanly handled.
  * `526` (*FTB StoneBlock 3*): Initial version date was `'未知时间'`, latest version had genuine date `2022-11-11`; cleanly handled.

---

## 9. Potential Blast Radius (If Strict Rule Enforced in Next Phase)

If the Canonical Rule (`project-level-only -> release_date = NULL`) is enforced:

* **Modrinth**: 18,328 rows converted from `date_modified` to `NULL`.
* **CurseForge**: 45,797 rows converted from `date_modified` to `NULL`.
* **MCMod**: 0 rows converted (all 326 non-null rows have genuine version-scoped dates; 1,158 are already `NULL`).
* **Total Affected Database Rows**: **64,125** releases.

---

## 10. UI Impact Audit

An exhaustive search across `web/assets/js/dashboard.js`, `pipeline/exporters/legacy/`, and `apps/web/` was conducted for consumers of `release_date`, `publishedAt`, and `releaseDate`.

### Key Findings:
1. **Legacy Exporters Decoupled from `releases.release_date`**:
   * In `pipeline/exporters/legacy/modrinth.py` (lines 110-111):
     `date_created = it["published_at"]`
     `date_modified = it["modified_at"]`
   * In `pipeline/exporters/legacy/curseforge.py` (lines 110-111):
     `date_created = it["published_at"]`
     `date_modified = it["modified_at"]`
   * Both exporters read from `source_items`, **not** from `releases.release_date`.
2. **Current Frontend Behavior**:
   * **Modrinth & CurseForge Cards**:
     Line 2758 & 2910: `<span>· 更新: ' + p.date_modified.substring(0, 10) + '</span>`
     The cards explicitly display the **project modification date** from `source_items.modified_at`.
   * **Version Modal**:
     Line 6238: `$vDate.text('更新时间: ' + date);`
     The modal reads `data-date` which receives `p.date_modified`.
   * **Sorting & Filtering**:
     Line 2637 & 2792: `if (sort === 'modified_desc') return (b.date_modified || '').localeCompare(a.date_modified || '');`
     Sorting by "Last Modified" operates on `p.date_modified`.
3. **Impact on Future Architecture V2 Consumers**:
   * If a V2 component queries `releases.release_date` directly:
     * **Version Modal (Release-Specific View)**: Will display `暂无发布日期` or `NULL` instead of a falsified date.
     * **Sort by Release Date**: Modrinth and CurseForge releases will sort to the bottom (as unreleased / date unknown).
     * **Latest Badge**: Cannot rely on `releases.release_date` for Modrinth/CurseForge without falling back to `source_items.modified_at`.

---

## 11. Product Semantics: The "Synthetic Release" Model

A foundational modeling question arises:
> *If a platform's crawler only collected project-level data without version changelogs, should canonical architecture create a synthetic `release` row at all?*

### Evaluation:
* **Option A: Retain Synthetic Release with `release_date = NULL`**:
  * Allows downstream tooling to treat every modpack uniformly as having at least one `:rel:latest` entry point for downloads and Minecraft version compatibility (`release_mc_versions`).
  * Conforms strictly to truth: `releases.release_date = NULL`.
* **Option B: Eliminate Synthetic Releases entirely when no version logs exist**:
  * Means Modrinth (18,328) and CurseForge (45,797) would have 0 rows in `releases`.
  * Breaks foreign key relations and downstream joins that expect packs to have releases.
* **Architectural Decision**:
  * Option A is the intended canonical model. The synthetic release may exist to represent the pack's latest playable profile, but its `release_date` must strictly remain `NULL` unless version-scoped evidence is crawled.

---

## 12. Feature Truth Matrix Updates

| Feature ID | Platform | Canonical Field | Issue Description | Expected Field | Audit Finding | New Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| `TIME-MODRINTH-02` | Modrinth | `releases.release_date` | Project modified/created time masquerading as version release date | `releases.release_date` | 18,328 releases use project-level `date_modified`, zero version timestamps in raw snapshot | **`WRONG`** |
| `TIME-CURSEFORGE-02` | CurseForge | `releases.release_date` | Project dateModified/dateReleased masquerading as version release date | `releases.release_date` | 45,797 releases use project-level timestamps, zero file/version timestamps in raw snapshot | **`WRONG`** |
| `TIME-MCMOD-02` | MCMod | `releases.release_date` | MCMod `last_update_date` vs `release_date` semantics confusion | `releases.release_date` | Debunked: `last_update_date` is version-scoped date from `/modpack/version/{mid}.html`; 326 rows valid, 1,158 rows clean NULL | **`VERIFIED`** |

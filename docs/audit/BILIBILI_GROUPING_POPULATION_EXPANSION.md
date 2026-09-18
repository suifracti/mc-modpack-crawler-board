# Bilibili Grouping — Population-Wide Audit Expansion (Phase 3G-F.1-B)

> Status: **audit only.** No runtime file was modified. No cutover or manifest
> artifact was touched. `docs/FEATURE_TRUTH_MATRIX.md` is deliberately unchanged;
> the suggested statuses at the bottom are *recommendations*, not edits.

## 1. Why this audit exists

Phase 3G-F-A adjudicated **7 confirmed population-level false merges** by scanning
the 3G-F identity-run groups with one signature:

```
anchor sits LATE in the key, and the token prefixes before it differ
```

That signature has a **structural blind spot**. Measured on the 936-record payload:

| metric | value |
| --- | --- |
| groups total | 668 |
| multi-member identity-run groups | 129 |
| **of which `anchor_index == 0` for every member** | **56 (43%)** |
| short anchor (≤3 identity chars) | 15 |

`bilibili_grouping_slogan_anchor_scan.js` sets `MIN_ANCHOR_INDEX = 1`, so it can
**never** emit an all-zero-index group. Verified on the artifact: `min index = 1,
count of zeros = 0`. In other words **43 % of the multi-member population was
invisible to the scanner that produced the headline number.**

A second blind spot: `bilibili_grouping_candidate_false_merge_check.js` hardcodes
`CANDIDATE_UPLOADERS = ['一个小寂哦','墨言eclipse','原界环','叙利亚自爆民兵','tibsalta']`.
A false merge belonging to any other uploader is silently invisible.

This phase widens the net. **The goal is recall on candidates, not precision.**

## 2. Scanner coverage — old vs new

| | v1 (3G-F-A) | v2 (3G-F.1-B) |
| --- | --- | --- |
| `MIN_ANCHOR_INDEX` | `1` (structurally blind to index 0) | **no index floor** |
| `MIN_DISTINCT_PREFIX` | `2` | superseded by per-class rules |
| detector classes | 1 signature | **10 independent classes** |
| uploader scoping | 5 hardcoded uploaders | **whole population (668 groups)** |
| emits verdicts | no | **no** (unchanged — by design) |

Candidate classes now emitted, with counts from the actual run:

| class | count | what it catches |
| --- | --- | --- |
| `anchor_index_zero` | 52 | the v1 blind spot — anchor leads the key |
| `repeated_title_boilerplate` | 37 | members share only template words |
| `late_anchor_distinct_prefix` | 31 | the original v1 signature |
| `bracket_series_tag` | 22 | anchor lives inside `【】[]「」《》（）` |
| `large_group` | 16 | size ≥ 5 → bigger blast radius if wrong |
| `mixed_anchor_position` | 16 | members disagree on where the anchor sits |
| `short_anchor` | 15 | anchor ≤ 3 identity chars (e.g. `涅槃`, `hnt`, `mon`) |
| `anchor_index_one` | 3 | anchor at position 1 |
| `low_discriminative_key` | 3 | shared tokens are all boilerplate |
| `generic_component_anchor` | 1 | anchor built only from mod/component names (`voxy`) |

**Result: 113 candidates** (`95` newly merged by 3G-F) out of 668 groups.

A cross-group layer was added separately (§6 below) to attack the *opposite*
defect — packs the algorithm **split apart**, which the candidate layer cannot see
by construction.

## 3. Architecture: scan and adjudication are separate layers

This separation is the point of the phase, not a nicety.

```
layer 1  bilibili_population_candidate_scan_v2.js      → review list (over-reports)
         bilibili_cross_group_undermerge_scan.js       → review list (over-reports)
                              ↓
layer 2  bilibili_population_adjudication_v2.js        → THE ONLY PLACE A VERDICT EXISTS
         (hand-maintained table; every entry written by reading member titles)
```

Enforced by test: the detectors are asserted to contain **no** `verdict` /
`confidence` field and **no** verdict string anywhere in their output.

**URL / QQ are supporting evidence only.** Phase 3G-E proved one download URL can
span many different packs (a single Quark link covered 28 distinct packs). They are
recorded to help a human adjudicate; they never establish identity.

## 4. Adjudication counts

All **113** candidates carry a verdict. None unadjudicated, none declared-but-absent.

| verdict | count |
| --- | --- |
| `REAL_FALSE_MERGE` | **8** |
| `LEGITIMATE_SAME_PACK` | 100 |
| `FALSE_SPLIT_INDICATOR` | 3 |
| `AMBIGUOUS` | 2 |
| **total** | **113** |

Cross-group layer: **58 clusters reviewed**, 35 confirmed `UNDER_MERGE`,
22 `NOT_UNDER_MERGE`, 1 `PARTIAL_UNDER_MERGE`.

## 5. Confirmed false merges

### 5.1 The known 7 (all still detected — 7/7)

`voxy` and `难度驱动` — the two the task singles out — are both present, each with
its original root-cause class intact (`generic_component_anchor` and
`bracket_series_tag` respectively).

| group key | size | class |
| --- | --- | --- |
| `一个小寂哦::星辉死神` | 4 | late anchor (Boss name) |
| `一个小寂哦::四叶草` | 2 | short anchor (item name) |
| `一个小寂哦::各大主播同款` | 2 | late anchor (slogan) |
| `墨言eclipse::颠覆性的` | 2 | late anchor (adjective) |
| `原界环::or not` | 2 | late anchor (name suffix) |
| `叙利亚自爆民兵::voxy` | 2 | **generic component anchor** |
| `tibsalta::难度驱动` | 2 | **bracket series tag** |

### 5.2 New confirmed false merges (beyond the known 7)

```text
一个小寂哦::怪物大乱斗           (confidence: medium)
```

*「怪物大乱斗 手机版」* and *「怪物大乱斗：重生」* are two separate releases; the
latter is an explicit high-version remake ("还原 1.7 怪物大乱斗"). Same uploader,
different generation, **different packs**. Note the contrast with the separate、
correctly-grouped `一个小寂哦::怪物大乱斗重生` (adjudicated `LEGITIMATE_SAME_PACK`),
which shows the rule works when the name differs — the defect is confined to the
name that stayed the same across a remake.

**Confirmed count = 8 total (7 known + 1 new). This is a LOWER BOUND.**

## 6. Under-merge (false split) findings

### 6.1 涅槃 — the canonical case, fully exposed

Hand-verified against `bili_data`: uploader 墨言eclipse, pack **涅槃**, **7 records
spread across 5 distinct group keys**. The task required this be surfaced as an
under-merge and that its two legitimate sub-groups **not** be miscounted as false
merges. Both hold:

| group key | verdict |
| --- | --- |
| `墨言eclipse::涅槃 无神明渡我 我亦是神明` | under-merge cluster |
| `墨言eclipse::涅槃 神吞降世 …镰刀 之旅` | under-merge cluster |
| `墨言eclipse::大型 禁忌 远古炼金 …涅槃v 0 宣传视频` | under-merge cluster |
| `墨言eclipse::沉浸 深度 a 咒镰双生` | **FALSE_SPLIT_INDICATOR** (not a false merge) |
| `墨言eclipse::未尽之路涅槃` | **FALSE_SPLIT_INDICATOR** (not a false merge) |

Coverage assertion: `5 / 5` keys, `0` missing.

Two independent clusters cover these keys (`涅槃` cluster = 4 keys, and the
`未尽之路` bridge contributes the 5th). The bridge cluster is a **mixed cluster**:
`未尽之路涅槃` belongs to 涅槃, but `拒绝同质` belongs to a *different* pack
(『未尽之路 / Unfinished Path』). At cluster granularity neither blanket verdict is
correct, so the ledger records `PARTIAL_UNDER_MERGE` plus an explicit per-key
resolution. Collapsing this to a single cluster verdict would either create a new
false merge or lose the 5th key.

### 6.2 New under-merges (newly discovered)

35 clusters confirmed. Representative cases (each hand-checked):

| uploader | groups | what was split |
| --- | --- | --- |
| `科里森Corrison` | 2 | `apotheosis conquest` ≡ `神之征伐` (EN/CN of one pack) |
| `落烟雨辰呀` | 2 | `诡厄 使徒` ≡ `诡厄使徒` (punctuation only) |
| `小兜兜呀_` | 2 | main pack vs its own view-count milestone video |
| `ZangHeRo` | 2 | `机械殖民地` ≡ `模拟殖民地` |
| `在职玩家JoStar` | 2 | `方可梦` ≡ `去吧，方可梦大师` |
| `炒雪吵狐力o` | 3 | RapidOptimization split three ways |
| `马赵龙zhao_long` | 3 | `宝可梦重铸` split three ways |
| `Pork猪排` | 4 | `化龍` (incl. simplified/traditional variants) |
| `吴也mc` | 3 | `悠然人生` series |
| `在下Shmily` | 3 | `最牛优化` performance pack |
| `小水滴的源头` | 3 | `蔚蓝档案` themed pack |
| `星遥工坊` | 2 | `刀剑异闻录` |
| `三只大猪TB_pig` | 2 | `铁砧工艺极速版` |
| `无双小星` | 2 | `幸运方块 低配版` |
| `SmartAkita` | 2 | `Cobblemon 方块宝可梦` |
| `碎砖做的砖块王` | 2 | `高版本幸运方块大` |
| `星必尘Sguan` | 2 | `RL Craft 基岩版汉化` |
| `我嘞个牢末ENd` | 2 | `增强·轻量` |
| `孑孑雨不是牢孑` | 2 | `烦村` |
| `空空如也js` | 2 | `惊变100天` |
| `韬可梦` | 2 | Pokémon-series pack |
| `流霜雾影` | 2 | `愚者` |
| `爱吃土豆的界王` | 2 | `山海大陆X斗罗大陆`, `考古与化石x侏罗纪` |
| `啊liu22`, `鹿清玖LQJ`, `Karashok_Leo`, `Drunk耀爵`, `KonataWorks`, `无双小星` | — | single ungrouped record vs its group |

### 6.3 Clusters explicitly REJECTED as under-merge

Important: the scanner over-reports here too, and rejecting is part of the audit.

| uploader | why rejected |
| --- | --- |
| `豆腐ki` (25 groups) | phone-port shipper — each group is a **different** third-party pack; bridged only by template words like `fcl启动器` |
| `一个小寂哦` (16 groups) | bridged by generic `泰坦` / `星辉死神` / `幸运方块` |
| `时唅` (7 groups) | 辐射新世纪 / 辐射次时代 / 生还者 / 潜行者 are genuinely different packs |
| `VM汉化组`, `吴也mc` | translation-group shipping channels |
| `WZW_王宗王`, `XyeBBS中文论坛` | shipping channels; bridged by `FCL` / `宣传片` |
| `明月庄主` | `命运齿轮` and `月亮工厂` are different packs |
| `P1nero` | `平底锅侠` / `方可梦·炽白真形` / `远梦之棺` are three packs |
| `墨竹ギ` | `史诗的地下城` ≠ `深渊之诗` |
| `爱吃土豆的界王` | `时光牧场` ≠ `侏罗纪公园` |

This is why adjudication is a separate layer: a purely heuristic count would have
reported dozens of spurious under-merges.

## 7. Ambiguous cases (not counted)

```text
-阳春面面-::青春复兴    格雷青春版 vs 蔚蓝档案超大型 — undecidable from titles
落烟雨辰呀::诡厄 使徒   1.0.x group; same pack as the 诡厄使徒 group, so not a merge
```

Both are reported as `AMBIGUOUS` and are **excluded from every count**.

## 8. Candidate-detector precision (§14)

```
value = real_false_merge / candidates_total
      = 8 / 113
      = 7.1%
```

**Read this carefully.** This is a statement about the **review list**, not about
the grouping algorithm. The detector's *design goal is to over-report* — the whole
point of this phase was to stop missing cases. A **low** value is the expected,
healthy outcome. A high value would mean the net is still too narrow, i.e. blind
spots remain. Do not optimise this number upward.

## 9. Declared blind spots (§15)

**`confirmed false merges = 8` is a LOWER BOUND, not a population count.**
Known remaining blind spots:

1. **Split-pack invisibility.** The candidate layer only inspects groups the
   current algorithm already produced. If a pack's members were split apart, the
   candidate layer cannot see it — the cross-group layer is only a partial remedy.
2. **Renames across uploads.** Adjudication uses titles + URL/QQ only.
3. **Absorbed singletons.** A false merge that absorbed *all* members of one pack
   leaves the other pack with no group; it is not a candidate and never appears.
4. **Homonymous packs.** Two identically-named packs from one prolific uploader
   would be indistinguishable (generic-name packs were only adjudicable because
   their uploaders are small).
5. **Rename-only splits.** The cross-group scanner needs a *rare shared token*.
   Two groups of one pack sharing no rare token are not surfaced.
6. **Title-only evidence.** Descriptions are truncated to 160 chars in the probe
   target; a pack identified only in the video body is out of reach.

## 10. Artifacts

| artifact | tracked | role |
| --- | --- | --- |
| `pipeline/audit/bilibili_population_candidate_scan_v2.js` | yes | detector, layer 1 |
| `pipeline/audit/bilibili_cross_group_undermerge_scan.js` | yes | detector, layer 1 (cross-group) |
| `pipeline/audit/bilibili_population_adjudication_v2.js` | yes | verdicts, layer 2 |
| `pipeline/audit/build_population_holdout_v2.js` | yes | holdout builder |
| `pipeline/audit/bilibili_population_adjudication_v2.json` | yes | **the ledger** |
| `pipeline/audit/bilibili_population_holdout_v2.json` | yes | holdout v2 (46 pos / 66 neg) |
| `build/audit/bilibili_population_candidates_v2.json` | no (gitignored) | 113 candidates |
| `build/audit/bilibili_cross_group_undermerge_v2.json` | no (gitignored) | 58 clusters |
| `tests/test_bilibili_population_audit_v2.py` | yes | regression suite |

## 11. Holdout expansion (§10)

The old frozen corpus (`bilibili_grouping_corpus.json`, 24 pos / 22 neg over 33
uploaders) is **untouched** — its shape is pinned by test.

New additive holdout `population_holdout_v2`:

| | value |
| --- | --- |
| positive cases | **46** (requirement ≥ 10) |
| negative cases | **66** (requirement ≥ 10) |
| uploaders | 95 |
| overlap with old corpus (dev **and** holdout) | **0** |

Positives are derived from the ledger: a hand-confirmed `LEGITIMATE_SAME_PACK`
group with ≥ 2 members that the **old** algorithm had split
(`old_distinct_keys > 1`) — i.e. a verified merge win. Negatives are multi-pack
uploaders with no `REAL_FALSE_MERGE`.

## 12. Suggested statuses for the Truth Matrix (NOT applied)

`docs/FEATURE_TRUTH_MATRIX.md` was **not modified**. Recommendations only:

* Bilibili grouping — false-merge row: keep **not clean**. Confirmed count moves
  **7 → 8 (lower bound)**, with 6 residual blind spots documented above.
* Bilibili grouping — under-merge row: **add**. 35 clusters confirmed, incl. the
  涅槃 5-way split; previously only 1 case was known.
* Add a note that the 3G-F-A "7 false merges" figure came from a scanner that was
  structurally blind to 43 % of multi-member groups.

## 13. Reproduce

```bash
node pipeline/audit/bilibili_population_candidate_scan_v2.js
node pipeline/audit/bilibili_cross_group_undermerge_scan.js
node pipeline/audit/bilibili_population_adjudication_v2.js
node pipeline/audit/build_population_holdout_v2.js
python -m pytest tests/test_bilibili_population_audit_v2.py -v
```

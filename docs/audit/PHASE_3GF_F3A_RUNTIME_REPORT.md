# Phase 3G-F.3-A — Bilibili under-merge runtime closure

## Scope and status

This A task performed the auditable runtime probe only. It did not perform final
runtime integration, Truth Matrix finalization, production cutover, or any
production-manifest change.

**Status: `BLOCKED` / runtime closure not complete.** The current generic
`apps/web/src/domain/bilibiliGrouping.ts` was compiled and run against the full
936-record population. It closed 5/26 frozen gate cases and left 21/26 open.
The result is deliberately not promoted to PASS.

The source of truth is unchanged `cbbfb58` + `a690d3d`: 26 original gate cases,
80 deduplicated BVIDs, 34 excess groups to unify (`sum(group_count - 1)`),
27 `DIFFERENT_PACKS` separation constraints, and 5 `AMBIGUOUS` protection
samples. Cases were selected by the original gate's author + original group-key
set; no new runtime group-key scan selected “remaining candidates”.

## Input hashes and reproducibility

| Input | SHA-256 / provenance |
|---|---|
| full payload bytes (`converted_output/data/bili_data.js`, 936 records) | `049fe4c567fabafb4e4c58018b606c1aa23d01d2d1511933856454915e79bebe` |
| original evidence (`build/audit/undermerge_evidence_v2.json`) | `bd8b76a51dba40079f258183ef27cbe438c7e220af972a5fe877a1f9ff2df083` |
| candidate baseline | `c32814f6926c2c5c6e2be5552d3e7cd0b61e7ead82d0e10e1d8c007c8ff846a4` |
| original gate bytes from `git show cbbfb58:` | `4e91fe1d8bc3c16a8fe1b3cc65be9a64dcc56f47b29b2a218524029ca82a9d90` |
| frozen baseline runtime bundle | `3d10e2e63cc50d1660d1d95c81658444b67ef21250f4af171366b97e1582c15e` |
| current source runtime bundle (fresh esbuild) | `12fb5f96f2cd3cf587130bae45f0eda19347e8ca54d019b8f2d553a8e7c7692e` |
| ground-truth commits | `cbbfb588262d06d386dab645deee88e0c4acb7c3`, `a690d3dfddc66d4260960b83c9cece7bdb3af72a` |

The Windows working-tree gate hash is also recorded separately in the closure
fixture because `autocrlf` changes LF/CRLF bytes; Git diff and semantic content
are unchanged.

The source blob `apps/web/src/domain/bilibiliGrouping.ts` has `git diff` exit
code 0 against `1bee6de`; Windows may still show a stale stat because of
LF/CRLF normalization. The current bundle above was freshly compiled from that
source after the production-map attempt was removed; it is not the rejected
static-map bundle. The probe rerun log is
`docs/audit/logs/phase3gf-f3a-runtime-probe-rerun.log`.

## Legacy audit-artifact read compatibility

The 1bee6de baseline retains two pre-existing audit artifacts at their historical
`.json` paths, but their raw bytes are gzip containers. The reader now detects
the gzip magic bytes and only adapts I/O; it does not regenerate labels,
reselect samples, or replace ground truth. The raw-file and decompressed
semantic checks are intentionally separate:

| Artifact | Raw bytes / SHA-256 | Decompressed semantic checks |
|---|---:|---|
| `pipeline/audit/bilibili_population_adjudication_v2.json` | 55,695 / `a6a6a4f92c10bf0c9d87dfb9501263fd3967405e3d750ae8854282b0602d18a8` | `candidates_total=100`, `real_false_merge=0`, `known_8_retired=8`, under-merge `60 reviewed / 33 confirmed` |
| `pipeline/audit/bilibili_population_holdout_v2.json` | 25,742 / `bb3da23781dc1a2ac82780c63c37c81a1273d933dd52571d2e5f588e11ecf072` | frozen old corpus `24/22`; derived holdout `44/71` |

The first unadapted adjudication run exited 1 with `UnicodeDecodeError` on the
gzip magic byte; it is retained in
`build/audit/test-logs/04-undermerge-adjudication.log`. After the minimal
reader and 1bee6de baseline assertions were applied, the same 26-test suite
exited 0; no legacy artifact bytes changed.

The exact machine-readable artifacts are:

- `pipeline/audit/bilibili_undermerge_runtime_closure.json`: 26→complete BVID
  mapping, original group members, source hashes, and coverage failures.
- `pipeline/audit/bilibili_undermerge_runtime_probe.json`: real baseline/current
  runtime group membership, full-population group members, per-case
  Before/After/Expected/evidence/result, and the 27/5 partition result.

## 26 frozen gate cases

`Before` is the frozen pre-change runtime bundle; `After` is the current
`1bee6de` generic grouping source compiled for this probe. `Expected` is one
runtime group because the cbbfb58 verdict is `CONFIRMED_SAME_PACK` or
`STRONG_SAME_PACK`. The `evidence` column is the exact `evidence.note` stored
for the row in the probe JSON; the BVID and full source-group membership are
also stored there.

| # | Case | Complete BVID members | Before → After groups | Expected | Evidence / result |
|---:|---|---|---:|---:|---|
| 1 | `-阳春面面-` | `BV1K6HjeTEKJ, BV1bZigehE6V, BV1qTDNY3Ekc` | 2 → 3 | 1 | version continuity on named 青春复兴 pack; **FAIL** |
| 2 | `Karashok_Leo` | `BV172KczaEke, BV1MCFSzTE62, BV1QN6HYnE5W, BV1iDdLYJESg` | 2 → 2 | 1 | identical registered Spell Dimension identities; **FAIL** |
| 3 | `KonataWorks` | `BV1Fg8gzHE7K, BV1Fg8gzHEVB` | 2 → 2 | 1 | same unnamed pack, consecutive versions; **FAIL** |
| 4 | `Pork猪排` | `BV12VtQzkEcm, BV1BA9wBqEnE, BV1GrzxBZE7S, BV1PMAVzKExm, BV1nbTqzCECX` | 4 → 2 | 1 | same 化龍 project identities/version chain; **FAIL** |
| 5 | `SmartAkita` | `BV13mD9YMEFq, BV1GKS4YtExK` | 2 → 2 | 1 | same Cobblemon release identity; **FAIL** |
| 6 | `三只大猪TB_pig` | `BV1Er7G6yEKK, BV1kDBpBcE9x` | 2 → 2 | 1 | same registered 铁砧工艺极速版 project; **FAIL** |
| 7 | `吴也mc` | `BV1LY4y1S756, BV1sY411d7bd` | 2 → 2 | 1 | named 灾难降临 update continuity; **FAIL** |
| 8 | `在下Shmily` | `BV12TxAzvE9r, BV1XTqSBHEyr, BV1zNvCBrEgL` | 3 → 1 | 1 | named 最牛优化 version continuity; **PASS** |
| 9 | `墨言eclipse` | `BV1CQtC6eEaC, BV1LyN366E4u, BV1UJET67ErR, BV1ZTuJ6rEJp, BV1sNjq6pEAd` | 4 → 1 | 1 | 涅槃 registered identities and versions; **PASS** |
| 10 | `孑孑雨不是牢孑` | `BV1ej411q7Kj, BV1of421v7ug` | 2 → 2 | 1 | 烦村 / annoying_villagers alias and update; **FAIL** |
| 11 | `小兜兜呀_` | `BV1JU4k69E61, BV1Y2K467EGN, BV1cjut6BEaG, BV1nJbQ6pEHo, BV1orhK64Em6, BV1qi8r69Eck, BV1tUTK6JE2o` | 2 → 2 | 1 | same BBSMC project identities; **FAIL** |
| 12 | `小水滴的源头` | `BV13rfqY2Ejf, BV14z9FYRED5, BV1UGveexEHn` | 3 → 3 | 1 | continuing 蔚蓝档案 pack updates; **FAIL** |
| 13 | `我嘞个牢末ENd` | `BV1SY7wzJE9w, BV1aojdzzE47` | 2 → 2 | 1 | same named 1.20.1 原版增强 pack; **FAIL** |
| 14 | `星必尘Sguan` | `BV1M3411d7xX, BV1dR4y1T7jD` | 2 → 2 | 1 | same 基岩版 RLCraft 汉化 pack; **FAIL** |
| 15 | `星遥工坊` | `BV17FUkBPEEb, BV1at1cYkEXV` | 2 → 2 | 1 | same 刀剑异闻录 pack name; **FAIL** |
| 16 | `流霜雾影` | `BV1CLnmzgECo, BV1iRL7zYExj, BV1s3ZNBYEQU` | 2 → 1 | 1 | shared `bbsmc:modpack/the-fool`; **PASS** |
| 17 | `炒雪吵狐力o` | `BV16dcgzUEm2, BV1HgGvz2ENe, BV1MzGAzqEsq, BV1f3eAz3Env, BV1zr8V62EvF` | 3 → 3 | 1 | shared `mcmod:modpack/1159`; **FAIL** |
| 18 | `爱吃土豆的界王·山海大陆` | `BV19vto6XETe, BV1bPQCBcEws, BV1zRjv6gEAp` | 2 → 2 | 1 | same 山海大陆×斗罗大陆 titles; **FAIL** |
| 19 | `爱吃土豆的界王·考古与化石` | `BV1RiPWzDE4Q, BV1ZsFbzZE1b` | 2 → 2 | 1 | punctuation-only title variation; **FAIL** |
| 20 | `爱玩游戏的烛梦` | `BV1iYt46kEtC, BV1u34162EuC` | 2 → 2 | 1 | same 基岩版仿亡者世界 pack/update; **FAIL** |
| 21 | `科里森Corrison` | `BV1ApFYz2E7v, BV1bzPMzYE91, BV1iCrMBnEG5, BV1j5V56TEoE, BV1xnvvBbEbj, BV1zGduBhEt2` | 2 → 2 | 1 | shared `xyebbs:resource/1421`, Chinese/English alias; **FAIL** |
| 22 | `空空如也js` | `BV1Jg4y1S7zy, BV1aN4y1W7Mx` | 2 → 2 | 1 | same 惊变100天 FTB500 identity; **FAIL** |
| 23 | `芦苇草的梦想` | `BV14e2LBuEAK, BV1KdrKBeE9Z, BV1hN6FBnEUp` | 3 → 1 | 1 | shared Modrinth project and version chain; **PASS** |
| 24 | `落烟雨辰呀` | `BV1JTwZzDEQr, BV1gkT66HEzV, BV1qg5a6dEuh, BV1s2X4BnEkR` | 2 → 1 | 1 | separator variant plus continuous versions; **PASS** |
| 25 | `韬可梦` | `BV13u4y1e7xC, BV1RT411h7gm` | 2 → 2 | 1 | same 宝可梦 pack continuity and tagline; **FAIL** |
| 26 | `鹿清玖LQJ` | `BV1AoULBgEoH, BV1aRYC6cE4p` | 2 → 2 | 1 | identical 溯渊 titles in two raw buckets; **FAIL** |

All `FAIL` rows are runtime observations, not changes to the cbbfb58 verdicts.
The 5 `PASS` rows are pre-existing generic-rule behavior and do not authorize
claiming the entire closure is complete.

## Partition boundary

The probe checked all 32 excluded original ledger cases. For
`DIFFERENT_PACKS`, **22 are `PROTECTED` and unchanged, while 5 are `FAIL`**
because the current generic runtime changed the excluded sample. For
`AMBIGUOUS`, **4 are `PROTECTED` and unchanged, while 1 is `FAIL`** for the
same reason. The ambiguous rows remain protection samples (“do not claim
different-pack proof”), not proved different packs. The failed partition rows
are therefore a blocker, not a license to alter the adjudication or to split
legal same-group relationships mechanically.

## Runtime boundary and blocker

No production runtime file was changed. In particular, the BVID→group-key
table was rejected as a production implementation and is not present. The
current generic grouping algorithm cannot close 21 cases without a new,
general rule supported by evidence; implementing that rule is outside this
auditable A closure after the scope correction. Therefore the runtime closure
is explicitly **blocked**, while the mapping/probe fixture remains available
for a future general runtime design.

## Verification record

| Command | Exit | Result / log |
|---|---:|---|
| `npm ci --prefix apps/web` | 0 | dependency install recorded in `docs/audit/logs/phase3gf-f3a-runtime-tests.log` |
| `npm --prefix apps/web run typecheck` | 0 | passed; `docs/audit/logs/phase3gf-f3a-runtime-finalization.log` |
| `npm --prefix apps/web test -- --run` | 0 | 11 files / 103 tests passed; same finalization log |
| `python -m unittest tests.test_bilibili_undermerge_runtime_closure -v` | 0 | 5 closure-contract tests passed; same finalization log |
| `node pipeline/audit/build_bilibili_undermerge_runtime_closure.js` | 0 | 26/26 original gate cases mapped; 80 unique BVIDs; closure artifact |
| `apps/web/node_modules/.bin/esbuild.cmd apps/web/src/domain/bilibiliGrouping.ts --bundle --platform=node --format=cjs --target=node20 --outfile=build/audit/bilibili_grouping_runtime_current.js` | 0 | current bundle hash recorded above |
| `node pipeline/audit/probe_bilibili_undermerge_runtime.js build/audit/bilibili_grouping_runtime_current.js` | 2 | expected diagnostic `BLOCKED`; `docs/audit/logs/phase3gf-f3a-runtime-probe-rerun.log` |
| `python -m unittest tests.test_bilibili_undermerge_adjudication -v` (after gzip compatibility) | 0 | 26 tests passed; `build/audit/test-logs/05-undermerge-adjudication-after-gzip.log` |

An earlier combined Python command exited 1: the population benchmark setup lacked
`converted_output/assets/index.js`, the adjudication setup observed regenerated
candidate drift after that population run, and the closure test still had the
pre-correction partition assertions. Those failures are retained in
`docs/audit/logs/phase3gf-f3a-runtime-tests.log`; the corrected standalone
closure-contract and adjudication tests above are the final results. The
adjudication rerun used the frozen restored candidate/evidence bytes and the
gzip-compatible reader; it did not promote the 21 runtime failures or rewrite
any verdict.

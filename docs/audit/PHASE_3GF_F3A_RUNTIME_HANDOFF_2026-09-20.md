# Phase 3G-F.3-A runtime handoff

日期：2026-09-20（Asia/Shanghai）
范围：仅 runtime closure + audit integration；未执行 Truth Matrix 定稿、最终 runtime integration 或 Production cutover。

## 结论

最终 runtime candidate 已通过本轮 acceptance：

- under-merge gate：26/26 PASS；25 uploaders、80 unique BVID records、34 excess groups to unify（定义为 `sum(group_count - 1)`，不是 34 个目标整合包）。
- safety partition：27/27 `DIFFERENT_PACKS` PROTECTED；5/5 `AMBIGUOUS` PROTECTED；没有把 AMBIGUOUS 自动纳入 merge。
- 当前实现：`ACCEPTED` 作为 runtime candidate；未发布到 Production。
- confirmed false merge：0；known-8 retired：8/8，仍 merging：0。

## 起点、审计输入与 Git

- 独立 worktree：`C:\Users\Administrator\.codex\worktrees\phase3gf-f3a-runtime\我的世界整合包获取`
- branch：`fix/phase3gf-f3a-runtime`
- starting HEAD：`28dca3c8a72ad17e884b59d0c2444ca09af18c27`
- runtime baseline candidate：`1bee6dea6a30ff0b6368091c614c528263a2f0a`
- implementation commit：`dd1f62445695d3455c2b9f67d02d7d700a91eff6`

已验证：

```text
cbbfb58 -> commit
a690d3d -> commit
```

当前 F.3 branch 已有相同 F.2-B patch：`a48dcaa` / `948a179`。`a48dcaa` 与 `cbbfb58` 的 stable patch-id 均为 `4959348a52b2d35db99779f6ad8c2e765146aff2`；`948a179` 对应 `a690d3d` 的 report-only 内容。因此没有重复 cherry-pick，未产生冲突，也没有覆盖另一条 worktree 的内容。交接时不要求 loose/packed 对象或文本形式相同，以 ref、对象和 HEAD 语义为准。

### 证据 hash

| Artifact | Hash / meaning |
|---|---|
| `pipeline/audit/bilibili_undermerge_adjudication_v2.json` | raw bytes `7a3b4a2889662bb0b035f14d2f1ca3d59d393868e6356100ca1300094c5995df`；normalized `8987d38db353c77f13385da3b8f4a00a4e95eaaa90bd21de1075c49b5a2f1feb` |
| `pipeline/audit/confirmed_undermerge_runtime_gate.json` | raw bytes `cafec9955c5e589315279b348dc5520a17594bebfc5d43dde08b4a810dfafad7`；normalized/Git semantic bytes `4e91fe1d8bc3c16a8fe1b3cc65be9a64dcc56f47b29b2a218524029ca82a9d90` |
| `pipeline/audit/fixtures/phase3gf_runtime_acceptance.json` | raw bytes `c76674e652de281bbf894cece086c0f85464c5f007e4685e1cfeb439c506b994` |
| immutable under-merge evidence | `bd8b76a51dba40079f258183ef27cbe438c7e220af972a5fe877a1f9ff2df083` |
| audit candidate evidence | `c32814f6926c2c5c6e2be5552d3e7cd0b61e7ead82d0e10e1d8c007c8ff846a4` |
| final acceptance report | `docs/audit/logs/phase3gf_f3a_runtime_acceptance.json`, raw `0fab11570b2c3e60d8e3c36f6b81021664409afe53053c21ffb321386d09a239` |
| expanded audit report | `docs/audit/logs/phase3gf_expanded_runtime_audit.json`, raw `9bb95d8d0a563aac16e3eb88d119409434df20dff86d0cdfd2371669b28a603f` |
| derived holdout report | `docs/audit/logs/phase3gf_runtime_holdout_v2.json`, raw `abfe5cdc1a4f30605becdb34ae024689565ed47b2a48cbf8ea0acd3c084ee900` |

`1bee6de` 祖链中的 gzip evidence 只做读取兼容与 raw-byte hash 检查；旧 v2 holdout source raw hash 为 `bb3da23781dc1a2ac82780c63c37c81a1273d933dd52571d2e5f588e11ecf072`，本轮未重生成、未改 ground truth。候选 runtime 的 worktree raw hash 为 `6a834dec354fee76c94b6bfcfa9a5527994b7fc65b823e029ebea88544b658b2`，Git-normalized hash 为 `c038f6f77b09757e8ea0ace3c193c7d1e2104b9b24951ef261ce7bcdbdfa1737`；acceptance 已验证 semantic match。

## Runtime 变更

修改只落在 `apps/web/src/domain/bilibiliGrouping.ts` 及本轮 audit fixture/runner；legacy bridge 只调用 domain implementation，没有复制 grouping rules。主要变化：

1. bridge identity 改为 whole-chain 一致性检查；孤立的 registered project identity 会分区，辅助 URL/QQ/theme 不单独产生 merge。
2. 扩展通用 slogan/描述词的负向 anchor 规则，并保留数字-only guard，避免把宣传词当 pack identity。
3. 对显式 edition head 执行通用的 exclusive-edition partition；mixed-script branded name 不被误拆，明确 edition 不被吸并。
4. acceptance fixture 现在从冻结 evidence 映射完整成员，核对 source SHA、raw/normalized hash、完整 pair relation coverage、80 unique gate BVIDs、26 case mapping；缺失、重复、空成员、映射不唯一均 fail closed。

新增规则没有 uploader、BVID 或 pack title 的 operational hardcode；审计 fixture 中的 BVID 仅用于冻结 ground truth 和测试输入。

## 26 条 under-merge gate

Baseline 是 `1bee6de` 原 runtime 的结果：5/26 PASS、21/26 FAIL。下表的 Before/After 是完整成员分区的 group count；Expected 是 adjudication ground truth identity count；Evidence 是冻结 evidence 中的裁定理由。最终 26 条全部 PASS。

| # | Uploader | Member BVIDs | Before → After | Expected identities | Evidence | Result |
|---:|---|---|---:|---:|---|---|
| 1 | -阳春面面- | `BV1K6HjeTEKJ, BV1bZigehE6V, BV1qTDNY3Ekc` | 2 → 1 | 1 | “青春复兴”是 pack name；另一个是 0.5.1，明确版本连续性 0.5.1 → 0.7.1。 | PASS |
| 2 | 爱吃土豆的界王 | `BV1RiPWzDE4Q, BV1ZsFbzZE1b` | 2 → 1 | 1 | “考古与化石X侏罗纪”同 pack，仅 X/空格分隔差异。 | PASS |
| 3 | 爱吃土豆的界王 | `BV19vto6XETe, BV1bPQCBcEws, BV1zRjv6gEAp` | 2 → 1 | 1 | “山海大陆X斗罗大陆”与“山海大陆·斗罗大陆”同 pack，含重复发布。 | PASS |
| 4 | 爱玩游戏的烛梦 | `BV1iYt46kEtC, BV1u34162EuC` | 2 → 1 | 1 | 同名“基岩版仿亡者世界整合包”，V1.2 update、同 QQ，版本连续。 | PASS |
| 5 | 炒雪吵狐力o | `BV16dcgzUEm2, BV1HgGvz2ENe, BV1MzGAzqEsq, BV1f3eAz3Env, BV1zr8V62EvF` | 3 → 1 | 1 | 三组共享 registered `mcmod:modpack/1159`，标题为同一优化 pack 的连续更新。 | PASS |
| 6 | 孑孑雨不是牢孑 | `BV1ej411q7Kj, BV1of421v7ug` | 2 → 1 | 1 | 烦村 / annoying_villagers 同 pack，1.0 到 5.0 明确 update。 | PASS |
| 7 | 科里森Corrison | `BV1ApFYz2E7v, BV1bzPMzYE91, BV1iCrMBnEG5, BV1j5V56TEoE, BV1xnvvBbEbj, BV1zGduBhEt2` | 2 → 1 | 1 | 共享 `xyebbs:resource/1421`；Apotheosis Conquest 中英文同 pack，v1.1 → v2.3。 | PASS |
| 8 | 空空如也js | `BV1Jg4y1S7zy, BV1aN4y1W7Mx` | 2 → 1 | 1 | 同一 1.18.2 惊变100天 FTB500，title/link/registered thread identity 一致。 | PASS |
| 9 | 流霜雾影 | `BV1CLnmzgECo, BV1iRL7zYExj, BV1s3ZNBYEQU` | 2 → 1 | 1 | 共享 `bbsmc:modpack/the-fool`，v0.1 → v0.2。 | PASS |
| 10 | 芦苇草的梦想 | `BV14e2LBuEAK, BV1KdrKBeE9Z, BV1hN6FBnEUp` | 3 → 1 | 1 | 共享 Modrinth project `my-biome-is-so-beautiful`，4.0.11 → 4.1.7 → 4.2.12。 | PASS |
| 11 | 鹿清玖LQJ | `BV1AoULBgEoH, BV1aRYC6cE4p` | 2 → 1 | 1 | 同 uploader、同 title“溯渊最新更新”、同 MC version；原 split 只因 key 低于 discriminative threshold。 | PASS |
| 12 | 落烟雨辰呀 | `BV1JTwZzDEQr, BV1gkT66HEzV, BV1qg5a6dEuh, BV1s2X4BnEkR` | 2 → 1 | 1 | 同 pack name separator variant，`mcmod:modpack/1241` 与 BBSMC line，1.0.6 → 1.1.0。 | PASS |
| 13 | 墨言eclipse | `BV1CQtC6eEaC, BV1LyN366E4u, BV1UJET67ErR, BV1ZTuJ6rEJp, BV1sNjq6pEAd` | 4 → 1 | 1 | 涅槃同 pack，均有 `xyebbs:resource/37418`，并有 `mcmod:modpack/1418`，0.1.5 → 0.2。 | PASS |
| 14 | 三只大猪TB_pig | `BV1Er7G6yEKK, BV1kDBpBcE9x` | 2 → 1 | 1 | 共享 `curveforge:anvilcraft-turbo` 及同名“铁砧工艺极速版”。 | PASS |
| 15 | 韬可梦 | `BV13u4y1e7xC, BV1RT411h7gm` | 2 → 1 | 1 | 同一养老向宝可梦 pack；同 uploader/QQ/tagline，明确实时/领先 update。 | PASS |
| 16 | 我嘞个牢末ENd | `BV1SY7wzJE9w, BV1aojdzzE47` | 2 → 1 | 1 | 同名《1.20.1原版增强》轻量整合包，v1.13/preview，共享 download link。 | PASS |
| 17 | 吴也mc | `BV1LY4y1S756, BV1sY411d7bd` | 2 → 1 | 1 | 同名灾难降临，标题明确“全新的…更新”与原始发布连续。 | PASS |
| 18 | 小兜兜呀_ | `BV1JU4k69E61, BV1Y2K467EGN, BV1cjut6BEaG, BV1nJbQ6pEHo, BV1orhK64Em6, BV1qi8r69Eck, BV1tUTK6JE2o` | 2 → 1 | 1 | 两组共享同一 BBSMC project 与 `-lts` edition；第二组为同 pack milestone/download-count announcement。 | PASS |
| 19 | 小水滴的源头 | `BV13rfqY2Ejf, BV14z9FYRED5, BV1UGveexEHn` | 3 → 1 | 1 | 同一蔚蓝档案 pack，early release → NPCAI system → 新版 release，明确 continuation。 | PASS |
| 20 | 星必尘Sguan | `BV1M3411d7xX, BV1dR4y1T7jD` | 2 → 1 | 1 | 同一基岩版 RLCraft 汉化 pack，v5/重大更新，同 uploader/platform/mirror。 | PASS |
| 21 | 星遥工坊 | `BV17FUkBPEEb, BV1at1cYkEXV` | 2 → 1 | 1 | 同名刀剑异闻录，周年 update 与 earlier release，title continuity。 | PASS |
| 22 | 在下Shmily | `BV12TxAzvE9r, BV1XTqSBHEyr, BV1zNvCBrEgL` | 3 → 1 | 1 | “最牛优化” V3.9 → V4.0，同 pack name、QQ/roadmap continuity。 | PASS |
| 23 | Karashok_Leo | `BV172KczaEke, BV1MCFSzTE62, BV1QN6HYnE5W, BV1iDdLYJESg` | 2 → 1 | 1 | raw bucket 与 spell-dimension group 共享 bbsmc/curseforge/github/mcmod identity set。 | PASS |
| 24 | KonataWorks | `BV1Fg8gzHE7K, BV1Fg8gzHEVB` | 2 → 1 | 1 | 同一未命名生电 pack，1.21.4 → 1.21.5，同 uploader/QQ/连续版本。 | PASS |
| 25 | Pork猪排 | `BV12VtQzkEcm, BV1BA9wBqEnE, BV1GrzxBZE7S, BV1PMAVzKExm, BV1nbTqzCECX` | 4 → 1 | 1 | 同一 hualong pack，1.0 → 1.2 → 1.3.1 → 1.3.2；两个 XyeBBS ids 是 slug/numeric 同项目。 | PASS |
| 26 | SmartAkita | `BV13mD9YMEFq, BV1GKS4YtExK` | 2 → 1 | 1 | 同一 Cobblemon 方块宝可梦 1.6 preview/release，同 servers 与 distribution。 | PASS |

完整机器可读结果：[`phase3gf_f3a_runtime_acceptance.json`](logs/phase3gf_f3a_runtime_acceptance.json)。每一行还包含完整 `before`、`after` 的 pair partition、population members、source group keys 和 failure reasons。

## Under-merge / false-merge / safety 结果

- 最终 gate remaining under-merges：0/26；没有失败 case。
- confirmed false merges：0。8 个历史 retired false-merge classes 全部保持 retired；没有重新合并。
- 模块 2 的 27 `DIFFERENT_PACKS` 与 5 `AMBIGUOUS` 均按完整 member partition 检查，不是只比较 group count；32/32 未被错误吸并。
- `DIFFERENT_PACKS` 是已裁定分离约束；`AMBIGUOUS` 是证据不足的保护样本。本轮未改变裁定，也未从中新增吸并。
- 外部未验证成员：26 gate cases 均为 0；unknown relation 的新 merge 会 fail closed。

## Frozen benchmark、holdout 与 population

### Frozen benchmark

使用当前 domain runtime 的 remediation evaluator，结果为：

```text
overall: TM=21 FS=3 TS=22 FM=0 Precision=1 Recall=0.875
negative regression: 22/22 separate
old false splits fixed: 18/21
```

`46/66/95`、`44/71/97` 没有被当作 invariant。冻结的是 generation contract、uploader separation、FM=0 和 expected labels。原始旧 benchmark 脚本仍是历史 baseline 读取器，不作为本轮最终 runtime acceptance；本轮实际结果见 [`phase3gf_frozen_benchmark.log`](logs/phase3gf_frozen_benchmark.log)。

### Final-runtime-derived expanded holdout

旧 v2 gzip corpus 只做 shape/source compatibility check；本轮在内存中依据 immutable evidence、旧合法 group map 和最终 runtime partition 派生 holdout，不覆盖旧 ground truth：

```text
40 positive cases / 62 negative cases / 102 total
104 positive videos / 223 negative videos / 91 uploaders
uploader overlap with old corpus: 0
pairwise: TM=234 FS=0 TS=326 FM=0 Precision=1 Recall=1
exact case partitions: 102/102
```

详情：[`phase3gf_expanded_runtime_audit.json`](logs/phase3gf_expanded_runtime_audit.json)、[`phase3gf_runtime_holdout_v2.json`](logs/phase3gf_runtime_holdout_v2.json)。

### Population counts

```text
Bilibili raw population: 936 records / 936 unique BVIDs -> 648 groups
mechanical power raw search: 53 records / 53 unique BVIDs -> 38 groups
Flat Mode raw-record invariant for mechanical power: PASS (53)
```

Grouped count is a measurement, not a raw-record invariant.

### 涅槃 boundary

`涅槃` 5 records 与 `未尽之路-涅槃` 2 records 保持两个不同 identity；runtime remediation test 验证 expected identities = 2，未执行 7 → 1。怪物大乱斗手机版/重生、voxy 你好新蒸程/你好新世代、难度驱动抗争之际/旅途痕迹也都保持分离；14/14 runtime remediation tests 通过。

## Tests and logs

| Command | Exit | Result | Log / artifact |
|---|---:|---|---|
| `npm.cmd --prefix apps/web run typecheck` | 0 | TypeScript typecheck PASS | [`phase3gf_typecheck.log`](logs/phase3gf_typecheck.log) |
| `npm.cmd --prefix apps/web run test` | 0 | 11 files / 103 tests PASS | [`phase3gf_vitest.log`](logs/phase3gf_vitest.log) |
| `python -m unittest -v tests.test_bilibili_undermerge_runtime_acceptance tests.test_bilibili_undermerge_runtime_closure` | 0 | 13 tests PASS | [`phase3gf_runtime_acceptance_tests.log`](logs/phase3gf_runtime_acceptance_tests.log) |
| `python -m unittest -v tests.test_bilibili_grouping_runtime_remediation_3gf2a` | 0 | 14 tests PASS | [`phase3gf_runtime_remediation_tests.log`](logs/phase3gf_runtime_remediation_tests.log) |
| `node pipeline/audit/phase3gf_runtime_acceptance.js --out docs/audit/logs/phase3gf_f3a_runtime_acceptance.json` | 0 | 26/26; 27/27; 5/5; PASS | [`phase3gf_f3a_runtime_acceptance.json`](logs/phase3gf_f3a_runtime_acceptance.json) |
| `node pipeline/audit/phase3gf_expanded_runtime_audit.js --out docs/audit/logs/phase3gf_expanded_runtime_audit.json --holdout-out docs/audit/logs/phase3gf_runtime_holdout_v2.json` | 0 | holdout PASS; known-8 8/8; population PASS | [`phase3gf_expanded_runtime_audit.json`](logs/phase3gf_expanded_runtime_audit.json) |
| reviewer `reproduce.cjs` | 0 | fresh PASS; relation-erased, external-absorption and known-different mutation probes failed closed as expected; runtime bridge singleton probes passed | [`phase3gf-review-reproduce-after-dd1f624.log`](logs/phase3gf-review-reproduce-after-dd1f624.log) |

### Known legacy-suite limitation / failure retained honestly

曾运行旧的综合 generator-dependent suite，退出码为 1（53 tests，另有 setUp errors）。它会用当前 runtime 重写 F.2 population/precision/adjudication derived artifacts，再拿这些新结果对旧 ground truth 断言；这不符合本轮“冻结旧 ground truth、不得为绿而重生成标签”的约束。失败包括：旧 named-case identity assertion、population audit 的 unadjudicated rows、precision audit 的 unadjudicated rows；早期 acceptance runner 的两个字符串断言也已修复，当前上表的 13/13 targeted runtime/closure suite 已通过。生成物已恢复，未将这次失败当作 final acceptance PASS，也未据此修改 ground truth。

## Git handoff

实现相对 starting HEAD 的统计：

```text
28dca3c..dd1f624
5 files changed, 3096 insertions(+), 1758 deletions(-)
```

变更文件仅为 domain runtime 与 acceptance/fixture/audit 脚本；没有修改 `FEATURE_TRUTH_MATRIX.md`、`cutover_frontend_to_modern.py`、`manifest.py`、`browser_harness.js`、`production_state.json` 或 Production artifacts。`git diff --check` 通过。测试后的最终 evidence/report commit 会作为本文件所在 worktree 的最终 HEAD，并在交回消息中给出精确 SHA；本轮停止于 runtime candidate acceptance，不执行 cutover。

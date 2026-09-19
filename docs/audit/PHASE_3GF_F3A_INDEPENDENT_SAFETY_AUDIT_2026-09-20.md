# Phase 3G-F.3-A 独立安全审计交接

日期：2026-09-20（Asia/Shanghai）  
分支：`fix/phase3gf-f3a-runtime`  
worktree：`C:\Users\Administrator\.codex\worktrees\phase3gf-f3a-runtime\我的世界整合包获取`

## 结论与停点

本轮状态保持：**26-case 及特定反例通过，expanded safety 未完成；runtime NOT ACCEPTED。**

- 当前源码上的 runtime acceptance：26/26 gate、27/27 `DIFFERENT_PACKS`、5/5 `AMBIGUOUS` 均通过。
- 独立 holdout / population 安全审计：FM=0、FS=0，但独立证据覆盖不完整，结果为 `BLOCKED`，exit code=2。
- 不执行 Truth Matrix 定稿、最终 runtime integration、Production cutover；不修改 manifest/cutover/production 文件。
- `AMBIGUOUS` 未自动吸并；`DIFFERENT_PACKS` 成员分区保持保护。

机器可读结果：

- [独立安全审计 JSON](logs/phase3gf_expanded_runtime_audit_independent.json)
- [独立 holdout JSON](logs/phase3gf_runtime_holdout_independent.json)
- [当前 runtime acceptance JSON](logs/phase3gf_f3a_runtime_acceptance_post_independent.json)

## 起点、输入与 provenance

本轮接管起点为 `37ea9f61fa1af5fe1731ccdc93130b69e4f64ea4`。runtime 源码基线为 `dd1f62445695d3455c2b9f67d02d7d700a91eff6`；审计在起点 SHA 的 worktree 上编译当前源码，未把当前 candidate 输出用于生成身份标签。

`cbbfb58` 与 `a690d3d` 两个 audit commit 对象已用 `git cat-file -t` 验证为 commit；本轮未重复创建 branch/worktree，也没有把 B 路或 cutover 路接入本分支。

候选 bundle 与输入 hash：

| 项目 | 值 |
|---|---|
| runtime source raw bytes SHA-256 | `b459c71083e0b33e85ebaea135fac147d20d91b6b1ab6f5510b2d28efb854766` |
| candidate bundle SHA-256 | `79214b900018cc0393606036c8d3ff64e4730009c0b8c7354a41bf894f60c51b` |
| 936 population raw bytes | `049fe4c567fabafb4e4c58018b606c1aa23d01d2d1511933856454915e79bebe` |
| original evidence raw bytes | `bd8b76a51dba40079f258183ef27cbe438c7e220af972a5fe877a1f9ff2df083` |
| final under-merge adjudication ledger raw bytes | `7a3b4a2889662bb0b035f14d2f1ca3d59d393868e6356100ca1300094c5995df` |
| population adjudication ledger raw bytes | `a6a6a4f92c10bf0c9d87dfb9501263fd3967405e3d750ae8854282b0602d18a8` |
| runtime gate raw bytes | `cafec9955c5e589315279b348dc5520a17594bebfc5d43dde08b4a810dfafad7` |
| relation fixture raw bytes | `c76674e652de281bbf894cece086c0f85464c5f007e4685e1cfeb439c506b994` |
| frozen legacy 40/62 raw bytes | `abfe5cdc1a4f30605becdb34ae024689565ed47b2a48cbf8ea0acd3c084ee900` |
| independent relation catalog SHA-256 | `74620e2e32bc1af469f6aa0e343e7fe947e1eeabfa7d577b45443ef0edb9ea6d` |

原始 hash 是解析前文件字节 hash；gzip JSON 通过 `pipeline/audit/lib/audit_artifact_io.js` 读取，解析后另记 semantic SHA。没有重生成标签、缩小样本或替换 ground truth。完整 raw/semantic hash 对见独立 JSON 的 `source_inputs`。

## 独立身份关系与 40/62 migration

冻结成员先从原始 `phase3gf_runtime_holdout_v2.json` 读取，再建立关系标签；legacy `group_key` 被忽略，candidate group 只作为测量结果。

| 冻结来源集合 | 总 case | 独立闭合 | 与独立关系冲突 | UNKNOWN/覆盖不足 |
|---|---:|---:|---:|---:|
| 原 positive | 40 | 40 | 0 | 0 |
| 原 negative | 62 | 4 | 28 | 30 |
| 合计 | 102 | 44 | 28 | 30 |

因此负例不能被当前预测生成的标签替代，也不能把 62 条静默缩成 4 条来报安全 PASS。旧 40/62 的逐 case 去向、BVID、逐 pair relation、source 与 candidate outcome 已完整保存在 JSON 的 `holdout_independent.migration` 和 `holdout_independent.cases`。

独立 holdout 关系结果：

| 指标 | 值 |
|---|---:|
| independently labeled positive / negative cases | 40 / 4 |
| true merge | 217 |
| false split | 0 |
| true separate | 4 |
| false merge | 0 |
| uncovered pairs | 277 |
| conflicting pairs | 62 |
| precision / recall（仅已闭合关系） | 1 / 1 |

`28` 个 case-level conflict、`30` 个 UNKNOWN_COVERAGE case 和 `277` 个未覆盖 pair 是阻塞项，不是可忽略的测量噪声。

## 当前 26-case runtime gate

下面的 `Before` 是实际 1bee6de baseline，`Pre-fix` 是审计 acceptance 使用的 repair-before runtime；两者不再混写为旧 evidence baseline。

| # | uploader | Before | Pre-fix | After | Expected identities | Result |
|---:|---|---:|---:|---:|---:|---|
| 1 | -阳春面面- | 2 | 3 | 1 | 1 | PASS |
| 2 | 爱吃土豆的界王 | 2 | 2 | 1 | 1 | PASS |
| 3 | 爱吃土豆的界王 | 2 | 2 | 1 | 1 | PASS |
| 4 | 爱玩游戏的烛梦 | 2 | 2 | 1 | 1 | PASS |
| 5 | 炒雪吵狐力o | 3 | 3 | 1 | 1 | PASS |
| 6 | 孑孑雨不是牢孑 | 2 | 2 | 1 | 1 | PASS |
| 7 | 科里森Corrison | 2 | 2 | 1 | 1 | PASS |
| 8 | 空空如也js | 2 | 2 | 1 | 1 | PASS |
| 9 | 流霜雾影 | 2 | 1 | 1 | 1 | PASS |
| 10 | 芦苇草的梦想 | 3 | 1 | 1 | 1 | PASS |
| 11 | 鹿清玖LQJ | 2 | 2 | 1 | 1 | PASS |
| 12 | 落烟雨辰呀 | 2 | 1 | 1 | 1 | PASS |
| 13 | 墨言eclipse | 4 | 1 | 1 | 1 | PASS |
| 14 | 三只大猪TB_pig | 2 | 2 | 1 | 1 | PASS |
| 15 | 韬可梦 | 2 | 2 | 1 | 1 | PASS |
| 16 | 我嘞个牢末ENd | 2 | 2 | 1 | 1 | PASS |
| 17 | 吴也mc | 2 | 2 | 1 | 1 | PASS |
| 18 | 小兜兜呀_ | 2 | 2 | 1 | 1 | PASS |
| 19 | 小水滴的源头 | 3 | 3 | 1 | 1 | PASS |
| 20 | 星必尘Sguan | 2 | 2 | 1 | 1 | PASS |
| 21 | 星遥工坊 | 2 | 2 | 1 | 1 | PASS |
| 22 | 在下Shmily | 3 | 1 | 1 | 1 | PASS |
| 23 | Karashok_Leo | 2 | 2 | 1 | 1 | PASS |
| 24 | KonataWorks | 2 | 2 | 1 | 1 | PASS |
| 25 | Pork猪排 | 4 | 2 | 1 | 1 | PASS |
| 26 | SmartAkita | 2 | 2 | 1 | 1 | PASS |

统计口径仍为 `25 uploaders / 80 unique BVID / 34 excess groups to unify`；34 是 `sum(group_count - 1)`，不是 34 个目标整合包。80 也仅在需要时按去重 BVID 报告。

特别核正：

- 青春复兴：实际 1bee6de Before=2，旧 evidence baseline 不能代替该值。
- 涅槃：实际 1bee6de Before=4；5 条涅槃记录与 2 条未尽之路-涅槃记录是两个不同 identity，当前 After=1 仅针对本 gate 的 5 条涅槃成员，不把 7 条合成一个 identity。
- 最牛优化：实际 1bee6de Before=3，当前 After=1。

## Runtime 变更

只修改了 `apps/web/src/domain/bilibiliGrouping.ts`，没有复制 legacy grouping rule；bridge 仍只调用 domain implementation。新增/收窄均为通用结构规则：

- 识别重复 identity run，并避免把 Latin 单词内部的 standalone `v` 拆成伪 token。
- 识别 bracketed platform/channel self-name，保留真正的 bracket/name-slot identity。
- `ver/版本/版/v` 作为版本格式时不制造 competing product；显式编号系列仍保持分区。
- `V3.0优化` 这类紧邻版本号的 modifier 作为更新描述；不放宽裸 `优化`、手机版、绿色版等 edition boundary。
- 注册项目只在已有共同 lexical identity 时做 author-local reconciliation；没有共同 lexical anchor 时不凭 project ID 发明 `registered-project:*` identity。
- QQ 只作辅助证据，不能覆盖已经由标题结构建立的不兼容 identity；English/Chinese alias 与重复 bracket 名称也受 author-local、release-shaped 和现有 identity 兼容性约束。
- 没有使用 uploader/BVID/pack-title 特判；现有泛化/反例测试通过。

## known-8 逐关系退休与故障注入

8 个历史错误大组均逐个展开原错误 pair，并检查当前关系；不是用 `afterKeys.length > 1` 代替逐 identity 验证。

| known case | 原错误关系 | 当前关系 | 只隔离一个成员后的 CANNOT 注入 |
|---|---|---|---|
| 一个小寂哦::星辉死神 | 神器收集计划 / 无尽幸运方块大陆 / 全网最全神器 | 全部原 CANNOT 为 DIFFERENT_GROUP | detected |
| 一个小寂哦::四叶草 | 新泰坦生物 / 执行之龙 | DIFFERENT_GROUP | detected |
| 一个小寂哦::各大主播同款 | 幸运方块大全 / 超困难神器泰坦随机合成 | DIFFERENT_GROUP | detected |
| 墨言eclipse::颠覆性的 | 摄影奇境 / 千界万锻 | DIFFERENT_GROUP | detected |
| 原界环::or not | Minecraft or Not: Girl&Gun / Maiden or not | DIFFERENT_GROUP | detected |
| 叙利亚自爆民兵::voxy | 你好新蒸程 / 你好新世代 | DIFFERENT_GROUP | detected |
| tibsalta::难度驱动 | 抗争之际 / 旅途痕迹 | DIFFERENT_GROUP | detected |
| 一个小寂哦::怪物大乱斗 | 怪物大乱斗手机版 / 怪物大乱斗重生 | DIFFERENT_GROUP | detected |

结果：`checked=8/8`、`retired_by_pair=8/8`、故障注入 `8/8`。涅槃 5+2、怪物大乱斗、voxy、难度驱动均另有 runtime regression 覆盖。

## 936 population 与机械动力

candidate 当前 population 统计（分组数不是 invariant）：

| 指标 | 936 population | 机械动力 query |
|---|---:|---:|
| raw records / unique BVID | 936 / 936 | 53 / 53 |
| grouped cards | 638 | 38 |
| net collapse | 298 | 15 |
| multi-record groups / records in them | 138 / 436 | 7 / 22 |
| largest group | 11 | — |
| Flat Mode raw invariant | — | 53，PASS |

population safety scope 覆盖：当前多成员组 138 组 / 436 records；历史 1bee6de 多成员组 129 组；pair scope 为 current=697、changed-vs-1bee6de=138、legacy 40/62 review=538；相对 1bee6de 的 changed group key=71。

| population relation audit | count |
|---|---:|
| confirmed same-pack | 630 |
| confirmed false merge | 0 |
| false split | 0 |
| explicitly audited safety relations | 6 |
| UNKNOWN evidence | 0 |
| uncovered | 296 |
| relation conflict | 94 |

`26 gate + 32 protection samples` 没有被当成全 936 population 的安全证明；未覆盖和冲突保持 BLOCKED。

## 独立检测测试与 fault injection

独立 self-test 在冻结标签之后运行 actual candidate decisions：

- frozen label SHA-256：`8336fa18b54e36e3a1b89d3528061228d9865a7df6f47084a66d675964bd5e6d`。
- `MUST` split 注入：`BV1RiPWzDE4Q / BV1ZsFbzZE1b`，结果 `false_split`。
- `CANNOT` merge 注入：`BV1TFUnB9ENB / BV1tG42evEuE`，结果 `false_merge`。
- candidate output 未用于生成 frozen labels；runtime rerun labels stable=true。

测试文件：[tests/test_bilibili_independent_safety_audit.py](../../tests/test_bilibili_independent_safety_audit.py)。它断言不完整独立证据必须返回 `BLOCKED`，而不是只检查样本格式或从 candidate output 派生 expected。

## 测试与日志

最终同源码门禁日志位于 `docs/audit/logs/`（日志文件按日期命名，末尾记录 `EXIT_CODE`）：

| 命令 | 退出码 | 日志 |
|---|---:|---|
| `node pipeline/audit/phase3gf_expanded_runtime_audit.js --self-test` | 0 | `phase3gf_independent_self_test_final3_2026-09-20.log` |
| `node pipeline/audit/phase3gf_expanded_runtime_audit.js --out ... --holdout-out ...` | 2（BLOCKED，预期） | `phase3gf_independent_audit_final3_2026-09-20.log` |
| `node pipeline/audit/phase3gf_runtime_acceptance.js --out ...` | 0 | `phase3gf_runtime_acceptance_final2_2026-09-20.log` |
| `python -m unittest -v tests.test_bilibili_independent_safety_audit` | 0 | `phase3gf_independent_audit_tests_final3_2026-09-20.log` |
| `python -m unittest -v tests.test_bilibili_undermerge_runtime_acceptance tests.test_bilibili_undermerge_runtime_closure` | 0 | `phase3gf_undermerge_acceptance_closure_final2_2026-09-20.log` |
| `python -m unittest -v tests.test_bilibili_grouping_runtime_remediation_3gf2a` | 0 | `phase3gf_runtime_remediation_3gf2a_final2_2026-09-20.log` |
| `npm.cmd --prefix apps/web run typecheck` | 0 | `phase3gf_web_typecheck_final2_2026-09-20.log` |
| `npm.cmd --prefix apps/web run test` | 0；11 files / 103 tests | `phase3gf_web_vitest_final2_2026-09-20.log` |
| reviewer `reproduce.cjs` search | 未发现文件，未运行 | — |

审计 JSON 在测试时记录 `audit_head=37ea9f61fa1af5fe1731ccdc93130b69e4f64ea4`；runtime source raw/bundle hash 如上。最终提交 SHA 与 clean status 在本次 Codex 回交消息中记录，需以最终提交后的 Git ref 为准；测试时 SHA 与最终 SHA 不混写。

## Git / 范围检查

允许变更仅限：

- `apps/web/src/domain/bilibiliGrouping.ts`
- `pipeline/audit/phase3gf_expanded_runtime_audit.js`（兼容入口）
- `pipeline/audit/phase3gf_independent_safety_audit.js`
- `tests/test_bilibili_independent_safety_audit.py`
- `docs/audit/` 审计结果与本报告

未修改 `FEATURE_TRUTH_MATRIX.md`、`cutover_frontend_to_modern.py`、`manifest.py`、`browser_harness.js`、`production_state.json` 或 Production artifacts。B 分支冻结，Obsidian 目录/共享规则/Handoff 未触碰。

最终决策：`runtime candidate = NOT ACCEPTED`，原因是独立关系覆盖与冲突仍未闭合；停在 audit handoff，等待 Codex 最终审核。

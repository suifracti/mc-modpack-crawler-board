# Phase 3G-F.3-A — runtime repair handoff

## 结论与边界

本轮 A 已完成验收器返修与通用 runtime 修复。修正后的动态 acceptance
通过：26/26 under-merge gate、27/27 DIFFERENT_PACKS protection、5/5
AMBIGUOUS protection。结果交回 Codex 审核；本轮不做 runtime integration、
Truth Matrix 最终定稿、Production cutover 或生产写入。

| 项目 | 值 |
|---|---|
| 起点 | 0f079a72023107bee5cf9058abca1fdd21659a75 |
| branch | fix/phase3gf-f3a-runtime |
| worktree | C:/Users/Administrator/.codex/worktrees/phase3gf-f3a-runtime/我的世界整合包获取 |
| runtime implementation | 61fd4e0c6594fa5e7577de0fc7f06dac4ca6af70 |
| acceptance run HEAD | 331b655467288da6114fe1bb3f365d609a5049ab |
| pre-report artifact HEAD | 15cfbe9bd0d041fed34b616d25ff7bea29aaa498 |
| B / integration / cutover | untouched / not performed / not performed |

331b655 只补了 acceptance runner 的 Git raw blob 与工作树语义分离；它与
61fd4e0 的 runtime 源文件 blob 相同。15cfbe9 只记录最终 acceptance JSON。

## 验收器修复

新增并冻结：

- pipeline/audit/fixtures/phase3gf_runtime_acceptance.json
- pipeline/audit/phase3gf_runtime_acceptance.js
- pipeline/audit/build_phase3gf_runtime_fixture.js
- tests/test_bilibili_undermerge_runtime_acceptance.py

fixture 固定原 26 条 gate 的完整 BVID 成员、32 条 protection case 的完整
成员分区、证据关系与来源 hash：27 条 DIFFERENT_PACKS、5 条 AMBIGUOUS、80
个去重后的 gate BVID、936 条完整 population。成员只从 immutable fixture
读取；evidence 仅用于逐项映射与 hash 校验，不会按当前 runtime group key
重新筛选候选。

三种基线严格区分：

| 语义 | 来源 | bundle SHA-256 |
|---|---|---|
| ground-truth evidence runtime | 4bf5e0fe4c614f3e630ae242db2ed5b66ef95fea | 3d10e2e63cc50d1660d1d95c81658444b67ef21250f4af171366b97e1582c15e |
| repair-before runtime | 1bee6dea6a30ff0b6368091c614c528263a2f0a2 | 12fb5f96f2cd3cf587130bae45f0eda19347e8ca54d019b8f2d553a8e7c7692e |
| candidate runtime | 61fd4e0 runtime blob, acceptance run at 331b655 | 74470f57624a8327891e37f7f68b5c9c0f87a936fd11e4a0b8f8c8d210ddc48e |

输入校验记录：

- fixture SHA-256: e199f305cdf4679dd68b79d027b899302f3e8696c5e23131634cd0277e56ba6f
- gate Git 原始字节: 4e91fe1d8bc3c16a8fe1b3cc65be9a64dcc56f47b29b2a218524029ca82a9d90
- gate 工作树原始字节: cafec9955c5e589315279b348dc5520a17594bebfc5d43dde08b4a810dfafad7
- gate 工作树规范化后: 4e91fe1d8bc3c16a8fe1b3cc65be9a64dcc56f47b29b2a218524029ca82a9d90
- Git raw 与规范化语义一致: true
- evidence: bd8b76a51dba40079f258183ef27cbe438c7e220af972a5fe877a1f9ff2df083
- candidate audit: c32814f6926c2c5c6e2be5552d3e7cd0b61e7ead82d0e10e1d8c007c8ff846a4
- population: 049fe4c567fabafb4e4c58018b606c1aa23d01d2d1511933856454915e79bebe

验收器现在 fail-closed：缺失、重复、空成员、模糊映射、输入 hash 漂移、
fixture/evidence 来源不一致、当前 runtime 变化而继续复用旧 JSON 均失败。
测试覆盖 group-key 纯改名、key 不变却吸入负例、空/缺失 evidence、hash
漂移与 current mutation。gzip artifact 只做最小读取适配，并分别记录容器
原始字节 hash 与解压后的语义一致性；没有重生成标签、缩小样本或替换
ground truth。

## 通用 runtime 修复

runtime 仍只在 apps/web/src/domain/bilibiliGrouping.ts；packName 的改动只
补充 ×/CJK x 分隔符，legacy bridge 只转发完整输入类型。规则按以下类别
实施，没有 BVID→group 映射、uploader 白名单或具体 pack title 特判：

1. 注册项目 identity 提取与传递：从注册项目 URL 提取 canonical identity，
   作为辅助 corroboration；必须有 author-local title anchor，URL/QQ 单独不能
   触发合并。
2. 名称与标点规范化：CJK/Latin compound、×/x、中文分隔符、noise token 与
   连接词分层处理，避免主题词或宣传语成为 identity。
3. 版本与更新连续性：版本/发布结构、重复标题与同一命名线可以桥接被省略
   的短名称，但必须满足重复、release/update signal 与唯一候选 identity。
4. 同主题不同包拒绝：registered project conflict、name-slot/bracket
   disagreement、feature-list 与 competing edition marker 会拒绝共享主题
   锚点；完整 population 中 case 所属 group 的外部成员也参与校验。

运行时输入可以携带 download_links 与 qq_group，但二者只作辅助证据。通用
规则反例和禁止硬编码测试均通过；源码中无运行时 BVID 映射、审计 fixture
import 或调试 marker。

## 26 条冻结 gate

Before 是 evidence source runtime，不是 1bee6de；Pre-fix 是可从 1bee6de
重编译的 runtime；After 是 candidate runtime。Expected 均为一个 identity。
完整成员、逐条 evidence、关系分区和 full-population 外部成员在
pipeline/audit/phase3gf_runtime_acceptance.json 的 gate_cases 中保存。

| # | case / author | 完整 BVID 成员 | Before / Pre-fix / After | evidence anchor | result |
|---:|---|---|---:|---|---|
| 1 | -阳春面面 | BV1K6HjeTEKJ, BV1bZigehE6V, BV1qTDNY3Ekc | 2 / 3 / 1 | 青春复兴命名线与版本连续性 | PASS |
| 2 | 爱吃土豆的界王 | BV1RiPWzDE4Q, BV1ZsFbzZE1b | 2 / 2 / 1 | 考古与化石同包、标点变体 | PASS |
| 3 | 爱吃土豆的界王 | BV19vto6XETe, BV1bPQCBcEws, BV1zRjv6gEAp | 2 / 2 / 1 | 山海大陆×斗罗大陆同包版本线 | PASS |
| 4 | 爱玩游戏的烛梦 | BV1iYt46kEtC, BV1u34162EuC | 2 / 2 / 1 | 基岩版仿亡者世界更新线 | PASS |
| 5 | 炒雪吵狐力o | BV16dcgzUEm2, BV1HgGvz2ENe, BV1MzGAzqEsq, BV1f3eAz3Env, BV1zr8V62EvF | 3 / 3 / 1 | mcmod:modpack/1159 与版本连续性 | PASS |
| 6 | 孑孑雨不是牢孑 | BV1ej411q7Kj, BV1of421v7ug | 2 / 2 / 1 | 烦村 / annoying_villagers alias | PASS |
| 7 | 科里森Corrison | BV1ApFYz2E7v, BV1bzPMzYE91, BV1iCrMBnEG5, BV1j5V56TEoE, BV1xnvvBbEbj, BV1zGduBhEt2 | 2 / 2 / 1 | xyebbs:resource/1421 与中英别名 | PASS |
| 8 | 空空如也js | BV1Jg4y1S7zy, BV1aN4y1W7Mx | 2 / 2 / 1 | 惊变100天 FTB500 identity | PASS |
| 9 | 流霜雾影 | BV1CLnmzgECo, BV1iRL7zYExj, BV1s3ZNBYEQU | 2 / 1 / 1 | bbsmc:modpack/the-fool | PASS |
| 10 | 芦苇草的梦想 | BV14e2LBuEAK, BV1KdrKBeE9Z, BV1hN6FBnEUp | 3 / 1 / 1 | Modrinth project 与版本链 | PASS |
| 11 | 鹿清玖LQJ | BV1AoULBgEoH, BV1aRYC6cE4p | 2 / 2 / 1 | 溯渊标题重复 | PASS |
| 12 | 落烟雨辰呀 | BV1JTwZzDEQr, BV1gkT66HEzV, BV1qg5a6dEuh, BV1s2X4BnEkR | 2 / 1 / 1 | 分隔符变体与连续版本 | PASS |
| 13 | 墨言eclipse | BV1CQtC6eEaC, BV1LyN366E4u, BV1UJET67ErR, BV1ZTuJ6rEJp, BV1sNjq6pEAd | 4 / 1 / 1 | 涅槃 pack 内注册 identity 与版本 | PASS |
| 14 | 三只大猪TB_pig | BV1Er7G6yEKK, BV1kDBpBcE9x | 2 / 2 / 1 | 铁砧工艺极速版注册项目 | PASS |
| 15 | 韬可梦 | BV13u4y1e7xC, BV1RT411h7gm | 2 / 2 / 1 | 宝可梦 pack 连续性 | PASS |
| 16 | 我嘞个牢末ENd | BV1SY7wzJE9w, BV1aojdzzE47 | 2 / 2 / 1 | 原版增强 1.20.1 同包 | PASS |
| 17 | 吴也mc | BV1LY4y1S756, BV1sY411d7bd | 2 / 2 / 1 | 灾难降临更新连续性 | PASS |
| 18 | 小兜兜呀_ | BV1JU4k69E61, BV1Y2K467EGN, BV1cjut6BEaG, BV1nJbQ6pEHo, BV1orhK64Em6, BV1qi8r69Eck, BV1tUTK6JE2o | 2 / 2 / 1 | BBSMC project identities | PASS |
| 19 | 小水滴的源头 | BV13rfqY2Ejf, BV14z9FYRED5, BV1UGveexEHn | 3 / 3 / 1 | 蔚蓝档案 release/update line | PASS |
| 20 | 星必尘Sguan | BV1M3411d7xX, BV1dR4y1T7jD | 2 / 2 / 1 | 基岩版 RLCraft 汉化 pack | PASS |
| 21 | 星遥工坊 | BV17FUkBPEEb, BV1at1cYkEXV | 2 / 2 / 1 | 刀剑异闻录 pack name | PASS |
| 22 | 在下Shmily | BV12TxAzvE9r, BV1XTqSBHEyr, BV1zNvCBrEgL | 3 / 1 / 1 | 最牛优化版本线 | PASS |
| 23 | Karashok_Leo | BV172KczaEke, BV1MCFSzTE62, BV1QN6HYnE5W, BV1iDdLYJESg | 2 / 2 / 1 | Spell Dimension registered identities | PASS |
| 24 | KonataWorks | BV1Fg8gzHE7K, BV1Fg8gzHEVB | 2 / 2 / 1 | unnamed pack consecutive versions | PASS |
| 25 | Pork猪排 | BV12VtQzkEcm, BV1BA9wBqEnE, BV1GrzxBZE7S, BV1PMAVzKExm, BV1nbTqzCECX | 4 / 2 / 1 | 化龍 project identities/version chain | PASS |
| 26 | SmartAkita | BV13mD9YMEFq, BV1GKS4YtExK | 2 / 2 / 1 | Cobblemon release identity | PASS |

相对 1bee6de 的 new merge / split / pure rename 逐 pair 记录也在 JSON；
正例新合并均有 identity anchor 与 evidence，protection 分区没有新增跨
identity 合并。没有确认的新增 false merge 被保留为已证实事实。

## Protection、known-8 与统计口径

- 27 DIFFERENT_PACKS：27/27 PROTECTED。按 BVID 的 must-link/cannot-link/
  unknown 分区与完整 population 外部成员检查，不把旧 group key 当 identity。
- 5 AMBIGUOUS：5/5 PROTECTED；继续是证据不足保护样本，没有升级为
  DIFFERENT_PACKS，也没有新增未经证实的合并。
- 32 个 protection case 均有完整成员与覆盖校验；缺失、重复、空成员不会
  因 every(empty) 被算作 PASS。逐 case 结果在 JSON 的 protected_cases。
- known-8 read-only check：8/8 CLOSED；没有重新出现 live false merge。
- 涅槃 corrected evidence：涅槃 5 条与未尽之路-涅槃 2 条是两个 identity；
  runtime remediation test 14/14 通过，不再使用旧的 7→1 premise。
- packs_to_unify=34 的定义是 sum(group_count - 1)，表示待归并的多余分组数，
  不是 34 个目标整合包。gate 的 80 records 报告为 80 个去重后的 BVID，
  不把相加数自动当成唯一记录数。

## 动态与 benchmark 结果

frozen benchmark 与 remediation evaluator：

- 936 raw records；机械动力 raw=53，前后不变，Flat Mode raw 不变。
- frozen scored benchmark：FM=0，precision=1，recall=0.875。
- expanded remediation：overall FM=0，recall=0.875；holdout FM=0，
  recall=1.0；22/22 negative separation；旧 false split 修复 18/21。
- population card count：857 → 639；size >= 5 groups 为 24。

这些是直接使用冻结 benchmark/holdout 与 corrected runtime acceptance 的结果。
旧的 population v2 / precision audit 仍把 closure 后的可变 group key 当作
旧 ledger key，不能作为新的 ground truth。它们的失败被保留并如实列在下面，
没有以修改 ground truth 的方式清零。

## 测试记录

| 命令 | 退出码 | 测试时 SHA / 结果 | 日志 |
|---|---:|---|---|
| npm.cmd --prefix apps/web run typecheck | 0 | runtime source 61fd4e0 | docs/audit/logs/phase3gf-f3a-final-typecheck-61fd4e0.log |
| npm.cmd --prefix apps/web run test | 0 | 11 files / 103 tests | docs/audit/logs/phase3gf-f3a-final-vitest-61fd4e0.log |
| python -m unittest tests.test_bilibili_undermerge_runtime_acceptance -v | 0 | 8/8 | docs/audit/logs/phase3gf-f3a-final-python-acceptance-61fd4e0.log |
| python -m unittest tests.test_bilibili_undermerge_runtime_closure -v | 0 | 5/5 | docs/audit/logs/phase3gf-f3a-final-python-acceptance-61fd4e0.log |
| python -m unittest tests.test_bilibili_grouping_runtime_remediation_3gf2a -v | 0 | 14/14 | docs/audit/logs/phase3gf-f3a-final-python-acceptance-61fd4e0.log |
| node pipeline/audit/bilibili_grouping_benchmark.js | 0 | frozen benchmark | docs/audit/logs/phase3gf-f3a-final-benchmark-61fd4e0.log |
| python pipeline/audit/split_bili_grouping_corpus.py | 0 | frozen dev/holdout split | docs/audit/logs/phase3gf-f3a-final-benchmark-61fd4e0.log |
| node pipeline/audit/bilibili_grouping_remediation_eval.js | 0 | benchmark/holdout result above | docs/audit/logs/phase3gf-f3a-final-benchmark-61fd4e0.log |
| node pipeline/audit/phase3gf_runtime_acceptance.js --current-module build/audit/phase3gf_final_runtime_bundle.js --out pipeline/audit/phase3gf_runtime_acceptance.json | 0 | 331b655; 26/26, 27/27, 5/5 | docs/audit/logs/phase3gf-f3a-final-runtime-gate-331b655-final.log |

旧套件的失败不被包装成 PASS：

- tests.test_bilibili_grouping_benchmark：exit 1，Python wrapper 需要缺失的
  converted_output/assets/index.js；对应直接 Node frozen benchmark 已 exit 0。
- tests.test_bilibili_undermerge_adjudication：exit 1，旧 scanner/evidence
  与 closure 后 group key 不再一一映射，唯一失败为旧的
  xyebbs:resource/1421 assertion；tracked ground truth 已恢复。
- tests.test_bilibili_population_audit_v2：exit 1，旧手工 ledger 依赖 pre-
  closure group key，当前 candidate 重新生成后出现 stale/unadjudicated rows；
  未修改 ledger，生成物已恢复。
- tests.test_bilibili_grouping_precision_audit：exit 1，同一 stale group-key
  耦合导致旧 anchor adjudication 不可独立验证；生成物已恢复。

完整旧套件日志为 docs/audit/logs/phase3gf-f3a-final-legacy-suite-results-331b655.log。
任何未通过项均未被计入本轮 runtime acceptance PASS。

## Git、生产只读与停点

本轮相对起点的完整 diff stat 以最终 git diff --stat
0f079a72023107bee5cf9058abca1fdd21659a75..HEAD 为准；其中 report-only
文档提交发生在所有 runtime 测试之后，没有重新宣称测试覆盖该提交。

变更只落在 runtime、acceptance fixture/runner/test 与报告 JSON；没有
apps/web 以外的生产 cutover 文件修改。ref 核验：

- git show-ref --verify refs/heads/fix/phase3gf-f3a-runtime 指向
  15cfbe9bd0d041fed34b616d25ff7bea29aaa498
- git rev-parse HEAD 与 HEAD^{commit} 一致
- git cat-file -t HEAD 为 commit
- git status --porcelain 为 0 行

A worktree 中没有可读取的 build/production_state.json。该结论只表示本
worktree 未提供 production state，不能推断整个生产部署不存在 state。
本轮没有写 production_state、Production manifest，也没有独立声称
production_build_commit、canonical hash 或 data rollup 已验证；manifest/
cutover 测试按本轮禁止发布边界未执行。当前 production 仍保持原发布状态
的假设，交由 Codex 在 runtime 接受后进行下一阶段只读核验。

最终停点：保留 branch 与全部 evidence/report，交 Codex 审核；不集成、
不发布、不修改 B。

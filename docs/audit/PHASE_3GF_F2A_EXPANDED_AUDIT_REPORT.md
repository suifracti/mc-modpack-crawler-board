# Phase 3G-F.2-A — Expanded Population Audit vs Runtime Remediation

**Branch** `3gf2a-expanded-audit` · **Worktree** `D:/ai/work/mc-3gf2a` (started from `3f81db2`)
**Final commit** `02bb18b` (parent `59edd47`, parent `d702caf` = `2f7ae1e`)
**Verdict** §13 → **runtime remediation candidate PASS** (四门禁全过)
**Production cutover** — **未执行**（按指示停在提交处）

---

## §0 Baseline 与 worktree

| 项 | 值 |
| --- | --- |
| Runtime fix | `3f81db2`（parent `ef411d1`）|
| Expanded audit | `e30e497` ← parent `ef411d1`；`2f7ae1e` ← parent `e30e497` |
| 独立 worktree | `D:/ai/work/mc-3gf2a`，从 `3f81db2` 起，分支 `3gf2a-expanded-audit` |

`e30e497` 的祖先是 `ef411d1` —— **确认**（即 expanded audit 与 runtime fix 同源，无隐性分叉）。

## §1 合并 expanded audit

`git cherry-pick e30e497` → `git cherry-pick 2f7ae1e`，**零冲突**（两者改动文件无重叠）。

- 逐文件字节校验：`git rev-parse <commit>:<file>` 与 `git hash-object <file>` **完全一致**。
- **未借冲突消解偷改 ground truth** —— 没有任何冲突可消解。

## §2 冻结 expanded audit

- tracked 产物确认为 `bilibili_population_adjudication_v2.json` 与 `bilibili_population_holdout_v2.json`。
- 连跑两次 → `git hash-object` 完全相同；`git status` 干净。

## §3 新审计先跑（不改 runtime）

对 `3f81db2` 的 runtime 跑 expanded audit：

| 项 | 结果 |
| --- | --- |
| 8 个已知真误合并 | **8/8 已 retired**，**0 个仍在合并** |
| 剩余 known confirmed false merge | **0** |
| `一个小寂哦::怪物大乱斗` | **已分列**：`手机版` 与 `重生版` 各自成组 |

## §4 怪物大乱斗 Ground Truth —— 独立验证后**成立**

**结论：模块 2 的主张正确，两包必须分开。**

独立取证：

| 记录 | 共享锚 | 其后 token | 身份字符 | 佐证 |
| --- | --- | --- | --- | --- |
| `BV1f4Kp6yEBf` | 怪物大乱斗 | **手机版** | 0 | — |
| `BV1nRBFBFEFw` | 怪物大乱斗 | **重生** | 0 | 同 uploader 自身 3 人组成组独立佐证 `重生` |

两 token 互斥、均为零身份字符、`run.length === 1` → 命中新增 **R5 `competing_edition`**，正确分列。
**未修改任何 ledger 来迁就算法。**

## §5 剩余误合并的修复范围

仅修剩余已确认个案。**未**做大规模停用词改动、**未**重设计整个分组、**未**对个案硬编码标题
（回归测试断言个案标题**不得**作为 runtime 字符串字面量出现）。

实际落地 4 项修复，全在共享 admissibility 层：

1. **R5 `competing_edition`** —— 互斥版本标签（怪物大乱斗）。
2. **`isSelfNameSegment`** —— `【天晓の整合包发布】` 是频道自称非包名（R1 曾对它失明）。
3. **R6 `bracketed_name_disagreement`** —— 方括号真名压过更弱的扁平描述符（墨竹ギ）。
4. **`containsRun` 支持拼接/拆分拼写** —— 长多 token 名此前不是其 join 形式的超集。

R6 保留**强度守卫** `identityChars(run) < bestBracketChars`：去掉会让 POS-URL-09 咒次元 Recall 0.875→0.8333。

## §6 Expanded Holdout

模块 2 新增 **46 positive / 66 negative / 95 uploaders / uploader overlap = 0**。

在 runtime fix 上运行后：

| 指标 | 值 |
| --- | --- |
| **holdout FM** | **0** ✅（硬门禁满足）|
| holdout Precision | **1.0** |
| holdout Recall | **1.0** |
| TM / FS / TS | 6 / 0 / 12 |
| 规模（重导后）| **44 pos / 71 neg / 97 uploaders**，overlap = 0 |

**为何数字变了（44/71/97 而非 46/66/95）：** holdout builder 消费 **(ledger × runtime × old-vs-new diff)**，
是**派生产物**。修完 runtime 必然重导 —— 这是**正确行为**。
个案 diff 确认净新增正例（`在下Shmily::最牛优化`、`不知名的莫理沙::星月枪姬与落魄勇者`）是修复带来的合并收益，
掉出的映射到 `RETIRED_CANDIDATE_KEYS`。
→ **测试因此钉「派生契约」（正负下限、uploader 不相交），不再钉某次测量的数字。**

## §7 113 Candidate Adjudication

对修复后的分组输出**重新映射**（未按旧 groupKey 直接判定）：

| 项 | 值 |
| --- | --- |
| candidates | **100**（v2 扫描器口径）|
| adjudicated | **100 / 100** |
| REAL_FALSE_MERGE 剩余 | **0** |
| LEGITIMATE_SAME_PACK | **100** |
| AMBIGUOUS | 0 |
| unadjudicated | 0 |
| declared-but-absent | 0 |
| retired candidate keys | 26 |

## §8 Under-Merge

**未把全部 34 条当 bug。** 按证据等级分类（58 簇全裁定）：

| 类别 | 数 |
| --- | --- |
| CONFIRMED | **24** |
| STRONG | 2 |
| DIFFERENT_PACKS | 27 |
| AMBIGUOUS | 5 |
| PARTIAL | 0 |

- **gate 只含 CONFIRMED + STRONG**（26 条 / 25 上传者 / 80 记录 / 34 待统一包）；**AMBIGUOUS 绝不入 gate**。
- **`confirmed under-merge remaining` = 33 簇** —— 它们是 false **split**（欠合并），按 §8 分类处置，**不当 bug 修**。
- 翻转模块 2 三例：`ZangHeRo`→DIFFERENT_PACKS、`在职玩家JoStar`→AMBIGUOUS、`爱吃土豆的界王::时光牧场vs侏罗纪公园`（仅共享恐龙主题）。

## §9 涅槃 Ground Truth 已纠正

`5 records → 涅槃`；`2 records → 未尽之路-涅槃`；`3 records → 未尽之路(unfinished-path)`。

| 名称 | 记录 | 组 | 注册身份 |
| --- | --- | --- | --- |
| `涅槃` | 5 | 4 | `xyebbs:resource/37418`, `mcmod:modpack/1418` |
| `未尽之路-涅槃` | 2 | 1 | `bbsmc:modpack/unfinished_path_nirvana`, `xyebbs:res-id/TUPN` |
| `未尽之路(unfinished-path)` | 3 | 1 | `bbsmc:modpack/unfinished-path`, `xyebbs:res-id/UP` |

- **正确目标 = 2 组**，不是 1 组。
- **测试不再要求 7→1**：`test_nie_corrected_target_is_two_groups` 断言 2 组；
  旧 5 键列表只留作**回归探测器** `nie_regressed_to_legacy_split`（阈值 `>1`，
  因为 `未尽之路涅槃` 本身是旧键且在正确目标里）。
- 旧测试 `test_all_known_7_adjudicated_real` 要求已知误合并**仍然是** `REAL_FALSE_MERGE`
  —— **它把「修复」断言成了「缺陷仍在」**（符号相反）。已改为**互斥两条**：
  ①已退休且有原因 ②不得以 live `REAL_FALSE_MERGE` 复现。**未靠放宽断言「修」它。**

## §10 Frozen Benchmark

`bilibili_grouping_remediation.json` 的 **`after`**（**交付口径**）：

| 指标 | 值 | 要求 | 状态 |
| --- | --- | --- | --- |
| **TM** | **21** | 21 | ✅ |
| **FS** | **3** | 3 | ✅ |
| **TS** | **22** | 22 | ✅ |
| **FM** | **0** | 0 | ✅ |
| **Recall** | **0.875** | ≥ 0.75 | ✅ |
| Precision | 1.0 | — | ✅ |

negative regression: **22/22 separate**（all=true）。old false splits fixed: **18/21**。

⚠️ 同文件里的 **BEFORE** 是 `TM=3 / FS=21 / R=0.125` —— **不是**交付口径（极易读错）。

## §11 机械动力

`raw = 53` **保持**（唯一不变量）。grouped 从 47 → **39**（**不是**不变量）。
测量面 = 前端搜索面 `title + author + desc + mc_version + loaders + categories`（title 正则只有 30）。
population: before 857 → after **673** cards。

## §12 测试

| 套件 | 结果 |
| --- | --- |
| expanded population audit v2 | **37 / 37** |
| runtime remediation 3G-F.2-A | **14 / 14** |
| precision audit | **17 / 17** |
| frozen benchmark | **12 / 12** |
| **Vitest** | **103 / 103** |
| **`tsc --noEmit`** | **exit 0** |

## §13 判定 —— 四门禁同时成立

| 门禁 | 值 | 状态 |
| --- | --- | --- |
| known confirmed false merge | **0**（8/8 retired，0 still merging）| ✅ PASS |
| holdout FM | **0**（P=1.0, R=1.0）| ✅ PASS |
| frozen benchmark FM | **0**（P=1.0）| ✅ PASS |
| frozen benchmark Recall | **0.875 ≥ 0.75** | ✅ PASS |

**→ runtime remediation candidate PASS。**

附带：100/100 candidates 全裁定、0 unadjudicated、0 declared-but-absent、0 跨上传者组、
33 confirmed under-merge（false split）、涅槃 = 2 组未回退。

## §14 收尾（额外）

**MEMORY.md 瘦身** 21556 → 21024 bytes（删掉已完整存在于 `docs/audit/` 的叙述）。
剩余全为单行硬约束，无冗余可再删。

**tracked 大产物改 gzip**（commit `02bb18b`）—— 台账 309KB + holdout 129KB 体积的**大头就是证据**
（`title` 621 条 61KB、`note` 210 条 28KB）。**删字段等于把台账退回成不可证伪的断言**。实测：

| 形式 | bytes | vs pretty |
| --- | --- | --- |
| pretty | 309,399 | 100% |
| minified | 147,424 | 48% |
| 短键名 + minified | 120,877 | 39% |
| **gzip -9** | **55,695** | **18%** |

gzip 每个维度都赢 —— 最小、零 schema 改动、解压即原文档。
新增 `pipeline/audit/lib/audit_artifact_io.js`（`readJson()` 按 magic bytes 自动识别）。
**逐字段比对 HEAD 确认 `semantic-identical: true`，零内容变化**；字节可复现测试复跑通过。

---

## 最终状态

```
分支     3gf2a-expanded-audit
HEAD     02bb18b3b053d59ad7f1f7fe6941309dcac1d184
parent   59edd47ee142d8dc668dd77c5c7ec0ad0401e034
祖链     02bb18b → 59edd47 → d702caf(=2f7ae1e) → 7a3c460(=e30e497)
相对 3f81db2: 13 files changed, 3547 insertions(+), 7 deletions(-)
git status: clean
Production cutover: 未执行
```

**完成后停下。未 cutover。**

# Phase 3G-F.2-B — Bilibili Under-Merge Ground-Truth Adjudication

**唯一要回答的问题**：模块2 发现的 under-merge candidates 里，哪些**真的**属于「同包被拆开」，
哪些只是名字相似或错误候选。

**范围**：candidate 冻结 · 逐条裁定 · runtime gate 产出 · 旧 corpus 只读
**明确不涉及**：runtime 改动 / grouping 算法改动 / cutover / Truth Matrix 主文件改写

**结论一句话**：58 个 under-merge clusters **全部裁定完成**（`58/58`，无 unadjudicated、无
declared-but-absent）；其中 **26 条**（24 CONFIRMED + 2 STRONG）证据充分，可进 runtime gate，
覆盖 **25 个上传者 / 80 条记录 / 34 个待统一包**；**27 条**实为不同包（现有 split 本就正确），
**5 条**证据不足（AMBIGUOUS，**不进 gate**）；模块2 的 UNDER_MERGE 判定被**翻转 3 例**，
其中 `ZangHeRo` 最典型——「模拟殖民地」只是「机械殖民地」标题里的**描述词**，
该组实际属于「剑与王国」。**0 条 AMBIGUOUS 泄漏进 gate**（测试断言锁定）。

---

## 1. worktree / starting commit

| 项 | 值 |
| --- | --- |
| 起始提交 | `2f7ae1e283e8627611b11638e11f3d8d3fa89857` |
| 隔离方式 | `git worktree add --detach D:/ai/work/mc-3gf-f2b 2f7ae1e`，分支 `audit-3gf2b-undermerge`（**扁平名**，规避本机 slash-ref 丢 ref） |
| 依赖补齐 | `converted_output/`（130M）、`apps/web/node_modules/`（78M）、`build/audit/`（含 module bundle）为 gitignore 资产，`robocopy /E /MT:16` 复制，**不共享可写状态** |
| ⚠️ 路径陷阱 | 必须传 Windows 绝对路径 `"D:/ai/work/mc-3gf-f2b"`；MSYS 风格 `/d/ai/work/...` 会被解析成 `D:/d/ai/work/...`（多一层 `d`） |

## 2. candidate artifact SHA（§1 冻结）

| 文件 | SHA-256 |
| --- | --- |
| `build/audit/bilibili_cross_group_undermerge_v2.json` | `c32814f6926c2c5c6e2be5552d3e7cd0b61e7ead82d0e10e1d8c007c8ff846a4` |
| `build/audit/bilibili_population_candidates_v2.json` | `e2ba144b7d7ba29b8f2c7ee96eea488d403a939945192c0d30a21ea2dd560770` |

candidate artifact 内容：`pairs_flagged: 226` / `clusters_flagged: 58` / `payload_records: 936`，
阈值 `min_shared_token_chars: 2` / `max_groups_per_token: 4` / `long_token_chars: 4`。

**产出物 SHA-256**：

| 文件 | SHA-256 |
| --- | --- |
| `pipeline/audit/bilibili_undermerge_adjudication_v2.json` | `8987d38db353c77f13385da3b8f4a00a4e95eaaa90bd21de1075c49b5a2f1feb` |
| `pipeline/audit/confirmed_undermerge_runtime_gate.json` | `4e91fe1d8bc3c16a8fe1b3cc65be9a64dcc56f47b29b2a218524029ca82a9d90` |

## 3. 两层分离架构（为什么 verdict 不能被误当成测量）

| 层 | 文件 | 职责 |
| --- | --- | --- |
| 证据提取 | `pipeline/audit/extract_undermerge_evidence.js` | 摊平 58 cluster 的全部成员标题 / URL / QQ。**严禁出现任何 verdict 字符串或字段**（测试 `test_extractors_emit_no_verdicts` 锁定） |
| 身份提取 | `pipeline/audit/extract_undermerge_project_identity.js` | 从 `download_links` 提取**注册项目身份**，输出「全部组共享 / 部分组共享」 |
| **裁定台账** | `pipeline/audit/bilibili_undermerge_adjudication_v2.js` | **唯一可宣布 verdict 处**，手工逐条维护 |
| gate 产出 | `pipeline/audit/build_undermerge_runtime_gate.js` | 只取 CONFIRMED + STRONG |

**规则**：**没有任何 verdict 由规则推导**。每条都是读成员标题与注册项目 id 后人工写入。

## 4. §2 涅槃作为 Ground-Truth 教训（false-positive 典型案例）

**原则**：`"标题 / 系列看起来相同" != "同一个包"`。

| 名称 | 记录 | 组 | 注册身份 |
| --- | --- | --- | --- |
| `涅槃` | 5 | 4 | `xyebbs:resource/37418`, `mcmod:modpack/1418` |
| `未尽之路-涅槃` | 2 | 1 | `bbsmc:modpack/unfinished_path_nirvana`, `xyebbs:res-id/TUPN` |
| `未尽之路(unfinished-path)` | 3 | 1 | `bbsmc:modpack/unfinished-path`, `xyebbs:res-id/UP` |

→ **`expected_packs = 2`**。

**解释**：`未尽之路-涅槃` 把「涅槃」当作 **`未尽之路` 系列的副标题**使用，因此与 `涅槃` 包
**共享一个词却不是同一个包**。注册身份把两者干净分开。

**推论**：模块2 扫描器**把涅槃 key 拆成两个 finding 是正确的**，且 `涅槃` 是本审计的
**reference false-positive under-merge candidate**；`涅槃`（4 组 → 1 包）与
`未尽之路涅槃`（2 个包）**绝不能合并**。

## 5. Evidence 优先级（§4）

**强证据（可单独决定）**
- 同一**注册项目身份**（MCMod / XYEbbs / BBSMC / CurseForge / Modrinth 的 id 或 slug）
- 同一**显式包名延续**
- 上传者**明确的更新 / 版本措辞**（针对具名包）

**辅助证据（永不能单独决定）**：同一下载 URL / 同一 QQ 群 / 同一主题。

> `never_sufficient`：共享下载 URL 或 QQ 群**永不足以**判定——Phase 3G-E 已实证
> **一个夸克链接可覆盖 28 个不同的包**。

**判定枢纽**：两组 `download_links` 是否指向**同一注册项目 id**。
注册身份提取器实测：**7 个 cluster 的全部组共享同一身份**
（`小兜兜呀_` / `科里森Corrison` / `墨言eclipse` / `炒雪吵狐力o` / `Karashok_Leo` /
`流霜雾影` / `三只大猪TB_pig`）。

## 6. §9 量化结果

| 指标 | 值 |
| --- | --- |
| candidates total | **58** |
| adjudicated | **58** |
| unadjudicated | `[]` |
| declared_but_absent | `[]` |
| **CONFIRMED_SAME_PACK** | **24** |
| **STRONG_SAME_PACK** | **2** |
| **DIFFERENT_PACKS** | **27** |
| **AMBIGUOUS** | **5** |
| **PARTIAL** | **0** |
| runtime gate size | **26** |
| distinct uploaders（gate 内） | **25** |
| records involved（gate 内） | **80** |
| packs to unify | **34** |
| excluded | **32**（27 DIFFERENT + 5 AMBIGUOUS） |

**置信度分布**：`high 42 / medium 12 / low 4`。

## 7. §8 Runtime Gate（只含 CONFIRMED + STRONG）

`pipeline/audit/confirmed_undermerge_runtime_gate.json` → `gate_size: 26`，`cases` 26 条，
verdict 混合 = `{CONFIRMED_SAME_PACK: 24, STRONG_SAME_PACK: 2}`。

**非 CONFIRMED/STRONG 出现在 gate 内：`[]`（零泄漏）**。

**gate 内 25 个上传者**：
`-阳春面面-` · `Karashok_Leo` · `KonataWorks` · `Pork猪排` · `SmartAkita` · `三只大猪TB_pig` ·
`吴也mc` · `在下Shmily` · `墨言eclipse` · `孑孑雨不是牢孑` · `小兜兜呀_` · `小水滴的源头` ·
`我嘞个牢末ENd` · `星必尘Sguan` · `星遥工坊` · `流霜雾影` · `炒雪吵狐力o` · `爱吃土豆的界王` ·
`爱玩游戏的烛梦` · `科里森Corrison` · `空空如也js` · `芦苇草的梦想` · `落烟雨辰呀` · `韬可梦` ·
`鹿清玖LQJ`

**排除理由已显式记录**：
- `AMBIGUOUS` = 证据不足以判定，**MUST NOT be gated**——把一个「承认无知」的条目送进 gate，
  等于**把无知转换成行为改变**。
- `DIFFERENT_PACKS` = 已裁定为不同包，**现有 split 正确**。
- `PARTIAL` = 部分 key 该合、部分不该合，**cluster 级改动会出错**。

## 8. §5 Named-case 复核（含实质翻转）

| 上传者 | 裁定 | 置信 | 依据 |
| --- | --- | --- | --- |
| **`科里森Corrison`** | `CONFIRMED_SAME_PACK` | high | 两组同 `xyebbs:resource/1421`；`apotheosis conquest` 就是「神之征伐」的英文名。**模块2 判定正确** |
| **`落烟雨辰呀`** | `CONFIRMED_SAME_PACK` | medium | 「诡厄使徒」≡「诡厄：使徒」，版本 `1.0.6 → 1.1.0` 连续 |
| **`ZangHeRo`** | **`DIFFERENT_PACKS`** ⚠️翻转 | medium | `机械殖民地` 与 `模拟殖民地` 是两个包；「模拟殖民地」只是 `机械殖民地` 标题里的**描述词**，`模拟殖民地` 组实际属「剑与王国」 |
| **`在职玩家JoStar`** | **`AMBIGUOUS`** ⚠️翻转 | low | `方可梦` 组标题里**根本没提** `去吧，方可梦大师` 那包名，可能是独立包 |
| `Karashok_Leo` | `CONFIRMED_SAME_PACK` | high | `__raw_` 桶与命名组**共享全部 4 个注册 id**（bbsmc / curseforge / github / mcmod 1024），split 是真的 |

**模块2 判定正确、予以保留的典型**：
- `VM汉化组`（汉化搬运，5 个**不同**上游 id）
- `豆腐ki`（25 个**不同**第三方包，含 `mcmod:613`/`49`、`curseforge:all-the-mods-3-expert`/`10` 冲突证据）
- `时唅`（4 系列：辐射新世纪 / 辐射次时代 / 生还者 / 潜行者）
- `一个小寂哦`（12+ 个不同包；泰坦 / 星辉死神是**共用组件**）
- `墨竹ギ`（深渊之诗 / 失落的异界 / 史诗的地下城 / 幻想的地下城）

## 9. §9 模块2 被翻转 3 例（记入 `overturns_of_module2`）

| cluster | 模块2 | 本台账 |
| --- | --- | --- |
| `ZangHeRo::机械殖民地 vs 模拟殖民地` | UNDER_MERGE | **DIFFERENT_PACKS** |
| `在职玩家JoStar::去吧 方可梦大师 vs 方可梦` | UNDER_MERGE | **AMBIGUOUS**（不进 gate） |
| `爱吃土豆的界王::时光牧场 vs 侏罗纪公园` | UNDER_MERGE | **DIFFERENT_PACKS**（仅共享恐龙主题） |

另有 `一个小寂哦::怪物大乱斗 vs 怪物大乱斗重生` 裁为 `DIFFERENT_PACKS`（手机版 vs 重生
是两个独立发行），与模块2 candidate 层结论一致。

## 10. §7 旧 corpus 只读（未修改）

以下文件**全部只读**，与 base `2f7ae1e` **逐字节相同**（`git diff --numstat` 无输出，
index blob hash 与工作区 hash 一致）：

- `pipeline/audit/bilibili_population_adjudication_v2.json`（模块2，`e93331cb…`）
- `pipeline/audit/bilibili_population_holdout_v2.json`（模块2，`a98c3126…`）
- `pipeline/audit/bilibili_grouping_corpus.json`
- 旧 positive / negative corpus · holdout v2 · false-merge adjudication

`runtime` / `grouping algorithm` / `cutover` / `manifest` / **Truth Matrix 主文件**：
**零改动**（`git diff --stat 2f7ae1e -- apps/web/src web/ pipeline/` 为空）。

> ⚠️ **踩坑记录（phantom modified）**：跑完测试后 `git status` 曾把这两个 tracked 产物报为
> ` M`，但 `git diff` 为空、`hash-object` 与 index blob **完全相同**、`python` 逐字节比较
> 输出 `IDENTICAL`。**根因是索引 stat 缓存陈旧**（缓存记 `size: 304440`，
> 实际 `296399`，`core.autocrlf=true` 下的伪差异）。修复：`git add --renormalize` +
> `git update-index --refresh`。**判据**：`git diff` 空但 `git status` 报 `M` = 看 stat 缓存，
> **不要**误判为内容漂移，**更不要**重新 add+commit。

## 11. §10 Truth Matrix 建议（不实际修改）

**仅建议，未落任何改动**：

1. **旧 `BILI-GRP-UNDERMERGE-01` 若专指涅槃 → `premise refuted`。**
   涅槃的 4→1 是**正确拆分**（`expected_packs = 2`），把它当作 under-merge 缺陷是**前提错误**。
   建议将该条目标注为 `WRONG`（前提不成立），而非继续记为待修缺陷。
2. **新增 broad population undermerge feature**：状态 `based on confirmed ledger`——
   即 feature 覆盖范围应**以本台账的 26 条 gate 为准**（25 上传者 / 80 记录 / 34 包），
   **不含** ambiguous；`DIFFERENT_PACKS` 条目应作为**负样本**（现有 split 正确）。
3. `BILI-GRP-02` 维持 **SUSPECT**：宽口径安全结论仍**不成立**。

## 12. §11 Tests

`tests/test_bilibili_undermerge_adjudication.py` → **26 tests 全过**（`Ran 26 tests`，`OK`）。

覆盖：`ledger no duplicate keys` · `every candidate adjudicated` · `every gate item has evidence` ·
`涅槃 expected_groups = 2` · `no ambiguous in runtime gate` · `deterministic artifacts` ·
`no undeclared adjudication` · `gate contains only CONFIRMED/STRONG` · `ZangHeRo is not confirmed` ·
`named cases were reviewed` · `existing corpora are untouched` · `extractors emit no verdicts` ·
`tracked artifacts are byte reproducible` · `generated_at honours SOURCE_DATE_EPOCH`。

**回归**：既有 4 个 bilibili 套件 `59 tests` 全过（仅既有 `ResourceWarning` 噪声，与本轮无关）。

**复现命令**（本机**未装 pytest**，必须用 unittest）：

```bash
export SOURCE_DATE_EPOCH=1786000000
python -m unittest tests.test_bilibili_undermerge_adjudication -v
```

## 13. 确定性重跑验证

固定 `SOURCE_DATE_EPOCH=1786000000` → `generated_at: 2026-08-06T07:06:40.000Z`，
连续重跑四个脚本，产物 **md5 一致**（`md5sum -c` → `OK / OK`）：

```
4bfc1bd06baa2bd18bbfbcbe3f99d465  bilibili_undermerge_adjudication_v2.json
e64fefc05ea6fd543994ca0cadb29205  confirmed_undermerge_runtime_gate.json
```

**四个脚本全部支持 `SOURCE_DATE_EPOCH`**；测试 harness 的 `subprocess.run` 已
`env.setdefault("SOURCE_DATE_EPOCH", "1786000000")`。

## 14. 工程陷阱（本轮踩过，值得留存）

1. **cluster key 手抄必错**——扫描器**每次运行会重新聚类**（`豆腐ki` 25 组被重聚、
   `一个小寂哦` 两个 entry 合并成 17 组 cluster）。已改为 **slug 化 `{author, signature}`
   运行时解析**，且**解析失败即 `throw`**（silent drop 必须被捕获，否则「少判了一条」
   会被误当成「干净结果」）。
2. **`resolveCase` 三分支**：`signature.includes('::')` 或 `startsWith('__raw_')` → 原样匹配；
   否则 `author + '::' + signature`。
3. **碰撞守卫**：`adjByKey.size !== CASES.length` → throw（两道 case 落到同一 cluster 即报错）。
   实际触发过一次：`一个小寂哦` 的 `::四叶草` 与 `::星辉死神` 重聚类后同 cluster，已去重。
4. **payload 无 `groupKey` 字段**——936 条记录只有 `platform/bvid/title/author/download_links/qq_group`。
   group key 必须**调用真实 runtime** `newMod.groupBilibiliPacks(data)` 派生（实测 `668` 个 key），
   否则描述的是**另一套聚类**。

## 15. git diff --stat / git status

```
$ git show --stat --oneline HEAD
cbbfb58 audit(3g-f.2-b): adjudicate Bilibili under-merge candidates to ground truth
 .../audit/bilibili_undermerge_adjudication_v2.js   |  725 ++++++
 .../audit/bilibili_undermerge_adjudication_v2.json | 2365 ++++++++++++++++++++
 pipeline/audit/build_undermerge_runtime_gate.js    |   90 +
 .../audit/confirmed_undermerge_runtime_gate.json   |  659 ++++++
 pipeline/audit/extract_undermerge_evidence.js      |  171 ++
 pipeline/audit/extract_undermerge_project_identity.js | 165 ++
 tests/test_bilibili_undermerge_adjudication.py     |  337 +++
 7 files changed, 4512 insertions(+)

$ git status --short          # 提交后
（干净）

$ git diff --numstat 2f7ae1e -- pipeline/audit/bilibili_population_adjudication_v2.json \
                                 pipeline/audit/bilibili_population_holdout_v2.json
（无输出 = 逐字节相同）
```

## 16. final commit

`cbbfb588262d06d386dab645deee88e0c4acb7c3`
— 分支 `audit-3gf2b-undermerge`，父提交 `2f7ae1e`（已跨命令块用 `git cat-file -p HEAD` 校验）。

---

## 附：证据文件索引

| 文件 | 内容 |
| --- | --- |
| `pipeline/audit/bilibili_undermerge_adjudication_v2.json` | **主台账**：58 条裁定 + 涅槃教训 + evidence policy + overturns（tracked） |
| `pipeline/audit/confirmed_undermerge_runtime_gate.json` | **runtime gate**：26 条（tracked） |
| `build/audit/bilibili_cross_group_undermerge_v2.json` | §1 冻结的 candidate artifact（模块2 产出） |
| `build/audit/undermerge_evidence_v2.json` | 摊平后的成员标题 / URL / QQ（**无 verdict**） |
| `build/audit/undermerge_project_identity_v2.json` | 每组的注册项目身份 + 共享情况（**无 verdict**） |
| `build/audit/bilibili_grouping_module.js` | esbuild 打包的 runtime grouping 模块（用于派生 group key） |

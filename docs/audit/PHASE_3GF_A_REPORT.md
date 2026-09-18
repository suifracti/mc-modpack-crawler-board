# Phase 3G-F-A — Bilibili Grouping Correctness / Benchmark Finalization

**范围**：grouping algorithm correctness · benchmark · dev/holdout · false merge/split · Truth Matrix
**明确不涉及**：cutover / manifest 性能、production_state、Git slash-ref 修复、Edge profile 基础设施

**结论一句话**：`4bf5e0f` 的 remediation **真实有效且精度未被牺牲**（Recall 0.1250 → 0.7500，
Precision 保持 1.0000，benchmark False Merge 0），并在**真实浏览器运行时**确证生效；
但全量审计在 corpus 之外**新确证 7 例误合并**，故宽口径安全结论**不成立**，
`BILI-GRP-02` 维持 **SUSPECT**；同时发现**反向缺陷**（同一包 `涅槃` 被拆成 5 组）。
新增三项显式标记（`BILI-GRP-PRECISION-POP-01 = WRONG`、
`BILI-GRP-UNDERMERGE-01 = WRONG`、`BILI-GRP-BATCH-01 = SUSPECT`）。

---

## 1. worktree / starting commit

| 项 | 值 |
| --- | --- |
| 起始提交 | `4bf5e0fe4c614f3e630ae242db2ed5b66ef95fea`（`fix(arch-v2): Phase 3G-F - Bilibili grouping false-split remediation (precision preserved)`） |
| 隔离方式 | `git worktree add --detach D:/ai/work/mc-3gf-a 4bf5e0f` → detached HEAD，**独立于主 working tree** |
| 依赖补齐 | `converted_output/`（130M）与 `apps/web/node_modules/`（78M）为 gitignore 资产，已**复制**而非链接，worktree 不共享任何可写状态 |
| data layer 校验 | `converted_output/data` = 2920 文件 / rollup `4c3a05ff06fd3051291543b050c6fa46d678b2a6f494012a97707e7eec534c9a`（与 Production 基线一致） |

## 2. corpus SHA

`pipeline/audit/bilibili_grouping_corpus.json`
→ **`b19b6653040c403aecc20ef04784752e7ab593670421bdf017a9b3d7f9b08577`**

**Ground truth 未漂移证明**：该文件在 3G-E(`5b1ebdd`) 与 3G-F(`4bf5e0f`) 的 git blob 同为
`859225f53b12b1c39bfc3246129aaaf5e10544a3`，`git diff 5b1ebdd 4bf5e0f -- <corpus>` 为空。
`git log` 显示它最后一次被改动就是 3G-E 提交。**未为使新算法好看而修改任何 expected label。**

## 3. old implementation fixture SHA

`pipeline/audit/fixtures/bili_grouping_legacy_impl.js`
→ **`249ebf86bc064875cf05a4c6d9de4e92cbaa88cae37a1b386db842dabf271643`**

冻结 dev/holdout：`pipeline/audit/bilibili_grouping_split.json` → `fd021bf1afc5493a7aa20cb1eb7d9f465ca11e3a16b62950fac9b748b32010fa`

**稳定性验证**：完整流水线（esbuild → extractor → splitter → 两个 evaluator）跑完后，
上述三个 SHA **逐字节不变**，worktree `git status` 干净。
`extract_bili_grouping_impl.py` 正确识别 `4bf5e0f` 为 post-3G-F bundle 并**拒绝覆写 fixture**。

## 4. old metrics（3G-E 旧实现，frozen fixture）

```
TM = 3   FS = 21   TS = 22   FM = 0
Precision = 1.0000   Recall = 0.1250
FalseMergeRate = 0.0000   FalseSplitRate = 0.8750
```

## 5. new metrics（`4bf5e0f` TS domain module）

```
TM = 18   FS = 6   TS = 22   FM = 0
Precision = 1.0000   Recall = 0.7500
FalseMergeRate = 0.0000   FalseSplitRate = 0.2500
```

## 6. Precision before / after

**1.0000 → 1.0000（未牺牲）**。22 个 hard negative 在孤立与全量两种上下文下均 0 误合并。

## 7. Recall before / after

**0.1250 → 0.7500（×6）**。False Split 21 → 6（**15/21 修复**）。

## 8. 21 例旧 false-split 逐条结果

| case | uploader | before | after | expected | fixed? | 原因 / 剩余 split |
| --- | --- | --- | --- | --- | --- | --- |
| POS-SPEC-HORIZON | ConfectionaryQwQ | 6 | 1 | 1 | ✅ | `地平线` |
| POS-URL-04 | AC6_ | 8 | 1 | 1 | ✅ | `云游四海` |
| POS-URL-05 | Verre | 8 | 1 | 1 | ✅ | `神秘启旅` |
| POS-URL-06 | 绘名青棺 | 6 | 1 | 1 | ✅ | `虚饰作品` |
| POS-URL-07 | 缓慢的开始 | 6 | 1 | 1 | ✅ | `soa3` |
| POS-URL-08 | cyq2号机 | 3 | 1 | 1 | ✅ | `foodie` |
| POS-URL-09 | Karashok_Leo | 4 | 2 | 1 | ❌ | 剩余：`咒次元` 恰 3 字，1 期被 `generic_guard` 拦为 `__raw_` |
| POS-URL-10 | 墨言eclipse | 4 | 3 | 1 | ❌ | 剩余：包名 `涅槃` 2 字；2 期靠副标题 run 合并，另 2 期 singleton |
| POS-URL-11 | 林点午安事睡觉 | 4 | 1 | 1 | ✅ | `明日方舟` |
| POS-URL-12 | 非茉涟柠 | 4 | 1 | 1 | ✅ | `hunt history 1949` |
| POS-URL-13 | ALTNOIR | 3 | 1 | 1 | ✅ | `亚特兰深渊` |
| POS-URL-14 | Pork猪排 | 2 | 2 | 1 | ❌ | 剩余：包名 `化龍` 2 字；2 期靠口号 run 合并，第 3 期 singleton |
| POS-URL-15 | 加一点芝士 | 3 | 1 | 1 | ✅ | `剑痕纪元` |
| POS-URL-16 | 啊liu22 | 3 | 1 | 1 | ✅ | `群峦野望` |
| POS-URL-18 | 白银_1223 | 2 | 1 | 1 | ✅ | `血族机械师` |
| POS-URL-19 | 芦苇草的梦想 | 3 | 3 | 1 | ❌ | 剩余：`芦苇` 2 字 + 共享 run `芦苇的 宣传片` 有效 identity 字数 2 < 3 |
| POS-URL-20 | 辣某人 | 3 | 3 | 1 | ❌ | 剩余：`沉浸战斗` 清洗后仅 `沉浸`（2 字），2 期 `generic_guard` |
| POS-URL-21 | 辣某人 | 3 | 3 | 1 | ❌ | 剩余：同上 |
| POS-URL-22 | 666sxss666 | 2 | 1 | 1 | ✅ | `海洋主题` |
| POS-URL-23 | Locknar | 2 | 1 | 1 | ✅ | `mon` |
| POS-URL-24 | P1nero | 2 | 1 | 1 | ✅ | `远梦之棺` |

**new merge reason**：15 例修复全部走 `identity_run`（跨期稳定、非噪声 token run）；
6 例剩余全部是「包名 ≤ 2 字」或「清洗后 ≤ 3 字被泛名守卫截断」，**无一例可通过放宽阈值修复而不牺牲 precision**。

## 9. all new false merges（benchmark 内）

**0 例**。`new_false_merges = []`，`negative_regression = 22/22 separate`。

> **但全量 corpus 之外新确证 7 例**，见 §9b —— 这是本轮最重要的发现。
> （首轮审计报 5 例；因扫描器 `MIN_ANCHOR_INDEX = 2` 存在**已证实的假阴性**，
> 放宽到 1 后逐条人工裁定，数字上调为 **7**，并新发现一类**反向缺陷**，见 §9c。）

### 9b. 全量 population 新确证误合并（corpus 未覆盖）

人工逐条裁定全部 **31 个 flagged 组**后确证 7 例，**全部 `preExisting=false`（3G-F 新引入）**：

| # | 组 key | 条数 | 被误合的包 | anchor 性质 |
| --- | --- | --- | --- | --- |
| 1 | `一个小寂哦::星辉死神` | 4 | 神器收集计划 + 无尽幸运方块大陆 | Boss 名 |
| 2 | `一个小寂哦::四叶草` | 2 | 泰坦生物 + 执行之龙生存 | 道具名 |
| 3 | `一个小寂哦::各大主播同款` | 2 | 幸运方块大全 + 神器泰坦随机合成 | 口号 |
| 4 | `墨言eclipse::颠覆性的` | 2 | 摄影奇境 + 千界万锻 | 形容词 |
| 5 | `原界环::or not` | 2 | Minecraft or Not: Girl&Gun + Maiden or not | 英文片段 |
| 6 | `叙利亚自爆民兵::voxy` | 2 | 《你好，新蒸程》+《你好，新世代》 | **通用模组名** |
| 7 | `tibsalta::难度驱动` | 2 | 《抗争之际0.6》+《旅途痕迹0.5》 | **方括号系列标签** |

**#6 / #7 是首轮漏报、本轮新确认**，并引入两种新根因类别：
- **通用模组名当 anchor**：`voxy` 是渲染模组名，任何用它的包都会共享该 token。
- **方括号系列标签当 anchor**：`【抗争之际0.6】【难度驱动】...` 中真包名在前一个方括号内，
  后一个方括号里的**系列标签**反被选为 anchor（清洗剥掉了括号符号但保留了其中文字）。

**裁定完整性**：31 flagged = **7 REAL + 23 LEGITIMATE + 1 UNDECIDED**，无未裁定项。
过程固化为可复算台账 `pipeline/audit/bilibili_grouping_anchor_adjudication.js`
→ `build/audit/bilibili_grouping_anchor_adjudication.json`，并由 `test_p12` / `test_p13` 强制。

> **⚠️ 该扫描器是审查清单生成器，不是判决器，既过报也漏报**（文档 §23.2 已注明）：
> 过报——anchor 落在真实包名（`勇者之章` / `齿轮与腐肉` / `soa3`）时也会被 flagged；
> 漏报——anchor 落在 key 第 0 个 token 的形态仍无法被发现。
> 因此 **7 例是下界**，不是全量保证。

### 9c. 反向发现：同一个包被拆成 5 组（宽口径误拆分）

核实 `bili_data` 后确认：含 `涅槃` 的 **7 条记录全部来自同一 UP 主 `墨言eclipse`、
且全部是同一个包**（`涅槃` v0.1.5 → v0.2），但算法把它们拆成了 **5 个 groupKey**：

```
墨言eclipse::涅槃 无神明渡我 我亦是神明                          (1)
墨言eclipse::涅槃 神吞降世 邪神投影 万魂幡 超越法则的 镰刀 之旅    (1)
墨言eclipse::大型 禁忌 远古炼金 世界污染 3万行代码深度 涅槃v 0 ... (1)
墨言eclipse::沉浸 深度 a 咒镰双生                                (2)
墨言eclipse::未尽之路涅槃                                        (2)
```

其中 `沉浸 深度 a 咒镰双生` 与 `未尽之路涅槃` **两个组本身合法**（成员确实同包），
只是 anchor 是「坏 anchor」——**不得记为误合并**（已用 `test_p14` 钉死这条边界）。
真正的问题是 **`涅槃`（2 字）被拆散**：短包名先被清洗稀释，再被其它 token 的
identity run 捞走，anchor 落到宣传 tag 或阶段性标题词上，每换一次标题风格就换一个 key。

→ 与 §9b 方向**相反**（欠合并 vs 过合并），两者不能相互抵消，已记为
`BILI-GRP-UNDERMERGE-01 = WRONG`。

**为什么 benchmark 仍报 FM = 0**：22 个 negative 只枚举特定配对。
`一个小寂哦` 确在语料中（NEG-03/04），但覆盖的是 `弑神之路` vs `小行星空岛`；
`墨言eclipse`（NEG-14/15）、`叙利亚自爆民兵`、`tibsalta` 同理。新发现的配对**不在语料内**。

## 10. Horizon 结果

`ConfectionaryQwQ` / `Horizon 地平线` v1.2.0 ~ v2.1.0：
**6 → 1 组**，key = `confectionaryqwq::地平线`，全部 6 期（含 v1.2.0/v1.3.0/v1.5.0/v1.7.0/v2.1.0 与首发）
正确合为同一逻辑包 ✅

## 11. 懂嗎懂嗎 结果

| 组 | before | after | 要求 | 结果 |
| --- | --- | --- | --- | --- |
| Group A（卓越前线） | 3 | **1** | 3 → 1 | ✅ |
| Group B（永无止境） | 3 | **1** | 3 → 1 | ✅ |

**两正确组均未回归。** 新增观察：在全量 population 下 A 与 B 还共同落入
`懂嗎懂嗎::齿轮与腐肉`（8 条）—— 冻结 corpus 未就「A 与 B 是否同包」裁定，故不计入 FM，
但已记入 `BILI-GRP-PRECISION-POP-01` 观察范围。

## 12. 黑金 negative 结果

`NEG-SPEC-HEIJIN`（合成重建，`SYNTH-HEIJIN-1/2`）：**保持分开** ✅
（`merged = false`、`correct = true`、`distinct_keys = 2 = 视频数`）
另注：corpus 明确记载真实 `黑金` 记录**不在当前 936 payload 中**（全字段 0 命中）。

## 13. low-key audit

| token | 记录 | 卡片 | 多视频组 | 判定 |
| --- | --- | --- | --- | --- |
| `沉浸` | 41 | 39 | 2（各 2 条） | 无异常大组 ✅ |
| `生电` | 16 | 12 | 2（`红石生电` 3、`绿色版红石生电优化` 3） | 同包，正确 ✅ |
| `原神` | 8 | 3 | 1（`原神与机械 的时代` 6） | 同包，正确 ✅ |
| `溯渊` | 2 | 2 | 0 | 无合并 ✅ |
| `泰坦` | 40 | 30 | 5 | **含 2 例误合并** ⚠️（`星辉死神`、`四叶草`） |

## 14. large-group audit（size ≥ 5 全列）

**17 个组**（旧实现 4 个），逐组人工核对：`辐射新世纪`(11)、`云游四海`(9)、
`阿卡迪亚的天启`(9)、`神秘启旅`(8)、`齿轮与腐肉`(8)、`辐射次时代`(8)、`虚饰作品`(7)、
`蛊真人 与`(7)、`香草纪元 食旅纪行`(7)、`soa3`(7)、`农夫乐事附属大型`(7)、
`原神与机械 的时代`(6)、`弑神之路`(6)、`农场物语`(6)、`地平线`(6)、
`类幸存者 终末幸存者 last one`(5)、`神之征伐 版本`(5)。

**17/17 均为同一 UP 主的同一整合包系列**，无跨 UP 主组（`cross_uploader_groups = 0`）。
最大组 11 条。**cards 越少 ≠ 越正确**：857 → 668 中既有真实修复，也含 §9b 的误合并。
（注：本轮因放宽 anchor 扫描阈值新增的 7 例误合并中，`tibsalta::难度驱动` 与
`叙利亚自爆民兵::voxy` 都只有 2 条，**不落在 size ≥ 5 区间**，故未被本表覆盖——
这也说明「只看大组」不足以发现全部误合并。）

## 15. download / QQ safety

`groupBilibiliPacks` 入参仅 `(bvid, title, author)`，`download_links` / `qq_group` **从未被读取**
→「同网盘链接即合并」「同 QQ 群即合并」**结构上不可能**。

回归重点 `豆腐ki`（`手机移植版` 共享 URL 簇）：**30 条记录 → 30 张卡片**，未被聚成一组 ✅

> **方法学收获**：本轮先尝试「同组成员 URL 互不相交 ⇒ 不同包」扫描，得 23 个候选，
> **经验证该启发式无效**（按版本发布会新建分享链接，`宝可梦地平线 v1.0→v2.0`、
> `蛊真人 2.1→2.4`、`生还者 1.0→3.1` 全部 URL 不相交却是同一个包）。
> 否决结论与反例已落盘，避免后续复用。

## 16. dev metrics

`uploader-disjoint, deterministic (sha256(uploader) ascending)`，21 个 UP 主 / 18 pos / 10 neg

| | before | after |
| --- | --- | --- |
| Precision | 1.0000 | **1.0000** |
| Recall | 0.1111 | **0.7222** |

## 17. holdout metrics

**holdout 已真实建立**（非伪造）：12 个 UP 主 / **6 positive / 12 negative**，与 dev **无 uploader 交集**。

| | before | after |
| --- | --- | --- |
| Precision | 1.0000 | **1.0000** |
| Recall | 0.1667 | **0.8333** |

**holdout recall ≥ dev recall**（0.8333 > 0.7222）→ **无过拟合迹象**。规则冻结后 holdout 只跑一次。

## 18. 936 population before / after

| 指标 | before | after |
| --- | --- | --- |
| raw videos | 936 | 936 |
| grouped cards | 857 | **668** |
| multi-video groups | 39 | **129** |
| largest group | 9 | 11 |
| size distribution | `{1:818, 2:22, 3-4:13, 5-9:4}` | `{1:539, 2:74, 3-4:38, 5-9:16, 10+:1}` |
| cross-uploader groups | 0 | **0** |

## 19. 机械动力 53 raw / grouped

```
raw = 53（不变量，Flat Mode 必须展示全部原始记录）✅
grouped = 36（过滤批上下文）  /  37（全量 936 上下文）
```

9 个多视频组：`懂嗎懂嗎::真菌感染 模拟`(7)、`zicaiot::农场物语`(3)、`白银_1223::血族机械师`(3)、
`明月庄主::命运齿轮`(3)、`小兜兜呀_::原神与机械 的时代`(2)、`叙利亚自爆民兵::voxy`(2)、
`橘子皮zero::拯救世界重建文明`(2)、`jsi我的世界制作组::create delight`(2)、
`明月庄主::机械动力 月亮工厂`(2)。

**precision 关键证据**：`命运齿轮`(3) 与 `月亮工厂`(2) 仍是**两个独立组**，未被模组名 `机械动力` 吞并。

**真实运行时（非离线 evaluator）**：headless Edge 驱动 production frontend 实测
**Raw 53 / Grouped 36**，`biliGroupsMap = 36` 与渲染卡片数一致，
`window.groupBilibiliPacks` 返回 **plain `Object` 而非 `Map`**（Map 桥接缺陷确已修复），
且 Horizon v1.2.0/v2.1.0 同组。门禁 `smoke_test_wiring.js` **18/18 PASSED**，
新探针 `probe_bili_grouping_runtime.js` **11/11 PASSED**。

## 20. BILI-GRP-02 status

**`SUSPECT`（维持，且证据显著加强；不升 VERIFIED）**

- benchmark 内 FM = 0，全量 22 negative 上下文 0 违规 ✅
- 但本轮**新确证 7 例** corpus 之外的误合并（§9b），全部为 3G-F 新引入
- → 「0 false merge」只在**已枚举的 negative 形态**下成立

## 21. BILI-GRP-03 status

**`SUSPECT`（维持；未强行 VERIFIED）**

- Recall 0.1250 → 0.7500，FS 21 → 6，Precision 1.0000，holdout 无过拟合
- 剩余 6 例根因逐条实测确认：包名 ≤ 2 字，或清洗后 ≤ 3 字被泛名守卫截断
- 修复须放宽守卫 / 降阈值 → 直接牺牲 precision → **按精度优先主动保留**
- 另发现**同族但未被 corpus 覆盖**的新形态 `涅槃`（§9c），记为 `BILI-GRP-UNDERMERGE-01 = WRONG`

## 22. Truth Matrix distribution

总项数 **76**（+3：POP-01 / UNDERMERGE-01 / BATCH-01）：

| 状态 | 数量 | 占比 |
| --- | --- | --- |
| VERIFIED | 47 | 61.8% |
| SUSPECT | **20** | 26.3% |
| WRONG | **2** | 2.6% |
| UNKNOWN | 7 | 9.2% |

8 个 BILI-GRP 条目：
`BILI-GRP-01 = VERIFIED`、`BILI-GRP-02 = SUSPECT`、`BILI-GRP-03 = SUSPECT`、
`BILI-GRP-MERGE-BENCH-01 = VERIFIED`、`BILI-GRP-PRECISION-BENCH-01 = VERIFIED（窄口径）`、
**`BILI-GRP-PRECISION-POP-01 = WRONG`（新增）**、
**`BILI-GRP-UNDERMERGE-01 = WRONG`（新增）**、**`BILI-GRP-BATCH-01 = SUSPECT`（新增）**。

> 窄口径 VERIFIED 与宽口径 WRONG **不矛盾**，两者差额正是 corpus 覆盖不足的量化证据。
> **两个 WRONG 方向相反**（过合并 POP-01 / 欠合并 UNDERMERGE-01），不能相互抵消。
> 同时**撤销**了 `BILI-GRP-02` 原先「已修复并闭环」的表述。

## 23. Tests

```
npm --prefix apps/web run typecheck                     PASS
npm --prefix apps/web test                              80 passed (11 files)
python tests/test_bilibili_grouping_benchmark.py        12 tests OK
python tests/test_bili_grouping_explanation.py          OK
python tests/test_feature_truth_matrix_contract.py      ALL PASSED
python tests/test_bilibili_grouping_precision_audit.py  14 tests OK   (本轮新增)
pipeline/smoke_test_wiring.js (converted_output)        18/18 PASSED
  └ Bilibili Search Wiring & Flat-Mode Raw Invariant - Raw Matches: 53, Grouped Cards: 36
```

两个 evaluator 连跑两次结果**逐字节一致**（除 `generated_at`），可重复性已确认。

> **门禁稳定性说明**：`smoke_test_wiring.js` 首跑出现
> `Preview page failed to initialize mcmodData in time`，同端口重试仍失败；
> 换端口（`converted_output 8921`）干净重跑 **18/18 PASS**。
> 观察：失败时 `tasklist` 中有 33 个 `msedgewebview2.exe` 但 **0 个 `msedge.exe`**，
> 端口只剩 `TIME_WAIT` —— 与 MEMORY 记录的「Edge 未真正启动即卡死」症状一致。
> 直接手动拉起 `msedge.exe --headless=new --remote-debugging-port=9911` 可正常 LISTENING，
> 证明 Edge 本身可用，属**环境/瞬时**问题。该基础设施**不在本轮范围内**，
> 故仅记录现象与可用绕法（换端口重试），未作修改。

## 24. git diff --stat

```
 docs/FEATURE_TRUTH_MATRIX.md                      |  30 ++--
 docs/audit/BILIBILI_GROUPING_AUDIT.md             | 358 ++++++++++++++++++++++
 docs/audit/PHASE_3GF_A_REPORT.md                  |  (本文件)
 tests/test_bilibili_grouping_precision_audit.py   |  14 tests
 2 files changed(跟踪文件中),  ~180 insertions(+), 14 deletions(-)
```

新增文件（7）：
```
pipeline/audit/probe_bili_grouping_runtime.js
pipeline/audit/bilibili_grouping_precision_probe.js
pipeline/audit/bilibili_grouping_precision_audit.js
pipeline/audit/bilibili_grouping_candidate_false_merge_check.js
pipeline/audit/bilibili_grouping_slogan_anchor_scan.js
pipeline/audit/bilibili_grouping_anchor_adjudication.js    ← 本轮新增（可复算裁定台账）
tests/test_bilibili_grouping_precision_audit.py
```

**未修改任何 runtime / 算法文件**（`bilibiliGrouping.ts`、`legacyAdapter.ts`、
`dashboard.legacy.js`、`smoke_test_*.js`、cutover 脚本均**零改动**）。

## 25. git status

```
 M docs/FEATURE_TRUTH_MATRIX.md
 M docs/audit/BILIBILI_GROUPING_AUDIT.md
 M docs/audit/PHASE_3GF_A_REPORT.md
 M pipeline/audit/bilibili_grouping_candidate_false_merge_check.js
 M pipeline/audit/bilibili_grouping_slogan_anchor_scan.js
 M tests/test_bilibili_grouping_precision_audit.py
?? pipeline/audit/bilibili_grouping_anchor_adjudication.js
```

（`pipeline/audit/bilibili_grouping_precision_*.js`、`probe_bili_grouping_runtime.js`
与 `bilibili_grouping_candidate_false_merge_check.js` 已在上一提交落库。）

## 26. final commit

见本文件所在提交（`audit(arch-v2): Phase 3G-F-A ...`），分支 `audit-phase3gf-a-final`。

---

## 附：证据文件索引

| 文件 | 内容 |
| --- | --- |
| `build/audit/bilibili_grouping_remediation.json` | before/after metrics、21 例结果表、剩余 6 例、机械动力、population、低区分度 |
| `build/audit/bilibili_grouping_benchmark.json` | 3G-E 旧实现基准（`53 raw → 47 cards`） |
| `build/audit/bilibili_grouping_runtime_probe.json` | 真实浏览器运行时 11 项桥接证明 |
| `build/audit/bilibili_grouping_precision_probe.json` | 批次依赖性 / 黑金 / 下载·QQ / 低区分度 / 人口 |
| `build/audit/bilibili_grouping_precision_audit.json` | 大组逐条 + 被否决的 URL 启发式 |
| `build/audit/bilibili_grouping_candidate_false_merge_check.json` | **7 例**误合并的独立证据 + 新旧算法对比 |
| `build/audit/bilibili_grouping_slogan_anchor_scan.json` | 口号锚点扫描（**建议性，故意过报且会漏报**，31 flagged） |
| `build/audit/bilibili_grouping_anchor_adjudication.json` | **逐条裁定台账**（31 = 7 REAL + 23 LEGITIMATE + 1 UNDECIDED） |
| `docs/audit/BILIBILI_GROUPING_AUDIT.md` §16–30 | 完整审计叙述 |

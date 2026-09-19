# Bilibili Grouping — False-Merge / False-Split Evidence Audit

> **Phase 3G-E** · base commit `4293851` · audit only, no algorithm change
>
> 本文件回答一个问题：**当前 Bilibili 聚合算法在真实数据上到底会不会误合并 / 误拆分？**
> 结论不依赖 `53 raw → 47 cards` 这一数学不变量 —— 那只能证明算法执行稳定，
> 不能证明这 4 组都应该合并、也不能证明其他本应合并的视频没有被拆开。
>
> 全部结论来自 **独立证据基准**（共享下载资源、互斥的核心包名、phase 指定的人工确认案例），
> **不使用 `cleanPackKey` 作为 ground truth** —— 因为被审计的正是 `cleanPackKey` 是否可信。

---

## 1. Grouping Lineage（真实代码链路）

```
canonical.db
  source_items (id, source_id, title, author, description, icon_url, ...)
  download_links
  source_items.extra  (pack_version / qq_group ...)
        │
        │  pipeline/exporters/legacy/bilibili.py :: BilibiliExporter.export_all()
        ▼
converted_output/data/bili_data.js      →  window.biliModpacksData   (936 records)
        │
        │  apps/web/src/legacy/dashboard.legacy.js:95
        ▼
var biliPacks = window.biliModpacksData || [];
        │
        │  apps/web/src/filters/platformFilters.ts:83  filterBilibiliPacks()
        │  （搜索 / 服务端 / 版本 / loader / 分类 / 网盘 / 日期 过滤）
        ▼
filtered[]
        │
        │  apps/web/src/legacy/dashboard.legacy.js:1515  groupPacks()
        │      ├─ apps/web/src/domain/packName.ts:36   cleanPackKey(title)
        │      └─ apps/web/src/legacy/dashboard.legacy.js:1507  BILI_GENERIC_PACK_KEYS
        ▼
grouped card  (#biliCardsGrid .bili-pack-card)
```

**参与 grouping decision 的字段（实际代码读取的）**

| 字段 | 来源 | 在 grouping 中的作用 |
| :--- | :--- | :--- |
| `author` | `source_items.author`（空 → `未知UP主`） | **作用域前缀**，小写 trim 后作为 key 前缀，跨 UP 主永不合并 |
| `title` | `source_items.title` | 唯一参与 `cleanPackKey` 的字段 |
| `bvid` | `source_items.source_id` | 泛名 / 过短 key 时生成 `__raw_<bvid>` 独立卡片 |
| `pub_timestamp` / `pub_time` | 版本/发布信息 | **仅用于组内选最新标题与封面**，不参与分组判定 |
| `mc_version` / `all_versions` / `loaders` / `categories` | 元信息 | **不参与分组判定**，只在合并后聚合展示 |
| `download_links` | `download_links` 表 | **不参与分组判定**（本轮审计用它做 ground truth 证据） |
| `qq_group` | `source_items.extra` | **不参与分组判定**（同上） |
| `pack_version` | `source_items.extra`（默认 `发布版`） | **不参与分组判定** |
| `desc` / `pinned_comment` / `subtitle_text` | 描述与字幕 | **不参与分组判定**（`subtitle_text` 全量 0 条非空） |

> ⚠️ **`BILI_GENERIC_PACK_KEYS` 在代码中存在两份**：`apps/web/src/domain/packName.ts:9` 的导出常量，
> 与 `apps/web/src/legacy/dashboard.legacy.js:1507` 的本地副本（bundle 中重命名为 `…_KEYS2`）。
> 实测两者内容一致（各 24 项），但**存在漂移风险**：`groupPacks` 用的是本地副本。
> 本轮仅记录，不修改。

---

## 2. `cleanPackKey` 完整定义（逐条规则 + 真实代码出处）

出处：`apps/web/src/domain/packName.ts:36-53`。

| # | 规则 | 正则 / 出处 | 后果 |
| :-- | :--- | :--- | :--- |
| 1 | 删除数学粗体字符 | `/[\uD835][\uDC00-\uDFFF]/g` | 去装饰性字体 |
| 2 | 删除「我的世界 / minecraft / mine craft / mc」 | `/(?:我的世界\|minecraft\|mine\s*craft\|mc)/gi` | 平台名不入 key |
| 3 | 括号 / 斜杠 / 竖线 / 波浪线等 → 空格 | `/[【】[\]（）(){}\u300C\u300D\u300E\u300F《》/\|·~～!！?？:：\-—+*#]+/g` | 分隔符归一 |
| 4 | 删除 Minecraft 版本号 | `/(?:mc\|minecraft\|我的世界)?\s*1\.\d{1,2}(?:\.\d+)?/gi` | `1.20.1` 等不入 key |
| 5 | 删除点分版本号 | `/(?:v\|ver\|version)?\s*\d+(?:\.\d+)+(?:[a-z\d_\-.]*)?/gi` | `v1.2.0` / `4.0.11` 等不入 key |
| 6 | 删除 `v123` 形态 | `/(?:v\|ver\|version)\s*\d+/gi` | 兜底 |
| 7 | 删除 loader 名 | `/\b(?:forge\|fabric\|neoforge\|quilt)\b/gi` | loader 不入 key |
| 8 | 删除包装词 | `/(?:整合包\|模组包\|魔改包\|懒人包\|重制版\|正式版\|抢先版\|公测版\|抢先体验\|测试版)/g` | 泛名剥离 |
| 9 | 删除动作词 | `/(?:最新\|首发\|公测\|更新\|发布\|分享\|下载\|自制\|自创\|开坑\|入坑\|通关\|介绍\|演示\|实况\|推荐)/g` | 动作词剥离 |
| 10 | 删除题材 buzzword | `BILI_GENRE_BUZZWORDS`（`packName.ts:6`，25 个：rpg/冒险/高度定制/史诗战斗/魔法/枪械/科技/生存/剧情/硬核/沉浸式/高难/爽游/原版/魔改/养老/纯净/探索/空岛/地牢/格斗/战斗/拔刀剑/工业/建造/现代战争） | **题材词被整体删除** |
| 11 | 删除固定句式尾巴 | `/(?:新的征途.*\|从此刻开始.*\|第一期.*\|第二期.*\|第\d+期.*\|ep\d+.*)/gi` | 注意：`.*` 会吃掉该词之后**全部**内容 |
| 12 | 非中英数字符 → 空格、trim、小写 | `/[^\u4e00-\u9fa5a-zA-Z0-9]/g` + `.toLowerCase()` | 归一 |
| 13 | 多空格压缩 | `/\s+/g` | 归一 |

### `groupPacks` 决策规则（`dashboard.legacy.js:1515`）

```
rawKey    = cleanPackKey(title)
authorKey = (author || 'unknown').trim().toLowerCase()

规则 1（禁止聚合）
  if (!rawKey || rawKey.length <= 3 || BILI_GENERIC_PACK_KEYS.has(rawKey))
      key = '__raw_' + bvid            # 独立单视频卡片

规则 2（同作者二阶段聚类）
  else:
      在已存在的 key 中找第一个满足下式的 k（前缀必须是 authorKey + '::'）：
          existRaw === rawKey
          || (existRaw.length >= 4 && rawKey.indexOf(existRaw) !== -1)
          || (rawKey.length >= 4 && existRaw.indexOf(rawKey) !== -1)
      key = 命中 ? k : authorKey + '::' + rawKey
```

**关键结构性质**

- 分组是**严格作者作用域内**的：key 以 `authorKey + '::'` 开头，跨 UP 主**结构上不可能**误合并。
- 合并只发生在「key 完全相同」或「一方是另一方子串（且长度 ≥ 4）」两种情况。
- **没有任何版本连续性、下载资源、QQ 群、描述文本的参与**。

---

## 3. Benchmark 方法

### 3.1 为什么不能拿 `cleanPackKey` 当 ground truth

被审计对象就是 `cleanPackKey` 本身。若以「两个视频 key 相同 ⇒ 同包」为真值，
则算法永远 100% 正确，审计没有意义。

### 3.2 独立证据（Evidence Level）

| 等级 | 含义 | 是否计入 P/R |
| :--- | :--- | :--- |
| `CONFIRMED` | phase 指定的人工确认案例 | ✅ |
| `STRONG` | 由**共享具体下载资源**或**互斥核心包名**独立推导 | ✅ |
| `reconstructed` | phase 指定但**不在当前 payload 中**，用其标题重建为合成记录 | ❌ 单独报告 |
| `AMBIGUOUS` | 证据不足，不强迫算法结论 | ❌ 单独保存 |

### 3.3 Positive 判定（expected = merge）

同 UP 主 + **至少 1 个完全相同的具体下载资源 URL**（真实网盘/资源页，排除 landing page）
+ 标题 **包名核心词重合度 ≥ 0.50**（版本号、平台术语已剥离）。

> 单靠共享 URL 不够：存在「一个 UP 主把多个不同整合包放在同一个网盘目录」的情况
> （实测 `豆腐ki` 一条夸克链接覆盖 28 个不同整合包）。因此叠加核心词重合度约束。

### 3.4 Negative 判定（expected = separate）

同 UP 主 + 双方标题**泛用词 ≥ 2 个**（正是算法最易出错的区间）
+ **无共享下载资源** + **版本剥离后的核心包名互斥且互不为子串**。

> 单靠「核心词不重合」不够：`潜行者3.1` vs `潜行者2.0` 是**同一个包的不同版本**，
> 必须先把版本号剥离；且 `潜行者` 与 `潜行者风暴` 需靠「互不为子串」排除。

### 3.5 评估方式

**调用真实实现**：`pipeline/audit/extract_bili_grouping_impl.py` 从生产 bundle
`converted_output/assets/index.js` 中**逐字提取** `cleanPackKey` / `groupPacks` /
`BILI_GENERIC_PACK_KEYS2` / `BILI_GENRE_BUZZWORDS`（bundle 未压缩，函数名保留），
由 `pipeline/audit/bilibili_grouping_benchmark.js` 在 Node 中执行。

**实现保真性验证**：提取出的 `cleanPackKey` 与前端单测
`apps/web/tests/domain.test.ts:19-23` 的 4 条期望**逐条一致**；
且对真实 payload 复现出 `机械动力 53 raw → 47 cards`、4 个多视频组 / 10 个视频 / net −6，
与生产门禁 `smoke_test_wiring.js` 的不变量完全相同。

---

## 4. 结果

### 4.1 四类结果

| 结果 | 数量 | 说明 |
| :--- | ---: | :--- |
| **True Merge** | **3** | 应合并且合并成功 |
| **False Split** | **21** | 应合并却被拆开 |
| **True Separate** | **22** | 应分开且分开成功 |
| **False Merge** | **0** | 不应合并却合并 |

| 指标 | 数值 |
| :--- | ---: |
| Merge Precision | **1.0000** |
| Merge Recall | **0.1250** |
| False Merge Rate | **0.0000** |
| False Split Rate | **0.8750** |

**corpus**：24 positive（93 视频）/ 22 negative / 33 独立 UP 主 / 3 CONFIRMED + 43 STRONG。

### 4.2 结论

- **误合并（False Merge）：在当前 commit 上未观察到。** 22 个 hard negative 全部正确分开，
  包括「同 UP 主 + 同 MC 版本 + 同模板 + 泛用词」的极端情形。
  作者作用域前缀让跨 UP 主误合并结构上不可能；泛名/短 key 守卫让「生存」「整合包」这类
  纯泛用标题退化为独立卡片。
- **误拆分（False Split）：系统性存在。** 24 个应合并的同包系列中 **21 个被拆开**。
  根因：`cleanPackKey` **保留了更新日志尾巴**，导致同包不同期的 key 既不相同也不互为子串。

### 4.3 逐条 False Split 清单

| case | UP 主 | 视频数 | 实际 key 数 | 独立证据 |
| :--- | :--- | ---: | ---: | :--- |
| `POS-SPEC-HORIZON` | ConfectionaryQwQ | 6 | **6** | Horizon 地平线 v1.2.0→v2.1.0，同一 123 云盘资源 |
| `POS-URL-04` | AC6_ | 8 | **8** | 云游四海 V1.1→V1.6.2，同一百度网盘 + 夸克 |
| `POS-URL-05` | Verre | 8 | **8** | 神秘启旅 1.4→1.9，同一百度网盘 + 夸克 |
| `POS-URL-06` | 绘名青棺 | 6 | **6** | 虚饰作品 v0.5→v1.4，同一夸克链接 |
| `POS-URL-07` | 缓慢的开始 | 6 | **6** | SoA3 虚无世界 更新日志#3→#8，同一夸克 + CurseForge + MC百科 |
| `POS-URL-08` | cyq2号机 | 4 | 3 | Foodie 吃货物语 1.2.0/2.0.0/2.0.1 |
| `POS-URL-09` | Karashok_Leo | 4 | **4** | 咒次元 0.6.0→0.8.0（`0.6.0` 一期 key 退化为 `__raw_`） |
| `POS-URL-10` | 墨言eclipse | 4 | **4** | 涅槃 v0.1.5→v0.2 |
| `POS-URL-11` | 林点午安事睡觉 | 4 | **4** | 大群方舟 3.0→4.0 |
| `POS-URL-12` | 非茉涟柠 | 4 | **4** | 猎杀：历史 1949 v1.1.3→v1.2.0 |
| `POS-URL-13` | ALTNOIR | 3 | **3** | 亚特兰深渊 1.0→1.2 |
| `POS-URL-14` | Pork猪排 | 3 | 2 | 化龍 1.0→1.2 |
| `POS-URL-15` | 加一点芝士 | 3 | **3** | 剑痕纪元 0.9.71 等 |
| `POS-URL-16` | 啊liu22 | 3 | **3** | 群峦野望 1.1/1.2/1.3 |
| `POS-URL-18` | 白银_1223 | 3 | 2 | 血族机械师 1.1.0/1.1.2 |
| `POS-URL-19` | 芦苇草的梦想 | 3 | **3** | 芦苇的整合包 4.0.11/4.1.7/4.2.12 |
| `POS-URL-20` | 辣某人 | 3 | **3** | 沉浸战斗 v3.6/4.0/4.2 |
| `POS-URL-21` | 辣某人 | 3 | **3** | 沉浸战斗 1.20.1 系列 |
| `POS-URL-22` | 666sxss666 | 2 | 2 | 1.20.1 海洋主题整合包（测试版两条） |
| `POS-URL-23` | Locknar | 2 | 2 | MON 0.5 / 0.6 |
| `POS-URL-24` | P1nero | 2 | 2 | 远梦之棺 1.5.0 |

**典型根因（`POS-URL-16` 啊liu22 / 群峦野望）**

```
BV1NaFrzkEBN  →  "群峦野望 原始 革新"
BV1XMDFByE5x  →  "群峦野望 沉浸 革新"
BV1eT7H6fETQ  →  "群峦野望 挖矿来 抢油气来"
```

三者共同前缀 `群峦野望`，但规则 2 要求**一方是另一方完整子串**；
三个 key 两两都不是子串关系 → 三张独立卡片。`1.1 / 1.2 / 1.3` 被规则 5 删除，
但**更新日志正文被完整保留**，成为拆分主因。

**对比：为什么 `懂嗎懂嗎` 能正确合并（True Merge 的来源）**

```
BV1Ziuw6ZE7C  →  "大型末日 齿轮与腐肉 机械动力 卓越前线 真菌感染 模拟 日志"
BV1fqNe6rEt5  →  "大型末日 齿轮与腐肉 机械动力 卓越前线 真菌感染 模拟 日志"   (完全相同)
BV1tVeVzDELy  →  "大型末日 齿轮与腐肉 机械动力 卓越前线 真菌感染 模拟"       (前者子串)
```

前两期 key 完全相同、第三期是前者的子串（长度 ≥ 4）→ 规则 2 命中 → 3 → 1。
这是**唯一**能触发合并的两种形态，也是 recall 仅 12.5% 的原因。

### 4.4 False Merge 清单

**空。** 0 例。

### 4.5 phase 指定案例 `黑金`（重建对照）

`黑金` 在当前 936 条 payload 中**完全不存在**（`title` / `author` / `desc` /
`pinned_comment` / `download_links` 全字段搜索命中 0）。

用 phase 给出的两条标题重建为合成记录后跑真实实现：

```
[MC整合包]生存整合包-1.21.1      →  key = __raw_SYNTH-HEIJIN-1
我的世界【生存整合包】生存        →  key = __raw_SYNTH-HEIJIN-2
```

**结果：正确分开。** 两条标题清洗后均为 `生存`（长度 2 ≤ 3），命中规则 1 的泛名守卫，
各自退化为独立卡片 —— 该历史缺陷在当前 commit 上**已不再复现**。
（confidence = `reconstructed`，不计入 precision/recall。）

---

## 5. Key Space 与判别力分析（936 条全量）

### 5.1 Key space

| 指标 | 数值 |
| :--- | ---: |
| raw videos | **936** |
| unique `author::cleanPackKey` groups | **881** |
| multi-video groups | **32** |
| single-video groups | **849** |
| videos inside multi-video groups | 87 |
| net collapse（key 层） | 55 |
| **跨 UP 主 key 碰撞** | **5** |
| 泛用词 key 组数 | 0 |

> `groupPacks` 实际输出 857 组（比 881 更少），因为规则 2 的子串合并会继续把不同 key 归并。

**跨 UP 主 key 碰撞实例**（结构上被作者作用域隔离，不产生误合并）：
`泰坦`、`蛊真人 与`、`泰坦生物 小`、`泰坦生物`、`生电`。

**最高频重复 key**：`辐射新世纪 末世 免费`(9)、`农夫乐事附属大型`(6)、`阿卡迪亚的天启`(4)、
`沉浸`(4)、`辐射次时代 真实末世 免费`(4)、`泰坦`(3)。

### 5.2 Key 判别力

| 指标 | 数值 |
| :--- | ---: |
| 总 key 组 | 881 |
| **低判别力 key**（长度 ≤ 4 或**无任何非泛用词**） | **36（4.1%）** |

key 长度分布：`0`→1 · `1-3`→18 · `4-6`→57 · `7-10`→92 · `11+`→713。

低判别力样例：`''`、`溯渊`、`泰坦`、`休闲`、`重生`、`沉浸`(4 视频)、`懒人`、`生电`、`原神`。

> 这些 key 长度 > 3 且不在 `BILI_GENERIC_PACK_KEYS` 白名单中，因此**会**参与聚合。
> 例如 `沉浸` 已聚合 4 个视频 —— 存在潜在误合并风险，只是本轮 negative corpus 未覆盖到该形态。

### 5.3 Generic 词表（从真实数据统计，非手写）

清洗后 key 的 **distinct token 数 = 2358**。Top 15 高频 token（出现在多少个 key 组中）：

| token | key 组数 | 是否在 `BILI_GENERIC_PACK_KEYS` |
| :--- | ---: | :--- |
| 版本 | 79 | ❌ |
| 正式 | 48 | ❌ |
| 与 | 46 | ❌ |
| v | 33 | ❌ |
| 手机移植版 | 27 | ❌ |
| 免费 | 26 | ❌ |
| fcl启动器移植 | 23 | ❌ |
| 机械动力 | 22 | ❌（实为模组名，有判别力） |
| 内容 | 20 | ❌ |
| amp | 18 | ❌ |
| 优化 | 18 | ❌ |
| 日志 | 17 | ❌ |
| 一键自动安装 | 16 | ❌ |
| 休闲 | 15 | ❌ |
| 在 | 15 | ❌ |

**发现**：当前泛名守卫只覆盖 24 个精确匹配的整 key 词（`BILI_GENERIC_PACK_KEYS`）
与题材 buzzword（`BILI_GENRE_BUZZWORDS`）。而真实数据里高频的
`版本` / `正式` / `与` / `v` / `内容` / `优化` / `日志` / `amp` / `在` 等 token
**既不在泛名白名单，也不在题材 buzzword 中**，会被保留进 key。
这既是 **false split 的成因**（更新日志词残留），也是**潜在的 false merge 风险**
（若两个不同包的 key 恰好只剩这类词）。本轮仅记录，不修改。

### 5.4 Version signal 审计

| 问题 | 数值 |
| :--- | ---: |
| 标题含点分版本号的视频 | 432 |
| 版本号**被完全删除**出 key | 501 |
| key 中残留**孤立数字**（版本残渣） | 77 |
| 版本号**保留**在 key 中 | **0** |

**结论**：版本号**从不参与** grouping。
- 对「同包版本更新」：版本被删除本身是**好事**（否则每期都不同 key）；
  真正导致拆分的是**版本号之外的更新日志正文**被保留。
- 对「不同包恰好同 MC 版本」：因 `mc_version` 不参与 grouping，不存在混淆。
  实测同 UP 主下同一 `mc_version` 可对应大量不同包
  （`1.20.1` → 198 个不同 key 组；`1.21.1` → 56；`1.16.5` → 36），
  算法并未因此误合并。

### 5.5 Download identity（仅用于审计 ground truth）

| 指标 | 数值 |
| :--- | ---: |
| 含下载链接的视频 | 667 |
| distinct URL | 1038 |
| 被 ≥ 2 个视频共享的 URL | 182 |
| 其中**具体资源** URL（排除 landing page） | **173** |
| 最大簇 | `pan.quark.cn/s/c5c78492b6ab` → **28 视频**（`豆腐ki`，跨多个不同整合包） |

**证据强度**：具体资源 URL 是**强证据但非充分**。
`豆腐ki` 一条夸克链接承载 28 个不同整合包，证明「同 URL ⇒ 同包」不成立；
必须叠加核心包名重合度。本轮**未**将其加入 grouping 算法。

### 5.6 QQ 群 identity（仅用于审计）

| 指标 | 数值 |
| :--- | ---: |
| 含 QQ 群的视频 | 242 |
| distinct QQ 群 | 140 |
| 覆盖 ≥ 2 个视频的群 | 39 |
| **跨 ≥ 2 个 UP 主的群** | **3** |
| 最大簇 | `240052014` → 22 视频 / **2 个 UP 主** |

**证据强度**：**弱到中等**。同一 UP 主的多个不同整合包可能共用同一个群
（`298929369` → 11 视频 / 1 UP 主），且存在跨 UP 主共用。
**不能**单独作为 identity。本轮未加入算法。

---

## 6. `机械动力 53 → 47` 逐组映射（§23）

| 组 key | UP 主 | 视频 | 卡片 | net | 判定 |
| :--- | :--- | ---: | ---: | ---: | :--- |
| `懂嗎懂嗎::大型末日 齿轮与腐肉 机械动力 卓越前线 真菌感染 模拟 日志` | 懂嗎懂嗎 | 3 | 1 | −2 | **correct merge**（= phase Group A） |
| `懂嗎懂嗎::大型末日 齿轮与腐肉 机械动力 永无止境 真菌感染 模拟 前瞻` | 懂嗎懂嗎 | 3 | 1 | −2 | **correct merge**（= phase Group B） |
| `zicaiot::在 中还原星露谷 农场物语` | ZiCaiOT | 2 | 1 | −1 | **correct merge**（农场物语 1.4.1 / 1.2.0） |
| `白银_1223::血族机械师 版本 机械动力 吸血鬼 轻量 任务书` | 白银_1223 | 2 | 1 | −1 | **correct merge**（血族机械师 1.1.2 / 1.1.0） |

```
10 videos → 4 cards → net −6        53 − 6 = 47  ✔
```

**这 4 组全部是 correct merge，没有 ambiguous。**
但同一次查询里 **`白银_1223` 的血族机械师 1.1.0 之前那一期（无版本号）落在另一个 key**，
即该包在 53 结果内实际只合并了 2/3 期 —— 53→47 的「正确」并不代表该包被完整合并。

### Flat Mode 不变量（§24）

Flat Mode 仍展示 **53 条 raw 记录**（`flat_mode_raw_records = 53`），
本轮未改动 runtime，raw identity 未被聚合审计破坏。

---

## 7. 复现方式

```bash
# 1) 从生产 bundle 逐字提取真实 grouping 实现
python pipeline/audit/extract_bili_grouping_impl.py

# 2) 用独立证据构建 benchmark corpus
python pipeline/audit/build_bili_grouping_corpus.py

# 3) 调用真实实现逐案评估 + 全量分析
node pipeline/audit/bilibili_grouping_benchmark.js

# 4) 契约测试
python tests/test_bilibili_grouping_benchmark.py
```

产物：

- `pipeline/audit/bilibili_grouping_corpus.json`（ground truth，受版本控制）
- `build/audit/bilibili_grouping_impl.js`（提取出的生产实现）
- `build/audit/bilibili_grouping_benchmark.json`（逐案 expected vs actual）
- `build/audit/bilibili_grouping_analysis.json`（全量 key / 判别力 / 泛用词 / 版本 / 资源统计）

---

## 8. 未做的事（本轮为纯审计）

**未**新增泛用词、**未**改 min key length、**未**改 `cleanPackKey` 正则、
**未**引入 download URL identity、**未**引入 QQ identity、**未**引入版本连续性、
**未**改 group key、**未**改 UI、**未**改 `canonical.db`、**未**新增 Migration。

---

# Phase 3G-F — False-Split Remediation（同文件续）

> base commit `5b1ebdd` · **本阶段修改了 grouping 实现**（3G-E 为纯审计）

## 9. 冻结与防过拟合

| 项 | 值 |
| :--- | :--- |
| 冻结 corpus SHA-256 | `b19b6653040c403aecc20ef04784752e7ab593670421bdf017a9b3d7f9b08577` |
| 冻结 benchmark SHA-256 | `39d89710e1ab23274ce64e5a6b07afa6436db3b7e1f60f9c841ecd5f9bbc312c` |
| 切分方式 | **uploader-disjoint**，确定性（`sha256(uploader)` 升序），非人工挑选 |
| dev | 21 UP 主 / 18 positive + 10 negative |
| holdout | 12 UP 主 / 6 positive + 12 negative |
| 固定进 dev | `懂嗎懂嗎`、`ConfectionaryQwQ`（phase 已给定真值，属「不可回归」而非盲测） |

## 10. 新算法（两级 identity / episode 模型）

单一来源：**`apps/web/src/domain/bilibiliGrouping.ts`**（纯函数 `groupBilibiliPacks`）。
`dashboard.legacy.js::groupPacks` 降级为**纯聚合器**，只消费预计算的 group key；
重复的本地 `BILI_GENERIC_PACK_KEYS` 副本已删除，由 `legacyAdapter.ts` 经 window 桥接。

```
cleanPackKey(title) → tokens
  ├─ 泛名守卫（不变）：空 / 长度 ≤ 3 / 属泛名白名单 → __raw_<bvid>
  └─ 同作者作用域内挖掘 identity anchor：
       任意相邻 token run，出现于 ≥ 2 条视频
       且 identityChars(run) ≥ 3
       且 run 含 ≥ 1 个「非噪声」token
     ↓
     每条记录取「覆盖视频数最多」的 anchor（并列比 specificity，再比字典序）
     ↓
     groupKey = authorKey::anchor
```

**噪声 token（不可锚定 identity，但仍保留在 key 中）**

- 渠道/平台术语：`手机移植版` `移植版` `启动器` `fcl启动器移植` `一键自动导入` …
- 更新/日志措辞：`版本` `正式` `更新` `发布` `前瞻` `日志` `内容` `优化` `支持` `添加` `免费` …
- 题材/规模描述词：`末世` `末日` `大型` `史诗` `沉浸` `硬核` `生存` `冒险` `科技` …
- **模组名**：`机械动力` `农夫乐事` `虚无世界` `匠魂` `等价交换` …
- **源游戏名**：`地下城` `死亡细胞`

**噪声按子串剥离**：中文描述词会连写（`大型`+`末世` → 一个 token `大型末世`），
故 `identityCharsOfToken()` 逐个剥离子串后再计长；纯描述词 token 计 0 → 不可锚定，
而真名里含噪声词者（`齿轮与腐肉` → `齿轮腐肉`）仍保留判别力。

**token 归一化**：含 CJK 的 token 去掉 ASCII 字母数字后缀（`虚饰作品v` ≡ `虚饰作品`，
`命运齿轮fom` ≡ `命运齿轮`）；纯拉丁 token（`mon`、`soa3`）保持原样。

**为什么不用 union-find**：传递闭包会把不同包串成一个大组
（实测出现 14 成员组混入 `弑神之路`/`神器收集计划`/`无尽幸运方块大陆`，
以及 6 成员组混入 `命运齿轮`/`月亮工厂`）。改为**直接取最优 anchor**，杜绝链式合并。

**download URL / QQ 群：本轮未参与算法**（仅作审计证据），满足「不得单独决定 merge」。

## 11. 结果

| 指标 | before | after |
| :--- | ---: | ---: |
| True Merge | 3 | **18** |
| False Split | 21 | **6** |
| True Separate | 22 | **22** |
| False Merge | **0** | **0** |
| Precision | 1.0000 | **1.0000** |
| Recall | 0.1250 | **0.7500** |

| 切分 | Recall | Precision |
| :--- | ---: | ---: |
| dev | 0.7222 | 1.0000 |
| holdout | **0.8333** | 1.0000 |

holdout 不低于 dev → **无过拟合迹象**。21 个旧 false split 中 **15 个已修复**。

**全量 936 条**：857 → 668 组；`机械动力 53 raw` → **36 组**（原 47）。
大 group（≥ 5）由 21 → **17**，逐个人工核对**全部为同一整合包系列**。

## 12. 剩余 6 例 false split（主动保留）

| case | UP 主 | 根因 |
| :--- | :--- | :--- |
| `POS-URL-09` | Karashok_Leo | 包名 `咒次元` 恰 3 字，被泛名守卫（`length <= 3`）截断 |
| `POS-URL-10` | 墨言eclipse | 包名 `涅槃` 仅 2 字，低于 identity 阈值 |
| `POS-URL-14` | Pork猪排 | 包名 `化龍` 仅 2 字 |
| `POS-URL-19` | 芦苇草的梦想 | 包名即频道名 `芦苇`，仅 2 字 |
| `POS-URL-20/21` | 辣某人 | 包名 `沉浸战斗` 完全由题材词构成 → 清洗后仅剩 `沉浸`，被守卫正确拦下 |

修复它们必须放宽泛名守卫或降低 identity 阈值 —— 会直接牺牲 precision。
按「**宁可保留少量 split，也不要引入已知 false merge**」原则**主动保留**。

## 13. 审计中发现并修复的两类真实误合并（corpus 未覆盖）

1. **模组名锚定**：`机械动力` 覆盖 5 条视频 → `命运齿轮` 与 `月亮工厂` 被并入一张卡片。
   → 加入模组名噪声表。
2. **源游戏名锚定**：`地下城` 覆盖 5 条视频 → `幻想的地下城` 与 `史诗的地下城` 合并。
   两者百度网盘链接**不同**（`1VIbbLScc1Na4p__OARuqe` vs `1ADiGWC44mCoRD32_QQpt2`），
   确证为不同整合包。→ 加入源游戏名噪声表。

这两例说明：**「0 false merge」只在已枚举的 negative 形态下成立**，
故 `BILI-GRP-02` 维持 **SUSPECT**，另以窄口径 `BILI-GRP-PRECISION-BENCH-01 = VERIFIED` 记录。

## 14. 实现缺陷（已修复）

`legacyAdapter` 初版直接把返回 `Map` 的 `groupBilibiliPacks` 挂到 window，
而 `dashboard.legacy.js` 以对象下标访问（`decisions[bvid]`）→ 恒为 `undefined`
→ **静默退化为「仅精确同 key 合并」**，浏览器实测 grouped cards = 48（应 36）。
已在 bridge 中改为返回以 bvid 为键的普通对象；并在 wiring 门禁中新增
`0 < groupedCards < rawMatches` 断言 —— 该断言正是能捕获此类「分组被静默禁用」的探针。

## 15. Flat Mode

`53 raw` 是**唯一不变量**并已固化为门禁断言；`47 grouped` **不再是 Golden**。
`smoke_test_wiring.js`、`tests/test_bili_grouping_explanation.py` 均已同步改写。

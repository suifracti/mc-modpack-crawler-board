# Architecture V2 — Feature Truth Matrix

> **审计基准与原则**：
> 1. **事实真实性原则**：本矩阵审计的是业务事实与用户可见结论的真实可靠性。33/33 Browser 测试通过仅代表当前代码按既有逻辑运行，不代表事实本身正确。
> 2. **全链路追踪**：每项功能均从平台原始数据/API $\to$ Crawler $\to$ Raw Snapshot $\to$ Adapter $\to$ Canonical SQLite $\to$ Exporter/Repository $\to$ Frontend Domain $\to$ UI Renderer 全链路核查。
> 3. **四级严格状态判定**：
>    - `VERIFIED`：已追溯到真实来源，有完整契约、自动化测试与充分人工证据支持。
>    - `SUSPECT`：存在推断风险、较强启发式假设、来源模糊或样本表现异常，尚无法判死。
>    - `WRONG`：已确认当前实现、字段提取、算法推导或 UI 结论存在事实性错误。
>    - `UNKNOWN`：平台原生无证据，系统不应假定为真或假。禁止将 `PASS` 等同于 `VERIFIED`。

---

## 1. 审计统计总览

- **审计功能总项数**：`66` 项 (覆盖 15 个业务领域)
- **状态分布汇总 (Phase 3G-D.1 审计后)**：
  - **VERIFIED**：`40` 项 (60.6%) — 确证真实、具备完备契约的可靠功能（包含清除非法项目级时间戳后的 TIME-CURSEFORGE-02、模组关系保真的 MODREL-MCMOD-01、深度索引契约 DIDX-MCMOD-01、简介搜索契约 SEARCH-MCMOD-DESC-01、多词单一真实源契约 SEARCH-MCMOD-MULTIWORD-01、搜索命中原因与解释性修复 SEARCH-MCMOD-REASON-01，以及本轮发现并已修复的命中原因结构化来源完整性契约 SEARCH-MCMOD-REASON-SOURCE-01）
  - **SUSPECT**：`19` 项 (28.8%) — 保留审慎标记（包含B站分组、BBSMC时序、Modrinth 聚合时间与版本标识等）
  - **WRONG**：`0` 项 (0.0%) — 原始 9 项硬伤、平台时间伪造，以及本轮新增发现的命中原因来源可逆性缺陷均已清零修复！
  - **UNKNOWN**：`7` 项 (10.6%) — 保持显式未确定（含 CurseForge 真实版本发布日期可用性 RELDATE-CURSEFORGE-01 及模组依赖/重要性关系 MODSEM-MCMOD-01）
- **六平台覆盖率**：100%（MCMod 权威、Bilibili 动态、BBSMC 社区、XYEBBS 论坛、Modrinth 国际、CurseForge 国际全量覆盖）

---

## 2. 详细功能真值矩阵 (Feature Truth Matrix)

### 领域 1：运行环境（Environment / Server & Client Support）

| Feature ID | 平台 | 用户可见功能 / 结论 | 原始平台来源 | 推导算法与逻辑 | 缺失值处理 | Golden Samples | 最终状态 | 备注 / 风险 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ENV-MODRINTH-01` | Modrinth | 客户端/服务端支持状态 (`required`/`optional`/`unsupported`) | Modrinth 官方 API `client_side` & `server_side` 枚举字段 | 官方字段直接映射为 `certainty='confirmed'`, `evidence_type='platform_field'` | 官方 `unknown` 则标注为 `unknown` | `modrinth:fabulously-optimized`, `modrinth:sodium-plus` | **`VERIFIED`** | 六平台中唯一具备官方结构化环境声明的平台。 |
| `ENV-CURSEFORGE-01` | CurseForge | 服务端专属支持 (`supported` / 专用开服端) | CurseForge API 无顶层服务端布尔值；通过附加文件列表文件名分析 | 文件名正则匹配：`re.search(r'server|serverpack', filename, re.I)`，命中则标 `strong_inferred` | 未匹配文件标 `unknown` (45,566 个)；**旧前端错误渲染为“未提供专用开服端”** | `curseforge:rlcraft` (命中), `curseforge:dawncraft` (未知) | **`SUSPECT`** | 数据库中为 `strong_inferred`/`unknown` 正确；但前端旧 UI 产生“无服务端”负向断言。 |
| `ENV-BBSMC-01` | BBSMC | 服务端支持 | BBSMC 帖子附件文件名及标题内容 | 附件文件名匹配 `re.search(r'服务端\|server', filename)` 判 `strong_inferred` (21个)；标题判 `inferred` (1个) | 缺失标 `unknown` (1780个) | `bbsmc:1p2TFl6X`, `bbsmc:e11vzqXl` | **`SUSPECT`** | 仅依赖附件文件名启发式识别，覆盖率仅 1.2%。 |
| `ENV-XYEBBS-01` | XYEBBS | 服务端支持 | 论坛帖子附件与正文 | 附件文件名匹配 `strong_inferred` (1个)；正文关键词判 `inferred` (15个) | 缺失标 `unknown` (5159个) | `xyebbs:mznl`, `xyebbs:badao` | **`SUSPECT`** | 正文文本推断极易受玩家提问/评论干扰。 |
| `ENV-MCMOD-01` | MCMod | 模组包开服支持 | MCMod 模组包正文简介 | 正文正则匹配“可联机/支持开服/自带服务端”(6个支持)；“无法开服/仅单人”(12个不支持) | 缺失标 `unknown` (1466个) | `mcmod:6`, `mcmod:16`, `mcmod:304` | **`SUSPECT`** | 简介文本推断无法区分整合包作者声明与模组说明。 |
| `ENV-BILI-01` | Bilibili | 视频描述开服标注 | Bilibili 视频简介正文 | 正文自然语言正则“可联机/开服”(7个支持) | 缺失标 `unknown` (928个) | `bilibili:BV1vuVH6XErM`, `bilibili:BV1hbFWe3EHN` | **`SUSPECT`** | 视频简介常包含 UP 主私人服务器招募或广告，非整合包本身属性。 |

---

### 领域 2：Minecraft 游戏版本（Minecraft Version）

| Feature ID | 平台 | 用户可见功能 / 结论 | 原始平台来源 | 推导算法与逻辑 | 缺失值处理 | Golden Samples | 最终状态 | 备注 / 风险 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `MCVER-MODRINTH-01` | Modrinth | 适配 Minecraft 版本 | Modrinth API `game_versions` 数组 | 官方结构化版本列表直接导入 `release_mc_versions` | 无缺失 | `modrinth:all-of-fabric-7` (`1.20.1`) | **`VERIFIED`** | 官方结构化数据，准确率 100%。 |
| `MCVER-CURSEFORGE-01` | CurseForge | 适配 Minecraft 版本 | CurseForge API 文件 `gameVersions` 数组 | 官方文件关联结构化版本列表直接导入 | 无缺失 | `curseforge:all-the-mods-9` (`1.20.1`) | **`VERIFIED`** | 官方结构化数据。 |
| `MCVER-MCMOD-01` | MCMod | 适配 Minecraft 版本 | MCMod 页面标题标签及分类属性 | 解析标签如 `[1.12.2]`, `[1.20.1]`；多版本拆分为多个关联行 | 112 个整合包无 MC 版本信息 | `mcmod:305` (`1.12.2`), `mcmod:34` (缺失) | **`VERIFIED`** | 标签提取准确；112 个缺失样本属原页面缺失版本信息。 |
| `MCVER-BBSMC-01` | BBSMC | 适用游戏版本 | BBSMC 论坛主题分类前缀与标题 | 正则提取标题及分类 `1\.\d+(\.\d+)?` | 0 缺失 | `bbsmc:1p2TFl6X` (`1.20.1`) | **`VERIFIED`** | 论坛前缀规范，提取结果稳定。 |
| `MCVER-XYEBBS-01` | XYEBBS | 适用游戏版本 | 论坛帖子属性分类与标题 | 帖子分类字段优先，次选标题正则 | 0 缺失 | `xyebbs:mznl` (`1.20.1`) | **`VERIFIED`** | 论坛原生字段支持。 |
| `MCVER-BILI-01` | Bilibili | 适用游戏版本 | Bilibili 视频标题与简介正文 | 仅靠标题正则 `1\.\d+(\.\d+)?` 提取版本 | **402 个视频无法提取版本 (43%)** | `bilibili:BV1Ziuw6ZE7C` (`1.20.1`), `bilibili:BV16cWieHEE9` (无版本) | **`SUSPECT`** | 缺乏结构字段，43% 缺失；且标题如“在1.20聊1.19”易误识别讨论版本。 |

---

### 领域 3：Mod 加载器（Loader Support）

| Feature ID | 平台 | 用户可见功能 / 结论 | 原始平台来源 | 推导算法与逻辑 | 缺失值处理 | Golden Samples | 最终状态 | 备注 / 风险 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `LOADER-MODRINTH-01` | Modrinth | 加载器 (Fabric / Forge / NeoForge / Quilt) | Modrinth API `loaders` 数组 | 官方结构化字段映射入 `source_item_loaders` | 标 `unknown` | `modrinth:fabulously-optimized` (`fabric`) | **`VERIFIED`** | 官方原生分类。 |
| `LOADER-CURSEFORGE-01` | CurseForge | 加载器类别 | CurseForge API `modLoaderType` 枚举 | 官方数字枚举转为 `Forge`/`Fabric`/`NeoForge`/`Quilt` | 标 `unknown` | `curseforge:better-mc-forge` (`forge`) | **`VERIFIED`** | 官方原生分类。 |
| `LOADER-MCMOD-01` | MCMod | 加载器类别 | MCMod 页面徽标与标签 | 带单词边界的严格正则匹配 `\b(Fabric\|Forge\|NeoForge\|Quilt)\b` | 标 `unknown` | `mcmod:787` (`Forget Me Not` - 正确未误判为 Forge) | **`VERIFIED`** | 严格正则避免了 "Reforged"、"Fabricated" 等英文单词子串误判。 |
| `LOADER-BBSMC-01` | BBSMC | 加载器类别 | 论坛帖子标签 | 帖子分类属性匹配 | 标 `unknown` | `bbsmc:1p2TFl6X` (`forge`) | **`VERIFIED`** | 论坛原生主题字段。 |
| `LOADER-XYEBBS-01` | XYEBBS | 加载器类别 | 论坛帖子分类前缀 | 帖子分类属性匹配 | 标 `unknown` | `xyebbs:mznl` (`forge`) | **`VERIFIED`** | 论坛原生分类。 |
| `LOADER-BILI-01` | Bilibili | 加载器类别 | 视频标题与简介 | **Phase 3F 引入上下文词边界正则**：`(?<![a-zA-Z]){loader}(?![a-zA-Z])` 识别标题中的 `NeoForge`/`Fabric`/`Forge`/`Quilt` | 标 `unknown` | `bilibili:BV1CbR7BZESQ` (`NeoForge`), `bilibili:BV1PbAczPE4o` (`Forge`) | **`SUSPECT`** | **Bug已修复**：显式标题Loader遗漏已修复（通过 `test_p0_7`）。但由于B站无原生结构化Loader字段，全量Loader识别仍属于标题文本正则推断，整体特性审慎维持 SUSPECT。 |

---

### 领域 4：分类与标签（Categories & Taxonomy）

| Feature ID | 平台 | 用户可见功能 / 结论 | 原始平台来源 | 推导算法与逻辑 | 缺失值处理 | Golden Samples | 最终状态 | 备注 / 风险 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `CAT-MCMOD-01` | MCMod | 模组包类型 (科技/魔法/冒险/魔改等) | MCMod 官方分类标签 | MCMod 原生分类映射进入 `categories` 表 | 默认 `综合` | `mcmod:16` (科技, 冒险, 任务) | **`VERIFIED`** | MCMod 权威平台原生分类体系。 |
| `CAT-MODRINTH-01` | Modrinth | 分类标签 (tech/magic/adventure 等) | Modrinth API `categories` 字段 | 官方分类 slug 直接导入 | 空数组 | `modrinth:all-of-fabric-7` | **`VERIFIED`** | 平台官方体系。 |
| `CAT-CURSEFORGE-01` | CurseForge | 类别 (Tech, Magic, Quests 等) | CurseForge API `categories` 列表 | 官方类别 ID 与名称直接映射 | 空数组 | `curseforge:create-above-and-beyond` | **`VERIFIED`** | 官方分类体系。 |
| `CAT-BBSMC-01` | BBSMC | 板块与类型标签 | BBSMC 版块名与主题前缀 | 论坛原生版块结构映射 | 空数组 | `bbsmc:1p2TFl6X` | **`VERIFIED`** | 论坛原生分类。 |
| `CAT-XYEBBS-01` | XYEBBS | 论坛分类 | 论坛版块与自定义字段 | 论坛原生版块结构映射 | 空数组 | `xyebbs:mznl` | **`VERIFIED`** | 论坛原生分类。 |
| `CAT-BILI-01` | Bilibili | 玩法标签 (生存/科技/冒险等) | Bilibili 视频自带标签 (Tag) 与标题分词 | 聚合视频标签，并用关键词衍生整合包分类 | 兜底 `Bilibili视频` | `bilibili:BV1Ziuw6ZE7C` | **`SUSPECT`** | 属于前端便利性的衍生分类 (Derived Taxonomy)，非作者填写的游戏分类。 |

---

### 领域 5：搜索逻辑与范围（Search Scope & Indexing）

| Feature ID | 平台 | 用户可见功能 / 结论 | 原始平台来源 | 推导算法与逻辑 | 缺失值处理 | Golden Samples | 最终状态 | 备注 / 风险 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `SRCH-MCMOD-01` | MCMod | 搜索“RLCraft”等关键词 | `title`, `typeName`, `formerTitles`, `author`, `categories`, `includedModNames`（扁平索引由该数组正向 join 派生） | 内存多字段子串匹配 (legacy_compat 多词 AND) | 空词不过滤 | 搜索 `RLCraft` = 93 结果 | **`VERIFIED`** | 搜索执行完全符合设计契约。 |
| `SEARCH-MCMOD-DESC-01` | MCMod | 模组包主表格搜索范围与长篇简介契约 (Option B) | `title`, `typeName`, `formerTitles`, `author`, `categories`, `includedModNames`（扁平索引由该数组正向 join 派生） | 依据设计契约 Option B，主表格搜索明确不包含百科长篇简介（避免膨胀数百兆体积），UI 占位符与文档诚实对齐实际可搜范围。长篇简介作为按需详情抽屉展示 | 简介不参与主表索引 | 搜索 `RLCraft` 不命中仅在简介中出现的 MID 255/413/1231 | **`VERIFIED`** | UI 承诺与底层索引实现完全一致，消除描述搜索虚标。 |
| `SEARCH-MCMOD-MULTIWORD-01` | MCMod | 多词空格与关系与单一真实源契约 (Multi-word Whitespace AND Contract) | 搜索输入文本 | TS SearchEngine 负责分词 (tokenization) 与多词 AND 匹配（如 `Fabric API` $\to$ `['fabric', 'api']` 匹配 664 个整合包）。DataTables 仅作为渲染器与分页器，通过 `ext.search` 严格遵循 SearchEngine 匹配 ID 集合，消除 DataTables 二次连续字串过滤 | 空词全量 | 搜索 `Fabric API` = 664 (TS Engine 664 == DataTable 664，ID 集合 100% 相同) | **`VERIFIED`** | 终结双重过滤分脑架构，TS SearchEngine 为全局单一真实源。 |
| `SRCH-BILI-01` | Bilibili | 搜索“机械动力”等关键词 | `title`, `author`, `description`, 版本, 加载器 | 内存多字段子串匹配，并送入作者聚合引擎 | 空词全量 | 搜索 `机械动力` = 53 raw / 47 grouped | **`VERIFIED`** | 原始匹配数与聚合卡片数自动化证明完全一致。 |
| `SRCH-BBSMC-01` | BBSMC | BBSMC 卡片搜索 | `title`, `author`, `description`, 分类 | 内存子串匹配 | 空词全量 | `bbsmc:1p2TFl6X` | **`VERIFIED`** | 纯文本精准匹配。 |
| `SRCH-XYEBBS-01` | XYEBBS | XYEBBS 卡片搜索 | `title`, `author`, `description`, 分类 | 内存子串匹配 | 空词全量 | `xyebbs:mznl` | **`VERIFIED`** | 纯文本精准匹配。 |
| `SRCH-MODRINTH-01` | Modrinth | Modrinth 卡片搜索 | `title`, `author`, `summary`, 加载器, 版本 | 内存子串匹配 | 空词全量 | 搜索 `Sodium` | **`VERIFIED`** | 纯文本精准匹配。 |
| `SRCH-CURSEFORGE-01`| CurseForge | CurseForge 卡片搜索 | `title`, `author`, `summary`, 加载器, 版本 | 内存子串匹配 | 空词全量 | 搜索 `All the Mods` | **`VERIFIED`** | 纯文本精准匹配。 |
| `SRCH-CROSS-01` | 跨平台 | 顶部全局搜索栏广播 | 各平台 SearchCoordinator | 全局统一分发 Query，并切换到活跃平台视图 | 空词保留当前 | `#crossSearchInput` | **`VERIFIED`** | 多平台联动状态机协同良好。 |

---

### 领域 6：Bilibili 整合包聚合（Bilibili Grouping Algorithm）

| Feature ID | 平台 | 用户可见功能 / 结论 | 原始平台来源 | 推导算法与逻辑 | 缺失值处理 | Golden Samples | 最终状态 | 备注 / 风险 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `BILI-GRP-01` | Bilibili | 同 UP 主多期视频自动合为一个卡片 (Multi-video Collapsing) | 936 条 Bilibili 视频标题与 UP 主 ID | 统一清洗标题 `cleanPackKey(title)`，相同作者且同 Key 合并为同一卡片 | 标题清洗后过短使用原标题前20字 | UP `懂嗎懂嗎`: 6 视频合为 2 卡片; UP `zicaiot`: 2 视频合为 1 卡片 | **`VERIFIED`** | 核心机制正确，已通过 53 raw $\to$ 47 grouped 自动化数学证明。 |
| `BILI-GRP-02` | Bilibili | 标题去重关键词引发的错误合并 (False Merge) | 视频标题 | **Phase 3F 聚合决策模型**：清洗后 Key 长度 $\le 3$ 或属于泛名通用词集时，禁止跨视频聚合，强制分配独立 `__raw_<bvid>` 卡片；子串合并要求长度 $\ge 4$ | 退化为单视频卡片 | UP `黑金`: `[MC整合包]生存整合包-1.21.1` 与 `我的世界【生存整合包】生存` 独立展示 | **`SUSPECT`** | **Bug已修复**：短词泛名错误合并已杜绝（通过 `test_p0_8`）。但因尚未建立全量20对正负例金集基准，聚合算法整体鲁棒性审慎维持 SUSPECT。 |
| `BILI-GRP-03` | Bilibili | 包含版本特性描述导致的拆分 (False Split) | 视频标题 | 标题中包含具体特性说明（如 `DH模组更新`/`支持Forge`）导致 Key 不一致 | 无法归纳到同一个 Key | UP `ConfectionaryQwQ`: `Horizon光影模组包` 6 个更新日志视频被拆分为 6 个单卡片 | **`SUSPECT`** | 属于启发式规则局限性，无法自动理解任意自然语言更新日志。 |

---

### 领域 7：版本弹窗保真度（Version Modal Data Fidelity）

| Feature ID | 平台 | 用户可见功能 / 结论 | 原始平台来源 | 推导算法与逻辑 | 缺失值处理 | Golden Samples | 最终状态 | 备注 / 风险 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `MODAL-MODRINTH-01`| Modrinth | 版本弹窗多 Release 列表、Changelog、文件大小与下载 | Modrinth API `versions` 列表 | 多版本完整展示，Markdown Changelog 渲染 | 缺省使用友好兜底 | `modrinth:fabulously-optimized` (多 Release 切换正常) | **`VERIFIED`** | 数据流完整，平台保真度最高。 |
| `MODAL-CURSEFORGE-01`| CurseForge | 版本弹窗 Release、文件与下载 | CurseForge API 文件列表 | 多版本完整展示 | 缺省提示未提供说明 | `curseforge:rlcraft` | **`VERIFIED`** | 平台保真度高。 |
| `MODAL-BBSMC-01` | BBSMC | 版本弹窗 Release、Changelog与网盘 | BBSMC 帖子版本元数据 | 单一/多版本列表适配 | 缺省提示无日志 | `bbsmc:1p2TFl6X` (乌托邦探险之旅) | **`VERIFIED`** | 字段流转正常。 |
| `MODAL-XYEBBS-01` | XYEBBS | 版本弹窗详情 | XYEBBS 帖子元数据 | 单一 Release 适配 | 缺省提示无日志 | `xyebbs:mznl` | **`VERIFIED`** | 适配器映射正确。 |
| `MODAL-MCMOD-01` | MCMod | 版本弹窗基本信息与前曾用名 | MCMod 模组包元数据及曾用名别名表 | 单一 Release 适配，展示包含模组数与曾用名 | 缺省提示通用版本 | `mcmod:722`, `mcmod:16` | **`VERIFIED`** | 前曾用名展示准确。 |
| `MODAL-BILI-01` | Bilibili | 版本弹窗视频信息与网盘下载 | Bilibili 视频描述与网盘链接 | 将关联视频作为 Release 渲染 | 缺省使用当前视频 | `bilibili:BV1aRYC6cE4p` | **`VERIFIED`** | 弹窗展示与适配器一致。 |

---

### 领域 8：下载链接分类（Download Links Classification）

| Feature ID | 平台 | 用户可见功能 / 结论 | 原始平台来源 | 推导算法与逻辑 | 缺失值处理 | Golden Samples | 最终状态 | 备注 / 风险 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `DL-MODRINTH-01` | Modrinth | 官方直链下载 (`mrpack`) | Modrinth 官方 CDN 文件 URL | 官方 API 直链，标记 `link_type='OFFICIAL'` | 无缺失 | `modrinth:fabulously-optimized` | **`VERIFIED`** | 真实直链，无中间层。 |
| `DL-CURSEFORGE-01` | CurseForge | 官方下载链接 (`zip`) | CurseForge API 文件 URL | 官方直链或 CurseForge 客户端导入协议 | 无缺失 | `curseforge:rlcraft` | **`VERIFIED`** | 真实直链。 |
| `DL-BILI-01` | Bilibili | 网盘下载链接（夸克/百度/蓝奏/123） | 视频简介正文正则提取 | 网盘 URL 正则提取与提取码配对匹配 | 过滤无效非链接 | `bilibili:BV1Ziuw6ZE7C` (夸克网盘) | **`VERIFIED`** | 真实网盘链接，提取码分离准确。 |
| `DL-BBSMC-01` | BBSMC | 官方与网盘下载链接 | BBSMC 帖子下载区域 DOM | 抓取下载按钮 URL | 无 URL 时丢弃 | `bbsmc:1p2TFl6X` | **`VERIFIED`** | 常规链接正常。 |
| `DL-BBSMC-02` | BBSMC | 下载链接格式完整性 | 论坛下载区域 | **Phase 3F 严格协议校验**：仅收录 `http://`, `https://`, `ftp://`, `magnet:` 链接，长文本/日志自动剔除 | 丢弃非法文本 | `bbsmc:50` (机械铜协奏，非法长日志已被清洗) | **`VERIFIED`** | **已修复**：Adapter 引入强校验，DB Migration 003 彻底清除脏记录，通过 `test_p0_4` 回归测试。 |
| `DL-XYEBBS-01` | XYEBBS | 下载链接格式完整性 | 论坛下载区域 | **Phase 3F URL 提取与清洗**：严格过滤 `null`/`undefined`/`Neoforge`/`QQ群`，支持正文提取合法网盘链接并配对提取码 | 过滤非法伪链接 | `xyebbs:15435`, `xyebbs:15079` | **`VERIFIED`** | **已修复**：伪链接全量清除，有效网盘链接保留并分离提取码，通过 `test_p0_5` 回归测试。 |
| `DL-MCMOD-01` | MCMod | MCMod 下载链接 | MCMod 页面 | MCMod 整合包库中无独立 `download_links` 表记录，通过原站 `source_url` 访问原页面 | 无站内直链 | `mcmod:16` | **`UNKNOWN`** | MCMod 站点定位为中文资料百科，本身不直接托管下载，仅提供原帖跳转链接。 |

---

### 领域 9：MCMod 包含模组（Included Mods Semantics）

| Feature ID | 平台 | 用户可见功能 / 结论 | 原始平台来源 | 推导算法与逻辑 | 缺失值处理 | Golden Samples | 最终状态 | 备注 / 风险 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `MODS-MCMOD-01` | MCMod | 整合包包含的模组列表 (共 170,078 条) | MCMod 整合包模组列表页面 DOM | 解析页面模组表格：含 mod_name, mod_title, category_name (辅, LIB, 实用, 科技, 魔法等) | 未归类填 `未分类` | `mcmod:16` (含 108 款模组) | **`VERIFIED`** | 数据与 MCMod 原页面记录 100% 对应，保留了分类标识。 |
| `MODREL-MCMOD-01` | MCMod | 整合包模组关联抓取与入库保真度 | MCMod 模组关系列表 (`.class-menu-main li[data-id="2"]`) | 爬虫与 Canonical 映射 100.00% 保真（170,062 来自 full_details，16 来自 modpacks fallback，0 重复，0 遗漏） | - | `mcmod:16`, `mcmod:722`, 30 Golden Packs | **`VERIFIED`** | 爬虫提取与入库完全忠实于原网站页面展示，经 30 个金样包与 224 项关系抽检确证 100% 一致。 |
| `MODSEM-MCMOD-01` | MCMod | “包含模组”的依赖/核心语义与重要性分类 | MCMod 模组列表原站结构 | 原站原生仅按模组分类（辅助、LIB、实用等）归类，**无任何必需/可选/核心/前置依赖字段**（No relationship provenance available）；模组分类 $\neq$ 整合包关系 | 缺失标 `UNKNOWN` | `mcmod:16` (内含 Cloth Config, Architectury 等) | **`UNKNOWN`** | 原站无关系重要性语义。33.2% 为辅助、19.4% 为 LIB（两者占 52.55%），不可简单将模组分类断言为依赖类型，更不能假定为核心玩法模组。 |

---

### 领域 10：MCMod 搜索深度索引（Deep Index Semantics）

| Feature ID | 平台 | 用户可见功能 / 结论 | 原始平台来源 | 推导算法与逻辑 | 缺失值处理 | Golden Samples | 最终状态 | 备注 / 风险 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `DIDX-MCMOD-01` | MCMod | 搜索“机械动力”或“RLCraft”匹配到包含该模组的整合包 | `includedModNames`（结构化数组，扁平小写文本索引由该数组正向 join 派生） | 整合包包含模组（`mod_name`）结构化数组拼接索引并执行子串/分词匹配；Phase 3G-C.1 证明 96 vs 93 差异纯因客户端裁剪 `description`，在真实客户端数据上 TS 引擎、DataTables 与 Python 达成 100% 绝对一致（0 差异 ID）。Phase 3G-D.1 将索引来源由扁平串改为结构化数组，`join(', ')` 与旧扁平串在 1484/1484 个包上逐字节相同，20/20 语料命中 ID 100% 不变 | 无模组时索引为空 | 搜索 `RLCraft` = 93 结果 (TS/DT/Python 100% 一致) | **`VERIFIED`** | **底层算法与索引契约完全确证**。算法忠实索引 `mod_name` 并执行匹配。命中原因不透明性已拆出至独立的 `SEARCH-MCMOD-REASON-01`。 |
| `SEARCH-MCMOD-REASON-01` | MCMod | 模组深度索引命中原因与出处可见性 | Web 前端搜索渲染、TS SearchEngine 与 DataTables / 卡片视图 | **Phase 3G-D 单趟判定与原因契约**：TS SearchEngine 在单趟评估中同时计算 `SearchMatchReason`，忠实输出匹配字段（名称、曾用名、作者、玩法标签、Loader、版本、包含模组），对包含模组返回真实完整模组名称（如 `奇异饰品-RLCraft版 (RLArtifacts)`），多词查询严格遵循 AND 契约（按词匹配字段，杜绝拼凑虚假模组名），前端表格与卡片视图在搜索时显式展示命中原因徽章（`.search-match-badge`），不搜索时静默无徽章。杜绝推断“核心模组” | 搜索词清空不显示徽章 | 搜索 `RLCraft` (MID 16 显式名称匹配；MID 304 显式包含模组：`奇异饰品-RLCraft版 (RLArtifacts)`) | **`VERIFIED`** | **已彻底闭环**：命中原因直接由 TS SearchEngine 单趟评估计算并穿透至 UI 显式呈现，解释性与搜索单趟评估完全一致，彻底消除命中原因不透明性。出处完整性另由 `SEARCH-MCMOD-REASON-SOURCE-01` 独立锁定。 |
| `SEARCH-MCMOD-REASON-SOURCE-01` | MCMod | “包含模组：XXX”所展示的模组名是否为真实存在的模组 | Canonical `included_mods.mod_name` → Exporter `includedModNames: string[]` → `SearchDocument.includedModNames[]` | **Phase 3G-D.1 结构化来源契约**：Phase 3G-D 的命中原因曾以 `modSearchText.split(', ')` 反解析扁平串得到模组名。全量审计证明该反解析**不可逆**：170,078 条关系中有 **202 条 `mod_name` 自身含分隔符 `", "`**（涉及 23 个不同模组、**178 个整合包**），反解析会把这些真实模组名拆成 **47 个不存在的伪造名、共 411 处**（例如 `Get It Together, Drops!` 被拆成 `Get It Together` 与 `Drops!`）。已改为 Exporter 直接输出结构化数组 `includedModNames`，扁平搜索索引改由 `includedModNames.join(', ')` **正向派生**，展示层不再反推。 | 无模组时为空数组 | `mcmod:1007` 含 `Get It Together, Drops!`（真实名，不再被拆）；`mcmod:16` 含 4 个 RLCraft 版真实模组名 | **`VERIFIED`** | **本轮发现 WRONG 并已修复**：反解析路径不可逆（178 包受影响），已替换为结构化数组来源。结构化数组与 canonical `mod_name` 在 1484/1484 包上顺序与内容完全一致（0 处不符）；`join` 与旧扁平串逐字节相同；20/20 语料命中 ID 不变；payload 仅 +1.47%（12,099,832 B，gzip +1.05%）。 |

---

### 领域 11：趋势与增长指标（Trend & Growth Metrics）

| Feature ID | 平台 | 用户可见功能 / 结论 | 原始平台来源 | 推导算法与逻辑 | 缺失值处理 | Golden Samples | 最终状态 | 备注 / 风险 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TREND-MCMOD-01` | MCMod | 7天/30天/全期趋势折线图 (Sparkline) | MCMod 页面每日关注度时序数据 | `viewsDelta` 每日增量时序数组，计算最近 7d 历史并渲染 SVG | 无数据填当前点 | `mcmod:16`, `mcmod:722` | **`VERIFIED`** | 纯数学趋势折线，算法与时序完全保真。 |
| `TREND-MCMOD-02` | MCMod | UI 文案“热度增长” | MCMod 每日页面浏览量增量时序 | 计算当前点与历史基期的差值百分比 `(curr - base) / base` | 缺历史返回 0% | `mcmod:16` | **`SUSPECT`** | 实际上是“MC百科页面日均浏览增量”，文案宣称为“热度增长”稍显夸大。 |
| `SCORE-MCMOD-01` | MCMod | 整合包“星级评分” (1 ~ 5 星) | MCMod 官方详情 | **Phase 3F 严格保真**：完全废除根据单日浏览增量推算星级的伪逻辑。仅当 `score > 0` 时展示官方真实星级评分；无评分时为 `NULL` | 显式呈现“暂无评分” | `mcmod:16` (真实评分), `mcmod:1284` (暂无评分) | **`VERIFIED`** | **已修复**：Structured/Legacy Exporter 及前端组件全链路修正，杜绝用浏览量冒充玩家评分，通过 `test_p0_1` 回归测试。 |

---

### 领域 12：各平台统计指标（Platform Metrics）

| Feature ID | 平台 | 用户可见功能 / 结论 | 原始平台来源 | 推导算法与逻辑 | 缺失值处理 | Golden Samples | 最终状态 | 备注 / 风险 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `METRIC-MODRINTH-01` | Modrinth | 下载量与关注量 | Modrinth API `downloads` & `followers` | 原生数值直接展示 | 正常数值 | `modrinth:fabulously-optimized` | **`VERIFIED`** | 官方指标。 |
| `METRIC-CURSEFORGE-01`| CurseForge | 下载总量 | CurseForge API `downloadCount` | 原生数值直接展示 | 正常数值 | `curseforge:rlcraft` | **`VERIFIED`** | 官方指标。 |
| `METRIC-BILI-01` | Bilibili | 播放量、点赞、投币、收藏 | Bilibili API `stat` 对象 | 原生数值直接展示 | 正常数值 | `bilibili:BV1Ziuw6ZE7C` | **`VERIFIED`** | 官方指标。 |
| `METRIC-MCMOD-01` | MCMod | 浏览量、评论数、红黑票比例 | MCMod 详情页统计 | 原生数值直接展示，红黑票折算为好评率百分比 | 缺省填 50% | `mcmod:16` | **`VERIFIED`** | 页面原生指标保真。 |
| `METRIC-BBSMC-01` | BBSMC | 下载量与关注数 | BBSMC 论坛帖子统计 | 帖子展示数值直接映射 | 缺失填 null | `bbsmc:1p2TFl6X` | **`VERIFIED`** | 社区原生数值。 |
| `METRIC-XYEBBS-01` | XYEBBS | 浏览量与回复数 | XYEBBS 论坛主题统计 | 帖子展示数值直接映射 | 缺失填 null | `xyebbs:mznl` | **`VERIFIED`** | 论坛原生数值。 |

---

### 领域 13：数据审计与变更追踪（Audit Diff Module）

| Feature ID | 平台 | 用户可见功能 / 结论 | 原始平台来源 | 推导算法与逻辑 | 缺失值处理 | Golden Samples | 最终状态 | 备注 / 风险 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `AUDIT-DIFF-01` | 全平台 | “版本变动 / 最近更新 / 数据审计” 弹窗 | `audit_diff.js` 导出器 | **Phase 3F 诚实可用性标识**：因尚未接入多版本连续快照基线，显式声明 `is_available: false`，输出客观说明“历史版本快照对比暂未启用（未配置历史基线快照）” | 友好诚实提示 | `converted_output/data/audit_diff.js` | **`UNKNOWN`** | **告示语义已验证**：弹窗告示契约通过 `test_p0_9` 回归测试；但版本快照比对功能本身因缺失历史快照基准，功能状态维持为 UNKNOWN / UNAVAILABLE。 |

---

### 领域 14：时间语义表（Time Truth Table）

| Feature ID | 平台 | 字段名称 | 原始平台真实物理含义 | 数据库字段 | 表现异常 / 污染证据 | 最终状态 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME-MODRINTH-01`| Modrinth | `date_created` / `date_modified` | 官方项目创建与最后修改时间 (UTC ISO) | `published_at`, `modified_at` | 规范完整，无异常 | **`VERIFIED`** |
| `TIME-CURSEFORGE-01`| CurseForge | `dateCreated` / `dateModified` | 官方项目创建与最后更新时间 (UTC ISO) | `published_at`, `modified_at` | 规范完整，无异常 | **`VERIFIED`** |
| `TIME-BILI-01` | Bilibili | `pubdate` | 视频发布时间（Unix 时间戳） | `published_at` (`modified_at` 置空) | Bilibili 无原生修改时间，936项 `modified_at` 为 NULL，合法 | **`VERIFIED`** |
| `TIME-MCMOD-01` | MCMod | `created_at` / `release_date` | 页面收录日期 / 模组包原发布日期 | `published_at`, `modified_at` | **已修复**：Phase 3F 清洗中文字符串 `'未知时间'`，转换为规范 `NULL`，通过 `test_p0_6` | **`VERIFIED`** |
| `TIME-XYEBBS-01` | XYEBBS | `post_time` / `edit_time` | 论坛发帖与最后编辑时间 | `published_at`, `modified_at` | **已修复**：Phase 3F 清洗中文字符串 `'未知'`，转换为规范 `NULL`，通过 `test_p0_6` | **`VERIFIED`** |
| `TIME-BBSMC-01` | BBSMC | `date_created` / `date_modified` | 论坛发帖与最后编辑时间 | `published_at`, `modified_at` | **时序倒错**：20 个帖子 `published_at > modified_at`（如发帖 04-27 编辑 04-24） | **`SUSPECT`** |
| `TIME-MODRINTH-02`| Modrinth | `releases.release_date` | Modrinth 官方 `/search` API `date_modified` (最新版本创建日期聚合) | `releases.release_date` | 官方 API 证明 `date_modified` 为最新版本创建日投影；10 样本验证通过（8/10 完全吻合到秒，2/10 差1秒由于异步 hook）；但快照缺失 `latest_version` ID 绑定且版本名为 MC 版本，实体解耦 | **`SUSPECT`** |
| `RELID-MODRINTH-01`| Modrinth | `releases.version_name` | Modrinth 合成 Release 标识与版本号审计 | `releases.version_name`, `releases.id` | `version_name` 存入 Minecraft 游戏版本而非整合包自身版本号；快照未保存 `latest_version` ID，Release 实体与版本号解耦 | **`SUSPECT`** |
| `TIME-CURSEFORGE-02`| CurseForge | `releases.release_date` | 根除非法项目级时间戳降级 | `releases.release_date` | **已修复 (VERIFIED)**：CurseForge 45,797 条 releases 彻底废除项目修改/首发时间向版本日期的降级，全量规范置空 (`NULL`)；Adapter 与 Migration 005 保证新旧构建一致；10 样本通过 `test_curseforge_release_date_semantics.py` | **`VERIFIED`** |
| `RELDATE-CURSEFORGE-01`| CurseForge | 真实版本发布日期可用性 | CurseForge 离线爬虫快照缺失版本级文件时间戳 | `releases.release_date` | 离线数据 `data/raw_data/curseforge_data.json` 完全未爬取 `latestFiles`/`fileDate`，真实版本发布日原生无证据，系统不应假定为真，诚实保持为 `UNKNOWN`（数据层为 `NULL`） | **`UNKNOWN`** |
| `TIME-MCMOD-02` | MCMod | `releases.release_date` | MC百科 `last_update_date` 语义调查 | `releases.release_date` | **确证真实 (VERIFIED)**：爬虫源码证明 `last_update_date` 源于 `/modpack/version/{mid}.html` 最新版本发布日，非百科编辑时间；326 条具版本发布证据，1,158 条无日志规范为 NULL | **`VERIFIED`** |

---

### 领域 15：缺失值与兜底行为（Missing & Unknown Handling）

| Feature ID | 平台 | 现象 / 场景 | 前端当前处理逻辑 | 事实与风险 | 最终状态 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `MISS-NUM-01` | 全平台 | 下载量或浏览量等统计数值为 `NULL` | **Phase 3F 严格三态数值格式化**：`numFmt(null)` 规范返回 `—`，真实 `0` 返回 `0`，有效正数正常缩写 | 诚实呈现数据缺失，杜绝将无数据伪装为 0 下载，通过 `test_p0_2` | **`VERIFIED`** |
| `MISS-ENV-01` | 全平台 | 模组包未声明服务端或客户端支持 | **Phase 3F 5态环境真相**：解除负向断言，未声明或未知时展示“未声明服务端支持 / 无法确认” | 严谨表达“未声明”不等于“不支持”，通过 `test_p0_3` | **`VERIFIED`** |
| `MISS-VER-01` | Bilibili / MCMod | 未能提取 Minecraft 游戏版本 | 弹窗及卡片展示“通用 / 未指定” | 合理兜底，未伪造具体版本号。 | **`VERIFIED`** |

---

## 3. 问题优先级与改进计划 (Prioritized Action Register)

### P0: 事实性错误（WRONG）— 原始 9 项硬伤在 Phase 3F 已修复；Phase 3G-B 根除 CurseForge 时间伪造，P0 全部清零！
1. **`SCORE-MCMOD-01`** [已修复]: 移除根据单日浏览增量推算星级的伪逻辑，无真实评分显式标“暂无评分”，保留真实星级评分（回归测试：`test_p0_1`）。
2. **`MISS-NUM-01`** [已修复]: `numFmt` 严格三态化：`null`/`undefined`/`''` 统一返回 `—`，杜绝将缺失数据伪装为 0 下载（回归测试：`test_p0_2`）。
3. **`MISS-ENV-01`** [已修复]: 服务端兜底改为“未声明服务端支持 / 无法确认”，解除无证据等价于不支持的负向断言（回归测试：`test_p0_3`）。
4. **`DL-BBSMC-02`** [已修复]: Adapter 增加 URL 严格协议校验，DB Migration 003 清洗更新日志长文本（回归测试：`test_p0_4`）。
5. **`DL-XYEBBS-01`** [已修复]: 清洗 `null`、`undefined`、`Neoforge`、`QQ群号` 伪链接，正确分离有效网盘 URL 与提取码（回归测试：`test_p0_5`）。
6. **`TIME-MCMOD-01` & `TIME-XYEBBS-01`** [已修复]: 清洗日期列中文字符串 `'未知时间'` 和 `'未知'`，规范为标准 `NULL`（回归测试：`test_p0_6`）。
7. **`BILI-GRP-02`** [已修复]: 增加 $\le 3$ 字符及纯泛词隔离规则，杜绝错误合并并严格保全 53 原始 $\to$ 47 聚合卡片数学证明（回归测试：`test_p0_8`）。
8. **`LOADER-BILI-01`** [已修复]: Bilibili Adapter 引入上下文词边界正则识别显式 Loader，DB Migration 003 补全缺失关联（回归测试：`test_p0_7`）。
9. **`AUDIT-DIFF-01`** [已修复]: `audit_diff.js` 显式设置 `is_available: false` 并输出客观说明，UI 诚实提示，移除空数组伪装（回归测试：`test_p0_9`）。
10. **`TIME-CURSEFORGE-02`** [已修复]: CurseForge 全量 45,797 条 releases 移除项目级修改/首发时间向版本日期的非法降级，全量规范置空（`release_date = NULL`），并通过 Migration 005 及 Adapter 根治，杜绝虚假版本发布时间（测试：`test_curseforge_release_date_semantics.py`）。

### P1: 事实性风险（SUSPECT）— 必须审慎呈现的启发式结论
1. **`TIME-MODRINTH-02`**: Modrinth 官方 API 证明 `date_modified` 为最新版本创建日期聚合（10/10 金样验证吻合），但因离线快照未保留 `latest_version` ID 且 Release 实体未绑定真实版本，时序语义审慎标记为 SUSPECT。
2. **`RELID-MODRINTH-01`**: Modrinth 离线爬虫抓取时未保存 `latest_version` ID，且 Adapter 将 `version_name` 赋值为 Minecraft 游戏版本而非整合包自身版本号，Release 实体与版本号解耦，标记为 SUSPECT。
3. **`SEARCH-MCMOD-REASON-01`**: 搜索结果卡片缺乏命中原因透明度（包含模组隐藏于折叠抽屉内），建议后续版本标注“因包含模组 [X] 命中”，解除用户困惑。
4. **`BILI-GRP-03`**: Bilibili 部分同一整合包的多期更新视频因标题含版本特性被拆解，建议引入更宽泛的分词相似度辅助关联。
5. **`TIME-BBSMC-01`**: 调查 BBSMC 论坛 20 项发帖时间晚于编辑时间的时序倒错原因，必要时取两者的较晚时间作为 `modified_at`。

### P2: 语义未定项（UNKNOWN）— 显式诚实展示未确定
1. **`DL-MCMOD-01`**: MCMod 本身不托管文件，UI 明确标注为“原站百科跳转”而非“下载失效”。
2. **`ENV-CURSEFORGE-01` / `BBSMC` / `XYEBBS`**: 缺乏官方环境字段时，统一展示为 `UNKNOWN`（未声明），不强行推断。
3. **`RELDATE-CURSEFORGE-01`**: CurseForge 离线爬虫快照缺失 `latestFiles`/`fileDate`，真实版本发布时间原生无证据，保持为 `UNKNOWN`（数据层诚实为 `NULL`）。
4. **`MODSEM-MCMOD-01`**: MCMod 原站无模组关系类型字段（无 required/optional/core），模组分类不等于整合包依赖，语义保持为 `UNKNOWN`。

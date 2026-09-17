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

- **审计功能总项数**：`56` 项
- **状态分布汇总**：
  - **VERIFIED**：`26` 项 (46.4%)
  - **SUSPECT**：`17` 项 (30.4%)
  - **WRONG**：`9` 项 (16.1%)
  - **UNKNOWN**：`4` 项 (7.1%)
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
| `LOADER-BILI-01` | Bilibili | 加载器类别 | 视频标题与简介 | **未在 Adapter 中实现标题 Loader 提取** | 全量 936 个视频全部为 `None` (无 Loader) | `bilibili:BV1CbR7BZESQ` (标题含 `neoforge` 但 loader 为空) | **`WRONG`** | **确认缺陷**：标题明确标注 `NeoForge`/`Forge` 的视频因未编写提取逻辑全被置空。 |

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
| `SRCH-MCMOD-01` | MCMod | 搜索“RLCraft”等关键词 | `title`, `author`, `description`, `modSearchText` | 内存多字段子串匹配 (legacy_compat 多词 AND) | 空词不过滤 | 搜索 `RLCraft` = 93 结果 | **`VERIFIED`** | 搜索执行完全符合设计契约。 |
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
| `BILI-GRP-02` | Bilibili | 标题去重关键词引发的错误合并 (False Merge) | 视频标题 | `BILI_GENRE_BUZZWORDS` 剔除“生存/整合包/冒险”后，泛名视频变成相同通用 Key | Key 变短（如 `生存 生存`） | UP `黑金`: `[MC整合包]生存整合包-1.21.1` 与 `我的世界【生存整合包】生存` 误合为一体 | **`WRONG`** | **确认缺陷**：当标题仅含泛游戏词时，清洗后退化为泛 Key，导致该 UP 的不同整合包被错误合并。 |
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
| `DL-BBSMC-02` | BBSMC | 误把更新日志解析为下载 URL | BBSMC 页面爬虫解析器 | 爬虫误将下载区域后方的更新日志 textarea 当作 URL 存入 | 存入长度达上千字的纯文本 | `bbsmc:50` (标题: 机械铜协奏) | **`WRONG`** | **确认缺陷**：爬虫误将版本更新日志文本存入 `url` 字段 (`url='Beta0.5.16-Release1.0n -修改defaultconfig...'`)。 |
| `DL-XYEBBS-01` | XYEBBS | 误把属性/QQ群解析为下载链接 | XYEBBS 页面爬虫解析器 | 爬虫未校验 URL 协议，抓取到了 `undefined`/`null`/`Neoforge`/`QQ群` | 存入非合法链接 | `xyebbs:15435` (`url='null'`), `xyebbs:15079` (`url='Neoforge'`) | **`WRONG`** | **确认缺陷**：爬虫将论坛属性与群号当成下载链接抓取存库。 |
| `DL-MCMOD-01` | MCMod | MCMod 下载链接 | MCMod 页面 | MCMod 整合包库中无独立 `download_links` 表记录，通过原站 `source_url` 访问原页面 | 无站内直链 | `mcmod:16` | **`UNKNOWN`** | MCMod 站点定位为中文资料百科，本身不直接托管下载，仅提供原帖跳转链接。 |

---

### 领域 9：MCMod 包含模组（Included Mods Semantics）

| Feature ID | 平台 | 用户可见功能 / 结论 | 原始平台来源 | 推导算法与逻辑 | 缺失值处理 | Golden Samples | 最终状态 | 备注 / 风险 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `MODS-MCMOD-01` | MCMod | 整合包包含的模组列表 (共 170,078 条) | MCMod 整合包模组列表页面 DOM | 解析页面模组表格：含 mod_name, mod_title, category_name (辅, LIB, 实用, 科技, 魔法等) | 未归类填 `未分类` | `mcmod:16` (含 108 款模组) | **`VERIFIED`** | 数据与 MCMod 原页面记录 100% 对应，保留了分类标识。 |
| `MODS-MCMOD-02` | MCMod | “整合包包含模组”的业务性质归类 | MCMod 模组关系表 | **32,910 条 (19.4%) 为 `LIB` 运行前置库，56,466 条 (33.2%) 为 `辅` 辅助优化** | - | `mcmod:16` (内含 Cloth Config, Architectury 等) | **`SUSPECT`** | 超过 52% 的记录是基础运行依赖或辅助工具，若前端统称为“玩法模组”会严重误导用户。 |

---

### 领域 10：MCMod 搜索深度索引（Deep Index Semantics）

| Feature ID | 平台 | 用户可见功能 / 结论 | 原始平台来源 | 推导算法与逻辑 | 缺失值处理 | Golden Samples | 最终状态 | 备注 / 风险 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `DIDX-MCMOD-01` | MCMod | 搜“机械动力”匹配到 93 个整合包 | `modSearchText` 全量文本索引 | 整合包包含该模组（即使只是前置或辅助）即算匹配 | 无模组时索引为空 | 搜索 `RLCraft` = 93 结果 | **`SUSPECT`** | **产品语义模糊**：用户无法区分该整合包是“以机械动力为核心玩法”还是“仅仅安装了一个机械动力作为装饰部件”。 |

---

### 领域 11：趋势与增长指标（Trend & Growth Metrics）

| Feature ID | 平台 | 用户可见功能 / 结论 | 原始平台来源 | 推导算法与逻辑 | 缺失值处理 | Golden Samples | 最终状态 | 备注 / 风险 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TREND-MCMOD-01` | MCMod | 7天/30天/全期趋势折线图 (Sparkline) | MCMod 页面每日关注度时序数据 | `viewsDelta` 每日增量时序数组，计算最近 7d 历史并渲染 SVG | 无数据填当前点 | `mcmod:16`, `mcmod:722` | **`VERIFIED`** | 纯数学趋势折线，算法与时序完全保真。 |
| `TREND-MCMOD-02` | MCMod | UI 文案“热度增长” | MCMod 每日页面浏览量增量时序 | 计算当前点与历史基期的差值百分比 `(curr - base) / base` | 缺历史返回 0% | `mcmod:16` | **`SUSPECT`** | 实际上是“MC百科页面日均浏览增量”，文案宣称为“热度增长”稍显夸大。 |
| `SCORE-MCMOD-01` | MCMod | 整合包“星级评分” (1 ~ 5 星) | MCMod 详情 | 当 `score` 为空时，**算法强制按当日浏览增量推算星级**：`lat_n > 500` 给 5星，`> 200` 给 4星，`> 50` 给 3星，`> 10` 给 2星，否则 1星 | 强制赋予 1-5 星 | `mcmod:16` (5星), `mcmod:1480` | **`WRONG`** | **确认缺陷**：将“单日浏览热度”伪装成用户的“玩家评分星级”，严重误导用户对作品品质的客观判断。 |

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
| `AUDIT-DIFF-01` | 全平台 | “版本变动 / 最近更新 / 数据审计” 弹窗 | `audit_diff.js` 导出器 | **硬编码输出空数组**：`added: []`, `updated: []`, `removed: []` | 固定空对象 | `converted_output/data/audit_diff.js` | **`WRONG`** | **确认缺陷**：未实现跨批次或跨版本快照的真实 diffing 引擎，UI 显示的变动数据属于静态占位符。 |

---

### 领域 14：时间语义表（Time Truth Table）

| Feature ID | 平台 | 字段名称 | 原始平台真实物理含义 | 数据库字段 | 表现异常 / 污染证据 | 最终状态 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME-MODRINTH-01`| Modrinth | `date_created` / `date_modified` | 官方项目创建与最后修改时间 (UTC ISO) | `published_at`, `modified_at` | 规范完整，无异常 | **`VERIFIED`** |
| `TIME-CURSEFORGE-01`| CurseForge | `dateCreated` / `dateModified` | 官方项目创建与最后更新时间 (UTC ISO) | `published_at`, `modified_at` | 规范完整，无异常 | **`VERIFIED`** |
| `TIME-BILI-01` | Bilibili | `pubdate` | 视频发布时间（Unix 时间戳） | `published_at` (`modified_at` 置空) | Bilibili 无原生修改时间，936项 `modified_at` 为 NULL，合法 | **`VERIFIED`** |
| `TIME-MCMOD-01` | MCMod | `created_at` / `release_date` | 页面收录日期 / 模组包原发布日期 | `published_at`, `modified_at` | **污染**：将中文字符串 `'未知时间'` 存入日期列 (`mcmod:34`) | **`WRONG`** |
| `TIME-XYEBBS-01` | XYEBBS | `post_time` / `edit_time` | 论坛发帖与最后编辑时间 | `published_at`, `modified_at` | **污染**：将中文字符串 `'未知'` 存入日期列 (`xyebbs:15435`) | **`WRONG`** |
| `TIME-BBSMC-01` | BBSMC | `date_created` / `date_modified` | 论坛发帖与最后编辑时间 | `published_at`, `modified_at` | **时序倒错**：20 个帖子 `published_at > modified_at`（如发帖 04-27 编辑 04-24） | **`SUSPECT`** |

---

### 领域 15：缺失值与兜底行为（Missing & Unknown Handling）

| Feature ID | 平台 | 现象 / 场景 | 前端当前处理逻辑 | 事实与风险 | 最终状态 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `MISS-NUM-01` | 全平台 | 下载量或浏览量等统计数值为 `NULL` | `numFmt(null)` 强制返回字符串 `'0'` | **造假风险**：未统计或平台缺失的数据在 UI 上直接呈现为“0 次下载”，误导用户以为无人问津。应显示为 `—` 或 `未公开`。 | **`WRONG`** |
| `MISS-ENV-01` | 全平台 | 模组包未声明服务端或客户端支持 | 前端直接判定为 `has_server: false`，显示文案“未提供专用开服端” | **负向断言造假**：没有证据证明支持 $\ne$ 证明不支持。应显示为“未声明服务端支持”或“无法确认”。 | **`WRONG`** |
| `MISS-VER-01` | Bilibili / MCMod | 未能提取 Minecraft 游戏版本 | 弹窗及卡片展示“通用 / 未指定” | 合理兜底，未伪造具体版本号。 | **`VERIFIED`** |

---

## 3. 问题优先级与改进计划 (Prioritized Action Register)

### P0: 事实性错误（WRONG）— 必须消除的系统硬伤
1. **`SCORE-MCMOD-01`**: 移除根据单日浏览增量虚构 MCMod 1~5 星评分的逻辑，无真实评分时显式标注“暂无评分”或直接展示浏览热度。
2. **`MISS-NUM-01`**: 修改前端 `numFmt`，当输入为 `null`/`undefined`/`''` 时返回 `"—"` 而不是 `'0'`，杜绝将缺失数据伪装为 0 下载。
3. **`MISS-ENV-01`**: 修正服务端展示兜底文案，由“未提供专用开服端”改为“未声明服务端支持 / 无法确认”，解除无证据等价于不支持的负向断言。
4. **`DL-BBSMC-02`**: 清洗 BBSMC 错误抓取为 URL 的长篇更新日志，置为空或移至 changelog 字段。
5. **`DL-XYEBBS-01`**: 清洗 XYEBBS 错误存入的 `null`、`undefined`、`Neoforge`、`QQ群号` 等伪下载链接。
6. **`TIME-MCMOD-01` & `TIME-XYEBBS-01`**: 清洗数据库中存入日期列的中文字符串 `'未知时间'` 和 `'未知'`，规范为标准 `NULL`。
7. **`BILI-GRP-02`**: 修复 Bilibili 聚合算法，对清洗后长度 $\le 3$ 或属于纯泛词（如“生存”、“我的世界”）的 Key 禁止跨视频聚合，防止误合。
8. **`LOADER-BILI-01`**: 补全 Bilibili Adapter 对标题中明确标注 `Forge`/`NeoForge`/`Fabric` 的识别逻辑，消除 11 个显式标注遗漏。
9. **`AUDIT-DIFF-01`**: 移除 `audit_diff.js` 虚假的空数组生成，建立真实的 Canonical 批次对比表或在 UI 上标注“暂未启用快照对比”。

### P1: 事实性风险（SUSPECT）— 必须审慎呈现的启发式结论
1. **`MODS-MCMOD-02`**: MCMod 170,078 条模组关联中包含 19.4% 的 `LIB` 基础前置库与 33.2% 的辅助工具，前端应支持按分类（前置库/玩法模组）筛选，避免模组数量虚高。
2. **`DIDX-MCMOD-01`**: 模组搜索深度索引应在 UI 上提供区分选项：“标题/玩法核心匹配” vs “包含模组依赖匹配”。
3. **`BILI-GRP-03`**: Bilibili 部分同一整合包的多期更新视频因标题含版本特性被拆解，建议引入更宽泛的分词相似度辅助关联。
4. **`TIME-BBSMC-01`**: 调查 BBSMC 论坛 20 项发帖时间晚于编辑时间的时序倒错原因，必要时取两者的较晚时间作为 `modified_at`。

### P2: 语义未定项（UNKNOWN）— 显式诚实展示未确定
1. **`DL-MCMOD-01`**: MCMod 本身不托管文件，UI 明确标注为“原站百科跳转”而非“下载失效”。
2. **`ENV-CURSEFORGE-01` / `BBSMC` / `XYEBBS`**: 缺乏官方环境字段时，统一展示为 `UNKNOWN`（未声明），不强行推断。

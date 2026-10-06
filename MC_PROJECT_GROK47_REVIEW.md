# MC Modpack Board — Grok 4.7 Independent Review

> 复核时间：2026-09-22  
> 角色：Independent Principal Reviewer / Devil's Advocate  
> 主材料：`MC_PROJECT_CONTEXT_FOR_ASTRA.md`  
> 本轮没有改功能代码，没有跑测试，没有启动浏览器服务，没有 merge / push，没有重新抓取。  
> 抽查范围：master `fa47ffe` 上的服务端过滤、搜索合同、desktopShell 全平台加载、MC百科 crawler 落盘、snapshot pipeline；PR #5 worktree 上个人库 key 与 B 站分组卡片的绑定；本机 `converted_output` 六份 sidecar 与 `crawler_output/mcmod_modpacks.json` 的字段普查。  
> 事实包里没有编号的 Next 1 / 2 / 3。下文的优先级是重新判断的，不是改写一份不存在的路线图。

标记：

- **FACT**：本次用 Git 对象、master/PR5 源码或本机 sidecar/raw 直接看到的。
- **INFERENCE**：由这些事实推出的产品或风险判断，不是新的测量。
- **RECOMMENDATION**：如果这个项目归我、资源有限，我会怎么选。

---

## 1. Executive Review

事实包的纪律是好的。Git 与 PR 边界、canonicalReady 的含义、B 站分组不是跨平台身份、测试 PASS 不能拼成 GUI 验收，这几件容易被后续模型写错的事，它都写成了明确限制。我不把这份材料推翻。

第二意见集中在四件它说得太轻、或现在已经对不上现场的事：

1. **活动数据目录现在复现不了。** 事实包把 `C:\Users\Administrator\AppData\Roaming\MCModpackBoard\data` 和快照 `20260920084809555-578e8c` 标成 CONFIRMED。本次磁盘上没有这个目录，仓库里也只有事实包自己提到这个快照 ID。同一组记录数可以在仓库 `converted_output` 上原样数出来。计划可以信任这份语料，不能把“服务此刻正读着那份 active snapshot”当成仍成立的现场。
2. **MC百科不是“部分字段缺失”。** 当前 sidecar 与 raw 都是 1,484 条：封面 URL 全空，Loader 全空，下载链接全空；约 78% 没有可排序的更新时间。这是用户判断“适不适合”时最重要的中文目录。事实包的能力矩阵把这些写成边界，数量级没有写出来。
3. **个人状态的现实风险不是 index fallback。** 这份语料六个平台的 source id 都齐全、无重复、无回退键。PR #5 的 B 站聚合卡片把收藏绑在“当前最新一条视频的 bvid”上。视频 ID 稳定，包分组不稳定。事实包把这两件事分开写了，没有把它们接上。
4. **全平台首页不是一次跨平台检索。** 服务端确实先过滤再分页；浏览器在“全部平台”下把每平台页大小固定为 12，再按平台顺序拼接。排序只发生在平台内部。这个行为对“不要被 CurseForge 淹没”反而是有益的，但它不实现搜索框承诺的跨平台找包。

架构可以继续用。不需要重写，不需要把 canonical identity、字段统一、数据健康台、导出恢复、保存搜索做成下一阶段。真正值得花钱的是：让现有字段诚实，让收藏能回来，让“找新包”发生在单个平台里。

---

## 2. Facts I Trust

这些我抽查后仍然接受，不在正文里重讲。

- **FACT** 仓库 `suifracti/mc-modpack-crawler-board`。本地 master 是 `fa47ffe`。主工作目录是 `codex/repository-cleanup` @ `34be1b2`，且是 master 的祖先。该工作目录磁盘上没有 `apps/web/src/desktopShell.ts`、`apps/desktop/server.cjs`；这两个文件在 master 上存在。PR #5 `feature/personal-library` @ `1d80a2c` 不是 master 的祖先，个人库文件在该 worktree 上存在。
- **FACT** 事实包对“已实现 / 已合并 / 已发布”的分层是对的：PR #1–#4 在 master 历史里，PR #5 是 OPEN 分支能力，Electron、A/B、Truth Matrix、production cutover 都不是当前启动路径。
- **FACT** `converted_output/data` 记录数与事实包一致：MC百科 1,484，Bilibili 936，BBSMC 1,802，XYEBBS 5,175，Modrinth 18,328，CurseForge 45,797，合计 73,522。`comments` 1,417 个文件，`mods` 1,484 个文件。这是平台行数。
- **FACT** 浏览器服务读现代 sidecar，不依赖活动快照里有 `canonical.db`。`snapshot_pipeline.py` 只有六个 raw 都在隔离 workspace 里才建 canonical；建失败会抛错，从而让本轮更新失败、旧 pointer 保留。这条代码与事实包的失败语义一致。
- **FACT** 搜索是空白分词、每个 term 必须命中某一字段。MC百科 desktop 路径调用 `buildSearchDocument(platform, raw)` 时没有传入 desc/comments。这与事实包第 7 节一致。
- **FACT** 个人库设计键是 `platform:sourceId`，文件在 dataRoot 根上，不在 snapshot 目录里。当前语料没有把这个键用坏的缺 ID 行。
- **FACT** 历史测试表被标成 HISTORICAL，GUI 被标成 UNKNOWN。这个边界应保持。

---

## 3. Possible Fact Conflicts

### 3.1 活动快照路径现在不存在

- **FACT** `defaultUserDataRoot()` 在 master 上确实会落到 `%APPDATA%/MCModpackBoard/data`。
- **FACT** 2026-09-22 本次检查：该目录不存在。快照 ID `20260920084809555-578e8c` 只出现在事实包正文，不出现在仓库其他文件。
- **FACT** 旁边有 Electron 时代目录 `%APPDATA%/mc-modpack-board-desktop/data`。其中 `snapshots` 与 `incoming` 都是空的，也没有 `active.json`。那个目录有 GPUCache、Session Storage，形态是旧壳的用户数据，不是事实包描述的活动快照。
- **INFERENCE** 快照 ID 和时间戳具体到毫秒与随机后缀，不像单凭函数默认值编出来的。更可能是写事实包时读到过、随后目录被清掉，或写在本次看不到的数据根上。两条都不能在今天复核。
- **RECOMMENDATION** Astra 把 73,522 条和字段空洞当作 `converted_output` 的事实；把“用户服务正在使用那份 active snapshot”降级为未能复现。不要为了填这个洞去重跑导入。

### 3.2 MC百科“部分缺失”与全量空洞

事实包写：Loader 很多为空；部分记录没有封面、版本或模组细节；adapter 把 `download_links` 置空。

本次对同一批 1,484 条的计数：

| 字段 | sidecar `mcmod_data.js` | raw `mcmod_modpacks.json` |
| --- | --- | --- |
| 稳定 mid，无重复 | 1,484 / 1,484 | 同左 |
| 封面 URL | 0 | `cover_url` 0 |
| `loaders` | 0 | raw 中没有 loader 键 |
| `download_links` | 0 | 该 raw 无此键 |
| 可作更新时间的日期 | 326（空 1,158） | `last_update_date` 328 |
| 其中落在 2026 | 123 | 未按同一函数再切 |
| 其中落在 2026-09 | 12 | 未按同一函数再切 |
| `mcVersions` | 1,372 | `mc_versions` 1,372 |
| 模组名 | 953 有，531 空 | raw 有 `mods` / `mod_count` |
| `downloads` | 0 | 无下载计数字段 |
| `latest_version` | sidecar 对象键里没有这一项 | 328 条非空 |
| `has_server === true` | 6 | 未单列 |

- **FACT** 封面和 Loader 在这批数据上是全体缺失，不是长尾缺失。
- **FACT** raw 已经有 328 条 `latest_version` 和 328 条 `last_update_date`。master 上 `build_modern_mcmod_entry()` 的返回值包含 `publishedAt` / `modifiedAt`，不包含 `latest_version`。sidecar 日期非空 326，与 raw 的 328 差 2 条。
- **INFERENCE** 用户在百科卡片上看不到版本名，不完全是源站没有，其中几百条是落盘时丢掉的。Loader 和封面则是采集结果里就没有，刷新快照不会自动长出来。
- 这不是事实包写反了，是 **CONFIRMED 的范围小于数据的实际空洞**。后续若写“百科已支持版本 / Loader / 封面”，就是超过证据。

### 3.3 “mcmod_data.js 由 StructuredMCModExporter 从 canonical.db 导出”

- **FACT** 离线 pipeline 里确有从 canonical 导出的路径。事实包第 9 节把现代 `mcmod_data.js` 说成这个导出契约。
- **FACT** desktop 更新路径要的 sidecar 文件名也是 `mcmod_data.js`，而 `mcmod_full_crawler.py` 自己在采集结束时写这个文件。`snapshot_pipeline.py` 建 `canonical.db` 后没有再调用 exporter 去覆盖 sidecar。
- **INFERENCE** 当前这份 `converted_output` 的字段形状（`environmentClaims`、`includedModNames`、空 `coverUrl`）与 crawler 内的 `build_modern_mcmod_entry()` 一致。不能据此证明它一定不是某次 exporter 产物；能确定的是：下一次走 desktop worker 的百科更新，写入者是 crawler，不是“必须先有 canonical.db 的 exporter”。
- **RECOMMENDATION** 计划里把“百科 sidecar 的生产者”写成两条路径。浏览路径不读 canonical。不要把补齐 Loader/封面写成“把 canonicalReady 变成 true”。

### 3.4 全平台结果的两句描述可以同时成立，但漏了页大小

- **FACT** `data-store.cjs` 在完整 normalized 集合上搜索、筛选、排序，然后 `slice` 分页。
- **FACT** `desktopShell.ts` 在 `state.platform === 'all'` 时向六个平台各请求一页，`requestPageSize` 固定为 12，忽略界面上的 24/48/100。结果按平台数组合并。`state.total` 是六份 total 之和。加载更多是每个平台再取下一页 12 条。
- **FACT** 排序菜单在非 B 站（含“全部平台”）使用下载、浏览、关注等键；这些键在每个平台内部排序。拼接顺序是平台注册顺序。
- 事实包“服务端全量过滤”和“全部平台是各平台当前页片段”可以同时为真。它没有写死的 12，也没有写排序不跨平台。
- **INFERENCE** “各平台当前已载入页面的首批匹配”容易被读成客户端只搜已经载入的页。源码不是这样。服务端搜全量，界面只展示每平台前 12 条命中。

### 3.5 index fallback 是代码风险，不是这批数据的现状

- **FACT** `normaliseRecord` 的优先级是：MC百科 `mid/source_id/id/project_id`，B 站 `bvid/source_id/id`，其他平台 `project_id/source_id/id/slug/...`，最后才是 `` `${platform}-${index+1}` ``。`id` 排在 `slug` 前面。
- **FACT** 按这套优先级数 `converted_output`：六个平台 missing stable id = 0，重复键 = 0，没有“只有 slug”或“没有 project_id 却在用 id”的行。
- 事实包把覆盖率标成 UNKNOWN 是对的，因为他们没扫。它后文用“可能失去个人状态关联”推动设计时，容易被读成当前语料已经在用回退键。
- **INFERENCE** 以这份语料合并 PR #5，不会因为列表重排而大面积错绑。回退键仍是以后 crawler 吐出无 ID 行时的脚枪。其他平台若将来只给不稳定的 `id` 而不给 `project_id`，`id` 会压过 `slug`。

### 3.6 没有把测试误写成产品验收

这一节没有冲突。事实包没有把 Vitest、HTTP、旧 20/20 搜索或 A/B Recall 升成当前产品 PASS。我同意。

### 3.7 工作目录与“当前源码”

事实包已经写明盘点发生在 `codex/repository-cleanup`，产品描述指向 master。抽查支持这个分层。

- **INFERENCE** 后续模型若直接改主工作目录，会改到一份没有 browser service 的旧树，同时仓库里又留着 `bilibiliGrouping.ts`。这是流程陷阱，不是事实包自相矛盾。
- **RECOMMENDATION** 任何实现都从 master 或明确的 feature 分支起，不要从当前主工作目录起。

---

## 4. Product Gaps

用户路径：找新包 → 筛选 → 判断适不适合 → 看版本、Loader、内容、评价、来源 → 记下想玩 → 以后回来 → 去原站获取。

### 已经好用的环节

- **FACT / 产品判断** 单平台里的版本、Loader、分类、渠道筛选发生在分页之前，候选集合是该平台全量命中，不是“当前页里再筛”。Modrinth、CurseForge、XYEBBS、BBSMC 的记录都有稳定 project id，Loader 计数为 0 缺失，下载数字段基本全有。
- **FACT** Modrinth 与 CurseForge 的下载链接在这批 sidecar 里是满的。XYEBBS 仅 1 条空下载链接。原站 URL 加 http/https 限制，符合“最后去原站拿”的目标。
- **FACT** MC百科的差异化是内容而不是发行元数据：953 条有模组名，搜索文档会索引 `includedModNames`。这是六个平台里唯一能按模组名找包的正式搜索面。
- **FACT** B 站 936 条都有 bvid 和封面，日期字段没有空值。平铺视图就是视频。作者范围内的标题归组是展示层，事实包对它的定位我同意。
- **FACT** 比较 tray 只比较作者、版本、Loader、分类、服务端文字和平台指标，而且活在页面内存里。作为临时并排足够，不构成“比较产品”。

### 只是功能有了

- **搜索框文案超过索引。** **FACT** 全平台输入框的 placeholder 写着按名称、游戏版本、模组名、玩法或作者做跨平台检索。模组名只进了 MC百科搜索文档。B 站字幕、置顶评论、QQ 群进了展示摘要，不进 `buildBilibili` 的 description 字段。非百科平台的 `versionsLower` 只取 `mc_version` 一个字段。
- **排序名在跨平台和百科上没有共同含义。** **FACT** “下载最多”只读 `raw.downloads`。MC百科和 B 站这批数据的 downloads 非空数是 0。全平台选择这个排序时，这两个平台内部几乎全是 0，再按标题打破平局，然后各贡献 12 张卡片。
- **“仅含服务端”在 Modrinth 上过宽。** **FACT** Modrinth `server_side`：required 10,495，optional 2,165，unsupported 5,542，unknown 126。`has_server === true` 为 12,660，等于 required + optional。筛选接受 required、optional、supported 或 `has_server === true`。CurseForge 同批只有 230 条 `has_server === true`。
- **INFERENCE** 用户以为自己在找“适合当服务器的包”。在 Modrinth 上，他会得到“服务端可选或必需”的大约 69% 目录。这是筛选语义，不是缺一个新筛选器。
- **时间预设是写死的日历。** **FACT** 日期菜单含 `2026` 与 `2026-09` 两个字面量，另有近 7/30/90 天。百科 sidecar 里 2026-09 只有 12 条。近 N 天用 `recordTimestamp`，时间戳为 0 的记录通不过。
- **详情里的版本史取决于 raw 有没有 releases。** **FACT** 百科 version adapter 在没有 `versionUrl` 时会打开 `https://www.mcmod.cn/modpack/version/${mid}.html`。当前 sidecar 记录上没有 `releases` / `versions_data`。应用内版本表是空的，离开应用可以看百科版本页。
- **更新面板是任务状态，不是“这个包更新了什么”。** 事实包这句我同意。它不在找包主路径上。

### 仍然断开的环节

1. **判断 MC百科条目适不适合。** 有中文标题、热度、评分、常常还有模组名单；没有封面、没有 Loader、没有下载、大多数没有更新时间，版本名即使 raw 里有也不在 sidecar。用户无法在应用里完成“版本 + Loader + 能不能下”。这一步今天只能跳到原站，而卡片没有把“这里没有 Loader/下载”说成数据事实。
2. **找“新”包。** 全平台默认“最近更新”不是一条时间线。百科大多没有时间，有时间的平台各自排完再被截成 12 条。B 站分组模式还会先把命中视频按 500 一页拉完再在客户端分组，那是另一条路径，当前 936 条承受得住。
3. **以后回来。** master 没有个人状态。PR #5 的收藏筛选是服务端、分页前的，所以“只看收藏”一旦合并，本身就能跨快照找回，不依赖把卡片都加载进浏览器。断开点是它还没进 master，以及 B 站分组卡片不代表一个稳定的包。
4. **B 站分组上的个人状态。** **FACT** PR #5 的分组卡片用 `latest.bvid` 查找 `state.records` 里的那条记录，个人键是这条记录的 `platform:sourceId`。新视频变成 latest 之后，分组卡片上的收藏按钮看到的是另一个 bvid。旧视频上的收藏还在。
5. **评价。** 百科有 score、推荐、红黑票，这是真评价。其他平台是播放、下载、关注。应用没有把这两种“评价”分开讲。比较面板把它们合成“平台指标”。

### 价值不高的已有能力

- 卡片对比的会话 tray。主路径是打开原站，不是在本地做采购表。
- 五种主题。与找包无关。
- 全平台同时铺六个渲染器。看起来完整，决策信息更差。
- 百科专业表格的趋势火花线。浏览量趋势对挑包的帮助低于版本和 Loader；而且这批封面全空，表格的丰富感来自统计，不来自“我能不能玩”。

### 高价值但仍然缺着的能力

缺的不是新子系统。缺的是把已经采集到的判断材料交到主路径上：

- 百科：模组名已经能搜；版本名有 328 条在 raw 里；Loader、封面、下载链接这批就是没有。应用应把“没有”显示成没有，而不是再采集五个新网站来补偿。
- 单平台的“这个版本 + 这个 Loader + 按下载或更新排序”。Modrinth / CurseForge / XYEBBS 上这条链是通的。
- 一个能活过重启的“想玩/收藏”，键稳定，并且在 B 站上明确绑视频还是绑分组。

不缺：跨平台同一实体、统一评论、统一模组清单、相关度模型、保存搜索。

---

## 5. Architectural Review

### 目前够不够合理

**RECOMMENDATION** 够用，而且比再引入一层“真正的数据库产品”更合适。

Node 只做本机 HTTP、快照和 API，Python 只做采集，浏览器不碰文件系统。73,522 条 sidecar 在进程内 normalize 后按平台缓存，CurseForge 那份大约 47MB，对个人本机工具是合适的量级。个人库用 dataRoot 上的一个 JSON，和快照拷贝分开，这个分离是对的。

### 现在值得处理的结构问题

只有一个会在用户下次成功抓取时咬人：

- **FACT** 单平台更新会把未选平台的旧 raw 抄进新 snapshot。隔离 workspace 里一旦六个 raw 齐全，`snapshot_pipeline.py` 就调用 `build_canonical_db`。异常会变成整次更新失败。
- **FACT** 浏览器不读这个 `canonical.db` 来渲染当前 sidecar。
- **INFERENCE** 用户已经拿到新的 raw 和 sidecar，仍可能因为一份界面不用的 SQLite 而看到失败，并继续看旧快照。当前活动导入若根本没有六份 raw，这条路径还没被日常触发。它是更新模型里的结构缺陷，不是浏览模型里的缺陷。
- **RECOMMENDATION** 下次碰更新流程时，让 canonical 失败变成 manifest 里的 `canonicalReady=false` 加原因，sidecar 合格就允许切换 pointer。不要为此重写 pipeline。

第二个结构问题是给后续 AI 的，不是给用户的：

- **FACT** 主工作目录没有 desktop 服务代码；master 上同时有 `desktopShell.ts`、`legacyAdapter.ts`、`dashboard.legacy.js`，以及 crawler 与 exporter 两条百科 sidecar 写入路径。
- **INFERENCE** 模型会改到旧 HTML、旧搜索状态机，或给 canonical 补字段并以为浏览器会读到。事实包已经警告不要删 legacy。警告是对的，但“两套都算正式”会继续制造这种修改。

### 可以永远不修的技术债

- Electron 的 `main.cjs` / `preload.cjs` 留在仓库里。没有启动路径调用它们。
- 个人库没有迁移框架、没有备份 UI、没有跨机器同步。一份 schema=1 的 JSON，在真有用户数据之前不需要框架。
- snapshot、raw、sidecar、manifest、canonical 不是同一个数据库事务。个人工具的提交边界已经是 `active.json` rename。统一事务没有产品收益。
- DTO 在 normalise、rich renderer、legacy bridge 之间转三次。难看，但六个平台本来就不同构。抽“唯一字段源”容易变成一次大迁移。
- 没有 snapshot 保留策略。磁盘会涨。真的涨了再删旧目录，并避开 dataRoot 根上的个人库文件。现在不做清理框架。
- A/B 归档 tag、Truth Matrix、cutover 脚本。留着即可。

### 会明显拖累以后 AI 开发的地方

- 在非 master 工作目录里继续派工。
- 把 legacy dashboard 和 desktopShell 都当成可以加功能的产品面。
- 用 canonical identity 或“平台字段统一”作为新需求的前置。模型会去读归档审计，而那些数字已被事实包正确标成 HISTORICAL。
- 搜索有 shared contract、legacy search、还有 desktopShell 里为展示而重建的 `allTextLower`。`matchesSearchDocument` 并不读 `allTextLower`。Modrinth/CurseForge 重写 `allTextLower` 时丢掉了版本和 Loader，当前服务端匹配仍靠独立字段，所以今天不是用户可见 bug。它会让下一个模型“修搜索”时改错层。

### 有没有更简单的路线

有，而且就是少做一点：继续 sidecar 加本机服务；发现以单平台为主；百科负责中文目录和模组名；Modrinth、CurseForge、XYEBBS、BBSMC 负责版本、Loader 和获取；B 站负责视频线索。跨平台页面保持“每平台一组样本”，不要升级成全局排序实体。

---

## 6. Data / Identity Review

### `platform:sourceId`

- **FACT** 这批语料上，该键在平台内唯一且不依赖行号。MC百科用 mid，B 站用 bvid，其余四平台按 `project_id` 优先时都能取到值。
- **INFERENCE** 用户数据错绑的当前概率低。未来错绑条件是：某平台开始产出无 `project_id` 的行，或产出会变的 `id` 且它排在 `slug` 之前。那是采集合同问题，不是现在就要做的身份工程。
- **RECOMMENDATION** 合并个人库时保持这个键。不要等 canonical id。可以在写入时拒绝 `` `${platform}-数字` `` 这种回退键，防止以后无 ID 行被静默收藏。这是一条保护，不是新的身份系统。

### 跨平台归并

- **FACT** 键不跨平台。同名整合包在百科、B 站、Modrinth 上是三行。
- **INFERENCE** 自动归并才会造成跨平台错绑：译名、版本号、作者名都不可靠。不归并的代价是收藏了两次，用户打得开原站自己认。这个代价比错并小。
- **RECOMMENDATION** 不做 canonical identity。以后若真要“这几条是同一个包”，只做用户手工关联，并且默认不存在。

### snapshot identity 与个人数据

- **FACT** PR #5 的个人文件不在 snapshot 目录。快照复制逻辑不负责拷贝或删除它。导入新 snapshot 后，同一 `platform:sourceId` 仍能对上，这是设计目标，事实包所说的测试也覆盖这个场景；那些测试本次没有重跑。
- **INFERENCE** 状态丢失的现实途径是：源 ID 变了、记录从新快照消失、或 B 站分组把 UI 指到了另一条 bvid。消失的收藏会变成没有卡片的 JSON 项。当前没有对账界面。一份 JSON 在条目还很少时，这是可以接受的。
- **FACT** 事实包说当前 dataRoot 没有 `personal-library.json`。默认 dataRoot 今天不存在，所以“没有这份文件”仍然成立，只是所在目录本身也不在。

### 平台字段差异会造成的搜索错误

- **FACT** 版本筛选用的是 normalize 后的 `record.versions`（百科 `mcVersions`，其他平台 `all_versions` 加 `mc_version`）。关键词里的版本，非百科只来自 `mc_version` 一个字符串。
- **FACT** 这批非百科 sidecar 里，不存在“有 `all_versions` 但 `mc_version` 为空”的行。主版本关键词和版本筛选在这批数据上大体指向同一批包。旧版本若只出现在 `all_versions` 数组里，关键词仍可能漏。我没有单独数这个子集。
- **FACT** 百科 Loader 筛选候选会是空的，因为 1,484 条 `loaders` 都是空数组。用户选 Fabric 时，百科整平台 0 命中。这不是筛选 bug，是数据空洞被精确执行。
- **INFERENCE** 最严重的搜索错误是期望错误：搜索框承诺模组名和玩法的跨平台检索；玩法没有独立字段；模组名只有百科。

### B 站视频和整合包的关系

- **FACT** 一条 sidecar 记录是一个视频。分组是作者作用域内的标题启发式，代码禁止跨作者合并，也不用下载 URL 或 QQ 群当键。
- **FACT** 个人库若按分组卡片写入，写下去的是 latest video 的 bvid，不是分组算法的 group id。
- **INFERENCE** 这会让“我收藏了这个整合包系列”在下一次更新视频后从分组卡片上消失，同时旧视频仍带着收藏。平铺视图不受这个错觉影响。
- **RECOMMENDATION** 在没有稳定分组 ID 的时候，收藏的对象就是视频。分组卡片如果要显示收藏，应该表示“组内存在已收藏视频”，写操作要明确写到哪一个 bvid。不要为了把收藏升成“包”而重开 A/B 归组工程。

### canonical 与 snapshot

canonicalReady=false 不会让浏览读到错的包。它只说明这份导入没有 SQLite。把个人数据或搜索绑到 canonical 行号上，才会引入第二套身份。现在没有这种绑定。保持没有。

---

## 7. Overengineering Risks

事实包第 19 节把 A/B、Truth Matrix、cutover、重写 identity、重做 UI、加数据源、恢复 Electron 都标成了不要自动展开。我支持这个刹车。下面这些方向即使听起来像“个人库下一阶段”，也容易变成无终点工程。

| 方向 | 意见 | 为什么 |
| --- | --- | --- |
| 个人库工作区 | 反对单独做成产品 | PR #5 的收藏/想玩/玩过筛选已经是分页前的全量过滤。工作区是另一种导航，不是“回来”所缺的那一层 |
| 最近查看 | 反对单独立项 | 它和收藏抢同一件工作，又多一套本地状态。浏览历史不是挑包 |
| 保存搜索 | 反对 | 搜索语义还没和文案对齐。把一次不可靠的查询存下来，会把错误固定成功能 |
| 保存筛选 | 反对现在做 | 版本 + Loader 筛选已经在。服务端筛选语义（尤其服务端、百科空 Loader）还没说清楚之前，保存只是多一个设置页 |
| 数据健康 | 反对做成界面 | 本次普查已经说明百科的空洞。健康台会膨胀成无限审计。用户需要的是卡片上的“无 Loader / 无下载” |
| 导出/恢复 | 反对 | 个人库还没有文件。恢复手段就是复制那一个 JSON。UI 和迁移框架都早了 |
| 搜索相关性 | 反对 | 现在是 AND 子串加一个业务排序。73k 个人目录不需要 BM25。先让字段和 placeholder 一致 |
| 平台字段统一 | 反对 | 六个来源的评论、模组、服务端证据本来就不是一个东西。压成统一模型会伪造精度 |
| canonical identity | 反对 | 错并的伤害大于重复收藏。canonical.db 也不是这条身份的完成证明 |
| B 站归组 | 保持现状，停止审计工程 | 当前启发式是正式展示。A 的 28/277 是历史安全证据缺口，不是本产品的停用条件 |
| legacy renderer | 停止加功能，先不删 | 删除要重新对调用链。继续加功能会让 AI 在两套 UI 上各写一半 |
| 更多数据源 | 反对 | CurseForge + Modrinth 已经约 87% 的行。新源线性增加 adapter、搜索和身份表面 |

---

## 8. STOP / DROP Candidates

这些可以停，包括已经投入过很多的：

1. **A/B B 站安全归组、26-case、holdout、under-merge 门禁。** 展示分组已经在 master。继续审计不改善“去原站看视频”这条主路径，而且历史上已经 BLOCKED 在安全证据上。沉没成本大，正好说明该停。
2. **跨平台 canonical identity，以及为它服务的 Truth Matrix / production cutover。** 浏览不读 canonical。身份工程会吃掉后面所有个人库工作。
3. **把六个平台的评论、模组清单、版本史做成统一详情。** 百科模组名单是局部优势。给 CurseForge 4.5 万条补模组清单是另一个产品。
4. **数据健康台、快照保留策略、个人库备份/恢复/同步、schema 迁移框架。** 都是平台工程。当前用户数据几乎还不存在。
5. **保存搜索、保存筛选、最近查看、独立“我的库”信息架构。** 在收藏筛选可用之后再看有没有人真的迷路。现在做是功能堆积。
6. **搜索相关度、全局去重排序、可解释搜索命中。** legacy 里已有更丰富的搜索解释，desktop 没有接上。不要把旧路径的完整度当成新路径的欠债清单。
7. **legacy dashboard 的新行为，以及 Electron EXE。** 兼容代码可以留。交付目标不要回去。
8. **新平台、全量重抓作为计划主体。** 这批数据的日期大约在 2026-09-14 到 2026-09-20，相对今天并不旧。百科缺的 Loader 和封面不是再抓一次就会出现，除非采集器本身开始解析它们。那是一个有界的百科采集问题，不是“更多数据源”。
9. **为 index fallback 做一轮全量身份修复项目。** 这批数据没有这种行。写一条拒绝回退键的保护就够，如果个人库要合并的话。

可以留下但不要发展的：会话对比、多主题、更新日志面板、canonical.db 作为离线侧车。它们不挡路，除非有人继续加功能。

---

## 9. My Alternative Priorities

资源只够三件事。顺序是用户判断，然后记得住，然后找得到新的。三件都不要展开成任务书。

### 1. 让“适不适合”使用真实字段

MC百科是中文用户最先想信的目录，也是当前判断链最断的目录：全体没有 Loader、封面和下载链接，大多数没有更新时间，版本名在 raw 里有几百条却没进浏览器 sidecar。Modrinth 的“仅含服务端”把 optional 算进去，和 CurseForge 不是同一个问题。搜索框还在承诺跨平台模组名。

先把这三处说真话，用户才有资格收藏。否则个人库收藏的是一张信息不够的卡片。这一项包括：空字段就显示空；服务端筛选的含义按平台说清楚；搜索文案退回到真正索引的字段。它不包括统一 schema，也不包括给所有平台补模组爬虫。百科 raw 里已经有的 `latest_version` 若要出现在卡片上，那是这条优先级里面的小修正，不是新项目。

### 2. 用已经写好的个人标记解决“以后回来”

PR #5 已经有收藏、想玩、玩过、评分和备注，而且筛选在服务端、在分页之前。键在这批数据上是稳的。这比新做工作区、最近查看或导出更接近用户路径。

合并前只需要一个产品决定：B 站分组卡片的标记到底写在哪一个 bvid 上，以及分组视图如何显示“组里已经有收藏”。不要把这个决定升级成归组算法重做，也不要捆绑工作区、备注搜索和评分排序。评分和备注留在详情里即可。

### 3. 把“找新包”定义成单平台浏览

全部平台作为六个样本橱窗可以留，但默认找包的动作应该是：选一个平台，用版本和 Loader 收窄，再按更新或下载排序。这个能力在 Modrinth、CurseForge、XYEBBS、BBSMC 上已经成立。百科适合按模组名和热度逛，不适合按“本月更新”逛，至少这批数据不适合。

不要做全局相关度，不要做跨平台去重榜。全平台每家 12 条的偶然好处是中文源不会被 4.5 万条 CurseForge 压没。拆掉它之前，先确定单平台路径已经是主路径。

更新可靠性（canonical 失败不要否决 sidecar）排在这三件事之后，而且只在下一次改更新流程时一起做。它不改变用户怎么挑包，它防止以后刷新把浏览打回旧快照。

---

## 10. Questions Astra Must Resolve

1. **MC百科在这个产品里是什么？** 中文内容目录（接受没有 Loader、封面、下载，强化模组名和原站链接），还是必须在应用内完成“能不能装”的发行源？两条路线的工作量差一个数量级。
2. **“仅含服务端”要哪一种语义？** 只保留 `server_side=required`，还是继续把 optional 算进去？Modrinth 上这两个选择差大约 2,165 条，而且和 CurseForge 的 `has_server` 不可比。
3. **全平台页是主页还是橱窗？** 若是主页，每平台 12 条加平台内排序就是正式契约，应停止承诺全局检索。若只是橱窗，默认入口就应改到单平台，而不必先做全局排序器。
4. **PR #5 是否直接合并？** 当前语料的 source id 支持合并。阻塞条件只应是 B 站分组卡片的写入目标，不应是工作区、canonical 或 fallback 普查。
5. **B 站收藏的对象是视频还是分组？** 没有稳定 group id 时，写成视频是诚实的。分组按钮若表示“整包”，就会在下一条视频出现后看起来丢状态。这个取舍要先定，再谈 UI。
6. **个人库要不要在第一次合并时拒绝回退键？** 这批数据没有回退行。拒绝 ``platform-序号`` 可以防止以后错绑，也会让缺 ID 的新行不能收藏。接受现状则代码更少，风险推迟到下次 crawler 变形。
7. **canonical 构建失败时，sidecar 更新算不算成功？** 浏览不用 canonical。让它阻塞 pointer，用户看到的是“更新失败”。让它降级，离线 SQLite 会落后于正在看的数据。二选一即可，不必重写 pipeline。
8. **时间筛选还要不要公历字面量？** `2026` 和 `2026-09` 在写这个菜单的当月看起来像功能。下个月它就是错的预设。只留近 7/30/90 天，会让百科几乎整表落选，因为 1,158 条没有日期。需要决定空日期是隐藏还是单独成组。
9. **搜索框还承诺模组名和玩法吗？** 收回文案很便宜。把 B 站字幕、QQ、百科简介接进 desktop 搜索文档，会改变命中集合，也可能让短词误伤变多。不要两件一起做。
10. **legacy dashboard 的正式程度？** 现在不能删。可以决定：它只是冻结的兼容入口，desktopShell 是唯一可以加行为的面。不决定的话，下一次 UI 改动还会双写。
11. **计划以哪份数据为准？** `converted_output` 今天能复核。事实包里的 active snapshot 路径今天不能复核。在有人再次导入之前，不要写“用户打开服务就能看到这 73,522 条”。
12. **以后允许手工“这几条是同一个包”吗？** 现在不做。若答案是永远不做，个人库文档就应写死平台内身份。若答案是以后也许，键的旁边要留空，而不是先建 identity 服务。

---

## 11. Final Reviewer Notes

事实包是一份合格的约束文件。它没有把 PR #5、A/B 指标、旧搜索 20/20、canonicalReady 或 73,522 行写成不该写成的东西。我没有为了独立而否定这些边界。

我补上的是数量和连接：百科空洞是全体而不是部分；个人库的活风险在 B 站 latest bvid，不在 index fallback；全平台是六次页大小为 12 的查询；活动 dataRoot 今天不在磁盘上；百科 sidecar 的 desktop 生产者是 crawler 自己。

本次普查是读本地 JSON，不是测试通过，也不是浏览器验收。中文标题在控制台里曾乱码，计数不依赖标题文本。我没有逐条打开 mods/comments 文件判断正文是否为空，事实包对“文件数不等于内容完整”的限制仍然有效。B 站分组的召回和误并，我没有重测，也不建议重测。

若 Astra 只采纳一件事：先让现有卡片上的版本、Loader、服务端和搜索承诺与这批 sidecar 一致。其余路线，包括事实包留出来的那些 UNKNOWN，多数可以继续保持未决定。

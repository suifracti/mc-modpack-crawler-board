# MC Modpack Board — Full Project Context for Astra Pro

> 生成时间：2026-09-22  
> 目的：给后续 Astra Pro Master Plan 提供一份可验证的项目事实包。  
> 本文件是只读盘点结果；本轮没有修改功能代码、没有运行测试、没有 merge、没有 push、没有重新抓取数据。

## 事实标记与证据边界

- [CONFIRMED] 由当前仓库源码、Git 对象、GitHub API/CLI 或本机实际文件直接核实。
- [HISTORICAL] 来自历史提交、已合并阶段文档、归档 tag 或过往验证记录；不能自动升级为当前状态。
- [UNKNOWN] 当前材料不足以证明；不要把它当作 bug 或已完成能力。
- [PROPOSED] 仅是供 Astra 后续决策的方向，不是当前承诺。

证据优先级按当前项目规则处理：当前真实运行路径与本机数据 > 当前源码/接口契约 > 当前测试结果 > 项目文档 > 执行者陈述 > 推测。本文件没有读取 Raw/Archive 目录内容；历史冻结路线只通过 Git ref、现行文档和已知提交信息定位。

## 0. Executive Snapshot

- [CONFIRMED] 这是一个面向个人、本地运行的 Minecraft 整合包发现与整理工具，聚合 MC百科、Bilibili、BBSMC、XYEBBS、Modrinth、CurseForge 六个平台的本地采集数据。
- [CONFIRMED] 当前主产品形态是跨平台 Node.js localhost 浏览器服务，默认监听 127.0.0.1:8765；当前交付路径不再是 Electron EXE。
- [CONFIRMED] 当前 master 为 fa47ffe283c0c7b3ce6dcc5293060b68667b2f58，内容包含 PR #1～#4；PR #5 个人整合包库尚未进入 master。
- [CONFIRMED] 本机活动用户快照为 20260920084809555-578e8c，来源为 local-import / converted_output，canonicalReady=false，但六个平台 sidecar 都可读：
  - MC百科 1,484
  - Bilibili 936
  - BBSMC 1,802
  - XYEBBS 5,175
  - Modrinth 18,328
  - CurseForge 45,797
  - 合计 73,522 条平台记录；这是平台记录行数，不是跨平台去重后的整合包实体数。
- [CONFIRMED] 当前浏览器服务直接读取快照中的现代 sidecar；canonicalReady=false 不等于“没有数据”，而是当前这个本地导入快照没有 canonical.db。
- [CONFIRMED] Bilibili 当前正式浏览路径使用现有 author-scoped、标题证据驱动的启发式归组；它不是跨平台 canonical identity，也不是归档 A 最终候选的生产发布。
- [CONFIRMED] 个人库 PR #5 的代码已经在独立分支和远端，但 GitHub PR 仍 OPEN、未 merged、无 merge SHA；不能写成当前主线能力。
- [HISTORICAL] A/B、Truth Matrix 定稿和 production cutover 都属于已冻结/暂缓路线，不是本轮或当前主线的默认前置。

## 1. Current Git / PR State

### 仓库与 refs

- [CONFIRMED] 仓库：suifracti/mc-modpack-crawler-board。
- [CONFIRMED] origin：https://github.com/suifracti/mc-modpack-crawler-board.git。
- [CONFIRMED] 远端 master：fa47ffe283c0c7b3ce6dcc5293060b68667b2f58。
- [CONFIRMED] 当前主工作目录 D:\ai\work\我的世界整合包获取：
  - branch：codex/repository-cleanup
  - HEAD：34be1b25aa853f1d28f5546e08451245c36d583c
  - 盘点开始前 working tree clean
  - 它不是 master，而是已合并 PR #1 后仍保留的本地分支。
- [CONFIRMED] PR #5 独立 worktree：
  - 路径：C:\Users\Administrator\.codex\worktrees\desktop-dashboard\我的世界整合包获取
  - branch：feature/personal-library
  - HEAD：1d80a2c6e4ea50a47350fcb90809feb69e677a96
  - 跟踪 origin/feature/personal-library
  - 存在历史审查材料 personal-library-review.patch 未跟踪文件；它不是功能代码。
- [CONFIRMED] 当前本地 branch：
  - codex/repository-cleanup -> 34be1b2
  - feature/personal-library -> 1d80a2c
  - master -> fa47ffe
- [CONFIRMED] 当前远端 branch 主要为 origin/master、origin/feature/personal-library；origin/HEAD 指向 origin/master。

### 最近主线

主线 first-parent 最近重要提交：

| ref/commit | 状态 | 含义 |
| --- | --- | --- |
| fa47ffe | [CONFIRMED] 当前 master | 合并 PR #4，恢复旧 HTML 的浏览器 dashboard 视图 |
| ee30605 | [CONFIRMED] 已在 master | 恢复浏览器 dashboard 筛选与工具 |
| d446673 | [CONFIRMED] 已在 master | 合并 desktop dashboard browser service |
| 8352204 | [CONFIRMED] 已在 master | 合并 PR #1 repository cleanup |
| 1d80a2c | [CONFIRMED] 不在 master | PR #5 persistent personal modpack library |

### PR #5 实际状态

- [CONFIRMED] PR：#5，标题 feat: add local personal modpack library。
- [CONFIRMED] base：master @ fa47ffe283c0c7b3ce6dcc5293060b68667b2f58。
- [CONFIRMED] head：feature/personal-library @ 1d80a2c6e4ea50a47350fcb90809feb69e677a96。
- [CONFIRMED] GitHub 状态：OPEN，非 draft，mergeCommit=null。
- [CONFIRMED] PR URL：https://github.com/suifracti/mc-modpack-crawler-board/pull/5。
- [CONFIRMED] 结论：IMPLEMENTED / OPEN / NOT_IN_MASTER。
- [CONFIRMED] 本轮没有 merge，也没有改 PR #5。

### Tags 与历史 refs

- [HISTORICAL] 归档 refs 包括 archive/2026-09-20/fix/phase3gf-f3a-runtime、archive/2026-09-20/integration/phase3gf-ab-v2、archive/2026-09-20/cutover/frontend-v2-phase3d-production 等。
- [HISTORICAL] 这些 tag 用于保留阶段现场，不能据此说 A/B 或 production cutover 已成为当前 master。
- [CONFIRMED] v1.0.0-verified 也是历史 tag，不是当前浏览器服务发布证明。

## 2. Product Goal

- [CONFIRMED] 目标是让个人在本地发现、搜索、筛选、比较和查看 Minecraft 整合包，保留各平台原始来源入口。
- [CONFIRMED] 当前产品不是平台官方客户端、不是公共服务、不是数据分发站，也不声明和 MC百科、Bilibili、Mojang、Microsoft 或作者有官方关系。
- [CONFIRMED] 数据采集建议低频、个人学习和本地整理使用；项目文档明确禁止高频抓取、绕过限制、完整数据再分发和商业使用。
- [CONFIRMED] 产品核心价值是“找包 → 判断版本/Loader/服务端证据 → 看模组/评论/统计 → 打开原站或下载入口”。
- [UNKNOWN] 下一阶段是否以个人库、更新提醒、安装管理或更强的跨平台发现为第一目标，当前没有产品决策；不要把历史任务书中的候选功能当作已批准路线。

## 3. Current Architecture

### 正式运行形态

- [CONFIRMED] 前端：apps/web 的 TypeScript/Vite，desktop build 入口为 apps/web/desktop.html，输出 build/desktop/frontend。
- [CONFIRMED] 服务端：apps/desktop/server.cjs，Node 内置 HTTP server，只监听本机默认 127.0.0.1:8765。
- [CONFIRMED] 浏览器端通过同源 fetch、EventSource/SSE 访问窄 API；浏览器没有 Node 或文件系统权限。
- [CONFIRMED] Python 仍负责既有采集脚本和 collector worker；Node 只负责服务、任务编排、快照和 API。
- [CONFIRMED] 用户可写数据默认位于系统用户数据目录，不写入仓库代码目录；Windows 默认是 %APPDATA%/MCModpackBoard/data，macOS 是 ~/Library/Application Support/MCModpackBoard/data，Linux 是 $XDG_DATA_HOME/MCModpackBoard/data 或 ~/.local/share/MCModpackBoard/data。

### 组件关系

    start_browser_service.*（先构建 desktop frontend）
      -> apps/desktop/server.cjs
        -> DataStore + UpdateManager + Python collector_worker.py
        -> apps/web/desktop.html
          -> desktopMain.ts
            -> browserApi.ts + desktopShell.ts
              -> shared normalisation/search + per-platform renderers/adapters

- [CONFIRMED] legacy static dashboard 仍由 apps/web/src/main.ts、legacyAdapter.ts、legacy/dashboard.legacy.js 和 web/ 相关资源支持；它是兼容/旧 HTML 路径，不等于 browser service 的 desktop.html 入口。
- [CONFIRMED] apps/desktop/main.cjs、preload.cjs 和 Electron 相关测试仍保留作历史参考，但当前启动文档和 master 交付路径不调用 Electron。
- [CONFIRMED] pipeline/ 的 canonical SQLite、adapters 和 exporters 仍是采集/离线预览的重要路径；browser service 的本地导入快照可以只保留 sidecar，canonicalReady 可以为 false。

## 4. Runtime Data Flow

### 浏览与读取

1. [CONFIRMED] 启动器构建 apps/web 的 desktop bundle；server.cjs 读取 build/desktop/frontend。
2. [CONFIRMED] server 启动时初始化 DataStore，读取 dataRoot/active.json，再读取 snapshots/<snapshotId>/manifest.json。
3. [CONFIRMED] DataStore 从 snapshots/<snapshotId>/data 中按平台选择现代 sidecar；可读取 mcmod_data.js、bili_data.js、bbsmc_data.js、xyebbs_data.js、modrinth_data.js、curseforge_data.js，并缓存解析/normalise 结果。
4. [CONFIRMED] 浏览器先请求 /api/state，再按平台请求 /api/platforms/:platform/records；服务端先在完整 normalized collection 上搜索/筛选/排序，最后分页。
5. [CONFIRMED] 详情由当前记录 raw 加平台 version adapter、图片/评论 sidecar和原站链接生成；外链只允许 http/https。

### 更新

    用户点击更新
      -> POST /api/updates
      -> UpdateManager.start(platform)
      -> DataStore.prepareUpdateWorkspace()
      -> incoming/<jobId> 隔离目录
      -> collector_worker.py
      -> 复制单个平台 crawler 到 _collector 并 runpy 执行
      -> crawler_output/<raw>.json
      -> converted_output/data/<modern sidecar>
      -> build/desktop_update_result.json
      -> snapshot_pipeline.py
      -> build/desktop_snapshot_manifest.json
      -> DataStore.validateStage()
      -> snapshots/.incoming-<id>
      -> 原快照数据/原始 JSON 保留并叠加本次平台结果
      -> 原子写 active.json
      -> 浏览器收到 SSE data/status/log

- [CONFIRMED] worker 使用显式 platform、workspace、source-root、limit/pages/until 参数，不调用 monolithic crawler 的 --auto-convert。
- [CONFIRMED] worker 通过 MC_DESKTOP_WORKSPACE 和 MC_DESKTOP_COLLECTION_RESULT 把输出路径/采集结果合同传给 crawler；脚本的 __file__ 不再决定生产快照位置。
- [CONFIRMED] 成功合同要求 crawler 回报 status、requestCompleted、fetchedCount、pages、truncated、failedRequests、errors、noChangeConfirmed 等信息。
- [CONFIRMED] 非 success_no_change 时，worker 还要求本轮 raw 和 modern sidecar 实际存在、非空并在本轮写入；仅旧 sidecar 非空不能证明更新成功。
- [CONFIRMED] validateStage 再次拒绝缺少合同、请求未完整、分页截断、失败请求、空 raw、空 sidecar 或未生成预期 modern sidecar 的阶段。
- [CONFIRMED] canonical.db 只有在隔离 workspace 中六个平台 raw 都可用时由 snapshot_pipeline 构建；失败不应触碰现有活动快照。
- [CONFIRMED] active pointer 是提交边界。准备、runner、验证和 pointer 切换前都检查取消；一旦 pointer commit 开始，cancel 返回 commit_started，不能承诺取消成功。
- [CONFIRMED] UpdateManager 只允许一个活动任务；shutdown 等待任务落定。
- [CONFIRMED] 失败、取消或进程退出前没有成功切换 pointer 时，旧 active snapshot 保留；未选择更新的平台从旧 snapshot 复制保留。

### 本地导入

- [CONFIRMED] POST /api/data/import 接收用户输入的本地目录路径，DataStore 只复制识别到的安全 sidecar/raw 文件，不执行被导入目录中的 JavaScript。
- [CONFIRMED] 导入会生成 source=local-import 的新 snapshot；本机当前活动快照就是这种路径。
- [CONFIRMED] 当前导入路径可以得到有效 sidecar 而 canonicalReady=false；它不代表 pipeline canonical DB 已构建。

## 5. Platform Capability Matrix

六个平台共享“标题、作者、版本、Loader、分类、时间、封面/图片、外链/下载、平台指标、原始 raw”的部分字段，但实际契约不同。下表描述当前代码和本机 sidecar 中确实存在的能力，不表示字段在六个平台都完整或语义相同。

| 平台 | 数据来源与处理 | 稳定 source id | 当前字段/能力 | 当前明确缺失或边界 |
| --- | --- | --- | --- | --- |
| MC百科 | mcmod_full_crawler.py；MCModAdapter；StructuredMCModExporter -> mcmod_data.js；另有 mods/comments lazy sidecars | mid | title、中英文名/旧名、author、type/mold、MC 版本、Loader（很多记录为空）、categories/tags、封面字段、views/score/recommendations/favorites/comments、votes、trendStats、environmentClaims、previewMods/includedModNames/includedModsCount、原站与版本入口 | 当前 adapter 明确把 download_links 置为空；服务端多数是 unknown/no evidence；部分记录没有封面/版本/模组细节；独立评论只对 MCMod 有读取实现 |
| Bilibili | bilibili_crawler.py；BilibiliAdapter -> bili_data.js | bvid | title、author、desc、bvid/url、mc_version/all_versions、pack_version、Loader、pic、download_links、views/danmaku/likes/coins/favorites/reply/share、pub time、QQ 群、提取码、置顶评论、字幕摘要/文本、mod_count、group version note | 没有当前独立评论 sidecar API；没有完整模组列表；分类通常为空；版本记录主要是视频/群内线索，不等价于官方 release registry |
| BBSMC | bbsmc_crawler.py；BbsmcAdapter -> bbsmc_data.js | project_id；缺失时 slug/旧 fallback | title/author/description、project_id/slug/url、MC 版本/all_versions、Loader/categories、icon/featured_gallery/gallery、versions_data、download_links、downloads/followers、has_server、created/modified time | 当前 sidecar没有独立评论和模组清单；字段完整度依赖 BBSMC 返回的版本/文件数据；服务端事实不一定有独立证据 |
| XYEBBS | xyebbs_crawler.py；XyebbsAdapter -> xyebbs_data.js | project_id；缺失时当前 adapter 使用 index fallback | title/author/description、project_id/slug/url、english_name、MC 版本/all_versions、Loader/categories、head/icon、download_links、releases_data、downloads/likes/views/comments、source_meta（sourceUrl/videoUrl/license/openSourceUrl/issueUrl 等） | 当前 sidecar没有独立评论/模组清单；release 明细可能为空；下载清洗会排除 QQ 群等非下载链接 |
| Modrinth | modrinth_crawler.py；ModrinthAdapter -> modrinth_data.js | project_id；其次 slug；缺失时 index fallback | title/author/description、project_id/slug/url、MC 版本/all_versions、Loader/categories、client_side/server_side/env_display、icon/gallery、downloads/followers、download_links、source_meta/license；支持 Modrinth 项目/文件入口 | 当前没有评论和整合包模组清单；gallery/版本文件完整度受当前 crawler 输出限制；server 仍需区分平台字段与推断 |
| CurseForge | curseforge_full_crawler.py；CurseForgeAdapter -> curseforge_data.js | project_id；其次 slug；缺失时 index fallback | title/author/description、project_id/slug/url、MC 版本/all_versions、Loader/categories、icon/gallery、downloads/followers、download_links、source_meta(game_id/main_file_id) | 当前没有评论和整合包模组清单；样本 gallery 可以为空；服务端字段不是所有记录都有可靠独立证据 |

### 平台字段的共同语义边界

- [CONFIRMED] 版本来源是平台字段的不同组合：MCMod 主要是 mcVersions，其他平台通常是 all_versions 加 mc_version。
- [CONFIRMED] Loader 和分类不是统一枚举；Modrinth/CurseForge 还有平台分类标签映射，不能把文本相同当作语义完全相同。
- [CONFIRMED] 图片来源是平台 raw 中的 cover/icon/pic/gallery/head 等字段；缺图时 desktopShell 使用平台 SVG fallback。图片不会因为没有 canonical.db 就自动生成。
- [CONFIRMED] 下载/原站入口来自 url 和 download_links；网盘名称、URL、type 用于渠道筛选，辅助识别不等于下载链接事实。
- [CONFIRMED] “服务端”在 normaliseRecord 中优先读取 structured environmentClaims/server_side；旧 has_server 只会被标作 inferred；缺字段显示 unknown。渲染器中的 badge 仍会按各平台 legacy 字段显示，不能把 badge 当作完全同等级证据。
- [CONFIRMED] 当前没有全平台统一评论、统一模组详情或统一版本发布史；详情页会显示“未知/没有独立文件”，不会凭空补齐。

## 6. Current User-Facing Features

### 浏览

- [CONFIRMED] 全平台首页/总览、六个平台导航、平台记录数和当前快照状态。
- [CONFIRMED] 普通卡片视图；平台 rich renderer 卡片；紧凑视图；MC百科专业表格。
- [CONFIRMED] Bilibili 两种视图：同包聚合和视频平铺。
- [CONFIRMED] 全平台关键词下会展示各平台当前已载入页面的首批匹配结果；这不是一个全局去重 identity 结果集。
- [CONFIRMED] 卡片支持封面 lazy load、平台标识、摘要、版本/Loader chips、平台指标、部分下载入口、详情和对比入口。
- [CONFIRMED] 卡片对比 tray 和对比面板存在，可比较作者、Minecraft、Loader、分类、服务端显示和平台指标。
- [CONFIRMED] 页面支持浅色/深色主题状态；desktop.html 默认 data-theme=light，但旧 theme 测试历史上有默认 dark 的旧路径证据，不能把两条路径混为一谈。

### 详情

- [CONFIRMED] 详情 panel 展示标题、作者、图片画廊、Minecraft/Loader/更新时间/服务端摘要、来源证据、平台指标。
- [CONFIRMED] 有版本详情 view model 和六平台 version adapter；版本条目可显示版本名、日期、MC 版本、Loader、changelog 和文件链接。
- [CONFIRMED] 有平台原站、版本详情、下载/渠道外链；外链只接受 http/https。
- [CONFIRMED] MCMod 有独立 comments/<mid>.js 或 .json 读取路径；其他平台当前 API 返回没有独立评论文件。
- [CONFIRMED] 详情会读取记录中的简介、置顶评论、版本列表和模组字段，并对 HTML/文本做转义；模组/发布记录的“完整度”由当前 raw/sidecar 决定。
- [CONFIRMED] 图片支持 cover/gallery/comment image 的放大 lightbox；链接无效时显示 fallback 或未知。

### 采集与工具

- [CONFIRMED] 顶部有数据目录导入、快照状态、变动审计入口。
- [CONFIRMED] 更新面板允许选择单个平台、limit/pages/until，显示 phase、处理数量、日志、成功/失败/取消状态。
- [CONFIRMED] API 通过 SSE 推送更新 status/log/data。
- [CONFIRMED] 页面缺少可用快照时显示空状态和选择数据目录入口；不会把空数据伪装成成功。

### 当前不应误写成已完成

- [UNKNOWN] 没有本轮真实鼠标/浏览器 GUI 逐项验收；HTTP 层测试不能证明所有点击、滚动、视觉布局和重启后浏览器状态。
- [CONFIRMED] “个人库”只有 PR #5 分支版本，不属于当前 master 用户入口。
- [CONFIRMED] 没有当前生产级跨平台 canonical 去重视图；Bilibili 同包聚合是单平台视频聚合。

## 7. Search / Filter / Sort

### 当前 browser service 搜索契约

- [CONFIRMED] 当前 desktopShell 的记录过滤最终由 apps/desktop/lib/data-store.cjs 调用 apps/shared/search-contract.cjs。
- [CONFIRMED] 搜索按空白拆分 term、转小写；每个 term 必须在至少一个搜索字段中出现。
- [CONFIRMED] MCMod search document 当前包含 title、typeName、former titles、author、categories、tags、included mod names、description/comment 参数位、Loader、MC versions；但 desktop DataStore normaliseRecord 调用时没有额外传入 desc/comment，不能把 legacy search 的全部字段当成当前 server path 已接通。
- [CONFIRMED] Bilibili/BBSMC/XYEBBS/Modrinth/CurseForge 的 shared document 主要包含 title/别名或 slug、author、description、mc_version、Loader、categories；不同平台的 comments/mods/QQ/subtitle 不会自动进入同一搜索字段。
- [CONFIRMED] legacy apps/web/src/search 仍有 legacy_compat/advanced、search reason 和更丰富的映射，但 desktop.html 当前入口不是直接调用旧 main.ts 的全量搜索状态机。
- [HISTORICAL] docs/SEARCH_CONTRACT.md 记录过旧静态浏览器环境的 20/20 搜索等价验证；那是旧路径 evidence，不等于当前 desktop API 全字段搜索已完成。

### 当前筛选

- [CONFIRMED] Minecraft 版本：按 normalized record.versions 精确匹配；MCMod 使用 mcVersions，其他平台合并 all_versions 与 mc_version。
- [CONFIRMED] Loader：按 normalized record.loaders 精确匹配。
- [CONFIRMED] 分类：按 record.categories 包含匹配。
- [CONFIRMED] 下载/来源渠道：百度、夸克、123、蓝奏、迅雷、Modrinth、CurseForge；XYEBBS 的 official 代表有原站 URL。实际可选值由当前 searched collection 中存在的链接计算。
- [CONFIRMED] 时间：近 7 天、近 30 天、近 90 天、2026 年、2026 年 9 月；时间字段按 raw timestamps 或 normalized updatedAt 解释。
- [CONFIRMED] 仅含服务端：structured status required/optional/supported 或 raw has_server=true；unknown 不会通过。
- [CONFIRMED] 个人状态筛选 favorite/want_to_play/played 只在 PR #5 overlay 中存在，不在当前 master。
- [CONFIRMED] 筛选在分页前执行；接口返回 total、availableVersions、availableLoaders、availableCategories、availablePans 和当前页 records。
- [CONFIRMED] UI 每页选项为 24/48/100；服务端允许 1～500 的 pageSize。

### 当前排序

- [CONFIRMED] 非 Bilibili：最近更新、下载最多、浏览最多、关注最多、点赞最多、评论最多、创建时间、名称 A-Z。
- [CONFIRMED] Bilibili：最新发布、播放最多、点赞最多、收藏最多、投币最多、分享最多、评论最多、弹幕最多。
- [CONFIRMED] 当前没有评分排序、个人备注排序、最近查看排序或个人库更新时间排序。

## 8. Platform-Specific Features

### Bilibili

- [CONFIRMED] 936 条当前视频记录；平铺视图保留视频级记录。
- [CONFIRMED] 同包聚合调用 apps/web/src/domain/bilibiliGrouping.ts；输入为 bvid/title/author，作者 scope 内寻找稳定 identity run，保留 episode residue，并有 exact/substring fallback。
- [CONFIRMED] 代码明确禁止跨 uploader 合并；下载 URL、QQ 群不会作为归组依据。
- [CONFIRMED] 聚合卡片会保留最新视频、历史视频、聚合播放/点赞/投币/收藏/弹幕/评论/分享统计、网盘链接、提取码、QQ群、群内最新版本提示和字幕内容。
- [CONFIRMED] 这是当前正式 desktopShell/legacy bridge 共享的 grouping implementation，但只是启发式，不是跨平台 identity。
- [HISTORICAL] A 的最终 runtime candidate、独立 safety audit 和 B integration 都在 archive tag，未进入当前 master；不能用它们的 Recall/FM 门禁替代当前产品验收。

### MC百科

- [CONFIRMED] MC百科专业表格列包括整合包、浏览、热度/推荐、趋势、投票、评论/收藏、包含模组、来源/个人入口等；trendStats 和 votes 来自 sidecar。
- [CONFIRMED] MC百科有 StructuredMCModItem mapper、selectors、tableColumns、sparkline、version adapter。
- [CONFIRMED] 当前本机快照有 mods 目录 1,484 个文件、comments 目录 1,417 个文件；这说明 lazy detail 资料存在，但不代表每条都有非空完整内容。
- [CONFIRMED] MCMod version adapter 默认目标是 version/<mid>.html，并优先使用明确 versionUrl/version_url；不要把普通原站 URL 自动当成版本页。
- [CONFIRMED] MCMod crawler/adapter 的 canonical bundle 可以记录 included mods、environment claims、trend/vote/metrics；当前 sidecar中有 previewMods/includedModNames，但不同记录的完整度差异很大。
- [UNKNOWN] 当前所有 1,484 条 MCMod 是否都能显示完整图片、模组、评论和版本历史；本轮没有逐条扫描。

## 9. Collection & Update Pipeline

### 入口与 crawler

- [CONFIRMED] 六个现有 crawler 文件：mcmod_full_crawler.py、bilibili_crawler.py、bbsmc_crawler.py、xyebbs_crawler.py、modrinth_crawler.py、curseforge_full_crawler.py。
- [CONFIRMED] 老的多平台聚合爬虫入口多平台聚合爬虫_v1.0.py 仍在仓库，但现代 desktop update worker 按平台调用现有 crawler，不调用它的 --auto-convert。
- [CONFIRMED] crawler 原始输出写到隔离 workspace/crawler_output；现代 sidecar 写到隔离 workspace/converted_output/data；采集结果合同写到 workspace/build。
- [CONFIRMED] MC百科现代 mcmod_data.js 是 StructuredMCModExporter 从 canonical.db 导出的独立契约；legacy table_rows.js/app_data.js 仍为兼容路径，不应被旧文件存在掩盖现代导出缺失。

### 成功、失败、取消

- [CONFIRMED] success_update：请求/分页合同通过，raw/sidecar 非空且本轮变化，验证通过后才创建新 snapshot 并切 active pointer。
- [CONFIRMED] success_no_change：crawler 明确确认请求完成、没有失败/截断且无变化有效；不能只凭缓存文件存在。
- [CONFIRMED] failed：合同缺失、请求未完成、分页截断、失败请求、空结果、缺 raw/sidecar、sidecar 解析失败或 canonical 构建失败；旧 active pointer 保留。
- [CONFIRMED] cancelled：取消在准备、runner、验证阶段会阻止提交并保留旧 pointer；pointer commit 开始后不再允许取消。
- [CONFIRMED] 未选择的平台在新 snapshot 中从旧 snapshot 复制；单平台更新不是清空其他五个平台。

## 10. Snapshot / Persistence Model

- [CONFIRMED] dataRoot 下的核心结构是 active.json、snapshots/、incoming/；活动内容位于 snapshots/<snapshotId>/data，原始采集位于 snapshots/<snapshotId>/crawler_output。
- [CONFIRMED] snapshot commit 使用临时 .incoming-<id> 目录、rename 成最终 snapshot 目录，再原子写 active.json。
- [CONFIRMED] 新 snapshot 会复制上一份 data/raw/canonical，再覆盖本轮平台输出；失败清理未提交的临时 snapshot。
- [CONFIRMED] 当前 desktop DataStore 的 cleanupWorkspace 只允许删除 incoming 下的 staging workspace；当前代码没有独立的 snapshot retention/cleanup 策略。
- [CONFIRMED] 因此当前已有 snapshot 可能持续占磁盘；未来若新增 cleanup，必须显式排除个人数据和 active pointer。
- [CONFIRMED] 当前 master 没有个人库文件/接口；PR #5 的个人文件设计放在 dataRoot 根部，不在 snapshots 或 incoming 内，理论上不会被 snapshot overlay 覆盖。
- [UNKNOWN] 未来是否要保留多少历史 snapshots、是否提供用户回滚入口、是否为个人库做迁移/备份，尚无产品决策。

## 11. Personal Library

### PR #5 设计（不在 master）

- [CONFIRMED] PR #5 新增 apps/desktop/lib/personal-library.cjs，文件名 personal-library.json。
- [CONFIRMED] 默认位置是 dataRoot/personal-library.json；dataRoot仍是系统用户数据目录，不是 snapshot data 目录。
- [CONFIRMED] key 是 platform:sourceId，平台先经 assertPlatform 校验，sourceId 要求非空、最长 256、拒绝 slash/backslash/NUL。
- [CONFIRMED] 状态字段：favorite、wantToPlay、played、rating（1～5 或 null）、note（最多 20,000 字符）、updatedAt。
- [CONFIRMED] 写入只接受白名单字段，JSON body 上限 64 KiB，普通文本 note 使用 HTML 转义后的页面输出，不作为可信 HTML 注入。
- [CONFIRMED] 文件写入为同目录临时文件 + rename，并串行排队写入。
- [CONFIRMED] API 只有 GET /api/library 和 PATCH /api/library/:platform/:sourceId；浏览器端没有任意文件写接口。
- [CONFIRMED] PR5 UI overlay 将个人收藏放入卡片、compact、MCMod 表格、Bilibili grouped/flat rich card 和详情 panel，并增加 favorite/want_to_play/played 筛选；评分和备注在详情中修改。
- [CONFIRMED] PR5 测试路径覆盖：写入状态、个人筛选、导入新 snapshot 后同 key 恢复、停止/重启服务后恢复、修改状态。
- [CONFIRMED] PR5 代码与 snapshot 数据分离，DataStore 的 snapshot copy/commit/import 不复制或清理 dataRoot/personal-library.json。

### 稳定性边界

- [CONFIRMED] 正常导出记录拥有平台稳定 ID：MCMod mid、Bilibili bvid、其他平台优先 project_id，再 slug。
- [CONFIRMED] 当前 normaliseRecord 和 adapters 都存在 index-derived fallback；例如缺少 project_id/slug 时可能使用 idx+1，Bilibili/MCMod 也有各自 fallback。
- [UNKNOWN] 当前活动快照中有多少记录使用了 fallback；本轮没有为此扫描全部记录。
- [CONFIRMED] 因此 platform:sourceId 对正常稳定源 ID 足够稳定，但对缺 ID 且依赖列表位置的记录，重新排序、删行或采集器行为变化可能使个人状态关联退化。
- [CONFIRMED] 这个 key 只保证平台内 source identity，不做跨平台同包归并，也不碰 canonical/A/B identity 工程。
- [CONFIRMED] 当前本机 dataRoot 没有 personal-library.json；结合 PR #5 未合并，只能说明当前 master 运行现场尚未产生个人库文件，不能说明 PR5 设计不可用。

## 12. Current Local Data

### 用户服务数据

- [CONFIRMED] 默认 Windows dataRoot：C:\Users\Administrator\AppData\Roaming\MCModpackBoard\data。
- [CONFIRMED] active.json 指向 snapshotId 20260920084809555-578e8c，更新时间 2026-09-20T08:48:13.583Z。
- [CONFIRMED] manifest.json：
  - source=local-import
  - importedFrom=converted_output
  - updatedPlatforms=mcmod,bilibili,bbsmc,xyebbs,modrinth,curseforge
  - canonicalReady=false
  - 六平台 count 与 Executive Snapshot 相同
- [CONFIRMED] 活动 snapshot 的 data 目录六个现代 sidecar 均能被当前 platforms.cjs 读取，未报解析错误。
- [CONFIRMED] dataRoot 顶层当前有 incoming、snapshots、active.json；没有 personal-library.json。

### 仓库工作目录本地数据

- [CONFIRMED] D:\ai\work\我的世界整合包获取\converted_output/data 也可读取相同六平台记录数；它不是 Git tree 中的 tracked source data。
- [CONFIRMED] D:\ai\work\我的世界整合包获取\crawler_output 有本地 raw：
  - bbsmc_modpacks.json 4,360,921 bytes，2026-09-17
  - bilibili_modpacks.json 1,698,727 bytes，2026-09-17
  - curseforge_modpacks.json 63,514,631 bytes，2026-09-14
  - mcmod_modpacks.json 4,043,634 bytes，2026-09-17
  - modrinth_modpacks.json 28,686,724 bytes，2026-09-14
  - xyebbs_modpacks.json 6,977,954 bytes，2026-09-17
  - MCMod 另有 mcmod_details_cache.json、mcmod_full_details.json。
- [CONFIRMED] 本地数据更新时间不能代表现在仍能联网重新采集；本轮没有全网抓取。
- [UNKNOWN] 这些本地快照是否就是用户当前日常使用的唯一数据源；可以确认服务默认会读 dataRoot，但用户也可以通过 /api/data/import 选择其他目录。

## 13. Tests & Existing Evidence

本轮只整理现有证据，没有重新执行测试矩阵。

| 证据 | 状态 | 证据来源与边界 |
| --- | --- | --- |
| Node desktop tests | [HISTORICAL] PR5 报告 9/9 | 针对 PR5 commit 的既有交接；本轮未重跑 |
| Web typecheck | [HISTORICAL] PASS | PR5 交接中的既有验证；本轮未重跑 |
| Frontend build | [HISTORICAL] PASS | PR5 交接中的既有验证；本轮未重跑 |
| Vitest | [HISTORICAL] 11 files / 80 tests PASS | docs/REPOSITORY_CLEANUP.md 的 cleanup 基线 evidence，不能自动当作当前 master 全量重验 |
| Python collector integration | [HISTORICAL] 1 个测试逐平台覆盖六平台受控请求并通过 | PR5 前桌面返修交接；不等同于六平台真实联网成功 |
| Browser service HTTP | [HISTORICAL] health/import/records 和 PR5 个人库场景覆盖 | test/browser-service.test.cjs；主要是 HTTP/API，不是实际 GUI 点击 |
| Update manager | [HISTORICAL] 成功、失败保留旧快照、准备/验证/提交边界取消覆盖 | test/update-manager.test.cjs；未在本轮重跑 |
| 301 条完整过滤 | [HISTORICAL] 已有回归证明先过滤后分页 | test/data-store.test.cjs；不是本轮新证据 |
| Modrinth 最小真实采集 | [HISTORICAL] 便携目录 --limit 1 曾成功产生 raw/sidecar/manifest | 旧桌面返修交接；不能替代当前 GUI 或全量更新验收 |
| BBSMC 最小真实采集 | [HISTORICAL] 曾退出 0 但未取得项目、无输出 | 旧桌面返修交接；这是失败语义边界 evidence，不能写成成功更新 |
| 旧静态搜索契约 | [HISTORICAL] docs 记录过真实浏览器 20/20 等价 | 旧 legacy path；不证明当前 desktop DataStore 搜索字段全覆盖 |
| GUI 点击/视觉/重启 | [UNKNOWN] 未有本轮真实浏览器逐项验收 | 不用 HTTP 进程响应冒充 GUI PASS |
| 当前活动 snapshot | [CONFIRMED] sidecar 六平台可读 | 本机只读检查，不是测试通过证明 |

重要区别：历史 test PASS 说明对应源码和场景的已知行为，不等于当前 master、PR5 或用户机器上的完整产品验收。A/B 的历史 Recall/FM/under-merge 门禁也不能替代本产品浏览器服务验收。

## 14. Source Code Map

| 路径 | 作用 | 谁调用 | 依赖 | 当前状态 |
| --- | --- | --- | --- | --- |
| apps/desktop/server.cjs | localhost HTTP/SSE 服务、静态资源、API 路由、启动/停止 | launcher、npm start | DataStore、UpdateManager、worker | [CONFIRMED] master 正式入口 |
| apps/desktop/lib/data-store.cjs | active pointer、snapshot 读写、导入、完整过滤、评论/审计读取 | server、UpdateManager | platforms.cjs、fs | [CONFIRMED] master 正式路径 |
| apps/desktop/lib/update-manager.cjs | 单任务编排、取消、失败、shutdown 等待 | server | DataStore、process-runner | [CONFIRMED] master 正式路径 |
| apps/desktop/lib/platforms.cjs | 六平台 config、sidecar parser、normaliseRecord、环境证据、URL/log 辅助 | DataStore/server | shared search contract | [CONFIRMED] master 正式路径 |
| apps/desktop/collector_worker.py | 单平台隔离执行、结果合同、raw/sidecar touched 检查 | server -> UpdateManager | Python crawler、desktop_collection_contract.py | [CONFIRMED] master 正式路径 |
| desktop_collection_contract.py | crawler 写入 request/page/fetch/error/no-change 合同 | worker 与六个平台 crawler | Python 标准库 | [CONFIRMED] master 正式路径 |
| apps/desktop/snapshot_pipeline.py | 阶段完整性检查、raw/sidecar hash、可选 canonical.db、manifest | collector_worker | pipeline.build_canonical_db | [CONFIRMED] master 正式路径 |
| apps/web/desktop.html | desktop browser 页面 HTML 入口 | Vite/server static | desktopMain.ts | [CONFIRMED] master 正式入口 |
| apps/web/src/desktopMain.ts | 加载 CSS、browserApi、desktopShell | desktop.html | browserApi、desktopShell | [CONFIRMED] master 正式入口 |
| apps/web/src/browserApi.ts | 同源 fetch/EventSource API 封装 | desktopMain/desktopShell | browser HTTP API | [CONFIRMED] master 正式路径 |
| apps/web/src/desktopShell.ts | 当前 dashboard UI、加载记录、筛选、排序、详情、Bili/MCMod视图 | desktopMain | browserApi、renderers、version adapters | [CONFIRMED] master 正式路径 |
| apps/web/src/desktopShell.css | 当前 desktop dashboard 样式与旧 HTML parity 补丁 | desktopMain | CSS variables/legacy styling | [CONFIRMED] master 正式路径 |
| apps/web/src/platforms/*/renderer.ts | BBSMC/XYEBBS/Modrinth/CurseForge/Bili rich cards、MCMod renderer 相关 | desktopShell、legacy bridge | platform DTO/types | [CONFIRMED] master 正式路径之一 |
| apps/web/src/platforms/*/versionAdapter.ts | 六平台版本详情统一 view model | buildViewModel -> desktopShell/modal | raw platform DTO | [CONFIRMED] master 正式路径 |
| apps/web/src/domain/bilibiliGrouping.ts | 当前 Bili 单平台分组决策 | desktopShell、legacyAdapter | packName noise/normalization | [CONFIRMED] master 正式路径；启发式 |
| apps/web/src/legacy/legacyAdapter.ts | 将模块化搜索/筛选/渲染/版本控制器暴露给旧 dashboard | apps/web/src/main.ts | LegacySidecarRepository、legacy modules | [CONFIRMED] 兼容路径 |
| apps/web/src/legacy/dashboard.legacy.js | 旧 HTML dashboard 行为和布局 | main.ts / legacy build | bridge globals、web assets | [CONFIRMED] 兼容/历史产品路径，不能随意删除 |
| apps/web/src/search、filters、router、modals | 旧/模块化前端的搜索、筛选、路由、版本模态逻辑 | legacy bridge/main | domain types/mappers | [CONFIRMED] 仍被兼容路径使用；不是 desktop API 的唯一查询实现 |
| pipeline/adapters/*.py | raw JSON -> canonical bundle | build_canonical_db/run_v2_pipeline | canonical models/db | [CONFIRMED] 正式离线 pipeline |
| pipeline/build_canonical_db.py | canonical SQLite ingestion | run_v2/snapshot_pipeline | adapters、SQLite schema | [CONFIRMED] 可选/隔离正式步骤 |
| pipeline/exporters/*.py | canonical.db -> structured/legacy sidecars | staging/export pipeline | canonical DB | [CONFIRMED] 正式导出路径 |
| 六个平台 crawler *.py | 各平台请求/分页/解析/raw/sidecar | worker 或统一旧入口 | 网络、平台响应、本地缓存 | [CONFIRMED] 现有数据源 |
| start_browser_service.cmd/.command/.sh | 构建 desktop frontend 后启动 Node 服务 | 用户双击/终端 | Node/npm、Python | [CONFIRMED] 已在 master；不产生 EXE |
| pipeline/rollback*、cutover* | 历史/人工 pipeline 操作 | 人工命令 | pipeline、生成数据 | [HISTORICAL] 不属于浏览器服务自动路径 |
| converted_output/、crawler_output/ | 本地生成数据/原始缓存 | crawler、旧静态服务、导入 | 本地数据 | [CONFIRMED] 本机存在但不在 Git tracked source |
| apps/desktop/main.cjs、preload.cjs | Electron shell | 旧 Electron 路径 | Electron | [HISTORICAL] 当前 browser service 不调用 |
| tests/、pipeline/tests/、apps/*/test | 回归/契约/桌面 API 测试 | npm/pytest/人工 | 本地数据或 fixtures | [CONFIRMED] 测试资产存在；本轮未执行 |

## 15. Historical / Frozen Paths

### 已完成历史阶段

- [HISTORICAL] 从两个脚本/旧 HTML 起步，扩展为六平台 crawler。
- [HISTORICAL] 增加 canonical SQLite、统一模型、platform adapters、legacy exporters 和 TypeScript/Vite frontend。
- [HISTORICAL] 旧 HTML dashboard 的搜索/筛选/卡片/MCMod/Bili 视图被模块化，再在 PR #4 恢复到当前浏览器 dashboard。
- [HISTORICAL] Electron portable dashboard 曾是 PR #2 及其返修阶段的交付尝试，随后被 browser service 替代。
- [CONFIRMED] PR #1～#4 已合并；PR #5 当前仍 OPEN。

### A：3G-F runtime route

- [HISTORICAL] ref/tag：archive/2026-09-20/fix/phase3gf-f3a-runtime，相关候选 commit 曾包含 1bee6de、dd1f624、37ea9f6、9c51a557 等阶段。
- [HISTORICAL] A 关注 Bilibili grouping 的 under-merge/false-merge、known/expanded audit、holdout 和 26-case gate。
- [HISTORICAL] A 最终交接保留 28 个冲突关系 case 与 277 个未覆盖 holdout pair；BLOCKED 指独立安全证据不完整，不表示整个产品不能使用。
- [CONFIRMED] A 没有合并到当前 master；A 的审计指标不是当前 browser service 的 release certificate。

### B：integration route

- [HISTORICAL] ref/tag：archive/2026-09-20/integration/phase3gf-ab-v2，已停止、未进入 master。
- [CONFIRMED] B 不应被视为当前 production runtime 或新功能开发前置。

### 明确非当前主线

- [HISTORICAL] Truth Matrix 文件和 production cutover 脚本/manifest 仍在仓库或历史 refs 中，但当前 master 没有把它们当作本轮发布流程。
- [HISTORICAL] archive tag 名字中含 cutover 不等于当前用户机器已完成 production cutover。

## 16. Confirmed Issues

这里只列当前事实能证明、且有行为后果的问题；不把猜测写成 bug。

1. [CONFIRMED] PR #5 个人库尚未进入 master；当前 master 没有 personal-library.cjs、/api/library 和个人状态 UI。
2. [CONFIRMED] current desktop API search 与 legacy search contract 是两条路径；desktop DataStore 的 shared search 不会自动覆盖 legacy 的全部 desc/comments/QQ/subtitle/mod explainability 字段。
3. [CONFIRMED] 正常平台 ID 的稳定性依赖源记录提供 mid/bvid/project_id/slug；代码中存在 index fallback，fallback 记录重排时可能失去个人状态关联。当前 fallback 覆盖率未测。
4. [CONFIRMED] 活动本机快照 canonicalReady=false；当前服务可以工作，但任何依赖 canonical.db 的规划都不能假定在这个快照上成立。
5. [CONFIRMED] 当前 desktop DataStore 没有历史 snapshot retention/cleanup policy；长期更新可能增加磁盘占用，个人数据保护规则也尚未有单独 cleanup 设计。
6. [CONFIRMED] 真实浏览器 GUI 的启动、视觉、点击、详情滚动、服务重启等没有在本轮独立验收；已有 HTTP/单元测试不能覆盖这些全部行为。

## 17. UX Gaps

- [CONFIRMED] 当前没有个人库长期入口：没有独立“我的收藏/想玩/玩过”工作区、最近查看、最近修改、评分排序、备注搜索；这些只能在 PR5 overlay 中局部存在，且 PR5 未合并。
- [CONFIRMED] 六个平台详情字段不对称；只有 MCMod 当前有独立评论/模组 sidecar 读取，其他平台更多依赖 raw 摘要/版本/下载字段。
- [CONFIRMED] 卡片和 rich renderer 会截取部分下载链接、图库、分类或模组预览；详情对 full data 的展开能力受各平台 raw 契约影响。
- [CONFIRMED] “全部平台”结果以各平台当前页片段组成，不是可跨平台排序/去重的统一实体列表。
- [CONFIRMED] update panel 是工程状态面板，不是完整更新历史、重试策略或用户可解释的 per-platform diff 工作区。
- [CONFIRMED] 启动器要求本机 Node/npm 并在启动前构建前端；当前不是零依赖、双击即用的已打包应用。
- [UNKNOWN] 用户实际机器上的图片加载、宽屏/窄屏布局、系统字体和跨平台 launcher 体验尚未形成当前证据。

## 18. Technical Debt

- [CONFIRMED] 新 desktopShell、apps/web/src/domain、legacyAdapter、dashboard.legacy.js、web/旧 CSS/转换器和 pipeline exporter 之间存在兼容层与重复 DTO 映射。
- [CONFIRMED] normaliseRecord 是六平台 generic bridge，之后又由 platform rich renderer 做二次 legacyPackBase 转换；长期维护需要明确哪一层是字段契约源。
- [CONFIRMED] 当前服务仍需要现代 sidecar 与 legacy/兼容 sidecar 共存；删除 table_rows.js、app_data.js、旧 renderer 或 web assets 前必须重新核对调用关系。
- [CONFIRMED] crawler worker 通过复制脚本、修改 cwd、runpy 和环境变量接入既有 crawler，实际可维护性依赖每个平台遵守 desktop_collection_result contract。
- [CONFIRMED] snapshot manifest、desktop_update_result、raw JSON、现代 sidecar、canonical.db 的 provenance/版本关系仍是多种文件合同，不是一个统一数据库事务。
- [CONFIRMED] 个人库 PR5 是 schema=1 JSON 文件，没有迁移框架、备份/恢复 UI 或跨机器同步。
- [UNKNOWN] 当前 pipeline canonical model 是否足以支持未来真正跨平台个人库聚合；不能因为 canonical.db 存在就假设跨平台 identity 已完成。

## 19. Explicitly Deferred Scope

以下是当前明确不要自动展开的范围：

- [HISTORICAL/DEFERRED] 不重开 A/B Bilibili 归组审计，不把 A 的 28/277 转成当前产品 blocker。
- [HISTORICAL/DEFERRED] 不定稿 Truth Matrix，不做 production cutover，不改 production_state/manifest/cutover infra。
- [HISTORICAL/DEFERRED] 不重写 canonical identity，不启动新的跨平台归组工程。
- [HISTORICAL/DEFERRED] 不重做整个 UI，不把六个平台强行压成完全一致的字段模型。
- [HISTORICAL/DEFERRED] 不新增大量数据源，不做全网重新抓取，不把历史 GUI 返修任务升级成全项目重审。
- [HISTORICAL/DEFERRED] 不恢复 Electron EXE 作为当前交付目标。
- [PROPOSED] 后续是否优先个人库工作区、更新历史/提醒、搜索契约收敛或数据可靠性，交给 Astra 基于事实排序。

## 20. Open Product / Architecture Questions

这些问题当前没有足够事实直接回答，应由后续规划明确：

1. [UNKNOWN] PR #5 是否先合并后做个人库工作区；个人库工作区是否只做平台内 key，还是需要未来的人工关联/别名机制。
2. [UNKNOWN] 对缺少稳定 source ID 的记录，产品应接受 index fallback、增加平台专属稳定键，还是暂时禁止保存个人状态。
3. [UNKNOWN] canonicalReady=false 的本地导入是否是长期支持模式，还是只用于兼容历史快照；是否需要在 UI 中更明确区分。
4. [UNKNOWN] 更新成功的产品定义是否允许每个平台不同：成功无变化、部分分页、需要登录、空结果分别应如何呈现。
5. [UNKNOWN] 详情应优先补全哪些平台的评论、模组列表、图片和 release history；当前没有证据支持一次性全补。
6. [UNKNOWN] snapshot 保留数量、用户回滚入口、磁盘预算和个人库备份策略尚未定义。
7. [UNKNOWN] /api/data/import 的本地路径导入在个人产品中是否需要更严格的允许目录/交互确认；当前不是任意文件写入 API，但它是本机路径读取边界。
8. [UNKNOWN] 前端构建是否继续要求用户安装 Node/npm，还是未来提供平台 launcher/package；当前任务不包含打包方案决策。
9. [UNKNOWN] legacy static dashboard 是否长期保留为兼容模式，还是在已有替代证据后逐步收敛；当前不能直接删除。

## 21. Facts Astra Must Not Misinterpret

- [CONFIRMED] master 是 fa47ffe，不是旧 Handoff 中的 8352204；8352204 是 PR #1 merge 的历史节点。
- [CONFIRMED] 当前检查所在主工作目录是 codex/repository-cleanup @ 34be1b2，不是 master；PR #5 在另一个 feature/personal-library worktree。
- [CONFIRMED] PR #5 的 1d80a2c 代码实际存在并已推到远端，但 PR 仍 OPEN、没有 merge commit；“代码存在”不等于“主线已具备”。
- [CONFIRMED] 当前本机有 active snapshot 和六个平台数据；数据不在 Git tracked source 中，是 local-import / converted_output 生成的本地事实。
- [CONFIRMED] 73,522 是六个平台 sidecar 记录数之和，不是去重后的 73,522 个跨平台整合包。
- [CONFIRMED] canonicalReady=false 只表示这份活动导入快照没有 canonical.db；浏览器服务仍能通过 modern sidecar 浏览。
- [CONFIRMED] Bilibili 同包聚合只在 Bilibili 内按 author/title heuristic 形成展示组，不是全平台 identity，也不是 A 最终安全验收结果。
- [HISTORICAL] A/B 的 PASS、Recall、False Merge、26-case 或 under-merge 数字不能被抄成当前 master 的最终 runtime acceptance。
- [HISTORICAL] A 交接中的 28 个冲突关系和 277 个未覆盖关系表示安全证据限制，不表示整个产品不可用；本文件不把它们列为当前产品停用条件。
- [CONFIRMED] 旧 Electron/EXE 路径、旧 HTML、legacy bridge、pipeline cutover 工具仍可能在仓库中存在；存在不等于当前启动路径会调用。
- [CONFIRMED] 六个平台字段不是同构的；“支持六平台”不等于每个平台都有评论、模组、完整 release history、可靠服务端事实或相同下载语义。
- [CONFIRMED] 旧静态 HTML 搜索测试、Node API 测试、Vitest、Python controlled integration 和真实最小采集各自只证明自己的边界，不能拼接成一次未发生的全产品 GUI PASS。
- [PROPOSED] 任何未来 Master Plan 都应先明确要解决的用户行为和证据边界，再决定是否改代码；不要把本事实包中的建议性问题自动当成交付承诺。

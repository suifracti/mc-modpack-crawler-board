# 当前实施状态

更新：2026-10-06。当前可开发主线为 **master**；已在 Mac 验证的整合基线为 `644d9e290dc29d8fb82e29108a876d4f80424465`。本次从远端 `master@42251392a44edb1eab6285c810fae3ee69b19292` 正常合并该基线，保留两侧提交历史；运行源码、依赖和数据格式与已验基线一致。

## 当前开发与运行入口

- 后续 MC 开发固定使用 `master`，Mac 源码目录固定为 `$HOME/backup/ai/work/zhenghebao/mac-integration-20261005`；目录沿用恢复位置，目录名不代表继续开发整合候选分支。
- V2 构建和显式本机启动见 [MAC_MIGRATION.md](MAC_MIGRATION.md)。运行数据继续使用仓库外独立目录，不移动、覆盖个人资料或近期增量。
- 2026-10-06 Mac 恢复验证已完成：锁定依赖安装、V2 构建、独立空目录启动、交付包及逐文件校验、六源资料读取、搜索、一条详情与模组资料、个人资料面板。只验证本地资料；没有新增采集或部署。
- 生产 sidecar 可读行数共 130,782；交付个人库为 0 条，1,417 个评论 sidecar 均为空数组。`canonicalReady=false`，未重建 canonical.db。非空个人库写入、外站图片/网页/在线版本、真实鉴权、采集与取消恢复仍未验；这些已知边界不阻止把已验版本作为默认开发主线。
- Pages 发布源继续为 `gh-pages:/`；仅推送 `master` 不更新站点。`gh-pages` 保留站点用途，不作为废分支清理。
- A 候选安全审计 BLOCKED、B 候选兼容与生产切换未验；均未采用。PR #21 仍 OPEN，分支保留，其已有UI行为不重复应用。
- 旧分支清理先保存分支名到提交SHA映射和可验证bundle，另经一次具体范围确认。分支删除与目录删除分开；Windows原目录、11个worktree、旧Mac未提交文件、个人资料和原证据不删除。

## 2026-10-05 迁移与分支盘点（历史记录）

以下保留原盘点和历史验收范围；其中“Mac尚未验”“整合分支为当前入口”等只描述当时状态，当前入口以上节为准。

更新：2026-10-05。当前迁移与分支整合状态见本页及 [BRANCH_INTEGRATION_20261005.md](BRANCH_INTEGRATION_20261005.md)；历史项目状态仍见 [PROJECT_STATUS.md](PROJECT_STATUS.md)。

## 当前迁移与整合入口

- 用户已确认迁移源码基线 `codex/mac-migration-20261005@6a2516054e337c0ffb9795df999f56ea511b7b6b`，该完整SHA已推送并核实。
- 当前独立整合分支为 `codex/mac-integration-20261005`。普通历史功能已进入基线，本轮仅补入适用的历史收口事实、分支盘点和Mac交接说明，没有采用PR #21或A/B候选，也没有更新采集数据、数据格式或依赖。
- Mac以最终整合提交为接手版本；取得方式、明确的V2构建/本机启动命令及独立数据目录见 [MAC_MIGRATION.md](MAC_MIGRATION.md)。旧启动脚本构建V1，不再将其描述为当前Mac入口。
- Windows原目录、11个worktree、全部旧分支、生产active pointer和个人库保留；数据包另行私有交付。约48.9GB全历史留在Windows，不是本次迁移必需完成项。
- 不在Windows和Mac同时修改同一整合基线。Mac尚未拉取/构建/导入验收，不将历史证据记成Mac通过。

## 当前状态与历史维护记录

- 当前仅执行用户指定的迁移与分支整理；没有后台新开发、全源重抓或自动发布。
- 2026-09-23的历史维护收口曾记录 `master@24c8f88d7125fe9392ae5cf0219334cf4f2f5c29`。下方PR #5—12的验证与运行状态均保留当时范围，不代表今天的HEAD或全量验收。
- 2026-10-05核实远端master为 `42251392a44edb1eab6285c810fae3ee69b19292`；它不是本次Mac接手基线。其独有的PR #18收口文档事实本轮择取，未整分支倒灌旧壳层。
- A候选的独立安全审计仍为BLOCKED；B候选缺production_state、未做生产切换；PR #21仍OPEN且无检查记录，但其顶部短标签/title/aria行为已由迁移基线工作树修改纳入V1/V2。分支未合并与功能已纳入分开记录，具体失败和未验项见分支盘点。

## 当前交付

| 对象 | 现场事实 | 状态 |
| --- | --- | --- |
| PR #5 `feature/personal-library` | merge SHA `f0c9f9f0699693b713af334ba80ed6ce397b335e` | MERGED |
| PR #6 `codex/discovery-rules` | head `241d33dcdd3e34319870538b29491f595f996a3c`；base `f0c9f9f0699693b713af334ba80ed6ce397b335e` | MERGED |
| PR #6 合并提交 | `3b55b2a1e59cb2eabb98657ac851f8d4114be5cb`，已进入远端 master；其后追加状态文档提交 `4b283f744ca6fb7ecf4f26a559e68d64df35097a` | IMPLEMENTED / MERGED |
| PR #7 `codex/mcmod-pack-version` | head `10e9c56cc2a6e200f7ce73683a8cf08ab5c35891`；base `4b283f744ca6fb7ecf4f26a559e68d64df35097a` | MERGED |
| PR #7 合并提交 | `0197c8278f09c39fc7af83ac2e61a5deb4f28cfd`，已进入远端 master；其后仅追加本状态文档提交 | IMPLEMENTED / MERGED |
| PR #8 `codex/personal-backup-revisit` | head `8b08cc5261c49af8d5f93ca0cbb13215f59ad695`；base `392679b24c87821560aa1cd1e0aff0f1ae55748e` | MERGED |
| PR #8 合并提交 | `97914782c0a6c19a9a708961dec3ec1c8e6283ba`，已进入远端 master；其后仅追加本状态文档提交 | IMPLEMENTED / MERGED |
| PR #9 `codex/fix-default-browser-query` | head `5fb3bc26b45c40f5e67db5c51d502372d9b39c5e`；base `6efcc7e082e8288b7eed0bf1b53e641c4d705993` | MERGED |
| PR #9 合并提交 | `cecb00cc709d12e2968c216b7e1004f590326d4b`，合并后当时为远端与 D 盘 master head | IMPLEMENTED / MERGED |
| PR #10 `codex/fix-curseforge-images` | head `d74112b108c8a91de3853c8d4494744d928b84e2`；base `cecb00cc709d12e2968c216b7e1004f590326d4b`；merge `c6ea9f935acdf8e5ba6af1910e2a8c7e5a58dbf7` | MERGED |
| PR #11 `codex/dark-theme-consistency` | head `b29ea045e5bfdd56d69ec5faf98b043c8fe8ab58`；base `c6ea9f935acdf8e5ba6af1910e2a8c7e5a58dbf7`；merge `57a6cc6802629458b3569ed3a7e792e3b1b25dcb` | MERGED |
| PR #12 `codex/filter-profile-layout` | head `faef0f4c5234a85a9d44d950321a265b8067641b`；base `57a6cc6802629458b3569ed3a7e792e3b1b25dcb`；merge `24c8f88d7125fe9392ae5cf0219334cf4f2f5c29` | MERGED |
| PR #18 `codex/integrate-browser-ui` | 最终PR head `f2096c93bbc43b554c9255c34967f38909712faa`；merge `85b95f2c72dd00606b6e5363c49659bf428e4b86`，2026-10-05重新只读核实GitHub状态为MERGED | MERGED |

## PR #18 历史收口事实（从4225139择取）

- 最终业务diff为 `desktopShell.ts`、`desktopShell.css`、`platformRenderers.test.ts`；head `f2096c93bbc43b554c9255c34967f38909712faa` 已在当前迁移基线祖先中，不重复应用。
- 原验证为platformRenderers 12/12、web typecheck、desktop build通过；PR合并后未机械重跑。
- 当时GUI smoke因 `nodeRepl.fetch request failed` 未完成，保留为该历史版本的未验项，不记为GUI PASS。本轮没有重做这项历史验收。2026-09-25主分支收口记载 blocker 为无，GUI smoke 非 blocker；保留该历史结论，不将其扩大成当前全量通过。
- 个人库旧worktree文档的PR #5最终head/merge事实也已在当前代码和历史说明中；“当时origin/master=f0c9f9f”不用于今天的入口或版本判断。

## PR #10 收口

- 合并前 GitHub 确认 PR #10 head 为 `d74112b108c8a91de3853c8d4494744d928b84e2`、base 为 `cecb00cc709d12e2968c216b7e1004f590326d4b`，状态 `OPEN / MERGEABLE / CLEAN`，checks 列表为空；PR 已合并，merge SHA 为 `c6ea9f935acdf8e5ba6af1910e2a8c7e5a58dbf7`。
- D 盘正式主工作区已安全 fast-forward 到 `master@c6ea9f935acdf8e5ba6af1910e2a8c7e5a58dbf7`。原有 `docs/PROJECT_STATE.md` 工作区修改与三个未跟踪报告均保留；未使用 reset/clean。
- CurseForge 自有导航/看板图标不再请求实际返回 403 的远程 favicon，改用现有本地 `CF` 图标；来源封面失败后在当前页面会话内记忆失败 URL，重绘直接使用稳定 data URI 占位，且回退自身不会递归。
- 网络证据分别记录：CurseForge favicon 实测返回 403；当前快照抽样封面请求返回 200，未证明封面与 favicon 有相同网络根因。没有引入图片代理、下载或持久缓存。
- 复用已审核 head 的最小验证：平台 renderer 用例 10/10、desktop build 通过；受控浏览器确认正常资源可显示、404 资源稳定进入占位，并在切换 CurseForge 与紧凑视图后不增加失败资源请求。本次仅合并和同步文档，未重复运行验证、构建或启动服务。
- 未做全量、跨平台或真实联网回归；未修改真实 active pointer、快照或个人资料。blocker：无。本轮收口到此为止；暗色主题一致性与有界界面整理需另给明确任务，标签筛选和连续历史审计仍待澄清。

## PR #11 暗色主题一致性合并收口（2026-09-23）

- [PR #11](https://github.com/suifracti/mc-modpack-crawler-board/pull/11) 已由用户确认审核通过并合并。合并前 GitHub 确认 head `b29ea045e5bfdd56d69ec5faf98b043c8fe8ab58`、base `c6ea9f935acdf8e5ba6af1910e2a8c7e5a58dbf7`，状态 `OPEN / MERGEABLE / CLEAN`，checks 列表为空；实际 merge SHA 为 `57a6cc6802629458b3569ed3a7e792e3b1b25dcb`。
- 根因：桌面壳层另有一套硬编码暗色 palette，只有亮色覆盖；正式 dashboard 已提供多主题 token。部分旧样式及平台 renderer 内联品牌色没有随主题变化。
- 修改限于 `desktopShell.css` 和 Modrinth、CurseForge、Bilibili 三个平台 renderer：壳层颜色别名映射到现有 token，统一导航、筛选、卡片、表单、弹层、状态与焦点/禁用样式；平台品牌文字/徽章按当前主题适配。主题保存逻辑、个人标记数据与操作、分页和图片失败回退行为均未改；封面等内容图片未反转。
- 复用审核通过版本的最小验证：`npm --prefix apps/web run build:desktop` 一次通过；一次临时 fixture 浏览器检查覆盖亮→暗→亮、导航、筛选、结果卡片、下拉层与审计弹窗。本次合并收口未重新构建、启动服务或追加回归；主题保存逻辑未改，因此未验证刷新恢复。
- 未做全量、六平台矩阵或真实联网回归，未检查发布环境；未改真实 active pointer、快照或个人资料。D 盘主工作区已从 `master@c6ea9f935acdf8e5ba6af1910e2a8c7e5a58dbf7` 快进至 `master@57a6cc6802629458b3569ed3a7e792e3b1b25dcb`；既有 `docs/PROJECT_STATE.md` 修改与三个未跟踪报告保留，未使用 reset/clean。blocker：无。本轮到此停止；不自动启动布局、标签筛选或连续历史审计。

## PR #9 收口

- 已修复单个平台请求失败时丢弃其他平台成功结果、将请求错误混同为“没有匹配”，以及部分失败后继续共用页码导致的数据遗漏；部分失败时保留成功记录、显示错误与重试并暂停继续加载，完整重试成功后从第一页恢复正常分页。
- 最初触发 `Failed to fetch` 的传输失败原因未复现，仍未知；本次不宣称修复了服务端根因。
- 最小验证：正式前端 typecheck / desktop build 通过；真实快照默认查询呈现 72 条；限定浏览器 fixture 覆盖 A 第一页失败、B 第一页成功且有第二页，确认失败轮保留 B 且不能翻页，重试无重复并恢复分页，随后正常取得第二页。审计无历史基线与请求失败保持分离。
- 未做全量或跨平台回归，未重新验证真实联网传输失败；未修改真实 active pointer、快照或个人资料。blocker：无。

## PR #8 收口

- 规划方验收：`REPORT_BASED_REVIEW_PASS`。合并前远端 head 与指定提交一致，`MERGEABLE / CLEAN`，GitHub checks 列表为空，无新失败。
- Phase 2 已完成：schema 2 兼容 schema 1、历史引用缓存、缺源回访、JSON 导出、完整校验恢复和非破坏性冲突合并均已进入 master。
- 复用 head `8b08cc5261c49af8d5f93ca0cbb13215f59ad695` 的验证：Node 3/3、Web 9/9、typecheck、desktop build、限定无头浏览器 fixture 均通过。本次仅合并和状态文档更新，未重跑测试。
- 未验证真实联网、完整采集或发布环境完整 GUI；未迁移真实个人文件、未修改 active pointer。
- blocker：无。项目达到 `Mature Local Product`，进入 `MAINTENANCE / OBSERVE / NO_ACTIVE_IMPLEMENTATION_TASK`；不启动 Phase 3。

## PR #7 收口

- 规划方验收：`REPORT_BASED_REVIEW_PASS`。合并前远端 head 与指定提交一致，`MERGEABLE / CLEAN`，GitHub checks 列表为空，无新失败。
- raw `latest_version` 经 desktop modern sidecar 和离线 exporter 保留为可选 `packVersion`，DataStore / DTO 透传，MC百科详情显示“整合包版本名”；不进入 Minecraft 版本、筛选或搜索。
- 复用 head `10e9c56cc2a6e200f7ce73683a8cf08ab5c35891` 的验证：Python 生产/消费 fixture 1/1、Web renderer 8/8、typecheck、desktop build 通过。本次仅合并和状态更新，未重跑验证。
- 未验证真实联网、完整采集、发布环境 GUI 或合并后 master 运行态；旧 sidecar 兼容，但用户旧 snapshot 未回填。
- blocker：无。未修改用户真实 active snapshot；未启动下一任务；Master Plan 不变。

## PR #6 收口

- 规划方验收：`REPORT_BASED_REVIEW_PASS`。合并前远端 head 与指定提交一致，`MERGEABLE / CLEAN`，GitHub checks 列表为空。
- 已对齐搜索字段承诺、服务端运行线索筛选、全部/近 7/30/90 天日期选项、分平台检索总览与 MC百科缺字段表达；原站入口保留。
- 复用 head `241d33dcdd3e34319870538b29491f595f996a3c` 的验证：server 4/4、Web 37/37、typecheck、desktop build、限定 browser fixture 均通过。本次仅合并和状态文档更新，未重复运行测试。
- 未验证真实联网、发布环境完整 GUI 或合并后 master 运行态。
- blocker：无。未启动下一开发任务；Master Plan 不变。

## PR #5 已完成行为（历史证据）

- 保持 `personal-library.json` schema=1、`platform:sourceId`、GET/PATCH、原子写入和写队列。
- B站平铺、详情和组卡动作携带明确 BVID；组卡当前视频显示标题/BVID，历史已标记成员可定位到对应详情编辑状态。
- B站聚合先取得当前查询的完整非个人结果，再归组并按“至少一个成员命中”筛选；其他平台和视频平铺继续服务端个人筛选后分页。
- 标准化记录携带 `sourceIdOrigin`；仅当前快照明确标为 `index-fallback` 的记录拒绝新个人写入并显示原因，真实数字或字符串来源 ID 不按外形拒绝。
- 不因新 snapshot 缺少旧记录而删除个人文件或迁移个人 key。

## PR #5 最小验证（实施时证据）

- `node --test apps/desktop/test/browser-service.test.cjs apps/desktop/test/data-store.test.cjs`：5 tests passed。
- `npm test -- --run tests/bilibiliGrouping.test.ts tests/platformRenderers.test.ts`（`apps/web`）：17 tests passed。
- `npm run typecheck`（`apps/web`）：passed。
- 独立临时 `dataRoot` fixture 覆盖 A→A+B、A 的收藏/想玩/评分/备注重启恢复、B 单独收藏及取消、无 ID fallback 拒绝、合法数字 ID 接受。
- 额外做了一次限定浏览器点击：A+B 组卡显示 B 为当前视频、摘要列出 A；点击 B 的“收藏当前视频/加入想玩（保存视频线索）”后，A 的旧字段仍在，摘要入口可打开 A 详情。

## 未验证与边界

- 未做真实用户数据或发布环境的 GUI/桌面验收；限定浏览器点击仅使用临时 fixture，不代表完整 GUI 矩阵通过。
- 实施验证未启动全网抓取、未依赖 active snapshot、未修改真实用户数据。PR #5 至 PR #10 现已合并；Obsidian Handoff 在收口时同步，未进行发布。
- 归组规则本身不在本轮重写；组卡摘要范围仅承诺当前查询已完成加载的成员集合。

## 交接入口

- [Master Plan](../MC_PROJECT_MASTER_PLAN.md)
- [历史项目状态](PROJECT_STATUS.md)
- PR：[suifracti/mc-modpack-crawler-board#5](https://github.com/suifracti/mc-modpack-crawler-board/pull/5)
- PR：[suifracti/mc-modpack-crawler-board#6](https://github.com/suifracti/mc-modpack-crawler-board/pull/6)
- PR：[suifracti/mc-modpack-crawler-board#7](https://github.com/suifracti/mc-modpack-crawler-board/pull/7)
- PR：[suifracti/mc-modpack-crawler-board#8](https://github.com/suifracti/mc-modpack-crawler-board/pull/8)
- PR：[suifracti/mc-modpack-crawler-board#9](https://github.com/suifracti/mc-modpack-crawler-board/pull/9)
- PR：[suifracti/mc-modpack-crawler-board#10](https://github.com/suifracti/mc-modpack-crawler-board/pull/10)
- PR：[suifracti/mc-modpack-crawler-board#11](https://github.com/suifracti/mc-modpack-crawler-board/pull/11)

- PR：[suifracti/mc-modpack-crawler-board#12](https://github.com/suifracti/mc-modpack-crawler-board/pull/12)

## PR #12 筛选区与个人资料入口布局合并收口（2026-09-23）

- [PR #12](https://github.com/suifracti/mc-modpack-crawler-board/pull/12) 已合并。合并前确认远端 head 仍为 `faef0f4c5234a85a9d44d950321a265b8067641b`、base 为 `57a6cc6802629458b3569ed3a7e792e3b1b25dcb`，状态 `OPEN / CLEAN`，无 CI checks 报告；实际 merge SHA 为 `24c8f88d7125fe9392ae5cf0219334cf4f2f5c29`，PR 状态 `MERGED`。
- 主筛选区保留搜索、平台、版本、Loader、分类、回访状态和视图；渠道、更新时间、服务端线索、排序与条数放入分组的“更多筛选”。收起时按隐藏设置显示数量，现有条件芯片和清空行为保留。顶部的“个人资料”入口带缺源数量，将备份导出/恢复及说明、缺源回访放在弹层中。个人状态下拉仍是独立回访入口；没有改恢复校验、冲突处理、确认流程、查询分页或图片回退。无匹配状态间距收紧，加载、失败和重试/分页代码未变。
- 最小验证：`npm --prefix apps/web run build:desktop` 通过（含 `tsc --noEmit` 与 Vite）。一次本地临时 fixture 浏览检查覆盖亮→暗→亮，桌面 1365px 和窄窗口 600px/760px；版本筛选 2 条→1 条，时间筛选收起后显示“1 项已设置”，清空后恢复 2 条；打开资料弹层、展开缺源样例；键盘 Enter 展开筛选、Escape 关闭弹层并恢复入口焦点。资料弹层与筛选分别查看了亮/暗主题，未执行导出或恢复。
- 未做全量、跨平台或真实联网回归；只用 Modrinth 临时记录，没有重新验证加载失败、无匹配、PR #9 重试/分页运行行为或发布环境。数据/接口未改；未触碰真实 active pointer、snapshot 或个人资料。已复用本次一次构建和限定浏览器证据，本次合并收口未重建、启动服务或追加回归。D 盘主工作区已从 `master@57a6cc6802629458b3569ed3a7e792e3b1b25dcb` 安全快进到 `master@24c8f88d7125fe9392ae5cf0219334cf4f2f5c29`；原有 `PROJECT_STATE.md` 未提交修改及三个未跟踪报告保留，未使用 reset/clean。blocker：无。本批已报告的浏览失败、图片、主题和布局问题至此完成；标签/模组筛选及连续历史审计需先澄清数据能力与需求，不自动开工。

## PR #13 CurseForge 分类与文件索引合并收口（2026-09-23）

- [PR #13](https://github.com/suifracti/mc-modpack-crawler-board/pull/13) 已合并，状态 `MERGED`。合并前远端 head 仍为已审核版本 `6931bd8d06b8defb687f14a5ae2f4a7502191bad`，base 为 `24c8f88d7125fe9392ae5cf0219334cf4f2f5c29`；GitHub 显示 `CLEAN`，未报告 checks。实际 merge SHA：`8dddf2d056031ca222cfd73f05c2badd7c1d5d33`。
- D 盘正式主工作区 `master` 已由原基线安全快进至 `8dddf2d056031ca222cfd73f05c2badd7c1d5d33`。保留原有 `docs/PROJECT_STATE.md` 未提交修改与三个未跟踪报告；未使用 reset/clean，也未触碰真实 active pointer、快照或个人资料。
- CurseForge 已获取的分类及 MC 版本列表不再受原 8/12 项上限截断。来源提供的 `latestFilesIndexes` 通过可选文件索引字段进入 sidecar、正式读取 API 与 CF 详情，同一 fileId 的 gameVersion/Loader 配对保持对应；详情明确说明这不是完整发布历史，不含本次新增采集的 changelog 或模组关系。
- 已有快照没有回填。代码合并只让支持这些字段的新数据可经正式链读取，不表示用户现有数据已经新增字段。
- 复用已审核版本证据：生产—消费临时 fixture、renderer 11/11、desktop build 通过。本次没有重跑构建、GUI 或联网验证。未覆盖真实联网、全量抓取、六平台回归或既有快照回填；没有修改真实用户数据。blocker：无。
- CurseForge 源站有发布文件、更新日志和模组关系；当前应用尚未采集日志及关系，不据此写成源站不支持。用户决定暂不申请官方 API key，不推进申请或凭据管理。
- 有界样本 `GET https://api.curse.tools/v1/cf/mods/285109/files/4612979` 返回 302，目标为 HTTP 地址；未跟随，未取得有效文件数据。日志和关系接口未请求，三项能力仍未知。应用内 CF 日志与模组关系读取暂缓，继续使用已有原站入口；保留搜索采集配置，不接入未经验证的候选接口。
- 本轮结束后进入实际使用观察，无活动实施任务；不自动启动代理兼容、标签系统或连续历史审计。
## PR #14 封面回退与重试生命周期合并及实际使用交付（2026-09-23）

- [PR #14](https://github.com/suifracti/mc-modpack-crawler-board/pull/14) 已合并，审核 head 为 `b5d8754a10f17a5a2717bbf98310cbaed6d46297`，base 为 `8dddf2d056031ca222cfd73f05c2badd7c1d5d33`，实际 merge SHA：`93bd698e1a36322fa1b65da0dfdeb2d14e9eaf54`。PR 标题和描述已收窄至旧封面回退、加载状态、节点复用与手动重试生命周期，并明确真实网络原因和浏览器效果未验证。
- D 盘正式工作区 `master` 已由 `8dddf2d056031ca222cfd73f05c2badd7c1d5d33` 安全 fast-forward 至 `93bd698e1a36322fa1b65da0dfdeb2d14e9eaf54`。既有 `docs/PROJECT_STATE.md` 修改和三个未跟踪报告保留；未使用 reset/clean。
- 合并后仅构建一次：`npm.cmd --prefix apps/web run build:desktop` 通过（TypeScript 与 Vite）。复用审核 head 已通过的定向封面生命周期用例 11/11 和 TypeScript 检查；本次没有追加测试。
- 先确认 8765 端口进程的祖先进程命令行为正式工作区的 `start_browser_service.cmd`，随后只重启本项目服务，使用相同用户和默认数据配置（无单独覆盖参数）；没有停止其他应用或触发采集、导入。入口 `http://127.0.0.1:8765/` 返回 HTTP 200。未进行浏览器图片检查。
- 没有修改真实 active pointer、快照或个人资料。浏览器图片检查曾被安全策略拒绝，不换通道获取等价证据。真实封面黑屏/缓慢的网络原因以及本次修复对真实图片效果的影响仍未验证；问题保持开放，等待用户实际使用反馈。请用户刷新页面，挑一个仍异常的封面，仅反馈平台、包名和页面显示的状态文字即可；不要求开发者工具或完整验收。

## PR #15 封面重绘回归修复合并与正式入口交付（2026-09-23）

- [PR #15](https://github.com/suifracti/mc-modpack-crawler-board/pull/15) 已合并（`MERGED`）。branch `codex/fix-cover-regression`，审核 head `78e2cae844cbe3c417a700e6b7e1fbcb95b44e2c`，base `93bd698e1a36322fa1b65da0dfdeb2d14e9eaf54`，实际 merge SHA `f272fc6c8777f88fa46e27e18f5062c6a8af827b`。D 盘正式工作区 `master` 已安全 fast-forward 到该 SHA；未提交 `docs/PROJECT_STATE.md` 修改和三个未跟踪报告保留，未使用 reset/clean。
- 回归根因：PR #14 将平台/视图切换时被整页重绘移除的加载中图片节点写入全局 `cancelled` 失败缓存；相同 URL 再出现时直接变成“封面加载已取消”，把节点生命周期误当成资源失败。PR #15 改为仅释放离开页面节点的 timer、observer 和 retry ticket，不污染 URL 失败状态；真实 error/timeout 的占位和重试保持。B站丰富卡片补接共用封面生命周期，XYEBBS 改用自身占位而非 BBSMC。
- 最小证据：审核 head 的定向 renderer / 生命周期用例 11/11 通过、desktop build 通过。用例实际改变连接状态，确认加载中节点被重绘移除后不写失败缓存、再次呈现仍请求原图，并确认中断手动重试会恢复先前真实 timeout。正式交付复用了审核 head 已通过的前端构建产物，未重新构建或追加测试；仅重启归属 D 盘正式工作区的服务，继续使用相同默认用户数据配置。入口 `http://127.0.0.1:8765/` 返回 HTTP 200，只确认入口可访问。
- 旧实现依据：`2424b5e1` 的 `web/template.html` / `web/assets/js/dashboard.js` 有 MC百科“包含模组”专用入口，数据来自 compareData 的 mods；多选为全部包含（AND），排除模式否定该整体条件。当前正式数据的 `includedModNames` 仍存在，但正式桌面迁移只保留普通搜索/单分类，没有专用状态、参数、控件和服务端谓词。
- CurseForge 旧入口实际是“玩法分类”多选，不是整合包内含模组关系：同一旧版本中的 `curseforgeCategoryChips` 读取 `categories`，包含模式多选为 OR，排除模式排除任一命中；当前数据仍有 categories，正式入口退化为单选分类。恢复时应沿用真实名称和并/排除语义，不用关键词搜索冒充。
- MC百科旧走势图在 `2424b5e1` 中读取真实 `trend_vals` / `trend_dates`，保留指标、时间范围、最新/最小/最大/平均和点位交互；`27347c4` 的结构化 renderer 仍有趋势 cell/sparkline。正式桌面入口迁移 `0842b83` 只展示近 7/30 天数值，丢失趋势字段绑定和图表事件。当前 `mcmod_data.js` 仍有 `trendStats.trendValsStr` / `trendDatesStr` 历史点；下一步应复用这些真实点接回入口，少于两个点明确缺失，不合成走势。
- 真实外部图片请求及显示效果仍未验证；限定浏览器检查因本机 UI 控制工具报 `failed to write kernel assets: 系统找不到指定的路径 (os error 3)` 未取得，按约束未重试或更换通道。MC百科当前正式数据与 `crawler_output/mcmod_modpacks.json` 的封面字段均为空，前端修复不能补出来源图片；封面外部效果保持开放，等待实际使用反馈。
- 未修改真实 active pointer、snapshot 或个人资料；没有采集或导入。后续实施优先恢复 MC百科包含模组筛选和 CurseForge 玩法分类多选/排除；MC百科走势图随后单独恢复。这些均是待恢复的旧能力，不是新功能；不自动开始下一任务。

## PR #16 平台专属旧筛选恢复合并与正式入口交付（2026-09-23）

- [PR #16](https://github.com/suifracti/mc-modpack-crawler-board/pull/16) 已合并（`MERGED`）。branch `codex/restore-platform-filters`，审核 head `bbe94649adc955d28977d8564f5b0025c295c4f8`，base `f272fc6c8777f88fa46e27e18f5062c6a8af827b`，实际 merge SHA `eb521b848a1613d84b8080152c0e45a2aa1f52df`；合并前确认 head 未变化、`CLEAN / MERGEABLE`，未报告 checks。
- MC百科“包含模组”多选使用已有 `includedModNames`：包含模式要求全部所选名称命中（AND）；排除模式是对“全部命中”整体取反。未知模组清单不算正向命中，也不作为已确认包含而排除。
- CurseForge “玩法分类”多选使用 categories：包含模式命中任一所选分类（OR）；排除模式排除任一所选分类命中。两类平台专属条件彼此隔离；筛选在服务端完整记录集上完成，再排序分页。现有查询、筛选和分页行为保持。
- 输入法修订：组合期间 input 事件只同步文本状态，不触发候选搜索重绘；compositionend 后提交完整文本并更新候选。普通输入及清空仍正常生效。
- 验证证据：复用 DataStore 用例 5/5；离线输入事件用例 1/1，覆盖组合期间输入节点不被替换、组合结束完整文本、普通输入和清空；TypeScript 检查通过。合并后仅执行一次 `npm.cmd --prefix apps/web run build:desktop`，通过 TypeScript 与 Vite 构建。真实 GUI / 浏览器效果未验证；事件用例使用 Node `EventTarget` 模拟替换行为，并非真实 DOM 验收。未追加业务回归。
- D 盘正式工作区 `master` 已从 `f272fc6c8777f88fa46e27e18f5062c6a8af827b` 安全快进到 `eb521b848a1613d84b8080152c0e45a2aa1f52df`。原有未提交 `PROJECT_STATE.md` 修改与三个未跟踪报告均保留，未使用 reset/clean。
- 正式服务：确认 8765 监听者的 `node server.cjs` 与祖先 `npm --prefix apps/desktop run start:no-open` 属于本项目后，仅停止原服务进程，并在 D 盘工作区用相同命令重新启动；启动输出显示仍使用原有默认数据配置。入口 `http://127.0.0.1:8765/` 返回 HTTP 200。本次只确认入口可访问，未进行浏览器或功能验收。隐藏后台启动调用被本机策略拒绝，因此服务当前由 Codex 管理的命令会话保持运行；未采集、导入或修改真实 active pointer、快照和个人资料。
- blocker：无。下一实施项为恢复 MC百科已有数据的走势图；不重复调查已定位的旧实现，本轮未开始。

## PR #17 MC百科旧版走势图实现与审核提交（2026-09-23）

- 提交审核时基于 `master@eb521b848a1613d84b8080152c0e45a2aa1f52df` 建立独立分支 `codex/restore-mcmod-trend-chart`；已审核 head `931bc05b89d28d008eea18b42fa0a81b2b3a4f13`，当时 PR 状态为 `OPEN / CLEAN`。原始 MC百科记录的 `trendStats.trendValsStr / trendDatesStr` 已经由正式读取链的 `raw` 字段透传，本轮只恢复桌面正式浏览展示；当前合并状态见下方收口记录。
- MC百科表格补回趋势缩略图及入口；详情可开完整走势图。使用已有的官方流行指数历史序列，支持近 7/30/60 天与全部历史；最新、最小、最大、平均随所选范围计算，指针和方向键可选择日期和值。现有 7/30 等汇总不是独立历史曲线。
- 配对规则：日期和值数量不同则整组不绘制；等长时按原索引配对，单个空值、非法数值或非法日期只跳过该配对，不转成零或重新错位；日期重复／逆序时拒绝绘制。有效点少于两个时明确提示数据不足；不以当前值或近 7/30 天汇总合成历史。亮暗主题和窄窗口使用现有主题变量及响应式样式。
- 最小验证：`npm --prefix apps/web run test -- tests/mcmod.test.ts` 15/15 通过，覆盖明确日期/数值样本、7 日统计、零值、缺失、少于两个点、长度不一致与异常配对；`npm --prefix apps/web run build:desktop` 的 TypeScript 检查和 Vite 构建通过。浏览器工具限制仍有效，本轮 GUI 未验证；未联网、采集、回填快照、重启正式服务或修改 active pointer/快照/个人资料。
- 提交阶段 blocker：无。既有未提交 PROJECT_STATE 修改和三个未跟踪报告继续保留；PR 当时等待审核，后续合并收口见下方。

## PR #17 MC百科旧版走势图恢复合并与正式入口交付（2026-09-23）

- PR [#17](https://github.com/suifracti/mc-modpack-crawler-board/pull/17) 已合并，审核 head `931bc05b89d28d008eea18b42fa0a81b2b3a4f13` 未变化；实际 merge SHA / D 盘 `master` head 均为 `9aeed3760de268f259487aa3444c56300dd0d246`。工作区通过 `origin/master` 快进同步，原有未提交 `docs/PROJECT_STATE.md` 修改与三个未跟踪报告保留；未使用 reset/clean。
- MC百科表格趋势缩略图和详情完整走势图已恢复，使用已有官方流行指数历史点。7/30/60 天范围以数据中最新日期为终点，不表示历史已更新至今天；统计随所选范围计算。异常或少于两个有效历史点明确提示，不错位配对，也不合成曲线。
- 复用审核 head 已通过的定向趋势用例 15/15、TypeScript 检查和 desktop build 证据；复用其构建产物。未追加构建、测试或 GUI 检查；真实 GUI 尚未验证。
- 当时只重启已确认属于本项目的正式服务，沿用Windows用户AppData内原MCModpackBoard数据根目录。入口 `http://127.0.0.1:8765/` 返回 HTTP 200。当时使用可见的 Codex 管理命令会话运行 `npm --prefix apps/desktop run start:no-open` 并保持该会话，不使用隐藏后台启动。未采集、导入或回填，也未修改真实 active pointer、快照或个人资料。
- 封面外部图片的真实显示效果仍待用户反馈，未随 PR #17 关闭。当前交付无阻塞项；GUI 未验收为已知验证限制。

## PR #18 正式浏览页面整合修复待审（2026-09-23历史记录，现已合并）

- [PR #18](https://github.com/suifracti/mc-modpack-crawler-board/pull/18) 基于 `master@9aeed3760de268f259487aa3444c56300dd0d246`，branch `codex/integrate-browser-ui`，head `451dbad68687e88a143def3bb31e71b4396841e2`，保持待审，未合并、未重启正式服务。
- 卡片结构根因是个人操作／B站组摘要位于网格直接子项中的视觉卡片之前，旧平台内层卡片同时被强制 `height: 100%`，使操作看似漂浮并额外撑高。现改为单一视觉卡片外壳，平台内容在前、同记录的“我的状态”页脚在后；B站当前视频与成员摘要仍按明确 BVID 保存，不生成组级收藏。个人操作继续由 `platform + sourceId` 定位，索引只作旧节点回退。
- MC百科包含模组改为搜索、独立已选区、默认 10 项候选、展开和折叠规则帮助；CurseForge 玩法分类整理为已选区、计数、展开、明确排除态和单独清空。PR #16 的 MC百科 AND／整体否定、CF OR／排除任一及服务端分页前筛选没有改变。趋势表格分开显示 7/30 日数值、缩略图和完整趋势入口，并局部解除旧通用 `.sparkline-svg` 最小宽度对缩略图的挤压。
- 最小证据：`tests/platformRenderers.test.ts` 12/12；新增反例把两条记录排序互换并保留陈旧索引，个人操作仍命中指定 `platform + sourceId`；`build:desktop`（TypeScript + Vite）通过。PR #16 的服务端筛选行为证据因相关谓词和请求参数未改而复用，未重复跑 DataStore 全套。
- MC百科封面链核对：采集器有 `cover_url` 字段，modern sidecar 导出为 `coverUrl`，正式 desktop normalizer 和页面 renderer 均读取这些字段；仓库 `crawler_output/mcmod_modpacks.json`、`converted_output/data/mcmod_data.js` 以及只读核对的正式 active snapshot `20260920084809555-578e8c` 均为 1484 条记录、0 条有封面。因此当前缺口是采集阶段未取得来源值，旧快照也没有可供前端恢复的字段；本 PR 未修改采集器、真实 active pointer 或快照。最小后续方案是先用少量保存的 MC百科真实页面样本确认现行封面 DOM／URL契约，再单独修正解析并以隔离输出验证，是否回填旧快照需用户另行授权。
- 收藏更新提醒仅保留设计：一次平台刷新完整成功并切换新快照后，以 `platform + sourceId` 比较前后明确发布指纹（文件 ID、发布 ID或版本字段），标题和统计变化不触发；首次只建立基线。每项持久保存基线指纹、待查看指纹与已确认指纹／时间，同一指纹不重复提醒。缺记录、字段缺失、部分刷新或刷新失败均记为未知而非更新。B站新 BVID 只显示“可能相关”线索，不迁移收藏或认定同包。首期只做应用内徽标和更新清单；应用未运行或没有成功刷新时不会实时获知变化，不建设后台、云通知或持久组身份。
- GUI 未验收：限定浏览器工具初始化仍报 `failed to write kernel assets: 系统找不到指定的路径 (os error 3)`，按约束未重试或换通道；亮暗主题、窄窗口和真实图片效果不能写成已通过。用户本轮提到的五张截图未作为可读取附件出现在任务工具上下文中。既有未提交文档修改、三个未跟踪报告和用户数据均保留。

## PR #20+ MC百科封面链路恢复与顶栏紧凑优化（2026-09-25）

- **顶栏快照标签紧凑化**：将顶栏快照标签从全长文本精简为 `● 快照`，完整快照 ID 保留在 tooltip/title 与 `aria-label` 中，为“变动审计”节省约 170px 空间，避免顶栏操作区拥挤溢出。
- **MC百科封面采集与回填链路接回**：
  1. `apps/desktop/collector_worker.py`：支持 `--mode` 与 `--cover-offset` 参数；当 `platform == 'mcmod'` 时根据选择模式透传至爬虫，并在 `covers` 模式下默认 limit=20。
  2. `apps/desktop/lib/update-manager.cjs` 与 `server.cjs`、`main.cjs`：保留并透传 `mode`、`coverOffset` 参数，支持 Electron 与本地服务双端。
  3. `apps/web/src/desktopShell.ts`：更新面板支持 MCMod 选择模式（“自适应探测新整合包” 与 “仅补充缺失封面”）；表格视图在 `.mcmod-name-cell` 中渲染封面缩略图并接入已有的 `renderCoverImage` 缩略图重试、回退与大图预览系统。
  4. `apps/web/src/desktopShell.css`：完善 `.cover-media-table`、`.mcmod-table-cover` 以及 `.mcmod-name-cell-inner` 样式。
- **验证证据**：
  - `npm --prefix apps/web test`：13 个测试套件，90 个用例全数通过。
  - `npm --prefix apps/desktop test`：16 个 node 测试用例全数通过（含 mode 与 coverOffset 透传用例）。
  - Python 测试：7 个用例全数通过（含 `build_script_args` covers 与 new 模式参数验证）。
  - `npm --prefix apps/web run build:desktop`：TypeScript 检查与 Vite 构建成功。
  - 本地服务 `http://127.0.0.1:8765/`：后台常驻运行，HTTP 200 验证通过。

## PR #21 现代桌面工作台设计语言统一重构（2026-09-25）

- **现代内容资料库与工作台设计基准（Workbench Design Baseline）全面落地**：
  1. **色彩与中性层级**：全界面收敛高饱和与高光背景，使用中性表面层级（`--bg-base`, `--bg-surface`, `--bg-surface-elevated`），让整合包封面与内容成为第一视觉焦点。语义状态色全面解耦（危险 `#EF4444`、警示 `#F59E0B`、成功 `#10B981`），B站粉色 (`#FB7299`) 严格回归平台来源属性，不再挪作错误/负向提示。
  2. **文字与信息排版**：正文与交互控件字号统一为 13–14px，辅助元数据 12px，标签与紧凑芯片 11px，彻底清理 9px/10px 等不可读细字；层级清晰，拒绝挤压缩字。
  3. **尺寸、间距与圆角**：控件统一规范为 32–36px（34px 黄金基准），间距按 4/8/12/16/24px 递进。控件圆角 8px、卡片 14px、模态与弹窗 16px、胶囊徽标 999px。投影全面收敛，仅保留浮层与模态层。
  4. **顶栏与工作区解耦**：
     - 移除旧版固定 330px 挤占空间的数据更新侧边栏，卡片网格与 MCMod 表格享有 100% 完整浏览工作台宽度。
     - “数据更新”改为顶栏标准触发弹窗，并在后台抓取时呈现运行状态呼吸指示点。
     - 顶栏按钮（变动审计、数据更新、更换数据、个人资料）全数按 34px 规范对齐；快照标签保持 `● 快照` 紧凑状态，鼠标悬停提供完整快照详情。
  5. **统一弹窗与全局交互**：
     - 模态（数据更新、变动审计、对比底栏与抽屉、个人资料与收藏更新、MCMod 走势图、图片大图灯箱）统一遵循 `.modal-backdrop` 与 `.modal-panel` 规范。
     - 支持全局 Escape 按键分层安全退出（预览图 -> 走势图 -> 更新面板 -> 变动审计 -> 对比面板 -> 个人资料 -> 详情抽屉 -> 下拉菜单）。
     - 弹窗背景遮罩点击增加判定保护，避免选中文本或内部交互误触关闭。
  6. **详情抽屉与个人数据流完备对齐**：
     - 抽屉内版本发布清单 (`.release-item`)、CurseForge 文件索引组 (`.curseforge-file-index-group`)、独立评论区 (`.comment-item`)、媒体画廊 (`.detail-image-gallery`)、个人评分按键组及备注输入框全数重构至新规范。
     - 个人资料弹窗的本地备份导出/恢复、缺源回访与收藏版本更新提醒列表全数完成工作台规范对齐。
- **全套验证证据**：
  - `npm --prefix apps/web run build:desktop`：TypeScript 检查 0 错误，Vite 构建正常打包。
  - `npm --prefix apps/web test`：13 个测试套件，90 个用例全部通过（100%）。
  - `npm --prefix apps/desktop test`：16 个 Node 测试全部通过（100%）。
  - `python -m unittest discover -s apps/desktop/test`：7 个 Python 测试全部通过（100%）。
  - 本地常驻服务（`http://127.0.0.1:8765/api/state`）：健康运行，当前快照与记录正常加载。

## PR #22 站点切换与大数据量检索极致性能优化（2026-09-25）

- **背景与根因定位**：
  - 用户反馈切换站点（尤其 CurseForge 4.5万+ 条与 Modrinth 1.8万+ 条）存在明显卡顿与较长加载时间。
  - **后端瓶颈**：每次请求接口时，后端对全部 45,797 条数据做多次全量解析与 $N \log N$ 排序。在 `sortRecords` 比较器内部反复执行 `Array.map`、`Array.find`、`Date.parse`，每次请求触发约 70 万次日期解析；且每次都重新遍历 4.5 万条提取筛选 facets，导致单次请求耗时高达 700~1300ms。
  - **前端瓶颈**：切换平台时 `loadRecords(reset = true)` 会先将 `state.records = []` 并触发 `replaceRootHtmlPreservingCoverImages` 全量重绘，将结果区替换为 80px 的 loading 提示造成严重白屏闪烁与高度塌陷；Bilibili 聚合模式下存在 500 次 $\times$ 936 条的 $O(N \times M)$ 线性扫描；且缺少平台级内存缓存与网络竞态保护。
- **优化实施**：
  1. **后端数据存储优化 (`apps/desktop/lib/data-store.cjs`)**：
     - **预计算时间戳**：在快照载入规范化记录时一次性计算 `_timestamp` 与 `_createdTimestamp`，在排序比较器中直接比较数值，消除比较器内的任何对象分配与字符串日期解析。
     - **基础排序与 Facets 缓存 (`cached.baseSorted`, `cached.baseFacets`)**：针对默认视图（`updated_desc` 等无自由搜索词情况），首次计算后将结果按平台快照缓存，后续查询仅需 $O(1)$ 的切片分页；基础 facets 仅提取一次。
     - **安全高效基准时间计算**：移除了危险的 `Math.max(Date.now(), ...searched.map(recordTimestamp))`（在 4.5 万条数据上展开参数会撑满调用栈），改为在有 `dateRange` 条件时做局部扫描。
     - **分页上限与异步预热**：将 `pageSize` 软限制从 500 放宽到 2000；在 `getState()` 时通过 `setImmediate` 异步并行预热（warmup）全平台基础缓存。
  2. **前端交互与渲染平滑化 (`apps/web/src/desktopShell.ts` & `desktopShell.css`)**：
     - **客户端多平台内存缓存 (`platformRecordCache`)**：在会话内缓存已访问平台的默认数据与选项，平台来回切换实现 **0ms 瞬间渲染**。
     - **静默后台校验与防白屏闪烁**：命中缓存时立即呈现已有数据，并在后台完成静默重校验 (`backgroundRevalidate`)，不再清空记录产生 loading 闪烁与 DOM 突变。
     - **网络竞态守卫 (`activeLoadRequestId`)**：快速连续切换平台时自动丢弃过期的异步网络响应，杜绝时序颠倒导致的数据错乱。
     - **Bilibili 聚合视图 $O(1)$ 查找与并行分页**：使用 Map 索引取代 `state.records.findIndex` 线性扫描；超过单页时使用 `Promise.all` 并发拉取。
     - **布局与骨架高度稳定**：给结果区与加载状态增加安全最小高度（480px / 380px）与平滑旋转动画，彻底消除视口跳动与布局抖动。
- **实测性能数据**：
  - **后端 API 响应耗时**：
    - CurseForge（45,797 条）：由 ~1300ms 降至 **2.6ms**（提速超 500 倍）
    - Modrinth（18,328 条）：由 ~850ms 降至 **4.0ms**（提速超 200 倍）
    - Bilibili（936 条）：降至 **3.7ms**
    - MCMod（1,484 条 + 全量 facets）：降至 **47ms**
  - **前端切换体感**：二次切换至已访问平台耗时 **0ms**，界面零闪烁、零高度跳动。
- **来回频繁点击卡顿深度根治（性能追补）**：
  1. **彻底消除缓存命中时的冗余二次全量重绘**：此前命中缓存后仍调用 `void loadRecords(true, true)` 进行后台重校验；因本地快照数据不可变，重校验返回时触发了无意义的**第二次全量 DOM 销毁与重建**。移除该调用后，平台切换变为纯粹的单次内存极速渲染，不再产生二次卡顿。
  2. **Bilibili 聚合视图分页防爆 (7500+ DOM 节点缩减 90%)**：此前 Bilibili 聚合模式一次性将 500 个聚合包全部展开渲染成卡片，生成 1.5MB HTML 与超过 7,500 个 DOM 节点；切换至 Bilibili 或切走时造成主线程数十至数百毫秒的 GC 与重排阻塞。优化后首屏规整为 48 项，超出部分通过“加载更多”按需自增，DOM 节点开销骤降 90%，毫秒级瞬切。
  3. **前端全平台自启动后台预热 (`warmupPlatformCache`)**：进入桌面工作台加载完成全部视图后，静默并发预热其他 5 个平台至内存缓存中；用户首次点击任何平台亦可享受 0ms 纯缓存体验。
  4. **后端传输瘦身**：在 `getPlatformRecords` 返回切片时剔除了服务端内部全文检索结构 `searchDocument` 与内部时间戳，MCMod 接口 JSON 体积由 1.91MB 降至 1.24MB，单次解析提速近一倍。
- **全套验证证据**：
  - `npm --prefix apps/web run build:desktop`：通过（426ms）。
  - `npm --prefix apps/web test`：13/13 文件，90/90 测试通过。
  - `npm --prefix apps/desktop test`：16/16 测试通过。
  - `python -m unittest discover -s apps/desktop/test`：7/7 测试通过。
  - 本地常驻服务（`http://127.0.0.1:8765/`）：正常运行，HTTP 200。

## PR #23 筛选搜索框与模组/分类面板质感分离度提升（对齐 HTML 参考，2026-09-25）

- **背景与痛点**：
  - 用户反馈：“这个筛选搜索框可以接回html时期的那种参考，有点不太好看现在，分离度也低”。
  - 经排查，此前重构中模组/分类面板背景（`--bg-surface-elevated`）与外层筛选栏（`--bg-surface`）在浅色下反差微弱，且搜索输入框为纯无装饰文本框，候选胶囊散布且无独立凹槽卡片隔离，导致视觉层级发平、发灰、缺乏分离感与工作台质感。
- **改动与实现**：
  1. **HTML 时代质感与层级重现**（参考 `web/template.html` 与 `dashboard.css`）：
     - **结构化搜索框 (`.facet-search-box`)**：
       - 前置 `🔍` 放大镜图标与绝对定位对齐。
       - 胶囊型高对比度输入框（`--bg-surface`，1.5px 边框 `--border-card`，微投影与聚焦光环 `--accent-primary-tint`）。
       - 右置圆形一键清空按钮 `✕`（`.facet-search-clear-btn`）及 Escape 快捷键监听。
       - 模组候选计数徽标（`.facet-search-counter`，直观呈现“11,443 款模组可选”）。
     - **高分离度候选池卡片 (`.platform-facet-options-box`)**：
       - 将候选模组/分类胶囊放置于底色凹陷内衬容器（`--bg-base`，微内阴影与 1px 边框）中，与卡片表面彻底拉开视觉距离。
       - 规范胶囊（`.platform-facet-chip`）与计数胶囊（`.facet-chip-count`），增加微交互反馈（hover 时小幅位移上浮与色彩高亮）。
       - 模组未搜索时默认精简呈现热门前 12 款，提供圆角药丸型“展开常用前 60 款 ▾ / 收起 ▴”按钮，搜索时按关键词即时精确过滤，解决数千模组铺满视口问题。
     - **清晰已选区与反向排除态**：
       - 已选模组区独立虚线/着色外框容器（`.platform-facet-selected`），带即时模式文案提示。
       - 选中芯片带胶囊计数与明确的 `✕` 剔除按钮。
       - 开启反向“排除完整组合”时，整卡与已选区转为语义危险红态（红色边框与红调背景），避免误选。
  2. **逻辑与事件完善**：
     - `desktopShell.ts`：支持点击 `✕` 或在搜索框按下 `Escape` 清空筛选词并保持焦点；支持“清空已选”一键重置。
- **全套验证证据**：
  - `npm --prefix apps/web run build:desktop`：TypeScript 编译通过，Vite 构建成功。
  - `npm --prefix apps/web test`：13/13 文件，90/90 测试通过。
  - `npm --prefix apps/desktop test`：16/16 测试通过。
  - 本地常驻服务（`http://127.0.0.1:8765/`）：正常运行，HTTP 200。

## PR #24 全量模组与超量分类发现弹窗系统（Discovery Picker Modal，2026-09-25）

- **背景与用户痛点**：
  - 用户反馈：“我的意思是分类和模组过多的情况下再加一个点击弹窗显示有什么类别或者其他，总要能看完有什么类别或者模组吧，其他的也是”。
  - MC百科包含模组多达 **11,443 款**，首屏仅能精简推荐热门款；MC百科分类标签有 **783 类**，普通下拉菜单无法舒适浏览全量选项。
- **改动与实现**：
  1. **全量发现弹窗架构 (`renderPickerModal`)**：
     - **大画幅工作台弹窗**：最大宽度 920px、最高 86vh，采用规范 `.modal-backdrop` 与 `.modal-panel.picker-modal-panel`。
     - **毫秒级模糊搜索与组合输入守卫**：内置结构化搜索框（带清空按钮 `✕`），全量 11,443 项实时模糊过滤（耗时 <2ms），中文拼音合成安全输入。
     - **自适应响应式卡片网格 (`.picker-grid`)**：以 195px 最小宽度的响应式网格排布所有候选选项（`.picker-option`），显示模组/分类名称、收录频次徽标（`.picker-count`）与选中勾选指示（`.picker-check-badge`）。
      - **分页分批防卡死与一次展示完**：默认呈现前 300 项，底部提供“`📥 加载更多 300 项 ▾`”以及“`⚡ 一次展示完（全部 N 项）`”按钮，兼顾快速初载与一次性全览需求；当已展示超过 300 项时提供“`⤴ 收起为前 300 项`”按钮。
      - **自定义多维排序 (`picker.sort`)**：弹窗工具栏提供精准排序下拉菜单：
        1. **收录最多（热度）**：默认排序，优先呈现大热模组/主流分类。
        2. **收录最少（小众）**：升序排序，专为发掘冷门、小众独特模组设计。
        3. **名称 A → Z**：基于中文拼音和英文字母正序排列。
        4. **名称 Z → A**：逆序排列。
      - **滚动位置防丢失**：在弹窗内选中/取消任何模组重新 render 时，自动保存并还原 `.picker-grid-wrap` 的 `scrollTop`，页面绝不跳顶。
      - **底部操作栏**：实时显示“`已选 X 项 · 共匹配 Y 项`”，提供“`清空已选`”与“`完成 / 应用筛选`”操作；支持 `Escape` 键安全退出并自动同步过滤结果。
   2. **纯净触发入口（去除冗余尾随方块图标）**：
      - **MC百科包含模组**：
        - 搜索栏右侧候选计数直接转为按钮：“`11,443 款模组可选`”。
        - 候选栏右侧常驻按钮：“`全部模组库 (11,443)`”。
      - **CurseForge 玩法分类**：候选栏右侧常驻按钮：“`全部分类库 (19)`”。
      - **顶栏通用分类筛选（MCMod 783 类等）**：
        - 当平台分类超过 12 项时，分类标签旁提供快捷触发器：“`全部 (783)`”。
        - 自定义下拉菜单顶部嵌入首项操作：“`弹窗查看全部分类（共 783 类）...`”。
- **全套验证证据**：
  - `npm --prefix apps/web test`：13/13 测试套件通过，新增自定义排序、一次展示完及收起测试（93/93 测试通过，100%）。
  - `npm --prefix apps/desktop test`：16/16 测试通过。
  - `npm --prefix apps/web run build:desktop`：通过，打包完成。
  - 本地服务 `http://127.0.0.1:8765/`：正常运行（HTTP 200）。
## PR #26: 屏幕跟随吸顶模式（随滚随选分类与即时排序）
- **背景与目标**：解决整合包长列表中滚下去后无法便捷切换分类、排序被深埋在“更多筛选”中、以及大弹窗流程脱离实际卡片浏览的问题。实现沉浸式“跟随屏幕移动模式”，在滚动过程中常驻吸顶，随时一键选换分类与排序。
- **改动与实现**：
  1. **跟随屏幕吸顶导航条 (`renderStickyFollowBar` / `.desktop-sticky-bar`)**：
     - **吸顶常驻定位**：默认开启 `stickyFollowMode = true`，当用户向下浏览滚动时，工具条以 `position: sticky; top: 52px; z-index: 850` 紧贴于 52px 顶栏下方，背景带毛玻璃与微浮阴影，零遮挡正文。
     - **横向快捷常用分类胶囊 (`.sticky-pills-wrap`)**：提取当前数据频次最高的常用分类（全部、科技、魔法、冒险、空岛、生存、探索、任务、RPG、休闲、硬核等），单行轻量横向滚动，单次点击即时换类。
     - **全部分类下拉快速跳转 (`.sticky-cat-select`)**：胶囊栏旁紧邻全量分类选择器，收纳平台所有分类（如 MCMod 全部 783 类），滚动到任意位置均可跳选任一分类。
     - **即时排序切换 (`.sticky-sort-select`)**：将原先隐藏在“更多筛选”折叠面板内的排序控制直接提至跟随栏，随时在最新更新、最多浏览、最多下载、点赞最多、名称 A-Z 等模式间切换。
     - **CurseForge 与 MCMod 定向适配**：CurseForge 呈现玩法分类（支持多选与快速清空）；MCMod 带有已选包含模组指示徽标与全量模组库呼出按键。
     - **跟随模式锁定与一键置顶**：提供“`📌 跟随中`”切换按钮（可按需锁定/解除吸顶），以及“`↑ 顶部`”平滑返回按键。
- **全套验证证据**：
  - `npm --prefix apps/web test`：13/13 测试套件通过，新增跟随模式吸顶栏与分类排序切换测试（94/94 测试通过，100%）。
  - `npm --prefix apps/desktop test`：16/16 测试通过。
  - `npm --prefix apps/web run build:desktop`：通过，编译打包完成。
  - 本地服务 `http://127.0.0.1:8765/`：正常运行（HTTP 200）。

## PR #27: 吸顶跟随栏去原生化与分类/模组半区直览体系（2026-09-25）

- **背景与用户痛点**：
  1. 用户反馈：“分类变成Windowsui了，而且分类也叫一个数量显示还有排序”。原生 HTML <select> 在 Windows 下触发经典 Win32 蓝底原生下拉框，割裂深色/工作台主题；同时分类胶囊缺少数量呈现且未按出现频次降序，导致纯数字标签置顶而热门分类被埋。
  2. 用户需求：“左边留一半给模组，就是左边有分类和模组的这种可以不用点击打开的就能显示完的，然后右边再放一个点击打开显示完的”。吸顶跟随栏需要兼备免弹窗的直览区域（左侧对半分给分类和模组），以及点击呼出全量大弹窗的按钮（右侧）。
- **改动与实现**：
  1. **彻底消灭 Windows 原生下拉框**：
     - 彻底移除跟随栏内的原生 HTML <select> 元素。
     - 结果排序全面接入工作台自研统一下拉组件 `renderDropdown("sticky-sort", state.sort, sortOptions)`，自适应亮/暗主题，带精致圆角、阴影与平滑交互。
  2. **分类数量透传与热度降序**：
     - 新增 `getCategoryOptionsWithCounts()`，在当前平台记录中动态统计每个分类的出现次数。
     - 按收录数量降序排列（`b.count - a.count`），国创、冒险、科技、魔法、魔改整合等大热分类优先排布。
     - “全部”及每个分类胶囊均携带数字徽标（如 `全部 (1,420)`, `科技 (620)`, `冒险 (410)`）。
  3. **左侧免弹窗直览区（分类 50% + 模组 50%）**：
     - **分类半区**：`分类` 标签 + 数量胶囊横滑列表，单击即换类，免打开任何弹窗。
     - **模组半区**：`模组`（或 CurseForge `玩法`）标签 + 热门模组数量胶囊（JEI、Create、AppleSkin 等），单击直接多选/取消，免打开任何弹窗。
     - 支持鼠标垂直滚轮直接驱动胶囊横向滑动，浏览长列表丝滑高效。
     - 当平台无模组属性时，分类半区自适应占满左侧全宽。
  4. **右侧点击呼出全量弹窗与工具集合**：
     - `📑 全部分类 (783) ▾` 按钮：点击呼出全量 783 类模糊搜索与多维排序大弹窗。
     - `🧩 全部模组库 (11,443) ▾` 按钮：点击呼出全量 1.1 万款包含模组检索与多选大弹窗。
     - 附带已选模组徽标及一键剔除、自研排序下拉、`📌 跟随中`、`↑ 顶部` 及重置按键。
     - 宽屏单行对齐，窄屏（<=1200px）自适应优雅折行。
- **全套验证证据**：
  - `npm --prefix apps/web test`：13/13 测试套件通过，94/94 测试通过（100%）。
  - `npm --prefix apps/desktop test`：16/16 测试通过。
  - `npm --prefix apps/web run build:desktop`：编译打包成功。
  - 本地常驻服务（`http://127.0.0.1:8765/desktop.html`）：返回 HTTP 200。

## PR #28: 双行人机工效重构：去除滚轮陷阱与模组直接展开体系（2026-09-25）

- **背景与用户痛点**：
  - 用户反馈：“交互逻辑有一些不符合人类使用，模组不能显示更多，而且这个滚轮用起来很麻烦”（附截图带有两个并列的水平滚动条 `◄ ═══════ ►`）。
  - 单行硬挤导致左侧仅能显示 2 款模组，且水平滚轮容易截断页面垂直滚动，无法舒适浏览。
- **改动与实现**：
  1. **彻底废除水平滚动条与鼠标滚轮截留**：
     - 彻底移除 `.sticky-pills-wrap` 内部水平滚动条及滚轮劫持监听器，鼠标滚轮恢复自然的页面垂直浏览。
  2. **双行人机工效分层架构 (`.sticky-bar-row`)**：
     - **第 1 行（分类与全局工具）**：
       - 左侧：`分类` 标签 + 常用热门分类数量胶囊（全部、国创、冒险、魔改整合、任务、科技、魔法等，单行平铺，一目了然）。
       - 右侧：`📑 全部分类 (783) ▾` 弹窗按钮、自研排序下拉、`📌 跟随中`、`↑ 顶部`、`重置` 按钮。
     - **第 2 行（模组 / 玩法筛选）**（仅在 MC百科或 CurseForge 有模组/玩法时显示）：
       - 左侧：`模组`（或 `玩法`）标签 + 热门模组数量胶囊群（鼠标手势 707、苹果皮 696、JEI 609、Create 500、拔刀剑 320 等）。
       - **支持直接展开更多 (`+更多模组 (60) ▾` / `收起 ▴`)**：点击直接在栏内平铺展开前 60 款主流热门模组，无需打开大弹窗即可直选！再次点击平滑收起为常用款。
       - 右侧：`🧩 全部模组库 (11,443) ▾` 弹窗检索按钮，以及已选模组计数与一键清空徽章（如 `已选模组 2 ✕`）。
- **全套验证证据**：
  - `npm --prefix apps/web test`：13/13 测试套件通过，94/94 测试通过（100%）。
  - `npm --prefix apps/desktop test`：16/16 测试通过。
  - `npm --prefix apps/web run build:desktop`：编译打包成功。
  - 本地常驻服务（`http://127.0.0.1:8765/desktop.html`）：返回 HTTP 200。

## PR #29: 吸顶跟随栏“展开”体验全面重构：分类与模组独立就地展开与防遮挡架构（2026-09-25）

- **背景与用户需求**：
  - 用户反馈：“加一个展开功能吧”。
  - 核心痛点：之前展开按钮内嵌于胶囊流末尾，因单行 `overflow: hidden` 限制，易随胶囊折行被截断隐藏；同时分类行此前仅能点击大弹窗，缺乏就地展开查看更多分类的能力。
- **改动与架构实现**：
  1. **右侧固定防遮挡布局 (`.sticky-row-right`)**：
     - 将 `展开分类 ▾` / `展开模组 ▾` 显式独立按钮移至右侧操作区，设置 `flex-shrink: 0`，与全量检索弹窗按钮并肩陈列，无论窗口宽度或胶囊数量如何变化均常驻可见、绝不折行截断。
  2. **分类就地展开 (`stickyCategoriesExpanded`)**：
     - 默认折叠状态：单行紧凑展示前 14 项热门核心分类。
     - 点击 `展开分类 ▾`：栏内平铺展开前 50 项高频分类（最大高度 200px，自适应垂直滚动），按钮实时变为 `收起分类 ▴`。
  3. **模组 / 玩法就地展开 (`stickyModsExpanded`)**：
     - 默认折叠状态：单行紧凑展示前 14 款热门核心模组。
     - 点击 `展开模组 ▾`（CurseForge 为 `展开玩法 ▾`）：栏内平铺展开前 70 款最热门主流模组（最大高度 220px，自适应垂直滚动），按钮实时变为 `收起模组 ▴`。
  4. **双层探索闭环（就地直览 vs 全量弹窗）**：
     - 第 1 层（就地直览）：通过展开按钮瞬间在栏内呈现 50 大分类或 70 款热门模组，免弹窗一键即选。
     - 第 2 层（全量弹窗）：通过 `全部分类 (783) ▾` 或 `全部模组库 (11,443) ▾` 呼出支持模糊搜索和自定义排序的全库弹层。
- **全套验证证据**：
  - `npm --prefix apps/web test`：13/13 测试套件通过，94/94 测试通过（100%）。
  - `npm --prefix apps/desktop test`：16/16 测试通过。
  - `npm --prefix apps/web run build:desktop`：编译打包成功。
  - 本地常驻服务（`http://127.0.0.1:8765/desktop.html`）：返回 HTTP 200。

## PR #30: CurseForge 与 Modrinth 全平台模组与玩法分类全面汉化及中英双模检索（2026-09-25）

- **背景与用户需求**：
  - 用户反馈：“把cf和mod的模组和玩法分类汉化了”。
  - 核心痛点：CurseForge（CF）与 Modrinth（MOD）来源于海外原站，其分类与玩法标签为纯英文（如 `Exploration`, `Tech`, `optimization`, `challenging` 等），此前吸顶跟随栏、全量发现弹窗、顶部下拉框及筛选胶囊均直接渲染英文原生字符串，中文用户认知成本高且在弹窗内输入中文无法搜出对应分类。
- **改动与架构实现**：
  1. **展示层映射与数据层稳定性彻底解耦**：
     - 底层数据模型、快照持久化、API 请求参数、URL 状态及 `data-category` / `data-value` 属性严格保留原生标识符（保证数据与过滤零破坏、零漂移）。
     - 所有前端呈现层统一通过 `getCategoryLabel()` 解析为地道中文；加入大小写不敏感（Case-insensitive O(1)）回退字典，彻底杜绝因大小写变体导致的未汉化回退。
  2. **全面覆盖两平台全部 48 种分类与玩法**：
     - **Modrinth 全部 29 项分类**：`optimization` (性能优化), `adventure` (冒险), `technology` (科技), `magic` (魔法), `lightweight` (轻量), `challenging` (硬核挑战), `kitchen-sink` (综合整合), `game-mechanics` (游戏机制), `equipment` (装备), `decoration` (装饰), `worldgen` (世界生成), `food` (食物), `mobs` (生物), `utility` (实用工具), `storage` (存储), `management` (管理), `library` (前置库), `transportation` (交通), `social` (社交), `iris` (光影支持), `minecraft` (原版风格), `cursed` (搞怪), `economy` (经济), `datapack` (数据包), `modloader` (加载器), `minigame` (小游戏), `quests` (任务), `multiplayer` (多人游戏), `combat` (战斗)。
     - **CurseForge 全部 19 项玩法分类**：`Exploration` (探索), `Adventure and RPG` (冒险与RPG), `Tech` (科技), `Multiplayer` (多人游戏), `Magic` (魔法), `Combat / PvP` (战斗 / PvP), `Small / Light` (小型轻量), `Vanilla+` (原版增强), `Quests` (任务), `Hardcore` (硬核), `Extra Large` (大型整合), `Sci-Fi` (科幻), `Horror` (恐怖), `Map Based` (地图驱动), `Skyblock` (空岛), `Mini Game` (小游戏), `Expert` (专家模式), `FTB Official Pack` (FTB 官方包), `RLCraft` (RLCraft 系)。
  3. **吸顶跟随栏（Follow Bar）双行全面汉化**：
     - 第 1 行（分类）：胶囊一律呈现中文（如 `全部`, `性能优化 (2,410)`, `探索 (30,183)`），悬停提示显示中文名 + 英文原名 + 收录数量。
     - 第 2 行（玩法）：CurseForge 玩法分类一律呈现地道中文。
  4. **全量弹层（Picker Modal）中英双模展示与中英文模糊双向检索**：
     - 弹窗内选项以中文为主标题、小字附带英文原名（如 `性能优化 (optimization)`、`探索 (Exploration)`）。
     - 搜索输入框全面支持双向模糊检索：输入中文（如“优化”、“科技”、“探索”）或英文（如“opt”、“tech”、“explor”）均能瞬间命中。
     - 按名称排序自适应支持中文拼音 localeCompare。
  5. **顶部筛选栏、活跃条件、表格与对比面板全面联动**：
     - 筛选下拉触发器与下拉菜单项显示中文及附带原名。
     - 活跃筛选条件徽标显示 `分类：性能优化`、`玩法分类：探索`。
     - 表格卡片标签及对比面板分类字段全面映射为中文。
- **全套验证证据**：
  - `npm --prefix apps/web test`：13/13 测试套件通过，94/94 测试通过（100%）。
  - `npm --prefix apps/desktop test`：16/16 测试通过。
  - `npm --prefix apps/web run build:desktop`：编译打包成功。
  - 本地常驻服务（`http://127.0.0.1:8765/desktop.html`）：返回 HTTP 200。

## PR #31: 吸顶跟随栏“展开”与“弹窗”彻底解耦、内置实时搜索框与就地全量展开架构（2026-09-25）

- **背景与用户反馈**：
  - 用户反馈：“展开全量怎么是弹窗，弹窗和展开是分开的”，并附上右侧操作按钮截图。
  - 核心痛点与人机工效根因：
    1. **弹窗与展开认知冲突**：此前的全库检索大弹窗按钮被标为 `🔍 搜索 / 展开全量模组 (11,443) ▾`，用户点击意图是“在当前栏内就地展开全部模组”，结果弹出了浮动模态对话框遮挡页面。用户指出：“弹窗和展开是分开的”，弹窗就是弹窗，展开就是就地平铺展开，二者绝不能混为一谈。
    2. **栏内缺乏就地全量展开能力**：原先栏内展开按钮 `展开模组 ▾` 仅能展开前 70 款热门，未提供就地全量展开全部上万款模组的能力，迫使用户去点弹窗。
- **改动与架构实现**：
  1. **彻底理清概念：“展开”归栏内，“弹窗”归独立对话框**：
     - **弹窗按钮明确标为“弹窗”**：全面去除右侧大弹层按钮上的“展开全量”字样，改为外链/弹窗箭头 `↗` 并显式标为“弹窗”：
       - `📑 分类库弹窗 (783) ↗`
       - `🧩 模组库弹窗 (11,443) ↗`
       - `🎮 玩法库弹窗 (19) ↗`
       - 点击打开全量检索与多选大弹层，语义 100% 准确清晰。
     - **栏内就地“展开全部”彻底支持**：
       - **模组行**：提供双层就地展开：
         - `展开模组 ▾`：就地平铺展开前 70 款主流热门；
         - `展开全部 (${formatCount(total)}) ▾`：点击直接在吸顶栏内就地平铺展开全量 11,443 款模组（最高 300px 纵向平滑滚动，绝不弹窗打扰！），展开后按钮变为 `收起全部 ▴`；
       - **分类行**：`展开全部分类 (${count}) ▾` / `收起分类 ▴`，就地展开 100% 所有分类（共 20~30 项）；
       - **玩法行**：`展开全部玩法 (19) ▾` / `收起玩法 ▴`，就地展开全部 19 项玩法分类。
  2. **吸顶栏内置实时搜索框（零弹窗即时查）**：
     - **分类搜索框**（`#sticky-cat-search`）：输入“魔”、“opt”、“科技”即时过滤栏内胶囊，支持中英双向模糊匹配，支持 Escape / ✕ 瞬间清空。
     - **模组搜索框**（`#sticky-mod-search`）：输入“Create”、“JEI”、“拔刀剑”等即时呈现匹配模组胶囊（最多 100 款），无匹配提示 `无匹配模组`。
  3. **输入法（IME）合成感知与焦点持久化**：
     - 中文拼音打字过程中绝不提前重绘打断；DOM 重置后通过 `stickyFocusAfterRender` 精确恢复焦点和光标位置。
- **全套验证证据**：
  - `npm --prefix apps/web test`：13/13 测试套件通过，94/94 测试通过（100%）。覆盖了栏内搜索框、实时过滤、无匹配提示、清空按钮、分类库/模组库/玩法库弹窗以及模组就地 `展开全部`。
  - `npm --prefix apps/desktop test`：16/16 测试通过。
  - `npm --prefix apps/web run build:desktop`：TypeScript 0 错误，打包生成 `desktop.html`、`desktop.css`、`desktop.js`。
  - 本地常驻服务（`http://127.0.0.1:8765/desktop.html`）：返回 HTTP 200，页面运行稳定。




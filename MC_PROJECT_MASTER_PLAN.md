# MC_PROJECT_MASTER_PLAN

本文件是当前 Master Plan 中唯一的下一任务摘录，不是另一份路线或第二个任务。用户指定 ChatGPT 负责最终规划，Lunamax 执行；Obsidian 只读，不改正在整理的 Vault。

## NEXT_IMPLEMENTATION_TASK

**任务名：完成 PR #5 的可靠个人标记闭环——B站保存视频，组卡正确反映成员状态。**
**优先级：NOW。执行者：Lunamax。交付单元：现有 `feature/personal-library` / PR #5。**

### Goal

让用户能收藏/标记想玩、在更新与重启后找回同一来源；尤其是 B站出现更新视频后，旧视频的收藏、想玩、评分和备注仍属于原 BVID，并能从组卡与个人筛选找到。

### Why This Is The Next Task

master 尚无正式个人标记，而 PR #5 已实现持久文件、窄 API、个人筛选和多视图入口。修正一个明确的保存/展示对象问题，就能复用已有代码接通“以后回来”。它比新个人工作区更直接，也不必等待百科 Loader/封面补齐。本任务不是单独再做一个 B站补丁并留下 PR5 不交付；它就是现有个人库 PR 的有界修订。信息不全的原站或视频线索仍值得保存。

### Current Truth

- 报告基线 master：`fa47ffe283c0c7b3ce6dcc5293060b68667b2f58`。
- PR #5：OPEN / NOT_IN_MASTER；head `1d80a2c6e4ea50a47350fcb90809feb69e677a96`，branch `feature/personal-library`。
- 报告中的 PR5 worktree：`C:\Users\Administrator\.codex\worktrees\desktop-dashboard\我的世界整合包获取`；主工作目录的旧 cleanup 分支不是实施基线。
- `dataRoot/personal-library.json`，schema=1；key=`platform:sourceId`；状态含 favorite、wantToPlay、played、rating、note、updatedAt。既有状态相互关系不在本任务中重新设计。
- 组卡个人状态必须独立于 latest，绑定来源记录/BVID；组本身不是稳定持久实体。
- 指定 active snapshot 仍 UNKNOWN；不以它作为测试前提，不启动全网抓取或导入来消解该未知。

开始只核对实际 Git/PR/worktree、用户已改动文件及任务涉及代码。状态仍符合时继续同一 branch/PR；不得在 cleanup 树施工，不重置或覆盖别的 Agent 的改动。若 PR 已合并、分支已变或相关实现已变，先回传准确差异，不盲目重做、重复建 PR 或重新全仓审计。

### Scope

1. 复用现有个人库实现。保留 JSON schema、`platform:sourceId`、GET/PATCH API、同目录原子写入、写队列、文本转义与 snapshot 分离；保留收藏/想玩/玩过筛选、评分和备注，不重写整套库。
2. 明确 B站写入目标。视频平铺和详情操作针对该 BVID。组卡按钮标“收藏当前视频”“加入想玩（保存视频线索）”，显示所指视频；点击时捕获对象，异步加载不能改写另一个新 latest。取消只改明确目标，绝不批量取消整组。
3. 组卡成员状态摘要。从本次查询参与归组的成员 BVID 和 GET `/api/library` 状态映射计算已标记成员；独立于 latest 的状态。摘要能定位已有历史成员并打开对应视频/编辑状态，复用现有历史列表，不新建工作区。评分、备注不折叠为组值。
4. 个人筛选与分组顺序一致。B站聚合模式先按非个人条件取得该次查询的成员集合，再归组、附加个人状态并按“至少一个成员符合”筛选组。摘要范围说明为当前查询结果，加载未完成不能用子集作否定结论。视频平铺及其他平台保持服务端分页前个人筛选，不新增全量全平台扫描或新的持久 group 注册表。
5. 仅保护明确的 index fallback。对标准化时确定由数组序号生成的 sourceId，不允许新建个人状态，并显示原因；从生成分支携带最小来源标记，不用 `platform-数字` 正则识别，不改真实源 ID、不迁移 key、不全量修复身份。不要以记录暂时不在 snapshot 为由删除既有个人数据。
6. 最小交接入口。在本 PR 加入/更新 `docs/PROJECT_STATE.md` 并落地本文件；有 AGENTS 时只补入口索引。状态写成 PR 待审，不能写成已合并/当前用户已可用。禁止写 Obsidian，不另做项目报告或路线设计。

### Out Of Scope

MC百科字段/爬虫修复、搜索与总览控件改动、canonical gating、full canonical identity、持久组 ID、A/B、归组算法重写、历史全量审计、新平台、新工作区、最近查看、保存搜索、评分排序、导出恢复、schema 迁移框架、Electron、UI 重写、发布/安装包。

不改用户真实 active pointer，不清理快照，不删除个人文件，不主动 merge/publish。本次交付到同一 PR，交给规划方按差异收口。

### Truth Authority

业务语义以本任务及 Master Plan 为准；实现事实以实际指定 branch/head 的源码、Git/PR、数据合同和本次定向证据为准。保存对象是来源记录/BVID。展示组、snapshotId、canonical 行号、数组位置、最新代表视频都不是可替代的持久包身份。权威个人状态仍是独立的个人文件，不是 UI 缓存或 snapshot 里的投影。

### Expected Modules / Files

先读涉及部分，不是命令逐个改完：

- `apps/desktop/lib/personal-library.cjs`：保持存储合同。
- `apps/desktop/server.cjs`、`lib/data-store.cjs`、`lib/platforms.cjs`：必要的查找/个人筛选与明确 fallback 来源保护；不重构整个服务。
- `apps/web/src/desktopShell.ts`：组卡动作目标、成员状态摘要、个人筛选与已有历史成员入口。
- `apps/web/src/browserApi.ts` 及 B站实际调用的 renderer/types：仅在接口类型或正式 UI 接线需要时修改。
- `apps/web/src/domain/bilibiliGrouping.ts`：原则上只读，复用成员输出；不重写归组规则。
- 已有 `apps/desktop/test/browser-service.test.cjs`、个人库/desktop 的实际相关测试位置，以及已有前端行为用例：按仓库真实位置定位，不新建成套测试框架。
- `docs/PROJECT_STATE.md`、本文件与已有 AGENTS 的最小索引。

### Acceptance Criteria

核心已知实例：同一当前展示组先有视频 A，收藏 A、标记想玩并添加评分/备注；导入包含 A 和更新视频 B 的新受控快照，B 成为代表视频。

- A 的各字段仍归 A，B 未被自动复制状态；组卡能提示并定位已标记的 A。
- 点“收藏当前视频 B”只改 B；取消 B 的收藏不影响 A。只要 A 仍被标记，组摘要不能显示整组未收藏。
- 收藏/想玩筛选能找到 A 所属的当前结果组；视频平铺及详情可找到确切 A。组摘要/计数不只取 latest，也不把尚未完成加载的子集当作完整结果。
- 重启服务、重新加载受控 snapshot 后，原有平台条目及 A 的个人字段恢复；原子写、白名单、转义和文件隔离不因本任务放宽。
- 明确 index fallback 的新记录不能保存持久状态；合法数字源 ID 不因字符串形状受拒绝。未知来源的其他身份治理不扩入本任务。
- 操作失败时不得呈现持久保存成功；旧个人数据不能被覆盖成空文件或迁移到组 key。
- 无需用户手工寻找新视频、构造真实数据目录或反复点击验收；执行方自行用独立 fixture/临时 dataRoot 证明相关行为。未做真实 GUI 时明确说明，不能冒充 GUI PASS。

### Targeted Verification

先检查 PR5 既有持久化/导入/重启用例能证明哪些不变行为；旧结果注明版本与复用理由，不机械重跑所有测试。

围绕 A→A+B 实例，优先扩展一个现有行为用例，覆盖保存对象、组摘要、个人筛选及重启后的关键不变量。fallback 保护用一个明确的无 ID 反例与合法 ID 对照即可。期望值由任务业务规则给出，不复制被测算法自证。

若改动涉及前端点击绑定而已有离线用例不能回答，则用环境已有的浏览器自动化做这个限定交互；不为此安装一套 E2E 平台，不占用用户实际数据与桌面。无法取得的 GUI 证据如实保留，交定向收口，不写通过。

TypeScript 类型变化检查相应 typecheck；只有实际需要运行前端才构建。最小充分证据到位即停。

### Definition Of Done

同一 `feature/personal-library` 分支上的 PR #5 已完成上述有界修订；当前冻结 head、diff、最小验证和未验证范围明确；可用独立数据证明 A→A+B 的状态归属；未改 Obsidian 或真实用户数据；没有新增第二个实施任务。

交付状态如实写 `IMPLEMENTED / READY_FOR_REVIEW / NOT_MERGED`（以现场为准）。最终主线可用必须在实际合并后确认，不能以 PR 打开、代码存在或旧 REVIEW_PASS 代替。

回滚单位是该 PR/相关实现提交；回滚应用代码时保留 `dataRoot/personal-library.json`，不附带数据删除或迁移。无需 canonical/A/B 或其他新功能才能独立验收与回滚。

回传给规划方：**branch/head/base；完成行为；最小证据与未验证项；PR/merge状态；尚存的具体 blocker（没有就写无）。** 不再写第四份全项目审计，不重新生成 Master Plan，不自动开始 Phase 0 的下一项。

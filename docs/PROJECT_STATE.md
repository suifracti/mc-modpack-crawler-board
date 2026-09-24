# 当前实施状态

更新：2026-09-25。本页记录 PR #18 合并后的维护收口状态；历史项目状态仍见 [PROJECT_STATUS.md](PROJECT_STATUS.md)。

## 当前状态：维护收口

- 状态：`MAINTENANCE / NO_ACTIVE_IMPLEMENTATION_TASK`。
- PR #18 已合入 master，合并 SHA：`85b95f2c72dd00606b6e5363c49659bf428e4b86`。
- 当前 master 合并基线：`85b95f2c72dd00606b6e5363c49659bf428e4b86`；本页更新后会产生新的文档提交。
- blocker：无。GUI smoke 是已知未验证项，不构成 blocker。
- 项目不主动启动下一开发任务；后续实施需用户明确指定任务。

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
| PR #18 `codex/integrate-browser-ui` | head `f2096c93bbc43b554c9255c34967f38909712faa`；base `2242a5e48e7bda4a1879eac6e407196b89f5ef02` | MERGED |
| PR #18 合并提交 | `85b95f2c72dd00606b6e5363c49659bf428e4b86`，已进入远端 master | MERGED |

## PR #18 收口

- PR #18 `codex/integrate-browser-ui` 已合并；merge SHA：`85b95f2c72dd00606b6e5363c49659bf428e4b86`。最终业务 diff 为 `desktopShell.ts`、`desktopShell.css`、`platformRenderers.test.ts`。
- 复用合并前 head `f2096c93bbc43b554c9255c34967f38909712faa` 的自动验证：`platformRenderers` 12/12、web typecheck、desktop build 均通过；合并后未机械重跑。
- GUI smoke 未完成：浏览器自动化连续因 `nodeRepl.fetch request failed` 失败；未记为 GUI PASS，也未继续排查或换工具。
- blocker：无；GUI smoke 保留为已知未验证项。


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
- 实施验证未启动全网抓取、未依赖 active snapshot、未修改真实用户数据。PR #5、PR #6、PR #7、PR #8 现已合并；Obsidian Handoff 在收口时同步，未进行发布。
- 归组规则本身不在本轮重写；组卡摘要范围仅承诺当前查询已完成加载的成员集合。

## 交接入口

- [Master Plan](../MC_PROJECT_MASTER_PLAN.md)
- [历史项目状态](PROJECT_STATUS.md)
- PR：[suifracti/mc-modpack-crawler-board#5](https://github.com/suifracti/mc-modpack-crawler-board/pull/5)
- PR：[suifracti/mc-modpack-crawler-board#6](https://github.com/suifracti/mc-modpack-crawler-board/pull/6)
- PR：[suifracti/mc-modpack-crawler-board#7](https://github.com/suifracti/mc-modpack-crawler-board/pull/7)
- PR：[suifracti/mc-modpack-crawler-board#8](https://github.com/suifracti/mc-modpack-crawler-board/pull/8)

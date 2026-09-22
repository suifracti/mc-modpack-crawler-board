# 当前实施状态

更新：2026-09-22。本页是 PR #5 的最小交接入口；历史项目状态仍见 [PROJECT_STATUS.md](PROJECT_STATUS.md)。

## 当前交付

| 对象 | 现场事实 | 状态 |
| --- | --- | --- |
| PR #5 `feature/personal-library` | base `fa47ffe283c0c7b3ce6dcc5293060b68667b2f58`；原 head `1d80a2c6e4ea50a47350fcb90809feb69e677a96` | IMPLEMENTED / READY_FOR_REVIEW / NOT_MERGED |
| 本轮个人标记闭环 | BVID 级写入目标、B站完整成员归组后个人筛选、组卡成员摘要、index fallback 来源保护 | 已实现，待 PR 审查 |

## 已完成行为

- 保持 `personal-library.json` schema=1、`platform:sourceId`、GET/PATCH、原子写入和写队列。
- B站平铺、详情和组卡动作携带明确 BVID；组卡当前视频显示标题/BVID，历史已标记成员可定位到对应详情编辑状态。
- B站聚合先取得当前查询的完整非个人结果，再归组并按“至少一个成员命中”筛选；其他平台和视频平铺继续服务端个人筛选后分页。
- 标准化记录携带 `sourceIdOrigin`；仅当前快照明确标为 `index-fallback` 的记录拒绝新个人写入并显示原因，真实数字或字符串来源 ID 不按外形拒绝。
- 不因新 snapshot 缺少旧记录而删除个人文件或迁移个人 key。

## 最小验证

- `node --test apps/desktop/test/browser-service.test.cjs apps/desktop/test/data-store.test.cjs`：5 tests passed。
- `npm test -- --run tests/bilibiliGrouping.test.ts tests/platformRenderers.test.ts`（`apps/web`）：17 tests passed。
- `npm run typecheck`（`apps/web`）：passed。
- 独立临时 `dataRoot` fixture 覆盖 A→A+B、A 的收藏/想玩/评分/备注重启恢复、B 单独收藏及取消、无 ID fallback 拒绝、合法数字 ID 接受。
- 额外做了一次限定浏览器点击：A+B 组卡显示 B 为当前视频、摘要列出 A；点击 B 的“收藏当前视频/加入想玩（保存视频线索）”后，A 的旧字段仍在，摘要入口可打开 A 详情。

## 未验证与边界

- 未做真实用户数据或发布环境的 GUI/桌面验收；限定浏览器点击仅使用临时 fixture，不代表完整 GUI 矩阵通过。
- 未启动全网抓取、未依赖 active snapshot、未修改 Obsidian、未修改真实用户数据、未合并或发布 PR。
- 归组规则本身不在本轮重写；组卡摘要范围仅承诺当前查询已完成加载的成员集合。

## 交接入口

- [Master Plan](../MC_PROJECT_MASTER_PLAN.md)
- [历史项目状态](PROJECT_STATUS.md)
- PR：[suifracti/mc-modpack-crawler-board#5](https://github.com/suifracti/mc-modpack-crawler-board/pull/5)

# 当前项目状态

更新：2026-09-20。此页维护当前工程入口；阶段报告保留历史原意。

| 对象 | 源码基线 | 状态 |
| --- | --- | --- |
| 本地看板/整理基础 | `4bf5e0fe4c614f3e630ae242db2ed5b66ef95fea` | 已有可用本地看板；本轮整理不改变运行时或生成数据 |
| A：B站 runtime 候选 | `9c51a557401119621c6cef90726e575f529c74bb` | 已停止、未集成；完整独立安全验收 BLOCKED |
| B：integration base v3 | `9b38c34fbe5b26a4d684c104a992f55492e49519` | 已停止、未集成；不是已发布版本 |

A 的交接报告记录原 26/27/5 门禁通过，同时保留 28 个冲突关系 case 和 277 个未覆盖 holdout pair。BLOCKED 指独立安全证据不完整，不代表整个产品不能使用，也不能改写成完全验收。

本轮没有合并 A/B、定稿 Truth Matrix、运行 production cutover 或重新采集数据。GitHub 源码同步与部署看板是两件事。

## 从两个脚本到现在

1. 采集从 MC百科扩展到六个平台，各平台保留独立 crawler。
2. 原始快照后增加 canonical SQLite、统一模型和平台适配器。
3. 导出器拆分，数据与前端文件分离；前端发展为 TypeScript/Vite 工程。
4. 搜索、筛选、版本弹窗、平台展示逐步模块化，增加字段来源与回归检查。
5. B站归组的后续实验留在 A/B，没有全部进入当前看板。

`web/`、旧转换器、`apps/web/src/legacy/` 仍有真实依赖，不能直接删除。

## 当前任务

整理后进入 [跨平台本地浏览器服务与采集更新](DESKTOP_TASK.md)。用户转发任务书，lunamax 实施，Codex 统筹与审核。沿用现有可用源码，不以重新完成全量归组审计作为桌面开发的前置条件。

## 文档入口

- [开发说明](DEVELOPMENT.md)
- [搜索契约](SEARCH_CONTRACT.md)
- [历史 Feature Truth Matrix](FEATURE_TRUTH_MATRIX.md)：保留原阶段记录，本轮未定稿。
- [审计索引](audit/README.md)
- [仓库整理记录](REPOSITORY_CLEANUP.md)

# 审计材料索引

当前状态以 [PROJECT_STATUS.md](../PROJECT_STATUS.md) 为准。保留历史证据，不把旧 PASS 自动升级为新版本结论。

当前整理基线包含：

- [Bilibili 归组审计](BILIBILI_GROUPING_AUDIT.md)
- [MC百科模组搜索审计](MCMOD_INCLUDED_MODS_SEARCH_AUDIT.md)
- [发布日期来源审计](RELEASE_DATE_SOURCE_AUDIT.md)

未集成 A 的最终报告在 `fix/phase3gf-f3a-runtime` 的 `docs/audit/PHASE_3GF_F3A_INDEPENDENT_SAFETY_AUDIT_2026-09-20.md`；B 的最终报告在 `integration/phase3gf-ab-v2` 的 `docs/audit/PHASE_3GF_F3B_REPORT.md`。切换对应 ref 阅读，不复制成当前已验收报告。

`pipeline/audit/` 的程序与 fixture 保留供回归和复现。大体积本地日志、数据库和浏览器数据不进入源码。

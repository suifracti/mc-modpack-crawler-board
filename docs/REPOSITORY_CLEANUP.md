# 仓库整理记录 · 2026-09-20

## 范围

基于 `4bf5e0fe4c614f3e630ae242db2ed5b66ef95fea` 整理仓库、GitHub 展示与下一轮入口。运行时代码、采集数据、生成看板、production state 和正式 Truth Matrix 均未改变。

## 已整理内容

- 中英文 README 对齐六平台与现代前端，移除无效参数和现代看板“双击 HTML”说明，保留原许可、AI 生成与第三方内容声明。
- 增加当前状态、开发说明、审计索引和桌面任务书，明确可用基线与 A/B 候选的区别。
- 补充凭据、虚拟环境、缓存与打包产物忽略规则。
- 15 个旧阶段分支转为 `archive/2026-09-20/<原分支>` 标签，保留原提交历史，不赋予新的 PASS 含义。
- 7 个停用 worktree 压缩并逐文件 SHA256 回读校验后移除。保留主工作目录及最新 A/B 两个 worktree。
- 源码历史整体保存为 Git bundle；旧 worktree 中源码、数据和证据保存在本地压缩包，未备份可重装的 `node_modules/`、`__pycache__/` 和 worktree `.git` 指针。

## 恢复

本机备份目录：`D:/ai/backups/mc-modpack-cleanup-20260920/`。

- `repository-before-cleanup.bundle`：整理前完整 Git refs 与历史，已通过 `git bundle verify`。
- `branch-archives.json`、`refs-before.txt`、`worktrees-before.txt`：旧名称、路径和提交映射。
- `mc-*.zip`、对应 `*.manifest.json`：停用 worktree 的文件与 hash 清单。

恢复源码可从历史 tag 新建 worktree；恢复本地数据时将对应压缩包解到新的恢复目录，再按需要取回文件。不要将 ZIP 直接覆盖当前工程。

## 验证与限制

- 整理基线 typecheck 通过；Vitest 11 个文件、80 tests 通过。A 报告中的 103 tests 属于另一个候选源码，不混用结果。
- CLI `--help` 核对了实际平台和参数。
- 待推送本地分支历史检查了 914 个带路径对象；常见凭据模式未命中，最大新增 blob 约 1.99 MB。此检查不等于完整秘密审计。
- 主目录旧浏览器缓存批量删除被自动审批阻止，保留在忽略的 `build/`，未绕过限制。
- 未重跑联网采集、全人口审计、完整 Python 数据依赖套件或生产发布。

GitHub 通过整理分支/PR 同步源码，A/B 单独备份，历史 ref 通过 archive tags 保留。默认分支合并仍按既有协作规范处理，不能把源码备份解释为候选功能验收或生产部署。

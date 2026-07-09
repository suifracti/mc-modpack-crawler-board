# MC Modpack Crawler Board

MC 整合包爬虫与看板。当前阶段主要完成了 MCMod 的抓取、数据转换和本地 HTML 看板；后续目标是把更多 MC 整合包平台接入同一套数据结构。

MC modpack crawler and dashboard. The current implementation mainly supports MCMod crawling, conversion, and a local HTML dashboard. The long-term direction is to add more MC modpack platforms under one shared data model.

## 当前状态 / Current Status

- 已实现 / Implemented: MCMod 爬虫、JSONL 数据输出、趋势历史读取、HTML 看板生成。
- 当前只完成了 MCMod；其他平台属于后续扩展方向。
- This project currently supports MCMod only. Other platforms are planned future extensions.

## 核心文件 / Core Files

| 路径 / Path | 作用 / Purpose |
| --- | --- |
| `多平台聚合爬虫_v1.0.py` | 抓取平台数据；当前主要是 MCMod。 |
| `多平台聚合转换器_v1.0.py` | 把 JSONL 和趋势历史转换成 HTML 看板。 |
| `多平台爬虫数据_v1.0.jsonl` | 当前主数据快照。 |
| `trend_history/` | 本地长期趋势历史。 |
| `多平台聚合看板_V1.0.html` | 生成后的本地看板。 |
| `LOCAL_FILE_MAP.md` | 给用户和后续 AI 的项目地图。 |
| `history_sources/` | 从旧归档整理出的历史源码参考。 |

## 本地私有文件 / Local-Only Files

这些内容不要提交到 Git:

- `ignored_local_files/browser_data/`: 浏览器登录状态、Cookie、缓存。
- `ignored_local_files/归档/`: 旧版本、旧实验、截图和备份。
- `.agents/`: AI 工具工作记录。
- `.vscode/`: 本机编辑器配置。
- `__pycache__/`: Python 自动缓存。

Do not commit these local/private/tool files to Git.

## 基本流程 / Basic Workflow

1. 运行爬虫，更新 `多平台爬虫数据_v1.0.jsonl` 和 `trend_history/`。
2. 运行转换器，生成 `多平台聚合看板_V1.0.html`。
3. 检查看板效果。
4. 满意后再提交并推送 GitHub。

## 给后续 AI 的提示 / Prompt For Future AI

```text
这是一个 Git 仓库，根目录是 [local-project-path]。
This is a Git repository. The root directory is [local-project-path].

项目名建议使用 mc-modpack-crawler-board，中文可理解为“MC 整合包爬虫与看板”。
The recommended repository name is mc-modpack-crawler-board.

当前实现只完成了 MCMod；不要误以为其他平台已经完成。
The current implementation supports MCMod only; do not assume other platforms are implemented.

开始前先看 LOCAL_FILE_MAP.md 和 git status --short --ignored。
不要覆盖用户已有改动，不要提交 ignored_local_files/、.agents/、.vscode/、__pycache__/。

提交前必须检查 Git 作者身份：
git config user.name
git config user.email

正确身份应该是：
suifracti
[redacted]

如果显示 Antigravity、Codex、Google、OpenAI 或其他工具身份，先停止并改成本仓库用户身份，不要直接提交。

完成后如果用户明确要求“同步 GitHub”，请先说明改动范围，运行必要检查，然后 git add、git commit、git push。
不要在用户没有确认的情况下把不相关改动一起提交。
```

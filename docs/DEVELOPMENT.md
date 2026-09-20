# 开发与构建

从仓库根目录执行。开发环境需要 Python 3、Node.js/npm；前端依赖以 `apps/web/package-lock.json` 为准。这些开发依赖不等于未来桌面用户的安装要求。

## 采集

```powershell
python "多平台聚合爬虫_v1.0.py" --help
python "多平台聚合爬虫_v1.0.py" --platform mcmod
python "多平台聚合爬虫_v1.0.py" --platform bilibili --bili-pages 1 --bili-max 20
```

平台选项：`mcmod`、`bilibili`、`bbsmc`、`xyebbs`、`modrinth`、`curseforge`、`all`。示例采集命令会真实联网，各平台访问条件和抓取范围不同。

旧 README 的 `--refresh-days` / `--refresh-all` 未被当前统一入口实现，勿沿用。交互入口可能在采集后询问是否运行旧转换器；现代预览流程请选择不转换。自动任务始终显式传平台。

`--auto-convert` 调用旧转换器并写入 `converted_output/`，不是现代前端的安全更新入口。

## 隔离预览

```powershell
npm --prefix apps/web ci
python pipeline/run_pipeline.py --pipeline v2 --mode staging --build-db
python pipeline/stage_frontend_preview.py
python -m http.server 8766 --bind 127.0.0.1 --directory build/frontend_preview
```

打开 <http://127.0.0.1:8766/>。需要先提供有效 `crawler_output/` 数据；未采集的平台不会凭空出现。生成 canonical 数据库与 legacy preview 后，staging 脚本准备现代前端、数据和样式。以上不执行生产切换。

`npm --prefix apps/web run build` 只构建前端，不会独立生成完整平台数据。

## 本地浏览器服务

桌面交付当前采用跨平台 Node.js 本地服务，不再打包 Electron EXE。构建并启动：

```powershell
npm --prefix apps/web run build:desktop
npm --prefix apps/desktop start
```

服务默认监听 `127.0.0.1:8765`，通过同源 HTTP API 和 SSE 为浏览器页面提供数据读取、筛选、详情、更新进度和取消操作；更新仍由现有 Python worker 在隔离目录执行。可用 `npm --prefix apps/desktop run start:no-open` 禁止自动打开浏览器，更多参数见 [`apps/desktop/README.md`](../apps/desktop/README.md)。

## 验证与协作

```powershell
npm --prefix apps/web run typecheck
npm --prefix apps/web test
```

Python 检查位于 `tests/`、`pipeline/tests/`，不少依赖本地数据库、固定快照或生成前端，运行前阅读对应依赖。缺数据应如实报告，不将其当作源码回归或吞掉后宣称全套通过。

同一任务使用一个短期分支和一个 PR，返修继续原分支。当前状态统一维护在 [PROJECT_STATUS.md](PROJECT_STATUS.md)。仅文档与仓库维护不重复联网全量采集或全人口审计。移除旧路径前必须检查实际调用关系。

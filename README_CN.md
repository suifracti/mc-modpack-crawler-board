# Minecraft 整合包看板

[English](README.md) · [当前状态](docs/PROJECT_STATUS.md) · [开发说明](docs/DEVELOPMENT.md) · [桌面软件任务书](docs/DESKTOP_TASK.md)

用于本地查找、筛选、查看 Minecraft 整合包的工具。已有 **MC百科、哔哩哔哩、BBSMC、XYEBBS、Modrinth、CurseForge** 六个平台的采集与展示代码，可查看版本、模组和来源记录并跳转原站。

目前形态是 **Python 数据流水线 + TypeScript/Vite 网页前端 + 跨平台本地浏览器服务**。服务监听本机地址并可自动打开浏览器，Windows、macOS 和 Linux 使用同一套入口；当前不再交付 EXE。

## 使用已有看板

本机已有完整 `converted_output/index.html`、`assets/` 和 `data/` 时，在仓库根目录运行：

```powershell
python -m http.server 8765 --bind 127.0.0.1 --directory converted_output
```

浏览器打开 <http://127.0.0.1:8765/>。现代前端使用 JS 模块，应使用本地 HTTP 打开；整个输出目录要保留完整。

刚 clone 的仓库只有源码，没有抓取数据或预生成看板。首次采集和预览步骤见[开发说明](docs/DEVELOPMENT.md)。

## 目录说明

| 路径 | 用途 |
| --- | --- |
| `多平台聚合爬虫_v1.0.py`、各平台 crawler | 统一采集入口及六平台实现 |
| `pipeline/` | Canonical SQLite 数据模型、平台适配、导出与发布工具 |
| `apps/web/` | 现代前端源码和单元测试 |
| `apps/desktop/` | 跨平台本地浏览器服务、更新管理和数据快照 |
| `web/`、`多平台聚合转换器_v1.0.py` | 共用样式及仍在使用的旧转换兼容路径 |
| `tests/`、`pipeline/tests/` | Python 检查，部分依赖本地数据 |
| `docs/` | 当前状态、契约、开发说明和历史证据 |
| `feedback/` | 可选反馈服务模板 |

采集数据 `crawler_output/`、看板 `converted_output/`、数据库和构建 `build/`、登录凭据及缓存留在本地，不提交 Git。

## 启动本地浏览器服务

在仓库根目录执行：

```powershell
npm --prefix apps/web run build:desktop
npm --prefix apps/desktop start
```

服务默认打开 <http://127.0.0.1:8765/>。不自动打开浏览器时使用 `npm --prefix apps/desktop run start:no-open`。详细参数和数据目录说明见 [`apps/desktop/README.md`](apps/desktop/README.md)。

也可以直接双击仓库根目录的 `start_browser_service.cmd`（Windows）或 `start_browser_service.command`（macOS）；Linux 可运行 `start_browser_service.sh`。启动器会先构建前端，再启动服务并打开默认浏览器。首次在 macOS 双击时如系统拦截，请在 Finder 中右键选择“打开”。

## 当前边界

六平台有实现不等于所有字段和包身份都已核实。未知信息保留未知。B站归组仍有启发式判断，最新 A 候选尚未集成、独立安全覆盖不完整。详见[当前状态](docs/PROJECT_STATUS.md)；历史 Truth Matrix 不代表当前版本完整安全认证。

## ⚠️ 使用说明与限制

- 本项目不是 MC百科官方工具，与 MC百科（MCMod）、Minecraft 官方或任何整合包作者没有合作关系。
- 数据采集脚本未获得第三方数据源的官方授权。
- 建议用于个人学习、本地整理和低频增量更新。
- 请勿进行高频访问、绕过访问限制、公开分发完整抓取数据或用于商业用途。
- 使用者应自行评估运行环境、数据来源和相关风险。

---

## 🔒 隐私说明

部分目录可能包含：

- 浏览器登录状态
- Cookie
- Token
- 本地配置

请勿上传或分享包含个人账号信息的文件。

---

## 🤖 AI 生成说明

本仓库的**代码、文档、配置、提交说明及上传过程，均由 AI 完整生成（或实质全部由 AI 完成）**。人类维护者未对每一行做人工编写或逐行背书。

AI 输出可能错误、不完整或不安全，**使用前请自行审查与测试**。公开本仓库不代表对正确性、安全性或任何抓取方式的担保与背书。

---

## 📄 数据与评价说明

本项目展示的数据：

- 排序
- 指数
- 趋势
- 评论整理

均为本地数据处理结果，仅用于信息整理和参考，不代表对任何整合包作品质量的官方评价。

---

## License

**未授予开源许可（No open-source license is granted）。**

本仓库仅供**个人学习与技术参考**。你可以阅读代码用于学习；本说明不授权商用、不授权再分发完整抓取数据，也不把本项目当作任何官方/授权产品。

第三方内容（包括但不限于整合包、模组、网页内容、评论等）版权归原权利人所有；本仓库不授予对这些内容的任何权利。

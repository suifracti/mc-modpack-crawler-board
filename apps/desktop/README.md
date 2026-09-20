# Windows 桌面看板

开发预览需要 Node.js/npm；最终便携包通过 `scripts/build_desktop.ps1` 打包 Electron、桌面 renderer 和应用内嵌的 Python runtime。用户启动便携 exe 后不需要命令行、Node 或单独安装 Python。

```powershell
./scripts/build_desktop.ps1 -Target portable
```

包内不会包含仓库 `.git`、浏览器 profile、Cookie、token、个人数据库或审计目录。数据快照写入 Windows 用户数据目录（Electron `app.getPath('userData')`）下的 `data/`，更新先写 `incoming/`，校验成功后通过 active pointer 切换；旧快照不被覆盖。

如果还没有数据，桌面应用会显示可操作的空状态。可以选择已有 `converted_output`、`build/frontend_preview` 或其 `data` 目录导入。导入的是数据文件，不会执行选中目录里的 JavaScript。

更新任务一次只允许一个平台；平台参数显式传给现有对应 crawler。更新入口不调用统一爬虫的 `--auto-convert`，也不写仓库 `converted_output/`。

开发时可用 `MC_DESKTOP_PYTHON` 指定 Python；便携构建默认下载 Python 3.12.10 embeddable runtime。首次联网更新是否成功取决于平台访问、限流和登录状态，应用会把真实失败原因留在任务日志中。

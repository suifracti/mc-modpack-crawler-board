# 本地浏览器服务

本项目不再打包 Electron EXE。它由 Node.js 启动一个仅监听本机的 HTTP 服务，并在默认浏览器打开看板，因此 Windows、macOS 和 Linux 共用同一套入口。

## 启动

在仓库根目录先构建桌面前端：

```powershell
npm --prefix apps/web run build:desktop
```

启动服务并自动打开浏览器：

```powershell
npm --prefix apps/desktop start
```

只启动服务、不自动打开浏览器：

```powershell
npm --prefix apps/desktop run start:no-open
```

仓库根目录也提供一键启动器：Windows 双击 `start_browser_service.cmd`，macOS 双击 `start_browser_service.command`，Linux 运行 `start_browser_service.sh`。启动器会先构建前端；服务运行期间不要关闭它打开的终端窗口。

默认地址为 `http://127.0.0.1:8765/`。可用参数覆盖本机端口、数据目录和 Python 命令：

```text
node apps/desktop/server.cjs --port 8765 --data-root <本地数据目录> --python <python3路径>
```

服务默认使用系统用户数据目录保存快照：Windows 为 `%APPDATA%/MCModpackBoard/data`，macOS 为 `~/Library/Application Support/MCModpackBoard/data`，Linux 为 `$XDG_DATA_HOME/MCModpackBoard/data` 或 `~/.local/share/MCModpackBoard/data`。也可通过 `MC_DESKTOP_DATA_ROOT` 指定。

## 浏览器端能力

- 浏览器页面通过同源 HTTP API 读取状态、完整数据筛选、评论和版本详情。
- 更新任务仍由现有 Python worker 执行，单次只允许一个平台，事件通过 SSE 推送到页面。
- 选择已有数据时，浏览器服务会要求输入本机数据目录路径；服务不会执行被导入目录中的 JavaScript。
- 外部来源链接在新浏览器标签页打开。
- 更新继续使用隔离 workspace、合同校验、active pointer 和旧快照保留机制。

## 依赖与边界

开发运行需要 Node.js、Python 3 和现有采集器依赖；服务只监听 `127.0.0.1`，不作为公网服务使用。平台访问限制、登录态、限流和网络失败会按真实结果显示，不会把失败伪装成成功。

`main.cjs`、`preload.cjs` 和旧 Electron 测试文件暂留作为历史实现参考，但当前启动脚本和交付路径不再使用 Electron 或生成 EXE。

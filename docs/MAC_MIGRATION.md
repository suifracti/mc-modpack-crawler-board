# MC Mac 接手说明

## 2026-10-06 默认主线与固定 Mac 目录

后续开发固定使用 `master`。已验整合基线为 `644d9e290dc29d8fb82e29108a876d4f80424465`，本轮正常合回原远端 `master@42251392a44edb1eab6285c810fae3ee69b19292`，保留提交历史；不再以迁移/整合候选分支作为默认入口。

固定 Mac 源码目录为 `$HOME/backup/ai/work/zhenghebao/mac-integration-20261005`，运行数据为 `$HOME/Library/Application Support/MCModpackBoard-migration-20261006/data`，交付原包另在 `$HOME/backup/ai/work/zhenghebao/MC-migration-20261006`。沿用已有恢复位置，不创建每个任务独立的默认目录。仓库外 `start-mc-v2.command` 是当前本机启动入口。

```sh
cd "$HOME/backup/ai/work/zhenghebao/mac-integration-20261005"
git switch master
git pull --ff-only origin master
npm --prefix apps/web run build:desktop-v2
SSL_CERT_FILE=/etc/ssl/cert.pem node apps/desktop/server.cjs --host 127.0.0.1 --port 8765 \
  --frontend-root "$PWD/build/desktop-v2/frontend" \
  --data-root "$HOME/Library/Application Support/MCModpackBoard-migration-20261006/data" \
  --python "$(command -v python3)" --no-open
```

本机 Node v24.18.0 / npm 11.16.0 / Python 3.14.6；依赖安装与 V2 构建已通过。Python 默认 CA 文件缺失，启动时局部使用系统 `/etc/ssl/cert.pem`，未禁用证书校验。完整 ZIP 和逐文件 SHA256 已核对；Mac 自己的快照指针已生成，近期增量与 Windows 来源证据分开保留。个人 JSON 和拒绝账本哈希保持一致；交付个人库实际为空，canonical 未重建，不扩大为完整业务验收。当前范围见 [PROJECT_STATE.md](PROJECT_STATE.md)。

以下为 2026-10-05 原交接记录，保留来源和历史边界；当前分支、Mac 已验状态与目录以上节为准。不要因历史“未推送/未验”文字重新建立候选或重放旧补丁。

2026-10-05分支整合补充：最终接手分支为 `codex/mac-integration-20261005`，从已推送的 `codex/mac-migration-20261005@6a2516054e337c0ffb9795df999f56ea511b7b6b` 建立。本轮仅更新三份交接/状态文档；运行源码、数据格式、依赖和两个数据ZIP内容未改变。完整分支处理结果见 [BRANCH_INTEGRATION_20261005.md](BRANCH_INTEGRATION_20261005.md)。最终整合SHA另见私下交接记录，尚未获得新整合分支的推送批准；不要把旧迁移分支当作最终整合版本。

2026-10-05。用户已指定本轮负责迁移整理；53个源码、测试与必要源资源按当前工作树保存。迁移仅本地提交，推送另待用户确认；没有合并、部署或删除原目录，全部11个worktree保留。

## 仓库、分支与成果归属

- 仓库：https://github.com/suifracti/mc-modpack-crawler-board （当前 public，保持不变）。
- 主目录：Windows主目录（绝对路径仅保留在本地交接清单），`codex/integrate-browser-ui`，HEAD `9fe154faa7f6755ba0737e772c36f3b5ac6df0a0`。
- 本地迁移分支：`codex/mac-migration-20261005`，直接以该 HEAD 的当前文件为基线，保存已核对的未提交修改；不是将相对 master 的整包差异再应用一次。
- GitHub master 当前 `42251392a44edb1eab6285c810fae3ee69b19292`；主目录与它有实际差异，不能直接切到 master 替代本机已交付源码。
- 其他 worktree 中的封面恢复、深色主题、筛选/个人区布局、MC封面采集、收藏更新通知与个人库代码，已是主目录 HEAD 的祖先，不再次 cherry-pick。
- `mc-3gf-i3v2` 的 B 候选 `9b38c34fbe5b26a4d684c104a992f55492e49519`、A 候选 `9c51a557401119621c6cef90726e575f529c74bb` 未集成；独立安全证据存在历史 BLOCKED，保持候选身份。
- PR #21 `codex/compact-snapshot-status` / `3ac30a42676bf361e4cecbffe32be897d2ddf227` 仍 OPEN，未合入本次主目录；只保留分支和 PR，不自动合并。
- 个人库旧 worktree 的 `docs/PROJECT_STATE.md` 未提交收口说明和 `personal-library-review.patch` 保留原位。代码已合入，不重新应用补丁。
- 当前 app 内只有本对话在维护 MC。旧负责人对话已归档，用户明确不再将旧对话回复作为前置；整理前未发现其他MC任务或项目进程实际写入，53文件与盘点一致。候选与旧worktree不处理。

具体53文件范围见 `MAC_MIGRATION_FILES.json`；逐文件大小与校验值另保留在私下交接清单。新增源码、测试、平台图标属于源码资源；排除 `.env`、凭据、用户资料、原始/生成数据、浏览器状态、node_modules、build、缓存、模型和运行 ZIP。B站设计文档原交接要求不默认提交，本次先列为留存材料。

## 依赖与构建

- Node.js：建议 Mac 使用 24 LTS（或受支持的22 LTS），见 https://nodejs.org/en/about/previous-releases 。Windows 既有验证版本为 26.7.0，不声称 Mac/Node24 已运行通过。
- npm：使用所选 Node 配套版本；安装依赖执行 `npm ci`，保留现有 lockfile。锁定包包括 Vite 6.4.3、TypeScript 5.9.3、Vitest 2.1.9；桌面 Node 服务无额外 npm 运行依赖。
- Python 3.10+，Mac 使用 `python3`。Windows 既有验证为 3.14.7；桌面 worker、B站公开HTML、CF官方/CFWidget当前路径使用标准库，不依赖模型。
- 老统一采集器的 Playwright、旧登录二维码 qrcode 属于可选历史路径，不是启动浏览器工作台的前提。本次不安装，不把受限B站API/登录路径作为恢复方案。
- Chrome 或其他现代浏览器；Mac `open`、Python SSL/CA、文件系统权限等仍须在 Mac 核对。不可通过禁用证书校验修网络问题。

在最终整合分支获准推送、远端完整SHA核实后，Mac 执行：

```sh
git clone https://github.com/suifracti/mc-modpack-crawler-board.git
cd mc-modpack-crawler-board
git switch --track origin/codex/mac-integration-20261005
git rev-parse HEAD # 与最终交接的迁移提交SHA核对
node --version
python3 --version
npm --prefix apps/web ci
npm --prefix apps/web run build:desktop-v2

# 用独立数据目录，明确选V2；初次不自动打开浏览器。
node apps/desktop/server.cjs --host 127.0.0.1 --port 8765 \
  --frontend-root "$PWD/build/desktop-v2/frontend" \
  --data-root "$HOME/Library/Application Support/MCModpackBoard-migration/data" \
  --python "$(command -v python3)"
```

打开 `http://127.0.0.1:8765/`。数据目录位于仓库之外，与Mac原有MCModpackBoard目录分离。不要运行 `npm start` 的IPv6默认绑定来代替这里的本机监听。关闭终端或 Ctrl+C 停止服务。

既有 `start_browser_service.command/.sh` 在 Git 中有可执行位与 LF，但它们构建 V1 `build:desktop`，不是本次已交付 V2；先使用上面显式命令。Windows `Start-Windows.cmd` 是旧运行包入口，Mac 不使用。

## 数据与配置

Git clone 仅有源码，不能凭空获得本机数据。另行转移文件及逐文件 SHA256 见本地 `migration-inventory.json`，只通过U盘/局域网/用户指定私有渠道提供，不能上传到此公开仓库或 GitHub Releases。

1. Windows 生产 active 仍是 `20260928091436829-095ebe`。为保留本地丰富资料，转移该快照的 `data/`、`crawler_output/` 与快照说明；使用页面“选择数据 → 导入外部数据包”，选择副本所在目录。它在 Mac 独立数据目录建立新快照，不运行源目录JS，不替换 Windows 指针。导入所需 `data/` 中包括 comments/mods 子目录，不能只拷六个列表。
2. 该生产快照的 manifest 记录 CF 原始行101,899，B站1,857；这与公开目录的唯一存档口径不同，未新增核验或清理。不能用线上75,371条直接描述该快照，也不能为迁移过滤旧行。
3. 10月4日六源最新隔离 raw 共约104 MB，另外保留为“近期增量输入”。尚未切入生产；尤其CF/B站与生产日期、丰富字段不同，不能直接覆盖生产 raw/sidecar。Mac 后续只按有证据的观察字段归并。
4. `personal-library.json`、`favorite-updates.json` 是用户私有连续性资料，单独传输，放到 Mac 新 dataRoot 对应根目录；先停止新服务，确认目标是新空目录后再复制，不覆盖已有 Mac 库。个人 JSON 不入 Git。
5. 本轮真实B站账本为 `mc-html-entry-live-state.json`，含每日尝试、隔离失效视频与 stopHistory。迁移到新 dataRoot 的 `collector-state/bilibili-public-html-state.json` 前核对已有账本；不得清空、重置后重抓。Windows 生产 dataRoot 未发现该标准位置账本，原任务路径必须单独交付。
6. `canonical.db` 是可重建产物（500,740,096字节），源码Git不含它。浏览侧可用 sidecar，导入后 canonicalReady 应按实际重建状态显示；不要手写“已ready”或改原manifest来伪造完整。
7. 生产整个目录约48.9GB、149,186文件，全部旧快照在Windows保留。它们不作为本次默认整包传输，但没有删除；若Mac也要完整历史，应再按清单单独复制，不能声称已经转移。

CF无Key默认CFWidget缓存，已有Key或 `CURSEFORGE_API_KEY_FILE` 则使用官方接口；`CURSEFORGE_PROVIDER=official|cfwidget` 可明确选定。凭据文件由Mac本地创建，不从聊天/仓库获取。选定提供方后拒绝即停，不回退。详细限制见 `docs/CURSEFORGE_API.md`。

## 当前能力、证据与边界

V2支持六源浏览/筛选、来源小窗资料/版本/图片与外部入口、左右资料与个人区、关闭/最小化、个人库、本地快照导入、分源隔离更新、取消及下次恢复。跨来源关联保留身份，不自动合并记录。页面聚合元数据并跳原出处，不提供整合包下载。

Windows既有证据：10月2日运行包51文件一致性与空目录启动，隔离GUI的导入/取消/恢复/部分提示/403拒绝保护通过；这些采集用保存网页回放。10月4日是真实在线有界增量及B站两页观察、CFWidget一个已知包读取，独立记录，不混称回放或六源全量刷新。随后B站404单视频隔离、CF官方认证/分页与缓存保留边界有针对性用例；相关TypeScript与构建通过。本次迁移文档不重跑全套旧测试。

线上 Pages最后已验证 `2e484b6c976c6c1db9e28c0f9a31a727fc99e8fa`，75,371条，CF46,529，B站1,865（候选932）。局部CFWidget响应时间10月4日21:26:56北京时间，上游缓存抓取时间未知。这是10月4日证据，不是10月5日刷新。本次不重新部署。

已知限制：B站API/search受robots限制，公开HTML新增发现仅已知有效种子/官方合集；CFWidget仅已有ID缓存核查，默认20/上限50，不能发现全站新包，官方Key认证仍未真实验证；9条新增MC百科记录仅有标题/ID/URL等最小检查点，丰富详情尚缺；A/B安全候选未集成，PR21未合并。新版CFWidget入口未重做GUI验收。已验Windows ZIP不含后来源码修复，保持原SHA，不重打包。

## Mac最小接手验证（尚未执行）

1. 确认迁移提交SHA、运行时版本；一次 `npm ci` + V2构建。
2. 仅在仓库外独立空dataRoot启动到页面可访问，确认V2及所选dataRoot；初次不联网采集。
3. 从单独传输的生产数据副本导入，核对六源可读、一条详情和个人状态；记录数据口径，不把线上计数当导入基准。原Windows指针及私人资料哈希保持不变。
4. 拒绝账本完整转移后，需要采集时才做一个有界来源动作；如果 Mac 取消/进程信号路径有真实问题，仅测取消→下次恢复。不要默认重跑GUI矩阵、全源采集、网页回放或冻结包。

待完成：用户确认最终整合分支与提交后才推送；Mac取得最终整合源码和私下交付数据，完成上述最小验证。Windows全历史快照尚未迁至Mac，按用户要求不计入迁移必需完成项。此前不删除Windows目录或worktree。

## 实际取得非Git数据

Windows已准备两个可复制的离线ZIP与 `SHA256SUMS.txt`，它们留在私下交接目录，**不在Git、Releases或公开下载地址**。它们是准备好的交付文件，不能称Mac已经收到或导入。最直接方式是用户将两个ZIP与校验文件复制到U盘/移动硬盘的 `MC-migration/`，然后连接Mac；也可以用用户控制的私有文件传输，勿上传公开分享链接。

- `public-origin-data-20261005.zip`：生产快照data（含comments/mods）、原始crawler_output及旧备份、六源10月4日隔离输入；另含两个保存HTML测试样本。这里的“公开来源”描述资料来源，并非授权公开再分发。
- `private-state-20261005.zip`：私人收藏/备注与更新状态、B站拒绝/隔离账本、原Windows指针和带本机路径的快照来源说明。只在私下交付，不能进入公开仓库。

Mac通过Finder将 `MC-migration` 文件夹复制到用户自己的目录，例如 `~/MC-migration`，然后：

```sh
cd "$HOME/MC-migration"
shasum -a 256 -c SHA256SUMS.txt
unzip public-origin-data-20261005.zip -d public-origin-data
unzip private-state-20261005.zip -d private-state
```

解压后两个 `TRANSFER-MANIFEST.json` 给出逐文件大小与SHA256；复制/解压失败或校验不符则停止导入。页面导入选择 `~/MC-migration/public-origin-data/production-snapshot`；不要选择 recent-incremental 覆盖生产快照。近期输入单独保存等待有证据的字段归并。原Windows指针和快照说明位于 `private-state/windows-provenance/`，用于核对，不能直接放成Mac active.json。

只在新Mac服务停止且目标个人库/拒绝账本尚不存在时，将 private-state/private-state/ 中两个JSON复制到新dataRoot根目录，将 private-state/collector-state/ 中账本复制到新dataRoot/collector-state/。有既有Mac个人库或账本则先保留并比较，不能覆盖。随后启动服务、通过页面导入公开来源资料，生成Mac自己的active pointer。

可选保存HTML测试（离线、不抓取外站）：

```sh
export MC_HTML_SAMPLE_DIR="$HOME/MC-migration/public-origin-data/test-fixtures/bilibili-html"
python3 -m unittest discover -s apps/desktop/test -p test_bilibili_public_html_collector.py
```

该测试仅在显式提供样本目录时验证保存样本；不提供时此样本项明确skip，其余行为用例仍执行。迁移只移除测试中的本机绝对路径和文档中的个人凭据路径示例，未修改采集行为。本轮未重跑全套测试、GUI或旧ZIP。

必需原数据清单合计994,403,159字节，另附342,886字节保存HTML样本。ZIP最终大小与校验见单独交付的transfer-packages.json与SHA256SUMS.txt；此次仅文档整合，内容与校验值沿用已生成包，不重打包。可重建canonical.db不在ZIP；Windows约48.9GB全历史目录不在本次默认迁移包，原文件全部保留，也不计入迁移必需完成项。

Mac接手开始后，Windows冻结最终整合基线，不同时继续改其源码。两个项目由各自对话维护：本仓库只整合MC，测速分支和单独保留的旧README由测速负责人交付；不将它们复制进MC仓库。

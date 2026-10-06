# CurseForge元数据接口

## 2026-10-06 Mac 本地目录更新

V2 日常更新固定使用 `recent`（近期 2 页），目录核对使用 `catalog`（提供方全部返回页），直接 worker 的默认日常入口也选择公开目录。无 Key 时不再把少量已知 ID 的 CFWidget 缓存核查当作日常目录更新。新项目正文、图库和 Loader 在同一目录任务内收录；已经观察过的项目若上游版本变化或仍只有摘要，会按项目 ID 补充详情。原站完整正文和文件历史优先保留；只有确认由本提供方保存的正文才随其新详情更新。未变化的目录观察保留详情加载标记。

六站批量队列由本地服务执行，单站失败继续剩余平台，取消停止剩余任务；刷新页面不会丢失队列。每站的实际范围与结果单独显示，批次记录保存到私有 dataRoot 的 `update-batch-history.json`。服务重启只恢复结果；不会自动重发中断采集。

无官方 Key 时，桌面 `catalog` / `recent` 任务在开始前明确选择 [Modpacks.ch 公共 API](https://modpacks.ch/api) 的 `/public/curseforge/browse/updated[/页码]`。本机已验证首页和第二页各返回 50 条，提供方报告 200 页；这代表该第三方提供的目录范围，不能称为全部 CurseForge 项目。命令行使用 `curseforge_full_crawler.py --public-catalog`，与默认已知 ID 缓存读取区分。历史“Modpacks.ch 超时”记录属于下方 10 月 4 日的观察，不代表当前结果。

新 ID 必须核对 `/public/curseforge/{id}` 的提供方、项目 ID 和原站链接；已有完整正文、图库、文件版本及旧 ID 保留，下载计数不回退。第三方的版本摘要保留来源与观察时间，不伪装成完整文件列表或直链。只请求公开元数据，不下载整合包，也不发送 Key、Cookie 或个人资料。按每秒至多一次请求，先核 robots，遇拒绝、跳转、访问门槛或无效身份即停止；不切换提供方、不重试拒绝。

完整遍历此提供方报告的页数仍标记 `third-party-catalog`、`fullRefresh: false`；未观察到的本地项目继续保留。实际运行结果和页数写入每次本地快照的 `desktop_update_result.json`。旧包文件版本补充仍使用原有 CFWidget 路径。ModpackIndex 的公开说明禁止批量重建竞争目录，因此本项目不使用它做全目录采集。

第三方详情返回的正文、正文图片 URL 和结构化 `targets` 加载器/游戏版本也接入存档。桌面 `metadata` 任务或命令行 `--public-details` 只补充本轮已通过详情身份确认的新项目，标记 `third-party-details`，不重新扫描目录；已有完整正文、图库与原文件列表仍保留。没有返回的版本文件直链、完整变更日志或项目首次发布时间不会由摘要推断。该方式取得的是第三方缓存资料，不等同于再次核验 CF 原页全部功能。

## 2026-10-04 已知 ID 缓存恢复记录

2026-10-04免费路径：CFWidget公开JSON接口明确免费，不需要注册、表单或Key。无任何Key配置时，当前源码在任务开始前选择CFWidget；已有Key/Key文件配置时选择官方接口。可用`CURSEFORGE_PROVIDER=cfwidget`或`official`明确选择，非法配置直接失败。一次任务选定后遇拒绝不会切换提供方。没有继续请求已403的api.curse.tools或官网路径。

CFWidget仅按**已有Minecraft整合包数字ID**读取缓存元数据和版本资料，没有已确认的全站搜索接口；不作为全站新包发现或完整刷新。采集入口每次默认20个、上限50个已知ID，按已有修改时间排序，单线程最多每秒一次，无自动重试；`--max N`在此路径限制核查数量，不裁剪输出旧目录，`--recent-pages`不能扩展为缓存服务的全站扫描。空目录没有已知ID时保留原状并说明原因。旧包版本入口保留已有版本并补充缓存中未收录条目，小窗只显示返回范围与原站发布页。每个任务先读取robots；跳转、401/403/412/429、验证码停止该缓存来源。认证头不会发给CFWidget。

真实联网证据：2026-10-04 21:26:56北京时间，本机`https://api.cfwidget.com/285109`返回200，身份为Minecraft/Modpacks/RLCraft，有21条文件元数据；下载计数为30,259,490（旧记录30,101,187）。没有下载整合包文件。响应未提供文档描述的`last_fetch`，因此**上游抓取时间未知**；HTTP响应时间/Last-Modified不作为CF项目发布时间。现有文本与项目日期保留，计数不回退，版本历史只合并不删旧项。Modpacks.ch公开目录单次请求超时，不采用、不自动回退。

免费接口依据：[CFWidget公开文档](https://cfwidget.com/)；[Modpacks.ch公开缓存API说明](https://modpacks.ch/api)。这次仅证明已知包缓存读取恢复，不能称官方直连认证恢复、全目录恢复或发现新包。原已验Windows ZIP不重打包，不包含本次源码修改；使用当前源码服务需重启，使入口载入新代码与前端资源。

## 保留的官方接口配置

2026-10-04：选择官方提供方后，采集、旧包版本核查与小窗版本读取使用`https://api.curseforge.com/v1`。原第三方`api.curse.tools`不再作为采集或版本读取入口，也不作为自动回退。只读取项目/文件元数据，不请求文件下载接口。

凭据只在本机服务和Python worker中使用。配置自己的、具有Minecraft读取权限的官方API Key，可选择以下一项：

- `CURSEFORGE_API_KEY`：Key值。兼容已有`CF_API_KEY`变量；前者优先。
- `CURSEFORGE_API_KEY_FILE`：UTF-8纯文本Key文件的绝对路径，文件只包含Key，可有末尾换行。已有直接Key变量时优先使用直接变量。

例如在启动本项目服务的PowerShell中设置文件路径，然后启动现有服务：

```powershell
$env:CURSEFORGE_API_KEY_FILE = Join-Path $env:USERPROFILE 'Documents\mc-credentials\curseforge-api-key.txt'
npm --prefix .\apps\desktop run start
```

该示例不会创建Key文件。文件和真实Key不要放进仓库、运行包或公开Pages。修改环境变量后重启服务，使后续worker继承配置。明确选择official却没有Key时直接报明缺少配置，外网请求为0；非法Key字符、非官方主机或非元数据路径在发请求前拒绝。Windows curl通过stdin发送认证头，Key不进入进程参数。官方接口返回401/403/412/429、跳转或验证码时停止本次来源；不跟随跳转、不更换UA/cookie/IP、不自动切换代理接口。

官方文件列表采用`index=0,50,…`的偏移分页。小窗版本读取仍只取首50项，旧包版本核查按返回分页继续读取；项目元数据更新保留已有版本历史字段。近期采集可使用已有`--recent-pages N`范围，首次接入应在独立数据目录进行，不自动切换生产active pointer。

2026-10-04实际状态：原第三方接口403；官网robots读取也403，已停止网页路径。本机没有官方Key，官方API业务请求0、真实认证与在线增量尚未验证。现有46,529条CF历史记录及其数据时间保留。仅接好源码不能称“CF在线刷新已恢复”。用户暂不填写申请表；目前未确认有免表即可获得Minecraft第三方读取权限的官方途径。后续拥有自己的有效Key时，再做一次有界在线核验与有效数据发布。

依据：[官方REST文档](https://docs.curseforge.com/rest-api/)、[第三方Key申请说明](https://support.curseforge.com/support/solutions/articles/9000208346-about-the-curseforge-api-and-how-to-apply-for-a-key)。Studios开发者控制台面向自有游戏，不能据此假定新建Key自动获得Minecraft权限。既有已验Windows ZIP没有重打包，不包含本次新增源码接入。

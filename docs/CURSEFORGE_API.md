# CurseForge元数据接口

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

# 公开采集数据（2026-10-04）

总记录 75371；B站全部存档1,865，其中发布/介绍候选931、过滤或待核验934。
聚合元数据与原站入口，不提供下载；元数据变化不等于整合包新版本。

本次为真实在线匿名增量，未使用保存网页回放。旧记录、个人库、生产active pointer、原目录与未提交源码保留；Windows运行包未重打包。

- mcmod: 状态 partial；本次新增 9；raw元数据变化 0；公开展示变化 0；失败请求 1；实际覆盖 9 new-ID official HTML titles/links retained from saved validated checkpoints; next detail redirects and is not followed; no full catalog/metrics/versions refresh；数据时间 2026-10-04T08:51:08.305785+00:00；原因 Unexpected redirect; stopped without following; only titles/IDs/URLs and HTML hashes survived; unavailable enriched fields remain unknown.。
- bilibili: 状态 retained-old；本次新增 0；raw元数据变化 0；公开展示变化 0；失败请求 0；实际覆盖 no-new-requests-persistent-html-stop；数据时间 2026-10-03T07:52:27.282598+00:00；原因 Previous HTML initial-state 404 stop persists; ledger not cleared and no external Bili requests made today.。
- bbsmc: 状态 success；本次新增 8；raw元数据变化 154；公开展示变化 154；失败请求 0；实际覆盖 updated-window-complete；数据时间 2026-10-04T08:51:02.704919+00:00；原因 无。
- xyebbs: 状态 success；本次新增 0；raw元数据变化 149；公开展示变化 149；失败请求 0；实际覆盖 official-update-and-create-windows；数据时间 2026-10-04T08:51:02.873330+00:00；原因 无。
- modrinth: 状态 success；本次新增 14；raw元数据变化 374；公开展示变化 374；失败请求 0；实际覆盖 updated-window-complete；数据时间 2026-10-04T08:50:58.591484+00:00；原因 无。
- curseforge: 状态 retained-old；本次新增 0；raw元数据变化 0；公开展示变化 0；失败请求 1；实际覆盖 failed-window-retained-complete-base；数据时间 2026-09-30T08:13:34.410444+00:00；原因 HTTP 302。

Modrinth按更新倒序4页、400条；BBSMC按更新倒序2页、200条，均穿过三天重叠边界，不能称全站刷新。XYEBBS创建与更新窗口各1页，合并149条唯一观察。
MC百科1527–1535共9条仅保留成功解析的名称、ID、原站URL及HTML哈希；封面、简介、作者和版本未保留，不填造。1536重定向即停止，未继续追踪。
CurseForge原有api.curse.tools路径robots可读，首个列表请求HTTP302即停止，未跟随、换路径或重试；46529条旧记录保留。
B站仍有2026-10-03的持久HTML初始状态404停止记录；本次B站外网请求0、API/search业务0、没有新视频发现，账本未清除。此前15条成功HTML观察的历史范围保留，最新成功时间仍2026-10-03 15:52:27北京时间，不能写成今天刷新。
45个历史小窗正文资源原样保留；列表更新不表示这些历史正文也已更新。封面仍取决于原站可用性。

页面核对发现旧总览将失败原因按来源写死。现已改为依据实际HTTP状态及持久停止记录显示：CurseForge本次为HTTP302跳转；B站本次未请求，累计HTML观察属于历史。保留历史HTML不能把今天的状态标为新局部核验。此修正只更新总览提示，数据、封面、卡片、小窗、图标、个人状态逻辑不变。

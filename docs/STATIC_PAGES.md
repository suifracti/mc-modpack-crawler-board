# GitHub Pages 静态交付

## 2026-10-06 Mac 当前资料导出

延用 `gh-pages:/` 和V2静态入口。Mac本地当前公开快照共131,721条：MC百科1,507、B站1,867、BBSMC1,875、XYEBBS5,181、Modrinth18,757、CF102,534。仅发布 `publication-manifest.json` 的精确文件清单；不提交原始快照、个人库、采集状态、日志或证据。

`MC_PAGES_REFRESH_REPORT` 为六平台当前公开raw输入路径、SHA256、数量、任务观察时间及真实覆盖；`MC_PAGES_SOURCE_DATA_DIR` 显式指定保存的公开sidecar目录，补MC模组、趋势等结构化资料；`MC_PAGES_PREVIEW_ARCHIVE_ROOT` 指定已保存正文／图片／版本预览的公开来源快照。上述输入只读，不导入、切换指针或采集。`MC_PAGES_SOURCE_COMMIT` 为40位已提交源码SHA，写入公开manifest及DATA_SCOPE，不能继续硬编码旧源码版本。

静态站的后台更新、快照审计和Mac服务队列继续禁用；站点只读取发布时公开资料，个人收藏在访问者自身浏览器保存。CF第三方目录覆盖与B已有视频局部核验不代表全站或完整历史；各站观察时间分别展示，不把快照保存或构建时间当作源内容更新时间。

2026-09-30：用户要求最新桌面界面与最新已有公开抓取数据，目标为公开仓库 `suifracti/mc-modpack-crawler-board` 的 `gh-pages`。不发布旧 portable。

在 `apps/web` 运行 `npm run build:pages`；`MC_PAGES_OUT` 可指定输出目录，默认 `build/pages`。发布仅使用 `publication-manifest.json` 的精确文件清单，不能将整个 build 或输出目录一并上传。清单不会包含 `data-report.json`、源码、个人库、配置、session、日志或运行快照。

读取现有 `crawler_output` 六平台数组；MC 使用 `converted_output/data` 的公开结构化字段补充模组、趋势与统计。数据源只读，不创建 DataStore、不改变 active pointer、不导入或重新采集。源文件时间逐平台展示，不能解释为同批实时抓取。

静态页面复用 `desktopShell-v2` 和 `desktopShell-v2.css`（2026-10-03纠正原V1入口），静态 API 本地读取 gzip 数据分片。筛选逻辑沿用 data-store 的查询契约。收藏、想玩、玩过、评分、备注写入访问者浏览器 localStorage，键 `mc-pages-personal-v1`；不上传既有个人库。隐藏采集、换快照、审计及个人库备份入口，原站小窗操作改为公开外链，不提供代理、后台服务、启动器安装或下载直链。外站封面仍受来源可用性影响。

现有公开封面可通过 `MC_PAGES_MCMOD_COVERS` 指定只含 `mid`/`cover_url` 的素材文件，只补空值；不会读取生产个人库或切换指针。本次素材来自只读正式快照，补1482条后1496条有封面，2条仍未知。`MC_PAGES_REFRESH_REPORT` 继续使用10月3日在线增量报告，75,340条/B站1,865条、原来源范围和时间保持。五个平台图标及站点favicon由Vite打包，发布清单覆盖这些必要资源。V2联动只表示当前已加载记录的关联线索，不能称已检索全库。

本轮已完成离线类型检查、静态构建和隔离浏览器实际页面验收：六平台加载、搜索、版本筛选、详情来源、刷新及本地收藏。页面脚本错误 0、缺失本地资源 0，未启动服务或真实采集。

发布阻塞：本机 gh 登录失效；GitHub 连接器首次 create_blob(DATA_SCOPE.md) 返回 HTTP 403 Resource not accessible by integration。已停止写请求；没有远端发布 commit、gh-pages 创建或 Pages 启用结果。需恢复正常 GitHub 写权限后仅发布清单文件，再将 Pages 来源设为 gh-pages 的根目录并验证实际站点。不能为解决此问题关闭 SSL 校验、修改代理或读取凭据。

## 静态体验核对补充

- 已修复 390px 窄屏平台卡片从 440px 横向溢出的真实问题；复测页面总宽 390px、卡片宽 350px。
- 已补齐页面原有提示 Ctrl/Cmd+K 的搜索聚焦行为；Enter 打开详情、Esc 关闭与 B 站静态卡片已有实际通过证据。
- 公开导出解码 86 个标题的已有 HTML 转义字符，仍由前端文本转义显示。一个缺少 URL 的 B 站记录根据已有合法 BVID 生成来源链接，证据明确标为未联网核验；原始 crawler_output 未修改。
- 六平台 ID 无重复。MC 封面和作者在现有结构化字段与已知详情缓存中缺失；保持未知及占位，不把介绍图片当封面，不重新采集。窄屏检查测得当前全量加载堆占用约 530MiB；没有低内存设备证据，不宣称已验证其性能。
- Library 已保存三张原验收截图和同一个静态 ZIP；ZIP 更新使用原 Library 身份，不生成新的备份。截图是原验收证据，不为追加局部修复重拍同图。GitHub 发布继续阻塞，不重试认证或写权限。


2026-09-30 increment checkpoint: isolated batch mc-refresh-20260930; MCMod +14, Modrinth +71/1029 display updates, BBSMC +4/137 display updates. Final 73,822 records. Bilibili robots prohibits search; XYEBBS connection closed; CurseForge requested updated order was not honored, so complete prior sources retained. No active pointer or personal library changes. Static source cards distinguish validated incremental windows from retained old data. Current public ZIP exact 40-file allowlist; GitHub integration publishing remains blocked by HTTP 403. New-data browser count/search/base-path/narrow-width checks passed.


Latest checkpoint 2026-09-30 08:22 UTC (supersedes the earlier retained-CF/XY result): 74,379 records. CF valid bounded 20-page merge added 552 and updated 444 display records; observed dateModified order is unstable, so no early cutoff or complete-window claim. XY official public frontend exposes UPDATE_DATE and CREATE_DATE; both one-page overlap windows validated, all 5 missing IDs recovered, 370 display records updated including prior HOT refresh. Bilibili robots prohibits both search and known video-view API; 936 prior records remain. Successful MCMod/Modrinth/BBSMC sources were not recrawled. Latest ZIP Library same identity libfile_4cdbe1978ccc8191ab82879d195439bb version 3 upload succeeded and metadata read back 24,674,304 bytes. ZIP SHA256 01716b5ba86d9e3d1ef3a9eebb410ceac2616ac53c8404d24d4e3c35f4a6b633. Independent remote-byte SHA not obtained: Windows materialization metadata helper lacks os.setxattr; authoritative Library identity/versions retained in task JSON. No GitHub publishing, active pointer change, personal data change or deletion. All collection sessions complete.


## 2026-09-30 搜索与键盘详情修复（最新界面交付）

本地 Chromium 动态复现：主搜索暂停后失焦、中文 composition 期间输入节点被移除、方向选区被清空；compact/cards/table 无原生详情入口。仅修改 desktopShell.ts：保存恢复搜索焦点与方向选区，复用现有 composition-aware helper，组合期间延后重绘并取消待执行查询；公共记录操作区及 B站聚合独立分支增加原生查看详情按钮，详情异步重绘保留控件焦点。暂停续写、组合事件与迟到响应、三布局 Tab/Enter 详情评分备注及 B站聚合键盘入口已通过。Windows 物理输入法未实测。

74,379 条及35个静态数据文件逐字节不变，无采集／active pointer／个人库／GitHub发布变更。当前用户交付沿用两ZIP根目录合并：第一包 Library libfile_207af3a996e48191b120f08c623c4ce1 已更新版本1（13,434,303字节），SHA256 a503a7d38375f2a5a161b964bb0ba9793ddc0befe88af9284632cc4c93d0cb46；第二包 libfile_5e27cc8c958881919e7c905cc450d56b 原CF数据不变。最新本地完整包 SHA256 b35ccf256926d9403c4debab7820d5245c65c33e839136384ff9e51ea5ec8199。此前完整包 Library版本3仍为旧UI，勿当作本轮最新界面。此次确认保存到Library，不声称用户已下载收到。


### 2026-09-30 个人状态补验与第一包v2

隔离Chrome实测发现241ms内由A切至B编辑备注会取消A保存。desktopShell.ts将备注350ms防抖按platform:sourceId分别计时；192ms同例两条均保存。刷新保留评分/备注/收藏；真实同名The Pixelmon Modpack的modrinth:vwgtbO0y和curseforge:389615不串状态；相同ID模拟数据更新后保留个人状态；新详情不沿用上一备注。35数据文件与上一交付逐字节相同，74379条；类型/构建、定向浏览器、ZIP回读通过。详见当前任务mc-personal-checkpoint.md与mc-personal-static-acceptance.json。

当前第一包同Library身份libfile_207af3a996e48191b120f08c623c4ce1更新为v2，13434334bytes，SHA256 58db83e23bb31a41a1865d3c81b7a227553a6a43089da65382efc93d22e6a44b；第二包libfile_5e27cc8c958881919e7c905cc450d56b不变。当地完整ZIP SHA256 720bd3cd3affd5a33bb837bfc089190794d9b9196756489976f61a24758a95a6。此前v1发送成功；v2仅Library保存已确认，不能声称已送达用户。Library完整包v3仍旧UI。Windows扩展属性附加不支持，已保留JSON版本身份；远端字节SHA未回读验证。GitHub发布403仍阻塞，未重试。无真实个人库/active pointer变更、无爬取、无提交推送。


### 2026-09-30 最新第一包v3：静态备注生命周期

隔离Chrome复现350ms内立即刷新/离页丢最后备注。现仅静态模式每input立即通过既有同步localStorage保存；桌面保持独立350ms异步防抖，不保证卸载完成。定向三个边界、同input同步存储、存储失败提示与旧内容保留均通过（任务mc-personal-lifecycle-after.json）。未重复旧矩阵，35数据文件逐字节不变，74379条。断线前构建导出已完成，新JS pages-BWhm4GNw.js；旧会话结果不可恢复，未重建。

第一包同ID libfile_207af3a996e48191b120f08c623c4ce1现在v3，13434443bytes，SHA256 bcb40e041d3ca47efa9208b867f1afcde6e08f68c568fa804225b7dff305e936；第二包沿用。当地完整ZIP SHA256 d1f6c8b052cfe485fba6f6b53ccd24774c52e7fa6bcd88e7ea47b87e5cd777d1。v2已发送Sentinel_3b2eddfa5b888191b1d024cf77ea1e8a但无本次修复；新第一包v3仅保存已确认，尚未发送确认。Library完整大包v3仍旧UI。GH403、实体系统IME与真实桌面卸载仍未验/阻塞。Windowsxattrs不支持，JSON身份保留。无采集、提交推送、真库或active pointer变化。


### 2026-09-30 最新第一包v4：按需首屏

静态无关键词/既有筛选的总览只读manifest展示真实六源数量/时间，取消静态warmup；代表记录延后到选来源或明确查询/筛选。来源状态真实未加载/分片进度/失败，现有retry可恢复。桌面模式不改。35数据文件/schema/缓存版本不变，74379条。

旧首屏28gzip回归先失败；新首屏只manifest、空白无请求、单XY两片、CF503部分结果保留且retry恢复、六源Create完整匹配数478/12/98/308/2470/2855一致、个人备注保留均通过。额外动态复现并修正过宽空查询guard，保留1.20.1等既有显式筛选。最终tsc/Vite、diff和ZIP回读通过。证据任务mc-static-lazy-after.json及mc-static-lazy-filter-after.json。

相同桌面/390px CPU4桌面模拟，首屏38→4响应、23.996→0.611MiB正文、就绪0.297/1.095秒、长任务179/818ms、JS堆2.7MiB。跨源首次Create仍新增34响应23.388MiB、3.776/13.655秒、搜索后堆305.6/287.8MiB，全库搜索内存与长任务风险未解决；非低内存真机/真实Pages网络验收。测量后仅收窄显式筛选guard，未改变默认cold/Create路径，性能证据复用未重复测。详见mc-static-lazy-checkpoint.md与mc-static-cold-performance-after.json。

原第一包ID libfile_207af3a996e48191b120f08c623c4ce1更新v4，13435241bytes，SHA256 169e6f218703fc3d75f9ffd7ea0fb45421dc1e198524a329b794641beb7fa120；第二包libfile_5e27cc8c958881919e7c905cc450d56b不变。本地完整ZIP SHA25631feebabaadd39523c2b4b7c232f00ca5ea9fb198fbc7f405d96a629a0b31953。旧第一包v3已发送Sentinel_99dcf4ee17d88191a8df2feaf7eda13d；v4尚无发送回执。Library完整大包v3仍旧UI。JSON版本身份已保存，Windowsxattrs不支持、远端字节SHA未回读。GH403、实体IME/低内存真机/桌面异步卸载边界保留。无采集/删除/active/真库改动、无GH写/提交推送。


### 2026-09-30 静态查询内存收口：第一包v5待汇总

仅 pagesQuery.ts normalization 改为 canonical result.records，搜索索引只保留 matcher 实际读取的字段，去掉未使用的重复合并文本和数组；原 raw、searchText、详情评论、releases、个人状态及六源 Promise 缓存保留。35数据文件/schema/缓存版本逐字节不变，74,379条；保留v4 manifest-only首屏，无采集/active pointer/个人库/GitHub写入。

先补修改前基线，再比较六源 × Create、中文科技、Create+1.20.1下载排序、版本+标题排序共24组：全部有序 public records（含raw）hash、总数、facets相同；各源 raw/releases/searchText hash及隔离个人状态不变。浏览器 Create 六源计数478/12/98/308/2470/2855，API无内部字段泄漏，重复查询/评论/版本无追加请求，冷首屏仍4响应仅manifest，page errors=0。tsc/Vite、diff check、40文件ZIP读回通过。

同一隔离桌面Chrome Create+强制GC口径，搜索后堆297.03→261.67MiB，GC后277.86→246.49MiB，实省31.37MiB（11.29%）；不是预估，不是整进程内存/低内存真机。全库搜索仍约246MiB风险保留。证据task/mc-query-equivalence-before.json、after.json、mc-search-memory-inspection.json、-after.json与mc-static-memory-checkpoint.md。

第一包原ID libfile_207af3a996e48191b120f08c623c4ce1 更新及读回确认v5，13435326bytes，本地SHA256 9be7e37907a7d7b622c9b33f4f6ce8b2039bc5d95a359e764f8d027d752c1bee。第二包 libfile_5e27cc8c958881919e7c905cc450d56b不变；完整本地ZIP SHA256 db8a17056cad6e839fbad04050980306819c20b94586a8d5fb4d931b373322e5。v3曾发用户，v4/v5均待汇总、未主动发送。Windows xattrs不支持，完整Library结果存JSON；远端字节SHA未独立读回。GH403、实体IME、低内存手机、桌面异步unload边界保持未验/阻塞。无提交/推送或其他授权外操作。


### 2026-09-30 静态展示字段防护：第一包v6待汇总

隔离fixture实际复现卡片来源/下载URL的引号DOM注入并执行onerror，及javascript:/data:危险href。最小修复公共escHtml引号转义、HTTP(S)-only escaped href助手，六平台卡片来源/下载/模组链接接入。详情与备注原转义已正确，不重写它们。修后六源卡片、B站平铺、详情、评论/回复、备注均无fixture执行或注入节点/事件属性；备注关闭重开仍是字面payload，合法含引号HTTPS链接保留，page errors=0。tsc/Vite、diff及ZIP读回通过。证据task/mc-static-data-safety-before.json、-after.json、-checkpoint.md。

35文件/74379条不变，查询缓存和个人库未改，复用v5内存/等价性及v4首屏证据，未重测全矩阵。原第一包libfile_207af3a996e48191b120f08c623c4ce1已确认v6，13435396bytes，本地SHA256 03f360363f14384bcc54fe1768e59a24c0adfdc7f1033d448087a430a48e2ccb；第二包不变。v6仅待汇总未发送；Windowsxattrs仍不支持、身份版本保存JSON、远端字节SHA未独立读回。GH403/实体IME/低内存真机/桌面async unload边界保留；无真实数据注入、用户localStorage、采集、GH权限或系统安全设置更改。


### 2026-09-30 URL字段离线复核最终关闭

父已发v6第一包 Sentinel_d65bbb51a3588191acff6a6cc4799966，第二包不变；不再待发。离线35文件URL出现465879次：HTTP(S)390042，合法特殊字符32次/17不同值（引号18次）；19普通坏/占位、10889空值；另列64929非HTTP应用/下载URI（modrinth18399/curseforge46529/magnet1），不称攻击。可疑脚本协议/事件注入值0，35文件hash不变；原利用仅隔离fixture证明，不是现有数据遭攻击证据。

5个隔离边界通过：大写HTTPS、控制字符混入脚本协议、HTML实体伪装协议、协议相对来源URL、合法HTTPS引号查询。卡片/详情/API均先URL解析再协议白名单；href最后转义、不提前实体解码，脚本执行0，无外部访问。本轮无代码/数据/包/Library改动。证据task/mc-real-url-inspection.json、mc-url-parse-boundaries.json、mc-url-safety-closeout.md。该路径无剩余缺陷；GH403仍未部署、实体IME/低内存真机与桌面async unload边界未验，不扩审计。


URL收口最终补正（取代上段初验“无代码/包改动”）：CF/Mod下载入口仍有startsWith大小写前置过滤，隔离同5值证实合法大写/前导空白HTTPS被漏掉；仅两处改为共享safeExternalHref输出判定。CF/Mod同5值复测全部通过，其他字段/数据/查询/缓存不变。tsc/Vite/diff/ZIP通过；35文件逐字节不变。原第一包已确认v7，13435402bytes，本地SHA256 80541752a0eceacb7bb65a0daae4f467e2c9d868fede5de59ada888f573b2728，第二包不变。v6已发Sentinel_d65bbb51a3588191acff6a6cc4799966；v7保存待汇总、未发送。统计仍为可疑执行值0，该发现关闭，详细证据task/mc-url-safety-closeout.md。


### 2026-09-30 真实公开部署及B站较新历史数据恢复（覆盖此前GH403待发布状态）


- 站点：https://suifracti.github.io/mc-modpack-crawler-board/
- 当前 gh-pages commit：cbc62a7e39de85ad95b193d7085cd99cc41e0f18
- Git tree：b09e8ecbb2bb3524cef4fa799c849d97d51027b7
- Pages build：1250263681，built，匹配当前提交；来源 gh-pages 根路径。
- 首版：008d2a8b0d7c9bed5b3c53a55376b19b2d382c37；本次普通快进提交新增B站恢复数据，无force。
- 75300条，40公开文件/35数据文件。MC1498/Bili1857/BBS1837/XY5180/Mod18399/CF46529。
- B站旧936个BVID全保留，新增921，无重复。源SHA256 fd853fb8c18c93c35a0bb4965d4022a434484388e1b5cc8d5eb30f18d2e7a79b。
- B站恢复9月28日本地较新数据，最后历史检查2026-09-28T05:33:49Z；本轮未在线刷新。1852条有检查时间，4条确认不可用，5条未成功检查；未观察字段保留未知。
- 其余五源分片逐字节不变，保留9月30日验证时间；CF仍为最近20页局部合并，不能声称全库同步更新。

远端完整40文件tree/blob与本地清单一致。5个更新文件的当前公开HTTP响应均200且SHA256匹配；其余35个复用首版的HTTP哈希证据，当前远端tree确认字节未变化。全量复核中一次未改XY分片连接提前结束，未重试该请求，不把它当发布失败或成功下载。首次实站六源Create搜索/详情/刷新已验证；新提交实站冷首屏0记录分片、B站1857、历史标签、详情原站按钮、刷新/基址通过，隔离浏览器无错误。截图 mc-bili-live-recovered.png，明细 mc-bili-live-browser.json。外部来源/封面请求在验收中阻止，未声称播放验证。

master保持42251392a44edb1eab6285c810fae3ee69b19292。未上传个人收藏/备注、配置、凭据、session、日志、本地路径或active pointer；未改变真实个人库。源码局部适配仍未提交，未改main业务源码。使用获准Windows官方gh REST，未复制/输出token、未使用Git HTTPS。Pages配置已匹配，因此没有配置写入或覆盖。

页面可用；静态站没有采集、服务、代理、快照管理；个人状态仅浏览器本地。B站今天在线刷新仍受robots限制，后续允许来源的新数据由独立任务提供再合并。实体IME、低内存手机、外部播放、桌面异步unload未验；历史性能口径不能冒充新数据真机测量。

Library第一包v7/74379仍是旧交付包（未主动发送），不能说已含本次1857恢复；已发用户的是v6。第二包不变。本轮交付以真实站点URL为准。


### 2026-09-30 B站第一批官方HTML部分观察已部署


站点：https://suifracti.github.io/mc-modpack-crawler-board/
gh-pages commit：58ba01483f6726ade3efa1371f18aa2d480e603a
tree：4791b1e5ad18f9047069b169d074b27ec8f3183c
Pages build：1250317508，built，匹配当前提交；来源 gh-pages 根路径。

总计75303条/35数据文件/40公开文件；MC1498、Bili1860、BBS1837、XY5180、Mod18399、CF46529。正常快进自cbc62a7e39de85ad95b193d7085cd99cc41e0f18，没有force或更改Pages设置。

B站1857历史记录继续保留9月28来源时间（最后检查2026-09-28T05:33:49Z），其中4确认不可用、5历史未成功检查。第一批今日HTML只核6条：新增3条历史漏收（全部发布日期早于9月28日，并非最近两天发布），旧3条更新官方网页明确观察的字段/统计；最新观察2026-09-30T13:58:27.141061+00:00。旧评论、字幕、下载集合和原观察时间不覆盖，不把整个1857标为今天更新。3条新增BVID：BV11Ugw6CEDW, BV16c3u6XEji, BV1EPxPz4EXj。

验证：来源hash匹配，1860 BVID唯一且旧1857全保留，旧记录未观察字段不变，其余五源分片逐字节不变，tsc/Vite及git diff检查通过。完整远端tree/blob匹配；5个变化文件当前HTTP200且SHA256匹配，35个未变化文件复用既有HTTP证据。真实隔离浏览器：75303/1860准确、部分HTML范围标签、3新增记录搜索、详情原站入口、刷新/基址均通过，page errors=0，首屏不拉记录片；无真实个人localStorage或外部来源播放。证据mc-bili-html-update-checkpoint.json、mc-bili-html-live-browser.json；截图mc-bili-html-live.png。

master保持42251392a44edb1eab6285c810fae3ee69b19292。未上传个人收藏/备注、配置、凭据、session、日志、本地路径或active pointer，未改真实个人库。只使用获准Windows官方gh REST，不读/输出/复制token，不用Git HTTPS，不改并发HTMLcollector。源码与交接本地仍未提交到主分支。

API/search robots限制仍保留；本批没有B站请求，由独立worker提供已核官方HTML观察。下一批9月28–30实际发布候选尚未交付，本批不提前加入。CF仍为20页局部刷新；静态站不执行后台采集/服务/快照管理，个人状态仅浏览器本地。实体IME、低内存真机、原站播放等仍未验。Library第一包仍旧v7/74379，不包含本批，第二包不变；本轮交付是实站URL。


### 2026-09-30 B站第二批已核数据上线（75308/1865）


站点：https://suifracti.github.io/mc-modpack-crawler-board/
gh-pages commit：7d74f3cafafb47efb8ae31f1acfbb67b7b258259
tree：c84a3689bb4af9a0750d1856e3eb9728be958533
Pages build：1250390710，built，匹配当前提交，gh-pages根路径。
普通快进自58ba01483f6726ade3efa1371f18aa2d480e603a，没有force、没有重做上一发布或更改Pages配置。

总75308条，Bili1865/MC1498/BBS1837/XY5180/Mod18399/CF46529；40公开文件、35数据文件。
本批补5个已核BVID：4个历史漏收（血族崛起2.0、乌托邦3.5、地下酒吧、逆转未来2.0.0），1个2026-09-30 08:00 UTC/北京时间16:00发布的介绍视频“绿宝石大陆:怪物大乱斗版”BV1emaW6gEtE；包本体首次发布时间及是否新版本未知，不能称已确认新包版本。

历史1857记录继续保留9月28来源时间，旧1860条逐对象不变、BVID全保留无重复。累计今日HTML观察仅11条：7历史漏收、1近期介绍视频、3旧记录观察更新，最近核验2026-09-30T14:21:44.798525+00:00；未刷新全库。第二批简介仅160字符以内摘录，明确标记“非完整简介”，raw.desc未填充、desc_observed=false，未知服务端/群版本保留null，评论/字幕及完整下载覆盖未知。详情有视频发布日期含义与分记录官方网页核查时间。

来源SHA256 94cc936b0d051ef0657ce613e7d6ad11e4301b8c61828561f6851d4522ac8e42。其他五源分片逐字节不变，tsc/Vite/diff通过；完整远端40文件Git树及blob匹配，5变化文件当前HTTP200/SHA256匹配，35未改文件复用既有HTTP证据。真实隔离浏览器确认75308/1865、5新增记录搜索、BV1emaW6gEtE详情短摘录及未知包版本说明、原站入口、刷新/基址通过，无页面错误，首屏不拉记录片；未打开外部来源或用户真实localStorage。证据mc-bili-html2-update-checkpoint.json、mc-bili-html2-live-browser.json、截图mc-bili-html2-live.png。

本地准备曾因把规范化sourceId误写为bvid而停止；仅续跑剩余元数据/构建，未重复合并、未在修正前发远端写入。详情核查说明在已有可展开核验记录内，测试展开后通过，无该项产品修复。

main/master保持42251392a44edb1eab6285c810fae3ee69b19292；个人库/收藏/备注、active pointer、其他来源不变，未上传配置/凭据/session/日志/本地路径。只改静态界面/导出器的必要展示，未应用独立HTML适配器补丁；本地源码与文档未提交到main。Windows官方gh REST凭据原位使用，不读/输出/复制token，不用Git HTTPS。

尚未完成全量新包发现；API/search限制仍保留，CF仍20页局部刷新，实体IME/低内存真机/外部播放未验。静态站无后台采集/服务/快照管理，个人状态只存浏览器。Library第一包仍v7/74379及旧本地ZIP，不含当前1865；第二包不变，本轮交付是实站URL。


### 2026-10-02 元数据核查与日期标签修正


站点：https://suifracti.github.io/mc-modpack-crawler-board/
gh-pages：b6682524c96f8ed2f9614b644b46b9abaecf3631；tree：92f0683e2fc56fd1dd454819de17bf4640b6c6b4；Pages build 1254510638 built，同提交。
普通快进自7d74f3cafafb47efb8ae31f1acfbb67b7b258259；未更改Pages配置或默认分支。

总75,308/B站1,865保持不变。此次两个固定候选官方主站页面HTTP200，robots预检允许；只更新既有阿卡迪亚BV1ihtP61EJU的公开统计与元数据核查时间2026-10-02T07:37:59.436922+00:00，标题/作者/视频发布日期与原数据一致。视频仍是2026-08-28 16:33 UTC发布，不称新包/版本更新。剑与王国BV1DS421R7xR官方日期2024-07-06、现行分类器未接纳，保留隔离证据但不导入；没有核实到9月30日后新发布视频。业务请求2次、API请求0、脚本执行/凭据/cookie/重试0。累计候选账本28/30，无拒绝或停止事件。

累计12个已收录BVID有分批HTML观察（8补收/4旧记录更新）；来源卡片修正“今日”旧措辞为累计分批核验，明确最新日期。其余1,864个B站对象逐对象不变，更新记录的原简介/评论/字幕/版本/下载字段及各自历史核查时间完整保留。总数/ID/去重保持，另外33数据文件SHA256不变，B站历史来源时间仍9月28日；其余五源不变。没有切active pointer或碰个人库。

定向验证：隔离浏览器先复现旧卡片在10月2日称9月30日观察为今日；修后本地与真实线上搜索、详情、原站按钮、空隔离备注、刷新/基址、准确累计日期均通过，首屏不拉记录片，无页面错误。未访问外部封面/视频/下载链接，不称外部播放通过。tsc/Vite/git diff --check通过；完整远端40文件Git树匹配，5个变化文件当前HTTP200/SHA256一致，35未变文件复用既有HTTP证据。

证据：mc-oct02-preflight.json、mc-oct02-candidate-plan.json、mc-bili-oct02-public-html/batch-report.json与observations.json、mc-oct02-update-checkpoint.json、mc-oct02-baseline-browser.json、mc-oct02-local-browser.json、mc-oct02-live-browser.json、mc-oct02-live.png、mc-bili-oct02-github-publication-state.json。

真实余项：生产collector_worker.py仍调用bilibili_crawler.py旧crawl/sync-desc，独立HTML适配器尚未接线，补丁也未应用；不能称自动采集已恢复。最小接线方案已提出待评审：显式限量固定候选HTML模式，复用robots/累计预算/拒绝停机及分字段时间，输出隔离增量；默认生产入口不偷偷切换。当前有界索引/旧候选材料未提供可核实的9月30日后新增视频，不代表不存在新包。API/search禁爬仍保留；CF仍20页局部范围；实体IME/低内存真机未验。

主源码HEAD仍9fe154f，默认远端master仍42251392a44edb1eab6285c810fae3ee69b19292；本地源码文档修改未提交到默认分支，保留此前用户修改。Library第一包仍v7/74,379且旧ZIP，不含现站1,865；本次交付实站URL而非重新打包。未删除、移动、创建备份、配置凭据或全库重抓。


### 2026-10-02 主站HTML入口接线阶段


源码集成已完成：bilibili_public_html_collector.py、复用adapter/extract、collector_worker.py，以及Electron main.cjs/browser server.cjs两入口共享拒绝账本。既有UI保留两个采集模式，改成HTML局部覆盖说明、真实计数与明确错误；去掉已不适用的检索页数。没有修改旧API脚本或启用其路由。

最终13项Python定向回归及6项JS入口测试通过，前端typecheck、现有桌面前端构建和git diff --check通过。构建结果build/desktop/frontend/desktop.html引用assets/desktop-CCj68jka.js与desktop-CVVMCwJv.css；为保留旧文件，构建仅临时关闭emptyOutDir，未清目录。

真实HTTP：通过实际collector_worker入口在mc-html-entry-live-workspace只核验一个先前未访问的官方页面，观察1/新增0/旧元数据更新1/失败0，raw和sidecar均1865，previousIdsPreserved=true，输出partial_update和隔离snapshot manifest。2026-10-02T08:14:24.881094+00:00观察，API/search机器人规则均禁止，业务请求0；仅3个robots预检与1个video页请求，累计候选29/30。其他1864个对象逐对象未变、被更新对象原全文/评论/字幕/下载/版本及历史时间保持，原input不变。证据mc-html-entry-live-check.json与workspace/build/desktop_update_result.json。

包装检查脚本在真实worker之后因Windows CP936被当UTF8读而退出1，没有捕获到子进程exit code；已从现有合同/快照回读核验，没有重新请求。worker进程UTF8边界随后已修，实际无种子离线子进程验证明确UTF8失败合同通过。源码最后修了先去重再限量；explicit --bv的已核页面逻辑不受该调度修正影响，最终代码相关边界由离线回归验证。

状态必须分开：源码入口接通；HTTP worker隔离验收完成；桌面两入口假runner/store合同完成；没有实际GUI点击、启动/重启真实服务、导入或切生产active pointer；没有生成/验证Electron安装包、提交/推送/合并默认分支。本阶段没有重新发布静态站或更改静态数据，最后已验证站点仍https://suifracti.github.io/mc-modpack-crawler-board/，commit b6682524c96f8ed2f9614b644b46b9abaecf3631，总75308/B站1865。此次隔离观察没有合并到静态站。

正常范围与余项：new仅在现有有效BVID种子与官方合集范围内发现，未核实到9月30日后新包，不代表全网没有新包；无种子要先提供有效采集输入或CLI明确BVID。拒绝状态必须保留，不允许重置后重复请求。本机真实GUI/已有进程加载新代码和安装包尚未验；可在用户运行新源码入口后定向确认，不要求大矩阵。个人库/原始快照/其他来源不变，保留之前全部未提交static成果。

源码/构建/最终哈希记录mc-html-entry-final-checkpoint.json；已批准设计docs/superpowers/specs/2026-10-02-bilibili-public-html-design.md。禁止默认提交设计文档的旧skill要求按本轮用户“不发布main”的边界跳过，无需重复批准。


### 2026-10-02 真实本地服务链回放收口

前一阶段仅证明源码接线和直接worker，实际DataStore消费HTML部分合同尚未闭环。本轮用独立临时dataRoot、回环端口、真实HTTP API/UpdateManager/DataStore/process runner/Python worker和保存的官方HTML定向回放，无新外站请求，已复现并修复两处真实缺陷：DataStore原先拒绝 `public-video-html-bounded`；Windows取消后worker的同步锁遗留导致下一任务被挡。

DataStore只增加B站同名coverage且有实际fetchedCount的受限合同兼容，旧ID/写入/数量/非截断守卫保留。UpdateManager只在本次已取消runner close且child明确退出、锁文件PID等于本次child时释放锁；不重置采集账本、attempted或访问停止状态，不碰其他PID的锁。

真实服务回放通过：无字节变化仍partial并提交隔离快照；跨任务先去重再限量；403保持旧active；后续任务持久拒绝且请求0；取消保持active和账本不变；取消后下一任务成功且不重复已尝试种子。新增4项取消锁安全回归、两处CJS语法与diff检查通过；此前13 Python/6 JS/typecheck/前端构建证据复用，不重复全矩阵。测试服务均已停止。原失败与修后证据在task的mc-html-service-replay/{baseline,full,cancel-fix,final}-checkpoint.json；交接mc-real-service-chain-handoff.md，最终代码hash更新mc-html-entry-final-checkpoint.json。

必须分清：实际本地服务链已回放验证，生产进程加载新源码、GUI点击及Electron安装包仍未验；此次外站请求0，前阶段单页真实HTTP worker证据独立保留。生产active、个人库、原始快照和其他来源未改，源码未提交/推送。静态站及75,308/B站1,865数据仍此前commit b6682524c96f8ed2f9614b644b46b9abaecf3631，本轮未再发布。有效种子/官方合集范围与API/search限制不变，不能称全站发现恢复。


### 2026-10-02 Windows预构建本地浏览器运行包

现行apps/desktop/README.md已明确不再生成Electron EXE，正式交付为Node本地浏览器服务；不再把Electron安装包列为本项目当前必需余项。本轮运行包位于task/mc-windows-browser-20261002.zip，351,050 bytes/51文件，SHA256 b77a17f65466ee4fdf34de82c486d7b94cd8e03ef1f664f1ebd877eeb559d3e8。解压目录内Start-Windows.cmd使用已有Node/Python，预构建前端无需npm；默认回环监听、空闲端口和包内runtime/data，原生产指针不自动加载。

含最新前端、B站HTML worker/adapter/extract、partial合同兼容与取消锁释放修复、现行六源入口和canonical必要模块。首轮包内启动发现共享search-contract漏装，补齐清单后通过；产品搜索行为未变，原失败证据保留。50项资源hash匹配，ZIP CRC及HTML/canonical本机导入检查通过。实际包内launcher进程在独立QA根启动，首页与JS/CSS HTTP200且hash匹配，初始无数据/idle真实；导入3条fixture后真实包内Python worker保存HTML回放提交partial_update，旧ID保留，观察1/API业务0/外站请求0；测试服务受控退出0。

MC服务/worker预检未发现，未关闭任何既有服务。生产数据/个人库/线上75308/B站1865未改，未提交推送或上传包。产物只在Windows，本机路径不代表云端可读。包不含生产数据与Node/Python运行时，初次启动无数据，需用户明确导入有效目录；不能称独立EXE。前台GUI/双击交互和其他五源在线采集未验，无新安装/下载/系统改动。证据mc-windows-package-checkpoint.json与mc-windows-package-handoff.md；已有6链路+4锁回归复用。

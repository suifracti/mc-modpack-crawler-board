# MC 分支整合盘点（2026-10-05）

2026-10-06 收口补充：默认开发主线为 `master`，已验 `644d9e290dc29d8fb82e29108a876d4f80424465` 从原远端 `42251392a44edb1eab6285c810fae3ee69b19292` 正常合并，运行源码与已验基线一致。最新远端分支SHA与本页既有盘点一致，没有需要追加采用的新业务成果。`gh-pages` 保留站点用途，PR #21 分支保留，A/B 候选继续不采用。已合并功能/迁移分支拟在保存映射和bundle、用户确认具体范围后清理；Windows原目录、11个worktree和旧Mac未提交成果不删除。最新可开发入口见 [PROJECT_STATE.md](PROJECT_STATE.md) 和 [MAC_MIGRATION.md](MAC_MIGRATION.md)。

以下是原2026-10-05盘点，不把历史“未推送/未验”文字作为今天的停止条件。

基线：`codex/mac-migration-20261005@6a2516054e337c0ffb9795df999f56ea511b7b6b`。独立整合分支：`codex/mac-integration-20261005`。
仓库：[suifracti/mc-modpack-crawler-board](https://github.com/suifracti/mc-modpack-crawler-board)，公开设置不变。整合分支仅本地提交，未推送、合并到master、部署或发布。

## 本轮整合范围

- 盘点所有本地分支、实际远端分支、11个worktree及未提交材料。未发现其他MC任务/项目进程写入；测速负责人已确认仅写测速仓库，旧README比较由测速对话交付。
- 历史功能分支均已在基线祖先中，没有发现需要再次应用的新业务代码。个人库旧补丁7个文件的postimage均可在基线历史中找到；不能把后来已演进的代码退回旧整包。
- 从 `4225139` 的PR #18收口文档择取准确的合并/验收历史，更新 `PROJECT_STATE.md`。不倒灌其2026-09-25的当前状态头部，不重复合入merge commit或旧壳层。
- 旧个人库worktree文档中PR #5最终head/merge事实已有记录；“当时origin/master=f0c9f9f”及停止下一开发任务等时效说明，不当作今天状态。原未提交文档/补丁保留。
- 本轮提交仅 `docs/PROJECT_STATE.md`、`docs/MAC_MIGRATION.md`、本盘点文件。运行源码、依赖、数据格式、生产指针和两个私下数据包均未改。

## 本地分支处理结果

|分支|盘点SHA|处理|
|---|---|---|
|`codex/compact-snapshot-status`|`3ac30a42676bf361e4cecbffe32be897d2ddf227`|PR #21未合并；UI行为已纳入；继续保留|
|`codex/cover-load-recovery`|`b5d8754a10f17a5a2717bbf98310cbaed6d46297`|已纳入基线；不重复应用|
|`codex/curseforge-file-index`|`6931bd8d06b8defb687f14a5ae2f4a7502191bad`|已纳入基线；不重复应用|
|`codex/dark-theme-consistency`|`b29ea045e5bfdd56d69ec5faf98b043c8fe8ab58`|已纳入基线；不重复应用|
|`codex/discovery-rules`|`241d33dcdd3e34319870538b29491f595f996a3c`|已纳入基线；不重复应用|
|`codex/favorite-update-notifications`|`7bde27e4b8084e9de8d8cf9253bf9827217e1b0a`|已纳入基线；不重复应用|
|`codex/filter-profile-layout`|`faef0f4c5234a85a9d44d950321a265b8067641b`|已纳入基线；不重复应用|
|`codex/fix-cover-regression`|`78e2cae844cbe3c417a700e6b7e1fbcb95b44e2c`|已纳入基线；不重复应用|
|`codex/fix-curseforge-images`|`d74112b108c8a91de3853c8d4494744d928b84e2`|已纳入基线；不重复应用|
|`codex/fix-default-browser-query`|`5fb3bc26b45c40f5e67db5c51d502372d9b39c5e`|已纳入基线；不重复应用|
|`codex/fix-mcmod-cover-collection`|`15cb982e607e7a84261fc2b64d4a9e6b576b0ad7`|已纳入基线；不重复应用|
|`codex/integrate-browser-ui`|`9fe154faa7f6755ba0737e772c36f3b5ac6df0a0`|已纳入基线；不重复应用|
|`codex/mac-migration-20261005`|`6a2516054e337c0ffb9795df999f56ea511b7b6b`|已纳入基线；不重复应用|
|`codex/mcmod-pack-version`|`10e9c56cc2a6e200f7ce73683a8cf08ab5c35891`|已纳入基线；不重复应用|
|`codex/personal-backup-revisit`|`8b08cc5261c49af8d5f93ca0cbb13215f59ad695`|已纳入基线；不重复应用|
|`codex/pr18-closeout-docs`|`42251392a44edb1eab6285c810fae3ee69b19292`|仅历史PR #18收口事实适用，本轮择取；不整分支合并|
|`codex/pr6-closeout`|`4b283f744ca6fb7ecf4f26a559e68d64df35097a`|已纳入基线；不重复应用|
|`codex/pr7-closeout`|`392679b24c87821560aa1cd1e0aff0f1ae55748e`|已纳入基线；不重复应用|
|`codex/pr8-closeout`|`6efcc7e082e8288b7eed0bf1b53e641c4d705993`|已纳入基线；不重复应用|
|`codex/repository-cleanup`|`34be1b25aa853f1d28f5546e08451245c36d583c`|已纳入基线；不重复应用|
|`codex/restore-mcmod-trend-chart`|`931bc05b89d28d008eea18b42fa0a81b2b3a4f13`|已纳入基线；不重复应用|
|`codex/restore-platform-filters`|`bbe94649adc955d28977d8564f5b0025c295c4f8`|已纳入基线；不重复应用|
|`feature/personal-library`|`7dd7537466b20db19fafa4e47fce2d8f18c7193b`|已纳入基线；不重复应用|
|`master`|`2242a5e48e7bda4a1879eac6e407196b89f5ef02`|已纳入基线；不重复应用|

远端各源码分支与已盘点远端跟踪SHA一致，没有额外未拉取的功能分支。远端 `master@42251392a44edb1eab6285c810fae3ee69b19292` 只有同一历史收口增量；`gh-pages@2e484b6c976c6c1db9e28c0f9a31a727fc99e8fa` 是线上生成产物，不作为源码反向合并。

## 11个worktree与未提交材料

- Windows主目录：从迁移基线建立独立整合分支；原迁移分支ref保留。未跟踪的 `docs/superpowers/specs/2026-10-02-bilibili-public-html-design.md` 是历史实施草稿，相关实现已在基线；保留原位，不将其中计划/早期验收描述改记为今天结果，不新增运行改动。
- cover-load-recovery、dark-theme-consistency、desktop-dashboard-discovery-rules、filter-profile-layout、mc-modpack-crawler-board-cover-fix、mc-modpack-favorite-update-reminders、mc-pr18-alignment：均已纳入且工作树干净。
- desktop-dashboard个人库worktree：历史 `docs/PROJECT_STATE.md` 修改及 `personal-library-review.patch` 留原位；7个补丁postimage均是基线可达历史blob，功能已演进，不重复应用。
- mc-pr18-state-update：干净，保存PR #21；mc-3gf-i3v2：干净，保存B候选；两者不采用。A候选对象在Git中保留，没有对应现存worktree，不虚构第12个。

## PR #21：分支未合并，功能已存在

- PR [#21](https://github.com/suifracti/mc-modpack-crawler-board/pull/21) 为OPEN，head `3ac30a42676bf361e4cecbffe32be897d2ddf227`，GitHub检查列表为空。PR相对master只改V1 `desktopShell.ts` 3增/1删。
- 独有提交意图：顶部只显示短“快照”标签，将完整ID放在title/aria-label，装饰圆点aria-hidden。逐行为比对发现这些已在迁移基线的V1/V2中；Git历史 `9db1c37` / `9fe154f` 已保存相关入口演进，并额外区分线上“静态展示”。
- 不将“PR未合并”当作“功能缺失”。没有新行为增量可应用，也不关闭/合并PR。
- 仅Git对象内进行三方合并模拟（未改index/文件/ref），整分支会在 `desktopShell.ts`、`PROJECT_STATE.md` 文本冲突。不能用旧header覆盖现有静态站提示、小窗等后续功能。若以后要整理PR状态，应单独决定关闭/更新，不需要重放其旧运行代码。

## A候选：归组运行逻辑与独立安全审计，仍BLOCKED

- 对象 `9c51a557401119621c6cef90726e575f529c74bb`，与基线共同祖先 `4bf5e0fe4c614f3e630ae242db2ed5b66ef95fea`。56个候选独有文件均与当前基线有差异。
- 运行增量集中于 `bilibiliGrouping.ts`（归组闭合、项目身份/版本分区）、`packName.ts`、`legacyAdapter.ts`、`debug.ts`；其余是归组审计、冻结证据、holdout/acceptance runner、gzip兼容与相关用例。不是新HTML采集/CF恢复方案。
- 26-case定向gate、27个DIFFERENT_PACKS与5个AMBIGUOUS保护样本通过，不能据此称全量安全。独立审计旧40/62 holdout只有44个case闭合，28个冲突、30个覆盖不足；277个pair未覆盖、62个关系冲突。population另有296个未覆盖、94个关系冲突。最终expanded safety为BLOCKED，exit 2，runtime NOT ACCEPTED。
- 原runtime handoff中的ACCEPTED/candidate-derived holdout已明确SUPERSEDED；历史generator-dependent旧suite还保留exit 1、53 tests及setUp errors，未伪造通过或删断言。
- Git三方模拟没有文本冲突，但这不是语义安全证明。采用会改变组卡归属/数量和个人线索展示，且安全证据尚缺。按既定边界不采用；后续须先决定是否继续解决独立证据冲突与覆盖缺口，不能直接选“合并通过”。

## B候选：审计整合基础与旧导入事务加固，未做生产切换

- 对象 `9b38c34fbe5b26a4d684c104a992f55492e49519`，同一共同祖先；38个独有文件均与当前基线有差异。包含population/undermerge裁定、稳定审计输出、Truth Matrix报告和测试；继承 `a55fb64` 的manifest校验、浏览器profile生命周期与cutover事务加固。
- 会影响 `pipeline/manifest.py`、`cutover_frontend_to_modern.py`、`browser_harness.js`、两个smoke入口及新事务/manifest用例；没有A的归组运行代码。报告整合不是生产cutover。
- 原记录在 `d05ffea` 上typecheck/Vitest/manifest/事务/审计用例通过；Truth Matrix第一次unittest入口exit 5、0 tests，随后正确文件入口通过，保留失败事实。测试后 `dbaa567` 为整合制品head，之后若干仅报告提交不能冒充该测试时版本。
- 当时production_state文件缺失，production_build_commit unavailable；manifest 2924/2924、canonical及data rollup未变，只对应旧released `4bf5e0f`，不是当前迁移数据包。runtime未改、Truth Matrix未最终定稿、production cutover未执行。
- Git三方模拟没有文本冲突，但继承的导入事务/manifest格式与当前Mac入口没有兼容验收，且此前候选边界继续有效。本轮不采用。后续可另选“只提取审计工具”或“单独验证事务加固”，不能把候选整包当当前已验源码。

## 最小验证与交接边界

- 本轮只改三份Markdown。验证仅检查提交文件范围、相对迁移基线运行/依赖差异为空、分支/worktree保留及文档链接/隐私路径；不启动业务或重跑构建、旧测试矩阵、GUI、A/B审计。
- 构建复用10月4日TypeScript/Vite通过证据；前端源码相对已盘点迁移基线未变，本轮无新的构建结果。10月2日Windows包验收属于保存HTML回放，10月4日有界线上结果另列；都不是Mac验收或全源刷新。
- PR #18当时GUI smoke未完成、A独立安全BLOCKED/旧suite失败、B错误测试入口与production_state unavailable、官方CF Key真实认证未验及Mac未验均保留。
- 两个ZIP和SHA256SUMS继续私有交付，数据格式/依赖未改，不重打包或重算无变化数据。48.9GB历史留Windows，不计入迁移必需完成项。Mac以最终整合SHA接手；新分支推送需再次确认，Mac接手后Windows冻结该基线。
- 测速的基线是另一个仓库的 `70f25a0947d5acf9ac8d35a1414a0a6a85b1c9e9`，由测速对话交付其分支处理与旧README适用性，不在MC复制、提交或验证。

/**
 * Phase 3G-F.2-B - Under-merge GROUND TRUTH adjudication ledger.
 *
 * Module 2 (3G-F.1-B) produced a REVIEW LIST: 58 uploader-scoped clusters of
 * group keys that MIGHT be one logical pack the algorithm split apart. It
 * deliberately did not decide. This file is the decision layer.
 *
 * It answers exactly one question per candidate:
 *     is this cluster "the same pack split across groups",
 *     or "several different packs that merely share a word"?
 *
 * WHY THIS IS A HAND-MAINTAINED TABLE
 * -----------------------------------
 * No rule produces these verdicts. The discriminating evidence is a REGISTERED
 * PROJECT IDENTITY - a stable id on MC百科 / 星原社区 / BBSMC / CurseForge that
 * every video advertising the pack carries. Where that id is shared by all groups
 * the case is settled. Where it is absent the reviewer has to read the titles and
 * decide, and the honest answer is sometimes "cannot tell".
 *
 * EVIDENCE PRECEDENCE (a shared download URL or QQ is NEVER sufficient - Phase
 * 3G-E proved one Quark link can front 28 different packs):
 *   strong   : same registered project identity; same explicit pack-name
 *              continuity; uploader's own update/version wording on a named pack
 *   supporting: same download URL, same QQ, same theme  (never decisive alone)
 *
 * THE 涅槃 LESSON - WHY "looks like the same series" IS NOT "same pack"
 * -------------------------------------------------------------------
 * Module 2 flagged 墨言eclipse three times, and the 涅槃 group keys were the
 * canonical known case. They are NOT all one pack:
 *     5 records -> 涅槃            (xyebbs:resource/37418, mcmod:modpack/1418)
 *     2 records -> 未尽之路-涅槃   (bbsmc:unfinished_path_nirvana, xyebbs:TUPN)
 *     3 records -> 未尽之路        (bbsmc:unfinished-path, xyebbs:UP)
 *   = 2 PACKS
 * `未尽之路涅槃` shares the word 涅槃 with the 涅槃 pack, so the naive reading is
 * "same pack, 7 records". The registered identities say otherwise: it is the
 * 未尽之路 line, carrying 涅槃 as a subtitle. 涅槃 is therefore the reference
 * example of a FALSE-POSITIVE under-merge candidate, and the split of the 涅槃
 * keys into two findings is CORRECT, not a bug.
 *
 * Output: pipeline/audit/bilibili_undermerge_adjudication_v2.json   (tracked)
 * Usage:  node pipeline/audit/bilibili_undermerge_adjudication_v2.js
 */
const fs = require('fs');
const path = require('path');

const REPO_ROOT = path.resolve(__dirname, '..', '..');
const IDENTITY = path.join(REPO_ROOT, 'build', 'audit', 'undermerge_project_identity_v2.json');
const EVIDENCE = path.join(REPO_ROOT, 'build', 'audit', 'undermerge_evidence_v2.json');
const OUT = path.join(REPO_ROOT, 'pipeline', 'audit', 'bilibili_undermerge_adjudication_v2.json');

const VERDICTS = ['CONFIRMED_SAME_PACK', 'STRONG_SAME_PACK', 'DIFFERENT_PACKS', 'AMBIGUOUS', 'PARTIAL'];

/**
 * Key = the canonical cluster key emitted by the module-2 scanner.
 * Built as author + '||' + sorted group_keys joined by '|' (see keyOf below).
 *
 * `expected_identity_count` is the number of DISTINCT registered projects the
 * cluster's evidence shows. It is the number the runtime should end up with:
 * 1 means the groups are one pack and must be unified, 2+ means they must stay
 * separate.
 */
/**
 * One entry per module-2 cluster. Keyed by (author, signature) instead of the
 * literal cluster key, because those keys are long and the scanner re-clustered
 * between runs - transcribing them by hand silently mis-targets a case. The
 * runtime resolves each entry against the live artifact and FAILS LOUDLY if a
 * signature is not found, so a dropped case can never pass unnoticed.
 *
 * `expected_identity_count` = how many DISTINCT registered packs the evidence
 * shows. 1 means the groups are one pack that must be unified; 2+ means they
 * must stay separate.
 */
const CASES = [
  {
    author: "一个小寂哦",
    signature: "一个小寂哦::四叶草",
    verdict: "DIFFERENT_PACKS",
    confidence: "high",
    expected_identity_count: 12,
    note: "NOT one pack. This uploader runs a family of distinct titan/lucky-block packs: 弑神之路, 怪物大乱斗, 怪物大乱斗重生, 四叶草, 超BT绿宝石大陆, 超级幸运方块 series, 追影之旅, 更多泰坦, 泰坦生物, 我是星辉死神, 随机方块泰坦, 浪客拔刀剑. “泰坦”/“星辉死神”/“幸运方块” are shared COMPONENTS and house style, not a pack name. The cluster is a token-connectivity artifact: 17 groups chained through generic words. Expectation: 12 distinct packs (several groups in the cluster are themselves still split, which is a separate finding).",
  },
  {
    author: "时唅",
    signature: "时唅::辐射新世纪",
    verdict: "DIFFERENT_PACKS",
    confidence: "high",
    expected_identity_count: 4,
    note: "NOT one pack. Four separately-named series: 辐射新世纪, 辐射次时代, 辐射生还者, 潜行者 (+ 潜行者风暴 as its own title). “末世/辐射/潜行者” are genre words this uploader uses on every video. Distinct Quark folders per series.",
  },
  {
    author: "豆腐ki",
    signature: "豆腐ki::超低配 无限打金 手机移植版 fcl启动器",
    verdict: "DIFFERENT_PACKS",
    confidence: "high",
    expected_identity_count: 25,
    note: "NOT one pack. This is a phone-port channel: 25 videos, mostly one group per video, each porting a DIFFERENT third-party pack (生活大冒险, 原环之理, FTB魔眼传说, 终末旅行家, 天空奥德赛, ATM3, ATM10, 殖民战争, 特摄世界, 自然之旅3, 无中生无尽, …). “低配/手机移植版/FCL启动器/一键自动安装” is a fixed house template. Groups carry conflicting registered ids (mcmod:613, mcmod:49, curseforge:all-the-mods-3-expert, curseforge:all-the-mods-10) - proof they are different projects. This cluster is pure boilerplate connectivity.",
  },
  {
    author: "墨竹ギ",
    signature: "墨竹ギ::深渊之诗",
    verdict: "DIFFERENT_PACKS",
    confidence: "high",
    expected_identity_count: 4,
    note: "NOT one pack. At least four separate packs: 深渊之诗 [Poetry of the Abyss], 失落的异界 [TheLostWorld], 史诗的地下城 [Dungeons of Fantasy], 幻想的地下城. The shared token 地下城 (“dungeon”) is a SUBJECT word used to describe a Minecraft-Dungeons-flavoured pack, not an identity. Note 史诗的地下城 and 幻想的地下城 share no registered id and are announced as separate releases.",
  },
  {
    author: "我的世界peaunt",
    signature: "__raw_BV1EhYN6AEWo",
    verdict: "DIFFERENT_PACKS",
    confidence: "medium",
    expected_identity_count: 3,
    note: "Different packs / different Minecraft generations. Two groups are un-named raw buckets (1.12.2 and 1.7.10 titan packs, no title identity at all), while 泰坦生物复刻 is an explicit 1.20.1 RECREATION with its own QQ group (791405778). The 1.7.10-era originals and the 1.20.1 recreation are announced as different products.",
  },
  {
    author: "明月庄主",
    signature: "明月庄主::月亮工厂",
    verdict: "DIFFERENT_PACKS",
    confidence: "high",
    expected_identity_count: 3,
    note: "NOT one pack. 命运齿轮 (FOM) and 月亮工厂 (MCF) are two separately-named Create-modpack lines with DIFFERENT registered ids: modrinth.com/modpack/mcf vs the 命运齿轮 line. The 航空动力学 video names both (server = one pack, client = the other), which is what bridged the cluster. 机械动力 is the underlying mod, not a pack name.",
  },
  {
    author: "明月庄主",
    signature: "明月庄主::红石生电",
    verdict: "AMBIGUOUS",
    confidence: "medium",
    expected_identity_count: 2,
    note: "AMBIGUOUS - do NOT gate on this. 红石生电, 红石生电优化 and 绿色版红石生电优化 look like one family (a base pack plus an optimisation edition and a “green/low-spec” edition), and the uploader is the same. But the groups point at DIFFERENT Modrinth projects: modrinth.com/modpack/rso for 红石生电 versus modrinth.com/modpack/moon-luseban for 绿色版红石生电优化. Whether “优化”/“绿色版” are editions of one project or separate projects cannot be settled from this payload. Left unresolved rather than forced.",
  },
  {
    author: "Puikre",
    signature: "puikre::定制模组 成为锻造大师",
    verdict: "DIFFERENT_PACKS",
    confidence: "high",
    expected_identity_count: 4,
    note: "NOT one pack. 成为锻造大师 / 炼狱锻魂 / 锻造大师 是 one forging-RPG line (multiple version suffixes), while 奇妙的洞穴 and alex洞穴之旅 are Alexcraft cave-exploration packs. “成为锻造大师吧” is a SLOGAN the uploader repeats across unrelated releases. Different packs, no shared registered id anywhere.",
  },
  {
    author: "Terminus_54-32",
    signature: "terminus_54-32::泰坦 看简介",
    verdict: "DIFFERENT_PACKS",
    confidence: "medium",
    expected_identity_count: 5,
    note: "Different packs. Six separate releases across 1.7.10 / 1.12.2 / 1.21.1 / 1.21.4 with different Quark/Baidu folders and titles that name different things (泰坦整合包, 泰坦生物, 新泰坦生物 / New Titan Creatures, 怪物大乱斗). The single shared word 泰坦 names the mod, not the pack. No registered identity to unify them; treated as separate. (Several groups collapsing into __raw_ shows the detector, not the pack, is what connected them.)",
  },
  {
    author: "P1nero",
    signature: "p1nero::远梦之棺",
    verdict: "DIFFERENT_PACKS",
    confidence: "high",
    expected_identity_count: 3,
    note: "NOT one pack. Three distinct registered projects: 远梦之棺 (xyebbs:resource/1261, xyebbs:res-id/the-casket-of-reveries), 平底锅侠 (bbsmc:modpack/skillet-man, curseforge:skillet-man), 方可梦：炽白真形 (xyebbs:resource/41975). Bridged only by the generic word 高度 in “高度魔改”.",
  },
  {
    author: "VM汉化组",
    signature: "vm汉化组::城作者的又一 破碎城 amp 官方汉化",
    verdict: "DIFFERENT_PACKS",
    confidence: "high",
    expected_identity_count: 5,
    note: "NOT one pack. This is a TRANSLATION GROUP, not a pack author: it localises many unrelated foreign packs. Each group carries a different upstream project id (curseforge:prominence-2-rpg, curseforge:integrated-minecraft, curseforge:fractured-opolis, curseforge:project-architect-2). “官方汉化” is the house style. 卓越 II appears twice and those two groups ARE the same project - so this cluster is genuinely MIXED and its group-level verdict must not be applied per-pair.",
  },
  {
    author: "爱吃土豆的界王",
    signature: "爱吃土豆的界王::时光牧场",
    verdict: "DIFFERENT_PACKS",
    confidence: "high",
    expected_identity_count: 2,
    note: "NOT one pack. 时光牧场 is a farming/ranch pack whose 1.20.1 release is themed “打造你的侏罗纪公园”; the other group is a standalone 侏罗纪公园 pack announcement. Sharing the dinosaur theme is not sharing the pack. Both 1.20.1 and same uploader, which is what confused the scanner.",
  },
  {
    author: "爱吃土豆的界王",
    signature: "爱吃土豆的界王::jojo 与 含手机版",
    verdict: "DIFFERENT_PACKS",
    confidence: "high",
    expected_identity_count: 2,
    note: "NOT one pack. 原初修真 appears twice (those two groups are the same pack - a genuine under-merge) but the third group is a JoJo pack. “含手机版” is a fixed phrase in this uploader’s titles.",
  },
  {
    author: "Drunk耀爵",
    signature: "drunk耀爵::晴小姐 测试",
    verdict: "DIFFERENT_PACKS",
    confidence: "high",
    expected_identity_count: 2,
    note: "Two unrelated packs: DeepSeek鲸鱼娘 and 晴小姐. The 晴小姐 raw bucket and the 晴小姐 group ARE the same pack (real under-merge); DeepSeek鲸鱼娘 is separate. Bridged only by the word 测试.",
  },
  {
    author: "WZW_王宗王",
    signature: "wzw_王宗王::fcl 低配宝可梦 手机版 安装教程",
    verdict: "DIFFERENT_PACKS",
    confidence: "high",
    expected_identity_count: 3,
    note: "NOT one pack. Three different third-party packs ported to phone: 勇者之章3, 农场物语, 低配宝可梦. “FCL启动器/手机移植版” is the shared template.",
  },
  {
    author: "在下Shmily",
    signature: "在下shmily::优化 老手机2800帧 最牛优化",
    verdict: "CONFIRMED_SAME_PACK",
    confidence: "high",
    expected_identity_count: 1,
    note: "SAME PACK. All three are “最牛优化” (optimisation) releases, explicitly version-continuous: V3.9 -> V4.0 with the same naming and the same stated project (“最牛优化整合包”). Uploader’s own version wording on a named pack. The two “老手机” groups share QQ 377265276; the V4.0 video shares the CMpack roadmap. One pack split three ways.",
  },
  {
    author: "小水滴的源头",
    signature: "小水滴的源头::当你在 中拥有了学生们的能力 蔚蓝档案主题",
    verdict: "CONFIRMED_SAME_PACK",
    confidence: "high",
    expected_identity_count: 1,
    note: "SAME PACK. These are successive updates of one 蔚蓝档案 (Blue Archive) themed pack, told as a continuing story: the early release introduces the pack, then “整合包更新NPCAI系统！(跨时代篇)” and “整合包新版发布介绍！(更新篇)”. Same uploader, same theme, explicit CONTINUATION wording with no competing pack name. One pack split three ways.",
  },
  {
    author: "芦苇草的梦想",
    signature: "芦苇草的梦想::芦苇的 宣传片4",
    verdict: "CONFIRMED_SAME_PACK",
    confidence: "high",
    expected_identity_count: 1,
    note: "SAME PACK. All three carry the SAME registered Modrinth project (modrinth.com/modpack/my-biome-is-so-beautiful) and are version-continuous updates of the same 芦苇的 pack (4.0.11 -> 4.1.7 -> 4.2.12). One pack split three ways.",
  },
  {
    author: "马赵龙zhao_long",
    signature: "马赵龙zhao_long::宝可梦重铸",
    verdict: "AMBIGUOUS",
    confidence: "low",
    expected_identity_count: 2,
    note: "AMBIGUOUS - do NOT gate on this. The first two groups clearly describe 宝可梦重铸 1.16.5 (one is a version update of the other), so at least those two are the same pack. The third is an FCL phone-launcher release whose title names no pack at all, so it cannot be attributed. Verdict: at least one real under-merge here, but the cluster boundary is not trustworthy.",
  },
  {
    author: "爱吃土豆的界王",
    signature: "爱吃土豆的界王::山海大陆斗罗大陆 与",
    verdict: "CONFIRMED_SAME_PACK",
    confidence: "high",
    expected_identity_count: 1,
    note: "SAME PACK. All three titles are the same pack: “山海大陆X斗罗大陆” / “山海大陆·斗罗大陆与山海经为背景”. Two of them are near-identical duplicate announcements. One pack split two ways.",
  },
  {
    author: "啊liu22",
    signature: "啊liu22::简单群峦",
    verdict: "DIFFERENT_PACKS",
    confidence: "high",
    expected_identity_count: 2,
    note: "NOT one pack. 简单群峦 owns its own registered identities (curseforge:simple-tfc, mcmod:modpack/940, xyebbs:resource/842) and 群峦传说：野望 points at a different project (curseforge:terra-firma-far-horizons). Two different TFC-derived packs.",
  },
  {
    author: "ZangHeRo",
    signature: "zanghero::模拟殖民地",
    verdict: "DIFFERENT_PACKS",
    confidence: "medium",
    expected_identity_count: 2,
    note: "NOT one pack. 机械殖民地 and 模拟殖民地 are announced as different packs. 模拟殖民地 is used as a DESCRIPTOR on the 机械殖民地 videos (“[整合包][模拟殖民地][我的世界]”), which is exactly what bridged them; the 模拟殖民地 group instead belongs to 剑与王国. No shared registered identity exists to unify them. Module 2 called this UNDER_MERGE - this ledger overturns it.",
  },
  {
    author: "-阳春面面-",
    signature: "-阳春面面-::青春复兴",
    verdict: "CONFIRMED_SAME_PACK",
    confidence: "medium",
    expected_identity_count: 1,
    note: "SAME PACK. “青春复兴” IS the pack name (蔚蓝档案超大型科技冒险整合包：青春复兴) and the other group is its earlier “0.5.1版本发布”. Explicit version continuity on a named pack: 0.5.1 -> 0.7.1. The uploader’s own update wording is the decisive evidence.",
  },
  {
    author: "鹿清玖LQJ",
    signature: "__raw_BV1aRYC6cE4p",
    verdict: "STRONG_SAME_PACK",
    confidence: "medium",
    expected_identity_count: 1,
    note: "SAME PACK. Two videos with IDENTICAL titles (“我的世界1.20.1整合包，溯渊最新更新”) by one uploader, both landing in un-named __raw_ buckets. Same pack name 溯渊, same MC version, near-identical publish dates. The only reason they are separate groups is that the key fell below the discriminative threshold, which is itself the defect. Treating as one pack.",
  },
  {
    author: "爱吃土豆的界王",
    signature: "爱吃土豆的界王::考古与化石 侏罗纪 与",
    verdict: "CONFIRMED_SAME_PACK",
    confidence: "high",
    expected_identity_count: 1,
    note: "SAME PACK. Both titles name “考古与化石X侏罗纪” - literally the same pack, one with an “X” separator instead of a space. Split only by punctuation normalisation. One pack split two ways.",
  },
  {
    author: "爱玩游戏的烛梦",
    signature: "爱玩游戏的烛梦::基岩版 仿亡者世界",
    verdict: "CONFIRMED_SAME_PACK",
    confidence: "high",
    expected_identity_count: 1,
    note: "SAME PACK. Same uploader, same title “基岩版仿亡者世界整合包”, one is the V1.2 update of the other, same QQ 1082956985. One pack split two ways.",
  },
  {
    author: "XyeBBS中文论坛",
    signature: "xyebbs中文论坛::方可梦 炽白真形 宣传片 真正的",
    verdict: "DIFFERENT_PACKS",
    confidence: "high",
    expected_identity_count: 2,
    note: "NOT one pack. Two different registered projects (xyebbs:resource/41975 方可梦：炽白真形 vs xyebbs:res-id/Fictional 虚饰作品). This is a FORUM account cross-posting other people’s packs; “宣传片” is the shared word.",
  },
  {
    author: "星遥工坊",
    signature: "星遥工坊::刀剑异闻录周年 附属万行 全新拔刀全新挑战 流程 性能全面优化",
    verdict: "CONFIRMED_SAME_PACK",
    confidence: "high",
    expected_identity_count: 1,
    note: "SAME PACK. Both name 刀剑异闻录 as the pack; one is the anniversary update, the other an earlier release of the same named pack. Same uploader, explicit pack-name continuity in both titles. Note the two groups disagree on which key they produced, so normalisation is still unstable on this title - a defect for the remediation phase, not a reason to doubt the verdict.",
  },
  {
    author: "-六五六-",
    signature: "-六五六-::也能畅玩射击 六五六极致",
    verdict: "DIFFERENT_PACKS",
    confidence: "medium",
    expected_identity_count: 2,
    note: "NOT one pack. 六五六极致枪械 (gun pack) and 六五六极致美化 (aesthetic pack) are different products sharing the “六五六极致” brand prefix. Both share the same unrelated mirror link and QQ 966737963, which is a channel identity, not a pack identity. Brand prefix is not pack identity.",
  },
  {
    author: "星辉の天晓",
    signature: "星辉の天晓::天晓 匠魂之旅",
    verdict: "DIFFERENT_PACKS",
    confidence: "high",
    expected_identity_count: 2,
    note: "NOT one pack. 匠魂之旅 and 血肉寄生虫 are announced as two separate packs on different MC versions (1.12.2 vs 1.20.1). “天晓の整合包发布” is the uploader’s intro prefix, not a pack name.",
  },
  {
    author: "KonataWorks",
    signature: "__raw_BV1Fg8gzHE7K",
    verdict: "STRONG_SAME_PACK",
    confidence: "medium",
    expected_identity_count: 1,
    note: "SAME PACK. Two releases of the same unnamed 生电 (technical-Minecraft) pack, 1.21.4 and 1.21.5, same uploader, same QQ 536926371, consecutive versions. Neither title carries a distinct pack name, and the earlier one fell into a __raw_ bucket. Treating as one pack.",
  },
  {
    author: "我嘞个牢末ENd",
    signature: "我嘞个牢末end::增强 轻量 v 内容新鲜出炉",
    verdict: "CONFIRMED_SAME_PACK",
    confidence: "high",
    expected_identity_count: 1,
    note: "SAME PACK. Both titles say 《1.20.1原版增强》轻量整合包 - the SAME named pack, one being a v1.13 update and the other a weekend preview, and they share the same download link (123684.com/s/qfKUVv-ulrPH). One pack split two ways.",
  },
  {
    author: "无双小星",
    signature: "无双小星::幸运泰坦",
    verdict: "DIFFERENT_PACKS",
    confidence: "medium",
    expected_identity_count: 2,
    note: "NOT one pack. 1.20.1幸运泰坦 and 1.12.2泰坦整合包 are different packs on different MC generations (the 1.12.2 one is an un-named raw bucket). “泰坦” is the mod.",
  },
  {
    author: "无双小星",
    signature: "无双小星::幸运大 低配",
    verdict: "DIFFERENT_PACKS",
    confidence: "medium",
    expected_identity_count: 2,
    note: "NOT one pack. 1.8.9幸运大冒险低配 vs 1.12.2幸运方块低配版: different pack names, different MC versions, and DIFFERENT QQ groups (676321183 vs 775098626). “低配” is a shared descriptor.",
  },
  {
    author: "SmartAkita",
    signature: "smartakita::方块宝可梦 版本 含服务端 免费 cobblemon 进化特效 全新宝可梦添加 双打模式",
    verdict: "CONFIRMED_SAME_PACK",
    confidence: "high",
    expected_identity_count: 1,
    note: "SAME PACK. Both are the uploader’s Cobblemon 方块宝可梦 1.6 release for MC 1.21/1.21.1 - one a preview, one the release, both offering the same two servers and free distribution. Explicit version identity (1.6) on the same pack. One pack split two ways.",
  },
  {
    author: "吴也mc",
    signature: "吴也mc::全新的灾难降临 安全开局 平衡大增",
    verdict: "CONFIRMED_SAME_PACK",
    confidence: "high",
    expected_identity_count: 1,
    note: "SAME PACK. Both name 灾难降临 as the pack, one an update of the other by the same uploader (“全新的灾难降临…更新介绍” vs the original “灾难降临！…发布”). Explicit pack-name continuity plus update wording. One pack split two ways.",
  },
  {
    author: "孑孑雨不是牢孑",
    signature: "孑孑雨不是牢孑::烦村 史诗级",
    verdict: "CONFIRMED_SAME_PACK",
    confidence: "high",
    expected_identity_count: 1,
    note: "SAME PACK. Both are 烦村 / annoying_villagers: one is the 1.0 release, the other the 5.0 “史诗级更新”. Chinese title and English alias are given for the same pack in the first video, and the second is an explicit version update. One pack split two ways.",
  },
  {
    author: "碎砖做的砖块王",
    signature: "碎砖做的砖块王::幸运方块大 高版本的幸运方块大 全站 46个幸运方块 版本",
    verdict: "AMBIGUOUS",
    confidence: "low",
    expected_identity_count: 2,
    note: "AMBIGUOUS - do NOT gate on this. Different pack names AND different MC versions: 幸运之证 1.20.1 vs 幸运方块大冒险 1.19.2 (46 blocks). That points to two packs. But the uploader is a small lucky-block channel whose two lines may be a rename, and there is no registered identity to settle it. Cannot decide from this payload.",
  },
  {
    author: "Deemo旋律",
    signature: "deemo旋律::地球2 版本",
    verdict: "DIFFERENT_PACKS",
    confidence: "high",
    expected_identity_count: 2,
    note: "NOT one pack. 地球2 和 地球3 are SEQUELS, i.e. separately named packs, not versions of one pack.",
  },
  {
    author: "空空如也js",
    signature: "空空如也js::惊变100天但是是",
    verdict: "CONFIRMED_SAME_PACK",
    confidence: "high",
    expected_identity_count: 1,
    note: "SAME PACK. Both are the same 1.18.2 惊变100天 FTB500 pack: identical titles modulo suffix (“惊变100天v1.3更新FTB500+” vs “惊变100天但是是1.18.2”) AND identical download links on both MCBBS and MineBBS. Same registered thread identity. One pack split two ways.",
  },
  {
    author: "以乐太洋",
    signature: "以乐太洋::fcl 优化 帧率肯定包提升的啊",
    verdict: "DIFFERENT_PACKS",
    confidence: "high",
    expected_identity_count: 2,
    note: "NOT one pack. 《生于灾厄》 is an FTB adventure pack; the other is a generic 1.20.1 optimisation pack. Two different products sharing “fcl” (the launcher) and the same QQ channel.",
  },
  {
    author: "韬可梦",
    signature: "韬可梦::宝可梦 向 领先 版本 主打紧跟时事",
    verdict: "CONFIRMED_SAME_PACK",
    confidence: "high",
    expected_identity_count: 1,
    note: "SAME PACK. One 养老向 宝可梦 pack, described twice as staying on the newest version (“实时更新最新版” / “领先更新1.20.1版本”), same uploader, same QQ 773422289, same “目标是成为宝可梦大师” tagline. No competing pack name. One pack split two ways.",
  },
  {
    author: "星必尘Sguan",
    signature: "星必尘sguan::基岩版 rlcraft适配手机版 汉化 年度优化 超真实 addon",
    verdict: "CONFIRMED_SAME_PACK",
    confidence: "high",
    expected_identity_count: 1,
    note: "SAME PACK. Both are the same 基岩版 RLCraft 汉化 pack: v5 update and the “重大更新”, same uploader, same platform scope (BE/PE), same 超真实 descriptor and the same Lanzou mirror host. Explicit version continuity (v5 follows the earlier release). One pack split two ways.",
  },
  {
    author: "三只大猪TB_pig",
    signature: "三只大猪tb_pig::最适合初次游玩铁砧工艺的 铁砧工艺极速版",
    verdict: "CONFIRMED_SAME_PACK",
    confidence: "high",
    expected_identity_count: 1,
    note: "SAME PACK. Both carry the SAME registered project curveforge:anvilcraft-turbo (the release video additionally lists bbsmc:anvilcraft-turbo and xyebbs:res-id/anvilcraft-turbo, which are other mirrors of the same project). Title is identical: 铁砧工艺极速版. One pack split two ways.",
  },
  {
    author: "Karashok_Leo",
    signature: "__raw_BV1iDdLYJESg",
    verdict: "CONFIRMED_SAME_PACK",
    confidence: "high",
    expected_identity_count: 1,
    note: "SAME PACK. The raw bucket and the named spell-dimension group carry the IDENTICAL registered identity set: bbsmc:modpack/spell-dimension, curseforge:spell-dimension, github:Karashok-Leo/Spell-Dimension-Modpack, mcmod:modpack/1024. The 0.6.0 release simply produced a key the algorithm could not attach to the others. One pack split two ways.",
  },
  {
    author: "Pork猪排",
    signature: "pork猪排::化龍 金鳞岂是池中物 一遇风云便化龙",
    verdict: "CONFIRMED_SAME_PACK",
    confidence: "high",
    expected_identity_count: 1,
    note: "SAME PACK. All four groups are the same hualong pack: the titles name it and the versions run 1.0 -> 1.2 -> 1.3.1 -> 1.3.2 with no competing pack name. Two groups resolve to xyebbs:res-id/beloong and the other two to xyebbs:resource/885, which are the slug and numeric forms of ONE XyeBBS project. One pack split four ways.",
  },
  {
    author: "冰冻酸奶盒",
    signature: "冰冻酸奶盒::voxy 真实物理",
    verdict: "DIFFERENT_PACKS",
    confidence: "medium",
    expected_identity_count: 2,
    note: "NOT one pack. The first group is the named pack with 4 records and its own QQ 242291254; the second is a DIFFERENT pack by the same uploader. Bridged by shared component words (voxy / realistic physics / high-version cobblemon), which are mods and descriptors, not pack names.",
  },
  {
    author: "吴也mc",
    signature: "吴也mc::新版直接变76个模组 dark amp 汉化",
    verdict: "DIFFERENT_PACKS",
    confidence: "high",
    expected_identity_count: 4,
    note: "NOT one pack. This is a LOCALISATION channel: each group translates a different upstream pack and carries a different registered id (curseforge:better-minecraft-fabric, curseforge:medieval-minecraft-fabric, plus DarkRPG and Vault Hunters). Localisation wording is the house style.",
  },
  {
    author: "吴也mc",
    signature: "吴也mc::体验悠然人生 以种植等收获来推动经济发展的休闲",
    verdict: "AMBIGUOUS",
    confidence: "low",
    expected_identity_count: 2,
    note: "AMBIGUOUS - do NOT gate on this. The first two groups are announced as SEPARATE numbered entries, which suggests sequels rather than one pack split; the third is an unnumbered entry. No registered identity exists to settle it.",
  },
  {
    author: "在职玩家JoStar",
    signature: "在职玩家jostar::去吧 方可梦大师",
    verdict: "AMBIGUOUS",
    confidence: "low",
    expected_identity_count: 2,
    note: "AMBIGUOUS - do NOT gate on this. The first group is well established (3.0 / 4.0 / 1.7 all in one group). The second group does NOT name that pack at all, so it may be a separate pack rather than an earlier release. A possible real split, but the cluster boundary is not trustworthy enough to gate on.",
  },
  {
    author: "墨言eclipse",
    signature: "墨言eclipse::颠覆性的",
    verdict: "DIFFERENT_PACKS",
    confidence: "high",
    expected_identity_count: 3,
    note: "NOT one pack. This single group contains TWO different registered projects (bbsmc:minecraft-photo-wanderer AND curseforge:sendims-banforges / mcmod:1426). The other groups are a third project (mcmod:1346, xyebbs:1491) and a fourth. The shared phrase is a marketing adjective used on all of them.",
  },
  {
    author: "墨言eclipse",
    signature: "墨言eclipse::大型 禁忌 远古炼金 世界污染 3万行代码深度 涅槃v 0 宣传视频",
    verdict: "CONFIRMED_SAME_PACK",
    confidence: "high",
    expected_identity_count: 1,
    note: "SAME PACK (nirvana). All four groups are the nirvana pack: every member carries xyebbs:resource/37418 and three of them also carry mcmod:modpack/1418. Versions 0.1.5 through 0.2 are explicit updates of the same named pack. One pack split four ways. NOTE: this is the nirvana half of the module-2 result - see the_nirvana_lesson for why the OTHER nirvana-labelled group is NOT part of it.",
  },
  {
    author: "墨言eclipse",
    signature: "墨言eclipse::未尽之路涅槃",
    verdict: "DIFFERENT_PACKS",
    confidence: "high",
    expected_identity_count: 2,
    note: "NOT the same pack as nirvana. This is the FALSE-POSITIVE lesson: this group uses nirvana as a SUBTITLE of the unfinished-path line, and it carries a completely different registered identity (bbsmc:modpack/unfinished_path_nirvana, xyebbs:res-id/TUPN) whereas the nirvana pack is xyebbs:resource/37418 + mcmod:1418. The other group here is unfinished-path itself (bbsmc:unfinished-path, xyebbs:UP). Two packs; the split is CORRECT.",
  },
  {
    author: "小兜兜呀_",
    signature: "小兜兜呀_::原神与机械 的时代",
    verdict: "CONFIRMED_SAME_PACK",
    confidence: "high",
    expected_identity_count: 1,
    note: "SAME PACK. Both groups carry the SAME two registered ids (a BBSMC project plus its -lts edition). The second video is a milestone / download-count announcement for the very same pack. One pack split two ways.",
  },
  {
    author: "流霜雾影",
    signature: "流霜雾影::愚者版本大",
    verdict: "CONFIRMED_SAME_PACK",
    confidence: "high",
    expected_identity_count: 1,
    note: "SAME PACK. Both groups carry the SAME registered id bbsmc:modpack/the-fool, and the versions run v0.1 -> v0.2 as explicit major updates of the one named pack. One pack split two ways.",
  },
  {
    author: "炒雪吵狐力o",
    signature: "炒雪吵狐力o::rapid",
    verdict: "CONFIRMED_SAME_PACK",
    confidence: "high",
    expected_identity_count: 1,
    note: "SAME PACK. All three groups carry the SAME registered id mcmod:modpack/1159 and every title names the same optimisation pack across successive updates. One pack split three ways.",
  },
  {
    author: "科里森Corrison",
    signature: "科里森corrison::apotheosis conquest",
    verdict: "CONFIRMED_SAME_PACK",
    confidence: "high",
    expected_identity_count: 1,
    note: "SAME PACK. Both groups carry the SAME registered id xyebbs:resource/1421, and the second group is literally the English title of the first (Apotheosis Conquest). Versions run v1.1 through v2.3 on one pack. One pack split two ways.",
  },
  {
    author: "落烟雨辰呀",
    signature: "落烟雨辰呀::诡厄 使徒",
    verdict: "CONFIRMED_SAME_PACK",
    confidence: "medium",
    expected_identity_count: 1,
    note: "SAME PACK. The two groups are the same pack name with a separator difference; the MCMod id mcmod:modpack/1241 belongs to the 1.0.x line and the two newer videos carry the BBSMC slugs. Versions 1.0.6 -> 1.1.0 are continuous. One pack split two ways.",
  },
];

const OVERTURNS = {
  'zanghero::机械殖民地 vs zanghero::模拟殖民地':
    'Module 2: UNDER_MERGE. This ledger: DIFFERENT_PACKS. 模拟殖民地 is a descriptor word on 机械殖民地 titles; the 模拟殖民地 group belongs to 剑与王国.',
  '在职玩家jostar::去吧 方可梦大师 vs 在职玩家jostar::方可梦':
    'Module 2: UNDER_MERGE. This ledger: AMBIGUOUS (not gated). The 方可梦 group names no pack, so it may be a separate pack rather than an earlier release of 去吧，方可梦大师.',
  '一个小寂哦::怪物大乱斗 vs 一个小寂哦::怪物大乱斗重生':
    'Ruled DIFFERENT_PACKS (手机版 vs 重生 are two separate releases), consistent with the module-2 candidate-layer finding that 怪物大乱斗 is a real false merge.',
  '爱吃土豆的界王::时光牧场 vs 爱吃土豆的界王::侏罗纪公园':
    'Module 2: UNDER_MERGE. This ledger: DIFFERENT_PACKS. Only the dinosaur theme is shared.',
};

// ------------------------------------------------------------------ plumbing
function keyOf(finding) {
  return finding.author + '||' + [...finding.group_keys].sort().join('|');
}

/**
 * Map a case (author + signature group_key) onto the live cluster that contains
 * that signature group. Throws when a case cannot be placed: a silently-dropped
 * adjudication is the one failure mode this ledger must never have.
 */
function resolveCase(c, findings) {
  // `signature` is normally a FULL group key (author::tail). Un-named raw buckets
  // (`__raw_<bvid>`) carry NO author prefix, so those are matched verbatim.
  const k = c.signature.includes('::') || c.signature.startsWith('__raw_')
    ? c.signature
    : c.author + '::' + c.signature;
  const hits = findings.filter((f) => f.group_keys.includes(k));
  if (hits.length === 0) {
    throw new Error('adjudication case has no matching cluster: ' + k);
  }
  if (hits.length > 1) {
    throw new Error(
      'adjudication signature is ambiguous (matches ' + hits.length + ' clusters): ' + k,
    );
  }
  return keyOf(hits[0]);
}

function main() {
  const idArtifact = JSON.parse(fs.readFileSync(IDENTITY, 'utf8'));
  const evArtifact = JSON.parse(fs.readFileSync(EVIDENCE, 'utf8'));
  const evByKey = new Map(evArtifact.findings.map((f) => [keyOf(f), f]));

  // Resolve every case to exactly one live cluster up front, so a bad signature
  // throws before any artifact is written.
  const adjByKey = new Map();
  for (const c of CASES) adjByKey.set(resolveCase(c, idArtifact.findings), c);
  if (adjByKey.size !== CASES.length) {
    throw new Error(
      'two adjudication cases resolved to the same cluster (' +
        CASES.length + ' cases -> ' + adjByKey.size + ' clusters)',
    );
  }

  const rows = idArtifact.findings.map((f) => {
    const key = keyOf(f);
    const adj = adjByKey.get(key);
    const ev = evByKey.get(key) || {};
    return {
      layer: 'undermerge_adjudication',
      cluster_key: key,
      author: f.author,
      group_keys: f.group_keys,
      group_count: f.group_count,
      record_count: f.record_count,
      detector_reasons: f.detector_reasons,
      shared_tokens: f.shared_tokens,
      project_identities_shared_by_all_groups: f.project_identities_shared_by_all_groups,
      project_identities_shared_by_some_groups: f.project_identities_shared_by_some_groups,
      verdict: adj ? adj.verdict : null,
      confidence: adj ? adj.confidence : null,
      expected_identity_count: adj ? adj.expected_identity_count : null,
      evidence: {
        note: adj ? adj.note : null,
        project_identities: f.project_identities_shared_by_all_groups,
        supporting: {
          shared_download_urls: ev.shared_download_urls || [],
          shared_qq_ids: ev.shared_qq_ids || [],
          'url_qq_caveat': 'Supporting context only. A shared netdisk URL can cover several packs (Phase 3G-E: 28 packs on one link), so it never decides a verdict on its own.',
        },
      },
    };
  });

  const unadjudicated = rows.filter((r) => !r.verdict).map((r) => r.cluster_key);
  // Every case resolved (resolveCase throws otherwise); this catches the reverse:
  // a cluster that exists but that nobody adjudicated.
  const declaredButAbsent = [...adjByKey.keys()].filter(
    (k) => !rows.some((r) => r.cluster_key === k),
  );
  const counts = {};
  for (const v of VERDICTS) counts[v] = rows.filter((r) => r.verdict === v).length;

  const confirmed = rows.filter((r) => r.verdict === 'CONFIRMED_SAME_PACK');
  const strong = rows.filter((r) => r.verdict === 'STRONG_SAME_PACK');
  const partial = rows.filter((r) => r.verdict === 'PARTIAL');
  const ambiguous = rows.filter((r) => r.verdict === 'AMBIGUOUS');
  const different = rows.filter((r) => r.verdict === 'DIFFERENT_PACKS');

  const gate = [...confirmed, ...strong];

  const result = {
    phase: '3G-F.2-B',
    generated_at: new Date(
      (process.env.SOURCE_DATE_EPOCH ? Number(process.env.SOURCE_DATE_EPOCH) * 1000 : Date.now()),
    ).toISOString(),
    artifact: 'bilibili_undermerge_adjudication_v2',
    question: 'Of the under-merge candidates from module 2, which are genuinely one pack split apart, and which are merely similarly-named or wrong candidates?',
    separation_of_concerns: {
      module2_scanner: 'build/audit/bilibili_cross_group_undermerge_v2.json (review list; no verdicts)',
      adjudication: 'pipeline/audit/bilibili_undermerge_adjudication_v2.js (this file; hand-maintained)',
      rule: 'No verdict is derived by rule. Every entry was written by reading member titles and registered project ids.',
    },
    evidence_policy: {
      strong: [
        'same registered project identity (MCMod / XyeBBS / BBSMC / CurseForge / Modrinth id or slug)',
        'same explicit pack name continuity',
        'uploader explicit update / version wording on a named pack',
      ],
      supporting_only: ['same download URL', 'same QQ', 'same theme'],
      never_sufficient: 'A shared download URL or QQ group can never decide a verdict; one Quark link was proven to front 28 different packs (Phase 3G-E).',
    },
    the_nirvana_lesson: {
      principle: '"the title / series looks the same" != "the same pack"',
      evidence: {
        '涅槃': { records: 5, group_keys: 4, identities: ['xyebbs:resource/37418', 'mcmod:modpack/1418'] },
        '未尽之路-涅槃': { records: 2, group_keys: 1, identities: ['bbsmc:modpack/unfinished_path_nirvana', 'xyebbs:res-id/TUPN'] },
        '未尽之路(unfinished-path)': { records: 3, group_keys: 1, identities: ['bbsmc:modpack/unfinished-path', 'xyebbs:res-id/UP'] },
        expected_packs: 2,
      },
      explanation: '未尽之路涅槃 carries 涅槃 as a SUBTITLE of the 未尽之路 line, so it shares a word with the 涅槃 pack without being it. The registered identities separate them cleanly. Therefore the module-2 scanner splitting the 涅槃 keys into two findings is CORRECT, and 涅槃 is the reference FALSE-POSITIVE under-merge candidate.',
      consequence: 'Module 2 recorded two of the 涅槃 groups as FALSE_SPLIT_INDICATOR. Under this adjudication those are correct as SPLITS (different pack) and must NOT be merged by any runtime change.',
    },
    candidates_total: rows.length,
    adjudicated_total: rows.filter((r) => r.verdict).length,
    unadjudicated,
    declared_but_absent: declaredButAbsent,
    counts,
    totals: {
      confirmed_same_pack: confirmed.length,
      strong_same_pack: strong.length,
      different_packs: different.length,
      ambiguous: ambiguous.length,
      partial: partial.length,
      runtime_gate_size: gate.length,
    },
    expected_identity_totals: {
      packs_to_unify: gate.reduce((n, r) => n + ((r.group_count || 1) - 1), 0),
      records_in_gated_cases: gate.reduce((n, r) => n + (r.record_count || 0), 0),
    },
    runtime_gate_clusters: gate.map((r) => ({
      cluster_key: r.cluster_key,
      author: r.author,
      verdict: r.verdict,
      confidence: r.confidence,
      group_count: r.group_count,
      record_count: r.record_count,
      expected_identity_count: r.expected_identity_count,
      group_keys: r.group_keys,
      evidence_note: r.evidence.note,
    })),
    overturns_of_module2: OVERTURNS,
    findings: rows,
  };

  // Deterministic ordering: sort by cluster_key so the artifact is byte-stable.
  result.findings.sort((a, b) => (a.cluster_key < b.cluster_key ? -1 : a.cluster_key > b.cluster_key ? 1 : 0));
  result.runtime_gate_clusters.sort((a, b) => (a.cluster_key < b.cluster_key ? -1 : 1));
  result.unadjudicated.sort();

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(result, null, 2), 'utf8');

  console.log('=== Phase 3G-F.2-B under-merge adjudication ledger ===');
  console.log(`candidates total      : ${rows.length}`);
  console.log(`adjudicated           : ${result.adjudicated_total}`);
  for (const v of VERDICTS) console.log(`  ${v.padEnd(22)}: ${counts[v]}`);
  console.log(`runtime gate size     : ${gate.length} (CONFIRMED + STRONG only)`);
  console.log(`packs to unify        : ${result.expected_identity_totals.packs_to_unify}`);
  if (unadjudicated.length) console.log(`!! UNADJUDICATED: ${unadjudicated.join(', ')}`);
  if (declaredButAbsent.length) console.log(`!! DECLARED BUT ABSENT: ${declaredButAbsent.join(', ')}`);
  console.log(`written               : ${path.relative(REPO_ROOT, OUT)}`);
}

main();

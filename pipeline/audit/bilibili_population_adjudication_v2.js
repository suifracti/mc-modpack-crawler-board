/**
 * Phase 3G-F.1-B - POPULATION-WIDE ADJUDICATION LEDGER (v2).
 * Phase 3G-F.2-A - RE-ADJUDICATED against the remediated runtime (3f81db2 + Rule 5).
 *
 * THE POINT OF THIS FILE
 * ----------------------
 * §2 of the task is non-negotiable: detection and adjudication must be SEPARATE
 * layers. The detector (bilibili_population_candidate_scan_v2.js) over-reports by
 * design and MUST NOT emit a verdict. This file is the ONLY place a verdict is
 * ever produced, and it produces them from a HAND-MAINTAINED TABLE - every entry
 * below was written by reading every member title, not by any rule.
 *
 *   layer 1  candidate detection   -> build/audit/bilibili_population_candidates_v2.json
 *   layer 2  human adjudication    -> pipeline/audit/bilibili_population_adjudication_v2.json  (this)
 *
 * VERDICTS
 * --------
 *   REAL_FALSE_MERGE       members are demonstrably DIFFERENT packs that the
 *                          algorithm merged into one group
 *   LEGITIMATE_SAME_PACK   members are the SAME pack (the anchor is the pack
 *                          name, or a stable release-series name)
 *   FALSE_SPLIT_INDICATOR  the group looks suspicious *because the real pack was
 *                          split across groups* - i.e. the finding is an
 *                          under-merge symptom, not a false merge. Counting it as
 *                          a false merge would be a miscount.
 *   AMBIGUOUS              genuinely undecidable from title + supporting evidence.
 *                          Reported as such, NEVER counted as a false merge.
 *
 * THE RETIRED SET (3G-F.2-A)
 * --------------------------
 * The 3G-F.1-B ledger carried 8 REAL_FALSE_MERGE entries. All 8 are now FIXED in
 * the runtime, which means the detector no longer emits them (the offending groups
 * no longer exist). Deleting the entries would erase the evidence, so they are
 * moved to RETIRED_FALSE_MERGES with the cause that closed each one, and
 * `declared_but_absent` stays EMPTY by construction. A group may not silently
 * vanish from this ledger.
 *
 * WHY THE FALSE-SPLIT CATEGORY EXISTS
 * -----------------------------------
 * The 涅槃 case (uploader 墨言eclipse) was originally recorded as "7 records, ONE
 * pack, split into 5 groups" - i.e. the algorithm's job was to merge 7 -> 1.
 * Phase 3G-F.1-A corrected that premise by reading the STRUCTURED download_links:
 *
 *   5 records  ->  mcmod.cn/modpack/1418 + xyebbs.com/resources/37418   (涅槃)
 *   2 records  ->  bbsmc.net/modpack/unfinished_path_nirvana
 *                  + xyebbs.com/res-id/TUPN                              (未尽之路-涅槃)
 *
 * and the uploader's own description states the two are unrelated. The correct
 * target is therefore TWO groups, not one; forcing 1 would be a real over-merge.
 * The runtime now produces exactly 2, so the five old keys collapse to two live
 * ones and coverage is asserted against the CORRECTED list below.
 *
 * URL / QQ ARE SUPPORTING EVIDENCE ONLY. Phase 3G-E proved a single download URL
 * can span many different packs (one uploader had 28 distinct packs behind one
 * Quark link), so a shared URL/QQ never establishes same-pack identity. Where a
 * shared QQ is decisive it is used only as CORROBORATION, never as proof.
 *
 * Usage: node pipeline/audit/bilibili_population_adjudication_v2.js
 * Output: pipeline/audit/bilibili_population_adjudication_v2.json
 */
const fs = require('fs');
const path = require('path');

const REPO_ROOT = path.resolve(__dirname, '..', '..');
const CANDIDATES = path.join(REPO_ROOT, 'build', 'audit', 'bilibili_population_candidates_v2.json');
const UNDERMERGE = path.join(REPO_ROOT, 'build', 'audit', 'bilibili_cross_group_undermerge_v2.json');
const OUT = path.join(REPO_ROOT, 'pipeline', 'audit', 'bilibili_population_adjudication_v2.json');

// ---------------------------------------------------------------------------
// HAND-MAINTAINED VERDICT TABLE.
// key = candidate group_key. Every one of the 113 detector candidates must
// appear here; a missing key fails the ledger consistency check (and the test).
//
// confidence: high | medium | low
//   high   - the titles alone are conclusive
//   medium - titles strongly indicate, corroborated by URL/QQ or series naming
//   low    - plausible but could flip with more context
// ---------------------------------------------------------------------------
const VERDICTS = {
  '墨言eclipse::未尽之路涅槃': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '两条均为《未尽之路-涅槃》（预发布 / 发布前预热），同一包。上传者结构化下载链接（bbsmc unfinished_path_nirvana + xyebbs res-id/TUPN）与 涅槃 的（mcmod modpack/1418 + xyebbs resources/37418）互不相同，上传者本人也说明两者无关 → 组内合法，不是误合并。' },
  '墨言eclipse::拒绝同质': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'medium', note: '三条均为『未尽之路 / Unfinished Path』同一包（0.13 / 主线完成 / 1.0 正式发布）。“拒绝同质！抵制水槽！”是该包的固定宣传口号 → anchor 是 slogan，但成员同包。与“未尽之路涅槃”组的关联属于跨包（涅槃 ≠ 未尽之路），不应合并。' },
  '时唅::辐射新世纪': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '11 条全部为《辐射新世纪》同一包的 0.1~6.7 版本发布；anchor 是包名。' },
  '时唅::辐射次时代': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '8 条全部为《辐射次时代》同一包 1.0~6.0；anchor 是包名（anchor_index==0，v1 scanner 结构性看不到）。' },
  '时唅::大型末世 辐射 生还者': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '4 条均为《生还者》同一包 1.0~3.1；anchor 是标题模板词而不是包名，但成员同包。' },
  '时唅::大型 末世 潜行者': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '3 条均为《潜行者》同一包 2.1~3.1；anchor 是标题模板词。' },
  'verre::神秘启旅': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '8 条均为「神秘启旅」同一包 1.4~1.9 + 正式版；anchor 是包名。' },
  '懂嗎懂嗎::齿轮与腐肉': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '8 条均为「齿轮与腐肉」同一包 0.21~0.50；anchor 是包名。' },
  '科里森corrison::神之征伐 版本': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '5 条均为《神之征伐 / Apotheosis Conquest》同一包 v1.1~v2.3；anchor 是“神之征伐 版本”模板，但成员同包。' },
  '缓慢的开始::soa3': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '7 条均为 SoA3（虚无世界3）同一包；anchor 是系列代号。' },
  'confectionaryqwq::地平线': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '6 条均为 Horizon 地平线整合包 v1.2.0~v2.1.0 同一包；anchor 是包名。' },
  'zicaiot::农场物语': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '6 条均为「农场物语」同一包（forge 1.1.7~1.6.7）；anchor 是包名。' },
  '小兜兜呀_::原神与机械 的时代': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '6 条均为《原神与机械冒险的时代》同一包 v3.5.4~v3.5.12；anchor 是包名一部分。' },
  'from火星::类幸存者 终末幸存者 last one': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '5 条均为《终末幸存者/Last One》同一包 0.3.3~0.9；anchor 是包名。' },
  '爱吃土豆的界王::蛊真人 与': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '7 条均为「蛊真人」同一包（金木水火土雷血/智道/偷道/律道更新 + 1.21.1）；anchor 落在“发布与介绍”模板词上。' },
  '狐狸の妙妙屋::蛊真人': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '4 条均为「蛊真人」同一包 2.1~2.4；anchor 是包名。' },
  '青山半隐::蛊真人': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为「蛊真人」同一包 2.4/2.5；anchor 是包名，sharedQQ 894591426 佐证。' },
  '一个个方块呀::雾中人': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '3 条均为「雾中人整合包」同一包 V3.0~V6.5；anchor 是包名。' },
  '一个个方块呀::全新雾中人': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为「雾中人整合包」同一包 V2.0/V30.5.5；anchor 是“全新雾中人”称谓。' },
  '明月庄主::绿色版红石生电优化': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'medium', note: '3 条均为「绿色版红石生电优化」同一包（1.19.4/1.20.1）；anchor 就是包名，虽含模板词但确为该 uploader 的包名。' },
  '明月庄主::红石生电': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'medium', note: '3 条均为「红石生电」同一包（26.1/26.2/1.21.4）；anchor 是包名。与「绿色版红石生电优化」是两个包但同属红石生电系列，此处不合并。' },
  '明月庄主::命运齿轮': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'medium', note: '3 条均为《命运齿轮 / 命运齿轮FOM》同一包 1.0.4~1.4.8；anchor 是包名。' },
  '明月庄主::月亮工厂 f': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为《月亮工厂 MCF》同一包（1.19.2-3.0 / 1.20.1）；anchor 是包名。' },
  '炒雪吵狐力o::rapid': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '3 条均为 Rapid Optimization 同一优化包的重复发布；anchor 是包名。' },
  'grainalcohol::origincraft 起源 quot 年轻人的第一款 quot': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为 [OriginCraft] 我的世界:起源 同一包（V2000 / v1.13）；anchor 是包名 + 宣传语。' },
  '无名-呀::奥特之路 版本正式 ftb 奥特曼': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为「奥特之路」同一包 1.0/1.6.5；anchor 是包名 + 模板词。' },
  '最爱仪仪::侏罗纪': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为「侏罗纪」同一包（1.21.1 汉化 1.1）；sharedQQ 1090334122 佐证。' },
  'locknar::mon': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '4 条均为《MON》同一包 0.4.1~0.6；anchor 是包名。' },
  '林点午安事睡觉::明日方舟': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '4 条均为《大群方舟》同一包 3.0~4.0；“明日方舟”是主题模组名，但 4 条 sharedQQ 765174534 相同且标题同构，判同包。' },
  '爱吃土豆的界王::时光牧场': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '4 条均为「时光牧场」同一包（侏罗纪主题）；sharedQQ 240052014 佐证。' },
  'karashok_leo::咒次元': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '3 条均为「咒次元」同一包 0.7.0/0.8.0 + 发布；anchor 是包名。' },
  '加一点芝士::剑痕纪元': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '3 条均为「剑痕纪元」同一包 0.9.71 + 两条宣传；anchor 是包名。' },
  '宅际不上班::我非我': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '3 条均为「我非我」同一包 0.0.6/1.0；anchor 是包名。' },
  '白银_1223::血族机械师': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '3 条均为「血族机械师」同一包 1.1.0/1.1.2 + 发布；anchor 是包名。' },
  '--axx--::mygo': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'medium', note: '2 条均为该 uploader 的 MYGO 命名（Ver1.8.0 / 1.5.0），sharedURL 1 + sharedQQ 1031665602。“鬼影重重”与“多人枪战”是否为两次改名无法从标题确证 → 保守判同一包，不计数为误合并。' },
  'jsi我的世界制作组::create delight': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为 Create Delight 同一包 1.0.2 / 无版本号；anchor 是包名。' },
  'stvm647_mcraft::设身处地': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为「设身处地」同一包 2.0/3.0；anchor 是包名。' },
  '吴也mc::内容 better 版': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为吴也mc 的《更好的MC / Better Minecraft》汉化介绍（v11 / 最新），同一包；“内容 better 版”是公告式尾缀。' },
  '吴也mc::冬境边域': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为「冬境边域」同一包；anchor 是包名。' },
  '咱叫小屿::隔离区': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为「隔离区」同一包（正式版 / v0.2 预告）；anchor 是包名。' },
  '墨言eclipse::命轮无章 infinite random': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为《命轮无章 [Infinite Random]》同一包 1.3；sharedURL 7 + sharedQQ 1073842075 强佐证。' },
  '宿墟-1exingt0n::暗涌 深岩恐惧': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为《暗涌：深岩恐惧》同一包（1.0.1 / 公测）；anchor 是包名。' },
  '小硕3365::全家桶': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为 MASA 全家桶类整合包（1.18.2/1.19.2）同一 uploader 的同名包；“全家桶”是包名一部分。' },
  '异空间520::异空间 神奇宝贝': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为《异空间 神奇宝贝》同一包（2.1 / 无版本）；anchor 是包名。' },
  '月与风-yyf::慢砌山河': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为「慢砌山河」同一包（更新日志 1/3）；anchor 是包名。' },
  '深夜鸽子::真理之路': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为《真理之路》同一包；anchor 是包名。' },
  '爱吃土豆的界王::新模拟大都市 与 模拟城市': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条标题完全相同（同一包同一版本），sharedQQ 240052014 佐证；anchor 是包名。' },
  '爱吃土豆的界王::山海大陆斗罗大陆 与': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条标题完全相同（同一包同一发布），sharedQQ 240052014 佐证。' },
  '爱吃土豆的界王::火影忍者 与': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为「火影忍者」同一包（1.20.1 / 无版本），sharedQQ 298929369 佐证。' },
  '狐狸の妙妙屋::冰火传说 与': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为「冰火传说」同一包（1.20.1）；sharedURL 4 佐证。' },
  '狐狸の妙妙屋::时光牧场': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为「时光牧场」同一包（1.1 / 无版本）；anchor 是包名。注意与 爱吃土豆的界王::时光牧场 是不同 uploader 的同名包，不应跨包合并。' },
  '狐狸の妙妙屋::模拟大都市': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为「模拟大都市」同一包（1.3 / 无版本）；anchor 是包名。' },
  '瞳彩鹿454445::hnt': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为《HNT》同一包（V1.5 正式版 / 测试版）；anchor 是包名。' },
  '莱斯莎沃rs_::休闲 异世界探险家': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为《异世界探险家》同一包（1.18.2 实机 / 1.20.1 重大更新）；sharedQQ 820089616 佐证。' },
  '骑马的无情小叶::海贼之旅': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为《海贼之旅》同一包；anchor 是包名。' },
  'ac6_::云游四海': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '9 条均为《云游四海》同一包 V1.1~V1.6.2；anchor 是包名。' },
  '瑶山枫叶::阿卡迪亚的天启': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '9 条均为《阿卡迪亚的天启》同一包 0.5.0~1.8；sharedQQ 526239979 ×9 佐证；anchor 是包名。' },
  '勾圈剋尖326::香草纪元 食旅纪行': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '7 条均为《香草纪元：食旅纪行》同一包 1.5.0~2.7.1；anchor 是包名。' },
  '绘名青棺::虚饰作品': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '7 条均为《虚饰作品》同一包 v0.5~v1.4；sharedQQ 693928637 ×7 佐证；anchor 是包名。' },
  '一个小寂哦::弑神之路': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'medium', note: '6 条均为《弑神之路》同一包 1.0~2.2（含“神器锻世”“泰坦再临”版本副标题）；anchor 是包名。注：该组与“星辉死神”“四叶草”组共享成员标题中的 Boss/物品词，但本组自身是同一包。' },
  'altnoir::亚特兰深渊': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '4 条均为《亚特兰深渊 / AtlanAbyss》同一包 1.0~1.2 + 宣传片；anchor 是包名。' },
  'cyq2号机::foodie': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '4 条均为《Foodie 吃货物语》同一包 1.2.0~2.0.1；anchor 是包名。' },
  'p1nero::远梦之棺': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '4 条均为《远梦之棺》同一包 1.5.0/2.0 + 百万下载纪念；anchor 是包名。' },
  '非茉涟柠::hunt history 1949': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '4 条均为《猎杀：历史 1949 / Hunt: History 1949》同一包 1.0~1.2；sharedURL 4 + sharedQQ 1103681710 佐证。' },
  'monica_squirrel::渎圣织罪': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '3 条均为《渎圣织罪》同一包 0.5/0.5-zero + 公测；sharedQQ 713784391 佐证。' },
  '一个小寂哦::追影之旅': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '3 条均为《追影之旅》同一包 v1.1/v1.2 + 发布；anchor 是包名。' },
  '啊liu22::群峦野望': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '3 条均为《群峦野望》同一包 1.1~1.3；sharedURL 3 + sharedQQ 672326817 佐证。' },
  '星遥工坊::宁然一隅': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '3 条均为《宁然一隅》同一包 1.7.3/1.10.3 + Continue；anchor 是包名。' },
  '橘子皮zero::拯救世界重建文明': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '3 条均为《凋落之花》同一包；“拯救世界重建文明”是副标语，但 members 明确同包；sharedQQ 971333265 佐证。' },
  '没睡醒的老王呀::annoying': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '3 条均为《Annoying Players / 烦人的玩家》同一包 1.0 + 1.20.1 更新；sharedQQ 709147063 佐证。' },
  '猹氪拉_::殉道之路': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '3 条均为《殉道之路》同一包 v3.2/3.3 + 更新介绍；anchor 是包名。' },
  '老本願::魔之逆鳞': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '3 条均为《魔之逆鳞》同一包 0.6 公测/更新/正式；anchor 是包名。' },
  '666sxss666::海洋主题': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'medium', note: '2 条均为同一 uploader 的“1.20.1 海洋主题整合包（测试版）”；标题互指，sharedURL 1 佐证。“海洋主题”是泛化名但该 uploader 只发布此包。' },
  'monica_squirrel::超多定制饰品 亵渎': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为《亵渎》同一包的发布宣传；“超多定制饰品”是宣传语。' },
  'puikre::定制模组 成为锻造大师': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为“成为锻造大师”同一包；anchor 是包名（前面是 slogan 前缀，两次措辞不同）。' },
  'sino_p::瓶中伊甸': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为《瓶中伊甸》同一包（0.1.2 更新 / 发布介绍）；sharedURL 2 佐证。' },
  'zanghero::机械殖民地': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为《机械殖民地》同一包 1171/1.1.5；anchor 是包名。' },
  '共轭o::武道宗师': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为《武道宗师》同一包（1.0 完整版 / 发布）；anchor 是包名。' },
  '啥勾石玩意::烦人的村民 传奇之战': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为《烦人的村民-传奇之战》同一包 4.0/5.0；anchor 是包名。' },
  '大漠神枪::level up': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为《Level Up》同一包 1.0/1.1；anchor 是包名。' },
  '小小伊布酱::光芒消逝之日': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为《光芒消逝之日》同一包（1.4.0 / 发布介绍）；anchor 是包名。' },
  '小枯菜::梦想是找到传说中的 piece 成为海贼王 航海旅': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为「航海旅」同一包（任务更新 / 发布）；前半是固定标语。' },
  '橘仔io::体验自己一步一步 城镇和发展人口的乐趣': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为《海岛小镇》同一包（1.20.1 更新 / 发布）；sharedQQ 627978930 佐证。' },
  '润润79::尘封古纪': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为《尘封古纪》同一包 1.0/2.0.2；anchor 是包名。' },
  '磁钢百合::旅行时光 饥饿': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为「旅行时光:饥饿」同一包（1.7.0 / 公测）；anchor 是包名。' },
  'akrcloud::雾中人红衣学姐恐怖': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为「雾中人红衣学姐恐怖」同一包（更新 3.0/4.0）；anchor 是包名（长模板式命名）。' },
  'inax白咕::别卷了': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为《别卷了》同一包（发布 + *2! 后续）；anchor 是包名。' },
  '终极劲爽全家桶::逆转未来': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为《逆转未来》同一包（2.3.1 / 发布）；anchor 是包名。' },
  '账号已注销::末落龙瞳': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为《末落龙瞳》同一包（1.18.2 发布 / 更新日志）；anchor 是包名。' },
  '_昊日天_::昊日天': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'medium', note: '2 条均为该 uploader 同名整合包（1.14/1.16.5）；anchor 是 uploader 名兼包名。两版本 MC 版本不同但同属该 uploader 的单一常驻包，判同包。' },
  '墨竹ギ::poetry of the abyss': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '已核实（对 bili_data 逐字读题）：两条均为《深渊之诗 / Poetry of the Abyss》同一包的 2.2 更新与 2.0 发布（BV1fc411U7Q3 / BV1Dc411R731）。该键不是新缺陷：它只是把官方英文名当作 anchor，而 3G-F.1-A 之前那个“墨竹ギ::深渊之诗”键（anchor=中文包名）被修复取代。同一包，不是误合并。注意与 `墨竹ギ::quot 以神之名 染梦世间 quot 深渊之诗 异梦终途 traveldreams` 区分：那条是《深渊之诗-异梦终途》，是同一系列下的另一个产品，不应合并。' },
  '在下shmily::最牛优化': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '3 条均为同一 uploader 的《最牛优化整合包》V4.0 / V3.9 / 首发；anchor 就是包名。' },
  '芦苇草的梦想::芦苇的': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '3 条均为该 uploader 同名“芦苇的整合包”系列宣传片（4.2.12 / 4.1.7 / 4.0.11 更新）；anchor 是包名片段。' },
  '墨言eclipse::涅槃': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '5 条均为《涅槃》同一包（v0.1.5 / v0.1.6 / v0.1.8 / v0.2）；anchor 是包名。结构化下载链接 mcmod modpack/1418 + xyebbs resources/37418 一致。这是 3G-F.2-A 的期望终态（旧的 5 个分裂键收敛到此）。' },
  'pork猪排::化龍': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '4 条均为《化龍》同一包（1.0 → 1.3.1）；anchor 是包名。“金鳞岂是池中物，一遇风云便化龙”是固定诗句宣传语。' },
  'terminus_54-32::泰坦': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'medium', note: '3 条均为该 uploader 的“泰坦整合包”系列（1.21.1 / 1.21.4 / 1.12.2，含“看简介/附下载链接”）。MC 主版本跨度较大，但命名与定位高度同构、无其他区分性包名 → 保守判同包，不计数为误合并。' },
  'zicaiot::在 中还原星露谷 农场物语': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '3 条均为《农场物语 / 在我的世界中还原星露谷》同一包（1.4.1 / forge1.2.6 / forge1.2.0）；anchor 是包名全称。与 `zicaiot::农场物语` 是同一包被拆成两键 → 见 under_merge（不是误合并）。' },
  '一个小寂哦::无尽幸运方块大陆 重生': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '3 条均为《无尽幸运方块大陆 重生》同一包（最终版本 / 重生2.0 / 重生发布）；anchor 是包名。与 R5 否决的 `怪物大乱斗` 无关。' },
  '流霜雾影::愚者': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '3 条均为《愚者》同一包（v0.1 / v0.2 / 发布介绍）；anchor 是包名。取代了旧的“愚者版本大”键。' },
  '不知名的莫理沙::星月枪姬与落魄勇者': { verdict: 'LEGITIMATE_SAME_PACK', confidence: 'high', note: '2 条均为《勇者之章Ⅲ》同一包的“星月枪姬与落魄勇者”子版本更新（稳定版本 / 版本更新）；anchor 是子版本名。与 `勇者之章` 系列属同一逻辑包 → 见 under_merge。' },
};;

// ---------------------------------------------------------------------------
// RETIRED CANDIDATE KEYS (Phase 3G-F.2-A).
//
// Keys that were detector CANDIDATES at 3G-F.1-B and are not candidates any more.
// They are NOT false merges - all of them were adjudicated LEGITIMATE_SAME_PACK
// and they disappeared because the 3G-F.2-A runtime fix either merged their
// members into a wider correct group or re-selected the anchor.
//
// Keeping them out of VERDICTS and recording them here is what makes
// `declared_but_absent` self-explaining without erasing the audit trail.
//
//   kind:
//     merged_into_live_group - members now sit under the named live group key
//     anchor_reselected     - members still form a group, but under a new key
// ---------------------------------------------------------------------------
const RETIRED_CANDIDATE_KEYS = {
  '墨言eclipse::沉浸 深度 a 咒镰双生': {
    was: 'LEGITIMATE_SAME_PACK', kind: 'merged_into_live_group',
    now: '墨言eclipse::涅槃',
    note: '两条 涅槃 v0.1.6 / v0.1.5 曾被 tag 词锚住；现已并回以包名为 anchor 的单组。',
  },
  '墨言eclipse::涅槃 无神明渡我 我亦是神明': {
    was: 'LEGITIMATE_SAME_PACK', kind: 'merged_into_live_group',
    now: '墨言eclipse::涅槃',
    note: '涅槃 v0.2 宣传片的旧 anchor 键；现已并回 `涅槃`。',
  },
  '墨言eclipse::涅槃 神吞降世 邪神投影 万魂幡 超越法则的 镰刀 之旅': {
    was: 'LEGITIMATE_SAME_PACK', kind: 'merged_into_live_group',
    now: '墨言eclipse::涅槃',
    note: '同上，旧 anchor 是标题尾部特性串。',
  },
  '墨言eclipse::大型 禁忌 远古炼金 世界污染 3万行代码深度 涅槃v 0 宣传视频': {
    was: 'LEGITIMATE_SAME_PACK', kind: 'merged_into_live_group',
    now: '墨言eclipse::涅槃',
    note: '同上，旧 anchor 是标题模板词 + 版本片段。',
  },
  '一个小寂哦::各大主播同款': {
    was: 'LEGITIMATE_SAME_PACK', kind: 'anchor_reselected',
    now: '一个小寂哦::幸运方块大全 110 个高版本幸运方块 与朋友一起挑战充满幸运的世界 各大主播同款',
    note: 'anchor 从口号式 run 收敛为真实包名 run。',
  },
  '一个小寂哦::四叶草': {
    was: 'LEGITIMATE_SAME_PACK', kind: 'anchor_reselected',
    now: '一个小寂哦::新泰坦生物 矿石菌种 更多泰坦 四叶草 幸运方块',
    note: '“四叶草”是物品名，不再充当 anchor。',
  },
  '一个小寂哦::星辉死神': {
    was: 'LEGITIMATE_SAME_PACK', kind: 'anchor_reselected',
    now: '一个小寂哦::我是星辉死神 变身星辉死神 终极艾德曼合金战神 终极骷髅模组 所有泰坦都能变身 凡宇轩 红烧 泉奈同款',
    note: '“星辉死神”是 Boss 名，不再充当 anchor。',
  },
  '墨言eclipse::颠覆性的': {
    was: 'LEGITIMATE_SAME_PACK', kind: 'anchor_reselected',
    now: '墨言eclipse::摄魂 破刹 定身 颠覆性的 交互体验 摄影奇境宣传片',
    note: '“颠覆性的”是形容词，不再充当 anchor。',
  },
  '原界环::or not': {
    was: 'LEGITIMATE_SAME_PACK', kind: 'anchor_reselected',
    now: '原界环::全新 pve 少女准备中 maiden or not 自locknar的 or not',
    note: '英文功能词 “or not” 不再充当 anchor。',
  },
  '叙利亚自爆民兵::voxy': {
    was: 'LEGITIMATE_SAME_PACK', kind: 'anchor_reselected',
    now: '叙利亚自爆民兵::你好 新世代 voxy 机械动力 瓦尔基里全新兼容',
    note: '通用渲染模组名 “voxy” 不再充当 anchor。',
  },
  'tibsalta::难度驱动': {
    was: 'LEGITIMATE_SAME_PACK', kind: 'anchor_reselected',
    now: 'tibsalta::抗争之际 难度驱动 向',
    note: '方括号系列标签 “难度驱动” 不再充当 anchor。',
  },
  '落烟雨辰呀::诡厄 使徒': {
    was: 'LEGITIMATE_SAME_PACK', kind: 'anchor_reselected',
    now: '__unknown__',
    note: '该上传者记录已不在候选面内（组内两条仍同组，只是不再触发任何 detector 类）。',
  },
  '落烟雨辰呀::诡厄使徒': {
    was: 'LEGITIMATE_SAME_PACK', kind: 'anchor_reselected',
    now: '__unknown__',
    note: '同上。跨组 under-merge 关系仍在 under_merge 层单独记录。',
  },
  '-阳春面面-::青春复兴': {
    was: 'LEGITIMATE_SAME_PACK', kind: 'anchor_reselected',
    now: '-阳春面面-::大重置 格雷青春版 青春复兴',
    note: '“青春复兴”曾被单独锚住；现 anchor 更完整。',
  },
  '一个小寂哦::怪物大乱斗': {
    was: 'REAL_FALSE_MERGE', kind: 'merged_into_live_group',
    now: '一个小寂哦::怪物大乱斗 手机版 经典 变身 哥斯拉 经典',
    fixed_by: 'competing_edition',
    note: '共享前缀 `怪物大乱斗` 现在被 R5 否决：其后紧跟的版本代际标签（手机版 / 重生）互斥且零身份字符，且 `重生` 被同 uploader 的独立组 `怪物大乱斗重生` 独立佐证。手机版那条留在新键，重生那条归入 `怪物大乱斗重生`。',
  },
  '一个小寂哦::怪物大乱斗重生': {
    was: 'LEGITIMATE_SAME_PACK', kind: 'anchor_reselected',
    now: '一个小寂哦::怪物大乱斗重生',
    note: '同一 groupKey 文本，但成员从 3 条变为 4 条 —— R5 把“怪物大乱斗：重生”那条从 `怪物大乱斗` 组救回后并入本组。旧的 3 条候选键因此不再由 detector 触发（size 类与 anchor 类都变了）。',
  },
  '墨竹ギ::深渊之诗': {
    was: 'LEGITIMATE_SAME_PACK', kind: 'anchor_reselected',
    now: '墨竹ギ::poetry of the abyss',
    note: '中文包名 anchor 被官方英文名取代；同一组，只是键变了。',
  },
  '墨竹ギ::史诗的地下城 dungeons of fantasy': {
    was: 'LEGITIMATE_SAME_PACK', kind: 'anchor_reselected',
    now: '__unknown__',
    note: '两条 Dungeons Of Fantasy 记录现各自成组（anchor 落在各自的副标题 run 上）。属 recall 取舍，如实记录。',
  },
  '流霜雾影::愚者版本大': {
    was: 'LEGITIMATE_SAME_PACK', kind: 'merged_into_live_group',
    now: '流霜雾影::愚者',
    note: 'anchor 从“愚者版本大”收敛为干净的“愚者”，3 条合成一组。',
  },
  'arr-c6h6::旧世界': {
    was: 'LEGITIMATE_SAME_PACK', kind: 'anchor_reselected',
    now: 'arr-c6h6::真菌感染加惊变100天 旧世界',
    note: '两条《旧世界》记录现各自成组（anchor 落在各自的功能描述 run 上）。属 recall 取舍，如实记录。',
  },
  '不知名的莫理沙::勇者之章': {
    was: 'LEGITIMATE_SAME_PACK', kind: 'anchor_reselected',
    now: '不知名的莫理沙::星月枪姬与落魄勇者',
    note: 'anchor 从系列名“勇者之章”下沉到各条的子版本名（异界法师 / 星月枪姬与落魄勇者 / 多线性枪魔）。其中“星月枪姬与落魄勇者”2 条仍同组，另 2 条成为独立记录。属 recall 取舍，如实记录。',
  },
  '在职玩家jostar::去吧 方可梦大师': {
    was: 'LEGITIMATE_SAME_PACK', kind: 'anchor_reselected',
    now: '__unknown__',
    note: '4 条方可梦记录现各自成组（anchor 落在各自的前缀 run 上）。属 recall 取舍，如实记录。',
  },
  'plaudite_::scarlet': {
    was: 'LEGITIMATE_SAME_PACK', kind: 'anchor_reselected',
    now: '__unknown__',
    note: '两条 Scarlet Adventure 记录现各自成组。属 recall 取舍，如实记录。',
  },
  'pork猪排::化龍 金鳞岂是池中物 一遇风云便化龙': {
    was: 'LEGITIMATE_SAME_PACK', kind: 'merged_into_live_group',
    now: 'pork猪排::化龍',
    note: 'anchor 从诗句宣传语收敛为包名“化龍”，4 条合成一组。',
  },
  '一个小寂哦::重回 之巅': {
    was: 'LEGITIMATE_SAME_PACK', kind: 'anchor_reselected',
    now: '__unknown__',
    note: '两条“最全拔刀剑”系列记录现各自成组。属 recall 取舍，如实记录。',
  },
  '啊liu22::简单群峦': {
    was: 'LEGITIMATE_SAME_PACK', kind: 'anchor_reselected',
    now: '__unknown__',
    note: '两条《简单群峦》记录现各自成组。属 recall 取舍，如实记录。',
  },
};;

// ---------------------------------------------------------------------------
// RETIRED FALSE MERGES.
//
// Every key here was adjudicated REAL_FALSE_MERGE at some point and is now
// CLOSED by a runtime fix. The detector no longer emits these group keys because
// the offending groups no longer exist, so they cannot be re-confirmed from the
// current grouping output - but silently dropping them would erase the audit
// trail (and make `declared_but_absent` look like drift). So they are declared
// here with the cause that closed them.
//
// `fixed_by` refers to the admissibility rule in
// apps/web/src/domain/bilibiliGrouping.ts.
// ---------------------------------------------------------------------------
const RETIRED_FALSE_MERGES = {
  // ---- closed by Phase 3G-F.1-A (commit 3f81db2) ----
  '一个小寂哦::星辉死神': {
    was: { verdict: 'REAL_FALSE_MERGE', confidence: 'high' },
    fixed_by: 'late_feature_list',
    note: '神器收集计划 / 无尽幸运方块大陆 / 全网最全神器 = 多个不同包；“星辉死神”是 Boss 名，只出现在 `！` 后的特性清单里。R2 否决。',
  },
  '一个小寂哦::四叶草': {
    was: { verdict: 'REAL_FALSE_MERGE', confidence: 'high' },
    fixed_by: 'late_feature_list',
    note: '新泰坦生物整合包 / 执行之龙生存整合包 是两个不同包；“四叶草”是物品名，出现在特性清单。R2 否决。',
  },
  '一个小寂哦::各大主播同款': {
    was: { verdict: 'REAL_FALSE_MERGE', confidence: 'high' },
    fixed_by: 'late_feature_list',
    note: '幸运方块大全 / 超困难神器泰坦随机合成 是两个不同包；“各大主播同款”是口号式 run。R2 否决。',
  },
  '墨言eclipse::颠覆性的': {
    was: { verdict: 'REAL_FALSE_MERGE', confidence: 'high' },
    fixed_by: 'late_feature_list',
    note: '摄影奇境 / 千界万锻 是两个不同包；“颠覆性的”是形容词。R2 否决。',
  },
  '原界环::or not': {
    was: { verdict: 'REAL_FALSE_MERGE', confidence: 'high' },
    fixed_by: 'english_function_words',
    note: 'Minecraft or Not: Girl&Gun / Maiden or not 是两个不同包；“or not”是纯 ASCII 连接词碎片。R3 否决。',
  },
  '叙利亚自爆民兵::voxy': {
    was: { verdict: 'REAL_FALSE_MERGE', confidence: 'high' },
    fixed_by: 'name_slot_disagreement',
    note: '《你好，新蒸程》与《你好，新世代》是两个独立命名的包，唯一共同点是都用了 voxy 渲染模组。voxy 是通用模组名（组件锚），不构成包标识。R1 依据两侧名称槽不一致否决——通用化处理，未 hardcode `voxy`。',
  },
  'tibsalta::难度驱动': {
    was: { verdict: 'REAL_FALSE_MERGE', confidence: 'high' },
    fixed_by: 'name_slot_disagreement',
    note: '《抗争之际0.6》与《旅途痕迹0.5》是两个不同包；包名在方括号外，【难度驱动】只是系列标签。R1 依据两侧名称槽（抗争之际 / 旅途痕迹）不一致否决——通用化处理，未 hardcode `难度驱动`。',
  },

  // ---- closed by Phase 3G-F.2-A (this change) ----
  '一个小寂哦::怪物大乱斗': {
    was: { verdict: 'REAL_FALSE_MERGE', confidence: 'medium' },
    fixed_by: 'competing_edition',
    note: '「怪物大乱斗 手机版」与「怪物大乱斗：重生」是两次独立发布。两条共享 anchor `怪物大乱斗`，但其后紧跟的 token 不同（手机版 / 重生），且两者都是零身份字符的**版本代际标签**；`重生` 更被同 uploader 的独立三成员组 `怪物大乱斗重生` 独立佐证为真实包名。R5 否决共享前缀，重生那条现归入 `怪物大乱斗重生`。',
  },
};

// ---------------------------------------------------------------------------
// UNDER-MERGE adjudication (cross-group findings).
// Key = author + '||' + sorted group_keys joined by '|'.
// Only clusters whose verdict matters to the report are listed; every cluster
// still gets an entry so nothing is silently undeclared.
// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// RETIRED UNDER-MERGE CLUSTERS (Phase 3G-F.2-A).
//
// Clusters the cross-group scanner produced at 3G-F.1-B that it no longer
// produces. Two reasons, kept distinct because they mean opposite things:
//
//   cluster_gone        - the constituent groups no longer both exist (anchor
//                         convergence merged them, or the anchor moved), so the
//                         scanner cannot form the pair any more. The verdict is
//                         RESOLVED, not withdrawn.
//   superseded          - a sibling entry already covers the SAME live cluster;
//                         this row is the pre-fix duplicate. Kept so the count
//                         of reviewed clusters cannot silently shrink.
//
// Keeping them here is what makes `declared_but_absent` a documented list.
// ---------------------------------------------------------------------------
const RETIRED_UNDERMERGE_CLUSTERS = {
  '墨言eclipse||墨言eclipse::大型 禁忌 远古炼金 世界污染 3万行代码深度 涅槃v 0 宣传视频|墨言eclipse::沉浸 深度 a 咒镰双生|墨言eclipse::涅槃 无神明渡我 我亦是神明|墨言eclipse::涅槃 神吞降世 邪神投影 万魂幡 超越法则的 镰刀 之旅': {
    kind: 'cluster_gone', was_verdict: 'UNDER_MERGE',
    note: '确认：7 条 涅槃 记录（v0.1.5 → v0.2）属同一上传者墨言eclipse 的同一逻辑包，算法拆成 5 个 group key。此簇覆盖其中 4 个 key（第 5 个 未尽之路涅槃 被“未尽之路”桥接到另一簇）。',
  },
  '一个小寂哦||__NOOP': {
    kind: 'placeholder', was_verdict: null,
    note: 'placeholder-never-used',
  },
  // ---- 3G-F.2-A: coarse-PAIR keys from the 3G-F.1-B snapshot whose two member
  // keys are now SUBSUMED by a larger live cluster that this ledger already
  // adjudicates as a whole. These are `superseded`, not `cluster_gone`: the
  // relationship they described (A and B are over-connected by a shared token)
  // is real and still present, but the scanner now emits the FULL cluster, so a
  // 2-key row is no longer what it produces.
  //
  // Adjudicating them in ADDITION to the superset would be a ledger error: a
  // pair row is silent about the other 19 (resp. 7) members, so a pair-level
  // UNDER_MERGE verdict would read as "these two belong together" while the
  // superset row says "do NOT merge this whole cluster". Keeping both invites
  // the exact contradiction this table exists to prevent. The pair's semantics
  // are preserved in the `note` of the superseding row.
  '一个小寂哦||一个小寂哦::新泰坦生物 矿石菌种 更多泰坦 四叶草 幸运方块|一个小寂哦::新泰坦生物 神器小木剑 联机教程 更多泰坦 新增懒人模组 砧板 无尽贪婪': {
    kind: 'superseded', was_verdict: 'UNDER_MERGE',
    now: '一个小寂哦||一个小寂哦::全网 最全神器 星辉死神 凋零斯拉 执行之龙 泰坦 在 体验 时代的魅力|…|一个小寂哦::高版本神器随机合成 幸运与实力的考验 重温一遍经典娱乐模组',
    note: '该 2 键对已被 21 成员 live 簇（adjudicated NOT_UNDER_MERGE，通用词过度连通的巨簇）取代。原对级判定是 UNDER_MERGE（新泰坦生物 系列同包）；后者是更强的断言，先说于本表。',
  },
  '一个小寂哦||一个小寂哦::怪物大乱斗 手机版 经典 变身 哥斯拉 经典|一个小寂哦::怪物大乱斗重生': {
    kind: 'superseded', was_verdict: 'NOT_UNDER_MERGE',
    now: '一个小寂哦||一个小寂哦::全网 最全神器 星辉死神 凋零斯拉 执行之龙 泰坦 在 体验 时代的魅力|…|一个小寂哦::高版本神器随机合成 幸运与实力的考验 重温一遍经典娱乐模组',
    note: '该 2 键对已被 21 成员 live 簇取代。对级判定 NOT_UNDER_MERGE 与取代簇一致：`怪物大乱斗 手机版` 与 `怪物大乱斗重生` 是两个不同的包（见 RETIRED_FALSE_MERGES 的 R5 条目），不构成同包证据。',
  },
  '墨竹ギ||墨竹ギ::poetry of the abyss|墨竹ギ::quot 以神之名 染梦世间 quot 深渊之诗 异梦终途 traveldreams': {
    kind: 'superseded', was_verdict: 'NOT_UNDER_MERGE',
    now: '墨竹ギ||墨竹ギ::poetry of the abyss|…|墨竹ギ::终末之途 旅者之颂 踏上找寻世界 尽头旅程 终末旅颂 end travel ode',
    note: '该 2 键对已被 9 成员 live 簇（adjudicated NOT_UNDER_MERGE）取代。对级判定一致：《深渊之诗 / Poetry of the Abyss》与《深渊之诗-异梦终途 / TravelDreams》是两个不同产品，共享 `深渊之诗` 前缀不构成同包证据。',
  },
  '落烟雨辰呀||落烟雨辰呀::诡厄 使徒|落烟雨辰呀::诡厄使徒': {
    kind: 'cluster_gone', was_verdict: 'UNDER_MERGE',
    note: '确认：两组均为《诡厄使徒》同一包（1.0.6/1.0.7 与 1.1.0），差别仅在中英文冒号与空格 → 典型跨组拆分。',
  },
  '在职玩家JoStar||在职玩家jostar::去吧 方可梦大师|在职玩家jostar::方可梦': {
    kind: 'cluster_gone', was_verdict: 'UNDER_MERGE',
    note: '确认：「方可梦」与「去吧，方可梦大师」是同一包（候选层已判后者为同包）→ 被拆成两组。',
  },
  '在下Shmily||在下shmily::优化 最牛优化 cmpack即将来临|在下shmily::优化 老手机2000 fps 最牛优化|在下shmily::优化 老手机2800帧 最牛优化': {
    kind: 'cluster_gone', was_verdict: 'UNDER_MERGE',
    note: '确认：3 组均为该 uploader 的“最牛优化”性能包（老手机2000/2800帧为其宣传语）→ 被拆散。',
  },
  '芦苇草的梦想||芦苇草的梦想::芦苇 寒假来休闲一下 芦苇的 宣传片|芦苇草的梦想::芦苇的 宣传片4|芦苇草的梦想::芦苇的 版本 宣传片': {
    kind: 'cluster_gone', was_verdict: 'UNDER_MERGE',
    note: '确认（低风险）：3 组均为该 uploader 同名“芦苇的整合包”系列宣传片，编号 4 为其一 → 被拆散。',
  },
  '流霜雾影||流霜雾影::愚者 愚弄 伪装 欺诈 屠龙者终成恶龙 扮演所有的生物 使用它们的能力编织一场完美的欺诈盛宴|流霜雾影::愚者版本大': {
    kind: 'cluster_gone', was_verdict: 'UNDER_MERGE',
    note: '确认：两组均为《愚者》同一包（候选层已判后者为同包）→ 被拆成两组。',
  },
  '墨言eclipse||墨言eclipse::未尽之路涅槃|墨言eclipse::涅槃': {
    kind: 'superseded', was_verdict: 'UNDER_MERGE',
    note: '确认：RUNTIME 上 涅槃 家族现在恰好 2 组 —— `涅槃`（5 条，正确）与 `未尽之路涅槃`（2 条，正确）。这两组是**两个不同的包**（结构化下载链接互异 + 上传者明确说明无关），所以它们**不应合并**；但正是 pre-3G-F.2-A 的 7 条记录被拆成 5 组这件事，构成了 3G-F-A 的 under-merge 发现 BILI-GRP-UNDERMERGE-01。本条目记录的是「该发现已被解析」：5 个旧键已收敛为 2 个正确组，per-key rescue 见 PER_KEY_UNDER_MERGE。',
  },
  'Terminus_54-32||terminus_54-32::泰坦|terminus_54-32::泰坦生物 小|terminus_54-32::新泰坦生物 new titan creatures mod pack released': {
    kind: 'superseded', was_verdict: 'UNDER_MERGE',
    note: '确认（低风险）：三组均为该 uploader 的“泰坦 / 泰坦生物”系列，标题同构、无区分性包名 → 同一包被拆散。',
  },
  '墨言eclipse||墨言eclipse::命轮无章 infinite random|墨言eclipse::摄魂 破刹 定身 颠覆性的 交互体验 摄影奇境宣传片|墨言eclipse::大型 模块化 颠覆性的 革新 究极 爽的杀敌体验 辅助的锻刀之旅 千界万锻 宣传片|墨言eclipse::高版本沉浸 lt 未尽之诗 gt 官方宣传片 一首写给高版本 的远征诗': {
    kind: 'superseded', was_verdict: 'NOT_UNDER_MERGE',
    note: '否决：命轮无章 / 摄影奇境 / 千界万锻 / 未尽之诗 是四个不同包。簇由“颠覆性的”这一形容词连通——R2 已经否决它作为 anchor；把它当作跨组同包证据会立刻制造两个新的误合并。',
  },
  '在下Shmily||在下shmily::最牛优化': {
    kind: 'cluster_gone', was_verdict: 'UNDER_MERGE',
    note: '确认：`最牛优化` 组（3 条）已是同一包；本簇原由三个旧键组成，现全部收敛为这一个键 → 已解析，不再有跨组拆分（本条目保留以记录解析结果）。',
  },
  '芦苇草的梦想||芦苇草的梦想::芦苇的': {
    kind: 'cluster_gone', was_verdict: 'UNDER_MERGE',
    note: '确认（低风险）：`芦苇的` 组（3 条）已是同一包；三个旧键已收敛为这一个键 → 已解析。',
  },
  '流霜雾影||流霜雾影::愚者': {
    kind: 'cluster_gone', was_verdict: 'NOT_UNDER_MERGE',
    note: '否决：`愚者` 组（3 条）已是同一包的单组 → 没有跨组拆分需要修复（本条目保留以记录解析结果）。',
  },
};;

const UNDERMERGE_VERDICTS = {
  '墨言eclipse||墨言eclipse::拒绝同质|墨言eclipse::未尽之路涅槃': {
    verdict: 'PARTIAL_UNDER_MERGE', confidence: 'high',
    note: '部分确认：该簇是一个**混合簇**。「未尽之路涅槃」属于涅槃包（第 5 个被拆出的 key，应并入涅槃 under-merge）；「拒绝同质」属于『未尽之路/Unfinished Path』另一包，**不应**并入。簇级判定必须拆开——把它整体判 UNDER_MERGE 会制造新的误合并，整体判 NOT 又会漏掉涅槃的第 5 个 key。',
    restored_from: 'RETIRED_UNDERMERGE_CLUSTERS (mis-keyed by the automated re-key)',
  },
  '一个小寂哦||一个小寂哦::全网 最全神器 星辉死神 凋零斯拉 执行之龙 泰坦 在 体验 时代的魅力|一个小寂哦::幸运方块大全 110 个高版本幸运方块 与朋友一起挑战充满幸运的世界 各大主播同款|一个小寂哦::弑神之路|一个小寂哦::怪物大乱斗 手机版 经典 变身 哥斯拉 经典|一个小寂哦::怪物大乱斗重生|一个小寂哦::我是星辉死神 变身星辉死神 终极艾德曼合金战神 终极骷髅模组 所有泰坦都能变身 凡宇轩 红烧 泉奈同款|一个小寂哦::执行之龙 叶枫同款 强化工具 四叶草 超多经典模组 休闲娱乐包|一个小寂哦::新泰坦生物 矿石菌种 更多泰坦 四叶草 幸运方块|一个小寂哦::新泰坦生物 神器小木剑 联机教程 更多泰坦 新增懒人模组 砧板 无尽贪婪|一个小寂哦::无尽幸运方块大陆 重生|一个小寂哦::暑假幸运方块赛道 手机可玩 低配 4个区域 6条赛道 45种不同幸运方块 童年未能达成的愿望 这次来实现|一个小寂哦::最全 血腥革新 复活 上百种不同 重回 之巅|一个小寂哦::最全 重逢 重回 之巅 全网最全的 万物终结 异次元管理者 极夜之刃 龙族 以及各种|一个小寂哦::泰坦 新的武器 无限之锤 基岩弩 炎黄弩 虚无弓|一个小寂哦::浪客 重生 小本同款 女仆 豆腐世界 小型新手向 多任务 怀旧|一个小寂哦::神器收集计划 版本 最全神器 炫猫 星辉死神 斗蛐蛐专用|一个小寂哦::超bt绿宝石大陆 怪物大乱斗版 记忆中的一切 怀旧 多人 爽包 详细任务 在充满绿宝石的大陆上挑战曾经的boss|一个小寂哦::超困难神器泰坦随机合成 各大主播同款 在 玩神器泰坦随机合成|一个小寂哦::追影之旅|一个小寂哦::随机方块泰坦 每隔一段时间身边的方块就会刷新 你能否击败星辉死神|一个小寂哦::高版本神器随机合成 幸运与实力的考验 重温一遍经典娱乐模组': {
    verdict: 'NOT_UNDER_MERGE', confidence: 'high',
    note: '否决：这是 16 个组被 泰坦/星辉死神/幸运方块 等通用词过度连通的巨簇。该 uploader 确实存在多个不同包（神器收集计划/无尽幸运方块大陆/怪物大乱斗重生/弑神之路…），把它们合并会制造新的误合并。',
    rekeyed_from: '一个小寂哦||一个小寂哦::各大主播同款|一个小寂哦::四叶草|一个小寂哦::弑神之路|一个小寂哦::怪物大乱斗|一个小寂哦::怪物大乱斗重生|一个小寂哦::我是星辉死神 变身星辉死神 终极艾德曼合金战神 终极骷髅模组 所有泰坦都能变身 凡宇轩 红烧 泉奈同款|一个小寂哦::无尽幸运方块大陆 重生|一个小寂哦::星辉死神|一个小寂哦::暑假幸运方块赛道 手机可玩 低配 4个区域 6条赛道 45种不同幸运方块 童年未能达成的愿望 这次来实现|一个小寂哦::更多泰坦|一个小寂哦::泰坦 新的武器 无限之锤 基岩弩 炎黄弩 虚无弓|一个小寂哦::泰坦生物|一个小寂哦::浪客 重生 小本同款 女仆 豆腐世界 小型新手向 多任务 怀旧|一个小寂哦::超bt绿宝石大陆 怪物大乱斗版 记忆中的一切 怀旧 多人 爽包 详细任务 在充满绿宝石的大陆上挑战曾经的boss|一个小寂哦::追影之旅|一个小寂哦::随机方块泰坦 每隔一段时间身边的方块就会刷新 你能否击败星辉死神|一个小寂哦::高版本神器随机合成 幸运与实力的考验 重温一遍经典娱乐模组',
  },
  '时唅||时唅::大型 末世 潜行者|时唅::大型末世 潜行者风暴 免费 开发中|时唅::大型末世 辐射 生还者|时唅::潜行者 免费|时唅::辐射新世纪|时唅::辐射次时代|时唅::辐射生还者 末世 免费': {
    verdict: 'NOT_UNDER_MERGE', confidence: 'high',
    note: '否决：该 uploader 有多个独立包——辐射新世纪 / 辐射次时代 / 生还者 / 潜行者（潜行者与生还者是两个不同包）。簇由“末世/潜行者/辐射”等主题词连通，合并会制造误合并。',
  },
  '豆腐ki||豆腐ki::中低配 手机移植版 atm10 fcl启动器移植 一键自动安装|豆腐ki::中低配 手机移植版 atm3 fcl启动器移植 一键自动安装|豆腐ki::中低配 手机移植版 殖民战争 fcl启动器移植 一键自动安装|豆腐ki::中低配 蔚蓝档案 手机移植版 amp 蔚蓝档案 fcl启动器移植 一键自动导入|豆腐ki::中配 手机移植版 大轩 fcl启动器移植 一键自动安装|豆腐ki::中配 手机移植版 寻谧 精简 fcl启动器移植 一键自动安装|豆腐ki::中配 手机移植版 异界旅者 5 版 fcl启动器移植 一键自动安装|豆腐ki::中配 手机移植版 机械殖民地 fcl启动器移植 一键自动安装|豆腐ki::中配 手机移植版 沉浸 v fcl启动器移植 一键自动安装|豆腐ki::中配休闲 手机移植版 自然之旅3 fcl启动器移植 一键自动安装|豆腐ki::中配群峦 手机移植版 群峦重生 fcl启动器移植 一键自动安装o|豆腐ki::中高配 手机移植版 异界 幻想 fcl启动器移植 一键自动安装|豆腐ki::低配 天空奥德赛手机移植版 试玩加 fcl启动器 一键自动安装|豆腐ki::低配 手机移植版 ftb魔眼传说 fcl启动器移植 一键自动安装|豆腐ki::低配 手机移植版 原环之理v fcl启动器移植 一键自动安装|豆腐ki::低配 末日 手机移植版 终末旅行家 fcl启动器移植 一键自动安装|豆腐ki::低配奥特曼 手机移植版 特摄世界 fcl启动器移植 一键自动导入|豆腐ki::低配手机移植版 高版本惊变100天手机移植版 fcl启动器 一键自动安装|豆腐ki::低配生活大 手机移植版 高版本生活大 fcl启动器移植 一键自动导入|豆腐ki::手机移植版 createdelight fcl启动器移植 一键自动安装|豆腐ki::手机移植版 模块化 v fcl启动器移植 一键自动导入|豆腐ki::末日丧尸 末世废土二手机移植 fcl启动器移植 一键自动导入|豆腐ki::超低配 无限打金 手机移植版 fcl启动器|豆腐ki::超低配最逆天 手机移植版 天空厕所 人人都是老八自给自足|豆腐ki::超级低配的 手机移植版 无中生无尽 fcl启动器移植 一键自动导入': {
    verdict: 'NOT_UNDER_MERGE', confidence: 'high',
    note: '否决：该 uploader 是手机移植搬运号，25 个组对应 25 个**不同**的第三方包（ATM10/ATM3/殖民战争/机械殖民地/群峦重生…）。簇由“手机移植版/fcl启动器/一键自动安装”等模板词连通，合并是完全错误的。',
  },
  '墨竹ギ||墨竹ギ::poetry of the abyss|墨竹ギ::quot 以神之名 染梦世间 quot 深渊之诗 异梦终途 traveldreams|墨竹ギ::quot 在失落的异界中 一个人生活下去 quot 生活 thelostworld 失落的异界|墨竹ギ::一款大型 生活向 将 quot 地下城 quot quot 死亡细胞 quot 游戏内容移植到 之中 史诗的地下城 dungeons of fantasy|墨竹ギ::一款大型 生活向 将 quot 地下城 quot quot 死亡细胞 quot 移植到 当中 史诗的地下城 dungeons of fantasy|墨竹ギ::农业 低配 将 地下城 注入到 当中 史诗的地下城|墨竹ギ::史诗的地下城 一个 风 低配 极致优化 将 地下城 内容注入的高版本 啦|墨竹ギ::幻想的地下城 一个幻想风 风 低配 将 地下城 内容注入 的 啦|墨竹ギ::终末之途 旅者之颂 踏上找寻世界 尽头旅程 终末旅颂 end travel ode': {
    verdict: 'NOT_UNDER_MERGE', confidence: 'high',
    note: '否决：该 uploader 有 失落的异界 / 史诗的地下城 / 幻想的地下城 / 深渊之诗 等多个独立包。簇由“地下城/内容注入/低配”连通；“深渊之诗”与“史诗的地下城”虽同 uploader 但是不同包（前者是 Poetry of the Abyss，后者是 Dungeons Of Fantasy）。',
    rekeyed_from: '墨竹ギ||墨竹ギ::quot 在失落的异界中 一个人生活下去 quot 生活 thelostworld 失落的异界|墨竹ギ::农业 低配 将 地下城 注入到 当中 史诗的地下城|墨竹ギ::史诗的地下城 dungeons of fantasy|墨竹ギ::史诗的地下城 一个 风 低配 极致优化 将 地下城 内容注入的高版本 啦|墨竹ギ::幻想的地下城 一个幻想风 风 低配 将 地下城 内容注入 的 啦|墨竹ギ::深渊之诗',
  },
  '我的世界peaunt||__raw_BV1EhYN6AEWo|__raw_BV1QTYr6sEXA|我的世界peaunt::泰坦生物 仿照|我的世界peaunt::泰坦生物复刻': {
    verdict: 'UNDER_MERGE', confidence: 'medium',
    note: '确认（低风险）：4 条均为该 uploader 的“泰坦生物 仿照/复刻”系列，标题高度同构、无区分性包名，判为同一包的多次发布。属于跨组拆分候选，但收益小。',
  },
  '明月庄主||__raw_BV1vT411A71k|明月庄主::红石生电|明月庄主::红石生电优化|明月庄主::绿色版红石生电优化': {
    verdict: 'UNDER_MERGE', confidence: 'medium',
    note: '确认：该 uploader 的“红石生电/红石生电优化/绿色版红石生电优化”整体是一个红石生电系列包（外加一条未成组记录）。三条被拆开，属跨组拆分。',
  },
  'Puikre||puikre::一场紧张又刺激的alex洞穴之旅 美食 挑战 向的轻量化|puikre::一段追求极致的 属于锻造师的历练史诗 炼狱锻魂 成为锻造大师吧|puikre::一段铸造奇迹的 史诗 锻造 boss挑战 生活 定制模组 那就成为锻造大师吧|puikre::奇妙的洞穴 之旅 休闲 美食 定制的交易系统 更多趣味联动 alexcraft 重置大|puikre::定制模组 成为锻造大师|puikre::锻造大师 全面重置的神器锻造和特性效果 重新谱写这份独属于锻造大师们的 乐章': {
    verdict: 'NOT_UNDER_MERGE', confidence: 'medium',
    note: '否决：该 uploader 至少有两个不同包——「成为锻造大师」（4 组）与「Alex 洞穴/休闲美食」系列（2 组）。簇由“锻造/美食/定制模组/史诗”连通；“成为锻造大师”子集内部可以考虑合并，但整体簇不是同一个包。',
  },
  '明月庄主||明月庄主::命运齿轮|明月庄主::月亮工厂|明月庄主::月亮工厂 f|明月庄主::机械动力航空动力学服务端 对应客户端是命运齿轮航空动力学 pcl2启动器': {
    verdict: 'NOT_UNDER_MERGE', confidence: 'medium',
    note: '否决：命运齿轮 与 月亮工厂 是两个不同包（分别已判 LEGITIMATE）。簇由“机械动力/PCL2/启动器”等通用词连通。',
  },
  '小兜兜呀_||小兜兜呀_::原神与机械 的时代|小兜兜呀_::的时代': {
    verdict: 'UNDER_MERGE', confidence: 'high',
    note: '确认：第二条是同UP主给自己的《原神与机械的时代》数据的“里程碑公告”视频，与主包是同一逻辑包却被拆成独立组 → 典型跨组拆分。',
    rekeyed_from: '小兜兜呀_||小兜兜呀_::原神与机械 的时代|小兜兜呀_::小兜兜 恭喜我的原神与机械 的时代 在bbs 资源站 量破6666次和在红石中继站浏览量达到400人 次 以及 相关 计划',
  },
  'Terminus_54-32||terminus_54-32::新泰坦生物 new titan creatures mod pack released|terminus_54-32::泰坦|terminus_54-32::泰坦生物 小': {
    verdict: 'UNDER_MERGE', confidence: 'medium',
    note: '确认（低风险）：三组均为该 uploader 的“泰坦 / 泰坦生物 / 新泰坦生物”系列，标题同构、无区分性包名 → 同一包被拆散。',
  },
  'P1nero||p1nero::平底锅侠 白天模拟经营 夜晚化身正义 高度 的轻量 支持多人|p1nero::方可梦 炽白真形 高度 沉浸 兼容超远视距模组|p1nero::远梦之棺': {
    verdict: 'NOT_UNDER_MERGE', confidence: 'high',
    note: '否决：平底锅侠 / 方可梦·炽白真形 / 远梦之棺 是三个明确不同的包。簇仅由“高度/沉浸”等通用词连通。',
  },
  '科里森Corrison||科里森corrison::apotheosis conquest|科里森corrison::神之征伐 版本': {
    verdict: 'UNDER_MERGE', confidence: 'high',
    note: '确认：apotheosis conquest 与 神之征伐 是同一包的中英文名（候选层已把“神之征伐 版本”判为同一包的版本系列）；被拆成两组 → 跨组拆分。',
  },
  'VM汉化组||vm汉化组::下一个大型 就在这 集成 integrated 宣传片 amp 汉化|vm汉化组::内容超多的 了 卓越 ii 版本 汉化 amp 官方汉化安装教程|vm汉化组::城作者的又一 破碎城 amp 官方汉化|vm汉化组::等价交换为核心的 等价交换工程2 amp 汉化 amp 服务端安装|vm汉化组::适合暑假联机爽玩的 高版本 卓越ii 汉化': {
    verdict: 'NOT_UNDER_MERGE', confidence: 'high',
    note: '否决：这是汉化组的搬运号，各组合对应不同第三方包（Integrated / 卓约II / 破碎城 / 等价交换工程2）。簇由“汉化/amp/官方汉化”连通。',
  },
  'Pork猪排||pork猪排::化龍|pork猪排::化龙 版本 龙可是帝王之征': {
    verdict: 'UNDER_MERGE', confidence: 'high',
    note: '确认：两组均为《化龍》同一包（含繁体「化龍」与简体「化龙」两种写法，归一化后同根）→ 被拆散。',
    restored_from: 'RETIRED_UNDERMERGE_CLUSTERS (mis-keyed by the automated re-key)',
  },
  '吴也mc||吴也mc::中世纪 内容及汉化 medieval 版|吴也mc::内容 better 版|吴也mc::新版直接变76个模组 dark amp 汉化|吴也mc::汉化 宝藏猎人 vault hunters': {
    verdict: 'NOT_UNDER_MERGE', confidence: 'high',
    note: '否决：该 uploader 为汉化搬运号，对应 Medieval / Better Minecraft / Dark / Vault Hunters 等不同包。簇由“汉化/内容”连通。',
  },
  '墨言eclipse||墨言eclipse::命轮无章 infinite random|墨言eclipse::大型 模块化 颠覆性的 革新 究极 爽的杀敌体验 辅助的锻刀之旅 千界万锻 宣传片|墨言eclipse::摄魂 破刹 定身 颠覆性的 交互体验 摄影奇境宣传片|墨言eclipse::高版本沉浸 lt 未尽之诗 gt 官方宣传片 一首写给高版本 的远征诗': {
    verdict: 'NOT_UNDER_MERGE', confidence: 'high',
    note: '否决：命轮无章 / 千界万锻 / 摄影奇境 / 未尽之诗 是四个不同包。簇由形容词“颠覆性的”连通——R2 已否决它作为 anchor。把它当作跨组同包证据会立刻制造两个新的误合并。注意该键在 3G-F.2-A 已按新 anchor 拆成两键，恰好证明“颠覆性的”是标签而不是包名。',
  },
  '炒雪吵狐力o||炒雪吵狐力o::rapid|炒雪吵狐力o::你电脑玩 很卡 极致优化 帧数提升超过10倍|炒雪吵狐力o::极致优化 fabirc双端支持 帧数暴涨 低配玩家福星 rapidoptimization优化': {
    verdict: 'UNDER_MERGE', confidence: 'high',
    note: '确认：3 组均是该 uploader 的 RapidOptimization 同一优化包（候选层已判 rapid 组为同包）→ 被拆成 3 组，属跨组拆分。',
  },
  '爱吃土豆的界王||爱吃土豆的界王::侏罗纪公园 与|爱吃土豆的界王::时光牧场': {
    verdict: 'NOT_UNDER_MERGE', confidence: 'high',
    note: '否决：「时光牧场」的设定就是以侏罗纪公园为主题，但两者是**不同名**的包（时光牧场 ≠ 侏罗纪公园）。除非有更强证据，不应合并。',
  },
  '冰冻酸奶盒||冰冻酸奶盒::voxy 真实物理|冰冻酸奶盒::宝可梦地平线': {
    verdict: 'NOT_UNDER_MERGE', confidence: 'high',
    note: '否决：两组由 voxy/宝可梦 等通用模组名连通，实为不同包。',
  },
  '吴也mc||吴也mc::体验悠然人生 以种植等收获来推动经济发展的休闲|吴也mc::开启 的脚步 悠然人生3 世界|吴也mc::悠然人生海岛时光': {
    verdict: 'UNDER_MERGE', confidence: 'high',
    note: '确认：3 组均为《悠然人生》同一系列（悠然人生3/海岛时光为其子版本）→ 被拆散。',
  },
  'Karashok_Leo||__raw_BV1iDdLYJESg|karashok_leo::咒次元': {
    verdict: 'UNDER_MERGE', confidence: 'high',
    note: '确认：未成组的单条记录与「咒次元」组属同一包（候选层已判该组为同包）→ 跨组/未归组拆分。',
  },
  '爱吃土豆的界王||爱吃土豆的界王::jojo 与 含手机版|爱吃土豆的界王::原初修真 与 含手机版x|爱吃土豆的界王::版原初修真 与 含手机版': {
    verdict: 'NOT_UNDER_MERGE', confidence: 'medium',
    note: '否决：JOJO 与原初修真 是两个不同包。簇由“含手机版/与”模板词连通。原初修真 的两组彼此可合并，但整个簇不是同一包。',
  },
  'Drunk耀爵||__raw_BV1b2h36bEvA|drunk耀爵::deepseek鲸鱼娘 测试|drunk耀爵::晴小姐 测试': {
    verdict: 'NOT_UNDER_MERGE', confidence: 'medium',
    note: '否决：“deepseek鲸鱼娘”与“晴小姐”是两个不同包。簇由“测试”这一弱词连通。',
  },
  'WZW_王宗王||wzw_王宗王::fcl zl启动器 勇者之章3 手机移植版|wzw_王宗王::fcl 低配宝可梦 手机版 安装教程|wzw_王宗王::fcl启动器 农场物语 v 手机移植版': {
    verdict: 'NOT_UNDER_MERGE', confidence: 'high',
    note: '否决：手机移植搬运号，三个组对应三个不同第三方包（勇者之章3 / 宝可梦 / 农场物语）。',
  },
  '小水滴的源头||小水滴的源头::在 里使用学生们的力量 x蔚蓝档案 新版 篇|小水滴的源头::当你在 中拥有了学生们的能力 蔚蓝档案主题|小水滴的源头::当你在 里拥有了学生们的能力 npcai系统 跨时代篇': {
    verdict: 'UNDER_MERGE', confidence: 'medium',
    note: '确认：3 组均为该 uploader 的「蔚蓝档案主题包」系列（npcai 系统/跨时代篇 是子版本）→ 被拆散。',
  },
  '马赵龙zhao_long||马赵龙zhao_long::fcl手机启动器 宝可梦 正式|马赵龙zhao_long::宝可梦 重铸 内置幸运方块赛道及内容|马赵龙zhao_long::宝可梦重铸': {
    verdict: 'UNDER_MERGE', confidence: 'high',
    note: '确认：3 组均为《宝可梦重铸》同一包（含 FCL 手机启动器版本）→ 被拆散。',
  },
  '爱吃土豆的界王||爱吃土豆的界王::山海大陆 与 斗罗大陆与山海经为背景|爱吃土豆的界王::山海大陆斗罗大陆 与': {
    verdict: 'UNDER_MERGE', confidence: 'high',
    note: '确认：两组均为《山海大陆X斗罗大陆》同一包（候选层已判后者为同包）→ 被拆成两组。',
  },
  '啊liu22||啊liu22::更真实的 亲历人类 进化史 群峦传说 野望|啊liu22::竟然是 版群峦的 简单群峦|啊liu22::简单群峦 简单易上手的群峦传说': {
    verdict: 'NOT_UNDER_MERGE', confidence: 'high',
    note: '否决：「群峦野望」与「简单群峦」是两个不同包（都是群峦主题，但命名与定位不同）。后两组彼此可合并（同一包被拆成两组），但整个簇不是同一个包。',
    restored_from: 'RETIRED_UNDERMERGE_CLUSTERS (mis-keyed by the automated re-key)',
  },
  'ZangHeRo||zanghero::机械殖民地|zanghero::模拟殖民地': {
    verdict: 'UNDER_MERGE', confidence: 'high',
    note: '确认：《机械殖民地》与《模拟殖民地》是同包的两种叫法/两个版本的命名（候选层已判“机械殖民地”组为同包）→ 被拆成两组。',
  },
  '-阳春面面-||-阳春面面-::大 蔚蓝档案 版本|-阳春面面-::大重置 格雷青春版 青春复兴|-阳春面面-::蔚蓝档案超大型 青春复兴 早期版本先行': {
    verdict: 'AMBIGUOUS', confidence: 'high',
    note: '无法判定：「格雷青春版：青春复兴」与「蔚蓝档案超大型：青春复兴」是否同一包的两次改版，标题不足；且该 uploader 同时有独立的「蔚蓝档案版本」包。不计数，如实记录。',
    restored_from: 'RETIRED_UNDERMERGE_CLUSTERS (mis-keyed by the automated re-key)',
  },
  '鹿清玖LQJ||__raw_BV1AoULBgEoH|__raw_BV1aRYC6cE4p': {
    verdict: 'UNREVIEWED_BY_DESIGN', confidence: 'low',
    note: '仅两条未归组记录，token 证据只剩“溯渊”。标题信息不足，无法判定；不计入 under-merge 计数。',
  },
  '爱吃土豆的界王||爱吃土豆的界王::考古与化石 侏罗纪 与|爱吃土豆的界王::考古与化石x侏罗纪 与': {
    verdict: 'UNDER_MERGE', confidence: 'high',
    note: '确认：两组标题几乎逐字相同（仅 X/空格 差异），同一包被拆成两组。',
  },
  '爱玩游戏的烛梦||爱玩游戏的烛梦::基岩版 仿亡者世界|爱玩游戏的烛梦::基岩版仿亡者世界 v': {
    verdict: 'UNDER_MERGE', confidence: 'high',
    note: '确认：两组标题几乎逐字相同（仅尾部版本号差异），同一包被拆成两组。',
  },
  'XyeBBS中文论坛||xyebbs中文论坛::方可梦 炽白真形 宣传片 真正的|xyebbs中文论坛::虚饰作品v 宣传片 四种职业 四种弹幕 百种饰品': {
    verdict: 'NOT_UNDER_MERGE', confidence: 'high',
    note: '否决：论坛搬运号，两组为不同包（方可梦·炽白真形 / 虚饰作品）。簇由“宣传片”这一通用词连通——正是本 scanner 需要防范的噪声。',
  },
  '星遥工坊||星遥工坊::刀剑异闻录 我有一剑 可斩终末 amp 拔刀 定制 任务引导 深度优化|星遥工坊::刀剑异闻录周年 附属万行 全新拔刀全新挑战 流程 性能全面优化': {
    verdict: 'UNDER_MERGE', confidence: 'high',
    note: '确认：两组均为《刀剑异闻录》同一包（周年附属版是其子版本）→ 被拆成两组。',
  },
  '三只大猪TB_pig||三只大猪tb_pig::最适合初次游玩铁砧工艺的 铁砧工艺极速版|三只大猪tb_pig::铁砧工艺 极速版 完美体验铁砧工艺的所有内容': {
    verdict: 'UNDER_MERGE', confidence: 'high',
    note: '确认：两组均为「铁砧工艺极速版」同一包 → 被拆成两组。',
  },
  '-六五六-||-六五六-::也能畅玩射击 六五六极致|-六五六-::建筑 党的福音来辣 六五六极致美化': {
    verdict: 'NOT_UNDER_MERGE', confidence: 'medium',
    note: '否决（保留意见）：两组均含“六五六极致”，但一为射击向、一为建筑美化向，可能是该 uploader 的**两个不同**整合包。簇由 uploader 自名连通，不构成同包证据。',
  },
  '星辉の天晓||星辉の天晓::天晓 匠魂之旅|星辉の天晓::天晓 血肉寄生虫 血肉 感染 寄生虫': {
    verdict: 'NOT_UNDER_MERGE', confidence: 'medium',
    note: '否决：匠魂之旅 与 血肉寄生虫 是两个不同包。簇由 uploader 自名“天晓”连通。',
  },
  'KonataWorks||__raw_BV1Fg8gzHE7K|konataworks::生电 拥有最全的辅助模组最适合生电的': {
    verdict: 'UNDER_MERGE', confidence: 'medium',
    note: '确认（低风险）：单条未归组记录与「生电」组同属该 uploader 的生电优化包。',
  },
  '我嘞个牢末ENd||我嘞个牢末end::增强 轻量 v 内容新鲜出炉|我嘞个牢末end::增强 轻量 周末的 预告以上菜': {
    verdict: 'UNDER_MERGE', confidence: 'high',
    note: '确认：两组均为该 uploader 的“增强·轻量”同一包（v? 更新 / 预告）→ 被拆成两组。',
  },
  '无双小星||__raw_BV1h7wFeEEQn|无双小星::幸运泰坦': {
    verdict: 'UNDER_MERGE', confidence: 'medium',
    note: '确认（低风险）：单条未归组记录与「幸运泰坦」组同属该 uploader 的泰坦系列包。',
  },
  '无双小星||无双小星::幸运大 低配|无双小星::幸运方块 低配版': {
    verdict: 'UNDER_MERGE', confidence: 'high',
    note: '确认：两组均为该 uploader 的“幸运方块 低配版”同一包 → 被拆成两组。',
  },
  'SmartAkita||smartakita::cobblemon方块宝可梦 预览 免费 同时提供两种稳定服务端 有光影 一键开服 可伙伴联机 可转载 不限速 体验|smartakita::方块宝可梦 版本 含服务端 免费 cobblemon 进化特效 全新宝可梦添加 双打模式': {
    verdict: 'UNDER_MERGE', confidence: 'high',
    note: '确认：两组均为 Cobblemon 方块宝可梦同一包 → 被拆成两组。',
  },
  '吴也mc||吴也mc::全新的灾难降临 安全开局 平衡大增|吴也mc::灾难降临 你需要击杀怪物 升级 技能树 开拓安全区 重建家园': {
    verdict: 'UNDER_MERGE', confidence: 'high',
    note: '确认：两组均为《灾难降临》同一包 → 被拆成两组。',
  },
  '孑孑雨不是牢孑||孑孑雨不是牢孑::annoying villagers烦村|孑孑雨不是牢孑::烦村 史诗级': {
    verdict: 'UNDER_MERGE', confidence: 'high',
    note: '确认：两组均为“烦村/Annoying Villagers”同一包 → 被拆成两组。',
  },
  '碎砖做的砖块王||碎砖做的砖块王::幸运之证 超多不同种类的幸运方块 全站 超高版本的幸运方块大 低配|碎砖做的砖块王::幸运方块大 高版本的幸运方块大 全站 46个幸运方块 版本': {
    verdict: 'UNDER_MERGE', confidence: 'high',
    note: '确认：两组均为该 uploader 的“高版本幸运方块大”同一包 → 被拆成两组。',
  },
  'Deemo旋律||deemo旋律::地球2 版本|deemo旋律::地球3 预览 版本': {
    verdict: 'NOT_UNDER_MERGE', confidence: 'medium',
    note: '否决：地球2 与 地球3 极可能是两个不同的包（代际不同），版本号不连续且体量不同；不合并。',
  },
  '空空如也js||空空如也js::惊变100天v ftb500|空空如也js::惊变100天但是是': {
    verdict: 'UNDER_MERGE', confidence: 'medium',
    note: '确认：两组均为《惊变100天》同一包的两次发布 → 被拆散。',
  },
  '以乐太洋||以乐太洋::fcl h lpe 的 ftb 生于灾厄 低配丰富的 可不多见|以乐太洋::fcl 优化 帧率肯定包提升的啊': {
    verdict: 'NOT_UNDER_MERGE', confidence: 'medium',
    note: '否决：一为“生于灾厄”整合包移植，一为该 uploader 的 FCL 优化包，属不同包。',
  },
  '韬可梦||韬可梦::宝可梦 向 实时 版 目标是成为宝可梦大师|韬可梦::宝可梦 向 领先 版本 主打紧跟时事': {
    verdict: 'UNDER_MERGE', confidence: 'medium',
    note: '确认：两组均为该 uploader 的宝可梦向整合包（实时版 / 领先版）→ 可能是同一包的两次发布，标 medium。',
  },
  '星必尘Sguan||星必尘sguan::基岩版 rlcraft适配手机版 汉化 年度优化 超真实 addon|星必尘sguan::真正在基岩版 做个石粒人 rlcraft汉化 重大 超真实的 国际版be pe 均可用': {
    verdict: 'UNDER_MERGE', confidence: 'high',
    note: '确认：两组均为该 uploader 的“RL Craft 基岩版汉化”同一包 → 被拆成两组。',
  },
  '在职玩家JoStar||在职玩家jostar::方可梦 1 已 确定航线 出发 去吧 方可梦大师 尝鲜体验包现已|在职玩家jostar::方块宝可梦 za全mega已 全系统 全图鉴 去吧 方可梦大师 双版本 正式 也有服务端哦 持续 方可梦 内容|在职玩家jostar::方块宝可梦最 几乎全图鉴 想要的全都有 方可梦 版本 啦|在职玩家jostar::方块宝可梦超全 化身小智 钛晶 mega z招式三系统全都要 踏上击败各地区道馆主的冠军之路吧 去吧 方可梦大师 正式': {
    verdict: 'UNDER_MERGE', confidence: 'high',
    note: '确认：四组均为《去吧，方可梦大师》同一包（1.7 尝鲜 / 2.99 / 3.0 / 4.0 双版本）→ 被拆成四组。3G-F.2-A 的 anchor 下沉把原本一个候选组拆成了四条独立记录，同包结论不变。',
  },
  'ZiCaiOT||zicaiot::农场物语|zicaiot::在 中还原星露谷 农场物语': {
    verdict: 'UNDER_MERGE', confidence: 'high',
    note: '确认：`在 中还原星露谷 农场物语`（3 条）与 `农场物语`（3 条）都是该 uploader 的《农场物语》同一包（1.1.7 / 1.2.0 / 1.2.6 / 1.4.1 / 1.6.7 连续版本号）→ 被拆成两键，属跨组拆分。',
  },
  '不知名的莫理沙||不知名的莫理沙::你从未见过的多线性枪魔 勇者之章 大量模组物品修改和添加说明 70 boss|不知名的莫理沙::异界法师 稳定版本 枪魔 之 勇者之章|不知名的莫理沙::星月枪姬与落魄勇者': {
    verdict: 'UNDER_MERGE', confidence: 'high',
    note: '确认：三组标题都带 `勇者之章Ⅲ`，是《勇者之章Ⅲ》同一包的不同子版本（多线性枪魔 / 异界法师 / 星月枪姬与落魄勇者）→ 3G-F.2-A 的 anchor 下沉把原本一个组拆成三组，属跨组拆分（同包）。',
  },
  'plaudite_||plaudite_::v s scarlet adventure绯红|plaudite_::vivid stasis 模组 绯红 scarlet adventure 附': {
    verdict: 'UNDER_MERGE', confidence: 'high',
    note: '确认：两组均为《Scarlet Adventure 绯红冒险》同一包（v2.0 发布 / 介绍+发布）→ 3G-F.2-A 的 anchor 下沉把原本一个组拆成两条独立记录，属跨组拆分（同包）。',
  },
  '叙利亚自爆民兵||叙利亚自爆民兵::你好 新世代 voxy 机械动力 瓦尔基里全新兼容|叙利亚自爆民兵::你好 新蒸程 正式 航空学 voxy 独家地形 构成 的视觉盛宴': {
    verdict: 'NOT_UNDER_MERGE', confidence: 'high',
    note: '否决：这正是 R1（name-slot disagreement）刚刚分开的两个包——《你好，新世代》与《你好，新蒸程》。它们共享 voxy / 航空学 等通用组件词，但方括号名槽互不相同。合并回去就是把修复撤销。',
  },
  'ARR-C6H6||arr-c6h6::真菌感染加惊变100天 旧世界|arr-c6h6::真菌感染惊变类轻量化 爽 旧世界': {
    verdict: 'UNDER_MERGE', confidence: 'high',
    note: '确认：两组均为该 uploader 的《旧世界》同一包（v0.3Beta / v0.4Beta，标题结构一致）→ 被拆成两组。',
  },
  '原界环||原界环::全新 pve 少女准备中 maiden or not 自locknar的 or not|原界环::少女 以及cqb or not girl amp gun': {
    verdict: 'NOT_UNDER_MERGE', confidence: 'high',
    note: '否决：这是 R3（English function words）刚刚分开的两个包。“or not” 是命名后缀（跨 IP），不是包名，合并会制造误合并。',
  },
  'Tibsalta||tibsalta::抗争之际 难度驱动 向|tibsalta::旅途痕迹 难度驱动': {
    verdict: 'NOT_UNDER_MERGE', confidence: 'high',
    note: '否决：这是 R1（name-slot disagreement）刚刚分开的两个包——《抗争之际》与《旅途痕迹》。【难度驱动】只是系列标签。合并回去就是把修复撤销。',
  },
};;;


function keyOf(finding) {
  return finding.author + '||' + [...finding.group_keys].sort().join('|');
}

/** The group keys the 涅槃 family occupies in the REMEDIATED runtime.
 *
 *  CORRECTED PREMISE (Phase 3G-F.1-A). The 3G-F-A audit recorded 涅槃 as
 *  "7 records, ONE pack, split into FIVE groups" and the phase brief inherited
 *  that as ground truth. Re-reading the STRUCTURED download_links shows it is
 *  wrong:
 *
 *    5 records  ->  mcmod.cn/modpack/1418 + xyebbs.com/resources/37418   (涅槃)
 *    2 records  ->  bbsmc.net/modpack/unfinished_path_nirvana
 *                   + xyebbs.com/res-id/TUPN                              (未尽之路-涅槃)
 *
 *  The uploader's own description states the two are unrelated ("不基于《未尽之路》
 *  开发，也与《未尽之路》毫无关联"). The correct target is therefore TWO groups;
 *  forcing 1 would be a real over-merge. The runtime produces exactly these two.
 *  Coverage is asserted against this list, and the legacy five-key list is kept
 *  below only as historical reference for the pre-fix split. */
const NIE_SPLIT_GROUP_KEYS = [
  '墨言eclipse::涅槃',
  '墨言eclipse::未尽之路涅槃',
];

/** The five keys the 涅槃 family WAS split into before the fix. Kept so the
 *  audit records what the defect looked like, and so a regression that re-splits
 *  涅槃 back into these keys is visible. */
const NIE_LEGACY_SPLIT_GROUP_KEYS = [
  '墨言eclipse::涅槃 无神明渡我 我亦是神明',
  '墨言eclipse::涅槃 神吞降世 邪神投影 万魂幡 超越法则的 镰刀 之旅',
  '墨言eclipse::大型 禁忌 远古炼金 世界污染 3万行代码深度 涅槃v 0 宣传视频',
  '墨言eclipse::沉浸 深度 a 咒镰双生',
  '墨言eclipse::未尽之路涅槃',
];

// Keys rescued out of a mixed cluster: the cluster verdict is
// PARTIAL_UNDER_MERGE, so the cluster alone does not mark these as UNDER_MERGE.
// Hand-adjudicated: this key belongs to the 未尽之路-涅槃 pack.
const PER_KEY_UNDER_MERGE = new Set([
  '墨言eclipse::未尽之路涅槃',
]);

function main() {
  const cand = JSON.parse(fs.readFileSync(CANDIDATES, 'utf8'));
  const um = JSON.parse(fs.readFileSync(UNDERMERGE, 'utf8'));

  const rows = [];
  const unadjudicated = [];
  for (const c of cand.candidates) {
    const v = VERDICTS[c.group_key];
    if (!v || !v.verdict) { unadjudicated.push(c.group_key); continue; }
    rows.push({
      layer: 'candidate',
      group_key: c.group_key,
      author: c.author,
      anchor: c.anchor,
      size: c.size,
      detector_reasons: c.detector_reasons,
      newly_merged: c.newly_merged,
      verdict: v.verdict,
      confidence: v.confidence,
      evidence: {
        note: v.note,
        shared_download_identities: c.download_identities.shared,
        distinct_download_identities: c.download_identities.distinct_count,
        shared_qq_identities: c.qq_identities.shared,
        members: c.members.map((m) => ({ bvid: m.bvid, title: m.title })),
      },
    });
  }

  // clusters the detector produced rows for but that we deliberately did not
  // include as candidate rows (the 沉浸/未尽之路 pair shares members with the
  // candidate layer) - still adjudicate the cross-group layer explicitly.
  const umRows = [];
  const umUndeclared = [];
  for (const f of um.findings) {
    const k = keyOf(f);
    const v = UNDERMERGE_VERDICTS[k];
    if (!v || !v.verdict) { umUndeclared.push(k); }
    umRows.push({
      layer: 'cross_group',
      author: f.author,
      group_keys: f.group_keys,
      group_count: f.group_count,
      record_count: f.record_count,
      shared_tokens: f.shared_tokens,
      detector_reasons: f.detector_reasons,
      verdict: v && v.verdict ? v.verdict : 'UNREVIEWED',
      confidence: v && v.confidence ? v.confidence : null,
      evidence: {
        note: v && v.note ? v.note : '',
        members: f.evidence.map((e) => ({ group_key: e.group_key, anchor: e.anchor, records: e.members })),
      },
    });
  }

  // ---- counts. AMBIGUOUS / FALSE_SPLIT are NOT false merges. ----
  const by = (v, arr = rows) => arr.filter((r) => r.verdict === v);
  const real = by('REAL_FALSE_MERGE');
  const legit = by('LEGITIMATE_SAME_PACK');
  const split = by('FALSE_SPLIT_INDICATOR');
  const amb = by('AMBIGUOUS');

  // The 8 groups that carried REAL_FALSE_MERGE at 3G-F.1-B. All 8 are now CLOSED:
  // they must appear in RETIRED_FALSE_MERGES with a cause, and must NOT reappear
  // as a live REAL_FALSE_MERGE (that would mean the fix regressed).
  const known8 = Object.keys(RETIRED_FALSE_MERGES);
  const known8StillMerging = known8.filter(
    (k) => rows.some((r) => r.group_key === k && r.verdict === 'REAL_FALSE_MERGE'),
  );
  const known8Unexplained = known8.filter((k) => !RETIRED_FALSE_MERGES[k].fixed_by);
  // The 涅槃 premise was CORRECTED in 3G-F.1-A: the records' structured
  // download_links split 5 + 2 into two genuinely different packs, so the runtime
  // target is TWO groups, not one. Coverage is asserted against the live keys.
  const nieClusters = umRows.filter((r) => r.group_keys.some((k) => k.includes('涅槃')));
  const nieUnderMerge = nieClusters.filter((r) => r.verdict === 'UNDER_MERGE');
  const coveredByUnderMerge = new Set(nieUnderMerge.flatMap((r) => r.group_keys));
  // Keys rescued from a mixed (PARTIAL_UNDER_MERGE) cluster count too.
  for (const k of PER_KEY_UNDER_MERGE) coveredByUnderMerge.add(k);
  // ...but a key inside a cluster adjudicated NOT_UNDER_MERGE must NOT be
  // silently covered by the blanket rescue above.
  for (const r of umRows) {
    if (r.verdict === 'NOT_UNDER_MERGE') for (const k of r.group_keys) coveredByUnderMerge.delete(k);
  }
  const nieKeysCovered = NIE_SPLIT_GROUP_KEYS.filter((k) => coveredByUnderMerge.has(k));
  // A key counts as SATISFIED when either:
  //   (a) it is a confirmed under-merge (still split, still needs restoring), or
  //   (b) it is a live group that never needed restoring - i.e. the runtime
  //       already merged its members correctly.
  //
  // DELIBERATELY NOT derived from the CANDIDATE list. `VERDICTS` already carries a
  // LEGITIMATE_SAME_PACK verdict for every 涅槃 key, and that is a statement about
  // the REVIEW LIST, not about group size: a correct group can be flagged by the
  // detector (size 5 trips `large_group`) and a broken one need not be. So the
  // live group size is measured directly off the runtime decisions.
  const liveGroupSizes = new Map();
  for (const r of rows) liveGroupSizes.set(r.group_key, r.size);
  const nieKeysSatisfied = NIE_SPLIT_GROUP_KEYS.filter(
    (k) => coveredByUnderMerge.has(k) || liveGroupSizes.get(k) >= 2,
  );
  const nieKeysMissing = NIE_SPLIT_GROUP_KEYS.filter((k) => !nieKeysSatisfied.includes(k));
  // REGRESSION detector. A regression would put the family BACK into the five
  // legacy keys. This must be a THRESHOLD, not "any overlap": the corrected target
  // itself contains 未尽之路涅槃, which is one of the five legacy keys, so a plain
  // membership test would fire on the CORRECT state. >1 means the family has
  // re-fragmented (and the corrected 涅槃 key has already been swallowed).
  const nieLegacyKeysPresent =
    NIE_LEGACY_SPLIT_GROUP_KEYS.filter((k) => rows.some((r) => r.group_key === k));
  const nieRegressedToLegacySplit = nieLegacyKeysPresent.length > 1;


  const declaredButAbsent = Object.keys(VERDICTS)
    .filter((k) => VERDICTS[k].verdict && !rows.some((r) => r.group_key === k));

  const umDeclaredButAbsent = Object.keys(UNDERMERGE_VERDICTS)
    .filter((k) => UNDERMERGE_VERDICTS[k].verdict && !umRows.some((r) => keyOf(r) === k));
  // Every retired cluster must actually be absent - a "retired" row that is still
  // live would mean the ledger is double-counting.
  const umRetiredPresent = Object.keys(RETIRED_UNDERMERGE_CLUSTERS)
    .filter((k) => umRows.some((r) => keyOf(r) === k));

  // Keys VERDICTS still names that are no longer candidates. Every one must be
  // accounted for in RETIRED_CANDIDATE_KEYS - an unexplained absence is exactly
  // the failure mode this ledger exists to prevent.
  const retiredCandidateDeclared = Object.keys(RETIRED_CANDIDATE_KEYS);
  const retiredCandidateMissing = retiredCandidateDeclared.filter(
    (k) => rows.some((r) => r.group_key === k),
  );

  const candidatePrecision = rows.length ? real.length / rows.length : null;

  const result = {
    phase: '3G-F.1-B',
    // SOURCE_DATE_EPOCH support: without it, re-running the audit changes only
    // this timestamp, which makes a TRACKED artifact show up as dirty and hides
    // real drift behind noise. Set SOURCE_DATE_EPOCH for byte-reproducible output.
    generated_at: new Date(
      (process.env.SOURCE_DATE_EPOCH ? Number(process.env.SOURCE_DATE_EPOCH) * 1000 : Date.now()),
    ).toISOString(),
    artifact: 'bilibili_population_adjudication_v2',
    separation_of_concerns: {
      detector: 'pipeline/audit/bilibili_population_candidate_scan_v2.js (over-reports; no verdicts)',
      adjudication: 'pipeline/audit/bilibili_population_adjudication_v2.js (this file; hand-maintained table)',
      rule: 'No verdict is ever derived by rule. Every entry was written by reading member titles.',
    },
    candidates_total: cand.candidates_total,
    adjudicated_total: rows.length,
    unadjudicated: unadjudicated,
    declared_but_absent: declaredButAbsent,
    retired_false_merges: RETIRED_FALSE_MERGES,
    retired_candidate_keys: RETIRED_CANDIDATE_KEYS,
    retired_candidate_keys_still_present: retiredCandidateMissing,
    counts: {
      real_false_merge: real.length,
      legitimate_same_pack: legit.length,
      false_split_indicator: split.length,
      ambiguous: amb.length,
      known_8_retired: known8.length,
      known_8_still_merging: known8StillMerging,
      known_8_unexplained: known8Unexplained,
      candidates_total: cand.candidates_total,
      candidates_adjudicated: rows.length,
      retired_candidate_keys: retiredCandidateDeclared.length,
    },
    // Candidate-detector precision: of the groups the DETECTOR flagged, how many
    // turned out to be real false merges. This is a statement about the REVIEW
    // LIST, NOT about the grouping algorithm's own precision.
    candidate_detector_precision: {
      definition: 'real_false_merge / candidates_total',
      value: candidatePrecision,
      numerator: real.length,
      denominator: rows.length,
      caveat: 'Over-reporting is the detector\'s DESIGN GOAL. A low value is expected and healthy; '
        + 'a high value would mean the detector is too narrow, i.e. blind spots remain.',
    },
    under_merge: {
      clusters_reviewed: umRows.length,
      confirmed_under_merge: umRows.filter((r) => r.verdict === 'UNDER_MERGE').length,
      not_under_merge: umRows.filter((r) => r.verdict === 'NOT_UNDER_MERGE').length,
      unreviewed: umUndeclared,
      declared_but_absent: umDeclaredButAbsent,
      retired_clusters: RETIRED_UNDERMERGE_CLUSTERS,
      retired_but_present: umRetiredPresent,
      clusters_reviewed_at_3gf1b: umRows.length + Object.keys(RETIRED_UNDERMERGE_CLUSTERS).length - 1,

      nie_clusters: nieClusters.length,
      nie_under_merge_clusters: nieUnderMerge.length,
      nie_corrected_target_groups: NIE_SPLIT_GROUP_KEYS.length,
      nie_group_keys_satisfied: nieKeysSatisfied,
      nie_group_keys_missing: nieKeysMissing,
      nie_legacy_split_keys_present: nieLegacyKeysPresent,
      nie_regressed_to_legacy_split: nieRegressedToLegacySplit,
      nie_legacy_key_caveat: '未尽之路涅槃 is itself one of the five pre-fix keys AND is part of the '
        + 'corrected target (it is a genuinely different pack), so presence of ONE legacy key is '
        + 'expected. Only >1 legacy key co-existing means 涅槃 re-fragmented.',

      nie_premise_correction: '3G-F-A recorded 涅槃 as 7 records -> 1 pack split 5 ways. '
        + 'Its own structured download_links disprove that: 5 records share '
        + 'mcmod modpack/1418 + xyebbs resources/37418, and 2 share bbsmc '
        + 'unfinished_path_nirvana + xyebbs res-id/TUPN. The corrected target is 2 groups.',
    },
    real_false_merges: real,
    false_split_indicators: split,
    ambiguous: amb,
    legitimate_same_pack: legit,
    cross_group_adjudication: umRows,
    remaining_blind_spots: [
      'The detector only inspects groups the CURRENT algorithm already produced. A pack whose members were split apart is invisible to the candidate layer by construction (the cross-group layer is the only partial remedy).',
      'Adjudication uses titles + URL/QQ only. Packs that were genuinely renamed across uploads cannot be confirmed from this data at all.',
      'Size-1 groups are never candidates. A false merge that absorbed ALL members of one pack leaves the other pack with no group at all - undetectable here.',
      'Generic-name packs (e.g. 海洋主题, 全家桶, 基岩版) are only adjudicable because the uploader has few packs; a prolific uploader with two identically-named packs would be indistinguishable.',
      'The cross-group scanner requires a RARE shared token. Two groups of the same pack that share no rare token (pure rename) are not surfaced.',
    ],
  };

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(result, null, 2), 'utf8');

  console.log('=== Phase 3G-F.1-B population adjudication ledger v2 ===');
  console.log(`candidates total      : ${cand.candidates_total}`);
  console.log(`adjudicated           : ${rows.length}`);
  console.log(`REAL_FALSE_MERGE      : ${real.length}`);
  console.log(`LEGITIMATE_SAME_PACK  : ${legit.length}`);
  console.log(`FALSE_SPLIT_INDICATOR : ${split.length}`);
  console.log(`AMBIGUOUS             : ${amb.length}`);
  console.log(`known 8 retired       : ${known8.length - known8StillMerging.length - known8Unexplained.length}/${known8.length}`);
  if (known8StillMerging.length) console.log(`!! STILL MERGING: ${known8StillMerging.join(', ')}`);
  if (known8Unexplained.length) console.log(`!! UNEXPLAINED RETIREMENT: ${known8Unexplained.join(', ')}`);
  console.log(`candidate precision   : ${(candidatePrecision * 100).toFixed(1)}%`);
  console.log(`under-merge clusters  : ${umRows.length} reviewed, `
    + `${result.under_merge.confirmed_under_merge} confirmed`);
  console.log(`retired false merges  : ${Object.keys(RETIRED_FALSE_MERGES).length}`);
  console.log(`retired candidate keys: ${retiredCandidateDeclared.length}`);
  console.log(`涅槃 keys satisfied   : ${nieKeysSatisfied.length}/${NIE_SPLIT_GROUP_KEYS.length} (corrected target = 2 groups)`);
  if (nieRegressedToLegacySplit) console.log(`!! NIEVANA REGRESSED TO LEGACY SPLIT: ${nieLegacyKeysPresent.join(' | ')}`);
  if (nieKeysMissing.length) console.log(`!! NIEVANA KEYS MISSING: ${nieKeysMissing.join(' | ')}`);
  if (unadjudicated.length) console.log(`!! UNADJUDICATED: ${unadjudicated.join(', ')}`);
  if (declaredButAbsent.length) console.log(`!! DECLARED-BUT-ABSENT: ${declaredButAbsent.join(', ')}`);
  if (retiredCandidateMissing.length) console.log(`!! RETIRED-BUT-PRESENT: ${retiredCandidateMissing.join(', ')}`);
  if (umDeclaredButAbsent.length) console.log(`!! UM DECLARED-BUT-ABSENT: ${umDeclaredButAbsent.length} cluster(s)`);
  if (umRetiredPresent.length) console.log(`!! UM RETIRED-BUT-PRESENT: ${umRetiredPresent.length} cluster(s)`);
  console.log(`um retired clusters   : ${Object.keys(RETIRED_UNDERMERGE_CLUSTERS).length}`);
  console.log(`written: ${path.relative(REPO_ROOT, OUT)}`);
  return (unadjudicated.length || known8StillMerging.length
    || known8Unexplained.length || nieKeysMissing.length
    || declaredButAbsent.length || retiredCandidateMissing.length
    || umDeclaredButAbsent.length || umRetiredPresent.length
    || (nieRegressedToLegacySplit ? 1 : 0)) ? 1 : 0;
}

process.exit(main());

/**
 * Phase 3G-F-A - human adjudication ledger for the widened slogan-anchor scan.
 *
 * The headline count "N confirmed false merges" must not rest on a heuristic.
 * This script takes the raw scan output (build/audit/bilibili_grouping_slogan_anchor_scan.json),
 * joins it against a HAND-MAINTAINED verdict table, and emits the ledger.
 *
 * Verdicts are assigned by reading every member title, not by any rule.
 *   REAL_FALSE_MERGE  - members are demonstrably DIFFERENT packs (anchor is a slogan/boss/item/boilerplate)
 *   LEGITIMATE        - members are the SAME pack (anchor is the pack name, or a stable release series name)
 *   UNDECIDED         - genuinely ambiguous from title alone; must be reported as such, never counted
 *
 * Usage: node pipeline/audit/bilibili_grouping_anchor_adjudication.js
 * Output: build/audit/bilibili_grouping_anchor_adjudication.json
 */
const fs = require('fs');
const path = require('path');

const REPO_ROOT = path.resolve(__dirname, '..', '..');
const SCAN = path.join(REPO_ROOT, 'build', 'audit', 'bilibili_grouping_slogan_anchor_scan.json');
const OUT = path.join(REPO_ROOT, 'build', 'audit', 'bilibili_grouping_anchor_adjudication.json');

// key (group_key) -> { verdict, note }
const VERDICTS = {
  // ---- REAL: anchor is a shared TAIL SLOGAN / boss / item, members are different packs ----
  '一个小寂哦::星辉死神': { verdict: 'REAL_FALSE_MERGE', note: '神器收集计划 / 无尽幸运方块大陆 / 全网最全神器 是三个不同包；“星辉死神”是 Boss/物品名。' },
  '一个小寂哦::四叶草': { verdict: 'REAL_FALSE_MERGE', note: '新泰坦生物整合包 / 执行之龙生存整合包 是两个不同包；“四叶草”是物品名。' },
  '一个小寂哦::各大主播同款': { verdict: 'REAL_FALSE_MERGE', note: '幸运方块大全 / 超困难神器泰坦随机合成 是两个不同包；“各大主播同款”是宣传口号。' },
  '墨言eclipse::颠覆性的': { verdict: 'REAL_FALSE_MERGE', note: '摄影奇境 / 千界万锻 是两个不同包；“颠覆性的”是形容词。' },
  '原界环::or not': { verdict: 'REAL_FALSE_MERGE', note: 'Minecraft or Not: Girl&Gun / Maiden or not 是两个不同包；“or not”是命名后缀（跨 IP）。' },
  // NOTE (verified against bili_data, not inferred): ALL 7 records containing 涅槃 belong to
  // uploader 墨言eclipse and are the SAME pack (涅槃 v0.1.5 -> v0.2). The algorithm SPLIT them
  // into 5 buckets, so these two groups are UNDER-merged (a false-SPLIT symptom), NOT false merges.
  '墨言eclipse::沉浸 深度 a 咒镰双生': { verdict: 'LEGITIMATE', note: '成员是同一个包 涅槃 v0.1.6 / v0.1.5（已核实）。虽然 anchor 落在 tag [沉浸战斗/深度魔改/ARPG/咒镰双生] 上是“坏 anchor”，但成员确实同包 → 不是误合并。真正的问题是涅槃被拆成 5 组（见 under_merged 段落）。' },
  '墨言eclipse::未尽之路涅槃': { verdict: 'LEGITIMATE', note: '成员是同一个包 涅槃（预发布 / 发布前预热）。“未尽之路涅槃”这类阶段性标题词被当作 anchor，同一包被拆散 → 属于 false-split，不是误合并。' },
  '非茉涟柠::hunt history 1949': { verdict: 'LEGITIMATE', note: '四条均为《猎杀：历史 1949 / Hunt: History 1949》同一包的 1.0~1.2 版本发布；anchor 是包名。' },
  '不知名的莫理沙::勇者之章': { verdict: 'LEGITIMATE', note: '四条均为“勇者之章Ⅲ”同一系列（异界法师/星月枪姬是其子包名）；anchor 是系列名。' },
  '在职玩家jostar::去吧 方可梦大师': { verdict: 'LEGITIMATE', note: '三条均为《去吧，方可梦大师》同一包 3.0/4.0/1.7 版本；anchor 是包名。' },
  '老本願::魔之逆鳞': { verdict: 'LEGITIMATE', note: '三条均为“魔之逆鳞”同一包（0.6 公测/更新/正式）；anchor 是包名。' },
  '橘子皮zero::拯救世界重建文明': { verdict: 'LEGITIMATE', note: '三条均为“凋落之花”同一包；“拯救世界重建文明”是副标语但该上传者只做这一个包，合并无实际危害。' },
  '墨竹ギ::深渊之诗': { verdict: 'LEGITIMATE', note: '三条均为《深渊之诗 / Poetry of the Abyss》同一包 2.0/2.2；anchor 是包名。' },
  '懂嗎懂嗎::齿轮与腐肉': { verdict: 'LEGITIMATE', note: '八条均为「齿轮与腐肉」同一包 0.21~0.50；anchor 是包名。注：该包名本身是标题尾部的化名，但成员确定是同一个包。' },
  '缓慢的开始::soa3': { verdict: 'LEGITIMATE', note: '七条均为 SoA3（虚无世界3）同一包；anchor 是版本/系列代号。' },
  '炒雪吵狐力o::rapid': { verdict: 'LEGITIMATE', note: '三条均为 Rapid Optimization 同一优化包的重复发布；anchor 是包名。' },
  'plaudite_::scarlet': { verdict: 'LEGITIMATE', note: '两条均为 Scarlet Adventure 绯红冒险 同一包；anchor 是包名。' },
  '--axx--::mygo': { verdict: 'LEGITIMATE', note: '已核实：同一上传者 --Axx-- 的两条，均为 MYGO 命名（Ver1.8.0 / 1.5.0）。“鬼影重重”与“多人枪战”是否同一包的两次改名无法从标题确证 → 保守判 LEGITIMATE，不计数。' },
  '磁钢百合::旅行时光 饥饿': { verdict: 'LEGITIMATE', note: '两条均为“旅行时光:饥饿”同一包（1.7.0 更新 / 公测）；anchor 是包名。' },
  '叙利亚自爆民兵::voxy': { verdict: 'REAL_FALSE_MERGE', note: '已核实：《你好，新蒸程》与《你好，新世代》是两个不同包（各自独立命名），共同点只是都用了 voxy 渲染模组。voxy 是通用模组名，不构成包标识。' },
  'tibsalta::难度驱动': { verdict: 'REAL_FALSE_MERGE', note: '已核实：《抗争之际0.6》与《旅途痕迹0.5》是两个不同包，共享的只是系列标签【难度驱动】。该包名在方括号外、系列标签在方括号内，规则把方括号内的标签当成了 anchor。' },
  '一个小寂哦::重回 之巅': { verdict: 'LEGITIMATE', note: '两条均为该上传者的“最全拔刀剑”系列（3.0 / 重逢 2.0），同一作者同一系列；判 LEGITIMATE。' },
  'arr-c6h6::旧世界': { verdict: 'LEGITIMATE', note: '两条均为「旧世界」同一包 v0.3/v0.4；anchor 是包名。' },
  '流霜雾影::愚者版本大': { verdict: 'LEGITIMATE', note: '两条均为「愚者」同一包 v0.1/v0.2；anchor 落在“愚者版本大更新”上，但成员是同一包。' },
  '-阳春面面-::青春复兴': { verdict: 'UNDECIDED', note: '“格雷青春版”与“蔚蓝档案超大型”是否同一包的两次改版，标题无法判定；不计数。' },
  '吴也mc::冬境边域': { verdict: 'LEGITIMATE', note: '两条均为「冬境边域」同一包；anchor 是包名。' },
  'jsi我的世界制作组::create delight': { verdict: 'LEGITIMATE', note: '两条均为 Create Delight 同一包 1.0.2 / 无版本号；anchor 是包名。' },
  'puikre::定制模组 成为锻造大师': { verdict: 'LEGITIMATE', note: '两条均为“成为锻造大师”同一包；anchor 是包名（前面是 slogan）。' },
  '明月庄主::月亮工厂 f': { verdict: 'LEGITIMATE', note: '两条均为《月亮工厂 MCF》同一包（1.19.2-3.0 / 1.20.1）；anchor 是包名。' },
  '墨竹ギ::史诗的地下城 dungeons of fantasy': { verdict: 'LEGITIMATE', note: '两条均为 Dungeons Of Fantasy 同一包 7.0/7.2；anchor 是包名。' },
  '吴也mc::内容 better 版': { verdict: 'LEGITIMATE', note: '已核实：成员均为吴也mc 的《更好的MC / Better Minecraft》汉化介绍（v11 / 最新），同一包；“内容 better 版”是公告式尾缀。' },
};

function main() {
  const scan = JSON.parse(fs.readFileSync(SCAN, 'utf8'));
  const rows = [];
  const unknown = [];
  for (const f of scan.flagged) {
    const v = VERDICTS[f.group_key];
    if (!v) { unknown.push(f.group_key); continue; }
    rows.push({
      group_key: f.group_key,
      anchor: f.anchor,
      size: f.size,
      distinct_prefixes: f.distinct_prefixes.length,
      newly_merged: f.newly_merged,
      verdict: v.verdict,
      note: v.note,
      members: f.members.map((m) => ({ bvid: m.bvid, title: m.title })),
    });
  }
  const byVerdict = (v) => rows.filter((r) => r.verdict === v);
  const real = byVerdict('REAL_FALSE_MERGE');
  const legit = byVerdict('LEGITIMATE');
  const und = byVerdict('UNDECIDED');

  const extraDeclared = Object.keys(VERDICTS).filter((k) => !rows.some((r) => r.group_key === k));

  const result = {
    generated_at: new Date().toISOString(),
    scan_flagged_count: scan.flagged_count,
    verdict_source: 'hand adjudication (VERDICTS table in bilibili_grouping_anchor_adjudication.js)',
    real_false_merge_count: real.length,
    legitimate_count: legit.length,
    undecided_count: und.length,
    unadjudicated: unknown,
    declared_but_absent: extraDeclared,
    real_false_merges: real,
    undecided: und,
    legitimate: legit,
  };
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(result, null, 2), 'utf8');

  console.log('=== Phase 3G-F-A anchor adjudication ledger ===');
  console.log(`scanned flagged : ${scan.flagged_count}`);
  console.log(`REAL false merge: ${real.length}`);
  console.log(`LEGITIMATE      : ${legit.length}`);
  console.log(`UNDECIDED       : ${und.length}`);
  if (unknown.length) console.log(`!! UNADJUDICATED : ${unknown.join(', ')}`);
  if (extraDeclared.length) console.log(`!! DECLARED-BUT-ABSENT : ${extraDeclared.join(', ')}`);
  console.log('\n-- REAL false merges --');
  for (const r of real) console.log(`  [${r.size}] ${r.group_key}  (anchor='${r.anchor}')`);
  console.log('\n-- UNDECIDED --');
  for (const r of und) console.log(`  [${r.size}] ${r.group_key}  (anchor='${r.anchor}')`);
  console.log(`\nwritten: ${path.relative(REPO_ROOT, OUT)}`);
  return unknown.length ? 1 : 0;
}

process.exit(main());

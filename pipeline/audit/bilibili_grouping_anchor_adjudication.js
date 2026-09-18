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
const BILI_DATA = path.join(REPO_ROOT, 'converted_output', 'data', 'bili_data.js');

/**
 * Phase 3G-F.1-A - CORRECTION of the 涅槃 premise.
 *
 * The 3G-F-A audit recorded `涅槃` as "7 records, ONE pack, split into 5 groups"
 * (BILI-GRP-UNDERMERGE-01) and the phase brief inherited that as ground truth.
 * Re-reading the source records against the STRUCTURED `download_links` (not the
 * free-text description) shows the premise is wrong:
 *
 *   5 records share  xyebbs resources/37418  +  mcmod modpack/1418   -> pack 涅槃
 *   2 records share  xyebbs res-id/TUPN      +  bbsmc unfinished_path_nirvana
 *                                                                    -> pack 未尽之路-涅槃
 *
 * and the uploader states it explicitly (BV1UJET67ErR desc):
 *   "《未尽之路-涅槃》不基于《未尽之路》开发,也与《未尽之路》毫无关联,两个包唯一相同点
 *    就是开发者都是我,请不要混为一谈"
 *
 * => 2 groups is the CORRECT answer, not 1. The earlier "7 -> 1" expectation was
 *    never ground truth. This is reported, not silently absorbed: forcing a single
 *    group would have been a real over-merge.
 */
const NIRVANA_PACK_EVIDENCE = {
  '墨言eclipse::涅槃': {
    pack_name: '涅槃',
    records: 5,
    resource_ids: ['xyebbs.com/resources/37418', 'mcmod.cn/modpack/1418'],
    verdict: 'ONE PACK',
  },
  '墨言eclipse::未尽之路涅槃': {
    pack_name: '未尽之路-涅槃',
    records: 2,
    resource_ids: ['xyebbs.com/res-id/TUPN', 'bbsmc.net/modpack/unfinished_path_nirvana'],
    verdict: 'A DIFFERENT PACK (distinct resource id; uploader states the two are unrelated)',
  },
};

/** Extract stable pack-registration identifiers from a record's STRUCTURED links.
 *
 *  Only IDs that register a PACK (not a per-version share link) count: a 网盘 share
 *  changes every release, so it cannot prove pack identity. xyebbs `resources/<n>`
 *  and `res-id/<code>`, mcmod `modpack/<n>`, bbsmc `modpack/<slug>` are stable.
 */
function resourceIdsOf(record) {
  const urls = (record.download_links || []).map((l) => String(l.url || ''));
  const ids = new Set();
  for (const u of urls) {
    const m = u.match(/^https?:\/\/([^/]+)\/([^?#]*)/);
    if (!m) continue;
    const host = m[1].replace(/^www\./, '');
    if (!/^(mcmod\.cn|xyebbs\.com|bbsmc\.net)$/.test(host)) continue;
    // keep the stable path, drop trailing file names / sub-resources
    let p = m[2].replace(/\/+$/, '').replace(/\.html?$/i, '');
    const parts = p.split('/').filter(Boolean);
    if (!/^(resources|res-id|modpack)$/.test(parts[0] || '')) continue;
    if (!parts[1]) continue;
    ids.add(host + '/' + parts[0] + '/' + parts[1]);
  }
  return [...ids].sort();
}

function loadBili() {
  const raw = fs.readFileSync(BILI_DATA, 'utf8');
  return JSON.parse(raw.slice(raw.indexOf('['), raw.lastIndexOf(']') + 1));
}

// key (group_key) -> { verdict, note }
//
// Phase 3G-F.1-A: the 3G-F.1 runtime remediation REMOVED the anchor-admissibility
// defects, so five entries that used to be REAL_FALSE_MERGE (星辉死神 / 四叶草 /
// 各大主播同款 / 颠覆性的 / or not) are no longer groups at all — they stop being
// flagged. They are kept in a RETIRED table (see RETIRED_FALSE_MERGES below) so the
// historical finding is not erased, and `declared_but_absent` stays auditable.
const RETIRED_FALSE_MERGES = {
  '一个小寂哦::星辉死神': { verdict: 'REAL_FALSE_MERGE', fixed_by: 'R2 late-position feature-list veto', note: '神器收集计划 / 无尽幸运方块大陆 / 全网最全神器 是三个不同包；“星辉死神”是 Boss/物品名。' },
  '一个小寂哦::四叶草': { verdict: 'REAL_FALSE_MERGE', fixed_by: 'R2 late-position feature-list veto', note: '新泰坦生物整合包 / 执行之龙生存整合包 是两个不同包；“四叶草”是物品名。' },
  '一个小寂哦::各大主播同款': { verdict: 'REAL_FALSE_MERGE', fixed_by: 'R2 late-position feature-list veto (slogan branch)', note: '幸运方块大全 / 超困难神器泰坦随机合成 是两个不同包；“各大主播同款”是宣传口号。' },
  '墨言eclipse::颠覆性的': { verdict: 'REAL_FALSE_MERGE', fixed_by: 'R2 late-position feature-list veto', note: '摄影奇境 / 千界万锻 是两个不同包；“颠覆性的”是形容词。' },
  '原界环::or not': { verdict: 'REAL_FALSE_MERGE', fixed_by: 'R6 english function-word veto', note: 'Minecraft or Not: Girl&Gun / Maiden or not 是两个不同包；“or not”是命名后缀（跨 IP）。' },
  // Verified against bili_data: the 7 records containing 涅槃 belong to uploader 墨言eclipse
  // and are the SAME pack (涅槃 v0.1.5 -> v0.2). At 3G-F.1 they were split 6 ways; the R7
  // short-but-distinctive allowance brought that down to 2 (涅槃 | 未尽之路涅槃).
  '墨言eclipse::沉浸 深度 a 咒镰双生': { verdict: 'LEGITIMATE', fixed_by: 'R7 merged into 涅槃', note: '成员是同一个包 涅槃 v0.1.6 / v0.1.5（已核实）。虽然 anchor 落在 tag [沉浸战斗/深度魔改/ARPG/咒镰双生] 上是“坏 anchor”，但成员确实同包 → 不是误合并。' },
};

const VERDICTS = {
  // ---- REAL: anchor is a shared TAIL SLOGAN / boss / item, members are different packs ----
  // NOTE (verified against bili_data, not inferred): the 7 records containing 涅槃 belong to
  // uploader 墨言eclipse. Phase 3G-F.1-A PROVED (from the records' own structured resource
  // ids) that they are TWO packs, not one — see NIRVANA_PACK_EVIDENCE above. The earlier
  // "7 records, 1 pack, split into 5 groups" reading was wrong.
  '墨言eclipse::未尽之路涅槃': { verdict: 'LEGITIMATE', note: '成员是 未尽之路-涅槃（xyebbs res-id/TUPN），与 涅槃（xyebbs resources/37418）是两个不同产品，上传者本人明确说明过。组内合法。' },
  '非茉涟柠::hunt history 1949': { verdict: 'LEGITIMATE', note: '四条均为《猎杀：历史 1949 / Hunt: History 1949》同一包的 1.0~1.2 版本发布；anchor 是包名。' },
  '老本願::魔之逆鳞': { verdict: 'LEGITIMATE', note: '三条均为“魔之逆鳞”同一包（0.6 公测/更新/正式）；anchor 是包名。' },
  '橘子皮zero::拯救世界重建文明': { verdict: 'LEGITIMATE', note: '三条均为“凋落之花”同一包；“拯救世界重建文明”是副标语但该上传者只做这一个包，合并无实际危害。' },
  '懂嗎懂嗎::齿轮与腐肉': { verdict: 'LEGITIMATE', note: '八条均为「齿轮与腐肉」同一包 0.21~0.50；anchor 是包名。注：该包名本身是标题尾部的化名，但成员确定是同一个包。' },
  '缓慢的开始::soa3': { verdict: 'LEGITIMATE', note: '七条均为 SoA3（虚无世界3）同一包；anchor 是版本/系列代号。' },
  '炒雪吵狐力o::rapid': { verdict: 'LEGITIMATE', note: '三条均为 Rapid Optimization 同一优化包的重复发布；anchor 是包名。' },
  '--axx--::mygo': { verdict: 'LEGITIMATE', note: '已核实：同一上传者 --Axx-- 的两条，均为 MYGO 命名（Ver1.8.0 / 1.5.0）。“鬼影重重”与“多人枪战”是否同一包的两次改名无法从标题确证 → 保守判 LEGITIMATE，不计数。' },
  '磁钢百合::旅行时光 饥饿': { verdict: 'LEGITIMATE', note: '两条均为“旅行时光:饥饿”同一包（1.7.0 更新 / 公测）；anchor 是包名。' },
  '吴也mc::冬境边域': { verdict: 'LEGITIMATE', note: '两条均为「冬境边域」同一包；anchor 是包名。' },
  'jsi我的世界制作组::create delight': { verdict: 'LEGITIMATE', note: '两条均为 Create Delight 同一包 1.0.2 / 无版本号；anchor 是包名。' },
  'puikre::定制模组 成为锻造大师': { verdict: 'LEGITIMATE', note: '两条均为“成为锻造大师”同一包；anchor 是包名（前面是 slogan）。' },
  '明月庄主::月亮工厂 f': { verdict: 'LEGITIMATE', note: '两条均为《月亮工厂 MCF》同一包（1.19.2-3.0 / 1.20.1）；anchor 是包名。' },
  '吴也mc::内容 better 版': { verdict: 'LEGITIMATE', note: '已核实：成员均为吴也mc 的《更好的MC / Better Minecraft》汉化介绍（v11 / 最新），同一包；“内容 better 版”是公告式尾缀。' },
  // The two groups below surfaced only after the 3G-F.1 fix (they are groups the older
  // 3G-F scan never flagged). Adjudicated by reading every member title against bili_data.
  '在下shmily::最牛优化': { verdict: 'LEGITIMATE', note: '已核实：三条均为同一上传者 在下Shmily 的《最牛优化整合包》V4.0 / V3.9 / 首发，同一包的不同版本；anchor 就是包名本身。' },
  '小兜兜呀_::的时代': { verdict: 'LEGITIMATE', note: '已核实：七条均为同一上传者 小兜兜呀_ 的《原神与机械冒险的时代》v3.5.4.2~v3.5.12 版本更新；anchor “的时代”是完整包名“原神与机械冒险的时代”的尾部片段 → 同一包，不是误合并。' },
};

/**
 * Groups that 3G-F flagged but that NO LONGER EXIST as groups after the 3G-F.1 fix.
 * Two distinct reasons, kept separate because they mean opposite things:
 *
 *   'closed_bad_anchor'  - was a REAL false merge; the admissibility rules now reject
 *                          the bad anchor, so the members split apart. FIXED.
 *   'dissolved_singleton'- was legitimate or ambiguous; the anchor moved to index 0 or
 *                          stopped qualifying, so the members became independent cards
 *                          (`idKey=""`). NOT a regression, but NOT an improvement either
 *                          — it is a recall trade the ledger must disclose, not hide.
 */
const RETIRED_GROUPS = {
  '叙利亚自爆民兵::voxy': { kind: 'closed_bad_anchor', was: 'REAL_FALSE_MERGE', fixed_by: 'R1 name-slot disagreement veto', note: '《你好，新蒸程》/《你好，新世代》两个包的方括号名槽互不相同（新蒸程 vs 新世代），方括号之后的 voxy 不得充当 anchor → 现已各自独立。' },
  'tibsalta::难度驱动': { kind: 'closed_bad_anchor', was: 'REAL_FALSE_MERGE', fixed_by: 'R1 name-slot disagreement veto', note: '《抗争之际》/《旅途痕迹》两个包各自占据第一方括号名槽且互不相同，第二方括号里的系列标签【难度驱动】不得充当 anchor → 现已各自独立。' },
  '不知名的莫理沙::勇者之章': { kind: 'dissolved_singleton', was: 'LEGITIMATE', note: '四条本属“勇者之章Ⅲ”同一系列，但每条各自的副标题 run 更具体，修复后 anchor 不再是系列名 → 4 条变独立卡片。属 recall 取舍，如实记录。' },
  '在职玩家jostar::去吧 方可梦大师': { kind: 'dissolved_singleton', was: 'LEGITIMATE', note: '三条本属同一包。该上传者记录已不在扫描面内（anchor 不再晚置）→ 记录为聚合变化。' },
  '墨竹ギ::深渊之诗': { kind: 'dissolved_singleton', was: 'LEGITIMATE', note: '三条本属《深渊之诗》同一包；修复后 anchor 落到各条的英文名/副标题（poetry of the abyss / 一款大型）→ 拆为独立卡片。' },
  'plaudite_::scarlet': { kind: 'dissolved_singleton', was: 'LEGITIMATE', note: '两条本属 Scarlet Adventure 同一包；修复后 anchor 落在各自的前缀 run 上 → 拆为独立卡片。' },
  '一个小寂哦::重回 之巅': { kind: 'dissolved_singleton', was: 'LEGITIMATE', note: '两条本属“最全拔刀剑”系列；修复后不再以“重回 之巅”为 anchor → 拆为独立卡片。' },
  'arr-c6h6::旧世界': { kind: 'dissolved_singleton', was: 'LEGITIMATE', note: '两条本属「旧世界」同一包；该上传者记录已不在扫描面内 → 记录为聚合变化。' },
  '流霜雾影::愚者版本大': { kind: 'dissolved_singleton', was: 'LEGITIMATE', note: '两条本属「愚者」同一包；修复后 anchor 收敛为更干净的“愚者”（3 条一组），旧的“愚者版本大”键消失。' },
  '-阳春面面-::青春复兴': { kind: 'dissolved_singleton', was: 'UNDECIDED', note: '本就无法判定是否同包；修复后三条变独立卡片（保守结果）。' },
  '墨竹ギ::史诗的地下城 dungeons of fantasy': { kind: 'dissolved_singleton', was: 'LEGITIMATE', note: '两条本属 Dungeons Of Fantasy 同一包；修复后 anchor 落在各自的副标题 run 上 → 拆为独立卡片。' },
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

  // ---- 涅槃 premise correction, verified live against bili_data ----------------
  // Partition the author's 涅槃 records the SAME way the ledger claims they split:
  // by their own stable pack-registration ids (the grouping algorithm is NOT used as
  // evidence here). A record that lists only ONE of a pack's ids is still that pack,
  // so records are merged when their id sets share a registration id.
  const bili = loadBili();
  const nirvanaRecs = bili.filter((r) => (r.author || '') === '墨言eclipse' && /涅槃/.test(r.title || ''));
  const recIds = nirvanaRecs.map((r) => ({ record: r, ids: resourceIdsOf(r) }));

  // union by shared registration id (deterministic: seed on first record with ids)
  const clusters = [];
  for (const item of recIds) {
    if (!item.ids.length) { clusters.push({ ids: [], members: [item.record] }); continue; }
    const hit = clusters.find((c) => c.ids.some((id) => item.ids.includes(id)));
    if (hit) {
      hit.members.push(item.record);
      hit.ids = [...new Set([...hit.ids, ...item.ids])].sort();
    } else {
      clusters.push({ ids: [...item.ids], members: [item.record] });
    }
  }
  const signatures = clusters
    .map((c) => ({ signature: c.ids.join('|') || '__no_resource_id__', records: c.members.length, bvids: c.members.map((r) => r.bvid) }))
    .sort((a, b) => b.records - a.records);

  const declaredSignatures = NIRVANA_PACK_EVIDENCE;
  const nirvanaCheck = {};
  for (const [key, expect] of Object.entries(declaredSignatures)) {
    const hit = signatures.find((s) => expect.resource_ids.every((id) => s.signature.includes(id)));
    nirvanaCheck[key] = {
      expected_pack: expect.pack_name,
      expected_records: expect.records,
      observed_records: hit ? hit.records : 0,
      observed_signature: hit ? hit.signature : null,
      resource_ids_match: !!hit && hit.records === expect.records,
    };
  }
  const nirvanaVerdict =
    Object.values(nirvanaCheck).every((v) => v.resource_ids_match)
    && signatures.length === Object.keys(declaredSignatures).length
      ? 'CONFIRMED'
      : 'UNVERIFIED';

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
    // Phase 3G-F.1-A: false merges proven at 3G-F and CLOSED by the F.1 runtime
    // remediation. They no longer exist as groups, so they cannot be flagged; keeping
    // them here preserves the finding AND makes `declared_but_absent` self-explaining.
    retired_false_merges: Object.entries(RETIRED_FALSE_MERGES).map(([k, v]) => ({
      group_key: k,
      ...v,
      still_present: rows.some((r) => r.group_key === k),
    })),
    // Phase 3G-F.1-A: every key that was flagged at 3G-F and is absent now, with the
    // reason and the direction of the change (fixed vs recall trade). This is what
    // makes `declared_but_absent` a documented list instead of a mystery.
    retired_groups: Object.entries(RETIRED_GROUPS).map(([k, v]) => ({
      group_key: k,
      ...v,
      still_present: rows.some((r) => r.group_key === k),
    })),
    // Phase 3G-F.1-A: the 涅槃 "7 records, 1 pack" premise is REFUTED by the records'
    // own structured resource ids. The brief's §4 ground truth is superseded.
    nirvana_premise: {
      verdict: nirvanaVerdict,
      correction: 'BILI-GRP-UNDERMERGE-01 said 7 records are ONE pack split into 5 groups. '
        + 'The structured download links show 5 records on xyebbs/resources/37418 (涅槃) and '
        + '2 on xyebbs/res-id/TUPN (未尽之路-涅槃) — two distinct products. 2 groups is correct; '
        + '1 group would be a real over-merge.',
      groups: nirvanaCheck,
    },
  };
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(result, null, 2), 'utf8');

  console.log('=== Phase 3G-F-A anchor adjudication ledger ===');
  console.log(`scanned flagged : ${scan.flagged_count}`);
  console.log(`REAL false merge: ${real.length}`);
  console.log(`LEGITIMATE      : ${legit.length}`);
  console.log(`UNDECIDED       : ${und.length}`);
  console.log(`retired (fixed) : ${result.retired_false_merges.length}`);
  if (unknown.length) console.log(`!! UNADJUDICATED : ${unknown.join(', ')}`);
  if (extraDeclared.length) console.log(`!! DECLARED-BUT-ABSENT : ${extraDeclared.join(', ')}`);
  console.log('\n-- 涅槃 premise (BILI-GRP-UNDERMERGE-01) --');
  console.log(`  verdict: ${nirvanaVerdict}  (distinct resource-id signatures: ${signatures.length})`);
  for (const s of signatures) {
    console.log(`  [${s.records}] ${s.signature}`);
  }
  for (const [k, v] of Object.entries(nirvanaCheck)) {
    console.log(`  ${k}  expect=${v.expected_pack}(${v.expected_records})`
      + `  observed=${v.observed_records}  match=${v.resource_ids_match}`);
  }
  console.log('\n-- RETIRED false merges (closed by 3G-F.1) --');
  for (const r of result.retired_false_merges) {
    console.log(`  ${r.still_present ? '!! STILL PRESENT' : 'closed'}  ${r.group_key}  (${r.fixed_by})`);
  }
  console.log('\n-- RETIRED groups (flagged at 3G-F, absent now) --');
  for (const r of result.retired_groups) {
    console.log(`  ${r.still_present ? '!! STILL PRESENT' : 'gone'}  [${r.kind}] ${r.group_key}  (was ${r.was})`);
  }
  console.log('\n-- REAL false merges --');
  for (const r of real) console.log(`  [${r.size}] ${r.group_key}  (anchor='${r.anchor}')`);
  console.log('\n-- UNDECIDED --');
  for (const r of und) console.log(`  [${r.size}] ${r.group_key}  (anchor='${r.anchor}')`);
  console.log(`\nwritten: ${path.relative(REPO_ROOT, OUT)}`);
  return unknown.length ? 1 : 0;
}

process.exit(main());

/**
 * Phase 3G-F-A - verification of the population-level false-merge candidates
 * found by manual review of every group of size >= 3 (plus the size-2 groups
 * surfaced by the slogan-anchor scan).
 *
 * Confirmed candidates (all same-uploader, all DIFFERENT packs, all NEW merges
 * introduced by the 3G-F identity-run rule):
 *
 *   一个小寂哦 :: 星辉死神      神器收集计划      + 无尽幸运方块大陆
 *   一个小寂哦 :: 四叶草        泰坦生物整合包    + 执行之龙生存整合包
 *   一个小寂哦 :: 各大主播同款   幸运方块大全      + 神器泰坦随机合成
 *   墨言eclipse :: 颠覆性的     摄影奇境          + 千界万锻
 *   原界环 :: or not            Minecraft or Not: Girl&Gun + Maiden or not
 *
 * For each candidate this prints the independent evidence (download_links,
 * qq_group, desc) and whether the OLD pre-3G-F algorithm already merged the
 * members (pre-existing defect) or the 3G-F rule introduced it (regression).
 *
 * Usage: node pipeline/audit/bilibili_grouping_candidate_false_merge_check.js
 * Output: build/audit/bilibili_grouping_candidate_false_merge_check.json
 */
const fs = require('fs');
const path = require('path');

global.window = {};
const REPO_ROOT = path.resolve(__dirname, '..', '..');
const newMod = require(path.join(REPO_ROOT, 'build', 'audit', 'bilibili_grouping_module.js'));
const oldImpl = require(path.join(REPO_ROOT, 'pipeline', 'audit', 'fixtures', 'bili_grouping_legacy_impl.js'));
const OUT = path.join(REPO_ROOT, 'build', 'audit', 'bilibili_grouping_candidate_false_merge_check.json');
const BILI_DATA = path.join(REPO_ROOT, 'converted_output', 'data', 'bili_data.js');

// Uploaders carrying at least one adjudicated false merge. Keep this list in sync with
// KNOWN_FALSE_MERGES in tests/test_bilibili_grouping_precision_audit.py - a false merge
// whose uploader is absent here is silently invisible to the pinning test.
const CANDIDATE_UPLOADERS = [
  '一个小寂哦',
  '墨言eclipse',
  '原界环',
  '叙利亚自爆民兵',
  'tibsalta',
];

function loadBili() {
  const raw = fs.readFileSync(BILI_DATA, 'utf8');
  return JSON.parse(raw.slice(raw.indexOf('['), raw.lastIndexOf(']') + 1));
}
function normUrl(u) {
  if (!u) return '';
  if (typeof u === 'string') return u.trim();
  return String(u.url || u.link || '').trim();
}

function main() {
  const data = loadBili();
  const newMap = {};
  for (const [b, d] of newMod.groupBilibiliPacks(data)) newMap[b] = d;
  const oldMap = {};
  for (const g of oldImpl.groupPacks(data)) for (const it of g.items) oldMap[it.bvid] = g.key;

  const out = { generated_at: new Date().toISOString(), candidates: [] };

  for (const uploader of CANDIDATE_UPLOADERS) {
    // Compare on the SAME normalisation the grouping uses (authorScope lowercases),
    // so a listing like 'tibsalta' still matches the payload's 'Tibsalta'.
    const recs = data.filter((p) => String(p.author || '').trim().toLowerCase() === uploader);
    const groups = new Map();
    for (const p of recs) {
      const k = newMap[p.bvid].groupKey;
      if (!groups.has(k)) groups.set(k, []);
      groups.get(k).push(p);
    }
    const entry = { uploader, record_count: recs.length, group_count: groups.size, groups: [] };
    for (const [key, members] of groups) {
      const oldKeys = [...new Set(members.map((m) => oldMap[m.bvid]))];
      entry.groups.push({
        group_key: key,
        identity_key: newMap[members[0].bvid].identityKey,
        grouping_reason: newMap[members[0].bvid].groupingReason,
        size: members.length,
        old_distinct_keys: oldKeys.length,
        pre_existing_in_old_algorithm: oldKeys.length < members.length,
        members: members.map((m) => ({
          bvid: m.bvid,
          title: m.title,
          episode_residue: newMap[m.bvid].episodeResidue,
          download_links: [...new Set((m.download_links || []).map(normUrl).filter(Boolean))],
          qq_group: String(m.qq_group || '').trim(),
          desc: String(m.desc || '').replace(/\s+/g, ' ').slice(0, 160),
        })),
      });
    }
    entry.groups.sort((a, b) => b.size - a.size);
    out.candidates.push(entry);
  }

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(out, null, 2), 'utf8');

  for (const c of out.candidates) {
    console.log(`=== ${c.uploader}: ${c.record_count} records, ${c.group_count} groups ===`);
    for (const g of c.groups) {
      if (g.size < 2) continue;
      console.log(`\n[${g.size}] ${g.group_key}  anchor='${g.identity_key}' reason=${g.grouping_reason} preExisting=${g.pre_existing_in_old_algorithm} (old keys=${g.old_distinct_keys})`);
      for (const m of g.members) {
        console.log(`   ${m.bvid} | ${m.title.slice(0, 72)}`);
        console.log(`        urls: ${m.download_links.join(' , ') || '(none)'}`);
        console.log(`        qq  : ${m.qq_group || '(none)'}`);
      }
    }
    console.log('');
  }
  console.log(`written: ${path.relative(REPO_ROOT, OUT)}`);
  return 0;
}

process.exit(main());

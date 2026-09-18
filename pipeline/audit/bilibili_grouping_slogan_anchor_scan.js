/**
 * Phase 3G-F-A - "slogan anchor" scan.
 *
 * Manual review of the 55 groups of size >= 3 found that the 3G-F identity-run
 * rule can anchor a group on a SLOGAN / boss name / item name instead of a pack
 * name. Example (uploader 一个小寂哦):
 *
 *   anchor "星辉死神"  -> 神器收集计划  + 无尽幸运方块大陆   (two different packs)
 *   anchor "四叶草"    -> 泰坦生物整合包 + 执行之龙生存整合包 (two different packs)
 *   anchor "各大主播同款" -> 幸运方块大全 + 神器泰坦随机合成   (two different packs)
 *
 * Signature: the anchor sits LATE in the key, and the tokens BEFORE it differ
 * between members - i.e. the members share a tail slogan, not a leading name.
 * (Chinese MC pack titles lead with the pack name; slogans trail.)
 *
 * This is a REVIEW-LIST GENERATOR, not a verdict. It deliberately over-reports:
 * some flagged groups are legitimate (the pack name itself may sit after the
 * anchor). Every flagged group is emitted with its members so it can be judged.
 *
 * Usage: node pipeline/audit/bilibili_grouping_slogan_anchor_scan.js
 * Output: build/audit/bilibili_grouping_slogan_anchor_scan.json
 */
const fs = require('fs');
const path = require('path');

global.window = {};
const REPO_ROOT = path.resolve(__dirname, '..', '..');
const newMod = require(path.join(REPO_ROOT, 'build', 'audit', 'bilibili_grouping_module.js'));
const packName = require(path.join(REPO_ROOT, 'build', 'audit', 'pack_name_module.js'));
const oldImpl = require(path.join(REPO_ROOT, 'pipeline', 'audit', 'fixtures', 'bili_grouping_legacy_impl.js'));
const OUT = path.join(REPO_ROOT, 'build', 'audit', 'bilibili_grouping_slogan_anchor_scan.json');
const BILI_DATA = path.join(REPO_ROOT, 'converted_output', 'data', 'bili_data.js');

const MIN_ANCHOR_INDEX = 2;   // anchor must not be the first/second token
const MIN_DISTINCT_PREFIX = 2; // at least two different prefixes => tail slogan

function loadBili() {
  const raw = fs.readFileSync(BILI_DATA, 'utf8');
  return JSON.parse(raw.slice(raw.indexOf('['), raw.lastIndexOf(']') + 1));
}

/** index of the anchor token run inside the key, or -1 */
function anchorIndex(key, anchor) {
  const kt = key.split(' ').filter(Boolean);
  const at = anchor.split(' ').filter(Boolean);
  if (!at.length) return -1;
  for (let i = 0; i + at.length <= kt.length; i++) {
    let ok = true;
    for (let j = 0; j < at.length; j++) if (kt[i + j] !== at[j]) { ok = false; break; }
    if (ok) return i;
  }
  return -1;
}

function main() {
  const data = loadBili();
  const dec = {};
  for (const [b, d] of newMod.groupBilibiliPacks(data)) dec[b] = d;
  const oldMap = {};
  for (const g of oldImpl.groupPacks(data)) for (const it of g.items) oldMap[it.bvid] = g.key;

  const groups = new Map();
  for (const p of data) {
    const k = dec[p.bvid].groupKey;
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k).push(p);
  }

  const flagged = [];
  for (const [key, members] of groups) {
    if (members.length < 2) continue;
    const anchor = dec[members[0].bvid].identityKey;
    if (!anchor) continue; // fallback exact/substring key path, not identity-run

    const rows = members.map((m) => {
      // the clean key the module actually matched on
      const k = packName.cleanPackKey(m.title);
      const i = anchorIndex(k, anchor);
      const kt = k.split(' ').filter(Boolean);
      return { m, key: k, idx: i, prefix: i >= 0 ? kt.slice(0, i).join(' ') : null };
    });
    const idxs = rows.map((r) => r.idx);
    const distinctPrefixes = [...new Set(rows.map((r) => r.prefix).filter((p) => p !== null && p !== ''))];
    const allLate = idxs.every((i) => i >= MIN_ANCHOR_INDEX);

    if (allLate && distinctPrefixes.length >= MIN_DISTINCT_PREFIX) {
      const oldKeys = new Set(members.map((m) => oldMap[m.bvid]));
      flagged.push({
        group_key: key,
        anchor,
        size: members.length,
        anchor_indices: idxs,
        distinct_prefixes: distinctPrefixes,
        newly_merged: oldKeys.size > 1,
        members: rows.map((r) => ({ bvid: r.m.bvid, title: r.m.title, clean_key: r.key, anchor_index: r.idx, prefix: r.prefix, residue: dec[r.m.bvid].episodeResidue })),
      });
    }
  }

  flagged.sort((a, b) => (b.distinct_prefixes.length - a.distinct_prefixes.length) || (b.size - a.size));

  const result = {
    generated_at: new Date().toISOString(),
    payload_records: data.length,
    heuristic: {
      min_anchor_index: MIN_ANCHOR_INDEX,
      min_distinct_prefixes: MIN_DISTINCT_PREFIX,
      note: 'review-list generator, over-reports by design',
    },
    flagged_count: flagged.length,
    flagged_newly_merged_count: flagged.filter((f) => f.newly_merged).length,
    flagged,
  };

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(result, null, 2), 'utf8');

  console.log('=== Phase 3G-F-A slogan-anchor scan ===');
  console.log(`flagged groups: ${flagged.length} (newly merged by 3G-F: ${result.flagged_newly_merged_count})`);
  for (const f of flagged) {
    console.log(`  [${f.size}] anchor='${f.anchor}' key=${f.group_key} | prefixes=${f.distinct_prefixes.length} | new=${f.newly_merged}`);
  }
  console.log(`written: ${path.relative(REPO_ROOT, OUT)}`);
  return 0;
}

process.exit(main());

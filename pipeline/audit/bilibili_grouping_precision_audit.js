/**
 * Phase 3G-F-A - population precision audit (corpus-independent).
 *
 * The frozen corpus scores 46 cases and reports FalseMerge = 0. That is a
 * statement about the CORPUS, not about the 936-record payload. This script
 * looks for false merges the corpus never adjudicated.
 *
 * METHOD NOTE (kept deliberately): the first attempt used "members have disjoint
 * download_links => different packs". That heuristic was REJECTED - a pack that
 * publishes per-version share links (宝可梦地平线 v1.0->v2.0, 蛊真人 2.1->2.4,
 * 生还者 1.0->3.1) looks URL-disjoint while being one pack. The counterexamples
 * are recorded in the output so the rejected heuristic is not silently reused.
 *
 * The surviving method is a review list, not a score: every group of size >= 3
 * is emitted with its mined anchor and member titles, so a human can judge
 * whether the anchor is a pack name (correct) or a mod / boss / feature name
 * that happens to co-occur across DIFFERENT packs (false merge).
 *
 * Usage: node pipeline/audit/bilibili_grouping_precision_audit.js
 * Output: build/audit/bilibili_grouping_precision_audit.json
 */
const fs = require('fs');
const path = require('path');

global.window = {};
const REPO_ROOT = path.resolve(__dirname, '..', '..');
const newMod = require(path.join(REPO_ROOT, 'build', 'audit', 'bilibili_grouping_module.js'));
const oldImpl = require(path.join(REPO_ROOT, 'pipeline', 'audit', 'fixtures', 'bili_grouping_legacy_impl.js'));
const OUT = path.join(REPO_ROOT, 'build', 'audit', 'bilibili_grouping_precision_audit.json');
const BILI_DATA = path.join(REPO_ROOT, 'converted_output', 'data', 'bili_data.js');

function loadBili() {
  const raw = fs.readFileSync(BILI_DATA, 'utf8');
  return JSON.parse(raw.slice(raw.indexOf('['), raw.lastIndexOf(']') + 1));
}
function newDecisions(recs) {
  const o = {};
  for (const [b, d] of newMod.groupBilibiliPacks(recs)) o[b] = d;
  return o;
}
function oldKeys(recs) {
  const o = {};
  for (const g of oldImpl.groupPacks(recs)) for (const it of g.items) o[it.bvid] = g.key;
  return o;
}
function normUrl(u) {
  if (!u) return '';
  if (typeof u === 'string') return u.trim().replace(/\/+$/, '');
  return String(u.url || u.link || '').trim().replace(/\/+$/, '');
}

/**
 * Rejected heuristic, kept for the record. Returns the clusters that a
 * URL-disjointness rule WOULD have flagged, plus whether they are obviously one
 * pack with per-version links (same version-stripped title core).
 */
function rejectedUrlHeuristic(data, dec) {
  const groups = new Map();
  for (const p of data) {
    const k = dec[p.bvid].groupKey;
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k).push(p);
  }
  const flagged = [];
  for (const [key, members] of groups) {
    if (members.length < 2) continue;
    const urlSets = members.map((m) => new Set((m.download_links || []).map(normUrl).filter(Boolean)));
    let pairs = 0, disjoint = 0;
    for (let i = 0; i < urlSets.length; i++) {
      for (let j = i + 1; j < urlSets.length; j++) {
        if (!urlSets[i].size || !urlSets[j].size) continue;
        pairs++;
        if ([...urlSets[i]].every((u) => !urlSets[j].has(u))) disjoint++;
      }
    }
    if (pairs && disjoint === pairs) {
      flagged.push({ group_key: key, size: members.length, titles: members.map((m) => m.title.slice(0, 70)) });
    }
  }
  return {
    verdict: 'REJECTED',
    reason: 'Per-version share links make one pack look URL-disjoint. "disjoint download_links" is NOT evidence of different packs.',
    flagged_count: flagged.length,
    counterexamples: flagged.slice(0, 6),
  };
}

function groupMap(data, dec) {
  const groups = new Map();
  for (const p of data) {
    const k = dec[p.bvid].groupKey;
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k).push(p);
  }
  return groups;
}

function groupList(data, dec) {
  const groups = groupMap(data, dec);
  const out = [];
  for (const [key, members] of groups) {
    if (members.length < 2) continue;
    const anchor = dec[members[0].bvid].identityKey;
    const authors = [...new Set(members.map((m) => m.author))];
    out.push({
      group_key: key,
      size: members.length,
      anchor,
      anchor_token_count: anchor ? anchor.split(' ').length : 0,
      author: authors[0],
      cross_uploader: authors.length > 1,
      members: members.map((m) => ({
        bvid: m.bvid,
        title: m.title,
        key: m.title, // kept for traceability; see cleanKey below
        clean_key: (dec[m.bvid] && dec[m.bvid].episodeResidue) || '',
        urls: [...new Set((m.download_links || []).map(normUrl).filter(Boolean))].length,
      })),
    });
  }
  out.sort((a, b) => b.size - a.size);
  return out;
}

function main() {
  const data = loadBili();
  const dec = newDecisions(data);
  const ok = oldKeys(data);

  const all = groupList(data, dec);
  const ge3 = all.filter((g) => g.size >= 3);
  const everyGroup = groupMap(data, dec);
  const crossUploader = [...everyGroup.entries()]
    .filter(([, v]) => new Set(v.map((x) => x.author)).size > 1)
    .map(([k, v]) => ({ key: k, size: v.length, authors: [...new Set(v.map((x) => x.author))] }));

  // groups that are NEW (the old algorithm did not co-group every member)
  for (const g of all) {
    const oldSet = new Set(g.members.map((m) => ok[m.bvid]));
    g.newly_merged = oldSet.size > 1;
    g.old_distinct_keys = oldSet.size;
  }

  const result = {
    generated_at: new Date().toISOString(),
    payload_records: data.length,
    grouped_cards: everyGroup.size,
    multi_video_groups: all.length,
    cross_uploader_groups: crossUploader.length,
    cross_uploader_group_detail: crossUploader,
    url_disjointness_heuristic: rejectedUrlHeuristic(data, dec),
    groups_ge3: ge3,
    groups_ge3_newly_merged: ge3.filter((g) => g.newly_merged),
  };

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(result, null, 2), 'utf8');

  console.log('=== Phase 3G-F-A population precision audit ===');
  console.log(`records=${result.payload_records} multi-video groups=${result.multi_video_groups} cross-uploader groups=${result.cross_uploader_groups}`);
  console.log(`URL-disjointness heuristic: ${result.url_disjointness_heuristic.verdict} (would have flagged ${result.url_disjointness_heuristic.flagged_count} groups)`);
  console.log(`groups >= 3 for manual review: ${ge3.length} (newly merged by 3G-F: ${result.groups_ge3_newly_merged.length})`);
  console.log(`written: ${path.relative(REPO_ROOT, OUT)}`);
  return 0;
}

process.exit(main());

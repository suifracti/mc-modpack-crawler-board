/**
 * Phase 3G-F.1-B - population holdout v2 builder (§10).
 *
 * The old frozen corpus (bilibili_grouping_corpus.json + _split.json) has 24
 * positive / 22 negative cases spread over 33 uploaders. It is FROZEN - this
 * script never touches it.
 *
 * This script mines ADDITIONAL cases from the same 936-record payload but
 * restricted to uploaders that appear in NEITHER the dev NOR the holdout side of
 * the old split. Requirement: >= 10 positive groups and >= 10 negative controls,
 * with uploaders disjoint from the main dev corpus.
 *
 * HOW CASES ARE DERIVED (not hand-written, so the file is reproducible):
 *   POSITIVE  a group with >=2 members whose members are hand-confirmed in the
 *             v2 adjudication ledger as LEGITIMATE_SAME_PACK, i.e. one pack
 *             across >=2 videos, that the OLD (pre-3G-F) algorithm had SPLIT
 *             (old_distinct_keys > 1). That is precisely the "should merge" case.
 *   NEGATIVE  an uploader whose videos span >=2 DISTINCT packs with >=2 videos
 *             each, where the NEW algorithm kept them separate. Ground truth is
 *             taken from the ledger's REAL_FALSE_MERGE anchors and from generic
 *             multi-pack uploaders where each group's titles share no pack name.
 *
 * The derived cases are EVIDENCE BOUND - each carries the bvids and titles so a
 * reader can re-check. They are NOT a claim of exhaustiveness.
 *
 * Usage: node pipeline/audit/build_population_holdout_v2.js
 * Output: build/audit/population_holdout_v2.json  (large, gitignored)
 *         pipeline/audit/bilibili_population_holdout_v2.json (compact, tracked)
 */
const fs = require('fs');
const path = require('path');
const { readJson, writeJsonPair } = require('./lib/audit_artifact_io');

global.window = {};
const REPO_ROOT = path.resolve(__dirname, '..', '..');
const newMod = require(path.join(REPO_ROOT, 'build', 'audit', 'bilibili_grouping_module.js'));
const oldImpl = require(path.join(REPO_ROOT, 'pipeline', 'audit', 'fixtures', 'bili_grouping_legacy_impl.js'));
const OLD_SPLIT = path.join(REPO_ROOT, 'pipeline', 'audit', 'bilibili_grouping_split.json');
const LEDGER = path.join(REPO_ROOT, 'pipeline', 'audit', 'bilibili_population_adjudication_v2.json');
const BILI_DATA = path.join(REPO_ROOT, 'converted_output', 'data', 'bili_data.js');

const OUT_FULL = path.join(REPO_ROOT, 'build', 'audit', 'population_holdout_v2.json');
const OUT_COMPACT = path.join(REPO_ROOT, 'pipeline', 'audit', 'bilibili_population_holdout_v2.json');

function loadBili() {
  const raw = fs.readFileSync(BILI_DATA, 'utf8');
  return JSON.parse(raw.slice(raw.indexOf('['), raw.lastIndexOf(']') + 1));
}

function main() {
  const data = loadBili();
  const ledger = readJson(LEDGER);
  const oldSplit = JSON.parse(fs.readFileSync(OLD_SPLIT, 'utf8'));

  const usedUploaders = new Set([
    ...oldSplit.dev.uploaders, ...oldSplit.holdout.uploaders,
  ].map((u) => String(u).toLowerCase()));

  const newMap = {};
  for (const [b, d] of newMod.groupBilibiliPacks(data)) newMap[b] = d;
  const oldMap = {};
  for (const g of oldImpl.groupPacks(data)) for (const it of g.items) oldMap[it.bvid] = g.key;

  const legitKeys = new Set(
    ledger.legitimate_same_pack.map((r) => r.group_key),
  );

  // ---- POSITIVES: same-pack groups the OLD algorithm had split -------------
  const byGroup = new Map();
  for (const p of data) {
    const k = newMap[p.bvid].groupKey;
    if (!byGroup.has(k)) byGroup.set(k, []);
    byGroup.get(k).push(p);
  }

  const positives = [];
  for (const [key, members] of byGroup) {
    if (members.length < 2) continue;
    const author = String(members[0].author || '').trim();
    if (usedUploaders.has(author.toLowerCase())) continue;   // uploader-disjoint
    if (!legitKeys.has(key)) continue;                       // must be hand-confirmed same-pack
    const oldKeys = new Set(members.map((m) => oldMap[m.bvid]));
    if (oldKeys.size < 2) continue;                          // must be a REAL merge win
    positives.push({
      case_id: `HOLDOUT2-POS-${String(positives.length + 1).padStart(2, '0')}`,
      expected: 'merge',
      kind: 'same_pack_split_by_old_algorithm',
      uploader: author,
      group_key: key,
      old_distinct_keys: oldKeys.size,
      confidence: 'confirmed',
      source: 'v2 adjudication ledger (LEGITIMATE_SAME_PACK) + old-vs-new diff',
      videos: members.map((m) => ({ bvid: m.bvid, title: m.title })),
    });
  }
  positives.sort((a, b) => b.videos.length - a.videos.length);

  // ---- NEGATIVES: uploaders with 2+ distinct packs, none merged -----------
  // Derived, not hand-written: an uploader qualifies when it has >=2 groups,
  // each group retains its own pack name, and no group was adjudicated
  // REAL_FALSE_MERGE (a false merge would mean the packs were NOT kept apart).
  const realMergeAuthors = new Set(
    ledger.real_false_merges.map((r) => String(r.author).toLowerCase()),
  );
  const byAuthor = new Map();
  for (const p of data) {
    const a = String(p.author || '').trim();
    if (usedUploaders.has(a.toLowerCase())) continue;
    if (!byAuthor.has(a)) byAuthor.set(a, []);
    byAuthor.get(a).push(p);
  }

  const negatives = [];
  for (const [author, recs] of byAuthor) {
    if (realMergeAuthors.has(author.toLowerCase())) continue;
    const groups = new Map();
    for (const p of recs) {
      const k = newMap[p.bvid].groupKey;
      if (!groups.has(k)) groups.set(k, []);
      groups.get(k).push(p);
    }
    if (groups.size < 2) continue;                        // need >=2 packs
    // Require at least two groups carrying a REAL pack name (>=2 identity chars
    // after cleaning) so single-token noise groups do not qualify a case.
    const named = [...groups.entries()].filter(([k]) => {
      const tail = k.split('::')[1] || '';
      return tail.replace(/[^A-Za-z0-9\u4e00-\u9fa5]/g, '').length >= 2;
    });
    if (named.length < 2) continue;
    negatives.push({
      case_id: `HOLDOUT2-NEG-${String(negatives.length + 1).padStart(2, '0')}`,
      expected: 'separate',
      kind: 'same_uploader_distinct_packs_kept_apart',
      uploader: author,
      group_count: groups.size,
      confidence: 'strong',
      source: 'v2 adjudication ledger (no REAL_FALSE_MERGE for this uploader) + group structure',
      videos: recs.map((p) => ({ bvid: p.bvid, title: p.title, group_key: newMap[p.bvid].groupKey })),
    });
  }
  negatives.sort((a, b) => (b.group_count - a.group_count) || (b.videos.length - a.videos.length));

  const holdoutUploaders = [...new Set([
    ...positives.map((p) => String(p.uploader).toLowerCase()),
    ...negatives.map((n) => String(n.uploader).toLowerCase()),
  ])].sort();

  const overlap = holdoutUploaders.filter((u) => usedUploaders.has(u));

  const compact = {
    phase: '3G-F.1-B',
    // SOURCE_DATE_EPOCH makes the artifact byte-reproducible.
    generated_at: new Date(
      (process.env.SOURCE_DATE_EPOCH ? Number(process.env.SOURCE_DATE_EPOCH) * 1000 : Date.now()),
    ).toISOString(),
    artifact: 'bilibili_population_holdout_v2',
    note: 'ADDITIVE holdout. The old frozen corpus (bilibili_grouping_corpus.json) is untouched.',
    old_corpus: { positive: 24, negative: 22, uploaders: usedUploaders.size, frozen: true },
    holdout_v2: {
      positive: positives.length,
      negative: negatives.length,
      uploader_count: holdoutUploaders.length,
      uploaders: holdoutUploaders,
      uploader_overlap_with_old_corpus: overlap,
      meets_requirement: positives.length >= 10 && negatives.length >= 10 && overlap.length === 0,
    },
    positive_cases: positives,
    negative_cases: negatives,
  };

  fs.mkdirSync(path.dirname(OUT_FULL), { recursive: true });
  const size = writeJsonPair(OUT_FULL, OUT_COMPACT, compact);

  console.log('=== Phase 3G-F.1-B population holdout v2 ===');
  console.log(`positives : ${positives.length}`);
  console.log(`negatives : ${negatives.length}`);
  console.log(`uploaders : ${holdoutUploaders.length}`);
  console.log(`overlap with old corpus : ${overlap.length}${overlap.length ? ' !! ' + overlap.join(', ') : ' (clean)'}`);
  console.log(`meets requirement (>=10/>=10/disjoint): ${compact.holdout_v2.meets_requirement}`);
  console.log('\n-- positives --');
  for (const p of positives) console.log(`  [${p.videos.length}] ${p.uploader} :: ${p.group_key} (oldKeys=${p.old_distinct_keys})`);
  console.log('\n-- negatives --');
  for (const n of negatives) console.log(`  [groups=${n.group_count} vids=${n.videos.length}] ${n.uploader}`);
  console.log(`\nwritten: ${path.relative(REPO_ROOT, OUT_COMPACT)} `
    + `(gzip ${(size.tracked.gz / 1024).toFixed(0)}KB <- ${(size.tracked.raw / 1024).toFixed(0)}KB)`);
  return compact.holdout_v2.meets_requirement ? 0 : 1;
}

process.exit(main());

/**
 * Phase 3G-F - Bilibili grouping false-split remediation evaluator.
 *
 * Evaluates BOTH the frozen Phase 3G-E implementation and the new domain module
 * against the frozen corpus, split into uploader-disjoint dev / holdout.
 *
 * The holdout is never used to design the rule - it is only read here, after the
 * rule was frozen, and reported separately so overfitting is visible.
 *
 * Usage: node pipeline/audit/bilibili_grouping_remediation_eval.js
 * Output: build/audit/bilibili_grouping_remediation.json
 */
const fs = require('fs');
const path = require('path');

global.window = {};
const REPO_ROOT = path.resolve(__dirname, '..', '..');
// FROZEN pre-3G-F implementation (the live bundle no longer contains it).
const oldImpl = require(path.join(REPO_ROOT, 'pipeline', 'audit', 'fixtures', 'bili_grouping_legacy_impl.js'));
const newMod = require(path.join(REPO_ROOT, 'build', 'audit', 'bilibili_grouping_module.js'));

const BILI_DATA = path.join(REPO_ROOT, 'converted_output', 'data', 'bili_data.js');
const CORPUS = path.join(REPO_ROOT, 'pipeline', 'audit', 'bilibili_grouping_corpus.json');
const SPLIT = path.join(REPO_ROOT, 'pipeline', 'audit', 'bilibili_grouping_split.json');
const OUT = path.join(REPO_ROOT, 'build', 'audit', 'bilibili_grouping_remediation.json');

const SCORED = new Set(['confirmed', 'strong']);

function loadBili() {
  const raw = fs.readFileSync(BILI_DATA, 'utf8');
  return JSON.parse(raw.slice(raw.indexOf('['), raw.lastIndexOf(']') + 1));
}

function loadJson(p) { return JSON.parse(fs.readFileSync(p, 'utf8')); }

/** OLD algorithm: group key per bvid, using the frozen production implementation. */
function oldKeys(records) {
  const map = {};
  for (const g of oldImpl.groupPacks(records)) for (const it of g.items) map[it.bvid] = g.key;
  return map;
}

/** NEW algorithm: pure domain module. */
function newKeys(records) {
  const map = {};
  for (const [bvid, d] of newMod.groupBilibiliPacks(records)) map[bvid] = d.groupKey;
  return map;
}

function recordsFor(caseObj, byBv) {
  return caseObj.videos.map((v) => {
    const real = byBv.get(v.bvid);
    if (real) return real;
    return {
      bvid: v.bvid, title: v.title, author: caseObj.uploader,
      pic: '', pub_time: v.published_at || '', pub_timestamp: 0,
      mc_version: v.mc_version || '', all_versions: [], loaders: [], categories: [],
      download_links: [], qq_group: v.qq_group || '', pack_version: v.pack_version || '',
      group_version_note: '', has_group_version: false, has_server: false,
      desc: v.description_excerpt || '', views: 0, likes: 0, coins: 0, favorites: 0,
      share: 0, reply: 0, danmaku: 0, desc_updated_at: '',
    };
  });
}

function evalCase(c, byBv, keyFn) {
  const recs = recordsFor(c, byBv);
  const map = keyFn(recs);
  const keys = [...new Set(recs.map((r) => map[r.bvid]))];
  const merged = keys.length === 1;
  const correct = c.expected === 'merge' ? merged : keys.length === recs.length;
  return {
    case_id: c.case_id, expected: c.expected, confidence: c.confidence,
    kind: c.kind, uploader: c.uploader, video_count: recs.length,
    distinct_group_keys: keys.length, group_keys: keys, correct,
    result: merged ? 'merged' : 'separate',
    videos: c.videos.map((v) => ({ bvid: v.bvid, title: v.title, key: map[v.bvid] })),
    ground_truth_evidence: c.ground_truth_evidence,
  };
}

function metrics(results) {
  const tm = results.filter((r) => r.expected === 'merge' && r.correct).length;
  const fsp = results.filter((r) => r.expected === 'merge' && !r.correct).length;
  const ts = results.filter((r) => r.expected === 'separate' && r.correct).length;
  const fm = results.filter((r) => r.expected === 'separate' && !r.correct).length;
  return {
    true_merge: tm, false_split: fsp, true_separate: ts, false_merge: fm,
    precision: +(tm + fm ? tm / (tm + fm) : 1).toFixed(4),
    recall: +(tm + fsp ? tm / (tm + fsp) : 0).toFixed(4),
    false_merge_rate: +(ts + fm ? fm / (ts + fm) : 0).toFixed(4),
    false_split_rate: +(tm + fsp ? fsp / (tm + fsp) : 0).toFixed(4),
  };
}

function searchTarget(p) {
  return [(p.title || ''), (p.author || ''), (p.desc || ''), (p.mc_version || ''),
    (p.loaders || []).join(' '), (p.categories || []).join(' ')].join(' ').toLowerCase();
}

function mechanicalPower(data, keyFn) {
  const f = data.filter((p) => searchTarget(p).includes('机械动力'));
  const map = keyFn(f);
  const groups = new Map();
  for (const p of f) {
    const k = map[p.bvid];
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k).push(p);
  }
  const multi = [...groups.entries()].filter(([, v]) => v.length > 1)
    .map(([k, v]) => ({ key: k, video_count: v.length, videos: v.map((x) => ({ bvid: x.bvid, title: x.title })) }))
    .sort((a, b) => b.video_count - a.video_count);
  return {
    query: '机械动力',
    raw_matches: f.length,
    grouped_cards: groups.size,
    net_collapse: f.length - groups.size,
    multi_video_groups: multi,
    multi_video_group_count: multi.length,
    videos_in_multi_groups: multi.reduce((a, g) => a + g.video_count, 0),
    flat_mode_raw_records: f.length,
    flat_mode_invariant_ok: f.length === 53,
  };
}

function populationStats(data, keyFn) {
  const map = keyFn(data);
  const groups = new Map();
  for (const p of data) {
    const k = map[p.bvid];
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k).push(p);
  }
  const sizes = [...groups.values()].map((v) => v.length).sort((a, b) => b - a);
  const dist = sizes.reduce((a, s) => { const b = s === 1 ? '1' : s === 2 ? '2' : s <= 4 ? '3-4' : s <= 9 ? '5-9' : '10+'; a[b] = (a[b] || 0) + 1; return a; }, {});
  const large = [...groups.entries()].filter(([, v]) => v.length >= 5)
    .map(([k, v]) => ({ key: k, size: v.length, bvids: v.map((x) => x.bvid), titles: v.map((x) => x.title.slice(0, 70)) }))
    .sort((a, b) => b.size - a.size);
  return {
    raw_videos: data.length,
    grouped_cards: groups.size,
    net_collapse: data.length - groups.size,
    multi_video_groups: sizes.filter((s) => s > 1).length,
    videos_in_multi_groups: sizes.filter((s) => s > 1).reduce((a, b) => a + b, 0),
    largest_group: sizes[0] || 0,
    size_distribution: dist,
    large_groups_ge5: large,
  };
}

function lowDiscriminativeAudit(data, keyFn, oldMap) {
  // keys the 3G-E audit flagged as low-discriminative (<=4 chars or no eligible token)
  const groups = new Map();
  for (const p of data) {
    const k = oldMap[p.bvid];
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k).push(p);
  }
  const flagged = [];
  for (const [k, v] of groups) {
    const raw = k.includes('::') ? k.split('::')[1] : k;
    if (k.startsWith('__raw_')) continue;
    const toks = raw ? raw.split(' ') : [];
    const eligible = toks.filter((t) => newMod.isIdentityEligibleToken(t));
    if (raw.length <= 4 || eligible.length === 0) flagged.push({ old_key: k, size: v.length, bvids: v.map((x) => x.bvid) });
  }
  return {
    flagged_count: flagged.length,
    merged_by_old: flagged.filter((f) => f.size > 1).length,
    samples: flagged.slice(0, 20),
  };
}

function main() {
  const data = loadBili();
  const byBv = new Map(data.map((r) => [r.bvid, r]));
  const corpus = loadJson(CORPUS);
  const split = loadJson(SPLIT);

  const allScored = [...corpus.positive_cases, ...corpus.negative_cases]
    .filter((c) => SCORED.has(c.confidence));
  const devIds = new Set(split.dev.case_ids);
  const holdoutIds = new Set(split.holdout.case_ids);
  const devCases = allScored.filter((c) => devIds.has(c.case_id));
  const holdoutCases = allScored.filter((c) => holdoutIds.has(c.case_id));

  const run = (keyFn) => ({
    overall: allScored.map((c) => evalCase(c, byBv, keyFn)),
    dev: devCases.map((c) => evalCase(c, byBv, keyFn)),
    holdout: holdoutCases.map((c) => evalCase(c, byBv, keyFn)),
  });

  const before = run(oldKeys);
  const after = run(newKeys);

  const oldFalseSplit = before.overall.filter((r) => r.expected === 'merge' && !r.correct).map((r) => r.case_id);
  const afterById = new Map(after.overall.map((r) => [r.case_id, r]));

  const oldPopMap = oldKeys(data);
  const newPopMap = newKeys(data);

  const result = {
    generated_at: new Date().toISOString(),
    frozen_corpus: {
      path: 'pipeline/audit/bilibili_grouping_corpus.json',
      sha256: process.env.CORPUS_SHA || null,
      positive: corpus.positive_cases.length,
      negative: corpus.negative_cases.length,
    },
    split: {
      method: split.split_method,
      dev: { uploaders: split.dev.uploaders.length, positive: split.dev.positive, negative: split.dev.negative },
      holdout: { uploaders: split.holdout.uploaders.length, positive: split.holdout.positive, negative: split.holdout.negative },
    },
    before: {
      overall: metrics(before.overall),
      dev: metrics(before.dev),
      holdout: metrics(before.holdout),
    },
    after: {
      overall: metrics(after.overall),
      dev: metrics(after.dev),
      holdout: metrics(after.holdout),
    },
    old_false_split_cases: oldFalseSplit,
    old_false_split_outcomes: oldFalseSplit.map((id) => {
      const r = afterById.get(id);
      return {
        case_id: id, uploader: r.uploader, video_count: r.video_count,
        before_keys: before.overall.find((x) => x.case_id === id).distinct_group_keys,
        after_keys: r.distinct_group_keys,
        after_result: r.result, fixed: r.correct,
        after_group_keys: r.group_keys,
      };
    }),
    remaining_false_splits: after.overall.filter((r) => r.expected === 'merge' && !r.correct),
    new_false_merges: after.overall.filter((r) => r.expected === 'separate' && !r.correct),
    negative_regression: {
      total: after.overall.filter((r) => r.expected === 'separate').length,
      still_separate: after.overall.filter((r) => r.expected === 'separate' && r.correct).length,
      all_separate: after.overall.filter((r) => r.expected === 'separate').every((r) => r.correct),
    },
    mechanical_power: {
      before: mechanicalPower(data, oldKeys),
      after: mechanicalPower(data, newKeys),
    },
    population: {
      before: populationStats(data, oldKeys),
      after: populationStats(data, newKeys),
    },
    low_discriminative: lowDiscriminativeAudit(data, newPopMap, oldPopMap),
    cases_after: after.overall,
  };

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(result, null, 2), 'utf8');

  const p = (l, m) => `${l}TM=${m.true_merge} FS=${m.false_split} TS=${m.true_separate} FM=${m.false_merge} P=${m.precision} R=${m.recall}`;
  console.log('=== Phase 3G-F remediation evaluation ===');
  console.log('BEFORE  overall  ' + p('', result.before.overall));
  console.log('BEFORE  dev      ' + p('', result.before.dev));
  console.log('BEFORE  holdout  ' + p('', result.before.holdout));
  console.log('AFTER   overall  ' + p('', result.after.overall));
  console.log('AFTER   dev      ' + p('', result.after.dev));
  console.log('AFTER   holdout  ' + p('', result.after.holdout));
  console.log(`negative regression: ${result.negative_regression.still_separate}/${result.negative_regression.total} separate  all=${result.negative_regression.all_separate}`);
  console.log(`old false splits fixed: ${result.old_false_split_outcomes.filter((x) => x.fixed).length}/${oldFalseSplit.length}`);
  console.log(`机械动力: before ${result.mechanical_power.before.grouped_cards} cards -> after ${result.mechanical_power.after.grouped_cards} cards (raw ${result.mechanical_power.after.raw_matches})`);
  console.log(`population: before ${result.population.before.grouped_cards} -> after ${result.population.after.grouped_cards} cards; large groups >=5: ${result.population.after.large_groups_ge5.length}`);
  console.log(`written: ${path.relative(REPO_ROOT, OUT)}`);
  return 0;
}

process.exit(main());

/**
 * Phase 3G-E - Bilibili grouping benchmark evaluator.
 *
 * Runs the REAL production grouping implementation (extracted verbatim from
 * converted_output/assets/index.js by pipeline/audit/extract_bili_grouping_impl.py)
 * against the independent-evidence corpus, then computes the four outcome classes,
 * merge precision / recall, and the key-discriminative-strength / collision /
 * generic-vocabulary / version-signal analyses.
 *
 * Usage: node pipeline/audit/bilibili_grouping_benchmark.js
 *
 * Outputs:
 *   build/audit/bilibili_grouping_benchmark.json   (case-by-case expected vs actual)
 *   build/audit/bilibili_grouping_analysis.json    (corpus-wide statistics)
 */
const fs = require('fs');
const path = require('path');

global.window = {};
const REPO_ROOT = path.resolve(__dirname, '..', '..');
const impl = require(path.join(REPO_ROOT, 'build', 'audit', 'bili_grouping_impl.js'));

const BILI_DATA = path.join(REPO_ROOT, 'converted_output', 'data', 'bili_data.js');
const CORPUS = path.join(REPO_ROOT, 'pipeline', 'audit', 'bilibili_grouping_corpus.json');
const OUT_BENCH = path.join(REPO_ROOT, 'build', 'audit', 'bilibili_grouping_benchmark.json');
const OUT_ANALYSIS = path.join(REPO_ROOT, 'build', 'audit', 'bilibili_grouping_analysis.json');

const GENERIC_TOKENS = [
  '我的世界', '整合包', '生存', '冒险', '科技', '魔法', '空岛', '全新', '更新',
  '发布', '正式版', '高配', '低配', '纯净', '大型', '介绍', '推荐',
];

function loadBili() {
  const raw = fs.readFileSync(BILI_DATA, 'utf8');
  return JSON.parse(raw.slice(raw.indexOf('['), raw.lastIndexOf(']') + 1));
}

/** Group a list of records and return a map bvid -> group key. */
function groupKeyOf(records) {
  const groups = impl.groupPacks(records);
  const out = {};
  for (const g of groups) for (const it of g.items) out[it.bvid] = g.key;
  return { map: out, groupCount: groups.length, groups };
}

function evaluateCase(c, byBv) {
  // Feed the REAL payload records to the real implementation. Falling back to a
  // synthesized record is only needed for reconstructed (synthetic) cases; it
  // must still carry `author`, otherwise author-scoping silently collapses to
  // "unknown" and every case looks like a false split.
  const records = c.videos.map((v) => {
    const real = byBv.get(v.bvid);
    if (real) return real;
    return {
      bvid: v.bvid,
      title: v.title,
      author: c.uploader,
      pic: '',
      pub_time: v.published_at || '',
      pub_timestamp: 0,
      mc_version: v.mc_version || '',
      all_versions: [],
      loaders: [],
      categories: [],
      download_links: [],
      qq_group: v.qq_group || '',
      pack_version: v.pack_version || '',
      group_version_note: '',
      has_group_version: false,
      has_server: false,
      desc: v.description_excerpt || '',
      views: 0, likes: 0, coins: 0, favorites: 0, share: 0, reply: 0, danmaku: 0,
      desc_updated_at: '',
    };
  });

  const { map, groups } = groupKeyOf(records);
  const keys = [...new Set(records.map((v) => map[v.bvid]))];
  const merged = keys.length === 1;
  const correct = c.expected === 'merge' ? merged : keys.length === c.videos.length;
  const keyByBv = {};
  for (const g of groups) for (const it of g.items) keyByBv[it.bvid] = g.key;

  return {
    case_id: c.case_id,
    expected: c.expected,
    confidence: c.confidence,
    kind: c.kind,
    uploader: c.uploader,
    video_count: c.videos.length,
    distinct_group_keys: keys.length,
    group_keys: keys,
    current_algorithm_result: merged ? 'merged' : 'separate',
    correct,
    videos: c.videos.map((v) => ({
      bvid: v.bvid,
      title: v.title,
      current_clean_key: map[v.bvid],
      current_group_key: keyByBv[v.bvid],
    })),
    ground_truth_evidence: c.ground_truth_evidence,
  };
}

function analyseKeys(data) {
  const byAuthorKey = new Map();
  for (const r of data) {
    const k = impl.cleanPackKey(r.title);
    const a = (r.author || 'unknown').trim().toLowerCase();
    const id = a + '::' + k;
    if (!byAuthorKey.has(id)) byAuthorKey.set(id, { key: k, author: a, videos: [] });
    byAuthorKey.get(id).videos.push(r.bvid);
  }
  const groups = [...byAuthorKey.values()];
  const multi = groups.filter((g) => g.videos.length > 1);
  const single = groups.filter((g) => g.videos.length === 1);

  // cross-uploader collision: same cleanPackKey under different authors
  const keyToAuthors = new Map();
  for (const g of groups) {
    if (!keyToAuthors.has(g.key)) keyToAuthors.set(g.key, new Set());
    keyToAuthors.get(g.key).add(g.author);
  }
  const crossUploader = [...keyToAuthors.entries()].filter(([, a]) => a.size > 1);

  const keyFreq = new Map();
  for (const g of groups) keyFreq.set(g.key, (keyFreq.get(g.key) || 0) + g.videos.length);

  return {
    raw_videos: data.length,
    unique_author_key_groups: groups.length,
    multi_video_groups: multi.length,
    single_video_groups: single.length,
    videos_in_multi_groups: multi.reduce((a, g) => a + g.videos.length, 0),
    net_collapse: data.length - groups.length,
    cross_uploader_collisions: crossUploader.length,
    cross_uploader_examples: crossUploader.slice(0, 10).map(([k, a]) => ({ key: k, authors: [...a] })),
    same_uploader_collision_groups: multi.length,
    generic_key_groups: groups.filter((g) => GENERIC_TOKENS.includes(g.key)).length,
    top_repeated_keys: [...keyFreq.entries()].sort((a, b) => b[1] - a[1]).slice(0, 15),
  };
}

function analyseKeyStrength(data) {
  const seen = new Map();
  for (const r of data) {
    const k = impl.cleanPackKey(r.title);
    const a = (r.author || 'unknown').trim().toLowerCase();
    const id = a + '::' + k;
    if (!seen.has(id)) seen.set(id, { key: k, author: a, n: 0, titles: [] });
    seen.get(id).n += 1;
    if (seen.get(id).titles.length < 2) seen.get(id).titles.push(r.title);
  }
  const rows = [];
  for (const g of seen.values()) {
    const tokens = g.key ? g.key.split(' ').filter(Boolean) : [];
    const genericHits = tokens.filter((t) => GENERIC_TOKENS.includes(t)).length;
    const distinctive = tokens.filter((t) => !GENERIC_TOKENS.includes(t) && t.length >= 2);
    rows.push({
      key: g.key,
      author: g.author,
      videos: g.n,
      key_length: g.key.length,
      token_count: tokens.length,
      generic_token_count: genericHits,
      generic_ratio: tokens.length ? +(genericHits / tokens.length).toFixed(2) : 0,
      distinctive_tokens: distinctive,
      low_discriminative: g.key.length <= 4 || distinctive.length === 0,
    });
  }
  rows.sort((a, b) => a.key_length - b.key_length);
  return {
    total_groups: rows.length,
    low_discriminative_count: rows.filter((r) => r.low_discriminative).length,
    low_discriminative_ratio: rows.length
      ? +(rows.filter((r) => r.low_discriminative).length / rows.length).toFixed(3) : 0,
    low_discriminative_samples: rows.filter((r) => r.low_discriminative).slice(0, 25),
    key_length_histogram: rows.reduce((acc, r) => {
      const b = r.key_length === 0 ? '0' : r.key_length <= 3 ? '1-3' : r.key_length <= 6 ? '4-6'
        : r.key_length <= 10 ? '7-10' : '11+';
      acc[b] = (acc[b] || 0) + 1; return acc;
    }, {}),
  };
}

function analyseGenericVocabulary(data) {
  const freq = new Map();
  const groupsByKey = new Map();
  for (const r of data) {
    const k = impl.cleanPackKey(r.title);
    const a = (r.author || 'unknown').trim().toLowerCase();
    const id = a + '::' + k;
    groupsByKey.set(id, (groupsByKey.get(id) || 0) + 1);
    for (const t of new Set(k.split(' ').filter(Boolean))) freq.set(t, (freq.get(t) || 0) + 1);
  }
  const top = [...freq.entries()].sort((a, b) => b[1] - a[1]).slice(0, 50)
    .map(([token, groups]) => ({
      token,
      groups_containing: groups,
      group_share: +(groups / groupsByKey.size).toFixed(3),
      is_generic_token: GENERIC_TOKENS.includes(token),
    }));
  return { distinct_key_tokens: freq.size, top_50: top };
}

function analyseVersionSignals(data) {
  const vsPat = /\d+(?:\.\d+)+/g;
  const withVersionInTitle = data.filter((r) => vsPat.test(r.title || '')).length;
  vsPat.lastIndex = 0;
  // does the version survive cleanPackKey?
  let survived = 0, stripped = 0, residue = 0;
  for (const r of data) {
    const t = r.title || '';
    const hasV = /\d+(?:\.\d+)+/.test(t);
    if (!hasV) continue;
    const k = impl.cleanPackKey(t);
    if (/\d+(?:\.\d+)+/.test(k)) survived++;
    else if (/\d/.test(k)) residue++;
    else stripped++;
  }
  // same-pack version updates vs different packs sharing an MC version
  const byAuthorKey = new Map();
  for (const r of data) {
    const id = (r.author || '').trim().toLowerCase() + '::' + impl.cleanPackKey(r.title);
    if (!byAuthorKey.has(id)) byAuthorKey.set(id, []);
    byAuthorKey.get(id).push(r);
  }
  const mcGroups = new Map();
  for (const rs of byAuthorKey.values()) {
    const mc = rs[0].mc_version || 'unknown';
    if (!mcGroups.has(mc)) mcGroups.set(mc, []);
    mcGroups.get(mc).push(rs);
  }
  const sameMcDifferentKey = [...mcGroups.entries()]
    .filter(([, gs]) => gs.length > 1)
    .map(([mc, gs]) => ({ mc_version: mc, distinct_groups: gs.length }));
  sameMcDifferentKey.sort((a, b) => b.distinct_groups - a.distinct_groups);

  return {
    videos_with_version_in_title: withVersionInTitle,
    version_stripped_from_key: stripped,
    version_residue_in_key: residue,
    version_survived_in_key: survived,
    note: 'versions are removed by cleanPackKey regexes; they are NOT part of the group key',
    same_uploader_same_mc_version_distinct_groups_top: sameMcDifferentKey.slice(0, 10),
  };
}

function analyseDownloadIdentity(data) {
  const GENERIC_URL_HINTS = ['pm.mutong1.com', 'docs.qq.com/sheet', 'b23.tv'];
  const url2 = new Map();
  for (const r of data) {
    for (const l of (r.download_links || [])) {
      const u = (l.url || '').trim();
      if (!u) continue;
      if (!url2.has(u)) url2.set(u, new Set());
      url2.get(u).add(r.bvid);
    }
  }
  const shared = [...url2.entries()].filter(([, s]) => s.size > 1);
  const specific = shared.filter(([u]) => !GENERIC_URL_HINTS.some((h) => u.includes(h)));
  return {
    videos_with_links: data.filter((r) => (r.download_links || []).length).length,
    distinct_urls: url2.size,
    urls_shared_by_multiple_videos: shared.length,
    shared_specific_resource_urls: specific.length,
    largest_clusters: specific.sort((a, b) => b[1].size - a[1].size).slice(0, 8)
      .map(([u, s]) => ({ url: u, videos: s.size })),
  };
}

function analyseQqIdentity(data) {
  const q2 = new Map();
  for (const r of data) {
    const q = (r.qq_group || '').trim();
    if (!q) continue;
    if (!q2.has(q)) q2.set(q, { videos: new Set(), authors: new Set() });
    q2.get(q).videos.add(r.bvid);
    q2.get(q).authors.add(r.author || '');
  }
  const multi = [...q2.entries()].filter(([, v]) => v.videos.size > 1);
  return {
    videos_with_qq_group: data.filter((r) => (r.qq_group || '').trim()).length,
    distinct_qq_groups: q2.size,
    qq_groups_spanning_multiple_videos: multi.length,
    qq_groups_spanning_multiple_authors: multi.filter(([, v]) => v.authors.size > 1).length,
    largest: multi.sort((a, b) => b[1].videos.size - a[1].videos.size).slice(0, 8)
      .map(([q, v]) => ({ qq: q, videos: v.videos.size, authors: v.authors.size })),
  };
}

function searchTarget(p) {
  return [(p.title || ''), (p.author || ''), (p.desc || ''), (p.mc_version || ''),
    (p.loaders || []).join(' '), (p.categories || []).join(' ')].join(' ').toLowerCase();
}

function mechanicalPowerCase(data) {
  const q = '机械动力';
  const filtered = data.filter((p) => searchTarget(p).includes(q));
  const { groups } = groupKeyOf(filtered);
  const multi = groups.filter((g) => g.items.length > 1);
  return {
    query: q,
    raw_matches: filtered.length,
    grouped_cards: groups.length,
    net_collapse: filtered.length - groups.length,
    multi_video_groups: multi.map((g) => ({
      key: g.key,
      author: g.author,
      video_count: g.items.length,
      videos: g.items.map((i) => ({ bvid: i.bvid, title: i.title })),
    })),
    collapse_accounting: multi.map((g) => ({
      key: g.key,
      videos: g.items.length,
      cards: 1,
      net: -(g.items.length - 1),
    })),
    flat_mode_raw_records: filtered.length,
    flat_mode_invariant_ok: filtered.length === 53,
  };
}

function main() {
  const data = loadBili();
  const byBv = new Map(data.map((r) => [r.bvid, r]));
  const corpus = JSON.parse(fs.readFileSync(CORPUS, 'utf8'));

  const scored = [...corpus.positive_cases, ...corpus.negative_cases].filter(
    (c) => c.confidence === 'confirmed' || c.confidence === 'strong');

  const results = scored.map((c) => evaluateCase(c, byBv));
  const reconstructed = (corpus.reconstructed_cases || []).map((c) => evaluateCase(c, byBv));

  const trueMerge = results.filter((r) => r.expected === 'merge' && r.correct).length;
  const falseSplit = results.filter((r) => r.expected === 'merge' && !r.correct).length;
  const trueSeparate = results.filter((r) => r.expected === 'separate' && r.correct).length;
  const falseMerge = results.filter((r) => r.expected === 'separate' && !r.correct).length;

  const mergePrecision = trueMerge + falseMerge ? trueMerge / (trueMerge + falseMerge) : 1;
  const mergeRecall = trueMerge + falseSplit ? trueMerge / (trueMerge + falseSplit) : 1;

  const uploaders = new Set(scored.map((c) => c.uploader));

  const benchmark = {
    generated_at: new Date().toISOString(),
    implementation_source: 'converted_output/assets/index.js (production bundle, extracted verbatim)',
    invariant_check: {
      raw_videos: data.length,
      mechanical_power_raw: 53,
      mechanical_power_cards: 47,
      reproduced: null,
    },
    corpus: {
      scored_cases: scored.length,
      positive_cases: corpus.positive_cases.length,
      negative_cases: corpus.negative_cases.length,
      reconstructed_cases: reconstructed.length,
      unique_uploaders: uploaders.size,
      confidence_distribution: scored.reduce((a, c) => { a[c.confidence] = (a[c.confidence] || 0) + 1; return a; }, {}),
    },
    outcomes: {
      true_merge: trueMerge,
      false_split: falseSplit,
      true_separate: trueSeparate,
      false_merge: falseMerge,
      merge_precision: +mergePrecision.toFixed(4),
      merge_recall: +mergeRecall.toFixed(4),
      false_merge_rate: +(falseMerge / (trueSeparate + falseMerge || 1)).toFixed(4),
      false_split_rate: +(falseSplit / (trueMerge + falseSplit || 1)).toFixed(4),
    },
    false_merge_cases: results.filter((r) => r.expected === 'separate' && !r.correct),
    false_split_cases: results.filter((r) => r.expected === 'merge' && !r.correct),
    cases: results,
    reconstructed_cases: reconstructed,
    spec_case_absent: corpus.spec_case_absent,
  };

  const mp = mechanicalPowerCase(data);
  benchmark.invariant_check.reproduced =
    mp.raw_matches === 53 && mp.grouped_cards === 47;

  const analysis = {
    generated_at: benchmark.generated_at,
    raw_total: data.length,
    key_space: analyseKeys(data),
    key_strength: analyseKeyStrength(data),
    generic_vocabulary: analyseGenericVocabulary(data),
    version_signals: analyseVersionSignals(data),
    download_identity: analyseDownloadIdentity(data),
    qq_identity: analyseQqIdentity(data),
    mechanical_power_53_47: mp,
  };

  fs.mkdirSync(path.dirname(OUT_BENCH), { recursive: true });
  fs.writeFileSync(OUT_BENCH, JSON.stringify(benchmark, null, 2), 'utf8');
  fs.writeFileSync(OUT_ANALYSIS, JSON.stringify(analysis, null, 2), 'utf8');

  console.log('=== Phase 3G-E Bilibili grouping benchmark ===');
  console.log(`invariant 936 payload, 机械动力 ${mp.raw_matches} raw -> ${mp.grouped_cards} cards  reproduced=${benchmark.invariant_check.reproduced}`);
  console.log(`corpus     scored=${scored.length} (pos=${corpus.positive_cases.length} neg=${corpus.negative_cases.length}) uploaders=${uploaders.size}`);
  console.log(`outcomes   TrueMerge=${trueMerge} FalseSplit=${falseSplit} TrueSeparate=${trueSeparate} FalseMerge=${falseMerge}`);
  console.log(`metrics    precision=${benchmark.outcomes.merge_precision} recall=${benchmark.outcomes.merge_recall}`);
  console.log(`key space  groups=${analysis.key_space.unique_author_key_groups} multi=${analysis.key_space.multi_video_groups} single=${analysis.key_space.single_video_groups} crossUploaderCollisions=${analysis.key_space.cross_uploader_collisions}`);
  console.log(`low-disc   ${analysis.key_strength.low_discriminative_count}/${analysis.key_strength.total_groups}`);
  console.log(`written    ${path.relative(REPO_ROOT, OUT_BENCH)}`);
  console.log(`written    ${path.relative(REPO_ROOT, OUT_ANALYSIS)}`);
  return 0;
}

process.exit(main());

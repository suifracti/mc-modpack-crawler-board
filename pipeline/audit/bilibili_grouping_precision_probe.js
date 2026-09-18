/**
 * Phase 3G-F-A - Bilibili grouping precision / safety probe.
 *
 * The frozen corpus (bilibili_grouping_corpus.json) scores 46 cases. This probe
 * covers the questions the corpus does NOT adjudicate, so that "precision = 1.0"
 * is not mistaken for "precision is fully proven":
 *
 *   1. batch dependence - the grouping runs on the FULL 936 payload in the
 *      dashboard, but the search view runs it on a filtered subset. If the two
 *      produce different groupKeys for the same bvid, "53 raw -> 36 cards" is
 *      not a property of the data, it is a property of the batch.
 *   2. reconstructed 黑金 negative (synthetic, not present in the 936 payload).
 *   3. download-URL-only / QQ-only merging safety (豆腐ki cluster).
 *   4. low-discriminative token audit (沉浸 / 生电 / 原神 / 溯渊 / 泰坦).
 *   5. group-size distribution and every group >= 5 for manual review.
 *
 * Usage: node pipeline/audit/bilibili_grouping_precision_probe.js
 * Output: build/audit/bilibili_grouping_precision_probe.json
 */
const fs = require('fs');
const path = require('path');

global.window = {};
const REPO_ROOT = path.resolve(__dirname, '..', '..');
const newMod = require(path.join(REPO_ROOT, 'build', 'audit', 'bilibili_grouping_module.js'));
const OUT = path.join(REPO_ROOT, 'build', 'audit', 'bilibili_grouping_precision_probe.json');

const BILI_DATA = path.join(REPO_ROOT, 'converted_output', 'data', 'bili_data.js');
const CORPUS = path.join(REPO_ROOT, 'pipeline', 'audit', 'bilibili_grouping_corpus.json');

function loadBili() {
  const raw = fs.readFileSync(BILI_DATA, 'utf8');
  return JSON.parse(raw.slice(raw.indexOf('['), raw.lastIndexOf(']') + 1));
}
function loadJson(p) { return JSON.parse(fs.readFileSync(p, 'utf8')); }

function keyMap(recs) {
  const o = {};
  for (const [b, d] of newMod.groupBilibiliPacks(recs)) {
    o[b] = { groupKey: d.groupKey, identityKey: d.identityKey, reason: d.groupingReason };
  }
  return o;
}

function searchTarget(p) {
  return [p.title || '', p.author || '', p.desc || '', p.mc_version || '',
    (p.loaders || []).join(' '), (p.categories || []).join(' ')].join(' ').toLowerCase();
}

function groupsOf(recs, map) {
  const g = new Map();
  for (const p of recs) {
    const k = map[p.bvid].groupKey;
    if (!g.has(k)) g.set(k, []);
    g.get(k).push(p);
  }
  return g;
}

/** 1 - batch dependence between the full payload and a filtered search batch. */
function batchDependence(data, fullMap, query) {
  const sub = data.filter((p) => searchTarget(p).includes(query));
  const subMap = keyMap(sub);
  const changed = [];
  for (const p of sub) {
    const a = fullMap[p.bvid].groupKey;
    const b = subMap[p.bvid].groupKey;
    if (a !== b) {
      changed.push({ bvid: p.bvid, author: p.author, title: p.title, population_key: a, batch_key: b });
    }
  }
  const fullGroups = groupsOf(sub, fullMap);
  const subGroups = groupsOf(sub, subMap);
  return {
    query,
    batch_size: sub.length,
    full_population_cards: fullGroups.size,
    filtered_batch_cards: subGroups.size,
    records_with_different_group_key: changed.length,
    examples: changed.slice(0, 15),
    identical: changed.length === 0,
  };
}

/** 2 - the reconstructed 黑金 negative control (synthetic bvids). */
function heijinCheck(corpus) {
  const c = corpus.reconstructed_cases.find((x) => x.case_id === 'NEG-SPEC-HEIJIN');
  const recs = c.videos.map((v) => ({
    bvid: v.bvid, title: v.title, author: c.uploader,
  }));
  const map = keyMap(recs);
  const keys = [...new Set(recs.map((r) => map[r.bvid].groupKey))];
  return {
    case_id: c.case_id,
    expected: c.expected,
    confidence: c.confidence,
    videos: recs.map((r) => ({ bvid: r.bvid, title: r.title, key: map[r.bvid].groupKey })),
    distinct_keys: keys.length,
    merged: keys.length === 1,
    correct: keys.length === recs.length,
  };
}

/** 3 - download-URL-only / QQ-only merge safety. */
function downloadQqSafety(data) {
  const byUrl = new Map();
  const byQq = new Map();
  const norm = (u) => String(u || '').trim().replace(/\/+$/, '');
  for (const p of data) {
    for (const u of (p.download_links || [])) {
      const k = norm(typeof u === 'string' ? u : (u && (u.url || u.link)) || '');
      if (!k) continue;
      if (!byUrl.has(k)) byUrl.set(k, []);
      byUrl.get(k).push(p);
    }
    const q = String(p.qq_group || '').trim();
    if (q) {
      if (!byQq.has(q)) byQq.set(q, []);
      byQq.get(q).push(p);
    }
  }
  const full = keyMap(data);

  // shared-URL clusters that span >1 record: does the URL alone merge them?
  const urlClusters = [];
  for (const [url, recs] of byUrl) {
    if (recs.length < 2) continue;
    const keys = new Set(recs.map((r) => full[r.bvid].groupKey));
    urlClusters.push({
      url: url.slice(0, 90),
      records: recs.length,
      distinct_group_keys: keys.size,
      merged_by_url_alone: keys.size === 1,
    });
  }
  const qqClusters = [];
  for (const [qq, recs] of byQq) {
    if (recs.length < 2) continue;
    const keys = new Set(recs.map((r) => full[r.bvid].groupKey));
    qqClusters.push({
      qq: qq.slice(0, 40),
      records: recs.length,
      distinct_group_keys: keys.size,
      merged_by_qq_alone: keys.size === 1,
    });
  }
  const multiUrl = urlClusters.filter((c) => c.records >= 2);
  const multiQq = qqClusters.filter((c) => c.records >= 2);
  return {
    distinct_download_urls_shared: multiUrl.length,
    url_clusters_merged_into_one_group: multiUrl.filter((c) => c.merged_by_url_alone).length,
    distinct_qq_groups_shared: multiQq.length,
    qq_clusters_merged_into_one_group: multiQq.filter((c) => c.merged_by_qq_alone).length,
    // the largest shared-URL cluster is the 豆腐ki case named in the brief
    largest_url_clusters: urlClusters.sort((a, b) => b.records - a.records).slice(0, 8),
    largest_qq_clusters: qqClusters.sort((a, b) => b.records - a.records).slice(0, 8),
    // explicit 豆腐ki regression
    doufuki: (() => {
      const recs = data.filter((p) => (p.author || '').includes('豆腐ki'));
      const g = groupsOf(recs, full);
      return {
        records: recs.length,
        groups: g.size,
        members: [...g.entries()].map(([k, v]) => ({ key: k, n: v.length, titles: v.map((x) => x.title.slice(0, 60)) })),
      };
    })(),
    note: 'groupBilibiliPacks consumes only (bvid, title, author). download_links / qq_group are never read, so URL-only or QQ-only merging is structurally impossible; these clusters measure whether the TITLE rule happens to collapse them anyway.',
  };
}

/** 4 - low-discriminative token audit. */
const LOW_TOKENS = ['沉浸', '生电', '原神', '溯渊', '泰坦'];
function lowDiscriminativeAudit(data) {
  const full = keyMap(data);
  const out = {};
  for (const t of LOW_TOKENS) {
    const hits = data.filter((p) => searchTarget(p).includes(t.toLowerCase()));
    const g = groupsOf(hits, full);
    const multi = [...g.entries()].filter(([, v]) => v.length > 1)
      .map(([k, v]) => ({ key: k, size: v.length, titles: v.map((x) => x.title.slice(0, 65)), authors: [...new Set(v.map((x) => x.author))] }))
      .sort((a, b) => b.size - a.size);
    out[t] = { matching_records: hits.length, cards: g.size, multi_video_groups: multi };
  }
  return out;
}

/** 5 - population + large groups. */
function populationAudit(data) {
  const full = keyMap(data);
  const g = groupsOf(data, full);
  const sizes = [...g.values()].map((v) => v.length).sort((a, b) => b - a);
  const dist = sizes.reduce((a, s) => {
    const b = s === 1 ? '1' : s === 2 ? '2' : s <= 4 ? '3-4' : s <= 9 ? '5-9' : '10+';
    a[b] = (a[b] || 0) + 1; return a;
  }, {});
  const large = [...g.entries()].filter(([, v]) => v.length >= 5)
    .map(([k, v]) => ({
      key: k, size: v.length,
      authors: [...new Set(v.map((x) => x.author))],
      cross_uploader: new Set(v.map((x) => x.author)).size > 1,
      titles: v.map((x) => x.title.slice(0, 80)),
    }))
    .sort((a, b) => b.size - a.size);
  return {
    raw_videos: data.length,
    grouped_cards: g.size,
    multi_video_groups: sizes.filter((s) => s > 1).length,
    largest_group: sizes[0] || 0,
    size_distribution: dist,
    large_groups_ge5: large,
    any_cross_uploader_group: large.some((x) => x.cross_uploader),
  };
}

function main() {
  const data = loadBili();
  const corpus = loadJson(CORPUS);
  const fullMap = keyMap(data);

  const result = {
    generated_at: new Date().toISOString(),
    payload_records: data.length,
    module_sha256: process.env.MODULE_SHA || null,
    batch_dependence: batchDependence(data, fullMap, '机械动力'),
    heijin_negative: heijinCheck(corpus),
    download_qq_safety: downloadQqSafety(data),
    low_discriminative_tokens: lowDiscriminativeAudit(data),
    population: populationAudit(data),
  };

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(result, null, 2), 'utf8');

  const bd = result.batch_dependence;
  console.log('=== Phase 3G-F-A precision / safety probe ===');
  console.log(`batch dependence (机械动力): batch=${bd.batch_size} full_cards=${bd.full_population_cards} batch_cards=${bd.filtered_batch_cards} changedKeys=${bd.records_with_different_group_key} identical=${bd.identical}`);
  console.log(`黑金 reconstructed negative: merged=${result.heijin_negative.merged} correct=${result.heijin_negative.correct}`);
  const s = result.download_qq_safety;
  console.log(`download/QQ safety: shared-URL clusters=${s.distinct_download_urls_shared} merged-by-URL-alone=${s.url_clusters_merged_into_one_group}; shared-QQ clusters=${s.distinct_qq_groups_shared} merged-by-QQ-alone=${s.qq_clusters_merged_into_one_group}`);
  console.log(`豆腐ki: ${s.doufuki.records} records -> ${s.doufuki.groups} groups`);
  console.log(`population: ${result.population.raw_videos} raw -> ${result.population.grouped_cards} cards; largest=${result.population.largest_group}; groups>=5=${result.population.large_groups_ge5.length}; crossUploader=${result.population.any_cross_uploader_group}`);
  console.log(`written: ${path.relative(REPO_ROOT, OUT)}`);
  return 0;
}

process.exit(main());

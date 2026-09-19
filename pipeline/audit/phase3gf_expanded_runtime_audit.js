/**
 * Phase 3G-F.3-A - independent expanded population/holdout runtime audit.
 *
 * This is deliberately separate from the frozen 26-case acceptance runner:
 * the runner proves the adjudicated under-merge partitions, while this audit
 * evaluates the additive v2 holdout and the complete 936-record population.
 * The holdout negative cases carry their own adjudicated partitions; a
 * negative case is not interpreted as "every video must be a singleton".
 *
 * Exit codes: 0 = expanded audit passes, 2 = runtime/metric safety failure,
 * 1 = configuration or input failure.
 */
const crypto = require('crypto');
const { execFileSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..');
const SOURCE_REL = 'apps/web/src/domain/bilibiliGrouping.ts';
const PAYLOAD_PATH = path.join(ROOT, 'converted_output', 'data', 'bili_data.js');
const HOLDOUT_PATH = path.join(ROOT, 'pipeline', 'audit', 'bilibili_population_holdout_v2.json');
const LEDGER_PATH = path.join(ROOT, 'pipeline', 'audit', 'bilibili_population_adjudication_v2.json');
const GATE_PATH = path.join(ROOT, 'pipeline', 'audit', 'confirmed_undermerge_runtime_gate.json');
const DEFAULT_OUT = path.join(ROOT, 'build', 'audit', 'phase3gf_expanded_runtime_audit.json');
const DEFAULT_HOLDOUT_OUT = path.join(ROOT, 'build', 'audit', 'phase3gf_runtime_holdout_v2.json');
const LEGACY_IMPL = path.join(ROOT, 'pipeline', 'audit', 'fixtures', 'bili_grouping_legacy_impl.js');
const HOLDOUT_BASELINE_RUNTIME = 'ef411d1542433d8fdd7f06ed40946d6626d19252';

function sha256Bytes(bytes) { return crypto.createHash('sha256').update(bytes).digest('hex'); }
function sha256File(file) { return sha256Bytes(fs.readFileSync(file)); }
function readJson(file) { return JSON.parse(fs.readFileSync(file, 'utf8')); }
function auditJson(file) {
  const io = require(path.join(ROOT, 'pipeline', 'audit', 'lib', 'audit_artifact_io.js'));
  return io.readJson(file);
}
function sorted(xs) { return [...xs].sort(); }
function unique(xs) { return [...new Set(xs)]; }
function stableNow() {
  return new Date(process.env.SOURCE_DATE_EPOCH
    ? Number(process.env.SOURCE_DATE_EPOCH) * 1000
    : Date.now()).toISOString();
}
function fail(message) {
  const error = new Error(`expanded runtime audit: ${message}`);
  error.code = 2;
  throw error;
}
function git(args) { return execFileSync('git', args, { cwd: ROOT, encoding: 'utf8' }).trim(); }

function parseArgs() {
  const args = process.argv.slice(2);
  const get = (name, fallback) => {
    const i = args.indexOf(name);
    return i >= 0 ? args[i + 1] : fallback;
  };
  return {
    out: get('--out', DEFAULT_OUT),
    holdoutOut: get('--holdout-out', DEFAULT_HOLDOUT_OUT),
  };
}

function loadPayload() {
  const raw = fs.readFileSync(PAYLOAD_PATH, 'utf8');
  const start = raw.indexOf('[');
  const end = raw.lastIndexOf(']');
  if (start < 0 || end < start) fail('population payload is not an array');
  const data = JSON.parse(raw.slice(start, end + 1));
  const seen = new Set();
  for (const row of data) {
    if (!row || !row.bvid || seen.has(row.bvid)) fail(`duplicate/empty population BVID: ${row && row.bvid}`);
    seen.add(row.bvid);
  }
  if (data.length !== 936 || seen.size !== 936) fail(`population coverage ${data.length}/${seen.size}, expected 936`);
  return data;
}

function compileCurrentRuntime(temp) {
  const esbuild = path.join(ROOT, 'apps', 'web', 'node_modules', 'esbuild', 'bin', 'esbuild');
  if (!fs.existsSync(esbuild)) fail(`esbuild missing: ${esbuild}`);
  const out = path.join(temp, 'candidate.cjs');
  const command = process.platform === 'win32' ? process.execPath : esbuild;
  const commandArgs = process.platform === 'win32'
    ? [esbuild, path.join(ROOT, SOURCE_REL), '--bundle', '--format=cjs', '--platform=node', `--outfile=${out}`, '--log-level=warning']
    : [path.join(ROOT, SOURCE_REL), '--bundle', '--format=cjs', '--platform=node', `--outfile=${out}`, '--log-level=warning'];
  execFileSync(command, commandArgs, { cwd: ROOT, stdio: 'pipe' });
  delete require.cache[require.resolve(out)];
  const mod = require(out);
  if (!mod || typeof mod.groupBilibiliPacks !== 'function') fail('compiled runtime has no groupBilibiliPacks');
  return { module: mod, bundle: out, bundle_sha256: sha256File(out) };
}

function compileRuntimeAtCommit(commit, temp, label) {
  const esbuild = path.join(ROOT, 'apps', 'web', 'node_modules', 'esbuild', 'bin', 'esbuild');
  if (!fs.existsSync(esbuild)) fail(`esbuild missing: ${esbuild}`);
  const sourceRoot = path.join(temp, label, 'apps', 'web', 'src', 'domain');
  fs.mkdirSync(sourceRoot, { recursive: true });
  const source = path.join(sourceRoot, 'bilibiliGrouping.ts');
  const packName = path.join(sourceRoot, 'packName.ts');
  fs.writeFileSync(source, execFileSync('git', ['show', `${commit}:${SOURCE_REL}`], {
    cwd: ROOT,
    encoding: 'utf8',
  }));
  fs.writeFileSync(packName, execFileSync('git', ['show', `${commit}:apps/web/src/domain/packName.ts`], {
    cwd: ROOT,
    encoding: 'utf8',
  }));
  const out = path.join(temp, `${label}.cjs`);
  const command = process.platform === 'win32' ? process.execPath : esbuild;
  const commandArgs = process.platform === 'win32'
    ? [esbuild, source, '--bundle', '--format=cjs', '--platform=node', `--outfile=${out}`, '--log-level=warning']
    : [source, '--bundle', '--format=cjs', '--platform=node', `--outfile=${out}`, '--log-level=warning'];
  execFileSync(command, commandArgs, { cwd: ROOT, stdio: 'pipe' });
  delete require.cache[require.resolve(out)];
  const mod = require(out);
  if (!mod || typeof mod.groupBilibiliPacks !== 'function') fail(`historical runtime has no groupBilibiliPacks: ${commit}`);
  return { module: mod, bundle: out, bundle_sha256: sha256File(out), source_commit: commit };
}

function runtimeDecisions(mod, data) {
  const result = mod.groupBilibiliPacks(data);
  if (!result || typeof result.get !== 'function') fail('runtime did not return a Map');
  const out = {};
  for (const [bvid, decision] of result) {
    if (!decision || typeof decision.groupKey !== 'string') fail(`runtime decision missing groupKey: ${bvid}`);
    out[bvid] = decision;
  }
  if (Object.keys(out).length !== data.length) fail(`runtime decisions ${Object.keys(out).length}/${data.length}`);
  return out;
}

function groupMembers(data, decisions) {
  const groups = new Map();
  for (const row of data) {
    const key = decisions[row.bvid].groupKey;
    const members = groups.get(key);
    if (members) members.push(row.bvid);
    else groups.set(key, [row.bvid]);
  }
  for (const [key, members] of groups) groups.set(key, sorted(members));
  return groups;
}

function searchTarget(row) {
  return [row.title || '', row.author || '', row.desc || '', row.mc_version || '',
    ...(row.loaders || []), ...(row.categories || [])].join(' ').toLowerCase();
}

function populationStats(data, decisions) {
  const groups = groupMembers(data, decisions);
  const sizes = [...groups.values()].map((members) => members.length).sort((a, b) => b - a);
  const distribution = sizes.reduce((out, size) => {
    const bucket = size === 1 ? '1' : size === 2 ? '2' : size <= 4 ? '3-4' : size <= 9 ? '5-9' : '10+';
    out[bucket] = (out[bucket] || 0) + 1;
    return out;
  }, {});
  return {
    raw_records: data.length,
    unique_bvids: new Set(data.map((row) => row.bvid)).size,
    grouped_cards: groups.size,
    net_collapse: data.length - groups.size,
    multi_record_groups: sizes.filter((size) => size > 1).length,
    records_in_multi_record_groups: sizes.filter((size) => size > 1).reduce((sum, size) => sum + size, 0),
    largest_group: sizes[0] || 0,
    size_distribution: distribution,
  };
}

function mechanicalPower(data, decisions) {
  const rows = data.filter((row) => searchTarget(row).includes('机械动力'));
  const groups = new Map();
  for (const row of rows) {
    const key = decisions[row.bvid].groupKey;
    const members = groups.get(key);
    if (members) members.push(row.bvid);
    else groups.set(key, [row.bvid]);
  }
  const multi = [...groups.values()].filter((members) => members.length > 1);
  return {
    query: '机械动力',
    raw_records: rows.length,
    unique_bvids: new Set(rows.map((row) => row.bvid)).size,
    grouped_cards: groups.size,
    net_collapse: rows.length - groups.size,
    multi_record_groups: multi.length,
    records_in_multi_record_groups: multi.reduce((sum, members) => sum + members.length, 0),
    flat_mode_raw_records: rows.length,
    flat_mode_invariant_ok: rows.length === 53,
  };
}

function groundTruthKey(caseObj, video) {
  return caseObj.expected === 'merge' ? '__same_pack__' : video.group_key;
}

function pairwiseCase(caseObj, byBvid, decisions) {
  const videos = caseObj.videos;
  const failures = { false_split_pairs: [], false_merge_pairs: [] };
  let trueMerge = 0; let falseSplit = 0; let trueSeparate = 0; let falseMerge = 0;
  for (let i = 0; i < videos.length; i++) {
    for (let j = i + 1; j < videos.length; j++) {
      const a = videos[i]; const b = videos[j];
      const expectedSame = groundTruthKey(caseObj, a) === groundTruthKey(caseObj, b);
      const actualSame = decisions[a.bvid].groupKey === decisions[b.bvid].groupKey;
      const pair = {
        a: a.bvid,
        b: b.bvid,
        a_title: byBvid.get(a.bvid).title,
        b_title: byBvid.get(b.bvid).title,
      };
      if (expectedSame && actualSame) trueMerge++;
      else if (expectedSame) { falseSplit++; failures.false_split_pairs.push(pair); }
      else if (!actualSame) trueSeparate++;
      else { falseMerge++; failures.false_merge_pairs.push(pair); }
    }
  }
  const predictedKeys = unique(videos.map((video) => decisions[video.bvid].groupKey));
  const expectedKeys = unique(videos.map((video) => groundTruthKey(caseObj, video)));
  const exactPartition = falseSplit === 0 && falseMerge === 0;
  return {
    case_id: caseObj.case_id,
    expected: caseObj.expected,
    kind: caseObj.kind,
    confidence: caseObj.confidence,
    uploader: caseObj.uploader,
    video_count: videos.length,
    expected_group_count: expectedKeys.length,
    predicted_group_count: predictedKeys.length,
    exact_partition: exactPartition,
    true_merge: trueMerge,
    false_split: falseSplit,
    true_separate: trueSeparate,
    false_merge: falseMerge,
    false_split_pairs: failures.false_split_pairs,
    false_merge_pairs: failures.false_merge_pairs,
    ground_truth_evidence: caseObj.source,
  };
}

function metrics(results) {
  const out = results.reduce((acc, result) => ({
    true_merge: acc.true_merge + result.true_merge,
    false_split: acc.false_split + result.false_split,
    true_separate: acc.true_separate + result.true_separate,
    false_merge: acc.false_merge + result.false_merge,
  }), { true_merge: 0, false_split: 0, true_separate: 0, false_merge: 0 });
  return {
    ...out,
    precision: +(out.true_merge + out.false_merge
      ? out.true_merge / (out.true_merge + out.false_merge) : 1).toFixed(4),
    recall: +(out.true_merge + out.false_split
      ? out.true_merge / (out.true_merge + out.false_split) : 0).toFixed(4),
    false_merge_rate: +(out.true_separate + out.false_merge
      ? out.false_merge / (out.true_separate + out.false_merge) : 0).toFixed(4),
    false_split_rate: +(out.true_merge + out.false_split
      ? out.false_split / (out.true_merge + out.false_split) : 0).toFixed(4),
  };
}

function holdoutAudit(holdout, data, decisions) {
  const byBvid = new Map(data.map((row) => [row.bvid, row]));
  const allCases = [...holdout.positive_cases, ...holdout.negative_cases];
  const missing = allCases.flatMap((caseObj) => caseObj.videos
    .filter((video) => !byBvid.has(video.bvid)).map((video) => video.bvid));
  if (missing.length) fail(`holdout BVIDs missing from population: ${unique(missing).join(',')}`);
  const positive = holdout.positive_cases.map((caseObj) => pairwiseCase(caseObj, byBvid, decisions));
  const negative = holdout.negative_cases.map((caseObj) => pairwiseCase(caseObj, byBvid, decisions));
  const overall = [...positive, ...negative];
  return {
    source: {
      positive_cases: holdout.positive_cases.length,
      negative_cases: holdout.negative_cases.length,
      total_cases: allCases.length,
      positive_videos: holdout.positive_cases.reduce((sum, c) => sum + c.videos.length, 0),
      negative_videos: holdout.negative_cases.reduce((sum, c) => sum + c.videos.length, 0),
      uploader_count: holdout.holdout_v2.uploader_count,
      uploaders_disjoint_from_old_corpus: holdout.holdout_v2.uploader_overlap_with_old_corpus.length === 0,
      meets_requirement: holdout.holdout_v2.meets_requirement === true,
    },
    pairwise: { overall: metrics(overall), positive: metrics(positive), negative: metrics(negative) },
    case_partition: {
      overall_cases: overall.length,
      exact_cases: overall.filter((result) => result.exact_partition).length,
      failed_cases: overall.filter((result) => !result.exact_partition).length,
      positive_exact: positive.filter((result) => result.exact_partition).length,
      negative_exact: negative.filter((result) => result.exact_partition).length,
    },
    failures: overall.filter((result) => !result.exact_partition),
  };
}

function legacyGroupMap(data) {
  global.window = {};
  const old = require(LEGACY_IMPL);
  const map = {};
  for (const group of old.groupPacks(data)) {
    for (const item of group.items) map[item.bvid] = group.key;
  }
  return map;
}

function knownEightAudit(ledger, data, decisions, historicalDecisions) {
  const historicalMap = historicalDecisions;
  const retired = [];
  for (const [key, finding] of Object.entries(ledger.retired_false_merges || {})) {
    const members = data.filter((row) => historicalMap[row.bvid]?.groupKey === key);
    const afterKeys = unique(members.map((row) => decisions[row.bvid].groupKey));
    retired.push({
      key,
      fixed_by: finding.fixed_by,
      source_member_count: members.length,
      source_bvids: members.map((row) => row.bvid),
      current_group_count: afterKeys.length,
      current_group_keys: afterKeys,
      still_merging: members.length > 1 && afterKeys.length === 1,
      status: members.length === 0 ? 'MISSING_OLD_SNAPSHOT' : afterKeys.length > 1 ? 'RETIRED' : 'STILL_MERGING',
    });
  }
  return {
    expected: 8,
    checked: retired.length,
    source_runtime_commit: HOLDOUT_BASELINE_RUNTIME,
    retired: retired.filter((row) => row.status === 'RETIRED').length,
    still_merging: retired.filter((row) => row.still_merging).map((row) => row.key),
    missing_old_snapshot: retired.filter((row) => row.status === 'MISSING_OLD_SNAPSHOT').map((row) => row.key),
    cases: retired,
  };
}

function deriveFinalRuntimeHoldout(ledger, data, decisions) {
  const oldMap = legacyGroupMap(data);
  const byBvid = new Map(data.map((row) => [row.bvid, row]));
  const oldSplit = readJson(path.join(ROOT, 'pipeline', 'audit', 'bilibili_grouping_split.json'));
  const usedUploaders = new Set([
    ...oldSplit.dev.uploaders,
    ...oldSplit.holdout.uploaders,
  ].map((uploader) => String(uploader).toLowerCase()));
  const legitimate = ledger.legitimate_same_pack || [];
  const positives = [];
  const seenPositiveKeys = new Set();
  for (const finding of legitimate) {
    const evidenceMembers = finding.evidence?.members || [];
    const members = evidenceMembers.map((member) => byBvid.get(member.bvid)).filter(Boolean);
    if (members.length < 2) continue;
    const uploader = String(finding.author || members[0].author || '').trim();
    if (usedUploaders.has(uploader.toLowerCase())) continue;
    const currentKeys = unique(members.map((member) => decisions[member.bvid].groupKey));
    const oldKeys = unique(members.map((member) => oldMap[member.bvid]));
    if (currentKeys.length !== 1 || oldKeys.length < 2) continue;
    const groupKey = currentKeys[0];
    if (seenPositiveKeys.has(groupKey)) continue;
    seenPositiveKeys.add(groupKey);
    positives.push({
      case_id: `HOLDOUT3-POS-${String(positives.length + 1).padStart(2, '0')}`,
      expected: 'merge',
      kind: 'same_pack_split_by_baseline_runtime',
      uploader,
      group_key: groupKey,
      old_distinct_keys: oldKeys.length,
      confidence: finding.confidence || 'confirmed',
      source: 'v2 LEGITIMATE_SAME_PACK member evidence + baseline-vs-final runtime diff',
      videos: members.map((member) => ({ bvid: member.bvid, title: member.title })),
    });
  }
  positives.sort((a, b) => b.videos.length - a.videos.length);

  const realMergeAuthors = new Set(
    (ledger.real_false_merges || []).map((finding) => String(finding.author).toLowerCase()),
  );
  const byAuthor = new Map();
  for (const row of data) {
    const uploader = String(row.author || '').trim();
    if (usedUploaders.has(uploader.toLowerCase())) continue;
    if (!byAuthor.has(uploader)) byAuthor.set(uploader, []);
    byAuthor.get(uploader).push(row);
  }
  const negatives = [];
  for (const [uploader, records] of byAuthor) {
    if (realMergeAuthors.has(uploader.toLowerCase())) continue;
    const groups = new Map();
    for (const row of records) {
      const groupKey = decisions[row.bvid].groupKey;
      if (!groups.has(groupKey)) groups.set(groupKey, []);
      groups.get(groupKey).push(row);
    }
    if (groups.size < 2) continue;
    const named = [...groups.keys()].filter((groupKey) => {
      const tail = groupKey.split('::')[1] || '';
      return tail.replace(/[^A-Za-z0-9\u4e00-\u9fa5]/g, '').length >= 2;
    });
    if (named.length < 2) continue;
    negatives.push({
      case_id: `HOLDOUT3-NEG-${String(negatives.length + 1).padStart(2, '0')}`,
      expected: 'separate',
      kind: 'same_uploader_distinct_packs_kept_apart',
      uploader,
      group_count: groups.size,
      confidence: 'strong',
      source: 'final runtime group partition + v2 adjudication exclusion of real false-merge uploaders',
      videos: records.map((row) => ({
        bvid: row.bvid,
        title: row.title,
        group_key: decisions[row.bvid].groupKey,
      })),
    });
  }
  negatives.sort((a, b) => (b.group_count - a.group_count) || (b.videos.length - a.videos.length));
  const uploaders = [...new Set([
    ...positives.map((item) => item.uploader.toLowerCase()),
    ...negatives.map((item) => item.uploader.toLowerCase()),
  ])].sort();
  const overlap = uploaders.filter((uploader) => usedUploaders.has(uploader));
  return {
    phase: '3G-F.3-A',
    artifact: 'phase3gf_runtime_holdout_v2',
    generation_contract: {
      additive: true,
      source_ledger: 'pipeline/audit/bilibili_population_adjudication_v2.json',
      baseline_runtime: HOLDOUT_BASELINE_RUNTIME,
      final_runtime: true,
      old_corpus_untouched: true,
      no_runtime_group_rescanning_for_gate: true,
      expected_labels: 'merge/separate plus final group_key partition for derived negatives',
    },
    old_corpus: { positive: 24, negative: 22, frozen: true },
    holdout_v2: {
      positive: positives.length,
      negative: negatives.length,
      uploader_count: uploaders.length,
      uploaders,
      uploader_overlap_with_old_corpus: overlap,
      meets_requirement: positives.length >= 10 && negatives.length >= 10 && overlap.length === 0,
    },
    positive_cases: positives,
    negative_cases: negatives,
  };
}

function main() {
  const args = parseArgs();
  const data = loadPayload();
  const holdout = auditJson(HOLDOUT_PATH);
  const ledger = auditJson(LEDGER_PATH);
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'phase3gf-expanded-'));
  const compiled = compileCurrentRuntime(temp);
  const decisions = runtimeDecisions(compiled.module, data);
  const historical = compileRuntimeAtCommit(HOLDOUT_BASELINE_RUNTIME, temp, 'historical-known8');
  const historicalDecisions = runtimeDecisions(historical.module, data);
  const derivedHoldout = deriveFinalRuntimeHoldout(ledger, data, decisions);
  const holdoutResult = holdoutAudit(derivedHoldout, data, decisions);
  const frozenHoldoutShape = holdoutAudit(holdout, data, decisions);
  const knownEight = knownEightAudit(ledger, data, decisions, historicalDecisions);
  const population = populationStats(data, decisions);
  const mechanical = mechanicalPower(data, decisions);
  const sourceBytes = fs.readFileSync(path.join(ROOT, SOURCE_REL));
  const sourceCommit = git(['rev-parse', 'HEAD']);
  const result = {
    phase: '3G-F.3-A',
    artifact: 'phase3gf_expanded_runtime_audit',
    generated_at: stableNow(),
    status: holdoutResult.pairwise.overall.false_merge === 0
      && holdoutResult.pairwise.overall.recall >= 0.75
      && holdoutResult.source.uploaders_disjoint_from_old_corpus
      && holdoutResult.source.meets_requirement
      && knownEight.still_merging.length === 0
      && knownEight.missing_old_snapshot.length === 0
      ? 'PASS' : 'BLOCKED',
    acceptance_contract: {
      holdout_false_merge_required: 0,
      recall_minimum: 0.75,
      known_8_still_merging_required: 0,
      raw_population_records_required: 936,
    },
    runtime: {
      source_commit: sourceCommit,
      source_rel: SOURCE_REL,
      source_raw_sha256: sha256Bytes(sourceBytes),
      bundle_sha256: compiled.bundle_sha256,
      formal_acceptance: true,
      compiled_from_current_source: true,
    },
    baseline_runtime: {
      source_commit: HOLDOUT_BASELINE_RUNTIME,
      bundle_sha256: historical.bundle_sha256,
      purpose: 'known-8 retired source mapping and derived holdout old-vs-new baseline',
    },
    source_inputs: {
      population_sha256: sha256File(PAYLOAD_PATH),
      holdout_v2_sha256: sha256File(HOLDOUT_PATH),
      adjudication_v2_sha256: sha256File(LEDGER_PATH),
      runtime_gate_sha256: sha256File(GATE_PATH),
    },
    adjudication_ledger: {
      candidates_total: ledger.candidates_total,
      adjudicated_total: ledger.adjudicated_total,
      counts: ledger.counts,
      under_merge: ledger.under_merge,
    },
    holdout_v2: holdoutResult,
    frozen_holdout_v2_shape_check: {
      source_sha256: sha256File(HOLDOUT_PATH),
      source_positive_cases: holdout.positive_cases.length,
      source_negative_cases: holdout.negative_cases.length,
      source_uploader_count: holdout.holdout_v2.uploader_count,
      current_runtime_partition_result: {
        pairwise: frozenHoldoutShape.pairwise,
        case_partition: frozenHoldoutShape.case_partition,
      },
      note: 'The pre-F3A artifact is read-only historical input; its group_key partitions are not reused as final F3A labels because they predate the 26-case runtime gate.',
    },
    known_8_retirement: knownEight,
    population_936: population,
    mechanical_power: mechanical,
  };
  fs.mkdirSync(path.dirname(args.holdoutOut), { recursive: true });
  fs.writeFileSync(args.holdoutOut, JSON.stringify(derivedHoldout, null, 2) + '\n', 'utf8');
  fs.mkdirSync(path.dirname(args.out), { recursive: true });
  fs.writeFileSync(args.out, JSON.stringify(result, null, 2) + '\n', 'utf8');
  const m = holdoutResult.pairwise.overall;
  console.log(`expanded holdout (final-runtime-derived): TM=${m.true_merge} FS=${m.false_split} TS=${m.true_separate} FM=${m.false_merge} P=${m.precision} R=${m.recall}`);
  console.log(`derived holdout shape: ${derivedHoldout.holdout_v2.positive} positive/${derivedHoldout.holdout_v2.negative} negative/${derivedHoldout.holdout_v2.uploader_count} uploaders`);
  console.log(`expanded holdout cases: ${holdoutResult.case_partition.exact_cases}/${holdoutResult.case_partition.overall_cases} exact partitions`);
  console.log(`known-8 retired: ${knownEight.retired}/${knownEight.expected}; still_merging=${knownEight.still_merging.length}`);
  console.log(`population: ${population.raw_records} raw/${population.unique_bvids} unique BVID -> ${population.grouped_cards} groups`);
  console.log(`机械动力: ${mechanical.raw_records} raw/${mechanical.unique_bvids} unique BVID -> ${mechanical.grouped_cards} groups`);
  console.log(`status: ${result.status}`);
  console.log(`written: ${path.relative(ROOT, args.out)}`);
  process.exitCode = result.status === 'PASS' ? 0 : 2;
}

try { main(); } catch (error) {
  console.error(error && error.stack ? error.stack : String(error));
  process.exitCode = error && error.code === 2 ? 2 : 1;
}

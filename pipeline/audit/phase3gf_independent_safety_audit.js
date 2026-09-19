/**
 * Phase 3G-F.3-A independent safety audit.
 *
 * The previous expanded audit selected positive cases from the candidate's
 * current partition and used candidate group_key values as negative labels.
 * This audit freezes membership first, obtains pair labels only from the
 * original evidence + final adjudication, and reports UNKNOWN/UNCOVERED
 * instead of treating them as safe.
 *
 * Exit codes: 0 = independent safety evidence complete and safe,
 * 2 = evidence/runtime safety is blocked or has a measured failure,
 * 1 = input/configuration failure.
 */
const crypto = require('crypto');
const { execFileSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..');
const SOURCE_REL = 'apps/web/src/domain/bilibiliGrouping.ts';
const PAYLOAD_PATH = path.join(ROOT, 'converted_output', 'data', 'bili_data.js');
const EVIDENCE_PATH = path.join(ROOT, 'build', 'audit', 'undermerge_evidence_v2.json');
const LEDGER_PATH = path.join(ROOT, 'pipeline', 'audit', 'bilibili_undermerge_adjudication_v2.json');
const POPULATION_LEDGER_PATH = path.join(ROOT, 'pipeline', 'audit', 'bilibili_population_adjudication_v2.json');
const GATE_PATH = path.join(ROOT, 'pipeline', 'audit', 'confirmed_undermerge_runtime_gate.json');
const RELATION_FIXTURE_PATH = path.join(ROOT, 'pipeline', 'audit', 'fixtures', 'phase3gf_runtime_acceptance.json');
const LEGACY_DERIVED_HOLDOUT_PATH = path.join(ROOT, 'docs', 'audit', 'logs', 'phase3gf_runtime_holdout_v2.json');
const OLD_HOLDOUT_PATH = path.join(ROOT, 'pipeline', 'audit', 'bilibili_population_holdout_v2.json');
const SPLIT_PATH = path.join(ROOT, 'pipeline', 'audit', 'bilibili_grouping_split.json');
const DEFAULT_OUT = path.join(ROOT, 'build', 'audit', 'phase3gf_expanded_runtime_audit.json');
const DEFAULT_HOLDOUT_OUT = path.join(ROOT, 'build', 'audit', 'phase3gf_runtime_holdout_independent.json');
const LEGACY_IMPL = path.join(ROOT, 'pipeline', 'audit', 'fixtures', 'bili_grouping_legacy_impl.js');
const HOLDOUT_BASELINE_RUNTIME = 'ef411d1542433d8fdd7f06ed40946d6626d19252';

const EXPECTED_SOURCE_HASHES = {
  evidence: 'bd8b76a51dba40079f258183ef27cbe438c7e220af972a5fe877a1f9ff2df083',
  ledger: '7a3b4a2889662bb0b035f14d2f1ca3d59d393868e6356100ca1300094c5995df',
  populationLedger: 'a6a6a4f92c10bf0c9d87dfb9501263fd3967405e3d750ae8854282b0602d18a8',
  relationFixture: 'c76674e652de281bbf894cece086c0f85464c5f007e4685e1cfeb439c506b994',
  gate: 'cafec9955c5e589315279b348dc5520a17594bebfc5d43dde08b4a810dfafad7',
  gateGit: '4e91fe1d8bc3c16a8fe1b3cc65be9a64dcc56f47b29b2a218524029ca82a9d90',
  payload: '049fe4c567fabafb4e4c58018b606c1aa23d01d2d1511933856454915e79bebe',
  legacyDerivedHoldout: 'abfe5cdc1a4f30605becdb34ae024689565ed47b2a48cbf8ea0acd3c084ee900',
};

function sha256Bytes(bytes) { return crypto.createHash('sha256').update(bytes).digest('hex'); }
function sha256File(file) { return sha256Bytes(fs.readFileSync(file)); }
function readJson(file) {
  const io = require(path.join(ROOT, 'pipeline', 'audit', 'lib', 'audit_artifact_io.js'));
  return io.readJson(file);
}
function sorted(xs) { return [...xs].sort(); }
function unique(xs) { return [...new Set(xs)]; }
function pairKey(a, b) { return a < b ? `${a}\0${b}` : `${b}\0${a}`; }
function displayPairKey(key) { return key.split('\0'); }
function pairs(items) {
  const out = [];
  for (let i = 0; i < items.length; i++) {
    for (let j = i + 1; j < items.length; j++) out.push([items[i], items[j]]);
  }
  return out;
}
function stable(value) {
  if (Array.isArray(value)) return `[${value.map(stable).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${stable(value[k])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}
function stableSha(value) { return sha256Bytes(Buffer.from(stable(value), 'utf8')); }
function stableNow() {
  return new Date(process.env.SOURCE_DATE_EPOCH
    ? Number(process.env.SOURCE_DATE_EPOCH) * 1000
    : Date.now()).toISOString();
}
function fail(message) {
  const error = new Error(`independent safety audit: ${message}`);
  error.code = 2;
  throw error;
}
function git(args) { return execFileSync('git', args, { cwd: ROOT, encoding: 'utf8' }).trim(); }
function sourceCommitForPath(rel) {
  return git(['log', '-1', '--format=%H', '--', rel]);
}

function parseArgs() {
  const args = process.argv.slice(2);
  const get = (name, fallback) => {
    const i = args.indexOf(name);
    return i >= 0 ? args[i + 1] : fallback;
  };
  return {
    out: get('--out', DEFAULT_OUT),
    holdoutOut: get('--holdout-out', DEFAULT_HOLDOUT_OUT),
    selfTest: args.includes('--self-test'),
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
  fs.writeFileSync(source, execFileSync('git', ['show', `${commit}:${SOURCE_REL}`], { cwd: ROOT, encoding: 'utf8' }));
  fs.writeFileSync(packName, execFileSync('git', ['show', `${commit}:apps/web/src/domain/packName.ts`], { cwd: ROOT, encoding: 'utf8' }));
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

function searchTarget(row) {
  return [row.title || '', row.author || '', row.desc || '', row.mc_version || '',
    ...(row.loaders || []), ...(row.categories || [])].join(' ').toLowerCase();
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

function caseKey(author, groupKeys) { return `${author}||${[...groupKeys].sort().join('|')}`; }

function loadIndependentSources() {
  for (const [name, file, expected] of [
    ['original evidence', EVIDENCE_PATH, EXPECTED_SOURCE_HASHES.evidence],
    ['final adjudication ledger', LEDGER_PATH, EXPECTED_SOURCE_HASHES.ledger],
    ['population adjudication ledger', POPULATION_LEDGER_PATH, EXPECTED_SOURCE_HASHES.populationLedger],
    ['relation fixture', RELATION_FIXTURE_PATH, EXPECTED_SOURCE_HASHES.relationFixture],
    ['runtime gate', GATE_PATH, EXPECTED_SOURCE_HASHES.gate],
    ['population', PAYLOAD_PATH, EXPECTED_SOURCE_HASHES.payload],
    ['legacy derived holdout', LEGACY_DERIVED_HOLDOUT_PATH, EXPECTED_SOURCE_HASHES.legacyDerivedHoldout],
  ]) {
    const actual = sha256File(file);
    if (actual !== expected) fail(`${name} raw-byte hash drift: ${actual} != ${expected}`);
  }
  const evidence = readJson(EVIDENCE_PATH);
  const ledger = readJson(LEDGER_PATH);
  const populationLedger = readJson(POPULATION_LEDGER_PATH);
  const gate = readJson(GATE_PATH);
  const relationFixture = JSON.parse(fs.readFileSync(RELATION_FIXTURE_PATH, 'utf8'));
  const legacyDerived = JSON.parse(fs.readFileSync(LEGACY_DERIVED_HOLDOUT_PATH, 'utf8'));
  const oldHoldout = readJson(OLD_HOLDOUT_PATH);
  const split = readJson(SPLIT_PATH);
  if (evidence.findings.length !== 58 || ledger.findings.length !== 58 || relationFixture.cases.length !== 58) {
    fail('58-case evidence/ledger/relation fixture contract failed');
  }
  if (legacyDerived.positive_cases.length !== 40 || legacyDerived.negative_cases.length !== 62) {
    fail(`legacy derived membership is not 40/62: ${legacyDerived.positive_cases.length}/${legacyDerived.negative_cases.length}`);
  }
  const fixtureSources = relationFixture.source_artifacts || {};
  if (fixtureSources.original_evidence?.sha256 !== EXPECTED_SOURCE_HASHES.evidence) fail('relation fixture evidence provenance drift');
  if (fixtureSources.population?.sha256 !== EXPECTED_SOURCE_HASHES.payload) fail('relation fixture population provenance drift');
  if (fixtureSources.runtime_gate?.working_tree_sha256 !== EXPECTED_SOURCE_HASHES.gate) fail('relation fixture runtime gate raw provenance drift');
  if (fixtureSources.runtime_gate?.git_source_sha256 !== EXPECTED_SOURCE_HASHES.gateGit) fail('relation fixture runtime gate semantic provenance drift');
  const evidenceByKey = new Map(evidence.findings.map((f) => [caseKey(f.author, f.group_keys), f]));
  const ledgerByKey = new Map(ledger.findings.map((f) => [caseKey(f.author, f.group_keys), f]));
  const fixtureByKey = new Map();
  for (const c of relationFixture.cases) {
    if (fixtureByKey.has(c.cluster_key)) fail(`duplicate relation fixture case: ${c.cluster_key}`);
    fixtureByKey.set(c.cluster_key, c);
    if (!evidenceByKey.has(c.cluster_key) || !ledgerByKey.has(c.cluster_key)) fail(`relation fixture source mapping missing: ${c.cluster_key}`);
    const relationLists = [c.relations.must_link, c.relations.cannot_link, c.relations.unknown_pairs];
    const pairSet = new Set();
    for (const list of relationLists) {
      for (const pair of list) {
        if (!Array.isArray(pair) || pair.length !== 2) fail(`bad relation pair: ${c.cluster_key}`);
        const key = pairKey(pair[0], pair[1]);
        if (pairSet.has(key)) fail(`relation pair repeated across partitions: ${c.cluster_key}/${key}`);
        pairSet.add(key);
      }
    }
    const bvids = sorted(c.groups.flatMap((g) => g.members.map((m) => m.bvid)));
    const memberSet = new Set(bvids);
    if (new Set(bvids).size !== bvids.length) fail(`fixture duplicate member: ${c.cluster_key}`);
    const expectedPairCount = bvids.length * (bvids.length - 1) / 2;
    if (pairSet.size !== expectedPairCount) fail(`fixture pair coverage incomplete: ${c.cluster_key}`);
    for (const pair of pairSet) {
      const [a, b] = pair.split('\0');
      if (!memberSet.has(a) || !memberSet.has(b)) fail(`fixture relation member outside case: ${c.cluster_key}`);
    }
  }
  if (relationFixture.coverage?.gate_cases !== 26
    || relationFixture.coverage?.protected_cases !== 32
    || relationFixture.coverage?.gate_unique_bvids !== 80) {
    fail('relation fixture 26/32/80 coverage contract drift');
  }
  for (const c of gate.cases || []) {
    if (!fixtureByKey.has(c.cluster_key)) fail(`runtime gate case missing from relation fixture: ${c.cluster_key}`);
    if (!['CONFIRMED_SAME_PACK', 'STRONG_SAME_PACK'].includes(c.verdict)) {
      fail(`runtime gate contains non-accepted verdict: ${c.cluster_key}`);
    }
  }
  if ((gate.cases || []).length !== 26) fail(`runtime gate case count drift: ${(gate.cases || []).length}`);
  return { evidence, ledger, populationLedger, gate, relationFixture, legacyDerived, oldHoldout, split, evidenceByKey, ledgerByKey, fixtureByKey };
}

function addRelation(catalog, a, b, relation, source, basis) {
  if (a === b) return;
  const key = pairKey(a, b);
  const entry = catalog.get(key);
  const item = { relation, sources: [{ source, basis }] };
  if (!entry) { catalog.set(key, item); return; }
  entry.sources.push({ source, basis });
  // UNKNOWN is evidence insufficiency, not a weaker MUST/CANNOT label.  If a
  // second independent source supplies a directional relation for the same
  // pair, preserve the disagreement as CONFLICT so the audit cannot silently
  // promote an ambiguous pair into a safety label.
  if (entry.relation === 'UNKNOWN' && relation !== 'UNKNOWN') entry.relation = 'CONFLICT';
  else if (relation === 'UNKNOWN' && entry.relation !== 'UNKNOWN') entry.relation = 'CONFLICT';
  else if (relation !== 'UNKNOWN' && entry.relation !== relation) entry.relation = 'CONFLICT';
}

function pairRelationFromFixture(c) {
  return [
    ...c.relations.must_link.map((pair) => ({ pair, relation: 'MUST' })),
    ...c.relations.cannot_link.map((pair) => ({ pair, relation: 'CANNOT' })),
    ...c.relations.unknown_pairs.map((pair) => ({ pair, relation: 'UNKNOWN' })),
  ];
}

function buildIndependentRelationCatalog(sources, data) {
  const catalog = new Map();
  for (const c of sources.relationFixture.cases) {
    for (const item of pairRelationFromFixture(c)) {
      addRelation(catalog, item.pair[0], item.pair[1], item.relation,
        `final-adjudication-relation:${c.cluster_key}`,
        `${c.verdict}; relation fixture derived from original evidence and final adjudication`);
    }
  }
  // The original population ledger contains 100 same-pack evidence sets. It
  // is independent of both the current and historical runtime partitions.
  for (const finding of sources.populationLedger.legitimate_same_pack || []) {
    const members = (finding.evidence?.members || []).map((m) => m.bvid);
    for (const [a, b] of pairs(members)) {
      addRelation(catalog, a, b, 'MUST', `population-ledger:${finding.group_key}`,
        'LEGITIMATE_SAME_PACK member evidence; current group_key not used as a label');
    }
  }
  // Cross-group adjudication is a separate evidence channel from the
  // legitimate_same_pack ledger.  A NOT_UNDER_MERGE finding supplies explicit
  // CANNOT links between its distinct source groups; an UNDER_MERGE finding
  // supplies MUST links across the groups it says are one pack.  Mixed,
  // ambiguous, and unreviewed findings remain UNKNOWN rather than being
  // guessed into either direction.
  for (const finding of sources.populationLedger.cross_group_adjudication || []) {
    const groups = (finding.evidence?.members || [])
      .map((group) => ({
        group_key: group.group_key,
        bvids: (group.records || []).map((record) => record.bvid),
      }))
      .filter((group) => group.bvids.length);
    const verdict = finding.verdict;
    const relation = verdict === 'NOT_UNDER_MERGE'
      ? 'CANNOT'
      : verdict === 'UNDER_MERGE' ? 'MUST' : 'UNKNOWN';
    for (let i = 0; i < groups.length; i++) {
      for (let j = i + 1; j < groups.length; j++) {
        for (const a of groups[i].bvids) for (const b of groups[j].bvids) {
          addRelation(catalog, a, b, relation,
            `population-cross-group:${finding.author}:${verdict}`,
            `${verdict}; independent cross-group adjudication for ${groups[i].group_key} vs ${groups[j].group_key}`);
        }
      }
    }
  }
  for (const spec of KNOWN_EIGHT_SPECS) {
    for (const partition of spec.partitions) {
      for (const [a, b] of pairs(partition.bvids)) {
        addRelation(catalog, a, b, 'MUST', `known-8:${spec.key}`, `retired false-merge identity: ${partition.identity}`);
      }
    }
    for (let i = 0; i < spec.partitions.length; i++) {
      for (let j = i + 1; j < spec.partitions.length; j++) {
        for (const a of spec.partitions[i].bvids) for (const b of spec.partitions[j].bvids) {
          addRelation(catalog, a, b, 'CANNOT', `known-8:${spec.key}`,
            `retired false-merge identity separation: ${spec.partitions[i].identity} != ${spec.partitions[j].identity}`);
        }
      }
    }
  }
  const byBvid = new Map(data.map((row) => [row.bvid, row]));
  for (const [key, entry] of catalog) {
    const [a, b] = displayPairKey(key);
    if (!byBvid.has(a) || !byBvid.has(b)) fail(`independent relation references missing population BVID: ${key}`);
  }
  return catalog;
}

function relationCatalogCounts(catalog) {
  const counts = { MUST: 0, CANNOT: 0, UNKNOWN: 0, CONFLICT: 0 };
  for (const { relation } of catalog.values()) counts[relation] = (counts[relation] || 0) + 1;
  return counts;
}

// These partitions are the identity-level reading of the eight retired
// population false merges. The key/group boundaries are not used to define
// identity; the labels come from the frozen ledger notes and the member title
// evidence in the 936-record payload.
const KNOWN_EIGHT_SPECS = [
  {
    key: '一个小寂哦::星辉死神', fixed_by: 'late_feature_list',
    source_note: '神器收集计划 / 无尽幸运方块大陆 / 全网最全神器 are distinct named packs; 星辉死神 is a feature/Boss token.',
    partitions: [
      { identity: '神器收集计划', bvids: ['BV1KxX5B7EE5'] },
      { identity: '无尽幸运方块大陆', bvids: ['BV13fm7BXEL9', 'BV1Kw2JB2ESX'] },
      { identity: '全网最全神器', bvids: ['BV1cfn1zAEMR'] },
    ],
  },
  {
    key: '一个小寂哦::四叶草', fixed_by: 'late_feature_list',
    source_note: '新泰坦生物与执行之龙是 distinct named packs; 四叶草 is a feature/item token.',
    partitions: [
      { identity: '新泰坦生物', bvids: ['BV1TST76EEJo'] },
      { identity: '执行之龙', bvids: ['BV16iC3BzEGr'] },
    ],
  },
  {
    key: '一个小寂哦::各大主播同款', fixed_by: 'late_feature_list',
    source_note: '幸运方块大全 and 超困难神器泰坦随机合成 are distinct packs; 各大主播同款 is a slogan.',
    partitions: [
      { identity: '幸运方块大全', bvids: ['BV1iBB9B6EpD'] },
      { identity: '超困难神器泰坦随机合成', bvids: ['BV1MZxnzsE2N'] },
    ],
  },
  {
    key: '墨言eclipse::颠覆性的', fixed_by: 'late_feature_list',
    source_note: '摄影奇境 and 千界万锻 are distinct projects; 颠覆性的 is a marketing adjective.',
    partitions: [
      { identity: '摄影奇境', bvids: ['BV1Ljug6yEhC'] },
      { identity: '千界万锻', bvids: ['BV1hA3Y6zEEQ'] },
    ],
  },
  {
    key: '原界环::or not', fixed_by: 'english_function_words',
    source_note: 'Minecraft or Not: Girl&Gun and Maiden or not are distinct named packs; or not is a function-word fragment.',
    partitions: [
      { identity: 'Minecraft or Not: Girl&Gun', bvids: ['BV17ZwjzvEpG'] },
      { identity: 'Maiden or not', bvids: ['BV1XPcXzWEZ4'] },
    ],
  },
  {
    key: '叙利亚自爆民兵::voxy', fixed_by: 'name_slot_disagreement',
    source_note: '你好新蒸程 and 你好新世代 are distinct named packs; voxy is a shared component.',
    partitions: [
      { identity: '你好新蒸程', bvids: ['BV1Kc96BWENb'] },
      { identity: '你好新世代', bvids: ['BV1PbAczPE4o'] },
    ],
  },
  {
    key: 'tibsalta::难度驱动', fixed_by: 'name_slot_disagreement',
    source_note: '抗争之际 and 旅途痕迹 are distinct names; 难度驱动 is a series label.',
    partitions: [
      { identity: '抗争之际', bvids: ['BV1wu411W7dV'] },
      { identity: '旅途痕迹', bvids: ['BV1ok4y1t7u9'] },
    ],
  },
  {
    key: '一个小寂哦::怪物大乱斗', fixed_by: 'competing_edition',
    source_note: '怪物大乱斗手机版 and 怪物大乱斗：重生 are separate generation/edition names.',
    partitions: [
      { identity: '怪物大乱斗手机版', bvids: ['BV1f4Kp6yEBf'] },
      { identity: '怪物大乱斗重生', bvids: ['BV1nRBFBFEFw'] },
    ],
  },
];

function loadFrozenLegacyCases(sources, data) {
  const byBvid = new Map(data.map((row) => [row.bvid, row]));
  const all = [
    ...sources.legacyDerived.positive_cases.map((c) => ({ ...c, legacy_set: 'positive' })),
    ...sources.legacyDerived.negative_cases.map((c) => ({ ...c, legacy_set: 'negative' })),
  ];
  const seen = new Set();
  return all.map((c) => {
    if (seen.has(c.case_id)) fail(`legacy derived case repeated: ${c.case_id}`);
    seen.add(c.case_id);
    const bvids = c.videos.map((v) => v.bvid);
    if (new Set(bvids).size !== bvids.length || bvids.length < 2) fail(`legacy derived case invalid members: ${c.case_id}`);
    for (const bvid of bvids) {
      if (!byBvid.has(bvid)) fail(`legacy derived case missing BVID: ${c.case_id}/${bvid}`);
      if (byBvid.get(bvid).title !== c.videos.find((v) => v.bvid === bvid).title) fail(`legacy derived title drift: ${c.case_id}/${bvid}`);
    }
    return {
      case_id: c.case_id,
      legacy_set: c.legacy_set,
      legacy_expected: c.expected,
      kind: c.kind,
      uploader: c.uploader,
      bvids: sorted(bvids),
      titles: Object.fromEntries(c.videos.map((v) => [v.bvid, v.title])),
      legacy_group_keys_ignored: c.videos.map((v) => ({ bvid: v.bvid, group_key: v.group_key || null })),
      source: c.source,
    };
  });
}

function scorePair(expected, actualSame) {
  if (expected === 'MUST') return actualSame ? 'true_merge' : 'false_split';
  if (expected === 'CANNOT') return actualSame ? 'false_merge' : 'true_separate';
  return 'UNKNOWN';
}

function classifyFrozenCase(caseObj, decisions, catalog) {
  const target = caseObj.legacy_expected === 'merge' ? 'MUST' : 'CANNOT';
  const pairResults = [];
  const counts = { MUST: 0, CANNOT: 0, UNKNOWN: 0, UNCOVERED: 0, CONFLICT: 0 };
  const outcomes = { true_merge: 0, false_split: 0, true_separate: 0, false_merge: 0 };
  for (const [a, b] of pairs(caseObj.bvids)) {
    const relation = catalog.get(pairKey(a, b));
    const expected = relation?.relation || 'UNCOVERED';
    counts[expected] = (counts[expected] || 0) + 1;
    const actualSame = decisions[a].groupKey === decisions[b].groupKey;
    const outcome = scorePair(expected, actualSame);
    outcomes[outcome] = (outcomes[outcome] || 0) + 1;
    pairResults.push({
      a, b, expected_relation: expected, actual_same_group: actualSame,
      actual_group_keys: [decisions[a].groupKey, decisions[b].groupKey],
      sources: relation?.sources || [], outcome,
    });
  }
  const contradictory = target === 'MUST' ? counts.CANNOT + counts.CONFLICT : counts.MUST + counts.CONFLICT;
  const unknown = counts.UNKNOWN + counts.UNCOVERED;
  const disposition = contradictory ? 'CONFLICT_WITH_INDEPENDENT_RELATION' : unknown ? 'UNKNOWN_COVERAGE' : 'INDEPENDENTLY_LABELED';
  const exact = disposition === 'INDEPENDENTLY_LABELED'
    && ((target === 'MUST' && outcomes.false_split === 0) || (target === 'CANNOT' && outcomes.false_merge === 0));
  return {
    case_id: caseObj.case_id,
    legacy_set: caseObj.legacy_set,
    uploader: caseObj.uploader,
    legacy_expected: caseObj.legacy_expected,
    bvids: caseObj.bvids,
    title_by_bvid: caseObj.titles,
    legacy_group_keys_ignored: caseObj.legacy_group_keys_ignored,
    pair_count: caseObj.bvids.length * (caseObj.bvids.length - 1) / 2,
    relation_counts: counts,
    candidate_outcomes: outcomes,
    disposition,
    exact_candidate_result: exact,
    pair_results: pairResults,
    source: caseObj.source,
  };
}

function relationMetrics(caseResults) {
  const totals = caseResults.reduce((out, c) => {
    for (const key of ['true_merge', 'false_split', 'true_separate', 'false_merge']) out[key] += c.candidate_outcomes[key] || 0;
    for (const key of ['UNKNOWN', 'UNCOVERED', 'CONFLICT']) out[key.toLowerCase()] += c.relation_counts[key] || 0;
    return out;
  }, { true_merge: 0, false_split: 0, true_separate: 0, false_merge: 0, unknown: 0, uncovered: 0, conflict: 0 });
  const knownPositive = totals.true_merge + totals.false_split;
  const knownNegative = totals.true_separate + totals.false_merge;
  return {
    ...totals,
    labeled_pairs: knownPositive + knownNegative,
    precision: +((totals.true_merge + totals.false_merge)
      ? totals.true_merge / (totals.true_merge + totals.false_merge) : 1).toFixed(4),
    recall: +(knownPositive ? totals.true_merge / knownPositive : 0).toFixed(4),
    false_merge_rate: +(knownNegative ? totals.false_merge / knownNegative : 0).toFixed(4),
    false_split_rate: +(knownPositive ? totals.false_split / knownPositive : 0).toFixed(4),
  };
}

function auditFrozenHoldout(cases, decisions, catalog, sources) {
  const results = cases.map((c) => classifyFrozenCase(c, decisions, catalog));
  const positive = results.filter((c) => c.legacy_set === 'positive');
  const negative = results.filter((c) => c.legacy_set === 'negative');
  const independentlyLabeled = results.filter((c) => c.disposition === 'INDEPENDENTLY_LABELED');
  const validPositive = independentlyLabeled.filter((c) => c.legacy_set === 'positive');
  const validNegative = independentlyLabeled.filter((c) => c.legacy_set === 'negative');
  const uploaders = sorted(unique(independentlyLabeled.map((c) => c.uploader.toLowerCase())));
  const oldUploaders = new Set([
    ...sources.split.dev.uploaders,
    ...sources.split.holdout.uploaders,
  ].map((x) => String(x).toLowerCase()));
  const overlap = uploaders.filter((x) => oldUploaders.has(x));
  const frozenLabels = results.map((c) => ({
    case_id: c.case_id, expected: c.legacy_expected, bvids: c.bvids,
    disposition: c.disposition,
    pair_labels: c.pair_results.map((p) => [p.a, p.b, p.expected_relation]),
  }));
  const metrics = relationMetrics(results);
  const dispositionCounts = results.reduce((out, c) => {
    out[c.disposition] = (out[c.disposition] || 0) + 1;
    return out;
  }, {});
  return {
    source: {
      artifact: 'docs/audit/logs/phase3gf_runtime_holdout_v2.json',
      raw_sha256: EXPECTED_SOURCE_HASHES.legacyDerivedHoldout,
      legacy_derived_positive_cases: positive.length,
      legacy_derived_negative_cases: negative.length,
      legacy_derived_total_cases: results.length,
      membership_frozen_before_candidate_run: true,
      legacy_group_keys_used_as_labels: false,
      candidate_output_used_to_select_members: false,
    },
    independent_relation_labels: {
      sha256: stableSha(frozenLabels),
      relation_catalog_sha256: stableSha([...catalog.entries()].sort(([a], [b]) => a.localeCompare(b))),
      positive_cases: validPositive.length,
      negative_cases: validNegative.length,
      total_cases: independentlyLabeled.length,
      uploader_count: uploaders.length,
      uploader_overlap_with_old_corpus: overlap,
      generation_contract_met: validPositive.length >= 10 && validNegative.length >= 10
        && independentlyLabeled.length === results.length && overlap.length === 0,
    },
    pairwise: metrics,
    case_partition: {
      overall_cases: results.length,
      independently_labeled_cases: independentlyLabeled.length,
      independently_labeled_positive: validPositive.length,
      independently_labeled_negative: validNegative.length,
      exact_candidate_cases: results.filter((c) => c.exact_candidate_result).length,
      conflict_cases: results.filter((c) => c.disposition === 'CONFLICT_WITH_INDEPENDENT_RELATION').length,
      unknown_coverage_cases: results.filter((c) => c.disposition === 'UNKNOWN_COVERAGE').length,
      disposition_counts: dispositionCounts,
    },
    migration: {
      old_derived_40_62: results.map((c) => ({
        case_id: c.case_id,
        old_set: c.legacy_set,
        uploader: c.uploader,
        members: c.bvids,
        disposition: c.disposition,
        relation_counts: c.relation_counts,
        candidate_outcomes: c.candidate_outcomes,
        note: c.disposition === 'CONFLICT_WITH_INDEPENDENT_RELATION'
          ? 'Old negative/positive label conflicts with an independently sourced pair relation; retained, not silently relabeled.'
          : c.disposition === 'UNKNOWN_COVERAGE'
            ? 'Independent source does not cover every pair; retained as UNKNOWN, not counted as safety PASS.'
            : 'Independent relation coverage is complete for this frozen case.',
      })),
    },
    cases: results,
  };
}

function addGroupPairs(groups, pairScopes, scopeName) {
  for (const members of groups.values()) {
    if (members.length < 2) continue;
    for (const [a, b] of pairs(members)) {
      const key = pairKey(a, b);
      const entry = pairScopes.get(key) || new Set();
      entry.add(scopeName);
      pairScopes.set(key, entry);
    }
  }
}

function populationSafetyAudit(data, decisions, historicalDecisions, catalog, frozenCases) {
  const currentGroups = groupMembers(data, decisions);
  const historicalGroups = groupMembers(data, historicalDecisions);
  const scopes = new Map();
  addGroupPairs(currentGroups, scopes, 'current_multimember_group');
  const historicalPairs = new Set();
  for (const members of historicalGroups.values()) {
    if (members.length < 2) continue;
    for (const [a, b] of pairs(members)) historicalPairs.add(pairKey(a, b));
  }
  const currentPairs = new Set();
  for (const [key, labels] of scopes) if (labels.has('current_multimember_group')) currentPairs.add(key);
  for (const key of new Set([...currentPairs, ...historicalPairs])) {
    if (currentPairs.has(key) !== historicalPairs.has(key)) {
      const labels = scopes.get(key) || new Set();
      labels.add('changed_vs_1bee6de');
      scopes.set(key, labels);
    }
  }
  for (const frozen of frozenCases) {
    for (const [a, b] of pairs(frozen.bvids)) {
      const key = pairKey(a, b);
      const labels = scopes.get(key) || new Set();
      labels.add('legacy_40_62_review_set');
      scopes.set(key, labels);
    }
  }
  const counts = {
    confirmed_same_pack: 0,
    false_split: 0,
    confirmed_false_merges: 0,
    audited_safety: 0,
    unknown_evidence: 0,
    uncovered: 0,
    relation_conflict: 0,
  };
  const examples = { confirmed_false_merges: [], unknown_evidence: [], uncovered: [], changed_vs_1bee6de: [] };
  const pairResults = [];
  for (const [key, labels] of scopes) {
    const [a, b] = displayPairKey(key);
    const relation = catalog.get(key)?.relation || 'UNCOVERED';
    const actualSame = decisions[a].groupKey === decisions[b].groupKey;
    let classification;
    if (relation === 'MUST') classification = actualSame ? 'confirmed_same_pack' : 'false_split';
    else if (relation === 'CANNOT') classification = actualSame ? 'confirmed_false_merges' : 'audited_safety';
    else if (relation === 'UNKNOWN') classification = 'unknown_evidence';
    else if (relation === 'CONFLICT') classification = 'relation_conflict';
    else classification = 'uncovered';
    counts[classification]++;
    const result = {
      a, b, scopes: sorted(labels), relation, actual_same_group: actualSame,
      actual_group_keys: [decisions[a].groupKey, decisions[b].groupKey],
      sources: catalog.get(key)?.sources || [], classification,
    };
    pairResults.push(result);
    if (classification === 'confirmed_false_merges' && examples.confirmed_false_merges.length < 50) examples.confirmed_false_merges.push(result);
    if (classification === 'unknown_evidence' && examples.unknown_evidence.length < 50) examples.unknown_evidence.push(result);
    if (classification === 'uncovered' && examples.uncovered.length < 50) examples.uncovered.push(result);
    if (labels.has('changed_vs_1bee6de') && examples.changed_vs_1bee6de.length < 50) examples.changed_vs_1bee6de.push(result);
  }
  const scopeCounts = {};
  for (const name of ['current_multimember_group', 'changed_vs_1bee6de', 'legacy_40_62_review_set']) {
    scopeCounts[name] = pairResults.filter((r) => r.scopes.includes(name)).length;
  }
  const changedGroups = sorted(unique(pairResults.filter((r) => r.scopes.includes('changed_vs_1bee6de'))
    .flatMap((r) => r.actual_group_keys)));
  return {
    status: counts.confirmed_false_merges === 0 && counts.false_split === 0 && counts.relation_conflict === 0
      && counts.unknown_evidence === 0 && counts.uncovered === 0 ? 'PASS' : 'BLOCKED',
    scope: {
      current_multimember_groups: [...currentGroups.values()].filter((x) => x.length > 1).length,
      current_multimember_records: [...currentGroups.values()].filter((x) => x.length > 1).reduce((n, x) => n + x.length, 0),
      historical_multimember_groups: [...historicalGroups.values()].filter((x) => x.length > 1).length,
      pair_counts: scopeCounts,
      changed_group_key_count: changedGroups.length,
      changed_group_keys_sample: changedGroups.slice(0, 100),
      candidate_group_keys_are_measurements_only: true,
    },
    coverage: counts,
    pair_results: pairResults,
    pair_results_sample: pairResults.filter((r) => r.scopes.includes('changed_vs_1bee6de') || r.classification !== 'audited_safety').slice(0, 500),
    examples,
  };
}

function currentRelationForPair(a, b, decisions) {
  return decisions[a].groupKey === decisions[b].groupKey ? 'SAME_GROUP' : 'DIFFERENT_GROUP';
}

function knownEightAudit(decisions, catalog) {
  const cases = [];
  for (let index = 0; index < KNOWN_EIGHT_SPECS.length; index++) {
    const spec = KNOWN_EIGHT_SPECS[index];
    const members = spec.partitions.flatMap((p) => p.bvids);
    const expectedPairs = [];
    for (let i = 0; i < spec.partitions.length; i++) {
      for (let j = i; j < spec.partitions.length; j++) {
        if (i === j) for (const [a, b] of pairs(spec.partitions[i].bvids)) expectedPairs.push({ a, b, expected: 'MUST', identity: spec.partitions[i].identity });
        else for (const a of spec.partitions[i].bvids) for (const b of spec.partitions[j].bvids) expectedPairs.push({ a, b, expected: 'CANNOT', identity: `${spec.partitions[i].identity} != ${spec.partitions[j].identity}` });
      }
    }
    const relationPairs = expectedPairs.map((p) => ({
      ...p,
      current_relation: currentRelationForPair(p.a, p.b, decisions),
      source_relation: catalog.get(pairKey(p.a, p.b))?.relation || 'UNCOVERED',
      sources: catalog.get(pairKey(p.a, p.b))?.sources || [],
    }));
    const stillMerging = relationPairs.filter((p) => p.expected === 'CANNOT' && p.current_relation === 'SAME_GROUP');
    const isolated = members[0];
    const remaining = members.slice(1);
    const controls = [];
    const faultIdentity = {};
    for (const partition of spec.partitions) for (const bvid of partition.bvids) faultIdentity[bvid] = partition.identity;
    if (remaining.length < 2) {
      const controlSpec = KNOWN_EIGHT_SPECS[(index + 1) % KNOWN_EIGHT_SPECS.length];
      controls.push(controlSpec.partitions[0].bvids[0]);
      faultIdentity[controls[0]] = `supplemental:${controlSpec.key}:${controlSpec.partitions[0].identity}`;
    }
    const merged = [...remaining, ...controls];
    const faultGroup = `__known8_fault_${index + 1}`;
    const faultSingleton = `__known8_fault_isolated_${index + 1}`;
    const faultDecisions = { ...decisions };
    for (const bvid of merged) faultDecisions[bvid] = { ...decisions[bvid], groupKey: faultGroup };
    faultDecisions[isolated] = { ...decisions[isolated], groupKey: faultSingleton };
    let injectedCannotPair;
    const injectedPairs = [];
    for (const a of merged) for (const b of merged) {
      if (a >= b) continue;
      if (faultIdentity[a] && faultIdentity[b] && faultIdentity[a] !== faultIdentity[b]) {
        injectedPairs.push({ a, b, expected_relation: 'CANNOT' });
      }
    }
    injectedCannotPair = injectedPairs[0] || null;
    cases.push({
      key: spec.key,
      fixed_by: spec.fixed_by,
      source_note: spec.source_note,
      source_member_count: members.length,
      source_bvids: members,
      identity_partitions: spec.partitions,
      original_error_pairs: relationPairs.filter((p) => p.expected === 'CANNOT'),
      current_pairs: relationPairs,
      still_merging: stillMerging,
      fault_injection: {
        model: 'all original members remain in one erroneous group except one isolated member',
        isolated_bvid: isolated,
        merged_remaining_bvids: merged,
        supplemental_control_bvid: controls[0] || null,
        injected_cannot_pair: injectedCannotPair,
        detected_false_merge: injectedPairs.length > 0,
        note: controls.length ? 'Two-member original case requires a supplemental independently separated control to leave an erroneous pair after isolating one original member.' : null,
      },
    });
  }
  return {
    expected: 8,
    checked: cases.length,
    retired_by_pair: cases.filter((c) => c.still_merging.length === 0).length,
    still_merging_cases: cases.filter((c) => c.still_merging.length > 0).map((c) => c.key),
    fault_injection_passed: cases.filter((c) => c.fault_injection.detected_false_merge).length,
    fault_injection_failed: cases.filter((c) => !c.fault_injection.detected_false_merge).map((c) => c.key),
    cases,
  };
}

function decisionLabelSnapshot(decisions) {
  return Object.keys(decisions).sort().map((bvid) => [bvid, decisions[bvid].groupKey]);
}

function selfTest(sources, data, catalog, compiled = null, suppliedDecisions = null) {
  const cases = loadFrozenLegacyCases(sources, data);
  const frozenA = cases.map((c) => ({ case_id: c.case_id, expected: c.legacy_expected, bvids: c.bvids }));
  const frozenB = loadFrozenLegacyCases(sources, data).map((c) => ({ case_id: c.case_id, expected: c.legacy_expected, bvids: c.bvids }));
  if (stableSha(frozenA) !== stableSha(frozenB)) throw new Error('frozen labels changed across generator rerun');
  const temp = compiled ? null : fs.mkdtempSync(path.join(os.tmpdir(), 'phase3gf-independent-self-test-'));
  const runtime = compiled || compileCurrentRuntime(temp);
  const decisions = suppliedDecisions || runtimeDecisions(runtime.module, data);
  const mustEntry = [...catalog.entries()].find(([, x]) => x.relation === 'MUST');
  const cannotEntry = [...catalog.entries()].find(([, x]) => x.relation === 'CANNOT');
  if (!mustEntry || !cannotEntry) throw new Error('self-test requires independent MUST and CANNOT pairs');
  const [mustA, mustB] = displayPairKey(mustEntry[0]);
  const [cannotA, cannotB] = displayPairKey(cannotEntry[0]);
  const splitInjected = { ...decisions, [mustB]: { ...decisions[mustB], groupKey: '__independent_self_test_split__' } };
  const mergeInjected = { ...decisions, [cannotB]: { ...decisions[cannotB], groupKey: decisions[cannotA].groupKey } };
  const mustActuallySplit = splitInjected[mustA].groupKey !== splitInjected[mustB].groupKey;
  const cannotActuallyMerged = mergeInjected[cannotA].groupKey === mergeInjected[cannotB].groupKey;
  const mustSplitOutcome = scorePair('MUST', !mustActuallySplit);
  const cannotMergeOutcome = scorePair('CANNOT', cannotActuallyMerged);
  if (mustSplitOutcome !== 'false_split') throw new Error(`must-link split injection did not produce FS: ${mustA}/${mustB} => ${JSON.stringify([decisions[mustA]?.groupKey, decisions[mustB]?.groupKey, splitInjected[mustA]?.groupKey, splitInjected[mustB]?.groupKey])}`);
  if (cannotMergeOutcome !== 'false_merge') throw new Error(`cannot-link merge injection did not produce FM: ${cannotA}/${cannotB} => ${JSON.stringify([decisions[cannotA]?.groupKey, decisions[cannotB]?.groupKey, mergeInjected[cannotA]?.groupKey, mergeInjected[cannotB]?.groupKey])}`);
  const candidateIndependent = cases.map((c) => ({ case_id: c.case_id, expected: c.legacy_expected, bvids: c.bvids }));
  if (stableSha(frozenA) !== stableSha(candidateIndependent)) throw new Error('candidate output altered frozen labels');
  const rerun = runtimeDecisions(runtime.module, data);
  const labelsStable = stableSha(decisionLabelSnapshot(decisions)) === stableSha(decisionLabelSnapshot(rerun));
  if (!labelsStable) throw new Error('runtime rerun changed candidate labels');
  const result = {
    frozen_labels_sha256: stableSha(frozenA),
    candidate_bundle_sha256: runtime.bundle_sha256,
    runtime_rerun_labels_stable: labelsStable,
    candidate_output_used_to_generate_labels: false,
    must_link_split_injection: { pair: [mustA, mustB], actual_split: mustActuallySplit, outcome: mustSplitOutcome },
    cannot_link_merge_injection: { pair: [cannotA, cannotB], actual_merge: cannotActuallyMerged, outcome: cannotMergeOutcome },
  };
  console.log(`self-test: frozen labels deterministic; MUST split => ${mustSplitOutcome}; CANNOT merge => ${cannotMergeOutcome}; runtime rerun stable`);
  return result;
}

function main() {
  const args = parseArgs();
  const data = loadPayload();
  const sources = loadIndependentSources();
  const catalog = buildIndependentRelationCatalog(sources, data);
  const frozenCases = loadFrozenLegacyCases(sources, data);
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'phase3gf-independent-'));
  const compiled = compileCurrentRuntime(temp);
  const decisions = runtimeDecisions(compiled.module, data);
  const independenceSelfTest = selfTest(sources, data, catalog, compiled, decisions);
  if (args.selfTest) return;
  const historical = compileRuntimeAtCommit(HOLDOUT_BASELINE_RUNTIME, temp, 'historical-1bee6de');
  const historicalDecisions = runtimeDecisions(historical.module, data);
  const holdout = auditFrozenHoldout(frozenCases, decisions, catalog, sources);
  const knownEight = knownEightAudit(decisions, catalog);
  const population = populationSafetyAudit(data, decisions, historicalDecisions, catalog, frozenCases);
  const populationStatsResult = populationStats(data, decisions);
  const mechanical = mechanicalPower(data, decisions);
  const sourceBytes = fs.readFileSync(path.join(ROOT, SOURCE_REL));
  const runtimeSourceCommit = sourceCommitForPath(SOURCE_REL);
  const result = {
    phase: '3G-F.3-A',
    artifact: 'phase3gf_expanded_runtime_audit_independent',
    generated_at: stableNow(),
    status: holdout.independent_relation_labels.generation_contract_met
      && holdout.pairwise.false_merge === 0
      && holdout.pairwise.false_split === 0
      && knownEight.still_merging_cases.length === 0
      && knownEight.fault_injection_failed.length === 0
      && population.status === 'PASS'
      ? 'PASS' : 'BLOCKED',
    acceptance_contract: {
      independent_labels_required: true,
      unknown_or_uncovered_not_safe: true,
      frozen_positive_denominator: 40,
      frozen_negative_denominator: 62,
      population_false_merge_required: 0,
      population_false_split_required: 0,
      known_8_pair_retirement_required: 8,
      known_8_fault_injection_required: 8,
      raw_population_records_required: 936,
    },
    runtime: {
      audit_head: git(['rev-parse', 'HEAD']),
      source_commit: runtimeSourceCommit,
      source_rel: SOURCE_REL,
      source_raw_sha256: sha256Bytes(sourceBytes),
      bundle_sha256: compiled.bundle_sha256,
      compiled_from_current_source: true,
      runtime_unchanged_from_dd1f624: runtimeSourceCommit === 'dd1f62445695d3455c2b9f67d02d7d700a91eff6',
    },
    baseline_runtime: {
      source_commit: HOLDOUT_BASELINE_RUNTIME,
      bundle_sha256: historical.bundle_sha256,
      purpose: 'historical pair boundary only; never an identity label source',
    },
    independence_self_test: independenceSelfTest,
    source_inputs: {
      population_sha256: sha256File(PAYLOAD_PATH),
      original_evidence_sha256: sha256File(EVIDENCE_PATH),
      final_adjudication_sha256: sha256File(LEDGER_PATH),
      population_adjudication_sha256: sha256File(POPULATION_LEDGER_PATH),
      runtime_gate_sha256: sha256File(GATE_PATH),
      relation_fixture_sha256: sha256File(RELATION_FIXTURE_PATH),
      legacy_derived_holdout_sha256: sha256File(LEGACY_DERIVED_HOLDOUT_PATH),
      old_holdout_v2_sha256: sha256File(OLD_HOLDOUT_PATH),
      relation_catalog_sha256: stableSha([...catalog.entries()].sort(([a], [b]) => a.localeCompare(b))),
      raw_byte_hashes_are_pre_parse: true,
      semantic_sha256: {
        population: stableSha(data),
        original_evidence: stableSha(sources.evidence),
        final_adjudication: stableSha(sources.ledger),
        population_adjudication: stableSha(sources.populationLedger),
        runtime_gate: stableSha(sources.gate),
        relation_fixture: stableSha(sources.relationFixture),
        legacy_derived_holdout: stableSha(sources.legacyDerived),
        old_holdout_v2: stableSha(sources.oldHoldout),
      },
      gzip_json_reader: 'pipeline/audit/lib/audit_artifact_io.js',
    },
    frozen_relation_source: {
      evidence_findings: sources.evidence.findings.length,
      final_adjudication_findings: sources.ledger.findings.length,
      population_ledger_same_pack_sets: (sources.populationLedger.legitimate_same_pack || []).length,
      relation_fixture_cases: sources.relationFixture.cases.length,
      relation_catalog_counts: relationCatalogCounts(catalog),
      labels_derive_from_candidate_output: false,
      candidate_group_keys_are_measurements_only: true,
      unknown_relation_policy: 'reported as UNKNOWN/UNCOVERED and excluded from safety PASS',
    },
    holdout_independent: holdout,
    known_8_pair_audit: knownEight,
    population_936: {
      stats: populationStatsResult,
      safety_audit: population,
    },
    mechanical_power: mechanical,
  };
  fs.mkdirSync(path.dirname(args.holdoutOut), { recursive: true });
  fs.writeFileSync(args.holdoutOut, JSON.stringify({
    phase: result.phase,
    artifact: 'phase3gf_runtime_holdout_independent',
    generated_at: result.generated_at,
    runtime_source_commit: runtimeSourceCommit,
    candidate_bundle_sha256: compiled.bundle_sha256,
    source_inputs: result.source_inputs,
    holdout: holdout,
  }, null, 2) + '\n', 'utf8');
  fs.mkdirSync(path.dirname(args.out), { recursive: true });
  fs.writeFileSync(args.out, JSON.stringify(result, null, 2) + '\n', 'utf8');
  const m = holdout.pairwise;
  console.log(`independent frozen holdout: legacy=${holdout.source.legacy_derived_positive_cases}/${holdout.source.legacy_derived_negative_cases}`);
  console.log(`independent valid cases: ${holdout.independent_relation_labels.positive_cases}/${holdout.independent_relation_labels.negative_cases}; UNKNOWN=${holdout.case_partition.unknown_coverage_cases}; CONFLICT=${holdout.case_partition.conflict_cases}`);
  console.log(`independent pairs: TM=${m.true_merge} FS=${m.false_split} TS=${m.true_separate} FM=${m.false_merge} UNKNOWN=${m.unknown} UNCOVERED=${m.uncovered}`);
  console.log(`known-8 pair retirement: ${knownEight.retired_by_pair}/${knownEight.expected}; fault injection=${knownEight.fault_injection_passed}/${knownEight.expected}`);
  console.log(`population safety: FM=${population.coverage.confirmed_false_merges} FS=${population.coverage.false_split} audited_safe=${population.coverage.audited_safety} CONFLICT=${population.coverage.relation_conflict} UNKNOWN=${population.coverage.unknown_evidence} UNCOVERED=${population.coverage.uncovered}`);
  console.log(`population: ${populationStatsResult.raw_records} raw/${populationStatsResult.unique_bvids} unique BVID -> ${populationStatsResult.grouped_cards} groups`);
  console.log(`机械动力: ${mechanical.raw_records} raw/${mechanical.unique_bvids} unique BVID -> ${mechanical.grouped_cards} groups`);
  console.log(`status: ${result.status}`);
  console.log(`written: ${path.relative(ROOT, args.out)}`);
  process.exitCode = result.status === 'PASS' ? 0 : 2;
}

module.exports = { main, selfTest };

try { if (require.main === module) main(); } catch (error) {
  console.error(error && error.stack ? error.stack : String(error));
  process.exitCode = error && error.code === 2 ? 2 : 1;
}

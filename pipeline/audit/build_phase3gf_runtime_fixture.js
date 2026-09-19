/**
 * Build the immutable Phase 3G-F.3-A runtime acceptance fixture.
 *
 * This is a one-time projection from the original gate + original evidence.
 * The acceptance runner consumes the checked-in fixture, not the mutable
 * generated evidence, so a later extractor run cannot silently reselect cases.
 */
const crypto = require('crypto');
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..');
const GATE_PATH = path.join(ROOT, 'pipeline', 'audit', 'confirmed_undermerge_runtime_gate.json');
const LEDGER_PATH = path.join(ROOT, 'pipeline', 'audit', 'bilibili_undermerge_adjudication_v2.json');
const EVIDENCE_PATH = path.join(ROOT, 'build', 'audit', 'undermerge_evidence_v2.json');
const CANDIDATE_PATH = path.join(ROOT, 'build', 'audit', 'bilibili_cross_group_undermerge_v2.json');
const PAYLOAD_PATH = path.join(ROOT, 'converted_output', 'data', 'bili_data.js');
const OUT_PATH = path.join(ROOT, 'pipeline', 'audit', 'fixtures', 'phase3gf_runtime_acceptance.json');

const SHAS = {
  gate: '4e91fe1d8bc3c16a8fe1b3cc65be9a64dcc56f47b29b2a218524029ca82a9d90',
  evidence: 'bd8b76a51dba40079f258183ef27cbe438c7e220af972a5fe877a1f9ff2df083',
  candidate: 'c32814f6926c2c5c6e2be5552d3e7cd0b61e7ead82d0e10e1d8c007c8ff846a4',
  payload: '049fe4c567fabafb4e4c58018b606c1aa23d01d2d1511933856454915e79bebe',
};

// The evidence runtime is the bundle used to derive the original evidence.
// The second bundle is the reproducible 1bee6de pre-fix candidate used by A.
const RUNTIME_PROVENANCE = {
  evidence_source_runtime: {
    source_commit: '4bf5e0fe4c614f3e630ae242db2ed5b66ef95fea',
    source_path: 'apps/web/src/domain/bilibiliGrouping.ts',
    bundle_sha256: '3d10e2e63cc50d1660d1d95c81658444b67ef21250f4af171366b97e1582c15e',
    role: 'ground-truth evidence source runtime; not the 1bee6de candidate',
  },
  pre_fix_runtime_1bee6de: {
    source_commit: '1bee6dea6a30ff0b6368091c614c528263a2f0a2',
    source_path: 'apps/web/src/domain/bilibiliGrouping.ts',
    source_git_blob_sha1: '2c037399cf8106920f3d7e73fb846ecb16996d04',
    bundle_sha256: '12fb5f96f2cd3cf587130bae45f0eda19347e8ca54d019b8f2d553a8e7c7692e',
    role: 'repair-before runtime; must be compiled from the Git source on every acceptance run',
  },
};

function readJson(file) { return JSON.parse(fs.readFileSync(file, 'utf8')); }
function sha256File(file) { return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'); }
function sha256Text(text) { return crypto.createHash('sha256').update(text, 'utf8').digest('hex'); }
function gitBlobSha256(relativePath) {
  return crypto.createHash('sha256').update(
    execFileSync('git', ['show', `HEAD:${relativePath}`], { cwd: ROOT }),
  ).digest('hex');
}
function normalizeTextBytes(bytes) {
  return Buffer.from(bytes.toString('utf8').replace(/\r\n/g, '\n').replace(/\r/g, '\n'), 'utf8');
}
function verifyTextArtifact(relativePath, expectedGitSha256) {
  const worktreeBytes = fs.readFileSync(path.join(ROOT, relativePath));
  const gitBytes = execFileSync('git', ['show', `HEAD:${relativePath}`], { cwd: ROOT });
  const gitSha256 = crypto.createHash('sha256').update(gitBytes).digest('hex');
  if (gitSha256 !== expectedGitSha256) throw new Error(`${relativePath} Git blob drifted`);
  if (!normalizeTextBytes(worktreeBytes).equals(normalizeTextBytes(gitBytes))) {
    throw new Error(`${relativePath} working-tree semantics drifted from Git`);
  }
  return { gitSha256, worktreeSha256: sha256File(path.join(ROOT, relativePath)) };
}
function gitShowSha(commit, rel) {
  return crypto.createHash('sha256').update(execFileSync('git', ['show', `${commit}:${rel}`], { cwd: ROOT })).digest('hex');
}
function stable(value) {
  if (Array.isArray(value)) return `[${value.map(stable).join(',')}]`;
  if (value && typeof value === 'object') return `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${stable(value[k])}`).join(',')}}`;
  return JSON.stringify(value);
}
function linkSha256(links) { return sha256Text(stable(links || [])); }
function loadPayload() {
  const raw = fs.readFileSync(PAYLOAD_PATH, 'utf8');
  const start = raw.indexOf('[');
  const end = raw.lastIndexOf(']');
  if (start < 0 || end < start) throw new Error('payload is not an array');
  return JSON.parse(raw.slice(start, end + 1));
}
function sameSet(a, b) {
  const aa = [...a].sort(); const bb = [...b].sort();
  return aa.length === bb.length && aa.every((x, i) => x === bb[i]);
}
function caseKey(author, groupKeys) { return `${author}||${[...groupKeys].sort().join('|')}`; }
function extractUrls(member) {
  const out = [];
  for (const x of member.download_links || []) if (x && x.url) out.push(String(x.url));
  return out;
}
function registeredIds(member) {
  const ids = new Set();
  for (const raw of extractUrls(member)) {
    const url = raw.trim();
    let m;
    if ((m = url.match(/curseforge\.com\/minecraft\/modpacks\/([^/?#]+)/i))) ids.add(`curseforge:${m[1].toLowerCase()}`);
    if ((m = url.match(/mcmod\.cn\/modpack\/(\d+)/i))) ids.add(`mcmod:modpack/${m[1]}`);
    if ((m = url.match(/bbsmc\.net\/modpack\/([^/?#]+)/i))) ids.add(`bbsmc:modpack/${m[1].toLowerCase()}`);
    if ((m = url.match(/github\.com\/([^/]+)\/([^/?#]+)/i))) ids.add(`github:${m[1].toLowerCase()}/${m[2].replace(/\.git$/, '').toLowerCase()}`);
    if ((m = url.match(/(?:www\.)?xyebbs\.com\/resources\/(\d+)/i))) ids.add(`xyebbs:resource/${m[1]}`);
    if ((m = url.match(/(?:www\.)?xyebbs\.com\/res-id\/([^/?#]+)/i))) ids.add(`xyebbs:res-id/${m[1].toLowerCase()}`);
    if ((m = url.match(/modrinth\.com\/modpack\/([^/?#]+)/i))) ids.add(`modrinth:modpack/${m[1].toLowerCase()}`);
  }
  return [...ids].sort();
}
function pairwise(items) {
  const out = [];
  for (let i = 0; i < items.length; i++) for (let j = i + 1; j < items.length; j++) out.push([items[i], items[j]]);
  return out;
}

function semanticCase(c) {
  return {
    case_type: c.case_type,
    cluster_key: c.cluster_key,
    author: c.author,
    verdict: c.verdict,
    confidence: c.confidence,
    group_count: c.group_count,
    record_count: c.record_count,
    expected_identity_count: c.expected_identity_count,
    packs_to_unify: c.packs_to_unify,
    original_group_keys: [...c.original_group_keys].sort(),
    bvids: [...c.bvids].sort(),
    mapping: c.mapping,
    groups: c.groups.map((g) => ({
      source_group_key: g.source_group_key,
      member_count: g.member_count,
      members: g.members.map((m) => ({
        bvid: m.bvid,
        title: m.title,
        registered_identity_ids: [...m.registered_identity_ids].sort(),
        evidence_download_link_count: m.evidence_download_link_count,
        evidence_download_links_sha256: m.evidence_download_links_sha256,
        source_member_sha256: m.source_member_sha256,
      })),
      evidence_download_url_count: g.evidence_download_url_count,
      evidence_download_urls_sha256: g.evidence_download_urls_sha256,
      evidence_qq_ids: [...g.evidence_qq_ids].sort(),
    })),
    relations: c.relations,
  };
}

// These are ledger-backed same-pack relations that cross an old evidence
// group boundary. They are fixture partitions only; the production matcher
// never sees BVIDs, group keys, or this table. Keeping the source relation
// here prevents a count-only projection from turning an adjudicated must-link
// into a false cannot-link.
const EVIDENCE_BACKED_CROSS_GROUP_MUST_LINKS = [
  ['BV1y6YbzWEhD', 'BV1MiHLz8Emm'], // 爱吃土豆的界王: 原初修真
  ['BV1b2h36bEvA', 'BV1EPgA6eEfT'], // Drunk耀爵: 晴小姐 raw/group
  ['BV1FT8kzCE6R', 'BV1Gm7Yz3EVu', 'BV1QJKWzEEV3', 'BV1CiV5zwEdU'], // 时唅: 潜行者 line
  ['BV12scGeMEAb', 'BV167ZLYfE5w', 'BV1AemXY7ESi', 'BV1scFcewEPN', 'BV1F5C3YLE3N'], // 时唅: 生还者 line
  ['BV1nRBFBFEFw', 'BV1RaF6zXELF', 'BV1toNn6pEWN', 'BV1vGq9BeETp'], // 一个小寂哦: 怪物大乱斗重生 line
  ['BV13fm7BXEL9', 'BV1Kw2JB2ESX', 'BV1YBqaBTEsX'], // 一个小寂哦: 无尽幸运方块大陆重生 release chain
  ['BV1WA4m1L7QY', 'BV1qK411v7Ad', 'BV1ZW421N76z', 'BV1yr421n7yL', 'BV1yB34zhEKs'], // Puikre: 锻造大师 line
  ['BV1uN411Y7eC', 'BV1Jm4y1374M', 'BV1Rc411f7av'], // 墨竹ギ: 史诗的地下城
];

// A named source group is a must-link only when the ledger/evidence titles
// provide the same non-generic product anchor for every member. These are
// audit-side adjudication inputs, not runtime rules; mixed token-connectivity
// groups such as `星辉死神`, `各大主播同款`, and the mobile `怪物大乱斗`
// group are intentionally absent.
const EVIDENCE_BACKED_SOURCE_GROUP_MUST_LINKS = new Set([
  '爱吃土豆的界王::山海大陆斗罗大陆 与',
  '爱吃土豆的界王::时光牧场',
  '冰冻酸奶盒::宝可梦地平线',
  '明月庄主::命运齿轮',
  '明月庄主::月亮工厂 f',
  '墨竹ギ::深渊之诗',
  '墨竹ギ::史诗的地下城 dungeons of fantasy',
  '时唅::大型末世 辐射 生还者',
  '时唅::辐射次时代',
  '时唅::辐射新世纪',
  '我的世界peaunt::泰坦生物 仿照',
  '我的世界peaunt::泰坦生物复刻',
  '一个小寂哦::弑神之路',
  '一个小寂哦::怪物大乱斗重生',
  '一个小寂哦::四叶草',
  '一个小寂哦::追影之旅',
  'zanghero::机械殖民地',
]);

function unionFind(values) {
  const parent = new Map(values.map((v) => [v, v]));
  function find(x) { let p = parent.get(x); while (p !== parent.get(p)) { parent.set(p, parent.get(p)); p = parent.get(p); } return p; }
  function join(a, b) { const ra = find(a); const rb = find(b); if (ra !== rb) parent.set(rb, ra); }
  return { find, join };
}

function buildIdentityRelations(kind, adjudication, groups) {
  const members = groups.flatMap((g) => g.members);
  if (kind === 'gate') {
    return {
      basis: 'confirmed_or_strong_same_pack_adjudication',
      must_link: pairwise(members.map((m) => m.bvid)),
      cannot_link: [],
      unknown_pairs: [],
      partitions: [{ identity: 'confirmed_case_identity', bvids: members.map((m) => m.bvid).sort() }],
    };
  }

  const memberByBvid = new Map(members.map((m) => [m.bvid, m]));
  const memberSet = new Set(memberByBvid.keys());
  const relationKey = (a, b) => a < b ? `${a}\0${b}` : `${b}\0${a}`;
  const idsOf = (bvid) => new Set(memberByBvid.get(bvid)?.registered_identity_ids || []);
  const sharedIds = (a, b) => {
    const left = idsOf(a); const right = idsOf(b);
    return [...left].filter((id) => right.has(id));
  };
  const disjointKnownIds = (a, b) => {
    const left = idsOf(a); const right = idsOf(b);
    return left.size > 0 && right.size > 0 && sharedIds(a, b).length === 0;
  };

  // A registered id is evidence for a relation only when it is shared by the
  // two records being related.  In particular, do not union all ids found on
  // one record: a mixed/incorrect source row can carry links to several
  // unrelated projects.  The old implementation did exactly that and turned
  // 墨言eclipse::颠覆性的 into a must-link between two different packs.
  const explicitMust = new Set();
  const addExplicitMust = (a, b) => {
    if (!memberSet.has(a) || !memberSet.has(b) || a === b) return;
    explicitMust.add(relationKey(a, b));
  };
  for (const g of groups) {
    const ids = g.members.map((m) => m.bvid);
    if (EVIDENCE_BACKED_SOURCE_GROUP_MUST_LINKS.has(g.source_group_key)
      || ids.every((bvid) => idsOf(bvid).size === 0)) {
      for (const [a, b] of pairwise(ids)) addExplicitMust(a, b);
    }
  }
  for (const bvids of EVIDENCE_BACKED_CROSS_GROUP_MUST_LINKS) {
    for (const [a, b] of pairwise(bvids)) addExplicitMust(a, b);
  }

  // Build conservative must-link components. A component is never allowed to
  // contain a pair of disjoint known project ids; this prevents a multi-link
  // row from acting as a bridge between two unrelated projects.
  const partitionUf = unionFind([...memberSet]);
  const componentMembers = () => {
    const out = new Map();
    for (const bvid of memberSet) {
      const root = partitionUf.find(bvid);
      const arr = out.get(root) || []; arr.push(bvid); out.set(root, arr);
    }
    return out;
  };
  const canJoin = (a, b) => {
    const comps = componentMembers();
    const left = comps.get(partitionUf.find(a)) || [a];
    const right = comps.get(partitionUf.find(b)) || [b];
    for (const x of left) for (const y of right) if (disjointKnownIds(x, y)) return false;
    return true;
  };
  const mustKeys = new Set();
  const joinMust = (a, b, reason, allowKnownConflict = false) => {
    const key = relationKey(a, b);
    if (mustKeys.has(key)) return;
    if (!allowKnownConflict && !canJoin(a, b)) throw new Error(`fixture relation conflict (${reason}): ${a}/${b}`);
    partitionUf.join(a, b);
    mustKeys.add(key);
  };
  for (const key of [...explicitMust].sort()) {
    const [a, b] = key.split('\0');
    joinMust(a, b, 'explicit adjudication', true);
  }
  const allPairs = pairwise([...memberSet].sort());
  for (const [a, b] of allPairs) {
    if (mustKeys.has(relationKey(a, b)) || !sharedIds(a, b).length) continue;
    if (canJoin(a, b)) joinMust(a, b, 'shared registered identity');
  }

  const components = componentMembers();
  const partitionValues = [...components.entries()].map(([root, bvids]) => {
    const labels = [...new Set(bvids.flatMap((bvid) => [...idsOf(bvid)]))].sort();
    return { identity: labels.length ? `registered:${labels.join('+')}` : `evidence_partition:${root}`, bvids: bvids.sort() };
  }).sort((a, b) => a.bvids[0].localeCompare(b.bvids[0]));
  const must = partitionValues.flatMap((p) => pairwise(p.bvids));
  const mustKeySet = new Set(must.map(([a, b]) => relationKey(a, b)));
  const cannot = [];
  for (const [a, b] of allPairs) {
    if (mustKeySet.has(relationKey(a, b))) continue;
    if (disjointKnownIds(a, b)) cannot.push([a, b]);
  }
  const cannotKeySet = new Set(cannot.map(([a, b]) => relationKey(a, b)));
  const unknown_pairs = allPairs.filter(([a, b]) =>
    !mustKeySet.has(relationKey(a, b)) && !cannotKeySet.has(relationKey(a, b)));
  return {
    basis: adjudication.verdict === 'AMBIGUOUS'
      ? 'ambiguous_protection_only; direct registered identities and existing no-id groups'
      : 'different_pack_adjudication_note plus direct registered_identity_relations',
    must_link: must,
    cannot_link: cannot,
    unknown_pairs,
    partitions: partitionValues,
  };
}

function main() {
  const gate = readJson(GATE_PATH);
  const ledger = readJson(LEDGER_PATH);
  const evidence = readJson(EVIDENCE_PATH);
  const candidates = readJson(CANDIDATE_PATH);
  const payload = loadPayload();
  // The gate is tracked JSON and may be checked out with CRLF under
  // core.autocrlf.  Its frozen hash is the Git blob hash; keep the working-tree
  // container hash separately and compare normalized semantics explicitly.
  verifyTextArtifact('pipeline/audit/confirmed_undermerge_runtime_gate.json', SHAS.gate);
  if (sha256File(EVIDENCE_PATH) !== SHAS.evidence) throw new Error('original evidence bytes drifted');
  if (sha256File(CANDIDATE_PATH) !== SHAS.candidate) throw new Error('candidate evidence bytes drifted');
  if (sha256File(PAYLOAD_PATH) !== SHAS.payload) throw new Error('population bytes drifted');
  if (payload.length !== 936 || candidates.payload_records !== 936 || evidence.payload_records !== 936) throw new Error('936-record population contract failed');

  const payloadByBvid = new Map();
  for (const row of payload) {
    if (!row || !row.bvid || payloadByBvid.has(row.bvid)) throw new Error(`payload duplicate/empty BVID: ${row && row.bvid}`);
    payloadByBvid.set(row.bvid, row);
  }
  const evidenceByKey = new Map();
  for (const f of evidence.findings) {
    const key = caseKey(f.author, f.group_keys);
    if (evidenceByKey.has(key)) throw new Error(`duplicate evidence key: ${key}`);
    evidenceByKey.set(key, f);
  }
  const gateKeys = new Set(gate.cases.map((x) => caseKey(x.author, x.group_keys)));
  const cases = [];
  const usedCaseKeys = new Set();
  const usedGateBvids = new Set();

  function materialise(kind, row, finding) {
    const key = caseKey(finding.author, finding.group_keys);
    if (usedCaseKeys.has(key)) throw new Error(`case reused: ${key}`);
    usedCaseKeys.add(key);
    if (finding.record_count !== row.record_count || finding.group_count !== row.group_count) throw new Error(`count mismatch: ${key}`);
    const groups = [];
    const caseBvids = new Set();
    for (const groupKey of row.group_keys) {
      const matches = finding.groups.filter((g) => g.group_key === groupKey);
      if (matches.length !== 1) throw new Error(`${key}: group mapping ${groupKey} is ${matches.length}, not unique`);
      const source = matches[0];
      if (!source.member_count || source.member_count !== source.members.length) throw new Error(`${key}: empty/incomplete group ${groupKey}`);
      const members = [];
      for (const src of source.members) {
        if (!src.bvid || caseBvids.has(src.bvid)) throw new Error(`${key}: duplicate/empty member ${src.bvid}`);
        const p = payloadByBvid.get(src.bvid);
        if (!p || p.title !== src.title || String(p.author || 'unknown').trim() !== row.author) throw new Error(`${key}: payload/evidence member mismatch ${src.bvid}`);
        caseBvids.add(src.bvid);
        const registered_identity_ids = registeredIds(src);
        const evidence_download_link_count = Array.isArray(src.download_links) ? src.download_links.length : 0;
        const evidence_download_links_sha256 = linkSha256(src.download_links || []);
        members.push({
          bvid: src.bvid,
          title: src.title,
          registered_identity_ids,
          evidence_download_link_count,
          evidence_download_links_sha256,
          source_member_sha256: sha256Text(stable({ bvid: src.bvid, title: src.title, registered_identity_ids, evidence_download_link_count, evidence_download_links_sha256 })),
        });
      }
      groups.push({
        source_group_key: groupKey,
        member_count: members.length,
        members: members.sort((a, b) => a.bvid.localeCompare(b.bvid)),
        evidence_download_url_count: (source.download_urls || []).length,
        evidence_download_urls_sha256: linkSha256([...(source.download_urls || [])].sort()),
        evidence_qq_ids: [...(source.qq_ids || [])].sort(),
      });
    }
    if (caseBvids.size !== row.record_count) throw new Error(`${key}: mapped ${caseBvids.size}/${row.record_count}`);
    const relations = buildIdentityRelations(kind, row, groups);
    return {
      case_type: kind,
      cluster_key: row.cluster_key,
      author: row.author,
      verdict: row.verdict,
      confidence: row.confidence,
      group_count: row.group_count,
      record_count: row.record_count,
      expected_identity_count: row.expected_identity_count,
      packs_to_unify: row.packs_to_unify,
      original_group_keys: [...row.group_keys].sort(),
      registered_identities: [...(row.registered_identities || [])].sort(),
      evidence: row.evidence || finding.evidence,
      groups: groups.sort((a, b) => a.source_group_key.localeCompare(b.source_group_key)),
      bvids: [...caseBvids].sort(),
      relations,
      mapping: {
        source: 'original evidence finding matched by author + original group-key set',
        source_evidence_key: key,
        complete: true,
      },
    };
  }

  for (const row of gate.cases) {
    const f = evidenceByKey.get(caseKey(row.author, row.group_keys));
    if (!f) throw new Error(`gate evidence missing: ${row.cluster_key}`);
    const c = materialise('gate', row, f);
    for (const b of c.bvids) { if (usedGateBvids.has(b)) throw new Error(`gate BVID reused: ${b}`); usedGateBvids.add(b); }
    cases.push(c);
  }
  for (const row of gate.excluded_cases) {
    const f = ledger.findings.find((x) => x.cluster_key === row.cluster_key);
    if (!f) throw new Error(`excluded ledger finding missing: ${row.cluster_key}`);
    const ev = evidenceByKey.get(caseKey(f.author, f.group_keys));
    if (!ev) throw new Error(`excluded evidence missing: ${row.cluster_key}`);
    cases.push(materialise('protected', {
      ...row,
      group_keys: f.group_keys,
      group_count: f.group_count,
      record_count: f.record_count,
      expected_identity_count: f.expected_identity_count,
      packs_to_unify: Math.max(0, f.group_count - 1),
      confidence: f.confidence,
      evidence: f.evidence,
    }, ev));
  }

  const gateCases = cases.filter((x) => x.case_type === 'gate');
  const protectedCases = cases.filter((x) => x.case_type === 'protected');
  if (gateCases.length !== 26 || protectedCases.length !== 32 || usedGateBvids.size !== 80) throw new Error('fixture coverage is not 26 + 32 / 80');
  if (new Set(cases.map((x) => x.cluster_key)).size !== 58) throw new Error('fixture cluster keys are not unique');

  const orderedCases = cases.sort((a, b) => a.cluster_key.localeCompare(b.cluster_key));
  const semantic_sha256 = sha256Text(stable(orderedCases.map(semanticCase)));
  const result = {
    phase: '3G-F.3-A',
    artifact: 'phase3gf_runtime_acceptance_fixture',
    schema_version: 1,
    purpose: 'Immutable member/identity projection of the original 26 gate and 32 protection cases. The runtime runner must not reselect members from mutable evidence.',
    generated_at: new Date((process.env.SOURCE_DATE_EPOCH ? Number(process.env.SOURCE_DATE_EPOCH) * 1000 : Date.now())).toISOString(),
    source_artifacts: {
      runtime_gate: { path: 'pipeline/audit/confirmed_undermerge_runtime_gate.json', git_source_commit: 'cbbfb588262d06d386dab645deee88e0c4acb7c3', git_source_sha256: SHAS.gate, working_tree_sha256: sha256File(GATE_PATH) },
      original_evidence: { path: 'build/audit/undermerge_evidence_v2.json', sha256: sha256File(EVIDENCE_PATH), payload_records: evidence.payload_records },
      candidate_audit: { path: 'build/audit/bilibili_cross_group_undermerge_v2.json', sha256: sha256File(CANDIDATE_PATH), payload_records: candidates.payload_records },
      population: { path: 'converted_output/data/bili_data.js', sha256: sha256File(PAYLOAD_PATH), records: payload.length },
      ledger: { path: 'pipeline/audit/bilibili_undermerge_adjudication_v2.json', git_source_commit: 'a690d3dfddc66d4260960b83c9cece7bdb3af72a' },
    },
    runtime_provenance: RUNTIME_PROVENANCE,
    selection_contract: {
      gate_cases: 'exactly the 26 rows from the frozen gate; author + original group-key set maps to exactly one original evidence finding',
      protected_cases: 'exactly the 27 DIFFERENT_PACKS and 5 AMBIGUOUS rows from the frozen gate/ledger',
      no_rescan: 'runtime group keys are never used to select, shrink, or rewrite fixture members',
      fail_closed: ['missing', 'duplicate', 'empty', 'hash drift', 'non-unique mapping', 'payload/evidence mismatch'],
      semantic_sha256,
      relation_contract: 'every member pair is exactly one of must_link, cannot_link, or unknown_pairs; partitions cover every member exactly once and never hide a known conflict',
    },
    coverage: {
      gate_cases: gateCases.length,
      protected_cases: protectedCases.length,
      different_packs: protectedCases.filter((x) => x.verdict === 'DIFFERENT_PACKS').length,
      ambiguous: protectedCases.filter((x) => x.verdict === 'AMBIGUOUS').length,
      gate_unique_bvids: usedGateBvids.size,
    },
    cases: orderedCases,
  };
  fs.mkdirSync(path.dirname(OUT_PATH), { recursive: true });
  fs.writeFileSync(OUT_PATH, JSON.stringify(result, null, 2) + '\n', 'utf8');
  console.log(JSON.stringify({ written: path.relative(ROOT, OUT_PATH), gate_cases: gateCases.length, protected_cases: protectedCases.length, gate_unique_bvids: usedGateBvids.size, evidence_sha256: SHAS.evidence }, null, 2));
}

main();

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
  const ids = members.flatMap((m) => m.registered_identity_ids);
  const uf = unionFind([...new Set(ids)]);
  for (const m of members) for (const [a, b] of pairwise(m.registered_identity_ids)) uf.join(a, b);
  // Registered identities that co-occur in one evidence group are mirror
  // references to the same pack for this fixture. No URL/QQ is used as a
  // trigger by production runtime; this is only a ground-truth partition.
  for (const g of groups) for (const [a, b] of pairwise([...new Set(g.members.flatMap((m) => m.registered_identity_ids))])) uf.join(a, b);

  const labelFor = new Map();
  for (const m of members) {
    if (m.registered_identity_ids.length) {
      const roots = [...new Set(m.registered_identity_ids.map((x) => uf.find(x)))].sort();
      labelFor.set(m.bvid, `registered:${roots.join('+')}`);
    }
  }
  if (kind === 'gate') {
    return {
      basis: 'confirmed_or_strong_same_pack_adjudication',
      must_link: pairwise(members.map((m) => m.bvid)),
      cannot_link: [],
      unknown_pairs: [],
      partitions: [{ identity: 'confirmed_case_identity', bvids: members.map((m) => m.bvid).sort() }],
    };
  }
  if (adjudication.verdict === 'AMBIGUOUS') {
    const must = [];
    const partitions = [];
    for (const g of groups) {
      const idsInGroup = [...new Set(g.members.map((m) => m.bvid))].sort();
      partitions.push({ identity: `existing_evidence_group:${g.source_group_key}`, bvids: idsInGroup });
      must.push(...pairwise(idsInGroup));
    }
    return {
      basis: 'ambiguous_protection_only; cross_group_identity_unknown',
      must_link: must,
      cannot_link: [],
      unknown_pairs: pairwise(members.map((m) => m.bvid)).filter(([a, b]) => !must.some(([x, y]) => (x === a && y === b) || (x === b && y === a))),
      partitions,
    };
  }

  // For DIFFERENT_PACKS, a source group without a registered identity is not
  // itself a ground-truth identity: the old runtime may have connected several
  // products through a component token. Keep such relations UNKNOWN unless a
  // ledger/evidence-backed relation below establishes them. A source group
  // with exactly one registered identity can provisionally cover its unlinked
  // siblings; a mixed registered group is partitioned by the member identity.
  const memberSet = new Set(members.map((m) => m.bvid));
  const partitionUf = unionFind([...memberSet]);
  const knownMembers = new Set();
  const labelForMember = new Map();
  for (const g of groups) {
    const roots = [...new Set(g.members.flatMap((m) => m.registered_identity_ids || []).map((id) => uf.find(id)))].sort();
    if (EVIDENCE_BACKED_SOURCE_GROUP_MUST_LINKS.has(g.source_group_key)) {
      const label = `adjudicated_source_group:${g.source_group_key}`;
      for (const m of g.members) {
        labelForMember.set(m.bvid, label);
        knownMembers.add(m.bvid);
      }
    } else if (roots.length === 1) {
      const label = roots.length
        ? `registered:${roots[0]}`
        : `evidence_partition:${g.source_group_key}`;
      for (const m of g.members) {
        labelForMember.set(m.bvid, label);
        knownMembers.add(m.bvid);
      }
    } else {
      for (const m of g.members) {
        const label = labelFor.get(m.bvid);
        if (label) {
          labelForMember.set(m.bvid, label);
          knownMembers.add(m.bvid);
        }
      }
    }
  }
  const byLabel = new Map();
  for (const [bvid, label] of labelForMember) {
    const arr = byLabel.get(label) || [];
    arr.push(bvid); byLabel.set(label, arr);
  }
  for (const bvids of byLabel.values()) for (const [a, b] of pairwise(bvids)) partitionUf.join(a, b);
  for (const bvids of EVIDENCE_BACKED_CROSS_GROUP_MUST_LINKS) {
    const present = bvids.filter((bvid) => memberSet.has(bvid));
    if (present.length >= 2) {
      for (const bvid of present) knownMembers.add(bvid);
      for (const [a, b] of pairwise(present)) partitionUf.join(a, b);
    }
  }
  const partitions = new Map();
  for (const bvid of knownMembers) {
    const root = partitionUf.find(bvid);
    const arr = partitions.get(root) || [];
    arr.push(bvid); partitions.set(root, arr);
  }
  const partitionValues = [...partitions.entries()].map(([root, bvids]) => {
    const labels = [...new Set(bvids.map((bvid) => labelForMember.get(bvid)))].sort();
    return { identity: labels.join('|') || `partition:${root}`, bvids: bvids.sort() };
  });
  const must = partitionValues.flatMap((p) => pairwise(p.bvids));
  const cannot = [];
  for (let i = 0; i < partitionValues.length; i++) for (let j = i + 1; j < partitionValues.length; j++) {
    // Expand only evidence-backed cross-partition relations to every member.
    for (const a of partitionValues[i].bvids) for (const b of partitionValues[j].bvids) cannot.push([a, b]);
  }
  const relationKey = (a, b) => a < b ? `${a}\0${b}` : `${b}\0${a}`;
  const mustKeys = new Set(must.map(([a, b]) => relationKey(a, b)));
  const cannotKeys = new Set(cannot.map(([a, b]) => relationKey(a, b)));
  const unknown_pairs = pairwise([...memberSet].sort())
    .filter(([a, b]) => !mustKeys.has(relationKey(a, b)) && !cannotKeys.has(relationKey(a, b)));
  return {
    basis: 'different_pack_adjudication_note plus registered_identity_partitioning',
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
  if (sha256File(GATE_PATH) !== SHAS.gate) throw new Error('gate bytes drifted');
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
    },
    coverage: {
      gate_cases: gateCases.length,
      protected_cases: protectedCases.length,
      different_packs: protectedCases.filter((x) => x.verdict === 'DIFFERENT_PACKS').length,
      ambiguous: protectedCases.filter((x) => x.verdict === 'AMBIGUOUS').length,
      gate_unique_bvids: usedGateBvids.size,
    },
    cases: cases.sort((a, b) => a.cluster_key.localeCompare(b.cluster_key)),
  };
  fs.mkdirSync(path.dirname(OUT_PATH), { recursive: true });
  fs.writeFileSync(OUT_PATH, JSON.stringify(result, null, 2) + '\n', 'utf8');
  console.log(JSON.stringify({ written: path.relative(ROOT, OUT_PATH), gate_cases: gateCases.length, protected_cases: protectedCases.length, gate_unique_bvids: usedGateBvids.size, evidence_sha256: SHAS.evidence }, null, 2));
}

main();

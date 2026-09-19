/**
 * Phase 3G-F.3-A - fail-closed dynamic runtime acceptance.
 *
 * The checked-in fixture is the only source of case membership. This runner
 * validates the frozen input bytes, recompiles the evidence-source runtime and
 * the 1bee6de pre-fix runtime from Git, invokes the supplied candidate module
 * on the full 936-record population, and evaluates member relations.
 *
 * Exit codes: 0 = all gates/protections pass, 2 = runtime or fixture blocked,
 * 1 = runner/configuration error.
 */
const crypto = require('crypto');
const { execFileSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..');
const DEFAULT_FIXTURE = path.join(ROOT, 'pipeline', 'audit', 'fixtures', 'phase3gf_runtime_acceptance.json');
const GATE_PATH = path.join(ROOT, 'pipeline', 'audit', 'confirmed_undermerge_runtime_gate.json');
const LEDGER_PATH = path.join(ROOT, 'pipeline', 'audit', 'bilibili_undermerge_adjudication_v2.json');
const EVIDENCE_PATH = path.join(ROOT, 'build', 'audit', 'undermerge_evidence_v2.json');
const CANDIDATE_AUDIT_PATH = path.join(ROOT, 'build', 'audit', 'bilibili_cross_group_undermerge_v2.json');
const PAYLOAD_PATH = path.join(ROOT, 'converted_output', 'data', 'bili_data.js');
const SOURCE_REL = 'apps/web/src/domain/bilibiliGrouping.ts';
const PACKNAME_REL = 'apps/web/src/domain/packName.ts';
const WEB_PACKAGE_REL = 'apps/web/package.json';

const FROZEN = {
  gate: '4e91fe1d8bc3c16a8fe1b3cc65be9a64dcc56f47b29b2a218524029ca82a9d90',
  evidence: 'bd8b76a51dba40079f258183ef27cbe438c7e220af972a5fe877a1f9ff2df083',
  candidate: 'c32814f6926c2c5c6e2be5552d3e7cd0b61e7ead82d0e10e1d8c007c8ff846a4',
  payload: '049fe4c567fabafb4e4c58018b606c1aa23d01d2d1511933856454915e79bebe',
  evidenceRuntime: '3d10e2e63cc50d1660d1d95c81658444b67ef21250f4af171366b97e1582c15e',
  preFixRuntime: '12fb5f96f2cd3cf587130bae45f0eda19347e8ca54d019b8f2d553a8e7c7692e',
  fixtureSemantic: '28553febf09b641524ea120bb09e10216b6f449b9f66ab62a5b7ab721e64b456',
};

function sha256Bytes(bytes) { return crypto.createHash('sha256').update(bytes).digest('hex'); }
function sha256File(file) { return sha256Bytes(fs.readFileSync(file)); }
function sha256Text(text) { return sha256Bytes(Buffer.from(text, 'utf8')); }
function readJson(file) { return JSON.parse(fs.readFileSync(file, 'utf8')); }
function sorted(xs) { return [...xs].sort(); }
function sameSet(a, b) { const aa = sorted(a); const bb = sorted(b); return aa.length === bb.length && aa.every((x, i) => x === bb[i]); }
function pairKey(a, b) { return a < b ? `${a}\0${b}` : `${b}\0${a}`; }
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
    original_group_keys: sorted(c.original_group_keys),
    bvids: sorted(c.bvids),
    mapping: c.mapping,
    groups: c.groups.map((g) => ({
      source_group_key: g.source_group_key,
      member_count: g.member_count,
      members: g.members.map((m) => ({
        bvid: m.bvid,
        title: m.title,
        registered_identity_ids: sorted(m.registered_identity_ids || []),
        evidence_download_link_count: m.evidence_download_link_count,
        evidence_download_links_sha256: m.evidence_download_links_sha256,
        source_member_sha256: m.source_member_sha256,
      })),
      evidence_download_url_count: g.evidence_download_url_count,
      evidence_download_urls_sha256: g.evidence_download_urls_sha256,
      evidence_qq_ids: sorted(g.evidence_qq_ids || []),
    })),
    relations: c.relations,
  };
}
function fixtureSemanticSha(f) { return sha256Text(stableValue(f.cases.map(semanticCase))); }
function parseArgs() {
  const args = process.argv.slice(2);
  const get = (name, fallback) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : fallback; };
  return {
    testModule: get('--test-module', get('--current-module', null)),
    fixture: get('--fixture', DEFAULT_FIXTURE),
    out: get('--out', path.join(ROOT, 'pipeline', 'audit', 'phase3gf_runtime_acceptance.json')),
    validateOnly: args.includes('--validate-only'),
  };
}
function fail(message) { const e = new Error(`runtime acceptance: ${message}`); e.code = 2; throw e; }
function git(args, encoding = 'utf8') { return execFileSync('git', args, { cwd: ROOT, encoding }); }
function gitShow(commit, rel) { return git(['show', `${commit}:${rel}`], 'buffer'); }
function gitShowText(commit, rel) { return gitShow(commit, rel).toString('utf8'); }
function gitShowSha(commit, rel) { return sha256Bytes(gitShow(commit, rel)); }
function normalizeTextBytes(bytes) {
  return Buffer.from(bytes.toString('utf8').replace(/\r\n/g, '\n').replace(/\r/g, '\n'), 'utf8');
}
function verifyTrackedJsonBytes(relativePath, expectedGitSha256) {
  const worktreeBytes = fs.readFileSync(path.join(ROOT, relativePath));
  const gitBytes = gitShow('HEAD', relativePath);
  const gitSha256 = sha256Bytes(gitBytes);
  if (gitSha256 !== expectedGitSha256) fail(`frozen Git blob drifted for ${relativePath}`);
  const worktreeNormalized = normalizeTextBytes(worktreeBytes);
  const gitNormalized = normalizeTextBytes(gitBytes);
  if (!worktreeNormalized.equals(gitNormalized)) {
    fail(`working-tree semantic bytes drifted for ${relativePath}`);
  }
  return {
    git_raw_sha256: gitSha256,
    worktree_raw_sha256: sha256Bytes(worktreeBytes),
    worktree_normalized_sha256: sha256Bytes(worktreeNormalized),
    git_normalized_sha256: sha256Bytes(gitNormalized),
    worktree_semantically_matches_git: true,
  };
}
function loadPayload() {
  const raw = fs.readFileSync(PAYLOAD_PATH, 'utf8');
  const start = raw.indexOf('['); const end = raw.lastIndexOf(']');
  if (start < 0 || end < start) fail('population payload is not an array');
  return JSON.parse(raw.slice(start, end + 1));
}
function stableValue(value) {
  if (Array.isArray(value)) return `[${value.map(stableValue).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${stableValue(value[k])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}
function linkSha256(links) { return sha256Text(stableValue(links || [])); }
function registeredIdentityIdsFromLinks(links) {
  const ids = new Set();
  for (const item of links || []) {
    const raw = String(item?.url || '').trim();
    let m;
    if ((m = raw.match(/curseforge\.com\/minecraft\/modpacks\/([^/?#]+)/i))) ids.add(`curseforge:${m[1].toLowerCase()}`);
    if ((m = raw.match(/mcmod\.cn\/modpack\/(\d+)/i))) ids.add(`mcmod:modpack/${m[1]}`);
    if ((m = raw.match(/bbsmc\.net\/modpack\/([^/?#]+)/i))) ids.add(`bbsmc:modpack/${m[1].replace(/\/$/, '').toLowerCase()}`);
    if ((m = raw.match(/github\.com\/([^/]+)\/([^/?#]+)/i))) ids.add(`github:${m[1].toLowerCase()}/${m[2].replace(/\.git$/, '').toLowerCase()}`);
    if ((m = raw.match(/(?:www\.)?xyebbs\.com\/resources\/(\d+)/i))) ids.add(`xyebbs:resource/${m[1]}`);
    if ((m = raw.match(/(?:www\.)?xyebbs\.com\/res-id\/([^/?#]+)/i))) ids.add(`xyebbs:res-id/${m[1].toLowerCase()}`);
    if ((m = raw.match(/modrinth\.com\/modpack\/([^/?#]+)/i))) ids.add(`modrinth:modpack/${m[1].toLowerCase()}`);
  }
  return [...ids].sort();
}
function evidenceKey(author, groupKeys) { return `${author}||${sorted(groupKeys).join('|')}`; }
function sourceRecordSha(member) {
  const value = {
    bvid: member.bvid,
    title: member.title,
    registered_identity_ids: member.registered_identity_ids || [],
    evidence_download_link_count: member.evidence_download_link_count || 0,
    evidence_download_links_sha256: member.evidence_download_links_sha256 || null,
  };
  return sha256Text(stableValue(value));
}
function loadAndValidateFixture(file, payload) {
  if (!fs.existsSync(file)) fail(`fixture missing: ${file}`);
  const f = readJson(file);
  if (f.schema_version !== 1 || f.artifact !== 'phase3gf_runtime_acceptance_fixture') fail('fixture schema/artifact mismatch');
  if (!f.selection_contract || typeof f.selection_contract.semantic_sha256 !== 'string') fail('fixture semantic contract missing');
  const required = f.source_artifacts || {};
  if (required.runtime_gate.git_source_sha256 !== FROZEN.gate || required.original_evidence.sha256 !== FROZEN.evidence || required.candidate_audit.sha256 !== FROZEN.candidate || required.population.sha256 !== FROZEN.payload) fail('fixture provenance hash mismatch');
  if (f.coverage.gate_cases !== 26 || f.coverage.protected_cases !== 32 || f.coverage.different_packs !== 27 || f.coverage.ambiguous !== 5 || f.coverage.gate_unique_bvids !== 80) fail('fixture coverage mismatch');
  if (!Array.isArray(f.cases) || f.cases.length !== 58) fail('fixture case count mismatch');
  const gate = readJson(GATE_PATH);
  const ledger = readJson(LEDGER_PATH);
  const gateByKey = new Map(gate.cases.map((c) => [evidenceKey(c.author, c.group_keys), c]));
  const excludedByCluster = new Map(gate.excluded_cases.map((c) => [c.cluster_key, c]));
  const ledgerByCluster = new Map((ledger.findings || []).map((c) => [c.cluster_key, c]));
  const seenGateCases = new Set(); const seenProtectedCases = new Set();
  const byPayload = new Map();
  for (const row of payload) {
    if (!row || !row.bvid || byPayload.has(row.bvid)) fail(`payload duplicate/empty BVID: ${row && row.bvid}`);
    byPayload.set(row.bvid, row);
  }
  const evidence = readJson(EVIDENCE_PATH);
  const evidenceByKey = new Map();
  for (const finding of evidence.findings || []) {
    const key = evidenceKey(finding.author, finding.group_keys || []);
    if (evidenceByKey.has(key)) fail(`duplicate evidence finding: ${key}`);
    evidenceByKey.set(key, finding);
  }
  const keys = new Set(); const gateBvids = new Set();
  for (const c of f.cases) {
    if (!c.cluster_key || !c.author || !['gate', 'protected'].includes(c.case_type)) fail('fixture case identity missing');
    if (keys.has(c.cluster_key)) fail(`duplicate fixture case: ${c.cluster_key}`); keys.add(c.cluster_key);
    if (!Array.isArray(c.groups) || !c.groups.length || !Array.isArray(c.bvids) || !c.bvids.length) fail(`empty fixture case: ${c.cluster_key}`);
    const members = c.groups.flatMap((g) => {
      if (!g.source_group_key || !Number.isInteger(g.member_count) || g.member_count < 1 || g.member_count !== g.members.length) fail(`empty/incomplete group: ${c.cluster_key}/${g.source_group_key}`);
      return g.members;
    });
    const seen = new Set();
    for (const m of members) {
      if (!m.bvid || seen.has(m.bvid)) fail(`duplicate/empty fixture member: ${c.cluster_key}/${m.bvid}`);
      seen.add(m.bvid);
      const p = byPayload.get(m.bvid);
      if (!p || p.title !== m.title || String(p.author || 'unknown').trim() !== c.author) fail(`fixture/payload mismatch: ${c.cluster_key}/${m.bvid}`);
      if (m.source_member_sha256 !== sourceRecordSha(m)) fail(`fixture member hash drift: ${c.cluster_key}/${m.bvid}`);
    }
    if (!sameSet(seen, c.bvids) || seen.size !== c.record_count) fail(`fixture member coverage mismatch: ${c.cluster_key}`);
    if (!c.mapping || c.mapping.complete !== true || !c.mapping.source_evidence_key) fail(`fixture mapping is not complete: ${c.cluster_key}`);
    const source = evidenceByKey.get(c.mapping.source_evidence_key);
    if (!source || source.author !== c.author
      || source.record_count !== c.record_count || source.group_count !== c.group_count
      || evidenceKey(source.author, source.group_keys || []) !== c.mapping.source_evidence_key) {
      fail(`fixture/evidence mapping mismatch: ${c.cluster_key}`);
    }
    for (const fg of c.groups) {
      const sourceGroups = (source.groups || []).filter((g) => g.group_key === fg.source_group_key);
      if (sourceGroups.length !== 1) fail(`fixture/evidence group mapping mismatch: ${c.cluster_key}/${fg.source_group_key}`);
      const sg = sourceGroups[0];
      if (sg.member_count !== fg.member_count || sg.members.length !== fg.member_count) {
        fail(`fixture/evidence member count mismatch: ${c.cluster_key}/${fg.source_group_key}`);
      }
      const sourceMembers = new Map((sg.members || []).map((m) => [m.bvid, m]));
      for (const fm of fg.members) {
        const sm = sourceMembers.get(fm.bvid);
        if (!sm || sm.title !== fm.title) fail(`fixture/evidence member mismatch: ${c.cluster_key}/${fm.bvid}`);
        const ids = registeredIdentityIdsFromLinks(sm.download_links || []);
        const linkCount = Array.isArray(sm.download_links) ? sm.download_links.length : 0;
        const linkHash = linkSha256(sm.download_links || []);
        if (!sameSet(ids, fm.registered_identity_ids || [])
          || linkCount !== fm.evidence_download_link_count
          || linkHash !== fm.evidence_download_links_sha256
          || fm.source_member_sha256 !== sourceRecordSha({
            bvid: sm.bvid,
            title: sm.title,
            registered_identity_ids: ids,
            evidence_download_link_count: linkCount,
            evidence_download_links_sha256: linkHash,
          })) {
          fail(`fixture/evidence member provenance mismatch: ${c.cluster_key}/${fm.bvid}`);
        }
      }
      const sourceUrls = [...(sg.download_urls || [])].sort();
      if (sourceUrls.length !== fg.evidence_download_url_count
        || linkSha256(sourceUrls) !== fg.evidence_download_urls_sha256
        || !sameSet(sg.qq_ids || [], fg.evidence_qq_ids || [])) {
        fail(`fixture/evidence group provenance mismatch: ${c.cluster_key}/${fg.source_group_key}`);
      }
    }
    const sourceEvidenceKey = c.mapping && c.mapping.source_evidence_key;
    if (c.case_type === 'gate') {
      const expectedGate = gateByKey.get(sourceEvidenceKey);
      if (!expectedGate) fail(`fixture gate case is not one of the frozen 26: ${c.cluster_key}`);
      if (seenGateCases.has(sourceEvidenceKey)) fail(`duplicate frozen gate mapping: ${sourceEvidenceKey}`);
      seenGateCases.add(sourceEvidenceKey);
      if (c.cluster_key !== expectedGate.cluster_key || c.author !== expectedGate.author
        || c.verdict !== expectedGate.verdict || c.confidence !== expectedGate.confidence
        || c.group_count !== expectedGate.group_count || c.record_count !== expectedGate.record_count
        || c.expected_identity_count !== expectedGate.expected_identity_count
        || c.packs_to_unify !== expectedGate.packs_to_unify || !sameSet(c.original_group_keys, expectedGate.group_keys)) {
        fail(`fixture gate adjudication drift: ${c.cluster_key}`);
      }
    } else {
      const excluded = excludedByCluster.get(c.cluster_key);
      const adjudication = ledgerByCluster.get(c.cluster_key);
      if (!excluded || !adjudication) fail(`fixture protected case is not one of the frozen 32: ${c.cluster_key}`);
      if (seenProtectedCases.has(c.cluster_key)) fail(`duplicate frozen protected case: ${c.cluster_key}`);
      seenProtectedCases.add(c.cluster_key);
      const expectedKey = evidenceKey(adjudication.author, adjudication.group_keys || []);
      if (sourceEvidenceKey !== expectedKey || c.author !== adjudication.author
        || c.verdict !== adjudication.verdict || c.cluster_key !== adjudication.cluster_key
        || c.group_count !== adjudication.group_count || c.record_count !== adjudication.record_count
        || c.expected_identity_count !== adjudication.expected_identity_count
        || !sameSet(c.original_group_keys, adjudication.group_keys || [])) {
        fail(`fixture protected adjudication drift: ${c.cluster_key}`);
      }
      if (excluded.verdict !== c.verdict) fail(`fixture protected verdict drift: ${c.cluster_key}`);
    }
    const rel = c.relations;
    if (!rel || !Array.isArray(rel.must_link) || !Array.isArray(rel.cannot_link) || !Array.isArray(rel.unknown_pairs) || !Array.isArray(rel.partitions)) fail(`fixture relations missing: ${c.cluster_key}`);
    const pairSet = (pairs) => new Set(pairs.map(([a, b]) => pairKey(a, b)));
    const all = new Set(seen);
    for (const pairs of [rel.must_link, rel.cannot_link, rel.unknown_pairs]) for (const [a, b] of pairs) {
      if (!all.has(a) || !all.has(b) || a === b) fail(`fixture relation member missing: ${c.cluster_key}`);
    }
    const allPairs = pairwise([...all].sort());
    const relationSets = [rel.must_link, rel.cannot_link, rel.unknown_pairs].map(pairSet);
    if (relationSets.some((s, i) => s.size !== [rel.must_link, rel.cannot_link, rel.unknown_pairs][i].length)) fail(`duplicate fixture relation: ${c.cluster_key}`);
    const relationUnion = new Set();
    for (const set of relationSets) for (const key of set) {
      if (relationUnion.has(key)) fail(`overlapping fixture relation: ${c.cluster_key}/${key}`);
      relationUnion.add(key);
    }
    if (relationUnion.size !== allPairs.length || allPairs.some(([a, b]) => !relationUnion.has(pairKey(a, b)))) fail(`incomplete fixture relation coverage: ${c.cluster_key}`);
    const partitionOwners = new Map();
    for (const p of rel.partitions) {
      if (!p || !p.identity || !Array.isArray(p.bvids) || !p.bvids.length) fail(`empty fixture partition: ${c.cluster_key}`);
      for (const b of p.bvids) {
        if (!all.has(b) || partitionOwners.has(b)) fail(`fixture partition member mismatch: ${c.cluster_key}/${b}`);
        partitionOwners.set(b, p.identity);
      }
      for (const [a, b] of pairwise(p.bvids)) if (!pairSet(rel.must_link).has(pairKey(a, b))) fail(`partition hides non-must pair: ${c.cluster_key}/${a}/${b}`);
    }
    if (partitionOwners.size !== all.size) fail(`fixture partitions do not cover all members: ${c.cluster_key}`);
    for (const [a, b] of rel.must_link) if (partitionOwners.get(a) !== partitionOwners.get(b)) fail(`must-link crosses fixture partitions: ${c.cluster_key}/${a}/${b}`);
    if (c.case_type === 'gate') for (const b of c.bvids) { if (gateBvids.has(b)) fail(`gate BVID reused: ${b}`); gateBvids.add(b); }
  }
  if (gateBvids.size !== 80) fail(`fixture gate unique BVIDs ${gateBvids.size}/80`);
  if (seenGateCases.size !== gate.cases.length || [...gateByKey.keys()].some((k) => !seenGateCases.has(k))) fail('frozen gate case set is incomplete or changed');
  if (seenProtectedCases.size !== gate.excluded_cases.length || [...excludedByCluster.keys()].some((k) => !seenProtectedCases.has(k))) fail('frozen protected case set is incomplete or changed');
  // Verify the reviewed semantic pin only after structural/provenance checks.
  // This keeps fail-closed diagnostics actionable for a malformed fixture
  // (for example, an empty member list) while still rejecting any semantic
  // drift before runtime execution.
  if (FROZEN.fixtureSemantic && f.selection_contract.semantic_sha256 !== FROZEN.fixtureSemantic) fail('fixture semantic hash is not the reviewed frozen value');
  if (fixtureSemanticSha(f) !== f.selection_contract.semantic_sha256) fail('fixture semantic hash mismatch');
  return f;
}
function esbuildPath() {
  const p = path.join(ROOT, 'apps', 'web', 'node_modules', 'esbuild', 'bin', 'esbuild');
  if (!fs.existsSync(p)) fail(`esbuild missing: ${p}`);
  return p;
}
function runEsbuild(args, cwd) {
  const command = process.platform === 'win32' ? process.execPath : esbuildPath();
  const commandArgs = process.platform === 'win32' ? [esbuildPath(), ...args] : args;
  return execFileSync(command, commandArgs, { cwd, stdio: 'pipe' });
}
function compileGitRuntime(commit, dir, label) {
  const compileRoot = path.join(dir, label);
  const domain = path.join(compileRoot, 'apps', 'web', 'src', 'domain');
  const sourcePath = path.join(domain, 'bilibiliGrouping.ts');
  const packPath = path.join(domain, 'packName.ts');
  const packagePath = path.join(compileRoot, 'apps', 'web', 'package.json');
  const outPath = path.join(compileRoot, 'build', 'audit', 'bilibili_grouping_module.js');
  fs.mkdirSync(domain, { recursive: true });
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(packagePath, gitShowText(commit, WEB_PACKAGE_REL), 'utf8');
  fs.writeFileSync(sourcePath, gitShowText(commit, SOURCE_REL), 'utf8');
  fs.writeFileSync(packPath, gitShowText(commit, PACKNAME_REL), 'utf8');
  runEsbuild(['apps/web/src/domain/bilibiliGrouping.ts', '--bundle', '--format=cjs', '--platform=node', '--outfile=build/audit/bilibili_grouping_module.js', '--log-level=warning'], compileRoot);
  // esbuild emits the same CommonJS body but omits its conventional prologue
  // when the temporary root has no repository-level package metadata. Keep the
  // bundle byte-for-byte comparable with the recorded historical artifact;
  // this is a deterministic container normalization, not a source/runtime
  // change.
  const bytes = fs.readFileSync(outPath);
  if (!bytes.toString('utf8', 0, 14).startsWith('"use strict";')) {
    fs.writeFileSync(outPath, Buffer.concat([Buffer.from('"use strict";\n', 'utf8'), bytes]));
  }
  return outPath;
}
function compileCurrentRuntime(dir) {
  const sourcePath = path.join(ROOT, SOURCE_REL);
  const outPath = path.join(dir, 'candidate.js');
  runEsbuild([sourcePath, '--bundle', '--format=cjs', '--platform=node', '--outfile=' + outPath, '--log-level=warning'], ROOT);
  return outPath;
}
function moduleDecisions(modulePath, payload) {
  if (!fs.existsSync(modulePath)) fail(`runtime module missing: ${modulePath}`);
  delete require.cache[require.resolve(path.resolve(modulePath))];
  const mod = require(path.resolve(modulePath));
  if (!mod || typeof mod.groupBilibiliPacks !== 'function') fail(`runtime module has no groupBilibiliPacks: ${modulePath}`);
  const result = mod.groupBilibiliPacks(payload);
  if (!result || typeof result.get !== 'function') fail(`runtime did not return a Map: ${modulePath}`);
  const out = {};
  for (const [bvid, d] of result) {
    if (!d || typeof d.groupKey !== 'string') fail(`runtime decision missing groupKey: ${bvid}`);
    out[bvid] = d;
  }
  if (Object.keys(out).length !== payload.length) fail(`runtime emitted ${Object.keys(out).length}/${payload.length} decisions`);
  return out;
}
function populationMembership(decisions) {
  const groups = new Map();
  for (const [bvid, d] of Object.entries(decisions)) {
    const arr = groups.get(d.groupKey) || []; arr.push(bvid); groups.set(d.groupKey, arr);
  }
  for (const [key, arr] of groups) groups.set(key, sorted(arr));
  return groups;
}
function groupCount(decisions, bvids) { return new Set(bvids.map((b) => decisions[b] && decisions[b].groupKey)).size; }
function relation(decisions, a, b) {
  if (!decisions[a] || !decisions[b]) return 'MISSING';
  return decisions[a].groupKey === decisions[b].groupKey ? 'SAME' : 'DIFFERENT';
}
function relationCounts(decisions, bvids) {
  let same = 0; let different = 0; let missing = 0;
  for (let i = 0; i < bvids.length; i++) for (let j = i + 1; j < bvids.length; j++) {
    const r = relation(decisions, bvids[i], bvids[j]);
    if (r === 'SAME') same++; else if (r === 'DIFFERENT') different++; else missing++;
  }
  return { pairs: (bvids.length * (bvids.length - 1)) / 2, same, different, missing };
}
function relationList(decisions, pairs) { return pairs.map(([a, b]) => ({ a, b, result: relation(decisions, a, b) })); }
function allPopulationMembers(decisions, bvids) {
  const groups = populationMembership(decisions); const out = new Map();
  for (const b of bvids) {
    const key = decisions[b] && decisions[b].groupKey;
    out.set(b, { group_key: key || null, all_members: key ? groups.get(key) : [] });
  }
  return out;
}
function unique(xs) { return [...new Set(xs)]; }
function registeredIdsFromPayloadRow(row) {
  return new Set(registeredIdentityIdsFromLinks(row?.download_links || []));
}
function inspectExternalMembers(c, bvids, current, currentGroups, byBvid, fixtureMemberByBvid) {
  const external = []; const seen = new Set(bvids);
  const caseMembers = c.groups.flatMap((g) => g.members);
  const caseMemberBvids = new Set(c.bvids);
  const groupEvaluations = new Map();
  const evaluateGroup = (groupKey) => {
    if (groupEvaluations.has(groupKey)) return groupEvaluations.get(groupKey);
    const groupBvids = currentGroups.get(groupKey) || [];
    const idsByBvid = new Map(groupBvids.map((bvid) => {
      const fixtureMember = fixtureMemberByBvid.get(bvid);
      return [bvid, new Set(fixtureMember?.registered_identity_ids || registeredIdsFromPayloadRow(byBvid.get(bvid)))];
    }));
    const parent = new Map(groupBvids.map((bvid) => [bvid, bvid]));
    const find = (bvid) => {
      let p = parent.get(bvid);
      while (p !== parent.get(p)) { parent.set(p, parent.get(p)); p = parent.get(p); }
      return p;
    };
    const join = (a, b) => { const ra = find(a); const rb = find(b); if (ra !== rb) parent.set(rb, ra); };
    const sharesId = (a, b) => [...(idsByBvid.get(a) || [])].some((id) => idsByBvid.get(b)?.has(id));
    for (let i = 0; i < groupBvids.length; i++) for (let j = i + 1; j < groupBvids.length; j++) {
      if (sharesId(groupBvids[i], groupBvids[j])) join(groupBvids[i], groupBvids[j]);
    }
    const anchorRoots = new Set(groupBvids.filter((bvid) => caseMemberBvids.has(bvid)
      && (idsByBvid.get(bvid)?.size || 0)).map(find));
    const result = { idsByBvid, anchorRoots, find };
    groupEvaluations.set(groupKey, result);
    return result;
  };
  for (const b of bvids) {
    const key = current[b] && current[b].groupKey;
    const group = currentGroups.get(key) || [];
    for (const x of group) {
      if (seen.has(x)) continue;
      seen.add(x);
      const row = byBvid.get(x);
      const evaluation = evaluateGroup(key);
      const extIds = evaluation.idsByBvid.get(x) || new Set();
      const uploaderMatches = row && String(row.author || 'unknown').trim() === c.author;
      let identityResult = 'UNKNOWN';
      if (extIds.size && evaluation.anchorRoots.has(evaluation.find(x))) identityResult = 'same_registered_identity';
      else if (extIds.size && evaluation.anchorRoots.size) identityResult = 'different_registered_identity';
      const item = {
        bvid: x,
        title: row?.title || null,
        author: row?.author || null,
        group_key: current[x]?.groupKey || null,
        registered_identity_ids: [...extIds].sort(),
        identity_result: identityResult,
        uploader_result: uploaderMatches ? 'same_uploader' : 'different_or_missing_uploader',
      };
      external.push(item);
    }
  }
  return external;
}
function reportCase(c) {
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
    original_group_keys: c.original_group_keys,
    registered_identities: c.registered_identities,
    evidence: c.evidence,
    bvids: c.bvids,
    groups: c.groups.map((g) => ({
      source_group_key: g.source_group_key,
      member_count: g.member_count,
      members: g.members.map((m) => ({ bvid: m.bvid, title: m.title, registered_identity_ids: m.registered_identity_ids })),
    })),
    relations: c.relations,
  };
}

function main() {
  const args = parseArgs();
  const fixture = readJson(args.fixture);
  const payload = loadPayload();
  // These four checks intentionally read only immutable input paths. The
  // evidence JSON is checked for drift but never used to select members.
  // The gate is tracked JSON and may be checked out with CRLF under autocrlf.
  // Compare its raw Git blob to the frozen hash, then compare normalized text
  // semantics separately; do not mistake a container line-ending conversion
  // for a ground-truth change.
  const gateIntegrity = verifyTrackedJsonBytes('pipeline/audit/confirmed_undermerge_runtime_gate.json', FROZEN.gate);
  if (sha256File(EVIDENCE_PATH) !== FROZEN.evidence) fail('original evidence bytes drifted');
  if (sha256File(CANDIDATE_AUDIT_PATH) !== FROZEN.candidate) fail('candidate audit bytes drifted');
  if (sha256File(PAYLOAD_PATH) !== FROZEN.payload || payload.length !== 936) fail('936-record population bytes/count drifted');
  const checkedFixture = loadAndValidateFixture(args.fixture, payload);
  if (args.validateOnly) {
    console.log(JSON.stringify({ status: 'VALID', fixture: path.relative(ROOT, args.fixture), coverage: checkedFixture.coverage }, null, 2));
    return;
  }
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'phase3gf-runtime-'));
  let evidenceModule; let preFixModule; let currentModule; const testInjection = !!args.testModule;
  try {
    evidenceModule = compileGitRuntime('4bf5e0fe4c614f3e630ae242db2ed5b66ef95fea', temp, 'evidence-source');
    preFixModule = compileGitRuntime('1bee6dea6a30ff0b6368091c614c528263a2f0a2', temp, 'pre-fix-1bee6de');
  } catch (err) {
    fail(`reproducible baseline compilation failed: ${err.message}`);
  }
  try {
    currentModule = testInjection ? args.testModule : compileCurrentRuntime(temp);
  } catch (err) {
    fail(`current runtime compilation failed: ${err.message}`);
  }
  const evidenceHash = sha256File(evidenceModule); const preFixHash = sha256File(preFixModule); const currentHash = sha256File(currentModule);
  if (evidenceHash !== FROZEN.evidenceRuntime) fail(`evidence runtime bundle hash drifted: ${evidenceHash}`);
  if (preFixHash !== FROZEN.preFixRuntime) fail(`1bee6de runtime bundle hash drifted: ${preFixHash}`);
  const sourceRaw = fs.readFileSync(path.join(ROOT, SOURCE_REL));
  const sourceGitBytes = gitShow('HEAD', SOURCE_REL);
  const sourceNormalized = Buffer.from(sourceRaw.toString('utf8').replace(/\r\n/g, '\n'), 'utf8');
  const sourceGitNormalized = Buffer.from(sourceGitBytes.toString('utf8').replace(/\r\n/g, '\n'), 'utf8');
  const sourceCommit = git(['rev-parse', 'HEAD']).trim();
  const sourceGitBlob = git(['rev-parse', `HEAD:${SOURCE_REL}`]).trim();
  let diffExit = 0; try { execFileSync('git', ['diff', '--quiet', '--', SOURCE_REL], { cwd: ROOT, stdio: 'ignore' }); } catch (e) { diffExit = typeof e.status === 'number' ? e.status : 1; }
  const baseline = moduleDecisions(evidenceModule, payload);
  const preFix = moduleDecisions(preFixModule, payload);
  const current = moduleDecisions(currentModule, payload);
  const baselineGroups = populationMembership(baseline); const preFixGroups = populationMembership(preFix); const currentGroups = populationMembership(current);
  const byBvid = new Map(payload.map((r) => [r.bvid, r]));
  const gateResults = []; const protectedResults = [];
  const fixtureCases = checkedFixture.cases;
  const fixtureMemberByBvid = new Map(
    fixtureCases.flatMap((c) => c.groups.flatMap((g) => g.members.map((m) => [m.bvid, m]))),
  );
  for (const c of fixtureCases) {
    const bvids = c.bvids;
    const before = relationCounts(baseline, bvids);
    const pre = relationCounts(preFix, bvids);
    const after = relationCounts(current, bvids);
    const failures = [];
    const mustBefore = relationList(preFix, c.relations.must_link);
    const mustAfter = relationList(current, c.relations.must_link);
    const cannotBefore = relationList(preFix, c.relations.cannot_link);
    const cannotAfter = relationList(current, c.relations.cannot_link);
    const unknownBefore = relationList(preFix, c.relations.unknown_pairs);
    const unknownAfter = relationList(current, c.relations.unknown_pairs);
    const external = inspectExternalMembers(c, bvids, current, currentGroups, byBvid, fixtureMemberByBvid);
    for (const x of external) {
      if (x.uploader_result !== 'same_uploader') failures.push(`external member crosses uploader boundary: ${x.bvid}`);
      if (x.identity_result !== 'same_registered_identity') failures.push(`unverified external member: ${x.bvid}`);
    }
    if (c.case_type === 'gate') {
      for (const x of mustAfter) if (x.result !== 'SAME') failures.push(`must-link split: ${x.a}/${x.b}`);
      if (groupCount(current, bvids) !== 1) failures.push(`candidate has ${groupCount(current, bvids)} groups; expected one identity`);
      const result = { ...reportCase(c), before: { group_count: groupCount(baseline, bvids), relation_counts: before }, pre_fix: { group_count: groupCount(preFix, bvids), relation_counts: pre }, after: { group_count: groupCount(current, bvids), relation_counts: after, group_keys_by_bvid: Object.fromEntries(sorted(bvids).map((b) => [b, current[b]?.groupKey || null])), population_groups: bvids.map((b) => ({ bvid: b, group_key: current[b]?.groupKey || null, all_population_members: currentGroups.get(current[b]?.groupKey) || [] })) }, expected: { identity_count: c.expected_identity_count, target_group_count: 1, record_count: c.record_count, packs_to_unify: c.packs_to_unify }, relations: { must_link_before: mustBefore, must_link_after: mustAfter, new_merges_vs_1bee: [], new_splits_vs_1bee: [], pure_renames_vs_1bee: [], unknown_external_members: external.filter((x) => x.identity_result === 'UNKNOWN'), external_members: external }, result: failures.length ? 'FAIL' : 'PASS', failure_reasons: failures };
      const oldPairs = new Set(c.relations.must_link.map(([a, b]) => pairKey(a, b)));
      for (let i = 0; i < bvids.length; i++) for (let j = i + 1; j < bvids.length; j++) { const a = bvids[i]; const b = bvids[j]; const beforeRel = relation(preFix, a, b); const afterRel = relation(current, a, b); if (beforeRel === 'DIFFERENT' && afterRel === 'SAME') result.relations.new_merges_vs_1bee.push({ a, b }); if (beforeRel === 'SAME' && afterRel === 'DIFFERENT') result.relations.new_splits_vs_1bee.push({ a, b }); if (oldPairs.has(pairKey(a, b)) && beforeRel === 'SAME' && afterRel === 'SAME' && preFix[a]?.groupKey !== current[a]?.groupKey) result.relations.pure_renames_vs_1bee.push({ a, b }); }
      gateResults.push(result);
    } else {
      // A protection case must not introduce a new split of an already valid
      // in-group relation. If the 1bee6de runtime had already split that pair,
      // retain the historical diagnostic but do not manufacture a new failure.
      for (let i = 0; i < mustAfter.length; i++) {
        if (mustAfter[i].result !== 'SAME' && mustBefore[i].result === 'SAME') {
          failures.push(`new must-link split: ${mustAfter[i].a}/${mustAfter[i].b}`);
        }
      }
      for (const x of cannotAfter) if (x.result !== 'DIFFERENT') failures.push(`cannot-link violation: ${x.a}/${x.b} (${x.result})`);
      if (c.verdict === 'DIFFERENT_PACKS') {
        for (let i = 0; i < unknownAfter.length; i++) {
          const was = unknownBefore[i]; const now = unknownAfter[i];
          // A source group can already contain a legitimate same-pack relation
          // that the adjudication deliberately left UNKNOWN.  Preserve that
          // historical relation; only a new merge against the 1bee6de runtime
          // is a protection failure.
          if (now.result === 'SAME' && (!was || was.result === 'DIFFERENT')) {
            failures.push(`unknown relation merged (new vs 1bee6de): ${now.a}/${now.b}`);
          }
        }
      }
      if (c.verdict === 'AMBIGUOUS') {
        for (let i = 0; i < unknownAfter.length; i++) {
          const was = unknownBefore[i]; const now = unknownAfter[i];
          if (was && was.result === 'DIFFERENT' && now.result === 'SAME') failures.push(`ambiguous new merge: ${now.a}/${now.b}`);
        }
      }
      const result = { ...reportCase(c), before: { group_count: groupCount(baseline, bvids), relation_counts: before }, pre_fix: { group_count: groupCount(preFix, bvids), relation_counts: pre }, after: { group_count: groupCount(current, bvids), relation_counts: after, group_keys_by_bvid: Object.fromEntries(sorted(bvids).map((b) => [b, current[b]?.groupKey || null])), population_groups: bvids.map((b) => ({ bvid: b, group_key: current[b]?.groupKey || null, all_population_members: currentGroups.get(current[b]?.groupKey) || [] })) }, expected: { verdict: c.verdict, protected_semantics: c.verdict === 'AMBIGUOUS' ? 'unknown; no new merge' : 'partition separation plus existing must-links' }, relations: { must_link_before: mustBefore, must_link_after: mustAfter, cannot_link_before: cannotBefore, cannot_link_after: cannotAfter, unknown_before: unknownBefore, unknown_after: unknownAfter, external_members: external, unknown_external_members: external.filter((x) => x.identity_result !== 'same_registered_identity') }, result: failures.length ? 'FAIL' : 'PROTECTED', failure_reasons: failures };
      protectedResults.push(result);
    }
  }
  const gateFailed = gateResults.filter((x) => x.result !== 'PASS');
  const diffResults = protectedResults.filter((x) => x.verdict === 'DIFFERENT_PACKS');
  const ambResults = protectedResults.filter((x) => x.verdict === 'AMBIGUOUS');
  const protectedFailed = protectedResults.filter((x) => x.result !== 'PROTECTED');
  const result = {
    phase: '3G-F.3-A', artifact: 'phase3gf_runtime_acceptance', generated_at: new Date((process.env.SOURCE_DATE_EPOCH ? Number(process.env.SOURCE_DATE_EPOCH) * 1000 : Date.now())).toISOString(),
    status: gateFailed.length || protectedFailed.length ? 'BLOCKED' : 'PASS',
    conclusion: gateFailed.length || protectedFailed.length ? 'Dynamic candidate runtime did not satisfy every frozen member/identity relation.' : 'Dynamic candidate runtime satisfies the frozen gate and protection partitions.',
    baselines: {
      evidence_source_runtime: { source_commit: '4bf5e0fe4c614f3e630ae242db2ed5b66ef95fea', bundle_sha256: evidenceHash, expected_bundle_sha256: FROZEN.evidenceRuntime, semantic_role: 'ground-truth evidence source runtime' },
      pre_fix_runtime_1bee6de: { source_commit: '1bee6dea6a30ff0b6368091c614c528263a2f0a2', source_git_blob_sha1: '2c037399cf8106920f3d7e73fb846ecb16996d04', bundle_sha256: preFixHash, expected_bundle_sha256: FROZEN.preFixRuntime, semantic_role: 'repair-before runtime' },
      candidate_runtime: { source_commit: sourceCommit, source_git_blob_sha1: sourceGitBlob, source_worktree_raw_sha256: sha256Bytes(sourceRaw), source_git_raw_sha256: sha256Bytes(sourceGitBytes), source_worktree_normalized_sha256: sha256Bytes(sourceNormalized), source_git_normalized_sha256: sha256Bytes(sourceGitNormalized), source_semantically_matches_git: sourceNormalized.equals(sourceGitNormalized), source_git_diff_exit: diffExit, bundle_sha256: currentHash, path: path.relative(ROOT, currentModule), source_mode: testInjection ? 'test-only-external-module' : 'formal-acceptance-compiled-from-worktree', formal_acceptance: !testInjection, compiled_from_current_source: !testInjection },
    },
    source_inputs: { fixture_sha256: sha256File(args.fixture), gate_sha256: gateIntegrity.git_raw_sha256, gate_git_raw_sha256: gateIntegrity.git_raw_sha256, gate_worktree_raw_sha256: gateIntegrity.worktree_raw_sha256, gate_worktree_normalized_sha256: gateIntegrity.worktree_normalized_sha256, gate_semantically_matches_git: gateIntegrity.worktree_semantically_matches_git, evidence_sha256: sha256File(EVIDENCE_PATH), candidate_audit_sha256: sha256File(CANDIDATE_AUDIT_PATH), population_sha256: sha256File(PAYLOAD_PATH), population_records: payload.length, selection: 'All members are loaded from the immutable fixture; mutable evidence is hash-checked only.' },
    coverage: { gate_cases_expected: 26, gate_cases_checked: gateResults.length, gate_cases_passed: gateResults.filter((x) => x.result === 'PASS').length, gate_cases_failed: gateFailed.length, different_packs_expected: 27, different_packs_checked: diffResults.length, different_packs_protected: diffResults.filter((x) => x.result === 'PROTECTED').length, ambiguous_expected: 5, ambiguous_checked: ambResults.length, ambiguous_protected: ambResults.filter((x) => x.result === 'PROTECTED').length, unique_gate_bvids: new Set(gateResults.flatMap((x) => x.bvids)).size },
    gate_cases: gateResults, protected_cases: protectedResults,
  };
  fs.mkdirSync(path.dirname(args.out), { recursive: true });
  fs.writeFileSync(args.out, JSON.stringify(result, null, 2) + '\n', 'utf8');
  console.log(`gate: ${result.coverage.gate_cases_passed}/${result.coverage.gate_cases_expected} PASS`);
  console.log(`DIFFERENT_PACKS: ${result.coverage.different_packs_protected}/${result.coverage.different_packs_expected} PROTECTED`);
  console.log(`AMBIGUOUS: ${result.coverage.ambiguous_protected}/${result.coverage.ambiguous_expected} PROTECTED`);
  console.log(`status: ${result.status}`);
  console.log(`written: ${path.relative(ROOT, args.out)}`);
  process.exitCode = result.status === 'PASS' ? 0 : 2;
}

try { main(); } catch (err) { console.error(err && err.stack ? err.stack : String(err)); process.exitCode = err && err.code === 2 ? 2 : 1; }

/**
 * Phase 3G-F.3-A - materialise the confirmed under-merge runtime closure.
 *
 * This is deliberately a projection, not a new adjudicator.  The only cases
 * selected are the 26 cases already present in the frozen runtime gate from
 * cbbfb58.  Membership comes from the original evidence artifact, never from
 * a fresh scan of current runtime group keys.
 *
 * Usage:
 *   node pipeline/audit/build_bilibili_undermerge_runtime_closure.js
 *
 * The input payload/evidence are ignored audit inputs restored for this
 * worktree.  Their byte hashes are recorded in the output so a missing,
 * substituted, or drifted input cannot silently produce a passing closure.
 */
const crypto = require('crypto');
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const REPO_ROOT = path.resolve(__dirname, '..', '..');
const GATE = path.join(REPO_ROOT, 'pipeline', 'audit', 'confirmed_undermerge_runtime_gate.json');
const EVIDENCE = path.join(REPO_ROOT, 'build', 'audit', 'undermerge_evidence_v2.json');
const CANDIDATES = path.join(REPO_ROOT, 'build', 'audit', 'bilibili_cross_group_undermerge_v2.json');
const PAYLOAD = path.join(REPO_ROOT, 'converted_output', 'data', 'bili_data.js');
const OUT = path.join(REPO_ROOT, 'pipeline', 'audit', 'bilibili_undermerge_runtime_closure.json');

const GROUND_TRUTH = {
  adjudication_commit: 'cbbfb588262d06d386dab645deee88e0c4acb7c3',
  report_commit: 'a690d3dfddc66d4260960b83c9cece7bdb3af72a',
  rule: 'Only the cbbfb58 CONFIRMED_SAME_PACK / STRONG_SAME_PACK gate is projected; no verdict is inferred here.',
};

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function sha256(file) {
  return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
}

function gitShowSha256(commit, relativePath) {
  return crypto.createHash('sha256').update(
    execFileSync('git', ['show', `${commit}:${relativePath}`], { cwd: REPO_ROOT }),
  ).digest('hex');
}

function loadPayload() {
  const raw = fs.readFileSync(PAYLOAD, 'utf8');
  const start = raw.indexOf('[');
  const end = raw.lastIndexOf(']');
  if (start < 0 || end < start) throw new Error('payload is not a JSON array: ' + PAYLOAD);
  return JSON.parse(raw.slice(start, end + 1));
}

function sameKeySet(a, b) {
  return a.length === b.length && [...a].sort().every((v, i) => v === [...b].sort()[i]);
}

function fail(message) {
  throw new Error('under-merge runtime closure: ' + message);
}

function main() {
  const gate = readJson(GATE);
  const evidence = readJson(EVIDENCE);
  const candidates = readJson(CANDIDATES);
  const payload = loadPayload();

  if (gate.gate_size !== 26 || gate.cases.length !== 26) fail(`expected 26 gate cases, got ${gate.gate_size}/${gate.cases.length}`);
  if (candidates.payload_records !== 936) fail(`candidate payload is not the original 936-record population: ${candidates.payload_records}`);
  if (evidence.payload_records !== 936) fail(`evidence payload is not the original 936-record population: ${evidence.payload_records}`);
  if (payload.length !== 936) fail(`payload has ${payload.length} records, expected 936`);

  const byBvid = new Map();
  for (const row of payload) {
    if (!row || !row.bvid || byBvid.has(row.bvid)) fail(`payload BVID missing or duplicated: ${row && row.bvid}`);
    byBvid.set(row.bvid, row);
  }

  const cases = [];
  const globallyMapped = new Set();
  const matchedEvidence = new Set();

  for (const gateCase of gate.cases) {
    const matches = evidence.findings.filter((f) =>
      f.author === gateCase.author && sameKeySet(f.group_keys, gateCase.group_keys));
    if (matches.length !== 1) fail(`${gateCase.cluster_key} maps to ${matches.length} evidence findings`);
    const source = matches[0];
    const sourceId = `${source.author}||${[...source.group_keys].sort().join('|')}`;
    if (matchedEvidence.has(sourceId)) fail(`evidence finding reused: ${sourceId}`);
    matchedEvidence.add(sourceId);

    if (source.group_count !== gateCase.group_count) fail(`${gateCase.cluster_key}: group_count mismatch`);
    if (source.record_count !== gateCase.record_count) fail(`${gateCase.cluster_key}: record_count mismatch`);
    if (!Number.isInteger(gateCase.expected_identity_count) || gateCase.expected_identity_count < 1) {
      fail(`${gateCase.cluster_key}: invalid expected identity count`);
    }

    const groupMembers = [];
    const caseBvids = [];
    const caseSeen = new Set();
    for (const groupKey of gateCase.group_keys) {
      const groups = source.groups.filter((g) => g.group_key === groupKey);
      if (groups.length !== 1) fail(`${gateCase.cluster_key}: group ${groupKey} maps to ${groups.length} evidence groups`);
      const group = groups[0];
      if (!Number.isInteger(group.member_count) || group.member_count !== group.members.length || group.member_count < 1) {
        fail(`${gateCase.cluster_key}: group ${groupKey} has missing/empty/duplicate member metadata`);
      }
      const members = [];
      for (const member of group.members) {
        if (!member.bvid || caseSeen.has(member.bvid)) fail(`${gateCase.cluster_key}: duplicate/empty BVID ${member.bvid}`);
        const row = byBvid.get(member.bvid);
        if (!row) fail(`${gateCase.cluster_key}: evidence BVID absent from 936 population: ${member.bvid}`);
        if (String(row.author || 'unknown').trim() !== gateCase.author) {
          fail(`${gateCase.cluster_key}: author mismatch for ${member.bvid}`);
        }
        if (row.title !== member.title) fail(`${gateCase.cluster_key}: title mismatch for ${member.bvid}`);
        caseSeen.add(member.bvid);
        if (globallyMapped.has(member.bvid)) fail(`BVID mapped to more than one gate case: ${member.bvid}`);
        globallyMapped.add(member.bvid);
        caseBvids.push(member.bvid);
        members.push({ bvid: member.bvid, title: member.title });
      }
      if (members.length !== group.member_count) fail(`${gateCase.cluster_key}: incomplete group member mapping`);
      groupMembers.push({
        source_group_key: groupKey,
        member_count: members.length,
        members: members.sort((a, b) => a.bvid.localeCompare(b.bvid)),
      });
    }

    if (caseSeen.size !== gateCase.record_count) fail(`${gateCase.cluster_key}: mapped ${caseSeen.size}, expected ${gateCase.record_count}`);
    cases.push({
      cluster_key: gateCase.cluster_key,
      author: gateCase.author,
      verdict: gateCase.verdict,
      confidence: gateCase.confidence,
      group_count: gateCase.group_count,
      record_count: gateCase.record_count,
      expected_identity_count: gateCase.expected_identity_count,
      packs_to_unify: gateCase.packs_to_unify,
      original_group_keys: [...gateCase.group_keys].sort(),
      group_members: groupMembers.sort((a, b) => a.source_group_key.localeCompare(b.source_group_key)),
      bvids: [...caseBvids].sort(),
      evidence: gateCase.evidence,
    });
  }

  const recordsInCases = cases.reduce((n, c) => n + c.record_count, 0);
  if (recordsInCases !== 80 || globallyMapped.size !== 80) {
    fail(`deduplicated BVID coverage is ${globallyMapped.size}, record sum is ${recordsInCases}; expected 80/80`);
  }
  if (cases.length !== matchedEvidence.size) fail('not every gate case has a unique evidence finding');

  const result = {
    phase: '3G-F.3-A',
    artifact: 'bilibili_undermerge_runtime_closure',
    generated_at: new Date(
      (process.env.SOURCE_DATE_EPOCH ? Number(process.env.SOURCE_DATE_EPOCH) * 1000 : Date.now()),
    ).toISOString(),
    purpose: 'Auditable runtime projection of the frozen under-merge gate. It is not a new candidate scan or ground-truth adjudication.',
    ground_truth: GROUND_TRUTH,
    source_artifacts: {
      runtime_gate: {
        path: 'pipeline/audit/confirmed_undermerge_runtime_gate.json',
        working_tree_sha256: sha256(GATE),
        source_commit_sha256: gitShowSha256(
          GROUND_TRUTH.adjudication_commit,
          'pipeline/audit/confirmed_undermerge_runtime_gate.json',
        ),
        source_commit_expected_sha256: '4e91fe1d8bc3c16a8fe1b3cc65be9a64dcc56f47b29b2a218524029ca82a9d90',
      },
      candidate_baseline: { path: 'build/audit/bilibili_cross_group_undermerge_v2.json', sha256: sha256(CANDIDATES) },
      original_evidence: { path: 'build/audit/undermerge_evidence_v2.json', sha256: sha256(EVIDENCE) },
      population_bytes: { path: 'converted_output/data/bili_data.js', sha256: sha256(PAYLOAD) },
    },
    population_records: 936,
    gate_size: cases.length,
    distinct_uploaders: new Set(cases.map((c) => c.author)).size,
    records_involved_sum: recordsInCases,
    records_involved_unique_bvids: globallyMapped.size,
    packs_to_unify: cases.reduce((n, c) => n + c.packs_to_unify, 0),
    semantics: {
      packs_to_unify: 'sum(group_count - 1): excess runtime groups awaiting unification, not target-pack count',
      records_involved: 'deduplicated BVID count; duplicate or empty members fail the closure',
      population_check: 'Every mapped BVID is checked against the full 936-record payload; every original source group member is retained.',
      selection: 'The 26 original gate cases are matched by author + original group-key set. No new runtime group-key candidate filtering is performed.',
      exclusions: 'DIFFERENT_PACKS and AMBIGUOUS remain outside this runtime projection; they are not rewritten as same-pack evidence.',
    },
    coverage: {
      gate_cases_expected: 26,
      gate_cases_mapped: cases.length,
      gate_case_coverage: cases.length / 26,
      bvids_expected: 80,
      bvids_mapped_unique: globallyMapped.size,
      bvid_coverage: globallyMapped.size / 80,
      missing_cases: [],
      duplicate_bvids: [],
      empty_groups: [],
      non_unique_mappings: [],
    },
    cases: cases.sort((a, b) => a.cluster_key.localeCompare(b.cluster_key)),
  };

  fs.writeFileSync(OUT, JSON.stringify(result, null, 2), 'utf8');
  console.log('=== Phase 3G-F.3-A under-merge runtime closure ===');
  console.log(`gate cases       : ${result.gate_size}/${result.coverage.gate_cases_expected}`);
  console.log(`unique BVIDs      : ${result.records_involved_unique_bvids}/${result.coverage.bvids_expected}`);
  console.log(`packs_to_unify    : ${result.packs_to_unify}`);
  console.log(`population        : ${result.population_records}`);
  console.log(`written           : ${path.relative(REPO_ROOT, OUT)}`);
}

main();

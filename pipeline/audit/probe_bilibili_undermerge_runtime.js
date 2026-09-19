/**
 * Phase 3G-F.3-A - real runtime probe for the under-merge closure.
 *
 * This probe is intentionally diagnostic.  It compiles/runs the actual
 * apps/web/src/domain/bilibiliGrouping.ts output supplied by the caller and
 * compares it with the frozen pre-change runtime bundle.  It never changes
 * runtime group keys and never selects cases from a new scan.
 *
 * Usage:
 *   node pipeline/audit/probe_bilibili_undermerge_runtime.js [current-module]
 *
 * Exit code 0 means all 26 cases closed.  Exit code 2 means the probe ran but
 * the generic runtime did not close the gate; the JSON report still records
 * every case and is the authoritative FAIL/BLOCKED evidence for this phase.
 */
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const REPO_ROOT = path.resolve(__dirname, '..', '..');
const BASELINE = path.join(REPO_ROOT, 'build', 'audit', 'bilibili_grouping_module.js');
const CURRENT = process.argv[2] || path.join(REPO_ROOT, 'build', 'audit', 'bilibili_grouping_runtime_current.js');
const GATE = path.join(REPO_ROOT, 'pipeline', 'audit', 'confirmed_undermerge_runtime_gate.json');
const LEDGER = path.join(REPO_ROOT, 'pipeline', 'audit', 'bilibili_undermerge_adjudication_v2.json');
const CLOSURE = path.join(REPO_ROOT, 'pipeline', 'audit', 'bilibili_undermerge_runtime_closure.json');
const EVIDENCE = path.join(REPO_ROOT, 'build', 'audit', 'undermerge_evidence_v2.json');
const PAYLOAD = path.join(REPO_ROOT, 'converted_output', 'data', 'bili_data.js');
const OUT = path.join(REPO_ROOT, 'pipeline', 'audit', 'bilibili_undermerge_runtime_probe.json');

function loadJson(file) { return JSON.parse(fs.readFileSync(file, 'utf8')); }
function sha256(file) { return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'); }
function sorted(xs) { return [...xs].sort(); }
function sameSet(a, b) {
  const aa = sorted(a); const bb = sorted(b);
  return aa.length === bb.length && aa.every((v, i) => v === bb[i]);
}
function sourceKey(f) { return `${f.author}||${sorted(f.group_keys).join('|')}`; }
function loadPayload() {
  const raw = fs.readFileSync(PAYLOAD, 'utf8');
  return JSON.parse(raw.slice(raw.indexOf('['), raw.lastIndexOf(']') + 1));
}
function decisions(modulePath, records) {
  const mod = require(path.resolve(modulePath));
  const out = {};
  for (const [bvid, decision] of mod.groupBilibiliPacks(records)) out[bvid] = decision;
  return out;
}
function membership(dec) {
  const out = new Map();
  for (const [bvid, d] of Object.entries(dec)) {
    if (!out.has(d.groupKey)) out.set(d.groupKey, []);
    out.get(d.groupKey).push(bvid);
  }
  for (const [key, ids] of out) out.set(key, sorted(ids));
  return out;
}
function snapshot(dec, bvids, populationMembership) {
  const groupKeys = sorted([...new Set(bvids.map((b) => dec[b].groupKey))]);
  return {
    distinct_group_count: groupKeys.length,
    group_keys_by_bvid: Object.fromEntries(sorted(bvids).map((b) => [b, dec[b].groupKey])),
    groups: groupKeys.map((groupKey) => ({
      group_key: groupKey,
      all_population_members: populationMembership.get(groupKey) || [],
    })),
  };
}

function main() {
  const gate = loadJson(GATE);
  const ledger = loadJson(LEDGER);
  const closure = loadJson(CLOSURE);
  const evidence = loadJson(EVIDENCE);
  const payload = loadPayload();
  const byBvid = new Map(payload.map((r) => [r.bvid, r]));
  const baseline = decisions(BASELINE, payload);
  const current = decisions(CURRENT, payload);
  const baselineMembership = membership(baseline);
  const currentMembership = membership(current);
  const evidenceByKey = new Map(evidence.findings.map((f) => [sourceKey(f), f]));
  const gateBvids = new Set(closure.cases.flatMap((c) => c.bvids));
  const gateResults = [];
  const excludedResults = [];

  for (const gateCase of gate.cases) {
    const source = evidenceByKey.get(sourceKey(gateCase));
    const failures = [];
    if (!source) failures.push('original evidence finding is missing');
    const sourceGroups = source ? source.groups : [];
    const bvids = sourceGroups.flatMap((g) => g.members.map((m) => m.bvid));
    if (new Set(bvids).size !== gateCase.record_count) failures.push('source member count is not unique/exact');
    for (const bvid of bvids) {
      if (!byBvid.has(bvid)) failures.push(`BVID absent from 936 population: ${bvid}`);
      if (!baseline[bvid] || !current[bvid]) failures.push(`runtime omitted BVID: ${bvid}`);
    }
    const originalGroupProof = sourceGroups.map((g) => {
      const expected = sorted(g.members.map((m) => m.bvid));
      const actual = baselineMembership.get(g.group_key) || [];
      const exact = sameSet(expected, actual);
      if (!exact) failures.push(`baseline group membership drift for ${g.group_key}`);
      return {
        source_group_key: g.group_key,
        expected_bvids: expected,
        baseline_population_members: actual,
        exact_full_population_membership: exact,
      };
    });
    const before = snapshot(baseline, bvids, baselineMembership);
    const after = snapshot(current, bvids, currentMembership);
    if (after.distinct_group_count !== 1) failures.push(`current runtime still has ${after.distinct_group_count} groups; expected 1`);
    const expectedAll = sorted(bvids);
    for (const g of after.groups) {
      if (!sameSet(g.all_population_members, expectedAll)) {
        failures.push(`current runtime group ${g.group_key} has extra/missing population members`);
      }
    }
    gateResults.push({
      cluster_key: gateCase.cluster_key,
      verdict: gateCase.verdict,
      confidence: gateCase.confidence,
      before,
      after,
      expected: {
        identity_count: gateCase.expected_identity_count,
        target_group_count: 1,
        record_count: gateCase.record_count,
        packs_to_unify: gateCase.packs_to_unify,
      },
      evidence: {
        author: gateCase.author,
        original_group_keys: sorted(gateCase.group_keys),
        source_member_count: bvids.length,
        original_group_membership: originalGroupProof,
        registered_identities: gateCase.registered_identities,
        note: gateCase.evidence,
      },
      result: failures.length ? 'FAIL' : 'PASS',
      failure_reasons: failures,
    });
  }

  for (const excluded of gate.excluded_cases) {
    const finding = ledger.findings.find((f) => f.cluster_key === excluded.cluster_key);
    const failures = [];
    if (!finding) failures.push('excluded ledger finding is missing');
    const bvids = finding ? finding.group_keys.flatMap((gk) => {
      const f = evidence.findings.find((x) => x.author === finding.author && x.group_keys.includes(gk));
      const group = f && f.groups.find((g) => g.group_key === gk);
      return group ? group.members.map((m) => m.bvid) : [];
    }) : [];
    if (bvids.some((b) => gateBvids.has(b))) failures.push('excluded BVID leaked into the confirmed runtime gate');
    const unchanged = bvids.every((b) => baseline[b] && current[b] && baseline[b].groupKey === current[b].groupKey);
    if (!unchanged) failures.push('runtime changed an excluded sample');
    excludedResults.push({
      cluster_key: excluded.cluster_key,
      author: excluded.author,
      verdict: excluded.verdict,
      expected: excluded.verdict === 'AMBIGUOUS'
        ? 'protection sample: preserve existing runtime; do not claim different-pack proof'
        : 'separation constraint: preserve existing runtime split',
      bvid_count: new Set(bvids).size,
      before_after_unchanged: unchanged,
      evidence: excluded.reason,
      result: failures.length ? 'FAIL' : 'PROTECTED',
      failure_reasons: failures,
    });
  }

  const confirmed = excludedResults.filter((x) => x.verdict === 'DIFFERENT_PACKS').length;
  const ambiguous = excludedResults.filter((x) => x.verdict === 'AMBIGUOUS').length;
  const failedGate = gateResults.filter((x) => x.result !== 'PASS');
  const failedExcluded = excludedResults.filter((x) => x.result === 'FAIL');
  const result = {
    phase: '3G-F.3-A',
    artifact: 'bilibili_undermerge_runtime_probe',
    generated_at: new Date((process.env.SOURCE_DATE_EPOCH ? Number(process.env.SOURCE_DATE_EPOCH) * 1000 : Date.now())).toISOString(),
    status: failedGate.length || failedExcluded.length ? 'BLOCKED' : 'PASS',
    conclusion: failedGate.length
      ? 'The current generic grouping runtime does not close the frozen gate. No runtime integration was applied in this A task.'
      : 'The current generic grouping runtime closes the frozen gate.',
    source: {
      ground_truth_commits: ['cbbfb588262d06d386dab645deee88e0c4acb7c3', 'a690d3dfddc66d4260960b83c9cece7bdb3af72a'],
      population_records: payload.length,
      population_sha256: sha256(PAYLOAD),
      evidence_sha256: sha256(EVIDENCE),
      closure_fixture_sha256: sha256(CLOSURE),
      baseline_runtime_bundle_sha256: sha256(BASELINE),
      current_runtime_bundle_sha256: sha256(CURRENT),
      current_runtime_source: 'apps/web/src/domain/bilibiliGrouping.ts',
      selection: '26 cases are loaded from the frozen gate and matched to original evidence group sets; no new runtime group-key scan selects candidates.',
    },
    coverage: {
      gate_cases_expected: 26,
      gate_cases_checked: gateResults.length,
      gate_cases_passed: gateResults.filter((x) => x.result === 'PASS').length,
      gate_cases_failed: failedGate.length,
      different_packs_expected: 27,
      different_packs_checked: confirmed,
      ambiguous_expected: 5,
      ambiguous_checked: ambiguous,
      unique_gate_bvids: new Set(gateResults.flatMap((x) => Object.keys(x.before.group_keys_by_bvid))).size,
    },
    gate_cases: gateResults,
    excluded_cases: excludedResults,
  };
  fs.writeFileSync(OUT, JSON.stringify(result, null, 2), 'utf8');
  console.log(`gate cases: ${result.coverage.gate_cases_passed}/${result.coverage.gate_cases_expected} PASS`);
  console.log(`DIFFERENT_PACKS protected: ${confirmed}/${result.coverage.different_packs_expected}`);
  console.log(`AMBIGUOUS protected: ${ambiguous}/${result.coverage.ambiguous_expected}`);
  console.log(`status: ${result.status}`);
  console.log(`written: ${path.relative(REPO_ROOT, OUT)}`);
  process.exitCode = result.status === 'PASS' ? 0 : 2;
}

main();

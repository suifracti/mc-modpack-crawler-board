/**
 * Phase 3G-F.2-B - RUNTIME GATE list builder.
 *
 * Emits the SUBSET of under-merge findings that a future runtime change is allowed
 * to act on: CONFIRMED_SAME_PACK and STRONG_SAME_PACK only.
 *
 * AMBIGUOUS cases are deliberately EXCLUDED. This is the whole point of separating
 * the ledger from the gate: an ambiguous case is one where the evidence does not
 * settle whether two groups are one pack, and forcing it into the gate would turn
 * an admission of ignorance into a runtime behaviour change. A low gate count is
 * the honest outcome, not a shortfall.
 *
 * Output: pipeline/audit/confirmed_undermerge_runtime_gate.json   (tracked)
 * Usage:  node pipeline/audit/build_undermerge_runtime_gate.js
 */
const fs = require('fs');
const path = require('path');

const REPO_ROOT = path.resolve(__dirname, '..', '..');
const LEDGER = path.join(REPO_ROOT, 'pipeline', 'audit', 'bilibili_undermerge_adjudication_v2.json');
const OUT = path.join(REPO_ROOT, 'pipeline', 'audit', 'confirmed_undermerge_runtime_gate.json');

const GATED_VERDICTS = ['CONFIRMED_SAME_PACK', 'STRONG_SAME_PACK'];

function main() {
  const ledger = JSON.parse(fs.readFileSync(LEDGER, 'utf8'));

  const gated = ledger.findings.filter((f) => GATED_VERDICTS.includes(f.verdict));
  const excluded = ledger.findings.filter((f) => !GATED_VERDICTS.includes(f.verdict));

  // Deterministic: sort by cluster_key.
  gated.sort((a, b) => (a.cluster_key < b.cluster_key ? -1 : 1));
  excluded.sort((a, b) => (a.cluster_key < b.cluster_key ? -1 : 1));

  const result = {
    phase: '3G-F.2-B',
    generated_at: new Date(
      (process.env.SOURCE_DATE_EPOCH ? Number(process.env.SOURCE_DATE_EPOCH) * 1000 : Date.now()),
    ).toISOString(),
    artifact: 'confirmed_undermerge_runtime_gate',
    purpose:
      'The only under-merge cases a runtime change may act on: human-adjudicated CONFIRMED or STRONG same-pack, each with its registered-project evidence.',
    source_ledger: 'pipeline/audit/bilibili_undermerge_adjudication_v2.json',
    gated_verdicts: GATED_VERDICTS,
    exclusions: {
      AMBIGUOUS: 'Not enough evidence to decide. MUST NOT be gated; gating one would convert an admission of ignorance into a behaviour change.',
      DIFFERENT_PACKS: 'Adjudicated as separate packs; the existing split is correct.',
      PARTIAL: 'Some keys belong together and some do not; a cluster-level change would be wrong.',
    },
    gate_size: gated.length,
    distinct_uploaders: new Set(gated.map((f) => f.author)).size,
    records_involved: gated.reduce((n, f) => n + (f.record_count || 0), 0),
    packs_to_unify: gated.reduce((n, f) => n + ((f.group_count || 1) - 1), 0),
    excluded_count: excluded.length,
    cases: gated.map((f) => ({
      cluster_key: f.cluster_key,
      author: f.author,
      verdict: f.verdict,
      confidence: f.confidence,
      group_count: f.group_count,
      record_count: f.record_count,
      expected_identity_count: f.expected_identity_count,
      packs_to_unify: (f.group_count || 1) - 1,
      group_keys: f.group_keys,
      registered_identities: f.project_identities_shared_by_all_groups,
      evidence: f.evidence.note,
    })),
    excluded_cases: excluded.map((f) => ({
      cluster_key: f.cluster_key,
      author: f.author,
      verdict: f.verdict,
      reason: f.evidence.note,
    })),
  };

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(result, null, 2), 'utf8');

  console.log('=== Phase 3G-F.2-B runtime gate list ===');
  console.log(`gate size         : ${result.gate_size}`);
  console.log(`distinct uploaders: ${result.distinct_uploaders}`);
  console.log(`records involved  : ${result.records_involved}`);
  console.log(`packs to unify    : ${result.packs_to_unify}`);
  console.log(`excluded          : ${result.excluded_count}`);
  const bad = gated.filter((f) => f.verdict === 'AMBIGUOUS');
  if (bad.length) console.log('!! AMBIGUOUS LEAKED INTO GATE:', bad.length);
  console.log(`written           : ${path.relative(REPO_ROOT, OUT)}`);
}

main();

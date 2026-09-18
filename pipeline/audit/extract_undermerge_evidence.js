/**
 * Phase 3G-F.2-B - Under-merge EVIDENCE EXTRACTOR.
 *
 * The cross-group scanner emits a review list: clusters of group keys that MIGHT
 * be one pack split apart. To adjudicate them a human has to read the actual
 * member titles, download URLs and QQ identities. Opening the 936-record payload
 * by hand for 58 clusters is not practical, so this script flattens everything a
 * reviewer needs into one file.
 *
 * This is a READ-ONLY, evidence-only tool:
 *   - it emits NO verdict field and no verdict wording
 *   - it does NOT filter or rank; it dumps all members of all flagged groups
 *   - URL / QQ are included as SUPPORTING context only. Phase 3G-E proved a single
 *     Quark URL can cover 28 different packs, so a shared URL alone proves nothing.
 *
 * Output: build/audit/undermerge_evidence_v2.json
 * Usage:  node pipeline/audit/extract_undermerge_evidence.js
 */
const fs = require('fs');
const path = require('path');

global.window = {};
const REPO_ROOT = path.resolve(__dirname, '..', '..');
// The payload carries no groupKey field: the scanner derives it by running the
// real grouping runtime over the records. We must reuse that runtime rather than
// reimplement the key logic, or the evidence would describe different groups
// from the ones the scanner actually flagged.
const newMod = require(path.join(REPO_ROOT, 'build', 'audit', 'bilibili_grouping_module.js'));
const BILI_DATA = path.join(REPO_ROOT, 'converted_output', 'data', 'bili_data.js');
const SCAN = path.join(REPO_ROOT, 'build', 'audit', 'bilibili_cross_group_undermerge_v2.json');
const OUT = path.join(REPO_ROOT, 'build', 'audit', 'undermerge_evidence_v2.json');

// ---------------------------------------------------------------- payload
// bili_data.js assigns a plain JSON array to a global. Read it as text and strip
// the assignment rather than eval'ing the whole file.
function loadPayload() {
  const raw = fs.readFileSync(BILI_DATA, 'utf8');
  return JSON.parse(raw.slice(raw.indexOf('['), raw.lastIndexOf(']') + 1));
}

// bvid -> groupKey, exactly as the scanner computed it.
function deriveGroupKeys(data) {
  const dec = {};
  for (const [b, d] of newMod.groupBilibiliPacks(data)) dec[b] = d;
  return dec;
}

function pick(rec) {
  // Keep the fields a reviewer actually reads. Everything else is noise here.
  const out = {
    bvid: rec.bvid || rec.BV || null,
    title: rec.title || rec.name || null,
    group_key: rec.groupKey || rec.group_key || null,
  };
  // carry through any download / qq / date-ish fields verbatim, whatever they are named
  for (const k of Object.keys(rec)) {
    if (out[k] !== undefined) continue;
    if (/url|link|pan|download|baidu|quark|aliyun|123pan/i.test(k)) out[k] = rec[k];
    else if (/qq/i.test(k)) out[k] = rec[k];
    else if (/date|time|publish|pubdate/i.test(k)) out[k] = rec[k];
  }
  return out;
}

// Collect URL / QQ values from an arbitrary record shape into flat string lists.
function harvest(rec, re, acc) {
  for (const v of Object.values(rec)) {
    if (typeof v === 'string') {
      if (re.test(v)) {
        // a field can hold several links separated by whitespace or commas
        for (const piece of v.split(/[\s,;，；]+/)) if (re.test(piece)) acc.add(piece.trim());
      }
    } else if (Array.isArray(v)) {
      for (const item of v) if (typeof item === 'string' && re.test(item)) acc.add(item.trim());
    }
  }
  return acc;
}

const URL_RE = /https?:\/\//i;
const QQ_RE = /(^|[^\d])(\d{6,12})([^\d]|$)/;

function main() {
  const data = loadPayload();
  const dec = deriveGroupKeys(data);
  const scan = JSON.parse(fs.readFileSync(SCAN, 'utf8'));

  // group_key -> members, using the runtime-derived key (not a field).
  const byGroup = new Map();
  for (const rec of data) {
    const d = dec[rec.bvid];
    if (!d || !d.groupKey) continue;
    if (!byGroup.has(d.groupKey)) byGroup.set(d.groupKey, []);
    byGroup.get(d.groupKey).push(rec);
  }

  const findings = scan.findings.map((f) => {
    const groups = f.group_keys.map((gk) => {
      const members = byGroup.get(gk) || [];
      const urls = new Set();
      const qqs = new Set();
      const cleanTitles = [];
      for (const m of members) {
        harvest(m, URL_RE, urls);
        cleanTitles.push(m.title || m.name || '');
        // QQ ids appear either in a dedicated field or embedded in text
        for (const [k, v] of Object.entries(m)) {
          if (typeof v === 'string' && /qq/i.test(k)) {
            const mt = v.match(/\d{6,12}/g);
            if (mt) mt.forEach((x) => qqs.add(x));
          }
          if (typeof v === 'string' && /qq|群/i.test(v)) {
            const mt = v.match(/(?:群|qq)[^\d]{0,4}(\d{6,12})/gi);
            if (mt) mt.forEach((x) => { const d = x.match(/\d{6,12}/); if (d) qqs.add(d[0]); });
          }
        }
      }
      return {
        group_key: gk,
        member_count: members.length,
        members: members.map(pick),
        clean_titles: cleanTitles,
        download_urls: [...urls],
        qq_ids: [...qqs],
      };
    });

    // URL / QQ shared across groups of THIS finding (supporting context only)
    const sharedUrls = groups.length
      ? groups.map((g) => new Set(g.download_urls)).reduce((a, b) => new Set([...a].filter((x) => b.has(x))))
      : new Set();
    const sharedQqs = groups.length
      ? groups.map((g) => new Set(g.qq_ids)).reduce((a, b) => new Set([...a].filter((x) => b.has(x))))
      : new Set();

    return {
      author: f.author,
      group_keys: f.group_keys,
      group_count: f.group_count,
      record_count: f.record_count,
      shared_tokens: f.shared_tokens,
      detector_reasons: f.detector_reasons,
      shared_download_urls: [...sharedUrls],
      shared_qq_ids: [...sharedQqs],
      distinct_download_url_count: new Set(groups.flatMap((g) => g.download_urls)).size,
      groups,
    };
  });

  const result = {
    phase: '3G-F.2-B',
    artifact: 'undermerge_evidence_v2',
    purpose: 'Flattened member evidence for human adjudication of under-merge candidates.',
    source_cluster_artifact: 'build/audit/bilibili_cross_group_undermerge_v2.json',
    payload_records: data.length,
    findings_total: findings.length,
    disclaimer: 'EVIDENCE ONLY. No verdicts. URL/QQ are supporting context, never proof.',
    findings,
  };

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(result, null, 2), 'utf8');

  console.log('=== Phase 3G-F.2-B under-merge evidence extractor ===');
  console.log(`payload records : ${data.length}`);
  console.log(`findings        : ${findings.length}`);
  console.log(`group keys seen : ${byGroup.size}`);
  console.log(`written         : ${path.relative(REPO_ROOT, OUT)}`);
}

main();

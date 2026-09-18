/**
 * Phase 3G-F.1-B - Population-wide candidate DETECTOR (v2).
 *
 * WHY THIS EXISTS
 * ---------------
 * Phase 3G-F-A adjudicated 7 REAL false merges by scanning the 3G-F identity-run
 * groups. The scan was a *review-list generator* built around ONE signature:
 *
 *     anchor sits LATE in the key, and the token prefixes before it differ.
 *
 * That signature is structurally blind to a whole family of cases. Measured on
 * the 936-record payload:
 *
 *     multi-member identity groups : 129
 *     of which anchor_index == 0  :  56   <-- 43% INVISIBLE to the old scanner
 *
 * (`MIN_ANCHOR_INDEX = 1` in bilibili_grouping_slogan_anchor_scan.js, so the
 *  old detector can NEVER emit an all-zero-index group. Verified: zeros=0.)
 *
 * This detector widens the net to multiple independent CANDIDATE CLASSES and
 * deliberately over-reports. It is a REVIEW-LIST GENERATOR, never a verdict.
 *
 * SEPARATION OF CONCERNS (non-negotiable)
 * ---------------------------------------
 *   this file            -> candidate detection (heuristic, over-reports)
 *   pipeline/audit/bilibili_population_adjudication_v2.json -> human verdicts
 *
 * This script MUST NOT emit REAL_FALSE_MERGE. Only the adjudication ledger does,
 * and only from a hand-maintained table.
 *
 * URL / QQ ARE SUPPORTING EVIDENCE ONLY. Phase 3G-E proved that a shared
 * download URL can span different packs (one uploader had 28 *different* packs
 * behind one Quark link), so URL/QQ can never establish same-pack identity.
 * They are recorded here purely to help a human adjudicate.
 *
 * Usage: node pipeline/audit/bilibili_population_candidate_scan_v2.js
 * Output: build/audit/bilibili_population_candidates_v2.json
 */
const fs = require('fs');
const path = require('path');

global.window = {};
const REPO_ROOT = path.resolve(__dirname, '..', '..');
const newMod = require(path.join(REPO_ROOT, 'build', 'audit', 'bilibili_grouping_module.js'));
const packName = require(path.join(REPO_ROOT, 'build', 'audit', 'pack_name_module.js'));
const oldImpl = require(path.join(REPO_ROOT, 'pipeline', 'audit', 'fixtures', 'bili_grouping_legacy_impl.js'));
const OUT = path.join(REPO_ROOT, 'build', 'audit', 'bilibili_population_candidates_v2.json');
const BILI_DATA = path.join(REPO_ROOT, 'converted_output', 'data', 'bili_data.js');

// ---------------------------------------------------------------------------
// Thresholds. Kept in one place so the report can print old-vs-new explicitly.
// ---------------------------------------------------------------------------
const TH = {
  // v1 (for contrast / the report's "old vs new thresholds" table)
  v1_min_anchor_index: 1,
  v1_min_distinct_prefix: 2,
  // v2
  short_anchor_chars: 3,        // anchor with <= this many identity chars is thin
  low_discriminative_chars: 4,  // alias kept for reporting clarity
  large_group_size: 5,          // >= this many members gets a large_group reason
  min_group_size: 2,
};

// Generic component / mod / source-game words. A group whose anchor is built
// ONLY out of these is anchored on something that is not a pack identity.
const GENERIC_COMPONENT_WORDS = [
  '机械动力', '农夫乐事', '虚无世界', '泰坦生物', '匠魂', '等价交换', '暮色森林',
  '神秘时代', '应用能源', '植物魔法', '血魔法', '女仆', '宝可梦', '蔚蓝档案',
  '沉浸工程', '通用机械', '热力膨胀', '生活调味料', '地下城', '死亡细胞',
  '我的世界地下城', '整合包', '模组', '渲染', '光影', 'voxy', 'sodium', 'iris',
];

// Boilerplate that appears in MANY titles of one uploader regardless of pack.
const TITLE_BOILERPLATE = [
  '我的世界', '整合包', '发布', '更新', '版本', '正式版', '介绍', '演示', '宣传',
  '实况', '推荐', '免费', '最新', '全新', '重制', '优化', '内容', '服务端',
];

function loadBili() {
  const raw = fs.readFileSync(BILI_DATA, 'utf8');
  return JSON.parse(raw.slice(raw.indexOf('['), raw.lastIndexOf(']') + 1));
}

function normUrl(u) {
  if (!u) return '';
  if (typeof u === 'string') return u.trim();
  return String(u.url || u.link || '').trim();
}

function identityChars(s) {
  return String(s || '').replace(/[^A-Za-z0-9\u4e00-\u9fa5]/g, '').length;
}

/** index of the anchor token run inside the key, or -1 */
function anchorIndexOf(key, anchor) {
  const kt = key.split(' ').filter(Boolean);
  const at = anchor.split(' ').filter(Boolean);
  if (!at.length) return -1;
  for (let i = 0; i + at.length <= kt.length; i++) {
    let ok = true;
    for (let j = 0; j < at.length; j++) if (kt[i + j] !== at[j]) { ok = false; break; }
    if (ok) return i;
  }
  return -1;
}

/** bracket segments present in a raw title: 【...】 [....] 「....」 《....》 （....） */
function bracketSegments(title) {
  const segs = [];
  const re = /[【\[「《（(]([^】\]」》）)]*)[】\]」》）)]/g;
  let m;
  while ((m = re.exec(String(title || '')))) {
    const body = m[1].trim();
    if (body) segs.push(body);
  }
  return segs;
}

/** tokens shared by EVERY member's clean key (contiguous-or-not, as a set) */
function commonTokens(keys) {
  if (!keys.length) return [];
  let sets = keys.map((k) => new Set(k.split(' ').filter(Boolean)));
  const first = [...sets[0]];
  return first.filter((t) => sets.every((s) => s.has(t)));
}

function main() {
  const data = loadBili();
  const dec = {};
  for (const [b, d] of newMod.groupBilibiliPacks(data)) dec[b] = d;
  const oldMap = {};
  for (const g of oldImpl.groupPacks(data)) for (const it of g.items) oldMap[it.bvid] = g.key;

  const byBvid = {};
  for (const p of data) byBvid[p.bvid] = p;

  const groups = new Map();
  for (const p of data) {
    const k = dec[p.bvid].groupKey;
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k).push(p);
  }

  const candidates = [];
  // Track which detection classes fire, for the coverage report.
  const classCounts = {};

  for (const [key, members] of groups) {
    if (members.length < TH.min_group_size) continue;

    const anchor = dec[members[0].bvid].identityKey;
    const reason = dec[members[0].bvid].groupingReason;
    const isIdentityRun = !!anchor && reason === 'identity_run';

    const rows = members.map((m) => {
      const k = packName.cleanPackKey(m.title);
      const idx = anchor ? anchorIndexOf(k, anchor) : -1;
      const kt = k.split(' ').filter(Boolean);
      return {
        m,
        key: k,
        idx,
        prefix: idx > 0 ? kt.slice(0, idx).join(' ') : '',
        suffix: idx >= 0 ? kt.slice(idx + (anchor ? anchor.split(' ').filter(Boolean).length : 0)).join(' ') : '',
      };
    });

    const idxs = rows.map((r) => r.idx);
    const prefixSet = [...new Set(rows.map((r) => r.prefix).filter((p) => p !== ''))];
    const anchorChars = identityChars(anchor);
    const anchorLower = String(anchor || '').toLowerCase();

    const detectors = [];
    const addReason = (name) => {
      if (!detectors.includes(name)) detectors.push(name);
      classCounts[name] = (classCounts[name] || 0) + 1;
    };

    // --- class 1: anchor_index == 0 for ALL members (v1 blind spot) ----------
    if (isIdentityRun && idxs.length && idxs.every((i) => i === 0)) {
      addReason('anchor_index_zero');
    }
    // --- class 2: anchor_index == 1 for all members -------------------------
    if (isIdentityRun && idxs.length && idxs.every((i) => i === 1)) {
      addReason('anchor_index_one');
    }
    // --- class 3: thin anchor ----------------------------------------------
    if (isIdentityRun && anchorChars > 0 && anchorChars <= TH.short_anchor_chars) {
      addReason('short_anchor');
    }
    // --- class 4: anchor is made ONLY of generic component/mod words --------
    if (isIdentityRun) {
      const at = String(anchor).split(' ').filter(Boolean);
      const onlyGeneric = at.length > 0 && at.every((t) =>
        GENERIC_COMPONENT_WORDS.some((g) => t.toLowerCase() === g.toLowerCase()));
      if (onlyGeneric) addReason('generic_component_anchor');
    }
    // --- class 5: bracket series tag ---------------------------------------
    // The anchor (or a large share of members' titles) lives inside a bracket
    // segment. 3G-F-A's tibsalta::难度驱动 regression had exactly this shape:
    // the real pack name sat OUTSIDE the bracket, the series tag INSIDE it.
    if (isIdentityRun && anchor) {
      const lower = anchorLower;
      const inBracket = members.filter((m) =>
        bracketSegments(m.title).some((seg) => seg.toLowerCase().includes(lower)
          || lower.includes(seg.toLowerCase()) && seg.length >= 3));
      if (inBracket.length >= 2 && inBracket.length >= members.length - 1) {
        addReason('bracket_series_tag');
      }
    }
    // --- class 6: low discriminative key (shared tokens are all boilerplate) -
    if (isIdentityRun || reason === 'exact_key' || reason === 'substring_key') {
      const shared = commonTokens(rows.map((r) => r.key));
      if (shared.length > 0 && shared.every((t) => TITLE_BOILERPLATE.some((b) => t.includes(b)))) {
        addReason('low_discriminative_key');
      }
    }
    // --- class 7: large group (bigger blast radius if wrong) ---------------
    if (isIdentityRun && members.length >= TH.large_group_size) {
      addReason('large_group');
    }
    // --- class 8: mixed stable-name signatures -----------------------------
    // Members disagree on where the anchor sits (some leading, some trailing),
    // or the anchor sits late while prefixes are all distinct -> the classic
    // slogan/anchor signature the v1 scanner targeted.
    if (isIdentityRun) {
      const distinct = new Set(idxs);
      if (distinct.size >= 2 && Math.min(...idxs) === 0 && Math.max(...idxs) >= 1) {
        addReason('mixed_anchor_position');
      }
      const allLate = idxs.every((i) => i >= TH.v1_min_anchor_index);
      if (allLate && prefixSet.length >= TH.v1_min_distinct_prefix) {
        addReason('late_anchor_distinct_prefix');
      }
    }
    // --- class 9: repeated uploader boilerplate across members -------------
    if (isIdentityRun) {
      const boiler = TITLE_BOILERPLATE.filter((b) => rows.every((r) => String(r.m.title).includes(b)));
      if (boiler.length >= 3) addReason('repeated_title_boilerplate');
    }

    if (!detectors.length) continue;

    const urlsPer = members.map((m) => [...new Set((m.download_links || []).map(normUrl).filter(Boolean))]);
    const qqsPer = members.map((m) => String(m.qq_group || '').trim());
    const sharedUrls = urlsPer.length
      ? urlsPer[0].filter((u) => urlsPer.slice(1).every((a) => a.includes(u))) : [];
    const distinctUrls = [...new Set(urlsPer.flat())];
    const sharedQqs = qqsPer.length
      ? qqsPer.filter((q) => q && qqsPer.slice(1).every((o) => o === q)) : [];

    const oldKeys = new Set(members.map((m) => oldMap[m.bvid]));

    candidates.push({
      group_key: key,
      author: members[0].author || 'unknown',
      anchor,
      anchor_index: idxs,
      anchor_frequency: members.length,
      anchor_identity_chars: anchorChars,
      key_length: rows.map((r) => r.key.length),
      grouping_reason: reason,
      size: members.length,
      detector_reasons: detectors,
      bracket_segments: [...new Set(members.flatMap((m) => bracketSegments(m.title)))],
      download_identities: {
        shared: sharedUrls,
        distinct_count: distinctUrls.length,
        all: distinctUrls,
      },
      qq_identities: {
        shared: sharedQqs,
        all: [...new Set(qqsPer.filter(Boolean))],
      },
      newly_merged: oldKeys.size > 1,
      old_distinct_keys: oldKeys.size,
      members: rows.map((r) => ({
        bvid: r.m.bvid,
        title: r.m.title,
        clean_key: r.key,
        anchor_index: r.idx,
        prefix: r.prefix,
        suffix: r.suffix,
        residue: dec[r.m.bvid].episodeResidue,
      })),
      // NOTE: no verdict field. Adjudication lives in the ledger, not here.
    });
  }

  candidates.sort((a, b) => (b.detector_reasons.length - a.detector_reasons.length)
    || (b.size - a.size) || (a.group_key < b.group_key ? -1 : 1));

  const result = {
    phase: '3G-F.1-B',
    // SOURCE_DATE_EPOCH makes the artifact byte-reproducible.
    generated_at: new Date(
      (process.env.SOURCE_DATE_EPOCH ? Number(process.env.SOURCE_DATE_EPOCH) * 1000 : Date.now()),
    ).toISOString(),
    artifact: 'bilibili_population_candidates_v2',
    payload_records: data.length,
    total_groups: groups.size,
    thresholds: {
      v1: { min_anchor_index: TH.v1_min_anchor_index, min_distinct_prefix: TH.v1_min_distinct_prefix },
      v2: {
        short_anchor_chars: TH.short_anchor_chars,
        large_group_size: TH.large_group_size,
        min_group_size: TH.min_group_size,
        detector_classes: 'see classCounts',
      },
    },
    detector_class_counts: classCounts,
    candidates_total: candidates.length,
    candidates_newly_merged: candidates.filter((c) => c.newly_merged).length,
    candidates,
    disclaimer: 'REVIEW-LIST GENERATOR. Detector reasons are NOT verdicts. '
      + 'URL/QQ are supporting evidence only and never establish same-pack identity.',
  };

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(result, null, 2), 'utf8');

  console.log('=== Phase 3G-F.1-B population candidate scan v2 ===');
  console.log(`groups total    : ${groups.size}`);
  console.log(`candidates      : ${candidates.length} (newly merged by 3G-F: ${result.candidates_newly_merged})`);
  console.log('-- detector class counts --');
  for (const [k, v] of Object.entries(classCounts).sort((a, b) => b[1] - a[1])) {
    console.log(`   ${String(v).padStart(4)}  ${k}`);
  }
  console.log(`written: ${path.relative(REPO_ROOT, OUT)}`);
  return 0;
}

process.exit(main());

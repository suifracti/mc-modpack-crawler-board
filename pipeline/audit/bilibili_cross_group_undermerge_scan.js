/**
 * Phase 3G-F.1-B - Cross-group UNDER-MERGE scanner.
 *
 * The population candidate scan looks INSIDE one group for evidence the members
 * are actually different packs (false merge). This scanner looks ACROSS groups
 * of the same uploader for evidence that two or more groups are actually ONE
 * pack that the algorithm failed to unify (false split / under-merge).
 *
 * The canonical known case (Phase 3G-F-A, hand-verified against bili_data):
 *
 *   uploader 墨言eclipse, pack 涅槃
 *     7 records, 5 distinct group keys
 *     -> the algorithm SPLIT one logical pack into five buckets
 *
 * WHY THE CRITERIA ARE STRICT
 * ---------------------------
 * A naive "any shared token" rule flags 410 pairs on this payload - useless.
 * The discriminator is a RARE, LONG, identity-bearing token (e.g. 涅槃) that
 * appears in a small number of groups of one uploader. Generic words, version
 * strings and boilerplate are excluded; a token must also be rare WITHIN the
 * uploader (appearing in <= 6 groups) to count, otherwise it is a house style.
 *
 * Clusters (connected components over the pair graph) are emitted so a pack
 * split five ways surfaces as ONE finding, not ten pairwise rows.
 *
 * SIGNALS (all weak indicators; adjudication still required)
 *   - stable_pack_name_overlap : a rare long token shared by different groups
 *   - version_continuity       : residue version ranges overlap / are adjacent
 *   - unique_series_identity   : the shared token is long (>=4 chars)
 *
 * This is a REVIEW-LIST GENERATOR. It must NOT assert UNDER_MERGE; the
 * adjudication ledger does that.
 *
 * Usage: node pipeline/audit/bilibili_cross_group_undermerge_scan.js
 * Output: build/audit/bilibili_cross_group_undermerge_v2.json
 */
const fs = require('fs');
const path = require('path');

global.window = {};
const REPO_ROOT = path.resolve(__dirname, '..', '..');
const newMod = require(path.join(REPO_ROOT, 'build', 'audit', 'bilibili_grouping_module.js'));
const packName = require(path.join(REPO_ROOT, 'build', 'audit', 'pack_name_module.js'));
const OUT = path.join(REPO_ROOT, 'build', 'audit', 'bilibili_cross_group_undermerge_v2.json');
const BILI_DATA = path.join(REPO_ROOT, 'converted_output', 'data', 'bili_data.js');

// Tokens that are version/changelog/boilerplate and therefore useless as proof
// that two groups are the same pack.
const NON_IDENTITY_TOKENS = new Set([
  '', 'v', '版', '版本', '更新', '发布', '整合包', '模组', '我的世界', 'minecraft',
  'mc', '正式', '正式版', '免费', '最新', '介绍', '演示', '宣传', '实况', '推荐',
  '内容', '优化', '支持', '适配', '全新', '重制', '测试版', '大型', '中型', '小型',
  '生存', '冒险', '科技', '魔法', '战斗', '剧情', '恐怖', '休闲', '硬核', '视频',
  '预', '前预热', '去同质化',
]);

const TH = {
  // A shared ROOT token must be at least this long. 2 chars is enough for CJK
  // pack names (涅槃 is 2 chars and is a real pack name), so the length filter
  // is paired with a RARITY filter - a 2-char token only counts when it is
  // shared by a small number of groups, which is what makes it discriminative.
  min_shared_token_chars: 2,
  max_groups_per_token: 4,       // above this a token is house-style, not a pack name
  long_token_chars: 4,           // "unique series identity" confidence floor
};

function loadBili() {
  const raw = fs.readFileSync(BILI_DATA, 'utf8');
  return JSON.parse(raw.slice(raw.indexOf('['), raw.lastIndexOf(']') + 1));
}

/** alphanumeric/cjk length of a token, digits stripped */
function nameChars(t) {
  return String(t || '').replace(/\d+/g, '').replace(/[^A-Za-z0-9\u4e00-\u9fa5]/g, '').length;
}

/**
 * Strip a trailing ASCII/loader suffix from a CJK-bearing token so that
 * "涅槃v" matches "涅槃". Mirrors normalizeTokenForMatch in the domain module:
 * a Chinese name written with a channel/version suffix is still the same name.
 */
function normalizeToken(t) {
  const s = String(t || '');
  if (!/[\u4e00-\u9fa5]/.test(s)) return s.toLowerCase();
  const stripped = s.replace(/[A-Za-z0-9]+/g, '');
  return (stripped || s).toLowerCase();
}

/** version numbers found in a string, e.g. "v0.2" -> [0,2] ; "1.0" -> [1,0] */
function versionsIn(s) {
  const out = [];
  const re = /v?(\d+(?:\.\d+){0,3})/gi;
  let m;
  while ((m = re.exec(String(s || '')))) {
    const parts = m[1].split('.').map(Number);
    if (parts.length >= 2) out.push(parts);
  }
  return out;
}

function versionContinuous(a, b) {
  if (!a.length || !b.length) return false;
  const flat = (v) => v[0] + (v[1] || 0) / 100;
  const amin = Math.min(...a.map(flat));
  const amax = Math.max(...a.map(flat));
  const bmin = Math.min(...b.map(flat));
  const bmax = Math.max(...b.map(flat));
  const gap = Math.min(Math.abs(bmin - amax), Math.abs(amin - bmax));
  return gap <= 0.5;
}

function main() {
  const data = loadBili();
  const dec = {};
  for (const [b, d] of newMod.groupBilibiliPacks(data)) dec[b] = d;

  const byAuthor = new Map();
  for (const p of data) {
    const a = String(p.author || 'unknown').trim().toLowerCase();
    if (!byAuthor.has(a)) byAuthor.set(a, []);
    byAuthor.get(a).push(p);
  }

  const findings = [];
  const allPairs = [];

  for (const [authorKey, recs] of byAuthor) {
    const groups = new Map();
    for (const p of recs) {
      const k = dec[p.bvid].groupKey;
      if (!groups.has(k)) groups.set(k, []);
      groups.get(k).push(p);
    }
    if (groups.size < 2) continue;
    const keys = [...groups.keys()];

    // Strong (rare-eligible) tokens per group. Tokens are normalised (trailing
    // ASCII suffix stripped) so "涅槃v" and "涅槃" collapse to one root.
    const groupStrong = new Map();
    for (const [k, members] of groups) {
      const s = new Set();
      for (const m of members) {
        for (const t of packName.cleanPackKey(m.title).split(' ').filter(Boolean)) {
          const lower = t.toLowerCase();
          if (NON_IDENTITY_TOKENS.has(lower)) continue;
          const norm = normalizeToken(t);
          if (nameChars(norm) < TH.min_shared_token_chars) continue;
          s.add(norm);
        }
      }
      groupStrong.set(k, s);
    }

    const tokenToGroups = new Map();
    for (const [k, s] of groupStrong) {
      for (const t of s) {
        if (!tokenToGroups.has(t)) tokenToGroups.set(t, new Set());
        tokenToGroups.get(t).add(k);
      }
    }

    /**
     * Rare roots shared by two groups.
     *
     * A root is a NORMALISED WHOLE TOKEN (trailing ASCII suffix stripped, so
     * "涅槃v" -> "涅槃"), which is how the domain module itself compares keys.
     *
     * Two rejection lessons are baked in here, both learned from real runs:
     *   1. FREE-FORM INFIX matching is unusable. Allowing any 2-char fragment to
     *      match anywhere linked 8 unrelated 墨言eclipse groups into one blob on
     *      fragments like 大型 / 之旅 / 宣传片.
     *   2. Even with a >=3-char floor, arbitrary infix matches still bridge
     *      unrelated groups (颠覆性的 vs 拒绝同质 share a fragment).
     *
     * So a short root is admitted ONLY as an EDGE-ANCHORED run: the root must be
     * a PREFIX or SUFFIX of the longer token. Chinese pack titles lead or trail
     * with the pack name, so 涅槃 is found at the end of "未尽之路涅槃" while
     * 大型 / 之旅 cannot bridge anything (they are interior fragments).
     * Roots of >=3 name chars matching anywhere are kept, since a >=3-char
     * Chinese run is already specific.
     */
    const EDGE_MIN_CHARS = 3;
    function sharedRoots(tokensA, tokensB) {
      const out = new Set();
      for (const a of tokensA) {
        for (const b of tokensB) {
          if (a === b) { out.add(a); continue; }
          const [short, long] = a.length <= b.length ? [a, b] : [b, a];
          if (nameChars(short) < 2) continue;
          const isEdge = long.startsWith(short) || long.endsWith(short);
          if (isEdge) { out.add(short); continue; }
          // interior match only when the shared run is itself substantial
          if (nameChars(short) >= EDGE_MIN_CHARS && long.includes(short)) out.add(short);
        }
      }
      return [...out];
    }

    // adjacent pairs sharing a RARE root
    const pairList = [];
    for (let i = 0; i < keys.length; i++) {
      for (let j = i + 1; j < keys.length; j++) {
        const kA = keys[i];
        const kB = keys[j];
        const sA = groupStrong.get(kA);
        const sB = groupStrong.get(kB);
        const shared = sharedRoots(sA, sB);
        // Rarity gate. For a root found by EXACT (normalised) equality we use
        // the precomputed index; for one only reachable as a substring we
        // re-count how many of this uploader's groups contain it at all, so a
        // short fragment used across many groups is rejected.
        const rareShared = shared.filter((t) => {
          const exact = tokenToGroups.get(t);
          if (exact) return exact.size <= TH.max_groups_per_token;
          let n = 0;
          for (const s of groupStrong.values()) {
            for (const tok of s) if (tok.includes(t)) { n++; break; }
          }
          return n <= TH.max_groups_per_token;
        });
        if (!rareShared.length) continue;

        // COHESION GATE.
        // A root that appears in only ONE member of a 3-member group is an
        // incidental subtitle, not the pack name. Without this, 未尽之路 (which
        // occurs in a single 涅槃 video as a subtitle) bridged the 涅槃 cluster
        // to an unrelated group. Require the root to be present in at least
        // half the members of BOTH groups (and always in a singleton group).
        //
        // Coverage is measured with the SAME normalisation used to build
        // groupStrong, so the gate can never disagree with the pair vote.
        const memberCovers = (root, members) => members.filter((m) =>
          packName.cleanPackKey(m.title).split(' ').filter(Boolean)
            .some((t) => {
              const n = normalizeToken(t);
              return n === root || n.includes(root) || root.includes(n) && n.length >= 2;
            })
        ).length;
        const cohesive = rareShared.filter((t) => {
          const membersA = groups.get(kA);
          const membersB = groups.get(kB);
          const needA = Math.max(1, Math.ceil(membersA.length / 2));
          const needB = Math.max(1, Math.ceil(membersB.length / 2));
          return memberCovers(t, membersA) >= needA && memberCovers(t, membersB) >= needB;
        });
        if (!cohesive.length) continue;
        const strongRoots = cohesive;

        const verA = groups.get(kA).flatMap((m) => versionsIn(m.title));
        const verB = groups.get(kB).flatMap((m) => versionsIn(m.title));
        const cont = versionContinuous(verA, verB);
        const long = strongRoots.filter((t) => nameChars(t) >= TH.long_token_chars);

        // Confidence floor.
        // A root qualifies when it is LONG (>=4 name chars), OR it is an EXACT
        // whole-token match, OR it is corroborated by version continuity.
        //
        // The exact-token case is essential and was initially missing: the real
        // pack name 涅槃 is only 2 chars ("涅槃v" normalises to "涅槃"), and the
        // record "[MC整合包发布:涅槃] 无神明渡我 我亦是神明" carries no version
        // number at all. Requiring length-or-version dropped that pair and lost
        // one of the five 涅槃 group keys the task explicitly requires. A rare
        // WHOLE-TOKEN match on a short CJK name is strong evidence by itself.
        const exactRoots = strongRoots.filter((t) => {
          const gs = tokenToGroups.get(t);
          if (!gs) return false;
          // token must be present verbatim in both groups' strong-token sets
          return sA.has(t) && sB.has(t);
        });
        if (!long.length && !exactRoots.length && !cont) continue;

        const reasons = ['stable_pack_name_overlap'];
        if (cont) reasons.push('version_continuity');
        if (long.length || exactRoots.length) reasons.push('unique_series_identity');

        const pair = {
          author: groups.get(kA)[0].author || 'unknown',
          group_keys: [kA, kB],
          shared_tokens: strongRoots,
          long_shared_tokens: long,
          detector_reasons: reasons,
          sizes: [groups.get(kA).length, groups.get(kB).length],
        };
        pairList.push(pair);
        allPairs.push(pair);
      }
    }

    // connected components over pairList
    const parent = {};
    const find = (x) => { while (parent[x] !== x) { parent[x] = parent[parent[x]]; x = parent[x]; } return x; };
    const union = (a, b) => { const ra = find(a), rb = find(b); if (ra !== rb) parent[ra] = rb; };
    for (const k of keys) parent[k] = k;
    for (const p of pairList) union(p.group_keys[0], p.group_keys[1]);

    const comps = new Map();
    for (const p of pairList) {
      const r = find(p.group_keys[0]);
      if (!comps.has(r)) comps.set(r, { keys: new Set(), pairs: [] });
      const c = comps.get(r);
      c.keys.add(p.group_keys[0]);
      c.keys.add(p.group_keys[1]);
      c.pairs.push(p);
    }

    for (const [, c] of comps) {
      const clusterKeys = [...c.keys];
      const memberCount = clusterKeys.reduce((n, k) => n + groups.get(k).length, 0);
      const allTokens = [...new Set(c.pairs.flatMap((p) => p.shared_tokens.length ? p.shared_tokens : []))];
      findings.push({
        author: groups.get(clusterKeys[0])[0].author || 'unknown',
        group_keys: clusterKeys,
        group_count: clusterKeys.length,
        record_count: memberCount,
        shared_tokens: allTokens,
        detector_reasons: [...new Set(c.pairs.flatMap((p) => p.detector_reasons))],
        pairs: c.pairs.length,
        evidence: clusterKeys.map((k) => ({
          group_key: k,
          anchor: dec[groups.get(k)[0].bvid].identityKey,
          members: groups.get(k).map((m) => ({ bvid: m.bvid, title: m.title })),
        })),
      });
    }
  }

  findings.sort((a, b) => (b.record_count - a.record_count) || (b.group_count - a.group_count));

  const out = {
    phase: '3G-F.1-B',
    generated_at: new Date().toISOString(),
    artifact: 'bilibili_cross_group_undermerge_v2',
    payload_records: data.length,
    thresholds: TH,
    pairs_flagged: allPairs.length,
    clusters_flagged: findings.length,
    pairs: allPairs,
    findings,
    disclaimer: 'REVIEW-LIST GENERATOR for under-merge (false split). Not a verdict. '
      + 'URL/QQ deliberately unused as proof.',
  };

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(out, null, 2), 'utf8');

  console.log('=== Phase 3G-F.1-B cross-group under-merge scan ===');
  console.log(`candidate pairs : ${allPairs.length}`);
  console.log(`clusters        : ${findings.length}`);
  const byReason = {};
  for (const f of findings) for (const r of f.detector_reasons) byReason[r] = (byReason[r] || 0) + 1;
  for (const [k, v] of Object.entries(byReason).sort((a, b) => b[1] - a[1])) console.log(`   ${String(v).padStart(4)}  ${k}`);
  const nie = findings.filter((f) => f.group_keys.some((k) => k.includes('涅槃')));
  console.log(`涅槃 clusters    : ${nie.length}`);
  for (const f of nie) console.log(`   groups=${f.group_count} records=${f.record_count} tokens=[${f.shared_tokens.join(',')}]`);
  console.log(`written: ${path.relative(REPO_ROOT, OUT)}`);
  return 0;
}

process.exit(main());

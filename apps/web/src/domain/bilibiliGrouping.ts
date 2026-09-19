/**
 * Bilibili grouping — single source of truth (Phase 3G-F).
 *
 * Replaces the legacy `groupPacks` key assignment that lived inline in
 * `dashboard.legacy.js` and duplicated `BILI_GENERIC_PACK_KEYS` locally.
 *
 * Problem being fixed (Phase 3G-E evidence): the previous rule only merged when
 * two same-author keys were EXACTLY equal or one was a >=4-char substring of the
 * other. Changelog text survives `cleanPackKey`, so sibling episodes of the same
 * pack produced keys that were neither equal nor substrings -> systematic false
 * split (Merge Recall 0.1250 over an independent-evidence corpus).
 *
 * Two-level model:
 *   identityKey    — a stable, discriminative token run shared by the episodes
 *   episodeResidue — whatever is left (version/changelog/update wording)
 *
 * Two titles are the same series because they share a contiguous identity run
 * whose identity-bearing characters are long enough, and that run is NOT built
 * out of channel jargon / changelog wording.
 *
 * Safety invariants (never relaxed):
 *   * author-scoped — cross-uploader merging is structurally impossible
 *   * generic/short key guard unchanged (preserves the historical 黑金 fix)
 *   * download URL / QQ group are NOT used here at all
 */

import { cleanPackKey, BILI_GENERIC_PACK_KEYS } from './packName';

/**
 * Tokens that may appear inside a title but must never by themselves constitute
 * a pack identity: channel/platform jargon and update/changelog wording.
 *
 * These are NOT deleted from the key (that would damage recall differently);
 * they are simply not eligible to *anchor* an identity.
 */
export const BILI_IDENTITY_NOISE_TOKENS = new Set<string>([
  // channel / porting / launcher jargon
  '手机移植版', '移植版', '移植', '启动器', 'fcl启动器移植', 'fcl启动器制作',
  '一键自动导入', '一键自动安装', 'fcl', 'pcl', '手机版', '电脑版',
  // update / changelog wording
  '版本', '正式', '更新', '发布', '前瞻', '日志', '预告', '宣传片', '介绍',
  '介绍视频', '演示', '实况', '推荐', '内容', '优化', '支持', '适配', '添加',
  '加入', '新增', '测试版', '正式版', '最新', '最新版', '免费', '全新', '重置',
  '重做', '改进', '修复', '调整', '平衡', '改动', '更新内容', '小版本', '大版本',
  // generic pack wording
  '整合包', '模组包', '魔改包', '懒人包', '包', '模组', '整合',
  // genre / scale descriptors (same class as BILI_GENRE_BUZZWORDS: a genre word
  // is never a pack identity). Without these, "大型末世" anchors 潜行者 to 生还者.
  '末世', '末日', '大型', '中型', '小型', '史诗', '高版本', '低版本', '高配',
  '低配', '中配', '轻量', '休闲', '硬核', '剧情', '恐怖', '沉浸', '类魂',
  '真实', '原版', '魔改', '养老', '探索', '地牢', '战斗', '生存', '冒险',
  '科技', '魔法', '空岛', '枪械', '拔刀剑', '工业', '建造', '现代战争', 'rpg',
  '系列', '合集',
  // Widely-used MOD names that channels use as genre tags. A mod name alone is not
  // a pack identity: it is what makes 命运齿轮 and 月亮工厂 collapse into one
  // "机械动力" card. Longer runs that merely CONTAIN these still work, because
  // noise is stripped as a substring (e.g. "机械动力 星辰" -> "星辰" remains).
  '机械动力', '农夫乐事', '虚无世界', '泰坦生物', '匠魂', '等价交换',
  '暮色森林', '神秘时代', '应用能源', '植物魔法', '血魔法', '女仆',
  '宝可梦', '蔚蓝档案', '沉浸工程', '通用机械', '热力膨胀', '生活调味料',
  // source-game references (《我的世界：地下城》/ 死亡细胞 ...) - a game title a
  // pack borrows content from is not that pack's own name. Without this, 幻想的地下城
  // and 史诗的地下城 (different packs, different 百度 links) merge on "地下城".
  '地下城', '死亡细胞', '我的世界地下城',
  // filler
  '与', '在', '的', '和', '版', '第', '期', 'v', 'amp', 'quot', 'gt', 'lt',
  'mod', 'minecraft', '我的世界',
]);

/** Minimum identity-bearing characters a shared run must carry. */
export const BILI_MIN_IDENTITY_CHARS = 3;

export interface BilibiliGroupingInput {
  bvid: string;
  title: string;
  author?: string | null;
}

export interface BilibiliGroupingDecision {
  /** Final grouping key used by the aggregator. */
  groupKey: string;
  /** Stable identity run, or '' when the record could not be grouped. */
  identityKey: string;
  /** Remaining episode/update wording after removing the identity run. */
  episodeResidue: string;
  /** Debug/test explainability: why this record ended up where it did. */
  groupingReason:
    | 'generic_guard'
    | 'identity_run'
    | 'exact_key'
    | 'substring_key'
    | 'singleton';
}

function tokensOf(key: string): string[] {
  return key ? key.split(' ').filter(Boolean) : [];
}

/**
 * Identity-bearing characters inside a single token.
 *
 * Descriptors concatenate in Chinese titles (`大型` + `末世` -> one token
 * "大型末世"), so a plain Set lookup is not enough: noise words are removed as
 * substrings and whatever remains is the identity-bearing part. A token made
 * entirely of noise/descriptors therefore contributes 0 and can never anchor an
 * identity, while a real name that merely contains a noise word (e.g.
 * "齿轮与腐肉" -> "齿轮腐肉") still contributes.
 */
export function identityCharsOfToken(token: string): number {
  if (!token) return 0;
  let s = token;
  for (const n of BILI_IDENTITY_NOISE_TOKENS) {
    if (n && s.includes(n)) s = s.split(n).join('');
  }
  s = s.replace(/\d+/g, '');
  return s.length;
}

export function isIdentityEligibleToken(token: string): boolean {
  return identityCharsOfToken(token) >= 2;
}

/** Identity-bearing character count of a token run. */
function identityChars(tokens: string[]): number {
  let n = 0;
  for (const t of tokens) n += identityCharsOfToken(t);
  return n;
}

function qualifiesAsIdentity(tokens: string[]): boolean {
  return identityChars(tokens) >= BILI_MIN_IDENTITY_CHARS
    && tokens.some(isIdentityEligibleToken);
}

/** author scope key, identical to the legacy normalisation. */
export function authorScope(author?: string | null): string {
  return (author || 'unknown').trim().toLowerCase();
}

/**
 * Normalise a token for MATCHING only: drop ASCII letters/digits from a token
 * that also contains CJK, so the same name written with a channel/loader suffix
 * still matches ("虚饰作品v" == "虚饰作品", "命运齿轮fom" == "命运齿轮",
 * "云游四海v" == "云游四海"). Tokens with no CJK (e.g. "mon", "soa3") are kept
 * as-is. A token that becomes empty falls back to its original form.
 */
export function normalizeTokenForMatch(token: string): string {
  if (!token) return token;
  if (!/[\u4e00-\u9fa5]/.test(token)) return token;
  const stripped = token.replace(/[A-Za-z0-9]+/g, '');
  return stripped.length ? stripped : token;
}

interface Entry {
  bvid: string;
  key: string;
  tokens: string[];
  /** tokens normalised for matching (suffix-stripped) */
  matchTokens: string[];
  authorKey: string;
  guarded: boolean;
  /** assigned identity run (joined), '' if none */
  identity: string;
  reason: BilibiliGroupingDecision['groupingReason'];
}

/**
 * Longest contiguous common token run between two token arrays.
 * Returns the run with the most identity-bearing characters; ties resolve to the
 * earliest occurrence in `a`, then lexicographically (fully deterministic).
 */
function bestCommonRun(a: string[], b: string[]): { run: string[]; chars: number } {
  let best: string[] = [];
  let bestChars = -1;
  for (let i = 0; i < a.length; i++) {
    for (let j = 0; j < b.length; j++) {
      let k = 0;
      while (i + k < a.length && j + k < b.length && a[i + k] === b[j + k]) k++;
      if (k === 0) continue;
      const run = a.slice(i, i + k);
      const chars = identityChars(run);
      if (chars > bestChars) {
        bestChars = chars;
        best = run;
      }
    }
  }
  return { run: best, chars: bestChars };
}

/**
 * Pure grouping decision for a batch of Bilibili records.
 * Returns a bvid -> decision map. Author-scoped; never merges across uploaders.
 */
export function groupBilibiliPacks(
  records: BilibiliGroupingInput[]
): Map<string, BilibiliGroupingDecision> {
  const entries: Entry[] = records.map((r) => {
    const key = cleanPackKey(r.title);
    const guarded = !key || key.length <= 3 || BILI_GENERIC_PACK_KEYS.has(key);
    return {
      bvid: r.bvid,
      key,
      tokens: tokensOf(key),
      matchTokens: tokensOf(key).map(normalizeTokenForMatch),
      authorKey: authorScope(r.author),
      guarded,
      identity: '',
      reason: guarded ? 'generic_guard' : 'singleton',
    };
  });

  const byAuthor = new Map<string, Entry[]>();
  for (const e of entries) {
    if (e.guarded) continue;
    const list = byAuthor.get(e.authorKey);
    if (list) list.push(e);
    else byAuthor.set(e.authorKey, [e]);
  }

  // ---- identity run mining, strictly inside one author scope -----------------
  for (const list of byAuthor.values()) {
    // anchor -> member bvids
    const anchorMembers = new Map<string, Set<string>>();

    for (let i = 0; i < list.length; i++) {
      for (let j = i + 1; j < list.length; j++) {
        const a = list[i];
        const b = list[j];
        const { run, chars } = bestCommonRun(a.matchTokens, b.matchTokens);
        if (chars < BILI_MIN_IDENTITY_CHARS) continue;
        if (!qualifiesAsIdentity(run)) continue;
        const anchor = run.join(' ');
        let set = anchorMembers.get(anchor);
        if (!set) { set = new Set<string>(); anchorMembers.set(anchor, set); }
        set.add(a.bvid);
        set.add(b.bvid);
      }
    }

    // DIRECT assignment, deliberately NOT transitive union-find.
    //
    // Union-find chains different packs together: pack P1 shares run R1 with P2,
    // P2 shares run R2 with P3 -> one giant component. Observed in production data
    // (e.g. a 14-member group mixing 弑神之路 / 神器收集计划 / 无尽幸运方块大陆,
    // and a 6-member group mixing 命运齿轮 / 月亮工厂). Precision is the priority,
    // so every record picks the single most specific anchor it contains, and only
    // records that agree on that anchor group together.
    // Ordering: the anchor that unites the MOST episodes wins; specificity is the
    // tie-break. The opposite order lets a long changelog run
    // ("维度 弹幕 超多饰品 深度") peel two episodes away from the six that share
    // the real pack name ("虚饰作品").
    //
    // Cohesion-first used to be unsafe because a mod-name run ("机械动力") could
    // swallow two different packs; that is now handled upstream by the mod-name
    // noise list, so this ordering no longer trades precision for recall.
    const anchors = [...anchorMembers.entries()]
      .filter(([, members]) => members.size >= 2)
      .map(([anchor, members]) => ({
        anchor,
        members,
        chars: identityChars(anchor.split(' ')),
      }))
      .sort((x, y) =>
        (y.members.size - x.members.size)
        || (y.chars - x.chars)
        || (x.anchor < y.anchor ? -1 : x.anchor > y.anchor ? 1 : 0));

    // Assign every record that CONTAINS the anchor as a contiguous token run.
    // Relying only on the mined member set is inconsistent: a pair whose best
    // common run happens to be a different (longer) run never registers the
    // broader anchor, so two episodes end up elsewhere while four use the real
    // name. Containment makes the assignment a pure function of (anchor, record).
    const containsRun = (tokens: string[], anchor: string[]): boolean => {
      if (anchor.length === 0 || anchor.length > tokens.length) return false;
      for (let i = 0; i + anchor.length <= tokens.length; i++) {
        let ok = true;
        for (let j = 0; j < anchor.length; j++) {
          if (tokens[i + j] !== anchor[j]) { ok = false; break; }
        }
        if (ok) return true;
      }
      return false;
    };

    for (const a of anchors) {
      const anchorTokens = a.anchor.split(' ');
      for (const e of list) {
        if (e.identity) continue;
        if (containsRun(e.matchTokens, anchorTokens)) {
          e.identity = a.anchor;
          e.reason = 'identity_run';
        }
      }
    }
  }

  // ---- fallback: legacy exact-key / substring behaviour ---------------------
  // Preserves merges the identity miner does not cover (e.g. a key that is a
  // >=4-char substring of a sibling's key) so nothing that already worked breaks.
  const fallbackBuckets = new Map<string, Entry[]>();
  for (const e of entries) {
    if (e.guarded || e.identity) continue;
    const b = fallbackBuckets.get(e.authorKey);
    if (b) b.push(e);
    else fallbackBuckets.set(e.authorKey, [e]);
  }
  for (const list of fallbackBuckets.values()) {
    const byKey = new Map<string, Entry[]>();
    for (const e of list) {
      const arr = byKey.get(e.key);
      if (arr) arr.push(e);
      else byKey.set(e.key, [e]);
    }
    const keyList = [...byKey.keys()];
    const canonical = new Map<string, string>();
    for (const k of keyList) canonical.set(k, k);
    for (let i = 0; i < keyList.length; i++) {
      for (let j = i + 1; j < keyList.length; j++) {
        const a = keyList[i];
        const b = keyList[j];
        const hit =
          a === b ||
          (a.length >= 4 && b.indexOf(a) !== -1) ||
          (b.length >= 4 && a.indexOf(b) !== -1);
        if (hit) canonical.set(b, canonical.get(a) as string);
      }
    }
    const target = new Map<string, Entry[]>();
    for (const k of keyList) {
      const c = canonical.get(k) as string;
      const arr = target.get(c);
      if (arr) arr.push(...(byKey.get(k) as Entry[]));
      else target.set(c, [...(byKey.get(k) as Entry[])]);
    }
    for (const [c, members] of target) {
      for (const m of members) {
        if (members.length > 1) {
          m.identity = c;
          m.reason = c === m.key ? 'exact_key' : 'substring_key';
        } else {
          m.reason = 'singleton';
        }
      }
    }
  }

  // ---- materialise decisions ------------------------------------------------
  const out = new Map<string, BilibiliGroupingDecision>();
  for (const e of entries) {
    let groupKey: string;
    if (e.guarded) {
      groupKey = '__raw_' + e.bvid;
    } else if (e.identity) {
      groupKey = e.authorKey + '::' + e.identity;
    } else {
      groupKey = e.authorKey + '::' + e.key;
    }
    let residue = e.key;
    if (e.identity) {
      const idx = e.key.indexOf(e.identity);
      residue = idx === -1
        ? e.key
        : (e.key.slice(0, idx) + ' ' + e.key.slice(idx + e.identity.length)).replace(/\s+/g, ' ').trim();
    }
    out.set(e.bvid, {
      groupKey,
      identityKey: e.identity,
      episodeResidue: residue,
      groupingReason: e.reason,
    });
  }
  return out;
}

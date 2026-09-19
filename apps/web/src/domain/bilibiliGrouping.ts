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
  // remaster / relaunch wording — the same mutable-update class as 重置/重做.
  // Proven missing by the Phase 3G-F.1-A population audit: without it, five
  // different packs (冰火魔龙 / 浪客拔刀剑 / 超变态钻石大陆 / 怪物大乱斗 /
  // 无尽幸运方块大陆) merged on the shared word 重生 under the short-run rule.
  '重生', '重制', '重塑', '归来', '回归', '启航', '启程', '再临', '重启', '焕新',
  // degree / intensity descriptors — the same class as 高配/低配/极致.
  // Without them "高度" anchors unrelated packs (高度魔改 is a modifier, not a name).
  '高度', '极高', '超高', '更高', '中等', '入门', '进阶', '轻度', '重度',
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
  '机械动力', '农夫乐事', '虚无世界', '泰坦生物', '泰坦', '幸运方块',
  '群峦传说', '匠魂', '等价交换', 'voxy', 'oxy',
  '暮色森林', '神秘时代', '应用能源', '植物魔法', '血魔法', '女仆',
  '宝可梦', '蔚蓝档案', '斗罗大陆', '手机', '生电', '红石生电', '红石', '基岩',
  'boss', '挑战',
  '沉浸工程', '通用机械', '热力膨胀', '生活调味料',
  // source-game references (《我的世界：地下城》/ 死亡细胞 ...) - a game title a
  // pack borrows content from is not that pack's own name. Without this, 幻想的地下城
  // and 史诗的地下城 (different packs, different 百度 links) merge on "地下城".
  '地下城', '死亡细胞', '我的世界地下城',
  // filler
  '与', '在', '的', '和', '版', '吧', '那就', '成为', '周年', '第', '期', 'v', 'amp', 'quot', 'gt', 'lt',
  'mod', 'minecraft', '我的世界',
]);

/** Minimum identity-bearing characters a shared run must carry. */
export const BILI_MIN_IDENTITY_CHARS = 3;

// A compound suffix can be part of a real name (山海大陆/绿宝石大陆), but the
// suffix by itself is not an identity. Keep it in the token so those names
// remain matchable; reject only the standalone candidate.
const BILI_NON_IDENTIFYING_TOKENS = new Set(['大陆', '无尽']);

export interface BilibiliGroupingInput {
  bvid: string;
  title: string;
  author?: string | null;
  /** Optional source metadata. It is supporting evidence, never a sole merge trigger. */
  download_links?: Array<{ url?: string | null } | null> | null;
  qq_group?: string | null;
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
  /**
   * Debug-only explainability (Phase 3G-F.1-A): the candidate anchors that were
   * proposed for this record and rejected by the admissibility layer, each with
   * the rule that rejected it. Empty for records with no rejected candidates.
   */
  rejectedAnchors?: BilibiliRejectedAnchor[];
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
  return !BILI_NON_IDENTIFYING_TOKENS.has(token) && identityCharsOfToken(token) >= 2;
}

/** Identity-bearing character count of a token run. */
function identityChars(tokens: string[]): number {
  let n = 0;
  for (const t of tokens) n += identityCharsOfToken(t);
  return n;
}

function qualifiesAsIdentity(tokens: string[]): boolean {
  return identityChars(tokens) >= BILI_MIN_IDENTITY_CHARS
    && tokens.some(isIdentityEligibleToken)
    && !tokens.some((token) => BILI_NON_IDENTIFYING_TOKENS.has(token));
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
  const canonical = stripped.replace(/[龍龜]/g, (ch) => ch === '龍' ? '龙' : '龟');
  return canonical.length ? canonical : token;
}

/**
 * `cleanPackKey` intentionally stays conservative, so titles that omit a
 * separator can leave a CJK/Latin or CJK/noise compound as one token
 * (`基岩版仿亡者世界`, `Cobblemon方块宝可梦`, `刀剑异闻录周年`).  Matching
 * needs the structural pieces while the final display key must retain the
 * original cleaned text.  This splitter is language-agnostic: it only cuts at
 * script boundaries and at already-declared noise words.
 */
function splitCompoundToken(token: string): string[] {
  if (!token) return [];
  let parts = [token];
  const splitAt = (value: string, boundary: string): string[] => {
    if (!boundary || !value.includes(boundary)) return [value];
    const out: string[] = [];
    let rest = value;
    while (rest.includes(boundary)) {
      const i = rest.indexOf(boundary);
      if (i > 0) out.push(rest.slice(0, i));
      out.push(boundary);
      rest = rest.slice(i + boundary.length);
    }
    if (rest) out.push(rest);
    return out.filter(Boolean);
  };
  parts = parts.flatMap((p) => p.split(/(?<=[A-Za-z0-9])(?=[\u4e00-\u9fa5])|(?<=[\u4e00-\u9fa5])(?=[A-Za-z0-9])/g));
  // These are connective/compound markers rather than identity labels. They
  // let the matcher see the stable noun on either side without deleting it.
  const structuralBoundaries = ['学生们', '极速', '但是', '拥有了', '使用'];
  // Identity-noise words are removed from identity character counts, but some
  // are complete lexical themes (`泰坦生物`, `斗罗大陆`, `宝可梦`) rather than
  // safe boundaries. Keep the older connective/descriptor splits, while
  // preserving those lexical themes as whole tokens so they cannot manufacture
  // fragments such as `大陆` or `生物`.
  const lexicalNoise = new Set([
    '泰坦生物', '泰坦', '幸运方块', '群峦传说', '宝可梦', '蔚蓝档案', '手机版',
    '斗罗大陆', '手机', '版', '生电', '红石生电', '红石', 'voxy', 'oxy',
  ]);
  const boundaries = [...new Set([
    ...[...BILI_IDENTITY_NOISE_TOKENS].filter((x) => !lexicalNoise.has(x)),
    ...structuralBoundaries,
  ])].sort((a, b) => b.length - a.length);
  for (const boundary of boundaries) parts = parts.flatMap((p) => splitAt(p, boundary));
  // A lexical theme may carry a suffix (`蔚蓝档案超大型`, `泰坦生物复刻`)
  // or a prefix (`方块宝可梦`). Split only at the outer edge; preserve an
  // exact lexical name such as `泰坦生物` as one token.
  for (const boundary of [...lexicalNoise].sort((a, b) => b.length - a.length)) {
    parts = parts.flatMap((p) => {
      if ([...lexicalNoise].some((longer) =>
        longer.length > boundary.length && (p === longer || p.startsWith(longer)))) return [p];
      if (p === boundary || !p.includes(boundary)) return [p];
      return splitAt(p, boundary);
    });
  }
  return parts.map(normalizeTokenForMatch).filter(Boolean);
}

function matchingTokensOf(key: string): string[] {
  return tokensOf(key).flatMap((token) => {
    const parts = splitCompoundToken(token);
    // Keep a compound product spelling in addition to its structural pieces
    // when a token contains a broad/connective noise word but still carries a
    // distinctive remainder. This preserves anchors such as
    // `无尽幸运方块大陆` and `原神与机械` without making standalone noise
    // tokens eligible identities; the admissibility layer still decides the
    // compound as a whole.
    const hasTheme = parts.some((part) => BILI_IDENTITY_NOISE_TOKENS.has(part));
    const compound = normalizeTokenForMatch(token);
    if (hasTheme
      && identityCharsOfToken(compound) >= BILI_MIN_IDENTITY_CHARS) {
      return [compound, ...parts];
    }
    return parts;
  });
}

/**
 * Canonicalise registered project references for identity corroboration.  The
 * parser deliberately ignores ordinary download hosts, QQ groups, and video
 * URLs.  A registered reference is only a supporting signal; the grouping
 * path below still requires an author-local title anchor before it can attach
 * a record to a project identity.
 */
function projectIdentityKeysOf(record: BilibiliGroupingInput): Set<string> {
  const out = new Set<string>();
  for (const link of record.download_links || []) {
    const raw = String(link?.url || '').trim();
    if (!raw) continue;
    let m: RegExpMatchArray | null;
    if ((m = raw.match(/curseforge\.com\/minecraft\/modpacks\/([^/?#]+)/i))) {
      out.add('curseforge:' + m[1].toLowerCase());
    }
    if ((m = raw.match(/mcmod\.cn\/modpack\/(\d+)/i))) {
      out.add('mcmod:modpack/' + m[1]);
    }
    if ((m = raw.match(/bbsmc\.net\/modpack\/([^/?#]+)/i))) {
      out.add('bbsmc:modpack/' + m[1].replace(/\/$/, '').toLowerCase());
    }
    if ((m = raw.match(/github\.com\/([^/]+)\/([^/?#]+)/i))) {
      out.add('github:' + m[1].toLowerCase() + '/' + m[2].replace(/\.git$/, '').toLowerCase());
    }
    if ((m = raw.match(/(?:www\.)?xyebbs\.com\/resources\/(\d+)/i))) {
      out.add('xyebbs:resource/' + m[1]);
    }
    if ((m = raw.match(/(?:www\.)?xyebbs\.com\/res-id\/([^/?#]+)/i))) {
      out.add('xyebbs:res-id/' + m[1].toLowerCase());
    }
    if ((m = raw.match(/modrinth\.com\/modpack\/([^/?#]+)/i))) {
      out.add('modrinth:modpack/' + m[1].toLowerCase());
    }
  }
  return out;
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
  /** Phase 3G-F.1-A: structural evidence used by the admissibility layer */
  adm: AdmissibilityEntry;
  /** Phase 3G-F.1-A: anchors that were proposed for this record and rejected */
  rejected: BilibiliRejectedAnchor[];
  /** Canonical registered project references carried by the source record. */
  projectIds: Set<string>;
  /** A QQ group is corroborating context only; it is never a sole merge key. */
  qqGroup: string;
}

/**
 * ------------------------------------------------------------------ Phase 3G-F.1-A
 * ANCHOR ADMISSIBILITY LAYER
 *
 * Phase 3G-F recovered recall by mining the longest shared identity run, but the
 * Phase 3G-F-A population audit proved it introduced >= 7 REAL false merges: the
 * winning run is sometimes a generic component name (`voxy`), a bracketed SERIES
 * TAG (`难度驱动`), a feature-list shout-out (`星辉死神` / `四叶草` /
 * `各大主播同款` / `颠覆性的`), or a connective English fragment (`or not`).
 *
 * The fix is ADDITIVE (measured, not guessed): the proven miner and its ordering
 * stay exactly as they are, and a run must now additionally pass a layered
 * admissibility check. Every rule below is a *class* rule derived from the 936
 * -record population — no title, token or uploader is special-cased.
 *
 * Evidence / selection harness: pipeline/audit/_3gf1a_r7_exp.js
 *   baseline                    7 false merges, P=1.000 R=0.750
 *   + layered admissibility     0 false merges, P=1.000 R=0.875
 */

/** Bracketed segments of the RAW title, in order. */
const BILI_BRACKET_SEGMENTS =
  /[【\[（(《「『]\s*([^】\]）)》」』]{1,40}?)\s*[】\]）)》」』]/g;

/**
 * Channel boilerplate that occupies a bracket slot without naming a pack. These
 * are never treated as the author's name slot, otherwise a series tag would look
 * like a pack name.
 */
const BILI_BOILERPLATE_SEGMENTS = new Set<string>([
  'mc整合包发布', 'mc大型整合包发布', '整合包发布', 'mc整合包更新', '整合包更新',
  'mc整合包预发布', '整合包预发布', 'mc整合包发布前预热', '整合包发布前预热',
  'mc 整合包发布', '整合包', '我的世界', 'mc', '发布', '更新', '首发', '首發',
  '预', '前预热', '预热',
]);

/**
 * A bracket segment of the shape `<self-name>の整合包发布` / `<self-name>整合包发布`
 * is the CHANNEL introducing itself, not the pack: `【天晓の整合包发布】匠魂之旅`
 * brackets the uploader's handle, and the actual pack name (匠魂之旅) sits in the
 * NEXT slot. Treating the handle as the name slot made R1 blind, so two different
 * packs of that channel merged on the shared handle (found by the Phase 3G-F.2-A
 * expanded audit: 匠魂之旅 vs 血肉寄生虫).
 *
 * The test is structural — an optional self-name followed by the release phrase —
 * so it generalises to any handle; no handle is enumerated.
 */
const BILI_SELF_NAME_SEGMENT = /^[^】\]）)》」』]{1,16}?(?:的|の)?(?:mc)?(?:大型)?(?:整合包|模组包)(?:发布|更新|预发布|发布前预热)$/i;

/** Is this raw bracketed segment channel self-identification rather than a pack name? */
function isSelfNameSegment(seg: string): boolean {
  const s = seg.replace(/\s+/g, '').replace(/^mc/i, 'mc');
  if (!s) return true;
  if (BILI_BOILERPLATE_SEGMENTS.has(s)) return true;
  return BILI_SELF_NAME_SEGMENT.test(s);
}

/**
 * Marketing / slogan vocabulary. Such a run praises or compares; it never names
 * a pack (and it very often sits inside a `！`-separated feature list).
 */
const BILI_SLOGAN_WORDS: readonly string[] = [
  '颠覆性', '主播同款', '同款', '全网', '最全', '极致', '旗舰', '典藏', '震撼',
  '炸裂', '超神', '无敌', '必玩', '神作', '天花板', '顶级', '顶尖', '超多',
  '更强', '全新', '重置', '重制', '终极', '究极', '完美', '史诗', '豪华',
  '更多', '大量', '各种', '更高', '更好', '专用',
];

/**
 * Closed, language-generic class of English function words. A run made only of
 * these is a connective fragment (`or not`), never a pack name.
 */
const BILI_EN_FUNCTION_WORDS = new Set<string>([
  'or', 'not', 'and', 'the', 'a', 'an', 'of', 'in', 'on', 'to', 'for', 'with',
  'by', 'at', 'is', 'are', 'be', 'as', 'it', 'its', 'this', 'that', 'from',
  'into', 'over', 'under', 'up', 'down', 'out', 'no', 'yes', 'do', 'does',
  'did', 'so', 'but', 'if', 'then', 'than', 'my', 'your', 'our', 'their',
  'his', 'her', 'we', 'you', 'they', 'i', 'me', 'us', 'them', 'he', 'she',
]);

/** A short run is one whose identity-bearing characters fall below the normal bar. */
const BILI_MAX_SHORT_RUN_CHARS = 2;

/** A run at or below this size, sitting late in the title, is a feature shout-out. */
const BILI_LIST_VETO_MAX_CHARS = 4;

/** Author-local recurrence that promotes a short token to a real pack name. */
const BILI_SHORT_RUN_MIN_RECURRENCE = 3;

/**
 * A small class of broad themes can corroborate a same-QQ release chain, but
 * never identify a pack by themselves.  This is deliberately separate from
 * the noise set: the words remain non-identifying for ordinary title mining.
 */
const BILI_QQ_ASSISTED_THEMES = new Set(['宝可梦', '生电']);

/** Broad franchise labels are supporting context, not a complete pack name. */
const BILI_THEME_ONLY_TOKENS = new Set(['方可梦']);

// Only a separately established franchise label may bridge a subject-only
// release to a named series. Generic components (mods, game names, or house
// style) remain non-bridging even when they recur across the author scope.
const BILI_VERSION_BRIDGE_THEMES = new Set(['蔚蓝档案']);

function hasReleaseOrVersionSignal(title: string): boolean {
  return /(?:整合包|发布|更新|版本|正式|测试|先行|重置|重制|\bv?\d+(?:\.\d+){1,3}\b)/i.test(title || '');
}

function hasDisjointRegisteredProjects(a: Entry, b: Entry): boolean {
  return a.projectIds.size > 0 && b.projectIds.size > 0
    && ![...a.projectIds].some((id) => b.projectIds.has(id));
}

function qqAssistedThemeOf(a: Entry, b: Entry): string | null {
  if (!a.qqGroup || a.qqGroup !== b.qqGroup) return null;
  if (hasDisjointRegisteredProjects(a, b)) return null;
  if (!hasReleaseOrVersionSignal(a.adm.title) || !hasReleaseOrVersionSignal(b.adm.title)) return null;
  if (!/(?:整合包|modpack|pack)/i.test(a.adm.title) || !/(?:整合包|modpack|pack)/i.test(b.adm.title)) return null;
  const common = bestCommonRun(a.matchTokens, b.matchTokens).run;
  for (const token of common) if (BILI_QQ_ASSISTED_THEMES.has(token)) return token;
  return null;
}

/**
 * A lexical theme at the title head can be the channel's actual release-line
 * name even though the same word is only a component elsewhere.  Use this
 * continuity path only for a repeated head theme with release/version wording,
 * and never across an explicit rebrand marker such as 重生 or 复刻.
 */
function leadingThemeOf(entry: Entry): string | null {
  const first = entry.matchTokens[0];
  if (!first || first.length < 4 || !/[\u4e00-\u9fa5]/.test(first)
    || !BILI_IDENTITY_NOISE_TOKENS.has(first)
    || identityCharsOfToken(first) !== 0 || !hasReleaseOrVersionSignal(entry.adm.title)) return null;
  if ([...BILI_SEPARATE_PRODUCT_MARKERS].some((marker) => entry.adm.title.includes(marker))) return null;
  return first;
}

function aliasShortRunAdmissible(
  a: AdmissibilityEntry, b: AdmissibilityEntry, run: string[],
): boolean {
  if (identityChars(run) !== 2 || run.length !== 1) return false;
  if (run.some((token) => BILI_NON_IDENTIFYING_TOKENS.has(token))) return false;
  if (run.some((token) => BILI_IDENTITY_NOISE_TOKENS.has(token)) || isSloganishRun(run)) return false;
  const joined = run.join('');
  const hasAlias = (title: string): boolean =>
    title.includes(joined) && /[A-Za-z]{4,}(?:[_ -][A-Za-z]{2,})?/.test(title);
  return (hasAlias(a.title) || hasAlias(b.title))
    && hasReleaseOrVersionSignal(a.title)
    && hasReleaseOrVersionSignal(b.title);
}

function hasNearbyPackMarker(entry: AdmissibilityEntry, run: string[]): boolean {
  const title = (entry.title || '').replace(/\s+/g, '');
  const needle = run.join('');
  const at = title.indexOf(needle);
  if (at < 0) return false;
  const around = title.slice(Math.max(0, at - 8), at + needle.length + 8);
  return /整合包|modpack|pack/i.test(around);
}

function lateNamedRunExemption(
  a: AdmissibilityEntry, b: AdmissibilityEntry, run: string[], recurrence: number,
): boolean {
  const hasPositionalNameUse = (entry: AdmissibilityEntry): boolean => {
    const joined = run.join('');
    const at = entry.title.indexOf(joined);
    if (at < 0) return false;
    const firstBoundary = entry.listBoundaries[0];
    const beforeBoundary = firstBoundary === undefined || at < firstBoundary;
    const compact = entry.title.replace(/[\s:：，,。！？!?【】\[\]（）()《》「」『』]/g, '');
    const after = compact.slice(compact.indexOf(joined) + joined.length);
    const tailOnly = after.length === 0 || /^(?:吧|版|版本|更新|发布|整合包|介绍|正式|免费|测试|先行)*$/u.test(after);
    return (beforeBoundary && at <= 12) || tailOnly;
  };
  return identityChars(run) >= BILI_MIN_IDENTITY_CHARS
    && recurrence >= 2
    && !isSloganishRun(run)
    && ((hasNearbyPackMarker(a, run) && hasNearbyPackMarker(b, run))
      || (hasPositionalNameUse(a) && hasPositionalNameUse(b)));
}

function bracketSegmentsOf(title: string): string[] {
  const out: string[] = [];
  BILI_BRACKET_SEGMENTS.lastIndex = 0;
  let m: RegExpExecArray | null;
  while ((m = BILI_BRACKET_SEGMENTS.exec(title || '')) !== null) out.push(m[1].trim());
  return out;
}

function isSloganishToken(token: string): boolean {
  const s = token.replace(/[^\u4e00-\u9fa5A-Za-z]/g, '');
  if (!s) return true;
  return BILI_SLOGAN_WORDS.some((w) => s.includes(w));
}

function isSloganishRun(run: string[]): boolean {
  return run.some(isSloganishToken);
}

/** An ASCII-only run built entirely from English function words. */
function isEnglishFunctionRun(run: string[]): boolean {
  if (!run.length) return false;
  if (run.some((t) => /[\u4e00-\u9fa5]/.test(t))) return false;
  return run.every((t) => BILI_EN_FUNCTION_WORDS.has(t.replace(/[^A-Za-z]/g, '').toLowerCase()));
}

/**
 * Does `tokens` contain `run` as a contiguous token run?
 *
 * Phase 3G-F.2-A: also accepts the CONCATENATED spelling. `cleanPackKey` maps `：`
 * and `：`-like separators to a space, so one author's `怪物大乱斗：重生` becomes the
 * two tokens `['怪物大乱斗','重生']` while another's `怪物大乱斗重生` stays a single
 * token. Both denote the same pack name, and without this the same anchor could not
 * be found in all of the pack's own episodes (the containment pass would leave one
 * record behind and an unrelated downstream anchor would then claim it).
 *
 * The concatenation test only joins a WHOLE run against a WHOLE run, so it cannot
 * make a shorter prefix match a longer unrelated token.
 */
function containsRun(tokens: string[], run: string[]): boolean {
  if (run.length === 0 || run.length > tokens.length) return false;
  for (let i = 0; i + run.length <= tokens.length; i++) {
    let ok = true;
    for (let j = 0; j < run.length; j++) {
      if (tokens[i + j] !== run[j]) { ok = false; break; }
    }
    if (ok) return true;
  }
  if (run.length === 1) {
    const joined = run[0];
    // a single-token run may be spelled across adjacent tokens
    for (let i = 0; i + 1 < tokens.length; i++) {
      if (tokens[i] + tokens[i + 1] === joined) return true;
    }
  } else {
    // a multi-token run may be spelled inside one token
    const joined = run.join('');
    for (const t of tokens) if (t === joined) return true;
  }
  return false;
}

interface AdmissibilityEntry {
  /** tokens of this record's own cleanPackKey, normalised for matching */
  matchTokens: string[];
  /** raw title (brackets intact) — the structure the key has already destroyed */
  title: string;
  /** the author's own name slot: first non-boilerplate bracketed segment, cleaned */
  nameSlotTokens: string[] | null;
  /**
   * Phase 3G-F.2-A: DISTINCT non-boilerplate bracket segments of the raw title,
   * cleaned but NOT merged into the flattened key.
   *
   * `cleanPackKey` turns every bracket into a space, so a bracketed pack name
   * (`史诗的地下城[Dungeons Of Fantasy]`, `深渊之诗[Poetry Of The Abyss]`) is
   * flattened into the same token soup as the surrounding changelog and can lose
   * the anchor race to a descriptive run like `一款大型`. Keeping the bracket
   * contents as their own channel lets a genuine bracketed name corroborate.
   */
  bracketNames: string[][];
  /** character offsets of `！!?？`-style list boundaries in the raw title */
  listBoundaries: number[];
}

function admissibilityEntryOf(title: string, matchTokens: string[]): AdmissibilityEntry {
  let nameSlotTokens: string[] | null = null;
  const bracketNames: string[][] = [];
  for (const seg of bracketSegmentsOf(title)) {
    if (isSelfNameSegment(seg)) continue;
    const cleaned = cleanPackKey(seg);
    const toks = matchingTokensOf(cleaned);
    if (!toks.length) continue;
    if (BILI_BOILERPLATE_SEGMENTS.has(toks.join(''))) continue;
    bracketNames.push(toks);
    if (!nameSlotTokens) nameSlotTokens = toks;
  }
  const listBoundaries: number[] = [];
  const raw = title || '';
  for (let i = 0; i < raw.length; i++) {
    if ('！!?？\n'.includes(raw[i])) listBoundaries.push(i);
  }
  return { matchTokens, title: raw, nameSlotTokens, bracketNames, listBoundaries };
}

/**
 * RULE 1 — NAME-SLOT DISAGREEMENT.
 *
 * If both titles expose a real bracketed name slot and those slots DISAGREE,
 * then a run that appears strictly AFTER the slot in both titles cannot be the
 * shared identity: it is a series tag or a secondary label.
 *
 * `【抗争之际0.6】【难度驱动】…` vs `【旅途痕迹0.5】【难度驱动】…` — the slots
 * 抗争之际 / 旅途痕迹 differ, so 难度驱动 (the second bracket) is rejected.
 */
function violatesNameSlot(
  a: AdmissibilityEntry, b: AdmissibilityEntry, run: string[],
): boolean {
  const na = a.nameSlotTokens;
  const nb = b.nameSlotTokens;
  if (!na || !nb) return false;
  if (na.join(' ') === nb.join(' ')) return false;
  if (containsRun(na, nb) || containsRun(nb, na)) return false;
  const runJoined = run.join(' ');
  if (na.join(' ') === runJoined || nb.join(' ') === runJoined) return false;
  const appearsAfter = (e: AdmissibilityEntry, slot: string[]): boolean => {
    const toks = e.matchTokens;
    for (let i = 0; i + slot.length <= toks.length; i++) {
      let ok = true;
      for (let j = 0; j < slot.length; j++) {
        if (toks[i + j] !== slot[j]) { ok = false; break; }
      }
      if (!ok) continue;
      const after = i + slot.length;
      for (let p = after; p + run.length <= toks.length; p++) {
        let hit = true;
        for (let j = 0; j < run.length; j++) {
          if (toks[p + j] !== run[j]) { hit = false; break; }
        }
        if (hit) return true;
      }
    }
    return false;
  };
  return appearsAfter(a, na) && appearsAfter(b, nb);
}

function violatesThemeNameSlot(
  a: AdmissibilityEntry, b: AdmissibilityEntry, run: string[],
): boolean {
  if (run.length !== 1 || !BILI_THEME_ONLY_TOKENS.has(run[0])) return false;
  const joined = run.join('');
  const mismatch = (entry: AdmissibilityEntry): boolean => {
    if (!entry.nameSlotTokens || containsRun(entry.nameSlotTokens, run)) return false;
    const at = entry.title.indexOf(joined);
    const firstBracket = entry.title.search(/[【\[（(《「『]/);
    return at >= 0 && firstBracket >= 0 && at > firstBracket;
  };
  return mismatch(a) || mismatch(b);
}

function hasNamedEditionDescriptor(entry: AdmissibilityEntry, run: string[]): boolean {
  if (run.length !== 1) return false;
  const tokens = entry.matchTokens;
  let firstRunIndex = -1;
  for (let i = 0; i < tokens.length; i++) {
    if (tokens[i] === run[0]) { firstRunIndex = i; break; }
  }
  for (let i = 0; i + run.length < tokens.length; i++) {
    if (i !== firstRunIndex || tokens[i] !== run[0] || tokens[i + run.length] !== '版') continue;
    const previous = tokens[i - 1];
    if (previous && identityCharsOfToken(previous) >= BILI_MIN_IDENTITY_CHARS
      && !BILI_IDENTITY_NOISE_TOKENS.has(previous)
      && !BILI_NON_IDENTIFYING_TOKENS.has(previous)
      && !isSloganishToken(previous)) return true;
  }
  return false;
}

/**
 * RULE 2 — LATE-POSITION FEATURE LIST.
 *
 * A SHORT or SLOGAN-ish run that occurs only after a `！`/`!`/`?` boundary is a
 * shout-out inside a feature list (`…！星辉死神！…`), not the pack name.
 *
 * A long, non-slogan run is a real name even when the author writes it late
 * (`…！…！…未尽之路涅槃` is the pack's own name in tail position).
 */
function violatesFeatureList(e: AdmissibilityEntry, run: string[]): boolean {
  if (!e.listBoundaries.length) return false;
  const shortOrSlogan =
    identityChars(run) <= BILI_LIST_VETO_MAX_CHARS || isSloganishRun(run);
  if (!shortOrSlogan) return false;
  const pos = e.title.indexOf(run[0]);
  if (pos === -1) return false;
  return pos > e.listBoundaries[0];
}

/**
 * RULE 3 — ENGLISH FUNCTION-WORD RUN.
 * `or not` is a connective fragment shared by two different English names
 * (Minecraft or Not / Maiden or not) — it is not an identity.
 */
function violatesEnglishFunction(run: string[]): boolean {
  return isEnglishFunctionRun(run);
}

/**
 * RULE 4 — SHORT-RUN ADMISSIBILITY.
 *
 * A run below the normal identity bar may still anchor, but only on positive
 * evidence that it is the pack's own name rather than a transient word:
 *   (a) it is the EXACT bracketed name slot of one of the two titles, or
 *   (b) it recurs as the name across >= 3 records of that author scope.
 * Negative evidence (generic pack keys, slogan vocabulary, English function
 * words) always disqualifies it.
 */
function shortRunAdmissible(
  a: AdmissibilityEntry, b: AdmissibilityEntry, run: string[], recurrence: number,
): boolean {
  for (const t of run) {
    if (BILI_GENERIC_PACK_KEYS.has(t)) return false;
    if (BILI_NON_IDENTIFYING_TOKENS.has(t)) return false;
    if (isSloganishToken(t)) return false;
  }
  if (isEnglishFunctionRun(run)) return false;
  const runJoined = run.join(' ');
  const isExactSlot = (e: AdmissibilityEntry): boolean =>
    !!e.nameSlotTokens && e.nameSlotTokens.join(' ') === runJoined;
  if (isExactSlot(a) || isExactSlot(b)) return true;
  return recurrence >= BILI_SHORT_RUN_MIN_RECURRENCE;
}

/**
 * RULE 6 — BRACKETED NAME OUTRANKS A FLATTENED DESCRIPTOR  (Phase 3G-F.2-A).
 *
 * `cleanPackKey` replaces every bracket with a space, so a pack whose real name is
 * bracketed (`…史诗的地下城[Dungeons Of Fantasy]`) competes for the anchor on equal
 * terms with the descriptive run surrounding it (`一款大型`) — and can lose. When
 * that happens a descriptive run becomes the shared "identity" of packs that are
 * actually distinct.
 *
 * The expanded audit found this twice under one uploader (墨竹ギ):
 *   `一款大型` anchored 深渊之诗 together with an unrelated 史诗的地下城.
 *
 * The veto is narrow: it fires only when BOTH records expose bracketed names, those
 * bracket channels DISAGREE, and the contested run is NOT itself one of them. That
 * is positive evidence that the real names were flattened away and something else
 * took their place — so the run is a descriptor, not an identity.
 *
 * Note this rule is about the BRACKET CHANNEL, not about position: a bracketed name
 * in either slot counts, so a genuine series that shares one bracketed name
 * (`[Poetry Of The Abyss]` in both 深渊之诗 episodes) still anchors normally.
 */
function violatesBracketName(
  a: AdmissibilityEntry, b: AdmissibilityEntry, run: string[],
): boolean {
  const ba = a.bracketNames;
  const bb = b.bracketNames;
  if (!ba.length || !bb.length) return false;
  const runJoined = run.join(' ');
  // The contested run must not itself be a bracketed name in either record.
  const isOwnBracketName = (list: string[][]): boolean =>
    list.some((toks) => toks.join(' ') === runJoined);
  if (isOwnBracketName(ba) || isOwnBracketName(bb)) return false;
  // Every bracketed name must be a genuine name, not a descriptor sitting in a slot.
  const isName = (list: string[][]): boolean =>
    list.some((toks) => qualifiesAsIdentity(toks));
  if (!isName(ba) || !isName(bb)) return false;
  // The two bracket channels must have NO name in common.
  const joinedOf = (list: string[][]): Set<string> =>
    new Set(list.map((toks) => toks.join(' ')));
  const sa = joinedOf(ba);
  const sb = joinedOf(bb);
  for (const s of sa) if (sb.has(s)) return false;
  // The contested run must be WEAKER than the names it is displacing. `一款大型`
  // carries 2 identity chars while the bracketed 深渊之诗 / 史诗的地下城 carry far
  // more, so the descriptor is clearly winning the race it should lose. But a run
  // like `享受纯粹的` (4 chars) is the ONLY identity two 咒次元 episodes share, so
  // displacing it would split a real pack — leave it alone.
  const runChars = identityChars(run);
  const bestBracketChars = (list: string[][]): number =>
    Math.max(...list.map((toks) => identityChars(toks)));
  return runChars < bestBracketChars(ba) && runChars < bestBracketChars(bb);
}

/**
 * RULE 5 — MUTUALLY-EXCLUSIVE EDITION LABELS  (Phase 3G-F.2-A).
 *
 * The 3G-F.1-B expanded population audit found ONE residual confirmed false merge
 * on top of the 3G-F.1-A set: `一个小寂哦::怪物大乱斗`, which absorbed the record
 * `…怪物大乱斗：重生…` because the mined anchor `怪物大乱斗` is a plain PREFIX of
 * that title's key.
 *
 * What makes this a real defect (see docs/audit/BILIBILI_GROUPING_POPULATION_EXPANSION.md §5):
 *   BV1f4Kp6yEBf  key `怪物大乱斗 手机版 …`  head = 手机版
 *   BV1nRBFBFEFw  key `怪物大乱斗 重生 …`    head = 重生
 * Both records sit in the SAME group on the shared anchor `怪物大乱斗`, yet they
 * disagree on the token IMMEDIATELY AFTER it, and neither head carries any
 * identity-bearing character — they are pure, mutually-exclusive EDITION labels
 * (a hardware target and a product generation), not version numbers and not
 * description words.
 *
 * Merely "the head differs" is FAR too weak: measured on the population, 77 groups
 * have a differing head, and splitting them would shatter correctly-merged packs
 * (涅槃, 齿轮与腐肉, 的时代 …). The discriminator that isolates the defect is
 * POSITIVE CORROBORATION: the competing head must be RECURRING as a real pack name
 * inside the SAME author scope. Here `重生` is independently attested — the uploader
 * publishes `一个小寂哦::怪物大乱斗重生` as its own 3-member group. So `重生` names a
 * genuinely different pack, and the shared anchor is NOT sufficient identity.
 *
 * With this extra requirement the rule fires on exactly 1 of the 10 groups that
 * have pure-noise competing heads (the other 9 — 辐射新世纪 / soa3 / 宝可梦地平线 /
 * 蛊真人 / 追影之旅 / 血族机械师 / 模拟大都市 / 全新雾中人 / 海洋主题 — keep their
 * correct merges, because none of their heads is attested anywhere as a name).
 * This is a CLASS rule over title structure; no title, token or uploader is
 * special-cased.
 */
function violatesCompetingEdition(
  a: AdmissibilityEntry, b: AdmissibilityEntry, run: string[],
  corroborates: (anchor: string[], head: string) => boolean,
): boolean {
  // Only a single-token anchor can be a bare prefix of a longer name.
  if (run.length !== 1) return false;
  const headsA = headAfter(a, run);
  const headsB = headAfter(b, run);
  if (!headsA.length || !headsB.length) return false;
  // Disjoint head sets, every head a pure edition/update word.
  const all = [...headsA, ...headsB];
  if (!all.every((t) => identityCharsOfToken(t) === 0)) return false;
  if (headsA.some((t) => headsB.includes(t))) return false;
  // At least one competing head must be independently attested as a real name.
  return all.some((t) => corroborates(run, t));
}

/**
 * The token immediately following `run` inside this entry's key, as a set-wrapped
 * single-element list (empty when `run` ends the key).
 *
 * Both spellings must be recognised: the author may write `怪物大乱斗 重生` (two
 * tokens) or `怪物大乱斗重生` (one concatenated token, which is what
 * `cleanPackKey` produces for the titles that omit the space/colon).
 */
function headAfter(e: AdmissibilityEntry, run: string[]): string[] {
  const toks = e.matchTokens;
  for (let i = 0; i + run.length <= toks.length; i++) {
    let ok = true;
    for (let j = 0; j < run.length; j++) {
      if (toks[i + j] !== run[j]) { ok = false; break; }
    }
    if (!ok) continue;
    const next = toks[i + run.length];
    if (next) return [next];
    // concatenated form: the anchor token itself equals run[0] + head
    break;
  }
  const head = run[0];
  for (const t of toks) {
    if (t.length > head.length && t.startsWith(head)) {
      return [t.slice(head.length)];
    }
  }
  return [];
}

/**
 * A human-readable reason why a candidate anchor was rejected, for debug output.
 */
export type BilibiliRejectedAnchorReason =
  | 'name_slot_disagreement'
  | 'late_feature_list'
  | 'english_function_words'
  | 'short_run_not_distinctive'
  | 'bracketed_name_disagreement'
  | 'competing_edition'
  | 'registered_identity_conflict';

export interface BilibiliRejectedAnchor {
  anchor: string;
  reason: BilibiliRejectedAnchorReason;
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

/** Pick the most recurrent named run in a project-ID bucket, not the longest
 * changelog sentence shared by only two releases. */
function projectTitleAnchor(entries: Entry[]): { run: string[]; chars: number } | null {
  const candidates = new Map<string, { run: string[]; chars: number }>();
  for (let i = 0; i < entries.length; i++) {
    for (let j = i + 1; j < entries.length; j++) {
      const pair = bestCommonRun(entries[i].matchTokens, entries[j].matchTokens);
      for (let start = 0; start < pair.run.length; start++) {
        for (let end = start + 1; end <= pair.run.length; end++) {
          const run = pair.run.slice(start, end);
          const chars = identityChars(run);
          if (chars <= 0 || run.some((t) => BILI_IDENTITY_NOISE_TOKENS.has(t)
            || BILI_NON_IDENTIFYING_TOKENS.has(t))) continue;
          if (isSloganishRun(run) || violatesEnglishFunction(run)) continue;
          const key = run.join(' ');
          const old = candidates.get(key);
          if (!old || chars > old.chars) candidates.set(key, { run, chars });
        }
      }
    }
  }
  const ranked = [...candidates.values()].map((candidate) => ({
    ...candidate,
    coverage: entries.filter((e) => containsRun(e.matchTokens, candidate.run)).length,
  })).filter((candidate) => candidate.coverage >= 2);
  ranked.sort((a, b) =>
    (b.coverage - a.coverage)
    || (b.chars - a.chars)
    || (b.run.length - a.run.length)
    || (a.run.join(' ') < b.run.join(' ') ? -1 : a.run.join(' ') > b.run.join(' ') ? 1 : 0));
  return ranked.length ? { run: ranked[0].run, chars: ranked[0].chars } : null;
}

function commonIdentityRuns(a: string[], b: string[]): Array<{ run: string[]; chars: number }> {
  const best = bestCommonRun(a, b);
  if (!best.run.length) return [];
  const out = new Map<string, { run: string[]; chars: number }>();
  // Do not let a descriptive sentence win merely because it wraps the real
  // name.  A run such as `大型 末世 潜行者` contributes the named core
  // `潜行者`; `时光牧场 打造你 的 侏罗纪公园` contributes separate title
  // fragments.  Noise remains available to the admissibility layer when it is
  // part of a title, but never changes the anchor boundary.
  const segments: string[][] = [];
  let segment: string[] = [];
  for (const token of best.run) {
    if (BILI_IDENTITY_NOISE_TOKENS.has(token)) {
      if (segment.length) segments.push(segment);
      segment = [];
    } else {
      segment.push(token);
    }
  }
  if (segment.length) segments.push(segment);
  for (const source of segments) for (let start = 0; start < source.length; start++) {
    for (let end = start + 1; end <= source.length; end++) {
      const run = source.slice(start, end);
      const chars = identityChars(run);
      if (chars <= 0) continue;
      const key = run.join(' ');
      const old = out.get(key);
      if (!old || chars > old.chars) out.set(key, { run, chars });
    }
  }
  return [...out.values()].sort((x, y) =>
    (y.chars - x.chars) || (y.run.length - x.run.length)
    || (x.run.join(' ') < y.run.join(' ') ? -1 : x.run.join(' ') > y.run.join(' ') ? 1 : 0));
}

/**
 * Two records with disjoint registered project references must not be pulled
 * together by a generic component/slogan.  A long, non-slogan title anchor
 * with an explicit release/version signal remains eligible: cross-platform
 * mirrors often use different registered IDs for the same named pack.
 */
function registeredIdentityConflict(
  a: Entry, b: Entry, run: string[],
): boolean {
  if (!a.projectIds.size || !b.projectIds.size) return false;
  if ([...a.projectIds].some((id) => b.projectIds.has(id))) return false;
  if (!run.length || isSloganishRun(run) || violatesEnglishFunction(run)) return true;
  const chars = identityChars(run);
  if (run.some((token) => BILI_IDENTITY_NOISE_TOKENS.has(token))) return true;
  // Short named packs such as 涅槃/化龍 legitimately use different mirror
  // IDs across releases. Once the run is neither a declared component nor a
  // slogan, the repeated title anchor is the corroborating signal; the
  // registered references are not required to be byte-identical.
  return chars <= 0;
}

const BILI_EDITION_MARKERS = [
  '优化', '绿色版', '绿化', '服务端', '客户端', '手机版', '手机移植', '移植版',
  '重生', '复刻', '仿照',
];
const BILI_SEPARATE_PRODUCT_MARKERS = new Set(['重生', '复刻', '手机版']);

function projectAssistedThemeOf(a: Entry, b: Entry): string | null {
  const oneProject = a.projectIds.size > 0 || b.projectIds.size > 0;
  if (!oneProject || hasDisjointRegisteredProjects(a, b)) return null;
  const common = bestCommonRun(a.matchTokens, b.matchTokens).run;
  const theme = common.find((token) =>
    BILI_IDENTITY_NOISE_TOKENS.has(token)
    && identityCharsOfToken(token) === 0
    && token.length >= 3,
  );
  if (!theme) return null;
  if (BILI_EDITION_MARKERS.some((marker) => a.adm.title.includes(marker) || b.adm.title.includes(marker))) return null;
  if (!hasReleaseOrVersionSignal(a.adm.title) || !hasReleaseOrVersionSignal(b.adm.title)) return null;
  return theme;
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
    const matchTokens = matchingTokensOf(key);
    return {
      bvid: r.bvid,
      key,
      tokens: tokensOf(key),
      matchTokens,
      authorKey: authorScope(r.author),
      guarded,
      identity: '',
      reason: guarded ? 'generic_guard' : 'singleton',
      adm: admissibilityEntryOf(r.title || '', matchTokens),
      rejected: [],
      projectIds: projectIdentityKeysOf(r),
      qqGroup: String(r.qq_group || '').trim(),
    };
  });

  const allByAuthor = new Map<string, Entry[]>();
  for (const e of entries) {
    const list = allByAuthor.get(e.authorKey);
    if (list) list.push(e);
    else allByAuthor.set(e.authorKey, [e]);
  }
  const byAuthor = new Map<string, Entry[]>();
  for (const e of entries) {
    if (e.guarded) continue;
    const list = byAuthor.get(e.authorKey);
    if (list) list.push(e);
    else byAuthor.set(e.authorKey, [e]);
  }

  // Registered project references can rescue a guarded/raw record, but only
  // when the same author also supplies a real title anchor.  URLs/IDs alone
  // never create a group.  This is intentionally before the normal unguarded
  // miner so a short key such as “咒次元” can join its longer sibling.
  for (const list of allByAuthor.values()) {
    const byProject = new Map<string, Entry[]>();
    for (const e of list) for (const id of e.projectIds) {
      const bucket = byProject.get(id);
      if (bucket) bucket.push(e);
      else byProject.set(id, [e]);
    }
    const projectAnchors = new Map<Entry, { anchor: string; chars: number }>();
    for (const bucket of byProject.values()) {
      const unique = [...new Set(bucket)];
      if (unique.length < 2) continue;
      const best = projectTitleAnchor(unique);
      if (!best) continue;
      const anchor = best.run.join(' ');
      for (const e of unique) {
        const old = projectAnchors.get(e);
        if (!old || best.chars > old.chars) projectAnchors.set(e, { anchor, chars: best.chars });
      }
    }
    for (const [e, chosen] of projectAnchors) {
      e.identity = chosen.anchor;
      e.reason = 'identity_run';
    }

    // If one release carries a registered project reference but its sibling
    // title has only the same broad theme, the project link can corroborate
    // that title. Edition-marked siblings are intentionally excluded: they
    // may be a separate optimisation/green/mobile line under the same theme.
    for (let i = 0; i < list.length; i++) {
      for (let j = i + 1; j < list.length; j++) {
        const a = list[i]; const b = list[j];
        const theme = projectAssistedThemeOf(a, b);
        if (!theme) continue;
        if ((a.identity && a.identity !== theme) || (b.identity && b.identity !== theme)) continue;
        const anchor = `project-theme:${theme}`;
        for (const e of list) {
          if (e.matchTokens.includes(theme) && !BILI_EDITION_MARKERS.some((marker) => e.adm.title.includes(marker))) {
            e.identity = anchor;
            e.reason = 'identity_run';
          }
        }
      }
    }

    // Exact repeated release titles are safe evidence for an otherwise raw
    // bucket. This is deliberately narrower than key equality: generic keys
    // such as “生存/冒险/整合包” remain guarded and independent.
    const exactTitles = new Map<string, Entry[]>();
    for (const e of list) {
      if (!e.key || BILI_GENERIC_PACK_KEYS.has(e.key)) continue;
      const fingerprint = e.adm.title.replace(/\s+/g, ' ').trim().toLowerCase();
      const bucket = exactTitles.get(fingerprint);
      if (bucket) bucket.push(e);
      else exactTitles.set(fingerprint, [e]);
    }
    for (const bucket of exactTitles.values()) {
      if (bucket.length < 2) continue;
      // Exact title repetition is useful evidence, but the cleaned key can
      // still contain a lexical theme and connective residue (for example a
      // title shaped like "named-pack + source-game + 与").  Repeating that
      // whole sentence would make the residue part of the identity and would
      // then split a shorter sibling.  Derive the repeated anchor from the
      // same noise-aware token runs used by the normal miner.
      const repeatedCandidates = commonIdentityRuns(bucket[0].matchTokens, bucket[1].matchTokens)
        .filter((candidate) => qualifiesAsIdentity(candidate.run)
          && !registeredIdentityConflict(bucket[0], bucket[1], candidate.run))
        .map((candidate) => ({
          ...candidate,
          recurrence: list.filter((e) => containsRun(e.matchTokens, candidate.run)).length,
        }))
        .sort((a, b) =>
          (b.recurrence - a.recurrence)
          || (b.chars - a.chars)
          || (b.run.length - a.run.length)
          || (a.run.join(' ') < b.run.join(' ') ? -1 : a.run.join(' ') > b.run.join(' ') ? 1 : 0));
      const anchor = repeatedCandidates.length ? repeatedCandidates[0].run.join(' ') : bucket[0].key;
      for (const e of bucket) {
        e.identity = anchor;
        e.reason = 'identity_run';
      }
    }

    // Same-QQ continuity is a corroboration path for broad themes such as a
    // Pokémon or redstone/electricity series.  The anchor is namespaced by the
    // observed theme and QQ only after both titles independently look like
    // releases; QQ alone never creates a group, and project-id conflicts veto it.
    for (let i = 0; i < list.length; i++) {
      for (let j = i + 1; j < list.length; j++) {
        const a = list[i]; const b = list[j];
        const theme = qqAssistedThemeOf(a, b);
        if (!theme) continue;
        if ((a.identity && a.identity !== theme) || (b.identity && b.identity !== theme)) continue;
        const anchor = `aux:${theme}:qq:${a.qqGroup}`;
        for (const e of list) {
          if (e.qqGroup === a.qqGroup && e.matchTokens.includes(theme)
            && hasReleaseOrVersionSignal(e.adm.title)) {
            e.identity = anchor;
            e.reason = 'identity_run';
          }
        }
      }
    }

    // A repeated lexical theme at the title head can represent a named
    // release line even when that same theme is only a component in other
    // titles. This is title-structure continuity, not a theme-only merge:
    // every member must independently look like a release and explicit
    // rebrand markers are excluded above.
    const leadingThemes = new Map<string, Entry[]>();
    for (const e of list) {
      const theme = leadingThemeOf(e);
      if (!theme) continue;
      const bucket = leadingThemes.get(theme);
      if (bucket) bucket.push(e);
      else leadingThemes.set(theme, [e]);
    }
    for (const [theme, bucket] of leadingThemes) {
      if (bucket.length < 2) continue;
      // If the same author repeatedly names another eligible token in these
      // titles, the head theme is a component/genre prefix rather than the
      // product identity (`机械动力 ... 命运齿轮` is the motivating shape).
      const hasCompetingNamedAnchor = bucket.some((e) => e.matchTokens.some((token) => {
        if (token === theme || BILI_IDENTITY_NOISE_TOKENS.has(token)
          || BILI_NON_IDENTIFYING_TOKENS.has(token) || isSloganishToken(token)
          || !isIdentityEligibleToken(token)) return false;
        return identityCharsOfToken(token) >= BILI_MIN_IDENTITY_CHARS + 1;
      }));
      if (hasCompetingNamedAnchor) continue;
      for (const e of bucket) {
        if (!e.identity || e.identity === theme || e.identity.startsWith(`aux:${theme}:`)) {
          e.identity = theme;
          e.reason = 'identity_run';
        }
      }
    }

    // A two-release author scope may contain one guarded/raw title. Promote a
    // short but non-generic title run only when both records carry release or
    // update language; this keeps the raw/named boundary from hiding a genuine
    // version chain without turning arbitrary short words into pack names.
    for (let i = 0; i < list.length; i++) {
      for (let j = i + 1; j < list.length; j++) {
        const a = list[i]; const b = list[j];
        const pair = bestCommonRun(a.matchTokens, b.matchTokens);
        if (!pair.run.length || registeredIdentityConflict(a, b, pair.run)) continue;
        if (!qualifiesAsIdentity(pair.run)) continue;
        const recurrence = list.filter((e) => containsRun(e.matchTokens, pair.run)).length;
        if (!a.guarded && !b.guarded) continue;
        const admissible = pair.chars >= BILI_MIN_IDENTITY_CHARS
          || shortRunAdmissible(a.adm, b.adm, pair.run, recurrence);
        if (!admissible) continue;
        const anchor = pair.run.join(' ');
        for (const e of list) {
          if (containsRun(e.matchTokens, pair.run) && (!e.identity || e.guarded)) {
            e.identity = anchor;
            e.reason = 'identity_run';
          }
        }
      }
    }
  }

  // ---- identity run mining, strictly inside one author scope -----------------
  for (const list of byAuthor.values()) {
    // anchor -> member bvids
    const anchorMembers = new Map<string, Set<string>>();
    const competingEditionAnchors = new Set<string>();
    // Members which carry a corroborated competing edition must not be pulled
    // back into the shorter shared anchor by the later containment pass.

    // Phase 3G-F.1-A: author-local recurrence of each candidate run, computed once.
    // A short token that names the pack recurs across that uploader's episodes; a
    // transient word (重生 / 高度) is concentrated and cannot satisfy this.
    const recurrenceOf = (run: string[]): number => {
      let n = 0;
      for (const e of list) if (containsRun(e.matchTokens, run)) n += 1;
      return n;
    };

    // Phase 3G-F.2-A: is `head` independently attested as a real pack name in this
    // same author scope? Count the records of this scope — EXCLUDING the two that
    // are colliding — whose key carries `anchor`+`head` in the concatenated form
    // `anchorhead` (or adjacently), i.e. the scope spells that longer name out.
    // `重生` qualifies for 怪物大乱斗 (the uploader runs a separate three-member
    // `怪物大乱斗重生` group); the one-off formatting words in the other nine
    // structurally similar groups are never attested this way.
    const corroboratedHead = (anchor: string[], head: string, a: Entry, b: Entry): boolean => {
      const joined = anchor.join('') + head;
      let attestations = 0;
      for (const e of list) {
        if (e === a || e === b) continue;
        const compactTitle = e.adm.title.replace(/[\s:：，,。！？!?【】\[\]（）()《》「」『』]/g, '');
        if (compactTitle.includes(joined)) attestations += 1;
      }
      return attestations >= 1;
    };

    for (let i = 0; i < list.length; i++) {
      for (let j = i + 1; j < list.length; j++) {
        const a = list[i];
        const b = list[j];
        // Keep the explainability contract for a shared component that is
        // rejected by disagreeing bracketed name slots, even when the
        // component is excluded from identity mining as declared noise.
        for (const token of new Set(a.matchTokens.filter((t) => b.matchTokens.includes(t)))) {
          if (!BILI_IDENTITY_NOISE_TOKENS.has(token)
            || !violatesNameSlot(a.adm, b.adm, [token])) continue;
          for (const e of [a, b]) {
            if (!e.rejected.some((x) => x.anchor === token && x.reason === 'name_slot_disagreement')) {
              e.rejected.push({ anchor: token, reason: 'name_slot_disagreement' });
            }
          }
        }
        for (const candidate of commonIdentityRuns(a.matchTokens, b.matchTokens)) {
          const { run, chars } = candidate;
          if (chars <= 0) continue;
        if (!qualifiesAsIdentity(run) && chars < BILI_MAX_SHORT_RUN_CHARS) continue;

        // ---- Phase 3G-F.1-A admissibility layer ------------------------------
        // Rules are evaluated most-specific first so the reported reason is the
        // strongest piece of evidence, and a rejection is recorded for debugging.
        let rejection: BilibiliRejectedAnchorReason | null = null;
        if (chars < BILI_MIN_IDENTITY_CHARS) {
          if (!shortRunAdmissible(a.adm, b.adm, run, recurrenceOf(run))
            && !aliasShortRunAdmissible(a.adm, b.adm, run)) {
            rejection = 'short_run_not_distinctive';
          }
        }
        if (!rejection && (violatesNameSlot(a.adm, b.adm, run)
          || violatesThemeNameSlot(a.adm, b.adm, run))) {
          rejection = 'name_slot_disagreement';
        }
        if (!rejection
          && (violatesFeatureList(a.adm, run) || violatesFeatureList(b.adm, run))
          && !lateNamedRunExemption(a.adm, b.adm, run, recurrenceOf(run))) {
          rejection = 'late_feature_list';
        }
        if (!rejection && violatesEnglishFunction(run)) {
          rejection = 'english_function_words';
        }
        if (!rejection && registeredIdentityConflict(a, b, run)) {
          rejection = 'registered_identity_conflict';
        }
        if (!rejection && violatesBracketName(a.adm, b.adm, run)) {
          rejection = 'bracketed_name_disagreement';
        }
        if (!rejection && violatesCompetingEdition(
          a.adm, b.adm, run,
          (anchor, head) => corroboratedHead(anchor, head, a, b),
        )) {
          rejection = 'competing_edition';
        }
        if (rejection) {
          const anchor = run.join(' ');
          for (const e of [a, b]) {
            if (!e.rejected.some((x) => x.anchor === anchor && x.reason === rejection)) {
              e.rejected.push({ anchor, reason: rejection });
            }
          }
          // Phase 3G-F.2-A: a competing-edition rejection tells us the shared
          // anchor is a PREFIX of a longer real name. Register that longer name
          // (`怪物大乱斗重生`) so the affected record lands on its own pack instead
          // of being re-attracted by an unrelated downstream anchor.
          if (rejection === 'competing_edition') {
            for (const e of [a, b]) {
              const head = headAfter(e.adm, run)[0];
              if (!head || identityCharsOfToken(head) !== 0) continue;
              const extendedTokens = [...run, head];
              const extended = extendedTokens.join(' ');
              if (corroboratedHead(run, head, a, b) && containsRun(e.matchTokens, extendedTokens)) {
                let s = anchorMembers.get(extended);
                if (!s) { s = new Set<string>(); anchorMembers.set(extended, s); }
                s.add(e.bvid);
                competingEditionAnchors.add(extended);
              }
            }
          }
          continue;
        }

        const anchor = run.join(' ');
        let set = anchorMembers.get(anchor);
        if (!set) { set = new Set<string>(); anchorMembers.set(anchor, set); }
        set.add(a.bvid);
        set.add(b.bvid);
        }
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

    // A corroborated rebrand marker is a longer product identity, not an
    // episode suffix. Promote only the explicitly registered competing
    // anchors; ordinary prefix anchors keep the historical ordering above.
    for (const anchor of competingEditionAnchors) {
      const tokens = anchor.split(' ');
      const head = tokens[tokens.length - 1];
      if (!BILI_SEPARATE_PRODUCT_MARKERS.has(head)) continue;
      for (const e of list) {
        if (containsRun(e.matchTokens, tokens)) {
          e.identity = anchor;
          e.reason = 'identity_run';
        }
      }
    }

    // A shared label followed by a bare edition marker can be a feature of a
    // different named pack (`独立名称 + shared-label + 版`). Do not let the
    // shorter anchor absorb that record after the pairwise admissibility pass.
    for (const e of list) {
      if (!e.identity || !hasNamedEditionDescriptor(e.adm, e.identity.split(' '))) continue;
      if (!e.rejected.some((x) => x.anchor === e.identity && x.reason === 'competing_edition')) {
        e.rejected.push({ anchor: e.identity, reason: 'competing_edition' });
      }
      e.identity = '';
      e.reason = 'singleton';
    }
  }

  // Version-chain bridge: a release may omit the pack's short name while
  // retaining a broad subject label that is present beside a stronger anchor
  // in the same author's other releases (for example, a former subject-only
  // title followed by a named `青春复兴` line).  Apply this only when exactly
  // one strong identity in the scope is supported by that shared subject and
  // both records carry release/version wording. Ambiguous subjects with more
  // than one competing identity remain unassigned.
  for (const list of allByAuthor.values()) {
    const candidates = new Map<string, Entry[]>();
    for (const e of list) {
      if (!e.identity || identityChars(e.identity.split(' ')) < BILI_MIN_IDENTITY_CHARS) continue;
      if (e.identity.split(' ').some((token) => BILI_IDENTITY_NOISE_TOKENS.has(token))) continue;
      const bucket = candidates.get(e.identity);
      if (bucket) bucket.push(e);
      else candidates.set(e.identity, [e]);
    }
    for (const e of list) {
      if (e.identity || !hasReleaseOrVersionSignal(e.adm.title)) continue;
      // A title that still contains its own independently named pack must not
      // be pulled into a different identity merely because both titles mention
      // the same broad subject (e.g. two adaptations of one franchise).  The
      // bridge is reserved for subject-only release/update records.
      const independentNameChars = identityChars(e.matchTokens.filter((token) =>
        !BILI_IDENTITY_NOISE_TOKENS.has(token),
      ));
      if (independentNameChars >= BILI_MIN_IDENTITY_CHARS) continue;
      const possible = new Map<string, Entry>();
      for (const [identity, members] of candidates) {
        const representative = members.find((member) => {
          if (!hasReleaseOrVersionSignal(member.adm.title)) return false;
          if (hasDisjointRegisteredProjects(e, member)) return false;
          return e.matchTokens.some((token) =>
            BILI_VERSION_BRIDGE_THEMES.has(token)
            && identityCharsOfToken(token) === 0
            && member.matchTokens.includes(token),
          );
        });
        if (representative) possible.set(identity, representative);
      }
      if (possible.size === 1) {
        e.identity = [...possible.keys()][0];
        e.reason = 'identity_run';
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
        const left = byKey.get(a) as Entry[];
        const right = byKey.get(b) as Entry[];
        const compatible = left.every((x) => right.every((y) => {
          const common = bestCommonRun(x.matchTokens, y.matchTokens);
          return qualifiesAsIdentity(common.run)
            && !registeredIdentityConflict(x, y, common.run);
        }));
        if (hit && compatible) canonical.set(b, canonical.get(a) as string);
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
    // Keep edition/green/mobile variants out of the project-theme rescue even
    // if a later title-mining pass assigned the same broad theme.  Registered
    // project evidence may corroborate a base line, but it cannot erase an
    // explicit edition marker.
    if (e.identity.startsWith('project-theme:')
      && BILI_EDITION_MARKERS.some((marker) => e.adm.title.includes(marker))) {
      e.identity = '';
      e.reason = e.guarded ? 'generic_guard' : 'singleton';
    }
    let displayIdentity = e.identity;
    if (displayIdentity && e.rejected.some((x) => x.reason === 'competing_edition')) {
      const marker = [...BILI_SEPARATE_PRODUCT_MARKERS]
        .find((candidate) => e.adm.title.includes(candidate));
      if (marker && !displayIdentity.includes(marker)) displayIdentity += marker;
    }
    // Edition markers are lexical suffixes in the public group label even
    // when the matching pass kept them as separate structural tokens.
    displayIdentity = displayIdentity.replace(/ (重生|复刻|手机版)$/u, '$1');
    let groupKey: string;
    if (e.guarded && !e.identity) {
      groupKey = '__raw_' + e.bvid;
    } else if (e.identity) {
      groupKey = e.authorKey + '::' + displayIdentity;
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
      identityKey: displayIdentity,
      episodeResidue: residue,
      groupingReason: e.reason,
      ...(e.rejected.length ? { rejectedAnchors: e.rejected } : {}),
    });
  }
  return out;
}

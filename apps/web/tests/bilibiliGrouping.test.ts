import { describe, it, expect } from 'vitest';
import {
  groupBilibiliPacks,
  identityCharsOfToken,
  normalizeTokenForMatch,
  authorScope,
  BILI_MIN_IDENTITY_CHARS,
} from '../src/domain/bilibiliGrouping';

const rec = (bvid: string, title: string, author: string) => ({ bvid, title, author });

function keyOf(records: ReturnType<typeof rec>[]) {
  const out: Record<string, string> = {};
  for (const [bvid, d] of groupBilibiliPacks(records)) out[bvid] = d.groupKey;
  return out;
}

describe('bilibiliGrouping — two-level identity model', () => {
  it('merges same-pack episodes whose changelog wording differs', () => {
    const keys = keyOf([
      rec('A1', '【整合包发布】群峦野望1.1-原始科技革新', '啊liu22'),
      rec('A2', '【整合包发布】群峦野望1.2-沉浸科技革新', '啊liu22'),
      rec('A3', '【整合包发布】群峦野望1.3-挖矿来！抢油气来！', '啊liu22'),
    ]);
    expect(new Set(Object.values(keys)).size).toBe(1);
  });

  it('keeps different packs of the same uploader separate', () => {
    const keys = keyOf([
      rec('B1', '我的世界 小行星空岛生存整合包发布！免费！体验up们同款小行星空岛！', '一个小寂哦'),
      rec('B2', '我的世界 《弑神之路2.2:神器锻世》整合包发布！1.20.1神器泰坦整合包', '一个小寂哦'),
    ]);
    expect(new Set(Object.values(keys)).size).toBe(2);
  });

  it('never merges across uploaders even with identical titles', () => {
    const t = 'MC整合包发布【阿卡迪亚的天启】1.8正式版更新！';
    const keys = keyOf([rec('C1', t, 'uploaderOne'), rec('C2', t, 'uploaderTwo')]);
    expect(keys.C1).not.toBe(keys.C2);
    expect(keys.C1.startsWith('uploaderone::')).toBe(true);
    expect(keys.C2.startsWith('uploadertwo::')).toBe(true);
  });

  it('keeps the generic/short-key guard (historical 黑金 false merge)', () => {
    const keys = keyOf([
      rec('D1', '[MC整合包]生存整合包-1.21.1', '黑金'),
      rec('D2', '我的世界【生存整合包】生存', '黑金'),
    ]);
    expect(keys.D1).toBe('__raw_D1');
    expect(keys.D2).toBe('__raw_D2');
  });

  it('does not let a mod name alone anchor an identity', () => {
    const keys = keyOf([
      rec('E1', '我的世界机械动力6.0.9 《命运齿轮整合包》1.4.8更新日志', '明月庄主'),
      rec('E2', '我的世界机械动力1.20.1整合包《月亮工厂MCF》发布，含开服方法！', '明月庄主'),
    ]);
    expect(keys.E1).not.toBe(keys.E2);
  });

  it('does not let a genre descriptor alone anchor an identity', () => {
    const keys = keyOf([
      rec('F1', '我的世界大型末世整合包《潜行者2.0》正式版免费发布', '时唅'),
      rec('F2', '我的世界大型末世整合包辐射《生还者3.1》低配版发布', '时唅'),
    ]);
    expect(keys.F1).not.toBe(keys.F2);
  });

  it('exposes debug explainability for every decision', () => {
    const d = groupBilibiliPacks([
      rec('G1', '【整合包发布】群峦野望1.1-原始科技革新', '啊liu22'),
      rec('G2', '【整合包发布】群峦野望1.2-沉浸科技革新', '啊liu22'),
    ]);
    const one = d.get('G1')!;
    expect(one.groupingReason).toBe('identity_run');
    expect(one.identityKey).toBe('群峦野望');
    expect(one.episodeResidue).toContain('革新');
  });

  it('is deterministic regardless of input order', () => {
    const a = rec('H1', '【整合包更新】云游四海V1.6：看到那颗黄金树了吗？', 'AC6_');
    const b = rec('H2', '【整合包更新】云游四海V1.5：一场没有负担的旅行', 'AC6_');
    const c = rec('H3', '【整合包更新】云游四海V1.4：因为山就在那里', 'AC6_');
    const k1 = keyOf([a, b, c]);
    const k2 = keyOf([c, a, b]);
    expect(k1).toEqual(k2);
  });

  it('normalises CJK tokens that carry a latin suffix', () => {
    expect(normalizeTokenForMatch('虚饰作品v')).toBe('虚饰作品');
    expect(normalizeTokenForMatch('云游四海v')).toBe('云游四海');
    expect(normalizeTokenForMatch('mon')).toBe('mon');
    expect(normalizeTokenForMatch('soa3')).toBe('soa3');
  });

  it('strips noise as substrings so concatenated descriptors cannot anchor', () => {
    expect(identityCharsOfToken('大型末世')).toBe(0);
    expect(identityCharsOfToken('齿轮与腐肉')).toBe(4);
    expect(identityCharsOfToken('机械动力')).toBe(0);
    expect(identityCharsOfToken('地下城')).toBe(0);
  });

  it('keeps a conservative identity threshold and author scoping', () => {
    expect(BILI_MIN_IDENTITY_CHARS).toBeGreaterThanOrEqual(3);
    expect(authorScope('  AC6_ ')).toBe('ac6_');
    expect(authorScope(null)).toBe('unknown');
  });
});

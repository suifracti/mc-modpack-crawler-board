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

/**
 * Phase 3G-F.1-A regression suite.
 *
 * Every case below is a REAL merge observed in the 936-record production payload
 * during the 3G-F-A population audit (or found by the 3G-F.1 fix itself). None is
 * covered by the frozen 22-case negative corpus, which is precisely why the
 * benchmark kept reporting FalseMerge = 0 while production merged different packs.
 * They are reproduced here from the actual titles so the guard is exercised on the
 * real wording, not a paraphrase.
 */
describe('bilibiliGrouping — Phase 3G-F.1-A population false-merge regressions', () => {
  it('splits 叙利亚自爆民兵: a render-mod name must not be the pack identity', () => {
    // Both titles share only "voxy" (a generic renderer mod). The bracketed name
    // slots 《你好，新蒸程》 vs 《你好，新世代》 DISAGREE -> different packs.
    // This is the `voxy` class: a component/mod name is title context, not identity.
    const keys = keyOf([
      rec('V1', '《你好，新蒸程》整合包正式发布！航空学，voxy，独家地形，构成mc的视觉盛宴', '叙利亚自爆民兵'),
      rec('V2', '《你好，新世代》整合包发布，voxy，机械动力6.0.8，瓦尔基里全新兼容，1.20.1forge', '叙利亚自爆民兵'),
    ]);
    expect(keys.V1).not.toBe(keys.V2);
  });

  it('splits tibsalta: a bracketed series tag must not outrank the pack name', () => {
    // The real pack names 【抗争之际】/【旅途痕迹】 sit in the FIRST bracket and
    // differ; 【难度驱动】 is the shared SERIES tag in the SECOND bracket.
    // cleanPackKey destroys bracket structure, so the series tag used to win by
    // default. This is the bracket/series-tag class.
    const keys = keyOf([
      rec('T1', '【抗争之际0.6】【难度驱动】1.19.2我的世界冒险向整合包发布', 'Tibsalta'),
      rec('T2', '【旅途痕迹0.5】【难度驱动】1.19.2我的世界整合包发布', 'Tibsalta'),
    ]);
    expect(keys.T1).not.toBe(keys.T2);
  });

  it('splits a late feature-list shout-out (星辉死神 / 四叶草 / 颠覆性的)', () => {
    // A short or slogan-ish run that only appears AFTER a ！/! boundary is a feature
    // call-out, not the pack identity.
    const xinghui = keyOf([
      rec('X1', '我的世界 神器收集计划0.1版本发布！最全神器！炫猫！星辉死神！斗蛐蛐专用整合包！', '一个小寂哦'),
      rec('X2', '我的世界 无尽幸运方块大陆：重生整合包发布！新增各种泰坦作为BOSS！星辉死神！终极骷髅！', '一个小寂哦'),
    ]);
    expect(xinghui.X1).not.toBe(xinghui.X2);

    const clover = keyOf([
      rec('Y1', '我的世界 1.21.4新泰坦生物整合包更新 矿石菌种？更多泰坦！四叶草！幸运方块？', '一个小寂哦'),
      rec('Y2', '我的世界 执行之龙生存整合包发布！叶枫同款！强化工具！四叶草！超多经典模组！', '一个小寂哦'),
    ]);
    expect(clover.Y1).not.toBe(clover.Y2);

    const dianfu = keyOf([
      rec('Z1', '【MC整合包发布】摄魂 破刹 定身！颠覆性的战斗交互体验---摄影奇境宣传片', '墨言eclipse'),
      rec('Z2', '【MC整合包发布】"颠覆性的全随机冒险，锚定命运的救世征途！"------- 命轮无章 [Infinite Random]', '墨言eclipse'),
    ]);
    expect(dianfu.Z1).not.toBe(dianfu.Z2);
  });

  it('splits on English function words (or not)', () => {
    // "or not" is an ASCII connective fragment shared across different IPs.
    const keys = keyOf([
      rec('R1', 'Minecraft or Not: Girl&Gun 整合包发布', '原界环'),
      rec('R2', 'Maiden or not 整合包发布', '原界环'),
    ]);
    expect(keys.R1).not.toBe(keys.R2);
  });

  it('keeps the brief-named voxy / 难度驱动 regressions separate', () => {
    // The two regressions named explicitly in the phase brief, asserted together
    // so a regression on either one fails on its own line.
    const all = keyOf([
      rec('N1', '《你好，新蒸程》整合包正式发布！航空学，voxy，独家地形，构成mc的视觉盛宴', '叙利亚自爆民兵'),
      rec('N2', '《你好，新世代》整合包发布，voxy，机械动力6.0.8，瓦尔基里全新兼容，1.20.1forge', '叙利亚自爆民兵'),
      rec('N3', '【抗争之际0.6】【难度驱动】1.19.2我的世界冒险向整合包发布', 'Tibsalta'),
      rec('N4', '【旅途痕迹0.5】【难度驱动】1.19.2我的世界整合包发布', 'Tibsalta'),
    ]);
    expect(all.N1).not.toBe(all.N2);
    expect(all.N3).not.toBe(all.N4);
  });

  it('does not merge 涅槃 with 未尽之路涅槃 (two packs, verified by resource ids)', () => {
    // Phase 3G-F.1-A CORRECTED the earlier premise: the 7 records containing 涅槃
    // are TWO packs — 涅槃 (xyebbs resources/37418) and 未尽之路-涅槃 (res-id/TUPN).
    // The uploader states the two are unrelated, so 2 groups is the CORRECT result;
    // forcing them into one group would be a real over-merge.
    const keys = keyOf([
      rec('P1', '[MC整合包发布:涅槃]  无神明渡我 我亦是神明', '墨言eclipse'),
      rec('P2', '[整合包更新-涅槃v0.2]神吞降世，邪神投影，万魂幡！ 超越法则的魔法镰刀战斗之旅', '墨言eclipse'),
      rec('P3', '[MC整合包预发布] 高度魔改/自制饰品/镰咒双生 未尽之路涅槃', '墨言eclipse'),
      rec('P4', '[MC整合包发布前预热] 去同质化!自制模组!大量自制饰品!全boss机制重构!以手中奥法之力,证世间无上涅槃-[未尽之路涅槃]', '墨言eclipse'),
    ]);
    // the two 涅槃 records agree
    expect(keys.P1).toBe(keys.P2);
    // the two 未尽之路-涅槃 records agree
    expect(keys.P3).toBe(keys.P4);
    // but the two packs stay apart
    expect(keys.P1).not.toBe(keys.P3);
  });

  it('allows a short pack name to anchor when it recurs as a name', () => {
    // R7: a 2-char run may anchor if it IS the pack name (recurs across episodes)
    // or is the exact name slot of one title. 涅槃 (2 chars) is below the normal
    // threshold but is genuinely the pack name here.
    const keys = keyOf([
      rec('Q1', '[MC整合包发布:涅槃]  无神明渡我 我亦是神明', '墨言eclipse'),
      rec('Q2', '[整合包更新-涅槃v0.2]神吞降世，邪神投影，万魂幡！', '墨言eclipse'),
      rec('Q3', '[MC整合包发布]涅槃v0.1.6 [沉浸战斗/深度魔改/ARPG/咒镰双生]', '墨言eclipse'),
    ]);
    expect(new Set(Object.values(keys)).size).toBe(1);
  });

  it('does not let a transient word anchor just because it is 2 chars', () => {
    // The mirror risk of R7: 重生 / 高度 are update descriptors, not pack names.
    // Two DIFFERENT packs that both mention 重生 must stay apart.
    const keys = keyOf([
      rec('W1', '我的世界 冰火魔龙-重生 整合包发布！高版本冰火传说！', '一个小寂哦'),
      rec('W2', '我的世界 怪物大乱斗重生整合包发布！高版本矿石菌种！哥斯拉！', '一个小寂哦'),
      rec('W3', '我的世界 超变态钻石大陆 重生！整合包发布 努力存活50天！', '一个小寂哦'),
    ]);
    expect(new Set(Object.values(keys)).size).toBe(3);
  });

  it('records rejected candidate anchors for explainability', () => {
    // §15: a decision must be able to say not just "which anchor won" but "which
    // candidate anchors were refused, and under which rule".
    const d = groupBilibiliPacks([
      rec('K1', '《你好，新蒸程》整合包正式发布！航空学，voxy，独家地形', '叙利亚自爆民兵'),
      rec('K2', '《你好，新世代》整合包发布，voxy，机械动力6.0.8', '叙利亚自爆民兵'),
    ]);
    expect(d.size).toBe(2);
    const rejected = [...d.values()].some(
      (v) => (v.rejectedAnchors || []).some((r) => r.reason === 'name_slot_disagreement')
    );
    expect(rejected).toBe(true);
  });

  it('keeps shared-URL / same-QQ-group packs separate (grouping never reads them)', () => {
    // §10: download_links and qq_group are NOT inputs. Two records that share a
    // URL but are different packs must not merge, because the function cannot even
    // see the URL.
    const shared = { bvid: 'S1', title: '【整合包发布】命运齿轮 1.0', author: '明月庄主' };
    const other = { bvid: 'S2', title: '【整合包发布】月亮工厂MCF 2.0', author: '明月庄主' };
    const keys = keyOf([shared, other] as never);
    expect(keys.S1).not.toBe(keys.S2);
  });

  it('still merges a genuine same-pack series after the admissibility rules', () => {
    // Recall guard: the new vetoes must not break a legitimate same-pack series.
    const keys = keyOf([
      rec('M1', '【MC整合包更新】原神与机械冒险的时代v3.5.12版本更新——新增部分模组实机演示', '小兜兜呀_'),
      rec('M2', '【MC整合包更新】原神与机械冒险的时代v3.5.11.1小版本更新--优化物品视觉辨识度', '小兜兜呀_'),
      rec('M3', '【MC整合包发布】原神与机械冒险的时代--在方块世界体验提瓦特式的冒险', '小兜兜呀_'),
    ]);
    expect(new Set(Object.values(keys)).size).toBe(1);
  });

  it('still merges 懂嗎懂嗎 齿轮与腐肉 across bracketed changelog variants', () => {
    const keys = keyOf([
      rec('C1', 'MC大型末日整合包发布[齿轮与腐肉]枪械/机械动力/卓越前线/真菌感染/硬核模拟0.50更新日志', '懂嗎懂嗎'),
      rec('C2', 'MC版僵毁整合包/枪械/搜索/机动/载具/真菌/硬核模拟「齿轮与腐肉」0.46更新前瞻', '懂嗎懂嗎'),
      rec('C3', 'MC大型末日整合包[齿轮与腐肉]枪械/机械动力/卓越前线/真菌感染/硬核模拟我的世界0.21版本更新前瞻', '懂嗎懂嗎'),
    ]);
    expect(new Set(Object.values(keys)).size).toBe(1);
  });

  it('still merges Horizon 地平线 across version wording', () => {
    const keys = keyOf([
      rec('H1', '【MC整合包】地平线 Horizon v2.1.0 更新！全新的冒险体验', 'confectionaryqwq'),
      rec('H2', '【MC整合包】地平线 Horizon v1.2.0 正式发布！', 'confectionaryqwq'),
    ]);
    expect(new Set(Object.values(keys)).size).toBe(1);
  });
});

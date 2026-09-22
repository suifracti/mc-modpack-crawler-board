import { describe, it, expect } from 'vitest';
import { deriveLegacyHasServer, EnvironmentClaim } from '../src/domain/types';
import type { McmodStructuredItem } from '../src/platforms/mcmod/types';
import { mapStructuredMcmodToPack } from '../src/platforms/mcmod/mappers';
import { generateSparklineSvg } from '../src/platforms/mcmod/sparkline';
import { buildMcmodSearchText } from '../src/platforms/mcmod/selectors';
import {
  renderTitleCell,
  renderTrendCell,
  renderGrowthCell,
  renderVotesCell,
  renderEngageCell,
  renderTagsCell,
  renderModsCell,
  renderEnvironmentBadge,
} from '../src/platforms/mcmod/renderer';

function makeClaim(
  side: 'client' | 'server',
  status: 'required' | 'optional' | 'supported' | 'unsupported' | 'unknown',
  certainty: 'confirmed' | 'strong_inferred' | 'inferred' | 'weak_inferred' | 'unknown',
  evidenceType: 'platform_field' | 'file_name' | 'text_rule' | 'no_evidence' = 'no_evidence',
  evidenceText: string | null = null,
  sourceField: string | null = null,
  rawValue: unknown | null = null
): EnvironmentClaim {
  return { side, status, certainty, evidenceType, evidenceText, sourceField, rawValue };
}

describe('MCMod Environment Claims & deriveLegacyHasServer (Canonical Parity)', () => {
  it('covers the exact 10-point Canonical Legacy Bool truth table', () => {
    // 1. required + confirmed -> true
    expect(deriveLegacyHasServer([makeClaim('server', 'required', 'confirmed', 'platform_field')])).toBe(true);

    // 2. optional + confirmed -> true
    expect(deriveLegacyHasServer([makeClaim('server', 'optional', 'confirmed', 'platform_field')])).toBe(true);

    // 3. supported + confirmed -> true
    expect(deriveLegacyHasServer([makeClaim('server', 'supported', 'confirmed', 'platform_field')])).toBe(true);

    // 4. supported + strong_inferred -> true
    expect(deriveLegacyHasServer([makeClaim('server', 'supported', 'strong_inferred', 'file_name')])).toBe(true);

    // 5. supported + inferred -> true
    expect(deriveLegacyHasServer([makeClaim('server', 'supported', 'inferred', 'text_rule')])).toBe(true);

    // 6. supported + weak_inferred -> true
    expect(deriveLegacyHasServer([makeClaim('server', 'supported', 'weak_inferred', 'text_rule')])).toBe(true);

    // 7. unsupported + confirmed -> false
    expect(deriveLegacyHasServer([makeClaim('server', 'unsupported', 'confirmed', 'platform_field')])).toBe(false);

    // 8. unsupported + inferred -> false
    expect(deriveLegacyHasServer([makeClaim('server', 'unsupported', 'inferred', 'text_rule')])).toBe(false);

    // 9. unknown + unknown -> false
    expect(deriveLegacyHasServer([makeClaim('server', 'unknown', 'unknown', 'no_evidence')])).toBe(false);

    // 10. no claim -> false
    expect(deriveLegacyHasServer([])).toBe(false);
    expect(deriveLegacyHasServer(null)).toBe(false);
    expect(deriveLegacyHasServer(undefined)).toBe(false);
  });

  it('handles multiple server claims deterministically using certainty precedence', () => {
    // confirmed > strong_inferred > inferred > weak_inferred > unknown
    const claims1: EnvironmentClaim[] = [
      makeClaim('server', 'unsupported', 'inferred', 'text_rule'),
      makeClaim('server', 'supported', 'strong_inferred', 'file_name'),
    ];
    // strong_inferred (supported) wins over inferred (unsupported)
    expect(deriveLegacyHasServer(claims1)).toBe(true);

    const claims2: EnvironmentClaim[] = [
      makeClaim('server', 'supported', 'inferred', 'text_rule'),
      makeClaim('server', 'unsupported', 'confirmed', 'platform_field'),
    ];
    // confirmed (unsupported) wins over inferred (supported)
    expect(deriveLegacyHasServer(claims2)).toBe(false);
  });
});

describe('MCMod Structured Mapper', () => {
  const sampleDto: McmodStructuredItem = {
    mid: 12345,
    title: 'RLCraft Definitive Edition (RLCraft)',
    chineseName: 'RLCraft 决定版',
    englishName: 'RLCraft',
    formerTitles: ['旧版 RLCraft'],
    url: 'https://www.mcmod.cn/modpack/12345.html',
    author: 'Shivaxi',
    typeName: '魔改整合',
    moldId: '2',
    coverUrl: 'https://example.com/cover.jpg',
    views: 150000,
    score: 5,
    recommendations: 1200,
    favorites: 3500,
    commentsCount: 450,
    votes: {
      redVotes: 900,
      blackVotes: 100,
      redPercent: 90,
      blackPercent: 10,
    },
    trendStats: {
      lat: 600,
      max: 850,
      avg: 450.5,
      days: 90,
      t7: 12.5,
      t30: 25.0,
      t60: 45.0,
      tall: 120.0,
      score: 5,
      history7d: [100, 200, 300, 400, 500, 550, 600],
      trendValsStr: '100,200,600',
      trendDatesStr: '2026-07-01,2026-08-01,2026-09-01',
    },
    tags: ['硬核', 'RPG', '冒险'],
    categories: ['生存', '冒险'],
    mcVersions: ['1.12.2'],
    loaders: ['Forge'],
    includedModsCount: 140,
    modCategories: [
      { categoryKey: 'cat0', categoryName: '核心/前置', count: 20 },
      { categoryKey: 'cat1', categoryName: '冒险/探索', count: 50 },
    ],
    previewMods: [
      { name: 'JEI', title: 'Just Enough Items', version: '4.15.0', url: 'https://www.mcmod.cn/class/284.html', categoryKey: 'cat0', categoryName: '核心/前置' },
    ],
    includedModNames: ['JEI', 'Lycanites Mobs', 'Ice and Fire'],
    modCategorySearch: '核心/前置, 冒险/探索',
    trendPoints: [
      { date: '2026-07-01', viewsDelta: 100 },
      { date: '2026-08-01', viewsDelta: 200 },
      { date: '2026-09-01', viewsDelta: 600 },
    ],
    environmentClaims: [
      makeClaim('client', 'unknown', 'unknown', 'no_evidence'),
      makeClaim('server', 'supported', 'inferred', 'text_rule', '含服务端配置', 'description', '含服务端配置'),
    ],
  };

  it('maps structured item into McmodPack domain model', () => {
    const pack = mapStructuredMcmodToPack(sampleDto);
    expect(pack.id).toBe('mcmod:12345');
    expect(pack.platform).toBe('mcmod');
    expect(pack.mid).toBe(12345);
    expect(pack.hasServer).toBe(true);
    expect(pack.serverClaim?.status).toBe('supported');
    expect(pack.chineseName).toBe('RLCraft 决定版');
    expect(pack.views).toBe(150000);
    expect(pack.trendStats.score).toBe(5);
  });

  it('builds comprehensive search document including titles, aliases, mods, and categories', () => {
    const searchDoc = buildMcmodSearchText(sampleDto);
    expect(searchDoc).toContain('rlcraft');
    expect(searchDoc).toContain('决定版');
    expect(searchDoc).toContain('旧版 rlcraft');
    expect(searchDoc).toContain('shivaxi');
    expect(searchDoc).toContain('1.12.2');
    expect(searchDoc).toContain('jei');
    expect(searchDoc).toContain('lycanites mobs');
  });
});

describe('MCMod Sparkline Vector Generator', () => {
  it('generates compact SVG path from trend points', () => {
    const vals = [10, 25, 40, 30, 60];
    const svg = generateSparklineSvg(vals);
    expect(svg).toContain('<svg class="sparkline-svg"');
    expect(svg).toContain('viewBox="0 0 100 24"');
    expect(svg).toContain('<path d="M 0 ');
    expect(svg).toContain('fill="rgba(var(--primary-rgb), 0.1)"');
  });

  it('returns empty string when values are fewer than 2', () => {
    expect(generateSparklineSvg([])).toBe('');
    expect(generateSparklineSvg([100])).toBe('');
    expect(generateSparklineSvg(null)).toBe('');
  });
});

describe('MCMod TypeScript Cell Renderers', () => {
  const sampleDto: McmodStructuredItem = {
    mid: 999,
    title: '机械动力：星辰大海 (Create: Cosmos)',
    chineseName: '机械动力：星辰大海',
    englishName: 'Create: Cosmos',
    formerTitles: [],
    url: 'https://www.mcmod.cn/modpack/999.html',
    author: 'DevTeam',
    typeName: '科技整合',
    moldId: '2',
    coverUrl: 'http://example.com/icon.png',
    views: 85000,
    score: 4,
    recommendations: 500,
    favorites: 1200,
    commentsCount: 95,
    votes: {
      redVotes: 400,
      blackVotes: 50,
      redPercent: 89,
      blackPercent: 11,
    },
    trendStats: {
      lat: 250,
      max: 400,
      avg: 210,
      days: 60,
      t7: 15.2,
      t30: -5.1,
      t60: 30.0,
      tall: 55.0,
      score: 4,
      history7d: [100, 120, 150, 180, 200, 220, 250],
      trendValsStr: '100,250',
      trendDatesStr: '2026-08-01,2026-09-01',
    },
    tags: ['科技', '探索'],
    categories: ['科技', '冒险'],
    mcVersions: ['1.20.1'],
    loaders: ['Forge'],
    includedModsCount: 65,
    modCategories: [
      { categoryKey: 'cat0', categoryName: '科技', count: 30 },
      { categoryKey: 'cat1', categoryName: '辅助', count: 35 },
    ],
    previewMods: [
      { name: 'Create', title: '机械动力', version: '0.5.1', url: 'https://www.mcmod.cn/class/2422.html', categoryKey: 'cat0', categoryName: '科技' },
    ],
    includedModNames: ['Create', 'JEI'],
    modCategorySearch: '科技, 辅助',
    trendPoints: [
      { date: '2026-08-01', viewsDelta: 100 },
      { date: '2026-09-01', viewsDelta: 250 },
    ],
    environmentClaims: [
      makeClaim('client', 'unknown', 'unknown', 'no_evidence'),
      makeClaim('server', 'supported', 'inferred', 'text_rule', '含服务端', 'description', '含服务端'),
    ],
  };

  it('renderTitleCell produces valid title, thumbnail, and link HTML', () => {
    const html = renderTitleCell(sampleDto);
    expect(html).toContain('data-mid="999"');
    expect(html).toContain('机械动力：星辰大海');
    expect(html).toContain('Create: Cosmos');
    expect(html).toContain('8.50万');
    expect(html).toContain('科技整合');
  });

  it('renderTrendCell produces score badge and sparkline SVG', () => {
    const html = renderTrendCell(sampleDto);
    expect(html).toContain('trend-consolidated-cell');
    expect(html).toContain('<b>4</b>');
    expect(html).toContain('最新: 250');
    expect(html).toContain('sparkline-svg');
  });

  it('renderGrowthCell produces formatted growth percentages', () => {
    const html = renderGrowthCell(sampleDto);
    expect(html).toContain('7日: +15%');
    expect(html).toContain('30日: -5%');
    expect(html).toContain('td-up');
    expect(html).toContain('td-down');
  });

  it('renderVotesCell produces vote counts and ratio bar', () => {
    const html = renderVotesCell(sampleDto);
    expect(html).toContain('450 票');
    expect(html).toContain('89% 红');
    expect(html).toContain('width: 89%');
    expect(html).toContain('黑票: 50');
  });

  it('renderEngageCell produces engagement counts and comment button trigger', () => {
    const html = renderEngageCell(sampleDto);
    expect(html).toContain('<b>500</b><em>推</em>');
    expect(html).toContain('<b>1200</b><em>藏</em>');
    expect(html).toContain('<b>95</b><em>评</em>');
    expect(html).toContain('engage-comment-trigger');
  });

  it('renderTagsCell produces category badges', () => {
    const html = renderTagsCell(sampleDto);
    expect(html).toContain('tag-cat');
    expect(html).toContain('科技');
    expect(html).toContain('冒险');
  });

  it('renderModsCell produces category summary chips and preview list', () => {
    const html = renderModsCell(sampleDto);
    expect(html).toContain('包含模组 <b>65</b>');
    expect(html).toContain('mod-summary-chip');
    expect(html).toContain('科技<b>30</b>');
    expect(html).toContain('辅助<b>35</b>');
    expect(html).toContain('Create');
    expect(html).toContain('data-loaded="0"');
  });

  it('renderEnvironmentBadge produces server badge if supported', () => {
    const html = renderEnvironmentBadge(sampleDto);
    expect(html).toContain('✔ 有服务端运行线索');
  });
});

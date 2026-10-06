import { describe, it, expect } from 'vitest';
import {
  extractPackFeatures,
  matchFeatures,
  findCrossPlatformAssociations,
  renderCardLinkageCapsule,
  renderDrawerLinkageSection,
} from '../src/domain/crossPlatformLinkage';
import type { DesktopRecord } from '../src/desktopShell-v2';

describe('crossPlatformLinkage', () => {
  it('extracts acronyms, English tokens and Chinese keywords from complex modpack titles', () => {
    const mcmodFeatures = extractPackFeatures('[NFWC]脆骨症 (No Flesh Within Chest)');
    expect(mcmodFeatures.acronyms).toContain('NFWC');
    expect(mcmodFeatures.chineseKeywords).toContain('脆骨症');
    expect(mcmodFeatures.englishKeywords).toContain('no flesh within chest');

    const bbsmcFeatures = extractPackFeatures('脆骨症 2 - No Flesh Within Chest 2');
    expect(bbsmcFeatures.chineseKeywords).toContain('脆骨症');
    expect(bbsmcFeatures.englishKeywords).toContain('no flesh within chest');

    const cfFeatures = extractPackFeatures('No Flesh Within Chest  [NFWC] (Unofficial)');
    expect(cfFeatures.acronyms).toContain('NFWC');
    expect(cfFeatures.englishKeywords).toContain('no flesh within chest');
  });

  it('matches across platforms using extracted features', () => {
    const features = extractPackFeatures('[NFWC]脆骨症 (No Flesh Within Chest)');
    expect(matchFeatures('脆骨症 2 - No Flesh Within Chest 2', features)).toBe(true);
    expect(matchFeatures('No Flesh Within Chest [NFWC]', features)).toBe(true);
    expect(matchFeatures('【MC整合包发布】另类的脆骨症-渎圣织罪0.5版本高度魔改', features)).toBe(true);
    expect(matchFeatures('暮色森林探险记', features)).toBe(false);
  });

  it('finds cross-platform associations among records and bilibili groups', () => {
    const mcmodRecord: DesktopRecord = {
      id: 'mcmod:123',
      platform: 'mcmod',
      sourceId: '123',
      title: '[NFWC]脆骨症 (No Flesh Within Chest)',
      author: '作者A',
      url: 'https://www.mcmod.cn/modpack/123.html',
      sourceIdOrigin: 'source',
      summary: '硬核生存整合包',
      versions: ['1.19.2'],
      loaders: ['Forge'],
      categories: ['生存'],
      updatedAt: '2024-12-01',
      coverUrl: '',
      environment: { status: 'supported', certainty: 'high', label: '服务端', sourceField: null },
      releases: [],
      raw: {},
      searchText: '',
      evidence: [],
      packVersion: '1.0.2',
    };

    const bbsmcRecord: DesktopRecord = {
      id: 'bbsmc:456',
      platform: 'bbsmc',
      sourceId: '456',
      title: '脆骨症 2 - No Flesh Within Chest 2',
      author: '汉化者B',
      url: 'https://bbsmc.net/thread-456.html',
      sourceIdOrigin: 'source',
      summary: '国内汉化与网盘分享',
      versions: ['1.19.2'],
      loaders: ['Forge'],
      categories: ['生存'],
      updatedAt: '2024-12-05',
      coverUrl: '',
      environment: { status: 'supported', certainty: 'high', label: '服务端', sourceField: null },
      releases: [],
      raw: {},
      searchText: '',
      evidence: [],
      packVersion: '2.0.0',
    };

    const biliGroups = [
      {
        key: '脆骨症',
        primaryTitle: '脆骨症视频',
        items: [
          {
            id: 'bili-1',
            bvid: 'BV123456',
            title: '【MC整合包发布】另类的脆骨症-渎圣织罪0.5版本',
            author: 'UP主小王',
            url: 'https://www.bilibili.com/video/BV123456',
            views: 12000,
            pub_time: '2024-12-10',
          },
        ] as any,
      },
    ];

    const result = findCrossPlatformAssociations(mcmodRecord, [mcmodRecord, bbsmcRecord], biliGroups as any);
    expect(result.totalMatches).toBe(2);
    expect(result.links.length).toBe(1);
    expect(result.links[0].platform).toBe('bbsmc');
    expect(result.biliVideos.length).toBe(1);
    expect(result.biliVideos[0].bvid).toBe('BV123456');

    // Test capsule render
    const capsuleHtml = renderCardLinkageCapsule(result);
    expect(capsuleHtml).toContain('全网联动');
    expect(capsuleHtml).toContain('B站 (1)');
    expect(capsuleHtml).toContain('论坛/网盘');

    // Test drawer section render
    const drawerHtml = renderDrawerLinkageSection(result, mcmodRecord);
    expect(drawerHtml).toContain('全网多平台关联生态');
    expect(drawerHtml).toContain('BBSMC 论坛');
    expect(drawerHtml).toContain('Bilibili 关联汉化与实况视频');
  });
});

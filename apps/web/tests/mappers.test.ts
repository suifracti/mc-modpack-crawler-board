import { describe, it, expect } from 'vitest';
import {
  mapLegacyMcmodToPack,
  mapLegacyBilibiliToPack,
  mapLegacyBbsmcToPack,
  mapLegacyXyebbsToPack,
  mapLegacyModrinthToPack,
  mapLegacyCurseforgeToPack,
} from '../src/domain/mappers';
import type { LegacyMcmodRow } from '../src/types/legacy/mcmod';
import type { LegacyBilibiliItem } from '../src/types/legacy/bilibili';
import type { LegacyBbsmcItem } from '../src/types/legacy/bbsmc';
import type { LegacyXyebbsItem } from '../src/types/legacy/xyebbs';
import type { LegacyModrinthItem } from '../src/types/legacy/modrinth';
import type { LegacyCurseforgeItem } from '../src/types/legacy/curseforge';

describe('Legacy Sidecar DTO Mappers', () => {
  it('maps MCMod legacy row correctly', () => {
    const row: LegacyMcmodRow = {
      mid: 123,
      c0: '1',
      c1: '<a href="/modpack/123.html">Test MCMod Pack</a>',
      c2: '冒险, 魔法',
      c3: '5,000',
      c4: '9.5',
      c5: '120',
      c6: '30',
      title: 'Test MCMod Pack',
      views_n: 5000,
      score_n: 9.5,
      has_server: true,
      mc_version: '1.20.1',
      category_search: '冒险, 魔法',
    };

    const pack = mapLegacyMcmodToPack(row);
    expect(pack.id).toBe('mcmod:123');
    expect(pack.platform).toBe('mcmod');
    expect(pack.title).toBe('Test MCMod Pack');
    expect(pack.views).toBe(5000);
    expect(pack.score).toBe(9.5);
    expect(pack.hasServer).toBe(true);
    expect(pack.mcVersions).toEqual(['1.20.1']);
    expect(pack.categories).toEqual(['冒险', '魔法']);
  });

  it('maps Bilibili legacy item correctly', () => {
    const item: LegacyBilibiliItem = {
      bvid: 'BV1xx411c7mD',
      title: 'Bili Modpack Showcase',
      author: 'Up主小明',
      url: 'https://www.bilibili.com/video/BV1xx411c7mD',
      views: 24000,
      danmaku: 500,
      likes: 1500,
      has_server: true,
      download_links: [{ pan_name: '百度网盘', url: 'http://pan.baidu.com/s/123' }],
      releases: [
        {
          version_id: 'v1.0',
          version_number: '1.0.0',
          mc_versions: ['1.20.1'],
          download_links: [{ pan_name: '百度网盘', url: 'http://pan.baidu.com/s/123' }],
        },
      ],
    };

    const pack = mapLegacyBilibiliToPack(item);
    expect(pack.id).toBe('bilibili:BV1xx411c7mD');
    expect(pack.platform).toBe('bilibili');
    expect(pack.title).toBe('Bili Modpack Showcase');
    expect(pack.author).toBe('Up主小明');
    expect(pack.views).toBe(24000);
    expect(pack.likes).toBe(1500);
    expect(pack.hasServer).toBe(true);
    expect(pack.downloadLinks.length).toBe(1);
    expect(pack.downloadLinks[0].url).toBe('http://pan.baidu.com/s/123');
    expect(pack.releases.length).toBe(1);
  });

  it('maps BBSMC and XYEBBS items', () => {
    const bbsmcItem: LegacyBbsmcItem = {
      project_id: 8888,
      title: 'BBSMC Awesome Pack',
      author: 'Steve',
      url: 'https://www.bbsmc.com/thread-8888-1-1.html',
      views: 1200,
      downloads: 300,
      replies: 45,
      has_server: false,
      mc_versions: ['1.16.5'],
      loaders: ['Fabric'],
      releases: [],
    };
    const packBbsmc = mapLegacyBbsmcToPack(bbsmcItem);
    expect(packBbsmc.platform).toBe('bbsmc');
    expect(packBbsmc.id).toBe('bbsmc:8888');
    expect(packBbsmc.title).toBe('BBSMC Awesome Pack');
    expect(packBbsmc.downloads).toBe(300);

    const xyebbsItem: LegacyXyebbsItem = {
      project_id: 9999,
      title: 'XYEBBS Pack',
      author: 'Alex',
      url: 'https://www.xyebbs.com/thread-9999-1-1.html',
      views: 3400,
      downloads: 800,
      replies: 80,
      has_server: true,
      mc_versions: ['1.20.1'],
      loaders: ['NeoForge'],
      releases: [],
    };
    const packXyebbs = mapLegacyXyebbsToPack(xyebbsItem);
    expect(packXyebbs.platform).toBe('xyebbs');
    expect(packXyebbs.id).toBe('xyebbs:9999');
    expect(packXyebbs.loaders).toEqual(['NeoForge']);
    expect(packXyebbs.hasServer).toBe(true);
  });

  it('maps Modrinth and CurseForge items', () => {
    const mr: LegacyModrinthItem = {
      project_id: 'mr_pack_1',
      slug: 'mr-pack',
      title: 'Modrinth Fast Pack',
      author: 'Creator',
      url: 'https://modrinth.com/modpack/mr-pack',
      downloads: 99999,
      followers: 1200,
      has_server: true,
      client_side: 'required',
      server_side: 'optional',
      mc_versions: ['1.20.1'],
      loaders: ['fabric', 'quilt'],
      releases: [],
    };
    const packMr = mapLegacyModrinthToPack(mr);
    expect(packMr.platform).toBe('modrinth');
    expect(packMr.id).toBe('modrinth:mr_pack_1');
    expect(packMr.downloads).toBe(99999);
    expect(packMr.hasServer).toBe(true);

    const cf: LegacyCurseforgeItem = {
      project_id: 777777,
      name: 'CurseForge Big Pack',
      title: 'CurseForge Big Pack',
      slug: 'cf-pack',
      author: 'CFDev',
      url: 'https://www.curseforge.com/minecraft/modpacks/cf-pack',
      downloads: 150000,
      has_server: true,
      mc_versions: ['1.12.2'],
      loaders: ['Forge'],
      releases: [],
    };
    const packCf = mapLegacyCurseforgeToPack(cf);
    expect(packCf.platform).toBe('curseforge');
    expect(packCf.id).toBe('curseforge:777777');
    expect(packCf.downloads).toBe(150000);
    expect(packCf.author).toBe('CFDev');
  });
});

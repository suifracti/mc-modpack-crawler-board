import { describe, it, expect } from 'vitest';
import { renderBiliGroupedCard, renderBiliFlatCard } from '../src/platforms/bilibili/renderer';
import { renderBbsmcCard } from '../src/platforms/bbsmc/renderer';
import { renderXyebbsCard } from '../src/platforms/xyebbs/renderer';
import { renderModrinthCard } from '../src/platforms/modrinth/renderer';
import { renderCurseforgeCard } from '../src/platforms/curseforge/renderer';
import { filterBilibiliGroupsByPersonalStatus, getDesktopSearchPlaceholder, renderPackVersionDetail } from '../src/desktopShell';
import type { BiliGroup } from '../src/platforms/bilibili/renderer';
import type { BilibiliPack } from '../src/types/legacy/bilibili';
import type { BbsmcPack } from '../src/types/legacy/bbsmc';
import type { XyebbsPack } from '../src/types/legacy/xyebbs';
import type { ModrinthPack } from '../src/types/legacy/modrinth';
import type { CurseforgePack } from '../src/types/legacy/curseforge';

describe('Platform Card Renderers', () => {
  it('renders the MCMod pack version separately and accepts old missing-field records', () => {
    expect(renderPackVersionDetail({ platform: 'mcmod', packVersion: '1.2.3' }))
      .toContain('<dt>整合包版本名</dt><dd>1.2.3</dd>');
    expect(renderPackVersionDetail({ platform: 'mcmod' })).toContain('未知（本地数据未提供）');
    expect(renderPackVersionDetail({ platform: 'mcmod', packVersion: '<img>' })).toContain('&lt;img&gt;');
    expect(renderPackVersionDetail({ platform: 'bilibili', packVersion: '1.2.3' })).toBe('');
  });
  it('renders Bilibili cards (grouped and flat)', () => {
    const p: BilibiliPack = {
      bvid: 'BV1test',
      title: 'B站测试包',
      author: '测试UP',
      url: 'https://bilibili.com/video/BV1test',
      views: 12000,
      danmaku: 500,
      likes: 1500,
      coins: 300,
      favorites: 800,
      reply: 100,
      share: 50,
      has_server: true,
      has_group_version: true,
      group_version_note: '群内更新',
      qq_group: '123456',
      mc_version: '1.20.1',
      loaders: ['Forge'],
      categories: ['冒险'],
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      download_links: [{ name: '百度网盘', url: 'https://pan.baidu.com/123' } as any],
    };

    const flatHtml = renderBiliFlatCard(p);
    expect(flatHtml).toContain('bili-pack-card');
    expect(flatHtml).toContain('B站测试包');
    expect(flatHtml).toContain('有服务端运行线索');
    expect(flatHtml).toContain('1.2万');

    const groupedHtml = renderBiliGroupedCard({
      key: 'test-key',
      items: [p],
      allVersions: new Set(['1.20.1']),
      allLoaders: new Set(['Forge']),
      allCategories: new Set(['冒险']),
      allGroups: new Set(['123456']),
      allLinks: [{ name: '百度网盘', url: 'https://pan.baidu.com/123' }],
      totalViews: 12000,
      totalLikes: 1500,
      totalCoins: 300,
      totalFavs: 800,
      totalDanmaku: 500,
      totalReply: 100,
      totalShare: 50,
      latestTimestamp: 1700000000,
      latestPubTime: '2026-09-01',
      has_server: true,
    });
    expect(groupedHtml).toContain('bili-pack-card');
    expect(groupedHtml).toContain('data-key="test-key"');
  });

  it('keeps every queried Bilibili member when a personal filter matches an older video', () => {
    const group = {
      key: '测试作者::测试整合包',
      items: [{ bvid: 'A', title: '测试整合包 A' }, { bvid: 'B', title: '测试整合包 B' }],
    } as unknown as BiliGroup;
    const personalLibrary = {
      'bilibili:A': { favorite: true, wantToPlay: false, played: false, rating: 4, note: '保留 A', updatedAt: null },
    };
    const filtered = filterBilibiliGroupsByPersonalStatus([group], personalLibrary, 'favorite');
    expect(filtered).toHaveLength(1);
    expect(filtered[0].items.map((item) => item.bvid)).toEqual(['A', 'B']);
  });

  it('describes search coverage by platform instead of promising MCMod fields everywhere', () => {
    expect(getDesktopSearchPlaceholder('all')).not.toContain('模组名');
    expect(getDesktopSearchPlaceholder('all')).toContain('平台已有字段');
    expect(getDesktopSearchPlaceholder('mcmod')).toContain('模组名');
    expect(getDesktopSearchPlaceholder('bilibili')).not.toContain('模组名');
  });

  it('renders BBSMC card', () => {
    const p: BbsmcPack = {
      project_id: 10,
      title: 'BBSMC 示范包',
      author: 'MC大师',
      url: 'https://bbsmc.net/10',
      downloads: 8000,
      followers: 200,
      replies: 50,
      views: 15000,
      has_server: true,
      mc_version: '1.19.2',
      loaders: ['Fabric'],
      categories: ['科技'],
      download_links: [{ name: '官方直链', url: 'https://bbsmc.net/dl/10.mrpack' }],
    };

    const html = renderBbsmcCard(p);
    expect(html).toContain('bbsmc-pack-card');
    expect(html).toContain('BBSMC 示范包');
    expect(html).toContain('MC大师');
    expect(html).toContain('有服务端运行线索');
  });

  it('renders XYEBBS card', () => {
    const p: XyebbsPack = {
      project_id: 20,
      title: 'XYEBBS 模组包',
      author: '创作者X',
      url: 'https://xyebbs.com/20',
      downloads: 4000,
      views: 12000,
      replies: 10,
      has_server: false,
      mc_version: '1.16.5',
      loaders: ['Forge'],
      download_links: [{ name: '夸克网盘', url: 'https://pan.quark.cn/s/1' }],
    };

    const html = renderXyebbsCard(p);
    expect(html).toContain('xyebbs-pack-card');
    expect(html).toContain('XYEBBS 模组包');
    expect(html).toContain('创作者X');
  });

  it('renders Modrinth card', () => {
    const p: ModrinthPack = {
      project_id: 'm-abc',
      slug: 'fabulous-pack',
      title: 'Fabulous Modpack',
      author: 'ModderM',
      url: 'https://modrinth.com/modpack/fabulous-pack',
      downloads: 25000,
      followers: 1200,
      has_server: true,
      env_display: '客户端和服务端',
      mc_version: '1.20.1',
      loaders: ['Fabric'],
      categories: ['optimization', 'technology'],
    };

    const html = renderModrinthCard(p);
    expect(html).toContain('modrinth-pack-card');
    expect(html).toContain('Fabulous Modpack');
    expect(html).toContain('2.5万');
    expect(html).toContain('性能优化');
  });

  it('renders CurseForge card', () => {
    const p: CurseforgePack = {
      project_id: 999,
      slug: 'awesome-cf',
      title: 'Awesome CF Pack',
      author: 'AuthorCF',
      url: 'https://curseforge.com/minecraft/modpacks/awesome-cf',
      downloads: 50000,
      followers: 3000,
      has_server: true,
      mc_version: '1.12.2',
      loaders: ['Forge'],
      categories: ['Tech', 'Quests'],
    };

    const html = renderCurseforgeCard(p);
    expect(html).toContain('curseforge-pack-card');
    expect(html).toContain('Awesome CF Pack');
    expect(html).toContain('5.0万');
    expect(html).toContain('科技');
  });
});

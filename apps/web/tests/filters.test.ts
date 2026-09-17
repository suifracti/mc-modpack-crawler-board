import { describe, it, expect } from 'vitest';
import {
  matchCategories,
  matchVersion,
  matchLoader,
  matchServerOnly,
  matchPan,
  matchDateRange,
  filterStore,
  filterBilibiliPacks,
  filterModrinthPacks,
  filterCurseforgePacks,
  getCategoryLabel,
} from '../src/filters';
import type { BilibiliPack } from '../src/types/legacy/bilibili';
import type { ModrinthPack } from '../src/types/legacy/modrinth';
import type { CurseforgePack } from '../src/types/legacy/curseforge';

describe('Filter Subsystem', () => {
  describe('Pure Predicates', () => {
    it('matches categories in union and exclusion modes', () => {
      expect(matchCategories([], ['科技', '魔法'])).toBe(true);
      expect(matchCategories(['科技'], ['科技', '魔法'])).toBe(true);
      expect(matchCategories(['冒险'], ['科技', '魔法'])).toBe(false);

      // Exclusion mode
      expect(matchCategories(['科技'], ['科技', '魔法'], true)).toBe(false);
      expect(matchCategories(['冒险'], ['科技', '魔法'], true)).toBe(true);
    });

    it('matches version across primary and all_versions', () => {
      expect(matchVersion('', '1.20.1', ['1.20.1'])).toBe(true);
      expect(matchVersion('1.20.1', '1.20.1', [])).toBe(true);
      expect(matchVersion('1.20', '1.20.1', [])).toBe(true);
      expect(matchVersion('1.19.2', '1.20.1', ['1.19.2', '1.20.1'])).toBe(true);
      expect(matchVersion('1.16.5', '1.20.1', ['1.19.2'])).toBe(false);
    });

    it('matches loader correctly', () => {
      expect(matchLoader('', ['Forge', 'Fabric'])).toBe(true);
      expect(matchLoader('Fabric', ['Forge', 'Fabric'])).toBe(true);
      expect(matchLoader('Quilt', ['Forge', 'Fabric'])).toBe(false);
    });

    it('matches serverOnly correctly', () => {
      expect(matchServerOnly(false, false)).toBe(true);
      expect(matchServerOnly(false, true)).toBe(true);
      expect(matchServerOnly(true, true)).toBe(true);
      expect(matchServerOnly(true, false)).toBe(false);
    });

    it('matches pan links correctly', () => {
      const links = [
        { name: '百度网盘', url: 'https://pan.baidu.com/s/123' },
        { name: '夸克网盘', url: 'https://pan.quark.cn/s/456' },
      ];
      expect(matchPan('百度', links)).toBe(true);
      expect(matchPan('夸克', links)).toBe(true);
      expect(matchPan('123', links)).toBe(false);
      expect(matchPan('official', links, 'https://example.com')).toBe(true);
    });

    it('matches date range filters', () => {
      const nowSec = 1700000000;
      expect(matchDateRange('7d', nowSec - 3 * 86400, '2026-09-14', nowSec)).toBe(true);
      expect(matchDateRange('7d', nowSec - 10 * 86400, '2026-09-07', nowSec)).toBe(false);
      expect(matchDateRange('2026', undefined, '2026-09-14')).toBe(true);
      expect(matchDateRange('2025', undefined, '2026-09-14')).toBe(false);
    });
  });

  describe('Platform Filter Pipelines', () => {
    it('filters Bilibili packs with combined criteria', () => {
      const packs: BilibiliPack[] = [
        {
          bvid: 'BV1',
          title: '机械动力整合包',
          author: 'UP1',
          url: 'https://bilibili.com/1',
          views: 1000,
          danmaku: 10,
          likes: 20,
          has_server: true,
          mc_version: '1.20.1',
          loaders: ['Forge'],
          categories: ['科技'],
        },
        {
          bvid: 'BV2',
          title: '魔法冒险',
          author: 'UP2',
          url: 'https://bilibili.com/2',
          views: 500,
          danmaku: 5,
          likes: 10,
          has_server: false,
          mc_version: '1.19.2',
          loaders: ['Fabric'],
          categories: ['魔法'],
        },
      ];

      const resServer = filterBilibiliPacks(packs, { serverOnly: true });
      expect(resServer.length).toBe(1);
      expect(resServer[0].bvid).toBe('BV1');

      const resLoader = filterBilibiliPacks(packs, { loader: 'Fabric' });
      expect(resLoader.length).toBe(1);
      expect(resLoader[0].bvid).toBe('BV2');
    });

    it('translates Modrinth and CurseForge category labels', () => {
      expect(getCategoryLabel('multiplayer')).toBe('多人游戏');
      expect(getCategoryLabel('Exploration')).toBe('探索');
      expect(getCategoryLabel('unknown_custom')).toBe('unknown_custom');
    });

    it('filters Modrinth and Curseforge packs correctly', () => {
      const modrinthPacks: ModrinthPack[] = [
        {
          project_id: 'm1',
          title: 'Fabric Performance',
          slug: 'fab-perf',
          author: 'Dev',
          url: 'https://modrinth.com/1',
          downloads: 500,
          has_server: true,
          loaders: ['Fabric'],
          categories: ['optimization'],
        },
      ];
      expect(filterModrinthPacks(modrinthPacks, { loader: 'Fabric' }).length).toBe(1);
      expect(filterModrinthPacks(modrinthPacks, { loader: 'Forge' }).length).toBe(0);

      const cursePacks: CurseforgePack[] = [
        {
          project_id: 1,
          title: 'CurseForge RLCraft',
          slug: 'rlcraft',
          author: 'Shivaxi',
          url: 'https://curseforge.com/1',
          downloads: 10000,
          has_server: true,
          loaders: ['Forge'],
        },
      ];
      expect(filterCurseforgePacks(cursePacks, { searchQuery: 'RLCraft' }).length).toBe(1);
      expect(filterCurseforgePacks(cursePacks, { searchQuery: 'Stoneblock' }).length).toBe(0);
    });
  });

  describe('FilterStore', () => {
    it('stores and updates criteria per platform', () => {
      filterStore.setCriteria('modrinth', { loader: 'Fabric', serverOnly: true });
      const crit = filterStore.getCriteria('modrinth');
      expect(crit.loader).toBe('Fabric');
      expect(crit.serverOnly).toBe(true);

      filterStore.reset('modrinth');
      expect(filterStore.getCriteria('modrinth')).toEqual({});
    });
  });
});

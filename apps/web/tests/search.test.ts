import { describe, it, expect } from 'vitest';
import {
  normalizeSearchKeyword,
  parseSearchQuery,
  matchDocument,
  filterItemsWithSearch,
  searchCoordinator,
  buildMcmodSearchDocument,
  buildBilibiliSearchDocument,
  buildBbsmcSearchDocument,
  buildXyebbsSearchDocument,
  buildModrinthSearchDocument,
  buildCurseforgeSearchDocument,
} from '../src/search';
import type { McmodStructuredItem } from '../src/platforms/mcmod/types';
import type { BilibiliPack } from '../src/types/legacy/bilibili';
import type { BbsmcPack } from '../src/types/legacy/bbsmc';
import type { XyebbsPack } from '../src/types/legacy/xyebbs';
import type { ModrinthPack } from '../src/types/legacy/modrinth';
import type { CurseforgePack } from '../src/types/legacy/curseforge';

describe('Search Subsystem', () => {
  describe('Query Parser', () => {
    it('normalizes keyword by trimming and lowercasing', () => {
      expect(normalizeSearchKeyword('  RLCraft  ')).toBe('rlcraft');
      expect(normalizeSearchKeyword(null)).toBe('');
      expect(normalizeSearchKeyword(undefined)).toBe('');
    });

    it('parses queries into terms and preserves scope', () => {
      const q = parseSearchQuery('  GregTech   New   Horizons  ', 'title');
      expect(q.isEmpty).toBe(false);
      expect(q.terms).toEqual(['gregtech', 'new', 'horizons']);
      expect(q.scope).toBe('title');
    });

    it('handles empty query gracefully', () => {
      const q = parseSearchQuery('');
      expect(q.isEmpty).toBe(true);
      expect(q.terms).toEqual([]);
    });
  });

  describe('Search Document Builders & Engine', () => {
    const mockMcmod: McmodStructuredItem = {
      mid: 100,
      title: 'RLCraft Hardcore Survival',
      chineseName: '真实生存',
      englishName: 'RLCraft',
      formerTitles: ['Roguelike Dungeons'],
      url: 'https://www.mcmod.cn/modpack/100.html',
      author: 'Shivaxi',
      typeName: '魔改整合',
      moldId: '2',
      coverUrl: '',
      views: 100000,
      score: 5,
      recommendations: 500,
      favorites: 800,
      commentsCount: 200,
      votes: { redVotes: 900, blackVotes: 100, redPercent: 90, blackPercent: 10 },
      trendStats: {
        lat: 100,
        max: 500,
        avg: 200,
        days: 30,
        t7: 15,
        t30: 50,
        t60: 80,
        tall: 100,
        score: 5,
        trendValsStr: '1,2,3',
        trendDatesStr: '2026-09-01',
      },
      tags: ['生存', '冒险'],
      categories: ['硬核', '冒险'],
      mcVersions: ['1.12.2'],
      loaders: ['Forge'],
      includedModsCount: 160,
      modCategories: [],
      previewMods: [],
      modSearchText: 'ice and fire, lycanites mobs, tough as nails',
      modCategorySearch: '冒险',
      environmentClaims: [],
    };

    it('matches MCMod items across title, alias, and mods', () => {
      const doc = buildMcmodSearchDocument(mockMcmod);

      // Match title
      const resTitle = matchDocument(doc, parseSearchQuery('RLCraft'));
      expect(resTitle.matches).toBe(true);
      expect(resTitle.matchedFields).toContain('title');

      // Match former title
      const resFormer = matchDocument(doc, parseSearchQuery('Roguelike'));
      expect(resFormer.matches).toBe(true);

      // Match mod
      const resMod = matchDocument(doc, parseSearchQuery('lycanites'));
      expect(resMod.matches).toBe(true);

      // Match scoped
      const resScopedPass = matchDocument(doc, parseSearchQuery('RLCraft', 'title'));
      expect(resScopedPass.matches).toBe(true);

      const resScopedFail = matchDocument(doc, parseSearchQuery('lycanites', 'title'));
      expect(resScopedFail.matches).toBe(false);
    });

    it('builds documents for all platforms and filters collections', () => {
      const bili: BilibiliPack = {
        bvid: 'BV123',
        title: '机械动力：星辰工坊',
        author: '测试UP',
        url: 'https://bilibili.com/video/BV123',
        views: 5000,
        danmaku: 200,
        likes: 300,
        has_server: true,
        mc_version: '1.20.1',
        loaders: ['Forge'],
        categories: ['科技'],
      };

      const bbsmc: BbsmcPack = {
        project_id: 1,
        title: 'BBSMC 冒险之旅',
        author: '作者A',
        url: 'https://bbsmc.net/1',
        downloads: 1000,
        replies: 50,
        views: 2000,
        has_server: false,
        mc_version: '1.19.2',
      };

      const xyebbs: XyebbsPack = {
        project_id: 2,
        title: 'XYEBBS 魔法王国',
        author: '作者B',
        url: 'https://xyebbs.com/2',
        downloads: 300,
        replies: 20,
        views: 500,
        has_server: true,
        mc_version: '1.16.5',
      };

      const modrinth: ModrinthPack = {
        project_id: 'm1',
        slug: 'mr-pack',
        title: 'Modrinth Fabric Pack',
        author: 'DevM',
        url: 'https://modrinth.com/modpack/mr-pack',
        downloads: 8000,
        has_server: true,
        loaders: ['Fabric'],
      };

      const curse: CurseforgePack = {
        project_id: 99,
        slug: 'cf-pack',
        title: 'CurseForge Skyblock',
        author: 'DevC',
        url: 'https://curseforge.com/minecraft/modpacks/cf-pack',
        downloads: 12000,
        has_server: false,
      };

      const docs = [
        buildBilibiliSearchDocument(bili),
        buildBbsmcSearchDocument(bbsmc),
        buildXyebbsSearchDocument(xyebbs),
        buildModrinthSearchDocument(modrinth),
        buildCurseforgeSearchDocument(curse),
      ];

      expect(filterItemsWithSearch(docs, (d) => d, '机械动力').length).toBe(1);
      expect(filterItemsWithSearch(docs, (d) => d, 'Fabric').length).toBe(1);
      expect(filterItemsWithSearch(docs, (d) => d, 'Skyblock').length).toBe(1);
    });
  });

  describe('Search State Coordinator & Search Modes', () => {
    it('sets and clears search queries across platforms', () => {
      searchCoordinator.setQuery('ATM9', 'mcmod');
      expect(searchCoordinator.getQuery('mcmod')).toBe('ATM9');

      searchCoordinator.setQuery('All The Mods');
      expect(searchCoordinator.getQuery()).toBe('All The Mods');

      searchCoordinator.clear('mcmod');
      expect(searchCoordinator.getQuery('mcmod')).toBe('');
    });

    it('defaults to legacy_compat and respects searchMode', () => {
      expect(searchCoordinator.getSearchMode()).toBe('legacy_compat');

      // In legacy_compat, -term is treated as literal token
      const qLegacy = parseSearchQuery('RLCraft -survival', 'all', 'legacy_compat');
      expect(qLegacy.mode).toBe('legacy_compat');
      expect(qLegacy.terms).toContain('-survival');
      expect(qLegacy.negatedTerms).toBeUndefined();

      // In advanced, -term is extracted into negatedTerms
      const qAdvanced = parseSearchQuery('RLCraft -survival "Hardcore pack" author:Shivaxi', 'all', 'advanced');
      expect(qAdvanced.mode).toBe('advanced');
      expect(qAdvanced.negatedTerms).toEqual(['survival']);
      expect(qAdvanced.exactPhrases).toEqual(['hardcore pack']);
      expect(qAdvanced.fieldQueries).toEqual({ author: 'shivaxi' });
    });
  });
});

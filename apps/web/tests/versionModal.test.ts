import { describe, it, expect } from 'vitest';
import {
  buildVersionModalViewModel,
  buildMcVersionStrip,
  renderSimpleMarkdown,
  renderOverviewPane,
  renderChangelogPane,
  renderDownloadsPane,
  renderDiscussionsPane,
} from '../src/modals/version';
import type { McmodStructuredItem } from '../src/platforms/mcmod/types';
import type { BilibiliPack } from '../src/types/legacy/bilibili';
import type { BbsmcPack } from '../src/types/legacy/bbsmc';
import type { XyebbsPack } from '../src/types/legacy/xyebbs';
import type { ModrinthPack } from '../src/types/legacy/modrinth';
import type { CurseforgePack } from '../src/types/legacy/curseforge';

describe('Version Modal Subsystem', () => {
  describe('Markdown & MC Strip Helpers', () => {
    it('renders simple markdown headings, lists, and code blocks safely', () => {
      const md = '# Header 1\n- Item A\n- Item B\n```js\nconst a = 1;\n```';
      const html = renderSimpleMarkdown(md);
      expect(html).toContain('<h1');
      expect(html).toContain('Header 1');
      expect(html).toContain('<li');
      expect(html).toContain('Item A');
      expect(html).toContain('<pre class="vmodal-code-block"');
    });

    it('builds Minecraft version family strip', () => {
      const versions = ['1.20.1', '1.20.2', '1.19.2', '1.19.4', '1.16.5'];
      const stripHtml = buildMcVersionStrip(versions);
      expect(stripHtml).toContain('mcver-strip');
      expect(stripHtml).toContain('1.20');
      expect(stripHtml).toContain('1.19');
      expect(stripHtml).toContain('1.16');
    });

    it('returns empty string if fewer than 2 versions for strip', () => {
      expect(buildMcVersionStrip(['1.20.1'])).toBe('');
      expect(buildMcVersionStrip([])).toBe('');
    });
  });

  describe('ViewModel Adapters & Pane Rendering', () => {
    it('builds ViewModel and renders panes for Bilibili', () => {
      const pack: BilibiliPack = {
        bvid: 'BV1abc',
        title: '测试整合包',
        author: '测试作者',
        url: 'https://bilibili.com/video/BV1abc',
        views: 1000,
        danmaku: 50,
        likes: 100,
        has_server: true,
        mc_version: '1.20.1',
        pub_time: '2026-09-01',
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        download_links: [{ name: '百度网盘', url: 'https://pan.baidu.com/123' } as any],
      };

      const vm = buildVersionModalViewModel('bilibili', pack);
      expect(vm.platform).toBe('bilibili');
      expect(vm.hasServer).toBe(true);
      expect(vm.releases.length).toBe(1);

      expect(vm.title).toBe('测试整合包');
      const ovHtml = renderOverviewPane(vm);
      expect(ovHtml).toContain('active-server');
      expect(ovHtml).toContain('支持联机开服');

      const dlHtml = renderDownloadsPane(vm);
      expect(dlHtml).toContain('百度网盘');

      const discHtml = renderDiscussionsPane(vm);
      expect(discHtml).toContain('哔哩哔哩');
    });

    it('builds ViewModel and renders panes for BBSMC', () => {
      const pack: BbsmcPack = {
        project_id: 123,
        id: '123',
        title: 'BBSMC 优秀整合',
        author: '作者BBS',
        url: 'https://bbsmc.net/modpack/123',
        downloads: 500,
        replies: 10,
        views: 800,
        has_server: false,
        versions: [
          {
            version_number: '1.0.0',
            name: '首发版',
            changelog: '初始发布',
            files: [{ filename: 'pack-1.0.0.zip', size: 1024 * 1024, url: 'https://cdn.example.com/pack.zip' }],
          },
        ],
      };

      const vm = buildVersionModalViewModel('bbsmc', pack);
      expect(vm.platform).toBe('bbsmc');
      expect(vm.releases.length).toBe(1);

      const clHtml = renderChangelogPane(vm);
      expect(clHtml).toContain('首发版');
      expect(clHtml).toContain('初始发布');
    });

    it('builds ViewModel and renders panes for MCMod, XYEBBS, Modrinth, CurseForge', () => {
      const mcmod: McmodStructuredItem = {
        mid: 50,
        title: 'MCMod 测试包',
        chineseName: '测试包',
        englishName: 'Test',
        formerTitles: [],
        url: 'https://www.mcmod.cn/modpack/50.html',
        author: 'Shivaxi',
        typeName: '原创',
        moldId: '1',
        coverUrl: '',
        views: 100,
        score: 3,
        recommendations: 10,
        favorites: 20,
        commentsCount: 5,
        votes: { redVotes: 10, blackVotes: 1, redPercent: 90, blackPercent: 10 },
        trendStats: { lat: 10, max: 20, avg: 15, days: 5, t7: 2, t30: 5, t60: 8, tall: 10, score: 3 },
        tags: [],
        categories: [],
        mcVersions: ['1.12.2', '1.16.5'],
        loaders: ['Forge'],
        includedModsCount: 50,
        modCategories: [],
        previewMods: [],
        includedModNames: [],
        modCategorySearch: '',
        environmentClaims: [],
        has_server: true,
      };
      const vmMcmod = buildVersionModalViewModel('mcmod', mcmod);
      expect(vmMcmod.platform).toBe('mcmod');
      expect(vmMcmod.hasServer).toBe(true);

      const xyebbs: XyebbsPack = {
        project_id: 1,
        id: '1',
        title: 'XYEBBS Pack',
        author: 'A',
        url: 'https://xyebbs.com/1',
        downloads: 10,
        replies: 1,
        views: 20,
        has_server: false,
        releases: [],
      };
      expect(buildVersionModalViewModel('xyebbs', xyebbs).platform).toBe('xyebbs');

      const modrinth: ModrinthPack = {
        project_id: 'm1',
        slug: 'pack',
        title: 'Modrinth Pack',
        author: 'M',
        url: 'https://modrinth.com/pack',
        downloads: 50,
        has_server: true,
        versions: [],
      };
      expect(buildVersionModalViewModel('modrinth', modrinth).platform).toBe('modrinth');

      const curse: CurseforgePack = {
        project_id: 9,
        slug: 'c-pack',
        title: 'Curse Pack',
        author: 'C',
        url: 'https://curseforge.com/pack',
        downloads: 100,
        has_server: false,
      };
      expect(buildVersionModalViewModel('curseforge', curse).platform).toBe('curseforge');
    });
  });
});

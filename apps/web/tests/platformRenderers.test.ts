import { describe, it, expect, beforeAll, afterAll, vi } from 'vitest';
import { BILIBILI_COVER_FALLBACK, renderBiliGroupedCard, renderBiliFlatCard } from '../src/platforms/bilibili/renderer';
import { renderBbsmcCard } from '../src/platforms/bbsmc/renderer';
import { renderXyebbsCard, XYEBBS_COVER_FALLBACK } from '../src/platforms/xyebbs/renderer';
import { renderModrinthCard } from '../src/platforms/modrinth/renderer';
import { CURSEFORGE_COVER_FALLBACK, renderCurseforgeCard } from '../src/platforms/curseforge/renderer';
import {
  filterBilibiliGroupsByPersonalStatus,
  getDesktopSearchPlaceholder,
  renderCurseforgeFileIndexDetail,
  renderPackVersionDetail,
  renderPersonalBackup,
  renderPickerModal,
  resolvePersonalTargetRecord,
  setPickerModalForTest,
  renderStickyFollowBar,
  setStickyFollowStateForTest,
  renderDetailSourceDynamics,
  renderInAppChangelogView,
  renderInAppSideContent,
  setInAppWindowStateForTest,
  getInAppWindowStateForTest,
  type DesktopRecord,
} from '../src/desktopShell';
import type { BiliGroup } from '../src/platforms/bilibili/renderer';
import type { BilibiliPack } from '../src/types/legacy/bilibili';
import type { BbsmcPack } from '../src/types/legacy/bbsmc';
import type { XyebbsPack } from '../src/types/legacy/xyebbs';
import type { ModrinthPack } from '../src/types/legacy/modrinth';
import type { CurseforgePack } from '../src/types/legacy/curseforge';
import { clearFailedImage, getImageFailure, rememberFailedImage } from '../src/utils/imageFallback';
import { releaseDetachedCoverImageRequest, renderCoverImage, startCoverImageRetry, type CoverImageRequestTarget } from '../src/utils/coverImage';

beforeAll(() => vi.stubGlobal('document', { documentElement: { dataset: {} } }));
afterAll(() => vi.unstubAllGlobals());

describe('Platform Card Renderers', () => {
  it('keeps a personal action bound to platform and source id after records reorder', () => {
    const record = (platform: DesktopRecord['platform'], sourceId: string, title: string) => ({ platform, sourceId, title }) as DesktopRecord;
    const first = record('modrinth', 'project-a', 'A');
    const target = record('modrinth', 'project-b', 'B');
    const reordered = [target, first];

    expect(resolvePersonalTargetRecord(reordered, 'modrinth', 'project-b', 1)).toBe(target);
    expect(resolvePersonalTargetRecord(reordered, undefined, undefined, 1)).toBe(first);
  });

  it('shows missing personal sources as historical references with safe links and backup controls', () => {
    const status = { favorite: true, wantToPlay: true, played: false, rating: 4, note: '<script>备注</script>', updatedAt: null };
    const html = renderPersonalBackup({
      'bilibili:BV-A': { ...status, reference: { title: '历史 A', sourceUrl: 'https://example.com/A', objectType: 'bilibili-video' } },
      'mcmod:123': status,
      'mcmod:456': { ...status, reference: { sourceUrl: 'javascript:alert(1)', objectType: 'platform-record' } },
    });
    expect(html).toContain('当前数据未包含此来源');
    expect(html).toContain('保存时记录的来源信息（非实时源站数据）');
    expect(html).toContain('历史 A');
    expect(html).toContain('评分：4');
    expect(html).toContain('&lt;script&gt;备注&lt;/script&gt;');
    expect(html).toContain('href="https://example.com/A"');
    expect(html).not.toContain('javascript:');
    expect(html).toContain('标题未知（本地数据未提供）');
    expect(html).toContain('/api/library/export');
    expect(html).toContain('type="file"');
  });
  it('renders the MCMod pack version separately and accepts old missing-field records', () => {
    expect(renderPackVersionDetail({ platform: 'mcmod', packVersion: '1.2.3' }))
      .toContain('<dt>整合包版本名</dt><dd>1.2.3</dd>');
    expect(renderPackVersionDetail({ platform: 'mcmod' })).toContain('未知（本地数据未提供）');
    expect(renderPackVersionDetail({ platform: 'mcmod', packVersion: '<img>' })).toContain('&lt;img&gt;');
    expect(renderPackVersionDetail({ platform: 'bilibili', packVersion: '1.2.3' })).toBe('');
  });
  it('renders CurseForge file indexes without presenting them as release history', () => {
    const html = renderCurseforgeFileIndexDetail({
      platform: 'curseforge',
      mainFileId: 9999,
      fileIndexes: [
        { fileId: 7101, filename: 'Arcadia 3.2.1.zip', releaseType: 1, gameVersion: '1.20.1', modLoader: 4 },
        { fileId: 7101, filename: 'Arcadia 3.2.1.zip', releaseType: 1, gameVersion: '1.20.2', modLoader: 6 },
        { fileId: 7102, filename: 'Arcadia unknown.zip', releaseType: 87, gameVersion: '1.20.3', modLoader: 77 },
      ],
    });
    expect(html).toContain('来源提供的文件索引');
    expect(html).toContain('非完整历史');
    expect(html).toContain('Arcadia 3.2.1.zip');
    expect(html).toContain('Minecraft：1.20.1 · Loader：Fabric');
    expect(html).toContain('Minecraft：1.20.2 · Loader：NeoForge');
    expect(html).toContain('未知发布类型（87）');
    expect(html).toContain('未知 Loader（77）');
    expect(html).toContain('主文件 ID 9999 未出现在当前文件索引中');
    expect(html).toContain('2 个文件 ID · 3 条索引项');
    expect(html).not.toContain('<span class="detail-submeta">主文件</span>');
    expect(html).not.toContain('整合包版本名');
    expect(html).not.toContain('发布日期');
    expect(html).not.toContain('release-item');

    const oldSidecar = renderCurseforgeFileIndexDetail({ platform: 'curseforge', mainFileId: 8888 });
    expect(oldSidecar).toContain('当前数据未提供文件索引');
    expect(oldSidecar).toContain('主文件 ID 8888 未出现在当前文件索引中');
    expect(renderCurseforgeFileIndexDetail({ platform: 'modrinth' })).toBe('');
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
      pic: 'https://example.com/bilibili-cover.jpg',
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
    expect(flatHtml).toContain('data-cover-image="true"');
    expect(flatHtml).toContain(`data-fallback-src="${BILIBILI_COVER_FALLBACK}"`);

    expect(flatHtml).toContain('data-action="open-in-app-window"');

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
    expect(groupedHtml).toContain('data-cover-image="true"');
    expect(groupedHtml).toContain('data-action="open-in-app-window"');
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
    expect(html).toContain('data-cover-state="missing"');
    expect(html).toContain('来源未提供封面');
    expect(html).toContain('data-action="open-in-app-window"');
    expect(html).toContain('bbsmc-comment-btn');
    expect(html).not.toContain('window.BBSMC_COVER_FALLBACK');
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
    expect(html).toContain('来源未提供封面');
    expect(html).toContain('data-action="open-in-app-window"');
    expect(html).toContain('xyebbs-comment-btn');
    expect(html).toContain(`src="${XYEBBS_COVER_FALLBACK}"`);
    expect(html).not.toContain('BBSMC%20');
    expect(html).not.toContain('window.XYEBBS_COVER_FALLBACK');
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
    expect(html).toContain('data-action="open-in-app-window"');
    expect(html).toContain('modrinth-comment-btn');
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
    expect(html).toContain('来源未提供封面');
    expect(html).toContain('data-action="open-in-app-window"');
    expect(html).toContain('curseforge-comment-btn');
    expect(html).not.toContain('window.MODRINTH_COVER_FALLBACK');
  });

  it('does not cache a detached loading cover as a failed resource', () => {
    const failedUrl = 'https://invalid.example.test/curseforge-cover.png';
    const makeTarget = (isConnected: boolean, state: string, initialSource: string) => {
      let source = initialSource;
      const assignments: string[] = [];
      const target: CoverImageRequestTarget = {
        isConnected,
        loading: 'lazy',
        dataset: {
          originalSrc: failedUrl,
          fallbackSrc: CURSEFORGE_COVER_FALLBACK,
          coverState: state,
        },
        get src() { return source; },
        set src(value: string) {
          source = value;
          assignments.push(value);
        },
      };
      return { target, assignments, source: () => source };
    };
    const p = {
      project_id: 1000,
      title: 'Broken Cover Pack',
      author: 'AuthorCF',
      url: 'https://curseforge.com/minecraft/modpacks/broken-cover',
      icon_url: failedUrl,
      downloads: 0,
      has_server: false,
    } as CurseforgePack;

    clearFailedImage(failedUrl);
    try {
      expect(renderCurseforgeCard(p)).toContain(`data-cover-state="loading"`);
      expect(renderCurseforgeCard(p)).toContain(`src="${failedUrl}"`);

      const initialLoad = makeTarget(false, 'loading', failedUrl);
      expect(releaseDetachedCoverImageRequest(initialLoad.target)).toBe(true);
      expect(initialLoad.target.dataset.coverState).toBe('loading');
      expect(initialLoad.source()).toBe(failedUrl);
      expect(initialLoad.assignments).toEqual([]);
      expect(getImageFailure(failedUrl)).toBeNull();

      const redisplayed = renderCoverImage({
        url: failedUrl,
        fallback: CURSEFORGE_COVER_FALLBACK,
        alt: 'Broken Cover Pack',
        key: 'curseforge:1000',
      });
      expect(redisplayed.state).toBe('loading');
      expect(redisplayed.source).toBe(failedUrl);

      rememberFailedImage(failedUrl, 'timeout');
      const retrying = makeTarget(true, 'timeout', CURSEFORGE_COVER_FALLBACK);
      const ticket = startCoverImageRetry(retrying.target);
      expect(ticket).not.toBeNull();
      retrying.target.isConnected = false;
      expect(releaseDetachedCoverImageRequest(retrying.target, ticket!)).toBe(true);
      expect(retrying.target.dataset.coverState).toBe('loading');
      expect(retrying.assignments).toEqual([failedUrl]);
      expect(getImageFailure(failedUrl)?.kind).toBe('timeout');
      const afterAbandonedRetry = renderCoverImage({
        url: failedUrl,
        fallback: CURSEFORGE_COVER_FALLBACK,
        alt: 'Broken Cover Pack',
        key: 'curseforge:1000',
      });
      expect(afterAbandonedRetry.state).toBe('timeout');
      expect(afterAbandonedRetry.source).toBe(CURSEFORGE_COVER_FALLBACK);
    } finally {
      clearFailedImage(failedUrl);
    }
  });

  it("renders discovery picker modal for included mods with search, selection, and batch limits", () => {
    try {
      expect(renderPickerModal()).toBe("");
      setPickerModalForTest(
        { type: "included-mod", search: "", limit: 2 },
        {
          platform: "mcmod",
          includedMods: ["JEI"],
          availableIncludedMods: [
            { value: "JEI", count: 609 },
            { value: "Create", count: 500 },
            { value: "AppleSkin", count: 400 },
          ],
        },
      );
      const html = renderPickerModal();
      expect(html).toContain("picker-modal-panel");
      expect(html).toContain("MOD DISCOVERY");
      expect(html).toContain("全部收录模组");
      expect(html).toContain("JEI");
      expect(html).toContain("609");
      expect(html).toContain("is-active");
      expect(html).toContain("Create");
      expect(html).toContain("500");
      expect(html).not.toContain("AppleSkin");
      expect(html).toContain("加载更多 300 项");
      expect(html).toContain("一次展示完");
      expect(html).toContain("data-action=\"picker-load-all\"");

      setPickerModalForTest({ type: "included-mod", search: "apple", limit: 10 });
      const searchHtml = renderPickerModal();
      expect(searchHtml).toContain("AppleSkin");
      expect(searchHtml).not.toContain(`data-value="Create"`);
    } finally {
      setPickerModalForTest(null);
    }
  });

  it("renders discovery picker modal for categories with option selection and counts", () => {
    try {
      setPickerModalForTest(
        { type: "category", search: "", limit: 100 },
        {
          platform: "mcmod",
          category: "科技",
          availableCategories: ["科技", "魔法", "冒险"],
        },
      );
      const html = renderPickerModal();
      expect(html).toContain("CATEGORY DISCOVERY");
      expect(html).toContain("MC百科 全部分类与标签（3 类）");
      expect(html).toContain("科技");
      expect(html).toContain("is-active");
      expect(html).toContain("魔法");
      expect(html).toContain("冒险");
    } finally {
      setPickerModalForTest(null);
    }
  });

  it("supports custom sorting and load-all controls in picker modal", () => {
    try {
      const availableMods = [
        { value: "Create", count: 500 },
        { value: "JEI", count: 609 },
        { value: "AppleSkin", count: 400 },
      ];
      // 1. count_desc (default)
      setPickerModalForTest(
        { type: "included-mod", search: "", limit: 10, sort: "count_desc" },
        { platform: "mcmod", availableIncludedMods: availableMods },
      );
      const descHtml = renderPickerModal();
      expect(descHtml).toContain("picker-sort-select");
      expect(descHtml).toContain("value=\"count_desc\" selected");
      const descJeiIndex = descHtml.indexOf("data-value=\"JEI\"");
      const descCreateIndex = descHtml.indexOf("data-value=\"Create\"");
      const descAppleIndex = descHtml.indexOf("data-value=\"AppleSkin\"");
      expect(descJeiIndex).toBeLessThan(descCreateIndex);
      expect(descCreateIndex).toBeLessThan(descAppleIndex);

      // 2. count_asc (niche first)
      setPickerModalForTest(
        { type: "included-mod", search: "", limit: 10, sort: "count_asc" },
        { platform: "mcmod", availableIncludedMods: availableMods },
      );
      const ascHtml = renderPickerModal();
      const ascAppleIndex = ascHtml.indexOf("data-value=\"AppleSkin\"");
      const ascCreateIndex = ascHtml.indexOf("data-value=\"Create\"");
      const ascJeiIndex = ascHtml.indexOf("data-value=\"JEI\"");
      expect(ascAppleIndex).toBeLessThan(ascCreateIndex);
      expect(ascCreateIndex).toBeLessThan(ascJeiIndex);

      // 3. name_asc (alphabetical A-Z)
      setPickerModalForTest(
        { type: "included-mod", search: "", limit: 10, sort: "name_asc" },
        { platform: "mcmod", availableIncludedMods: availableMods },
      );
      const nameAscHtml = renderPickerModal();
      const nameApple = nameAscHtml.indexOf("data-value=\"AppleSkin\"");
      const nameCreate = nameAscHtml.indexOf("data-value=\"Create\"");
      const nameJei = nameAscHtml.indexOf("data-value=\"JEI\"");
      expect(nameApple).toBeLessThan(nameCreate);
      expect(nameCreate).toBeLessThan(nameJei);

      // 4. name_desc (alphabetical Z-A)
      setPickerModalForTest(
        { type: "included-mod", search: "", limit: 10, sort: "name_desc" },
        { platform: "mcmod", availableIncludedMods: availableMods },
      );
      const nameDescHtml = renderPickerModal();
      const descNameJei = nameDescHtml.indexOf("data-value=\"JEI\"");
      const descNameCreate = nameDescHtml.indexOf("data-value=\"Create\"");
      const descNameApple = nameDescHtml.indexOf("data-value=\"AppleSkin\"");
      expect(descNameJei).toBeLessThan(descNameCreate);
      expect(descNameCreate).toBeLessThan(descNameApple);

      // 5. collapse button when limit > 300 and total > 300
      const largeList = Array.from({ length: 350 }, (_, i) => ({ value: `Mod-${i}`, count: i }));
      setPickerModalForTest(
        { type: "included-mod", search: "", limit: 999999, sort: "count_desc" },
        { platform: "mcmod", availableIncludedMods: largeList },
      );
      const allHtml = renderPickerModal();
      expect(allHtml).toContain("picker-collapse-btn");
      expect(allHtml).toContain("data-action=\"picker-reset-limit\"");
      expect(allHtml).toContain("收起为前 300 项");

      // 6. category modal translates Modrinth English tags and allows Chinese search
      setPickerModalForTest(
        { type: "category", search: "优化", limit: 10, sort: "count_desc" },
        { platform: "modrinth", availableCategories: ["optimization", "technology", "magic"] },
      );
      const catModalHtml = renderPickerModal();
      expect(catModalHtml).toContain("性能优化");
      expect(catModalHtml).toContain("(optimization)");
      expect(catModalHtml).not.toContain("technology");

      // 7. gameplay modal translates CurseForge English tags and allows Chinese search
      setPickerModalForTest(
        { type: "gameplay-category", search: "探索", limit: 10, sort: "count_desc" },
        {
          platform: "curseforge",
          availableGameplayCategories: [
            { value: "Exploration", count: 100 },
            { value: "Tech", count: 50 },
          ],
        },
      );
      const gameplayModalHtml = renderPickerModal();
      expect(gameplayModalHtml).toContain("探索");
      expect(gameplayModalHtml).toContain("(Exploration)");
      expect(gameplayModalHtml).not.toContain("Tech");
    } finally {
      setPickerModalForTest(null);
    }
  });

  it("renders sticky follow bar with category pills, dropdown, sort options, and follow mode toggle", () => {
    try {
      setStickyFollowStateForTest({
        platform: "mcmod",
        category: "科技",
        availableCategories: ["科技", "魔法", "冒险", "空岛"],
        sort: "views_desc",
        stickyFollowMode: true,
        records: [
          { categories: ["科技", "冒险"] } as DesktopRecord,
          { categories: ["科技"] } as DesktopRecord,
        ],
      });
      const html = renderStickyFollowBar();
      expect(html).toContain("desktop-sticky-bar");
      expect(html).toContain("is-sticky");
      expect(html).toContain("sticky-category-row");
      expect(html).toContain("sticky-pills-flow");
      expect(html).toContain("data-category=\"科技\"");
      expect(html).toContain("is-active");
      expect(html).toContain("sticky-pill-count");
      expect(html).not.toContain("<select");
      expect(html).toContain('data-dropdown-root="sticky-sort"');
      expect(html).toContain("sticky-all-btn");
      expect(html).toContain('data-picker="category"');
      expect(html).toContain('data-picker="included-mod"');
      expect(html).toContain("views_desc");
      expect(html).toContain("📌 跟随中");
      expect(html).toContain("↑ 顶部");
      expect(html).toContain('id="sticky-cat-search"');
      expect(html).toContain('id="sticky-mod-search"');
      expect(html).toContain("分类库弹窗");
      expect(html).toContain("模组库弹窗");

      // Test with stickyFollowMode: false
      setStickyFollowStateForTest({ stickyFollowMode: false });
      const unpinnedHtml = renderStickyFollowBar();
      expect(unpinnedHtml).not.toContain("is-sticky");
      expect(unpinnedHtml).toContain("📌 开启跟随");

      // Test inline search filtering in sticky bar for categories
      setStickyFollowStateForTest({
        availableCategories: ["科技", "魔法", "冒险", "空岛"],
        stickyCatSearch: "魔",
      });
      const catSearchHtml = renderStickyFollowBar();
      expect(catSearchHtml).toContain("魔法");
      expect(catSearchHtml).not.toContain('data-category="冒险"');
      expect(catSearchHtml).toContain('data-action="clear-sticky-cat-search"');

      // Test no match for category search
      setStickyFollowStateForTest({
        availableCategories: ["科技", "魔法"],
        stickyCatSearch: "不存在的分类名称",
      });
      const catNoMatchHtml = renderStickyFollowBar();
      expect(catNoMatchHtml).toContain("无匹配分类");

      // Test inline search filtering in sticky bar for mods
      setStickyFollowStateForTest({
        stickyCatSearch: "",
        availableIncludedMods: [
          { value: "JEI 物品管理器", count: 100 },
          { value: "机械动力 (Create)", count: 80 },
          { value: "苹果皮 (AppleSkin)", count: 50 },
        ],
        stickyModSearch: "Create",
      });
      const modSearchHtml = renderStickyFollowBar();
      expect(modSearchHtml).toContain("机械动力 (Create)");
      expect(modSearchHtml).not.toContain("苹果皮");
      expect(modSearchHtml).toContain('data-action="clear-sticky-mod-search"');

      // Test no match for mod search
      setStickyFollowStateForTest({
        stickyModSearch: "不存在的模组",
      });
      const modNoMatchHtml = renderStickyFollowBar();
      expect(modNoMatchHtml).toContain("无匹配模组");

      // Test inline expand for category and mod rows
      setStickyFollowStateForTest({
        stickyModSearch: "",
        stickyFollowMode: true,
        availableCategories: Array.from({ length: 20 }, (_, i) => `分类-${i}`),
        availableIncludedMods: Array.from({ length: 80 }, (_, i) => ({ value: `Mod-${i}`, count: i })),
        stickyCategoriesExpanded: true,
        stickyModsExpanded: true,
        stickyModsExpandAll: false,
      });
      const expandedHtml = renderStickyFollowBar();
      expect(expandedHtml).toContain("sticky-category-row is-expanded");
      expect(expandedHtml).toContain("收起分类 ▴");
      expect(expandedHtml).toContain("toggle-sticky-categories-expanded");
      expect(expandedHtml).toContain("sticky-mods-row is-expanded");
      expect(expandedHtml).toContain("收起模组 ▴");
      expect(expandedHtml).toContain("toggle-sticky-mods-expanded");
      expect(expandedHtml).toContain("toggle-sticky-mods-expand-all");
      expect(expandedHtml).toContain("展开全部 (80) ▾");

      // Test inline expand-all for mods (expands all without opening popup)
      setStickyFollowStateForTest({
        stickyModsExpandAll: true,
      });
      const expandAllHtml = renderStickyFollowBar();
      expect(expandAllHtml).toContain("sticky-mods-row is-expanded is-expanded-all");
      expect(expandAllHtml).toContain("收起全部 ▴");
      expect(expandAllHtml).toContain("toggle-sticky-mods-expand-all");

      // Test Modrinth platform category pills translation
      setStickyFollowStateForTest({
        platform: "modrinth",
        availableCategories: ["optimization", "technology", "magic"],
        category: "optimization",
        stickyModsExpandAll: false,
      });
      const mrHtml = renderStickyFollowBar();
      expect(mrHtml).toContain("性能优化");
      expect(mrHtml).toContain("科技");
      expect(mrHtml).toContain("魔法");

      // Test CurseForge platform category and gameplay pills translation
      setStickyFollowStateForTest({
        platform: "curseforge",
        availableCategories: ["Exploration", "Adventure and RPG", "Tech"],
        category: "Exploration",
        gameplayCategories: ["Exploration"],
        availableGameplayCategories: [
          { value: "Exploration", count: 10 },
          { value: "Tech", count: 5 },
        ],
      });
      const cfHtml = renderStickyFollowBar();
      expect(cfHtml).toContain("探索");
      expect(cfHtml).toContain("冒险与RPG");
      expect(cfHtml).toContain("科技");
      expect(cfHtml).toContain("玩法库弹窗");
      expect(cfHtml).toContain("clear-gameplay-categories");
      expect(cfHtml).toContain("toggle-sticky-gameplay-category");
    } finally {
      setStickyFollowStateForTest({
        platform: "mcmod",
        category: "",
        availableCategories: [],
        gameplayCategories: [],
        availableGameplayCategories: [],
        sort: "updated_desc",
        stickyFollowMode: true,
        stickyCategoriesExpanded: false,
        stickyModsExpanded: false,
        stickyModsExpandAll: false,
        stickyModSearch: "",
        stickyCatSearch: "",
        records: [],
      });
    }
  });

  it('renders clickable comment preview buttons in bilibili and xyebbs cards', () => {
    const p: BilibiliPack = {
      bvid: 'BV-comment-test',
      title: 'B站评论测试包',
      author: '测试UP',
      url: 'https://bilibili.com/video/BV-comment-test',
      views: 5000,
      likes: 200,
      reply: 42,
      danmaku: 10,
      has_server: false,
      mc_version: '1.20.1',
      loaders: ['Forge'],
      categories: ['冒险'],
    };

    const flatHtml = renderBiliFlatCard(p);
    expect(flatHtml).toContain('data-action="open-comment-preview"');
    expect(flatHtml).toContain('data-source-id="BV-comment-test"');
    expect(flatHtml).toContain('42');

    const xy: XyebbsPack = {
      platform: 'xyebbs',
      project_id: 999,
      slug: 'test-pack',
      title: 'XYEBBS评论测试',
      author: '测试作者',
      url: 'https://xyebbs.com/res-id/test-pack',
      downloads: 100,
      views: 500,
      comments: 18,
      replies: 18,
      has_server: false,
    };
    const xyHtml = renderXyebbsCard(xy);
    expect(xyHtml).toContain('data-action="open-comment-preview"');
    expect(xyHtml).toContain('data-source-id="999"');
    expect(xyHtml).toContain('18');
  });

  it('renders platform-specific source dynamics or standardized empty states with in-app window buttons', () => {
    // 1. mcmod with packVersion and empty releases
    const mcmodRecord: DesktopRecord = {
      id: 'mcmod:1145',
      platform: 'mcmod',
      sourceId: '1145',
      sourceIdOrigin: 'source',
      title: '元素觉醒',
      author: '创作者',
      url: 'https://www.mcmod.cn/modpack/1145.html',
      summary: '测试整合包',
      versions: ['1.20.1'],
      loaders: ['Forge'],
      categories: ['魔法'],
      updatedAt: '2026-09-14',
      coverUrl: '',
      environment: { status: 'supported', certainty: 'high', label: '支持', sourceField: null },
      releases: [],
      raw: {},
      searchText: '',
      evidence: [],
      packVersion: 'v1.4.6',
    };
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const vmEmpty = { releases: [], targetUrl: 'https://www.mcmod.cn/modpack/1145.html', mcVersionsList: ['1.20.1'] } as any;
    const mcmodHtml = renderDetailSourceDynamics(mcmodRecord, vmEmpty);
    expect(mcmodHtml).toContain('v1.4.6');
    expect(mcmodHtml).toContain('本地快照暂未收录更新日志');
    expect(mcmodHtml).toContain('🪟 软件内查看原站更新');
    expect(mcmodHtml).toContain('data-action="open-in-app-window"');

    // 2. curseforge empty state
    const cfRecord: DesktopRecord = {
      id: 'curseforge:12345',
      platform: 'curseforge',
      sourceId: '12345',
      sourceIdOrigin: 'source',
      title: 'CF测试包',
      author: 'CF作者',
      url: 'https://www.curseforge.com/minecraft/modpacks/test',
      summary: '',
      versions: ['1.20.1'],
      loaders: ['Forge'],
      categories: [],
      updatedAt: '2026-09-01',
      coverUrl: '',
      environment: { status: 'unknown', certainty: 'low', label: '未知', sourceField: null },
      releases: [],
      raw: {},
      searchText: '',
      evidence: [],
    };
    const cfHtml = renderDetailSourceDynamics(cfRecord, vmEmpty);
    expect(cfHtml).toContain('本地快照暂未收录文件索引与更新记录');
    expect(cfHtml).toContain('🪟 软件内查看原站文件');

    // 3. modrinth empty state
    const modrinthRecord: DesktopRecord = {
      ...cfRecord,
      id: 'modrinth:test',
      platform: 'modrinth',
      url: 'https://modrinth.com/modpack/test',
    };
    const modrinthHtml = renderDetailSourceDynamics(modrinthRecord, vmEmpty);
    expect(modrinthHtml).toContain('本地快照暂未收录版本发布记录');
    expect(modrinthHtml).toContain('🪟 软件内查看原站版本');

    // 4. bilibili grouped multiple episodes
    const biliRecord: DesktopRecord = {
      ...cfRecord,
      id: 'bilibili:BV123',
      platform: 'bilibili',
      sourceId: 'BV123',
      title: '自制包第一期',
      url: 'https://www.bilibili.com/video/BV123',
    };
    const sampleGroup: BiliGroup = {
      key: 'test-group',
      items: [
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        { bvid: 'BV123', title: '自制包第一期', pub_time: '2026-09-01', views: 5000 } as any,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        { bvid: 'BV456', title: '自制包第二期更新', pub_time: '2026-09-10', views: 8000 } as any,
      ],
      allVersions: new Set(),
      allLoaders: new Set(),
      allCategories: new Set(),
      allGroups: new Set(),
      allLinks: [],
      totalViews: 13000,
      totalLikes: 1000,
      totalCoins: 200,
      totalFavs: 500,
      totalDanmaku: 100,
      totalReply: 50,
      totalShare: 20,
      latestTimestamp: 1700000000,
      latestPubTime: '2026-09-10',
    };
    const biliHtml = renderDetailSourceDynamics(biliRecord, vmEmpty, [sampleGroup]);
    expect(biliHtml).toContain('关联视频与版本动态');
    expect(biliHtml).toContain('同系列共 2 期视频');
    expect(biliHtml).toContain('自制包第二期更新');
    expect(biliHtml).toContain('data-action="open-in-app-window"');

    // 5. bbsmc and xyebbs empty states
    const bbsmcRecord: DesktopRecord = {
      ...cfRecord,
      id: 'bbsmc:1',
      platform: 'bbsmc',
      url: 'https://bbsmc.net/1',
    };
    const bbsmcHtml = renderDetailSourceDynamics(bbsmcRecord, vmEmpty);
    expect(bbsmcHtml).toContain('本地快照暂未收录更新记录');
    expect(bbsmcHtml).toContain('🪟 软件内查看原帖动态');

    const xyebbsRecord: DesktopRecord = {
      ...cfRecord,
      id: 'xyebbs:1',
      platform: 'xyebbs',
      url: 'https://xyebbs.com/1',
    };
    const xyebbsHtml = renderDetailSourceDynamics(xyebbsRecord, vmEmpty);
    expect(xyebbsHtml).toContain('本地快照暂未收录更新日志');
    expect(xyebbsHtml).toContain('🪟 软件内查看原帖更新');
  });

  it('preserves and restores previous selected record when opening and closing in-app window', () => {
    const dummyRecord: DesktopRecord = {
      id: 'mcmod:100',
      platform: 'mcmod',
      sourceId: '100',
      sourceIdOrigin: 'source',
      title: '测试包',
      author: '作者',
      url: 'https://www.mcmod.cn/modpack/100.html',
      summary: '',
      versions: [],
      loaders: [],
      categories: [],
      updatedAt: '',
      coverUrl: '',
      environment: { status: 'unknown', certainty: 'low', label: '未知', sourceField: null },
      releases: [],
      raw: {},
      searchText: '',
      evidence: [],
    };

    // User is viewing detail drawer, then opens mini window
    setInAppWindowStateForTest(
      { url: 'https://example.com', title: '小窗测试' },
      null, // detail is tucked away
      dummyRecord, // saved previous
    );
    const beforeClose = getInAppWindowStateForTest();
    expect(beforeClose.inAppWindow).not.toBeNull();
    expect(beforeClose.selected).toBeNull();
    expect(beforeClose.previousSelected).toBe(dummyRecord);

    // After closing mini window, detail drawer should pop back up
    if (beforeClose.previousSelected) {
      setInAppWindowStateForTest(null, beforeClose.previousSelected, null);
    }
    const afterClose = getInAppWindowStateForTest();
    expect(afterClose.inAppWindow).toBeNull();
    expect(afterClose.selected).toBe(dummyRecord);
    expect(afterClose.previousSelected).toBeNull();

    // Clean up
    setInAppWindowStateForTest(null, null, null);
  });

  it('renders in-app side pane with personal library and platform dynamics for all platforms', () => {
    const baseRecord: DesktopRecord = {
      id: 'mcmod:100',
      platform: 'mcmod',
      sourceId: '100',
      title: '宝可梦探险包',
      author: 'MCModder',
      url: 'https://www.mcmod.cn/modpack/100.html',
      sourceIdOrigin: 'source',
      summary: '测试简介',
      versions: ['1.20.1'],
      loaders: ['Forge'],
      categories: ['冒险'],
      updatedAt: '2026-03-01',
      coverUrl: '',
      environment: { status: 'unknown', certainty: 'low', label: '未知', sourceField: null },
      releases: [],
      raw: {},
      searchText: '',
      evidence: [],
      packVersion: 'v2.1.0',
    };

    // 1. MCMod
    const mcmodSideHtml = renderInAppSideContent(baseRecord);
    expect(mcmodSideHtml).toContain('宝可梦探险包');
    expect(mcmodSideHtml).toContain('MC百科');
    expect(mcmodSideHtml).toContain('我的整合包库');
    const mcmodChangelogHtml = renderInAppChangelogView(baseRecord);
    expect(mcmodChangelogHtml).toContain('v2.1.0');

    // 2. CurseForge
    const cfRecord: DesktopRecord = {
      ...baseRecord,
      id: 'curseforge:200',
      platform: 'curseforge',
      sourceId: '200',
      title: 'RLCraft Test',
      fileIndexes: [
        { fileId: 101, filename: 'RLCraft-v1.0.zip', releaseType: 1, gameVersion: '1.12.2', modLoader: 'Forge' },
      ],
    };
    const cfSideHtml = renderInAppSideContent(cfRecord);
    expect(cfSideHtml).toContain('RLCraft Test');
    const cfChangelogHtml = renderInAppChangelogView(cfRecord);
    expect(cfChangelogHtml).toContain('CurseForge 文件索引快照');
    expect(cfChangelogHtml).toContain('1 个文件');

    // 3. CurseForge without files shows explicit '没有'
    const cfEmptyRecord: DesktopRecord = {
      ...cfRecord,
      packVersion: '',
      fileIndexes: [],
    };
    const cfEmptyChangelogHtml = renderInAppChangelogView(cfEmptyRecord);
    expect(cfEmptyChangelogHtml).toContain('没有');

    // 4. Modrinth
    const mrRecord: DesktopRecord = {
      ...baseRecord,
      id: 'modrinth:300',
      platform: 'modrinth',
      sourceId: '300',
      title: 'Fabulously Optimized',
      packVersion: '',
    };
    const mrSideHtml = renderInAppSideContent(mrRecord);
    expect(mrSideHtml).toContain('Fabulously Optimized');
    const mrChangelogHtml = renderInAppChangelogView(mrRecord);
    expect(mrChangelogHtml).toContain('没有');

    // 5. Bilibili
    const biliRecord: DesktopRecord = {
      ...baseRecord,
      id: 'bilibili:BV123456',
      platform: 'bilibili',
      sourceId: 'BV123456',
      title: '【MC整合包】超好玩生存',
      packVersion: '',
    };
    const biliSideHtml = renderInAppSideContent(biliRecord);
    expect(biliSideHtml).toContain('超好玩生存');
    const biliChangelogHtml = renderInAppChangelogView(biliRecord);
    expect(biliChangelogHtml).toContain('视频发布记录');

    // 6. BBSMC
    const bbsmcRecord: DesktopRecord = {
      ...baseRecord,
      id: 'bbsmc:400',
      platform: 'bbsmc',
      sourceId: '400',
      title: '论坛精选整合包',
      packVersion: '',
    };
    const bbsmcSideHtml = renderInAppSideContent(bbsmcRecord);
    expect(bbsmcSideHtml).toContain('论坛精选整合包');
    const bbsmcChangelogHtml = renderInAppChangelogView(bbsmcRecord);
    expect(bbsmcChangelogHtml).toContain('没有');
  });

  it('renders in-app changelog view with releases or explicit empty status', () => {
    const emptyRecord: DesktopRecord = {
      id: 'xyebbs:500',
      platform: 'xyebbs',
      sourceId: '500',
      title: '星域论坛整合包',
      author: 'XYEAuthor',
      url: 'https://www.xyebbs.com/thread-500.html',
      sourceIdOrigin: 'source',
      summary: '',
      versions: [],
      loaders: [],
      categories: [],
      updatedAt: '',
      coverUrl: '',
      environment: { status: 'unknown', certainty: 'low', label: '未知', sourceField: null },
      releases: [],
      raw: {},
      searchText: '',
      evidence: [],
    };

    // When empty: displays explicit '没有' and button to switch to web tab
    const emptyChangelogHtml = renderInAppChangelogView(emptyRecord);
    expect(emptyChangelogHtml).toContain('没有');
    expect(emptyChangelogHtml).toContain('当前本地快照暂无收录结构化更新日志');
    expect(emptyChangelogHtml).toContain('data-action="set-in-app-window-tab"');

    // When releases exist: displays releases list
    const recordWithReleases: DesktopRecord = {
      ...emptyRecord,
      releases: [
        {
          versionName: 'Release v1.5',
          date: '2026-03-01',
          gameVersions: ['1.20.1'],
          loaders: ['Fabric'],
          changelogMd: '修复了已知模组冲突',
        },
      ],
    };
    const changelogHtml = renderInAppChangelogView(recordWithReleases);
    expect(changelogHtml).toContain('Release v1.5');
    expect(changelogHtml).toContain('修复了已知模组冲突');
    expect(changelogHtml).toContain('2026-03-01');
  });
});


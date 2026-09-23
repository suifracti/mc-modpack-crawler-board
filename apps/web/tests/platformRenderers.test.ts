import { describe, it, expect, vi } from 'vitest';
import { renderBiliGroupedCard, renderBiliFlatCard } from '../src/platforms/bilibili/renderer';
import { renderBbsmcCard } from '../src/platforms/bbsmc/renderer';
import { renderXyebbsCard } from '../src/platforms/xyebbs/renderer';
import { renderModrinthCard } from '../src/platforms/modrinth/renderer';
import { CURSEFORGE_COVER_FALLBACK, renderCurseforgeCard } from '../src/platforms/curseforge/renderer';
import { filterBilibiliGroupsByPersonalStatus, getDesktopSearchPlaceholder, renderCurseforgeFileIndexDetail, renderPackVersionDetail, renderPersonalBackup } from '../src/desktopShell';
import type { BiliGroup } from '../src/platforms/bilibili/renderer';
import type { BilibiliPack } from '../src/types/legacy/bilibili';
import type { BbsmcPack } from '../src/types/legacy/bbsmc';
import type { XyebbsPack } from '../src/types/legacy/xyebbs';
import type { ModrinthPack } from '../src/types/legacy/modrinth';
import type { CurseforgePack } from '../src/types/legacy/curseforge';
import { beginImageRetry, clearFailedImage, COVER_IMAGE_RETRY_COOLDOWN_MS, rememberFailedImage } from '../src/utils/imageFallback';

describe('Platform Card Renderers', () => {
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
    expect(html).toContain('data-cover-state="missing"');
    expect(html).toContain('来源未提供封面');
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
    expect(html).not.toContain('window.MODRINTH_COVER_FALLBACK');
  });

  it('keeps a failed CurseForge cover stable and allows bounded manual recovery', () => {
    const failedUrl = 'https://invalid.example.test/curseforge-cover.png';
    const p = {
      project_id: 1000,
      title: 'Broken Cover Pack',
      author: 'AuthorCF',
      url: 'https://curseforge.com/minecraft/modpacks/broken-cover',
      icon_url: failedUrl,
      downloads: 0,
      has_server: false,
    } as CurseforgePack;

    vi.useFakeTimers();
    try {
      clearFailedImage(failedUrl);
      expect(renderCurseforgeCard(p)).toContain(`data-cover-state="loading"`);
      expect(renderCurseforgeCard(p)).toContain(`src="${failedUrl}"`);
      rememberFailedImage(failedUrl, 'timeout');
      const timedOut = renderCurseforgeCard(p);
      expect(timedOut).toContain(`src="${CURSEFORGE_COVER_FALLBACK}"`);
      expect(timedOut).toContain('封面加载超时');
      expect(timedOut).toContain('data-original-src="' + failedUrl + '"');
      expect(timedOut).toContain('data-action="retry-cover"');

      expect(beginImageRetry(failedUrl)).toBe(true);
      expect(renderCurseforgeCard(p)).toContain(`src="${failedUrl}"`);
      expect(renderCurseforgeCard(p)).toContain(`data-cover-state="loading"`);

      rememberFailedImage(failedUrl, 'error');
      expect(renderCurseforgeCard(p)).toContain('封面加载失败');
      expect(beginImageRetry(failedUrl)).toBe(false);
      vi.advanceTimersByTime(COVER_IMAGE_RETRY_COOLDOWN_MS);
      expect(beginImageRetry(failedUrl)).toBe(true);
      expect(renderCurseforgeCard(p)).toContain(`src="${failedUrl}"`);
    } finally {
      clearFailedImage(failedUrl);
      vi.useRealTimers();
    }
  });
});

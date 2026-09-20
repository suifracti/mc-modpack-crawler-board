import { describe, expect, it } from 'vitest';
import { adaptMcmodToVersionModal } from './versionAdapter';

describe('MC百科 desktop version details', () => {
  it('keeps the pack source URL separate from the version page URL', () => {
    const view = adaptMcmodToVersionModal({
      mid: 1,
      title: '真实测试包',
      url: 'https://www.mcmod.cn/modpack/1.html',
      mcVersions: ['1.7.10'],
      formerTitles: [],
    });

    expect(view.mcVersionsList).toEqual(['1.7.10']);
    expect(view.targetUrl).toBe('https://www.mcmod.cn/modpack/version/1.html');
  });
});

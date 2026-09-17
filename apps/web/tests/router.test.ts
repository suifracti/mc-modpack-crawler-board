import { describe, it, expect } from 'vitest';
import { platformRouter, parseHash } from '../src/router';

describe('Router Subsystem', () => {
  it('parses hash and query string defaults correctly', () => {
    const parsed = parseHash();
    expect(parsed.tab).toBeDefined();
    expect(parsed.query).toBeDefined();
  });

  it('manages platform tab navigation in memory', () => {
    platformRouter.navigateTo('bilibili', '机械动力', false);
    expect(platformRouter.getActiveTab()).toBe('bilibili');
    expect(platformRouter.getState().query).toBe('机械动力');

    platformRouter.navigateTo('modrinth', '', false);
    expect(platformRouter.getActiveTab()).toBe('modrinth');
  });

  it('notifies subscribers on route state change', () => {
    let notifiedTab = '';
    const unsubscribe = platformRouter.subscribe((newState) => {
      notifiedTab = newState.tab;
    });

    platformRouter.navigateTo('curseforge', '', false);
    expect(notifiedTab).toBe('curseforge');

    unsubscribe();
  });
});

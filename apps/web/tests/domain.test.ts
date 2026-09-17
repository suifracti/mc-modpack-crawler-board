import { describe, it, expect } from 'vitest';
import { extractMcVersion } from '../src/domain/minecraft';
import { cleanPackKey } from '../src/domain/packName';

describe('Minecraft Domain Recognition', () => {
  it('extractMcVersion extracts explicit mc versions from text or object', () => {
    expect(extractMcVersion('1.20.1')).toBe('MC 1.20.1');
    expect(extractMcVersion('MC 1.12.2 模组包')).toBe('MC 1.12.2');
    expect(extractMcVersion('All the Mods 9 - To the Sky')).toBe('MC 1.20.1');
    expect(extractMcVersion('All the Mods 8')).toBe('MC 1.19.2');
    expect(extractMcVersion('All the Mods 7')).toBe('MC 1.18.2');
    expect(extractMcVersion('All the Mods 6')).toBe('MC 1.16.5');
    expect(extractMcVersion({ mc_version: '1.20.1', title: 'Test Pack' })).toBe('MC 1.20.1');
    expect(extractMcVersion({ title: 'Better MC [FORGE] 1.19.2' })).toBe('MC 1.19.2');
    expect(extractMcVersion('')).toBe('');
    expect(extractMcVersion(null)).toBe('');
  });

  it('cleanPackKey normalizes pack titles and strips bracketed noise', () => {
    expect(cleanPackKey('【1.20.1】机械动力：星辰大海【已汉化】')).toBe('机械动力 星辰大海 已汉化');
    expect(cleanPackKey('[Forge 1.12.2] 启示录整合包 v1.2')).toBe('启示录 v');
    expect(cleanPackKey('【整合包发布】超难生存挑战')).toBe('超难 挑战');
    expect(cleanPackKey('')).toBe('');
  });
});

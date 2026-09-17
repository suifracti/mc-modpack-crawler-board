import { describe, it, expect, beforeEach, beforeAll } from 'vitest';
import { getTheme, setTheme, toggleTheme, Theme } from '../src/state/theme';

describe('Theme State Management', () => {
  const store = new Map<string, string>();
  let docTheme = '';

  beforeAll(() => {
    const mockStorage = {
      getItem: (k: string) => store.get(k) ?? null,
      setItem: (k: string, v: string) => store.set(k, String(v)),
      removeItem: (k: string) => {
        store.delete(k);
      },
      clear: () => store.clear(),
      length: 0,
      key: () => null,
    };

    (globalThis as unknown as { window: unknown }).window = globalThis;
    (globalThis as unknown as { localStorage: Storage }).localStorage = mockStorage;

    (globalThis as unknown as { document: unknown }).document = {
      documentElement: {
        setAttribute: (_k: string, v: string) => {
          docTheme = v;
        },
        getAttribute: (_k: string) => docTheme,
        removeAttribute: (_k: string) => {
          docTheme = '';
        },
      },
      querySelectorAll: () => [],
      addEventListener: () => {},
    };
  });

  beforeEach(() => {
    store.clear();
    docTheme = '';
  });

  it('defaults to dark when localStorage is empty', () => {
    expect(getTheme()).toBe('dark');
  });

  it('sets theme and updates documentElement and localStorage', () => {
    setTheme('eye');
    expect(getTheme()).toBe('eye');
    expect(store.get('mcmod-theme-v2')).toBe('eye');
    expect(docTheme).toBe('eye');
  });

  it('rejects invalid themes and falls back to dark', () => {
    setTheme('invalid-theme' as Theme);
    expect(getTheme()).toBe('dark');
  });

  it('toggleTheme cycles through themes correctly', () => {
    setTheme('light');
    const next = toggleTheme();
    expect(next).toBe('dark');
    expect(getTheme()).toBe('dark');
  });
});

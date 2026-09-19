/**
 * Centralized Theme Management and Synchronization.
 * Extracted from dashboard.js.
 */

export type Theme = 'light' | 'dark' | 'eye' | 'warm' | 'pink';

export const THEME_STORAGE_KEY = 'mcmod-theme-v2';

export const VALID_THEMES: Theme[] = ['dark', 'light', 'eye', 'warm', 'pink'];

export function getTheme(): Theme {
  if (typeof window === 'undefined' || !window.localStorage) {
    return 'dark';
  }
  const stored = localStorage.getItem(THEME_STORAGE_KEY) as Theme;
  if (stored && VALID_THEMES.includes(stored)) {
    return stored;
  }
  return 'dark';
}

export function setTheme(theme: Theme): void {
  const targetTheme: Theme = VALID_THEMES.includes(theme) ? theme : 'dark';

  if (typeof document !== 'undefined' && document.documentElement) {
    document.documentElement.setAttribute('data-theme', targetTheme);
  }
  if (typeof window !== 'undefined' && window.localStorage) {
    localStorage.setItem(THEME_STORAGE_KEY, targetTheme);
  }

  // Synchronize UI active classes on buttons and dots
  if (typeof document !== 'undefined') {
    document.querySelectorAll('.top-tdot, .theme-dot, .theme-btn').forEach((el) => {
      const btnTheme = el.getAttribute('data-theme');
      if (btnTheme === targetTheme) {
        el.classList.add('active');
      } else {
        el.classList.remove('active');
      }
    });
  }
}

export function toggleTheme(): Theme {
  const current = getTheme();
  const next: Theme = current === 'dark' ? 'light' : 'dark';
  setTheme(next);
  return next;
}

export function initTheme(): Theme {
  const initial = getTheme();
  setTheme(initial);
  return initial;
}

export function bindThemeControls(): void {
  if (typeof document === 'undefined') return;

  document.addEventListener('click', (e) => {
    const target = (e.target as HTMLElement)?.closest?.('.top-tdot, .theme-dot, .theme-btn') as HTMLElement | null;
    if (target) {
      const requestedTheme = target.getAttribute('data-theme') as Theme;
      if (requestedTheme && VALID_THEMES.includes(requestedTheme)) {
        setTheme(requestedTheme);
      }
    }
  });
}

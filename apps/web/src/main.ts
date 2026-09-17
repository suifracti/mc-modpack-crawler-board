/**
 * Main Frontend Entrypoint (Architecture V2 — Phase 3A).
 * Integrates TypeScript Domain Types, Repository Layer, Pure Utilities,
 * Theme State, and Legacy Dashboard Controller.
 */
import { setupLegacyBridge } from './legacy/legacyAdapter';
import { initLegacyDashboard } from './legacy/dashboard.legacy';

// 1. Setup global window bridge and theme system
const { repository } = setupLegacyBridge();

// 2. Export repository for modern ES module consumers
export { repository };

// 3. Initialize dashboard logic once DOM is ready
function runDashboard(): void {
  const win = window as unknown as { $: unknown; jQuery: unknown };
  if (typeof win.$ === 'function') {
    (win.$ as (handler: () => void) => void)(() => {
      initLegacyDashboard();
    });
  } else if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      initLegacyDashboard();
    });
  } else {
    initLegacyDashboard();
  }
}

runDashboard();

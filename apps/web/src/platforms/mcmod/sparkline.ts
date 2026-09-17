/**
 * Sparkline SVG Vector Generator (Architecture V2 — Phase 3B).
 * Pure TypeScript vector calculation producing identical visual traces.
 * ZERO external charting dependencies (no Chart.js, no ECharts).
 */

export function generateSparklineSvg(
  vals: number[] | null | undefined,
  width = 118,
  height = 34
): string {
  if (!vals || vals.length < 2) {
    return '';
  }

  const minV = Math.min(...vals);
  const maxV = Math.max(...vals);
  const vRange = maxV > minV ? maxV - minV : 1.0;
  const n = vals.length;

  const pts: [number, number][] = [];
  for (let i = 0; i < n; i++) {
    const x = Math.round(((i / (n - 1)) * 100.0) * 10) / 10;
    const y = Math.round((22.0 - ((vals[i] - minV) / vRange) * 20.0) * 10) / 10;
    pts.push([x, y]);
  }

  const lineD = 'M ' + pts.map(([x, y]) => `${x} ${y}`).join(' L ');
  const areaD = `${lineD} L ${pts[pts.length - 1][0]} 24 L ${pts[0][0]} 24 Z`;

  return (
    `<svg class="sparkline-svg" viewBox="0 0 100 24" width="${width}" height="${height}" style="opacity: 0.95;">` +
    `<path d="${areaD}" fill="rgba(var(--primary-rgb), 0.1)"></path>` +
    `<path d="${lineD}" fill="none" stroke="var(--primary)" stroke-width="2" stroke-linecap="round"></path>` +
    `</svg>`
  );
}

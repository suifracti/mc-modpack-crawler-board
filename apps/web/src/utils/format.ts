/**
 * Formatting and numeric helper utilities.
 * Extracted from dashboard.js.
 */

export function fmtBigNum(n: number | string | null | undefined): string {
  if (n === null || n === undefined || n === '') return '';
  const v = Number(n);
  if (!Number.isFinite(v)) return String(n);
  if (v >= 100000000) {
    return (v / 100000000).toFixed(2).replace(/\.?0+$/, '') + '亿';
  }
  if (v >= 10000) {
    return (v / 10000).toFixed(1).replace(/\.0$/, '') + '万';
  }
  return v.toLocaleString('zh-CN');
}

export function numFmt(n: number | string | null | undefined): string {
  if (n === null || n === undefined || n === '') return '—';
  const v = Number(n);
  if (!Number.isFinite(v)) return '—';
  return v.toLocaleString('zh-CN');
}

export function formatVFileSize(bytes: number | string | null | undefined): string {
  if (!bytes || isNaN(Number(bytes)) || Number(bytes) <= 0) return '';
  const b = Number(bytes);
  if (b >= 1073741824) return (b / 1073741824).toFixed(2) + ' GB';
  if (b >= 1048576) return (b / 1048576).toFixed(1) + ' MB';
  if (b >= 1024) return (b / 1024).toFixed(0) + ' KB';
  return b + ' B';
}

export function asArray<T>(v: T | T[] | null | undefined): T[] {
  if (!v) return [];
  return Array.isArray(v) ? v : [v];
}

export function getVPanClass(str: string | null | undefined): string {
  const s = String(str || '').toLowerCase();
  if (s.includes('quark') || s.includes('夸克')) return 'pan-btn-quark';
  if (s.includes('baidu') || s.includes('百度')) return 'pan-btn-baidu';
  if (s.includes('123')) return 'pan-btn-pan123';
  if (s.includes('xunlei') || s.includes('迅雷')) return 'pan-btn-xunlei';
  if (s.includes('lanzou') || s.includes('蓝奏')) return 'pan-btn-lanzou';
  if (s.includes('modrinth')) return 'pan-btn-modrinth';
  if (s.includes('curseforge')) return 'pan-btn-curseforge';
  return 'pan-btn-default';
}

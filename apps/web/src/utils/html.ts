/**
 * HTML escaping and string sanitization utilities.
 * Extracted from dashboard.js.
 */

export function escHtml(str: string | null | undefined, noFormat = false): string {
  if (str === null || str === undefined) return '';
  let raw: string;
  if (typeof document !== 'undefined' && typeof document.createElement === 'function') {
    const d = document.createElement('div');
    d.textContent = str;
    raw = d.innerHTML;
  } else {
    raw = String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  const LF = String.fromCharCode(10);
  const CR = String.fromCharCode(13);
  // This helper is also used in quoted HTML attributes.
  const text = raw.replace(/"/g, '&quot;').replace(/'/g, '&#39;')
    .split(CR + LF).join(LF).split(CR).join(LF);
  if (noFormat) {
    return text.split(LF).join('<br>');
  }
  return text;
}

export function escAttrJs(str: string | null | undefined): string {
  return escHtml(str || '', true)
    .replace(/<br>/g, '&#10;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/** An escaped href for public source links; reject executable URL schemes. */
export function safeExternalHref(value: unknown): string {
  try {
    const url = new URL(String(value || ''));
    if (url.protocol === 'http:' || url.protocol === 'https:') return escHtml(url.toString());
  } catch { /* Invalid source links remain inert. */ }
  return '#';
}

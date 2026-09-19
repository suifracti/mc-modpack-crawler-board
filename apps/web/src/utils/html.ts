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
  const text = raw.split(CR + LF).join(LF).split(CR).join(LF);
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

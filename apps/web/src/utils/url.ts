/**
 * URL sanitization and validation utilities.
 */

export function safeExternalUrl(value: unknown): string {
  try {
    const url = new URL(String(value || ''));
    return url.protocol === 'http:' || url.protocol === 'https:' ? url.toString() : '';
  } catch {
    return '';
  }
}

export function safeImageUrl(value: unknown): string {
  let text = String(value ?? '').trim();
  if (text.startsWith('//')) text = `https:${text}`;
  if (text.startsWith('data:image/')) return text;
  return safeExternalUrl(text);
}

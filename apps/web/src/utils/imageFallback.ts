const failedImageUrls = new Set<string>();

export function rememberFailedImage(url: string): void {
  const value = String(url || '').trim();
  if (value) failedImageUrls.add(value);
}

export function stableImageSource(url: string, fallback: string): string {
  const value = String(url || '').trim();
  return !value || failedImageUrls.has(value) ? fallback : value;
}

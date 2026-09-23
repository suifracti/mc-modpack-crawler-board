export type ImageFailureKind = 'error' | 'timeout' | 'cancelled';

export interface ImageFailure {
  kind: ImageFailureKind;
  retryAt: number;
  retries: number;
}

export type ImageRetryTicket = ImageFailure;

export const COVER_IMAGE_TIMEOUT_MS = 12_000;
export const COVER_IMAGE_RETRY_COOLDOWN_MS = 30_000;

const failedImageUrls = new Map<string, ImageFailure>();

export function rememberFailedImage(url: string, kind: ImageFailureKind = 'error'): void {
  const value = String(url || '').trim();
  if (!value) return;
  const previous = failedImageUrls.get(value);
  const retries = previous?.retries || 0;
  failedImageUrls.set(value, {
    kind,
    retries,
    retryAt: retries ? (previous?.retryAt || Date.now() + COVER_IMAGE_RETRY_COOLDOWN_MS) : Date.now(),
  });
}

export function clearFailedImage(url: string): void {
  const value = String(url || '').trim();
  if (!value) return;
  failedImageUrls.delete(value);
}

export function getImageFailure(url: string): ImageFailure | null {
  const value = String(url || '').trim();
  if (!value) return null;
  return failedImageUrls.get(value) || null;
}

export function canRetryImage(url: string): boolean {
  const failure = getImageFailure(url);
  return Boolean(failure && failure.retryAt <= Date.now());
}

export function imageRetryDelay(url: string): number {
  const failure = getImageFailure(url);
  return failure ? Math.max(0, failure.retryAt - Date.now()) : 0;
}

export function beginImageRetry(url: string): ImageRetryTicket | null {
  const value = String(url || '').trim();
  if (!value) return null;
  const previous = failedImageUrls.get(value);
  if (!previous || previous.retryAt > Date.now()) return null;
  failedImageUrls.set(value, {
    ...previous,
    retries: previous.retries + 1,
    retryAt: Date.now() + COVER_IMAGE_RETRY_COOLDOWN_MS,
  });
  return { ...previous };
}

export function cancelImageRetry(url: string, ticket: ImageRetryTicket): boolean {
  const value = String(url || '').trim();
  if (!value || !failedImageUrls.has(value)) return false;
  const current = failedImageUrls.get(value)!;
  failedImageUrls.set(value, { ...ticket, kind: current.kind });
  return true;
}

export function finishImageLoad(url: string): void {
  clearFailedImage(url);
}

export function stableImageSource(url: string, fallback: string): string {
  const value = String(url || '').trim();
  return !value || failedImageUrls.has(value) ? fallback : value;
}

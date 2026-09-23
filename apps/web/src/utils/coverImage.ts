import { escAttrJs, escHtml } from './html';
import {
  beginImageRetry,
  canRetryImage,
  cancelImageRetry,
  getImageFailure,
  stableImageSource,
  type ImageRetryTicket,
} from './imageFallback';

export type CoverImageState = 'loading' | 'loaded' | 'error' | 'timeout' | 'missing';

export interface CoverImageRequestTarget {
  isConnected: boolean;
  src: string;
  loading: 'lazy' | 'eager';
  dataset: { originalSrc?: string; fallbackSrc?: string; coverState?: string };
}

export interface CoverImageMarkup {
  state: CoverImageState;
  source: string;
  image: string;
  status: string;
  retryButton: string;
}

function safeCoverUrl(value: unknown): string {
  const text = String(value ?? '').trim();
  if (text.startsWith('data:image/')) return text;
  try {
    const url = new URL(text);
    return url.protocol === 'https:' || url.protocol === 'http:' ? text : '';
  } catch {
    return '';
  }
}

function statusText(state: CoverImageState): string {
  if (state === 'loading') return '封面加载中…';
  if (state === 'error') return '封面加载失败';
  if (state === 'timeout') return '封面加载超时';
  if (state === 'missing') return '来源未提供封面';
  return '';
}

export function renderCoverImage(options: {
  url: unknown;
  fallback: string;
  alt: string;
  key: string;
  className?: string;
}): CoverImageMarkup {
  const original = safeCoverUrl(options.url);
  const fallback = safeCoverUrl(options.fallback);
  const failure = getImageFailure(original);
  const state: CoverImageState = !original ? 'missing' : failure?.kind || 'loading';
  const source = stableImageSource(original, fallback);
  const image = `<img class="cover-image ${escAttrJs(options.className || '')}" data-cover-image="true" data-cover-key="${escAttrJs(options.key)}" data-cover-state="${state}" data-original-src="${escAttrJs(original)}" data-fallback-src="${escAttrJs(fallback)}" src="${escAttrJs(source)}" alt="${escAttrJs(options.alt)}" loading="lazy" referrerpolicy="no-referrer">`;
  const status = `<span class="cover-image-status" role="status" aria-live="polite">${escHtml(statusText(state))}</span>`;
  const retryable = Boolean(failure);
  const canRetry = retryable && canRetryImage(original);
  const retryLabel = canRetry ? '重试封面' : '稍后可重试';
  const retryButton = `<button type="button" class="cover-image-retry" data-action="retry-cover" aria-label="${escAttrJs(`${retryLabel}：${options.alt}`)}"${retryable ? '' : ' hidden'}${retryable && !canRetry ? ' disabled' : ''}>${retryLabel}</button>`;
  return { state, source, image, status, retryButton };
}

export function startCoverImageRetry(target: CoverImageRequestTarget): ImageRetryTicket | null {
  const original = safeCoverUrl(target.dataset.originalSrc);
  const ticket = original ? beginImageRetry(original) : null;
  if (!original || !ticket) return null;
  target.loading = 'eager';
  target.dataset.coverState = 'loading';
  target.src = original;
  return ticket;
}

export function releaseDetachedCoverImageRequest(
  target: CoverImageRequestTarget,
  ticket?: ImageRetryTicket,
): boolean {
  if (target.isConnected || target.dataset.coverState !== 'loading') return false;
  const original = safeCoverUrl(target.dataset.originalSrc);
  if (ticket && original) cancelImageRetry(original, ticket);
  return true;
}

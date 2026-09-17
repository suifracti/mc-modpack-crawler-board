import { describe, it, expect } from 'vitest';
import { escHtml, escAttrJs } from '../src/utils/html';
import { fmtBigNum, numFmt, formatVFileSize, asArray, getVPanClass } from '../src/utils/format';

describe('HTML Sanitization Utilities', () => {
  it('escHtml should escape dangerous HTML characters', () => {
    expect(escHtml('<script>alert("xss")</script>')).toBe('&lt;script&gt;alert("xss")&lt;/script&gt;');
    expect(escHtml('Tom & Jerry')).toBe('Tom &amp; Jerry');
    expect(escHtml('Plain text')).toBe('Plain text');
    expect(escHtml('')).toBe('');
    expect(escHtml(null)).toBe('');
    expect(escHtml(undefined)).toBe('');
  });

  it('escAttrJs should escape dangerous characters for inline JS string attributes', () => {
    expect(escAttrJs('alert("xss")')).toBe('alert(&quot;xss&quot;)');
    expect(escAttrJs("it's cool")).toBe('it&#39;s cool');
    expect(escAttrJs('<tag>')).toBe('&lt;tag&gt;');
    expect(escAttrJs('')).toBe('');
  });
});

describe('Formatting Utilities', () => {
  it('fmtBigNum formats counts into human-readable compact notation', () => {
    expect(fmtBigNum(0)).toBe('0');
    expect(fmtBigNum(999)).toBe('999');
    expect(fmtBigNum(1000)).toBe('1,000');
    expect(fmtBigNum(12500)).toBe('1.3万');
    expect(fmtBigNum(100000)).toBe('10万');
    expect(fmtBigNum(150000000)).toBe('1.5亿');
    expect(fmtBigNum(null)).toBe('');
    expect(fmtBigNum(undefined)).toBe('');
  });

  it('numFmt formats numbers with locale separators', () => {
    expect(numFmt(1234567)).toBe('1,234,567');
    expect(numFmt(0)).toBe('0');
    expect(numFmt(null)).toBe('0');
  });

  it('formatVFileSize formats byte sizes into B, KB, MB, GB', () => {
    expect(formatVFileSize(0)).toBe('');
    expect(formatVFileSize(500)).toBe('500 B');
    expect(formatVFileSize(1024)).toBe('1 KB');
    expect(formatVFileSize(1048576)).toBe('1.0 MB');
    expect(formatVFileSize(1073741824)).toBe('1.00 GB');
    expect(formatVFileSize(null)).toBe('');
    expect(formatVFileSize(-1)).toBe('');
  });

  it('asArray ensures array representation', () => {
    expect(asArray([1, 2, 3])).toEqual([1, 2, 3]);
    expect(asArray('foo')).toEqual(['foo']);
    expect(asArray(null)).toEqual([]);
    expect(asArray(undefined)).toEqual([]);
  });

  it('getVPanClass detects cloud drive brands', () => {
    expect(getVPanClass('百度网盘')).toBe('pan-btn-baidu');
    expect(getVPanClass('123云盘')).toBe('pan-btn-pan123');
    expect(getVPanClass('夸克网盘')).toBe('pan-btn-quark');
    expect(getVPanClass('未知网盘')).toBe('pan-btn-default');
  });
});

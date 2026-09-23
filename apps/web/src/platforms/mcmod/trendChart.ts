export interface McmodTrendPoint {
  date: string;
  value: number;
}

export type McmodTrendRange = '7d' | '30d' | '60d' | 'all';
export type McmodTrendStatus = 'missing' | 'mismatch' | 'invalid-order' | 'insufficient' | 'ready';

export interface McmodTrendSeries {
  status: McmodTrendStatus;
  points: McmodTrendPoint[];
  skippedCount: number;
}

export interface McmodTrendSummary {
  count: number;
  latest: number;
  minimum: number;
  maximum: number;
  average: number;
  firstDate: string;
  lastDate: string;
}

const RANGE_DAYS: Record<Exclude<McmodTrendRange, 'all'>, number> = {
  '7d': 7,
  '30d': 30,
  '60d': 60,
};

function splitCsv(value: unknown): string[] {
  if (typeof value !== 'string' || !value.length) return [];
  return value.split(',');
}

function validIsoDate(value: string): boolean {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) return false;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  if (month < 1 || month > 12 || day < 1) return false;
  const leapYear = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const daysInMonth = [31, leapYear ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1];
  return day <= daysInMonth;
}

function parseTrendValue(value: string): number | null {
  const text = value.trim();
  if (!text || !/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$/.test(text)) return null;
  const parsed = Number(text);
  return Number.isFinite(parsed) ? parsed : null;
}

export function parseMcmodTrendSeries(valuesInput: unknown, datesInput: unknown): McmodTrendSeries {
  const values = splitCsv(valuesInput);
  const dates = splitCsv(datesInput);
  if (!values.length && !dates.length) return { status: 'missing', points: [], skippedCount: 0 };
  if (values.length !== dates.length) return { status: 'mismatch', points: [], skippedCount: 0 };

  const points: McmodTrendPoint[] = [];
  let skippedCount = 0;
  for (let index = 0; index < dates.length; index += 1) {
    const date = dates[index].trim();
    const valueText = values[index];
    const value = parseTrendValue(valueText);
    if (!date || value === null || !validIsoDate(date)) {
      skippedCount += 1;
      continue;
    }
    if (points.length && date <= points[points.length - 1].date) {
      return { status: 'invalid-order', points: [], skippedCount };
    }
    points.push({ date, value });
  }

  return {
    status: points.length >= 2 ? 'ready' : 'insufficient',
    points,
    skippedCount,
  };
}

export function selectMcmodTrendRange(points: McmodTrendPoint[], range: McmodTrendRange): McmodTrendPoint[] {
  if (range === 'all' || !points.length) return points;
  const newest = Date.parse(`${points[points.length - 1].date}T00:00:00Z`);
  const firstIncluded = newest - (RANGE_DAYS[range] - 1) * 24 * 60 * 60 * 1000;
  return points.filter((point) => {
    const timestamp = Date.parse(`${point.date}T00:00:00Z`);
    return timestamp >= firstIncluded && timestamp <= newest;
  });
}

export function summarizeMcmodTrend(points: McmodTrendPoint[]): McmodTrendSummary | null {
  if (!points.length) return null;
  const values = points.map((point) => point.value);
  return {
    count: points.length,
    latest: points[points.length - 1].value,
    minimum: values.reduce((current, value) => Math.min(current, value), Number.POSITIVE_INFINITY),
    maximum: values.reduce((current, value) => Math.max(current, value), Number.NEGATIVE_INFINITY),
    average: values.reduce((total, value) => total + value, 0) / values.length,
    firstDate: points[0].date,
    lastDate: points[points.length - 1].date,
  };
}

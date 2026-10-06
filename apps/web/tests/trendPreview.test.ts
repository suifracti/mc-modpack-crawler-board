import {describe,it,expect} from 'vitest';
import {generateSparklineSvg} from '../src/platforms/mcmod/sparkline';
import {parseMcmodTrendSeries,selectMcmodTrendRange} from '../src/platforms/mcmod/trendChart';
describe('trend previews',()=>{
 it('uses the full available plot width and retains the last source point',()=>{
  const svg=generateSparklineSvg([444,100,43]);
  expect(svg).toContain('preserveAspectRatio="none"');
  expect(svg).toContain('100 22');
 });
 it('preserves valid later points and ends a range at the latest real observation rather than today',()=>{
  const series=parseMcmodTrendSeries('444,100,43','2026-09-20,2026-09-21,2026-09-22');
  expect(series.status).toBe('ready');
  expect(selectMcmodTrendRange(series.points,'7d').at(-1)).toEqual({date:'2026-09-22',value:43});
 });
});

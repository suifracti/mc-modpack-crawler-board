import {describe,it,expect} from 'vitest';
import {formatAuditTime,renderAuditHistory,renderAuditPlatformTimes,renderAuditChanges} from '../src/domain/auditHistory';
describe('audit history presentation',()=>{
 it('shows precise Beijing collection times and distinct task counts',()=>{
  const history=[0,1,2,3,4].map(i=>({snapshotId:`s${i}`,stats:{added_count:10-i,updated_count:i},platform_updates:{curseforge:{startedAt:`2026-10-0${6-i}T05:28:40.289Z`,finishedAt:`2026-10-0${6-i}T05:29:30.811Z`,updatedAt:`2026-10-0${6-i}T05:30:12Z`,baselineAt:'2026-10-01T00:00:00Z',stats:{added_count:10-i}}}}));
  const html=renderAuditHistory(history,1);
  expect(html).toContain('每次更新');expect(html).toContain('共 5 次');expect(html).toContain('value="s4"');
  expect(html).toContain('2026-10-06 13:29:30');expect(html).toContain('新增 9');expect(html).toContain('value="s1" selected');
  const times=renderAuditPlatformTimes(history[0].platform_updates);expect(times).toContain('采集开始');expect(times).toContain('2026-10-06 13:28:40');expect(times).toContain('2026-10-01 08:00:00');
 });
 it('does not label missing historical tasks as zero changes or infer collection start from publication time',()=>{
  expect(renderAuditHistory([],null)).toContain('没有可读取');
  expect(formatAuditTime(null)).toBe('未记录');expect(formatAuditTime('2026-10-06')).toContain('时区未注明');
 });
 it('shows readable before and after values and escapes source text',()=>{
  const html=renderAuditChanges({changes:{title:{before:'<script>old</script>',after:'新标题'},view:{before:'10',after:'12'},versions:{before:['minecraft:1.20.1'],after:['minecraft:1.20.1','minecraft:1.21.1']}}});
  expect(html).toContain('标题');expect(html).toContain('播放量');expect(html).toContain('更新前');expect(html).toContain('更新后');
  expect(html).toContain('10');expect(html).toContain('12');expect(html).toContain('1.21.1');
  expect(html).not.toContain('<script>');expect(html).toContain('&lt;script&gt;');
 });
 it('does not invent previous values for legacy entries without a detailed diff',()=>{
  const html=renderAuditChanges({changedFields:['title','view']});
  expect(html).toContain('标题');expect(html).toContain('播放量');expect(html).toContain('未保存前后值');
 });
});

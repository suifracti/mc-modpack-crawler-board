import {describe,it,expect} from 'vitest';
import {planPlatformUpdate} from '../src/domain/updatePlans';
describe('one update center for all six platforms',()=>{
 it('daily CF uses recent public catalogue while B rotates an existing batch',()=>{
  expect(planPlatformUpdate('curseforge','daily-fast',50)).toEqual({platform:'curseforge',options:{mode:'recent',pages:2}});
  expect(planPlatformUpdate('bilibili','daily-fast',50)).toEqual({platform:'bilibili',options:{mode:'catalog',limit:30}});
 });
 it('catalog checks have explicit modes and no daily CF cap',()=>{
  expect(planPlatformUpdate('curseforge','full-catalog',50).options).toEqual({mode:'catalog'});
  expect(planPlatformUpdate('bilibili','full-catalog',50).options).toEqual({mode:'catalog',limit:5000});
 });
 it('version enrichment remains a separate existing-data mode',()=>{
  expect(planPlatformUpdate('curseforge','enrich-versions',150).options).toEqual({mode:'existing',limit:150});
  expect(planPlatformUpdate('bilibili','enrich-versions',150).options).toEqual({mode:'existing',limit:30});
 });
 it('plans are independent of later UI scenario changes',()=>{
  const a=planPlatformUpdate('mcmod','daily-fast',50);planPlatformUpdate('mcmod','full-catalog',300);
  expect(a.options).toEqual({mode:'new'});
  expect(planPlatformUpdate('modrinth','daily-fast',50).options).toEqual({mode:'catalog',limit:100});
 });
});

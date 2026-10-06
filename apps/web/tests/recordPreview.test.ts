import {describe,it,expect} from 'vitest';
import * as previewModule from '../src/domain/recordPreview';
import type {DesktopRecord} from '../src/desktopShell-v2';
import type {RecordPreview} from '../src/domain/recordPreview';
const record = {id:'mcmod:1261',platform:'mcmod',sourceId:'1261',url:'https://www.mcmod.cn/modpack/1261.html',title:'虚饰作品',author:'',sourceIdOrigin:'source',versions:[],loaders:[],categories:[],updatedAt:'',coverUrl:'',environment:{status:'unknown',certainty:'unknown',label:'未知',sourceField:null},searchText:'',evidence:[],summary:'',releases:[{id:'existing'}],raw:{gallery:['https://i.mcmod.cn/cover.jpg']}} as DesktopRecord;
const preview:RecordPreview={platform:'mcmod',sourceId:'1261',sourceUrl:record.url,archivedAt:'2026-09-28',description:'已有完整正文',images:['https://i.mcmod.cn/one.webp'],releases:[]};
describe('local preview merge',()=>{
 it('restores archived text and images while retaining existing releases',()=>{
  expect(typeof previewModule.mergeRecordPreview).toBe('function');
  const merged=previewModule.mergeRecordPreview(record,preview);
  expect(merged.raw.description).toBe('已有完整正文');
  expect(merged.raw.gallery).toEqual(['https://i.mcmod.cn/cover.jpg','https://i.mcmod.cn/one.webp']);
  expect(merged.releases).toEqual(record.releases);
 });
 it('never attaches another source archive or replaces fuller text with an excerpt',()=>{
  expect(typeof previewModule.mergeRecordPreview).toBe('function');
  expect(previewModule.mergeRecordPreview(record,{...preview,sourceId:'999'})).toBe(record);
  const full={...record,raw:{description:'来源的详细正文比存档摘录更长'}};
  expect(previewModule.mergeRecordPreview(full,{...preview,description:'摘录'}).raw.description).toBe(full.raw.description);
 });
});

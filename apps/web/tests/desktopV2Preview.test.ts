import {describe,it,expect,beforeAll,afterAll,vi} from 'vitest';
import {renderRecord,recordImageUrls,renderCompactRecord,renderInAppSideContent,bindActionButtons,type DesktopRecord} from '../src/desktopShell-v2';
beforeAll(()=>vi.stubGlobal('document',{documentElement:{dataset:{}}}));
afterAll(()=>vi.unstubAllGlobals());
const record:DesktopRecord={id:'mcmod:1261',platform:'mcmod',sourceId:'1261',sourceIdOrigin:'source',title:'虚饰作品',author:'未知',url:'https://www.mcmod.cn/modpack/1261.html',summary:'',versions:['1.20.1'],loaders:[],categories:[],updatedAt:'',coverUrl:'',environment:{status:'unknown',certainty:'unknown',label:'未知',sourceField:null},releases:[],raw:{trendStats:{trendValsStr:'400,300,43',trendDatesStr:'2026-09-20,2026-09-21,2026-09-22'}},searchText:'',evidence:[]};
describe('V2 trend placements',()=>{
 it('search replacement rows keep their own clickable preview actions',()=>{
  const dispatch=vi.fn();
  const row=()=>{let click:(event:Event)=>void;return {dataset:{action:'open-in-app-window',url:'https://www.bilibili.com/video/BV1234567890/'},addEventListener:(_event:string,fn:(event:Event)=>void)=>{click=fn;},press:()=>click(new Event('click')),textContent:'',title:''};};
  const first=row(),replacement=row();
  for(const button of [first,replacement])bindActionButtons({querySelectorAll:()=>[button]} as unknown as ParentNode,dispatch);
  replacement.press();expect(dispatch).toHaveBeenCalledOnce();expect(dispatch.mock.calls[0][0]).toBe(replacement);expect(replacement.textContent).toBe('🪟 B站资料小窗');
 });
 it('lists a Bilibili cover once rather than thumbnail and original as separate pictures',()=>{
  const bili={...record,platform:'bilibili' as const,raw:{pic:'http://i1.hdslb.com/bfs/archive/cover.jpg'}};
  expect(recordImageUrls(bili)).toEqual(['https://i1.hdslb.com/bfs/archive/cover.jpg']);
 });
 it.each([['card',renderRecord],['compact',renderCompactRecord]])('shows real trend and latest date in %s view',(_name,render)=>{
  const html=render(record,0);expect(html).toContain('data-action="open-mcmod-trend"');expect(html).toContain('2026-09-22');expect(html).toContain('指数 43');expect(html).toContain('sparkline-svg');
 });
 it('retains trend in the window sidebar and does not invent trends for other sources',()=>{
  expect(renderInAppSideContent(record)).toContain('2026-09-22');
  expect(renderRecord({...record,platform:'bilibili',id:'bilibili:BV0001'},0)).not.toContain('open-mcmod-trend');
 });
});

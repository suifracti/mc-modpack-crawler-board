import {it,expect,beforeAll,afterAll,vi} from 'vitest';
import {renderBiliFlatCard} from '../src/platforms/bilibili/renderer';
import {classifyBilibiliContent,bilibiliContentScope} from '../../shared/bilibili-content.cjs';
import {queryStaticRecords} from '../src/pagesQuery';
beforeAll(()=>vi.stubGlobal('document',{documentElement:{dataset:{}}}));afterAll(()=>vi.unstubAllGlobals());
it('current public excerpt overrides an older archived description for content filtering',()=>{
 const row={title:'我的世界 怪物大乱斗:重生整合包分享 支持手机版fcl启动器',raw:{desc:'整合包包含100个模组 https://www.mcmod.cn/modpack/123.html',description_excerpt_observed:true,description_excerpt:'三连+关注后自动发送更多整合包！！！\n本次整合包 https://pan.quark.cn/s/example'}};
 expect(classifyBilibiliContent(row).candidate).toBe(false);
});
it('local card labels archived description time as a record rather than an author release update',()=>{
 const html=renderBiliFlatCard({bvid:'BV1ZxaS6nEoh',title:'MC整合包分享',author:'fixture',pub_time:'2026-10-02 18:09',desc_updated_at:'2026-02-06 18:21'} as any,{});
 expect(html).not.toContain('简介更新:');expect(html).toContain('简介记录:');expect(html).toContain('视频发布:');
});
it('sharing a project link does not promote a repost into an original Bilibili release',()=>{
 for(const title of ['我的世界整合包分享 支持手机版','转载 MC整合包发布：星港','我的世界整合包更新推荐：星港','MC 分享作者自制的整合包 星港','MC 推荐这款原创整合包 星港','【籽岷/MC】籽岷看小水滴大佬制作的脑叶公司整合包2.0预告']) {
  const decision=classifyBilibiliContent({title,raw:{desc:'https://www.mcmod.cn/modpack/123.html'}});
  expect(decision.kind).toBe('showcase');expect(bilibiliContentScope(decision)).toBe('secondary');
 }
 expect(bilibiliContentScope(classifyBilibiliContent({title:'MC 我制作的整合包分享：星港'}))).toBe('candidates');
 expect(bilibiliContentScope(classifyBilibiliContent({title:'MC 不是我制作的整合包分享：星港'}))).toBe('secondary');
});
it('older explicit admission refusals remain excluded after a policy upgrade',()=>{
 expect(bilibiliContentScope(classifyBilibiliContent({title:'MC整合包发布：星港',raw:{content_policy_schema:8,content_candidate:false,content_category:'promotion',content_reason:'已有公开HTML拒绝证据'}}))).toBe('excluded');
});
it('static browsing filters release and secondary scopes before pagination and keeps all archives',async()=>{
 const rows=[{title:'MC整合包发布：星港',sourceId:'release'},{title:'我的世界整合包分享 星港',sourceId:'share'},{title:'MC整合包实况 第2期',sourceId:'play'}].map(r=>({...r,platform:'bilibili',id:'bilibili:'+r.sourceId,raw:{},summary:'',versions:[],loaders:[],categories:[]}));
 const cache={normalized:rows,result:{sourceFile:"fixture",error:null}};const entries: Record<string,unknown>={};
 const result=await queryStaticRecords('bilibili',{pageSize:1,bilibiliContent:'candidates'},cache,entries);
 expect(result.total).toBe(1);expect(result.records[0].sourceId).toBe('release');
 const secondary=await queryStaticRecords('bilibili',{bilibiliContent:'secondary'},cache,entries);
 expect(secondary.total).toBe(1);expect(secondary.records[0].sourceId).toBe('share');
 expect(result.bilibiliCounts).toEqual({all:3,candidates:1,secondary:1,excluded:1});
 expect((await queryStaticRecords('bilibili',{bilibiliContent:'all'},cache,entries)).total).toBe(3);
});

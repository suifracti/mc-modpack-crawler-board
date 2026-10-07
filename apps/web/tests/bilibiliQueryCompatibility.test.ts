import {it,expect} from 'vitest';
import {createBilibiliCompatibleQuery} from '../src/domain/bilibiliQueryCompatibility';
it('filters an older live server archive across pages and reuses an immutable snapshot cache',async()=>{
 const rows=Array.from({length:2001},(_,i)=>({id:'bilibili:'+i,sourceId:String(i),platform:'bilibili',title:i===2000?'MC整合包发布：永生':'我的世界整合包分享 星港',raw:{},summary:'',versions:[],loaders:[],categories:[]}));
 const calls: any[]=[];
 const query=createBilibiliCompatibleQuery(async options=>{
  calls.push(options);const size=options.pageSize||48,page=options.page||1;
  return {platform:'bilibili',sourceFile:'snapshot/1',total:rows.length,page,pageSize:size,records:rows.slice((page-1)*size,page*size),bilibiliCounts:{all:2001,candidates:2001,excluded:0},availableVersions:[],availableLoaders:[],availableCategories:[],availableIncludedMods:[],availableGameplayCategories:[],availablePans:[]} as any;
 },async()=>({'bilibili:2000':{favorite:true}} as any),async()=> 'snapshot/1');
 const primary=await query({bilibiliContent:'candidates',pageSize:1});
 expect(primary.total).toBe(1);expect(primary.records[0].sourceId).toBe('2000');
 expect(calls.filter(c=>c.bilibiliContent==='all').length).toBe(2);
 const secondary=await query({bilibiliContent:'secondary',pageSize:1});expect(secondary.total).toBe(2000);
 expect(calls.filter(c=>c.bilibiliContent==='all').length).toBe(2);
 const favorite=await query({bilibiliContent:'candidates',personalStatus:'favorite'});expect(favorite.total).toBe(1);
});
it('refuses to join pages from different snapshots',async()=>{
 let calls=0;
 const query=createBilibiliCompatibleQuery(async()=>({platform:'bilibili',sourceFile:'bili_data.js',records:[],total:0,page:1,pageSize:2000} as any),async()=>({}),async()=> ++calls===1?'old':'new');
 await expect(query({bilibiliContent:'candidates'})).rejects.toThrow('快照正在切换');
});

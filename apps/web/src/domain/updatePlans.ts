import type {Platform} from './types';
export type UpdateScenario='daily-fast'|'enrich-versions'|'full-catalog';
export interface PlatformUpdatePlan {platform:Platform;options?:{mode?:string;limit?:number;pages?:number}}
export interface UpdateBatchStatus {
 state:'running'|'completed'|'cancelled';total:number;completed:number;
 platforms?:Platform[];
 results:Array<{platform:Platform;state:string;error?:string|null;endedAt?:string;result?:Record<string,unknown>}>;
}
export function planPlatformUpdate(platform:Platform,scenario:UpdateScenario,enrichSize=50):PlatformUpdatePlan {
 if(platform==='bilibili')return {platform,options:scenario==='enrich-versions'?{mode:'existing',limit:30}:{mode:'catalog',limit:scenario==='full-catalog'?5000:30}};
 if(scenario==='enrich-versions')return {platform,options:{mode:platform==='mcmod'?'versions':'existing',limit:enrichSize}};
 if(platform==='curseforge')return {platform,options:scenario==='full-catalog'?{mode:'catalog'}:{mode:'recent',pages:2}};
 if(platform==='mcmod')return {platform,options:scenario==='full-catalog'?{mode:'all',limit:50}:{mode:'new'}};
 return {platform,options:{mode:'catalog',limit:scenario==='full-catalog'?1000:100}};
}

import {it,expect} from 'vitest';
import {downloadSourceLabels} from '../src/domain/downloadSources';
it('labels actual clouds and site file hosts, including links inside releases',()=>{
 expect(downloadSourceLabels({platform:'bbsmc',raw:{download_links:[{url:'https://pan.baidu.com/s/abc'},{url:'https://pan.quark.cn/s/def'}],versions_data:[{files:[{url:'https://cdn.bbsmc.net/files/pack.mrpack'}]}]}})).toEqual(['百度网盘','夸克网盘','BBSMC 站内文件']);
});
it('does not invent a file download from an original page or a cloud lookalike hostname',()=>{
 expect(downloadSourceLabels({platform:'bilibili',url:'https://www.bilibili.com/video/BV1234567890/',raw:{}})).toEqual(['原视频页面（未收录下载链接）']);
 expect(downloadSourceLabels({platform:'mcmod',raw:{download_links:[{url:'https://pan.baidu.com.evil.invalid/s/abc'}]}})).toEqual(['外部链接']);
 expect(downloadSourceLabels({platform:'curseforge',raw:{download_links:[{url:'https://www.curseforge.com/minecraft/modpacks/the-fool'}]}})).toEqual(['CurseForge 原站页面']);
});

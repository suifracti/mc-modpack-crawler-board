/** Labels describe saved links, never an assumed download behind a project page. */
export function downloadSourceLabels(record: {platform: string; url?: string; raw?: Record<string, unknown>; releases?: unknown[]}): string[] {
 const labels=new Set<string>();
 const visit=(value: unknown, depth=0): void=>{
  if(depth>5 || !value || typeof value!=='object')return;
  if(Array.isArray(value)){value.forEach(x=>visit(x,depth+1));return;}
  const item=value as Record<string,unknown>;
  const link=item.url || item.downloadUrl || item.download_url;
  if(typeof link==='string') {
   try {
    const parsed=new URL(link);if(!['https:','http:'].includes(parsed.protocol))return;
    const host=parsed.hostname.toLowerCase(), inDomain=(domain:string)=>host===domain || host.endsWith('.'+domain);
    if(host==='pan.baidu.com')labels.add('百度网盘');
    else if(host==='pan.quark.cn')labels.add('夸克网盘');
    else if(['123pan.com','123684.com','123865.com','123912.com'].some(inDomain))labels.add('123云盘');
    else if(['alipan.com','aliyundrive.com'].some(inDomain))labels.add('阿里云盘');
    else if(host==='pan.xunlei.com')labels.add('迅雷云盘');
    else if(host==='drive.google.com')labels.add('Google Drive');
    else if(host==='github.com')labels.add('GitHub');
    else if(inDomain('mediafire.com'))labels.add('MediaFire');
    else if(host==='mega.nz')labels.add('MEGA');
    else if(host==='1drv.ms' || inDomain('onedrive.live.com'))labels.add('OneDrive');
    else if(['lanzou.com','lanzoui.com','lanzoux.com','lanzouj.com','lanzouf.com','lanzouv.com'].some(inDomain))labels.add('蓝奏云');
    else if(host==='cdn.bbsmc.net')labels.add('BBSMC 站内文件');
    else if(host==='cdn.modrinth.com')labels.add('Modrinth 文件');
    else if(inDomain('forgecdn.net'))labels.add('CurseForge 文件');
    else if(inDomain('modrinth.com'))labels.add('Modrinth 原站页面');
    else if(inDomain('curseforge.com'))labels.add(/\/download(?:\/|$)|\/files\//.test(parsed.pathname)?'CurseForge 文件页面':'CurseForge 原站页面');
    else if(inDomain('bbsmc.net'))labels.add('BBSMC 原站页面');
    else if(inDomain('xyebbs.com'))labels.add(/\/download(?:\/|$)/.test(parsed.pathname)?'XYEBBS 站内下载':'XYEBBS 原站页面');
    else if(inDomain('mcmod.cn'))labels.add('MC百科原站页面');
    else if(inDomain('bilibili.com'))labels.add('原视频页面');
    else labels.add('外部链接');
   }catch { /* Invalid link provides no source evidence. */ }
  }
  for(const key of ['files','links','downloads','download_links','downloadLinks','releases','versions_data','releases_data','versions'])visit(item[key],depth+1);
 };
 const raw=record.raw || {};
 for(const key of ['download_links','downloadLinks','releases','versions_data','releases_data'])visit(raw[key]);
 visit(record.releases);
 return labels.size?[...labels]:[record.platform==='bilibili'?'原视频页面（未收录下载链接）':'原站页面（未收录下载链接）'];
}

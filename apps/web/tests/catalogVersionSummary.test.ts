import {it,expect} from 'vitest';
import {renderCatalogVersionSummary,type DesktopRecord} from '../src/desktopShell-v2';
it('shows public cache version evidence without inventing original file history',()=>{
 const record={platform:'curseforge',raw:{catalog_latest_version:{provider:'modpacks-ch',name:'Pack v0.3 <img>',updatedAt:'2026-09-30'}}} as unknown as DesktopRecord;
 const html=renderCatalogVersionSummary(record);expect(html).toContain('第三方目录版本摘要');expect(html).toContain('Pack v0.3 &lt;img&gt;');expect(html).toContain('原站文件历史另列');
 expect(renderCatalogVersionSummary({...record,platform:'mcmod'})).toBe('');
});

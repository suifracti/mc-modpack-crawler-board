interface AuditStats { [key:string]: unknown }
export interface AuditPlatformUpdate {
 snapshotId?:string; baselineSnapshotId?:string; updatedAt?:string|null; baselineAt?:string|null;
 startedAt?:string|null; finishedAt?:string|null; outcome?:string|null; coverage?:string|null; stats?:AuditStats;
}
export interface AuditHistorySummary {
 snapshotId?:string; baselineSnapshotId?:string; scope?:string; stats?:AuditStats|null;
 platform_updates?:Record<string,AuditPlatformUpdate>;
}
const names:Record<string,string>={mcmod:'MC百科',bilibili:'B站',bbsmc:'BBSMC',xyebbs:'XYEBBS',modrinth:'Modrinth',curseforge:'CurseForge'};
const esc=(v:unknown)=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]!));
export function formatAuditTime(value?:string|null):string {
 if(!value) return '未记录';
 if(!/(?:Z|[+-]\d\d:\d\d)$/.test(value)) return `${value}（时区未注明）`;
 const date=new Date(value);if(!Number.isFinite(date.getTime()))return '时间不可读';
 return new Intl.DateTimeFormat('sv-SE',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).format(date);
}
export function renderAuditHistory(history:AuditHistorySummary[],selected:number|string|null):string {
 if(!history.length)return '<div class="empty-evidence">没有可读取的本地更新记录，不能计算逐次变动。</div>';
 return `<div class="audit-history-picker"><label>每次更新记录 · 共 ${history.length} 次<select class="field js-audit-history-select" aria-label="选择更新记录">${history.map((entry,i)=>{
  const updates=entry.platform_updates||{},items=Object.values(updates),stats=entry.stats||{};
  const when=items.map(x=>x.finishedAt||x.updatedAt).filter(Boolean).sort().at(-1);
  return `<option value="${esc(entry.snapshotId)}"${selected===i||selected===entry.snapshotId?' selected':''}>${i===0?'最新一次 · ':''}${esc(formatAuditTime(when))} · ${esc(Object.keys(updates).map(p=>names[p]||p).join('、'))} · 新增 ${Number(stats.added_count||0).toLocaleString()} / 更新 ${Number(stats.updated_count||0).toLocaleString()} / 补版本 ${Number(stats.version_gained_count||0).toLocaleString()} / 移除 ${Number(stats.removed_count||0).toLocaleString()}</option>`;
 }).join('')}</select></label><button type="button" class="button secondary small" data-action="select-audit-round" data-round="0">最新一次</button></div>`;
}

const fieldNames:Record<string,string>={title:'标题',author:'作者',url:'来源网址',summary:'简介 / 正文',updatedAt:'来源更新时间',coverUrl:'封面',loaders:'Loader',categories:'分类',serverStatus:'服务端状态',downloads:'下载量',download_count:'下载量',views:'播放量',view:'播放量',likes:'点赞',favorites:'收藏',follows:'关注',versions:'版本 / 下载证据'};
const displayValue=(value:unknown):string=>value===null||value===undefined?'未收录':Array.isArray(value)?(value.length?value.map(String).join('、'):'未收录'):String(value)||'空';
export function renderAuditChanges(item:Record<string,unknown>):string {
 const changes=item.changes && typeof item.changes==='object'?Object.entries(item.changes as Record<string,{before:unknown;after:unknown}>):[];
 if(changes.length) return `<details class="audit-field-changes"><summary>具体变化：${esc(changes.map(([key])=>fieldNames[key]||key).join('、'))}</summary><div class="audit-change-columns"><span>更新前</span><span>更新后</span></div>${changes.map(([key,value])=>`<div class="audit-field-change"><strong>${esc(fieldNames[key]||key)}</strong><div class="audit-change-columns"><pre>${esc(displayValue(value.before))}</pre><pre>${esc(displayValue(value.after))}</pre></div></div>`).join('')}</details>`;
 const fields=Array.isArray(item.changedFields)?item.changedFields.map(String):[];
 return fields.length?`<p class="audit-list-count">变化：${esc(fields.map(key=>fieldNames[key]||key).join('、'))}（此历史记录未保存前后值）</p>`:'';
}
export function renderAuditPlatformTimes(updates:Record<string,AuditPlatformUpdate>={}):string {
 const rows=Object.entries(updates);if(!rows.length)return '';
 return `<details class="audit-timing" open><summary>各站独立统计与时间（北京时间 UTC+8）</summary><div class="audit-timing-scroll"><table><thead><tr><th>站点 / 实际范围</th><th>采集开始 → 结束</th><th>基线 → 快照保存</th><th>新增 / 更新 / 补版本 / 移除</th></tr></thead><tbody>${rows.map(([p,v])=>{
 const s=v.stats||{},coverage=v.coverage==='public-video-html-bounded'?'公开视频局部核验':v.coverage==='known-project-cached-metadata-only'?'已知 ID 缓存':v.coverage==='third-party-catalog'?'第三方目录':v.coverage==='third-party-details'?'新增项目资料补充':v.outcome==='partial_update'?'局部更新':'本次保存结果';
 return `<tr><th>${esc(names[p]||p)}<small>${esc(coverage)}</small></th><td>${esc(formatAuditTime(v.startedAt))}<br>→ ${esc(formatAuditTime(v.finishedAt))}</td><td title="${esc(v.baselineSnapshotId)} → ${esc(v.snapshotId)}">${esc(formatAuditTime(v.baselineAt))}<br>→ ${esc(formatAuditTime(v.updatedAt))}</td><td>${['added_count','updated_count','version_gained_count','removed_count'].map(k=>Number(s[k]||0).toLocaleString()).join(' / ')}</td></tr>`;
 }).join('')}</tbody></table></div></details>`;
}

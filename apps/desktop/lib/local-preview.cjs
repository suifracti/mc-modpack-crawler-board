const fs = require('node:fs/promises');
const path = require('node:path');

const text = value => typeof value === 'string' ? value.trim() : '';
function safeUrl(value) {
 try {const url = new URL(String(value)); return ['https:', 'http:'].includes(url.protocol) ? url.href : '';}catch {return '';}
}
function images(value) {
 if (Array.isArray(value)) return value.flatMap(images);
 if (value && typeof value === 'object') return images(value.url || value.src || value.image || value.full || '');
 const url = safeUrl(value);return url ? [url] : [];
}
function descriptionImages(description) {
 const found=[];
 for (const match of description.matchAll(/!\[[^\]]*\]\(\s*(?:<([^>\n]+)>|([^\s)]+))(?:\s+["'][^"'\n]*["'])?\s*\)/g)) found.push(match[1] || match[2]);
 for (const match of description.matchAll(/<img\b[^>]*\bsrc=["']([^"']+)["']/gi)) found.push(match[1].replace(/&amp;/g,'&'));
 return images(found);
}
async function readJson(file) {
 try {return JSON.parse((await fs.readFile(file,'utf8')).replace(/^\uFEFF/,''));}
 catch(error) {if(error.code === 'ENOENT') return null;throw error;}
}
async function readLocalPreview(snapshotDir, manifest, record) {
 const platform = record.platform, id = record.sourceId;
 const rawFile = path.join(snapshotDir,'crawler_output',`${platform}_modpacks.json`);
 const rows = platform === 'mcmod' ? await readJson(rawFile) : null;
 const row = Array.isArray(rows) ? rows.find(r => String(r.project_id ?? r.mid ?? r.bvid ?? r.id ?? '') === id) : null;
 // A matching number with a conflicting origin URL is not the same source.
 const usable = row && (!row.url || safeUrl(row.url) === safeUrl(record.url)) ? row : {};
 let detail = {...record.raw, ...usable};
 if (platform === 'mcmod') {
  const cache = await readJson(path.join(snapshotDir,'crawler_output','mcmod_details_cache.json'));
  const found = cache?.[id];
  if (found && (!found.url || safeUrl(found.url) === safeUrl(record.url))) detail = {...usable, ...found};
 }
 const candidates = [detail.text, detail.description, detail.desc, detail.intro, record.summary].map(text);
 const description = candidates.reduce((best, value) => value.length > best.length ? value : best, '');
 const imageUrls = [...new Set([...images([detail.images,detail.intro_images,detail.gallery,detail.featured_gallery,record.raw.images,record.raw.intro_images,record.raw.gallery]),...descriptionImages(description)])];
 const releases = [record.releases,usable.releases,usable.versions_data,usable.releases_data,usable.version_history]
  .find(items => Array.isArray(items) && items.length) || [];
 return {versions:releases,provider:'local-snapshot',fetchedAt:manifest.updatedAt || manifest.createdAt || '',
  preview:{platform,sourceId:id,sourceUrl:record.url,archivedAt:manifest.updatedAt || manifest.createdAt || '',description,images:imageUrls,releases}};
}
module.exports = {readLocalPreview};

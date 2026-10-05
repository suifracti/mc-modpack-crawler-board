// Read an explicitly selected historical public archive; never instantiate DataStore.
const fs = require('node:fs');
const path = require('node:path');
const zlib = require('node:zlib');
const platforms = ['mcmod', 'bilibili', 'bbsmc', 'xyebbs', 'modrinth', 'curseforge'];
const readJson = p => JSON.parse(fs.readFileSync(p, 'utf8').replace(/^\uFEFF/, ''));
const sourceId = row => String(row.project_id ?? row.mid ?? row.bvid ?? row.id ?? '');
const text = value => typeof value === 'string' ? value.trim() : '';
function safeUrl(value) {
  try { const url = new URL(value); return ['https:', 'http:'].includes(url.protocol) ? url.href : ''; }
  catch { return ''; }
}
function imageUrls(value) {
  if (Array.isArray(value)) return value.flatMap(imageUrls);
  if (value && typeof value === 'object') return imageUrls(value.url || value.src || value.image || '');
  const url = safeUrl(value);
  return url ? [url] : [];
}
function releases(row) {
  const list = [row.releases, row.versions_data, row.releases_data, row.version_history, row.versions]
    .find(items => Array.isArray(items) && items.some(item => item && typeof item === 'object')) || [];
  // Source URLs/files/download codes are deliberately absent. Keep complete public notes.
  return list.filter(item => item && typeof item === 'object').map(item => ({
    versionName: text(item.versionName || item.version_number || item.version || item.name || item.displayName || item.fileName),
    date: text(item.date || item.date_published || item.release_date || item.createDate),
    changelog: text(item.changelogMd || item.changelog || item.changelogHtml || item.notes),
    gameVersions: (item.gameVersions || item.game_versions || item.mc_versions || []).filter?.(v => typeof v === 'string') || [],
    loaders: (item.loaders || item.loader || []).filter?.(v => typeof v === 'string') || [],
  })).filter(item => item.versionName || item.changelog);
}
function exportPreviews(out, archiveRoot) {
  const archive = path.resolve(archiveRoot);
  const manifest = readJson(path.join(archive, 'manifest.json'));
  if (!manifest.snapshotId || !manifest.createdAt) throw Error('Archive must have a dated snapshot manifest');
  const mcCache = readJson(path.join(archive, 'crawler_output', 'mcmod_details_cache.json'));
  const index = { schema: 1, archivedAt: manifest.createdAt, platforms: {} };
  const files = [];
  const coverage = {};
  for (const platform of platforms) {
    const catalogIndex = readJson(path.join(out, 'data', platform + '.json'));
    const catalog = catalogIndex.files.flatMap(name => {
      const bytes = fs.readFileSync(path.join(out, 'data', name));
      return JSON.parse(bytes[0] === 0x1f && bytes[1] === 0x8b ? zlib.gunzipSync(bytes) : bytes.toString('utf8'));
    });
    const publicRecords = new Map(catalog.map(row => [row.sourceId, row]));
    const raw = readJson(path.join(archive, 'crawler_output', platform + '_modpacks.json'));
    const stats = { records: 0, descriptions: 0, images: 0, versions: 0, modLinks: 0, excludedRecords: 0, archivedAt: manifest.createdAt };
    const entries = [];
    for (const row of raw) {
      const id = sourceId(row), current = publicRecords.get(id);
      if (!current) { stats.excludedRecords++; continue; }
      const archivedUrl = safeUrl(row.url), publicUrl = safeUrl(current.url);
      if (!archivedUrl || archivedUrl !== publicUrl) { stats.excludedRecords++; continue; }
      const detail = platform === 'mcmod' ? mcCache[id] || {} : row;
      const description = text(detail.text || detail.desc || detail.description || detail.intro);
      const images = [...new Set(imageUrls([detail.images, detail.intro_images, detail.gallery, detail.featured_gallery]))];
      const history = releases(row);
      const preview = { platform, sourceId: id, sourceUrl: publicUrl, archivedAt: manifest.createdAt, description, images, releases: history };
      if (platform === 'mcmod') {
        const p = path.join(archive, 'data', 'mods', id + '.js');
        if (fs.existsSync(p)) {
          const match = fs.readFileSync(p, 'utf8').match(/^window\.__registerModDetailData\("(\d+)",([\s\S]+)\);\s*$/);
          if (!match || match[1] !== id) throw Error('Invalid archived mod sidecar: ' + id);
          preview.includedMods = JSON.parse(match[2]).flatMap(group => (group.m || []).map(mod => ({
            title: String(mod[0] || ''), url: safeUrl(mod[2]), categoryName: String(group.n || ''), version: String(mod[1] || ''),
          }))).filter(mod => mod.title && mod.url && new URL(mod.url).hostname === 'www.mcmod.cn');
          stats.modLinks += preview.includedMods.length;
        }
      }
      if (!description && !images.length && !history.length && !preview.includedMods?.length) continue;
      entries.push([id, preview]); stats.records++;
      if (description) stats.descriptions++;
      stats.images += images.length; stats.versions += history.length;
    }
    index.platforms[platform] = {};
    let bucket = {}, size = 0, part = 0;
    const flush = () => {
      if (!size) return;
      const name = `preview-${platform}-${++part}.json.gz`;
      const bytes = zlib.gzipSync(JSON.stringify(bucket), { level: 9 });
      fs.writeFileSync(path.join(out, 'data', name), bytes);
      files.push('data/' + name);
      for (const id of Object.keys(bucket)) index.platforms[platform][id] = name;
      bucket = {}; size = 0;
    };
    for (const [id, preview] of entries) {
      const bytes = Buffer.byteLength(JSON.stringify(preview));
      if (size && size + bytes > 4 * 1024 * 1024) flush();
      bucket[id] = preview; size += bytes;
    }
    flush(); coverage[platform] = stats;
  }
  fs.writeFileSync(path.join(out, 'data', 'previews.json'), JSON.stringify(index));
  files.push('data/previews.json');
  const result = { files, coverage, archiveSnapshot: manifest.snapshotId, archivedAt: manifest.createdAt, metadataCollection: false };
  fs.writeFileSync(path.join(out, 'preview-export.json'), JSON.stringify(result, null, 2));
  return result;
}
module.exports = { exportPreviews };
if (require.main === module) {
  if (!process.env.MC_PAGES_OUT || !process.env.MC_PAGES_PREVIEW_ARCHIVE_ROOT) throw Error('Set explicit output and public archive paths');
  console.log(JSON.stringify(exportPreviews(process.env.MC_PAGES_OUT, process.env.MC_PAGES_PREVIEW_ARCHIVE_ROOT)));
}

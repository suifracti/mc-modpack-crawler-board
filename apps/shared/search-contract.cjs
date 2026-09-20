function list(value) {
  if (Array.isArray(value)) return value.filter(Boolean).map(String);
  if (typeof value === 'string' && value.trim()) return value.split(/[,，|/]/).map((item) => item.trim()).filter(Boolean);
  return value === undefined || value === null || value === '' ? [] : [String(value)];
}

function first(record, keys) {
  for (const key of keys) {
    const value = record && record[key];
    if (value !== undefined && value !== null && value !== '') return value;
  }
  return '';
}

function text(value) {
  return Array.isArray(value) ? value.filter(Boolean).map(String).join('、') : String(value || '').trim();
}

function buildMcmod(item, descText = '', commentsText = '') {
  const former = list(first(item, ['formerTitles', 'former_titles']));
  const title = text(first(item, ['title', 'name']));
  const typeName = text(first(item, ['typeName', 'type_name']));
  const cats = list(first(item, ['categories']));
  const tags = list(first(item, ['tags']));
  const mods = list(first(item, ['includedModNames', 'included_mod_names', 'mods']));
  const allText = `${title} ${typeName} ${former.join(' ')} ${text(first(item, ['author', 'uploader']))} ${cats.join(' ')} ${tags.join(' ')} ${mods.join(' ')} ${descText || ''} ${commentsText || ''}`;
  return {
    id: item?.mid ?? item?.id ?? '',
    platform: 'mcmod',
    title,
    titleLower: `${title} ${typeName}`.toLowerCase(),
    formerTitlesLower: former.map((value) => value.toLowerCase()),
    authorLower: text(first(item, ['author', 'uploader'])).toLowerCase(),
    categoriesLower: cats.join(' ').toLowerCase(),
    tagsLower: tags.join(' ').toLowerCase(),
    modsLower: mods.join(' ').toLowerCase(),
    descLower: String(descText || '').toLowerCase(),
    commentsLower: String(commentsText || '').toLowerCase(),
    loadersLower: list(first(item, ['loaders', 'loader'])).join(' ').toLowerCase(),
    versionsLower: list(first(item, ['mcVersions', 'mc_versions', 'all_versions', 'versions'])).join(' ').toLowerCase(),
    allTextLower: allText.toLowerCase(),
    includedModNames: list(first(item, ['includedModNames', 'included_mod_names', 'mods'])),
  };
}

function buildSimple(platform, item, fields) {
  const title = text(first(item, fields.title || ['title', 'name']));
  const extraTitle = text(first(item, fields.extraTitle || []));
  const author = text(first(item, ['author', 'uploader', 'creator', 'owner']));
  const description = text(first(item, fields.description || ['description', 'desc', 'summary']));
  const version = text(first(item, ['mc_version']));
  const loaders = list(first(item, ['loaders', 'loader']));
  const categories = list(first(item, ['categories', 'tags']));
  const allText = `${title} ${extraTitle} ${author} ${description} ${version} ${loaders.join(' ')} ${categories.join(' ')}`;
  return {
    id: first(item, ['id', 'bvid', 'project_id', 'slug']),
    platform,
    title,
    titleLower: `${title} ${extraTitle}`.toLowerCase(),
    formerTitlesLower: [],
    authorLower: author.toLowerCase(),
    categoriesLower: categories.join(' ').toLowerCase(),
    tagsLower: '',
    modsLower: '',
    descLower: description.toLowerCase(),
    commentsLower: '',
    loadersLower: loaders.join(' ').toLowerCase(),
    versionsLower: version.toLowerCase(),
    allTextLower: allText.toLowerCase(),
    includedModNames: [],
  };
}

function buildBilibili(item) {
  return buildSimple('bilibili', item, { description: ['desc', 'description', 'summary'] });
}

function buildBbsmc(item) {
  return buildSimple('bbsmc', item, { description: ['description', 'desc', 'summary'] });
}

function buildXyebbs(item) {
  return buildSimple('xyebbs', item, { description: ['description', 'desc', 'summary'], extraTitle: ['english_name', 'englishName'] });
}

function buildModrinth(item) {
  const document = buildSimple('modrinth', item, { description: ['description', 'desc', 'summary'], extraTitle: ['slug'] });
  document.allTextLower = `${document.title} ${text(first(item, ['slug']))} ${document.authorLower} ${document.descLower} ${document.categoriesLower}`.toLowerCase();
  return document;
}

function buildCurseforge(item) {
  const document = buildSimple('curseforge', item, { description: ['description', 'desc', 'summary'], extraTitle: ['slug'] });
  document.allTextLower = `${document.title} ${text(first(item, ['slug']))} ${document.authorLower} ${document.descLower} ${document.categoriesLower}`.toLowerCase();
  return document;
}

function buildSearchDocument(platform, item, descText = '', commentsText = '') {
  if (platform === 'mcmod') return buildMcmod(item, descText, commentsText);
  if (platform === 'bilibili') return buildBilibili(item);
  if (platform === 'bbsmc') return buildBbsmc(item);
  if (platform === 'xyebbs') return buildXyebbs(item);
  if (platform === 'modrinth') return buildModrinth(item);
  return buildCurseforge(item);
}

function matchesSearchDocument(document, query) {
  const terms = String(query || '').trim().toLowerCase().split(/\s+/).filter(Boolean);
  if (!terms.length) return true;
  const fields = [
    document.titleLower,
    ...(document.formerTitlesLower || []),
    document.authorLower,
    document.categoriesLower,
    document.tagsLower,
    document.modsLower,
    document.descLower,
    document.commentsLower,
    document.loadersLower,
    document.versionsLower,
  ].filter(Boolean);
  return terms.every((term) => fields.some((field) => field.includes(term)));
}

module.exports = {
  buildMcmodSearchDocument: buildMcmod,
  buildBilibiliSearchDocument: buildBilibili,
  buildBbsmcSearchDocument: buildBbsmc,
  buildXyebbsSearchDocument: buildXyebbs,
  buildModrinthSearchDocument: buildModrinth,
  buildCurseforgeSearchDocument: buildCurseforge,
  buildSearchDocument,
  matchesSearchDocument,
};

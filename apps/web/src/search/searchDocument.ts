/**
 * Search Document Builders (Architecture V2 — Phase 3C).
 * Maps multi-platform items into unified SearchDocuments for uniform query matching.
 */
import type { SearchDocument } from './types';
import type { McmodStructuredItem } from '../platforms/mcmod/types';
import type { BilibiliPack } from '../types/legacy/bilibili';
import type { BbsmcPack } from '../types/legacy/bbsmc';
import type { XyebbsPack } from '../types/legacy/xyebbs';
import type { ModrinthPack } from '../types/legacy/modrinth';
import type { CurseforgePack } from '../types/legacy/curseforge';

export function buildMcmodSearchDocument(
  item: McmodStructuredItem,
  descText?: string,
  commentsText?: string
): SearchDocument {
  const former = (item.formerTitles || []).join(' ');
  const titleStr = `${item.title || ''} ${item.typeName || ''} ${former}`.trim();
  const cats = (item.categories || []).join(' ');
  const tags = (item.tags || []).join(' ');
  const mods = item.modSearchText || '';
  const desc = descText || '';
  const comments = commentsText || '';

  const allText = `${titleStr} ${item.author || ''} ${cats} ${tags} ${mods} ${desc} ${comments}`;

  return {
    id: item.mid,
    platform: 'mcmod',
    title: item.title || '',
    titleLower: titleStr.toLowerCase(),
    authorLower: (item.author || '').toLowerCase(),
    categoriesLower: cats.toLowerCase(),
    tagsLower: tags.toLowerCase(),
    modsLower: mods.toLowerCase(),
    descLower: desc.toLowerCase(),
    commentsLower: comments.toLowerCase(),
    loadersLower: (item.loaders || []).join(' ').toLowerCase(),
    versionsLower: (item.mcVersions || []).join(' ').toLowerCase(),
    allTextLower: allText.toLowerCase(),
  };
}

export function buildBilibiliSearchDocument(p: BilibiliPack): SearchDocument {
  const title = p.title || '';
  const author = p.author || '';
  const desc = p.desc || '';
  const ver = p.mc_version || '';
  const loaders = (p.loaders || []).join(' ');
  const cats = (p.categories || []).join(' ');
  const allText = `${title} ${author} ${desc} ${ver} ${loaders} ${cats}`;

  return {
    id: p.id || p.bvid || '',
    platform: 'bilibili',
    title,
    titleLower: title.toLowerCase(),
    authorLower: author.toLowerCase(),
    categoriesLower: cats.toLowerCase(),
    tagsLower: '',
    modsLower: '',
    descLower: desc.toLowerCase(),
    commentsLower: '',
    loadersLower: loaders.toLowerCase(),
    versionsLower: ver.toLowerCase(),
    allTextLower: allText.toLowerCase(),
  };
}

export function buildBbsmcSearchDocument(p: BbsmcPack): SearchDocument {
  const title = p.title || '';
  const author = p.author || '';
  const desc = p.description || '';
  const ver = p.mc_version || '';
  const loaders = (p.loaders || []).join(' ');
  const cats = (p.categories || []).join(' ');
  const allText = `${title} ${author} ${desc} ${ver} ${loaders} ${cats}`;

  return {
    id: p.id || '',
    platform: 'bbsmc',
    title,
    titleLower: title.toLowerCase(),
    authorLower: author.toLowerCase(),
    categoriesLower: cats.toLowerCase(),
    tagsLower: '',
    modsLower: '',
    descLower: desc.toLowerCase(),
    commentsLower: '',
    loadersLower: loaders.toLowerCase(),
    versionsLower: ver.toLowerCase(),
    allTextLower: allText.toLowerCase(),
  };
}

export function buildXyebbsSearchDocument(p: XyebbsPack): SearchDocument {
  const title = p.title || '';
  const eng = p.english_name || '';
  const author = p.author || '';
  const desc = p.description || '';
  const ver = p.mc_version || '';
  const loaders = (p.loaders || []).join(' ');
  const cats = (p.categories || []).join(' ');
  const allText = `${title} ${eng} ${author} ${desc} ${ver} ${loaders} ${cats}`;

  return {
    id: p.id || '',
    platform: 'xyebbs',
    title,
    titleLower: `${title} ${eng}`.toLowerCase(),
    authorLower: author.toLowerCase(),
    categoriesLower: cats.toLowerCase(),
    tagsLower: '',
    modsLower: '',
    descLower: desc.toLowerCase(),
    commentsLower: '',
    loadersLower: loaders.toLowerCase(),
    versionsLower: ver.toLowerCase(),
    allTextLower: allText.toLowerCase(),
  };
}

export function buildModrinthSearchDocument(p: ModrinthPack): SearchDocument {
  const title = p.title || '';
  const slug = p.slug || '';
  const author = p.author || '';
  const desc = p.description || '';
  const cats = (p.categories || []).join(' ');
  const loaders = (p.loaders || []).join(' ');
  const ver = p.mc_version || '';
  const allText = `${title} ${slug} ${author} ${desc} ${cats}`;

  return {
    id: p.id || p.slug || '',
    platform: 'modrinth',
    title,
    titleLower: `${title} ${slug}`.toLowerCase(),
    authorLower: author.toLowerCase(),
    categoriesLower: cats.toLowerCase(),
    tagsLower: '',
    modsLower: '',
    descLower: desc.toLowerCase(),
    commentsLower: '',
    loadersLower: loaders.toLowerCase(),
    versionsLower: ver.toLowerCase(),
    allTextLower: allText.toLowerCase(),
  };
}

export function buildCurseforgeSearchDocument(p: CurseforgePack): SearchDocument {
  const title = p.title || '';
  const slug = p.slug || '';
  const author = p.author || '';
  const desc = p.description || '';
  const cats = (p.categories || []).join(' ');
  const loaders = (p.loaders || []).join(' ');
  const ver = p.mc_version || '';
  const allText = `${title} ${slug} ${author} ${desc} ${cats}`;

  return {
    id: p.id || p.slug || '',
    platform: 'curseforge',
    title,
    titleLower: `${title} ${slug}`.toLowerCase(),
    authorLower: author.toLowerCase(),
    categoriesLower: cats.toLowerCase(),
    tagsLower: '',
    modsLower: '',
    descLower: desc.toLowerCase(),
    commentsLower: '',
    loadersLower: loaders.toLowerCase(),
    versionsLower: ver.toLowerCase(),
    allTextLower: allText.toLowerCase(),
  };
}

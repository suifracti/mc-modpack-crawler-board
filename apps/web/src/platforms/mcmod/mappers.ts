/**
 * MCMod Structured Data Mappers.
 * Converts McmodStructuredItem DTO into Unified McmodPack Domain Model.
 */
import type { McmodPack } from '../../domain/types';
import { deriveLegacyHasServer, resolvePrimaryClaim } from '../../domain/types';
import type { McmodStructuredItem } from './types';

export function mapStructuredMcmodToPack(dto: McmodStructuredItem): McmodPack {
  const claims = dto.environmentClaims || [];
  const serverClaim = resolvePrimaryClaim(claims, 'server');
  const clientClaim = resolvePrimaryClaim(claims, 'client');
  const hasServer = deriveLegacyHasServer(claims);

  return {
    id: `mcmod:${dto.mid}`,
    platform: 'mcmod',
    sourceId: String(dto.mid),
    mid: dto.mid,
    title: dto.title,
    chineseName: dto.chineseName,
    englishName: dto.englishName,
    formerTitles: dto.formerTitles || [],
    url: dto.url,
    author: dto.author,
    typeName: dto.typeName,
    moldId: dto.moldId,
    coverUrl: dto.coverUrl,
    views: dto.views,
    score: dto.score,
    recommendations: dto.recommendations,
    favorites: dto.favorites,
    commentsCount: dto.commentsCount,
    votes: dto.votes,
    trendStats: dto.trendStats,
    tags: dto.tags || [],
    categories: dto.categories || [],
    mcVersions: dto.mcVersions || [],
    loaders: dto.loaders || [],
    includedModsCount: dto.includedModsCount,
    includedModGroups: [], // Full groups loaded on-demand via mods/{mid}.js
    trendPoints: dto.trendPoints || [],
    environmentClaims: claims,
    serverClaim,
    clientClaim,
    hasServer,
    updatedAt: dto.modifiedAt || dto.publishedAt,
    categorySearch: dto.categories ? dto.categories.join(', ') : '',
    tagsSearch: dto.tags ? dto.tags.join(', ') : '',
    modsSearch: dto.modSearchText || '',
  };
}

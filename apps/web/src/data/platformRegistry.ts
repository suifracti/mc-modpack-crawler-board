/**
 * Central Platform Registry and Sidecar Metadata.
 * Extracted from dashboard.js.
 */
import type { Platform } from '../domain/types';

export interface PlatformConfig {
  id: Platform;
  name: string;
  src: string;
  globalVar: string;
  expectedCount: number;
}

export const PLATFORM_CONFIGS: Record<Platform, PlatformConfig> = {
  mcmod: {
    id: 'mcmod',
    name: 'MC百科',
    src: 'data/mcmod_data.js',
    globalVar: 'mcmodData',
    expectedCount: 1484,
  },
  bilibili: {
    id: 'bilibili',
    name: 'B站自制',
    src: 'data/bili_data.js',
    globalVar: 'biliModpacksData',
    expectedCount: 936,
  },
  bbsmc: {
    id: 'bbsmc',
    name: 'BBSMC',
    src: 'data/bbsmc_data.js',
    globalVar: 'bbsmcModpacksData',
    expectedCount: 1802,
  },
  xyebbs: {
    id: 'xyebbs',
    name: 'XYEBBS',
    src: 'data/xyebbs_data.js',
    globalVar: 'xyebbsModpacksData',
    expectedCount: 5175,
  },
  modrinth: {
    id: 'modrinth',
    name: 'Modrinth',
    src: 'data/modrinth_data.js',
    globalVar: 'modrinthModpacksData',
    expectedCount: 18328,
  },
  curseforge: {
    id: 'curseforge',
    name: 'CurseForge',
    src: 'data/curseforge_data.js',
    globalVar: 'curseforgeModpacksData',
    expectedCount: 45797,
  },
};

export const ALL_PLATFORMS: Platform[] = [
  'mcmod',
  'bilibili',
  'bbsmc',
  'xyebbs',
  'modrinth',
  'curseforge',
];

import type { Platform } from '../domain/types';
import mcmodIcon from '../assets/mcmod-site-icon.ico';
import bilibiliIcon from '../assets/bilibili-site-icon.ico';
import bbsmcIcon from '../assets/bbsmc-site-icon.ico';
import xyebbsIcon from '../assets/xyebbs-site-icon.ico';
import modrinthIcon from '../assets/modrinth-site-icon.ico';

export const STATIC_PLATFORM_ICONS: Partial<Record<Platform, string>> = {
  mcmod: mcmodIcon,
  bilibili: bilibiliIcon,
  bbsmc: bbsmcIcon,
  xyebbs: xyebbsIcon,
  modrinth: modrinthIcon,
};

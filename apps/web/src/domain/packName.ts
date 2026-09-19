/**
 * Pack Name Cleaning, Token Normalization, and Buzzword Stripping.
 * Extracted from dashboard.js.
 */

export const BILI_GENRE_BUZZWORDS =
  /(?:rpg|冒险|高度定制|史诗战斗|魔法|枪械|科技|生存|剧情|硬核|沉浸式|高难|爽游|原版|魔改|养老|纯净|探索|空岛|地牢|格斗|战斗|拔刀剑|工业|建造|现代战争)/gi;

export const BILI_GENERIC_PACK_KEYS = new Set([
  '',
  'mc',
  '我的世界',
  'minecraft',
  '模组',
  '整合',
  '游戏',
  '自制',
  '包',
  '整合包',
  '全新',
  '纯净',
  '高配',
  '低配',
  '生存',
  '冒险',
  '科技',
  '魔法',
  '空岛',
  '大型',
  '超好玩',
  '免费',
  '客户端',
  '体验',
]);

export function cleanPackKey(s: string | null | undefined): string {
  if (!s) return '';
  let str = String(s);
  str = str.replace(/[\uD835][\uDC00-\uDFFF]/g, '');
  str = str.replace(/(?:我的世界|minecraft|mine\s*craft|mc)/gi, ' ');
  // Treat the Chinese/ASCII multiplication sign used between co-branded pack
  // names as a separator.  It is punctuation in this title grammar, not part
  // of an English project slug (those remain untouched unless surrounded by
  // CJK characters below).
  str = str.replace(/[×]+/g, ' ');
  str = str.replace(/(?<=[\u4e00-\u9fa5])[xX](?=[\u4e00-\u9fa5])/g, ' ');
  str = str.replace(/[【】[\]（）(){}\u300C\u300D\u300E\u300F《》/|·~～!！?？:：\-—+*#]+/g, ' ');
  str = str.replace(/(?:mc|minecraft|我的世界)?\s*1\.\d{1,2}(?:\.\d+)?/gi, ' ');
  str = str.replace(/(?:v|ver|version)?\s*\d+(?:\.\d+)+(?:[a-z\d_\-.]*)?/gi, ' ');
  str = str.replace(/(?:v|ver|version)\s*\d+/gi, ' ');
  str = str.replace(/\b(?:forge|fabric|neoforge|quilt)\b/gi, ' ');
  str = str.replace(/(?:整合包|模组包|魔改包|懒人包|重制版|正式版|抢先版|公测版|抢先体验|测试版)/g, ' ');
  str = str.replace(/(?:最新|首发|公测|更新|发布|分享|下载|自制|自创|开坑|入坑|通关|介绍|演示|实况|推荐)/g, ' ');
  str = str.replace(BILI_GENRE_BUZZWORDS, ' ');
  str = str.replace(/(?:新的征途.*|从此刻开始.*|第一期.*|第二期.*|第\d+期.*|ep\d+.*)/gi, ' ');
  str = str.replace(/[^\u4e00-\u9fa5a-zA-Z0-9]/g, ' ').trim().toLowerCase();
  str = str.replace(/\s+/g, ' ');
  return str;
}

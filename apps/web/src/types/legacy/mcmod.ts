/**
 * Legacy Sidecar DTO for MC百科 (data/table_rows.js).
 */
export interface LegacyMcmodRow {
  mid: number;
  c0: string; // 序号/封面
  c1: string; // 整合包名/链接
  c2: string; // 分类
  c3: string; // 浏览量
  c4: string; // 评分
  c5: string; // 模组数
  c6: string; // 评论数
  views_n?: number;
  score_n?: number;
  has_server: boolean;
  title?: string;
  cover_url?: string;
  mc_version?: string;
  mc_versions?: string[];
  tags_search?: string;
  category_search?: string;
  mod_category_search?: string;
  mod_search?: string;
  [key: string]: unknown;
}

/**
 * Legacy Sidecar DTO for BBSMC (data/bbsmc_data.js).
 */
export interface LegacyBbsmcRelease {
  version_id?: string;
  version_number: string;
  release_date?: string;
  mc_versions?: string[];
  loaders?: string[];
  download_links?: Array<{ pan_name: string; url: string; extract_code?: string }>;
  changelog?: string;
}

export interface LegacyBbsmcItem {
  project_id: number;
  title: string;
  author: string;
  url: string;
  cover?: string;
  downloads: number;
  replies: number;
  views: number;
  has_server: boolean;
  categories?: string[];
  mc_versions?: string[];
  loaders?: string[];
  releases?: LegacyBbsmcRelease[];
  [key: string]: unknown;
}

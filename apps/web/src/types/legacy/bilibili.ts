/**
 * Legacy Sidecar DTO for Bilibili (data/bili_data.js).
 */
export interface LegacyBiliDownloadLink {
  pan_name: string;
  url: string;
  extract_code?: string;
  note?: string;
  size_bytes?: number;
}

export interface LegacyBiliRelease {
  version_id: string;
  version_number: string;
  release_date?: string;
  announced_at?: string;
  observed_at?: string;
  mc_versions?: string[];
  loaders?: string[];
  download_links?: LegacyBiliDownloadLink[];
  changelog?: string;
}

export interface LegacyBilibiliItem {
  bvid: string;
  title: string;
  author: string;
  url: string;
  cover?: string;
  views: number;
  danmaku: number;
  likes: number;
  pinned_comment?: string;
  download_links?: LegacyBiliDownloadLink[];
  qq_group?: string;
  extract_code?: string;
  has_server: boolean;
  date?: string;
  published_at?: string;
  update_notice_at?: string;
  pinned_comment_at?: string;
  last_observed_update_at?: string | null;
  observation_time_source?: string;
  releases?: LegacyBiliRelease[];
  subtitle_summary?: string;
  [key: string]: unknown;
}

/**
 * Legacy Sidecar DTO for Modrinth (data/modrinth_data.js).
 */
export interface LegacyModrinthRelease {
  version_id?: string;
  version_number: string;
  release_date?: string;
  mc_versions?: string[];
  loaders?: string[];
  downloads?: number;
  files?: Array<{ filename: string; size: number; url: string }>;
  changelog?: string;
}

export interface LegacyModrinthItem {
  project_id: string;
  slug?: string;
  title: string;
  author: string;
  url: string;
  icon_url?: string;
  downloads: number;
  followers?: number;
  client_side?: string;
  server_side?: string;
  has_server: boolean;
  categories?: string[];
  mc_versions?: string[];
  loaders?: string[];
  releases?: LegacyModrinthRelease[];
  [key: string]: unknown;
}

// Convenience alias for legacy & modern renderer
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type ModrinthPack = LegacyModrinthItem & Record<string, any>;

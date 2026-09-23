/**
 * Legacy Sidecar DTO for CurseForge (data/curseforge_data.js).
 */
export interface LegacyCurseforgeRelease {
  version_id?: string;
  version_number: string;
  release_date?: string;
  mc_versions?: string[];
  loaders?: string[];
  downloads?: number;
  files?: Array<{ filename: string; size: number; url: string }>;
  changelog?: string;
}

/** A source-provided index entry; this is not a complete release record. */
export interface CurseforgeFileIndex {
  file_id?: number | string | null;
  filename?: string | null;
  release_type?: number | string | null;
  game_version?: string | null;
  mod_loader?: number | string | null;
}

export interface LegacyCurseforgeItem {
  project_id: number;
  slug?: string;
  title: string;
  author: string;
  url: string;
  logo_url?: string;
  downloads: number;
  has_server: boolean;
  categories?: string[];
  mc_versions?: string[];
  loaders?: string[];
  main_file_id?: number | string | null;
  file_indexes?: CurseforgeFileIndex[];
  releases?: LegacyCurseforgeRelease[];
  [key: string]: unknown;
}

// Convenience alias for legacy & modern renderer
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type CurseforgePack = LegacyCurseforgeItem & Record<string, any>;

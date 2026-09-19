/**
 * Version Modal Types (Architecture V2 — Phase 3C).
 */

export interface DownloadItemViewModel {
  name: string;
  url: string;
  panClass: string;
  sizeStr?: string;
  versionName?: string;
  code?: string;
  isOfficial?: boolean;
}

export interface ReleaseItemViewModel {
  versionId: string;
  versionName: string;
  date?: string;
  changelogMd?: string;
  changelogHtml?: string;
  loaders?: string[];
  gameVersions?: string[];
  downloads?: DownloadItemViewModel[];
}

export interface VersionModalViewModel {
  platform: string;
  id: string | number;
  title: string;
  platformName: string;
  siteShort: string;
  latestVersion: string;
  lastUpdated: string;
  dateCreated?: string;
  versionCount: number;
  mcVersionsSummary: string;
  mcVersionsList: string[];
  typeName: string;
  modCountStr?: string;
  targetUrl: string;
  hasServer: boolean;
  serverStatus?: 'required' | 'optional' | 'supported' | 'unsupported' | 'unknown';
  envDisplay?: string;
  formerTitles?: string[];
  hasGroupVersion?: boolean;
  groupVersionNote?: string;
  qqGroup?: string;
  releases: ReleaseItemViewModel[];
  discussionsHtml?: string;
  noticeText?: string;
  btnLabel?: string;
}

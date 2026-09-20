interface SearchContractDocument {
  id: string | number;
  platform: string;
  title: string;
  titleLower: string;
  formerTitlesLower: string[];
  authorLower: string;
  categoriesLower: string;
  tagsLower: string;
  modsLower: string;
  descLower: string;
  commentsLower: string;
  loadersLower: string;
  versionsLower: string;
  allTextLower: string;
  includedModNames: string[];
}

interface SearchContractModule {
  buildMcmodSearchDocument(item: Record<string, unknown>, descText?: string, commentsText?: string): SearchContractDocument;
  buildBilibiliSearchDocument(item: Record<string, unknown>): SearchContractDocument;
  buildBbsmcSearchDocument(item: Record<string, unknown>): SearchContractDocument;
  buildXyebbsSearchDocument(item: Record<string, unknown>): SearchContractDocument;
  buildModrinthSearchDocument(item: Record<string, unknown>): SearchContractDocument;
  buildCurseforgeSearchDocument(item: Record<string, unknown>): SearchContractDocument;
  buildSearchDocument(platform: string, item: Record<string, unknown>, descText?: string, commentsText?: string): SearchContractDocument;
  matchesSearchDocument(document: SearchContractDocument, query: string): boolean;
}

declare const searchContract: SearchContractModule;
export = searchContract;

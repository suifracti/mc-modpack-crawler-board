/**
 * Minecraft Version Recognition and ATM family intelligence heuristics.
 * Extracted from dashboard.js.
 */

export const ATM_VERSION_MAP: Record<string, string> = {
  '10': 'MC 1.21.1 / 1.21',
  '10s': 'MC 1.21.1 / 1.21',
  '11': 'MC 1.21.1',
  '9': 'MC 1.20.1',
  '9s': 'MC 1.20.1',
  '9nf': 'MC 1.20.1',
  'g2': 'MC 1.20.1',
  '8': 'MC 1.19.2',
  '7': 'MC 1.18.2',
  '7s': 'MC 1.18.2',
  '6': 'MC 1.16.5',
  '6s': 'MC 1.16.5',
  '5': 'MC 1.15.2',
  '4': 'MC 1.14.4',
  '3': 'MC 1.12.2',
  '3e': 'MC 1.12.2',
  '3l': 'MC 1.12.2',
  '3r': 'MC 1.12.2',
  '2': 'MC 1.11.2',
  '1': 'MC 1.10.2',
  '0': 'MC 1.7.10',
  'ar': 'MC 1.18.2',
};

export interface VersionInfoCarrier {
  mc_versions?: string[];
  mc_version?: string;
  title?: string;
  tags_search?: string;
}

export function extractMcVersion(r: VersionInfoCarrier | string | null | undefined): string {
  if (!r) return '';

  let carrier: VersionInfoCarrier;
  if (typeof r === 'string') {
    carrier = { title: r };
  } else {
    carrier = r;
  }

  // 1. 优先读取已解析的官方 MC 运行版本 (支持多版本展示，如 ATM10: 1.21.1 / 1.21)
  if (carrier.mc_versions && Array.isArray(carrier.mc_versions) && carrier.mc_versions.length > 0) {
    if (carrier.mc_versions.length > 2) {
      return `MC ${carrier.mc_versions[0]} (+${carrier.mc_versions.length - 1})`;
    }
    return `MC ${carrier.mc_versions.join(' / ')}`;
  }
  if (carrier.mc_version) {
    return `MC ${carrier.mc_version}`;
  }

  // 2. ATM 家族智能识别
  const title = carrier.title || '';
  const mAtm = title.match(/\[ATM([0-9A-Za-z]+)\]/i) || title.match(/All [Tt]he Mods\s*(\d+)/i);
  if (mAtm) {
    const atmKey = mAtm[1].toLowerCase();
    if (ATM_VERSION_MAP[atmKey]) {
      return ATM_VERSION_MAP[atmKey];
    }
  }

  // 3. 标题中的明确 Minecraft 版本 (如 [1.20.1] 或 1.12.2)
  const mTitleMC = title.match(/\b(1\.(?:[7-9]|1\d|2\d)(?:\.\d+)?)\b/);
  if (mTitleMC) {
    return `MC ${mTitleMC[1]}`;
  }

  // 4. 标题中的整合包大版本号 (如 v1.2.0)
  const mVer = title.match(/\bv(\d+(?:\.\d+)*)\b/i);
  if (mVer) {
    return mVer[0];
  }

  // 5. 标签中的版本
  const mTagsMC = (carrier.tags_search || '').match(/\b(1\.(?:[7-9]|1\d|2\d)(?:\.\d+)?)\b/);
  if (mTagsMC) {
    return `MC ${mTagsMC[1]}`;
  }

  return '';
}

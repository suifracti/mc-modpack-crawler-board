import type {DesktopApi, DesktopRecordQuery, PersonalStatus} from '../desktopShell';
import {queryStaticRecords} from '../pagesQuery';

type Result = Awaited<ReturnType<DesktopApi['getPlatformRecords']>> & {sourceFile?: string | null};

// An ongoing collector keeps its server alive. Older servers can still serve the
// complete archive; apply the shared policy locally until they next restart.
export function createBilibiliCompatibleQuery(
  query: (options: DesktopRecordQuery) => Promise<Result>,
  personalEntries: () => Promise<Record<string, PersonalStatus>>,
  snapshotIdentity: () => Promise<string>,
) {
  let revision = '';
  let archive: Promise<{result: Result}> | null = null;
  return async (options: DesktopRecordQuery): Promise<Result> => {
    const probe = await query(options);
    if (probe.error || probe.bilibiliCounts?.secondary !== undefined) return probe;
    const currentSnapshot = await snapshotIdentity();
    if (!currentSnapshot) throw new Error('B站存档缺少快照身份，不能安全应用筛选');
    if (revision !== currentSnapshot || !archive) {
      revision = currentSnapshot;
      const expected = revision;
      archive = (async () => {
        const first = await query({bilibiliContent:'all',page:1,pageSize:2000});
        if (first.error) throw new Error(first.error);
        const records = [...first.records];
        for (let page = 2; page <= Math.ceil(first.total / first.pageSize); page++) {
          const next = await query({bilibiliContent:'all',page,pageSize:2000});
          if (next.error) throw new Error(next.error);
          if (next.total !== first.total) throw new Error('B站快照正在切换，请重新加载');
          records.push(...next.records);
        }
        if (records.length !== first.total) throw new Error('B站存档读取不完整，不能安全应用筛选');
        if (await snapshotIdentity() !== expected) throw new Error('B站快照正在切换，请重新加载');
        return {result:{...first,records}};
      })();
    }
    try {
      const cache = await archive;
      const entries = options.personalStatus ? await personalEntries() : {};
      if (await snapshotIdentity() !== currentSnapshot) throw new Error('B站快照正在切换，请重新加载');
      return await queryStaticRecords('bilibili',options,cache,entries);
    } catch (error) {
      archive = null;
      throw error;
    }
  };
}

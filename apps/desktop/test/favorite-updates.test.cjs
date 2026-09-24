const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { DataStore } = require('../lib/data-store.cjs');
const { FavoriteUpdateTracker } = require('../lib/favorite-updates.cjs');
const { PersonalLibrary } = require('../lib/personal-library.cjs');
const { UpdateManager } = require('../lib/update-manager.cjs');

const SIDECARS = {
  curseforge: ['curseforge_data.js', 'curseforge_modpacks.json'],
  bilibili: ['bili_data.js', 'bilibili_modpacks.json'],
  modrinth: ['modrinth_data.js', 'modrinth_modpacks.json'],
};

async function writeSnapshotSource(root, records) {
  const source = path.join(root, 'source');
  const data = path.join(source, 'data');
  const raw = path.join(root, 'crawler_output');
  await fs.mkdir(data, { recursive: true });
  await fs.mkdir(raw, { recursive: true });
  for (const [platform, items] of Object.entries(records)) {
    const [sidecar, rawFile] = SIDECARS[platform];
    await fs.writeFile(path.join(data, sidecar), `window.sample = ${JSON.stringify(items)};\n`, 'utf8');
    await fs.writeFile(path.join(raw, rawFile), JSON.stringify(items), 'utf8');
  }
  return source;
}

function stagedRunner(platform, record, mode = 'success') {
  return ({ workspace }) => ({
    cancel() {},
    promise: (async () => {
      if (mode === 'failure') return { code: 1, signal: null };
      const [sidecar, rawFile] = SIDECARS[platform];
      await fs.mkdir(path.join(workspace, 'converted_output', 'data'), { recursive: true });
      await fs.mkdir(path.join(workspace, 'crawler_output'), { recursive: true });
      await fs.mkdir(path.join(workspace, 'build'), { recursive: true });
      await fs.writeFile(path.join(workspace, 'converted_output', 'data', sidecar), `window.sample = ${JSON.stringify([record])};\n`, 'utf8');
      await fs.writeFile(path.join(workspace, 'crawler_output', rawFile), JSON.stringify([record]), 'utf8');
      await fs.writeFile(path.join(workspace, 'build', 'desktop_update_result.json'), JSON.stringify({
        platform,
        outcome: 'success_update',
        rawTouched: true,
        sidecarTouched: true,
        collectionResultTouched: true,
        sidecarFile: sidecar,
        crawlerResult: { status: 'success', requestCompleted: true, fetchedCount: 1, failedRequests: 0, truncated: false },
        changed: true,
      }), 'utf8');
      return { code: 0, signal: null };
    })(),
  });
}

test('favorite notices use post-activation release/link fields, persist read state, and ignore failures or missing fields', async (t) => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'favorite-updates-flow-'));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  const userData = path.join(root, 'profile-and-snapshots');
  const time = (() => { let tick = 0; return () => new Date(Date.UTC(2026, 0, 1, 0, 0, tick++)).toISOString(); })();
  const library = new PersonalLibrary(userData);
  await library.init();
  const store = new DataStore(userData, { personalLibrary: library });
  await store.init();

  const initialCurseForge = {
    project_id: 285109,
    title: 'RLCraft',
    url: 'https://www.curseforge.com/minecraft/modpacks/rlcraft',
    file_indexes: [{ file_id: 4612979, filename: 'RLCraft.zip' }],
  };
  const initialBilibili = {
    bvid: 'BV-update-test',
    title: '测试整合包视频',
    url: 'https://www.bilibili.com/video/BV-update-test',
    download_links: [{ name: '下载', url: 'https://pan.example/old-link' }],
  };
  const initialModrinth = {
    project_id: 'modrinth-project-1',
    title: '无发布明细样本',
    url: 'https://modrinth.com/modpack/sample',
    download_links: [
      { type: 'OFFICIAL', url: 'https://modrinth.com/modpack/sample' },
      { type: 'APP_IMPORT', url: 'modrinth://modpack/sample' },
    ],
  };
  const initialSource = await writeSnapshotSource(root, {
    curseforge: [initialCurseForge],
    bilibili: [initialBilibili],
    modrinth: [initialModrinth],
  });
  await store.importDirectory(initialSource);

  for (const [platform, sourceId] of [
    ['curseforge', '285109'],
    ['bilibili', 'BV-update-test'],
    ['modrinth', 'modrinth-project-1'],
  ]) {
    await library.update(platform, sourceId, { favorite: true }, await store.findSourceRecord(platform, sourceId));
  }

  const tracker = new FavoriteUpdateTracker(userData, { now: time });
  await tracker.init();
  await tracker.seedMissingFavorites((await library.list()).entries, (platform, sourceId) => store.findSourceRecord(platform, sourceId));

  async function refresh(platform, record, mode = 'success') {
    const manager = new UpdateManager({
      store,
      runnerFactory: stagedRunner(platform, record, mode),
      now: time,
      onSnapshotActivated: async ({ platform: activatedPlatform }) => tracker.processSuccessfulRefresh(
        activatedPlatform,
        (await library.list()).entries,
        (sourcePlatform, sourceId) => store.findSourceRecord(sourcePlatform, sourceId),
      ),
    });
    return manager.start(platform);
  }

  const seeded = tracker.list((await library.list()).entries);
  assert.equal(seeded.events.length, 0);
  assert.deepEqual(seeded.unknown.map((item) => item.key), ['modrinth:modrinth-project-1']);

  const firstCfUpdate = {
    ...initialCurseForge,
    file_indexes: [
      { file_id: 4612979, filename: 'RLCraft.zip' },
      { file_id: 4613000, filename: 'RLCraft-new.zip' },
    ],
  };
  assert.equal((await refresh('curseforge', firstCfUpdate)).state, 'success');
  let result = tracker.list((await library.list()).entries);
  assert.equal(result.events.length, 1);
  assert.equal(result.events[0].kind, 'file-index');
  assert.match(result.events[0].summary, /4613000/);

  // A second activated snapshot adds a separate file index while the first notice remains unread.
  const secondCfUpdate = {
    ...firstCfUpdate,
    file_indexes: [...firstCfUpdate.file_indexes, { file_id: 4613001, filename: 'RLCraft-newer.zip' }],
  };
  assert.equal((await refresh('curseforge', secondCfUpdate)).state, 'success');
  assert.equal(tracker.list((await library.list()).entries).events.length, 2);

  // Re-reading the same source file index does not create a duplicate notice.
  assert.equal((await refresh('curseforge', secondCfUpdate)).state, 'success');
  assert.equal(tracker.list((await library.list()).entries).events.length, 2);

  // Link-only changes are labeled separately and remain tied to the same BVID.
  const changedBilibili = { ...initialBilibili, download_links: [{ name: '下载', url: 'https://pan.example/new-link' }] };
  assert.equal((await refresh('bilibili', changedBilibili)).state, 'success');
  result = tracker.list((await library.list()).entries);
  const linkEvent = result.events.find((item) => item.kind === 'download-links');
  assert.ok(linkEvent);
  assert.match(linkEvent.summary, /下载链接/);
  assert.equal(linkEvent.sourceId, 'BV-update-test');
  assert.equal(result.unreadCount, 3);

  const beforeFailure = (await store.getActiveSnapshot()).snapshotId;
  assert.equal((await refresh('bilibili', { ...changedBilibili, download_links: [{ url: 'https://pan.example/failed-attempt' }] }, 'failure')).state, 'failed');
  assert.equal((await store.getActiveSnapshot()).snapshotId, beforeFailure);
  assert.equal(tracker.list((await library.list()).entries).events.length, 3);

  // A successfully activated record with missing file indexes becomes unjudgeable, not a false update.
  const missingCfFields = { project_id: 285109, title: 'RLCraft', url: initialCurseForge.url };
  assert.equal((await refresh('curseforge', missingCfFields)).state, 'success');
  result = tracker.list((await library.list()).entries);
  assert.equal(result.events.length, 3);
  assert.ok(result.unknown.some((item) => item.key === 'curseforge:285109'));

  const firstEventId = result.events.find((item) => item.kind === 'file-index').id;
  assert.ok(await tracker.markRead(firstEventId));
  const reloadedTracker = new FavoriteUpdateTracker(userData, { now: time });
  await reloadedTracker.init();
  result = reloadedTracker.list((await library.list()).entries);
  assert.equal(result.events.length, 3);
  assert.equal(result.events.find((item) => item.id === firstEventId).readAt !== null, true);
  assert.equal(result.unreadCount, 2);

  // Reminder state is stored beside, not inside, the schema-2 personal-library backup.
  const backup = await library.list();
  assert.deepEqual(Object.keys(backup).sort(), ['entries', 'schema']);
  const restoredLibrary = new PersonalLibrary(path.join(root, 'restored-profile'));
  await restoredLibrary.init();
  assert.equal((await restoredLibrary.restore(backup)).restored, 3);
  assert.equal((await restoredLibrary.list()).entries['bilibili:BV-update-test'].favorite, true);

});

test('Bilibili link reminders distinguish confirmed empty, preserve URL fragments, and ignore list order', async (t) => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'favorite-link-signals-'));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  const tracker = new FavoriteUpdateTracker(root);
  await tracker.init();

  const baselines = {
    confirmedEmpty: {
      bvid: 'BV-confirmed-empty',
      title: '确认无链接',
      url: 'https://www.bilibili.com/video/BV-confirmed-empty',
      download_links: [],
      download_links_observed: true,
    },
    unknownEmpty: {
      bvid: 'BV-unknown-empty',
      title: '未确认链接',
      url: 'https://www.bilibili.com/video/BV-unknown-empty',
      download_links: [],
    },
    fragment: {
      bvid: 'BV-fragment',
      title: '片段链接',
      url: 'https://www.bilibili.com/video/BV-fragment',
      download_links: [{ url: 'https://pan.example/download#file=old' }],
      download_links_observed: true,
    },
    ordered: {
      bvid: 'BV-order',
      title: '排序链接',
      url: 'https://www.bilibili.com/video/BV-order',
      download_links: [{ url: 'https://pan.example/a' }, { url: 'https://pan.example/b' }],
      download_links_observed: true,
    },
    unconfirmedRefresh: {
      bvid: 'BV-unconfirmed-refresh',
      title: '未确认刷新',
      url: 'https://www.bilibili.com/video/BV-unconfirmed-refresh',
      download_links: [{ url: 'https://pan.example/old' }],
      download_links_observed: true,
    },
  };
  const keys = Object.values(baselines).map((record) => `bilibili:${record.bvid}`);
  const entries = Object.fromEntries(keys.map((key) => [key, { favorite: true }]));
  for (const record of Object.values(baselines)) {
    await tracker.setFavorite('bilibili', record.bvid, true, record);
  }

  const refreshed = {
    [baselines.confirmedEmpty.bvid]: {
      ...baselines.confirmedEmpty,
      download_links: [{ url: 'https://pan.example/new' }],
    },
    [baselines.unknownEmpty.bvid]: {
      ...baselines.unknownEmpty,
      download_links: [{ url: 'https://pan.example/new' }],
      download_links_observed: true,
    },
    [baselines.fragment.bvid]: {
      ...baselines.fragment,
      download_links: [{ url: 'https://pan.example/download#file=new' }],
    },
    [baselines.ordered.bvid]: {
      ...baselines.ordered,
      download_links: [...baselines.ordered.download_links].reverse(),
    },
    [baselines.unconfirmedRefresh.bvid]: {
      ...baselines.unconfirmedRefresh,
      download_links: [{ url: 'https://pan.example/new' }],
      download_links_observed: false,
    },
  };

  const observed = await tracker.processSuccessfulRefresh('bilibili', entries, async (_platform, sourceId) => refreshed[sourceId]);
  assert.equal(observed.eventsAdded, 2);
  const events = tracker.list(entries).events;
  assert.deepEqual(events.map((event) => event.sourceId).sort(), ['BV-confirmed-empty', 'BV-fragment']);
  assert.deepEqual(events.find((event) => event.sourceId === 'BV-confirmed-empty').previousValues, []);
  assert.deepEqual(events.find((event) => event.sourceId === 'BV-fragment').previousValues, ['https://pan.example/download#file=old']);
  assert.deepEqual(events.find((event) => event.sourceId === 'BV-fragment').currentValues, ['https://pan.example/download#file=new']);
});

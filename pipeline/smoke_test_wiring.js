/**
 * Architecture V2 - Phase 3C.1 Integration Wiring Test Suite.
 * Automates proof that Phase 3C TypeScript subsystems are actively executing
 * in the Preview browser runtime path.
 *
 * Phase 3G-F-B: process lifecycle moved to pipeline/lib/browser_harness.js.
 * Two defects are fixed here:
 *   1. Edge was launched *outside* the try/finally, so a failed launch leaked
 *      the static server and left its port LISTENING.
 *   2. Nothing verified that the CDP port belonged to this run's Edge, so a
 *      stale browser answering on the port made `start()` "succeed" and every
 *      subsequent evaluate() waited on a page that would never load.
 */
const path = require('path');

const harness = require('./lib/browser_harness');
const { REPO_ROOT, createStaticServer, EdgeCDPClient, installExitHooks } = harness;

const targetArg = process.argv[2] || path.join('build', 'frontend_preview');
const targetDir = path.isAbsolute(targetArg) ? targetArg : path.join(REPO_ROOT, targetArg);
const PORT = parseInt(process.argv[3] || '8780', 10);
const CDP_PORT = PORT + 1000;

async function main() {
  console.log('============================================================');
  console.log('  Phase 3C.1 Integration Wiring Test Suite');
  console.log('============================================================');

  const { server, port } = await createStaticServer(targetDir, PORT);
  console.log(`[+] Static server listening at http://127.0.0.1:${port}`);

  const cdp = new EdgeCDPClient(CDP_PORT, { suite: 'wiring' });

  // Registered before the launch: a failed launch must still release the
  // static server and remove the profile directory.
  const teardown = installExitHooks({ clients: [cdp], servers: [server] });

  try {
    await cdp.start();
    console.log(`[+] Edge headless launched on CDP port ${CDP_PORT}`);

    const page = await cdp.createPage(`http://127.0.0.1:${port}/看板.html`, { returnByValue: true });
    const evalFn = page.evaluate;

    // Wait for page initialization
    let ready = false;
    for (let i = 0; i < 50; i++) {
      await new Promise(r => setTimeout(r, 200));
      const isReady = await evalFn('Boolean(window.mcmodData && window.mcmodData.length > 0)');
      if (isReady) { ready = true; break; }
    }
    if (!ready) throw new Error('Preview page failed to initialize mcmodData in time');

    const results = [];
    function assert(name, condition, details) {
      const pass = Boolean(condition);
      results.push({ name, pass, details });
      console.log(`  [${pass ? 'PASS' : 'FAIL'}] ${name} - ${details}`);
    }

    // 1. Debug Instrumentation presence
    const debugExists = await evalFn('Boolean(window.__frontendDebug)');
    assert('Debug Instrumentation Initialized', debugExists, 'window.__frontendDebug is mounted');

    // 2. Network Payload Lazy Invariant (mcmod_trends.js 0 requests on init)
    const resourceRequests = await evalFn(`
      performance.getEntriesByType('resource').map(r => r.name)
    `);
    const trendsRequested = resourceRequests.some(url => url.includes('mcmod_trends.js'));
    assert('MCMod Trends Lazy Invariant', !trendsRequested, `mcmod_trends.js initial requests: 0 (Total resources: ${resourceRequests.length})`);

    // 3. Search Wiring Test: MCMod
    await evalFn(`
      $('#mcmodUnifiedSearch').val('RLCraft').trigger('input');
    `);
    await new Promise(r => setTimeout(r, 400));
    const mcmodSearchDebug = await evalFn(`(() => {
      const dbg = window.__frontendDebug || {};
      const ids = (dbg.lastSearchMatchedIds || []).map(Number);
      ids.sort((a, b) => a - b);
      return {
        searchCalls: dbg.searchCalls || 0,
        lastQuery: dbg.lastSearchQuery || '',
        matchedCount: (dbg.lastSearchMatchedIds || []).length,
        top10Sorted: ids.slice(0, 10)
      };
    })()`);
    assert('MCMod Search Wired', mcmodSearchDebug && mcmodSearchDebug.searchCalls > 0 && mcmodSearchDebug.lastQuery === 'RLCraft',
      `searchCalls: ${mcmodSearchDebug?.searchCalls}, query: '${mcmodSearchDebug?.lastQuery}', matched: ${mcmodSearchDebug?.matchedCount}`);

    // Verify top 10 sorted IDs against Python Golden IDs
    // [16, 57, 198, 221, 304, 305, 339, 360, 370, 399]
    const expectedTop10Sorted = [16, 57, 198, 221, 304, 305, 339, 360, 370, 399];
    const actualTop10Sorted = mcmodSearchDebug?.top10Sorted || [];
    const top10Matches = JSON.stringify(actualTop10Sorted) === JSON.stringify(expectedTop10Sorted);
    assert('MCMod Search Golden Match', top10Matches && mcmodSearchDebug.matchedCount === 93,
      `Matches: ${mcmodSearchDebug?.matchedCount} (Golden: 93), Top 10 sorted matches Golden: ${top10Matches} (${JSON.stringify(actualTop10Sorted)})`);

    // 4. Bilibili search wiring & Flat-Mode raw invariant (Phase 3G-F revised)
    await evalFn(`
      switchPlatformTab('bilibili');
    `);
    for (let j = 0; j < 30; j++) {
      await new Promise(r => setTimeout(r, 200));
      if (await evalFn('Boolean(window.biliModpacksData && window.biliModpacksData.length)')) break;
    }
    await evalFn(`
      $('#biliSearchInput').val('机械动力').trigger('input');
    `);
    await new Promise(r => setTimeout(r, 500));
    const biliSearchDebug = await evalFn(`(() => {
      const dbg = window.__frontendDebug || {};
      return {
        searchCalls: dbg.searchCalls || 0,
        lastQuery: dbg.lastSearchQuery || '',
        rawMatchedCount: dbg.lastSearchMatchedIds ? dbg.lastSearchMatchedIds.length : 0,
        groupedCardsCount: document.querySelectorAll('#biliCardsGrid .bili-pack-card').length,
        filterCalls: dbg.filterCalls ? (dbg.filterCalls.bilibili || 0) : 0
      };
    })()`);
    // 4. Bilibili search wiring & Flat-Mode raw invariant
    //
    // Phase 3G-F: `53 raw` is the invariant (Flat Mode must surface every raw
    // record). `47 grouped` is NOT an invariant - it was only a snapshot of the
    // pre-remediation algorithm and legitimately moved once false splits were
    // repaired. What must still hold is that grouping is ACTIVE (cards < raw),
    // which is the assertion that catches a silently disabled grouping bridge.
    assert('Bilibili Search Wiring & Flat-Mode Raw Invariant',
      biliSearchDebug
        && biliSearchDebug.rawMatchedCount === 53
        && biliSearchDebug.groupedCardsCount > 0
        && biliSearchDebug.groupedCardsCount < biliSearchDebug.rawMatchedCount,
      `Raw Matches: ${biliSearchDebug?.rawMatchedCount} (Invariant: 53), `
      + `Grouped Cards: ${biliSearchDebug?.groupedCardsCount} (must be 0 < cards < raw; `
      + `47 is NOT an invariant since Phase 3G-F)`);

    // Bilibili Flat mode check
    await evalFn(`
      $('#biliViewToggle button[data-mode="flat"]').trigger('click');
    `);
    await new Promise(r => setTimeout(r, 400));
    const biliFlatCount = await evalFn(`document.querySelectorAll('#biliCardsGrid .bili-pack-card, #biliCardsGrid .bili-flat-card').length`);
    assert('Bilibili Flat Mode Count', biliFlatCount === 48, `Flat Cards Rendered: ${biliFlatCount} (48 per page of 53 total records)`);
    await evalFn(`$('#biliViewToggle button[data-mode="grouped"]').trigger('click'); $('#biliSearchInput').val('').trigger('input');`);
    await new Promise(r => setTimeout(r, 300));

    // 5. Filter Wiring Tests across all platforms
    // 5.1 MCMod Server Filter
    await evalFn(`
      switchPlatformTab('mcmod');
      $('#mcmodServerOnly').prop('checked', true).trigger('change');
    `);
    await new Promise(r => setTimeout(r, 400));
    const mcmodMatched = await evalFn(`(() => {
      const dbg = window.__frontendDebug || {};
      return dbg.lastFilterMatchedCounts ? (dbg.lastFilterMatchedCounts.mcmod || 0) : 0;
    })()`);
    assert('MCMod Server Filter Wired', mcmodMatched === 6,
      `MCMod serverOnly matched: ${mcmodMatched} (Golden: 6)`);
    await evalFn(`$('#mcmodServerOnly').prop('checked', false).trigger('change');`);

    // 5.2 BBSMC Server Filter
    await evalFn(`
      switchPlatformTab('bbsmc');
    `);
    for (let j = 0; j < 30; j++) {
      await new Promise(r => setTimeout(r, 200));
      if (await evalFn('Boolean(window.bbsmcModpacksData && window.bbsmcModpacksData.length)')) break;
    }
    await evalFn(`$('#bbsmcServerOnly').prop('checked', true).trigger('change');`);
    await new Promise(r => setTimeout(r, 400));
    const bbsmcMatched = await evalFn(`(() => {
      const dbg = window.__frontendDebug || {};
      return dbg.lastFilterMatchedCounts ? (dbg.lastFilterMatchedCounts.bbsmc || 0) : 0;
    })()`);
    assert('BBSMC Server Filter Wired', bbsmcMatched === 21,
      `BBSMC serverOnly matched: ${bbsmcMatched} (Golden: 21)`);
    await evalFn(`$('#bbsmcServerOnly').prop('checked', false).trigger('change');`);

    // 5.3 XYEBBS Server Filter
    await evalFn(`
      switchPlatformTab('xyebbs');
    `);
    for (let j = 0; j < 30; j++) {
      await new Promise(r => setTimeout(r, 200));
      if (await evalFn('Boolean(window.xyebbsModpacksData && window.xyebbsModpacksData.length)')) break;
    }
    await evalFn(`$('#xyebbsServerOnly').prop('checked', true).trigger('change');`);
    await new Promise(r => setTimeout(r, 400));
    const xyebbsMatched = await evalFn(`(() => {
      const dbg = window.__frontendDebug || {};
      return dbg.lastFilterMatchedCounts ? (dbg.lastFilterMatchedCounts.xyebbs || 0) : 0;
    })()`);
    assert('XYEBBS Server Filter Wired', xyebbsMatched === 1,
      `XYEBBS serverOnly matched: ${xyebbsMatched} (Golden: 1)`);
    await evalFn(`$('#xyebbsServerOnly').prop('checked', false).trigger('change');`);

    // 5.4 Modrinth Server Filter
    await evalFn(`
      switchPlatformTab('modrinth');
    `);
    for (let j = 0; j < 40; j++) {
      await new Promise(r => setTimeout(r, 200));
      if (await evalFn('Boolean(window.modrinthModpacksData && window.modrinthModpacksData.length)')) break;
    }
    await evalFn(`$('#modrinthServerOnly').prop('checked', true).trigger('change');`);
    await new Promise(r => setTimeout(r, 400));
    const modrinthMatched = await evalFn(`(() => {
      const dbg = window.__frontendDebug || {};
      return dbg.lastFilterMatchedCounts ? (dbg.lastFilterMatchedCounts.modrinth || 0) : 0;
    })()`);
    assert('Modrinth Server Filter Wired', modrinthMatched === 12660,
      `Modrinth serverOnly matched: ${modrinthMatched} (Golden: 12660)`);
    await evalFn(`$('#modrinthServerOnly').prop('checked', false).trigger('change');`);

    // 5.5 CurseForge Server Filter
    await evalFn(`
      switchPlatformTab('curseforge');
    `);
    for (let j = 0; j < 40; j++) {
      await new Promise(r => setTimeout(r, 200));
      if (await evalFn('Boolean(window.curseforgeModpacksData && window.curseforgeModpacksData.length)')) break;
    }
    await evalFn(`$('#curseforgeServerOnly').prop('checked', true).trigger('change');`);
    await new Promise(r => setTimeout(r, 400));
    const curseforgeMatched = await evalFn(`(() => {
      const dbg = window.__frontendDebug || {};
      return dbg.lastFilterMatchedCounts ? (dbg.lastFilterMatchedCounts.curseforge || 0) : 0;
    })()`);
    assert('CurseForge Server Filter Wired', curseforgeMatched === 230,
      `CurseForge serverOnly matched: ${curseforgeMatched} (Golden: 230)`);
    await evalFn(`$('#curseforgeServerOnly').prop('checked', false).trigger('change');`);

    // 6. Router Wiring Test
    const routerDebug = await evalFn(`(() => {
      const dbg = window.__frontendDebug || {};
      return {
        navigationCount: dbg.navigationCount || 0,
        lastTab: dbg.lastRoute ? dbg.lastRoute.tab : ''
      };
    })()`);
    assert('Router Navigation Wired', routerDebug && routerDebug.navigationCount >= 5 && routerDebug.lastTab === 'curseforge',
      `navigationCount: ${routerDebug?.navigationCount}, lastTab: ${routerDebug?.lastTab}`);

    // 7. Version Modal Wiring Test
    // CurseForge Modal
    await evalFn(`
      $('#curseforgeCardsGrid .js-open-plat-version-modal:first').trigger('click');
    `);
    await new Promise(r => setTimeout(r, 300));
    const curseforgeModalOpen = await evalFn(`({
      isOpen: $('#versionModalOverlay').hasClass('show') || $('#versionModalOverlay').is(':visible'),
      modalCalls: window.__frontendDebug.modalCalls,
      lastVm: window.__frontendDebug.lastModalViewModel
    })`);
    assert('CurseForge Version Modal Wired',
      curseforgeModalOpen.isOpen && curseforgeModalOpen.modalCalls.curseforge > 0,
      `isOpen: ${curseforgeModalOpen.isOpen}, calls: ${curseforgeModalOpen.modalCalls.curseforge}, title: ${curseforgeModalOpen.lastVm?.title}`);
    await evalFn(`$('#versionModalCloseBtn, #versionModalOverlay .close').trigger('click');`);

    // BBSMC Modal
    await evalFn(`switchPlatformTab('bbsmc');`);
    await new Promise(r => setTimeout(r, 300));
    await evalFn(`$('#bbsmcCardsGrid .js-open-plat-version-modal:first').trigger('click');`);
    await new Promise(r => setTimeout(r, 300));
    const bbsmcModalDebug = await evalFn(`({
      isOpen: $('#versionModalOverlay').hasClass('show') || $('#versionModalOverlay').is(':visible'),
      calls: window.__frontendDebug.modalCalls.bbsmc,
      vm: window.__frontendDebug.lastModalViewModel
    })`);
    assert('BBSMC Version Modal Wired',
      bbsmcModalDebug.isOpen && bbsmcModalDebug.calls > 0,
      `isOpen: ${bbsmcModalDebug.isOpen}, calls: ${bbsmcModalDebug.calls}, title: ${bbsmcModalDebug.vm?.title}`);
    await evalFn(`$('#versionModalCloseBtn, #versionModalOverlay .close').trigger('click');`);

    // Modrinth Modal
    await evalFn(`switchPlatformTab('modrinth');`);
    await new Promise(r => setTimeout(r, 300));
    await evalFn(`$('#modrinthCardsGrid .js-open-plat-version-modal:first').trigger('click');`);
    await new Promise(r => setTimeout(r, 300));
    const modrinthModalDebug = await evalFn(`({
      isOpen: $('#versionModalOverlay').hasClass('show') || $('#versionModalOverlay').is(':visible'),
      calls: window.__frontendDebug.modalCalls.modrinth,
      vm: window.__frontendDebug.lastModalViewModel
    })`);
    assert('Modrinth Version Modal Wired',
      modrinthModalDebug.isOpen && modrinthModalDebug.calls > 0,
      `isOpen: ${modrinthModalDebug.isOpen}, calls: ${modrinthModalDebug.calls}, title: ${modrinthModalDebug.vm?.title}`);
    await evalFn(`$('#versionModalCloseBtn, #versionModalOverlay .close').trigger('click');`);

    // Bilibili Modal
    await evalFn(`switchPlatformTab('bilibili');`);
    await new Promise(r => setTimeout(r, 300));
    await evalFn(`$('#biliCardsGrid .js-open-bili-group-versions:first, #biliCardsGrid .js-open-plat-version-modal:first').trigger('click');`);
    await new Promise(r => setTimeout(r, 300));
    const biliModalDebug = await evalFn(`({
      isOpen: $('#versionModalOverlay').hasClass('show') || $('#versionModalOverlay').is(':visible'),
      calls: window.__frontendDebug.modalCalls.bilibili,
      vm: window.__frontendDebug.lastModalViewModel
    })`);
    assert('Bilibili Version Modal Wired',
      biliModalDebug.isOpen && biliModalDebug.calls > 0,
      `isOpen: ${biliModalDebug.isOpen}, calls: ${biliModalDebug.calls}, title: ${biliModalDebug.vm?.title}`);
    await evalFn(`$('#versionModalCloseBtn, #versionModalOverlay .close').trigger('click');`);

    // 8. Renderer Debug Counts
    const rendererCalls = await evalFn(`window.__frontendDebug.rendererCalls`);
    const allRenderersCalled = Boolean(
      rendererCalls.bilibili > 0 &&
      rendererCalls.bbsmc > 0 &&
      rendererCalls.xyebbs > 0 &&
      rendererCalls.modrinth > 0 &&
      rendererCalls.curseforge > 0
    );
    assert('All Platform Card Renderers Wired', allRenderersCalled,
      `bilibili: ${rendererCalls.bilibili}, bbsmc: ${rendererCalls.bbsmc}, xyebbs: ${rendererCalls.xyebbs}, modrinth: ${rendererCalls.modrinth}, curseforge: ${rendererCalls.curseforge}`);

    // 9. Uncaught exceptions check
    const exceptions = page.uncaughtErrors;
    assert('Zero Uncaught Runtime Exceptions', exceptions.length === 0, `Uncaught exceptions: ${exceptions.length}`);

    const allPassed = results.every(r => r.pass);
    console.log(`\n============================================================`);
    console.log(`  Wiring Tests Result: ${allPassed ? 'ALL PASSED' : 'SOME FAILED'} (${results.filter(r => r.pass).length}/${results.length})`);
    console.log(`============================================================\n`);

    if (!allPassed) process.exitCode = 1;
  } finally {
    teardown();
    // Safety net: an unclosed handle must never keep the gate alive after its
    // verdict has already been printed.
    setTimeout(() => process.exit(process.exitCode || 0), 5000).unref();
  }
}

main().catch(err => {
  console.error('Test execution failed:', err);
  process.exit(1);
});

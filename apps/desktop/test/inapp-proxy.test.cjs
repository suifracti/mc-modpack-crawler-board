const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const fsp = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { createBrowserService, rewriteProxiedHtml } = require('../server.cjs');

test('in-app proxy HTML keeps remote resource base and routes document links through the proxy', () => {
  const html = rewriteProxiedHtml('<html><head><title>Pack</title></head><body><a href="/next">Next</a></body></html>', 'https://www.mcmod.cn/modpack/1145.html');
  assert.match(html, /<base href="https:\/\/www\.mcmod\.cn\/modpack\/1145\.html">/);
  assert.match(html, /\/api\/proxy-page\?url=/);
  assert.match(html, /<a href="\/next">Next<\/a>/);
});

test('static in-app preview removes remote application scripts and inline handlers', () => {
  const html = rewriteProxiedHtml('<html><head><script src="/app.js"></script></head><body><a href="/next" onclick="boot()">Next</a><script>boot()</script></body></html>', 'https://www.xyebbs.com/res-id/demo', { static: true });
  assert.doesNotMatch(html, /app\.js|boot\(\)|onclick=/);
  assert.match(html, /\/api\/proxy-page\?static=1&url=/);
  assert.match(html, />Next<\/a>/);
});

test('in-app proxy validates allowed domains and security', async () => {
  const tempDir = await fsp.mkdtemp(path.join(os.tmpdir(), 'mc-proxy-test-'));
  try {
    const service = createBrowserService({
      dataRoot: tempDir,
      port: 0,
    });
    const { port } = await service.start();

    // Test disallowed domain
    const disRes = await fetch(`http://127.0.0.1:${port}/api/proxy-page?url=${encodeURIComponent('https://evil.example.com')}`);
    assert.equal(disRes.status, 403);
    const disJson = await disRes.json();
    assert.match(disJson.error, /不支持代理该域名/);

    // Test missing url
    const missRes = await fetch(`http://127.0.0.1:${port}/api/proxy-page`);
    assert.equal(missRes.status, 400);

    await service.stop();
  } finally {
    await fsp.rm(tempDir, { recursive: true, force: true });
  }
});

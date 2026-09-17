const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const server = http.createServer((req, res) => {
  let p = decodeURIComponent(req.url.split('?')[0]);
  if (p === '/' || p === '') p = '/点击打开.html';
  const fp = path.join(process.cwd(), 'build', 'frontend_preview', p);
  if (!fs.existsSync(fp)) {
    res.writeHead(404);
    res.end('Not found');
    return;
  }
  const ext = path.extname(fp);
  const mime = { '.html': 'text/html; charset=utf-8', '.js': 'application/javascript; charset=utf-8', '.css': 'text/css' };
  res.writeHead(200, { 'Content-Type': mime[ext] || 'application/octet-stream' });
  fs.createReadStream(fp).pipe(res);
});

server.listen(8999, '127.0.0.1', async () => {
  const edge = spawn('C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe', [
    '--headless=new',
    '--remote-debugging-port=9999',
    '--disable-gpu',
    '--no-first-run',
    '--no-default-browser-check',
    'http://127.0.0.1:8999/点击打开.html'
  ]);

  setTimeout(async () => {
    try {
      const listRes = await fetch('http://127.0.0.1:9999/json/list');
      const tabs = await listRes.json();
      const wsUrl = tabs[0].webSocketDebuggerUrl;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        ws.send(JSON.stringify({ id: 1, method: 'Runtime.enable' }));
        setTimeout(() => {
          const expr = `(async () => {
            switchPlatformTab('bilibili');
            for (let i = 0; i < 20; i++) {
              await new Promise(r => setTimeout(r, 100));
              if (window.biliModpacksData && window.biliModpacksData.length) break;
            }
            const rawPacks = window.biliModpacksData || [];
            const q = '机械动力';
            const rawMatches = rawPacks.filter(p => {
              const s = ((p.title || '') + ' ' + (p.author || '') + ' ' + (p.desc || '') + ' ' + (p.mc_version || '') + ' ' + (p.loaders || []).join(' ') + ' ' + (p.categories || []).join(' ')).toLowerCase();
              return s.indexOf(q) !== -1;
            });

            $('#biliSearchInput').val('机械动力').trigger('input');
            await new Promise(r => setTimeout(r, 400));

            const cards = document.querySelectorAll('#biliCardsGrid .bili-pack-card').length;
            const modeText = $('#biliCurrentModeText').text();
            
            // Switch to flat
            $('#biliViewToggle button[data-mode="flat"]').trigger('click');
            await new Promise(r => setTimeout(r, 400));
            const flatCards = document.querySelectorAll('#biliCardsGrid .bili-pack-card, #biliCardsGrid .bili-flat-card').length;
            const flatModeText = $('#biliCurrentModeText').text();

            return {
              rawMatchesCount: rawMatches.length,
              rawBvids: rawMatches.map(x => x.bvid),
              groupedCardsCount: cards,
              groupedModeText: modeText,
              flatCardsCount: flatCards,
              flatModeText: flatModeText
            };
          })()`;
          ws.send(JSON.stringify({ id: 2, method: 'Runtime.evaluate', params: { expression: expr, awaitPromise: true, returnByValue: true } }));
        }, 600);
      };

      ws.onmessage = (evt) => {
        const res = JSON.parse(evt.data);
        if (res.id === 2) {
          console.log('BROWSER EVAL RESULT:', JSON.stringify(res, null, 2));
          edge.kill();
          server.close();
          process.exit(0);
        }
      };
    } catch (e) {
      console.error(e);
      edge.kill();
      server.close();
      process.exit(1);
    }
  }, 1800);
});

const test = require('node:test');
const assert = require('node:assert/strict');
const { openCommand } = require('../lib/system-open.cjs');

test('uses native platform opener without shell-built paths', () => {
  assert.deepEqual(openCommand('/Users/test/Data Pack', { platform: 'darwin', kind: 'path' }), {
    command: 'open', args: ['/Users/test/Data Pack'], windowsHide: false,
  });
  assert.deepEqual(openCommand('https://example.com/a?x=1&y=2', { platform: 'darwin', kind: 'url' }), {
    command: 'open', args: ['https://example.com/a?x=1&y=2'], windowsHide: false,
  });
  const windowsPathCommand = openCommand('C:\\Data Pack', { platform: 'win32', kind: 'path' });
  assert.equal(windowsPathCommand.command, 'powershell.exe');
  assert.deepEqual(windowsPathCommand.args.slice(0, 4), ['-NoProfile', '-STA', '-NonInteractive', '-Command']);
  assert.deepEqual(windowsPathCommand.env, { MC_OPEN_TARGET: 'C:\\Data Pack' });
  assert.equal(windowsPathCommand.windowsHide, true);
  assert.match(windowsPathCommand.args[4], /Shell\.Application/);
  assert.match(windowsPathCommand.args[4], /AppActivate/);
  assert.deepEqual(openCommand('/tmp/data', { platform: 'linux', kind: 'path' }), {
    command: 'xdg-open', args: ['/tmp/data'], windowsHide: false,
  });
});

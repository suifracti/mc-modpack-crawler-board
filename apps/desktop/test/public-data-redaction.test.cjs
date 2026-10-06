const test=require('node:test');
const assert=require('node:assert/strict');
const {scrubLocalText}=require('../../web/scripts/public-data-redaction.cjs');

test('public descriptions redact local addresses while keeping useful public text',()=>{
  const text='安装 /Users/example/Library/config.txt，或 C:\\Users\\example\\config.txt；参考 https://example.com/guide。';
  const result=scrubLocalText(text);
  assert.doesNotMatch(result,/\/Users\/|C:\\Users/);
  assert.match(result,/安装/);assert.match(result,/https:\/\/example.com\/guide/);
  for(const value of ['file:///private/var/temp/test','http://127.0.0.1:8765/data','localhost:8080/config','/private/var/temp'])assert.doesNotMatch(scrubLocalText(value),/file:|localhost|127\.0\.0\.1|\/private\/var/);
  assert.equal(scrubLocalText('https://example.com/Users/public-guide'),'https://example.com/Users/public-guide');
});

// Redact local examples inside public prose without discarding the whole body.
function scrubLocalText(value) {
  if(typeof value!=='string')return value;
  const local=/(?<![\p{L}\p{N}_/:])(?:file:\/\/[^\s<>"'`，。；）)\]}]+|(?:https?:\/\/)?(?:localhost|127\.0\.0\.1)(?::\d+)?(?:\/[^\s<>"'`，。；）)\]}]*)?|(?:[A-Za-z]:[\\/]+(?=[\p{L}\p{N}_])|\/Users\/|\/private\/var\/)[^\s<>"'`，。；）)\]}]+)/giu;
  return value.replace(local,'[本地地址已省略]');
}
module.exports={scrubLocalText};

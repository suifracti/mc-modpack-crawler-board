/**
 * Shared writer/reader for the LARGE tracked audit artifacts.
 *
 * Why gzip instead of trimming fields
 * -----------------------------------
 * The 3G-F.2-A ledger (bilibili_population_adjudication_v2) is 309 KB and the
 * holdout is 129 KB, both TRACKED by git. They are large because they carry the
 * per-record EVIDENCE (member bvid + title, per-group notes) that makes every
 * verdict independently re-checkable by a human. That evidence is the whole
 * point of an adjudication ledger -- deleting it to save bytes would convert
 * the ledger back into an unfalsifiable assertion.
 *
 * Measured options for the ledger:
 *   pretty JSON        309,399 B   (100%)
 *   minified JSON      147,424 B   ( 48%)   - unreadable in diffs AND only 2x
 *   short structural keys + minified
 *                      120,877 B   ( 39%)   - still only 2.6x
 *   gzip -9 of pretty   55,695 B   ( 18%)   - 5.6x, evidence 100% intact
 *
 * gzip wins on every axis: it is the smallest, it keeps the human-readable
 * pretty formatting when inflated, and it requires no schema surgery.
 *
 * `generated_at` is derived from SOURCE_DATE_EPOCH (see reproducibility rules)
 * so that re-running the audit does not by itself dirty the tracked artifact.
 */
const fs = require('fs');
const zlib = require('zlib');

/** Read a JSON artifact that may be stored either plain or gzipped. */
function readJson(file) {
  const buf = fs.readFileSync(file);
  const isGzip = buf.length >= 2 && buf[0] === 0x1f && buf[1] === 0x8b;
  const text = isGzip ? zlib.gunzipSync(buf).toString('utf8') : buf.toString('utf8');
  return JSON.parse(text);
}

/**
 * Write a JSON artifact as gzip. Uses the same pretty-printed body that the
 * plain form used, so inflating yields the original human-readable document.
 * Deterministic: zlib is invoked without mtime, and the payload carries no
 * wall-clock value of its own beyond `generated_at` (SOURCE_DATE_EPOCH-pinned).
 */
function writeJsonGz(file, value) {
  const body = Buffer.from(JSON.stringify(value, null, 2), 'utf8');
  const gz = zlib.gzipSync(body, { level: 9 });
  fs.writeFileSync(file, gz);
  return { raw: body.length, gz: gz.length };
}

/** Write plain JSON (used by the untracked build/audit copies). */
function writeJson(file, value) {
  const body = JSON.stringify(value, null, 2);
  fs.writeFileSync(file, body, 'utf8');
  return { raw: Buffer.byteLength(body, 'utf8'), gz: null };
}

/**
 * Write BOTH the untracked full copy (plain, easy to eyeball in build/audit/)
 * and the tracked compact copy (gzip). Returns byte counts for the log line.
 */
function writeJsonPair(fullFile, trackedFile, value) {
  const full = writeJson(fullFile, value);
  const tracked = writeJsonGz(trackedFile, value);
  return { full, tracked };
}

module.exports = { readJson, writeJson, writeJsonGz, writeJsonPair };

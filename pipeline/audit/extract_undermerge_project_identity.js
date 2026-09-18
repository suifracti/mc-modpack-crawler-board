/**
 * Phase 3G-F.2-B - registered-project identity extractor.
 *
 * Adjudicating under-merge candidates turns on ONE question: do two groups point
 * at the SAME registered project? A pack that is published on MC百科 / 星原社区 /
 * BBSMC / CurseForge keeps a stable numeric or slug identity across every video
 * that advertises it. That identity is strong evidence; a shared download URL or
 * QQ group is not (Phase 3G-E proved one Quark link can front 28 different packs).
 *
 * So this script pulls the canonical project identifiers out of every member's
 * download links and groups them, letting a reviewer see at a glance whether two
 * groups collide on `mcmod.cn/modpack/1418` or merely on a Quark folder.
 *
 * READ-ONLY. Emits no verdicts.
 *
 * Output: build/audit/undermerge_project_identity_v2.json
 */
const fs = require('fs');
const path = require('path');

global.window = {};
const REPO_ROOT = path.resolve(__dirname, '..', '..');
const newMod = require(path.join(REPO_ROOT, 'build', 'audit', 'bilibili_grouping_module.js'));
const BILI_DATA = path.join(REPO_ROOT, 'converted_output', 'data', 'bili_data.js');
const SCAN = path.join(REPO_ROOT, 'build', 'audit', 'bilibili_cross_group_undermerge_v2.json');
const OUT = path.join(REPO_ROOT, 'build', 'audit', 'undermerge_project_identity_v2.json');

function loadPayload() {
  const raw = fs.readFileSync(BILI_DATA, 'utf8');
  return JSON.parse(raw.slice(raw.indexOf('['), raw.lastIndexOf(']') + 1));
}

function deriveGroupKeys(data) {
  const dec = {};
  for (const [b, d] of newMod.groupBilibiliPacks(data)) dec[b] = d;
  return dec;
}

/**
 * Map a download link to a canonical REGISTERED PROJECT identity, or null when the
 * link is not a project page (a netdisk share link, a promo shortlink, a donation
 * page are all per-video or per-author, never per-project).
 */
function projectIdentity(url) {
  if (!url) return null;
  const u = String(url);
  let m;
  // 星原社区 (XyeBBS)
  if ((m = u.match(/xyebbs\.com\/resources\/(\d+)/i))) return `xyebbs:resource/${m[1]}`;
  if ((m = u.match(/xyebbs\.com\/res-id\/([A-Za-z0-9_-]+)/i))) return `xyebbs:res-id/${m[1]}`;
  // MC百科 (MCMod)
  if ((m = u.match(/mcmod\.cn\/modpack\/(\d+)\.html/i))) return `mcmod:modpack/${m[1]}`;
  // BBSMC
  if ((m = u.match(/bbsmc\.net\/modpack\/([A-Za-z0-9_\-%]+)/i))) return `bbsmc:modpack/${m[1]}`;
  // CurseForge
  if ((m = u.match(/curseforge\.com\/minecraft\/modpacks\/([A-Za-z0-9_\-]+)/i))) return `curseforge:${m[1]}`;
  // GitHub
  if ((m = u.match(/github\.com\/([A-Za-z0-9_.\-]+\/[A-Za-z0-9_.\-]+)/i))) return `github:${m[1]}`;
  return null;
}

/** Links that identify a PROJECT but are not on a known registry host. */
function isProjectishLink(url) {
  if (!url) return false;
  const u = String(url);
  if (/pan\.(quark|xunlei|baidu)\.|aliyundrive|123pan|tanggaoyun|pd\.qq\.com|b23\.tv|afdian|ifdian|pm\.mutong1/i.test(u)) return false;
  return true;
}

function main() {
  const data = loadPayload();
  const dec = deriveGroupKeys(data);
  const scan = JSON.parse(fs.readFileSync(SCAN, 'utf8'));

  const byBvid = new Map();
  for (const rec of data) byBvid.set(rec.bvid, rec);

  const findings = scan.findings.map((f) => {
    const groups = f.group_keys.map((gk) => {
      const members = data.filter((r) => dec[r.bvid] && dec[r.bvid].groupKey === gk);
      const identities = new Set();
      const projectish = new Set();
      const netdisk = new Set();
      const qqs = new Set();
      for (const m of members) {
        for (const l of (m.download_links || [])) {
          const id = projectIdentity(l.url);
          if (id) identities.add(id);
          else if (isProjectishLink(l.url)) projectish.add(l.url);
          else netdisk.add(l.url);
        }
        if (m.qq_group) qqs.add(String(m.qq_group).trim());
      }
      return {
        group_key: gk,
        member_count: members.length,
        project_identities: [...identities].sort(),
        other_project_links: [...projectish].sort(),
        netdisk_links: [...netdisk].sort(),
        qq_ids: [...qqs].sort(),
        members: members.map((m) => ({
          bvid: m.bvid,
          title: m.title,
          pub_time: m.pub_time,
          pack_version: m.pack_version,
        })),
      };
    });

    // Identities shared by EVERY group (the decisive signal), and by SOME groups.
    const sets = groups.map((g) => new Set(g.project_identities));
    const sharedByAll = sets.length
      ? [...sets.reduce((a, b) => new Set([...a].filter((x) => b.has(x))))]
      : [];
    const union = new Set(groups.flatMap((g) => g.project_identities));
    const sharedBySome = [...union].filter((x) => {
      const n = sets.filter((s) => s.has(x)).length;
      return n > 1 && n < sets.length;
    });

    return {
      author: f.author,
      group_keys: f.group_keys,
      group_count: f.group_count,
      record_count: f.record_count,
      shared_tokens: f.shared_tokens,
      project_identities_shared_by_all_groups: sharedByAll.sort(),
      project_identities_shared_by_some_groups: sharedBySome.sort(),
      project_identities_union_count: union.size,
      groups,
    };
  });

  const result = {
    phase: '3G-F.2-B',
    artifact: 'undermerge_project_identity_v2',
    purpose: 'Registered-project identity per group, the strong evidence for under-merge adjudication.',
    source_cluster_artifact: 'build/audit/bilibili_cross_group_undermerge_v2.json',
    identity_kinds: {
      'xyebbs:resource/N': '星原社区 resource id',
      'xyebbs:res-id/SLUG': '星原社区 slug',
      'mcmod:modpack/N': 'MC百科 project id',
      'bbsmc:modpack/SLUG': 'BBSMC project slug',
      'curseforge:SLUG': 'CurseForge modpack slug',
      'github:OWNER/REPO': 'GitHub repository',
    },
    disclaimer: 'EVIDENCE ONLY. No verdicts. Absence of a shared identity is NOT proof of different packs.',
    findings,
  };

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(result, null, 2), 'utf8');

  // console summary: how many findings have an all-groups shared identity
  const withAll = findings.filter((f) => f.project_identities_shared_by_all_groups.length);
  console.log('=== Phase 3G-F.2-B project identity extractor ===');
  console.log(`findings                : ${findings.length}`);
  console.log(`shared identity by ALL  : ${withAll.length}`);
  console.log(`written                 : ${path.relative(REPO_ROOT, OUT)}`);
  for (const f of withAll) {
    console.log(`  ${f.author}  ${f.project_identities_shared_by_all_groups.join(', ')}`);
  }
}

main();

"""
Phase 3G-E - Bilibili grouping benchmark corpus builder.

Builds an INDEPENDENT-EVIDENCE benchmark corpus for the current Bilibili
grouping algorithm (BILI-GRP-02 / BILI-GRP-03). The corpus deliberately does NOT
use `cleanPackKey` as ground truth - the whole point is to audit whether that key
is trustworthy.

Evidence used (all independent of the grouping algorithm):

  positive (expected = merge)
    * same uploader
    * >= 1 IDENTICAL specific download resource URL (a real per-pack share link,
      never a generic landing page / aggregation sheet)
    * high PACK-NAME overlap between titles: version-stripped, jargon-stripped
      core-token containment >= 0.5  (this rejects "one 网盘 link reused across
      many unrelated packs", e.g. a porting channel that hosts everything on a
      single quark folder)

  negative (expected = separate)
    * same uploader
    * both titles generic-heavy (>= 2 generic tokens) -> the algorithm's danger zone
    * NO shared download resource
    * version-stripped core pack names are non-empty and DISJOINT
      (rejects "潜行者3.1 vs 潜行者2.0", which is the SAME pack across versions)

Output (tracked source of truth):
    pipeline/audit/bilibili_grouping_corpus.json
"""
import collections
import itertools
import json
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BILI_DATA = os.path.join(REPO_ROOT, "converted_output", "data", "bili_data.js")
OUT = os.path.join(REPO_ROOT, "pipeline", "audit", "bilibili_grouping_corpus.json")

GENERIC_URL_HINTS = (
    "pm.mutong1.com",
    "docs.qq.com/sheet",
    "b23.tv",
    "curseforge.com/minecraft/mc-mods",
)

GENERIC_TOKENS = [
    "我的世界", "整合包", "生存", "冒险", "科技", "魔法", "空岛", "全新", "更新",
    "发布", "正式版", "高配", "低配", "纯净", "大型", "介绍", "推荐",
]

# Platform / channel jargon: shared by unrelated packs from the same channel, so
# it must not count as pack-name evidence.
JARGON_TOKENS = [
    "手机移植版", "启动器", "一键自动导入", "一键自动安装", "移植版", "移植", "汉化",
    "fcl", "pcl", "演示", "实况", "免费", "同款", "体验", "整合", "包", "版",
    "正式", "测试", "小版本", "大版本", "更新日志", "前瞻", "日志", "预热",
    "介绍视频", "宣传片", "最新版", "最新", "支持", "适配", "添加", "加入", "优化",
]

SPEC_UPLOADER_MIXIN = "懂嗎懂嗎"
SPEC_UPLOADER_HORIZON = "ConfectionaryQwQ"

SPEC_GROUP_A = ["BV1Ziuw6ZE7C", "BV1fqNe6rEt5", "BV1tVeVzDELy"]
SPEC_GROUP_B = ["BV1vuVH6XErM", "BV1k3Lg6zEjY", "BV1ACA8zjELd"]


def load_bili():
    raw = open(BILI_DATA, encoding="utf-8").read()
    return json.loads(raw[raw.index("["):raw.rindex("]") + 1])


def urls_of(rec):
    out = set()
    for l in (rec.get("download_links") or []):
        u = (l.get("url") or "").strip()
        if u and not any(h in u for h in GENERIC_URL_HINTS):
            out.add(u)
    return out


def generic_count(title):
    return sum(1 for g in GENERIC_TOKENS if g in title)


def core_tokens(title):
    """Version-stripped, jargon-stripped distinctive pack-name tokens.

    Only digit runs are removed (never the CJK that follows them), otherwise
    titles like "弑神之路2.2:神器锻世" would lose the pack-name suffix.
    """
    s = title.lower()
    s = re.sub(r"\d+(?:\.\d+)*", " ", s)          # 2.8.7 / 1.20.1 / 3.09 / 1949
    s = re.sub(r"α|β|γ", " ", s)
    for g in GENERIC_TOKENS + JARGON_TOKENS:
        s = s.replace(g.lower(), " ")
    s = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9]+", " ", s)
    return {w for w in s.split() if len(w) >= 2}


def names_are_disjoint(a, b):
    """True only when no token of A is a substring of a token of B (or vice versa).

    Guards against "潜行者" vs "潜行者风暴" being treated as different packs.
    """
    if a & b:
        return False
    for x in a:
        for y in b:
            if x in y or y in x:
                return False
    return True


def core_containment(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / max(1, min(len(a), len(b)))


def brief(rec, key_of):
    return {
        "bvid": rec["bvid"],
        "title": rec.get("title") or "",
        "published_at": rec.get("pub_time") or "",
        "description_excerpt": (rec.get("desc") or "")[:200],
        "download_identity": "; ".join(sorted(urls_of(rec)))[:300],
        "qq_group": rec.get("qq_group") or "",
        "pack_version": rec.get("pack_version") or "",
        "mc_version": rec.get("mc_version") or "",
        "current_clean_key": key_of(rec),
    }


def main():
    data = load_bili()
    by_bv = {r["bvid"]: r for r in data}

    key_js = (
        "global.window={};const m=require('./build/audit/bili_grouping_impl.js');"
        "const fs=require('fs');const raw=fs.readFileSync('converted_output/data/bili_data.js','utf8');"
        "const d=JSON.parse(raw.slice(raw.indexOf('['),raw.lastIndexOf(']')+1));"
        "console.log(JSON.stringify(Object.fromEntries(d.map(r=>[r.bvid,m.cleanPackKey(r.title)]))));"
    )
    res = subprocess.run(["node", "-e", key_js], cwd=REPO_ROOT, capture_output=True,
                         text=True, encoding="utf-8")
    if res.returncode != 0:
        raise SystemExit("key extraction failed: " + res.stderr)
    keys = json.loads(res.stdout)
    key_of = lambda rec: keys.get(rec["bvid"], "")

    byauth = collections.defaultdict(list)
    for r in data:
        byauth[(r.get("author") or "").strip().lower()].append(r)

    positives = []
    seen_author_pos = collections.Counter()

    def add_positive(case_id, uploader, recs, evidence, confidence, kind):
        positives.append({
            "case_id": case_id,
            "expected": "merge",
            "confidence": confidence,
            "kind": kind,
            "uploader": uploader,
            "videos": [brief(r, key_of) for r in recs],
            "ground_truth_evidence": evidence,
        })

    add_positive("POS-SPEC-MIXIN-A", SPEC_UPLOADER_MIXIN,
                 [by_bv[b] for b in SPEC_GROUP_A if b in by_bv],
                 ["Phase 3G-E brief names this as a human-confirmed same-pack series (卓越前线 edition)",
                  "all three titles share 齿轮与腐肉 + 卓越前线 and differ only by version number"],
                 "confirmed", "spec_named")
    add_positive("POS-SPEC-MIXIN-B", SPEC_UPLOADER_MIXIN,
                 [by_bv[b] for b in SPEC_GROUP_B if b in by_bv],
                 ["Phase 3G-E brief names this as a human-confirmed same-pack series (永无止境 edition)",
                  "all three titles share 齿轮与腐肉 + 永无止境 and differ only by version number"],
                 "confirmed", "spec_named")
    seen_author_pos[SPEC_UPLOADER_MIXIN.lower()] += 2   # two spec cases from this uploader

    horizon = sorted([r for r in byauth.get(SPEC_UPLOADER_HORIZON.lower(), [])
                      if "horizon" in (r.get("title") or "").lower()],
                     key=lambda r: r.get("pub_time") or "")
    if len(horizon) >= 2:
        shared = set.intersection(*[urls_of(r) for r in horizon])
        add_positive("POS-SPEC-HORIZON", SPEC_UPLOADER_HORIZON, horizon,
                     ["Phase 3G-E brief names Horizon 光影整合包 as a known false-split corpus (v1.2 -> v2.1)",
                      "same uploader, same series name Horizon/地平线 across v1.2.0 .. v2.1.0",
                      f"shared download resource(s): {sorted(shared)[:2] or 'none'}",
                      "titles differ only by version + changelog wording"],
                     "confirmed", "spec_named")
        seen_author_pos[SPEC_UPLOADER_HORIZON.lower()] += 1

    # ---- mined positives: same uploader + identical specific resource + high core overlap
    clusters = {}
    for a, rs in byauth.items():
        u2 = collections.defaultdict(list)
        for r in rs:
            for u in urls_of(r):
                u2[u].append(r)
        for u, vs in u2.items():
            uniq = {v["bvid"]: v for v in vs}
            if len(uniq) < 2:
                continue
            recs = sorted(uniq.values(), key=lambda r: r.get("pub_time") or "")
            cores = [core_tokens(r.get("title") or "") for r in recs]
            shared = set.intersection(*cores) if cores else set()
            contain = core_containment(cores[0], cores[1]) if len(cores) >= 2 else 0.0
            if contain < 0.5 or not shared:
                continue          # rejects "one link reused across many unrelated packs"
            sig = tuple(sorted(uniq))
            if sig in clusters:
                continue
            clusters[sig] = (a, u, recs, shared, contain)

    taken_sets = [ {v["bvid"] for v in c["videos"]} for c in positives ]
    for (a, u, recs, shared, contain) in sorted(clusters.values(), key=lambda x: (-len(x[2]), x[0])):
        if len(positives) >= 24:
            break
        if seen_author_pos[a] >= 2:
            continue
        vids = {r["bvid"] for r in recs}
        # Skip clusters that are a subset of an already-included case (duplicate evidence).
        if any(vids <= s for s in taken_sets):
            continue
        seen_author_pos[a] += 1
        taken_sets.append(vids)
        add_positive(f"POS-URL-{len(positives)+1:02d}", recs[0].get("author") or a, recs,
                     [f"same uploader ({recs[0].get('author')})",
                      f"identical download resource shared by all {len(recs)} videos: {u}",
                      f"pack-name core-token containment {contain:.2f} (>= 0.50 required)",
                      f"shared distinctive tokens: {sorted(shared)[:6]}"],
                     "strong", "shared_download_resource")

    # ---- negatives: same uploader, generic-heavy, no shared resource, disjoint core names
    negatives = []
    seen_author_neg = collections.Counter()
    # Uploaders whose generic-heavy pairs could not be resolved to different packs
    # with independent evidence (kept out of the scored corpus rather than guessed).
    NEG_EXCLUDE_AUTHORS = {"小水滴的源头"}
    pairs = []
    for a, rs in byauth.items():
        if a in NEG_EXCLUDE_AUTHORS:
            continue
        for x, y in itertools.combinations(rs, 2):
            tx, ty = x.get("title") or "", y.get("title") or ""
            if generic_count(tx) < 2 or generic_count(ty) < 2:
                continue
            if urls_of(x) & urls_of(y):
                continue
            cx, cy = core_tokens(tx), core_tokens(ty)
            if not cx or not cy:
                continue
            if not names_are_disjoint(cx, cy):
                continue          # shared / nested core name -> possibly the same pack
            pairs.append((a, x, y, generic_count(tx) + generic_count(ty), cx, cy))
    pairs.sort(key=lambda c: (-c[3], c[0]))

    for a, x, y, gsum, cx, cy in pairs:
        if len(negatives) >= 22:
            break
        if seen_author_neg[a] >= 2:
            continue
        seen_author_neg[a] += 1
        negatives.append({
            "case_id": f"NEG-{len(negatives)+1:02d}",
            "expected": "separate",
            "confidence": "strong",
            "kind": "same_author_generic_titles",
            "uploader": x.get("author") or a,
            "videos": [brief(x, key_of), brief(y, key_of)],
            "ground_truth_evidence": [
                f"same uploader ({x.get('author')}) but different packs",
                f"both titles generic-heavy (generic tokens: {generic_count(tx)} / {generic_count(ty)})",
                "NO shared download resource -> different 网盘 targets",
                f"version-stripped core pack names are disjoint: A={sorted(cx)[:4]} B={sorted(cy)[:4]}",
            ],
        })

    corpus = {
        "generated_from": "converted_output/data/bili_data.js",
        "raw_video_total": len(data),
        "note": (
            "Ground truth derives from independent evidence (shared download resources, "
            "disjoint version-stripped core pack names, phase-named human-confirmed cases). "
            "cleanPackKey is recorded for documentation only and is NEVER the expected answer."
        ),
        "spec_case_absent": {
            "uploader": "黑金",
            "reason": (
                "the 黑金 false-merge pair named in the phase brief is NOT present in the current "
                "936-record production payload (0 records match 黑金 in title/author/desc/pinned_comment/"
                "download_links). The equivalent failure mode - same uploader, reused naming template, "
                "generic-heavy titles, different packs - is covered by the NEG corpus."
            ),
        },
        "positive_cases": positives,
        "negative_cases": negatives,
        "reconstructed_cases": [
            {
                "case_id": "NEG-SPEC-HEIJIN",
                "expected": "separate",
                "confidence": "reconstructed",
                "kind": "spec_named_absent_from_payload",
                "uploader": "黑金",
                "note": (
                    "The phase brief names 黑金 as a known false merge driven by the generic token 生存. "
                    "Neither video exists in the current 936-record payload, so the two titles from the brief "
                    "are reconstructed as synthetic records and pushed through the REAL grouping implementation "
                    "separately. Excluded from precision/recall because its confidence is neither CONFIRMED nor STRONG."
                ),
                "videos": [
                    {
                        "bvid": "SYNTH-HEIJIN-1",
                        "title": "[MC整合包]生存整合包-1.21.1",
                        "published_at": "", "description_excerpt": "", "download_identity": "",
                        "qq_group": "", "pack_version": "", "mc_version": "1.21.1",
                        "current_clean_key": "",
                    },
                    {
                        "bvid": "SYNTH-HEIJIN-2",
                        "title": "我的世界【生存整合包】生存",
                        "published_at": "", "description_excerpt": "", "download_identity": "",
                        "qq_group": "", "pack_version": "", "mc_version": "1.21.1",
                        "current_clean_key": "",
                    },
                ],
                "ground_truth_evidence": [
                    "phase brief: these are two DIFFERENT packs by the same uploader",
                    "titles share only generic tokens (生存 / 整合包 / 我的世界) - no distinctive pack name",
                    "historically merged because the generic token 生存 was used as the group key",
                ],
            }
        ],
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(corpus, f, indent=2, ensure_ascii=False)

    uploaders = {c["uploader"] for c in positives} | {c["uploader"] for c in negatives}
    print(f"[+] positive cases  : {len(positives)}")
    print(f"[+] negative cases  : {len(negatives)}")
    print(f"[+] unique uploaders: {len(uploaders)}")
    print(f"[+] written         : {os.path.relpath(OUT, REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

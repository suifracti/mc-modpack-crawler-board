"""
Phase 3G-F - Uploader-disjoint dev / holdout split for the Bilibili grouping corpus.

The split is by UPLOADER (never by video) so title templates cannot leak between
dev and holdout. Assignment is deterministic (sha256 of the uploader name) rather
than cherry-picked, so the holdout cannot be chosen to flatter the new algorithm.

The phase-named uploaders (懂嗎懂嗎, ConfectionaryQwQ) are pinned to DEV because the
phase brief already declares their ground truth - they are "must not regress"
cases, not blind ones.

Output (tracked):
    pipeline/audit/bilibili_grouping_split.json
"""
import collections
import hashlib
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CORPUS = os.path.join(REPO_ROOT, "pipeline", "audit", "bilibili_grouping_corpus.json")
OUT = os.path.join(REPO_ROOT, "pipeline", "audit", "bilibili_grouping_split.json")

PINNED_TO_DEV = {"懂嗎懂嗎", "ConfectionaryQwQ"}
MIN_HOLDOUT_POS = 5
MIN_HOLDOUT_NEG = 5
MAX_HOLDOUT_CASE_SHARE = 0.40


def main():
    corpus = json.load(open(CORPUS, encoding="utf-8"))
    pos = corpus["positive_cases"]
    neg = corpus["negative_cases"]

    per = collections.defaultdict(lambda: {"pos": 0, "neg": 0})
    for c in pos:
        per[c["uploader"]]["pos"] += 1
    for c in neg:
        per[c["uploader"]]["neg"] += 1

    total_cases = len(pos) + len(neg)

    # Deterministic order: sha256(uploader) ascending. No human choice involved.
    ordered = sorted(per.keys(), key=lambda u: hashlib.sha256(u.encode("utf-8")).hexdigest())

    holdout = set()
    hp = hn = 0
    for u in ordered:
        if u in PINNED_TO_DEV:
            continue
        cand_p = hp + per[u]["pos"]
        cand_n = hn + per[u]["neg"]
        cand_cases = cand_p + cand_n
        # Stop once both minimums are met and we would exceed the share cap.
        if hp >= MIN_HOLDOUT_POS and hn >= MIN_HOLDOUT_NEG:
            if (cand_cases / total_cases) > MAX_HOLDOUT_CASE_SHARE:
                break
        holdout.add(u)
        hp, hn = cand_p, cand_n

    dev_uploaders = sorted(set(per) - holdout)
    holdout_uploaders = sorted(holdout)

    dev_cases = [c["case_id"] for c in pos + neg if c["uploader"] not in holdout]
    holdout_cases = [c["case_id"] for c in pos + neg if c["uploader"] in holdout]

    result = {
        "split_method": "uploader-disjoint, deterministic (sha256(uploader) ascending)",
        "pinned_to_dev": sorted(PINNED_TO_DEV),
        "dev": {
            "uploaders": dev_uploaders,
            "case_ids": dev_cases,
            "positive": sum(1 for c in pos if c["uploader"] not in holdout),
            "negative": sum(1 for c in neg if c["uploader"] not in holdout),
        },
        "holdout": {
            "uploaders": holdout_uploaders,
            "case_ids": holdout_cases,
            "positive": sum(1 for c in pos if c["uploader"] in holdout),
            "negative": sum(1 for c in neg if c["uploader"] in holdout),
        },
    }

    # Contract assertions - the split must be usable as a gate.
    assert result["holdout"]["positive"] >= MIN_HOLDOUT_POS, "holdout positive too small"
    assert result["holdout"]["negative"] >= MIN_HOLDOUT_NEG, "holdout negative too small"
    assert not (set(dev_uploaders) & set(holdout_uploaders)), "uploader leaked across split"

    json.dump(result, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"[+] dev     : {len(dev_uploaders)} uploaders, "
          f"{result['dev']['positive']} pos + {result['dev']['negative']} neg")
    print(f"[+] holdout : {len(holdout_uploaders)} uploaders, "
          f"{result['holdout']['positive']} pos + {result['holdout']['negative']} neg")
    print(f"[+] holdout uploaders: {', '.join(holdout_uploaders)}")
    print(f"[+] written : {os.path.relpath(OUT, REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

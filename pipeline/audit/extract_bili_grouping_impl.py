"""
Phase 3G-E — Bilibili grouping benchmark evaluator (extraction step).

The production bundle `converted_output/assets/index.js` ships UNMINIFIED, so the
real grouping implementation can be extracted verbatim and executed in Node.
This script extracts the exact source text of:

    * the local generic-key set   (BILI_GENERIC_PACK_KEYS2)
    * cleanPackKey(...)
    * groupPacks(...)

into build/audit/bili_grouping_impl.js, which the Node evaluator requires.

No reimplementation: the extracted text is the shipped production code.
"""
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUNDLE = os.path.join(REPO_ROOT, "converted_output", "assets", "index.js")
OUT = os.path.join(REPO_ROOT, "build", "audit", "bili_grouping_impl.js")


def extract_balanced(src, start_idx, open_ch="{"):
    """Return src[start_idx:] up to and including the matching close char."""
    close_ch = {"{": "}", "[": "]", "(": ")"}[open_ch]
    i = src.index(open_ch, start_idx)
    depth = 0
    in_str = None
    esc = False
    while i < len(src):
        ch = src[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                in_str = None
        else:
            if ch in "'\"`":
                in_str = ch
            elif ch == open_ch:
                depth += 1
            elif ch == close_ch:
                depth -= 1
                if depth == 0:
                    return src[start_idx:i + 1]
        i += 1
    raise RuntimeError("unbalanced source")


def main():
    src = open(BUNDLE, encoding="utf-8").read()

    decl = re.search(r"(?:var|const|let)\s+BILI_GENERIC_PACK_KEYS2\s*=\s*(?:/\*[^*]*\*/\s*)?new Set\(", src)
    if not decl:
        raise SystemExit("generic key set not found in bundle")
    set_src = extract_balanced(src, decl.start(), "(") + ";"
    # Re-declare as const for the CommonJS module scope.
    set_src = re.sub(r"^(?:var|const|let)\s+", "const ", set_src, count=1)
    set_src = set_src.replace("/* @__PURE__ */ ", "")

    fn_clean = src.index("function cleanPackKey(")
    clean_src = extract_balanced(src, fn_clean, "{")

    # BILI_GENRE_BUZZWORDS is emitted as a single-line regex literal.
    buzz_line = None
    for line in src.splitlines():
        if re.match(r"\s*(?:var|const|let)\s+BILI_GENRE_BUZZWORDS\s*=\s*/", line):
            buzz_line = line.strip()
            break
    if not buzz_line:
        raise SystemExit("BILI_GENRE_BUZZWORDS not found in bundle")
    buzz_src = re.sub(r"^(?:var|const|let)\s+", "const ", buzz_line, count=1)
    if not buzz_src.endswith(";"):
        buzz_src += ";"

    fn_group = src.index("function groupPacks(")
    group_src = extract_balanced(src, fn_group, "{")

    body = "\n".join([
        "// Auto-extracted verbatim from converted_output/assets/index.js (production bundle).",
        "// Do not edit by hand - regenerate with pipeline/audit/bili_grouping_benchmark.py",
        buzz_src,
        set_src,
        clean_src,
        group_src,
        "module.exports = { cleanPackKey, groupPacks, BILI_GENERIC_PACK_KEYS2, BILI_GENRE_BUZZWORDS };",
        "",
    ])

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(body)

    print(f"[+] extracted buzzword regex: {len(buzz_src)} chars")
    print(f"[+] extracted generic set   : {len(set_src)} chars")
    print(f"[+] extracted cleanPackKey  : {len(clean_src)} chars")
    print(f"[+] extracted groupPacks    : {len(group_src)} chars")
    print(f"[+] written                 : {os.path.relpath(OUT, REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
Phase 3G-F.2-A - runtime remediation regression test.

This suite pins the RUNTIME behaviour of the fixes delivered in 3G-F.2-A
(`3f81db2` + the expanded-audit merge), against the real 936-record payload.
Every assertion here is on `groupBilibiliPacks` output, not on an audit
artifact, so a ledger edit can never make these pass.

The four defects pinned, with the generic mechanism that closes each:

  1. 怪物大乱斗 (R5 `competing_edition`) - a bare PREFIX anchor. Two records
     shared the run `怪物大乱斗` because the longer real name is
     `怪物大乱斗重生`. The token following the run differs (`手机版` vs `重生`),
     both are zero-identity-char edition labels, and `重生` is independently
     attested by the uploader's own 3-member group. Ground truth (§4) was
     independently verified from the titles; the rule separates them.

  2. 星辉の天晓 (R6 `bracketed_name_disagreement`) - a CHANNEL SELF-NAME
     bracket. `【天晓の整合包发布】` is the channel's self-identification, not a
     pack name, so R1's name slot was blind and two unrelated packs merged on
     the shared handle `天晓`. The self-name segment is now excluded from the
     name slot.

  3. 墨竹ギ (R6 `bracketed_name_disagreement`) - FLATTENED BRACKET NAMES.
     `cleanPackKey` destroys `[]`/`（）`, so `史诗的地下城[Dungeons Of Fantasy]`
     and `深渊之诗[Poetry Of The Abyss]` lose their real names and a
     descriptive run (`一款大型`) won the anchor race. The bracketed names are
     now captured and outrank a weaker flattened descriptor.

  4. 涅槃 - TWO packs, not one (corrected premise, §9). The records' own
     structured registration ids split 5 + 2. Asserting 7 -> 1 would be
     demanding a real over-merge.

Generic-mechanism guard: this suite also asserts the fixes are NOT
case-specific. The rules are exercised through the shared anchor-admissibility
layer, and the suite pins that no title literal from the four cases appears in
the runtime source as a special case.
"""
import json
import os
import re
import subprocess
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNTIME_SRC = os.path.join(REPO_ROOT, "apps", "web", "src", "domain",
                           "bilibiliGrouping.ts")
BILI_DATA = os.path.join(REPO_ROOT, "converted_output", "data", "bili_data.js")
PROBE = os.path.join(REPO_ROOT, "build", "audit",
                     "_3gf2a_runtime_probe.js")


def run(cmd):
    env = dict(os.environ)
    env.setdefault("SOURCE_DATE_EPOCH", "1786000000")
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env)


PROBE_JS = r"""
const fs = require('fs');
const path = require('path');
global.window = {};
const REPO = %(repo)s;
const mod = require(path.join(REPO, 'build', 'audit', 'bilibili_grouping_module.js'));
const raw = fs.readFileSync(path.join(REPO, 'converted_output', 'data', 'bili_data.js'), 'utf8');
const data = JSON.parse(raw.slice(raw.indexOf('['), raw.lastIndexOf(']') + 1));
const map = {};
for (const [b, d] of mod.groupBilibiliPacks(data)) map[b] = d;

const out = { groups: 0, records: data.length, byAuthor: {} };
out.groups = new Set(Object.values(map).map((d) => d.groupKey)).size;

for (const author of %(authors)s) {
  const recs = data.filter((r) => String(r.author || '').trim().toLowerCase() === author.toLowerCase());
  const g = {};
  for (const r of recs) {
    const k = map[r.bvid].groupKey;
    (g[k] = g[k] || []).push({ bvid: r.bvid, title: r.title, groupKey: k, anchor: map[r.bvid].anchor });
  }
  out.byAuthor[author] = Object.entries(g).map(([k, v]) => ({
    groupKey: k, size: v.length, members: v,
  }));
}

// author scope: no group may span two uploaders
const owners = {};
let crossUploader = 0;
for (const r of data) {
  const k = map[r.bvid].groupKey;
  const a = String(r.author || '').trim().toLowerCase();
  if (owners[k] === undefined) owners[k] = a;
  else if (owners[k] !== a) crossUploader++;
}
out.cross_uploader_records = crossUploader;

// 机械动力 raw invariant (§11). Must use the SAME search surface as the
// frontend / benchmark: title + author + desc + mc_version + loaders +
// categories. A title-only regex gives 30 and is the wrong measurement.
function searchTarget(p) {
  return [p.title || '', p.author || '', p.desc || '', p.mc_version || '',
    (p.loaders || []).join(' '), (p.categories || []).join(' ')].join(' ').toLowerCase();
}
out.jixie_raw = data.filter((r) => searchTarget(r).includes('机械动力')).length;
out.jixie_grouped = new Set(
  data.filter((r) => searchTarget(r).includes('机械动力')).map((r) => map[r.bvid].groupKey),
).size;

// 涅槃 family: records of 墨言eclipse whose TITLE contains 涅槃, grouped by the
// runtime's own decision.
out.nievana = {};
for (const r of data) {
  if (String(r.author || '').trim() !== '墨言eclipse') continue;
  if (!/涅槃/.test(r.title || '')) continue;
  const k = map[r.bvid].groupKey;
  (out.nievana[k] = out.nievana[k] || []).push({ bvid: r.bvid, title: r.title });
}

console.log(JSON.stringify(out));
"""


class TestRuntimeRemediation3GF2A(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        esbuild = os.path.join(REPO_ROOT, "apps", "web", "node_modules", ".bin",
                               "esbuild.cmd" if os.name == "nt" else "esbuild")
        r0 = run([esbuild, "apps/web/src/domain/bilibiliGrouping.ts", "--bundle",
                  "--format=cjs", "--platform=node",
                  "--outfile=build/audit/bilibili_grouping_module.js",
                  "--log-level=warning"])
        assert r0.returncode == 0, f"esbuild failed: {r0.stdout}\n{r0.stderr}"

        authors = ["一个小寂哦", "星辉の天晓", "墨竹ギ", "墨言eclipse"]
        with open(PROBE, "w", encoding="utf-8") as fp:
            fp.write(PROBE_JS % {"repo": json.dumps(REPO_ROOT.replace("\\", "/")),
                                 "authors": json.dumps(authors, ensure_ascii=False)})
        r = run(["node", PROBE])
        assert r.returncode == 0, f"probe failed: {r.stdout}\n{r.stderr}"
        cls.probe = json.loads(r.stdout.strip().splitlines()[-1])

    def group_keys_of(self, author, needle=None):
        entries = self.probe["byAuthor"][author]
        if needle is None:
            return entries
        return [e for e in entries if needle in e["groupKey"]]

    # -------------------------------------------------- 1. 怪物大乱斗 (§4)
    def test_monster_melee_editions_are_separate(self):
        """`怪物大乱斗 手机版` and `怪物大乱斗重生` are two different packs.

        Ground truth was independently verified from the titles (they differ in
        the token directly after the shared name) and from the uploader's own
        attested 3-member `怪物大乱斗重生` group. A shared bare PREFIX is not
        evidence of same-pack.
        """
        bang = self.group_keys_of("一个小寂哦", "怪物大乱斗")
        phone = [e for e in bang if "手机版" in e["groupKey"]]
        reborn = [e for e in bang if e["groupKey"].endswith("怪物大乱斗重生")]
        self.assertEqual(len(phone), 1, "手机版 group not found")
        self.assertEqual(len(reborn), 1, "重生 group not found")
        self.assertNotEqual(phone[0]["groupKey"], reborn[0]["groupKey"],
                            "R5 regression: the two editions merged again")
        # membership must not overlap
        pb = {m["bvid"] for m in phone[0]["members"]}
        rb = {m["bvid"] for m in reborn[0]["members"]}
        self.assertEqual(pb & rb, set())

    def test_monster_melee_reborn_group_is_at_least_two(self):
        """`重生` must be genuinely attested (>=2 records), not a singleton
        escape hatch invented by the rule."""
        reborn = self.group_keys_of("一个小寂哦", "怪物大乱斗重生")
        self.assertEqual(len(reborn), 1)
        self.assertGreaterEqual(reborn[0]["size"], 2,
                                "重生 collapsed to a singleton - the separation is "
                                "not backed by an attested longer name")

    # ------------------------------ 2. 星辉の天晓 channel self-name bracket
    def test_channel_self_name_bracket_does_not_leak_anchor(self):
        """`【天晓の整合包发布】` is the channel's self-name, NOT a pack name.

        Before the fix, R1's name slot read that bracket as the pack name, so
        two unrelated packs (`匠魂之旅`, `血肉寄生虫`) merged on the handle
        `天晓`.
        """
        entries = self.group_keys_of("星辉の天晓")
        keys = [e["groupKey"] for e in entries]
        self.assertGreaterEqual(len(keys), 3,
                                f"expected >=3 distinct packs, got {keys}")
        # none of the real pack names may be fused together
        fused = [k for k in keys if "匠魂之旅" in k and "血肉寄生虫" in k]
        self.assertEqual(fused, [], "self-name bracket leaked: two packs fused")
        # the bare handle must not be an anchor of a multi-member group
        for e in entries:
            if e["size"] >= 2:
                self.assertNotEqual(e["groupKey"].split("::", 1)[-1], "天晓",
                                    "bare channel handle became a group anchor")

    # ------------------------------------ 3. 墨竹ギ flattened bracket names
    def test_bracketed_pack_names_outrank_flattened_descriptor(self):
        """`史诗的地下城[Dungeons Of Fantasy]` vs `深渊之诗[Poetry Of The
        Abyss]`: `cleanPackKey` flattens the brackets, so a descriptive run
        (`一款大型`) could win the anchor race across two different packs.
        """
        entries = self.group_keys_of("墨竹ギ")
        keys = [e["groupKey"] for e in entries]
        abyss = [k for k in keys if k.endswith("poetry of the abyss")]
        self.assertEqual(len(abyss), 1, "Poetry Of The Abyss group missing")
        e = next(x for x in entries if x["groupKey"].endswith("poetry of the abyss"))
        self.assertGreaterEqual(e["size"], 2, "abyss group lost its 2.2/2.0 records")
        # The other product must NOT be inside it.
        for m in e["members"]:
            self.assertNotIn("异梦终途", m["title"],
                             "深渊之诗-异梦终途 (a different product) was merged in")

    def test_flattened_descriptor_is_not_a_group_anchor(self):
        """A descriptive run like `一款大型` must never become the anchor."""
        entries = self.group_keys_of("墨竹ギ")
        offenders = [e["groupKey"] for e in entries if e["groupKey"].endswith("一款大型")]
        self.assertEqual(offenders, [],
                         f"descriptive run became an anchor: {offenders}")

    # --------------------------------------------------- 4. 涅槃 (§9)
    def test_nirvana_is_exactly_two_packs(self):
        """涅槃 is 5 + 2 = TWO packs (corrected premise). Asserting ONE group
        would demand a real over-merge."""
        nie = self.probe["nievana"]
        self.assertEqual(len(nie), 2,
                         f"涅槃 must be 2 groups, got {len(nie)}: {list(nie)}")
        sizes = sorted(len(v) for v in nie.values())
        self.assertEqual(sizes, [2, 5],
                         f"涅槃 split is 5+2, got {sizes}")

    def test_nirvana_keys_match_corrected_target(self):
        nie = self.probe["nievana"]
        for expected in ("墨言eclipse::涅槃", "墨言eclipse::未尽之路涅槃"):
            self.assertIn(expected, nie, f"{expected} missing from 涅槃 groups")

    # ------------------------------------------------ scope invariants
    def test_no_group_spans_two_uploaders(self):
        self.assertEqual(self.probe["cross_uploader_records"], 0,
                         "author scope violated at population scale")

    def test_every_record_is_grouped(self):
        self.assertGreater(self.probe["groups"], 0)
        self.assertEqual(self.probe["records"], 936,
                         "payload size changed - re-baseline the audit")

    # ------------------------------------ 机械动力 raw invariant (§11)
    def test_jixie_dongli_raw_count_is_invariant(self):
        """§11: `raw = 53` is the ONLY invariant (Flat Mode must show every
        original record). The grouped card count is NOT -- it legitimately moves
        with the algorithm and with the batch context."""
        self.assertEqual(self.probe["jixie_raw"], 53,
                         "机械动力 raw count must stay 53 (Flat Mode completeness)")

    def test_jixie_dongli_grouped_is_a_strict_collapse(self):
        """A grouping that did nothing (grouped == raw) or that over-collapsed
        (grouped == 1) would both be broken. Assert the band, not a number."""
        raw = self.probe["jixie_raw"]
        grouped = self.probe["jixie_grouped"]
        self.assertGreater(grouped, 0)
        self.assertLess(grouped, raw,
                        f"grouped={grouped} must be < raw={raw} if grouping works")
        self.assertGreater(grouped, raw * 0.4,
                           f"grouped={grouped} collapsed too aggressively for raw={raw}")

    # --------------------------- generic-mechanism guard (no hardcoding)
    def test_fixes_are_generic_not_case_hardcoded(self):
        """The forbidden shortcut is a per-case hardcoded title. Assert no
        case title literal leaked into the runtime as a special case."""
        with open(RUNTIME_SRC, encoding="utf-8") as fp:
            src = fp.read()
        # These are the case titles. None may appear as a string literal.
        literals = ["怪物大乱斗", "星辉", "天晓", "墨竹", "深渊之诗",
                    "史诗的地下城", "一款大型", "涅槃"]
        for lit in literals:
            # allow them only inside COMMENTS (a `//` or `*` line), never in code
            for m in re.finditer(re.escape(lit), src):
                line_start = src.rfind("\n", 0, m.start()) + 1
                line_end = src.find("\n", m.start())
                line = src[line_start:line_end if line_end != -1 else len(src)]
                stripped = line.strip()
                if stripped.startswith("//") or stripped.startswith("*") \
                        or stripped.startswith("/*"):
                    continue
                self.fail(f"case title literal {lit!r} appears in runtime CODE, "
                          f"not in a comment:\n  {line.strip()}")

    def test_new_rules_are_in_the_shared_admissibility_layer(self):
        """R5/R6 must live in the shared anchor-admissibility layer, so every
        group gets them -- not in a per-case branch."""
        with open(RUNTIME_SRC, encoding="utf-8") as fp:
            src = fp.read()
        for name in ("violatesCompetingEdition", "violatesBracketName",
                     "bracketed_name_disagreement", "competing_edition"):
            self.assertIn(name, src,
                          f"{name} missing - the rule is not in the shared layer")

    def test_self_name_segment_helper_is_present(self):
        with open(RUNTIME_SRC, encoding="utf-8") as fp:
            src = fp.read()
        self.assertIn("isSelfNameSegment", src)


if __name__ == "__main__":
    unittest.main(verbosity=2)

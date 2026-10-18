"""ptrbatches.py: translator batches for pointer strings (menus, items, moves, Granbo data, system and battle text).

    python -X utf8 tools/ptrbatches.py split [--size 150] [--chars 3000]   -> work/tl/pNNN.tsv (+ .terms.txt)
    python -X utf8 tools/ptrbatches.py check pNNN                           -> validates work/tl/pNNN.out.tsv
    python -X utf8 tools/ptrbatches.py merge pNNN                           -> check, then writes en into script/ptr
TSV in: id<TAB>group<TAB>form<TAB>limit<TAB>jp. A string is drawn exactly as written (no auto-wrap): " / " stands
for a plain newline; {82xx} and every other code must be copied. limit = the pixel width of each Japanese line
(8 px per glyph): the English line must not be wider (the proportional font fits ~1.5x the letters). form "padded":
the Japanese aligns columns with runs of spaces; keep the same number of " / "-free segments separated by "  "
(two spaces) - the build re-pads them (tools/ptrbatches.py PADDED).
TSV out: id<TAB>en.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import batches  # noqa: E402
import build  # noqa: E402
import fit  # noqa: E402
import lint  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TL = ROOT / "work/tl"
NL = re.compile(r"\{8[23][0-9A-F]{2}\}|\n")  # new line {82xx}/"\n" and new box {83xx} both end a line
SKIP = {"ptr/t1A9A18.json"}  # character names: translated by hand (RAM name slots, 7 glyphs)


def lines(s):
    return NL.split(s)


def padded(jp):
    return any(re.search(r"\S {3,}\S", l) for l in lines(jp))


BOX_PX = {"r290000": 216,  # credits / Data Pad help: whole width
          "t1AA48C": 112, "t293E34": 112}  # place names: the Data Pad map-name box (fit.TABLE_NAME_PX in dialogue)
NAME_FIELD_PX = 96  # list fields; the skills list (cost column at ~52 px) gets an engine fix (docs/status.md)
MSG_BOX = {"t1A1568", "t098F4C", "t1A952C"}  # battle message window: event-box geometry (fit.first_x / line_x)


def box_limits(s):
    """Per-line limits in the message window: a box's first line starts after its speaker field, later lines at
    the column their {82xx} sets; text may run to fit.LINE_END."""
    out = []
    for box in re.split(r"\{83[0-9A-F]{2}\}", s):
        h = fit.header(box)
        codes = re.findall(r"\{82[0-9A-F]{2}\}|\n", box)
        out.append(fit.LINE_END - fit.first_x(names_header(h)))
        out += [fit.LINE_END - fit.line_x(c) for c in codes]
    return out


def names_header(h):
    import names
    return names.english_header(h) if names.INLINE.search(h) else h
ID_PX = {"s26E5B8": 46}  # default player name (カケル -> Kakeru): a name-entry field, 7 glyphs like the RAM slots
# strings the game copies into fixed RAM buffers: at most this many units (found by tools/bisect_entries.py: a
# longer name-entry title overran into the keyboard task at 0x02026398 and the keyboard stopped taking input)
ID_UNITS = {"s26FB04": 10}


def limits(jp, group=None):
    """Hard pixel limit per line: the JP width plus a little slack (fields usually have spare cells), never over
    the 216 px a full-width box holds; lines in battle message boxes and the credits get the box width.
    Screen QA catches the fields that are tighter."""
    if group in MSG_BOX:
        return box_limits(jp)
    if group == "t290574" and len(lines(jp)) == 1 and len(fit.TOKEN.findall(jp)) <= 10 and " " not in jp:
        return [NAME_FIELD_PX]  # item/move/Granbo names: list fields (skills menu ~110 px before the cost column)
    out = []
    for l in lines(jp):
        px = 8 * len(fit.TOKEN.findall(l))
        out.append(BOX_PX.get(group) or (min(216, max(px + 8, px * 6 // 5)) if px else 0))
    return out


def show(s):
    return s.replace("\n", " / ")


def unshow(s):
    if s.endswith(" /"):  # an empty last line: the editors strip the space after the final " / "
        s += " "
    return s.replace(" / ", "\n")


def entries():
    for name, f in build.load_script().items():
        if name.startswith("ptr/") and name not in SKIP:
            for e in f["entries"]:
                yield name, e


def split(size, chars):
    TL.mkdir(parents=True, exist_ok=True)
    out, cur, n = [], [], 0
    for name, e in entries():
        if e.get("en") or not re.sub(r"\{[0-9A-F]{4}\}|\s", "", e["jp"]):
            continue
        if cur and (len(cur) >= size or n + len(e["jp"]) > chars):
            out.append(cur)
            cur, n = [], 0
        cur.append((name, e))
        n += len(e["jp"])
    if cur:
        out.append(cur)
    gl = batches.glossary_rows()
    start = len(list(TL.glob("p*.tsv")))
    index = {}
    for k, b in enumerate(out, start):
        pid = f"p{k:03d}"
        rows = []
        for name, e in b:
            form = "padded" if padded(e["jp"]) else "text"
            lim = "/".join(str(x) for x in limits(e["jp"], Path(name).stem)) + "px"
            rows.append(f"{e['id']}\t{Path(name).stem}\t{form}\t{lim}\t{show(e['jp'])}")
        (TL / f"{pid}.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
        text = "".join(e["jp"] for _, e in b)
        terms = [row for jp_terms, row in gl if any(t.strip() and t.strip() in text for t in jp_terms.split("/"))]
        (TL / f"{pid}.terms.txt").write_text("\n".join(terms) + "\n", encoding="utf-8", newline="\n")
        index[pid] = [e["id"] for _, e in b]
    idx = TL / "pindex.json"
    old = json.loads(idx.read_text(encoding="utf-8")) if idx.exists() else {}
    old.update(index)
    idx.write_text(json.dumps(old, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(out)} batches ({start}..{start + len(out) - 1}), {sum(map(len, out))} entries")


def issues(e, en, group=None):
    jp = e["jp"]
    out = lint.issues({**e, "en": en}, "ptr")
    if e["id"] in ID_UNITS and len(fit.TOKEN.findall(en)) > ID_UNITS[e["id"]]:
        out.append(f"{len(fit.TOKEN.findall(en))} units > {ID_UNITS[e['id']]} (copied into a fixed RAM buffer)")
    jl, el = lines(jp), lines(en)
    if len(jl) != len(el):
        out.append(f"{len(el)} lines, JP has {len(jl)} (' / ' and {{82xx}} are line breaks)")
    elif not padded(jp):
        lims = [ID_PX[e["id"]]] * len(el) if e["id"] in ID_PX else limits(jp, group)
        for i, (lim, line) in enumerate(zip(lims, el), 1):
            w = fit.width(line)
            if w > lim:
                out.append(f"line {i}: {w} px > {lim} px")
    return out


def check(pid):
    want = [l.split("\t", 1)[0] for l in (TL / f"{pid}.tsv").read_text(encoding="utf-8").splitlines() if l]
    got = batches.read_out(pid)
    errs = [f"missing id {i}" for i in want if i not in got] + [f"extra id {i}" for i in got if i not in want]
    by_id = {e["id"]: (e, Path(name).stem) for name, e in entries()}
    merged = {}
    for i in want:
        if i not in got:
            continue
        en = unshow(got[i].rstrip("\r"))  # leading spaces centre some lines: keep them
        if not en.isascii():
            errs.append(f"{i}: non-ASCII: {''.join(sorted(set(c for c in en if not c.isascii())))}")
            continue
        e, group = by_id[i]
        errs += [f"{i}: {m}" for m in issues(e, en, group)]
        # a JP tail that follows a name or number ("をおあずかりしました") starts with a particle: give the English a
        # space (after the width check: the limit is the tail's own text)
        if re.match(r"[をがはのにでともへや]", e["jp"]) and en[:1].isalnum():
            en = " " + en
        merged[i] = en
    return errs, merged


def merge(pid):
    errs, merged = check(pid)
    if errs:
        sys.exit("\n".join(errs) + f"\n{len(errs)} problems: not merged")
    for p in sorted((ROOT / "script/ptr").glob("*.json")):
        f = json.loads(p.read_text(encoding="utf-8"))
        hit = False
        for e in f["entries"]:
            if e["id"] in merged:
                e["en"], e["status"] = merged[e["id"]], "translated"
                hit = True
        if hit:
            p.write_text(batches.build_dumps(f), encoding="utf-8", newline="\n")
    print(f"merged {len(merged)} entries from {pid}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("split")
    s.add_argument("--size", type=int, default=150)
    s.add_argument("--chars", type=int, default=3000)
    for c in ("check", "merge"):
        sub.add_parser(c).add_argument("batch")
    a = ap.parse_args()
    if a.cmd == "split":
        split(a.size, a.chars)
    elif a.cmd == "check":
        errs, merged = check(a.batch)
        print("\n".join(errs) + f"\n{len(errs)} problems" if errs else f"OK ({len(merged)} entries)")
        sys.exit(1 if errs else 0)
    else:
        merge(a.batch)

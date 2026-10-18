"""batches.py: translator batches for the event script.

    python -X utf8 tools/batches.py split [--size 110] [--chars 3800]   -> work/tl/bNNN.tsv (+ .terms.txt), index.json
    python -X utf8 tools/batches.py check bNNN                          -> validates work/tl/bNNN.out.tsv; prints OK
    python -X utf8 tools/batches.py merge bNNN                          -> check, then writes en into script/events
Input TSV: id<TAB>speaker<TAB>form<TAB>limit<TAB>jp. The jp column holds only what the translator writes: page
bodies joined by " || " (page headers, end codes, 「」 and inline NPC labels are added back by assemble()),
" / " where the JP breaks a line. Output TSV: id<TAB>en with the same " || " page count, every inline code kept.
split skips entries that already have en; it never touches script/.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402
import fit  # noqa: E402
import lint  # noqa: E402
import names  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TL = ROOT / "work/tl"
SEP = " || "


def parts(jp_page):
    """(header, body, tail) of one JP page."""
    h = fit.header(jp_page)
    rest = jp_page[len(h):]
    tail = fit.END_CODES.search(rest).group(1)
    body = rest[:len(rest) - len(tail)] if tail else rest
    return h, body, tail


def jp_for_translator(jp):
    out = []
    for page in fit.split_pages(jp):
        _, body, _ = parts(page)
        body = re.sub(r"\{82[0-9A-F]{2}\}|\n", " / ", body)
        out.append(body.replace("「", "").replace("」", ""))
    return SEP.join(out)


def assemble(jp, en_body):
    jp_pages, en_pages = fit.split_pages(jp), re.split(r" ?\|\| ?", en_body)  # editors eat a trailing space
    if len(jp_pages) != len(en_pages):
        raise ValueError(f"{len(en_pages)} pages (' || '), JP has {len(jp_pages)}")
    out = []
    for jp_page, en_page in zip(jp_pages, en_pages):
        h, _, tail = parts(jp_page)
        # drop " / " line marks (and a trailing " /") without touching other runs of spaces: menus pad with them
        body = re.sub(r"(?:^|(?<=\s))/(?:\s|$)", "", en_page).strip()
        # a name code ending the header ({9403}: running text, not a speaker) needs a space before the English
        if re.search(r"\{94([0-8][0-9A-F]|9[0-5])\}$", h) and body[:1].isalnum():
            body = " " + body
        out.append(names.english_header(h) + body + tail)
    return "{8300}".join(out)


def entries():
    for name, f in build.load_script().items():
        if name.startswith("events/"):
            for e in f["entries"]:
                yield name, e


def glossary_rows():
    rows = []
    for line in (ROOT / "glossary.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", line)
        if m and m.group(1) not in ("JP", "---"):
            rows.append((m.group(1), line))
    return rows


def split(size, chars):
    TL.mkdir(parents=True, exist_ok=True)
    batches, cur, n = [], [], 0
    for name, e in entries():
        if e.get("en"):
            continue
        jp = jp_for_translator(e["jp"])
        if cur and (len(cur) >= size or n + len(jp) > chars):
            batches.append(cur)
            cur, n = [], 0
        cur.append((name, e, jp))
        n += len(jp)
    if cur:
        batches.append(cur)
    index, gl = {}, glossary_rows()
    start = len(list(TL.glob("b*.tsv")))
    for k, b in enumerate(batches, start):
        bid = f"b{k:03d}"
        lines = []
        for name, e, jp in b:
            h = parts(fit.split_pages(e["jp"])[0])[0]
            lines.append(f"{e['id']}\t{names.speaker(h)}\tdlg\t{fit.LINES} lines x {fit.LINE_END - 56}px/page\t{jp}")
        (TL / f"{bid}.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        text = "".join(e["jp"] for _, e, _ in b)
        terms = [row for jp_terms, row in gl if any(t.strip() and t.strip() in text for t in jp_terms.split("/"))]
        (TL / f"{bid}.terms.txt").write_text("\n".join(terms) + "\n", encoding="utf-8", newline="\n")
        index[bid] = [e["id"] for _, e, _ in b]
    idx = TL / "index.json"
    old = json.loads(idx.read_text(encoding="utf-8")) if idx.exists() else {}
    old.update(index)
    idx.write_text(json.dumps(old, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(batches)} batches ({start}..{start + len(batches) - 1}), {sum(map(len, batches))} entries")


def read_out(bid):
    path = TL / f"{bid}.out.tsv"
    out = {}
    for n, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        i, _, en = line.partition("\t")  # a bare id = empty text (editors strip the trailing tab)
        if " " in i:
            raise ValueError(f"{path.name}:{n}: no tab after the id")
        if i in out:
            raise ValueError(f"{path.name}:{n}: duplicate id {i}")
        out[i] = en
    return out


def check(bid):
    want = [l.split("\t", 1)[0] for l in (TL / f"{bid}.tsv").read_text(encoding="utf-8").splitlines() if l]
    out = read_out(bid)
    errs = [f"missing id {i}" for i in want if i not in out] + [f"extra id {i}" for i in out if i not in want]
    by_id = {e["id"]: e for _, e in entries()}
    merged = {}
    for i in want:
        if i not in out:
            continue
        e = by_id[i]
        if not out[i].isascii():
            errs.append(f"{i}: non-ASCII: {''.join(sorted(set(c for c in out[i] if not c.isascii())))}")
            continue
        try:
            en = assemble(e["jp"], out[i])
        except ValueError as ex:
            errs.append(f"{i}: {ex}")
            continue
        errs += [f"{i}: {m}" for m in lint.issues({**e, "en": en}, "event")]
        merged[i] = en
    return errs, merged


def merge(bid):
    errs, merged = check(bid)
    if errs:
        sys.exit("\n".join(errs) + f"\n{len(errs)} problems: not merged")
    root = ROOT / "script"
    for p in sorted((root / "events").glob("*.json")):
        f = json.loads(p.read_text(encoding="utf-8"))
        hit = False
        for e in f["entries"]:
            if e["id"] in merged:
                e["en"], e["status"] = merged[e["id"]], "translated"
                hit = True
        if hit:
            p.write_text(build_dumps(f), encoding="utf-8", newline="\n")
    print(f"merged {len(merged)} entries from {bid}")


def build_dumps(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("split")
    s.add_argument("--size", type=int, default=110)
    s.add_argument("--chars", type=int, default=3800)
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

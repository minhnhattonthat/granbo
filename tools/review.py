"""review.py: reviewer batches for the translated event script (the review pass after first drafts).

    python -X utf8 tools/review.py split [--batches 8]       -> work/tl/rNNN.tsv (+ .terms.txt), events
    python -X utf8 tools/review.py split-ptr [--batches 6]   -> work/tl/qNNN.tsv, pointer strings
Input TSV: id<TAB>speaker<TAB>form<TAB>limit<TAB>jp<TAB>en, jp and en both in translator form (pages " || ", JP line
breaks " / ", headers and end codes stripped: batches.jp_for_translator). The reviewer writes rNNN.out.tsv
(id<TAB>English for every id, unchanged lines copied) and rNNN.notes.txt; `tools/batches.py check|merge rNNN`
validates and merges exactly like a translation batch. Brief: docs/reviewer-brief.md.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import batches  # noqa: E402
import fit  # noqa: E402
import names  # noqa: E402
import ptrbatches  # noqa: E402


def en_for_reviewer(jp, en):
    """The translator-form English of an assembled entry: each page minus its English header and end codes."""
    out = []
    for jp_page, en_page in zip(fit.split_pages(jp), fit.split_pages(en)):
        h, _, tail = batches.parts(jp_page)
        eh = names.english_header(h)
        assert en_page.startswith(eh) and en_page.endswith(tail), (jp_page, en_page)
        body = en_page[len(eh):len(en_page) - len(tail)] if tail else en_page[len(eh):]
        out.append(re.sub(r"\{82[0-9A-F]{2}\}|\n", " / ", body).strip())
    return batches.SEP.join(out)


def split(n):
    rows = []
    for name, e in batches.entries():
        if not e.get("en"):
            continue
        jp, en = batches.jp_for_translator(e["jp"]), en_for_reviewer(e["jp"], e["en"])
        assert batches.assemble(e["jp"], en) == e["en"], e["id"]  # merging an unchanged line is a no-op
        h = batches.parts(fit.split_pages(e["jp"])[0])[0]
        rows.append((e, f"{e['id']}\t{names.speaker(h)}\tdlg\t{fit.LINES} lines x {fit.LINE_END - 56}px/page\t{jp}\t{en}"))
    size = -(-len(rows) // n)
    gl = batches.glossary_rows()
    for k in range(n):
        part = rows[k * size:(k + 1) * size]
        bid = f"r{k:03d}"
        (batches.TL / f"{bid}.tsv").write_text("\n".join(r for _, r in part) + "\n", encoding="utf-8", newline="\n")
        text = "".join(e["jp"] for e, _ in part)
        terms = [row for jp_terms, row in gl if any(t.strip() and t.strip() in text for t in jp_terms.split("/"))]
        (batches.TL / f"{bid}.terms.txt").write_text("\n".join(terms) + "\n", encoding="utf-8", newline="\n")
    print(f"{n} batches of <= {size} entries ({len(rows)} total)")


def split_ptr(n):
    """Pointer strings: work/tl/qNNN.tsv in ptrbatches' layout plus the current English (" / " = newline);
    `tools/ptrbatches.py check|merge qNNN` validates and merges."""
    rows = []
    for name, e in ptrbatches.entries():
        if not e.get("en") or not re.sub(r"\{[0-9A-F]{4}\}|\s", "", e["jp"]):
            continue
        g = Path(name).stem
        form = "padded" if ptrbatches.padded(e["jp"]) else "text"
        lim = "/".join(str(x) for x in ptrbatches.limits(e["jp"], g)) + "px"
        rows.append((e, f"{e['id']}\t{g}\t{form}\t{lim}\t{ptrbatches.show(e['jp'])}\t{ptrbatches.show(e['en'])}"))
    size = -(-len(rows) // n)
    gl = batches.glossary_rows()
    for k in range(n):
        part = rows[k * size:(k + 1) * size]
        qid = f"q{k:03d}"
        (batches.TL / f"{qid}.tsv").write_text("\n".join(r for _, r in part) + "\n", encoding="utf-8", newline="\n")
        text = "".join(e["jp"] for e, _ in part)
        terms = [row for jp_terms, row in gl if any(t.strip() and t.strip() in text for t in jp_terms.split("/"))]
        (batches.TL / f"{qid}.terms.txt").write_text("\n".join(terms) + "\n", encoding="utf-8", newline="\n")
    print(f"{n} batches of <= {size} entries ({len(rows)} total)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("split")
    s.add_argument("--batches", type=int, default=8)
    s = sub.add_parser("split-ptr")
    s.add_argument("--batches", type=int, default=6)
    a = ap.parse_args()
    split(a.batches) if a.cmd == "split" else split_ptr(a.batches)

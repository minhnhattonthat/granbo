"""lint.py: per-entry checks for translated text. Used by tests/test_lint.py and tools/batches.py check.

    issues(entry, kind) -> list of strings ([] = ok); kind is "event" or "ptr"
Checks: encodable with the English font; control codes the same multiset as the JP (newline codes and page
breaks aside: fit.py owns those for events); no Japanese left; no ordinal glued to a variable; events fit their
pages after fit.fit (width, 3 lines, 136-unit page buffer).
"""
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fit  # noqa: E402
import text  # noqa: E402

CODE = re.compile(r"\{([0-9A-F]{4})\}")
JAPANESE = re.compile(r"[぀-ヿ一-鿿！-～]")
LAYOUT = re.compile(r"^(82|83)")  # newline / page codes: fit.py may add or move them


def codes(s, layout=False):
    return Counter(c for c in CODE.findall(s) if layout or not LAYOUT.match(c))


def issues(e, kind):
    en, jp = e.get("en", ""), e["jp"]
    if not en:
        return []
    out = []
    bad = sorted(set(JAPANESE.findall(en.replace("「", ""))))
    if bad:
        out.append("Japanese/fullwidth characters: " + "".join(bad))
    try:
        text.encode_en(en)
    except ValueError as ex:
        out.append(str(ex))
        return out
    want, got = codes(jp, layout=kind != "event"), codes(en, layout=kind != "event")
    if want != got:
        miss, extra = want - got, got - want
        out.append("control codes differ:" + (" missing " + " ".join(f"{{{c}}}" for c in miss) if miss else "")
                   + (" extra " + " ".join(f"{{{c}}}" for c in extra) if extra else ""))
    if re.search(r"\}(st|nd|rd|th)\b", en):
        out.append("ordinal suffix after a variable")
    if kind == "event":
        if jp.count("{8300}") != en.count("{8300}"):
            out.append(f"page count {en.count('{8300}') + 1} != JP {jp.count('{8300}') + 1} (keep one page per JP page;"
                       " the build adds pages when text overflows)")
        inline = re.findall(r"\{94(?:C[89A-F]|[D-F][0-9A-F])\}([^{「]*)(?:\{[0-9A-F]{4}\})*「?", en)
        if len(re.findall(r"\{94(?:C[89A-F]|[D-F][0-9A-F])\}", jp)) and any(
                not re.search(r"\{94(?:C[89A-F]|[D-F][0-9A-F])\}[^{「]*(?:\{[0-9A-F]{4}\})*「", p)
                for p in fit.split_pages(en) if re.search(r"\{94(?:C[89A-F]|[D-F][0-9A-F])\}", p)):
            out.append("inline speaker: write the name right after {94C8} and end it with 「")
        for name in inline:
            if fit.width(name) > fit.NAME_PX or len(name) > 9:
                out.append(f"speaker name {name!r} longer than 9 glyphs / {fit.NAME_PX} px")
        out += fit.problems(fit.fit(en, jp))
    return out

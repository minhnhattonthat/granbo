"""fit.py: wrap English message text into the game's lines and pages (event messages and other message windows).

Translators write each page as plain text: control codes kept, no line breaks needed. fit() wraps every page by
pixel width (font_en advances), inserts the newline code the Japanese page used, and splits a page that needs more
than LINES lines into extra pages, repeating its portrait/speaker codes (not the 80xx message-start code).
Box geometry (docs/re/text.md, measured with --qa ruler builds): a line ends at cell 28 (x=224); {82xx} starts the
next line at cell xx; a speaker page's first line starts at cell 7 (after the 6-cell name).
    fit(en, jp) -> fitted en string;  problems(fitted) -> list of lint messages
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import font_en  # noqa: E402

LINE_END = 28 * 8
LINES = 3
PAGE_UNITS = 136  # IWRAM page buffer 0x030026B0-0x030027BF, after {94xx} expansion
NAME_PX = 46  # speaker name field: cells 1-6, text starts at cell 7 (x=56); also the worst case for a player name
TOKEN = re.compile(r"\{[0-9A-F]{4}\}|\n|[^{\n]")
PAGE = "{8300}"
END_CODES = re.compile(r"((?:\{(?:84|81|8B|8C|8D|8F)[0-9A-F]{2}\})*)$")


def split_pages(s):
    return s.split(PAGE)


def header(page):
    """Leading control codes (+ an inline speaker name through 「 for {94C8}+)."""
    m = re.match(r"((?:\{[0-9A-F]{4}\})*)", page)
    h = m.group(1)
    rest = page[len(h):]
    if re.search(r"\{94(C[89A-F]|[D-F][0-9A-F])\}$", h) and "「" in rest:
        name, _, _ = rest.partition("「")
        h += name + "「"
    return h


def is_speaker(h):
    return bool(re.search(r"\{94(9[6-9A-F]|[A-F][0-9A-F])\}", h))


def newline_code(jp_page, h):
    m = re.search(r"\{(82[0-9A-F]{2})\}", jp_page)
    if m:
        return "{" + m.group(1) + "}"
    if "\n" in jp_page:
        return "\n"
    return "{8207}" if is_speaker(h) else "\n"


def start_cell(code):
    return 0 if code == "\n" else int(code[3:5], 16)


def tok_width(tok, names=None):
    if tok.startswith("{"):
        v = int(tok[1:5], 16)
        if v >> 8 == 0x94 and (v & 0xFF) < 0x96:
            return (names or {}).get(v & 0xFF, NAME_PX)
        return 0
    return font_en.advance(tok) if tok in font_en.ART else 8


def width(s, names=None):
    return sum(tok_width(t, names) for t in TOKEN.findall(s))


def wrap(body, first_px, px, names=None):
    """Greedy wrap of body (no newlines) into lines: first line `first_px` wide, the rest `px`."""
    words = re.findall(r"\S+|\s+", body)
    lines, cur = [], ""
    for w in words:
        if w.isspace():
            if cur:
                cur += " "
            continue
        limit = first_px if not lines else px
        cand = cur + w
        if cur and width(cand.rstrip(), names) > limit:
            lines.append(cur.rstrip())
            cur = w
        else:
            cur = cand
    if cur.strip():
        lines.append(cur.rstrip())
    return lines or [""]


def fit_page(page, jp_page, cont_header, names=None):
    h = header(page)
    tail = END_CODES.search(page[len(h):]).group(1)
    body = page[len(h):len(page) - len(tail)] if tail else page[len(h):]
    body = re.sub(r"\{82[0-9A-F]{2}\}|\n", " ", body)
    code = newline_code(jp_page, h)
    px = LINE_END - start_cell(code) * 8
    first = LINE_END - (7 * 8 if is_speaker(h) else start_cell(code) * 8)
    first -= width(h, names) if not is_speaker(h) else 0
    lines = wrap(body.strip(), first, px, names)
    pages = []
    for i in range(0, len(lines), LINES):
        hh = h if i == 0 else cont_header
        pages.append(hh + code.join(lines[i:i + LINES]))
    return PAGE.join(pages) + tail


def fit(en, jp):
    """Fit a whole message. Pages map to the JP's pages by index (for the newline code)."""
    jp_pages = split_pages(jp)
    out = []
    for i, page in enumerate(split_pages(en)):
        jp_page = jp_pages[min(i, len(jp_pages) - 1)]
        h = header(page)
        cont = re.sub(r"\{80[0-9A-F]{2}\}", "", h)
        out.append(fit_page(page, jp_page, cont))
    return PAGE.join(out)


def problems(fitted, names=None):
    out = []
    for n, page in enumerate(split_pages(fitted), 1):
        h = header(page)
        units = len(TOKEN.findall(page)) + 1
        if units > PAGE_UNITS:
            out.append(f"page {n}: {units} units > {PAGE_UNITS}")
        lines = re.split(r"\{82[0-9A-F]{2}\}|\n", page[len(h):])
        if len(lines) > LINES:
            out.append(f"page {n}: {len(lines)} lines > {LINES}")
        for i, line in enumerate(lines):
            start = (7 * 8 if is_speaker(h) else 0) if i == 0 else start_cell(
                re.findall(r"\{82[0-9A-F]{2}\}|\n", page)[i - 1]) * 8
            w = (width(h, names) if not is_speaker(h) and i == 0 else 0) + width(line, names)
            if start + w > LINE_END:
                out.append(f"page {n} line {i + 1}: {start + w - LINE_END} px too wide")
    return out


if __name__ == "__main__":
    jp = "{8002}{8620}{94A7}「・・・平和じゃのう・・・」{8300}{8620}{94A7}「良い事{8207}元{8207}たいくつ」{8400}{8100}"
    en = ("{8002}{8620}{94A7}...How peaceful.{8300}{8620}{94A7}I'm sure it's a good thing, but for a former "
          "Granbo Saver like me, it's dreadfully dull! Nothing ever happens around here anymore, does it?{8400}{8100}")
    f = fit(en, jp)
    print(f)
    print(problems(f) or "ok")

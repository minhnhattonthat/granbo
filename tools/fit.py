"""fit.py: wrap English message text into the game's lines and pages (event messages and other message windows).

Translators write each page as plain text: control codes kept, no line breaks needed. fit() wraps every page by
pixel width (font_en advances), inserts the newline code the Japanese page used, and splits a page that needs more
than LINES lines into extra pages, repeating its portrait/speaker codes (not the 80xx message-start code).
Box geometry (docs/re/text.md, measured in the field box with --qa builds): text may run to x=224; {8200} starts
the next line at x=8, {82xx} at x=8+8*xx ({8207}: x=64, right of the portrait). A speaker page's first line starts
right after the name field: the name padded with spaces (3 px each under the VWF) to 8 units (RAM name slots) or
10 units (inline {94C8} labels), from x=8 (tools/engine.py widens the game's 6-unit loops).
    fit(en, jp) -> fitted en string;  problems(fitted) -> list of lint messages
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import font_en  # noqa: E402
import names as names_mod  # noqa: E402

LINE_END = 224
LINE_X = 8
LINES = 3
PAGE_UNITS = 136  # IWRAM page buffer 0x030026B0-0x030027BF, after {94xx} expansion
NAME_PX = 46  # widest speaker name / label; also the worst case for the player's name
TABLE_NAME_PX = 110  # worst case for a {94xx} place/table name in running text until those are measured
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


def line_x(code):
    return LINE_X + (0 if code == "\n" else 8 * int(code[3:5], 16))


def first_x(h):
    """x where a page's first line starts: after the padded speaker name, else LINE_X."""
    m = names_mod.INLINE.search(h)
    if m:
        label = m.group(2)
        return LINE_X + width(label) + 3 * max(1, 10 - len(label))
    m = re.search(r"\{94([0-9A-F]{2})\}", h)
    if m and int(m.group(1), 16) >= 0x96:
        k = int(m.group(1), 16) - 0x96
        name = names_mod.SLOTS[k] if 0 < k < len(names_mod.SLOTS) else None
        return LINE_X + (width(name) + 3 * (8 - len(name)) if name else NAME_PX + 3)
    return LINE_X


def tok_width(tok, names=None):
    if tok.startswith("{"):
        v = int(tok[1:5], 16)
        if v >> 8 == 0x94 and (v & 0xFF) < 0x96:
            k = v & 0xFF
            if k in (names or {}):
                return names[k]
            if 0 < k < 0x1E and k < len(names_mod.SLOTS):
                return width(names_mod.SLOTS[k])
            return NAME_PX if k < 0x1E else TABLE_NAME_PX
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
    jp_tail = END_CODES.search(jp_page).group(1)
    jp_body = jp_page[:len(jp_page) - len(jp_tail)] if jp_tail else jp_page
    choice = bool(re.search(r"(\{82[0-9A-F]{2}\}|\n)$", jp_body))  # empty last line kept for a Yes/No prompt
    px = LINE_END - line_x(code)
    first = LINE_END - first_x(h) - (width(h, names) if not is_speaker(h) else 0)
    if is_speaker(h):  # a name code after the speaker ("{949B}{9400}, have you...") prints as running text
        m = re.search(r"((?:\{94(?:[0-8][0-9A-F]|9[0-5])\})+)$", h)
        first -= width(m.group(1), names) if m else 0
    # "{9400} and friends...": a header ending in a name code that is running text keeps the space after it
    lead = " " if body[:1] == " " and re.search(r"\{94[0-9A-F]{2}\}$", h) and not is_speaker(h) else ""
    lines = wrap(body.strip(), first - width(lead), px, names)
    lines[0] = lead + lines[0]
    chunks, i = [], 0
    while i < len(lines):
        n = LINES - 1 if choice and len(lines) - i <= LINES - 1 else LINES
        if choice and len(lines) - i == LINES:
            n = LINES - 1  # last chunk must leave the prompt line free
        chunks.append(lines[i:i + n])
        i += n
    pages = []
    for k, chunk in enumerate(chunks):
        hh = h if k == 0 else cont_header
        pages.append(hh + code.join(chunk) + (code if choice and k == len(chunks) - 1 else ""))
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
        lines = re.split(r"\{82[0-9A-F]{2}\}|\n", END_CODES.sub("", page[len(h):]))
        if len(lines) > LINES:
            out.append(f"page {n}: {len(lines)} lines > {LINES}")
        for i, line in enumerate(lines):
            start = first_x(h) if i == 0 else line_x(re.findall(r"\{82[0-9A-F]{2}\}|\n", page)[i - 1])
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

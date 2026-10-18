"""ligatures.py: two-letter glyphs so Granbo names fit their 6-byte RAM field.

A Granbo's name is stored in its RAM record as 6 single-byte glyph codes (0x0804B73C packs a name string into them,
0x0804B71C expands them back for display), so an English species name must encode to <= 6 codes, each < 256.
Names longer than 6 letters get letter pairs as one "wide" glyph: the pair is drawn as two 8 px font cells (codes
c and c+1, both in the kana range 0x0B-0xAB that English text never uses) and WIDTHS[c] is the pair's advance
(> 8), which tells the VWF blitters (asm/vwf*.s) to draw c+1 as the right half.
    plan(files) -> {"names": {entry id: [chunk, ...]}, "pairs": {pair: code}}
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import font_en  # noqa: E402

FIRST, LAST = 0x0B, 0xAB  # kana codes free in English (pairs use c and c+1)
MAX_CODES = 6
MAX_PX = 16


def species_entries(files):
    """The species-name strings: each follows a 「こいつは…」 database comment in the Granbo records (t290574)."""
    d = files["ptr/t290574.json"]["entries"]
    return [d[i + 1] for i, e in enumerate(d[:-1]) if e["jp"].startswith("「こいつは") and d[i + 1].get("en")]


def pair_px(p):
    return font_en.advance(p[0]) + font_en.advance(p[1])


def fits(p):
    """A pair's ink must fit in 16 px: the first letter's advance plus the second letter's art."""
    return font_en.advance(p[0]) + font_en.width(p[1]) <= MAX_PX


def chunk(name, known):
    """Split name into <= MAX_CODES chunks of 1-2 letters, preferring pairs already in `known`."""
    out = list(name)
    for prefer in (True, False):
        i = 0
        while len(out) > MAX_CODES and i < len(out) - 1:
            p = out[i] + out[i + 1]
            if len(out[i]) == 1 and len(out[i + 1]) == 1 and fits(p) and (not prefer or p in known):
                out[i:i + 2] = [p]
            i += 1
    if len(out) > MAX_CODES:
        raise ValueError(f"cannot fit Granbo name {name!r} into {MAX_CODES} codes")
    return out


def plan(files):
    names, pairs = {}, {}
    for e in species_entries(files):
        en = e["en"]
        if len(en) <= MAX_CODES:
            continue
        chunks = chunk(en, pairs)
        for c in chunks:
            if len(c) == 2 and c not in pairs:
                pairs[c] = FIRST + 2 * len(pairs)
        names[e["id"]] = chunks
    if pairs and max(pairs.values()) + 1 > LAST:
        raise OverflowError(f"{len(pairs)} letter pairs need codes past {LAST:#x}")
    return {"names": names, "pairs": pairs}


def glyphs(pair):
    """(left 0x40 bytes, right 0x40 bytes) for a pair: the two letters' art side by side, split at x=8."""
    a, b = font_en.pixels(pair[0]), font_en.pixels(pair[1])
    xa = font_en.advance(pair[0])
    rows = [[3] * 16 for _ in range(16)]
    for y in range(16):
        for x in range(8):
            if a[y][x] != 3:
                rows[y][x] = a[y][x]
            if b[y][x] != 3 and xa + x < 16:
                rows[y][xa + x] = b[y][x]
    halves = []
    for x0 in (0, 8):
        out = bytearray()
        for half in (0, 8):
            for y in range(half, half + 8):
                for x in range(x0, x0 + 8, 2):
                    out.append(rows[y][x] | rows[y][x + 1] << 4)
        halves.append(bytes(out))
    return halves[0], halves[1]

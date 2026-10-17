"""text.py: Granbo string codec. A string is u16 LE units up to and including 0x8500 (end).

Units < 512 are glyphs (tools/gen_tbl.py GLYPHS). Every other unit is a control code written `{XXXX}` (4 hex
digits), except the aliases below. decode() drops the final {end}; encode() appends it. Roundtrip is exact.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_tbl import GLYPHS  # noqa: E402

END = 0x8500
ALIASES = {0x8200: "\n"}  # plain newline; other 82xx stay hex (they set the next line's start column, guess)
CHAR = {c: i for i, c in enumerate(GLYPHS) if c != " " or i == 0}
CHAR.update({v: k for k, v in ALIASES.items()})
# ASCII typed by translators -> the font's own glyphs
ASCII = {"!": "！", "?": "？", ",": "、", ".": "。", "+": "＋", "-": "－", "/": "／", "=": "＝", "(": "（",
         ")": "）", "~": "～", "'": "”", '"': "”"}


def units(rom, off, limit=8000):
    """u16 units from off up to and including END."""
    out = []
    for i in range(limit):
        v = struct.unpack_from("<H", rom, off + 2 * i)[0]
        out.append(v)
        if v == END:
            return out
    raise ValueError(f"no end within {limit} units of {off:#x}")


def decode_units(us):
    assert us and us[-1] == END, us[-1:]
    out = []
    for v in us[:-1]:
        if v < 512:
            out.append(GLYPHS[v])
        elif v in ALIASES:
            out.append(ALIASES[v])
        else:
            out.append("{%04X}" % v)
    return "".join(out)


def decode(rom, off):
    us = units(rom, off)
    return decode_units(us), 2 * len(us)


def encode_units(text, ascii_map=False):
    out, i = [], 0
    while i < len(text):
        ch = text[i]
        if ch == "{":
            j = text.index("}", i)
            out.append(int(text[i + 1:j], 16))
            i = j + 1
            continue
        if ascii_map and ch in ASCII:
            ch = ASCII[ch]
        if ch not in CHAR:
            raise ValueError(f"no glyph for {ch!r} in {text!r}")
        out.append(CHAR[ch])
        i += 1
    return out + [END]


def encode(text, ascii_map=False):
    us = encode_units(text, ascii_map)
    return struct.pack("<%dH" % len(us), *us)

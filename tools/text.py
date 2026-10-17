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


def encode_units(text):
    """Japanese text (as decoded) -> units."""
    out, i = [], 0
    while i < len(text):
        ch = text[i]
        if ch == "{":
            j = text.index("}", i)
            out.append(int(text[i + 1:j], 16))
            i = j + 1
            continue
        if ch not in CHAR:
            raise ValueError(f"no glyph for {ch!r} in {text!r}")
        out.append(CHAR[ch])
        i += 1
    return out + [END]


def encode(text):
    us = encode_units(text)
    return struct.pack("<%dH" % len(us), *us)


def encode_en_units(s):
    """English text -> units with the English font's codes (tools/engine.py EN_CODES); `{XXXX}` stays a code."""
    from engine import EN_CODES
    out, i = [], 0
    while i < len(s):
        ch = s[i]
        if ch == "{":
            j = s.index("}", i)
            out.append(int(s[i + 1:j], 16))
            i = j + 1
            continue
        if ch == "\n":
            out.append(0x8200)
        elif ch in EN_CODES:
            out.append(EN_CODES[ch])
        else:
            raise ValueError(f"no English glyph for {ch!r} in {s!r}")
        i += 1
    return out + [END]


def encode_en(s):
    us = encode_en_units(s)
    return struct.pack("<%dH" % len(us), *us)

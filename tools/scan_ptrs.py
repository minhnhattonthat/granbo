"""scan_ptrs.py: candidate text pointers in the original ROM (analysis only, writes nothing).

A candidate is an aligned u32 0x08xxxxxx whose target is even and decodes as glyph codes / control codes up to an
8500 terminator. Prints pointer runs (tables) and isolated pointers (code literal pools) with the first string.
    python -X utf8 tools/scan_ptrs.py [--lo 0x1A0000 --hi 0x2A0000] [--min-run 1]
"""
import argparse
import struct
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom/0291 - Granbo (J)(Lord Moyne).gba"
CTRL_HI = {0x80, 0x81, 0x82, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8A, 0x8B, 0x8C, 0x8D, 0x8E, 0x8F,
           0x90, 0x91, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98}


def string_len(rom, t, limit=4000):
    """Units up to and including 8500, or None if a non-text unit comes first."""
    for i in range(limit):
        v = struct.unpack_from("<H", rom, t + 2 * i)[0]
        if v == 0x8500:
            return i + 1
        if v >= 512 and (v >> 8) not in CTRL_HI:
            return None
    return None


def scan(rom, lo, hi):
    n = len(rom) // 4
    words = struct.unpack("<%dI" % n, rom)
    hits = []
    for i, v in enumerate(words):
        t = v - 0x08000000
        if lo <= t < hi and not t & 1 and string_len(rom, t):
            hits.append((i * 4, t))
    return hits


def runs(hits):
    out, cur = [], []
    for p, t in hits:
        if cur and p == cur[-1][0] + 4:
            cur.append((p, t))
        else:
            if cur:
                out.append(cur)
            cur = [(p, t)]
    if cur:
        out.append(cur)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lo", type=lambda s: int(s, 0), default=0x1A0000)
    ap.add_argument("--hi", type=lambda s: int(s, 0), default=0x2A0000)
    ap.add_argument("--min-run", type=int, default=1)
    a = ap.parse_args()
    rom = ROM.read_bytes()
    hits = scan(rom, a.lo, a.hi)
    targets = defaultdict(list)
    for p, t in hits:
        targets[t].append(p)
    print(f"{len(hits)} pointers, {len(targets)} distinct targets")
    for r in runs(hits):
        if len(r) >= a.min_run:
            print(f"run {r[0][0]:#08x} n={len(r):5d} -> {min(t for _, t in r):#08x}..{max(t for _, t in r):#08x}")

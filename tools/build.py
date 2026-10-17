"""build.py: original ROM + script/*.json -> build/granbo_en.gba (+ build/writes.txt for romdiff.py --writes).

Placement (docs/re/text.md): new data goes past the original 8 MiB (0x800000+).
- events: a block with any `en` is copied verbatim to new space with every message re-encoded and appended after
  the copy; its offset table entries are rewritten to the appended messages, and every block literal is repointed.
  The verbatim copy keeps any table index the dump missed pointing at valid (Japanese) text.
- ptr strings: an entry with `en` is appended once (identical texts share one copy) and every pointer is repointed.
No `en` anywhere -> output == original (identity build, tests/test_build.py).
    python -X utf8 tools/build.py [--out build/granbo_en.gba] [--lang en] [--marker]
"""
import argparse
import json
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_rom  # noqa: E402
import engine  # noqa: E402
import text  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom/0291 - Granbo (J)(Lord Moyne).gba"
NEW_BASE = 0x800000
GBA = 0x08000000


class Rom:
    def __init__(self, orig):
        self.orig = orig
        self.data = bytearray(orig)
        self.writes = []
        self.free = NEW_BASE

    def put(self, off, data, by):
        assert off + len(data) <= len(self.data), (hex(off), by)
        self.writes.append("%X %s %s %s" % (off, self.orig[off:off + len(data)].ljust(len(data), b"\xff").hex(),
                                            data.hex(), by))
        self.data[off:off + len(data)] = data

    def alloc(self, data, by, align=4):
        self.free = (self.free + align - 1) & ~(align - 1)
        off = self.free
        if off + len(data) > 0x2000000:
            raise OverflowError("ROM past 32 MiB")
        if off + len(data) > len(self.data):
            self.data.extend(b"\xff" * (off + len(data) - len(self.data)))
        self.put(off, data, by)
        self.free = off + len(data)
        return off

    def finish(self):
        if len(self.data) > len(self.orig):  # pad to a 64 KiB multiple
            self.data.extend(b"\xff" * (-len(self.data) % 0x10000))
        return bytes(self.data)


def load_script(root=ROOT / "script"):
    files = {}
    for p in sorted(root.rglob("*.json")):
        files[p.relative_to(root).as_posix()] = json.loads(p.read_text(encoding="utf-8"))
    return files


def MARKER(e):
    """Marker text: every control code of the jp kept (windows, waits and portraits need them), the first text
    run replaced by the id in English-font glyphs (the font has no [ or _), later runs by '+'."""
    out, first = [], True
    for tok in re.findall(r"\{[0-9A-F]{4}\}|\n|[^{\n]+", e["jp"]):
        if tok.startswith("{") or tok == "\n":
            out.append(tok)
        elif first:
            out.append("<" + e["id"].replace("_", "-") + ">")
            first = False
        else:
            out.append("+")
    return "".join(out) if not first else "<" + e["id"].replace("_", "-") + ">" + "".join(out)


def text_of(e, lang, marker):
    if marker:
        return marker(e)
    return e.get(lang) or None


def build(orig, files, lang="en", marker=None, engine_patch=True):
    """engine_patch=False with no translations gives the original ROM (identity build)."""
    r = Rom(orig)
    if engine_patch:
        engine.patch(r)
    for name, f in files.items():
        if not name.startswith("events/"):
            continue
        new = [(e, text_of(e, lang, marker)) for e in f["entries"]]
        if not any(t for _, t in new):
            continue
        b, t = int(f["block"], 16), int(f["table"], 16)
        # verbatim copy of the old block (through the end of its last message), then the new messages
        last = max((b + 2 * struct.unpack_from("<H", orig, t + 2 * i)[0] for e in f["entries"] for i in e["idx"]))
        copy_end = last + len(b"".join([struct.pack("<H", u) for u in text.units(orig, last)]))
        blob = bytearray(orig[b:copy_end])
        offs = {}
        for e, s in new:
            enc = text.encode_en(s) if s else text.encode(e["jp"])
            offs[e["id"]] = len(blob) // 2
            blob += enc
        if len(blob) > 0x20000:
            raise OverflowError(f"{name}: block {len(blob):#x} bytes > u16 unit offsets")
        nb = r.alloc(bytes(blob), f"block {name}")
        for e, _ in new:
            for i in e["idx"]:
                r.put(t + 2 * i, struct.pack("<H", offs[e["id"]]), f"table {e['id']}")
        for lit in f["block_lits"]:
            lo = int(lit, 16)
            assert struct.unpack_from("<I", orig, lo)[0] == GBA + b, (name, lit)
            r.put(lo, struct.pack("<I", GBA + nb), f"blockptr {name}")
    placed = {}
    for name, f in files.items():
        if not name.startswith("ptr/"):
            continue
        for e in f["entries"]:
            s = text_of(e, lang, marker)
            if not s:
                continue
            enc = text.encode_en(s)
            if enc not in placed:
                placed[enc] = r.alloc(enc, f"str {e['id']}", align=2)
            at = int(e["at"], 16)
            for p in e["ptrs"]:
                po = int(p, 16)
                assert struct.unpack_from("<I", orig, po)[0] == GBA + at, (e["id"], p)
                r.put(po, struct.pack("<I", GBA + placed[enc]), f"ptr {e['id']}")
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "build/granbo_en.gba"))
    ap.add_argument("--lang", default="en")
    ap.add_argument("--marker", action="store_true", help="every string -> its id (marker build)")
    a = ap.parse_args()
    check_rom.check()
    orig = ROM.read_bytes()
    marker = MARKER if a.marker else None
    r = build(orig, load_script(), a.lang, marker)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(r.finish())
    out.with_name("writes.txt").write_text("\n".join(r.writes) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {out} ({len(r.writes)} writes, new data to {r.free:#x})")


if __name__ == "__main__":
    main()

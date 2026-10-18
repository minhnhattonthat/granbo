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
import find_rel  # noqa: E402
import fit  # noqa: E402
import gfx  # noqa: E402
import ligatures  # noqa: E402
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


CENTRED = {"ptr/r290000.json", "ptr/r1B0000.json"}  # narration subtitles, centred in the JP by leading spaces


def centre(s):
    """Re-pad a subtitle line: N spaces put the text at x = 8N (vwf_menu snaps text after 2+ spaces to its
    monospace column), so pick N for a centred line; past 28 cells (the JP's widest line) fall back to 1 space."""
    t = s.lstrip(" ")
    w = fit.width(t)
    n = max(2, round((240 - w) / 16))
    return " " * (n if 8 * n + w <= 224 else 1) + t


GAP = "\N{EM SPACE}"  # blank glyph with an 8 px advance (engine.EN_CODES, font_en)


def clear_portrait(s):
    """Battle dialogue (t1A1568): the battle box leaves the speaker's name slot empty, so a page starts after the
    blank name's padding - 48 px in the JP (6 cells), 24 px under the VWF (8 spaces), under the 32 px portrait.
    GAP glyphs (blank, 8 px each) after each portrait+speaker header put the text clear of it."""
    pages = []
    for page in fit.split_pages(s):
        h = fit.header(page)
        if re.search(r"\{86[0-9A-F]{2}\}", h) and fit.is_speaker(h):
            page = h + GAP * 3 + page[len(h):].lstrip(" ")
        pages.append(page)
    return fit.PAGE.join(pages)


def place_rel(r, orig, files, lang, marker):
    """Strings code reaches as base pointer + fixed offset (tools/find_rel.py: kind "adds" = `adds rX, #off` at
    site, "subs" = `subs rX, #-off`, "word" = a literal word holding off, "neg" = `movs rX, #-off`, then
    negated). Every string linked this way is placed in one block, in original order (offset signs stay), and each
    site rewritten. Targets without a script entry are skipped (find_rel.py --missing lists them). Returns
    {id: new offset} for the ptr loop."""
    ents = {e["id"]: e for n, f in files.items() if n.startswith("ptr/") for e in f["entries"]}
    by_at = {int(e["at"], 16): i for i, e in ents.items()}
    rels = [(by_at[t], b, k, s) for t, b, k, s in find_rel.relations(orig, ents.values()) if t in by_at]
    group = {}
    for a, b, _, _ in rels:  # union of linked ids
        ga, gb = group.get(a, {a}), group.get(b, {b})
        for i in ga | gb:
            group[i] = ga | gb
    new = {}
    for g in {frozenset(g) for g in group.values()}:
        if not any(text_of(ents[i], lang, marker) for i in g):
            continue  # nothing translated: leave the original strings and offsets alone
        for i in sorted(g, key=lambda i: int(ents[i]["at"], 16)):
            s = text_of(ents[i], lang, marker)
            new[i] = r.alloc(text.encode_en(s) if s else text.encode(ents[i]["jp"]), f"str {i} (rel)", align=2)
    seen = {}
    for a, b, kind, site in rels:
        if a not in new:
            continue
        assert seen.setdefault(site, (a, b)) == (a, b), (hex(site), a, b, seen[site])  # one meaning per site
        off, old = new[a] - new[b], int(ents[a]["at"], 16) - int(ents[b]["at"], 16)
        if kind == "word":
            assert struct.unpack_from("<i", orig, site)[0] == old, (a, hex(site))
            r.put(site, struct.pack("<i", off), f"rel {a}")
            continue
        hw = struct.unpack_from("<H", orig, site)[0]
        sign = 1 if kind == "adds" else -1
        op = {"adds": 0b00110, "subs": 0b00111, "neg": 0b00100}[kind]  # adds/subs/movs rX, #imm8
        assert hw >> 11 == op, (a, hex(site))
        assert hw & 0xFF == sign * old and 0 <= sign * off < 256, (a, hex(site), off)
        r.put(site, struct.pack("<H", hw & 0xFF00 | sign * off), f"rel {a}")
    return new


def build(orig, files, lang="en", marker=None, engine_patch=True):
    """engine_patch=False with no translations gives the original ROM (identity build)."""
    r = Rom(orig)
    lig = ligatures.plan(files) if engine_patch and lang == "en" else {"names": {}, "pairs": {}}
    if engine_patch:
        engine.patch(r, lig)
        if lang == "en":
            gfx.patch(r, lig["pairs"])
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
            enc = text.encode_en(fit.fit(s, e["jp"]) if not marker else s) if s else text.encode(e["jp"])
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
    grp = place_rel(r, orig, files, lang, marker)
    for name, f in files.items():
        if not name.startswith("ptr/"):
            continue
        for e in f["entries"]:
            s = text_of(e, lang, marker)
            if not s and e["id"] not in grp:
                continue
            at = int(e["at"], 16)
            if e["id"] in grp:  # placed by place_rel
                new = grp[e["id"]]
            else:
                if not marker and e["id"] in lig["names"]:  # Granbo name: <= 6 codes with letter pairs
                    us = [lig["pairs"][c] if len(c) == 2 else engine.EN_CODES[c] for c in lig["names"][e["id"]]]
                    enc = struct.pack("<%dH" % (len(us) + 1), *us, text.END)
                else:
                    if name in CENTRED and e["jp"].startswith("  ") and "\n" not in e["jp"] and not marker:
                        s = centre(s)
                    if name == "ptr/t1A1568.json" and not marker:
                        s = clear_portrait(s)
                    enc = text.encode_en(s)
                if enc not in placed:
                    placed[enc] = r.alloc(enc, f"str {e['id']}", align=2)
                new = placed[enc]
            for p in e["ptrs"]:
                po = int(p, 16)
                assert struct.unpack_from("<I", orig, po)[0] == GBA + at, (e["id"], p)
                r.put(po, struct.pack("<I", GBA + new), f"ptr {e['id']}")
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "build/granbo_en.gba"))
    ap.add_argument("--lang", default="en")
    ap.add_argument("--marker", action="store_true", help="every string -> its id (marker build)")
    ap.add_argument("--qa", action="append", default=[], metavar="ID=TEXT",
                    help="override one entry's text (stress/width tests; \\n = newline)")
    a = ap.parse_args()
    check_rom.check()
    orig = ROM.read_bytes()
    files = load_script()
    qa = dict(q.split("=", 1) for q in a.qa)
    for f in files.values():
        for e in f["entries"]:
            if e["id"] in qa:
                e[a.lang] = qa.pop(e["id"]).replace("\\n", "\n")
                e["qa"] = True
    if qa:
        sys.exit(f"--qa: unknown ids {sorted(qa)}")
    marker = (lambda e: e[a.lang] if e.get("qa") else MARKER(e)) if a.marker else None
    r = build(orig, files, a.lang, marker)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(r.finish())
    out.with_name("writes.txt").write_text("\n".join(r.writes) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {out} ({len(r.writes)} writes, new data to {r.free:#x})")


if __name__ == "__main__":
    main()

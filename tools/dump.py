"""dump.py: extract every reachable string of the original ROM into script/*.json (jp + empty en).

Two kinds (docs/re/text.md):
- script/events/ev<BLOCK>.json: per-map message block; message n = BLOCK + 2*TABLE[n] (u16 offsets in units).
  The inserter rewrites TABLE in place and repoints the block literal(s) in the map init code.
- script/ptr/<group>.json: strings reached by u32 pointers (tables, record arrays, code literal pools).
  Each entry lists every pointer word; the inserter repoints all of them.
Existing files keep their `en`, `notes` and `status` per id; `jp` is refreshed and changes are reported.
    python -X utf8 tools/dump.py [--check]   (--check: write nothing, exit 1 if any file would change)
"""
import argparse
import json
import struct
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import map_blocks  # noqa: E402
import scan_ptrs  # noqa: E402
import text  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "script"
CODE_END = 0x1A0000
TEXT_LO, TEXT_HI = 0x1A0000, 0x2A0000
# Not text: compared byte for byte by code. Left untouched and out of the script.
DATA_RANGES = [(0x28CB98, 0x28D440)]  # name-entry profanity filter list (romaji + kana words), guess: ends ~0x28D440


def u16(rom, o):
    return struct.unpack_from("<H", rom, o)[0]


def is_data(off):
    return any(a <= off < b for a, b in DATA_RANGES)


def event_blocks(rom):
    """{block: {"table", "lits": [literal offsets], "msgs": [(index, unit offset)]}}"""
    st = map_blocks.stores(rom)
    blocks, tables = {}, {}
    for q, kind, v, lit in st:
        (blocks if kind == "block" else tables).setdefault(v, {"sites": set(), "lits": set()})
        d = (blocks if kind == "block" else tables)[v]
        d["sites"].add(q)
        d["lits"].add(lit)
    known = set(blocks) | set(tables)
    out = {}
    for b, bd in blocks.items():
        # the table stored next to this block's store (same init function)
        site = min(bd["sites"])
        t = min(((abs(min(td["sites"]) - site), tv) for tv, td in tables.items()))[1]
        msgs, n = [], 0
        while n < 4096:
            pos = t + 2 * n
            if n and pos in known:
                break
            o = u16(rom, pos)
            a = b + 2 * o
            if not (o == 0 or u16(rom, a - 2) == text.END):
                break
            try:
                text.units(rom, a)
            except ValueError:
                break
            msgs.append((n, o))
            n += 1
        out[b] = {"table": t, "lits": sorted(bd["lits"]), "tlits": sorted(tables[t]["lits"]), "msgs": msgs}
    return out


def strides(ps, min_len=3):
    """Pointer offsets that sit in an arithmetic run (constant stride <= 0x100) of >= min_len."""
    ok = set()
    ps = sorted(ps)
    for i in range(len(ps)):
        for j in range(i + 1, min(i + 4, len(ps))):
            d = ps[j] - ps[i]
            if not 4 <= d <= 0x100:
                continue
            run = [ps[i]]
            while run[-1] + d in set(ps):
                run.append(run[-1] + d)
            if len(run) >= min_len:
                ok.update(run)
    return ok


def pointer_strings(rom, event_lits, event_starts):
    hits = [(p, t) for p, t in scan_ptrs.scan(rom, TEXT_LO, TEXT_HI)
            if p not in event_lits and not is_data(t)]
    starts = lambda t: t in event_starts or u16(rom, t - 2) == text.END
    hits = [(p, t) for p, t in hits if starts(t)]
    inrun = {p for r in scan_ptrs.runs(hits) if len(r) >= 2 for p, _ in r}
    stride = strides([p for p, _ in hits if p >= CODE_END])
    code = {p for p, _ in hits if p < CODE_END and any(True for _ in map_blocks.literal_loads(rom, p))}
    good, rejected = defaultdict(list), []
    for p, t in hits:
        if p in inrun or p in stride or p in code:
            good[t].append(p)
        else:
            rejected.append((p, t))
    return good, rejected, inrun


def group_of(ptrs, inrun, rom_runs):
    p = min(ptrs)
    if p < CODE_END and p not in inrun:
        return "code"
    for start, end in rom_runs:
        if start <= p <= end:
            return f"t{start:06X}"
    return f"r{p >> 16:02X}0000"


def build(rom):
    files = {}
    ev = event_blocks(rom)
    event_lits = {l for d in ev.values() for l in d["lits"] + d["tlits"]}
    event_starts = set()
    for b, d in sorted(ev.items()):
        by_off = defaultdict(list)
        for n, o in d["msgs"]:
            by_off[o].append(n)
        entries = []
        for o, idx in sorted(by_off.items()):
            a = b + 2 * o
            event_starts.add(a)
            jp, _ = text.decode(rom, a)
            entries.append({"id": f"ev{b:06X}_{idx[0]:03d}", "idx": idx, "jp": jp, "en": ""})
        files[f"events/ev{b:06X}.json"] = {
            "block": f"{b:#08x}", "table": f"{d['table']:#08x}", "count": len(d["msgs"]),
            "block_lits": [f"{x:#08x}" for x in d["lits"]], "entries": entries}
    good, rejected, inrun = pointer_strings(rom, event_lits, event_starts)
    rom_runs = []  # pointer tables; record arrays (runs split by a few non-pointer fields) merge into one group
    for r in scan_ptrs.runs(sorted((p, 0) for ps in good.values() for p in ps)):
        if len(r) < 2:
            continue
        if rom_runs and r[0][0] - rom_runs[-1][1] <= 0x40:
            rom_runs[-1] = (rom_runs[-1][0], r[-1][0])
        else:
            rom_runs.append((r[0][0], r[-1][0]))
    groups = defaultdict(list)
    for t, ps in sorted(good.items()):
        jp, _ = text.decode(rom, t)
        groups[group_of(ps, inrun, rom_runs)].append(
            {"id": f"s{t:06X}", "at": f"{t:#08x}", "ptrs": [f"{p:#08x}" for p in sorted(ps)], "jp": jp, "en": ""})
    for g, entries in groups.items():
        files[f"ptr/{g}.json"] = {"entries": entries}
    return files, rejected


def merge(new, old):
    """Keep translator fields from old per id; return (merged, ids whose jp changed)."""
    keep = {e["id"]: e for e in old.get("entries", [])}
    changed = []
    for e in new["entries"]:
        o = keep.get(e["id"])
        if not o:
            continue
        for k in ("en", "notes", "status"):
            if k in o:
                e[k] = o[k]
        if o["jp"] != e["jp"] and o.get("en"):
            changed.append(e["id"])
    return new, changed


def dumps(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    import check_rom
    check_rom.check()
    rom = scan_ptrs.ROM.read_bytes()
    files, rejected = build(rom)
    dirty = 0
    for name, obj in sorted(files.items()):
        path = SCRIPT / name
        if path.exists():
            obj, changed = merge(obj, json.loads(path.read_text(encoding="utf-8")))
            for i in changed:
                print(f"jp changed for translated {i}: re-check its en")
        s = dumps(obj)
        if not path.exists() or path.read_text(encoding="utf-8") != s:
            dirty += 1
            if not a.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(s, encoding="utf-8", newline="\n")
    n = sum(len(f["entries"]) for f in files.values())
    print(f"{len(files)} files, {n} entries, {len(rejected)} rejected pointer candidates, {dirty} files changed")
    sys.exit(1 if a.check and dirty else 0)

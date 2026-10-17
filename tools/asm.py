"""asm.py: assemble asm/*.s (Thumb) with keystone at a fixed ROM address; symbols are substituted textually.

keystone mis-encodes conditional `bl` (skill platform-gba.md): none are used here, and assemble() checks every
instruction by disassembling the result with capstone and comparing mnemonics with the source.
    python -X utf8 tools/asm.py asm/vwf.s 0x087F3000 STATE=0x0203F000 WIDTHS=0x087F3400   (prints a listing)
"""
import re
import sys
from pathlib import Path

import capstone
import keystone

ROOT = Path(__file__).resolve().parents[1]


def assemble(path, base, symbols):
    src = "\n".join(l.split("@")[0].rstrip() for l in Path(path).read_text(encoding="utf-8").splitlines())
    for k, v in symbols.items():
        src = re.sub(rf"\b{k}\b", f"{v:#x}", src)
    ks = keystone.Ks(keystone.KS_ARCH_ARM, keystone.KS_MODE_THUMB)
    enc, _ = ks.asm(src, base)
    code = bytes(enc)
    _verify(src, code, base)
    return code


def _ops(src):
    out = []
    for line in src.splitlines():
        line = line.split("@")[0].strip()
        if not line or line.endswith(":") or line.startswith("."):
            continue
        line = re.sub(r"^\w+:\s*", "", line)
        if line.startswith("."):
            continue
        out.append(line.split()[0].lower())
    return out


def _verify(src, code, base):
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    want = _ops(src)
    ins = list(md.disasm(code, base))[:len(want)]
    got = [i.mnemonic for i in ins]
    bad = [(i, w, g) for i, (w, g) in enumerate(zip(want, got)) if g != w]
    # ARM7TDMI has no Thumb-2: every instruction must be 16-bit except bl (a 2-halfword pair)
    wide = [(i.address, i.mnemonic) for i in ins if i.size != 2 and i.mnemonic != "bl"]
    if len(got) < len(want) or bad or wide:
        raise AssertionError(f"assembly mismatch: {bad[:5]} wide={wide[:5]} (got {len(got)} of {len(want)})")


if __name__ == "__main__":
    path, base = sys.argv[1], int(sys.argv[2], 0)
    syms = {k: int(v, 0) for k, v in (a.split("=") for a in sys.argv[3:])}
    code = assemble(path, base, syms)
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    for i in md.disasm(code, base):
        print(f"{i.address:08X} {i.bytes.hex():10s} {i.mnemonic} {i.op_str}")
    print(f"{len(code)} bytes")

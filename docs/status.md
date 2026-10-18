# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 6 (translation) for event dialogue; 5 (engine) still open for menus/battle/fixed-cell text.
- **Done:**
  - Step 0 setup; recon (`docs/re/text.md`): u16 glyph text, 8x16 font + 8x8 small font, 254 event message
    blocks, ~3,600 pointer strings; table labels checked against script context.
  - Extract/build: `tools/dump.py` -> `script/`, `tools/build.py` relocates text past 8 MiB; roundtrip, identity and
    marker tests (`tests/`).
  - Engine: original English proportional font (`tools/font_en.py`), VWF for the message window (`asm/vwf.s`, hook at
    0x08056058, window column synced to pixels), speaker-name loops widened. Field-box geometry measured and used by
    `tools/fit.py` (auto-wrap + extra pages). Pilot batch b006 (opening at Old Gen's house) translated and checked
    in game.
  - Translator pipeline: `tools/batches.py split|check|merge`, `docs/translator-brief.md`, style reference,
    synopsis, glossary seed (names, places, NPC labels in `tools/names.py`).
- **Next:**
  - Merge translator waves (54 event batches, b006 done), review each, polish pass.
  - Pointer strings: names (t1A9A18 -> RAM name slots, 7 glyphs), places (t1AA48C), skills/Granbo data
    (t290574: name / 2-line description / space-padded battle description for fixed 8 px cells), battle messages
    (t1A1568, t098F4C, t1A952C), menus (`code.json`). Needs: which renderer draws each (fixed-cell routine
    0x0800F9B0 draws N cells, optional centring; 8x8 small font at 0x08310C58 for some), field widths.
  - 8x8 small font: add English glyphs for the codes the 8x16 font got in kanji slots (' : ; % & * #) or remap.
  - Graphics text survey (title logo グランボ, name entry grid, battle UI), debug/warp tool (phase 2, agent).
- **Open bugs:** speaker name tags still Japanese until t1A9A18 is translated.
- **Waiting on the user:** nothing.

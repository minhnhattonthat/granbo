# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 6 (translation) done as first drafts; 5 (engine) open for per-screen layout; 8 (QA) started.
- **Done:**
  - Recon, extraction, build with relocation, roundtrip/identity/marker tests; debug warp tool (20 scenes, all pass
    on the English build; `docs/re/debug.md`, `tools/debug/regen_states.py`).
  - Every string with text has an English draft: 4117 event messages, 3218 pointer strings (687 + 383 are code-only).
  - Engine (`tools/engine.py`, `asm/`): English proportional font; VWF in the message window (`vwf.s`), in
    draw_menu_string (`vwf_menu.s`: lazy cells, column snap after 2+ spaces, cell reload from VRAM across frames),
    in the typewriter window 0x0804B524 (own `vwf_menu.s` copy + `tw_wrap.s` column sync), in the fixed-cell routine
    0x0800F9B0 8x16 mode (`vwf_cells.s`); wide (two-letter) glyphs so Granbo names fit their 6-byte RAM field
    (`tools/ligatures.py`, 56 pairs in kana codes 0x0B-0x7A); speaker-name loops widened.
  - Batch tools: `tools/batches.py` (events), `tools/ptrbatches.py` (pointer strings, per-group pixel limits,
    `ID_UNITS` for strings copied into fixed RAM buffers), `tools/bisect_entries.py` (find the entry that breaks a
    warp scene).
  - Base+offset strings (docs/re/text.md): `tools/find_rel.py` traces code that adds offsets to a string pointer;
    the build places each linked group in order and rewrites the offsets; ~70 such strings added to code.json.
    Status, card, save, options, shop, storage/Data Ball menus, Yes/No prompts fixed by it.
  - Screens fixed: skills list (no per-row cost; description pads without cutting, `asm/pad_col.s`), name fields
    draw all 6 cells (`asm/name6.s` + vwf_menu name_fill), battle HUD names (`asm/hud_name.s`, compact font
    `tools/font_small.py`), stat/card/save column moves (engine.py), dialogue choice cursor (vwf.s run-start space =
    8 px), narration subtitles centred by the build (`build.centre`).
  - QA helpers: `tools/lua/setmoves.lua`, `setname.lua` (force move slots / name bytes), warp scene battle_moves.
- **Next (screen QA + fixes, see the warp tour after `regen_states.py`):**
  - the second status page using the stat labels (0x0808AF70, icons moved to x=160) is not reached by a warp scene:
    find and check it. Link-battle screens (Record W/L composite, FLAGGED 1-cell W/L) unverified.
  - intro subtitles (code.json s27196A.., fixed zero-padded slots, new-game opening) unchecked.
  - battle message lines: 12 merged lines over the box width (`ptrbatches.issues` over t1A1568); p002/p005/p006
    battle lines over-trimmed under an older check: restore fuller wording.
  - padded choice menus (278 strings): check alignment after the column snap.
  - other strings copied into fixed RAM buffers may overflow like the name-entry title did: a broad play/QA tour.
  - FLAGGED abbreviation: tournament list titles "X Cup" vs dialogue "X Saver Tournament" (glossary); measure field.
  - Graphics: title logo (グランボ katakana; draw original English lettering), name-entry grid (kana -> letters),
    battle UI labels (コウゲキ etc.), 8x8 small-font glyphs for ' : ; % & * # (kanji slots 0x1F0+).
  - Review pass on events (reviewer agents), whole-project sampled review, polish (Grazie's identity/voice -
    lines labelled Grazie read as a serious scientist father; "Bata" vs "Hop!" cry; Message Board capitalisation).
  - Release: BPS patch, README, jp_left scan, qa_gate.
- **Open bugs:** see Next.
- **Waiting on the user:** nothing.

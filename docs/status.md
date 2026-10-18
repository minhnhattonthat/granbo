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
- **Next (screen QA + fixes, see the warp tour `work/qa/all_scenes.png` after `regen_states.py`):**
  - skills list: name field ~52 px before the "E 4" cost (drawn by 0x0806A47C into its own tiles; row text from
    0x0804B71C at x=40): move the cost right; many move names are wider.
  - status screen: labels こうげき/ぼうぎょ/すばやさ overrun the AT./DF./SP. icons (32 px); evolution-EXP label garbled.
  - card screen ("NameKakeru", "Record 0d 0Type 0urn Limit"): composed strings + numbers overlap.
  - options screen: "◀sic▶" (value field truncated), "y" labels (所持数 also shows "y" in the shop).
  - prologue/attract narration (r1B0000, leading-space centring) still monospace and truncated: find its routine.
  - save prompt shows leftover prologue tiles under it: compare with the original.
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

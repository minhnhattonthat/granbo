# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 9 - released. v1.0 (patched CRC32 5DC2BC16) published 2026-10-18; v1.0.1 (fix #1, from a9c23ed,
  patched CRC32 A75C838B, all release steps pass) published by the user 2026-11-14 on GitHub releases.
  Visual QA gate: 419 sheets ok (`work/qa/verdicts/`; v1.0 verdicts archived in `work/qa/verdicts_v1.0/`).
  QA gotchas: `regen_states.py` defaults to the JP ROM (pass build/granbo_en.gba); the manifest's warp sheets are
  copies `work/qa/tour/warp_<scene>.png` of `work/qa/warp_<scene>/sheet.png` (copy them after a regen); the map
  tour is not deterministic, so every re-tour changes ~230 sheets.
- **Done:**
  - Recon, extraction, build with relocation, roundtrip/identity/marker tests; debug warp tool (21 scenes,
    `docs/re/debug.md`, `tools/debug/regen_states.py`); map tour of every map variant (`tools/debug/map_tour.py`,
    sheets in `work/qa/tour/`).
  - All text translated and reviewed: 4117 event messages (review pass 1, `tools/review.py split`, 122 fixes) and
    ~3290 pointer strings (review pass 2, `split-ptr`, 240 fixes). Briefs: `docs/reviewer-brief.md`,
    `docs/ptr-reviewer-brief.md`.
  - Engine (`tools/engine.py`, `asm/`): proportional font + VWF in the message window (`vwf.s`; a run-start space
    keeps 8 px for the choice cursor), draw_menu_string (`vwf_menu.s`; name fields drawn to their 6-cell end via
    `asm/name6.s`), the typewriter window, the fixed-cell routine; two-letter glyphs for Granbo names; battle HUD
    names (`asm/hud_name.s`, compact font `tools/font_small.py`); skills list without the per-row cost and an
    uncut description line (`asm/pad_col.s`); column moves on status/card/save; English name-entry keyboard.
  - Base+offset strings (docs/re/text.md): `tools/find_rel.py` traces them (adds/subs/word/neg); the build places
    each group and rewrites the offsets; a test fails if a derived string has no entry.
  - Graphics (`tools/gfx.py`, docs/re/graphics.md): title logo (`tools/gen_title.py` -> `assets/title_en.png`),
    battle command labels, element pictograms, 通信中 -> Linking, small-font punctuation.
  - Title redesign: custom angular GRANBO lettering, silver bevels and indigo extrusion; original 240x160
    indexed palette and 600-tile budget retained. Regeneration is byte-identical; 10 tests, build and cold-boot
    smoke pass; independent visual review and `title_logo_manifest.tsv` QA gate pass (1 sheet).
    Before: `work/qa/title_logo_before/final.png`; after: `work/qa/title_logo/final.png`.
    The local build and the rebuilt v1.0 release archive include this redesign.
  - Playtest fixes: Yes/No prompt line keeps the JP newline (an {8207} one pushed "No" past the canvas at
    0x03000CC0 into game state 0x03002320: crash at ev1BC98C_012); speaker text starts at x=64 on every line
    (D8: 「 tabs there in vwf.s, fit adds it after RAM-slot names); GAP drawn opaque so the choice cursor erases.
    QA round 2: prompt line stays on the JP's line ("Got all that?" {8207}\n); pointer-table dialogue with a
    speaker is fitted too (field box x=64; battle box {8A01} gets clear_portrait, x=48); overflowing pages split
    evenly (no 1-word widow page); continuation pages drop a running-text name code ({9408}); Grisha spelling.
  - Release tooling: `tools/release.py <ver>` (build, tests, jp_left with `docs/jp_known.txt`, qa_gate, smoke, BPS,
    README from `docs/README-release.txt`, zip in release/; never publishes).
  - QA-pass fixes: battle dialogue clears the portrait (`build.clear_portrait`), battle move popup 12 cells in a
    14-wide box, small-font pair glyphs (Data Ball grids), element icon copies, fit width fixes for name codes.
- **Issue #1 (2026-11-14):** the Grand Change result message ('グランドチェンジはかんりょうしました') and
  '子分の服をきがえた' were never extracted: event-script message pointers {0x38, ptr} sat outside any run, so
  dump.py rejected them; the JP text then drew through the EN font as garbage. dump.py now accepts them
  (`script/ptr/r1A0000.json`), test `test_event_script_messages_have_entries`, warp scene `grand_change_done`.
  Note: re-running dump.py rewrites `script/ptr/code.json` without its find_rel entries (ptrs []): restore those.
- **Yes/No prompt overflow (issue #1 screenshots, fixed 2026-11-14, not in a release yet):** the 11
  '...?    はい  いいえ' prompts (Grand Change, Data Ball, evolve, Is this OK?, terms, save before battle) put
  Yes/No at their EN glyph index via the 2-space snap, past the cursor (drawn one cell left of the JP columns,
  0x0807A8EC: x = 0xA0 + sel*32) and off the window. `build.yes_no` re-pads the last line with GAP glyphs and
  single spaces so Yes/No start at the JP pixel columns (+0..2 px); test `test_yes_no_prompts_at_jp_columns`;
  "Branch-evolve to this Granbo?" shortened to clear the cursor. Verified: GAP/pen math on the rename prompt
  (`--qa` override; that window clips at ~17 cells). Not seen on the real Grand Change screen: still no warp
  (PROG=4 gives the rename keyboard; poking game +8 to 3/4 does nothing). Needs a v1.0.2 release (user's call).
- **Next (after user playtesting):**
  - Unverified screens (no warp scene): the second status page (0x0808AF70, icons moved to x=160), storage /
    Data Ball / shop prompts added by find_rel (ID_PX limits in ptrbatches are their current widths), link-battle
    screens (Record W/L composite with 1-cell W/L, FLAGGED), intro subtitles (s27196A.., new-game opening).
  - Reviewer notes left open: shop prompts keep a double space before {8E03} (menu placement, check on screen);
    some move short descriptions keep JP column spaces; "Team X" for 全X moves that hit all foes (glossary rule);
    `{940E}`/`{940F}` name codes unknown (Bermuda lines ev240336_019, ev2407DE_003, ev2082EE_022).
  - FLAGGED: tournament list titles "X Cup" vs dialogue "X Saver Tournament"; battle label ヘンシン = "Morph".
- **Choices made without the user (pre-approved autonomy, D6) that they may want to revisit:** skills list drops
  the per-row EN cost (shown in the description box); element kanji became pictograms; name-entry pages are
  ABC / 123 / A-Z; the title logo is new "GRANBO" lettering over a reconstructed egg.
- **Waiting on the user:** nothing.

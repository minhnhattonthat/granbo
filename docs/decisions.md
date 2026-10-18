# Decisions

The user's rulings on scope, style and trade-offs, newest last. Read before asking the user anything; if a later
decision replaces one, mark the old one "replaced by D<n>" instead of deleting it. Binding term spellings live in
`glossary.md`; this file holds the why.

| # | Date | Question | Options offered | Decision and reason |
|---|---|---|---|---|
| D1 | 2026-10-18 | Honorifics and name order | keep (-kun), drop; JP or Western order | Drop honorifics, Western order: kids' game, natural English. |
| D2 | 2026-10-18 | Romanization source for names | official Capcom romaji, Hepburn | Official where known (e.g. GRANBO logo), else adapted freely for punch. |
| D3 | 2026-10-18 | Credits | stay Japanese, translate | Translate. |
| D4 | 2026-10-18 | Abbreviations | engine work first (default), abbreviate | Default (not asked separately): full names, engine work first. |
| D5 | 2026-10-18 | Graphics text left in Japanese | translate all, credits stay JP, text only | Translate all tile-drawn Japanese. |
| D6 | 2026-10-18 | Specs and plans | need approval, pre-approved | Pre-approved: run phases autonomously, report at end; never publish without user. |
| D7 | 2026-10-18 | English title logo redesign | User-specified direction | Keep GRANBO (D2); use bold, chunky lettering with outline, shadow and dimension in the original style/palette. Keep the 240x160 image, tile budget and shared palette; generate reproducibly in `tools/gen_title.py`, leave NEW GAME alone. |
| D8 | 2026-10-18 | Dialogue text alignment | first line right after the speaker name (was), all lines at one left edge like the JP | Follow the original: every line of a speaker's text starts at x=64 (「 after the name tabs there, `asm/vwf.s`; `fit.SPEAKER_X`). |

# Reviewer brief - Granbo (GBA, Capcom 2001)

You review part of the English draft of Granbo's dialogue for a fan patch. The draft is complete; your job is to find
and fix real problems, not to restyle lines that already work. Work only on the batch named in your dispatch. Do all
the work yourself; do not dispatch subagents. Do not edit any file except your two output files.

## Read first
1. `docs/style-reference.md` - character voices and approved example pairs.
2. `glossary.md` - binding names and terms, and "Decisions from earlier batches". `work/tl/<batch>.terms.txt` lists
   the glossary rows that occur in your batch.
3. `docs/synopsis.md` - who is who. `docs/translator-brief.md` - the rules the translators followed (codes, pages).

## Input: `work/tl/<batch>.tsv`
`id<TAB>speaker<TAB>form<TAB>limit<TAB>Japanese<TAB>current English`, in game order (use neighbours for context).
` || ` separates pages (boxes); ` / ` marks a Japanese line break (the build wraps English itself).

## Fix (in this order of importance)
1. Mistranslation: the English says something the Japanese does not, or misses what it says (who does what, a
   negation, a number, an item or place). Lines shortened under an old width check may have dropped meaning:
   restore it (width is checked by the tool below; a page may wrap into two in game, that is fine).
2. Names and terms that differ from `glossary.md` (spelling, capitalisation such as "Message Board", "Granbo Saver",
   move tiers 1/2/3), and a recurring term your batch spells two ways.
3. Voice: Old Gen gruff and folksy; Shizuku polite; Akari bossy; Daigoro easygoing ("...y'know!"); Bermuda coldly
   polite; grunts "Aye aye, sir!". Grazie (グラッチェ, slot {9405}): the glossary marks his identity OPEN - he says
   ミー/ユー flamboyantly ("moi"), yet some lines labelled Grazie read as a serious scientist father. Read every Grazie
   line in your batch with its neighbours and make the voice fit what the Japanese shows; say what you found in
   your notes. Batakichi/Hopper's cry ばた is "Hop!" (not "Bata").
4. English errors: grammar, typos, unnatural phrasing a young player would trip on, leftover Japanese-isms,
   translator notes, doubled spaces, stray leading spaces.
Leave alone: lines that are accurate and natural, even if you would phrase them differently.

## Rules for any line you change (same as the translators')
- Same page count (` || `), every control code `{XXXX}` kept exactly, plain ASCII, no tabs inside the English.
- Honorifics dropped, Western order, `...` for ・・・, at most `!!`. No abbreviations to save space.
- `{9400}` and other name codes print a name: no suffix glued on, no "a/an" right before one.

## Output (write with your file-write tool, not a shell heredoc)
1. `work/tl/<batch>.out.tsv`: `id<TAB>English` for **every** input id, same order. Copy unchanged English exactly.
2. `work/tl/<batch>.notes.txt`: one line per changed id: `id: what was wrong -> what you did` (short).
Then run `python -X utf8 tools/batches.py check <batch>` from the repo root and fix every reported id until it
prints OK.

## Report (reply with only this)
Entries reviewed, number changed; then any `TERM: jp -> en (seen as X and Y)` inconsistencies you could not settle,
`UNSURE: id - note` for lines you could not judge, and your finding on Grazie in one or two lines.

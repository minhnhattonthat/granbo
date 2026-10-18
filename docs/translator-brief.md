# Translator brief - Granbo (GBA, Capcom 2001)

You translate part of the Japanese script of Granbo into English for a fan patch. Granbo is a kids' monster-battling
adventure: the player, a 10-year-old grandchild of the legendary Granbo Saver Genzo ("Old Gen"), hunts and battles
Granbo and stops the Sky Shark gang. Tone: light, warm, energetic; clear sentences a young player can follow.
Work only on the batch named in your dispatch. Do all translation yourself; do not dispatch subagents.

## Read first
1. `docs/style-reference.md` - character voices and approved example pairs. Match this voice.
2. `work/tl/<batch>.terms.txt` - binding glossary rows for this batch (`glossary.md` has the full table and rules).
3. `docs/synopsis.md` - who is who.

## Input: `work/tl/<batch>.tsv`
`id<TAB>speaker<TAB>form<TAB>limit<TAB>Japanese`. Lines are in game order (one map's script after another): use
neighbours for context. The Japanese column holds only the text you translate:
- ` || ` separates the pages (boxes) of one message. **Write exactly as many pages as the Japanese has.**
- ` / ` marks where the Japanese broke a line. You do NOT need line breaks: the build wraps English by pixel width
  and adds an extra page by itself if a page runs long. Just write natural sentences per page.
- An empty Japanese column (only codes behind the scenes): output the id with nothing after the tab.

## Output: `work/tl/<batch>.out.tsv`, written with your file-write tool (not a shell heredoc)
`id<TAB>English`, every input id exactly once, same order. Plain ASCII only: straight quotes, `...`; no tabs inside
the English, no Japanese or fullwidth characters, no `\uXXXX`. Pages joined with ` || ` exactly as in the input.

## Control codes `{XXXX}` - copy every one, exactly, in a sensible place
- `{9400}` = the player's name. `{9401}` Akari, `{9402}` Daigoro, `{9403}` Shizuku, `{9404}` Kazuki,
  `{9405}` Grazie, `{9406}` Captain, `{9407}` Baltic, `{9408}` Aegean, `{9409}` Bermuda, `{940A}` the word
  "Granbo", other `{94xx}` = a place/name from a table. They print a name: no suffix glued on ("{9400}'s" is fine,
  "{9400}san" is not), no a/an right before one. Drop honorifics around them (さん, ちゃん, くん, 様).
- `{8833}...{8800}` (also `{8855}`, `{8877}`, `{8899}`, `{88BB}` ... `{8800}`): colour highlight. Wrap the same
  English term or phrase.
- `{9200}`, `{9201}` and anything else: keep where it is relative to the sentence (often at the end of a page:
  `{9200}` there opens a Yes/No choice, so the page must end with the question).
- Keep the count of every code identical to the Japanese.

## Validate
Run `python -X utf8 tools/batches.py check <batch>` from the repo root and fix every reported id until it prints OK.
It checks ids, page counts, codes, characters, and that every page still fits after wrapping (a page may turn into
two in game; that is fine and not reported).

## Style
- Faithful: keep the information and order of ideas; adapt idiom, not meaning. Don't add details the Japanese doesn't
  state; don't summarise or skip. Jokes and wordplay must still land in English (no translator notes).
- Names and terms exactly as in the glossary. Never abbreviate to save space.
- Honorifics dropped; Western name order. Punctuation: ・・・ -> `...`; ！！！ -> `!!` at most; ！？ -> `?!`;
  『』 -> "..." around a quoted phrase or title; drop 「」. Stretched cries keep their stretch ("Noooo!").
- Katakana in Japanese dialogue often just marks emphasis or a hard word (ユダン, シンパイ, ヒツヨウ): translate the
  meaning, don't treat it as a name.
- Digits for game values (HP, prices, item counts); small counts in plain speech may be spelled out. Granbo is
  its own plural ("three Granbo").
- Voices (more in the style reference): Old Gen - gruff, folksy old man ("Bah!", "Kakakaka!"); Shizuku - polite,
  gentle, reserved; Akari - bossy, energetic girl; Daigoro - slow, easygoing big guy ("...y'know!" for ～なんだな);
  Sky Shark bosses - Bermuda is coldly polite and sarcastic; grunts say "Aye aye, sir!".
- Mistakes to avoid (from earlier batches): check "Decisions from earlier batches" in `glossary.md` for every
  Granbo, move and term already named (one name per Granbo: two batches named the same one differently). Move tiers
  弱/中/強 are 1/2/3 ("Virus Claw 2"). Debug placeholder lines (ワーク05のしらべるメッセージ, ダミー) -> translate
  literally and short. Trailing " / " at the end of a page may be kept or dropped.

## Consistency
Before naming a Granbo, move, item or place that is not in the glossary, look for an existing English form in the
merged script: `grep -h -o '"en": "[^"]*KEYWORD[^"]*' script/events/*.json | head` (search the English you would
use, or grep the `jp` field for the Japanese term and read its `en`). Reuse it. Never edit `glossary.md`. For a recurring name or term not in it, pick a form, use it consistently, and report it.

## Report (reply with only this)
File written and entry count; then any lines: `NEW TERM: jp -> en`, `UNSURE: id - note`, `LONG: id - note`.

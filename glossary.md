# Glossary - Granbo (GBA, Capcom 2001)

Binding for every translator and reviewer. Agents propose additions in reports; only the controller edits this file.
Options and reasons for each ruling: `docs/decisions.md`.

## Rulings (asked of the user 2026-10-18)
- Honorifics: dropped (D1). "{9400}さん" -> just the name; "ちゃん"/"くん" -> name alone (or a nickname if the
  speaker is being cute). Name order: Western.
- Romanisation source: official Capcom romaji where known (title logo GRANBO); otherwise adapted names chosen
  for English readers (puns kept), listed below (D2).
- Credits: translated (D3). Graphics text: all translated (D5).
- Register / flavour: a kids' monster-battling adventure. Light, energetic, clear sentences; keep each
  character's voice (see Characters notes). No crude slang, no modern memes.
- Abbreviations: never to fit a line; the build wraps text and adds pages (D4). Flag `LONG:` instead.
- Sound effects: *Bam!*, *Rumble...* in asterisks only when the JP is an onomatopoeia line on its own.

## Style rules
- Punctuation: 「」 dropped in dialogue (the speaker's name tag is shown); 『』 -> quotes "..." for titles/terms;
  ・・・ / ・・ -> `...`; ！ -> `!`, ！！！ -> `!!` at most; ！？ -> `?!`; ～ -> `~` only for a sing-song tone; ー
  (long vowel in a cry) -> repeat the letter ("Waaah!").
- Numbers stay digits. Money and counts keep the variable codes exactly where the sentence needs them.
- Coloured spans `{8833}...{8800}` (and other `{88xx}`): wrap the same term in English.
- Name variables `{94xx}`: keep each exactly once where the JP has it; no suffix glued to it; no a/an before it.

## Characters (name slots: speaker code {94xx} with xx >= 0x96 = slot xx-0x96; {94xx} with xx < 0x1E = slot xx)
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| (slot 0) | player name | 7 glyphs | set at name entry; {9400} / {9496} | |
| アカリ | Akari | 7 | slot 1 | |
| ダイゴロウ | Daigoro | 7 | slot 2 | |
| シズク | Shizuku | 7 | slot 3 | |
| カズキ | Kazuki | 7 | slot 4 | |
| グラッチェ | Grazie | 7 | slot 5; pun on Italian "grazie" | Gracche |
| キャプテン | Captain | 7 | slot 6 | |
| バルト | Baltic | 7 | slot 7; Sky Shark boss, named after a sea | Balt |
| エーゲ | Aegean | 7 | slot 8; Sky Shark, sea name | Aege |
| バミューダ | Bermuda | 7 | slot 9 / 16; Sky Shark, sea name | |
| グランボ | Granbo | 7 | the monsters; plural "Granbo" | Granbos |
| 本部長 | Chief | 7 | HQ chief | |
| かんごふ | Nurse | 7 | | |
| ハルナ | Haruna | 7 | | |
| 子分 | Grunt | 7 | Sky Shark henchman; 子分3 -> Grunt 3 | Underling |
| ゲンじい | Old Gen | 7 | slot 17 | |
| グラッチョ | Grazio | 7 | slot 18; pairs with Grazie | |

## Inline speaker labels ({94C8}NAME「 - the merge fills these in; max 46 px)
女の子 Girl / 男の子 Boy / おじさん Man / 少年セイバー Kid Saver / おじいさん Old Man / おばあさん Old Lady /
おばさん Lady / 元セイバー Ex-Saver / 少女セイバー Gal Saver / しかいしゃ Emcee / 大人セイバー Saver / オーナー Owner /
店長 Manager / かいさついん Gatekeep / かかりいん Staff / ならず者 Thug / じいさん Gramps / お姉さん Miss /
ヒゲじい Beardy / ばあさん町長 Mayor / こども Kid / システム System / 町長 Mayor / おかみ Landlady / 老人 Elder /
おっちゃん Mister / ダイゴロウ父 Dad / てんいん Clerk / とりまき男 Groupie / とりまき女 Groupie / 客の男 Guest /
コック Cook / おばちゃん Auntie / 子ども Kid / けいびいん Guard / 店長の子ども Kid / ？？？？？？ ??? / ダイゴロウ母 Mom /
元ならず者 Ex-Thug / ギャル Gal / 大人 Adult / ばあさん村長 Chief / うけつけ Desk / おじちゃん Uncle / セイバー Saver /
とりまき達 Groupies / 男の声 Voice / チロ Chiro / パイロット Pilot / 男の人 Man / へんそう子分 Grunt / 子分店長 Grunt /
お兄さん Lad / 女の声 Voice / グランボ Granbo / 大人の声 Voice

## Places
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| ウッディーナ | Woodina | | continent | |
| ウォーティア | Wateria | | continent | |
| ボルカニア | Volcania | | continent | |
| フォレスティア | Forestia | | continent | |
| フレイマー | Flamer | | continent | |
| マッドアクア | Mud Aqua | | continent | |
| ブロッサムタウン | Blossom Town | | | |
| アプリコットタウン | Apricot Town | | | |
| マスカットタウン | Muscat Town | | | |
| ピーチタウン | Peach Town | | | |
| キウイタウン | Kiwi Town | | | |
| ココナッツタウン | Coconut Town | | | |
| ブルーベリータウン | Blueberry Town | | | |
| ローズタウン | Rose Town | | | |
| カトレアタウン | Cattleya Town | | | |
| ハントグローブ研究所 | Huntgrove Lab | | | |
| ドウクツ研究所 | Cave Lab | | | |
| スカイポート | Skyport | | | |
| バトルスタジアム | Battle Stadium | | | |
| ドリームマウンテン | Dream Mountain | | | |
| ホテル・グランドボルカニア | Hotel Grand Volcania | | | |
| グランドチェンジタワー | Grand Change Tower | | | |
| ワールドチェンジタワー | World Change Tower | | | |
| 闇ダンジョン / 火ダンジョン / 水ダンジョン | Dark / Fire / Water Dungeon | | | |
| ヒミツダンジョン | Secret Dungeon | | | |
| セイバーステーション | Saver Station | | | |

## Items / skills / terms
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| グランボセイバー / セイバー | Granbo Saver / Saver | | a Granbo tamer | Sabre |
| スカイシャーク | Sky Shark | | villain gang | |
| グランドチェンジ | Grand Change | | | |
| ワールドチェンジ | World Change | | | |
| ヘンシン | transform | | | |
| データボール | Data Ball | | | |
| ウイルス / エラー / ストップ | Virus / Error / Stop | | status effects | |
| EN | EN | | energy | |
| ワザ | move | | a Granbo's attack/skill | technique |
| アイテム | item | | | |
| ゲージ | gauge | | | |
| ヒヨッコ / カケダシ / シロウト / クロウト / ミツボシ / ベテラン / マスター / スーパー / ウルトラ / キング / ゴッド セイバー | Chick / Rookie / Amateur / Pro / Three-Star / Veteran / Master / Super / Ultra / King / God Saver | | Saver ranks | |
| グランボバトル | Granbo battle | | | |

## Decisions from earlier batches

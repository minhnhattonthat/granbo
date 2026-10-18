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

## Granbo species (from the game's data records; binding - romanised, lightly adapted)
ピヨリカ Piyorika / ヨーダッチ Yodatch / ローバッファ Robuffa / ラ・ゴーリ La Gori / ファントレー Fantray /
クスーフェ Kusufe / タマジャン Tamajan / チョトッツ Chototz / ガッチン Gatchin / ゴーダー Goder / ゴウアン Gouan /
ジキーガ Jikiga / グレスブトム Gresbutom / メッサー Messer / ホットブログ Hotbrog / ウォームー Warmoo /
ウキウッキ Ookook / オーム Polly (parrot pun on オウム) / タヌボン Tanubon / レディー Lady / イグール Igul / フォング Fong / ガルキック Garkick /
ガーダバーゲ Gardabage / ペンペン Penpen / ハリボン Haribon / フォックル Foxle / マキリーター Makiriter / ヴァイア Vaia /
ラ・グーゲン La Gugen / ホッパー Hopper / ワルッサ Warussa / ブロウド Broud / ウドメッカ Udomecha / ガーサス Garsus /
ダイル Dyle / バージス Burgis / ウパロン Uparon / ワルオン Waruon / ワルックル Warukkle / モゴモグ Mogomog / ガルオー Garoh /
ピカリ Pikari / マッグ・ゴウ Mag Gou / メガッチン Megatchin / メガニワン Meganiwan / ラフィ Raffy / ドランパ Drampa /
デメッキ Demekki / カラクロー Karaclaw / ラ・ハイド La Hide / ワルボン Warubon / メザバーン Mezabarn / ムーガイオ Mugaio /
ガデム Gadem / マナズー Manazoo / ラック Rack / クラゲルン Kurageln / ガザリ Gazari / シランガー Shiranger /
ル・ベルケス Le Berkes / レシオス Resios / アビラ Abila / ギロザウラン Girozauran / ムームー Mumu / メガ Mega /
コロコラン Korokoran / ガニガブ Ganigab / ククージャ Kukuja / ラトプ Ratop / トカトビーゲ Tokatobige / チッピー Chippy /
ミーゼン Meesen / ラミーゴ Ramigo / テゴザ Tegoza / ダパンパ Dapampa / イウッチ Iutch / ヒョーグ Hyog / ミーゼット Meesette /
ザイドン Zaidon / カモダック Kamoduck / バイエン Baien / テラドン Teradon / ガメーダ Gameda.
Pet nicknames are not species: バタキチ -> Batakichi (not "Hopper", which is a species).

## Decisions from earlier batches
- Move tiers 弱/中/強 -> 1/2/3 after the name: ウイルスボム中 -> Virus Bomb 2, ATアップ中 -> AT Up 2, ほえる強 -> Roar 3
  (b001/b003 used M/Mid; fixed before merge).
- Granbo names: バタキチ/バタきち -> Batakichi (a pet's name; its species is Hopper; its cry ばた -> "Hop!", tic
  ", hop!"), バブルス -> Bubbles (monkey, ウキ -> "ook!"),
  ブトム -> Butom, ピヨリカ -> Piyorika, ヤブッサ -> Yabussa, フォックル -> Foxle, バズメッカ -> Buzzmecha,
  ワオン -> Woofon.
- Terms: ゾクセイ -> element; ハント -> hunt; しんか -> evolve/evolution; ランクポイント -> Rank Points;
  セイバーランク -> Saver Rank; スカイシップ -> Skyship (not Sky Ship); データパッド -> Data Pad; メカエッグ -> Mecha Egg;
  ハントグローブ -> Hunt Glove; ドリームフラワー -> Dream Flower; リサイクルボックス -> Recycle Box; コンテナ -> Container;
  アイテムロッカー -> Item Locker; ノラグランボ -> stray Granbo; セイバー本部 -> Saver HQ; グランボショップ -> Granbo Shop;
  データボールシステム -> Data Ball System; チョトッツ -> Headlong Rush; ウイルスミサイル -> Virus Missile;
  じゅうじボタン -> +Control Pad; 買う/売る/やめる -> Buy / Sell / Quit.
- People: キャプテン・カリブ -> Captain Caribbean (Sky Shark top boss, sea name; the {9406} "Captain" slot);
  カリブさま -> Lord Caribbean; メッセージボード -> Message Board; システムコマンド -> System commands;
  ワザをがくしゅうします -> Learn Move; HP回復小/中/大 -> HP Heal 1/2/3; ガン弱/中/強 -> Gun 1/2/3;
  HPカプセル -> HP Capsule; ハントフード -> Hunt Food; メカやさい -> Mecha Veggies; ポチマル -> Pochimaru (pet); {9409}さま from grunts -> Boss {9409};
  かんぶ -> boss; ゲンゾウさん from polite speakers -> Mr. Genzo (allowed: natural English politeness, not an
  honorific suffix); Beardy's ばみうだ -> "Bermooda".
- Elements 火/水/木/光/闇 -> Fire / Water / Wood / Light / Dark (capitalised). Battle commands コウゲキ / ワザ /
  アイテム / ヘンシン / ボウギョ / ニゲル -> Attack / Move / Item / Transform / Defend / Run (to match the menus once
  translated). ハントゲージ -> Hunt Gauge; ハントワザ -> Hunt Move; データボールこうかんマシン -> Data Ball Exchange
  Machine; 作戦カイギ -> strategy meeting. Granbo: モクモン -> Mokumon, チューバット -> Chubat.
- DFアップ弱 -> DF Up 1; 本きょ地 -> headquarters; イモムシがたのデータボール -> caterpillar-type Data Ball; the
  Captain's コゾウ / ボウズ -> squirt / kid; rabbit Granbo cry ウサ -> "bun!".
- バタッチ -> Batatch (pet nickname, cry "hop!"); フリーズガン -> Freeze Gun; ALLソング中 -> ALL Song 2 (ALL moves keep
  "ALL" in caps); アネゴ -> Big Sis; 南のハシ -> south bridge.
- バトルメカエッグ -> Battle Mecha Egg; ヒクウテイ -> airship (not Skyship); ウイルスカプセル -> Virus Capsule;
  グランドチェンジ研究家 -> Grand Change researcher; タワーの元カンリ人 -> former caretaker of the tower.
- そこぢから -> Reserve Power; スモーク -> Smoke; ガゲット -> Gaget; 水オタマジャクシ -> Water Tadpole;
  ヨビのデータボール -> spare Data Ball; うけつけ -> front desk; {9407}さま -> Boss {9407}.
- プレイヤーデータ -> Player Data; ジョウタイイジョウ -> status effect; パラメータ -> stats; 物知りじいさん -> wise old man;
  君のような少年 -> "a youngster like you" (keep the player's gender neutral unless the JP line hinges on it).
- Numbers: digits for game values (HP, prices, counts of items); small counts in plain speech may be spelled out
  ("the two machines").
- Grazie (グラッチェ) says ミー/ユー: flamboyant faux-foreign speech -> "moi" for ミー, "you" stays; light flourish
  ("Magnifico!"), never mocking.

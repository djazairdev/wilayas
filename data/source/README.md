# Transcriptions

One file per official text, as printed in the Journal officiel, in both editions, and one for the commune codes of ONS, the statistics office. The texts are listed in [`../texts.csv`](../texts.csv) and ONS's lists in [`../ons.csv`](../ons.csv), with links to their PDFs and the checksums of the files we read. The API is built from these transcriptions; they are never edited to "fix" a spelling ([why](#spellings)).

| File | Text | Rows |
|---|---|---|
| `decree-84-79.csv` | Decree 84-79 of 3 April 1984: the names and chefs-lieux of wilayas 01 to 48 ([below](#decree-84-79)) | 48 |
| `executive-decree-91-306.csv` | Executive Decree 91-306 of 24 August 1991: the daïras of the 48 wilayas, each with its seat and the communes its chef de daïra runs | 2096 |
| `executive-decree-92-66.csv` | Executive Decree 92-66 of 12 February 1992: the daïras it adds to or redraws in Decree 91-306's tables for seven wilayas ([below](#decrees-92-66-18-302-and-25-87)) | 63 |
| `ordinance-97-14.csv` | Ordinance 97-14 of 31 May 1997: the communes it detaches from Boumerdès, Tipaza and Blida and attaches to Algiers (articles 2 to 5) ([below](#ordinance-97-14)) | 24 |
| `executive-decree-18-302.csv` | Executive Decree 18-302 of 4 December 2018: the daïras it adds to or redraws for Constantine, Oran and Illizi | 27 |
| `law-19-12.csv` | Law 19-12 of 11 December 2019: the lists it rewrites (articles 5 to 51) and the ten wilayas it creates (52 bis to 52 bis 9) | 162 |
| `presidential-decree-21-117.csv` | Presidential Decree 21-117 of 22 March 2021: the names and chefs-lieux of wilayas 49 to 58 | 10 |
| `ordinance-21-03.csv` | Ordinance 21-03 of 25 March 2021: the lists of Ouargla and Touggourt, which it rewrites (articles 34 and 52 bis 6) | 21 |
| `executive-decree-25-87.csv` | Executive Decree 25-87 of 24 February 2025: the daïras it adds to or redraws for Tlemcen | 7 |
| `law-26-06.csv` | Law 26-06 of 4 April 2026: the lists it rewrites (articles 7 to 36) and the eleven wilayas it creates (52 bis 10 to 52 bis 20) | 404 |
| `presidential-decree-26-206.csv` | Presidential Decree 26-206 of 25 May 2026: the names and chefs-lieux of wilayas 59 to 69 | 11 |
| `executive-decree-21-198.csv` | Executive Decree 21-198 of 11 May 2021: the daïras of the 18 wilayas Law 19-12 changed or created, whose tables it rewrites or adds in Decree 91-306's annex ([below](#decree-21-198)) | 240 |
| `executive-decree-26-253.csv` | Executive Decree 26-253 of 15 July 2026: the daïras of the 21 wilayas Law 26-06 changed or created, whose tables it rewrites or adds in Decree 91-306's annex | 546 |
| `ons-2021.csv` | ONS's code géographique national of June 2021: the code of each of the 1,541 communes of the 58 wilayas, with its names ([below](#onss-code-géographique)) | 1541 |
| `readings.csv` | Names read on the rendered page ([below](#how-each-name-was-checked)) | |

## Columns

The files of the laws and of the ordinance have one row per commune per list:

| Column | Meaning |
|---|---|
| `text` | The text's id in `texts.csv` |
| `article` | The article of Law 84-09 that holds the list, as the amending law writes it: `7`, `52 bis`, `52 bis 10` |
| `via` | The article of the amending text that rewrites or adds it: `2` rewrites existing articles, `3` adds new ones |
| `item` | The commune's number in the list |
| `of` | The number of communes the article announces |
| `name_fr`, `name_ar` | The name as printed in the French and Arabic editions |
| `check` | How the name was checked ([below](#how-each-name-was-checked)) |

The file of Ordinance 97-14 has the same columns but `via` and `of`: `article` is the article of the ordinance that names the commune (2, 3 or 4), and `item` its place in the article.

The files of Decrees 84-79, 21-117 and 26-206 have one row per wilaya: `item` is the wilaya's number, `name_fr` and `name_ar` its name, and `seat_fr` and `seat_ar` its chef-lieu.

The files of the daïra decrees (91-306, 92-66, 18-302, 21-198, 25-87 and 26-253) have one row per daïra seat and one per commune, in the order of the annex:

| Column | Meaning |
|---|---|
| `wilaya` | The wilaya's number, as its heading prints it: `01` to `48` in Decree 91-306; in the later decrees, the wilayas whose tables they amend, rewrite or add |
| `daira` | The daïra's place in its wilaya's table as the decree prints it, from 1 |
| `item` | `seat` for the seat of the daïra, which comes first; then the commune's place in the daïra's list, from 1; or `unchanged` ([below](#decrees-92-66-18-302-and-25-87)) |
| `name_fr`, `name_ar`, `check` | As above. A name an edition doesn't print is empty ([below](#decree-91-306)) |

A list's number is not a commune code. The codes are ONS's, and `ons-2021.csv` has one row per commune, in the order of the list:

| Column | Meaning |
|---|---|
| `wilaya` | The wilaya's number, the first two digits of the code |
| `commune` | The commune's number in its wilaya, the last two |
| `name_fr`, `name_ar`, `check` | As above |

A wilaya keeps its communes' codes, gaps included, when a law takes some of them away; the communes it gives to a new wilaya are numbered again from 01 there.

## How each name was checked

The laws, Ordinance 21-03 and Decrees 18-302, 21-117, 21-198, 25-87, 26-206 and 26-253 have a text layer. The French comes from the text of the PDF, which is exact. The Arabic is read twice, by OCR of the rendered page and from the PDF's own text, which is drawn correctly but stored out of order. `check` says what happened:

- **Empty:** the two readings have the same letters. In the daïra tables of Decrees 18-302, 21-198, 25-87 and 26-253, and in ONS's list, they must also put the spaces in the same places: there the text layer sometimes puts a space inside a word, and the OCR one after a letter that doesn't join the next.
- **`eye`:** they don't, or one of them missed the name. The name was read on the rendered page, and `readings.csv` records the reading, the page, who read it, who checked it and why.

Claude, the AI model that ran the transcription, made every reading (`by` is `claude`). Before version 1, the project's founder checks each one against the printed page: `reviewed_by` is then `founder`, and a reading the founder corrects becomes the founder's (`by` is `founder`), its note saying what Claude had read. The founder has checked the first 1,738 readings against the printed page: the 61 of the laws, Ordinance 21-03 and Decrees 21-117 and 26-206, the 1,410 of Decree 91-306, the 43 of Decree 92-66, the 20 of Ordinance 97-14, the 18 of Decree 21-198, the 25 of Decree 26-253 and the 161 of ONS's list. The founder confirmed all of them but two of Decree 91-306, which the founder corrected; those two are the founder's own readings (`by` is `founder`), so `reviewed_by` is empty. The 41 readings of Decree 84-79 wait for the founder's check.

The tests refuse any other value, and check that each `eye` row matches its reading.

### Decree 84-79

Law 84-09 of 4 February 1984 created the 48 wilayas, and Decree 84-79 of 3 April 1984 fixes their names and chefs-lieux (article 1), in the order of their numbers: "01 — wilaya d'Adrar avec chef-lieu à Adrar". Each wilaya is named after its chef-lieu. Decrees 21-117 and 26-206 complete the list for wilayas 49 to 69.

Both editions of JO n° 14 of 1984 are scans, read as Ordinance 97-14 is: each page by OCR whole, and the list again at 400 dpi. The entries come in order, so an entry's place gives its number. A name is taken from the OCR when both readings agree and it is the label of a commune in Wikidata; the other entries were read on the rendered page, 25 French and 16 Arabic. In `readings.csv`, `item` is the wilaya's number and `name` the whole entry, "Adrar / Adrar": the wilaya's name, then its chef-lieu's. The Arabic is transcribed without harakat.

ONS numbers each wilaya's chef-lieu 01, but for Algiers: the decree's chef-lieu is "Alger", and ONS's 16-01 is the commune of Alger Centre.

### Decree 91-306

Both editions of JO n° 41 of 1991 are scans, with no text to read. Each page was read by OCR four ways: whole, by half-page column and by row of the tables at 300 dpi, and by row again at 400 dpi. A name was taken from the OCR when every reading agrees and is the label of a commune in Wikidata (CC0), an independent second reading. Wikidata's aliases don't count, and nothing from Wikidata goes into the data. Every other name was read on the rendered page: 647 French names and 763 Arabic ones. A row's `check` is `eye` when either of its names was read on the page.

In `readings.csv`, `article` is the wilaya and `item` the daïra and the item, as in `5/seat` or `5/2`. The first clause of each note says why the name needed the page: the OCR's readings differ; or they agree, but not with the print ("the OCR read …"); or they agree with the print but match no Wikidata label. Other rows are cited the same way: `04 5/seat` is the seat of the fifth daïra of wilaya 04.

The readings follow these rules:

- A name is kept as printed, misprints included, and its words are spaced as printed: 48 2/3 prints "عبدالله" as one word.
- ى and ي are kept as printed, and so is ڤ, which 05 1/3, 39 2/3 and 42 7 (seat and commune) print for the sound g.
- Harakat, the short vowels and the shadda, aren't transcribed.
- A hamza is read from the shape of the alif on the scan. A hamza merged into the alif's head makes it narrow on top, then a bulge, usually 9 to 12 pixels wide, where a bare alif's head is no wider than its stem; a hamza below is a mark of its own under the foot. [`tools/gazette/alifs.py`](../../tools/gazette/alifs.py) measures every alif that stands on its own and lists the names the scan contradicts; each one it lists was looked at again.
- A broken letter is read from its traces, or from the same name printed elsewhere when they aren't enough, and the note says what shows. Specks and flaws are noted, not transcribed.
- Letters the print doesn't show at all are marked `[…]`. Only 15 17/3 had them: the print shows only the end of the name, which Claude read "بتين", and the founder completed it on review as "إليلتين" (the French edition prints Illilten).
- Sizes in the notes are pixels of the scan, about 305 dpi.

The two editions print the same tables in the same order, but for three lines that only the Arabic prints. Their French name is empty:

- 18 10/2 and 3: the Arabic prints Boudria Beniyadjis as two communes, بودريعة and بني ياجيس.
- 30 10/2: the French leaves out Rouissat (الرويسات).
- 34 3/4: the Arabic adds تكستين to Ras El Oued. It looks like Tixter (تيكستر), which both editions list under Aïn Taghrout (34 9/2).

So the French lists 1,540 communes and the Arabic 1,543 lines. With Rouissat, the decree covers 1,541 communes: one more than the 1,540 of Law 84-09 (art. 3).

### Ordinance 97-14

Ordinance 97-14 of 31 May 1997 defines the new territorial frame of the wilayas of Algiers, Boumerdès, Tipaza and Blida. It detaches six communes from Boumerdès (article 2), fourteen from Tipaza (article 3) and four from Blida (article 4), and article 5 attaches them to Algiers from 31 July 1997. Ordinance 97-15, in the same issue, made Algiers the Governorate of Greater Algiers; it was dissolved in 2000, and the 24 communes stayed in Algiers.

The names are in the text of the articles, not in lists. Both editions of JO n° 38 of 1997 are scans, read as Decree 91-306 is: each page by OCR whole, and the articles again at 400 dpi. A name is taken from the OCR when both readings agree and it is the label of a commune in Wikidata; the other 20 were read on the rendered page, 11 French and 9 Arabic. In every case the two readings agreed with each other and with the print; they are names Wikidata spells otherwise. The Arabic is transcribed without harakat, as Decree 91-306 is: the print puts a shadda on half of the names. In `readings.csv`, `article` is the article and `item` the commune's place in it.

Each commune is one of its old wilaya's in Decree 91-306, by its French or its Arabic name; Khraïcia (خرايسية) is Khraissia (الخرايصية) there.

### Decrees 92-66, 18-302 and 25-87

These three decrees amend Decree 91-306's annex wilaya by wilaya, and reprint only the daïras they add or redraw: each wilaya's table ends "Le reste sans changement" ("الباقي بدون تغيير"). Decree 92-66 redraws daïras in seven wilayas (02, 04, 08, 09, 15, 28 and 35), Decree 18-302 in Constantine, Oran and Illizi (25, 31 and 33), and Decree 25-87 in Tlemcen (13).

Decrees 18-302 and 25-87 also print a daïra's seat with "(sans changement)" in place of its communes, to place a new daïra among the old. Such a daïra is its `seat` row, then one row with the item `unchanged` and no names: the daïra keeps the communes it had, which the decree doesn't print. It is not a daïra without communes. Decree 25-87 also opens Tlemcen's table with a row that says only "(sans changement)", for the daïras before the ones it prints; it has no row here.

A printed daïra replaces the daïra with the same seat, or is added, and the communes it lists leave the wilaya's other daïras. No commune is created or moved between wilayas: the tests apply the decrees in order and check that each wilaya keeps its communes ([below](#the-daïras-in-2021)).

Decree 92-66 is in JO n° 13 of 1992, both editions scans, read as Decree 91-306 is. Its French seats are not in capitals. 43 names were read on the rendered page, 22 French and 21 Arabic: in 35 the OCR's readings agree with each other and with the print but match no Wikidata label, in 2 they agree but miss a hyphen, and in 6 they differ. It prints one commune of 04 as "El Fedjoudj, Boughrara, Saoudi" ("الفجوج، بوغرارة، سعودي"), with commas, which Decree 91-306 prints without; the seat "Bourdj Menaiel" heads the commune "Bordj Menaiel".

Decrees 18-302 (JO n° 72 of 2018) and 25-87 (JO n° 15 of 2025) have a text layer, and are read as Decree 21-198 is; their tables span the page's width. Every name's two readings agree.

### Decree 21-198

Decree 21-198 does for Law 19-12 what Decree 26-253 does for Law 26-06. It rewrites the tables of the eight wilayas Law 19-12 took communes from (01, 07, 08, 11, 30, 33, 39 and 47), adds those of the ten it created (49 to 58), and says the other tables are unchanged. Its 78 daïras share out the 162 communes of those wilayas, as Law 19-12 lists them and Ordinance 21-03 rewrites them for Ouargla and Touggourt, each commune once.

Both editions of JO n° 38 of 2021 have a text layer and are read as Decree 26-253's are, but the French prints each commune on its own line without a dash: there each line is a name. The 18 Arabic names read on the rendered page are four the OCR missed, one it misread, two where it put a space after a letter that doesn't join the next, and eleven where the text layer puts a space inside a word ("س يدي عون" for "سيدي عون"); in all of them the text layer's letters are the print's. Both editions name the seat of the daïra of Abalessa "Silet Abalessa" (سيلات أباليسا), after a place in the commune.

### Decree 26-253

Decree 26-253 amends Decree 91-306's annex. It rewrites the tables of the ten wilayas Law 26-06 took communes from (03, 05, 07, 12, 13, 14, 17, 26, 28 and 32), adds those of the eleven it created (59 to 69), and says the other tables are unchanged. Its 142 daïras share out the 404 communes Law 26-06 lists for those wilayas, each commune once.

The tables are laid out as in 1991: a row per daïra, with the seat in one column and its communes in the other, each after a dash. Both editions of JO n° 52 of 2026 have a text layer, and each name is placed in its row from the positions of its text, between the rules found on the rendered page. The French is the text of the PDF. In the Arabic, the text layer garbles the wilaya headings and runs a few lines together, so the Arabic is also read by OCR, of whole pages and of each row at 400 dpi, and the wilaya numbers come from the OCR. A name is kept from the text layer when an OCR reading has the same letters and the same spaces. The other 25 were read on the rendered page: names the text layer garbles or runs together, names the OCR missed, misread or cut short, and eight where the OCR puts a space after a letter that doesn't join the next ("أو لاد" for "أولاد"); in all eight, the text layer's spacing is the print's. In `readings.csv` they are cited as for Decree 91-306: `article` is the wilaya, and `item` the daïra and the item.

### The daïras in 2021

[`tools/resolve.py`](../../tools/resolve.py) rebuilds the daïra tables of June 2021 from the texts, and the tests run it: Decree 91-306, then Decree 92-66, Ordinance 97-14, Decree 18-302 and Decree 21-198. Then each wilaya's daïras share out the communes ONS's list gives it, each commune once. Ordinance 97-14 moves its 24 communes to Algiers without placing them in a daïra.

Seven daïras of Decree 91-306 are left without communes on the way. Decree 92-66 gives Chebli's to the new daïra of Bouinan, and Ordinance 97-14 moves to Algiers all the communes of Birtouta (Blida), Rouiba (Boumerdès), and Chéraga, Douéra, Draria and Zéralda (Tipaza). It also moves the seats of two daïras, Sidi Moussa (Blida) and Reghaïa (Boumerdès), but not their other communes: Ouled Selama stays in Blida, and Ouled Hadjadj and Boudouaou El Bahri in Boumerdès.

Decree 21-198 names seven communes otherwise than Decree 91-306, beyond spelling: "Tamast" for "Tamest", "Abalessa" for "Silet Abalessa", and "M’Rara" for "M’Ghagha", among others. M'Rara is M'Ghagha only by elimination: the one commune of El M'Ghaier (57) left unpaired, and the one of El Oued (39).

ONS names 98 communes otherwise than the latest decree that lists them. Most are spellings, as "Benaria" (Decree 91-306) for ONS's "BENAIRIA"; a few are new names, as Decree 91-306's "Hamma Annassers" for ONS's "MOHAMED BELOUIZDAD". `tools/resolve.py` lists all of them. Decree 25-87 and Decree 26-253 then apply as well: the 69 wilayas share out 1,541 communes, and the wilayas Decree 26-253 leaves alone keep those of 2021. Decree 26-253 names eight communes otherwise than any text before it, beyond spelling, as "Eddouair" for ONS's "TLATET EDDOUAIR" and "Abdelkader Azil" for "AZIL ABDELKADER"; each is the one commune of its wilaya left unpaired.

### ONS's code géographique

ONS's code géographique national of June 2021 applies the interministerial order of 12 September 2021, which amends the register of local authorities of 22 June 1985 for the 58 wilayas of Law 19-12. Each wilaya has a heading, then a row per commune: the French name in capitals, the wilaya's number, the commune's number and the Arabic name. It is the latest edition ONS has published: there are no codes yet for the communes Law 26-06 moved to wilayas 59 to 69.

The list has a text layer, but it stores the Arabic in pieces, some of them run together with the codes, so each row is rebuilt from the place of each character on the page ([`tools/ons/`](../../tools/ons/)). The French and the codes are the text of the PDF. The Arabic is read again by OCR, of whole pages and of each row at 400 dpi, and a name is kept from the text layer when an OCR reading has the same letters and the same spaces. The other 161 were read on the rendered page. About one name in ten is stored with its letters out of order, and some with spaces the print doesn't have, or without one it has; every one of the 161 uses exactly the letters the text layer stores, in another order or spaced differently.

The rows are ruled with dotted lines drawn over the letters, and the rule hides the dots of a final ي that dips onto it: the print looks like ى, and the OCR reads ى. Rendered at 700 dpi, the tops of the dots still show above the rule, and in every case where they can be seen, the text layer's ي or ى matches the print. So a final ي or ى is the text layer's.

In `readings.csv`, `article` is the wilaya and `item` the commune's number.

The number of communes in each wilaya matches the texts: ONS puts 57 communes in Algiers, Decree 91-306's 33 and the 24 of Ordinance 97-14. It numbers the 24 after Algiers' own, 34 to 57: Blida's four, then Boumerdès' six, then Tipaza's fourteen, each in the ordinance's order. So a wilaya that receives communes numbers them after its own, where a new wilaya numbers its communes from 01.

## Spellings

The texts don't always agree with each other. Law 26-06 prints the commune "آفلو" and Decree 26-206 prints the wilaya "أفلو"; Decree 26-253 prints both, "آفلو" for the seat of the daïra and "أفلو" for the commune. Law 19-12 prints "لواء", "Oumach" and "Khenguet Sidi Nadji" where Law 26-06 prints "ليوة", "Oumache" and "Khangat Sidi Nadji". Ordinance 21-03 prints "حاسي بن عبد الله", "Ain Beida" and "Blidate Ameur" where Law 19-12 prints "حاسي بن عبد اللّه", "Aïn Beïda" and "Blidat Ameur". Decree 21-117 names the chef-lieu of wilaya 57 "El M’Ghaier", and Law 19-12 lists the commune as "El Megaier". Within Decree 91-306, a daïra's seat is printed apart from its list of communes, and the seat's commune heads the list. Fourteen times the two differ by more than capitals, accents, hyphens, hamzas or the dots of a final ي or ة: the seat "BEDJIA" heads the commune "Béjaia", "GUENZET" heads "Gunzet", "MOSTEFA BEN BRAHIM" heads "Mostepha Ben Brahim", and "عين موسى" heads "عمي موسى". Two seats, "El HACHIMIA" and "OUED El ABTAL", print "El" in small letters. In Decree 26-253 a seat and its commune differ five times, only by an accent, a capital, the shape of an apostrophe, or the hamza or madda on an alif. Decree 26-253 spells 26 names differently from Law 26-06, 19 French and 7 Arabic. Most differ by an accent, an apostrophe or a capital, as the decree's "Aïn Yagout" for the law's "Ain Yagout", or by the dots of a final ي; four differ by more: the decree prints "Béni Yaagoub", "El Azizia", "Bougtoub" and "سيدي عبد الرحمن" where the law prints "Ben Yaagoub", "Al Azizia", "Bougtob" and "سيدي عبد الرحمان". The tests list all of them.

Decree 92-66 spells "Oultem" (ولتام) and "Touarga" (توارقة) where Decree 91-306 prints "Oultene" (ولتان) and "Taourga" (تورقة), and spells others differently by a letter in one edition, as "Mossedek" for "Moussedek".

Decree 21-198 spells 18 names differently from Law 19-12 or Ordinance 21-03, 10 French and 8 Arabic, among them "Tamast", "Temacine", "تاظروك" and "الطريفاوي" where the law prints "Tamest", "Tamacine", "تازروق" and "تريفاوي". The tests list all of them.

Decree 84-79 spells some names without the accents and hamzas later texts print, as "Bejaïa", "Tebessa" and "Boumerdes", or "الاغواط"; and its Arabic ends names with ى where later texts print ي, as "أم البواقى" and "تيزى وزو".

Each file keeps its own text's spelling. The API uses the spelling of the latest text that names the place, and gives the others as aliases.

The tools that made these files are in [`tools/gazette/`](../../tools/gazette/) and [`tools/ons/`](../../tools/ons/).

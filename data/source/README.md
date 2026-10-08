# Transcriptions

One file per official text, as printed in the Journal officiel, in both editions. The texts are listed in [`../texts.csv`](../texts.csv), with links to their PDFs and the checksums of the files we read. The API is built from these transcriptions; they are never edited to "fix" a spelling ([why](#spellings)).

| File | Text | Rows |
|---|---|---|
| `executive-decree-91-306.csv` | Executive Decree 91-306 of 24 August 1991: the daïras of the 48 wilayas, each with its seat and the communes its chef de daïra runs | 2096 |
| `law-19-12.csv` | Law 19-12 of 11 December 2019: the lists it rewrites (articles 5 to 51) and the ten wilayas it creates (52 bis to 52 bis 9) | 162 |
| `presidential-decree-21-117.csv` | Presidential Decree 21-117 of 22 March 2021: the names and chefs-lieux of wilayas 49 to 58 | 10 |
| `ordinance-21-03.csv` | Ordinance 21-03 of 25 March 2021: the lists of Ouargla and Touggourt, which it rewrites (articles 34 and 52 bis 6) | 21 |
| `law-26-06.csv` | Law 26-06 of 4 April 2026: the lists it rewrites (articles 7 to 36) and the eleven wilayas it creates (52 bis 10 to 52 bis 20) | 404 |
| `presidential-decree-26-206.csv` | Presidential Decree 26-206 of 25 May 2026: the names and chefs-lieux of wilayas 59 to 69 | 11 |
| `executive-decree-26-253.csv` | Executive Decree 26-253 of 15 July 2026: the daïras of the 21 wilayas Law 26-06 changed or created, whose tables it rewrites or adds in Decree 91-306's annex | 546 |
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

The files of Decrees 21-117 and 26-206 have one row per wilaya: `item` is the wilaya's number, `name_fr` and `name_ar` its name, and `seat_fr` and `seat_ar` its chef-lieu.

The files of Decrees 91-306 and 26-253 have one row per daïra seat and one per commune, in the order of the annex:

| Column | Meaning |
|---|---|
| `wilaya` | The wilaya's number, as its heading prints it: `01` to `48` in Decree 91-306; in Decree 26-253, the 21 wilayas whose tables it rewrites or adds |
| `daira` | The daïra's place in its wilaya's table, from 1 |
| `item` | `seat` for the seat of the daïra, which comes first; then the commune's place in the daïra's list, from 1 |
| `name_fr`, `name_ar`, `check` | As above. A name an edition doesn't print is empty ([below](#decree-91-306)) |

A list's number is not a commune code. The codes go back to the 1984 lists, and a wilaya keeps them, gaps included, when a later law rewrites its list.

## How each name was checked

The laws, the ordinance and Decrees 21-117, 26-206 and 26-253 have a text layer. The French comes from the text of the PDF, which is exact. The Arabic is read twice, by OCR of the rendered page and from the PDF's own text, which is drawn correctly but stored out of order. `check` says what happened:

- **Empty:** the two readings have the same letters.
- **`eye`:** they don't, or one of them missed the name. The name was read on the rendered page, and `readings.csv` records the reading, the page, who read it, who checked it and why.

Claude, the AI model that ran the transcription, made every reading (`by` is `claude`). Before version 1, the project's founder checks each one against the printed page: `reviewed_by` is then `founder`, and a reading the founder corrects becomes the founder's (`by` is `founder`), its note saying what Claude had read. The founder has checked the 61 readings of the laws, the ordinance and Decrees 21-117 and 26-206 and confirmed them all, and 83 of the 1,410 of Decree 91-306, confirming 81 and correcting two. The rest, and the 17 of Decree 26-253, are next.

The tests refuse any other value, and check that each `eye` row matches its reading.

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

### Decree 26-253

Decree 26-253 amends Decree 91-306's annex. It rewrites the tables of the ten wilayas Law 26-06 took communes from (03, 05, 07, 12, 13, 14, 17, 26, 28 and 32), adds those of the eleven it created (59 to 69), and says the other tables are unchanged. Its 142 daïras share out the 404 communes Law 26-06 lists for those wilayas, each commune once.

The tables are laid out as in 1991: a row per daïra, with the seat in one column and its communes in the other, each after a dash. Both editions of JO n° 52 of 2026 have a text layer, and each name is placed in its row from the positions of its text, between the rules found on the rendered page. The French is the text of the PDF. In the Arabic, the text layer garbles the wilaya headings and runs a few lines together, so the Arabic is also read by OCR, of whole pages and of each row at 400 dpi, and the wilaya numbers come from the OCR. A name is kept from the text layer when an OCR reading has the same letters. The other 17 were read on the rendered page: names the text layer garbles or runs together, and names the OCR missed, misread or cut short. In `readings.csv` they are cited as for Decree 91-306: `article` is the wilaya, and `item` the daïra and the item.

## Spellings

The texts don't always agree with each other. Law 26-06 prints the commune "آفلو" and Decree 26-206 prints the wilaya "أفلو"; Decree 26-253 prints both, "آفلو" for the seat of the daïra and "أفلو" for the commune. Law 19-12 prints "لواء", "Oumach" and "Khenguet Sidi Nadji" where Law 26-06 prints "ليوة", "Oumache" and "Khangat Sidi Nadji". Ordinance 21-03 prints "حاسي بن عبد الله", "Ain Beida" and "Blidate Ameur" where Law 19-12 prints "حاسي بن عبد اللّه", "Aïn Beïda" and "Blidat Ameur". Decree 21-117 names the chef-lieu of wilaya 57 "El M’Ghaier", and Law 19-12 lists the commune as "El Megaier". Within Decree 91-306, a daïra's seat is printed apart from its list of communes, and the seat's commune heads the list. Fourteen times the two differ by more than capitals, accents, hyphens, hamzas or the dots of a final ي or ة: the seat "BEDJIA" heads the commune "Béjaia", "GUENZET" heads "Gunzet", "MOSTEFA BEN BRAHIM" heads "Mostepha Ben Brahim", and "عين موسى" heads "عمي موسى". Two seats, "El HACHIMIA" and "OUED El ABTAL", print "El" in small letters. In Decree 26-253 a seat and its commune differ five times, only by an accent, a capital, the shape of an apostrophe, or the hamza or madda on an alif. Decree 26-253 spells 26 names differently from Law 26-06, 19 French and 7 Arabic. Most differ by an accent, an apostrophe or a capital, as the decree's "Aïn Yagout" for the law's "Ain Yagout", or by the dots of a final ي; four differ by more: the decree prints "Béni Yaagoub", "El Azizia", "Bougtoub" and "سيدي عبد الرحمن" where the law prints "Ben Yaagoub", "Al Azizia", "Bougtob" and "سيدي عبد الرحمان". The tests list all of them.

Each file keeps its own text's spelling. The API uses the spelling of the latest text that names the place, and gives the others as aliases.

The tools that made these files are in [`tools/gazette/`](../../tools/gazette/).

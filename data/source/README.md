# Transcriptions

One file per official text, as printed in the Journal officiel, in both editions. The texts are listed in [`../texts.csv`](../texts.csv), with links to their PDFs and the checksums of the files we read. The API is built from these transcriptions; they are never edited to "fix" a spelling ([why](#spellings)).

| File | Text | Rows |
|---|---|---|
| `law-19-12.csv` | Law 19-12 of 11 December 2019: the lists it rewrites (articles 5 to 51) and the ten wilayas it creates (52 bis to 52 bis 9) | 162 |
| `presidential-decree-21-117.csv` | Presidential Decree 21-117 of 22 March 2021: the names and chefs-lieux of wilayas 49 to 58 | 10 |
| `ordinance-21-03.csv` | Ordinance 21-03 of 25 March 2021: the lists of Ouargla and Touggourt, which it rewrites (articles 34 and 52 bis 6) | 21 |
| `law-26-06.csv` | Law 26-06 of 4 April 2026: the lists it rewrites (articles 7 to 36) and the eleven wilayas it creates (52 bis 10 to 52 bis 20) | 404 |
| `presidential-decree-26-206.csv` | Presidential Decree 26-206 of 25 May 2026: the names and chefs-lieux of wilayas 59 to 69 | 11 |
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

The decrees' files have one row per wilaya: `item` is the wilaya's number, `name_fr` and `name_ar` its name, and `seat_fr` and `seat_ar` its chef-lieu.

A list's number is not a commune code. The codes go back to the 1984 lists, and a wilaya keeps them, gaps included, when a later law rewrites its list.

## How each name was checked

The French comes from the text of the PDF, which is exact. The Arabic is read twice, by OCR of the rendered page and from the PDF's own text, which is drawn correctly but stored out of order. `check` says what happened:

- **Empty:** the two readings have the same letters.
- **`eye`:** they don't, or one of them missed the name. The name was read on the rendered page, and `readings.csv` records the reading, the page, who read it and why.

So far every reading is by Claude, the AI model that ran the transcription (`by` is `claude`). They are reviewed against the printed pages before version 1.

The tests refuse any other value, and check that each `eye` row matches its reading.

## Spellings

The texts don't always agree with each other. Law 26-06 prints the commune "آفلو" and the decree prints the wilaya "أفلو". Law 19-12 prints "لواء", "Oumach" and "Khenguet Sidi Nadji" where Law 26-06 prints "ليوة", "Oumache" and "Khangat Sidi Nadji". Ordinance 21-03 prints "حاسي بن عبد الله", "Ain Beida" and "Blidate Ameur" where Law 19-12 prints "حاسي بن عبد اللّه", "Aïn Beïda" and "Blidat Ameur". Decree 21-117 names the chef-lieu of wilaya 57 "El M’Ghaier", and Law 19-12 lists the commune as "El Megaier". Each file keeps its own text's spelling. The API uses the spelling of the latest text that names the place, and gives the others as aliases.

The tools that made these files are in [`tools/gazette/`](../../tools/gazette/).

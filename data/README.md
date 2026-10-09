# Data

The tables the API is built from. [`tools/resolve.py`](../tools/resolve.py) makes them from the transcriptions of the official texts in [`source/`](source/), and the tests check that they are up to date. Don't edit them by hand: correct the transcription, then run

```bash
python3 tools/resolve.py
```

| File | Rows | What it holds |
|---|---|---|
| `wilayas.csv` | 69 | Each wilaya, its names and its chef-lieu |
| `dairas.csv` | 538 | Each daïra, with the wilaya it is in |
| `communes.csv` | 1,541 | Each commune, with its wilaya and daïra |
| `changes.csv` | 119 | The 2026 changes: the 11 wilayas Law 26-06 creates and the 108 communes it moves to them |
| `aliases.csv` | | Other spellings of the names, with the texts that print them |
| `texts.csv` | | The official texts, with links to their PDFs and checksums |
| `ons.csv` | | ONS's code géographique, with a link and a checksum |

## Citations

Every record cites the text it comes from by its id in `texts.csv` or `ons.csv`, an article and an item:

- In the laws and ordinances, `article` and `item` are the article and the number in its list.
- In the daïra decrees, which list communes in tables, `article` is the wilaya whose table it is, and `item` the daïra's place in the table and the commune's place in the daïra: `10/2` is the second commune of the tenth daïra. A daïra is cited by its place alone: `10`.

This is how [`source/readings.csv`](source/readings.csv) cites them too.

## Wilayas

| Column | Meaning |
|---|---|
| `code` | `01` to `69` |
| `name_fr`, `name_ar` | As the text that names the wilaya prints them |
| `named_by`, `named_article`, `named_item` | That text: Decree 84-79 for 01 to 48, Decree 21-117 for 49 to 58, Decree 26-206 for 59 to 69 |
| `seat` | The code of the commune that is its chef-lieu. Empty for Algiers, whose chef-lieu is the city of Algiers, not one commune |
| `parent` | For 49 to 69, the wilaya whose communes it was made of |
| `created`, `created_by`, `created_article` | For 49 to 69, the date of the Journal officiel issue of the law that created it, the law and its article |
| `listed_by`, `listed_article` | The article of Law 84-09 that lists its communes, and the latest text that wrote it: Law 84-09 itself, Law 19-12, Ordinance 21-03 or Law 26-06 |
| `dairas`, `communes` | How many |

Decree 84-79 dates from 1984, and the API names wilayas 01 to 48 as it prints them. Its Arabic writes a final ى where later texts write ي, as in "تيزى وزو", and "الاغواط" without a hamza.

## Daïras

| Column | Meaning |
|---|---|
| `code` | The code of the commune that is its seat |
| `wilaya` | The wilaya it is in |
| `name_fr`, `name_ar` | The names of its seat's commune. The decrees print a seat's name apart from its list of communes, sometimes spelled otherwise; those spellings are aliases |
| `listed_by`, `listed_article`, `listed_item` | The latest decree that prints the daïra, and its place there |
| `communes` | How many |

The daïras are those of Decree 91-306 of 1991, as Decrees 92-66, 18-302, 21-198, 25-87 and 26-253 redraw them. Two kinds of commune have no daïra (`daira` is empty in `communes.csv`):

- **Algiers' 57 communes.** In 1991 Algiers had 12 daïras. Ordinance 97-14 added 24 communes to it without placing them in a daïra, and Algiers' later organisation is not among the texts transcribed here. Its 12 daïras of 1991 are left out.
- **Three communes of Blida and Boumerdès.** Ordinance 97-14 moved to Algiers the seats of the daïras of Sidi Moussa (Blida) and Reghaïa (Boumerdès), but not their other communes: Ouled Selama, Ouled Hadjadj and Boudouaou El Bahri. No text transcribed here places them in another daïra.

## Communes

| Column | Meaning |
|---|---|
| `code` | ONS's code: the wilaya's two digits, then the commune's. The 108 communes Law 26-06 moved keep their old wilaya's code until ONS gives them new ones |
| `wilaya` | The wilaya it is in today |
| `daira` | The code of its daïra, or empty ([above](#daïras)) |
| `name_fr`, `name_ar` | As printed in the latest text that lists the commune |
| `name_fr_by`, `name_ar_by` | Where each name comes from: that text, or `ons-2021` for the three exceptions below |
| `listed_by`, `listed_article`, `listed_item` | The latest text that lists the commune, and its place there |
| `wilaya_before` | For the 108 communes Law 26-06 moved, the wilaya they were in |

A commune's code comes from ONS's code géographique of 2021, the latest edition. Each commune is paired with the one code whose names are its own, but for spelling; `tools/resolve.py` lists the names that differ by more.

The names are as printed: the API doesn't fix a spelling, and the texts don't always agree ([`source/README.md`](source/README.md#spellings)). Three communes take ONS's names instead:

- **Mohamed Belouizdad (1604) and Houari Boumediene (2427).** The latest text that lists them, Decree 91-306, names them Hamma Annassers and Aïn Hsainia. ONS lists them under their new names, and no text transcribed here renames them. Their names are ONS's, in its capitals; the old names are aliases. Five other communes renamed since 1991 are printed under their new names by Law 26-06 and Decree 26-253, such as Mouhamed Boudiaf, formerly Oued Chair.
- **Boudria Beni Yadjis (1822), in Arabic.** Decree 91-306's Arabic prints its name on two lines, as if it were two communes; the Arabic name is ONS's.

## Changes

| Column | Meaning |
|---|---|
| `date` | The date of the Journal officiel issue: 5 April 2026 for Law 26-06 |
| `type` | `wilaya_created` or `commune_moved` |
| `subject` | The wilaya's or the commune's code |
| `from`, `to` | The wilaya it was taken from, and the new one |
| `by`, `article`, `item` | The text and the place in it: the article of Law 84-09 that Law 26-06 adds, and the commune's number in its list |

## Aliases

| Column | Meaning |
|---|---|
| `kind` | `wilaya`, `daira` or `commune` |
| `code` | Its code |
| `lang` | `fr`, `ar`, or `en` for Algiers |
| `name` | The other spelling |
| `texts` | The texts that print it, oldest first |

An alias is any spelling a transcribed text prints for the place other than the name the API gives it. Spellings that differ only in capitals or in the shape of the apostrophe count as one.

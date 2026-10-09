# Gazette tools

These scripts transcribe the official texts in the Journal officiel into `data/source/`. They ran once, on a Mac, to make the files there; the build and the tests don't need them. To check a name, read the text itself: every text in `data/texts.csv` links to its PDFs.

| Script | What it does |
|---|---|
| `columns.swift` | Prints the text of a text PDF column by column (macOS PDFKit). |
| `runs.swift` | Prints each run of text with its position. Used for the Arabic editions of JO n° 78 of 2019 and n° 22 of 2021, which store their text one word at a time, and for both editions of JO n° 38 of 2021 and n° 52 of 2026, to place the names in the tables of Decrees 21-198 and 26-253. |
| `ocr.swift` | Reads rendered pages with macOS Vision OCR and prints each line with its position. |
| `render.swift` | Renders part of a page as a PNG, to read it by eye. |
| `crops.swift` | Renders many parts of pages as PNGs in one run. |
| `lists.py` | Builds the lists of communes of a law or an ordinance from both editions. |
| `decree.py` | Builds the names and chefs-lieux of new wilayas from Decree 21-117 (49 to 58) or Decree 26-206 (59 to 69). |
| `review.py` | Crops the printed line of every name in `readings.csv`, to check the readings against the page. |
| `rules.swift` | Finds the rules between the rows of the tables on rendered pages (Decrees 91-306, 21-198 and 26-253). |
| `regions.py` | Prints the parts of Decree 91-306's pages to read again by OCR: each half-page column, or each row of a table. |
| `regions.swift` | Reads those parts, or the rows of the tables that `tables.py` prints (Decrees 21-198 and 26-253), with macOS Vision OCR, as `ocr.swift` reads whole pages. |
| `dairas.py` | Builds the daïra tables of one edition of Decree 91-306 from the OCR and the rules. |
| `wikidata.py` | Fetches the labels of Algeria's communes from Wikidata (CC0), which the OCR's readings are checked against. Nothing from Wikidata goes into the data. |
| `annex.py` | Pairs the two editions' tables of Decree 91-306 and checks each name. |
| `sheets.py`, `grid.swift` | Lay out on sheets, to read by eye, the names of Decree 91-306 that the OCR doesn't settle. |
| `bitmap.swift` | Renders parts of pages as black-and-white bitmaps, to measure the letters. |
| `alifs.py` | Checks the hamzas of Decree 91-306's Arabic names against the shapes of the alifs on the scan. |
| `ordinance.py` | Builds the communes Ordinance 97-14 moves to Algiers from the OCR of both editions. |
| `tables.py` | Builds the daïra tables of Decree 26-253, or with `--text` of Decree 21-198, from both editions' text and rules, and the OCR of the Arabic. |

## Method

- **French:** the text of the PDF, which is exact.
- **Arabic:** read twice, once by OCR of the rendered page and once from the PDF's own text, and the two readings are aligned item by item.
  - Where they have the same letters, the PDF's characters are kept.
  - Every other name is read on the rendered page and recorded, with who read it, in [`data/source/readings.csv`](../../data/source/readings.csv).
- Both editions must give the same articles, with the same number of communes in each list.
- **Tables** (Decrees 21-198 and 26-253): each name is placed in its table from the positions of its text, between the rules found on the rendered page. The Arabic text layer garbles the wilaya headings and runs a few lines together, so the Arabic is also read by OCR, of whole pages and of each row at 400 dpi, and the wilaya numbers come from the OCR's headings. A name is kept from the text layer when an OCR reading has the same letters and the same spaces. Both editions must give the same wilayas, with the same number of daïras in each and of communes in each daïra.
- **Scans** (Decree 91-306, both editions): each page is read by OCR four ways: whole and by half-page column at 300 dpi, and by row of the tables at 300 and 400 dpi. A name is taken from the OCR when every reading agrees and is the label of a commune in Wikidata. Every other name is read on the rendered page and recorded in `readings.csv`. Both editions must give the same tables, but for the lines listed in `GAPS` in `annex.py`. Ordinance 97-14 (both editions) is read the same way, whole and by its articles at 400 dpi; both editions must give the same number of communes in each article.

## Commands

The PDFs come from `https://www.joradp.dz/FTP/` (see `data/texts.csv`) and are kept out of git in `sources/joradp/`. The working files go to `work/`, also out of git.

```sh
# Law 26-06 (JO n° 25 of 2026)
swift tools/gazette/columns.swift fr sources/joradp/F2026025.pdf 4 9 > work/F2026025.txt
swift tools/gazette/columns.swift ar sources/joradp/A2026025.pdf 4 11 > work/A2026025.txt
swift tools/gazette/ocr.swift sources/joradp/A2026025.pdf 4 11 ar-SA > work/A2026025.ocr.jsonl
python3 tools/gazette/lists.py law-26-06 work/F2026025.txt work/A2026025.txt work/A2026025.ocr.jsonl > data/source/law-26-06.csv

# Law 19-12 (JO n° 78 of 2019)
swift tools/gazette/columns.swift fr sources/joradp/F2019078.pdf 12 15 > work/F2019078.txt
swift tools/gazette/runs.swift sources/joradp/A2019078.pdf 13 16 > work/A2019078.runs.jsonl
swift tools/gazette/ocr.swift sources/joradp/A2019078.pdf 12 17 ar-SA > work/A2019078.ocr.jsonl
python3 tools/gazette/lists.py law-19-12 work/F2019078.txt work/A2019078.runs.jsonl work/A2019078.ocr.jsonl > data/source/law-19-12.csv

# Presidential Decree 21-117 and Ordinance 21-03 (JO n° 22 of 2021)
swift tools/gazette/columns.swift fr sources/joradp/F2021022.pdf 6 8 > work/F2021022.txt
swift tools/gazette/runs.swift sources/joradp/A2021022.pdf 7 8 > work/A2021022.runs.jsonl
swift tools/gazette/ocr.swift sources/joradp/A2021022.pdf 7 8 ar-SA > work/A2021022.ocr.jsonl
python3 tools/gazette/decree.py presidential-decree-21-117 work/F2021022.txt work/A2021022.runs.jsonl work/A2021022.ocr.jsonl > data/source/presidential-decree-21-117.csv
python3 tools/gazette/lists.py ordinance-21-03 work/F2021022.txt work/A2021022.runs.jsonl work/A2021022.ocr.jsonl > data/source/ordinance-21-03.csv

# Presidential Decree 26-206 (JO n° 40 of 2026)
swift tools/gazette/columns.swift fr sources/joradp/F2026040.pdf 5 5 > work/F2026040.txt
swift tools/gazette/columns.swift ar sources/joradp/A2026040.pdf 6 6 > work/A2026040.txt
swift tools/gazette/ocr.swift sources/joradp/A2026040.pdf 6 6 ar-SA > work/A2026040.ocr.jsonl
python3 tools/gazette/decree.py presidential-decree-26-206 work/F2026040.txt work/A2026040.txt work/A2026040.ocr.jsonl > data/source/presidential-decree-26-206.csv

# Executive Decree 91-306 (JO n° 41 of 1991): both editions are scans
swift tools/gazette/ocr.swift sources/joradp/F1991041.pdf 3 28 fr-FR > work/F1991041.ocr.jsonl
swift tools/gazette/ocr.swift sources/joradp/A1991041.pdf 3 32 ar-SA > work/A1991041.ocr.jsonl
swift tools/gazette/rules.swift sources/joradp/F1991041.pdf 3 28 > work/F1991041.rules.jsonl
swift tools/gazette/rules.swift sources/joradp/A1991041.pdf 3 32 > work/A1991041.rules.jsonl
for e in F:fr A:ar; do
  f=work/${e%:*}1991041 l=${e#*:}
  python3 tools/gazette/regions.py columns $l $f.ocr.jsonl | swift tools/gazette/regions.swift > $f.columns.ocr.jsonl
  python3 tools/gazette/regions.py rows $l $f.ocr.jsonl $f.rules.jsonl | swift tools/gazette/regions.swift > $f.rows.ocr.jsonl
  python3 tools/gazette/regions.py rows $l $f.ocr.jsonl $f.rules.jsonl 400 | swift tools/gazette/regions.swift > $f.rows400.ocr.jsonl
  python3 tools/gazette/dairas.py $l $f.rules.jsonl $f.rows.jsonl $f.ocr.jsonl $f.columns.ocr.jsonl $f.rows.ocr.jsonl $f.rows400.ocr.jsonl
done
python3 tools/gazette/wikidata.py > work/wikidata-labels.json
python3 tools/gazette/annex.py work/F1991041.rows.jsonl work/A1991041.rows.jsonl work/wikidata-labels.json > data/source/executive-decree-91-306.csv

# Ordinance 97-14 (JO n° 38 of 1997): both editions are scans
swift tools/gazette/ocr.swift sources/joradp/F1997038.pdf 1 12 fr-FR > work/F1997038.ocr.jsonl
swift tools/gazette/ocr.swift sources/joradp/A1997038.pdf 1 8 ar-SA > work/A1997038.ocr.jsonl
python3 tools/gazette/ordinance.py regions | swift tools/gazette/regions.swift > work/1997038.articles.ocr.jsonl
python3 tools/gazette/ordinance.py work/F1997038.ocr.jsonl work/A1997038.ocr.jsonl work/1997038.articles.ocr.jsonl work/wikidata-labels.json > data/source/ordinance-97-14.csv

# Executive Decree 21-198 (JO n° 38 of 2021)
swift tools/gazette/runs.swift sources/joradp/F2021038.pdf 8 11 > work/F2021038.runs.jsonl
swift tools/gazette/runs.swift sources/joradp/A2021038.pdf 9 12 > work/A2021038.runs.jsonl
swift tools/gazette/rules.swift sources/joradp/F2021038.pdf 8 11 > work/F2021038.rules.jsonl
swift tools/gazette/rules.swift sources/joradp/A2021038.pdf 9 12 > work/A2021038.rules.jsonl
swift tools/gazette/ocr.swift sources/joradp/A2021038.pdf 9 12 ar-SA > work/A2021038.ocr.jsonl
python3 tools/gazette/tables.py regions work/A2021038.runs.jsonl work/A2021038.rules.jsonl sources/joradp/A2021038.pdf ar-SA 400 | swift tools/gazette/regions.swift > work/A2021038.bands.ocr.jsonl
python3 tools/gazette/tables.py --text executive-decree-21-198 work/F2021038.runs.jsonl work/F2021038.rules.jsonl work/A2021038.runs.jsonl work/A2021038.rules.jsonl work/A2021038.ocr.jsonl work/A2021038.bands.ocr.jsonl > data/source/executive-decree-21-198.csv

# Executive Decree 26-253 (JO n° 52 of 2026)
swift tools/gazette/runs.swift sources/joradp/F2026052.pdf 10 16 > work/F2026052.runs.jsonl
swift tools/gazette/runs.swift sources/joradp/A2026052.pdf 10 18 > work/A2026052.runs.jsonl
swift tools/gazette/rules.swift sources/joradp/F2026052.pdf 10 16 > work/F2026052.rules.jsonl
swift tools/gazette/rules.swift sources/joradp/A2026052.pdf 10 18 > work/A2026052.rules.jsonl
swift tools/gazette/ocr.swift sources/joradp/A2026052.pdf 10 18 ar-SA > work/A2026052.ocr.jsonl
python3 tools/gazette/tables.py regions work/A2026052.runs.jsonl work/A2026052.rules.jsonl sources/joradp/A2026052.pdf ar-SA 400 | swift tools/gazette/regions.swift > work/A2026052.bands.ocr.jsonl
python3 tools/gazette/tables.py work/F2026052.runs.jsonl work/F2026052.rules.jsonl work/A2026052.runs.jsonl work/A2026052.rules.jsonl work/A2026052.ocr.jsonl work/A2026052.bands.ocr.jsonl > data/source/executive-decree-26-253.csv
```

`lists.py`, `decree.py`, `ordinance.py` and `tables.py` list on stderr every name still waiting to be read on the page. To read one, render it:

```sh
swift tools/gazette/render.swift sources/joradp/A2026025.pdf 6 416 564 149 67 crop.png 300
```

The coordinates are in PDF points from the page's bottom-left corner.

To check the names already read on the page, crop each one with its neighbours. The crops are placed from the OCR's positions:

```sh
python3 tools/gazette/review.py work/review   # writes work/review/crops/*.png and work/review/readings.json
```

For Decree 91-306, `annex.py` lists on stderr the names that need the page, and `sheets.py` lays them out, 24 to a sheet, with the OCR's readings and the nearest Wikidata label in `items.json`. Once the readings are in `readings.csv`, `alifs.py` lists the Arabic names whose hamzas the scan contradicts, to look at again:

```sh
python3 tools/gazette/sheets.py work/F1991041.rows.jsonl work/A1991041.rows.jsonl work/wikidata-labels.json work/eye
python3 tools/gazette/alifs.py work/F1991041.rows.jsonl work/A1991041.rows.jsonl
python3 tools/gazette/alifs.py work/F1991041.rows.jsonl work/A1991041.rows.jsonl --show 44 8/3   # one name, drawn in text
```

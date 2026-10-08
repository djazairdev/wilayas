# Gazette tools

These scripts transcribe the official texts in the Journal officiel into `data/source/`. They ran once, on a Mac, to make the files there; the build and the tests don't need them. To check a name, read the text itself: every text in `data/texts.csv` links to its PDFs.

| Script | What it does |
|---|---|
| `columns.swift` | Prints the text of a text PDF column by column (macOS PDFKit). |
| `runs.swift` | Prints each run of text with its position. Used for the Arabic edition of JO n° 78 of 2019, which stores its text one word at a time. |
| `ocr.swift` | Reads rendered pages with macOS Vision OCR and prints each line with its position. |
| `render.swift` | Renders part of a page as a PNG, to read it by eye. |
| `lists.py` | Builds the lists of communes of a law from both editions. |
| `decree.py` | Builds the names and chefs-lieux of wilayas 59 to 69 from Decree 26-206. |

## Method

- **French:** the text of the PDF, which is exact.
- **Arabic:** read twice, once by OCR of the rendered page and once from the PDF's own text, and the two readings are aligned item by item.
  - Where they have the same letters, the PDF's characters are kept.
  - Every other name is read on the rendered page and recorded, with who read it, in [`data/source/readings.csv`](../../data/source/readings.csv).
- Both editions must give the same articles, with the same number of communes in each list.

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

# Presidential Decree 26-206 (JO n° 40 of 2026)
swift tools/gazette/columns.swift fr sources/joradp/F2026040.pdf 5 5 > work/F2026040.txt
swift tools/gazette/columns.swift ar sources/joradp/A2026040.pdf 6 6 > work/A2026040.txt
swift tools/gazette/ocr.swift sources/joradp/A2026040.pdf 6 6 ar-SA > work/A2026040.ocr.jsonl
python3 tools/gazette/decree.py work/F2026040.txt work/A2026040.txt work/A2026040.ocr.jsonl > data/source/presidential-decree-26-206.csv
```

`lists.py` and `decree.py` list on stderr every name still waiting to be read on the page. To read one, render it:

```sh
swift tools/gazette/render.swift sources/joradp/A2026025.pdf 6 416 564 149 67 crop.png 300
```

The coordinates are in PDF points from the page's bottom-left corner.

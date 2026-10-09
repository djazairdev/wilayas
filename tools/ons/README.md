# ONS tools

These scripts transcribe ONS's code géographique national into `data/source/ons-2021.csv`. They ran once, on a Mac; the build and the tests don't need them. The PDFs come from ONS's site (see `data/ons.csv`) and are kept out of git in `sources/ons/`; the working files go to `work/ons/`, also out of git.

| Script | What it does |
|---|---|
| `chars.swift` | Prints every character of a text PDF with its box (macOS PDFKit). |
| `codes.py` | Rebuilds the list's rows from the characters, checks the Arabic against the OCR, and writes the CSV. |

The OCR uses `tools/gazette/ocr.swift` and `tools/gazette/regions.swift`, and the names to read are rendered with `tools/gazette/crops.swift`.

## Method

- **Rows:** the characters on one line make a row. Its four digits are the code; the letters left of them are the French name, and those right of them the Arabic name, read right to left. A gap between two letters is a space. Every row's wilaya must be its heading's, and every code is printed once.
- **French and codes:** the text of the PDF, which is exact.
- **Arabic:** the text of the PDF, read again by OCR of whole pages and of each row at 400 dpi. A name is kept when an OCR reading has the same letters and the same spaces. Every other name is read on the rendered page and recorded in [`data/source/readings.csv`](../../data/source/readings.csv). About one name in ten is stored with its letters out of order; the OCR's readings of those are only a guide.

## Commands

```sh
swift tools/ons/chars.swift sources/ons/code_geo_2021.pdf 4 66 > work/ons/2021.chars.jsonl
swift tools/gazette/ocr.swift sources/ons/code_geo_2021.pdf 4 66 ar-SA > work/ons/2021.ocr.jsonl
python3 tools/ons/codes.py regions work/ons/2021.chars.jsonl sources/ons/code_geo_2021.pdf ar-SA 400 | swift tools/gazette/regions.swift > work/ons/2021.rows.ocr.jsonl
python3 tools/ons/codes.py work/ons/2021.chars.jsonl work/ons/2021.ocr.jsonl work/ons/2021.rows.ocr.jsonl > data/source/ons-2021.csv
```

`codes.py` lists on stderr every name still waiting to be read on the page.

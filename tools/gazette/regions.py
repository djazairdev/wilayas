"""Print the regions of the scanned annex of Decree 91-306 to read again by OCR, one JSON line
each, for tools/gazette/regions.swift:

- `columns`: each page's two half-page columns, split at the gutter (dairas.gutter);
- `rows`: each row of the tables, the band between two rules (tools/gazette/rules.swift).

The OCR of the whole pages (tools/gazette/ocr.swift) places the gutter.

    python3 tools/gazette/regions.py columns ar work/A1991041.ocr.jsonl [dpi]
    python3 tools/gazette/regions.py rows ar work/A1991041.ocr.jsonl work/A1991041.rules.jsonl [dpi]

Another scan laid out the same way (Decree 92-66) is named before the arguments, with its PDF and
the pages of its tables: `--pdf sources/joradp/F1992013.pdf 17 18`.

Standard library only.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dairas  # noqa: E402

PAGES = {'fr': ('sources/joradp/F1991041.pdf', 3, 28, 'fr-FR'), 'ar': ('sources/joradp/A1991041.pdf', 3, 32, 'ar-SA')}
TOP = 0.05     # rules above this belong to the running head
MIN_ROW = 0.012  # thinner bands are a rule drawn twice
PAD = 0.002    # each band reaches a little past its rules


def main():
    args = sys.argv[1:]
    other = None
    if args[0] == '--pdf':
        other, args = (args[1], int(args[2]), int(args[3])), args[4:]
    kind, language, ocr_path, *rest = args
    pdf, first, last, lang = PAGES[language]
    if other:
        pdf, first, last = other
    with open(ocr_path, encoding='utf-8') as f:
        lines = [json.loads(line) for line in f]
    rules = dairas.read_rules(rest.pop(0)) if kind == 'rows' else {}
    dpi = int(rest[0]) if rest else 300
    for page in range(first, last + 1):
        g = dairas.gutter([e for e in lines if e['page'] == page and e['y'] >= dairas.HEAD])
        for side, x0, x1 in (('left', 0.0, g), ('right', g, 1.0)):
            if kind == 'columns':
                bands = [(0.0, 1.0)]
            else:
                ys = [y for y in rules.get((page, side), []) if y > TOP]
                bands = [(max(0, a - PAD), min(1, b + PAD)) for a, b in zip(ys, ys[1:]) if b - a > MIN_ROW]
            for top, bottom in bands:
                print(json.dumps({'pdf': pdf, 'page': page, 'x': x0, 'y': top, 'w': x1 - x0, 'h': bottom - top,
                                  'dpi': dpi, 'lang': lang}))


if __name__ == '__main__':
    main()

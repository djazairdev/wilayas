"""Parse a presidential decree that names new wilayas and their chefs-lieux, completing
article 1 of Decree 84-79: Decree 21-117 (wilayas 49 to 58) or Decree 26-206 (59 to 69).

Article 1 lists them as "49- Wilaya de Timimoun avec chef-lieu à Timimoun ;" (21-117) or
"59- Wilaya d'Aflou avec chef-lieu la ville d'Aflou ;" (26-206) and, in Arabic, as
"59- ولاية أفلو، مقرها مدينة أفلو،". The French comes from the PDF's text
(tools/gazette/columns.swift), which is exact. The Arabic comes from OCR
(tools/gazette/ocr.swift), because the PDF's text mixes up most of these lines. Each
OCR'd entry is compared with the PDF's own text where that text can still be parsed (as
columns from columns.swift, or as runs from runs.swift for issues that store their Arabic
one word at a time), and with data/source/readings.csv, which records entries read on the
rendered page (the reading's `name` is the whole entry: "ولاية أفلو، مقرها مدينة أفلو").
An entry with neither is listed on stderr, and the tests refuse it.

    python3 tools/gazette/decree.py presidential-decree-26-206 F.txt A.txt A.ocr.jsonl > data/source/presidential-decree-26-206.csv

Standard library only.
"""
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lists  # noqa: E402

# The wilayas each decree names
DECREES = {
    'presidential-decree-21-117': range(49, 59),
    'presidential-decree-26-206': range(59, 70),
}
FR_ENTRY = re.compile(r"(\d{2})\s*-\s*Wilaya\s+d(?:e\s+|['’]\s*)(.+?)\s+avec\s+chef-lieu\s+"
                      r"(?:la\s+ville\s+d(?:e\s+|['’]\s*)|à\s+)(.+?)\s*[;.,](?=\s|$)")
# An entry ends at its comma or full stop, or where the next article starts (21-117 prints
# no full stop after its last entry)
AR_ENTRY = re.compile(r'(\d{2})\s*[–-]\s*(ولاية\s+.+?،\s*مقرها\s+مدينة\s+.+?)\s*(?:[،.](?=\s|$)|(?=\s+المادّ?ة\b))')
AR_PARTS = re.compile(r'^ولاية\s+(.+?)،\s*مقرها\s+مدينة\s+(.+)$')


def french(lines):
    """{code: (name, seat)} from the French edition."""
    text = ' '.join(l.strip() for l in lines if l.strip() and not lists.NOISE.match(l.strip()))
    return {m.group(1): (m.group(2), m.group(3)) for m in FR_ENTRY.finditer(re.sub(r'\s+', ' ', text))}


def arabic(lines):
    """{code: entry} from Arabic lines [(page, text)] in reading order."""
    text = re.sub(r'\s+', ' ', ' '.join(t for _, t in lines))
    return {m.group(1): m.group(2) for m in AR_ENTRY.finditer(text)}


def main():
    text, fr_path, ar_path, ocr_path = sys.argv[1:5]
    codes = [str(n) for n in DECREES[text]]
    fr = french(lists.columns(fr_path))
    ocr = arabic(lists.ocr_lines(ocr_path, rtl=True))
    pdf = arabic(lists.run_lines(ar_path) if ar_path.endswith('.jsonl') else lists.column_lines(ar_path))
    seen = lists.readings(text)
    if sorted(fr) != codes or sorted(ocr) != codes:
        raise SystemExit(f'{text}: expected entries {codes[0]} to {codes[-1]}, '
                         f'got {sorted(fr)} in French and {sorted(ocr)} in Arabic')
    w = csv.DictWriter(sys.stdout, ['text', 'article', 'item', 'name_fr', 'seat_fr', 'name_ar', 'seat_ar', 'check'],
                       lineterminator='\n')
    w.writeheader()
    for code in codes:
        entry, check = ocr[code], 'ocr'
        if pdf.get(code) == entry:
            check = ''
        read = seen.get(('1', int(code), 'ar'))
        if read is not None:
            if read != entry:
                print(f'{code}: read {read!r}, the OCR has {entry!r}', file=sys.stderr)
            entry, check = read, 'eye'
        if check == 'ocr':
            print(f'to read: entry {code}: {entry} (the PDF has {pdf.get(code)!r})', file=sys.stderr)
        name_ar, seat_ar = AR_PARTS.match(entry).groups()
        w.writerow({'text': text, 'article': '1', 'item': code, 'name_fr': fr[code][0], 'seat_fr': fr[code][1],
                    'name_ar': name_ar, 'seat_ar': seat_ar, 'check': check})


if __name__ == '__main__':
    main()

"""Parse Presidential Decree 26-206, which names the new wilayas 59 to 69 and their chefs-lieux.

Its article 1 lists them as "59- Wilaya d'Aflou avec chef-lieu la ville d'Aflou ;" and,
in Arabic, "59- ولاية أفلو، مقرها مدينة أفلو،". The French comes from the PDF's text
(tools/gazette/columns.swift), which is exact. The Arabic comes from OCR
(tools/gazette/ocr.swift), because the PDF's text mixes up most of these lines. Each
OCR'd entry is compared with the PDF's own text where that text can still be parsed, and
with data/source/readings.csv, which records entries read on the rendered page (the
reading's `name` is the whole entry: "ولاية أفلو، مقرها مدينة أفلو"). An entry with
neither is listed on stderr, and the tests refuse it.

    python3 tools/gazette/decree.py F.txt A.txt A.ocr.jsonl > data/source/presidential-decree-26-206.csv

Standard library only.
"""
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lists  # noqa: E402

TEXT = 'presidential-decree-26-206'
FR_ENTRY = re.compile(r"(\d{2})\s*-\s*Wilaya\s+d(?:e\s+|['’]\s*)(.+?)\s+avec\s+chef-lieu\s+la\s+ville\s+"
                      r"d(?:e\s+|['’]\s*)(.+?)\s*[;.](?=\s|$)")
AR_ENTRY = re.compile(r'(\d{2})\s*[–-]\s*(ولاية\s+.+?،\s*مقرها\s+مدينة\s+.+?)\s*[،.](?=\s|$)')
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
    fr_path, ar_path, ocr_path = sys.argv[1:4]
    fr = french(lists.columns(fr_path))
    ocr = arabic(lists.ocr_lines(ocr_path, rtl=True))
    pdf = arabic(lists.column_lines(ar_path))
    seen = lists.readings(TEXT)
    codes = [str(n) for n in range(59, 70)]
    if sorted(fr) != codes or sorted(ocr) != codes:
        raise SystemExit(f'{TEXT}: expected entries 59 to 69, got {sorted(fr)} in French and {sorted(ocr)} in Arabic')
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
            print(f'to read: entry {code}: {entry}', file=sys.stderr)
        name_ar, seat_ar = AR_PARTS.match(entry).groups()
        w.writerow({'text': TEXT, 'article': '1', 'item': code, 'name_fr': fr[code][0], 'seat_fr': fr[code][1],
                    'name_ar': name_ar, 'seat_ar': seat_ar, 'check': check})


if __name__ == '__main__':
    main()

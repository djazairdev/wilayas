"""Build data/source/decree-84-79.csv from Decree 84-79 of 3 April 1984, which fixes the names and
the chefs-lieux of the 48 wilayas Law 84-09 created. Decrees 21-117 and 26-206 complete its
article 1 for wilayas 49 to 69 (tools/gazette/decree.py).

Article 1 lists them as "01 - wilaya d'Adrar avec chef-lieu à Adrar." and, in Arabic, as
"01 - ولاية أدرار مقرها مدينة أدرار،". Both editions of JO n° 14 of 1984 are scans, read as
Ordinance 97-14 is (tools/gazette/ordinance.py): each page by OCR whole
(tools/gazette/ocr.swift), and the list again at 400 dpi (tools/gazette/regions.swift). The
entries come in order, one to a wilaya, so an entry's place gives its number, which the OCR
often misreads. A name is taken from the OCR when both readings agree and it is the label of a
commune in Wikidata (a wilaya is named after its chef-lieu); any other name is read on the
rendered page, and data/source/readings.csv records the reading of the whole entry, as
"Adrar / Adrar": the wilaya's name, then its chef-lieu's. An entry with neither is listed on
stderr and gets the check `ocr`, which the tests refuse.

The Arabic is transcribed without harakat, as the other scans are.

    python3 tools/gazette/names84.py regions fr | swift tools/gazette/regions.swift > work/F1984014.list.ocr.jsonl
    python3 tools/gazette/names84.py regions ar | swift tools/gazette/regions.swift > work/A1984014.list.ocr.jsonl
    python3 tools/gazette/names84.py work/F1984014.ocr.jsonl work/F1984014.list.ocr.jsonl work/A1984014.ocr.jsonl work/A1984014.list.ocr.jsonl work/wikidata-labels.json > data/source/decree-84-79.csv

Standard library only.
"""
import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from annex import clean, known_names  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
READINGS = os.path.join(ROOT, 'data', 'source', 'readings.csv')
TEXT = 'decree-84-79'
FIELDS = ['text', 'article', 'item', 'name_fr', 'seat_fr', 'name_ar', 'seat_ar', 'check']
WILAYAS = 48
# The parts of the pages that hold article 1's list, in reading order (fractions of the page,
# y from the top)
REGIONS = {
    'fr': [('sources/joradp/F1984014.pdf', 3, 0.5, 0.43, 0.48, 0.56),
           ('sources/joradp/F1984014.pdf', 4, 0.02, 0.04, 0.48, 0.505)],
    'ar': [('sources/joradp/A1984014.pdf', 4, 0.02, 0.605, 0.47, 0.33),
           ('sources/joradp/A1984014.pdf', 5, 0.5, 0.05, 0.48, 0.88),
           ('sources/joradp/A1984014.pdf', 5, 0.02, 0.045, 0.47, 0.3)],
}
LANG = {'fr': 'fr-FR', 'ar': 'ar-SA'}
LINE = 0.008  # OCR boxes whose tops are this close are on one line
# The start of an entry: its number (often misread), a dash, and "wilaya"
START = {'fr': re.compile(r'^\W?\S{0,3}\s*[-–—]\s*w\S{3,5}\b', re.I), 'ar': re.compile(r'^\S{0,4}\s*[-–—]?\s*ولاية')}
# An entry: the wilaya's name, then the chef-lieu's ("avec chef-lieu à", which the OCR garbles)
ENTRY = {
    'fr': re.compile(r"\W?\S{0,3}\s*[-–—]\s*w\S{3,5}\s+(?:d\s?['’]\s?|de\s+)(.+?)\s+\S{2}[ae]c\s+ch\S{1,2}f?-?\s?\S{3,5}\s+(?:[àaA&i]\s+)?(.+?)$", re.I),
    'ar': re.compile(r'ولاية\s+(.+?)\s+مقرها\s+مدينة\W*\s+(.+?)$'),
}
HARAKAT = re.compile('[ً-ٰٟ]')


def load(path):
    with open(path, encoding='utf-8') as f:
        return [json.loads(line) for line in f]


def lines(ocr, edition):
    """The OCR's lines of the list, in reading order: each line's text, its boxes left to right, or
    right to left in Arabic, and the region it is in."""
    out = []
    for pdf, page, x, y, w, h in REGIONS[edition]:
        boxes = [o for o in ocr if o['page'] == page and x - 0.01 <= o['x'] and o['x'] + o['w'] <= x + w + 0.01
                 and y - 0.005 <= o['y'] <= y + h]
        rows = []
        for o in sorted(boxes, key=lambda o: o['y']):
            if rows and o['y'] - rows[-1][0]['y'] < LINE:
                rows[-1].append(o)
            else:
                rows.append([o])
        for row in rows:
            row = sorted(row, key=lambda o: -o['x'] if edition == 'ar' else o['x'])
            out.append((' '.join(o['text'] for o in row), row, (pdf, page, x, y, w, h)))
    return out


def name(text, edition):
    """A name as the OCR read it, without the marks the scan leaves after it."""
    return clean(re.sub(r'[\s»«*؛؟()]+$', '', text), edition)


def grouped(ocr, edition):
    """[(text, boxes, region)] for each entry in one OCR reading of an edition, in the order of the
    list."""
    found = []
    for line, boxes, place in lines(ocr, edition):
        line = re.sub(r'\s+', ' ', line).strip()
        if START[edition].match(line) or not found:
            found.append((line, boxes, place))
        else:
            found[-1] = (found[-1][0] + ' ' + line, found[-1][1] + boxes, found[-1][2])
    if len(found) != WILAYAS:
        raise SystemExit(f'{edition}: {len(found)} entries found')
    return found


def entries(ocr, edition):
    """[(name, chef-lieu)] from one OCR reading of an edition, in the order of the list."""
    out = []
    for e, _, _ in grouped(ocr, edition):
        e = HARAKAT.sub('', e) if edition == 'ar' else e
        m = ENTRY[edition].search(e)
        out.append((name(m.group(1), edition), name(m.group(2), edition)) if m else (e, ''))
    return out


def readings(path=READINGS):
    """{(item, edition): (name, chef-lieu)} read on the rendered page."""
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8', newline='') as f:
        return {(r['item'], r['edition']): tuple(r['name'].split(' / ')) for r in csv.DictReader(f) if r['text'] == TEXT}


def main():
    if sys.argv[1] == 'regions':
        edition = sys.argv[2]
        for pdf, page, x, y, w, h in REGIONS[edition]:
            print(json.dumps({'pdf': pdf, 'page': page, 'x': x, 'y': y, 'w': w, 'h': h, 'dpi': 400, 'lang': LANG[edition]}))
        return
    fr_page, fr_list, ar_page, ar_list, labels_path = sys.argv[1:6]
    found = {'fr': (entries(load(fr_page), 'fr'), entries(load(fr_list), 'fr')),
             'ar': (entries(load(ar_page), 'ar'), entries(load(ar_list), 'ar'))}
    known, read = known_names(labels_path), readings()
    out = csv.DictWriter(sys.stdout, FIELDS, lineterminator='\n')
    out.writeheader()
    waiting = 0
    for i in range(WILAYAS):
        item = f'{i + 1:02d}'
        row, checks = {'text': TEXT, 'article': '1', 'item': item}, []
        for e in ('fr', 'ar'):
            page, region = found[e][0][i], found[e][1][i]
            if (item, e) in read:
                (row['name_' + e], row['seat_' + e]), how = read[(item, e)], 'eye'
            elif page == region and all(n in known[e] for n in page):
                (row['name_' + e], row['seat_' + e]), how = page, ''
            else:
                (row['name_' + e], row['seat_' + e]), how = page, 'ocr'
                waiting += 1
                print(f'{item} {e}: page {" / ".join(page)!r} list {" / ".join(region)!r}'
                      f'{"" if all(n in known[e] for n in page) else ", not a Wikidata label"}', file=sys.stderr)
            checks.append(how)
        row['check'] = 'ocr' if 'ocr' in checks else 'eye' if 'eye' in checks else ''
        out.writerow(row)
    print(f'{waiting} entries to read on the page', file=sys.stderr)


if __name__ == '__main__':
    main()

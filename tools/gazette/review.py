"""Prepare the names read on the rendered page for review: one crop of the printed page per
reading in data/source/readings.csv, and a JSON list describing them.

Each crop shows the item with its neighbours, located from the OCR's positions: the item
itself when the OCR read it, otherwise the space between the items before and after it.
Decree 91-306's names, and Decree 92-66's, are cropped from the lines tools/gazette/dairas.py
placed, with the lines above and below, in the edition read (300 dpi in French, 400 in Arabic, to
see the hamzas).
Decrees 21-198's and 26-253's are cropped the same way, at 400 dpi, from the boxes
tools/gazette/tables.py gives their names. ONS's code géographique's are cropped from the rows
tools/ons/codes.py rebuilds, with the codes and the rows above and below, at 400 dpi. Ordinance
97-14's names are in the text of its articles: each crop is the whole article, in the edition
read, at 400 dpi. Decree 84-79's entries are cropped from the boxes of the list's OCR at 400 dpi,
with the entries above and below.

    python3 tools/gazette/review.py OUT_DIR
    # writes OUT_DIR/crops/*.png and OUT_DIR/readings.json

Needs the PDFs in sources/joradp/ and sources/ons/, and the OCR output in work/ (see README.md
and tools/ons/README.md).
Standard library only, plus crops.swift.
"""
import csv
import difflib
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import annex  # noqa: E402
import ordinance  # noqa: E402
import lists  # noqa: E402
import names84  # noqa: E402
import tables  # noqa: E402
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ons'))
import codes  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCE = os.path.join(ROOT, 'data', 'source')

# The Arabic edition's PDF and OCR output for each text
EDITIONS = {
    'law-26-06': ('sources/joradp/A2026025.pdf', 'work/A2026025.ocr.jsonl'),
    'law-19-12': ('sources/joradp/A2019078.pdf', 'work/A2019078.ocr.jsonl'),
    'presidential-decree-21-117': ('sources/joradp/A2021022.pdf', 'work/A2021022.ocr.jsonl'),
    'ordinance-21-03': ('sources/joradp/A2021022.pdf', 'work/A2021022.ocr.jsonl'),
    'presidential-decree-26-206': ('sources/joradp/A2026040.pdf', 'work/A2026040.ocr.jsonl'),
}
TITLES = {
    'law-26-06': 'Law 26-06',
    'law-19-12': 'Law 19-12',
    'presidential-decree-21-117': 'Decree 21-117',
    'ordinance-21-03': 'Ordinance 21-03',
    'presidential-decree-26-206': 'Decree 26-206',
}
LINE = 0.024  # a line of text, as a fraction of the page height
MARGIN = 0.012
# Decrees 91-306 and 92-66, both scans: the title, each edition's PDF and the resolution of its
# crops, the rows dairas.py made from each edition, and the lines only one edition prints
SCANS = {
    annex.TEXT: ('Decree 91-306', {'fr': ('sources/joradp/F1991041.pdf', 300), 'ar': ('sources/joradp/A1991041.pdf', 400)},
                 ('work/F1991041.rows.jsonl', 'work/A1991041.rows.jsonl'), annex.GAPS),
    'executive-decree-92-66': ('Decree 92-66', {'fr': ('sources/joradp/F1992013.pdf', 300), 'ar': ('sources/joradp/A1992013.pdf', 400)},
                               ('work/F1992013.rows.jsonl', 'work/A1992013.rows.jsonl'), {}),
}
# Decrees 21-198 and 26-253: the Arabic edition's PDF, and what tables.py places its names from
TABLES = {
    'executive-decree-21-198': ('Decree 21-198', 'sources/joradp/A2021038.pdf',
                                ('work/A2021038.runs.jsonl', 'work/A2021038.rules.jsonl',
                                 'work/A2021038.ocr.jsonl', 'work/A2021038.bands.ocr.jsonl')),
    'executive-decree-26-253': ('Decree 26-253', 'sources/joradp/A2026052.pdf',
                                ('work/A2026052.runs.jsonl', 'work/A2026052.rules.jsonl',
                                 'work/A2026052.ocr.jsonl', 'work/A2026052.bands.ocr.jsonl')),
}
# Decree 84-79: the OCR of each edition's list at 400 dpi
LIST_84_79 = {'fr': 'work/F1984014.list.ocr.jsonl', 'ar': 'work/A1984014.list.ocr.jsonl'}
# ONS's code géographique: the PDF, and the characters codes.py rebuilds its rows from
PDF_ONS = 'sources/ons/code_geo_2021.pdf'
CHARS_ONS = 'work/ons/2021.chars.jsonl'
# Ordinance 97-14: each article in each edition, (pdf, page, x, y, w, h)
ARTICLES_97_14 = {
    ('fr', '2'): ('sources/joradp/F1997038.pdf', 4, 0.5, 0.835, 0.47, 0.06),
    ('fr', '3'): ('sources/joradp/F1997038.pdf', 4, 0.5, 0.9, 0.47, 0.08),
    ('fr', '4'): ('sources/joradp/F1997038.pdf', 5, 0.02, 0.07, 0.47, 0.06),
    ('ar', '2'): ('sources/joradp/A1997038.pdf', 5, 0.03, 0.415, 0.47, 0.08),
    ('ar', '3'): ('sources/joradp/A1997038.pdf', 5, 0.03, 0.495, 0.47, 0.1),
    ('ar', '4'): ('sources/joradp/A1997038.pdf', 5, 0.03, 0.6, 0.47, 0.055),
}


def read(path):
    with open(path, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def ocr_entries(path):
    with open(os.path.join(ROOT, path), encoding='utf-8') as f:
        return [json.loads(line) for line in f]


def similar(a, b):
    return difflib.SequenceMatcher(None, lists.squeeze(a), lists.squeeze(b)).ratio()


def find_item(entries, pages, n, name):
    """The OCR line that reads item n of a list, on one of the pages: the same number and
    nearly the same name, or, where the OCR misread the number ("0- سيدي عمران" for 6),
    the same name."""
    best, score = None, 0.0
    for e in entries:
        m = lists.OCR_ITEM.match(e['text'].strip())
        if e['page'] in pages and m:
            r = similar(m.group(2), name)
            if (int(m.group(1)) == n and r >= 0.7) or r >= 0.9:
                if r > score:
                    best, score = e, r
    return best


def find_entry(entries, page, code):
    """The OCR line of a decree's entry, which starts with its number ("62- ولاية …")."""
    for e in entries:
        if e['page'] == page and re.match(rf'^{code}\s*[-–]', e['text'].strip()):
            return e
    return None


def column(e):
    return 'right' if e['x'] + e['w'] / 2 >= 0.5 else 'left'


def region(anchors, target):
    """(page, x, y, w, h) around the target line, or between its neighbours when the OCR
    missed it. anchors are the OCR lines of items n-1 and n+1 (either may be None)."""
    before, after = anchors
    if target is not None:
        near = [e for e in (before, target, after)
                if e is not None and e['page'] == target['page'] and column(e) == column(target)
                and abs(e['y'] - target['y']) < 3 * LINE]
        top, bottom, page, side = (min(e['y'] for e in near), max(e['y'] + e['h'] for e in near),
                                   target['page'], column(target))
    elif before is not None and after is not None and before['page'] == after['page'] \
            and column(before) == column(after) and after['y'] > before['y']:
        top, bottom, page, side = before['y'], after['y'] + after['h'], before['page'], column(before)
    elif before is not None:
        top, bottom, page, side = before['y'], before['y'] + before['h'] + 2 * LINE, before['page'], column(before)
    elif after is not None:
        top, bottom, page, side = after['y'] - 2 * LINE, after['y'] + after['h'], after['page'], column(after)
    else:
        return None
    if after is None:  # show the line below too: the item may run onto it
        bottom += LINE
    x = 0.5 if side == 'right' else 0.04
    top, bottom = max(0.0, top - MARGIN), min(1.0, bottom + MARGIN)
    return page, x, top, 0.46, bottom - top


def reading_id(r):
    """The reading's id on the review page: 'law-26-06-52-bis-10-1-ar', 'executive-decree-91-306-04-5-seat-ar'."""
    return '-'.join(re.sub(r'[\s/]+', '-', v) for v in (r['text'], r['article'], r['item'], r['edition']))


def lines_scan(text):
    """{(wilaya, 'daïra/item', edition): (row, OCR line)} for Decree 91-306 or 92-66."""
    title, pdfs, paths, gaps = SCANS[text]
    fr, ar = (annex.load(os.path.join(ROOT, p)) for p in paths)
    with open(os.path.join(SOURCE, text + '.csv'), encoding='utf-8', newline='') as f:
        rows = {(r['wilaya'], f"{r['daira']}/{r['item']}"): r for r in csv.DictReader(f)}
    out = {}
    for wilaya, daira, item, f, a in annex.entries(fr, ar, gaps):
        key = (f'{wilaya:02d}', f'{daira}/{item}')
        for edition, line in (('fr', f), ('ar', a)):
            if line is not None:
                out[key + (edition,)] = (rows[key], line)
    return out


def lines_tables(text):
    """{(wilaya, 'daïra/item', 'ar'): (row, name)} for Decree 21-198 or 26-253, each name with its box."""
    runs, rules, *ocr = (os.path.join(ROOT, p) for p in TABLES[text][2])
    with open(os.path.join(SOURCE, text + '.csv'), encoding='utf-8', newline='') as f:
        rows = {(r['wilaya'], f"{r['daira']}/{r['item']}"): r for r in csv.DictReader(f)}
    out = {}
    for wilaya, dairas in tables.arabic(runs, rules, ocr).items():
        for d, daira in enumerate(dairas, 1):
            items = [('seat', daira['seat'])] + [(str(i), e) for i, e in enumerate(daira['communes'], 1)]
            for item, e in items:
                out[(wilaya, f'{d}/{item}', 'ar')] = (rows[(wilaya, f'{d}/{item}')], e)
    return out


def lines_ons():
    """{(wilaya, commune, 'ar'): (row, the row's place)} for ONS's code géographique."""
    with open(os.path.join(SOURCE, codes.TEXT + '.csv'), encoding='utf-8', newline='') as f:
        rows = {(r['wilaya'], r['commune']): r for r in csv.DictReader(f)}
    return {(r['wilaya'], r['commune'], 'ar'): (rows[(r['wilaya'], r['commune'])], r)
            for r in codes.parse(codes.load(os.path.join(ROOT, CHARS_ONS)))}


def row_region(r):
    """(page, x, y, w, h) around a row of ONS's list, from the codes to the Arabic name, with the
    rows above and below."""
    y0, y1 = max(0.0, r['y'] - 1.15 * r['h']), min(1.0, r['y'] + 2.15 * r['h'])
    return r['page'], 0.42, y0, 0.54, y1 - y0


def scan_region(line):
    """(page, x, y, w, h) around a line of the scan, with the lines above and below."""
    x0, x1 = max(0.0, line['x'] - 0.03), min(1.0, line['x'] + line['w'] + 0.03)
    y0, y1 = max(0.0, line['y'] - 1.6 * line['h']), min(1.0, line['y'] + 2.6 * line['h'])
    return line['page'], x0, y0, x1 - x0, y1 - y0


def name_region(e):
    """(page, x, y, w, h) around a name of Decree 21-198 or 26-253, which may take two lines, with the
    lines above and below."""
    x0, x1 = max(0.0, e['x'] - 0.03), min(1.0, e['x'] + e['w'] + 0.03)
    y0, y1 = max(0.0, e['y'] - 1.5 * LINE), min(1.0, e['y'] + e['h'] + 1.5 * LINE)
    return e['page'], x0, y0, x1 - x0, y1 - y0


def entry_region(entries, n):
    """(pdf, page, x, y, w, h) around entry n of Decree 84-79's list (from 1), with the entries
    above and below it in the same column."""
    _, boxes, (pdf, page, x, y, w, h) = entries[n - 1]
    near = [b for _, bs, place in entries[max(0, n - 2):n + 1] if place == entries[n - 1][2] for b in bs]
    y0, y1 = min(b['y'] for b in near), max(b['y'] + b['h'] for b in near)
    y0, y1 = max(0.0, y0 - MARGIN), min(1.0, y1 + MARGIN)
    return pdf, page, x, y0, w, y1 - y0


def main():
    out = sys.argv[1]
    os.makedirs(os.path.join(out, 'crops'), exist_ok=True)
    readings = read(os.path.join(SOURCE, 'readings.csv'))
    rows, entries, requests, manifest = {}, {}, [], []
    placed = {}  # the daïra decrees' names, placed on the page
    for r in readings:
        text = r['text']
        if text == ordinance.TEXT:
            if text not in rows:
                rows[text] = {(x['article'], x['item']): x for x in read(os.path.join(SOURCE, text + '.csv'))}
            row, key = rows[text][(r['article'], r['item'])], reading_id(r)
            crop = f'crops/{key}.png'
            pdf, p, x, y, w, h = ARTICLES_97_14[(r['edition'], r['article'])]
            requests.append({'pdf': os.path.join(ROOT, pdf), 'page': p, 'x': x, 'y': y, 'w': w, 'h': h,
                             'out': os.path.join(out, crop), 'dpi': 400})
            manifest.append({'id': key, 'text': text, 'title': 'Ordinance 97-14', 'article': r['article'],
                             'item': r['item'], 'edition': r['edition'], 'reading': r['name'],
                             'name_fr': row['name_fr'], 'name_ar': row['name_ar'], 'page': r['pdf_page'],
                             'by': r['by'], 'reviewed_by': r['reviewed_by'], 'note': r['note'], 'crop': crop})
            continue
        if text == names84.TEXT:
            if text not in rows:
                rows[text] = {x['item']: x for x in read(os.path.join(SOURCE, text + '.csv'))}
            edition = r['edition']
            if (text, edition) not in placed:
                placed[(text, edition)] = names84.grouped(names84.load(os.path.join(ROOT, LIST_84_79[edition])), edition)
            row, key = rows[text][r['item']], reading_id(r)
            crop = f'crops/{key}.png'
            pdf, p, x, y, w, h = entry_region(placed[(text, edition)], int(r['item']))
            requests.append({'pdf': os.path.join(ROOT, pdf), 'page': p, 'x': x, 'y': y, 'w': w, 'h': h,
                             'out': os.path.join(out, crop), 'dpi': 400})
            manifest.append({'id': key, 'text': text, 'title': 'Decree 84-79', 'article': r['article'],
                             'item': r['item'], 'edition': edition, 'reading': r['name'],
                             'name_fr': f"{row['name_fr']} / {row['seat_fr']}", 'name_ar': f"{row['name_ar']} / {row['seat_ar']}",
                             'page': r['pdf_page'], 'by': r['by'], 'reviewed_by': r['reviewed_by'], 'note': r['note'],
                             'crop': crop})
            continue
        if text in SCANS or text == codes.TEXT or text in TABLES:
            if text not in placed:
                placed[text] = (lines_tables(text) if text in TABLES else
                                lines_scan(text) if text in SCANS else lines_ons())
            row, line = placed[text][(r['article'], r['item'], r['edition'])]
            key = reading_id(r)
            crop = f'crops/{key}.png'
            if text in SCANS:
                (p, x, y, w, h), (pdf, dpi), title = scan_region(line), SCANS[text][1][r['edition']], SCANS[text][0]
            elif text == codes.TEXT:
                (p, x, y, w, h), (pdf, dpi), title = row_region(line), (PDF_ONS, 400), 'ONS code géographique'
            else:
                (p, x, y, w, h), (pdf, dpi), title = name_region(line), (TABLES[text][1], 400), TABLES[text][0]
            requests.append({'pdf': os.path.join(ROOT, pdf), 'page': p, 'x': x, 'y': y, 'w': w, 'h': h,
                             'out': os.path.join(out, crop), 'dpi': dpi})
            manifest.append({'id': key, 'text': text, 'title': title, 'article': r['article'],
                             'item': r['item'], 'edition': r['edition'], 'reading': r['name'],
                             'name_fr': row['name_fr'], 'name_ar': row['name_ar'], 'page': r['pdf_page'],
                             'by': r['by'], 'reviewed_by': r['reviewed_by'], 'note': r['note'], 'crop': crop})
            continue
        if text not in rows:
            rows[text] = {(x['article'], x['item']): x for x in read(os.path.join(SOURCE, text + '.csv'))}
            entries[text] = ocr_entries(EDITIONS[text][1])
        row = rows[text][(r['article'], r['item'])]
        page, n = int(r['pdf_page']), int(r['item'])
        if 'seat_ar' in row:  # a decree: one line per wilaya
            target = find_entry(entries[text], page, n)
            anchors = (find_entry(entries[text], page, n - 1), find_entry(entries[text], page, n + 1))
        else:
            def name(k):
                other = rows[text].get((r['article'], str(k)))
                return other['name_ar'] if other else None
            target = find_item(entries[text], {page}, n, r['name'])
            anchors = tuple(find_item(entries[text], {page - 1, page, page + 1}, k, name(k)) if name(k) else None
                            for k in (n - 1, n + 1))
        box = region(anchors, target)
        key = reading_id(r)
        if box is None:
            print(f'not located: {key}', file=sys.stderr)
            continue
        crop = f'crops/{key}.png'
        p, x, y, w, h = box
        requests.append({'pdf': os.path.join(ROOT, EDITIONS[text][0]), 'page': p, 'x': x, 'y': y, 'w': w, 'h': h,
                         'out': os.path.join(out, crop), 'dpi': 220})
        manifest.append({'id': key, 'text': text, 'title': TITLES[text], 'article': r['article'],
                         'item': r['item'], 'edition': r['edition'], 'reading': r['name'],
                         'name_fr': row['name_fr'], 'name_ar': row.get('name_ar', ''), 'page': r['pdf_page'],
                         'by': r['by'], 'reviewed_by': r['reviewed_by'], 'note': r['note'], 'crop': crop})
    subprocess.run(['swift', os.path.join(ROOT, 'tools', 'gazette', 'crops.swift')], check=True,
                   input='\n'.join(json.dumps(q) for q in requests) + '\n', text=True)
    with open(os.path.join(out, 'readings.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    print(f'{len(manifest)} of {len(readings)} readings cropped into {out}', file=sys.stderr)


if __name__ == '__main__':
    main()

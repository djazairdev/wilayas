"""Prepare the names read on the rendered page for review: one crop of the printed page per
reading in data/source/readings.csv, and a JSON list describing them.

Each crop shows the item with its neighbours, located from the OCR's positions: the item
itself when the OCR read it, otherwise the space between the items before and after it.

    python3 tools/gazette/review.py OUT_DIR
    # writes OUT_DIR/crops/*.png and OUT_DIR/readings.json

Needs the PDFs in sources/joradp/ and the OCR output in work/ (see README.md).
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
import lists  # noqa: E402

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


def main():
    out = sys.argv[1]
    os.makedirs(os.path.join(out, 'crops'), exist_ok=True)
    readings = read(os.path.join(SOURCE, 'readings.csv'))
    rows, entries, requests, manifest = {}, {}, [], []
    for r in readings:
        text = r['text']
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
        key = '-'.join(re.sub(r'\s+', '-', v) for v in (text, r['article'], r['item'], r['edition']))
        if box is None:
            print(f'not located: {key}', file=sys.stderr)
            continue
        crop = f'crops/{key}.png'
        p, x, y, w, h = box
        requests.append({'pdf': os.path.join(ROOT, EDITIONS[text][0]), 'page': p, 'x': x, 'y': y, 'w': w, 'h': h,
                         'out': os.path.join(out, crop), 'dpi': 220})
        manifest.append({'id': key, 'text': text, 'title': TITLES[text], 'article': r['article'],
                         'item': r['item'], 'edition': r['edition'], 'reading': r['name'],
                         'name_fr': row['name_fr'], 'page': r['pdf_page'], 'by': r['by'], 'note': r['note'],
                         'crop': crop})
    subprocess.run(['swift', os.path.join(ROOT, 'tools', 'gazette', 'crops.swift')], check=True,
                   input='\n'.join(json.dumps(q) for q in requests) + '\n', text=True)
    with open(os.path.join(out, 'readings.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    print(f'{len(manifest)} of {len(readings)} readings cropped into {out}', file=sys.stderr)


if __name__ == '__main__':
    main()

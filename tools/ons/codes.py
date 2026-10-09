"""Build data/source/ons-2021.csv from ONS's code géographique national of June 2021: the code of
each of the 1,541 communes, with its names as printed.

The list has a text layer. Each wilaya has a heading (its name in Arabic, its number, its name in
French), then a row per commune: the French name, the wilaya's number (W.), the commune's number
(C.) and the Arabic name. The Arabic is stored in pieces, some of them run together with the codes,
so the rows are rebuilt from the place of each character (tools/ons/chars.swift): the characters on
one line make a row, its four digits are the code, the letters left of them the French name and
those right of them the Arabic name, read right to left. A gap between two letters is a space.

- French and codes: the PDF's text, which is exact.
- Arabic: the PDF's text, read again by OCR of the whole pages (tools/gazette/ocr.swift) and of
  each row at 400 dpi (tools/gazette/regions.swift). Where an OCR reading has the same letters,
  the PDF's characters are kept, if an OCR reading also puts the spaces in the same places. Any
  other name is read on the rendered page, and data/source/readings.csv records the reading
  (`check` is `eye`). About one name in ten is stored with its letters out of order, which neither
  the characters' places nor their order in the file put right; the OCR's readings of those are
  only a guide to reading them. A name with neither is listed on stderr, and its `check` says why
  it needs reading: `spaces` (the letters agree, the spaces don't), `order` (the OCR's readings
  agree and have the PDF's letters in another order), `differs` or `pdf` (no OCR reading). The
  tests refuse all four.

Every row's wilaya must be its heading's, and the codes must be unique.

    python3 tools/ons/codes.py regions work/ons/2021.chars.jsonl sources/ons/code_geo_2021.pdf ar-SA 400 | swift tools/gazette/regions.swift > work/ons/2021.rows.ocr.jsonl
    python3 tools/ons/codes.py work/ons/2021.chars.jsonl work/ons/2021.ocr.jsonl work/ons/2021.rows.ocr.jsonl > data/source/ons-2021.csv

The first command prints the Arabic part of each row for regions.swift.

Standard library only.
"""
import csv
import json
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
READINGS = os.path.join(ROOT, 'data', 'source', 'readings.csv')
TEXT = 'ons-2021'
FIELDS = ['text', 'wilaya', 'commune', 'name_fr', 'name_ar', 'check']
FOOT = 0.9     # the running foot: "Code Géographique National" and the page number
LINE = 0.006   # characters of one line: their middles are this close (rows are 0.026 apart)
GAP = 0.003    # letters of one word touch; a gap wider than this is a space (spaces measure about 0.009)
NEAR = 0.01    # how far an OCR line's middle may be from its row's
FURNITURE = re.compile(r'suite|Commune')


def load(path):
    with open(path, encoding='utf-8') as f:
        return [json.loads(line) for line in f]


def mid(e):
    return e['y'] + e['h'] / 2


def lines(chars):
    """{page: [[char]]}, the characters of each line, top to bottom. A ligature (lam-alef) comes
    once per character it stands for, with the same box: it is kept once."""
    pages = {}
    for c in chars:
        if mid(c) < FOOT:
            pages.setdefault(c['page'], []).append(c)
    out = {}
    for page, cs in sorted(pages.items()):
        seen, rows = set(), []
        for c in sorted(cs, key=lambda c: (mid(c), c['i'])):
            key = (c['x'], c['y'], c['w'], c['h'], c['c'])
            if key in seen:
                continue
            seen.add(key)
            if rows and mid(c) - rows[-1][-1] < LINE:
                rows[-1][0].append(c)
                rows[-1][1] = mid(c)
            else:
                rows.append([[c], mid(c)])
        out[page] = [r for r, _ in rows]
    return out


def word(chars, rtl):
    """The text of some characters on one line, with a space at each gap."""
    cs = sorted(chars, key=lambda c: (-c['x'], c['i']) if rtl else (c['x'], c['i']))
    out = ''
    for a, b in zip([None] + cs, cs):
        if a is not None:
            gap = a['x'] - (b['x'] + b['w']) if rtl else b['x'] - (a['x'] + a['w'])
            if gap > GAP:
                out += ' '
        out += b['c']
    return unicodedata.normalize('NFC', out).replace('ـ', '').strip()


def parse(chars):
    """[{'wilaya', 'commune', 'fr', 'ar', 'page', 'y', 'x0'}], in the order of the list; raises
    unless every row's wilaya is its heading's."""
    rows, wilaya = [], None
    for page, page_lines in lines(chars).items():
        for line in page_lines:
            text = ''.join(c['c'] for c in sorted(line, key=lambda c: c['x']))
            digits = [c for c in sorted(line, key=lambda c: c['x']) if c['c'].isdigit()]
            if FURNITURE.search(text):
                continue
            if len(digits) in (1, 2):
                wilaya = ''.join(c['c'] for c in digits)
                continue
            if len(digits) != 4:
                continue  # the second line of a heading
            code = ''.join(c['c'] for c in digits)
            if code[:2] != wilaya:
                raise SystemExit(f'page {page}: {code} under the heading of wilaya {wilaya}')
            left, right = digits[0]['x'], digits[-1]['x'] + digits[-1]['w']
            ar = [c for c in line if not c['c'].isdigit() and c['x'] >= right]
            rows.append({'wilaya': code[:2], 'commune': code[2:], 'page': page, 'y': min(c['y'] for c in line),
                         'h': max(c['y'] + c['h'] for c in line) - min(c['y'] for c in line),
                         'x0': min((c['x'] for c in ar), default=right),
                         'fr': word([c for c in line if not c['c'].isdigit() and c['x'] < left], False),
                         'ar': word(ar, True)})
    codes = [r['wilaya'] + r['commune'] for r in rows]
    if len(set(codes)) != len(codes):
        raise SystemExit('a code is printed twice')
    return rows


def regions(chars_path, pdf, lang, dpi):
    """Print the Arabic part of each row, with a little room around it, for regions.swift."""
    for r in parse(load(chars_path)):
        print(json.dumps({'pdf': pdf, 'page': r['page'], 'x': r['x0'] - 0.02, 'y': r['y'] - 0.004,
                          'w': 0.98 - r['x0'], 'h': r['h'] + 0.008, 'dpi': dpi, 'lang': lang}))


def arabic_only(text):
    """An OCR line without the codes and the French it may have run into."""
    return re.sub(r'\s+', ' ', re.sub(r'[0-9A-Za-z\'’.()|-]+', ' ', text)).strip()


def letters(s):
    """The letters of a name, without its spaces, punctuation or vowel marks (the OCR adds a shadda
    and a small alif to "الله")."""
    return re.sub(r'[\s.,،:;!"“”«»()\u064b-\u065f\u0670]+', '', unicodedata.normalize('NFC', s).replace('ـ', ''))


def words(s):
    return [letters(w) for w in s.split() if letters(w)]


def ocr_readings(rows, sources):
    """{index of row: [OCR reading]}: for each OCR source, the text of its lines whose middle is the
    row's, right to left, or None."""
    out = {i: [None] * len(sources) for i in range(len(rows))}
    for n, ocr in enumerate(sources):
        found = {}
        for o in ocr:
            text = arabic_only(o['text'])
            if not text or o['x'] + o['w'] < 0.5:
                continue
            for i, r in enumerate(rows):
                if r['page'] == o['page'] and abs(mid(o) - (r['y'] + r['h'] / 2)) < NEAR:
                    found.setdefault(i, []).append((o['x'], text))
        for i, parts in found.items():
            out[i][n] = ' '.join(t for _, t in sorted(parts, reverse=True))
    return out


def check_arabic(pdf, ocr):
    """(name, check): the PDF's text, '' when an OCR reading has the same letters and the same
    spaces. Otherwise the best reading there is and why the name must be read on the page: the
    PDF's text when it has the same letters as an OCR reading, which only places a space
    differently (`spaces`); the OCR's text when every OCR reading agrees and has exactly the PDF's
    letters in another order (`order`); else the PDF's text, `differs` or `pdf` (no OCR reading)."""
    found = [o for o in ocr if o]
    if any(words(o) == words(pdf) for o in found):
        return pdf, ''
    if any(letters(o) == letters(pdf) for o in found):
        return pdf, 'spaces'
    if len(found) == len(ocr) and len(set(found)) == 1 and sorted(letters(found[0])) == sorted(letters(pdf)):
        return found[0], 'order'
    return pdf, ('differs' if found else 'pdf')


def readings(path=READINGS):
    """{(wilaya, commune, edition): name} read on the rendered page."""
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8', newline='') as f:
        return {(r['article'], r['item'], r['edition']): r['name'] for r in csv.DictReader(f) if r['text'] == TEXT}


def main():
    if sys.argv[1:2] == ['regions']:
        regions(*sys.argv[2:5], int(sys.argv[5]))
        return
    chars_path, ocr_path, rows_ocr_path = sys.argv[1:4]
    rows = parse(load(chars_path))
    found = ocr_readings(rows, [load(ocr_path), load(rows_ocr_path)])
    read = readings()
    out = csv.DictWriter(sys.stdout, FIELDS, lineterminator='\n')
    out.writeheader()
    waiting = 0
    for i, r in enumerate(rows):
        name, check = check_arabic(r['ar'], found[i])
        if (r['wilaya'], r['commune'], 'ar') in read:
            name, check = read[(r['wilaya'], r['commune'], 'ar')], 'eye'
        elif check:
            waiting += 1
            print(f"{r['wilaya']}{r['commune']} p{r['page']} {r['fr']}: pdf {name!r} ocr {found[i]}", file=sys.stderr)
        out.writerow({'text': TEXT, 'wilaya': r['wilaya'], 'commune': r['commune'], 'name_fr': r['fr'],
                      'name_ar': name, 'check': check})
    print(f'{len(rows)} communes, {waiting} Arabic names to read on the page', file=sys.stderr)


if __name__ == '__main__':
    main()

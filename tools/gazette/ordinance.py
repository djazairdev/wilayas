"""Build data/source/ordinance-97-14.csv from Ordinance 97-14 of 31 May 1997 on the territorial
organisation of the wilaya of Algiers: the communes it detaches from Boumerdès (article 2),
Tipaza (article 3) and Blida (article 4), which article 5 attaches to Algiers.

Both editions of JO n° 38 of 1997 are scans. The names are in the text of the articles, not in
lists: "Les communes de A, B, … et Z sont détachées de la wilaya de W" and "تفصل بلديات A وB …
وZ عن ولاية W". Each edition is read by OCR twice, the whole page (tools/gazette/ocr.swift) and
the articles again at 400 dpi (tools/gazette/regions.swift). As for Decree 91-306
(tools/gazette/annex.py), a name is taken from the OCR when both readings agree and it is the
label of a commune in Wikidata, an independent second reading; any other name is read on the
rendered page, and data/source/readings.csv records the reading. A name with neither is listed
on stderr and gets the check `ocr`, which the tests refuse. Both editions must give the same
number of communes in each article.

The Arabic is transcribed without harakat, as Decree 91-306 is: the shadda the print puts on
some names is left out.

    python3 tools/gazette/ordinance.py regions | swift tools/gazette/regions.swift > work/1997038.articles.ocr.jsonl
    python3 tools/gazette/ordinance.py work/F1997038.ocr.jsonl work/A1997038.ocr.jsonl work/1997038.articles.ocr.jsonl work/wikidata-labels.json > data/source/ordinance-97-14.csv

The first command prints the parts of the pages that hold articles 2 to 4, for regions.swift.

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
TEXT = 'ordinance-97-14'
FIELDS = ['text', 'article', 'item', 'name_fr', 'name_ar', 'check']
ARTICLES = ['2', '3', '4']
# The parts of the pages that hold articles 2 to 4 (fractions of the page, y from the top)
REGIONS = {
    'fr': [('sources/joradp/F1997038.pdf', 4, 0.5, 0.835, 0.47, 0.145), ('sources/joradp/F1997038.pdf', 5, 0.02, 0.07, 0.47, 0.06)],
    'ar': [('sources/joradp/A1997038.pdf', 5, 0.03, 0.415, 0.47, 0.24)],
}
LANG = {'fr': 'fr-FR', 'ar': 'ar-SA'}
LINE = 0.008  # OCR boxes whose tops are this close are on one line
# An article's number, where the OCR read it, and its names
PATTERN = {
    'fr': re.compile(r'Art\.(?: (\d)\.)? ?\W* Les communes de (.+?) sont détachées de la wilaya'),
    'ar': re.compile(r'(\d)? ?: ?تفصل بل\S*ات (.+?) عن ولاية'),
}
HARAKAT = re.compile('[ً-ٰٟ]')


def load(path):
    with open(path, encoding='utf-8') as f:
        return [json.loads(line) for line in f]


def text(ocr, edition):
    """The text of an edition's articles 2 to 4, from one OCR reading: its lines in reading order,
    each line's boxes right to left in Arabic."""
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
            out += [o['text'] for o in sorted(row, key=lambda o: -o['x'] if edition == 'ar' else o['x'])]
    return re.sub(r'\s+', ' ', ' '.join(out))


def names(ocr, edition):
    """{article: [name]} from one OCR reading of an edition. The articles come in order; the OCR
    sometimes misses an article's number, but must not read another."""
    found = {}
    matches = PATTERN[edition].findall(text(ocr, edition))
    if len(matches) != len(ARTICLES):
        raise SystemExit(f'{edition}: {len(matches)} articles found')
    for article, (number, names) in zip(ARTICLES, matches):
        if number and number != article:
            raise SystemExit(f'{edition}: article {number} where {article} should be')
        if edition == 'fr':
            parts = re.split(r', | et ', names)
        else:
            parts = re.split(r' و(?=\S)', HARAKAT.sub('', names))
        found[article] = [clean(p, edition) for p in parts]
    return found


def readings(path=READINGS):
    """{(article, item, edition): name} read on the rendered page."""
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8', newline='') as f:
        return {(r['article'], r['item'], r['edition']): r['name'] for r in csv.DictReader(f) if r['text'] == TEXT}


def main():
    if sys.argv[1:2] == ['regions']:
        for edition, regions in REGIONS.items():
            for pdf, page, x, y, w, h in regions:
                print(json.dumps({'pdf': pdf, 'page': page, 'x': x, 'y': y, 'w': w, 'h': h, 'dpi': 400, 'lang': LANG[edition]}))
        return
    fr_page, ar_page, articles_path, labels_path = sys.argv[1:5]
    articles = load(articles_path)
    found = {e: [names(load(path), e), names(articles, e)] for e, path in (('fr', fr_page), ('ar', ar_page))}
    known, read = known_names(labels_path), readings()
    out = csv.DictWriter(sys.stdout, FIELDS, lineterminator='\n')
    out.writeheader()
    waiting = 0
    for article in ARTICLES:
        counts = {len(found[e][n][article]) for e in ('fr', 'ar') for n in (0, 1)}
        if len(counts) != 1:
            raise SystemExit(f'article {article}: the readings give {sorted(counts)} communes')
        for i in range(counts.pop()):
            row, eye, unread = {'text': TEXT, 'article': article, 'item': str(i + 1)}, False, False
            for e in ('fr', 'ar'):
                page, region = found[e][0][article][i], found[e][1][article][i]
                row['name_' + e] = page
                if (article, row['item'], e) in read:
                    row['name_' + e], eye = read[(article, row['item'], e)], True
                elif page != region or page not in known[e]:
                    waiting, unread = waiting + 1, True
                    print(f"{article}/{row['item']} {e}: page {page!r} articles {region!r}"
                          f"{'' if page in known[e] else ', not a Wikidata label'}", file=sys.stderr)
            row['check'] = 'ocr' if unread else 'eye' if eye else ''
            out.writerow(row)
    print(f'{waiting} names to read on the page', file=sys.stderr)


if __name__ == '__main__':
    main()

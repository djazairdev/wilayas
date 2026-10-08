"""Build data/source/executive-decree-91-306.csv from the tables of Executive Decree 91-306
(1991): for each wilaya, its daïras, each with its seat and the communes its chef de daïra runs.

Both editions are scans. tools/gazette/dairas.py reads each edition's tables from OCR; this
pairs them row by row (the editions print the same tables in the same order, but for the
misprints in GAPS) and checks each name. The page is read by OCR several ways (see dairas.py);
where every reading agrees and is the label of a commune in Wikidata (tools/gazette/wikidata.py),
an independent second reading agrees with it. Wikidata's aliases don't count: they hold the
spellings without hamzas or accents that the OCR's own mistakes produce. Any other name is read
on the rendered page, and data/source/readings.csv records the reading. A name with neither is
listed on stderr and gets the check `ocr`, which the tests refuse.

The French seats are printed in capitals without accents ("BENI MAOUCHE" for Béni Maouche), so
they are compared with the labels in capitals without accents. The French apostrophe is printed
curly; the OCR reads it ', and we write ’.

    python3 tools/gazette/annex.py work/F1991041.rows.jsonl work/A1991041.rows.jsonl work/wikidata-labels.json > data/source/executive-decree-91-306.csv

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
TEXT = 'executive-decree-91-306'
FIELDS = ['text', 'wilaya', 'daira', 'item', 'name_fr', 'name_ar', 'check']
# Entries one edition prints and the other doesn't: (wilaya, daïra, item) -> the edition without it
GAPS = {
    (18, 10, 3): 'fr',  # the Arabic prints Boudria Beniyadjis as two communes, بودريعة and بني ياجيس
    (30, 10, 2): 'fr',  # the French leaves out Rouissat (الرويسات)
    (34, 3, 4): 'fr',   # the Arabic also lists Tixter under Ras El Oued, as تكستين
}


def clean(text, language):
    """A name as the OCR read it, without the dash before an Arabic commune or stray marks."""
    text = unicodedata.normalize('NFC', text).replace('ـ', '')
    text = re.sub(r'^[\s\-–—_.•·،,:;"/]+|[\s\-–—_.•·،,:;"/]+$', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.replace("'", '’') if language == 'fr' else text


def capitals(text):
    """A French name as the seats are printed: in capitals, without accents."""
    text = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in text if not unicodedata.combining(c)).upper()


def known_names(path):
    """{'fr': names, 'fr seat': names in capitals, 'ar': names} from Wikidata's labels."""
    with open(path, encoding='utf-8') as f:
        bindings = json.load(f)['results']['bindings']
    out = {'fr': set(), 'fr seat': set(), 'ar': set()}
    for b in bindings:
        if b['kind']['value'] != 'label':
            continue
        language, name = b['lang']['value'], clean(b['label']['value'], b['lang']['value'])
        out[language].add(name)
        if language == 'fr':
            out['fr seat'].add(capitals(name))
    return out


def readings(path=READINGS):
    """{(wilaya, 'daïra/item', edition): name} read on the rendered page."""
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8', newline='') as f:
        return {(r['article'], r['item'], r['edition']): r['name'] for r in csv.DictReader(f) if r['text'] == TEXT}


def load(path):
    """{wilaya: [rows]} from dairas.py, in the order of the annex."""
    out = {}
    with open(path, encoding='utf-8') as f:
        for r in map(json.loads, f):
            out.setdefault(r['wilaya'], []).append(r)
    return out


def names(row, language):
    """(seat line, [commune lines]): the seat's lines joined into one."""
    lines = row['seat']
    x0, y0 = min(e['x'] for e in lines), min(e['y'] for e in lines)
    seat = {'page': lines[0]['page'], 'x': x0, 'y': y0,
            'w': max(e['x'] + e['w'] for e in lines) - x0, 'h': max(e['y'] + e['h'] for e in lines) - y0,
            'text': ' '.join(e['text'] for e in lines),
            'alt': [' '.join(alts) for alts in zip(*[e.get('alt', [e['text']]) for e in lines])]}
    return seat, row['communes']


def entries(fr, ar):
    """[(wilaya, daïra, item, fr line, ar line)], item 'seat' first in each daïra; raises on any
    difference between the editions' tables but GAPS."""
    if sorted(fr) != sorted(ar):
        raise SystemExit(f'the editions have different wilayas: {sorted(fr)} and {sorted(ar)}')
    out = []
    for w in sorted(fr):
        if len(fr[w]) != len(ar[w]):
            raise SystemExit(f'wilaya {w:02d}: {len(fr[w])} daïras in French, {len(ar[w])} in Arabic')
        for d, (f, a) in enumerate(zip(fr[w], ar[w]), 1):
            (fs, fc), (as_, ac) = names(f, 'fr'), names(a, 'ar')
            fc, ac = list(fc), list(ac)
            for (gw, gd, gi), edition in sorted(GAPS.items()):
                if (gw, gd) == (w, d):
                    (fc if edition == 'fr' else ac).insert(gi - 1, None)
            if len(fc) != len(ac):
                raise SystemExit(f'wilaya {w:02d}, daïra {d}: {len(fc)} communes in French, {len(ac)} in Arabic')
            out.append((w, d, 'seat', fs, as_))
            out += [(w, d, str(i), x, y) for i, (x, y) in enumerate(zip(fc, ac), 1)]
    return out


def check(line, language, seat, known):
    """The name if every OCR reading of it is the same known name, else None."""
    if line is None:
        return ''
    found = {clean(t, language) for t in [line['text']] + line.get('alt', [])}
    name = found.pop()
    return name if not found and name in known['fr seat' if language == 'fr' and seat else language] else None


def main():
    fr, ar = load(sys.argv[1]), load(sys.argv[2])
    known, seen = known_names(sys.argv[3]), readings()
    w = csv.DictWriter(sys.stdout, FIELDS, lineterminator='\n')
    w.writeheader()
    todo = 0
    for wilaya, daira, item, f, a in entries(fr, ar):
        key = (f'{wilaya:02d}', f'{daira}/{item}')
        row = {'text': TEXT, 'wilaya': key[0], 'daira': daira, 'item': item}
        checks = []
        for language, line in (('fr', f), ('ar', a)):
            read = seen.get(key + (language,))
            name = check(line, language, item == 'seat', known)
            if read is not None:
                name, how = read, 'eye'
            elif name is not None:
                how = ''
            else:
                name, how = clean(line['text'], language), 'ocr'
                todo += 1
                print(f'to read: {key[0]} {key[1]} {language} p{line["page"]}: {name!r} '
                      f'(also {sorted({clean(t, language) for t in line.get("alt", [])} - {name})})', file=sys.stderr)
            row['name_' + language] = name
            checks.append(how)
        row['check'] = 'ocr' if 'ocr' in checks else 'eye' if 'eye' in checks else ''
        w.writerow(row)
    if todo:
        print(f'{todo} names to read', file=sys.stderr)


if __name__ == '__main__':
    main()

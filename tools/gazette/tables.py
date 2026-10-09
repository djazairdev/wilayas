"""Build data/source/executive-decree-26-253.csv from the annex of Executive Decree 26-253
(2026). The decree rewrites the daïra tables of Decree 91-306 for the 21 wilayas Law 26-06
touched; the annex says "sans changement" for the others.

Both editions of JO n° 52 of 2026 have a text layer. As in 1991, each wilaya has a table: a row
per daïra, the band between two rules (tools/gazette/rules.swift), with the seat in the outer
sub-column and the communes in the inner one, each after a dash. runs.swift gives the text and
its place on the page.

- French: the PDF's text, which is exact.
- Arabic: the PDF's text is drawn right but stored in display order (tools/gazette/lists.py
  turns it back), and here and there its lines are scrambled. It is read again by OCR, of the
  whole pages (ocr.swift) and of each band at 400 dpi (regions.swift). The PDF's runs and the
  OCR's lines are placed in the same bands and grouped by line; a line that starts with a dash
  in either reading starts a commune. Where the PDF's text and an OCR reading have the same
  letters, the PDF's characters are kept. Any other name is read on the rendered page, and
  data/source/readings.csv records the reading (`check` is `eye`). A name with neither is listed
  on stderr, and its `check` says why it needs reading: `spaces` (the letters agree, the spaces
  don't), `differs`, `pdf` (no OCR reading) or `ocr` (no text in the PDF). The tests refuse all
  four.

The Arabic text layer garbles the wilaya headings, so the Arabic tables take their wilaya
numbers from the OCR's headings. The editions must give the same wilayas, the same number of
daïras in each and the same number of communes in each daïra.

    python3 tools/gazette/tables.py regions work/A2026052.runs.jsonl work/A2026052.rules.jsonl sources/joradp/A2026052.pdf ar-SA 400 | swift tools/gazette/regions.swift > work/A2026052.bands.ocr.jsonl
    python3 tools/gazette/tables.py work/F2026052.runs.jsonl work/F2026052.rules.jsonl work/A2026052.runs.jsonl work/A2026052.rules.jsonl work/A2026052.ocr.jsonl work/A2026052.bands.ocr.jsonl > data/source/executive-decree-26-253.csv

The first command prints the bands of the annex's pages for regions.swift.

Standard library only.
"""
import csv
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lists  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
READINGS = os.path.join(ROOT, 'data', 'source', 'readings.csv')
TEXT = 'executive-decree-26-253'
FIELDS = ['text', 'wilaya', 'daira', 'item', 'name_fr', 'name_ar', 'check']
HEAD = 0.06       # the running head
MIN_BAND = 0.012  # thinner bands are a rule drawn twice
LINE = 0.009      # parts of one line: their middles are this close (lines are about 0.026 apart)
SLACK = 0.005     # how far a part may stray past the edge between the sub-columns
TALL = 0.03       # a run of the Arabic text taller than this (a line is 0.02) is several lines scrambled into one
DASH = re.compile(r'^\s*[-–—]\s*')
FR_HEADING = re.compile(r'^(\d{1,2})\s*[-–—]\s*WILAYA\b')
AR_HEADING = re.compile(r'^(\d{1,2})\s*[-–—]\s*ولاية')
# The next text in the issue, after the last table
END = re.compile(r'^\s*(Décret (exécutif|présidentiel)|مرسوم (تنفيذي|رئاسي))')
# A band of an undashed table that isn't a row: the column heads, or a note on the wilayas left alone
FURNITURE = re.compile(r'Sièges|Sans changement')
SEAT_GAP = 0.05   # in an undashed table, the communes start at least this far right of the seats


def load(path):
    with open(path, encoding='utf-8') as f:
        return [json.loads(line) for line in f]


def side(e):
    return 'right' if e['x'] + e['w'] / 2 >= 0.5 else 'left'


def mid(e):
    return e['y'] + e['h'] / 2


def bands(rules, page, where):
    """The bands between the rules of one half-page column, top to bottom, with one band above
    the first rule and one below the last."""
    ys = sorted(r['y'] for r in rules if r['page'] == page and r['side'] == where)
    ys = [0.0] + ys + [1.0]
    return [(a, b) for a, b in zip(ys, ys[1:]) if b - a > MIN_BAND]


def clean(text):
    """A name without its dash, with single spaces."""
    text = unicodedata.normalize('NFC', DASH.sub('', text)).replace('ـ', '')
    return re.sub(r'\s+', ' ', text).strip()


def by_line(parts):
    """Group parts into lines, top to bottom, by the middles of their heights."""
    out = []
    for p in sorted(parts, key=mid):
        if out and mid(p) - sum(map(mid, out[-1])) / len(out[-1]) < LINE:
            out[-1].append(p)
        else:
            out.append([p])
    return out


def name(parts, sources, rtl):
    """{source: text} of one name from its parts, line after line, each line in reading order."""
    out = {}
    for src in sources:
        lines = by_line([p for p in parts if p['src'] == src])
        text = ' '.join(' '.join(p['text'] for p in sorted(line, key=lambda p: -p['x'] if rtl else p['x']))
                        for line in lines)
        out[src] = clean(text) if lines else None
    return out


def tables(parts, rules, rtl, sources, headings, dashed=True):
    """{wilaya: [{'seat': name, 'communes': [name]}]} in the order of the annex, each name
    {'text': {source: text}, 'page', 'side', 'x', 'y', 'w', 'h'}, with its box on the page. parts are
    the PDF's runs (source 'pdf') and, for the Arabic, the OCR's lines (source: the pass, 0, 1, ...),
    all placed on the page.

    headings(page, side, top, bottom) gives the wilaya number a band announces, if any. A band
    with a heading is never a row: above the first one stands the decree's own text, whose
    Arabic clauses start with a dash too.

    Where the names have no dashes (dashed is False: the French of Decree 21-198), each line is a
    name and the communes are the parts that start right of the seat's sub-column. The tables
    end with the next text in the issue."""
    out, current = {}, None
    pages = sorted({p['page'] for p in parts if p['src'] == 'pdf'})

    def entry(group, page, where):
        left, top = min(p['x'] for p in group), min(p['y'] for p in group)
        return {'text': name(group, sources, rtl), 'page': page, 'side': where, 'x': left, 'y': top,
                'w': max(p['x'] + p['w'] for p in group) - left, 'h': max(p['y'] + p['h'] for p in group) - top}

    for page in pages:
        for where in (('right', 'left') if rtl else ('left', 'right')):
            column = [p for p in parts if p['page'] == page and side(p) == where and p['y'] >= HEAD]
            for top, bottom in bands(rules, page, where):
                inside = [p for p in column if top <= mid(p) < bottom]
                if any(END.match(p['text']) for p in inside):
                    current = None
                    continue
                number = headings(page, where, top, bottom)
                if number is not None:
                    current = number
                    out.setdefault(current, [])
                    continue
                if not dashed:
                    if current is None or not inside or FURNITURE.search(' '.join(p['text'] for p in inside)):
                        continue
                    first = min(p['x'] for p in inside)
                    edge = min((p['x'] for p in inside if p['x'] > first + SEAT_GAP), default=None)
                    if edge is None:
                        raise SystemExit(f'page {page} {where}, band {top:.3f}: no communes beside the seat')
                    seat = [p for p in inside if p['x'] < edge]
                    communes = by_line([p for p in inside if p['x'] >= edge])
                    out[current].append({'seat': entry(seat, page, where), 'communes': [entry(n, page, where) for n in communes]})
                    continue
                dashes = [p for p in inside if DASH.match(p['text'])]
                if current is None or not dashes:
                    continue
                # The seat stands in the outer sub-column, the communes in the inner one, aligned on
                # their dashes. The PDF's runs place the edge best; the OCR's boxes are looser.
                ref = [p for p in dashes if p['src'] == 'pdf'] or dashes
                if rtl:
                    edge = max(p['x'] + p['w'] for p in ref)
                    seat = [p for p in inside if p['x'] >= edge - SLACK]
                    communes = [p for p in inside if p['x'] + p['w'] <= edge + SLACK]
                else:
                    edge = min(p['x'] for p in ref)
                    seat = [p for p in inside if p['x'] + p['w'] <= edge + SLACK]
                    communes = [p for p in inside if p['x'] >= edge - SLACK]
                # a part that straddles the edge belongs to neither: an OCR line run over both
                names = []
                for line in by_line(communes):
                    if any(DASH.match(p['text']) for p in line) or not names:
                        names.append(list(line))
                    else:  # a name that runs onto a second line
                        names[-1] += line
                empty = {'text': {}, 'page': page, 'side': where, 'x': 0.5 if where == 'right' else 0.0, 'y': top,
                         'w': 0.5, 'h': bottom - top}
                out[current].append({'seat': entry(seat, page, where) if seat else empty,
                                     'communes': [entry(n, page, where) for n in names]})
    return out


def french(runs_path, rules_path):
    runs = [dict(r, src='pdf') for r in load(runs_path)]

    def headings(page, where, top, bottom):
        for r in runs:
            if r['page'] == page and side(r) == where and top <= mid(r) < bottom:
                m = FR_HEADING.match(r['text'])
                if m:
                    return f'{int(m.group(1)):02d}'
        return None
    # Decree 26-253 puts a dash before each commune; Decree 21-198's French puts none
    dashed = any(re.match(r'^\s*[-–—]\s*\w', r['text']) for r in runs)
    return tables(runs, load(rules_path), False, ['pdf'], headings, dashed)


def arabic(runs_path, rules_path, ocr_paths):
    parts = [dict(r, text=lists.arabic(r['text']), src='pdf') for r in load(runs_path) if r['h'] <= TALL]
    ocr = [dict(e, src=i) for i, p in enumerate(ocr_paths) for e in load(p)]

    def headings(page, where, top, bottom):
        for e in ocr:
            if e['page'] == page and side(e) == where and top <= mid(e) < bottom:
                m = AR_HEADING.match(e['text'].strip())
                if m:
                    return f'{int(m.group(1)):02d}'
        return None
    return tables(parts + ocr, load(rules_path), True, ['pdf'] + list(range(len(ocr_paths))), headings)


def letters(s):
    return re.sub(r'[\s.,،:;!"“”«»()]+', '', s)


def check_arabic(text):
    """(name, check): the PDF's text, '' when an OCR reading has the same letters and the same
    spaces; otherwise the best reading there is and why the name must be read on the page. Neither
    reading's spaces can be trusted: Decree 21-198's text layer puts spaces inside words ("س يدي
    عون"), and the OCR often puts one after a letter that doesn't join the next ("أو لاد")."""
    pdf, ocr = text.get('pdf'), [v for k, v in text.items() if k != 'pdf' and v]
    if pdf and any(o.split() == pdf.split() for o in ocr):
        return pdf, ''
    if pdf and any(letters(o) == letters(pdf) for o in ocr):
        return pdf, 'spaces'
    if not pdf:
        return (ocr[0] if ocr else ''), 'ocr'
    return pdf, ('differs' if ocr else 'pdf')


def readings(path=READINGS):
    """{(wilaya, 'daïra/item', edition): name} read on the rendered page."""
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8', newline='') as f:
        return {(r['article'], r['item'], r['edition']): r['name'] for r in csv.DictReader(f) if r['text'] == TEXT}


def regions(runs_path, rules_path, pdf, lang, dpi):
    """Print each band of the pages the runs cover, both half-page columns, for regions.swift."""
    runs, rules = load(runs_path), load(rules_path)
    for page in sorted({r['page'] for r in runs}):
        for where, x0 in (('right', 0.5), ('left', 0.0)):
            for top, bottom in bands(rules, page, where):
                top = max(top, HEAD)
                if bottom - top > MIN_BAND:
                    print(json.dumps({'pdf': pdf, 'page': page, 'x': x0, 'y': top, 'w': 0.5, 'h': bottom - top,
                                      'dpi': dpi, 'lang': lang}))


def entries(fr, ar):
    """[(wilaya, daïra, item, French name, Arabic name)], item 'seat' first in each daïra; raises
    on any difference between the editions' tables."""
    if list(fr) != list(ar):
        raise SystemExit(f'the editions give different wilayas:\n  fr {list(fr)}\n  ar {list(ar)}')
    out = []
    for wilaya in fr:
        if len(fr[wilaya]) != len(ar[wilaya]):
            raise SystemExit(f'wilaya {wilaya}: {len(fr[wilaya])} daïras in French, {len(ar[wilaya])} in Arabic')
        for d, (f, a) in enumerate(zip(fr[wilaya], ar[wilaya]), 1):
            if len(f['communes']) != len(a['communes']):
                raise SystemExit(f"wilaya {wilaya}, daïra {d} ({f['seat']['text'].get('pdf')}): {len(f['communes'])} "
                                 f"communes in French, {len(a['communes'])} in Arabic")
            out.append((wilaya, d, 'seat', f['seat'], a['seat']))
            out += [(wilaya, d, str(i), x, y) for i, (x, y) in enumerate(zip(f['communes'], a['communes']), 1)]
    return out


def main():
    global TEXT
    if sys.argv[1] == '--text':  # another decree laid out the same way
        TEXT = sys.argv[2]
        del sys.argv[1:3]
    if sys.argv[1] == 'regions':
        runs_path, rules_path, pdf, lang, *dpi = sys.argv[2:]
        regions(runs_path, rules_path, pdf, lang, int(dpi[0]) if dpi else 400)
        return
    fr_runs, fr_rules, ar_runs, ar_rules, *ocr_paths = sys.argv[1:]
    rows = entries(french(fr_runs, fr_rules), arabic(ar_runs, ar_rules, ocr_paths))
    seen = readings()
    w = csv.DictWriter(sys.stdout, FIELDS, lineterminator='\n')
    w.writeheader()
    todo = 0
    for wilaya, d, item, f, a in rows:
        key = (wilaya, f'{d}/{item}')
        name_fr = f['text'].get('pdf') or ''
        read = seen.get(key + ('ar',))
        if read is not None:
            name_ar, check = read, 'eye'
        else:
            name_ar, check = check_arabic(a['text'])
            if check:
                todo += 1
                print(f"to read: {wilaya} {d}/{item} p{a['page']}: {a['text']} (French {name_fr!r})", file=sys.stderr)
        w.writerow({'text': TEXT, 'wilaya': wilaya, 'daira': d, 'item': item,
                    'name_fr': name_fr, 'name_ar': name_ar, 'check': check})
    if todo:
        print(f'{todo} names to read', file=sys.stderr)


if __name__ == '__main__':
    main()

"""Read the annex of Executive Decree 91-306 (1991): for each wilaya, a table of daïras,
each with its seat (siège, المقر) and the communes its chef de daïra runs.

Both editions of JO n° 41 of 1991 are scans, so the text comes from OCR
(tools/gazette/ocr.swift) and the tables' rules from the page images
(tools/gazette/rules.swift). The OCR of a whole page loses a line here and there, and so do
the OCR of each column on its own and the OCR of each row of a table, but rarely the same line:
the lines of the first OCR are completed with the lines of the others that overlap none of them.
A line read more than once keeps the other readings too, in `alt`.

Each page holds two half-page columns; each column holds wilaya headings
("03 - WILAYA DE LAGHOUAT", "03 - ولاية الأغواط") and tables. A row of a table is the band
between two rules: the seat on the outer side of the column, the communes on the inner side,
one per line ("- فنوغيل" in Arabic).

    python3 tools/gazette/dairas.py fr work/F1991041.rules.jsonl work/F1991041.rows.jsonl work/F1991041.ocr.jsonl work/F1991041.columns.ocr.jsonl work/F1991041.rows.ocr.jsonl work/F1991041.rows400.ocr.jsonl
    python3 tools/gazette/dairas.py ar work/A1991041.rules.jsonl work/A1991041.rows.jsonl work/A1991041.ocr.jsonl work/A1991041.columns.ocr.jsonl work/A1991041.rows.ocr.jsonl work/A1991041.rows400.ocr.jsonl

writes the rows to the third file named, prints a summary per wilaya, and lists on stderr the
rows that need a look on the page. Decree 92-66, a scan laid out the same way, takes the pages of
its tables first: `--pages 17 18 fr ...`. tools/gazette/README.md has the commands that make the OCR
files. Standard library only.
"""
import bisect
import difflib
import json
import re
import statistics
import sys
import unicodedata

HEAD = 0.05  # the running head (page number, title, date) is centred above this
END = re.compile(r'DECISIONS\s+INDIVIDUELLES|مراسيم\s+فردية')
# The line that closes an amending decree's tables (Decree 92-66). It ends a column, not the page:
# what follows it in reading order is the column after it.
AMENDED_END = re.compile(r'reste\s+sans\s+changement|الباقي\s+بدون\s+تغيير')
# "03 - WILAYA DE LAGHOUAT", "02 — WILAYADE CHLEF (Suite)", "32 - EL BAYADH", or just "42 -" at the
# top of a column, where the OCR lost the rest of the heading
FR_WILAYA = re.compile(r'^([0-9]{1,2})\s*[-—–]+\s*(?:WILAYA\s*D|[A-Z]{2})|^([0-9]{1,2})\s*[-—–]?\s*$'
                       r'|^([0-9]{1,2})\s*[-—–]*\s*Wilaya\s+d')  # Decree 92-66: "04 Wilaya d'Oum El Bouaghi"
# "03 - ولاية الأغواط", "10 - البويرة", "38 ولاية تيسمسيلت", "/ 30 - ولاية ورقلة", in Western digits:
# the OCR reads the odd dash as "١٠"
AR_WILAYA = re.compile(r'^\W*([0-9]{1,2})\s*(?:[-—–.]+\s*\.?\s*(?:ولاية\s*)?[ء-ي]|ولاية)')
# The tables' column headings as the OCR reads them ("chet de daira concerné", "دئرة ى"), the
# rest of a heading whose number the OCR read as a line of its own, page numbers and dates
FR_SKIP = re.compile(r"Si[eè]ge'?s|Communes?\s+à\s+animer|Communes?\s+animées|^de\s+da[iï]ra\s+concern|che[ft]\s+de\s+da[iï]ra|WILAYA\s*D|^\d+$", re.I)
AR_SKIP = re.compile(r'ينشط|كل\s+رئيس|دا?ئرة\W*\s*م?[عغ]ن|^دا?ئ?رة\s+\S{2,4}$|^د[ئا]?رة\b|^ال?مق[ـ]*ا?ر\b|صفر\s+عام|ولاية|تابع|^\d+$|^\W*$')
DASH = re.compile(r'^\W*[-–]')


def read(paths, first, last, language, amending=False):
    """The OCR lines of the annex: none from the running heads, or from the individual decisions
    that follow it on its last page (their heading spans both columns, so only the OCR of the whole
    page reads it). Lines from the later files complete those of the first."""
    def load(path):
        with open(path, encoding='utf-8') as f:
            return [e for e in map(json.loads, f) if first <= e['page'] <= last and e['y'] + e['h'] / 2 >= HEAD]
    lines = load(paths[0])
    if amending:
        def order(e):  # (page, column in reading order, y)
            left = e['x'] + e['w'] / 2 < 0.5
            return (e['page'], int(left if language == 'ar' else not left), e['y'])
        end = min((order(e) for e in lines if AMENDED_END.search(e['text'])), default=(last + 1, 0, 0.0))
    else:
        def order(e):
            return (e['page'], e['y'])
        end = min((order(e) for e in lines if END.search(e['text'])), default=(last + 1, 0.0))
    for path in paths[1:]:
        found = load(path)
        # a box drawn around two lines, which this OCR reads one by one
        lines = [e for e in lines if sum(1 for o in found if o['page'] == e['page'] and within(o, e)) < 2]
        new = []
        for e in found:
            same = [o for o in lines if o['page'] == e['page'] and overlap(e, o)]
            if same:
                for o in same:
                    o.setdefault('alt', []).append(e['text'])
            elif plausible(e, language):
                new.append(e)
        lines += new
    return [e for e in lines if order(e) < end]


def plausible(e, language):
    """False for what the OCR makes of specks and rules ("Çİ·O", "فهفهي هه"): a line only one OCR
    found must be as tall as a line of print, and written in the edition's own letters."""
    letters = [c for c in e['text'] if c.isalpha()]
    script = (lambda c: 'ء' <= c <= 'ي') if language == 'ar' else (lambda c: c.isascii() or 'À' <= c <= 'ÿ' or c in 'Œœ')
    return e['h'] >= 0.008 and len(letters) >= 2 and all(map(script, letters))


def overlap(a, b):
    """True if two lines' boxes cover much of each other: the same line, read twice."""
    dy = min(a['y'] + a['h'], b['y'] + b['h']) - max(a['y'], b['y'])
    dx = min(a['x'] + a['w'], b['x'] + b['w']) - max(a['x'], b['x'])
    return dy > 0.5 * min(a['h'], b['h']) and dx > 0.3 * min(a['w'], b['w'])


def within(a, b):
    """True if line a lies inside line b's box, give or take a little."""
    return (a['y'] >= b['y'] - 0.004 and a['y'] + a['h'] <= b['y'] + b['h'] + 0.004
            and a['x'] + a['w'] / 2 > b['x'] and a['x'] + a['w'] / 2 < b['x'] + b['w'] and a['h'] < 0.7 * b['h'])


def read_rules(path):
    """{(page, side): [y of each rule, top to bottom]}"""
    out = {}
    with open(path, encoding='utf-8') as f:
        for r in map(json.loads, f):
            out.setdefault((r['page'], r['side']), []).append(r['y'])
    return {k: sorted(v) for k, v in out.items()}


def gutter(lines):
    """The x between a page's two columns: the middle of the gap no line crosses that lies nearest
    the middle of the page. Some pages are scanned off centre, and a left-hand table can reach past
    the middle."""
    xs = [0.4 + i / 1000 for i in range(201)]
    crossed = [sum(1 for e in lines if e['w'] < 0.6 and e['x'] < x < e['x'] + e['w']) for x in xs]
    runs, start = [], None
    for i, n in enumerate(crossed + [None]):
        if n == min(crossed) and start is None:
            start = i
        elif n != min(crossed) and start is not None:
            runs.append((xs[start] + xs[i - 1]) / 2)
            start = None
    return min(runs, key=lambda x: abs(x - 0.5))


def columns(lines, rtl):
    """The half-page columns in reading order: [(page, side, (left, right), [lines by y])]."""
    out = []
    for page in sorted({e['page'] for e in lines}):
        on_page = [e for e in lines if e['page'] == page]
        g = gutter(on_page)
        halves = {'left': [], 'right': []}
        for e in on_page:
            halves['left' if e['x'] + e['w'] / 2 < g else 'right'].append(e)
        for side in (('right', 'left') if rtl else ('left', 'right')):
            bounds = (0.0, g) if side == 'left' else (g, 1.0)
            out.append((page, side, bounds, sorted(halves[side], key=lambda e: e['y'])))
    return out


def split_seat(e, edge):
    """An Arabic line the OCR ran across the rule, seat and commune together
    ("الأربعاء نايث ايراثن - الأربعاء نايث ايراثن"): the seat, then the commune."""
    seat, commune = e['text'].split(' - ', 1)
    return (dict(e, text=seat.strip(), x=edge, w=e['x'] + e['w'] - edge),
            dict(e, text='- ' + commune.strip(), w=edge - e['x']))


def capitals(text):
    """True for a French seat: they are printed in capitals, the communes in small letters."""
    letters = [c for c in text if c.isalpha()]
    return len(letters) >= 2 and sum(c.isupper() for c in letters) >= 0.8 * len(letters)


def tables(lines, language):
    """[{wilaya, page, side, seats: [lines], communes: [lines]}], one per table and column."""
    rtl = language == 'ar'
    wilaya_re, skip_re = (AR_WILAYA, AR_SKIP) if rtl else (FR_WILAYA, FR_SKIP)
    out, current = [], None
    for page, side, bounds, col in columns(lines, rtl):
        for e in col:
            text = e['text'].strip()
            # a heading the other OCR read better ("2 واة" for "29 - ولاية معسكر")
            m = next((m for t in [text] + e.get('alt', []) if len(t) < 60 for m in [wilaya_re.search(t.strip())] if m), None)
            if m:
                current = {'wilaya': int(next(g for g in m.groups() if g)), 'page': page, 'side': side,
                           'bounds': bounds, 'lines': []}
                out.append(current)
                continue
            if current is None or skip_re.search(text):
                continue
            if (current['page'], current['side']) != (page, side):
                # a table that runs on into the next column, without a new heading
                current = dict(current, page=page, side=side, bounds=bounds, lines=[])
                out.append(current)
            current['lines'].append(e)
    for t in out:
        t['seats'], t['communes'] = [], []
        if rtl:
            # Arabic communes are set against the rule that separates them from the seats, after a
            # dash; the seats against the table's outer edge. Only the table's own lines count here:
            # the decree's preamble shares the first column, and its paragraphs start with a dash too.
            edges = [e['x'] + e['w'] for e in t['lines'] if DASH.match(e['text'])]
            edge = statistics.median(edges) if edges else t['bounds'][0] + 0.32
        for e in t.pop('lines'):
            text = e['text'].strip()
            if rtl and ' - ' in text and e['x'] < edge - 0.02 and e['x'] + e['w'] > edge + 0.03:
                seat, commune = split_seat(e, edge + 0.015)
                t['seats'].append(seat)
                t['communes'].append(commune)
                continue
            # The seats are on the outer side: the left of a French column, the right of an Arabic one
            if rtl:
                seat = e['x'] + e['w'] > edge + 0.03
            else:
                seat = capitals(text) or e['x'] + e['w'] / 2 - t['bounds'][0] < 0.16
            t['seats' if seat else 'communes'].append(e)
    return out


def rows(table, rules, language):
    """[(seat lines, commune lines)] for one table: one per band between two rules that holds text,
    split where a rule was missed (see split)."""
    ys = rules.get((table['page'], table['side']), [])
    bands = {}
    for kind in ('seats', 'communes'):
        for e in table[kind]:
            i = bisect.bisect_right(ys, e['y'] + e['h'] / 2)
            bands.setdefault(i, ([], []))[0 if kind == 'seats' else 1].append(e)
    return [r for i in sorted(bands) for r in split(*(ordered(b, language) for b in bands[i]), language)]


def ordered(lines, language):
    """Lines in reading order: by height, and along the line for pieces of one line
    ("CHELLALAT" and "EL", read apart)."""
    out = []
    for e in sorted(lines, key=lambda e: e['y']):
        if out and abs(e['y'] - out[-1][0]['y']) < 0.006:
            out[-1].append(e)
        else:
            out.append([e])
    return [e for line in out for e in sorted(line, key=lambda e: -e['x'] if language == 'ar' else e['x'])]


def split(seats, communes, language):
    """A band with the seats of several daïras, where the scan lost a rule: each seat is set level
    with the first of its communes, which bears the seat's name, so a seat line that is level with a
    commune of its name starts a daïra. Other seat lines carry on the seat above (long names wrap)."""
    starts = [seats[0]] if seats else []
    for s in seats[1:]:
        if s['y'] > starts[-1]['y'] + 0.006 and any(
                abs(c['y'] - s['y']) < 0.012 and similar(s['text'], c['text'], language) for c in communes):
            starts.append(s)
    if len(starts) < 2:
        return [(seats, communes)]
    def owner(e):
        return max(i for i, s in enumerate(starts) if s['y'] <= e['y'] + e['h'] / 2 or i == 0)
    out = [([], []) for _ in starts]
    for s in seats:
        out[owner(s)][0].append(s)
    for c in communes:
        out[owner(c)][1].append(c)
    return out


def similar(a, b, language):
    a, b = loose(a, language), loose(b, language)
    return bool(a) and bool(b) and difflib.SequenceMatcher(None, a, b).ratio() >= 0.6


def loose(s, language):
    """A name with only what the OCR reads reliably: letters, without accents, hamzas or spaces."""
    if language == 'ar':
        s = re.sub('[أإآ]', 'ا', s).replace('ى', 'ي').replace('ة', 'ه')
        return re.sub(r'[^ء-ي]', '', s)
    s = unicodedata.normalize('NFKD', s.replace('’', "'"))
    return re.sub(r'[^a-z]', '', ''.join(c for c in s if not unicodedata.combining(c)).casefold())


def doubts(seat, communes, language):
    """Why a row needs a look on the page, or None."""
    if not seat:
        return 'no seat'
    if not communes:
        return 'no communes'
    if loose(' '.join(e['text'] for e in seat), language) != loose(communes[0]['text'], language):
        return 'the seat is not the first commune'
    return None


def main():
    args = sys.argv[1:]
    pages = None
    if args[0] == '--pages':  # another scan laid out the same way (Decree 92-66)
        pages, args = (int(args[1]), int(args[2])), args[3:]
    language, rules_path, rows_path, *paths = args
    first, last = pages or ((3, 28) if language == 'fr' else (3, 32))
    rules = read_rules(rules_path)
    by_wilaya, out = {}, []
    for t in tables(read(paths, first, last, language, amending=pages is not None), language):
        for seat, communes in rows(t, rules, language):
            by_wilaya.setdefault(t['wilaya'], []).append((seat, communes))
            out.append({'wilaya': t['wilaya'], 'page': t['page'], 'side': t['side'], 'seat': seat, 'communes': communes})
            why = doubts(seat, communes, language)
            if why:
                print(f"{t['wilaya']:02d} p{t['page']} {t['side']}: {why}: "
                      f"{' '.join(e['text'] for e in seat)!r} {[e['text'] for e in communes]}", file=sys.stderr)
    total_d = total_c = 0
    for w in sorted(by_wilaya):
        rs = by_wilaya[w]
        n = sum(len(c) for _, c in rs)
        total_d, total_c = total_d + len(rs), total_c + n
        print(f'{w:02d}\t{len(rs)} daïras\t{n} communes\t' + ' '.join(str(len(c)) for _, c in rs))
    print(f'{len(by_wilaya)} wilayas, {total_d} daïras, {total_c} communes', file=sys.stderr)
    with open(rows_path, 'w', encoding='utf-8') as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()

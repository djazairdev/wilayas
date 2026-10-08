"""Parse the lists of communes in a law that amends Law 84-09, in both editions.

Each list reads "Art. 7. — Les douze (12) communes suivantes constituent une wilaya :"
and then "1. Laghouat ;", "2. Ksar El Hirane ;" and so on. Both editions give the
article, the number of communes announced and the names. The lists are matched article
by article, and the two editions must agree on the articles and the counts.

The French comes from the PDF's text (tools/gazette/columns.swift), which is exact. The
Arabic text in these PDFs is drawn in the right places but recorded in the wrong ones:
lines merge or break near the article headers. So the Arabic is read twice, by OCR of the
rendered pages (tools/gazette/ocr.swift) and from the PDF's text, and the two readings are
aligned item by item. Where they have the same letters, the PDF's characters are kept,
since the OCR slips on spacing ("أو لاد"). Every other name is read on the rendered
page and recorded in data/source/readings.csv; its `check` then says `eye`. Rows still
waiting for a reading are listed on stderr, and the tests refuse them.

    python3 tools/gazette/lists.py law-26-06 F.txt A.txt A.ocr.jsonl > data/source/law-26-06.csv

A.txt comes from columns.swift; for the 2019 issue, pass runs.swift's A.runs.jsonl instead.

Standard library only.
"""
import csv
import difflib
import json
import os
import re
import sys
import unicodedata

MIRROR = str.maketrans('()[]{}«»“”', ')(][}{»«”“')
DIGITS = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')

# Running heads and page furniture in the French edition
NOISE = re.compile(r'^(=== page .*|\d+\s+JOURNAL OFFICIEL.*|JOURNAL OFFICIEL.*|\d{1,2}\s+\S+\s+(?:El\s+)?\S*\s*\d{4}|\d{1,3})$')

READINGS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'source', 'readings.csv')


def columns(path):
    """Lines of a columns.swift file, in reading order, with its page markers."""
    with open(path, encoding='utf-8') as f:
        return [line.rstrip('\n') for line in f]


def arabic(line):
    """Turn a line of display-order Arabic, as PDFKit gives it, into normal text."""
    s = unicodedata.normalize('NFKC', line[::-1]).replace('ـ', '')
    s = re.sub(r'\d+', lambda m: m.group(0)[::-1], s).translate(MIRROR)
    return re.sub(r'\s+', ' ', s).strip()


def article_id(raw):
    """'52. Bis 10' -> '52 bis 10'; '7' -> '7'."""
    return re.sub(r'\s+', ' ', raw.replace('.', ' ')).strip().lower()


# "Art. 7. — Les douze (12) communes suivantes constituent une wilaya :" (the laws), or
# "Art. 34. — La wilaya de Ouargla est constituée des huit (8) communes suivantes :" (Ordinance 21-03)
HEADER = re.compile(
    r'Art\.?\s*(\d+(?:\.?\s*bis(?:\s*\d+)?)?)\s*\.?\s*[—–-]+\s*'
    r'(?:Les\s+([a-zà-ÿ\s-]+?)\s*\((\d+)\s*\)\s*communes\s+suivantes\s+constituent\s+une\s+wilaya'
    r'|La\s+wilaya\s+d(?:e\s+|[\'’]\s*).+?\s+est\s+constituée\s+des\s+([a-zà-ÿ\s-]+?)\s*\((\d+)\s*\)\s*communes\s+suivantes)'
    r'\s*:', re.I)
AMENDING = re.compile(r'(?<![«\w])Art\.?\s*(\d+)\s*\.?\s*[—–-]+\s*(?:Les\s+dispositions|L’intitulé|L\'intitulé)', re.I)
# A list ends at a full stop that doesn't follow a number: before the closing quote, the next
# article, or the next text (Ordinance 21-03's last list runs straight into Decree 21-117)
LIST_END = re.compile(r'\.\s*»|»\s*\.|\.\s*(?=«|Art\b)|\.\s*$|(?<!\d)\.(?=\s)')
ITEM = re.compile(r'^\s*(\d{1,2})\s*\.?\s+(.+?)\s*$')


def french_items(body):
    """[(n, name)] from "1. Laghouat ; 2. Ksar El Hirane ; … 12. Hadj Mechri." The gazette
    sometimes drops the dot after a number ("5 In Amguel", Law 19-12)."""
    body = LIST_END.split(body.strip(), maxsplit=1)[0]
    return [(int(m.group(1)), m.group(2)) for m in map(ITEM.match, body.split(';')) if m]


def french_lists(lines):
    """[{article, via, announced, items: [(n, name)]}] from the French edition."""
    text = ' '.join(l.strip() for l in lines if l.strip() and not NOISE.match(l.strip()))
    text = re.sub(r'\s+', ' ', text)
    amending = [(m.start(), m.group(1)) for m in AMENDING.finditer(text)]
    headers = list(HEADER.finditer(text))
    out = []
    for i, h in enumerate(headers):
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        nxt = [p for p, _ in amending if p > h.end()]
        if nxt:
            end = min(end, nxt[0])
        body = text[h.end():end]
        items = french_items(body)
        via = [a for p, a in amending if p < h.start()]
        out.append({'article': article_id(h.group(1)), 'via': via[-1] if via else '',
                    'announced': int(h.group(3) or h.group(5)), 'items': items})
    return out


# "1. الأغواط،" (2026) or "1- أدرار،" (2019)
AR_ITEM = re.compile(r'^(\d{1,2})\s*[.\-–]\s*([^\d\s،.”“"][^،.”“"]*?)\s*(?:[،.”“"]|$)')


def column_lines(path):
    """[(page, text)] from columns.swift's Arabic output, turned back into normal text."""
    out, page = [], 0
    for raw in columns(path):
        m = re.match(r'=== page (\d+)', raw)
        if m:
            page = int(m.group(1))
        else:
            out.append((page, arabic(raw)))
    return out


def arabic_run(text):
    """One run of text from the 2019 Arabic edition, whose runs store every character,
    digits included, right to left."""
    s = unicodedata.normalize('NFKC', text[::-1]).replace('ـ', '')
    return s.translate(MIRROR).translate(DIGITS).strip()


def run_lines(path, head=0.057):
    """[(page, text)] in reading order, rebuilt from runs.swift's output: runs on the same
    baseline make a line, read right to left, right column first."""
    by_column = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            d = json.loads(line)
            if d['y'] >= head:
                column = 0 if d['x'] + d['w'] / 2 >= 0.5 else 1
                by_column.setdefault((d['page'], column), []).append(d)
    out = []
    for page, column in sorted(by_column):
        line = []
        for d in sorted(by_column[(page, column)], key=lambda d: d['y']) + [None]:
            if line and (d is None or d['y'] - line[0]['y'] > 0.006):
                text = ' '.join(arabic_run(r['text']) for r in sorted(line, key=lambda r: -r['x']))
                out.append((page, re.sub(r'\s+', ' ', text)))
                line = []
            if d is not None:
                line.append(d)
    return out


def pdf_arabic_items(lines):
    """[(page, n, name)] for every numbered item in the PDF's own Arabic text."""
    items = []
    for page, text in lines:
        m = AR_ITEM.match(text)
        if m:
            items.append((page, int(m.group(1)), m.group(2).strip()))
    return items


def ocr_lines(path, rtl, head=0.057):
    """[(page, text)] in reading order from ocr.swift's output, without the running head."""
    pages = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            d = json.loads(line)
            if d['y'] < head:
                continue
            right = d['x'] + d['w'] / 2 >= 0.5
            column = (0 if right else 1) if rtl else (1 if right else 0)
            pages.setdefault(d['page'], []).append((column, d['y'], d['text']))
    return [(page, text) for page in sorted(pages) for _, _, text in sorted(pages[page])]


OCR_ITEM = re.compile(r'^(\d{1,2})\s*[.\-–]\s*([^\d\s].*?)[\s،,.:”“"»«!]*$')
# "المادة 52 مكرر 10 : تتشكل ولاية من الاثنتي عشرة (12) بلدية الآتية:" (2026), or
# "المادّة 52 مكرر 5 : تتشكل ولاية من البلديتين الاثنتين (2) الآتيتين:" (2019). The OCR
# often reads the opening bracket as "!" or ",".
AR_HEADER = re.compile(r'المادّ?ة\s*(\d+)(\s*مكرر\s*(\d*))?\s*:\s*تتشكل\s+ولاية\s+(?:[^\s:]+\s+){0,3}?من\s+.+?[!(,]+\s*(\d+)\s*\)\s*'
                       r'(?:بلدي(?:ة|ات)\s+)?الآتي(?:ة|تين)')
AR_ARTICLE = re.compile(r'^["“”«]?\s*المادّ?ة\b')


def ocr_arabic_lists(lines):
    """[{article, announced, items: [(page, n, name)]}] from the OCR'd Arabic edition.

    A list starts at its header, which can run over two lines, and ends at the next
    article of any kind. Items out of order are dropped and reported on stderr; the gaps
    they leave are filled from the PDF's text.
    """
    out, current, head = [], None, None
    for page, text in lines:
        text = text.strip()
        item = OCR_ITEM.match(text)
        if AR_ARTICLE.match(text):
            head, current = text, None
        elif head is not None and not item:
            head += ' ' + text
        if head is not None:
            m = AR_HEADER.search(head)
            if m:
                article = m.group(1) + ((' bis ' + m.group(3)).rstrip() if m.group(2) else '')
                current = {'article': article, 'announced': int(m.group(4)), 'items': []}
                out.append(current)
                head = None
                continue
        if item:
            head = None
            if current is None:
                continue
            n, last = int(item.group(1)), current['items'][-1][1] if current['items'] else 0
            if last < n <= current['announced']:
                current['items'].append((page, n, item.group(2).strip()))
            else:
                print(f"art. {current['article']}: dropped OCR item {n} after {last}: {text}", file=sys.stderr)
    return out


def squeeze(s):
    return re.sub(r'\s+', '', s)


def pair(ocr, pdf):
    """Pair OCR items with PDF items, in order: the longest run of pairs with the same
    number and nearly the same letters. Both are [(page, n, name)]. Returns {i: j}."""
    def same(o, p):
        return o[1] == p[1] and difflib.SequenceMatcher(None, squeeze(o[2]), squeeze(p[2])).ratio() >= 0.8
    n, m = len(ocr), len(pdf)
    match = [[same(o, p) for p in pdf] for o in ocr]
    best = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            best[i][j] = best[i + 1][j + 1] + 1 if match[i][j] else max(best[i + 1][j], best[i][j + 1])
    pairs, i, j = {}, 0, 0
    while i < n and j < m:
        if match[i][j] and best[i][j] == best[i + 1][j + 1] + 1:
            pairs[i] = j
            i, j = i + 1, j + 1
        elif best[i + 1][j] >= best[i][j + 1]:
            i += 1
        else:
            j += 1
    return pairs


def arabic_lists(ocr_lists, pdf, pdf_spaces=True):
    """[[(n, name, check, page)]] for the OCR's lists, numbered 1 to the count announced.

    check is empty where the OCR and the PDF's text have the same letters (the PDF's
    spelling is kept); otherwise it says why the name must be read on the page:
    `differs` (the readings disagree), `ocr` or `pdf` (only one reading has the item; the
    PDF's is taken from between its neighbours) or `missing`.

    Where the readings differ only in spaces, the PDF's spaces are kept if pdf_spaces is
    true: the OCR puts spaces after letters that don't join ("أو لاد"). Text rebuilt from
    runs (2019) splits words, so there the difference is marked `spaces`.
    """
    flat = [(li, item) for li, l in enumerate(ocr_lists) for item in l['items']]
    pairs = pair([item for _, item in flat], pdf)
    out = []
    for li, l in enumerate(ocr_lists):
        mine = [k for k, (lj, _) in enumerate(flat) if lj == li]
        by_n = {flat[k][1][1]: k for k in mine}
        rows = []
        for n in range(1, l['announced'] + 1):
            k = by_n.get(n)
            if k is not None:
                page, _, name = flat[k][1]
                if k in pairs:
                    p = pdf[pairs[k]]
                    if squeeze(p[2]) != squeeze(name):
                        check = 'differs'
                    else:
                        check = '' if pdf_spaces or p[2] == name else 'spaces'
                    rows.append((n, p[2], check, page))
                else:
                    rows.append((n, name, 'ocr', page))
                continue
            # Not in the OCR: look in the PDF's text between the neighbours' partners
            at = min([k for k in mine if flat[k][1][1] > n] or [max(mine or [-1]) + 1])
            before = [pairs[k] for k in pairs if k < at]
            after = [pairs[k] for k in pairs if k >= at]
            lo, hi = max(before, default=-1), min(after, default=len(pdf))
            found = [pdf[j] for j in range(lo + 1, hi) if pdf[j][1] == n]
            if len(found) == 1:
                rows.append((n, found[0][2], 'pdf', found[0][0]))
            else:
                rows.append((n, '', 'missing', 0))
        out.append(rows)
    return out


def readings(text_id, path=READINGS):
    """{(article, item, edition): name} as read on the rendered page, for one text."""
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8', newline='') as f:
        return {(r['article'], int(r['item']), r['edition']): r['name']
                for r in csv.DictReader(f) if r['text'] == text_id}


def rows(text_id, fr, ar_lists, ar, seen):
    """Match the editions article by article and yield one row per commune; raise on any mismatch."""
    if [(l['article'], l['announced']) for l in fr] != [(l['article'], l['announced']) for l in ar_lists]:
        raise SystemExit(f"{text_id}: the editions' lists differ:\n"
                         f"  fr {[(l['article'], l['announced']) for l in fr]}\n"
                         f"  ar {[(l['article'], l['announced']) for l in ar_lists]}")
    for f, a in zip(fr, ar):
        numbers = [n for n, _ in f['items']]
        if numbers != list(range(1, f['announced'] + 1)):
            raise SystemExit(f"{text_id}, art. {f['article']}: French items {numbers}, announced {f['announced']}")
        for (n, name_fr), (_, name_ar, check, page) in zip(f['items'], a):
            read_fr = seen.get((f['article'], n, 'fr'))
            read_ar = seen.get((f['article'], n, 'ar'))
            if read_ar is not None and check == 'pdf' and squeeze(read_ar) != squeeze(name_ar):
                print(f"art. {f['article']}, {n}: read {read_ar!r}, the PDF's text has {name_ar!r}", file=sys.stderr)
            if read_fr is not None or read_ar is not None:
                name_fr, name_ar, check = read_fr or name_fr, read_ar or name_ar, 'eye'
            yield {'text': text_id, 'article': f['article'], 'via': f['via'], 'item': n,
                   'of': f['announced'], 'name_fr': name_fr, 'name_ar': name_ar, 'check': check,
                   'page': page}


FIELDS = ['text', 'article', 'via', 'item', 'of', 'name_fr', 'name_ar', 'check']


def main():
    text_id, fr_path, ar_path, ocr_path = sys.argv[1:5]
    fr = french_lists(columns(fr_path))
    ar_lists = ocr_arabic_lists(ocr_lines(ocr_path, rtl=True))
    runs = ar_path.endswith('.jsonl')
    pdf_lines = run_lines(ar_path) if runs else column_lines(ar_path)
    ar = arabic_lists(ar_lists, pdf_arabic_items(pdf_lines), pdf_spaces=not runs)
    w = csv.DictWriter(sys.stdout, FIELDS, extrasaction='ignore', lineterminator='\n')
    w.writeheader()
    waiting = []
    for row in rows(text_id, fr, ar_lists, ar, readings(text_id)):
        w.writerow(row)
        if row['check'] not in ('', 'eye'):
            waiting.append(row)
    for r in waiting:
        print(f"to read: art. {r['article']}, item {r['item']} ({r['check']}), page {r['page']}: "
              f"{r['name_ar']} / {r['name_fr']}", file=sys.stderr)
    if waiting:
        print(f'{len(waiting)} rows to read on the page', file=sys.stderr)


if __name__ == '__main__':
    main()

"""Check the hamzas of the Arabic names of Decree 91-306 against the scan.

An alif that stands alone (first in its word, or after a letter that doesn't join the next) is a
shape of its own on the scan, so the shapes match the name's standing alifs one to one, right to
left. In this type, at the scan's resolution (about 305 dpi):

- a bare alif's head is no wider than its stem;
- a hamza above merges into the head, narrow on the top rows and then a bulge, usually 9 to 12
  pixels wide, or stands just above it, a mark of its own;
- a madda is a flat cap 7 to 10 pixels wide on the top rows, then a narrow neck, or a flat mark
  of its own just above the alif;
- a hamza below is a mark of its own under the foot, 10 to 12 pixels wide and as tall. The two
  dots of a ي (about 14 by 6 pixels) and smaller blots are not.

For each Arabic name in data/source/executive-decree-91-306.csv, this measures the standing
alifs on its printed line and lists the names the scan contradicts, and those it can't match one
to one (a crack, a speck or a joined letter taken for an alif, or an alif joined to its
neighbour). The lam-alif isn't measured: look at it on the page.

    python3 tools/gazette/alifs.py work/F1991041.rows.jsonl work/A1991041.rows.jsonl
    python3 tools/gazette/alifs.py work/F1991041.rows.jsonl work/A1991041.rows.jsonl --show 44 8/3

--show prints the scan of one name with the alifs it found drawn as A.
Standard library only, plus bitmap.swift.
"""
import csv
import json
import os
import statistics
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import annex  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = 'sources/joradp/A1991041.pdf'
DPI, PAD = 305, 0.004
ALIFS = 'اأإآ'
NONJOINING = set('اأإآدذرزوؤةء')
EXPECTED = {'ا': 'bare', 'أ': 'hamza', 'إ': 'bare', 'آ': 'madda'}


def components(rows):
    """[{'pixels': [(y, x)], 'top', 'bottom', 'left', 'right'}], 8-connected."""
    h, w = len(rows), len(rows[0])
    seen = [[False] * w for _ in range(h)]
    out = []
    for y in range(h):
        for x in range(w):
            if rows[y][x] != '#' or seen[y][x]:
                continue
            stack, pixels = [(y, x)], []
            seen[y][x] = True
            while stack:
                cy, cx = stack.pop()
                pixels.append((cy, cx))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and rows[ny][nx] == '#':
                            seen[ny][nx] = True
                            stack.append((ny, nx))
            ys, xs = [p[0] for p in pixels], [p[1] for p in pixels]
            out.append({'pixels': pixels, 'top': min(ys), 'bottom': max(ys), 'left': min(xs), 'right': max(xs)})
    return out


def spans(c):
    """Width of the shape on each of its rows, top to bottom."""
    rows = {}
    for y, x in c['pixels']:
        lo, hi = rows.get(y, (x, x))
        rows[y] = (min(lo, x), max(hi, x))
    return [rows[y][1] - rows[y][0] + 1 if y in rows else 0 for y in range(c['top'], c['bottom'] + 1)]


def kind(profile, stem):
    """'madda', 'hamza' or 'bare' from the widths of an alif's top rows (see above), or 'unclear'."""
    p = profile + [0] * (14 - len(profile))
    wide = [w >= stem + 3 for w in p]
    if not any(wide[:12]):
        return 'bare'
    first = wide.index(True)
    neck = min(p[first + 2:first + 7]) if first + 2 < 14 else 99
    if first <= 2 and max(p[:3]) >= stem + 3 and neck <= stem:
        return 'madda'
    if first >= 3 and max(p[:3]) <= stem + 2 and sum(wide[3:12]) >= 3:
        return 'hamza'
    return 'unclear'


def standing(text):
    """The alifs of text that stand alone, in the order of the text (right to left on the page)."""
    return [ch for i, ch in enumerate(text) if ch in ALIFS and (i == 0 or text[i - 1] == ' ' or text[i - 1] in NONJOINING)]


def measure(rows, show=False):
    """The alifs found on a line's bitmap, right to left: [{'kind', 'below', 'profile', 'stem'}]."""
    h, w = len(rows), len(rows[0])
    shapes = [c for c in components(rows) if c['top'] > 0 and c['bottom'] < h - 1]
    # the column rules and the dash's neighbours that span the line
    shapes = [c for c in shapes if c['bottom'] - c['top'] + 1 < 0.9 * h and c['right'] - c['left'] + 1 < 0.8 * w]
    found = []
    for c in shapes:
        height, width = c['bottom'] - c['top'] + 1, c['right'] - c['left'] + 1
        s = spans(c)
        if height < 22 or width > 15 or sum(v <= 8 for v in s) < 0.6 * len(s):
            continue
        stem = statistics.median(s[int(0.4 * len(s)):max(int(0.4 * len(s)) + 1, int(0.85 * len(s)))])
        head, below = kind(s[:14], stem), False
        for m in shapes:
            mh, mw = m['bottom'] - m['top'] + 1, m['right'] - m['left'] + 1
            if m is c or mh > 14 or mw > 15 or len(m['pixels']) < 20:
                continue
            if m['right'] < c['left'] - 3 or m['left'] > c['right'] + 3:
                continue
            if head == 'bare' and m['bottom'] <= c['top'] + 2 and c['top'] - m['bottom'] <= 8:
                head = 'madda' if mw >= 1.6 * mh and mw >= 6 else 'hamza'
            elif 0 <= m['top'] - c['bottom'] + 2 <= 10 and mh >= 9 and mw >= 9 and len(m['pixels']) >= 50:
                below = True
        if show:
            for y, x in c['pixels']:
                rows[y] = rows[y][:x] + 'A' + rows[y][x + 1:]
        found.append({'x': (c['left'] + c['right']) / 2, 'kind': head, 'below': below,
                      'profile': s[:12], 'stem': stem})
    return sorted(found, key=lambda f: -f['x'])


def verdict(text, found):
    """None if the scan agrees with the name's alifs, else why not."""
    alifs = standing(text)
    if len(alifs) != len(found):
        return f'{len(alifs)} standing alifs in the name, {len(found)} on the scan'
    for ch, f in zip(alifs, found):
        if (ch == 'إ') != f['below']:
            return f"{ch}: {'a' if f['below'] else 'no'} mark below on the scan"
        if f['kind'] not in (EXPECTED[ch], 'unclear'):
            return f"{ch}: the head is {f['kind']} on the scan (widths {f['profile']}, stem {f['stem']})"
    return None


def main():
    args = sys.argv[1:]
    show = None
    if '--show' in args:
        i = args.index('--show')
        show = tuple(args[i + 1:i + 3])
        del args[i:i + 3]
    fr, ar = annex.load(args[0]), annex.load(args[1])
    with open(os.path.join(annex.ROOT, 'data', 'source', annex.TEXT + '.csv'), encoding='utf-8', newline='') as f:
        names = {(r['wilaya'], f"{r['daira']}/{r['item']}"): r['name_ar'] for r in csv.DictReader(f)}
    todo = []
    for wilaya, daira, item, _, line in annex.entries(fr, ar):
        key = (f'{wilaya:02d}', f'{daira}/{item}')
        if show and key != show:
            continue
        todo.append((key, line))
    jobs = [json.dumps({'pdf': PDF, 'page': line['page'], 'x': line['x'] - PAD, 'y': line['y'] - PAD,
                        'w': line['w'] + 2 * PAD, 'h': line['h'] + 2 * PAD, 'dpi': DPI}) for _, line in todo]
    out = subprocess.run(['swift', os.path.join(HERE, 'bitmap.swift')], input='\n'.join(jobs) + '\n',
                         capture_output=True, text=True, check=True).stdout
    disagree = 0
    for (key, line), bitmap in zip(todo, out.splitlines()):
        rows = json.loads(bitmap)['rows']
        found = measure(rows, show=bool(show))
        if show:
            print('\n'.join(r for r in rows if r.strip('.')))
            print(names[key], [(f['kind'], f['below'], f['profile']) for f in found])
            continue
        why = verdict(names[key], found)
        if why:
            disagree += 1
            print(f'{key[0]} {key[1]} p{line["page"]} {names[key]}: {why}')
    if not show:
        print(f'{disagree} of {len(todo)} names to look at', file=sys.stderr)


if __name__ == '__main__':
    main()

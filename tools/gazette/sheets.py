"""Lay out in sheets, to read them by eye, the names of Decree 91-306 that no second reading
confirms: the names whose OCR readings differ, or agree on a name that isn't a Wikidata label
(tools/gazette/annex.py), and that data/source/readings.csv doesn't record yet.

    python3 tools/gazette/sheets.py work/F1991041.rows.jsonl work/A1991041.rows.jsonl work/wikidata-labels.json work/eye

writes to the folder given:
- items.json: the names in each edition, numbered from 1, with the place of their line on the
  page, the OCR's readings and the nearest Wikidata label, to compare;
- crops/fr-0001.png and so on: the printed line of each name, at 300 dpi in French and 400 in
  Arabic, to see the dots and hamzas;
- sheet-fr-01.png and so on: the crops, 24 to a sheet.

Prints how many names are left to read: none, once readings.csv has them all.
Standard library only, plus crops.swift and grid.swift.
"""
import difflib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import annex  # noqa: E402

PER, COLUMNS = 24, 3
PDF = {'fr': 'sources/joradp/F1991041.pdf', 'ar': 'sources/joradp/A1991041.pdf'}
DPI = {'fr': 300, 'ar': 400}


def main():
    fr_path, ar_path, labels_path, folder = sys.argv[1:]
    fr, ar = annex.load(fr_path), annex.load(ar_path)
    known, seen = annex.known_names(labels_path), annex.readings()
    items = {'fr': [], 'ar': []}
    for wilaya, daira, item, f, a in annex.entries(fr, ar):
        key = (f'{wilaya:02d}', f'{daira}/{item}')
        for language, line in (('fr', f), ('ar', a)):
            if line is None or key + (language,) in seen or annex.check(line, language, item == 'seat', known) is not None:
                continue
            cands = []
            for t in [line['text']] + line.get('alt', []):
                c = annex.clean(t, language)
                if c not in cands:
                    cands.append(c)
            pool = known['fr seat' if language == 'fr' and item == 'seat' else language]
            wd = difflib.get_close_matches(cands[0], pool, n=1, cutoff=0.5)
            items[language].append({'n': len(items[language]) + 1, 'key': ' '.join(key), 'page': line['page'],
                                    'cands': cands, 'wd': wd[0] if wd else '',
                                    'box': [line['x'], line['y'], line['w'], line['h']]})
    os.makedirs(os.path.join(folder, 'crops'), exist_ok=True)
    jobs = []
    for language, todo in items.items():
        for it in todo:
            x, y, w, h = it['box']
            it['crop'] = os.path.join(folder, 'crops', f'{language}-{it["n"]:04d}.png')
            jobs.append(json.dumps({'pdf': PDF[language], 'page': it['page'], 'x': max(0, x - 0.012), 'y': max(0, y - 0.007),
                                    'w': w + 0.024, 'h': h + 0.014, 'dpi': DPI[language], 'out': it['crop']}))
    if jobs:
        subprocess.run(['swift', os.path.join(HERE, 'crops.swift')], input='\n'.join(jobs) + '\n', text=True, check=True)
    for language, todo in items.items():
        for s in range(0, len(todo), PER):
            out = os.path.join(folder, f'sheet-{language}-{s // PER + 1:02d}.png')
            subprocess.run(['swift', os.path.join(HERE, 'grid.swift'), out, str(COLUMNS)]
                           + [f'{it["n"]}={it["crop"]}' for it in todo[s:s + PER]], check=True)
    with open(os.path.join(folder, 'items.json'), 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=0)
    print({k: len(v) for k, v in items.items()}, 'names to read')


if __name__ == '__main__':
    main()

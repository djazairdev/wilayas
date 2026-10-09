"""Checks on the tables the API is built from (data/wilayas.csv, dairas.csv, communes.csv,
changes.csv and aliases.csv): that tools/resolve.py makes them from data/source/ as they are,
and that they fit together.

    python3 -m unittest discover -s tests

Standard library only.
"""
import csv
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
SOURCE = os.path.join(DATA, 'source')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import resolve  # noqa: E402

ARABIC = re.compile(r'^[ء-يڤ]+(?: [ء-يڤ]+)*$')
FRENCH = re.compile(r"^[A-Za-zÀ-ÿ’']+(?:[ -][A-Za-zÀ-ÿ’']+)*$")
# Decree 92-66 prints one commune's name with commas
PRINTED = {'0419': ('El Fedjoudj, Boughrara, Saoudi', 'الفجوج، بوغرارة، سعودي')}


def read(name):
    with open(os.path.join(DATA, name), encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


def source_row(text, article, item):
    """The row of a transcription that a citation names: for a daïra decree, article is the
    wilaya and item the daïra and the commune ('10/2') or the daïra alone ('10')."""
    for r in resolve.source(text):
        if 'daira' in r:
            if r['wilaya'] == article and (f"{r['daira']}/{r['item']}" == item or r['daira'] == item and r['item'] == 'seat'):
                return r
        elif r['article'] == article and r['item'] == item:
            return r
    return None


class Tables(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wilayas = read('wilayas.csv')
        cls.dairas = read('dairas.csv')
        cls.communes = read('communes.csv')
        cls.changes = read('changes.csv')
        cls.aliases = read('aliases.csv')
        texts = {t['id'] for t in resolve.read(os.path.join(DATA, 'texts.csv'))}
        cls.texts = texts | {t['id'] for t in resolve.read(os.path.join(DATA, 'ons.csv'))}

    def test_up_to_date(self):
        """tools/resolve.py makes these files from data/source/ as they are."""
        self.assertEqual(resolve.write(resolve.build(), check=True), [])

    def test_fields(self):
        self.assertEqual(self.wilayas[0], resolve.WILAYA_FIELDS)
        self.assertEqual(self.dairas[0], resolve.DAIRA_FIELDS)
        self.assertEqual(self.communes[0], resolve.COMMUNE_FIELDS)
        self.assertEqual(self.changes[0], resolve.CHANGE_FIELDS)
        self.assertEqual(self.aliases[0], resolve.ALIAS_FIELDS)

    def test_wilayas(self):
        wilayas, communes = self.wilayas[1], self.communes[1]
        self.assertEqual([w['code'] for w in wilayas], [f'{n:02d}' for n in range(1, 70)])
        for w in wilayas:
            with self.subTest(wilaya=w['code']):
                self.assertRegex(w['name_fr'], FRENCH)
                self.assertRegex(w['name_ar'], ARABIC)
                self.assertIn(w['named_by'], self.texts)
                self.assertIn(w['listed_by'], self.texts)
                self.assertEqual(w['listed_article'], resolve.law_article(w['code']))
                mine = [c for c in communes if c['wilaya'] == w['code']]
                self.assertEqual(int(w['communes']), len(mine))
                self.assertEqual(int(w['dairas']), sum(1 for d in self.dairas[1] if d['wilaya'] == w['code']))
                if w['code'] in resolve.NO_SEAT:
                    self.assertEqual(w['seat'], '')
                else:
                    self.assertIn(w['seat'], [c['code'] for c in mine])
                new = int(w['code']) > 48
                self.assertEqual(bool(w['parent']), new)
                self.assertEqual(bool(w['created']), new)
                if new:
                    self.assertIn(w['created_by'], ('law-19-12', 'law-26-06'))
                    self.assertEqual(w['created'], '2019-12-18' if w['created_by'] == 'law-19-12' else '2026-04-05')

    def test_communes(self):
        communes = self.communes[1]
        codes = [c['code'] for c in communes]
        self.assertEqual(len(codes), 1541)
        self.assertEqual(codes, sorted(set(codes)))
        dairas = {d['code']: d for d in self.dairas[1]}
        without = [c['code'] for c in communes if not c['daira']]
        moved_seats = [c['code'] for c in communes if c['wilaya'] in ('09', '35') and not c['daira']]
        self.assertEqual(len(without), sum(1 for c in communes if c['wilaya'] == '16') + len(moved_seats))
        self.assertEqual(len(moved_seats), 3, 'the communes left in the daïras of Sidi Moussa and Reghaïa')
        for c in communes:
            with self.subTest(code=c['code']):
                self.assertRegex(c['code'], r'^\d{4}$')
                if c['code'] in PRINTED:
                    self.assertEqual((c['name_fr'], c['name_ar']), PRINTED[c['code']])
                else:
                    self.assertRegex(c['name_fr'], FRENCH)
                    self.assertRegex(c['name_ar'], ARABIC)
                if c['daira']:
                    self.assertEqual(dairas[c['daira']]['wilaya'], c['wilaya'])
                if int(c['wilaya']) > 58:
                    self.assertEqual(c['wilaya_before'], c['code'][:2])
                else:
                    self.assertEqual(c['wilaya_before'], '')
                    self.assertEqual(c['code'][:2], c['wilaya'])

    def test_each_commune_cites_the_row_it_comes_from(self):
        """The names are those the cited row prints, but where they come from ONS's list."""
        ons = {r['wilaya'] + r['commune']: r for r in resolve.source('ons-2021')}
        for c in self.communes[1]:
            with self.subTest(code=c['code']):
                self.assertIn(c['listed_by'], self.texts)
                row = source_row(c['listed_by'], c['listed_article'], c['listed_item'])
                self.assertIsNotNone(row)
                for lang in ('fr', 'ar'):
                    by = c[f'name_{lang}_by']
                    self.assertIn(by, (c['listed_by'], 'ons-2021'))
                    printed = ons[c['code']] if by == 'ons-2021' else row
                    self.assertEqual(c['name_' + lang], printed['name_' + lang])

    def test_dairas(self):
        communes = {c['code']: c for c in self.communes[1]}
        self.assertEqual(len(self.dairas[1]), 538)
        for d in self.dairas[1]:
            with self.subTest(daira=d['code']):
                seat = communes[d['code']]
                self.assertEqual((seat['wilaya'], seat['daira']), (d['wilaya'], d['code']), 'the seat is in its daïra')
                self.assertEqual((d['name_fr'], d['name_ar']), (seat['name_fr'], seat['name_ar']))
                self.assertEqual(int(d['communes']), sum(1 for c in communes.values() if c['daira'] == d['code']))
                row = source_row(d['listed_by'], d['listed_article'], d['listed_item'])
                self.assertEqual(row['item'], 'seat')

    def test_changes(self):
        """Law 26-06 creates eleven wilayas and moves 108 communes to them, each cited by the
        item of the law's list that names it."""
        changes = self.changes[1]
        communes = {c['code']: c for c in self.communes[1]}
        created = [c for c in changes if c['type'] == 'wilaya_created']
        moved = [c for c in changes if c['type'] == 'commune_moved']
        self.assertEqual(len(created) + len(moved), len(changes))
        self.assertEqual([c['subject'] for c in created], [str(n) for n in range(59, 70)])
        self.assertEqual(sorted(c['subject'] for c in moved), sorted(k for k, c in communes.items() if c['wilaya_before']))
        self.assertEqual(len(moved), 108)
        aliases = {}
        for a in self.aliases[1]:
            aliases.setdefault((a['kind'], a['code']), []).append(a['name'])
        for c in changes:
            with self.subTest(change=c['subject']):
                self.assertEqual((c['date'], c['by']), ('2026-04-05', 'law-26-06'))
                if c['type'] == 'commune_moved':
                    commune = communes[c['subject']]
                    self.assertEqual((c['from'], c['to']), (commune['wilaya_before'], commune['wilaya']))
                    self.assertEqual(c['article'], resolve.law_article(c['to']))
                    row = source_row('law-26-06', c['article'], c['item'])
                    names = [commune['name_fr'], commune['name_ar']] + aliases.get(('commune', c['subject']), [])
                    self.assertTrue(row['name_fr'] in names or row['name_ar'] in names
                                    or resolve.same_commune((commune['name_fr'], commune['name_ar']),
                                                            (row['name_fr'], row['name_ar'])))

    def test_aliases(self):
        names = {('wilaya', w['code']): w for w in self.wilayas[1]}
        names.update({('daira', d['code']): d for d in self.dairas[1]})
        names.update({('commune', c['code']): c for c in self.communes[1]})
        seen = set()
        for a in self.aliases[1]:
            key = (a['kind'], a['code'], a['lang'], a['name'])
            with self.subTest(alias=key):
                self.assertNotIn(key, seen)
                seen.add(key)
                self.assertIn((a['kind'], a['code']), names)
                self.assertIn(a['lang'], ('fr', 'ar', 'en'))
                if a['lang'] != 'en':
                    self.assertFalse(resolve.same_spelling(a['name'], names[(a['kind'], a['code'])]['name_' + a['lang']]))
                    texts = a['texts'].split(' ')
                    self.assertTrue(texts)
                    for t in texts:
                        self.assertIn(t, self.texts)


if __name__ == '__main__':
    unittest.main()

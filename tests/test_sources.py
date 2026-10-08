"""Checks on the transcriptions of the official texts (data/source/) and on data/texts.csv.

    python3 -m unittest discover -s tests

Standard library only.
"""
import csv
import glob
import os
import re
import unicodedata
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
SOURCE = os.path.join(DATA, 'source')

LIST_FIELDS = ['text', 'article', 'via', 'item', 'of', 'name_fr', 'name_ar', 'check']
DECREE_FIELDS = ['text', 'article', 'item', 'name_fr', 'seat_fr', 'name_ar', 'seat_ar', 'check']
READING_FIELDS = ['text', 'article', 'item', 'edition', 'name', 'pdf_page', 'by', 'note']
TEXT_FIELDS = ['id', 'kind', 'number', 'signed', 'jo_number', 'jo_date', 'url_ar', 'url_fr', 'sha256_ar', 'sha256_fr']

# Arabic letters and the shadda, words separated by single spaces
ARABIC = re.compile(r'^[ء-يّ]+(?: [ء-يّ]+)*$')
FRENCH = re.compile(r"^[A-Za-zÀ-ÿ’']+(?:[ -][A-Za-zÀ-ÿ’']+)*$")
DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

# (article, via, count) for every list, in the order of the text
LAW_19_12 = [
    ('5', '2', 16), ('11', '2', 27), ('12', '2', 11), ('15', '2', 5), ('34', '2', 7), ('37', '2', 4),
    ('43', '2', 22), ('51', '2', 10),
    ('52 bis', '3', 10), ('52 bis 1', '3', 2), ('52 bis 2', '3', 6), ('52 bis 3', '3', 10), ('52 bis 4', '3', 3),
    ('52 bis 5', '3', 2), ('52 bis 6', '3', 14), ('52 bis 7', '3', 2), ('52 bis 8', '3', 8), ('52 bis 9', '3', 3),
]
LAW_26_06 = [
    ('7', '2', 12), ('9', '2', 53), ('11', '2', 22), ('16', '2', 24), ('17', '2', 49), ('18', '2', 36),
    ('21', '2', 18), ('30', '2', 43), ('32', '2', 24), ('36', '2', 15),
    ('52 bis 10', '3', 12), ('52 bis 11', '3', 8), ('52 bis 12', '3', 5), ('52 bis 13', '3', 4),
    ('52 bis 14', '3', 4), ('52 bis 15', '3', 6), ('52 bis 16', '3', 10), ('52 bis 17', '3', 8),
    ('52 bis 18', '3', 21), ('52 bis 19', '3', 23), ('52 bis 20', '3', 7),
]
# Each list starts with its chef-lieu: Law 26-06's ten parent wilayas
PARENTS_26_06 = ['Laghouat', 'Batna', 'Biskra', 'Tébessa', 'Tlemcen', 'Tiaret', 'Djelfa', 'Médéa', 'M’Sila', 'El Bayadh']

# Biskra is the one wilaya both laws list. Law 26-06 splits its 2019 list between
# Biskra and El Kantara, and spells some names differently (Law 19-12 -> Law 26-06).
# These become aliases (PRD §7.4).
BISKRA_SPELLINGS = {
    'name_ar': {'البرانس': 'البرانيس', 'لشانة': 'ليشانة', 'لواء': 'ليوة', 'مخادمة': 'أمخادمة', 'مليلي': 'أمليلي'},
    'name_fr': {'Khenguet Sidi Nadji': 'Khangat Sidi Nadji', "M'Lili": 'M’Lili', 'Oumach': 'Oumache'},
}


def read(path):
    with open(path, encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


def lists(text_id):
    """{article: [rows]} in the order of the text."""
    out = {}
    for row in read(os.path.join(SOURCE, text_id + '.csv'))[1]:
        out.setdefault(row['article'], []).append(row)
    return out


def loose_fr(s):
    s = unicodedata.normalize('NFKD', s.replace('’', "'"))
    return ''.join(c for c in s if not unicodedata.combining(c)).casefold()


def loose_ar(s):
    return re.sub('[أإآ]', 'ا', s)


class Files(unittest.TestCase):
    def test_csv_files_are_plain_utf8(self):
        paths = glob.glob(os.path.join(DATA, '**', '*.csv'), recursive=True)
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(path=os.path.relpath(path, ROOT)):
                with open(path, 'rb') as f:
                    raw = f.read()
                self.assertFalse(raw.startswith(b'\xef\xbb\xbf'), 'byte order mark')
                self.assertNotIn(b'\r', raw)
                self.assertTrue(raw.endswith(b'\n'))
                fields, rows = read(path)
                for row in rows:
                    self.assertNotIn(None, row, 'a row with more fields than the header')
                    self.assertNotIn(None, row.values(), 'a row with fewer fields than the header')


class Texts(unittest.TestCase):
    fields, texts = read(os.path.join(DATA, 'texts.csv'))

    def test_fields(self):
        self.assertEqual(self.fields, TEXT_FIELDS)
        ids = [t['id'] for t in self.texts]
        self.assertEqual(len(ids), len(set(ids)))

    def test_each_text(self):
        for t in self.texts:
            with self.subTest(text=t['id']):
                self.assertIn(t['kind'], ('law', 'presidential decree', 'executive decree'))
                self.assertEqual(t['id'], f"{t['kind'].replace(' ', '-')}-{t['number']}")
                self.assertRegex(t['number'], r'^\d{2}-\d{2,3}$')
                self.assertRegex(t['signed'], DATE)
                self.assertRegex(t['jo_date'], DATE)
                self.assertLessEqual(t['signed'], t['jo_date'])
                self.assertEqual(t['signed'][2:4], t['number'][:2], 'texts are numbered by the year they are signed')
                year, number = t['jo_date'][:4], int(t['jo_number'])
                for edition, folder in (('ar', 'jo-arabe'), ('fr', 'jo-francais')):
                    self.assertEqual(t['url_' + edition], f'https://www.joradp.dz/FTP/{folder}/{year}/'
                                     f'{edition[0].upper()}{year}{number:03d}.pdf')
                    self.assertRegex(t['sha256_' + edition], r'^[0-9a-f]{64}$')

    def test_every_transcription_is_of_a_known_text(self):
        ids = {t['id'] for t in self.texts}
        for path in glob.glob(os.path.join(SOURCE, '*.csv')):
            name = os.path.basename(path)[:-4]
            if name != 'readings':
                self.assertIn(name, ids)
                for row in read(path)[1]:
                    self.assertEqual(row['text'], name)


class Lists(unittest.TestCase):
    """The lists of communes in the laws that amend Law 84-09."""

    def check_text(self, text_id, expected):
        fields, rows = read(os.path.join(SOURCE, text_id + '.csv'))
        self.assertEqual(fields, LIST_FIELDS)
        found = lists(text_id)
        self.assertEqual([(a, l[0]['via'], len(l)) for a, l in found.items()], expected)
        seen = []
        for row in rows:  # each list is in one piece, numbered 1 to its count
            if not seen or seen[-1] != row['article']:
                self.assertNotIn(row['article'], seen)
                seen.append(row['article'])
        for article, items in found.items():
            with self.subTest(text=text_id, article=article):
                self.assertEqual([r['item'] for r in items], [str(n) for n in range(1, len(items) + 1)])
                self.assertEqual({r['of'] for r in items}, {str(len(items))})
                for r in items:
                    self.assertRegex(r['name_fr'], FRENCH)
                    self.assertRegex(r['name_ar'], ARABIC)
                    self.assertIn(r['check'], ('', 'eye'), 'every name is checked: two readings agree, or it was read on the page')
        return found

    def test_law_19_12(self):
        found = self.check_text('law-19-12', LAW_19_12)
        self.assertEqual(sum(len(l) for a, l in found.items() if a.startswith('52 bis')), 60)

    def test_law_26_06(self):
        found = self.check_text('law-26-06', LAW_26_06)
        self.assertEqual(sum(len(l) for a, l in found.items() if a.startswith('52 bis')), 108)
        self.assertEqual([l[0]['name_fr'] for a, l in found.items() if not a.startswith('52 bis')], PARENTS_26_06)

    def test_biskra_is_split_between_biskra_and_el_kantara(self):
        before, after = lists('law-19-12'), lists('law-26-06')
        for edition, spellings in BISKRA_SPELLINGS.items():
            with self.subTest(edition=edition):
                old = sorted(spellings.get(r[edition], r[edition]) for r in before['11'])
                new = sorted(r[edition] for r in after['11'] + after['52 bis 12'])
                self.assertEqual(old, new)


class Decree(unittest.TestCase):
    """Decree 26-206: the names and chefs-lieux of wilayas 59 to 69."""
    fields, rows = read(os.path.join(SOURCE, 'presidential-decree-26-206.csv'))

    def test_entries(self):
        self.assertEqual(self.fields, DECREE_FIELDS)
        self.assertEqual([r['item'] for r in self.rows], [str(n) for n in range(59, 70)])
        for r in self.rows:
            with self.subTest(wilaya=r['item']):
                self.assertEqual(r['article'], '1')
                for key in ('name_fr', 'seat_fr'):
                    self.assertRegex(r[key], FRENCH)
                for key in ('name_ar', 'seat_ar'):
                    self.assertRegex(r[key], ARABIC)
                self.assertIn(r['check'], ('', 'eye'))

    def test_each_chef_lieu_heads_its_list_in_law_26_06(self):
        """Wilaya 59 is the one in article 52 bis 10, and so on in order. The texts
        spell some names differently (آفلو and أفلو; Bou Saada and Bou Saâda)."""
        new = lists('law-26-06')
        for r in self.rows:
            with self.subTest(wilaya=r['item']):
                first = new[f"52 bis {int(r['item']) - 49}"][0]
                self.assertEqual(loose_fr(first['name_fr']), loose_fr(r['seat_fr']))
                self.assertEqual(loose_ar(first['name_ar']), loose_ar(r['seat_ar']))


class Readings(unittest.TestCase):
    """data/source/readings.csv: the names read on the rendered page, and who read them."""
    fields, readings = read(os.path.join(SOURCE, 'readings.csv'))

    @staticmethod
    def row_names(text_id):
        """{(article, item, edition): name as the reading records it}, for rows read by eye."""
        out = {}
        for r in read(os.path.join(SOURCE, text_id + '.csv'))[1]:
            if r['check'] != 'eye':
                continue
            key = (r['article'], r['item'])
            if 'seat_ar' in r:
                out[key + ('ar',)] = f"ولاية {r['name_ar']}، مقرها مدينة {r['seat_ar']}"
                out[key + ('fr',)] = None
            else:
                out[key + ('ar',)], out[key + ('fr',)] = r['name_ar'], r['name_fr']
        return out

    def test_fields(self):
        self.assertEqual(self.fields, READING_FIELDS)
        keys = [(r['text'], r['article'], r['item'], r['edition']) for r in self.readings]
        self.assertEqual(len(keys), len(set(keys)))

    def test_readings_match_the_rows_read_by_eye(self):
        texts = sorted({r['text'] for r in self.readings})
        rows = {t: self.row_names(t) for t in texts}
        for r in self.readings:
            with self.subTest(text=r['text'], article=r['article'], item=r['item']):
                self.assertIn(r['edition'], ('ar', 'fr'))
                self.assertRegex(r['pdf_page'], r'^\d+$')
                self.assertIn(r['by'], ('claude', 'founder'))
                self.assertTrue(r['note'])
                self.assertEqual(rows[r['text']].get((r['article'], r['item'], r['edition'])), r['name'])
        # and every row read by eye has its reading
        read_keys = {(r['text'], r['article'], r['item']) for r in self.readings}
        for path in glob.glob(os.path.join(SOURCE, '*.csv')):
            text_id = os.path.basename(path)[:-4]
            if text_id == 'readings':
                continue
            for r in read(path)[1]:
                if r['check'] == 'eye':
                    self.assertIn((text_id, r['article'], r['item']), read_keys)


if __name__ == '__main__':
    unittest.main()

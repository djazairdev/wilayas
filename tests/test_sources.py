"""Checks on the transcriptions of the official texts and of ONS's code géographique (data/source/),
and on data/texts.csv and data/ons.csv.

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
DAIRA_FIELDS = ['text', 'wilaya', 'daira', 'item', 'name_fr', 'name_ar', 'check']
READING_FIELDS = ['text', 'article', 'item', 'edition', 'name', 'pdf_page', 'by', 'reviewed_by', 'note']
TEXT_FIELDS = ['id', 'kind', 'number', 'signed', 'jo_number', 'jo_date', 'url_ar', 'url_fr', 'sha256_ar', 'sha256_fr']
ONS_FIELDS = ['id', 'title', 'published', 'url', 'sha256']
CODE_FIELDS = ['text', 'wilaya', 'commune', 'name_fr', 'name_ar', 'check']

# Arabic letters and the shadda, words separated by single spaces
ARABIC = re.compile(r'^[ء-يّ]+(?: [ء-يّ]+)*$')
# Decree 91-306 is a scan, transcribed without harakat; it prints ڤ for the sound g
ARABIC_SCAN = re.compile(r'^[ء-يڤ]+(?: [ء-يڤ]+)*$')
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
ORDINANCE_21_03 = [('34', '2', 8), ('52 bis 6', '2', 13)]
# Each list starts with its chef-lieu: Law 26-06's ten parent wilayas
PARENTS_26_06 = ['Laghouat', 'Batna', 'Biskra', 'Tébessa', 'Tlemcen', 'Tiaret', 'Djelfa', 'Médéa', 'M’Sila', 'El Bayadh']

# Biskra is the one wilaya both laws list. Law 26-06 splits its 2019 list between
# Biskra and El Kantara, and spells some names differently (Law 19-12 -> Law 26-06).
# These become aliases (data/source/README.md, Spellings).
BISKRA_SPELLINGS = {
    'name_ar': {'البرانس': 'البرانيس', 'لشانة': 'ليشانة', 'لواء': 'ليوة', 'مخادمة': 'أمخادمة', 'مليلي': 'أمليلي'},
    'name_fr': {'Khenguet Sidi Nadji': 'Khangat Sidi Nadji', "M'Lili": 'M’Lili', 'Oumach': 'Oumache'},
}
# Ordinance 21-03 moves El Borma from Touggourt back to Ouargla, and spells some names
# differently (Law 19-12 -> Ordinance 21-03)
OUARGLA_SPELLINGS = {
    'name_ar': {'حاسي بن عبد اللّه': 'حاسي بن عبد الله'},
    'name_fr': {'Aïn Beïda': 'Ain Beida', 'Blidat Ameur': 'Blidate Ameur', "M'Naguar": 'M’Naguar'},
}

# The decrees completing Decree 84-79: the wilayas each one names, and the law whose new
# lists they head (wilaya 49 is the one in article 52 bis, 50 in 52 bis 1, and so on)
DECREES = {
    'presidential-decree-21-117': (range(49, 59), 'law-19-12'),
    'presidential-decree-26-206': (range(59, 70), 'law-26-06'),
}
# Chefs-lieux the decree spells differently from the law's list (decree -> law)
SEAT_SPELLINGS = {'El M’Ghaier': 'El Megaier'}

# Decree 91-306 lists 553 daïras in the 48 wilayas. The French has 1,540 communes and leaves out
# Rouissat: 1,541. The rows only one edition prints are all in the Arabic:
# (wilaya, daïra, item) -> the name.
GAPS_91_306 = {
    ('18', '10', '3'): 'بني ياجيس',  # the French prints Boudria Beniyadjis as one commune, the Arabic as two
    ('30', '10', '2'): 'الرويسات',   # Rouissat, which the French leaves out
    ('34', '3', '4'): 'تكستين',      # Tixter again: both editions list it in 34 9/2
}
# Seats printed with a lower-case l
SEATS_NOT_IN_CAPITALS = {'El HACHIMIA', 'OUED El ABTAL'}
# Seats named or spelled differently from the commune that heads their list (seat -> commune)
SEAT_SPELLINGS_91_306 = {
    'fr': {'AIN DJASSER': 'Aïn Djassar', 'BEDJIA': 'Béjaia', 'BENNI YENNI': 'Béni Yenni', 'BOUTLETIS': 'Boutlelis',
           'EL MALAH': 'El Maleh', 'GUENZET': 'Gunzet', 'GUIDJEL': 'Guijel', 'IFRI OUZELLAGUENE': 'Ouzellaguène',
           'MARSA BEN MEHDI': 'Marsa Ben M’Hidi', 'MOSTEFA BEN BRAHIM': 'Mostepha Ben Brahim',
           'OULED ATTIA': 'Ouled Atia'},
    'ar': {'الرغاية': 'رغاية', 'عين الكحيل': 'عين الكيحل', 'عين موسى': 'عمي موسى'},
}


# Decree 26-253 rewrites the daïra tables of the 21 wilayas Law 26-06 touched: its ten parent
# wilayas and the eleven it creates. The annex says the others are unchanged.
WILAYAS_26_253 = ['03', '05', '07', '12', '13', '14', '17', '26', '28', '32'] + [str(n) for n in range(59, 70)]
# Communes the decree spells differently from Law 26-06's lists, beyond accents, apostrophes,
# capitals, hamzas and the dots of a final ي or ة (decree -> law)
SPELLINGS_26_253 = {'fr': {'Béni Yaagoub': 'Ben Yaagoub', 'El Azizia': 'Al Azizia', 'Bougtoub': 'Bougtob'},
                    'ar': {'سيدي عبد الرحمن': 'سيدي عبد الرحمان'}}

# ONS's code géographique of 2021 prints its French names in capitals; two abbreviate, and one
# Arabic name abbreviates with dots
ONS_FRENCH = re.compile(r"^[A-Z’']+(?: [A-Z’']+)*$")
ONS_ABBREVIATED = {'0230': ('OULED BEN.AEK', None), '0809': ('MECHRAA H. BOUMEDIENE', None),
                   '4309': (None, 'بن يحي .ع. رحمان')}

# Ordinance 97-14 detaches communes from Boumerdès (article 2), Tipaza (3) and Blida (4), and
# article 5 attaches them to Algiers: article -> (the wilaya it detaches them from, how many)
ORDINANCE_97_14 = {'2': ('35', 6), '3': ('42', 14), '4': ('09', 4)}
ORDINANCE_97_14_FIELDS = ['text', 'article', 'item', 'name_fr', 'name_ar', 'check']
# Communes neither of whose names is the one Decree 91-306 gives them in their old wilaya (97-14 -> 91-306)
SPELLINGS_97_14 = {('Khraïcia', 'خرايسية'): ('Khraissia', 'الخرايصية')}
# ONS numbers the 24 after Algiers' 33, as 34 to 57: article 4's, then 2's, then 3's, each in the
# ordinance's order. Names it spells differently (97-14 -> ONS), beyond accents, hyphens and capitals
ONS_ALGIERS = ['4', '2', '3']
ONS_SPELLINGS_97_14 = {
    'fr': {'Heraoua': 'HARAOUA', 'Mâalma': 'MAHELMA', 'Baba Hassen': 'BABA HASSAN'},
    'ar': {'تسالة المرجة': 'تسالة المرجى', 'أولاد شبل': 'أولاد الشبل', 'هراوة': 'الهراوة', 'الرغاية': 'رغاية',
           'السويدانية': 'سويدانية', 'الدرارية': 'درارية'},
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


def row_key(r):
    """(article, item) of a transcribed row, as readings.csv names it: for the daïra decrees,
    the wilaya and 'daïra/item'; for ONS's list, the wilaya and the commune."""
    if 'commune' in r:
        return r['wilaya'], r['commune']
    return (r['wilaya'], f"{r['daira']}/{r['item']}") if 'wilaya' in r else (r['article'], r['item'])


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
                self.assertIn(t['kind'], ('law', 'ordinance', 'presidential decree', 'executive decree'))
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
        ids = {t['id'] for t in self.texts} | {t['id'] for t in read(os.path.join(DATA, 'ons.csv'))[1]}
        for path in glob.glob(os.path.join(SOURCE, '*.csv')):
            name = os.path.basename(path)[:-4]
            if name != 'readings':
                self.assertIn(name, ids)
                for row in read(path)[1]:
                    self.assertEqual(row['text'], name)


class Lists(unittest.TestCase):
    """The lists of communes in the laws and the ordinance that amend Law 84-09."""

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

    def test_ordinance_21_03(self):
        found = self.check_text('ordinance-21-03', ORDINANCE_21_03)
        before = lists('law-19-12')
        self.assertEqual(before['52 bis 6'][-1]['name_fr'], 'El Borma')
        self.assertEqual(found['34'][-1]['name_fr'], 'El Borma')
        for edition, spellings in OUARGLA_SPELLINGS.items():
            with self.subTest(edition=edition):
                old = [spellings.get(r[edition], r[edition]) for r in before['34'] + before['52 bis 6']]
                new = [r[edition] for r in found['34'] + found['52 bis 6']]
                self.assertEqual(sorted(old), sorted(new))

    def test_biskra_is_split_between_biskra_and_el_kantara(self):
        before, after = lists('law-19-12'), lists('law-26-06')
        for edition, spellings in BISKRA_SPELLINGS.items():
            with self.subTest(edition=edition):
                old = sorted(spellings.get(r[edition], r[edition]) for r in before['11'])
                new = sorted(r[edition] for r in after['11'] + after['52 bis 12'])
                self.assertEqual(old, new)


class Ordinance9714(unittest.TestCase):
    """Ordinance 97-14 of 31 May 1997: the communes it moves to Algiers. Both editions are scans,
    transcribed without harakat."""
    fields, rows = read(os.path.join(SOURCE, 'ordinance-97-14.csv'))

    def test_fields(self):
        self.assertEqual(self.fields, ORDINANCE_97_14_FIELDS)

    def test_articles(self):
        found = lists('ordinance-97-14')
        self.assertEqual({a: len(l) for a, l in found.items()}, {a: n for a, (_, n) in ORDINANCE_97_14.items()})
        self.assertEqual(list(found), sorted(found))
        for article, items in found.items():
            self.assertEqual([r['item'] for r in items], [str(n) for n in range(1, len(items) + 1)])
            for r in items:
                with self.subTest(article=article, item=r['item']):
                    self.assertRegex(r['name_fr'], FRENCH)
                    self.assertRegex(r['name_ar'], ARABIC_SCAN)
                    self.assertIn(r['check'], ('', 'eye'), 'every name is checked: two readings agree, or it was read on the page')

    def test_each_commune_was_in_the_wilaya_it_leaves(self):
        """Each commune is one of its old wilaya's in Decree 91-306, by its French or its Arabic name."""
        decree = [r for r in read(os.path.join(SOURCE, 'executive-decree-91-306.csv'))[1] if r['item'] != 'seat']
        for r in self.rows:
            with self.subTest(article=r['article'], item=r['item']):
                fr, ar = SPELLINGS_97_14.get((r['name_fr'], r['name_ar']), (r['name_fr'], r['name_ar']))
                wilaya = [d for d in decree if d['wilaya'] == ORDINANCE_97_14[r['article']][0]]
                self.assertTrue([d for d in wilaya if loose_fr(d['name_fr']).replace('-', ' ') == loose_fr(fr).replace('-', ' ')
                                 or loose_ar(d['name_ar']) == loose_ar(ar)])

    def test_ons_numbers_them_after_algiers_own(self):
        found = lists('ordinance-97-14')
        moved = [r for a in ONS_ALGIERS for r in found[a]]
        ons = [r for r in read(os.path.join(SOURCE, 'ons-2021.csv'))[1] if r['wilaya'] == '16']
        self.assertEqual([r['commune'] for r in ons[-len(moved):]], [f'{n:02d}' for n in range(34, 58)])
        for r, o in zip(moved, ons[-len(moved):]):
            with self.subTest(commune=o['commune']):
                fr = ONS_SPELLINGS_97_14['fr'].get(r['name_fr'], r['name_fr'])
                self.assertEqual(loose_fr(fr).replace('-', ' ').upper(), loose_fr(o['name_fr']).upper())
                self.assertEqual(ONS_SPELLINGS_97_14['ar'].get(r['name_ar'], r['name_ar']), o['name_ar'])


class Decrees(unittest.TestCase):
    """Decrees 21-117 and 26-206: the names and chefs-lieux of wilayas 49 to 58 and 59 to 69."""

    def test_entries(self):
        for text, (codes, _) in DECREES.items():
            fields, rows = read(os.path.join(SOURCE, text + '.csv'))
            with self.subTest(text=text):
                self.assertEqual(fields, DECREE_FIELDS)
                self.assertEqual([r['item'] for r in rows], [str(n) for n in codes])
            for r in rows:
                with self.subTest(text=text, wilaya=r['item']):
                    self.assertEqual(r['article'], '1')
                    for key in ('name_fr', 'seat_fr'):
                        self.assertRegex(r[key], FRENCH)
                    for key in ('name_ar', 'seat_ar'):
                        self.assertRegex(r[key], ARABIC)
                    self.assertIn(r['check'], ('', 'eye'))

    def test_each_chef_lieu_heads_its_list(self):
        """The texts spell some names differently (آفلو and أفلو; Bou Saada and Bou Saâda;
        El M’Ghaier and El Megaier)."""
        for text, (_, law) in DECREES.items():
            new = lists(law)
            for r in read(os.path.join(SOURCE, text + '.csv'))[1]:
                n = int(r['item']) - 49
                with self.subTest(text=text, wilaya=r['item']):
                    first = new['52 bis' + (f' {n}' if n else '')][0]
                    seat = SEAT_SPELLINGS.get(r['seat_fr'], r['seat_fr'])
                    self.assertEqual(loose_fr(first['name_fr']), loose_fr(seat))
                    self.assertEqual(loose_ar(first['name_ar']), loose_ar(r['seat_ar']))


class Dairas(unittest.TestCase):
    """Executive Decree 91-306: the daïras of each wilaya, each with its seat and the communes
    its chef de daïra runs."""
    fields, rows = read(os.path.join(SOURCE, 'executive-decree-91-306.csv'))

    def dairas(self):
        """{(wilaya, daïra): [rows]} in the order of the text, the seat first."""
        out = {}
        for r in self.rows:
            out.setdefault((r['wilaya'], r['daira']), []).append(r)
        return out

    def test_fields(self):
        self.assertEqual(self.fields, DAIRA_FIELDS)
        self.assertEqual({r['text'] for r in self.rows}, {'executive-decree-91-306'})

    def test_layout(self):
        """The 48 wilayas in order, each with its daïras numbered from 1; each daïra is its seat,
        then its communes numbered from 1."""
        dairas = self.dairas()
        self.assertEqual(len(dairas), 553)
        wilayas = list(dict.fromkeys(w for w, d in dairas))
        self.assertEqual(wilayas, [f'{n:02d}' for n in range(1, 49)])
        for w in wilayas:
            numbers = [d for x, d in dairas if x == w]
            self.assertEqual(numbers, [str(n) for n in range(1, len(numbers) + 1)])
        for key, rows in dairas.items():
            with self.subTest(daira=key):
                self.assertGreater(len(rows), 1)
                self.assertEqual([r['item'] for r in rows], ['seat'] + [str(n) for n in range(1, len(rows))])

    def test_communes(self):
        communes = [r for r in self.rows if r['item'] != 'seat']
        self.assertEqual(sum(1 for r in communes if r['name_fr']), 1540)
        self.assertEqual(sum(1 for r in communes if r['name_ar']), 1540 + len(GAPS_91_306))

    def test_names(self):
        for r in self.rows:
            key = (r['wilaya'], r['daira'], r['item'])
            with self.subTest(row=key):
                self.assertIn(r['check'], ('', 'eye'), 'every name is checked: two readings agree, or it was read on the page')
                if key in GAPS_91_306:
                    self.assertEqual((r['name_fr'], r['name_ar']), ('', GAPS_91_306[key]))
                    continue
                self.assertRegex(r['name_fr'], FRENCH)
                self.assertRegex(r['name_ar'], ARABIC_SCAN)
                if r['item'] == 'seat' and r['name_fr'] not in SEATS_NOT_IN_CAPITALS:
                    self.assertEqual(r['name_fr'], r['name_fr'].upper(), 'the French prints the seats in capitals')

    def test_each_seat_heads_its_list(self):
        """A daïra's seat is the first commune of its list, but for the names in SEAT_SPELLINGS_91_306.
        The seats are in capitals without accents, and the Arabic writes final ي and ة with or
        without their dots."""
        loose = {'fr': lambda s: loose_fr(s).replace('-', ' '),
                 'ar': lambda s: loose_ar(s).replace('ى', 'ي').replace('ة', 'ه')}
        for key, rows in self.dairas().items():
            seat, first = rows[0], rows[1]
            for edition in ('fr', 'ar'):
                with self.subTest(daira=key, edition=edition):
                    name = seat['name_' + edition]
                    name = SEAT_SPELLINGS_91_306[edition].get(name, name)
                    self.assertEqual(loose[edition](name), loose[edition](first['name_' + edition]))


class Dairas2026(unittest.TestCase):
    """Executive Decree 26-253: the daïra tables of the 21 wilayas Law 26-06 touched, each daïra
    with its seat and the communes its chef de daïra runs."""
    fields, rows = read(os.path.join(SOURCE, 'executive-decree-26-253.csv'))

    def dairas(self):
        """{(wilaya, daïra): [rows]} in the order of the text, the seat first."""
        out = {}
        for r in self.rows:
            out.setdefault((r['wilaya'], r['daira']), []).append(r)
        return out

    def test_fields(self):
        self.assertEqual(self.fields, DAIRA_FIELDS)
        self.assertEqual({r['text'] for r in self.rows}, {'executive-decree-26-253'})

    def test_layout(self):
        """The 21 wilayas in order, each with its daïras numbered from 1; each daïra is its seat,
        then its communes numbered from 1."""
        dairas = self.dairas()
        self.assertEqual(len(dairas), 142)
        wilayas = list(dict.fromkeys(w for w, d in dairas))
        self.assertEqual(wilayas, WILAYAS_26_253)
        for w in wilayas:
            numbers = [d for x, d in dairas if x == w]
            self.assertEqual(numbers, [str(n) for n in range(1, len(numbers) + 1)])
        for key, rows in dairas.items():
            with self.subTest(daira=key):
                self.assertGreater(len(rows), 1)
                self.assertEqual([r['item'] for r in rows], ['seat'] + [str(n) for n in range(1, len(rows))])

    def test_names(self):
        for r in self.rows:
            with self.subTest(row=(r['wilaya'], r['daira'], r['item'])):
                self.assertIn(r['check'], ('', 'eye'), 'every name is checked: two readings agree, or it was read on the page')
                self.assertRegex(r['name_fr'], FRENCH)
                self.assertRegex(r['name_ar'], ARABIC)

    def test_same_communes_as_law_26_06(self):
        """Each wilaya's daïras share out the communes Law 26-06 lists for it, spelled the same
        but for SPELLINGS_26_253."""
        law = lists('law-26-06')
        loose = {'fr': loose_fr, 'ar': lambda s: loose_ar(s).replace('ى', 'ي').replace('ة', 'ه')}
        for wilaya in WILAYAS_26_253:
            article = str(int(wilaya) + 4) if int(wilaya) < 59 else f'52 bis {int(wilaya) - 49}'
            mine = [r for r in self.rows if r['wilaya'] == wilaya and r['item'] != 'seat']
            for edition in ('fr', 'ar'):
                with self.subTest(wilaya=wilaya, edition=edition):
                    spelled = SPELLINGS_26_253[edition]
                    self.assertEqual(sorted(loose[edition](spelled.get(r['name_' + edition], r['name_' + edition])) for r in mine),
                                     sorted(loose[edition](r['name_' + edition]) for r in law[article]))

    def test_each_seat_heads_its_list(self):
        """A daïra's seat is the first commune of its list, spelled the same but for an accent, an
        apostrophe or a capital, and in Arabic a hamza."""
        for key, rows in self.dairas().items():
            seat, first = rows[0], rows[1]
            with self.subTest(daira=key):
                self.assertEqual(loose_fr(seat['name_fr']), loose_fr(first['name_fr']))
                self.assertEqual(loose_ar(seat['name_ar']), loose_ar(first['name_ar']))


class Ons(unittest.TestCase):
    """ONS's code géographique national of June 2021: the code of each of the 1,541 communes of the
    58 wilayas, with their names as printed."""
    fields, rows = read(os.path.join(SOURCE, 'ons-2021.csv'))

    def test_sources(self):
        fields, lists = read(os.path.join(DATA, 'ons.csv'))
        self.assertEqual(fields, ONS_FIELDS)
        for t in lists:
            with self.subTest(list=t['id']):
                self.assertRegex(t['id'], r'^ons-\d{4}$')
                self.assertEqual(t['published'][:4], t['id'][4:])
                self.assertRegex(t['published'], r'^\d{4}(-\d{2})?$')
                self.assertTrue(t['url'].startswith('https://www.ons.dz/IMG/'))
                self.assertRegex(t['sha256'], r'^[0-9a-f]{64}$')

    def test_fields(self):
        self.assertEqual(self.fields, CODE_FIELDS)

    def test_codes(self):
        codes = [r['wilaya'] + r['commune'] for r in self.rows]
        self.assertEqual(len(codes), 1541)
        self.assertEqual(len(set(codes)), len(codes))
        self.assertEqual(sorted({r['wilaya'] for r in self.rows}), [f'{n:02d}' for n in range(1, 59)])
        for r in self.rows:
            self.assertRegex(r['commune'], r'^\d{2}$')
            self.assertNotEqual(r['commune'], '00')
        # each wilaya's communes in the order of their codes, gaps and all
        for w in {r['wilaya'] for r in self.rows}:
            numbers = [r['commune'] for r in self.rows if r['wilaya'] == w]
            self.assertEqual(numbers, sorted(numbers), w)

    def test_names(self):
        for r in self.rows:
            with self.subTest(code=r['wilaya'] + r['commune']):
                self.assertEqual(r['text'], 'ons-2021')
                self.assertIn(r['check'], ('', 'eye'))
                fr, ar = ONS_ABBREVIATED.get(r['wilaya'] + r['commune'], (None, None))
                self.assertEqual(r['name_fr'], fr) if fr else self.assertRegex(r['name_fr'], ONS_FRENCH)
                self.assertEqual(r['name_ar'], ar) if ar else self.assertRegex(r['name_ar'], ARABIC)

    def test_communes_per_wilaya(self):
        """As many communes in each wilaya as the texts give it: Decree 91-306 for the wilayas the
        2019 reform left alone, less the communes Ordinance 97-14 moves to Algiers, and the lists
        of Law 19-12, or of Ordinance 21-03 where it rewrote them, for the others (article 5 of
        Law 84-09 is wilaya 01, 52 bis is 49)."""
        gaps = {('18', '10', '3'), ('34', '3', '4')}  # the Arabic's extra lines in Decree 91-306
        expected = {}
        for r in read(os.path.join(SOURCE, 'executive-decree-91-306.csv'))[1]:
            if r['item'] != 'seat' and (r['wilaya'], r['daira'], r['item']) not in gaps:
                expected[r['wilaya']] = expected.get(r['wilaya'], 0) + 1
        for article, (wilaya, count) in ORDINANCE_97_14.items():
            expected[wilaya] -= count
            expected['16'] += count
        for text_id in ('law-19-12', 'ordinance-21-03'):
            for article, rows in lists(text_id).items():
                rest = article[len('52 bis'):].strip() if article.startswith('52 bis') else None
                wilaya = 49 + int(rest or 0) if rest is not None else int(article) - 4
                expected[f'{wilaya:02d}'] = len(rows)
        got = {}
        for r in self.rows:
            got[r['wilaya']] = got.get(r['wilaya'], 0) + 1
        self.assertEqual(sum(got.values()), sum(expected.values()))
        differ = {w: (got.get(w), expected.get(w)) for w in sorted(set(got) | set(expected)) if got.get(w) != expected.get(w)}
        self.assertEqual(differ, {})


class Readings(unittest.TestCase):
    """data/source/readings.csv: the names read on the rendered page, who read them and who
    checked the reading on the page afterwards."""
    fields, readings = read(os.path.join(SOURCE, 'readings.csv'))

    @staticmethod
    def row_names(text_id):
        """{(article, item, edition): name as the reading records it}, for rows read by eye."""
        out = {}
        for r in read(os.path.join(SOURCE, text_id + '.csv'))[1]:
            if r['check'] != 'eye':
                continue
            key = row_key(r)
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
                self.assertIn(r['reviewed_by'], ('', 'founder'))
                if r['reviewed_by']:
                    self.assertNotEqual(r['reviewed_by'], r['by'], 'a reading is reviewed by someone else')
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
                    self.assertIn((text_id,) + row_key(r), read_keys)


if __name__ == '__main__':
    unittest.main()

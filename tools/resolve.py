"""Build the API's tables in data/ from the transcriptions in data/source/: wilayas.csv,
dairas.csv, communes.csv, changes.csv and aliases.csv.

Decree 91-306 gives the daïras of 1991 and the communes of each. The later texts are applied in
order, each commune keeping its identity from one to the next:

- Decree 92-66 redraws daïras in seven wilayas;
- Ordinance 97-14 moves 24 communes to Algiers, without placing them in a daïra;
- Decree 18-302 redraws daïras in three wilayas;
- Decree 21-198 rewrites the tables of the 18 wilayas Law 19-12 changed or created.

That is June 2021, when ONS's code géographique gives each wilaya's communes their codes: each
commune is paired with the one code whose names are its own, but for spelling (same_commune), or
by ONS_NAMES. Then:

- Decree 25-87 redraws daïras in Tlemcen;
- Decree 26-253 rewrites the tables of the 21 wilayas Law 26-06 changed or created, whose
  communes are paired with the codes of the ten wilayas Law 26-06 took them from.

A commune's names are those of the latest of these texts that lists it, but
for the two communes ONS lists under a new name that no later text prints (RENAMED), and for the
Arabic name Decree 91-306 prints on two lines (ARABIC_FROM_ONS). The wilayas' names and
chefs-lieux are those of Decrees 84-79, 21-117 and 26-206. Every other spelling of a name in
these texts is an alias.

A daïra is identified by its seat's commune code, and named after that commune. Algiers' communes
have no daïra: in 1991 Algiers had 12, Ordinance 97-14 added 24 communes it placed in none, and
the later organisation of Algiers is not transcribed. Two daïras of Blida and Boumerdès lose their
seat to Algiers in 1997, and their other communes have no daïra either (SEAT_MOVED;
data/README.md).

    python3 tools/resolve.py         # writes the five tables
    python3 tools/resolve.py --check # fails if they differ from what the sources give

Standard library only.
"""
import csv
import io
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
SOURCE = os.path.join(DATA, 'source')

# Decree 91-306's lines only its Arabic prints: (wilaya, daïra, item). Rouissat is a commune
# the French leaves out; the other two are not communes (data/source/README.md).
ROUISSAT_91_306 = ('30', '10', '2')
# Decree 92-66 spells two communes otherwise than Decree 91-306 in both editions (92-66 -> 91-306)
SPELLINGS_92_66 = {('Oultem', 'ولتام'): ('Oultene', 'ولتان'), ('Touarga', 'توارقة'): ('Taourga', 'تورقة')}
# Ordinance 97-14 detaches communes from Boumerdès (article 2), Tipaza (3) and Blida (4), and
# article 5 attaches them to Algiers: article -> (the wilaya it detaches them from, how many)
ORDINANCE_97_14 = {'2': ('35', 6), '3': ('42', 14), '4': ('09', 4)}
# A commune neither of whose names is the one Decree 91-306 gives it in its old wilaya (97-14 -> 91-306)
SPELLINGS_97_14 = {('Khraïcia', 'خرايسية'): ('Khraissia', 'الخرايصية')}
# The daïras an amendment leaves without communes, by their seats in Decree 91-306: Decree 92-66
# moves Chebli's to Bouinan, and Ordinance 97-14 moves to Algiers all the communes of six
EMPTIED = {
    'executive-decree-92-66': {('09', 'CHEBLI')},
    'ordinance-97-14': {('09', 'BIRTOUTA'), ('35', 'ROUIBA'), ('42', 'CHERAGA'), ('42', 'DOUERA'), ('42', 'DRARIA'),
                        ('42', 'ZERALDA')},
}
# The wilayas whose tables Decrees 21-198 and 26-253 rewrite or add
WILAYAS_21_198 = ['01', '07', '08', '11', '30', '33', '39', '47'] + [str(n) for n in range(49, 59)]
# Communes Decree 21-198 names otherwise than the latest text before it, Decree 91-306, beyond
# accents, apostrophes, hyphens, spaces, capitals, hamzas and the dots of a final ي or ة
# (21-198 -> 91-306). Decree 91-306 named the commune of Abalessa after Silet, a place in it. M'Rara
# is M'Ghagha only by elimination: the one commune of 57 and the one of 39 left once the others
# are paired.
PAIRS_21_198 = {
    ('Tamast', 'تاماست'): ('Tamest', 'تامست'), ('Abalessa', 'أباليسا'): ('Silet Abalessa', 'سيلات أباليسا'),
    ('Beni Guecha', 'بني قشة'): ('Ben Guecha', 'بني ڤشة'), ('Mih Ouansa', 'ميه ونسى'): ('Mih Ouensa', 'مية وانسة'),
    ('Oued El Alenda', 'وادي العلندة'): ('Oued Allenda', 'وادي العندلة'),
    ('Fouggaret Ezzaouia', 'فقارت الزاوية'): ('Foggaret Ezzouaoua', 'فقارات الزاوية'),
    ('M’Rara', 'مرارة'): ('M’Ghagha', 'مغاغة'),
}
WILAYAS_26_253 = ['03', '05', '07', '12', '13', '14', '17', '26', '28', '32'] + [str(n) for n in range(59, 70)]
# Communes Decree 26-253 names otherwise than any text before it, beyond accents, apostrophes,
# hyphens, spaces, capitals, hamzas and the dots of a final ي or ة: by its names, ONS's of 2021.
# Each is the one name of its wilaya left once the others are paired, and the one commune of the
# wilaya it comes from. Law 26-06 spells them as the decree does.
PAIRS_26_253 = {
    ('Azaïls', 'لعزايل'): ('AZAILES', 'العزايل'), ('Moudjbara', 'المجبارة'): ('MOUDJEBARA', 'مجبارة'),
    ('Béni Yaagoub', 'بن يعقوب'): ('BENI YAGOUB', 'بنى يعقوب'), ('Tamezguida', 'تمزقيدة'): ('TAMESGUIDA', 'تامسقيدة'),
    ('Eddouair', 'الدواير'): ('TLATET EDDOUAIR', 'ثلاثة دوائر'), ('Hadj Mechri', 'الحاج المشري'): ('HADJ MECHERI', 'حاج مشري'),
    ('M’Doukal', 'امدوكال'): ('AMDOUKEL', 'إمدوكل'), ('Abdelkader Azil', 'عبد القادر عزيل'): ('AZIL ABDELKADER', 'عزيل عبد القادر'),
}
# The communes ONS's list of 2021 names otherwise than the decrees: by its code, the French name
# the latest decree prints. Most are spellings; some communes were renamed after 1991
# (Hamma Annassers is ONS's Mohamed Belouizdad).
ONS_NAMES = {
    '0203': 'Benaria', '0233': 'Oum Drou', '0420': 'Ouled Zoui', '0425': 'Aïn Fekroun', '0511': 'Inoughissen',
    '0515': 'Metkaouek', '0539': 'Guecha', '0555': 'M’Doukel', '0610': 'Thinabdher', '0618': 'Iflaine El Maten',
    '0912': 'Hammam El Ouane', '0913': 'Ben Khellil', '1006': 'Hanif', '1011': 'Mesdour', '1037': 'M’Chedellah',
    '1043': 'Taourirt', '1216': 'Ghorriguer', '1225': 'Boulhef Dyn', '1311': 'Oued Chouli', '1321': 'Azail',
    '1325': 'Aïn Nahala', '1331': 'Ain Fetah', '1348': 'Béni Khaled', '1424': 'Djillali Ben Amar',
    '1437': 'Takhmaret', '1438': 'Sidi Abderrahmane', '1439': 'Serguine', '1506': 'Mechtras',
    '1513': 'Aït Chaffa', '1521': 'Larbaa Nath-Iraten', '1539': 'Djebel Aïssa Mimoun', '1546': 'Béni Zeki',
    '1604': 'Hamma Annassers', '1606': 'Bologhine', '1623': 'Dely Ibrahim', '1631': 'Maquaria',
    '1641': 'Heraoua', '1702': 'Mouadjebar', '1719': 'Sidi Ladjel', '1724': 'Oum El Adham', '1735': 'Aïn Feka',
    '1821': 'Ouled Yahia khadrouche', '1823': 'Khier Oued Adjoul', '1932': 'Hammam Sokhna',
    '1953': 'Beni Oussine', '1957': 'Oued Bared', '1960': 'Telaa', '2108': 'Benazouz', '2136': 'Khenag Mayoun',
    '2207': 'Boukhenefis', '2211': 'Tafessour', '2224': 'Aïn Tidamine', '2307': 'Chorfa', '2309': 'Aïn El Berda',
    '2406': 'Oued Fraga', '2411': 'Badjarah', '2415': 'Khzara', '2427': 'Aïn Hsainia', '2503': 'Ben Badis',
    '2605': 'El Aïssaouia', '2645': 'Tlelat Ed Douair', '2649': 'Meftaha', '2661': 'Sedraya',
    '2706': 'Hassi Mameche', '2713': 'Benabdelmalek Ramdane', '2834': 'Oued Chair', '2836': 'Bir Foda',
    '2839': 'Ouled Attia', '2938': 'El Gueithna', '3209': 'Arbaout', '3218': 'Sidi Amar', '3410': 'Sidi M’Barek',
    '3417': 'Ouled Braham', '3428': 'El Anceur', '3429': 'Tasmart', '3522': 'Keddara', '3525': 'Touarga',
    '3533': 'Ouled Hadjadj', '3615': 'Chbaita Mokhtar', '3819': 'Tamelaht', '4007': 'Taouzinet', '4014': 'Tamza',
    '4111': 'Khedara', '4236': 'Hattatba', '4241': 'Beni Meleuk', '4305': 'Aïn Mellouk', '4306': 'Teleghma',
    '4320': 'Derradji Bousselah', '4322': 'Amira Arres', '4323': 'Terrai Baïnem', '4404': 'Khemis',
    '4419': 'Bir Ould Khlifa', '4429': 'Djemaa Ouled Chikh', '4508': 'Djeniene Bourezg', '4622': 'Oued Kihel',
    '4813': 'Beni Dergoune', '4821': 'Ouarizène', '5303': 'Fouggaret Ezzaouia',
}
# Communes ONS lists under a new name that no later text prints: they take ONS’s names (the
# founder's decision, 9 October 2026), and the decrees' become aliases
RENAMED = {'1604', '2427'}
# Decree 91-306's Arabic prints Boudria Beni Yadjis on two lines, as two communes; its Arabic name
# is ONS's
ARABIC_FROM_ONS = {'1822'}
# Chefs-lieux Decrees 21-117 and 26-206 spell otherwise than the commune (decree -> commune, French)
SEAT_SPELLINGS = {'El M’Ghaier': 'El Megaier'}
# Algiers' chef-lieu is the city, not one commune
NO_SEAT = {'16'}
# Daïras whose seat Ordinance 97-14 moved to Algiers, by their seats in Decree 91-306: their other
# communes stay in their wilaya, and no text we hold places them in another daïra
SEAT_MOVED = {('09', 'SIDI MOUSSA'), ('35', 'REGHAIA')}
LAW_26_06 = 'law-26-06'

WILAYA_FIELDS = ['code', 'name_fr', 'name_ar', 'named_by', 'named_article', 'named_item', 'seat', 'parent',
                 'created', 'created_by', 'created_article', 'listed_by', 'listed_article', 'dairas', 'communes']
DAIRA_FIELDS = ['code', 'wilaya', 'name_fr', 'name_ar', 'listed_by', 'listed_article', 'listed_item', 'communes']
COMMUNE_FIELDS = ['code', 'wilaya', 'daira', 'name_fr', 'name_ar', 'name_fr_by', 'name_ar_by',
                  'listed_by', 'listed_article', 'listed_item', 'wilaya_before']
CHANGE_FIELDS = ['date', 'type', 'subject', 'from', 'to', 'by', 'article', 'item']
ALIAS_FIELDS = ['kind', 'code', 'lang', 'name', 'texts']


class Inconsistent(Exception):
    """The texts don't fit together as the chain expects."""


def read(path):
    with open(path, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def source(text_id):
    return read(os.path.join(SOURCE, text_id + '.csv'))


def lists(text_id):
    """{article: [rows]} of a law or an ordinance, in the order of the text."""
    out = {}
    for row in source(text_id):
        out.setdefault(row['article'], []).append(row)
    return out


def loose_fr(s):
    s = unicodedata.normalize('NFKD', s.replace('’', "'"))
    return ''.join(c for c in s if not unicodedata.combining(c)).casefold()


def loose_ar(s):
    return re.sub('[أإآ]', 'ا', s)


def same_commune(a, b):
    """Whether two (French, Arabic) names are one commune's: either edition's names are the same
    but for accents, apostrophes, hyphens, commas, spaces, capitals, the shadda, hamzas and the
    dots of a final ي or ة."""
    def fr(s):
        return re.sub(r"[-' ,]", '', loose_fr(s))

    def ar(s):
        return re.sub('[ ،ّ]', '', loose_ar(s).replace('ى', 'ي').replace('ة', 'ه'))
    return bool(a[0] and b[0] and fr(a[0]) == fr(b[0]) or a[1] and b[1] and ar(a[1]) == ar(b[1]))


def law_article(wilaya):
    """The article of Law 84-09 that lists a wilaya's communes: 5 for 01, 52 bis for 49, 52 bis 1 for 50."""
    n = int(wilaya)
    return str(n + 4) if n < 49 else '52 bis' if n == 49 else f'52 bis {n - 49}'


class Commune:
    """A commune through the texts: its names as each text prints them, the latest text's
    citation, and its ONS code once it has one."""

    def __init__(self, fr, ar, cite):
        self.fr, self.ar, self.cite, self.code = fr, ar, cite, None
        self.printed = [(cite[0], fr, ar)]

    @property
    def names(self):
        return self.fr, self.ar

    def listed(self, fr, ar, cite):
        self.fr, self.ar, self.cite = fr, ar, cite
        self.printed.append((cite[0], fr, ar))

    def __repr__(self):
        return f'Commune({self.fr!r}, {self.ar!r}, {self.code})'


def tables(text_id):
    """{wilaya: [daïra]} of a daïra decree, each daïra {'seat': (fr, ar), 'cite': (text, wilaya,
    daïra), 'communes': [(fr, ar, cite)], 'unchanged': bool}. Decree 91-306's lines only its
    Arabic prints are left out, but for Rouissat."""
    out = {}
    for r in source(text_id):
        d = out.setdefault(r['wilaya'], {}).setdefault(r['daira'], {
            'seat': None, 'cite': (text_id, r['wilaya'], r['daira']), 'communes': [], 'unchanged': False})
        if r['item'] == 'seat':
            d['seat'] = (r['name_fr'], r['name_ar'])
        elif r['item'] == 'unchanged':
            d['unchanged'] = True
        elif r['name_fr'] or (r['wilaya'], r['daira'], r['item']) == ROUISSAT_91_306:
            d['communes'].append((r['name_fr'], r['name_ar'], (text_id, r['wilaya'], f"{r['daira']}/{r['item']}")))
    return {w: list(dairas.values()) for w, dairas in out.items()}


def find(communes, names, what):
    """The one commune of communes that a text has printed with these names."""
    found = [c for c in communes if any(same_commune(p[1:], names) for p in c.printed)]
    if len(found) != 1:
        raise Inconsistent(f'{what}: {names} matches {found}')
    return found[0]


def amend(state, text_id, spellings=None):
    """Applies a decree that reprints some daïras: a printed daïra replaces the one with the same
    seat, or is added, and the communes it lists leave the wilaya's other daïras. A daïra printed
    "sans changement" keeps its communes. Each wilaya keeps its communes."""
    spellings = spellings or {}
    for wilaya, dairas in tables(text_id).items():
        mine = state[wilaya]
        before = [c for d in mine for c in d['communes']]
        printed = []  # (the daïra printed, the daïra it replaces or None, [(commune, fr, ar, cite)])
        for d in dairas:
            same = [x for x in mine if x['seat'] and same_commune(x['seat'], d['seat'])]
            if len(same) > 1:
                raise Inconsistent(f'{text_id} {wilaya}: two daïras with the seat {d["seat"]}')
            if d['unchanged']:
                if not same:
                    raise Inconsistent(f'{text_id} {wilaya}: {d["seat"]} is "sans changement" but was not there')
                continue
            communes = [(find(before, spellings.get((fr, ar), (fr, ar)), f'{text_id} {wilaya}'), fr, ar, cite)
                        for fr, ar, cite in d['communes']]
            printed.append((d, same[0] if same else None, communes))
        taken = {id(c) for _, _, communes in printed for c, *_ in communes}
        if len(taken) != sum(len(communes) for _, _, communes in printed):
            raise Inconsistent(f'{text_id} {wilaya}: a commune is listed twice')
        for x in mine:
            x['communes'] = [c for c in x['communes'] if id(c) not in taken]
        for d, same, communes in printed:
            for c, fr, ar, cite in communes:
                c.listed(fr, ar, cite)
            if same is not None and same['communes']:
                raise Inconsistent(f'{text_id} {wilaya}: {d["seat"]} leaves communes in no daïra')
            if same is not None:
                same.update(seat=d['seat'], cite=d['cite'], communes=[c for c, *_ in communes])
            else:
                mine.append({'seat': d['seat'], 'cite': d['cite'], 'communes': [c for c, *_ in communes]})
        if sorted(map(id, before)) != sorted(id(c) for d in mine for c in d['communes']):
            raise Inconsistent(f'{text_id} {wilaya}: the wilaya does not keep its communes')


def rewrite(state, text_id, wilayas, pool, spellings=None):
    """Applies a decree that rewrites whole tables: each commune it lists is one of the pool's
    [(wilaya, commune)], which leave their old wilayas. Returns {wilaya: the wilayas its communes
    come from}.

    A name is paired with the one commune of the pool that any text has printed so, but for
    spelling (same_commune), or as spellings says. A wilaya's own communes are paired first. A
    new wilaya's names that fit communes of two old wilayas are paired with those of the one its
    other communes come from."""
    spellings = spellings or {}
    origin = {id(c): w for w, c in pool}
    printed = tables(text_id)
    pending = []
    for wilaya, dairas in printed.items():
        if wilaya not in wilayas:
            raise Inconsistent(f'{text_id}: an unexpected table, {wilaya}')
        for d in dairas:
            for fr, ar, cite in d['communes']:
                pending.append((wilaya, cite, spellings.get((fr, ar), (fr, ar))))
    pending.sort(key=lambda p: p[0] not in origin.values())
    found, sources = {}, {}
    while pending:
        left = []
        for wilaya, cite, names in pending:
            taken = {id(c) for c in found.values()}
            match = [c for w, c in pool if id(c) not in taken and any(same_commune(p[1:], names) for p in c.printed)]
            own = [c for c in match if origin[id(c)] == wilaya]
            parent = sources.get(wilaya, set())
            if own:
                match = own
            elif len(parent) == 1:
                match = [c for c in match if origin[id(c)] in parent]
            if len(match) == 1:
                found[cite] = match[0]
                sources.setdefault(wilaya, set()).add(origin[id(match[0])])
            else:
                left.append((wilaya, cite, names))
        if len(left) == len(pending):
            break
        pending = left
    if pending or len(found) != len(pool):
        listed = {id(c) for c in found.values()}
        raise Inconsistent(f'{text_id}: unmatched {[(w, n) for w, _, n in pending]}; '
                           f'not listed {[c for w, c in pool if id(c) not in listed]}')
    for wilaya, dairas in printed.items():
        new = []
        for d in dairas:
            communes = []
            for fr, ar, cite in d['communes']:
                c = found[cite]
                sources.setdefault(wilaya, set()).add(origin[id(c)])
                c.listed(fr, ar, cite)
                communes.append(c)
            new.append({'seat': d['seat'], 'cite': d['cite'], 'communes': communes})
        state[wilaya] = new
    return sources


def emptied(state):
    """{(wilaya, seat)} of the daïras without communes, which are then dropped."""
    out = set()
    for wilaya, dairas in state.items():
        out |= {(wilaya, d['seat'][0]) for d in dairas if not d['communes']}
        state[wilaya] = [d for d in dairas if d['communes']]
    return out


def chain():
    """Runs the texts in order. Returns (state, in_2021, parents): {wilaya: [daïra]} today, each
    daïra {'seat', 'cite', 'communes': [Commune]}, the same in June 2021, and {wilaya: parent}
    for the wilayas 49 to 69."""
    state = {w: [{'seat': d['seat'], 'cite': d['cite'], 'communes': [Commune(*c) for c in d['communes']]} for d in dairas]
             for w, dairas in tables('executive-decree-91-306').items()}

    amend(state, 'executive-decree-92-66', SPELLINGS_92_66)
    check_emptied(state, 'executive-decree-92-66')

    algiers = []
    for article, rows in lists('ordinance-97-14').items():
        wilaya = ORDINANCE_97_14[article][0]
        for r in rows:
            names = SPELLINGS_97_14.get((r['name_fr'], r['name_ar']), (r['name_fr'], r['name_ar']))
            c = find([c for d in state[wilaya] for c in d['communes']], names, f'ordinance-97-14 {wilaya}')
            for d in state[wilaya]:
                d['communes'] = [x for x in d['communes'] if x is not c]
            c.listed(r['name_fr'], r['name_ar'], ('ordinance-97-14', article, r['item']))
            algiers.append(c)
    state['16'].append({'seat': None, 'cite': None, 'communes': algiers})
    check_emptied(state, 'ordinance-97-14')

    amend(state, 'executive-decree-18-302')
    old = WILAYAS_21_198[:8]
    pool = [(w, c) for w in old for d in state[w] for c in d['communes']]
    sources = rewrite(state, 'executive-decree-21-198', WILAYAS_21_198, pool, PAIRS_21_198)
    check_emptied(state, 'executive-decree-21-198')
    parents = parents_of(sources, range(49, 59))

    codes = ons_codes(state)
    in_2021 = {w: [dict(d, communes=list(d['communes'])) for d in dairas] for w, dairas in state.items()}

    amend(state, 'executive-decree-25-87')
    old = WILAYAS_26_253[:10]
    pool = [(w, c) for w in old for d in state[w] for c in d['communes']]
    sources = rewrite(state, 'executive-decree-26-253', WILAYAS_26_253, pool, PAIRS_26_253)
    check_emptied(state, 'executive-decree-26-253')
    parents.update(parents_of(sources, range(59, 70)))

    if sorted(state) != [f'{n:02d}' for n in range(1, 70)]:
        raise Inconsistent('not 69 wilayas')
    final = [c for dairas in state.values() for d in dairas for c in d['communes']]
    if sorted(c.code for c in final) != sorted(codes):
        raise Inconsistent('the communes are not the 1,541 of ONS')
    return state, in_2021, parents


def check_emptied(state, text_id):
    if emptied(state) != EMPTIED.get(text_id, set()):
        raise Inconsistent(f'{text_id}: other daïras left without communes than EMPTIED says')


def parents_of(sources, numbers):
    """{wilaya: parent} for new wilayas, each made of communes of one older wilaya."""
    out = {}
    for n in numbers:
        found = sources.get(f'{n:02d}', set())
        if len(found) != 1:
            raise Inconsistent(f'wilaya {n:02d} is made of communes of {sorted(found)}')
        out[f'{n:02d}'] = found.pop()
    return out


def ons_codes(state):
    """Pairs each commune of June 2021 with its ONS code. Returns {code: ONS row}."""
    ons = {}
    for r in source('ons-2021'):
        ons.setdefault(r['wilaya'], []).append(r)
    if sorted(state) != sorted(ons):
        raise Inconsistent('the wilayas of 2021 are not those of ONS')
    used, codes = set(), {}
    for wilaya, rows in ons.items():
        communes = [c for d in state[wilaya] for c in d['communes']]
        if len(communes) != len(rows):
            raise Inconsistent(f'{wilaya}: {len(communes)} communes, ONS lists {len(rows)}')
        for c in communes:
            found = []
            for r in rows:
                code = r['wilaya'] + r['commune']
                if same_commune(c.names, (r['name_fr'], r['name_ar'])):
                    found.append(code)
                elif code in ONS_NAMES and same_commune(c.names, (ONS_NAMES[code], '')):
                    found.append(code)
                    used.add(code)
            if len(found) != 1:
                raise Inconsistent(f'{wilaya}: {c} matches the codes {found}')
            c.code = found[0]
        if sorted(c.code for c in communes) != sorted(r['wilaya'] + r['commune'] for r in rows):
            raise Inconsistent(f'{wilaya}: two communes share a code')
        for r in rows:
            codes[r['wilaya'] + r['commune']] = r
    if used != set(ONS_NAMES):
        raise Inconsistent(f'ONS_NAMES has names it does not need: {sorted(set(ONS_NAMES) - used)}')
    for c in [c for d in sum(state.values(), []) for c in d['communes']]:
        r = codes[c.code]
        c.printed.append(('ons-2021', r['name_fr'], r['name_ar']))
    return codes


def jo_dates():
    """{text: the date of its Journal officiel issue}, and ONS's list."""
    out = {t['id']: t['jo_date'] for t in read(os.path.join(DATA, 'texts.csv'))}
    out.update({t['id']: t['published'] for t in read(os.path.join(DATA, 'ons.csv'))})
    return out


def names(c, ons):
    """((fr, by), (ar, by)): a commune's names and where each comes from."""
    row = ons[c.code]
    text = c.cite[0]
    if c.code in RENAMED:
        if text not in ('executive-decree-91-306', 'executive-decree-92-66', 'ordinance-97-14'):
            raise Inconsistent(f'{c.code}: a later text lists it; drop it from RENAMED')
        return (row['name_fr'], 'ons-2021'), (row['name_ar'], 'ons-2021')
    if c.code in ARABIC_FROM_ONS:
        if text != 'executive-decree-91-306':
            raise Inconsistent(f'{c.code}: a later text lists it; drop it from ARABIC_FROM_ONS')
        return (c.fr, text), (row['name_ar'], 'ons-2021')
    if not c.fr or not c.ar:
        raise Inconsistent(f'{c.code}: the latest text that lists it does not print both names')
    return (c.fr, text), (c.ar, text)


def build():
    """{file name: rows} of the five tables."""
    state, in_2021, parents = chain()
    ons = {r['wilaya'] + r['commune']: r for r in source('ons-2021')}
    dates = jo_dates()
    by_code = {c.code: c for dairas in state.values() for d in dairas for c in d['communes']}
    wilaya_2021 = {c.code: w for w, dairas in in_2021.items() for d in dairas for c in d['communes']}

    # the texts that write each article of Law 84-09, oldest first: the laws and Ordinance 21-03,
    # each with the article of its own that writes it
    articles = {}
    for text in ('law-19-12', 'ordinance-21-03', LAW_26_06):
        for article, rows in lists(text).items():
            articles.setdefault(article, []).append((text, rows[0]['via']))

    communes, dairas_out, aliases, moved = [], [], [], set()
    for wilaya in sorted(state):
        for d in state[wilaya]:
            seat = None
            if d['seat'] is not None and wilaya not in NO_SEAT:
                if any(same_commune(p[1:], d['seat']) for c in d['communes'] for p in c.printed):
                    seat = find(d['communes'], d['seat'], f'the seat of {d["cite"]}')
                else:
                    moved.add((wilaya, d['seat'][0]))
            for c in d['communes']:
                (fr, fr_by), (ar, ar_by) = names(c, ons)
                text, article, item = c.cite
                communes.append({
                    'code': c.code, 'wilaya': wilaya, 'daira': seat.code if seat else '',
                    'name_fr': fr, 'name_ar': ar, 'name_fr_by': fr_by, 'name_ar_by': ar_by,
                    'listed_by': text, 'listed_article': article, 'listed_item': item,
                    'wilaya_before': wilaya_2021[c.code] if wilaya_2021[c.code] != wilaya else '',
                })
            if seat:
                text, article, item = d['cite']
                dairas_out.append({'code': seat.code, 'wilaya': wilaya, 'listed_by': text,
                                   'listed_article': article, 'listed_item': item, 'communes': len(d['communes']),
                                   'seat': d['seat']})
    if moved != SEAT_MOVED:
        raise Inconsistent(f'daïras whose seat is not one of their communes: {sorted(moved)}')
    communes.sort(key=lambda r: r['code'])
    commune_names = {r['code']: (r['name_fr'], r['name_ar']) for r in communes}
    for r in dairas_out:
        r['name_fr'], r['name_ar'] = commune_names[r['code']]
    if len({r['code'] for r in dairas_out}) != len(dairas_out):
        raise Inconsistent('two daïras share a seat')

    # the aliases: every other spelling of a commune's names, with the texts that print it
    for code, c in sorted(by_code.items()):
        printed = c.printed + law_names(code, c, wilaya_2021, state)
        aliases += alias_rows('commune', code, printed, commune_names[code], dates)
    for r in dairas_out:
        seat_text = r['listed_by']
        aliases += alias_rows('daira', r['code'], [(seat_text,) + r.pop('seat')], (r['name_fr'], r['name_ar']), dates)
    dairas_out.sort(key=lambda r: r['code'])

    wilayas = wilaya_rows(state, parents, articles, dairas_out, dates)
    aliases.append({'kind': 'wilaya', 'code': '16', 'lang': 'en', 'name': 'Algiers', 'texts': ''})
    changes = change_rows(wilayas, communes, by_code, dates)
    order = {'wilaya': 0, 'daira': 1, 'commune': 2}
    aliases.sort(key=lambda r: (order[r['kind']], r['code'], r['lang'], r['name']))
    return {'wilayas.csv': (WILAYA_FIELDS, wilayas), 'dairas.csv': (DAIRA_FIELDS, dairas_out),
            'communes.csv': (COMMUNE_FIELDS, communes), 'changes.csv': (CHANGE_FIELDS, changes),
            'aliases.csv': (ALIAS_FIELDS, aliases)}


def law_names(code, c, wilaya_2021, state):
    """[(text, fr, ar)]: how the lists of Law 19-12, Ordinance 21-03 and Law 26-06 print the
    commune, if one lists it."""
    out = []
    final = next(w for w, dairas in state.items() for d in dairas if c in d['communes'])
    for text, wilaya in (('law-19-12', wilaya_2021[code]), ('ordinance-21-03', wilaya_2021[code]), (LAW_26_06, final)):
        rows = lists(text).get(law_article(wilaya), [])
        found = [r for r in rows if same_commune(c_names(c, text), (r['name_fr'], r['name_ar']))]
        if len(found) > 1:
            raise Inconsistent(f'{text}: {c} matches {len(found)} names')
        out += [(text, r['name_fr'], r['name_ar']) for r in found]
    return out


def c_names(c, text):
    """The names to find a commune by in a law's list: those of the decree that followed it."""
    later = {'law-19-12': 'executive-decree-21-198', 'ordinance-21-03': 'executive-decree-21-198',
             LAW_26_06: 'executive-decree-26-253'}[text]
    for t, fr, ar in c.printed:
        if t == later:
            return fr, ar
    return c.names


def same_spelling(a, b):
    """Whether two names are spelled the same but for capitals and the shape of the apostrophe."""
    return a.replace('’', "'").casefold() == b.replace('’', "'").casefold()


def alias_rows(kind, code, printed, name, dates):
    """The spellings in printed [(text, fr, ar)] other than name (fr, ar), each with the texts
    that print it, oldest first. Spellings that differ only in capitals or the shape of the
    apostrophe are one, as the oldest text prints it."""
    found = {}
    for text, fr, ar in sorted(printed, key=lambda p: dates[p[0]]):
        for lang, value, own in (('fr', fr, name[0]), ('ar', ar, name[1])):
            if value and not same_spelling(value, own):
                key = next((k for k in found if k[0] == lang and same_spelling(k[1], value)), (lang, value))
                found.setdefault(key, [])
                if text not in found[key]:
                    found[key].append(text)
    return [{'kind': kind, 'code': code, 'lang': lang, 'name': value, 'texts': ' '.join(texts)}
            for (lang, value), texts in found.items()]


def wilaya_rows(state, parents, articles, dairas, dates):
    named = {r['item']: ('decree-84-79', r) for r in source('decree-84-79')}
    for text in ('presidential-decree-21-117', 'presidential-decree-26-206'):
        named.update({f"{int(r['item']):02d}": (text, r) for r in source(text)})
    out = []
    for wilaya in sorted(state):
        text, r = named[wilaya]
        communes = [c for d in state[wilaya] for c in d['communes']]
        seat = ''
        if wilaya not in NO_SEAT:
            names = (SEAT_SPELLINGS.get(r['seat_fr'], r['seat_fr']), r['seat_ar'])
            seat = find(communes, names, f'the chef-lieu of {wilaya}').code
        written = articles.get(law_article(wilaya), [('law-84-09', '')])
        first, via = written[0] if wilaya in parents else ('', '')
        out.append({
            'code': wilaya, 'name_fr': r['name_fr'], 'name_ar': r['name_ar'], 'named_by': text,
            'named_article': r['article'], 'named_item': r['item'], 'seat': seat, 'parent': parents.get(wilaya, ''),
            'created': dates[first] if first else '', 'created_by': first, 'created_article': via,
            'listed_by': written[-1][0], 'listed_article': law_article(wilaya),
            'dairas': sum(1 for d in dairas if d['wilaya'] == wilaya),
            'communes': len(communes),
        })
    return out


def change_rows(wilayas, communes, by_code, dates):
    """The 2026 changes: the eleven wilayas Law 26-06 creates and the communes it moves to them,
    each cited by the article and item of the law's list."""
    out = []
    date = dates[LAW_26_06]
    law = lists(LAW_26_06)
    for w in wilayas:
        if w['created_by'] == LAW_26_06:
            out.append({'date': date, 'type': 'wilaya_created', 'subject': w['code'], 'from': w['parent'], 'to': w['code'],
                        'by': LAW_26_06, 'article': w['created_article'], 'item': ''})
    for r in communes:
        if r['wilaya_before']:
            rows = law[law_article(r['wilaya'])]
            names = [(fr, ar) for text, fr, ar in by_code[r['code']].printed]
            found = [x for x in rows if any(same_commune(n, (x['name_fr'], x['name_ar'])) for n in names)]
            if len(found) != 1:
                raise Inconsistent(f'{r["code"]}: {len(found)} items of Law 26-06 list it')
            out.append({'date': date, 'type': 'commune_moved', 'subject': r['code'], 'from': r['wilaya_before'],
                        'to': r['wilaya'], 'by': LAW_26_06, 'article': found[0]['article'], 'item': found[0]['item']})
    return out


def write(tables_, check=False):
    """Writes the tables, or with check, returns the names of those that differ."""
    differ = []
    for name, (fields, rows) in tables_.items():
        buf = io.StringIO()
        out = csv.DictWriter(buf, fields, lineterminator='\n')
        out.writeheader()
        out.writerows(rows)
        path = os.path.join(DATA, name)
        if check:
            with open(path, encoding='utf-8', newline='') as f:
                if f.read() != buf.getvalue():
                    differ.append(name)
        else:
            with open(path, 'w', encoding='utf-8', newline='') as f:
                f.write(buf.getvalue())
    return differ


def main():
    check = sys.argv[1:] == ['--check']
    try:
        tables_ = build()
    except Inconsistent as e:
        sys.exit(f'inconsistent: {e}')
    differ = write(tables_, check)
    if differ:
        sys.exit(f'out of date: {", ".join(differ)} (run python3 tools/resolve.py)')


if __name__ == '__main__':
    main()

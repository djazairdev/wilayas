"""Build the API: the static files under dist/, from the tables in data/.

    python3 build.py          # writes dist/
    python3 build.py OUT_DIR  # writes OUT_DIR/ instead

dist/v1/ holds the JSON and CSV files, the JSON Schemas (dist/v1/schemas/) and the OpenAPI
description (dist/v1/openapi.json); public/ is copied to dist/ as it is. Each JSON file is an
object with the data version and its payload under a named key. The latest entry in
CHANGELOG.md gives the version, as "## 1.2.3 (2026-10-09)": index.json and the OpenAPI
description carry the version (1.2.3), and every file the data version, its date. The major
version is the one in the path, v1 (tools/release.py).

The schemas and the OpenAPI description are made here, from DEFS, so they always describe the
files this script writes; tests/test_build.py checks every file against its schema.

Standard library only.
"""
import csv
import io
import json
import os
import re
import shutil
import sys
import unicodedata

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, 'data')
PUBLIC = os.path.join(ROOT, 'public')
API_MAJOR = 1  # dist/v1/: a breaking change is a new major version, under /v2
API_DIR = f'v{API_MAJOR}'
BASE_URL = f'https://wilayas.djazair.dev/{API_DIR}'
# A changelog entry's heading: '## 1.2.3 (2026-10-09)'
HEADING = re.compile(r'^## (\d+\.\d+\.\d+) \((\d{4}-\d{2}-\d{2})\)[ \t]*$', re.M)
REPOSITORY = 'https://github.com/djazairdev/wilayas'

# Law 26-06, art. 4, rewrites art. 54 of Law 84-09: the parent wilayas run the new ones' services
# until the handover, by 31 December 2026 at the latest
TRANSITION = {'until': '2026-12-31', 'by': {'text': 'law-26-06', 'article': '4'}}
# ISO 3166-2 lists wilayas 01 to 58
ISO_WILAYAS = 58


def read(name):
    with open(os.path.join(DATA, name), encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def changelog(text):
    """[(version, date, entry)] of a changelog, newest first: each '## 1.2.3 (2026-10-09)' heading
    and the text under it, up to the next heading."""
    found = list(HEADING.finditer(text))
    return [(m.group(1), m.group(2), text[m.end():found[i + 1].start() if i + 1 < len(found) else len(text)].strip())
            for i, m in enumerate(found)]


def latest(root=ROOT):
    """(version, date, entry) of the latest entry in CHANGELOG.md."""
    with open(os.path.join(root, 'CHANGELOG.md'), encoding='utf-8') as f:
        found = changelog(f.read())
    if not found:
        raise SystemExit('CHANGELOG.md has no "## 1.2.3 (YYYY-MM-DD)" entry')
    return found[0]


def version():
    """The API's version: the latest changelog entry's, as 1.2.3."""
    return latest()[0]


def data_version():
    """The data version: the date of the latest changelog entry."""
    return latest()[1]


def slug(name):
    """ASCII, lower case, words joined by hyphens: "M’Sila" -> "m-sila", "Aïn Defla" -> "ain-defla"."""
    s = unicodedata.normalize('NFKD', name)
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def cite(text, article, item=''):
    out = {'text': text, 'article': article}
    if item:
        out['item'] = item
    return out


# The JSON Schemas of the records (2020-12). Each file's schema is made from these.
DEFS = {
    'name': {
        'type': 'object', 'additionalProperties': False, 'required': ['ar', 'fr'],
        'description': 'As printed in the Arabic and the French editions of the text cited',
        'properties': {'ar': {'type': 'string', 'minLength': 1}, 'fr': {'type': 'string', 'minLength': 1}},
    },
    'citation': {
        'type': 'object', 'additionalProperties': False, 'required': ['text', 'article'],
        'description': 'A place in a text of texts.json. In the daïra decrees, which list communes in tables, '
                       'article is the wilaya whose table it is, and item the daïra and the commune ("10/2").',
        'properties': {
            'text': {'type': 'string', 'pattern': '^[a-z0-9-]+$'},
            'article': {'type': 'string', 'minLength': 1},
            'item': {'type': 'string', 'minLength': 1},
        },
    },
    'wilaya_code': {'type': 'string', 'pattern': '^(0[1-9]|[1-5][0-9]|6[0-9])$'},
    'commune_code': {'type': 'string', 'pattern': '^[0-9]{4}$'},
    'date': {'type': 'string', 'pattern': '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'},
    'slug': {'type': 'string', 'pattern': '^[a-z0-9]+(-[a-z0-9]+)*$'},
    'alias': {
        'type': 'object', 'additionalProperties': False, 'required': ['lang', 'name', 'texts'],
        'properties': {
            'lang': {'enum': ['ar', 'fr', 'en']},
            'name': {'type': 'string', 'minLength': 1},
            'texts': {'type': 'array', 'items': {'type': 'string'}, 'description': 'The texts that print it, oldest first'},
        },
    },
    'wilaya': {
        'type': 'object', 'additionalProperties': False,
        'required': ['code', 'iso_3166_2', 'name', 'slug', 'seat', 'named_by', 'defined_by', 'created', 'parent',
                     'administered_by', 'counts', 'aliases'],
        'properties': {
            'code': {'$ref': '#/$defs/wilaya_code'},
            'iso_3166_2': {'type': ['string', 'null'], 'pattern': '^DZ-[0-9]{2}$',
                           'description': 'Null for 59 to 69 until ISO 3166-2 lists them'},
            'name': {'$ref': '#/$defs/name'},
            'slug': {'$ref': '#/$defs/slug'},
            'seat': {'anyOf': [{'$ref': '#/$defs/commune_code'}, {'type': 'null'}],
                     'description': "The chef-lieu's commune; null for Algiers, whose chef-lieu is the city"},
            'named_by': {'$ref': '#/$defs/citation'},
            'defined_by': {
                'type': 'object', 'additionalProperties': False, 'required': ['text', 'article', 'amended_by'],
                'description': 'The article of Law 84-09 that lists its communes, and the latest text that wrote it',
                'properties': {'text': {'const': 'law-84-09'}, 'article': {'type': 'string'},
                               'amended_by': {'type': ['string', 'null']}},
            },
            'created': {'anyOf': [{'type': 'null'}, {
                'type': 'object', 'additionalProperties': False, 'required': ['date', 'by'],
                'properties': {'date': {'$ref': '#/$defs/date'}, 'by': {'$ref': '#/$defs/citation'}}}],
                'description': 'For 49 to 69: the date of the Journal officiel issue of the law that created it'},
            'parent': {'anyOf': [{'$ref': '#/$defs/wilaya_code'}, {'type': 'null'}],
                       'description': 'For 49 to 69: the wilaya it was made from'},
            'administered_by': {'anyOf': [{'type': 'null'}, {
                'type': 'object', 'additionalProperties': False, 'required': ['wilaya', 'until', 'by'],
                'properties': {'wilaya': {'$ref': '#/$defs/wilaya_code'}, 'until': {'$ref': '#/$defs/date'},
                               'by': {'$ref': '#/$defs/citation'}}}],
                'description': 'For 59 to 69: the parent wilaya runs its services until the handover, at the latest'},
            'counts': {'type': 'object', 'additionalProperties': False, 'required': ['dairas', 'communes'],
                       'properties': {'dairas': {'type': 'integer', 'minimum': 0},
                                      'communes': {'type': 'integer', 'minimum': 1}}},
            'aliases': {'type': 'array', 'items': {'$ref': '#/$defs/alias'}},
        },
    },
    'daira': {
        'type': 'object', 'additionalProperties': False,
        'required': ['code', 'name', 'slug', 'wilaya', 'listed_by', 'counts', 'aliases'],
        'description': "A daïra, identified and named by its seat's commune",
        'properties': {
            'code': {'$ref': '#/$defs/commune_code'},
            'name': {'$ref': '#/$defs/name'},
            'slug': {'$ref': '#/$defs/slug'},
            'wilaya': {'$ref': '#/$defs/wilaya_code'},
            'listed_by': {'$ref': '#/$defs/citation'},
            'counts': {'type': 'object', 'additionalProperties': False, 'required': ['communes'],
                       'properties': {'communes': {'type': 'integer', 'minimum': 1}}},
            'aliases': {'type': 'array', 'items': {'$ref': '#/$defs/alias'}},
        },
    },
    'commune': {
        'type': 'object', 'additionalProperties': False,
        'required': ['code', 'name', 'slug', 'wilaya', 'daira', 'wilaya_before', 'listed_by', 'names_from',
                     'previous_codes', 'aliases'],
        'properties': {
            'code': {'$ref': '#/$defs/commune_code'},
            'name': {'$ref': '#/$defs/name'},
            'slug': {'$ref': '#/$defs/slug'},
            'wilaya': {'$ref': '#/$defs/wilaya_code'},
            'daira': {'anyOf': [{'$ref': '#/$defs/commune_code'}, {'type': 'null'}]},
            'wilaya_before': {'anyOf': [{'type': 'null'}, {
                'type': 'object', 'additionalProperties': False, 'required': ['wilaya', 'until', 'by'],
                'properties': {'wilaya': {'$ref': '#/$defs/wilaya_code'}, 'until': {'$ref': '#/$defs/date'},
                               'by': {'$ref': '#/$defs/citation'}}}],
                'description': 'For the 108 communes Law 26-06 moved: the wilaya they were in'},
            'listed_by': {'$ref': '#/$defs/citation'},
            'names_from': {'type': 'object', 'additionalProperties': False, 'required': ['ar', 'fr'],
                           'description': 'The text each name comes from: the one cited, or ONS\'s list',
                           'properties': {'ar': {'type': 'string'}, 'fr': {'type': 'string'}}},
            'previous_codes': {'type': 'array', 'items': {
                'type': 'object', 'additionalProperties': False, 'required': ['code', 'until'],
                'properties': {'code': {'$ref': '#/$defs/commune_code'}, 'until': {'$ref': '#/$defs/date'}}}},
            'aliases': {'type': 'array', 'items': {'$ref': '#/$defs/alias'}},
        },
    },
    'commune_summary': {
        'type': 'object', 'additionalProperties': False, 'required': ['code', 'name', 'slug', 'daira'],
        'properties': {'code': {'$ref': '#/$defs/commune_code'}, 'name': {'$ref': '#/$defs/name'},
                       'slug': {'$ref': '#/$defs/slug'},
                       'daira': {'anyOf': [{'$ref': '#/$defs/commune_code'}, {'type': 'null'}]}},
    },
    'daira_summary': {
        'type': 'object', 'additionalProperties': False, 'required': ['code', 'name', 'slug', 'communes'],
        'properties': {'code': {'$ref': '#/$defs/commune_code'}, 'name': {'$ref': '#/$defs/name'},
                       'slug': {'$ref': '#/$defs/slug'}, 'communes': {'type': 'integer', 'minimum': 1}},
    },
    'change': {
        'type': 'object', 'additionalProperties': False, 'required': ['date', 'type', 'subject', 'from', 'to', 'by'],
        'properties': {
            'date': {'$ref': '#/$defs/date', 'description': 'The date of the Journal officiel issue'},
            'type': {'enum': ['wilaya_created', 'commune_moved']},
            'subject': {'type': 'string', 'description': "The wilaya's or the commune's code"},
            'from': {'$ref': '#/$defs/wilaya_code'},
            'to': {'$ref': '#/$defs/wilaya_code'},
            'by': {'$ref': '#/$defs/citation'},
        },
    },
    'text': {
        'type': 'object', 'additionalProperties': False,
        'required': ['id', 'kind', 'number', 'signed', 'jo_number', 'jo_date', 'url_ar', 'url_fr', 'sha256_ar', 'sha256_fr'],
        'properties': {
            'id': {'type': 'string'}, 'kind': {'enum': ['law', 'ordinance', 'decree', 'presidential decree', 'executive decree']},
            'number': {'type': 'string'}, 'signed': {'$ref': '#/$defs/date'},
            'jo_number': {'type': 'integer'}, 'jo_date': {'$ref': '#/$defs/date'},
            'url_ar': {'type': 'string'}, 'url_fr': {'type': 'string'},
            'sha256_ar': {'type': 'string', 'pattern': '^[0-9a-f]{64}$'},
            'sha256_fr': {'type': 'string', 'pattern': '^[0-9a-f]{64}$'},
        },
    },
    'list': {
        'type': 'object', 'additionalProperties': False, 'required': ['id', 'title', 'published', 'url', 'sha256'],
        'description': "ONS's code géographique national",
        'properties': {'id': {'type': 'string'}, 'title': {'type': 'string'}, 'published': {'type': 'string'},
                       'url': {'type': 'string'}, 'sha256': {'type': 'string', 'pattern': '^[0-9a-f]{64}$'}},
    },
    'division_wilaya': {
        'type': 'object', 'additionalProperties': False, 'required': ['code', 'name', 'slug', 'communes'],
        'properties': {'code': {'$ref': '#/$defs/wilaya_code'}, 'name': {'$ref': '#/$defs/name'},
                       'slug': {'$ref': '#/$defs/slug'}, 'communes': {'type': 'integer', 'minimum': 1}},
    },
    'division_commune': {
        'type': 'object', 'additionalProperties': False, 'required': ['code', 'name', 'slug', 'wilaya'],
        'properties': {'code': {'$ref': '#/$defs/commune_code'}, 'name': {'$ref': '#/$defs/name'},
                       'slug': {'$ref': '#/$defs/slug'}, 'wilaya': {'$ref': '#/$defs/wilaya_code'}},
    },
}


def array_of(name):
    return {'type': 'array', 'items': {'$ref': f'#/$defs/{name}'}}


def with_lists(name, lists):
    """A record with lists of others added: a wilaya with its daïras and communes."""
    out = json.loads(json.dumps(DEFS[name]))
    out['required'] = out['required'] + list(lists)
    out['properties'].update({k: array_of(v) for k, v in lists.items()})
    return out


# Each kind of file: its schema's name, the key of its payload, and the payload's schema
FILES = {
    'wilayas': ('wilayas', array_of('wilaya')),
    'wilaya': ('wilaya', with_lists('wilaya', {'dairas': 'daira_summary', 'communes': 'commune_summary'})),
    'dairas': ('dairas', array_of('daira')),
    'daira': ('daira', with_lists('daira', {'communes': 'commune_summary'})),
    'communes': ('communes', array_of('commune')),
    'commune': ('commune', {'$ref': '#/$defs/commune'}),
    'changes': ('changes', array_of('change')),
    'texts': ('texts', array_of('text')),
    'division-wilayas': ('wilayas', array_of('division_wilaya')),
    'division-communes': ('communes', array_of('division_commune')),
}
INDEX_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'required': ['name', 'description', 'version', 'data_version', 'base_url', 'counts', 'licences',
                 'repository', 'files'],
    'properties': {
        'name': {'const': 'wilayas'}, 'description': {'type': 'string'},
        'version': {'type': 'string', 'pattern': f'^{API_MAJOR}\\.[0-9]+\\.[0-9]+$',
                    'description': 'The API\'s version: the major one is in the path'},
        'data_version': {'$ref': '#/$defs/date'},
        'base_url': {'type': 'string'},
        'counts': {'type': 'object', 'additionalProperties': {'type': 'integer'}},
        'licences': {'type': 'object', 'additionalProperties': False, 'required': ['data', 'code'],
                     'properties': {'data': {'const': 'CC0-1.0'}, 'code': {'const': 'MIT'}}},
        'repository': {'type': 'string'},
        'files': {'type': 'object', 'additionalProperties': {'type': 'string'}},
    },
}


def schema(kind):
    """The JSON Schema of a kind of file, with the definitions it needs."""
    if kind == 'index':
        body = INDEX_SCHEMA
    else:
        key, payload = FILES[kind]
        body = {'type': 'object', 'additionalProperties': False, 'required': ['data_version', key],
                'properties': {'data_version': {'$ref': '#/$defs/date'}, key: payload}}
        if kind == 'texts':  # the texts, and ONS's lists
            body['required'].append('lists')
            body['properties']['lists'] = array_of('list')
    needed, todo = set(), [body]
    while todo:
        for ref in re.findall(r'"#/\$defs/([a-z_0-9]+)"', json.dumps(todo.pop())):
            if ref not in needed:
                needed.add(ref)
                todo.append(DEFS[ref])
    return {'$schema': 'https://json-schema.org/draft/2020-12/schema', '$id': f'{BASE_URL}/schemas/{kind}.json',
            'title': kind, **body, '$defs': {k: DEFS[k] for k in sorted(needed)}}


def build_records():
    """The records of every file, from the tables in data/."""
    wilayas, dairas, communes = read('wilayas.csv'), read('dairas.csv'), read('communes.csv')
    changes, aliases = read('changes.csv'), read('aliases.csv')
    moves = {c['subject']: c for c in changes if c['type'] == 'commune_moved'}
    alias_of = {}
    for a in aliases:
        alias_of.setdefault((a['kind'], a['code']), []).append(
            {'lang': a['lang'], 'name': a['name'], 'texts': a['texts'].split() if a['texts'] else []})

    def name(r):
        return {'ar': r['name_ar'], 'fr': r['name_fr']}

    out_communes = []
    for c in communes:
        move = moves.get(c['code'])
        out_communes.append({
            'code': c['code'], 'name': name(c), 'slug': slug(c['name_fr']), 'wilaya': c['wilaya'],
            'daira': c['daira'] or None,
            'wilaya_before': {'wilaya': c['wilaya_before'], 'until': move['date'],
                              'by': cite(move['by'], move['article'], move['item'])} if c['wilaya_before'] else None,
            'listed_by': cite(c['listed_by'], c['listed_article'], c['listed_item']),
            'names_from': {'ar': c['name_ar_by'], 'fr': c['name_fr_by']},
            'previous_codes': [],
            'aliases': alias_of.get(('commune', c['code']), []),
        })
    out_dairas = [{
        'code': d['code'], 'name': name(d), 'slug': slug(d['name_fr']), 'wilaya': d['wilaya'],
        'listed_by': cite(d['listed_by'], d['listed_article'], d['listed_item']),
        'counts': {'communes': int(d['communes'])}, 'aliases': alias_of.get(('daira', d['code']), []),
    } for d in dairas]
    out_wilayas = []
    for w in wilayas:
        new = int(w['code']) > 58
        out_wilayas.append({
            'code': w['code'], 'iso_3166_2': f"DZ-{w['code']}" if int(w['code']) <= ISO_WILAYAS else None,
            'name': name(w), 'slug': slug(w['name_fr']), 'seat': w['seat'] or None,
            'named_by': cite(w['named_by'], w['named_article'], w['named_item']),
            'defined_by': {'text': 'law-84-09', 'article': w['listed_article'],
                           'amended_by': None if w['listed_by'] == 'law-84-09' else w['listed_by']},
            'created': {'date': w['created'], 'by': cite(w['created_by'], w['created_article'])} if w['created'] else None,
            'parent': w['parent'] or None,
            'administered_by': {'wilaya': w['parent'], **TRANSITION} if new else None,
            'counts': {'dairas': int(w['dairas']), 'communes': int(w['communes'])},
            'aliases': alias_of.get(('wilaya', w['code']), []),
        })
    out_changes = [{'date': c['date'], 'type': c['type'], 'subject': c['subject'], 'from': c['from'], 'to': c['to'],
                    'by': cite(c['by'], c['article'], c['item'])} for c in changes]
    texts = [dict(t, jo_number=int(t['jo_number'])) for t in read('texts.csv')]
    lists_ = read('ons.csv')
    return out_wilayas, out_dairas, out_communes, out_changes, texts, lists_


def summary_commune(c):
    return {'code': c['code'], 'name': c['name'], 'slug': c['slug'], 'daira': c['daira']}


def summary_daira(d):
    return {'code': d['code'], 'name': d['name'], 'slug': d['slug'], 'communes': d['counts']['communes']}


def csv_text(fields, rows):
    buf = io.StringIO()
    out = csv.writer(buf, lineterminator='\n')
    out.writerow(fields)
    out.writerows(rows)
    return buf.getvalue()


def wilaya_csv(rows):
    fields = ['code', 'iso_3166_2', 'name_fr', 'name_ar', 'slug', 'seat', 'parent', 'created', 'administered_by',
              'administered_until', 'dairas', 'communes']
    return csv_text(fields, [[w['code'], w['iso_3166_2'] or '', w['name']['fr'], w['name']['ar'], w['slug'],
                              w['seat'] or '', w['parent'] or '', (w['created'] or {}).get('date', ''),
                              (w['administered_by'] or {}).get('wilaya', ''), (w['administered_by'] or {}).get('until', ''),
                              w['counts']['dairas'], w['counts']['communes']] for w in rows])


def commune_csv(rows):
    fields = ['code', 'wilaya', 'daira', 'name_fr', 'name_ar', 'slug', 'wilaya_before', 'listed_by', 'listed_article',
              'listed_item']
    return csv_text(fields, [[c['code'], c['wilaya'], c['daira'] or '', c['name']['fr'], c['name']['ar'], c['slug'],
                              (c['wilaya_before'] or {}).get('wilaya', ''), c['listed_by']['text'],
                              c['listed_by']['article'], c['listed_by'].get('item', '')] for c in rows])


def daira_csv(rows):
    fields = ['code', 'wilaya', 'name_fr', 'name_ar', 'slug', 'communes', 'listed_by', 'listed_article', 'listed_item']
    return csv_text(fields, [[d['code'], d['wilaya'], d['name']['fr'], d['name']['ar'], d['slug'], d['counts']['communes'],
                              d['listed_by']['text'], d['listed_by']['article'], d['listed_by'].get('item', '')]
                             for d in rows])


def change_csv(rows):
    fields = ['date', 'type', 'subject', 'from', 'to', 'by', 'article', 'item']
    return csv_text(fields, [[c['date'], c['type'], c['subject'], c['from'], c['to'], c['by']['text'],
                              c['by']['article'], c['by'].get('item', '')] for c in rows])


def files():
    """{path under dist/v1/: (kind, content)}: kind is a schema's name for JSON, 'csv' or 'openapi'."""
    date = data_version()
    wilayas, dairas, communes, changes, texts, lists_ = build_records()
    out = {}

    def put(path, kind, key, payload):
        out[path] = (kind, {'data_version': date, key: payload})

    put('wilayas.json', 'wilayas', 'wilayas', wilayas)
    out['wilayas.csv'] = ('csv', wilaya_csv(wilayas))
    for w in wilayas:
        mine_c = [c for c in communes if c['wilaya'] == w['code']]
        mine_d = [d for d in dairas if d['wilaya'] == w['code']]
        put(f"wilayas/{w['code']}.json", 'wilaya', 'wilaya',
            dict(w, dairas=[summary_daira(d) for d in mine_d], communes=[summary_commune(c) for c in mine_c]))
        put(f"wilayas/{w['code']}/communes.json", 'communes', 'communes', mine_c)
        out[f"wilayas/{w['code']}/communes.csv"] = ('csv', commune_csv(mine_c))
        put(f"wilayas/{w['code']}/dairas.json", 'dairas', 'dairas', mine_d)
    put('dairas.json', 'dairas', 'dairas', dairas)
    out['dairas.csv'] = ('csv', daira_csv(dairas))
    for d in dairas:
        put(f"dairas/{d['code']}.json", 'daira', 'daira',
            dict(d, communes=[summary_commune(c) for c in communes if c['daira'] == d['code']]))
    put('communes.json', 'communes', 'communes', communes)
    out['communes.csv'] = ('csv', commune_csv(communes))
    for c in communes:
        put(f"communes/{c['code']}.json", 'commune', 'commune', c)
    put('changes.json', 'changes', 'changes', changes)
    out['changes.csv'] = ('csv', change_csv(changes))
    out['texts.json'] = ('texts', {'data_version': date, 'texts': texts, 'lists': lists_})

    # the division of 2019: 58 wilayas, the 108 communes Law 26-06 moved in their old ones
    before = [dict(c, wilaya=(c['wilaya_before'] or {}).get('wilaya', c['wilaya'])) for c in communes]
    put('divisions/2019/wilayas.json', 'division-wilayas', 'wilayas', [
        {'code': w['code'], 'name': w['name'], 'slug': w['slug'],
         'communes': sum(1 for c in before if c['wilaya'] == w['code'])} for w in wilayas if int(w['code']) <= 58])
    put('divisions/2019/communes.json', 'division-communes', 'communes', [
        {'code': c['code'], 'name': c['name'], 'slug': c['slug'], 'wilaya': c['wilaya']} for c in before])

    for kind in ['index'] + list(FILES):
        out[f'schemas/{kind}.json'] = ('schema', schema(kind))
    out['openapi.json'] = ('openapi', openapi(version(), date))
    counts = {'wilayas': len(wilayas), 'dairas': len(dairas), 'communes': len(communes), 'changes': len(changes)}
    paths = [p for p in sorted(out) if '/' not in p or p.startswith(('divisions/', 'schemas/'))] + ['index.json']
    paths += ['wilayas/{code}.json', 'wilayas/{code}/communes.json', 'wilayas/{code}/communes.csv',
              'wilayas/{code}/dairas.json', 'dairas/{code}.json', 'communes/{code}.json']
    listed = {re.sub(r'[^a-z0-9]+', '_', p.replace('.json', '').replace('{code}', 'code')).strip('_'): p
              for p in sorted(paths)}
    out['index.json'] = ('index', {
        'name': 'wilayas',
        'description': "Algeria's wilayas, daïras and communes, from the official texts in the Journal officiel",
        'version': version(), 'data_version': date, 'base_url': BASE_URL + '/', 'counts': counts,
        'licences': {'data': 'CC0-1.0', 'code': 'MIT'}, 'repository': REPOSITORY, 'files': listed})
    return out


# The OpenAPI paths: (path, summary, the file's schema, its CSV twin or None, path parameter or None)
PATHS = [
    ('/index.json', 'Counts, versions, licences and the list of files', 'index', None, None),
    ('/wilayas.json', 'The 69 wilayas', 'wilayas', '/wilayas.csv', None),
    ('/wilayas/{code}.json', 'One wilaya, with its daïras and communes', 'wilaya', None, 'wilaya'),
    ('/wilayas/{code}/communes.json', "One wilaya's communes", 'communes', '/wilayas/{code}/communes.csv', 'wilaya'),
    ('/wilayas/{code}/dairas.json', "One wilaya's daïras", 'dairas', None, 'wilaya'),
    ('/dairas.json', 'All the daïras', 'dairas', '/dairas.csv', None),
    ('/dairas/{code}.json', 'One daïra, with its communes', 'daira', None, 'commune'),
    ('/communes.json', 'The 1,541 communes', 'communes', '/communes.csv', None),
    ('/communes/{code}.json', 'One commune', 'commune', None, 'commune'),
    ('/changes.json', 'The 2026 changes: wilayas created and communes moved', 'changes', '/changes.csv', None),
    ('/texts.json', 'The official texts and lists cited', 'texts', None, None),
    ('/divisions/2019/wilayas.json', 'The 58 wilayas of the 2019 division', 'division-wilayas', None, None),
    ('/divisions/2019/communes.json', 'The communes in their wilayas of the 2019 division', 'division-communes', None, None),
]


def openapi(api_version, date):
    """The OpenAPI 3.1 description of the files, with the schemas as components."""
    components = {kind.replace('-', '_'): {k: v for k, v in schema(kind).items() if k not in ('$schema', '$id', '$defs')}
                  for kind in ['index'] + list(FILES)}
    components.update(DEFS)
    text = json.dumps(components).replace('#/$defs/', '#/components/schemas/')
    components = json.loads(text)
    params = {
        'wilaya': {'name': 'code', 'in': 'path', 'required': True, 'description': 'The wilaya code, 01 to 69',
                   'schema': {'$ref': '#/components/schemas/wilaya_code'}},
        'commune': {'name': 'code', 'in': 'path', 'required': True,
                    'description': "A commune code; for a daïra, its seat's commune code",
                    'schema': {'$ref': '#/components/schemas/commune_code'}},
    }
    paths = {}
    for path, summary, kind, csv_path, param in PATHS:
        op = {'summary': summary, 'responses': {
            '200': {'description': 'OK', 'content': {'application/json': {
                'schema': {'$ref': f"#/components/schemas/{kind.replace('-', '_')}"}}}}}}
        if param:
            op['parameters'] = [params[param]]
            op['responses']['404'] = {'description': 'No such code'}
        paths[path] = {'get': op}
        if csv_path:
            csv_op = {'summary': summary + ', as CSV', 'responses': {
                '200': {'description': 'OK', 'content': {'text/csv': {'schema': {'type': 'string'}}}}}}
            if param:
                csv_op['parameters'] = [params[param]]
                csv_op['responses']['404'] = {'description': 'No such code'}
            paths[csv_path] = {'get': csv_op}
    return {
        'openapi': '3.1.0',
        'info': {'title': 'wilayas', 'version': api_version,
                 'description': "Algeria's 69 wilayas, their daïras and 1,541 communes, from the official texts. "
                                f'Static files; data version {date}. Not an official government service.',
                 'license': {'name': 'CC0-1.0 (data), MIT (code)', 'identifier': 'CC0-1.0'}},
        'servers': [{'url': BASE_URL}],
        'paths': paths,
        'components': {'schemas': components},
    }


def dump(content):
    return json.dumps(content, ensure_ascii=False, separators=(',', ':')) + '\n'


def write(out_dir):
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    shutil.copytree(PUBLIC, out_dir)
    built = files()
    for path, (kind, content) in built.items():
        full = os.path.join(out_dir, API_DIR, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, 'w', encoding='utf-8', newline='') as f:
            f.write(content if kind == 'csv' else dump(content))
    return built


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'dist')
    built = write(out_dir)
    print(f'{len(built)} files in {os.path.join(out_dir, API_DIR)}', file=sys.stderr)


if __name__ == '__main__':
    main()

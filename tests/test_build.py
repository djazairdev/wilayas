"""Checks on the API's files: build.py writes the same files every time, each JSON file fits its
schema, the files agree with each other and with data/, every text cited is in texts.json, and
the files keep within their size budgets.

    python3 -m unittest discover -s tests

Standard library only.
"""
import csv
import glob
import gzip
import io
import json
import os
import re
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import build  # noqa: E402

# Compressed size budgets in bytes: (glob under dist/v1/, the most)
BUDGETS = [('communes.json', 100_000), ('wilayas.json', 8_000), ('wilayas/*.json', 10_000), ('wilayas/*/*', 10_000)]


def validate(instance, schema, root, path='$'):
    """The ways instance breaks schema, a JSON Schema 2020-12, as far as the keywords build.py uses go."""
    errors = []
    if '$ref' in schema:
        name = schema['$ref'].split('/')[-1]
        errors += validate(instance, root['$defs'][name], root, path)
    if 'anyOf' in schema:
        if all(validate(instance, s, root, path) for s in schema['anyOf']):
            errors.append(f'{path}: fits none of anyOf')
    if 'const' in schema and instance != schema['const']:
        errors.append(f'{path}: not {schema["const"]!r}')
    if 'enum' in schema and instance not in schema['enum']:
        errors.append(f'{path}: {instance!r} not in {schema["enum"]}')
    if 'type' in schema:
        types = schema['type'] if isinstance(schema['type'], list) else [schema['type']]
        kinds = {'string': str, 'object': dict, 'array': list, 'null': type(None), 'boolean': bool}
        ok = any(isinstance(instance, int) and not isinstance(instance, bool) if t == 'integer'
                 else isinstance(instance, kinds[t]) for t in types)
        if not ok:
            return errors + [f'{path}: {type(instance).__name__} is not {types}']
    if isinstance(instance, str):
        if 'pattern' in schema and not re.search(schema['pattern'], instance):
            errors.append(f'{path}: {instance!r} does not match {schema["pattern"]}')
        if len(instance) < schema.get('minLength', 0):
            errors.append(f'{path}: too short')
    if isinstance(instance, int) and 'minimum' in schema and instance < schema['minimum']:
        errors.append(f'{path}: below {schema["minimum"]}')
    if isinstance(instance, dict):
        for key in schema.get('required', []):
            if key not in instance:
                errors.append(f'{path}: no {key}')
        props = schema.get('properties', {})
        extra = schema.get('additionalProperties', True)
        for key, value in instance.items():
            if key in props:
                errors += validate(value, props[key], root, f'{path}.{key}')
            elif extra is False:
                errors.append(f'{path}: unexpected {key}')
            elif isinstance(extra, dict):
                errors += validate(value, extra, root, f'{path}.{key}')
    if isinstance(instance, list) and 'items' in schema:
        for i, item in enumerate(instance):
            errors += validate(item, schema['items'], root, f'{path}[{i}]')
    return errors


class Build(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dist = os.path.join(cls.tmp.name, 'dist')
        cls.built = build.write(cls.dist)
        cls.v1 = os.path.join(cls.dist, 'v1')

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def load(self, path):
        with open(os.path.join(self.v1, path), encoding='utf-8') as f:
            return json.load(f)

    def test_the_same_files_every_time(self):
        again = os.path.join(self.tmp.name, 'again')
        build.write(again)
        for path in self.built:
            with self.subTest(path=path):
                with open(os.path.join(self.v1, path), 'rb') as a, open(os.path.join(again, 'v1', path), 'rb') as b:
                    self.assertEqual(a.read(), b.read())

    def test_public_files(self):
        with open(os.path.join(self.dist, '_headers'), encoding='utf-8') as f:
            headers = f.read()
        self.assertIn('Access-Control-Allow-Origin: *', headers)
        self.assertIn('X-Content-Type-Options: nosniff', headers)
        self.assertTrue(os.path.exists(os.path.join(self.dist, 'index.html')))

    def test_every_json_file_fits_its_schema(self):
        schemas = {}
        for path, (kind, _) in self.built.items():
            if kind in ('csv', 'schema', 'openapi'):
                continue
            if kind not in schemas:
                schemas[kind] = self.load(f'schemas/{kind}.json')
            with self.subTest(path=path):
                self.assertEqual(validate(self.load(path), schemas[kind], schemas[kind])[:5], [])

    def test_schemas_and_openapi(self):
        for path, (kind, _) in self.built.items():
            if kind == 'schema':
                s = self.load(path)
                self.assertEqual(s['$schema'], 'https://json-schema.org/draft/2020-12/schema')
                for ref in re.findall(r'"#/\$defs/([a-z_0-9]+)"', json.dumps(s)):
                    self.assertIn(ref, s['$defs'], path)
        api = self.load('openapi.json')
        self.assertEqual(api['openapi'], '3.1.0')
        names = api['components']['schemas']
        for ref in re.findall(r'"#/components/schemas/([a-z_0-9]+)"', json.dumps(api)):
            self.assertIn(ref, names)
        self.assertNotIn('$defs', json.dumps(api))
        tags = [t['name'] for t in api['tags']]
        for path, item in api['paths'].items():
            self.assertEqual(len(item['get']['tags']), 1, path)
            self.assertIn(item['get']['tags'][0], tags, path)
            for param in item['get'].get('parameters', []):
                example = path.lstrip('/').replace('{code}', param['example'])
                self.assertTrue(os.path.exists(os.path.join(self.v1, example)), example)

    def test_docs_page(self):
        with open(os.path.join(self.dist, 'docs', 'index.html'), encoding='utf-8') as f:
            page = f.read()
        self.assertIn("url: '/v1/openapi.json'", page)
        self.assertIn('validatorUrl: null', page)
        tags = re.findall(r'<(?:script|link)\b[^>]*>', page)
        external = [t for t in tags if 'https://' in t]
        self.assertEqual(len(external), 2)
        for tag in external:
            self.assertRegex(tag, r'swagger-ui-dist@\d+\.\d+\.\d+/', 'an exact version')
            self.assertRegex(tag, r'integrity="sha256-[A-Za-z0-9+/]{43}="', 'an integrity hash')
            self.assertIn('crossorigin="anonymous"', tag)

    def expand(self, template):
        """The files a path with {code} stands for."""
        if '{code}' not in template:
            return [template]
        if template.startswith('wilayas/'):
            codes = [w['code'] for w in self.load('wilayas.json')['wilayas']]
        elif template.startswith('dairas/'):
            codes = [d['code'] for d in self.load('dairas.json')['dairas']]
        else:
            codes = [c['code'] for c in self.load('communes.json')['communes']]
        return [template.replace('{code}', c) for c in codes]

    def test_every_listed_path_exists(self):
        index = self.load('index.json')
        listed = set(index['files'].values())
        for path in self.load('openapi.json')['paths']:
            self.assertIn(path.lstrip('/'), listed)
        for template in listed:
            for path in self.expand(template):
                self.assertTrue(os.path.exists(os.path.join(self.v1, path)), path)
        self.assertEqual(index['counts'], {'wilayas': 69, 'dairas': 538, 'communes': 1541, 'changes': 119})
        self.assertEqual(index['data_version'], build.data_version())
        self.assertEqual(index['version'], build.version())
        self.assertEqual(self.load('openapi.json')['info']['version'], build.version())
        self.assertEqual(index['base_url'], f'https://wilayas.djazair.dev/v{build.API_MAJOR}/')

    def test_files_agree(self):
        wilayas = self.load('wilayas.json')['wilayas']
        communes = self.load('communes.json')['communes']
        dairas = self.load('dairas.json')['dairas']
        version = build.data_version()
        for w in wilayas:
            with self.subTest(wilaya=w['code']):
                one = self.load(f"wilayas/{w['code']}.json")
                self.assertEqual(one['data_version'], version)
                mine = [c for c in communes if c['wilaya'] == w['code']]
                self.assertEqual(self.load(f"wilayas/{w['code']}/communes.json")['communes'], mine)
                self.assertEqual([c['code'] for c in one['wilaya']['communes']], [c['code'] for c in mine])
                self.assertEqual(len(mine), w['counts']['communes'])
                self.assertEqual(len(one['wilaya']['dairas']), w['counts']['dairas'])
                self.assertEqual(self.load(f"wilayas/{w['code']}/dairas.json")['dairas'],
                                 [d for d in dairas if d['wilaya'] == w['code']])
                slugs = [c['slug'] for c in mine]
                self.assertEqual(len(slugs), len(set(slugs)), 'slugs are unique within a wilaya')
                if w['seat']:
                    self.assertIn(w['seat'], [c['code'] for c in mine])
        for c in communes:
            self.assertEqual(self.load(f"communes/{c['code']}.json")['commune'], c)
        for d in dairas:
            one = self.load(f"dairas/{d['code']}.json")['daira']
            self.assertEqual([c['code'] for c in one['communes']], [c['code'] for c in communes if c['daira'] == d['code']])
        division = self.load('divisions/2019/wilayas.json')['wilayas']
        self.assertEqual(len(division), 58)
        self.assertEqual(sum(w['communes'] for w in division), 1541)

    def test_csv_files_match_the_json(self):
        pairs = [('wilayas.csv', 'wilayas.json', 'wilayas'), ('communes.csv', 'communes.json', 'communes'),
                 ('dairas.csv', 'dairas.json', 'dairas'), ('changes.csv', 'changes.json', 'changes')]
        pairs += [(f'wilayas/{n:02d}/communes.csv', f'wilayas/{n:02d}/communes.json', 'communes') for n in range(1, 70)]
        for csv_path, json_path, key in pairs:
            with self.subTest(path=csv_path):
                with open(os.path.join(self.v1, csv_path), 'rb') as f:
                    raw = f.read()
                self.assertFalse(raw.startswith(b'\xef\xbb\xbf'))
                self.assertNotIn(b'\r', raw)
                rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8'))))
                records = self.load(json_path)[key]
                self.assertEqual([r.get('code') or r.get('subject') for r in rows],
                                 [r.get('code') or r.get('subject') for r in records])

    def test_every_text_cited_is_in_texts_json(self):
        texts = self.load('texts.json')
        known = {t['id'] for t in texts['texts']} | {t['id'] for t in texts['lists']}
        cited = set()

        def walk(x):
            if isinstance(x, dict):
                if set(x) >= {'text', 'article'}:
                    cited.add(x['text'])
                if 'amended_by' in x and x['amended_by']:
                    cited.add(x['amended_by'])
                if set(x) == {'ar', 'fr'} and all(v in known for v in x.values()):
                    cited.update(x.values())
                if 'texts' in x and isinstance(x['texts'], list) and x.get('lang'):
                    cited.update(x['texts'])
                for v in x.values():
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
        for path in ('wilayas.json', 'communes.json', 'dairas.json', 'changes.json'):
            walk(self.load(path))
        for c in self.load('communes.json')['communes']:
            cited.update(c['names_from'].values())
        self.assertEqual(cited - known, set())

    def test_size_budgets(self):
        for pattern, most in BUDGETS:
            for path in glob.glob(os.path.join(self.v1, pattern)):
                if os.path.isfile(path):
                    with open(path, 'rb') as f:
                        size = len(gzip.compress(f.read()))
                    self.assertLessEqual(size, most, os.path.relpath(path, self.v1))


if __name__ == '__main__':
    unittest.main()

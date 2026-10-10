"""Checks on tools/release.py and CHANGELOG.md: the changelog's entries, the version's checks, and
the guard that a change to the API's files gets a title that releases it.

    python3 -m unittest discover -s tests

Standard library only.
"""
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import build  # noqa: E402
import release  # noqa: E402

# What a throwaway repository needs to build the API
TREE = ['build.py', 'CHANGELOG.md', 'version.txt', 'public'] + release.TABLES


class Changelog(unittest.TestCase):
    def test_entries(self):
        with open(os.path.join(ROOT, 'CHANGELOG.md'), encoding='utf-8') as f:
            found = build.changelog(f.read())
        self.assertTrue(found)
        versions = [release.parse(v) for v, _, _ in found]
        self.assertEqual(versions, sorted(set(versions), reverse=True), 'newest first, one entry a version')
        dates = [d for _, d, _ in found]
        self.assertEqual(dates, sorted(dates, reverse=True))
        for version, _, entry in found:
            self.assertTrue(entry, version)
        self.assertEqual(release.current()[0], build.version())

    def test_entries_parse(self):
        text = ('# Changelog\n\n## 1.2.3 (2026-10-09) is a heading\n\n'
                '## [1.2.0](https://github.com/djazairdev/wilayas/compare/v1.1.0...v1.2.0) (2026-12-01)\n\n\n'
                '### Features\n\n* New data.\n\n## 1.1.0 (2026-11-25)\n\n- New.\n\n## 1.0.0 (2026-10-09)\n\n- Old.\n')
        self.assertEqual(build.changelog(text), [('1.2.0', '2026-12-01', '### Features\n\n* New data.'),
                                                 ('1.1.0', '2026-11-25', '- New.'), ('1.0.0', '2026-10-09', '- Old.')])

    def test_titles_that_release(self):
        for title in ['fix: wrong name for Adrar', 'fix(data): a citation', 'feat: postal codes', 'perf: smaller files',
                      'revert: fix: x', 'refactor!: rename a field']:
            self.assertTrue(release.releases(title), title)
        for title in ['docs: the setup', 'chore(main): release 1.2.0', 'ci: cache', 'Fix the data', 'fix:no space', '']:
            self.assertFalse(release.releases(title), title)


class Repository(unittest.TestCase):
    """release.py in a throwaway repository that holds what build.py needs."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        for path in TREE:
            src, dst = os.path.join(ROOT, path), os.path.join(self.root, path)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            (shutil.copytree if os.path.isdir(src) else shutil.copy)(src, dst)
        self.git('init', '-q')
        self.commit()
        self.git('tag', 'base')
        self.version = release.current()[0]
        self.saved = release.ROOT
        release.ROOT = self.root

    def tearDown(self):
        release.ROOT = self.saved
        self.tmp.cleanup()

    def git(self, *args):
        subprocess.run(['git', '-c', 'user.name=test', '-c', 'user.email=test@example.invalid', *args],
                       cwd=self.root, check=True, capture_output=True)

    def commit(self):
        self.git('add', '-A')
        self.git('commit', '-q', '--allow-empty', '-m', 'test')

    def edit(self, path, old, new):
        full = os.path.join(self.root, path)
        with open(full, encoding='utf-8') as f:
            text = f.read()
        self.assertIn(old, text)
        with open(full, 'w', encoding='utf-8') as f:
            f.write(text.replace(old, new, 1))
        self.commit()

    def run_quietly(self, function, *args):
        with contextlib.redirect_stdout(io.StringIO()):
            function(*args)

    def new_version(self, version, date='2099-01-01'):
        # Above the latest entry, whichever form release-please gave its heading
        full = os.path.join(self.root, 'CHANGELOG.md')
        with open(full, encoding='utf-8') as f:
            text = f.read()
        latest = build.HEADING.search(text).group(0)
        self.edit('CHANGELOG.md', latest, f'## {version} ({date})\n\n- A change.\n\n{latest}')
        self.edit('version.txt', self.version, version)

    def test_the_version_passes(self):
        self.run_quietly(release.check)

    def test_the_major_version_is_the_path(self):
        self.new_version('2.0.0')
        with self.assertRaises(SystemExit):
            self.run_quietly(release.check)

    def test_version_txt_matches_the_changelog(self):
        self.edit('version.txt', self.version, '9.9.9')
        with self.assertRaises(SystemExit):
            self.run_quietly(release.check)

    def test_unchanged_files_take_any_title(self):
        self.edit('CHANGELOG.md', '# Changelog', '# The changelog')
        self.run_quietly(release.guard, 'base', 'docs: the changelog')

    def test_changed_files_need_a_title_that_releases_them(self):
        self.edit('data/communes.csv', 'Adrar', 'Adrarr')
        with self.assertRaises(SystemExit):
            self.run_quietly(release.guard, 'base', 'docs: a name')
        self.run_quietly(release.guard, 'base', 'fix(data): a name')


if __name__ == '__main__':
    unittest.main()

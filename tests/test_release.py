"""Checks on tools/release.py and CHANGELOG.md: the changelog's entries, and the check that a
change to the API's files gets a new version.

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
TREE = ['build.py', 'CHANGELOG.md', 'public'] + release.TABLES


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
        text = ('# Changelog\n\n## 1.2.3 (2026-10-09) is a heading\n\n## 1.1.0 (2026-11-25)\n\n- New.\n\n'
                '## 1.0.0 (2026-10-09)\n\n- Old.\n')
        self.assertEqual(build.changelog(text), [('1.1.0', '2026-11-25', '- New.'), ('1.0.0', '2026-10-09', '- Old.')])

    def test_release_notes_link_to_the_tag(self):
        notes = release.release_notes('See [the data](data/README.md), [OSM](https://x.org) and [below](#b).', 'v1.0.0')
        self.assertEqual(notes, 'See [the data](https://github.com/djazairdev/wilayas/blob/v1.0.0/data/README.md), '
                                '[OSM](https://x.org) and [below](#b).')


class Check(unittest.TestCase):
    """release.check() in a throwaway repository that holds what build.py needs."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        for path in TREE:
            src, dst = os.path.join(ROOT, path), os.path.join(self.root, path)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            (shutil.copytree if os.path.isdir(src) else shutil.copy)(src, dst)
        self.git('init', '-q')
        self.commit()
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

    def check(self):
        with contextlib.redirect_stdout(io.StringIO()):
            release.check()

    def new_entry(self, version, date='2099-01-01'):
        self.edit('CHANGELOG.md', f'## {self.version} (', f'## {version} ({date})\n\n- A change.\n\n## {self.version} (')

    def test_a_new_version_passes(self):
        self.check()

    def test_a_released_version_whose_files_are_the_same_passes(self):
        self.git('tag', 'v' + self.version)
        self.edit('CHANGELOG.md', 'When a change alters', 'When a change to the data alters')
        self.check()

    def test_changed_files_need_a_new_version(self):
        self.git('tag', 'v' + self.version)
        self.edit('data/communes.csv', 'Adrar', 'Adrarr')
        with self.assertRaises(SystemExit):
            self.check()
        major, minor, patch = release.parse(self.version)
        self.new_entry(f'{major}.{minor}.{patch + 1}')
        self.check()

    def test_a_version_not_newer_than_the_last_release_fails(self):
        self.git('tag', 'v1.2.0')
        self.new_entry('1.1.9')
        with self.assertRaises(SystemExit):
            self.check()

    def test_the_major_version_is_the_path(self):
        self.new_entry('2.0.0')
        with self.assertRaises(SystemExit):
            self.check()


if __name__ == '__main__':
    unittest.main()

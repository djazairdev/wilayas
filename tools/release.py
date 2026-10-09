"""Tag and release each version of the API (docs/deploy.md#releases).

The version is the latest entry in CHANGELOG.md, headed "## 1.2.3 (2026-10-09)". Its release
is the git tag v1.2.3 and a GitHub release of the same name, with the entry as its notes and the
files attached: the built API as a zip, and the tables in data/.

    python3 tools/release.py check         # fails if the API's files changed since the version's
                                           # release, or the version isn't newer than the last one
    python3 tools/release.py notes         # prints the version's changelog entry
    python3 tools/release.py publish DIST  # tags HEAD and creates the release, unless it exists

check builds the API as it was at the version's tag and compares it with the API built now: any
file that differs, data or schema, needs a new version. check and publish need the repository's
tags (git fetch --tags); publish needs gh and GH_TOKEN.

Standard library only.
"""
import filecmp
import io
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import build  # noqa: E402

REPOSITORY = os.environ.get('GITHUB_REPOSITORY') or 'djazairdev/wilayas'
SEMVER = re.compile(r'^(\d+)\.(\d+)\.(\d+)$')
# The tables attached to each release
TABLES = ['data/wilayas.csv', 'data/dairas.csv', 'data/communes.csv', 'data/changes.csv', 'data/aliases.csv',
          'data/texts.csv', 'data/ons.csv']


def parse(version):
    return tuple(int(n) for n in SEMVER.match(version).groups())


def current():
    """(version, date, entry) of the latest changelog entry, checked."""
    version, date, entry = build.latest(ROOT)
    if not entry:
        raise SystemExit(f'CHANGELOG.md: the entry for {version} is empty')
    if parse(version)[0] != build.API_MAJOR:
        raise SystemExit(f'CHANGELOG.md: {version} is not a version of /{build.API_DIR}/. A breaking change is a new '
                         'major version, served under a new path: change API_MAJOR in build.py too.')
    return version, date, entry


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout


def released():
    """The versions released so far, oldest first: the tags v1.2.3."""
    found = [t[1:] for t in git('tag', '--list', 'v*').split() if SEMVER.match(t[1:])]
    return sorted(found, key=parse)


def build_into(src, out):
    """Runs the build.py of the tree src into out/."""
    subprocess.run([sys.executable, '-I', 'build.py', out], cwd=src, check=True, capture_output=True)
    return out


def built_at(ref, tmp):
    """The API as it was at a git ref, built under tmp/."""
    src = os.path.join(tmp, 'src')
    os.makedirs(src)
    archive = subprocess.run(['git', 'archive', '--format=tar', ref], cwd=ROOT, check=True, capture_output=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(src, filter='data')
    return build_into(src, os.path.join(tmp, 'dist'))


def differences(a, b):
    """The paths under two directories that are in one only, or differ."""
    out, stack = [], [('', filecmp.dircmp(a, b))]
    while stack:
        prefix, c = stack.pop()
        out += [prefix + n for n in c.left_only + c.right_only + c.funny_files]
        out += [prefix + n for n in c.common_files
                if not filecmp.cmp(os.path.join(c.left, n), os.path.join(c.right, n), shallow=False)]
        stack += [(f'{prefix}{n}/', sub) for n, sub in c.subdirs.items()]
    return sorted(out)


def check():
    version, _, _ = current()
    versions = released()
    if version in versions:
        with tempfile.TemporaryDirectory() as tmp:
            old = built_at('v' + version, os.path.join(tmp, 'old'))
            changed = differences(old, build_into(ROOT, os.path.join(tmp, 'new')))
        if changed:
            raise SystemExit(f"The API's files changed since v{version}: {len(changed)}, such as "
                             f"{', '.join(changed[:5])}. Add an entry to CHANGELOG.md with a new version, dated "
                             'today: a patch for corrections, a minor version for new data, fields or files.')
        print(f'v{version} is released, and the API is as released.')
    elif versions and parse(version) <= parse(versions[-1]):
        raise SystemExit(f'CHANGELOG.md: {version} is not newer than the last release, v{versions[-1]}.')
    else:
        print(f'v{version} is new: CI releases it once main deploys it.')


def release_notes(entry, tag):
    """A changelog entry as release notes: its relative links point to the files at the tag."""
    return re.sub(r'\]\((?!https?://|#|mailto:)([^)]+)\)', rf'](https://github.com/{REPOSITORY}/blob/{tag}/\1)', entry)


def publish(dist):
    version, date, notes = current()
    tag = 'v' + version
    if version in released():
        print(f'{tag} is already released.')
        return
    with tempfile.TemporaryDirectory() as tmp:
        notes_path = os.path.join(tmp, 'notes.md')
        with open(notes_path, 'w', encoding='utf-8') as f:
            f.write(release_notes(notes, tag) + '\n')
        archive = shutil.make_archive(os.path.join(tmp, f'wilayas-{tag}'), 'zip', dist, build.API_DIR)
        assets = [archive] + [os.path.join(ROOT, t) for t in TABLES]
        subprocess.run(['gh', 'release', 'create', tag, '--target', git('rev-parse', 'HEAD').strip(),
                        '--title', f'{tag} ({date})', '--notes-file', notes_path, *assets], cwd=ROOT, check=True)
    print(f'Released {tag}.')


def main():
    command = sys.argv[1:2]
    if command == ['check']:
        check()
    elif command == ['notes']:
        print(current()[2])
    elif command == ['publish'] and len(sys.argv) == 3:
        publish(sys.argv[2])
    else:
        raise SystemExit(__doc__)


if __name__ == '__main__':
    main()

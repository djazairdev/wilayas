"""Checks on the API's versions, and the files of each release (docs/deploy.md#releases).

release-please makes the versions: it reads the titles of the pull requests merged into main,
keeps a release pull request open with the next version, and tags v1.2.3 and creates the GitHub
release when that pull request is merged. This script checks what release-please can't:

    python3 tools/release.py check              # the version is right for the API's path
    python3 tools/release.py guard BASE TITLE   # a pull request that changes the API's files has
                                                # a title that releases them
    python3 tools/release.py attach TAG DIST    # attaches the built API and the tables to a release

guard builds the API as it was at BASE and as it is now, and compares the two: if any file differs,
data or schema, the title must be fix:, feat:, perf: or revert:, or mark a breaking change (!), so
that the change is released. attach needs gh and GH_TOKEN.

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

SEMVER = re.compile(r'^(\d+)\.(\d+)\.(\d+)$')
# A Conventional Commit title: the type, an optional scope, ! for a breaking change, the summary
TITLE = re.compile(r'(\w+)(?:\([\w./-]+\))?(!)?: \S.*')
# The types release-please releases: feat is a minor version, the others a patch
RELEASING = {'feat', 'fix', 'perf', 'revert'}
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
    with open(os.path.join(ROOT, 'version.txt'), encoding='utf-8') as f:
        written = f.read().strip()
    if written != version:
        raise SystemExit(f'version.txt says {written}, but the latest entry in CHANGELOG.md is {version}: '
                         'release-please updates both.')
    return version, date, entry


def releases(title):
    """Whether release-please releases a pull request with this title."""
    m = TITLE.fullmatch(title.strip())
    return bool(m) and (m.group(1) in RELEASING or bool(m.group(2)))


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


def changed(base):
    """The API's files that differ between the git ref base and the working tree."""
    with tempfile.TemporaryDirectory() as tmp:
        old = built_at(base, os.path.join(tmp, 'old'))
        return differences(old, build_into(ROOT, os.path.join(tmp, 'new')))


def check():
    version, _, _ = current()
    print(f'{version} is a version of /{build.API_DIR}/, in CHANGELOG.md and version.txt.')


def guard(base, title):
    files = changed(base)
    if not files:
        print("The API's files are unchanged: any title will do.")
    elif releases(title):
        print(f"The API's files change ({len(files)}), and the title releases them.")
    else:
        raise SystemExit(
            f"This pull request changes the API's files ({len(files)}, such as {', '.join(files[:5])}), so its title "
            'must release them: "fix: …" for a correction to the data, "feat: …" for new data, fields or files. '
            f'The title is "{title}". Edit it, and this check runs again.')


def attach(tag, dist):
    """Attaches the built API, as a zip of v1/, and the tables to the release tag."""
    with tempfile.TemporaryDirectory() as tmp:
        archive = shutil.make_archive(os.path.join(tmp, f'wilayas-{tag}'), 'zip', dist, build.API_DIR)
        assets = [archive] + [os.path.join(ROOT, t) for t in TABLES]
        subprocess.run(['gh', 'release', 'upload', tag, '--clobber', *assets], cwd=ROOT, check=True)
    print(f'Attached the API and the tables to {tag}.')


def main():
    args = sys.argv[1:]
    if args == ['check']:
        check()
    elif args[:1] == ['guard'] and len(args) == 3:
        guard(args[1], args[2])
    elif args[:1] == ['attach'] and len(args) == 3:
        attach(args[1], args[2])
    else:
        raise SystemExit(__doc__)


if __name__ == '__main__':
    main()

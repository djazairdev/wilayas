## What and why

<!-- What does this change, and why? Link the issue: Closes #12 -->

## Evidence

<!-- For a change to the data: the official text, its Journal officiel issue, and the PDF page that shows it. Delete this section otherwise. -->

## Checks

- [ ] The title says what it changes: `fix(data):` for a correction, `feat:` for new data, fields or files, `docs:`, `test:`, `ci:` or `chore:` when the API's files don't change
- [ ] `python3 tools/resolve.py --check`, `python3 tools/release.py check` and `python3 -m unittest discover -s tests` pass
- [ ] I changed `data/source/`, not the tables in `data/`, and ran `python3 tools/resolve.py`

## AI assistance

- [ ] I used no AI tools for this change.
- [ ] I used AI tools (name them, and say what they did). I understand every line, and I ran the checks myself.

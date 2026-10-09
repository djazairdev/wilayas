# Instructions for coding agents

<!-- djazairdev-template: 1.0.0 -->

This file tells coding agents (Claude Code, Codex, Cursor, Copilot and others) how to work in this repository. [CONTRIBUTING.md](CONTRIBUTING.md) says the same for people.

## The project

A static API of Algeria's wilayas, daïras and communes, built from the official texts. `data/source/` holds the transcriptions of the texts; `tools/resolve.py` turns them into the tables in `data/`; `build.py` turns the tables into the API's files in `dist/v1/` (JSON, CSV, JSON Schemas, OpenAPI); `src/worker.js` and `public/` serve them on Cloudflare Workers. Python 3.12+, standard library only.

## Commands

```bash
python3 build.py                          # build dist/
python3 -m compileall -q build.py tools tests
node --check src/worker.js
python3 tools/resolve.py --check          # the tables match the transcriptions
python3 tools/release.py check            # a change to the API's files has a new version (needs the tags)
python3 -m unittest discover -s tests     # the tests CI runs
```

## Rules

- Run the checks above before you say a change is done, and say if any fails.
- **Python's standard library only.** No packages, in the tools, the build or the tests.
- **The data comes only from official texts**, transcribed as printed. Never copy another dataset, even an open one, and never "fix" a spelling the text prints. Wikidata may be compared with, never copied from.
- **Never edit `data/*.csv` by hand.** Change the transcription in `data/source/`, then run `python3 tools/resolve.py`.
- **Who read a name.** In `data/source/readings.csv`, a reading an agent made records the agent in `by`, never a person; only the maintainer fills `reviewed_by`.
- **Versions.** A change to the API's files needs a new entry in `CHANGELOG.md` (`## 1.2.3 (YYYY-MM-DD)`), as [docs/deploy.md](docs/deploy.md#releases) says.
- Don't put the Worker's workers.dev address in any file: write `<account>`.
- Don't push, merge, deploy, publish a release, or change repository settings unless the maintainer asks. A merge to `main` deploys the API and can release a version.
- Never commit secrets, tokens or personal data, and don't change the licences.

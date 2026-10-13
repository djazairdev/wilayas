# Contributing

Thanks for helping. Newcomers are welcome: you don't need to be an expert, and no question is too small.

## Ways to help

- **Report a data error.** A name, code or citation that doesn't match the official texts: use the [Data error form](https://github.com/djazairdev/wilayas/issues/new?template=data-error.yml), with the text that shows it.
- **Pick an issue.** Issues labelled [good first issue](https://github.com/djazairdev/wilayas/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) are small and well described; [help wanted](https://github.com/djazairdev/wilayas/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22) issues need more context but are ready for anyone. Comment on the issue to say you're working on it, and say so if you stop.
- **Something bigger?** Open an issue first and agree on the approach.

## Set up

Everything runs on **Python 3.12 or later**, with the standard library only: there is nothing else to install.

- **Check your version** with `python3 --version`. macOS comes with Python 3.9, which is too old: install the latest from [python.org](https://www.python.org/downloads/), or with `brew install python`.
- **On Windows,** install Python from [python.org](https://www.python.org/downloads/) and type `py` wherever this guide says `python3`.

New to pull requests? GitHub's guide to [contributing to a project](https://docs.github.com/en/get-started/exploring-projects-on-github/contributing-to-a-project) walks through each step below.

1. [Fork the repository](https://github.com/djazairdev/wilayas/fork), then clone your fork and make a branch:

   ```bash
   git clone https://github.com/<your-username>/wilayas
   cd wilayas
   git switch -c fix-the-thing
   ```

2. Build the API and look at it:

   ```bash
   python3 build.py                      # writes the API's files to dist/ in under a second
   python3 -m http.server -d dist 8000   # then open http://localhost:8000/v1/index.json
   ```

   To serve it exactly as Cloudflare does, with the Worker in `src/worker.js` (its headers and the docs page), run `npx wrangler dev` instead. That one needs Node.js.

## Run the checks

The same commands CI runs on every pull request. They take about 15 seconds:

```bash
python3 -m compileall -q build.py tools tests
node --check src/worker.js          # only if you changed the Worker; needs Node.js
python3 tools/resolve.py --check    # the tables in data/ are up to date
python3 tools/release.py check      # the version is right for /v1/
python3 -m unittest discover -s tests
```

## How the data works

- **Only official texts.** Every record comes from a text in the Journal officiel, or from ONS's code géographique for commune codes, and cites it. We never copy another dataset, even an open one: we only compare with them.
- **As printed.** The transcriptions in [`data/source/`](data/source/) give each name as the text prints it. A spelling that looks wrong is not an error if the text prints it that way ([why](data/source/README.md#spellings)).
- **Never edit the tables by hand.** [`tools/resolve.py`](tools/resolve.py) makes the tables in `data/` from the transcriptions: correct the transcription, then run `python3 tools/resolve.py`. [`data/README.md`](data/README.md) describes every table and column.
- A change to `data/source/` needs the text that supports it, linked in the pull request.
- **Arabic and French only.** The official texts print names in those two languages, so the API has no other. Names in Tamazight, or translations, come in only when an official text prints them.

### Words you'll meet

| Word | Meaning |
|---|---|
| wilaya | One of Algeria's 69 provinces |
| daïra | A district of a wilaya, which groups communes |
| commune | A municipality, the smallest division |
| chef-lieu | A wilaya's capital |
| seat | The commune a daïra is named after |
| JO | The *Journal officiel*, Algeria's official gazette, printed in an Arabic and a French edition |
| ONS | The *Office national des statistiques*, which publishes the communes' codes |
| transcription | A text's names, copied as printed, in [`data/source/`](data/source/) |
| reading | A name read on the printed page by a person or a tool, recorded in [`data/source/readings.csv`](data/source/readings.csv) |

[`data/source/README.md`](data/source/README.md) explains how each text was transcribed. You don't need to read it to contribute.

## Correct a name

The most useful fix is a name that doesn't match the printed text.

1. **Find where the name comes from.** Each record in the API says so: in [`communes/0302.json`](https://wilayas.djazair.dev/v1/communes/0302.json), `names_from` gives the text that names it (`executive-decree-26-253`), and `listed_by` its row in that text (`"article": "03", "item": "2/1"`: wilaya 03, daïra 2, item 1). The row is in `data/source/executive-decree-26-253.csv`, and [`data/texts.csv`](data/texts.csv) links the text's PDFs, in Arabic and in French.
2. **Compare it with the print.** If the transcription differs from the page, that's an error to fix. If the page itself looks wrong, it isn't: we keep names as printed ([why](data/source/README.md#spellings)).
3. **Fix the row** in `data/source/`, letter for letter as printed. A daïra's seat is printed apart from the commune that heads its list, so if you correct one, check the other. Then record that you read it on the page: set the row's `check` to `eye`, and add a row to [`data/source/readings.csv`](data/source/readings.csv) with the text, article and item, the edition (`ar` or `fr`), the name, the PDF's page number, your GitHub username in `by`, `reviewed_by` left empty (a maintainer fills it), and a short note on what was wrong. If the name already has a row there, update that row instead.
4. **Rebuild the tables and run the checks:** `python3 tools/resolve.py`, then the commands in *Run the checks*. The tests compare each text with the others. If one says that names differ, its message lists them: correct the other text too if it's also wrong, or, if the two texts really print the name differently, add the pair to the table it names in `tests/test_sources.py`.
5. **Open the pull request** with a title such as `fix(data): Ksar El Hirane in Decree 26-253`, and link the PDF page that shows the name.

If you'd rather not change files, the [Data error form](https://github.com/djazairdev/wilayas/issues/new?template=data-error.yml) is just as welcome.

## Versions

You don't pick the version or edit [`CHANGELOG.md`](CHANGELOG.md): the pull request's title does it ([how](docs/deploy.md#releases)). If your change alters what the API serves, a check makes sure the title releases it:

| Title | When | Version |
|---|---|---|
| `fix(data): wrong name for commune 3101` | A correction to the data | Patch, `1.1.2` |
| `feat: add the 2026 daïras` | New data, fields or files | Minor, `1.2.0` |
| `docs: explain the codes` | Docs, tests, tools: the API's files don't change | None |

Use `test:`, `ci:`, `chore:` or `refactor:` for other changes that leave the API as it is. A change that could break a client (`feat!:`) needs a new path, `/v2/`: talk to the maintainers first.

## Send a pull request

1. Make one change per pull request, on a branch of your fork (see *Set up*), with a test when you change behaviour.
2. Run the checks above.
3. Push your branch (`git push -u origin fix-the-thing`) and open the pull request, with a title as above. Say what it changes and why, and link the issue (`Closes #12`).
4. If CI fails and you can't tell why, say so in the pull request: we'll help.

CI runs the checks. Pull requests are squash-merged, so the title becomes the commit's message.

## Review

- A maintainer reviews every pull request; we may ask for changes, which is normal.
- **CI on a pull request from a fork waits until a maintainer approves the run.** That's a safety setting, not a judgement on your change.
- Answer review comments with new commits rather than a force-push, so the conversation stays readable. The squash merge tidies the history.
- A maintainer merges once CI passes and every conversation is resolved.
- Nothing is closed automatically. If a pull request goes quiet for a long time, we ask before we close it.

## AI-assisted contributions

AI coding tools are welcome. You are the author: understand every line you submit, run the checks yourself, and say in the pull request which tool you used and what it did. A name a tool read from a text is the tool's reading (`by` in `data/source/readings.csv`), never yours. No agent opens an issue, a pull request or a comment on its own. [AGENTS.md](AGENTS.md) has the rules your agent follows.

## Our pledge

The maintainers reply to every newcomer's pull request within 7 days, even if only to say when we'll review it.

## Conduct and security

Everyone follows the [code of conduct](https://github.com/djazairdev/.github/blob/main/CODE_OF_CONDUCT.md). Report security problems privately, as the [security policy](https://github.com/djazairdev/.github/blob/main/SECURITY.md) says, never in a public issue.

## Licence

The code is released under the [MIT licence](LICENSE) and the data under [CC0 1.0](LICENSE-data). By submitting a contribution, you agree that it's released under the same terms, as section D.6 of [GitHub's Terms of Service](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service) provides, and that you have the right to submit it. Data comes only from the official texts (*How the data works*): never from another dataset, even an open one.

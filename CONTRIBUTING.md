# Contributing

Thanks for helping. Newcomers are welcome: you don't need to be an expert, and no question is too small.

## Ways to help

- **Report a data error.** A name, code or citation that doesn't match the official texts: use the [Data error form](https://github.com/djazairdev/wilayas/issues/new?template=data-error.yml), with the text that shows it.
- **Pick an issue.** Issues labelled [good first issue](https://github.com/djazairdev/wilayas/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) are small and well described; [help wanted](https://github.com/djazairdev/wilayas/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22) issues need more context but are ready for anyone. Comment on the issue to say you're working on it, and say so if you stop.
- **Something bigger?** Open an issue first and agree on the approach.

## Set up

Everything runs on Python 3.12 or later with the standard library only: there is nothing to install.

```bash
git clone https://github.com/djazairdev/wilayas
cd wilayas
python3 build.py          # writes the API's files to dist/
```

To serve `dist/` as Cloudflare does, with the Worker in `src/worker.js`, run `npx wrangler dev` (it needs Node.js).

## Run the checks

The same commands CI runs on every pull request:

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

## Versions

You don't pick the version or edit [`CHANGELOG.md`](CHANGELOG.md): the pull request's title does it ([how](docs/deploy.md#releases)). If your change alters what the API serves, a check makes sure the title releases it:

| Title | When | Version |
|---|---|---|
| `fix(data): wrong name for commune 3101` | A correction to the data | Patch, `1.1.2` |
| `feat: add the 2026 daïras` | New data, fields or files | Minor, `1.2.0` |
| `docs: explain the codes` | Docs, tests, tools: the API's files don't change | None |

Use `test:`, `ci:`, `chore:` or `refactor:` for other changes that leave the API as it is. A change that could break a client (`feat!:`) needs a new path, `/v2/`: talk to the maintainers first.

## Send a pull request

1. Fork the repository and create a branch from `main`.
2. Make one change per pull request, with a test when you change behaviour.
3. Run the checks above.
4. Open the pull request with a title as above, say what it changes and why, and link the issue (`Closes #12`).

CI runs the checks. Pull requests are squash-merged, so the title becomes the commit's message.

## Review

- A maintainer reviews every pull request; we may ask for changes, which is normal.
- **CI on a pull request from a fork waits until a maintainer approves the run.** That's a safety setting, not a judgement on your change.
- Answer review comments with new commits rather than a force-push, so the conversation stays readable. The squash merge tidies the history.
- A maintainer merges once CI passes and every conversation is resolved.
- Nothing is closed automatically. If a pull request goes quiet for a long time, we ask before we close it.

## AI-assisted contributions

You're welcome to use AI coding tools, on these terms:

- **You are the author.** Understand every line you submit, and be ready to explain it in review. "The model wrote it" doesn't answer a review comment.
- **Say so.** Tick the AI box in the pull request template, and name the tool and what it did. A commit may credit it in a `Co-Authored-By:` or `Assisted-by:` trailer.
- **Run the checks yourself,** and report the results you actually got.
- **Point your agent at [AGENTS.md](AGENTS.md).** Most coding agents read it on their own, and its rules bind them as they bind you.
- **No autonomous agents.** A person writes or reviews every issue, pull request and comment; an agent may not open them on its own.
- **A name, code or citation a tool read from a text** is recorded as the tool's reading, never a person's (`by` in `data/source/readings.csv`, as [AGENTS.md](AGENTS.md) says), and a maintainer reviews it.
- **Check what a tool finds** before you report it, and report security problems privately. An unchecked report is closed.
- **Keep private things out of AI tools:** unpublished security reports, other people's personal data, and any secret.
- Maintainers may close a low-effort generated pull request or issue without a detailed review.

## Our pledge

The maintainers reply to every newcomer's pull request within 7 days, even if only to say when we'll review it.

## Conduct and security

Everyone follows the [code of conduct](https://github.com/djazairdev/.github/blob/main/CODE_OF_CONDUCT.md). Report security problems privately, as the [security policy](https://github.com/djazairdev/.github/blob/main/SECURITY.md) says, never in a public issue.

## Licence

The code is released under the [MIT licence](LICENSE) and the data under [CC0 1.0](LICENSE-data). By submitting a contribution, you agree that it's released under the same terms, as section D.6 of [GitHub's Terms of Service](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service) provides, and that you have the right to submit it. Data comes only from the official texts (*How the data works*): never from another dataset, even an open one.

# wilayas

[![CI](https://github.com/djazairdev/wilayas/actions/workflows/ci.yml/badge.svg)](https://github.com/djazairdev/wilayas/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/djazairdev/wilayas?sort=semver)](https://github.com/djazairdev/wilayas/releases/latest)
[![Good first issues](https://img.shields.io/github/issues/djazairdev/wilayas/good%20first%20issue?label=good%20first%20issues&color=7057ff)](https://github.com/djazairdev/wilayas/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
[![Improvements](https://img.shields.io/github/issues/djazairdev/wilayas/enhancement?label=improvements&color=a2eeef)](https://github.com/djazairdev/wilayas/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement+sort%3Areactions-%2B1-desc)

Algeria's 69 wilayas, 538 daïras and 1,541 communes as a free API in JSON and CSV, built from the official texts in the Journal officiel, with a citation for every record. No keys, no sign-up: any website can call it.

**Live at [`https://wilayas.djazair.dev/v1/`](https://wilayas.djazair.dev/v1/index.json)**, with [API docs](https://wilayas.djazair.dev/docs/) where you can try every path.

## Quick start

```bash
curl https://wilayas.djazair.dev/v1/communes/3101.json
```

```js
const { wilayas } = await fetch('https://wilayas.djazair.dev/v1/wilayas.json').then((r) => r.json());
```

Everything else is in [`docs/`](docs/): [the files and how to call them](docs/api.md), [the official texts](docs/sources.md), and [how CI deploys and releases](docs/deploy.md). [`data/README.md`](data/README.md) describes the tables.

## Make your first contribution

1. Pick an issue labelled [good first issue](https://github.com/djazairdev/wilayas/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22).
2. Comment on it to say you're working on it.
3. Follow [CONTRIBUTING.md](CONTRIBUTING.md) to set up, test and open a pull request. It needs only Python.
4. We reply to newcomers' pull requests within 7 days. A review or a merge may take longer.

You can help without writing code, too: check names and codes against the official texts, improve the docs, or try the API in your project and tell us what's missing.

## Feedback

- [Ask a question](https://github.com/orgs/djazairdev/discussions/categories/q-a)
- [Report a data error](https://github.com/djazairdev/wilayas/issues/new?template=data-error.yml): a name, code or citation that doesn't match the official texts
- [Report a bug](https://github.com/djazairdev/wilayas/issues/new?template=bug.yml)
- [Suggest an improvement](https://github.com/djazairdev/wilayas/issues/new?template=idea.yml), or 👍 the [improvements](https://github.com/djazairdev/wilayas/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement+sort%3Areactions-%2B1-desc) you want most
- [Propose a new project](https://github.com/djazairdev/djazair.dev/discussions/categories/ideas) for Algeria
- Follow djazairdev on [Facebook](https://www.facebook.com/djazairdev) and [X](https://x.com/djazairdev) for news

Ask in Arabic, Tamazight, French or English. Code, docs and issue titles are in English, so everyone can search them. Report security problems [privately](https://github.com/djazairdev/wilayas/security/policy), never in an issue.

## Licence

Data: [CC0 1.0](LICENSE-data), use it for anything. Code: [MIT](LICENSE). This is not an official government service.

---

Part of [djazairdev](https://github.com/djazairdev): growing Algeria's open-source community through useful projects, welcoming first contributions and collaboration. Find more projects in the [djazair.dev Hub](https://djazair.dev/en/hub/). Everyone follows our [code of conduct](https://github.com/djazairdev/.github/blob/main/CODE_OF_CONDUCT.md).

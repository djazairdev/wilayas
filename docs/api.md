# Using the API

The API is a set of static, versioned files in JSON and CSV at `https://wilayas.djazair.dev/v1/`. There are no keys and no sign-up, and any website can call it. The [API docs](https://wilayas.djazair.dev/docs/) show every path, and you can try each one there.

## What it serves

- **The 69 wilayas**, with their codes, Arabic and French names and chefs-lieux.
- **The daïras**, each with its seat and its communes.
- **The 1,541 communes**, with the wilaya and the daïra each one belongs to.
- **The 2026 changes**: Law 26-06 of 4 April 2026 created 11 wilayas (59 to 69) and moved 108 communes into them. The parent wilayas run the new ones until 31 December 2026 at the latest. The API gives the old and the new wilaya of each moved commune, with the dates.
- **A citation for every record**: the text, its Journal officiel issue and the article it comes from.

## Calling it

```bash
curl https://wilayas.djazair.dev/v1/communes/3101.json
```

```js
const { wilayas } = await fetch('https://wilayas.djazair.dev/v1/wilayas.json').then((r) => r.json());
```

- Every response allows any origin (`Access-Control-Allow-Origin: *`), preflights included, so a web page can call the API directly.
- Responses may be cached for an hour (`Cache-Control: public, max-age=3600`); the data changes only with a new version.
- A code that doesn't exist, such as `/v1/communes/9999.json`, is a 404 with an empty body.
- To work offline, download a release: each one holds the whole API as a zip and the tables as CSV.

## Files

| Path | Contents |
|---|---|
| `index.json` | Counts, versions, licences and the list of files |
| `wilayas.json`, `wilayas.csv` | The 69 wilayas |
| `wilayas/{code}.json` | One wilaya, with its daïras and communes |
| `wilayas/{code}/communes.json`, `.csv` | One wilaya's communes |
| `wilayas/{code}/dairas.json` | One wilaya's daïras |
| `dairas.json`, `dairas.csv` | All the daïras |
| `dairas/{code}.json` | One daïra, with its communes. A daïra's code is its seat's commune code |
| `communes.json`, `communes.csv` | The 1,541 communes |
| `communes/{code}.json` | One commune |
| `changes.json`, `changes.csv` | The 2026 changes: the wilayas created and the communes moved |
| `texts.json` | The official texts cited, with links to their PDFs |
| `divisions/2019/wilayas.json`, `communes.json` | The 58 wilayas of the 2019 division |
| `openapi.json`, `schemas/*.json` | The OpenAPI description and the JSON Schemas |

Each JSON file is an object with `data_version`, the date of the data, and its payload under a named key:

```json
{"data_version": "2026-10-09", "commune": {"code": "0717", "name": {"ar": "القنطرة", "fr": "El Kantara"}, "wilaya": "61", "daira": "0717", "wilaya_before": {"wilaya": "07", "until": "2026-04-05", "by": {"text": "law-26-06", "article": "52 bis 12", "item": "1"}}, "…": "…"}}
```

## Versions

The versions follow [semantic versioning](https://semver.org), and the path holds the major version: `/v1/` serves every 1.x version, and only a change that could break a client would move to `/v2/`, with `/v1/` kept. `index.json` gives the version, and every file `data_version`, the date of its data. Each version is a [GitHub release](https://github.com/djazairdev/wilayas/releases), `v1.2.3`, and an entry in the [changelog](../CHANGELOG.md):

- a **patch** (1.0.1) corrects the data;
- a **minor** version (1.1.0) adds data, fields or files and leaves the old ones as they are.

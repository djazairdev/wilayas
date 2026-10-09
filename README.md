# wilayas

Algeria's 69 wilayas and 1,541 communes as a free, read-only JSON API, built from the official texts published in the Journal officiel.

> **Status: in development.** The first version is due by 30 November 2026, with [djazair.dev](https://github.com/djazairdev/djazair.dev).

## What it will serve

- **The 69 wilayas**, with their codes, Arabic and French names and chef-lieux.
- **The daïras**, each with its seat and its communes.
- **The 1,541 communes**, with the wilaya and the daïra each one belongs to.
- **The 2026 changes**: Law 26-06 of 4 April 2026 created 11 wilayas (59 to 69) and moved 108 communes into them. The parent wilayas run the new ones until 31 December 2026 at the latest. The API gives the old and the new wilaya of each moved commune, with the dates.
- **A citation for every record**: the text, its Journal officiel issue and the article it comes from.

The API is a set of static, versioned files in JSON and CSV. There are no keys and no sign-up, and any website can call it.

## Files

Under `https://wilayas.djazair.dev/v1/`. The [API docs](https://wilayas.djazair.dev/docs/) show every path, and you can try each one there.

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

## Build

The data is in [`data/`](data/), and its README describes every table and column. To build the files into `dist/` and run the tests, with Python 3.12 and nothing else:

```bash
python3 build.py
python3 -m unittest discover -s tests
```

[`docs/deploy.md`](docs/deploy.md) says how CI deploys the files to Cloudflare.

## Sources

- Law 84-09 of 4 February 1984 on the territorial division of the country, as amended, most recently by Law 26-06 of 4 April 2026 (Journal officiel n° 25 of 5 April 2026).
- Decree 84-79 of 3 April 1984 (Journal officiel n° 14 of 3 April 1984), which names wilayas 1 to 48 and their chefs-lieux.
- Presidential Decree 26-206 of 25 May 2026 (Journal officiel n° 40 of 3 June 2026), which names and numbers the new wilayas.
- Ordinance 97-14 of 31 May 1997 (Journal officiel n° 38 of 4 June 1997), which moved 24 communes of Boumerdès, Tipaza and Blida to Algiers.
- Executive Decree 91-306 of 24 August 1991 (Journal officiel n° 41 of 4 September 1991), which lists the communes of each daïra.
- Executive Decrees 92-66 of 12 February 1992 (Journal officiel n° 13 of 19 February 1992), 18-302 of 4 December 2018 (n° 72 of 5 December 2018) and 25-87 of 24 February 2025 (n° 15 of 6 March 2025), which redraw some of those daïras.
- Executive Decree 21-198 of 11 May 2021 (Journal officiel n° 38 of 20 May 2021), which rewrites those lists for the 18 wilayas Law 19-12 changed or created.
- Executive Decree 26-253 of 15 July 2026 (Journal officiel n° 52 of 21 July 2026), which rewrites those lists for the 21 wilayas Law 26-06 changed or created.
- The code géographique national of ONS, the statistics office (June 2021), for the commune codes.

This is not an official government service.

## Licences

- Data: [CC0 1.0](LICENSE-data). Use it for anything, no permission needed.
- Code: [MIT](LICENSE).

Part of [djazair.dev](https://github.com/djazairdev).

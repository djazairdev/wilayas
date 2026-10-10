# Changelog

The API's versions follow [semantic versioning](https://semver.org). [release-please](https://github.com/googleapis/release-please) writes each entry from the titles of the pull requests merged since the last version, so don't edit this file by hand ([how](docs/deploy.md#releases)). The API's files carry the entry's date as `data_version`, and `index.json` the version.

- **Patch** (`1.0.1`), from `fix:` titles: corrections to the data, such as a name misread or a citation.
- **Minor** (`1.1.0`), from `feat:` titles: new data, fields or files that leave the old ones as they are, such as a new text applied or a new field.
- **Major** (`2.0.0`): a change that could break a client, such as a field removed or renamed. It is served under a new path, `/v2/`, and `/v1/` stays.

## 1.1.1 (2026-10-09)

- `openapi.json`: every path has an `operationId`, such as `getCommune` or `listWilayasCsv`, so the [API docs](https://wilayas.djazair.dev/docs/) link to each path by name (`/docs/#/Communes/getCommune`) and clients generated from the description get readable method names.

## 1.1.0 (2026-10-09)

- API docs at [`/docs/`](https://wilayas.djazair.dev/docs/): the OpenAPI description in Swagger UI, where every path can be tried.
- `openapi.json`: the paths are grouped by tags (Index, Wilayas, Daïras, Communes, Changes, Sources, Divisions), and each code parameter has an example (wilaya `31`, daïra `3101`, commune `3101`). A daïra's code parameter is described as a daïra's, no longer as a commune's.

## 1.0.0 (2026-10-09)

The first version.

- The 69 wilayas, 538 daïras and 1,541 communes, from the official texts in the Journal officiel and ONS's code géographique of 2021 ([data/README.md](data/README.md)).
- The 2026 changes: the 11 wilayas Law 26-06 creates and the 108 communes it moves to them.
- The division of 2019: 58 wilayas.

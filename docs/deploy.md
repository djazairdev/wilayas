# Deploying

The API is a Cloudflare Worker named `djazair-wilayas`, made of static assets, the files `build.py` writes to `dist/`, behind a small Worker, [`src/worker.js`](../src/worker.js), that every request goes through ([below](#responses)). [`wrangler.jsonc`](../wrangler.jsonc) configures it, and the CI workflow ([`.github/workflows/ci.yml`](../.github/workflows/ci.yml)) deploys it.

## What CI does

On every pull request and every push to `main`, CI runs the tests on Python 3.12 and 3.13, checks that the tables in `data/` are up to date (`tools/resolve.py --check`) and that a change to the API's files has a new version ([below](#releases)), and builds `dist/`. Then:

- **A push to `main`** deploys `dist/` as the live version (`wrangler deploy`), then releases its version, if it is new ([below](#releases)).
- **A pull request from this repository** uploads a version that only its preview address serves, `pr-<number>-djazair-wilayas.<account>.workers.dev` (`wrangler versions upload`).

A deploy runs only after every test and the build pass, so a failing change never replaces the last good version.

## Turning deploys on

Deploys need three settings, and CI skips them, with a notice, until all three are there:

| Setting | Kind | Where |
|---|---|---|
| `CLOUDFLARE_API_TOKEN` | Secret | Organisation secret of djazairdev, shared with this repository |
| `CLOUDFLARE_ACCOUNT_ID` | Secret | Organisation secret of djazairdev, shared with this repository |
| `DEPLOY_ENABLED` | Variable | This repository: Settings → Secrets and variables → Actions → Variables. Set it to `true` |

`DEPLOY_ENABLED` decides when the API first goes live, and can turn deploys off again without touching the secrets.

The first deploy must come from `main`, by a push or by running the workflow by hand (Actions → CI → Run workflow): a pull request can upload a preview only once the Worker exists.

## Releases

The API's versions follow [semantic versioning](https://semver.org). The version is the latest entry in [`CHANGELOG.md`](../CHANGELOG.md), headed `## 1.2.3 (YYYY-MM-DD)`, and each version is a git tag and a GitHub release, `v1.2.3`, made by CI. `index.json` and the OpenAPI description carry the version; every file carries the entry's date as `data_version`.

- **Patch** (`1.0.1`): corrections to the data, such as a name misread or a citation.
- **Minor** (`1.1.0`): new data, fields or files that leave the old ones as they are.
- **Major** (`2.0.0`): a change that could break a client. The major version is the path: `/v1/` serves version 1, and version 2 would be served under `/v2/`, with `API_MAJOR` in `build.py` changed to match.

What CI checks and does:

- **On every pull request,** the tests run `tools/release.py check`. When the latest version is already released, it builds the API as it was at that version's tag and compares the two, file by file: if any file differs, data or schema, the pull request needs a new changelog entry. A new version must be newer than the last release, and its major version must be `API_MAJOR`.
- **Once `main` is deployed,** the `release` job tags the commit `v1.2.3` and creates the release `v1.2.3 (YYYY-MM-DD)`, unless that version is already released. The release notes are the changelog entry, and the release holds the built API as a zip (`wilayas-v1.2.3.zip`, the folder `v1/`) and the tables of `data/`.

A release always follows a successful deploy, so every release is a version that was live. While deploys are off, nothing is released. A change that leaves the API's files as they are, such as to the docs or the tests, needs no new version.

## Responses

`public/_headers` gives every file:

- `Access-Control-Allow-Origin: *`, so any website can call the API;
- `Cache-Control: public, max-age=3600, stale-while-revalidate=86400`;
- `X-Content-Type-Options: nosniff`.

JSON files are served as `application/json`, CSV files as `text/csv; charset=utf-8`.

Every request goes through the Worker first (`run_worker_first`), because Cloudflare would otherwise answer a CORS preflight for a file with a 405. The Worker passes `GET` and `HEAD` to the files and answers the rest itself, each answer with `Access-Control-Allow-Origin: *`:

- a CORS preflight (`OPTIONS`), which a browser sends before a request with headers of its own, such as `Authorization`: a 204 that allows `GET`, `HEAD` and `OPTIONS` and the headers asked for;
- `/v1` and `/v1/`, the base URL `index.json` gives: a 302 to `/v1/index.json`;
- any other path, such as a commune code that doesn't exist: a 404 with an empty body;
- any other method: a 405.

So every request to the API counts toward the account's Workers requests: 100,000 a day on the Workers free plan, shared by the account's Workers, or 10 million a month on the paid plan. Past the free plan's limit, the API answers with errors until the next day.

To serve `dist/` locally as Cloudflare would:

```bash
python3 build.py
npx wrangler dev
```

## The address

The API is served at `https://wilayas.djazair.dev/v1/`, a custom domain of the Worker (`routes` in `wrangler.jsonc`). Each deploy keeps it attached; Cloudflare manages its DNS record and certificate in the `djazair.dev` zone, so the record must not be created or edited by hand. The Worker's workers.dev address stays on, for the previews of pull requests.

# Deploying

The API is a Cloudflare Worker named `djazair-wilayas`, served at [`wilayas.djazair.dev`](#the-address). It is made of the static files `build.py` writes to `dist/`, and of a small script, [`src/worker.js`](../src/worker.js), that every request goes through ([below](#responses)). [`wrangler.jsonc`](../wrangler.jsonc) configures it, and the CI workflow ([`.github/workflows/ci.yml`](../.github/workflows/ci.yml)) deploys it.

## What CI does

On every pull request and every push to `main`, CI runs the tests on Python 3.12 and 3.13, checks that the tables in `data/` are up to date (`tools/resolve.py --check`) and that the version is right for `/v1/` ([below](#releases)), and builds `dist/`. Then:

- **A release** (`v1.2.3`) deploys `dist/` as the live version (`wrangler deploy`), then attaches its files to the release ([below](#releases)). A push to `main` doesn't deploy, so the live API is always a released version.
- **Deploying `main` by hand** (Actions → CI → Run workflow, on `main`) makes it the live version without a release, such as for a fix to the docs page. Its `index.json` still gives the last version.
- **A pull request from this repository** uploads a version that only its preview address serves, `pr-<number>-djazair-wilayas.<account>.workers.dev` (`wrangler versions upload`).

A deploy runs only after every test and the build pass, so a failing change never replaces the last good version.

## Deploy settings

Deploys need three settings, and CI skips them, with a notice, unless all three are there:

| Setting | Kind | Where |
|---|---|---|
| `CLOUDFLARE_API_TOKEN` | Secret | Organisation secret of djazairdev, shared with this repository |
| `CLOUDFLARE_ACCOUNT_ID` | Secret | Organisation secret of djazairdev, shared with this repository |
| `DEPLOY_ENABLED` | Variable | This repository: Settings → Secrets and variables → Actions → Variables. Set it to `true` |

All three are set: `DEPLOY_ENABLED` has been `true` since the first deploy, on 9 October 2026. Setting it to anything else pauses deploys without touching the secrets. A release made while deploys are off isn't deployed and gets no files: run CI by hand on its tag once deploys are back on.

If the Worker is ever deleted, the next deploy must come from `main` or a release tag, by running the workflow by hand (Actions → CI → Run workflow): a pull request can upload a preview only once the Worker exists.

## Releases

The API's versions follow [semantic versioning](https://semver.org), and [release-please](https://github.com/googleapis/release-please) makes them from the titles of the pull requests, which are [Conventional Commits](https://www.conventionalcommits.org). The version is the latest entry in [`CHANGELOG.md`](../CHANGELOG.md) and `version.txt`, and each version is a git tag and a GitHub release, `v1.2.3`. `index.json` and the OpenAPI description carry the version; every file carries the entry's date as `data_version`.

- **Patch** (`1.0.1`), from `fix:` titles: corrections to the data, such as a name misread or a citation.
- **Minor** (`1.1.0`), from `feat:` titles: new data, fields or files that leave the old ones as they are.
- **Major** (`2.0.0`): a change that could break a client. The major version is the path: `/v1/` serves version 1, and version 2 would be served under `/v2/`, with `API_MAJOR` in `build.py` changed to match.

How a version is made:

1. **Every pull request's title** is checked by `pr-title.yml`: it must be a Conventional Commit, and if the pull request changes the API's files, its title must release them. `tools/release.py guard` builds the API as it was before the pull request and as it is after, and compares the two, file by file: if any file differs, data or schema, the title must be `fix:`, `feat:`, `perf:` or `revert:`. A change that leaves the API's files as they are, such as to the docs or the tests, takes any type.
2. **Pull requests are squash-merged,** so each lands on `main` as one commit named by its title.
3. **On every push to `main`,** `release.yml` runs release-please, which keeps one pull request open, *chore(main): release 1.2.3*, with the next version in `CHANGELOG.md` and `version.txt`. A pull request made by GitHub Actions starts no workflows, so `release.yml` starts CI and the title check on it.
4. **Merging the release pull request** makes release-please tag `v1.2.3` and create the GitHub release, with the changelog entry as its notes. `release.yml` then runs CI on the tag, which deploys it and attaches the built API as a zip (`wilayas-v1.2.3.zip`, the folder `v1/`) and the tables of `data/`.

On every pull request, `tools/release.py check` also checks that the version in `CHANGELOG.md` matches `version.txt` and that its major version is `API_MAJOR`, so a breaking change can't be released under `/v1/`. The maintainers choose when to release: the release pull request can wait while changes collect.

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

## Docs

`/docs/` is the OpenAPI description, `/v1/openapi.json`, in [Swagger UI](https://github.com/swagger-api/swagger-ui). The page, [`public/docs/index.html`](../public/docs/index.html), loads Swagger UI from jsDelivr at an exact version, with integrity hashes, so a changed file doesn't load. To move to a newer version, take one released at least two weeks before, and its hashes from `https://data.jsdelivr.com/v1/packages/npm/swagger-ui-dist@<version>?structure=flat` (`sha256-` and each file's `hash`). The docs' "Try it out" calls the live API, the OpenAPI description's server.

## The address

The API is served at `https://wilayas.djazair.dev/v1/`, a custom domain of the Worker (`routes` in `wrangler.jsonc`). Each deploy keeps it attached; Cloudflare manages its DNS record and certificate in the `djazair.dev` zone, so the record must not be created or edited by hand. The Worker's workers.dev address stays on, for the previews of pull requests.

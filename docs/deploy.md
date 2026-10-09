# Deploying

The API is a Cloudflare Worker named `djazair-wilayas`, made only of static assets: the files `build.py` writes to `dist/`. There is no Worker code. [`wrangler.jsonc`](../wrangler.jsonc) configures it, and the CI workflow ([`.github/workflows/ci.yml`](../.github/workflows/ci.yml)) deploys it.

## What CI does

On every pull request and every push to `main`, CI runs the tests on Python 3.12 and 3.13, checks that the tables in `data/` are up to date (`tools/resolve.py --check`), and builds `dist/`. Then:

- **A push to `main`** deploys `dist/` as the live version (`wrangler deploy`).
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

## Responses

`public/_headers` gives every file:

- `Access-Control-Allow-Origin: *`, so any website can call the API;
- `Cache-Control: public, max-age=3600, stale-while-revalidate=86400`;
- `X-Content-Type-Options: nosniff`.

JSON files are served as `application/json`, CSV files as `text/csv; charset=utf-8`. An unknown path, such as a commune code that doesn't exist, is a 404 with an empty body (`not_found_handling: "none"`).

To serve `dist/` locally as Cloudflare would:

```bash
python3 build.py
npx wrangler dev
```

## At launch

`wilayas.djazair.dev` becomes a custom domain of the Worker: uncomment `routes` in `wrangler.jsonc`. The API's address before then is the Worker's workers.dev address.

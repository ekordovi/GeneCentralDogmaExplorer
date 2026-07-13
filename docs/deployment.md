# Deployment Runbook

## Web Demo

The Streamlit app can stay on Streamlit Community Cloud for a free public demo.
Use the deployed Streamlit URL for portfolio sharing while the native app is
still going through TestFlight.

## FastAPI Backend

The iOS app needs the FastAPI backend on HTTPS for live lookup.

1. Deploy this repository with `render.yaml`, or create an equivalent web
   service on Render, Fly.io, Railway, or another HTTPS host.
2. Confirm the hosted backend responds:

```bash
curl https://your-api-host.example/api/health
curl https://your-api-host.example/api/info
```

`/api/health` should identify the service name, version, environment, and
Ensembl REST data source. `/api/info` should also expose the public support
URL, privacy URL, educational disclaimer, endpoint list, and
`privacy_safe_logging: true`.

3. Confirm live example lookup:

```bash
curl "https://your-api-host.example/api/gene?symbol=HBB&species=homo_sapiens"
```

4. Set CORS for production:

```bash
GENE_DOGMA_ALLOWED_ORIGINS=https://gene-explorer.streamlit.app,https://your-support-site.example
GENE_DOGMA_API_ENV=production
GENE_DOGMA_API_VERSION=1.0.0
```

For a public educational API, CORS is not the main security boundary, but
restricting it keeps the production setup tidy.

## iOS API URL

For local simulator work, the Debug `GENE_DOGMA_API_BASE_URL` build setting
points to `http://127.0.0.1:8000`. `GeneDogmaAPIBaseURL` in `Info.plist` reads
from that build setting.

Before TestFlight or App Store upload:

1. Replace the Release `GENE_DOGMA_API_BASE_URL` build setting with the
   deployed HTTPS backend base URL.
2. Run the app on an iPhone simulator.
3. Verify HBB, BRCA1, and TP53 live lookup.
4. If the production build no longer needs local HTTP testing, remove the
   local-networking App Transport Security exception.

The bundled HBB example still works offline if the live backend is down.

## Uptime Check

The workflow `.github/workflows/api-health.yml` can check the deployed backend
daily. It runs `scripts/verify_v1.py --base-url`, so it verifies `/api/health`,
`/api/info`, the bundled HBB example, famous examples, and mutation behavior,
not just that a URL responds.

After the backend is deployed, add this GitHub repository variable:

```text
GENE_DOGMA_API_BASE_URL=https://your-api-host.example
```

The older `GENE_DOGMA_API_HEALTH_URL=https://your-api-host.example/api/health`
variable is still accepted for compatibility. Then run the `API Health`
workflow manually once. If neither URL is configured, the workflow exits
successfully with a notice instead of failing the repo.

## Public Support Pages

The `docs/` folder contains static pages that can be served by GitHub Pages:

- `docs/index.html`
- `docs/support.html`
- `docs/privacy.html`

In GitHub, enable Pages with source `main` and folder `/docs`. Use the resulting
support URL in App Store Connect.

This repository is currently configured for:

```text
Support URL: https://ekordovi.github.io/GeneCentralDogmaExplorer/support.html
Privacy URL: https://ekordovi.github.io/GeneCentralDogmaExplorer/privacy.html
```

## Verification Command

Run the offline v1 verifier before demos:

```bash
python scripts/verify_v1.py
python scripts/verify_ios_config.py
```

After deployment, verify the hosted API:

```bash
python scripts/verify_v1.py --base-url https://your-api-host.example --live-lookup
```

Before TestFlight or App Store upload, replace the Release API URL placeholder
in the Xcode project and run the strict release gate:

```bash
python scripts/verify_release_ready.py --live-lookup
```

This command intentionally fails while the Release build setting still points
to `https://your-api-host.example`.

## Privacy-Safe Operational Logging

Version 1 does not use analytics. The FastAPI backend logs only method, path
without query string, status code, coarse category, and duration. It does not
log gene-search terms, mutation payloads, DNA/protein sequences, health data,
names, contact details, precise device location, or analytics profiles. If
crash logging is added later, keep it at the same coarse operational level.

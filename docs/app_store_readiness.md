# App Store Readiness Checklist

## Manual Prerequisites

- Install full Xcode from the Mac App Store.
- Set full Xcode as the active developer directory:

```bash
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
```

- Enroll in the Apple Developer Program.
- Create an App Store Connect app record:
  - Name: Gene Central Dogma Explorer
  - Bundle ID: com.evankordovi.GeneCentralDogmaExplorer
  - Category: Education
  - Price: Free for v1

## Backend

- Deploy the FastAPI backend over HTTPS.
- Recommended low-cost v1 path: Render, Fly.io, Railway, or another small
  always-on HTTPS service. Avoid a free service that sleeps if the iOS app needs
  reliable live lookup during demos.
- Set `GENE_DOGMA_ALLOWED_ORIGINS` to the deployed web/support domains instead
  of leaving CORS open for every origin.
- Confirm these endpoints work:
  - `GET /api/health`
  - `GET /api/info`
  - `GET /api/example`
  - `GET /api/famous-examples`
  - `GET /api/gene?symbol=HBB&species=homo_sapiens`
  - `POST /api/mutation`
- Confirm `/api/health` includes the API name, version, and Ensembl REST data
  source. Confirm `/api/info` includes the educational disclaimer, support URL,
  privacy URL, and public endpoint list.
- Update the Release `GENE_DOGMA_API_BASE_URL` iOS build setting with the
  deployed HTTPS base URL. `Info.plist` reads `GeneDogmaAPIBaseURL` from that
  build setting.
- Add a simple uptime check for `/api/health` before TestFlight. A daily GitHub
  Actions curl or provider health check is enough for v1. This repo includes
  `.github/workflows/api-health.yml`; set `GENE_DOGMA_API_HEALTH_URL` after the
  backend is deployed.

## Native App Requirements

- Confirm the app opens to the bundled HBB example with no account required.
- Confirm the app is not a plain WebView.
- Confirm the educational disclaimer appears in the About tab.
- Confirm the privacy text matches `docs/privacy_policy.md`.
- Host the static `docs/support.html` and `docs/privacy.html` pages on a public
  support site, such as GitHub Pages from the `/docs` folder. Current URLs:
  - Support: `https://ekordovi.github.io/GeneCentralDogmaExplorer/support.html`
  - Privacy: `https://ekordovi.github.io/GeneCentralDogmaExplorer/privacy.html`
- Confirm the AppIcon asset renders correctly in Xcode and on the simulator.
- Confirm backend logs stay privacy-compliant: method, path without query
  string, status code, coarse category, and duration only. No gene-search
  payloads, mutation payloads, sequences, health data, names, contact data, or
  analytics profile.

## TestFlight

- Build and run on an iPhone simulator.
- Build and run on a real iPhone.
- Archive in Xcode and upload to App Store Connect.
- Add internal TestFlight testers first.
- Verify:
  - HBB offline demo works.
  - Live lookup works for HBB, BRCA1, and TP53.
  - Failed lookup shows a friendly error.
  - Mutation simulator shows silent/missense/nonsense/frameshift labels.
  - Text wraps cleanly on small iPhones.
- Run `python scripts/verify_v1.py` before every demo.
- Run `python scripts/verify_ios_config.py` before TestFlight upload.
- After replacing the Release API URL placeholder, run
  `python scripts/verify_release_ready.py --live-lookup` before TestFlight or
  App Store upload.

## Screenshot Plan

Capture App Store screenshots on a current iPhone simulator after the production
API URL is configured:

- First screen with the offline HBB example and central-dogma path visible.
- HBB mutation simulator showing a missense edit and compare-two-mutations.
- BRCA1 or TP53 live lookup showing trustworthy Ensembl-backed data.
- Study mode or saved genes showing why a student or teacher would come back.
- About screen showing the educational disclaimer and privacy posture.

Use `app_store/screenshots.md` for the exact screenshot captions and optional
Xcode launch arguments, such as `--gene-demo-tab=mutation --gene-demo-compare`,
that prime repeatable local demo states for screenshot capture.

## App Store Listing Draft

- Subtitle: Learn genes from DNA to RNA to protein.
- Keywords: gene, DNA, RNA, protein, biology, genetics, education, mutation
- Full metadata package: `docs/app_store_metadata.md` and
  `app_store/metadata/en-US/`.
- Description:

Gene Central Dogma Explorer helps students and curious learners understand how a
gene connects to RNA transcripts, coding sequence, proteins, and simple mutation
effects. Search a gene, explore its central-dogma path, compare transcripts, run
simple mutation examples, and read beginner-friendly explanations.

This app is for education only and is not medical advice.

## Version Updates

- `1.0`: HBB offline demo, live lookup, central-dogma path, simple mutation
  simulator, compare-two-mutations, saved genes, shareable reports, study mode,
  two-minute teacher guide, privacy/support docs, and AppIcon.
- `1.1`: More curated examples, better classroom handouts, and additional
  screenshot-ready polish after TestFlight feedback.
- Later: only add clinical or variant database integrations if the app wording,
  privacy policy, and review notes stay clear that this is educational, not
  medical decision support.

## Review Notes

Tell App Review that version 1 has no accounts, payments, ads, analytics, or
medical claims. Live lookups use the app backend and Ensembl REST. The bundled
HBB demo is available offline.

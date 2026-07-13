# Gene Central Dogma Explorer

An educational central-dogma project with three surfaces:

- A Streamlit prototype for fast iteration.
- A FastAPI backend for iOS and web clients.
- A native SwiftUI iPhone app scaffold for App Store distribution.

```text
genomic DNA -> pre-mRNA proxy -> transcript cDNA / mRNA -> coding sequence -> protein
```

The app uses Ensembl REST for live gene-symbol lookup and sequence retrieval.
It is designed to support any gene in any Ensembl-supported species, as long as
the species alias and gene symbol resolve through Ensembl.

## Features

- Search by gene symbol and species.
- Opens with a bundled HBB teaching example and guided buttons for HBB, BRCA1,
  TP53, search, and mutation simulation.
- Supports common species presets and custom Ensembl species aliases.
- Shows gene metadata: Ensembl ID, genomic region, strand, assembly, biotype,
  and description.
- Lists transcripts and highlights protein-coding translations.
- Shows genomic DNA, pre-mRNA proxy, transcript cDNA/mRNA, coding DNA/mRNA, and
  protein sequence where available.
- Provides sequence summaries and FASTA downloads.
- Includes a bundled HBB example for offline demonstration.
- Simulates simple coding-DNA edits and compares two mutations side by side.
- Exposes API endpoints for gene lookup and mutation simulation.
- Includes a native SwiftUI iOS app with offline HBB demo support.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Streamlit

```bash
streamlit run app.py
```

## Run API

```bash
uvicorn api:app --reload
```

For production, restrict browser access to your deployed web domains:

```bash
GENE_DOGMA_ALLOWED_ORIGINS=https://your-app.example,https://your-site.example uvicorn api:app
```

Important endpoints:

- `GET /api/health`
- `GET /api/example`
- `GET /api/gene?symbol=HBB&species=homo_sapiens`
- `POST /api/mutation`

Example mutation request:

```bash
curl -X POST http://127.0.0.1:8000/api/mutation \
  -H "Content-Type: application/json" \
  -d '{"coding_dna":"ATGGAGTAA","change":"5 A>T"}'
```

## iOS App

Open the native app project in full Xcode:

```bash
open iOS/GeneCentralDogmaExplorer/GeneCentralDogmaExplorer.xcodeproj
```

For simulator live lookup and mutation testing, start the local API first:

```bash
source .venv/bin/activate
uvicorn api:app --reload
```

Then run the `GeneCentralDogmaExplorer` scheme in Xcode on an iPhone simulator.
The bundled HBB demo and simple iOS mutation practice work offline. Live gene
lookup uses the Debug `GENE_DOGMA_API_BASE_URL` build setting, currently
`http://127.0.0.1:8000`, which maps from the iOS simulator back to your Mac.

Before App Store upload:

- Install full Xcode and set it active with `xcode-select`.
- Confirm the included AppIcon renders correctly in Xcode and on the simulator.
- Deploy the API over HTTPS and update the Release
  `GENE_DOGMA_API_BASE_URL` build setting in the Xcode project with that URL.
- Remove the local-networking App Transport Security exception if the production
  build no longer needs local HTTP access.
- Host `docs/support.md` and `docs/privacy_policy.md` as simple public support
  and privacy pages. GitHub Pages is configured at
  `https://ekordovi.github.io/GeneCentralDogmaExplorer/`.
- Follow `docs/deployment.md` for backend hosting, iOS production URL setup,
  and the optional GitHub Actions uptime check.
- See `docs/app_store_readiness.md`.

## Test

```bash
python -m pytest
```

The API tests require `fastapi` and `httpx` from `requirements.txt`.

To verify the core v1 learning loop without network access:

```bash
python scripts/verify_v1.py
python scripts/verify_streamlit_ui.py
python scripts/verify_app_store_metadata.py
python scripts/verify_ios_config.py
```

To verify a deployed API after hosting:

```bash
python scripts/verify_v1.py --base-url https://your-api-host.example --live-lookup
```

Before TestFlight or App Store upload, run the strict release gate after the
Release API URL points to the hosted backend:

```bash
python scripts/verify_release_ready.py --live-lookup
```

## Data Source

Live lookups use Ensembl REST endpoints:

- `/lookup/symbol/:species/:symbol?expand=1`
- `/sequence/id/:id?type=genomic`
- `/sequence/id/:id?type=cdna`
- `/sequence/id/:id?type=cds`
- `/sequence/id/:id?type=protein`

## Scientific Notes

- The pre-mRNA view is a teaching proxy made by converting genomic DNA `T` to
  RNA `U`; real pre-mRNA includes transcript context and processing details not
  fully represented by this simple view.
- The mature RNA view is based on Ensembl transcript cDNA with `T` converted to
  `U`.
- Non-coding genes or non-translated transcripts may not return CDS or protein
  sequences.

## Educational Disclaimer

This project is for education and portfolio demonstration. It is not medical
advice, diagnosis, or treatment guidance.

## Mutation Simulator Scope

Mutation mode is a simple coding-DNA teaching tool. It supports small examples
such as `20 A>T`, `20del`, and `20insA`; it does not parse HGVS notation, map
genomic coordinates to transcript coordinates, evaluate splice effects, inspect
exon boundaries, query ClinVar, or classify clinical variants.

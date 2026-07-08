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
- Supports common species presets and custom Ensembl species aliases.
- Shows gene metadata: Ensembl ID, genomic region, strand, assembly, biotype,
  and description.
- Lists transcripts and highlights protein-coding translations.
- Shows genomic DNA, pre-mRNA proxy, transcript cDNA/mRNA, coding DNA/mRNA, and
  protein sequence where available.
- Provides sequence summaries and FASTA downloads.
- Includes a bundled HBB example for offline demonstration.
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
The bundled HBB demo works offline. Live lookup and mutation calls use
`http://127.0.0.1:8000`, which maps from the iOS simulator back to your Mac.

Before App Store upload:

- Install full Xcode and set it active with `xcode-select`.
- Replace the placeholder AppIcon with real artwork.
- Deploy the API over HTTPS and update `GeneDogmaAPIClient` with that URL.
- Remove the local-networking App Transport Security exception if the production
  build no longer needs local HTTP access.
- See `docs/app_store_readiness.md`.

## Test

```bash
python -m pytest
```

The API tests require `fastapi` and `httpx` from `requirements.txt`.

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

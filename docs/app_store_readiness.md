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
- Set `GENE_DOGMA_ALLOWED_ORIGINS` to the deployed web/support domains instead
  of leaving CORS open for every origin.
- Confirm these endpoints work:
  - `GET /api/health`
  - `GET /api/example`
  - `GET /api/gene?symbol=HBB&species=homo_sapiens`
  - `POST /api/mutation`
- Update `GeneDogmaAPIBaseURL` in the iOS app `Info.plist` with the deployed
  HTTPS base URL.

## Native App Requirements

- Confirm the app opens to the bundled HBB example with no account required.
- Confirm the app is not a plain WebView.
- Confirm the educational disclaimer appears in the About tab.
- Confirm the privacy text matches `docs/privacy_policy.md`.
- Host `docs/support.md` and `docs/privacy_policy.md` on a public support site.
- Replace the placeholder AppIcon asset with a real 1024 x 1024 icon before
  App Store upload.

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

## App Store Listing Draft

- Subtitle: Learn genes from DNA to RNA to protein.
- Keywords: gene, DNA, RNA, protein, biology, genetics, education, mutation
- Description:

Gene Central Dogma Explorer helps students and curious learners understand how a
gene connects to RNA transcripts, coding sequence, proteins, and simple mutation
effects. Search a gene, explore its central-dogma path, compare transcripts, run
simple mutation examples, and read beginner-friendly explanations.

This app is for education only and is not medical advice.

## Review Notes

Tell App Review that version 1 has no accounts, payments, ads, analytics, or
medical claims. Live lookups use the app backend and Ensembl REST. The bundled
HBB demo is available offline.

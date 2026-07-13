# App Store Metadata

## App Identity

- App Store name: Gene Central Dogma Explorer
- Home screen display name: Gene Dogma
- Bundle ID: `com.evankordovi.GeneCentralDogmaExplorer`
- Category: Education
- Price: Free for v1
- Support URL: https://ekordovi.github.io/GeneCentralDogmaExplorer/support.html
- Privacy URL: https://ekordovi.github.io/GeneCentralDogmaExplorer/privacy.html

## Subtitle

Learn DNA to RNA to protein

## Promotional Text

Start with HBB, follow DNA to RNA to protein, and compare simple mutation effects with beginner-friendly explanations.

## Keywords

gene,DNA,RNA,protein,biology,genetics,education,mutation,central dogma,student

## Description

Gene Central Dogma Explorer helps students and curious learners understand how a
gene connects to RNA transcripts, coding sequence, proteins, and simple mutation
effects.

Start with the offline HBB example, then try live lookup for genes such as
BRCA1 and TP53. Follow the central dogma from DNA to RNA to protein, inspect
clear gene cards, compare two simple coding-DNA mutations, save or share a
report, and use teacher-ready study prompts to review the core idea.

Version 1 focuses on education:

- Offline HBB example for first launch and demos
- Live Ensembl-backed gene lookup through the app backend
- DNA, RNA, coding sequence, and protein views
- Simple mutation simulator for missense, nonsense, silent, and frameshift
  teaching examples
- Compare-two-mutations workflow
- Shareable gene story reports
- Saved genes, quiz mode, and a two-minute teacher guide
- Beginner-friendly explanations with advanced details available when needed

This app is for education only. It is not medical advice, diagnosis, treatment
guidance, or clinical variant interpretation.

## What's New

Version 1.0 includes the offline HBB demo, live gene lookup, central-dogma path,
simple mutation simulation, compare-two-mutations, saved genes, shareable
reports, study mode, teacher guide, public support/privacy pages, and a
privacy-first educational disclaimer.

## Screenshot Captions

1. Start with HBB
   The app opens with a classic beta-globin example instead of a blank search
   box.
2. Follow the Central Dogma
   Move from DNA to RNA to coding sequence to protein with clear visual steps.
3. Compare Mutations
   See how two coding-DNA edits can produce different mutation effects.
4. Try Live Gene Lookup
   Explore familiar genes such as BRCA1 and TP53 using Ensembl-backed data.
5. Study and Save
   Save genes and use teacher-ready prompts to turn the app into a lesson tool.

## App Review Notes

Gene Central Dogma Explorer is an educational biology app. It has no accounts,
payments, ads, analytics, or medical claims. The bundled HBB example works
offline. Live gene lookup uses the app backend, which queries Ensembl REST for
gene, transcript, sequence, and protein information. Mutation mode is a simple
coding-DNA teaching simulator and does not parse HGVS, map genomic coordinates,
query ClinVar, classify patient variants, or provide medical guidance.

## Privacy Nutrition Label Draft

- Data collected: None for v1.
- Accounts: None.
- Payments: None.
- Advertising: None.
- Analytics: None.
- Location: Not collected.
- Contacts/photos/files: Not collected.
- Health data: Not collected.
- User-provided search terms: Gene symbol, species, and optional transcript ID
  are sent to the app backend only when live lookup is used.
- Local storage: Saved gene symbols are stored locally on the device.
- Third-party services: Live lookup depends on the app backend and Ensembl REST.

## Manual Submission Checks

- Confirm production `GeneDogmaAPIBaseURL` uses HTTPS.
- Confirm HBB works offline with no account.
- Confirm HBB, BRCA1, and TP53 live lookup work against production.
- Confirm failed lookup shows a friendly message.
- Confirm mutation comparison explains missense and nonsense clearly.
- Confirm support and privacy URLs open publicly over HTTPS.
- Confirm screenshots do not imply diagnosis, treatment, or clinical variant
  interpretation.

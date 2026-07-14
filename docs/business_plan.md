# Business Plan

Gene Central Dogma Explorer is an educational biology app for students,
teachers, and interview/portfolio demos. The first value promise is simple:
pick a gene, follow DNA to RNA to protein, simulate a mutation, understand the
effect, then save or share the story for study.

## Positioning

- Category: Education.
- Price: Free for version 1.
- Primary audience: biology students, teachers, tutors, and portfolio reviewers.
- First career value: a credible bioinformatics/education product demo.
- First user value: understand the central dogma through a real gene instead of
  a blank search form.

This is not a medical product. It does not diagnose, treat, classify patient
variants, provide clinical variant interpretation, or replace professional
medical guidance.

## First 30 Seconds

The app should open with the bundled HBB example and make the workflow obvious
without instructions:

1. HBB explains how one DNA change can alter hemoglobin biology.
2. Guided buttons offer Explore HBB, BRCA1, TP53, search, and mutation mode.
3. The learner sees a gene card, central dogma path, and short explanation
   before raw sequence details.
4. Beginner mode keeps the story focused; Advanced mode exposes deeper details.

## Version 1 Scope

- Offline HBB story.
- Live Ensembl-backed lookup for genes such as HBB, BRCA1, and TP53.
- DNA, RNA, coding sequence, and protein path.
- Simple coding-DNA mutation simulator.
- Compare two mutations.
- Missense, nonsense, silent, and frameshift explanations.
- Saved genes.
- Shareable story reports and saved-gene study packs.
- Teacher guide, quiz prompts, and demo script.
- Public support and privacy pages.
- App Store metadata, screenshots plan, and review notes.

## Trust Package

- Educational-only disclaimer appears in app, web demo, support page, privacy
  page, metadata, review notes, and reports.
- Live data source is Ensembl REST through the app backend.
- The bundled HBB example works offline.
- Version 1 has no accounts, payments, ads, or analytics.
- Backend logs must stay coarse: method, endpoint path without query string,
  status code, coarse category, and duration only.
- Do not log gene-search terms, mutation payloads, DNA/protein sequences, health
  data, names, contact details, or analytics profiles.

## Distribution Plan

1. Keep the Streamlit web demo free on Streamlit Community Cloud for portfolio
   sharing and fast iteration.
2. Host the FastAPI backend over HTTPS before TestFlight/App Store submission.
3. Configure the iOS Release API URL to the production backend.
4. Enable GitHub Pages for support and privacy pages from `/docs`.
5. Use TestFlight internally before public App Store release.
6. Publish version 1 as a free Education app.

## Backend Cost Plan

For v1, use the lowest-cost reliable HTTPS backend that does not sleep during
demos. Render, Fly.io, Railway, or an equivalent small web service are all
reasonable. A free sleeping backend is acceptable for experiments but risky for
interviews, class demos, and TestFlight because the first live lookup may fail
slowly.

## Success Criteria

- A learner can understand HBB DNA -> RNA -> protein in under two minutes.
- A learner can compare missense versus nonsense without seeing developer
  errors.
- A teacher can use the app during a short lesson.
- The web demo and iOS app make the educational boundary obvious.
- A reviewer can see App Store readiness: support URL, privacy URL, metadata,
  screenshots plan, no medical claims, and data-source attribution.
- The app is strong enough to show in an interview as a serious biology/software
  project.

## Current Blocking Items Before App Store

- Apple Developer Program enrollment.
- Production FastAPI backend URL over HTTPS.
- Release `GENE_DOGMA_API_BASE_URL` updated in Xcode.
- Live release verification for HBB, BRCA1, and TP53.
- Fresh simulator screenshots from the production API build.
- Final TestFlight pass on a real iPhone.

## Operating Rule

Keep the product narrow and trustworthy. Improve the learner's understanding;
do not recreate Ensembl, overclaim clinical meaning, or bury the user in raw
database fields before the app earns their attention.

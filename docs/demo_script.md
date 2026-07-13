# Demo Script

Use this when showing Gene Central Dogma Explorer in class, in an interview, or
as a portfolio project. The goal is to prove the app in two minutes: a learner
starts with HBB, follows DNA to RNA to protein, compares mutations, and leaves
with a plain-English explanation.

## Two-Minute Walkthrough

1. Open with the built-in HBB example.
   Say: "This starts with a classic gene story instead of a blank search box:
   one DNA change in HBB can alter hemoglobin biology."

2. Point to the gene card and chromosome location.
   Say: "The app begins with the essentials: gene name, location, strand,
   transcript, protein product, and a visual chromosome position."

3. Follow the central dogma path.
   Say: "DNA is copied into RNA, RNA is processed into a transcript, the coding
   sequence is read in codons, and those codons build the protein."

4. Open mutation mode and compare two edits.
   Use the suggested missense and nonsense examples.
   Say: "A missense edit swaps one amino acid. A nonsense edit creates a stop
   signal. The app keeps this as coding-DNA practice, not clinical variant interpretation."

5. Show study mode.
   Say: "This is not just a lookup tool. It includes a two-minute teacher guide,
   quiz prompts, saved genes, a downloadable study pack, and shareable reports."

## What To Show

- First screen: HBB is already loaded and the learner sees guided buttons for
  HBB, BRCA1, TP53, search, and mutation simulation.
- Dogma map: the large path explains transcription, splicing, translation, and
  protein product without overwhelming raw sequence blocks.
- Mutation comparison: show missense versus nonsense side by side.
- Study mode: show the teacher guide and exit ticket.
- Saved genes: show the Markdown study pack export for student review.
- About/support: show the educational disclaimer, Ensembl REST attribution, and
  privacy posture.

## What To Avoid

- Do not frame it as medical advice, diagnosis, treatment guidance, or clinical
  variant interpretation.
- Do not lead with raw DNA/RNA/protein sequence blocks.
- Do not spend the first minute explaining Ensembl fields.
- Do not demo live lookup as the only path; the offline HBB story should work
  even if the network is having a bad day.

## Quick Commands

Run the local product checks before a demo:

```bash
python scripts/verify_v1.py
python scripts/verify_streamlit_ui.py
python scripts/verify_product_readiness.py
```

For iOS screenshots, use the launch flags in `app_store/screenshots.md`, such
as `--gene-demo-tab=mutation --gene-demo-compare`.

# Screenshot Plan

Capture screenshots on a current iPhone simulator after the production API URL
is configured.

## Required Shots

1. Start with HBB
   - Show the first screen with the HBB card and DNA -> RNA -> protein path.
   - Caption: Start with a classic gene story.
   - Launch argument: `--gene-demo-tab=search`
2. Follow the Central Dogma
   - Show Explore with DNA, RNA, coding sequence, and protein steps.
   - Caption: Follow DNA to RNA to protein.
   - Launch argument: `--gene-demo-tab=explore`
3. Compare Mutations
   - Show Mutation with `20 A>T` and `19 G>T` comparison.
   - Caption: Compare mutation effects side by side.
   - Launch arguments: `--gene-demo-tab=mutation --gene-demo-compare`
4. Try Live Gene Lookup
   - Show BRCA1 or TP53 loaded from production backend.
   - Caption: Explore familiar genes with trusted public data.
   - Capture after the production API URL is configured and live lookup is verified.
5. Study and Save
   - Show the teacher guide, quiz/study, or saved genes.
   - Caption: Save genes and turn the story into a lesson.
   - Launch arguments: `--gene-demo-tab=study --gene-demo-saved`

## Simulator Launch Arguments

For repeatable screenshots, edit the Xcode scheme and add launch arguments under
Run > Arguments. These flags only prepare local demo state and do not send data:

- `--gene-demo-tab=search`
- `--gene-demo-tab=explore`
- `--gene-demo-tab=mutation --gene-demo-compare`
- `--gene-demo-tab=study --gene-demo-saved`
- `--gene-demo-tab=saved --gene-demo-saved`
- `--gene-demo-tab=about`

Shortcut for mutation/study/saved demo state:

```text
--gene-demo=screenshots
```

Use one tab argument at a time. The screenshot demo state uses the bundled HBB
example, primes missense/nonsense mutation comparison, and fills the local saved
gene list with HBB, BRCA1, and TP53 for the running simulator session.

## Avoid

- Do not imply medical diagnosis or treatment.
- Do not show patient data.
- Do not show scary raw error traces.
- Do not lead with a blank search form.

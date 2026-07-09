# Gene Central Dogma Explorer Support

Gene Central Dogma Explorer is an educational app for learning how genes connect
to RNA transcripts, coding sequence, proteins, and simple mutation examples.

## Educational Disclaimer

This app is for education only. It is not medical advice, diagnosis, treatment
guidance, or clinical variant interpretation.

## Data Source

Live gene lookup uses the Gene Central Dogma Explorer API, which queries Ensembl
REST for gene, transcript, sequence, and protein information. The app also
includes a bundled HBB example for offline demonstration.

## Mutation Simulator Scope

Mutation mode supports simple coding-DNA practice examples such as `20 A>T`,
`20del`, and `20insA`. It does not parse HGVS notation, convert genomic
coordinates, evaluate splice effects, inspect exon boundaries, query ClinVar, or
classify patient variants.

## Privacy

See `docs/privacy_policy.md` for the privacy policy.

## Contact

For support or privacy questions, use the public GitHub issue tracker:

https://github.com/ekordovi/GeneCentralDogmaExplorer/issues

Before App Store submission, host this page at the support URL listed in App
Store Connect. The hosted page should keep the same educational disclaimer,
data-source note, mutation-scope limits, and privacy link.

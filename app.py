from __future__ import annotations

import json
from pathlib import Path
from textwrap import shorten

import pandas as pd
import streamlit as st

from gene_dogma import EnsemblError, fetch_gene_central_dogma
from gene_dogma.sequence_utils import simulate_dna_mutation, summarize_sequence, to_mrna, translate_dna, wrap_fasta
from gene_dogma.visualization import dogma_visual_html


PROJECT_ROOT = Path(__file__).parent
EXAMPLE_CACHE = PROJECT_ROOT / "data" / "example_gene_cache.json"

SPECIES = {
    "Human": "homo_sapiens",
    "Mouse": "mus_musculus",
    "Rat": "rattus_norvegicus",
    "Zebrafish": "danio_rerio",
    "Fruit fly": "drosophila_melanogaster",
    "C. elegans": "caenorhabditis_elegans",
    "Yeast": "saccharomyces_cerevisiae",
    "Arabidopsis": "arabidopsis_thaliana",
}

FAMOUS_GENES = {
    "HBB": {
        "label": "Hemoglobin beta",
        "why": "A tiny DNA change in HBB is the classic sickle-cell example, which makes it perfect for learning DNA -> protein consequences.",
        "function": "Encodes beta-globin, a core chain of adult hemoglobin that helps red blood cells carry oxygen.",
        "disease": "Hemoglobin disorders including sickle cell disease and beta-thalassemia.",
        "expression": "Highest in erythroid blood-lineage cells that are making hemoglobin.",
    },
    "BRCA1": {
        "label": "DNA repair",
        "why": "BRCA1 shows how a gene can protect genome stability, and why broken repair pathways can raise cancer risk.",
        "function": "Supports DNA damage repair, especially homologous recombination repair of double-strand breaks.",
        "disease": "Hereditary breast and ovarian cancer risk is associated with some pathogenic variants.",
        "expression": "Broadly expressed, with special importance in dividing cells that must repair DNA accurately.",
    },
    "TP53": {
        "label": "Tumor suppressor",
        "why": "TP53 is often called the guardian of the genome because it helps cells respond to DNA damage and stress.",
        "function": "Encodes p53, a transcription factor that can pause the cell cycle, trigger repair, or promote cell death.",
        "disease": "Somatic TP53 variants are common across many cancers; inherited variants can cause Li-Fraumeni syndrome.",
        "expression": "Broadly expressed and activated strongly during cellular stress.",
    },
    "CFTR": {
        "label": "Ion channel",
        "why": "CFTR connects DNA sequence to a membrane protein and a very concrete disease mechanism in cystic fibrosis.",
        "function": "Encodes a chloride/bicarbonate channel important for fluid balance across epithelial surfaces.",
        "disease": "Pathogenic variants can cause cystic fibrosis and related CFTR disorders.",
        "expression": "Important in airway, pancreatic, intestinal, sweat gland, and reproductive epithelial tissues.",
    },
    "INS": {
        "label": "Insulin",
        "why": "INS is an intuitive example because its protein product, insulin, directly controls blood glucose biology.",
        "function": "Encodes preproinsulin, which is processed into insulin in pancreatic beta cells.",
        "disease": "Some variants are linked to monogenic diabetes or insulin-processing disorders.",
        "expression": "Highly specialized expression in pancreatic beta cells.",
    },
    "APOE": {
        "label": "Lipid transport",
        "why": "APOE is a memorable gene because common protein variants affect lipid transport and Alzheimer disease risk.",
        "function": "Encodes apolipoprotein E, which helps transport lipids between cells and tissues.",
        "disease": "APOE alleles are associated with differences in Alzheimer disease and cardiovascular risk.",
        "expression": "Strongly relevant in liver, brain glia, macrophages, and lipid-handling tissues.",
    },
}


st.set_page_config(page_title="Gene Central Dogma Explorer", page_icon="DNA", layout="wide")

st.markdown(
    """
    <style>
      .block-container {
        max-width: 1180px;
        padding-top: 1.25rem;
        padding-bottom: 4rem;
      }
      h1, h2, h3 {
        letter-spacing: 0;
      }
      [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #d8dee9;
        border-radius: 8px;
        padding: 0.75rem;
      }
      [data-testid="stMetric"],
      [data-testid="stMetric"] * {
        color: #111827 !important;
      }
      [data-testid="stMetricValue"] {
        white-space: normal;
        overflow-wrap: anywhere;
        font-size: 1.35rem;
      }
      [data-testid="stMetricLabel"] {
        white-space: normal;
        overflow-wrap: anywhere;
      }
      [data-testid="stCodeBlock"] pre {
        white-space: pre-wrap;
        overflow-wrap: anywhere;
        max-height: 20rem;
      }
      [data-testid="stCodeBlock"] code,
      [data-testid="stCodeBlock"] code span {
        white-space: pre-wrap !important;
        overflow-wrap: anywhere !important;
        word-break: break-word !important;
      }
      div[data-testid="stDataFrame"] {
        width: 100%;
      }
      .beginner-card {
        border: 1px solid #d8dee9;
        border-radius: 8px;
        padding: 1rem;
        background: #ffffff;
        margin: 0.75rem 0 1rem;
      }
      .beginner-card strong {
        color: #111827;
      }
      .quick-facts {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.75rem;
      }
      .quick-fact {
        border: 1px solid #d8dee9;
        border-radius: 8px;
        background: #ffffff;
        padding: 0.75rem;
        min-width: 0;
      }
      .quick-fact-label {
        color: #4b5563;
        font-size: 0.8rem;
        margin-bottom: 0.25rem;
      }
      .quick-fact-value {
        color: #111827;
        font-weight: 750;
        overflow-wrap: anywhere;
      }
      .web-hero {
        border: 1px solid #d8dee9;
        border-radius: 8px;
        background: #ffffff;
        padding: 1.1rem;
        margin: 0.75rem 0 1rem;
      }
      .web-hero-kicker {
        color: #3a86ff;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
      }
      .web-hero-title {
        color: #111827;
        font-size: 2.35rem;
        font-weight: 850;
        line-height: 1.02;
        overflow-wrap: anywhere;
      }
      .web-hero-copy {
        color: #374151;
        font-size: 1rem;
        line-height: 1.45;
        margin-top: 0.65rem;
      }
      .pill-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
        margin-top: 0.8rem;
      }
      .pill {
        border: 1px solid #d8dee9;
        border-radius: 999px;
        color: #111827;
        background: #f9fafb;
        padding: 0.3rem 0.65rem;
        font-size: 0.82rem;
        font-weight: 700;
      }
      .story-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.75rem;
        margin: 0.85rem 0;
      }
      .story-card {
        border: 1px solid #d8dee9;
        border-radius: 8px;
        background: #ffffff;
        padding: 0.85rem;
        min-width: 0;
      }
      .story-card-title {
        color: #111827;
        font-weight: 800;
        margin-bottom: 0.35rem;
      }
      .story-card-body {
        color: #4b5563;
        font-size: 0.92rem;
        line-height: 1.4;
      }
      .sequence-strip {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.6rem;
        margin: 0.85rem 0;
      }
      .sequence-chip {
        border: 1px solid #d8dee9;
        border-radius: 8px;
        background: #ffffff;
        padding: 0.75rem;
      }
      .sequence-chip-label {
        color: #4b5563;
        font-size: 0.78rem;
        margin-bottom: 0.25rem;
      }
      .sequence-chip-value {
        color: #111827;
        font-weight: 800;
      }
      .disclaimer-band {
        border-left: 4px solid #3a86ff;
        background: #f7fafc;
        color: #374151;
        padding: 0.8rem 0.9rem;
        border-radius: 8px;
        margin: 0.85rem 0;
      }
      .sequence-summary-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.65rem;
        margin: 0.75rem 0;
      }
      .sequence-summary-card {
        border: 1px solid #d8dee9;
        border-radius: 8px;
        background: #ffffff;
        padding: 0.75rem;
        min-width: 0;
      }
      .sequence-summary-label {
        color: #4b5563;
        font-size: 0.78rem;
        margin-bottom: 0.25rem;
      }
      .sequence-summary-value {
        color: #111827;
        font-size: 1.15rem;
        font-weight: 850;
        overflow-wrap: anywhere;
      }
      .readable-sequence {
        border: 1px solid #d8dee9;
        border-radius: 8px;
        background: #ffffff;
        color: #111827;
        padding: 0.9rem;
        margin: 0.7rem 0 0.9rem;
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: 0.86rem;
        line-height: 1.55;
        white-space: pre-wrap;
        overflow-wrap: anywhere;
        word-break: break-word;
      }
      .stage-note {
        border-left: 4px solid #1f9d8a;
        background: #ffffff;
        border-radius: 8px;
        color: #374151;
        padding: 0.75rem 0.9rem;
        margin: 0.7rem 0;
      }
      .stTabs [data-baseweb="tab-list"] {
        gap: 0.25rem;
      }
      .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.5rem 0.75rem;
      }
      @media (max-width: 760px) {
        .block-container {
          padding-left: 0.75rem;
          padding-right: 0.75rem;
          padding-top: 0.75rem;
        }
        [data-testid="stSidebar"] {
          min-width: 17rem;
        }
        h1 {
          font-size: 1.75rem;
          line-height: 1.15;
        }
        h2 {
          font-size: 1.35rem;
        }
        h3 {
          font-size: 1.1rem;
        }
        .quick-facts {
          grid-template-columns: 1fr 1fr;
          gap: 0.5rem;
        }
        .web-hero {
          padding: 0.9rem;
        }
        .web-hero-title {
          font-size: 1.85rem;
        }
        .story-grid,
        .sequence-strip,
        .sequence-summary-grid {
          grid-template-columns: 1fr;
        }
        .beginner-card {
          padding: 0.85rem;
        }
        [data-testid="stMetric"] {
          padding: 0.65rem;
        }
        [data-testid="stMetricValue"] {
          font-size: 1.05rem;
        }
        div[data-testid="stButton"] > button,
        div[data-testid="stDownloadButton"] > button,
        div[data-testid="stLinkButton"] > a {
          width: 100%;
        }
      }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_example() -> dict:
    return json.loads(EXAMPLE_CACHE.read_text())


@st.cache_data(show_spinner=True)
def cached_lookup(symbol: str, species: str, transcript_id: str | None = None) -> dict:
    return fetch_gene_central_dogma(symbol=symbol, species=species, preferred_transcript_id=transcript_id)


def short_sequence(sequence: str, flank: int = 240) -> str:
    if len(sequence) <= flank * 2:
        return sequence
    return f"{sequence[:flank]}\n...\n{sequence[-flank:]}"


def strand_label(strand: int | str | None) -> str:
    if strand == 1 or strand == "1":
        return "+ sense"
    if strand == -1 or strand == "-1":
        return "- antisense"
    return "Unknown"


def gene_locus(gene: dict) -> str:
    region = gene.get("seq_region_name") or "?"
    start = gene.get("start")
    end = gene.get("end")
    if start and end:
        return f"chr{region}:{start:,}-{end:,}"
    return f"chr{region}"


def known_aliases(gene: dict) -> str:
    aliases = gene.get("aliases") or gene.get("synonyms") or gene.get("xrefs") or []
    if isinstance(aliases, str):
        aliases = [aliases]
    aliases = [str(alias) for alias in aliases if alias]
    return ", ".join(aliases[:8]) if aliases else "No aliases returned"


def famous_gene_note(gene: dict, field: str) -> str | None:
    symbol = (gene.get("display_name") or "").upper()
    note = FAMOUS_GENES.get(symbol)
    return note.get(field) if note else None


def known_function(gene: dict) -> str:
    curated = famous_gene_note(gene, "function")
    if curated:
        return curated
    description = (gene.get("description") or "").strip()
    if description:
        return shorten(description, width=260, placeholder="...")
    return "No plain-English function is available yet for this gene."


def why_gene_matters(gene: dict) -> str:
    name = gene.get("display_name") or "This gene"
    description = (gene.get("description") or "").strip()
    biotype = gene.get("biotype") or "gene"
    curated = famous_gene_note(gene, "why")
    if curated:
        return curated
    if name.upper() == "HBB":
        return (
            "HBB encodes beta-globin, one of the core protein chains in adult hemoglobin. "
            "Small DNA changes in this gene can alter oxygen transport and cause classic hemoglobin disorders."
        )
    if "hemoglobin" in description.lower():
        return f"{name} is tied to hemoglobin biology, so its sequence connects directly to oxygen transport."
    if biotype == "protein_coding":
        return f"{name} matters because its coding DNA can be translated into a protein that may affect cell behavior."
    return f"{name} is a {biotype}; its biological role may come from RNA function, regulation, or transcript processing."


def beginner_summary(data: dict) -> list[str]:
    gene = data["gene"]
    sequences = data["sequences"]
    selected = data.get("selected_transcript") or {}
    protein = sequences.get("protein", "")
    transcript = sequences.get("transcript_cdna", "")
    coding = sequences.get("coding_dna", "")
    name = gene.get("display_name") or "This gene"
    points = [
        f"{name} is found at {gene_locus(gene)} on the {strand_label(gene.get('strand'))} strand.",
        f"The selected transcript is {selected.get('display_name') or selected.get('id') or 'not available'}, which is the RNA version this app is following.",
    ]
    if coding and protein:
        points.append(f"Its coding sequence is {len(coding):,} DNA letters long and translates into a protein with {len(protein):,} amino acids.")
    elif transcript:
        points.append(f"Its transcript is {len(transcript):,} letters long, but this lookup did not return a translated protein.")
    else:
        points.append("This lookup did not return enough sequence data for a full DNA to RNA to protein walk-through.")
    points.append(why_gene_matters(gene))
    return points


def beginner_glossary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"term": "Gene", "plain_english": "A stretch of DNA that carries biological instructions."},
            {"term": "Transcript", "plain_english": "An RNA copy of a gene. One gene can make multiple transcript versions."},
            {"term": "Exon", "plain_english": "A transcript segment that remains after RNA splicing."},
            {"term": "Intron", "plain_english": "A segment removed when the cell processes RNA."},
            {"term": "CDS", "plain_english": "The coding sequence read three letters at a time to build a protein."},
            {"term": "Codon", "plain_english": "A three-letter DNA or RNA word that maps to an amino acid."},
            {"term": "Protein", "plain_english": "A chain of amino acids that can do work in the cell."},
        ]
    )


def render_beginner_intro(data: dict) -> None:
    gene = data["gene"]
    st.markdown(
        f"""
        <div class="beginner-card">
          <strong>Plain-English takeaway:</strong> {escape_html(why_gene_matters(gene))}
        </div>
        """,
        unsafe_allow_html=True,
    )
    for point in beginner_summary(data):
        st.write(f"- {point}")


def render_quick_facts(gene: dict) -> None:
    facts = [
        ("Gene", gene.get("display_name", "NA")),
        ("Species", gene.get("species") or "See lookup"),
        ("Aliases", known_aliases(gene)),
        ("Type", gene.get("biotype") or "NA"),
        ("Location", gene_locus(gene)),
        ("Strand", strand_label(gene.get("strand"))),
    ]
    html = ['<div class="quick-facts">']
    for label, value in facts:
        html.append(
            (
                '<div class="quick-fact">'
                f'<div class="quick-fact-label">{escape_html(label)}</div>'
                f'<div class="quick-fact-value">{escape_html(str(value))}</div>'
                "</div>"
            )
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def escape_html(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def wrap_for_display(sequence: str, line_width: int = 72, max_symbols: int = 720) -> str:
    cleaned = "".join(char for char in str(sequence or "").upper() if char.isalpha() or char == "*")
    if not cleaned:
        return "No sequence returned."
    shown = cleaned[:max_symbols]
    lines = [shown[index : index + line_width] for index in range(0, len(shown), line_width)]
    if len(cleaned) > max_symbols:
        lines.append(f"... {len(cleaned) - max_symbols:,} more symbols")
    return "\n".join(lines)


def sequence_summary_cards(summary: dict) -> str:
    values = [
        ("Length", f"{summary['length']:,}"),
        ("GC %", "NA" if summary["gc_percent"] is None else str(summary["gc_percent"])),
        ("Starts", summary["starts_with"][:12] or "NA"),
        ("Ends", summary["ends_with"][-12:] or "NA"),
    ]
    html = ['<div class="sequence-summary-grid">']
    for label, value in values:
        html.append(
            (
                '<div class="sequence-summary-card">'
                f'<div class="sequence-summary-label">{escape_html(label)}</div>'
                f'<div class="sequence-summary-value">{escape_html(value)}</div>'
                "</div>"
            )
        )
    html.append("</div>")
    return "".join(html)


def transcript_rows(transcripts: list[dict], selected_id: str | None = None) -> list[dict]:
    rows = []
    for tx in transcripts:
        translation = tx.get("Translation") or {}
        protein_length = int(translation.get("length") or 0)
        exon_count = len(tx.get("Exon") or tx.get("exons") or [])
        rows.append(
            {
                "transcript_id": tx.get("id", ""),
                "name": tx.get("display_name", ""),
                "biotype": tx.get("biotype", ""),
                "canonical": "Yes" if tx.get("is_canonical") else "No",
                "selected": "Yes" if selected_id and tx.get("id") == selected_id else "No",
                "exon_count": exon_count or None,
                "transcript_length": int(tx.get("length") or 0),
                "cds_length_estimate": protein_length * 3 if protein_length else None,
                "protein_id": translation.get("id", ""),
                "protein_length": protein_length or None,
            }
        )
    return rows


def sequence_panel(label: str, sequence: str, alphabet: str, fasta_header: str, key_prefix: str) -> None:
    summary = summarize_sequence(sequence, alphabet)
    st.markdown(sequence_summary_cards(summary), unsafe_allow_html=True)
    st.markdown(
        f'<div class="readable-sequence">{escape_html(wrap_for_display(sequence))}</div>',
        unsafe_allow_html=True,
    )
    with st.expander(f"Show more {label} text"):
        st.text_area(
            f"{label} sequence",
            value=wrap_for_display(sequence, line_width=80, max_symbols=4000),
            height=260,
            key=f"{key_prefix}-sequence-text",
        )
    st.download_button(
        f"Download {label} FASTA",
        data=wrap_fasta(fasta_header, sequence),
        file_name=f"{fasta_header.replace('|', '_')}.fasta",
        mime="text/plain",
        key=f"{key_prefix}-download-fasta",
    )


def transcript_table(transcripts: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(transcript_rows(transcripts))


def save_gene_record(data: dict) -> None:
    gene = data["gene"]
    record = {
        "symbol": gene.get("display_name", ""),
        "species": data.get("query", {}).get("species", "homo_sapiens"),
        "type": gene.get("biotype", ""),
        "location": gene_locus(gene),
        "why": why_gene_matters(gene),
    }
    existing = st.session_state.setdefault("saved_genes", [])
    existing[:] = [item for item in existing if item.get("symbol") != record["symbol"] or item.get("species") != record["species"]]
    existing.insert(0, record)


def saved_genes_table() -> pd.DataFrame:
    return pd.DataFrame(st.session_state.get("saved_genes", []))


def central_dogma_map(data: dict) -> None:
    gene = data["gene"]
    sequences = data["sequences"]
    selected = data.get("selected_transcript") or {}
    stages = [
        (
            "Genomic DNA",
            "DNA at the gene locus, before transcript processing.",
            sequences.get("genomic_dna", ""),
            "dna",
            f"{gene['display_name']}|genomic_dna",
        ),
        (
            "Exons / Introns",
            "Ensembl transcript models define exons. Introns are the genomic intervals removed during splicing.",
            sequences.get("genomic_dna", ""),
            "dna",
            f"{gene['display_name']}|exon_intron_context",
        ),
        (
            "Spliced mRNA",
            "The transcript cDNA converted to RNA letters, representing the mature spliced transcript.",
            to_mrna(sequences.get("transcript_cdna", "")),
            "rna",
            f"{gene['display_name']}|spliced_mrna",
        ),
        (
            "Coding Sequence",
            "The CDS is the part of the transcript read in codons to build the protein.",
            sequences.get("coding_dna", ""),
            "dna",
            f"{gene['display_name']}|coding_sequence",
        ),
        (
            "Amino Acid Chain",
            "The amino acid sequence produced by translating the coding sequence.",
            sequences.get("protein", ""),
            "protein",
            f"{gene['display_name']}|protein",
        ),
    ]
    labels = [stage[0] for stage in stages]
    selected_stage = st.segmented_control("Central dogma stage", labels, default=labels[0])
    stage = stages[labels.index(selected_stage or labels[0])]
    st.markdown(f'<div class="stage-note">{escape_html(stage[1])}</div>', unsafe_allow_html=True)
    if stage[0] == "Exons / Introns":
        exons = selected.get("Exon") or selected.get("exons") or []
        if exons:
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "exon_id": exon.get("id", ""),
                            "start": exon.get("start", ""),
                            "end": exon.get("end", ""),
                            "strand": strand_label(exon.get("strand")),
                        }
                        for exon in exons
                    ]
                ),
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("Exon coordinates were not included in this lookup response. The genomic sequence is shown as context.")
    sequence_panel(stage[0], stage[2], stage[3], stage[4], f"dogma-map-{selected_stage}")


def mutation_simulator(sequences: dict) -> None:
    coding_dna = sequences.get("coding_dna", "")
    default_change = "20 A>T" if len(coding_dna) >= 20 else ""
    change = st.text_input("DNA change", value=default_change, placeholder="20 A>T, 20del, or 20insA")
    if st.button("Simulate Mutation"):
        try:
            result = simulate_dna_mutation(coding_dna, change)
        except ValueError as exc:
            st.error(str(exc))
            return

        cols = st.columns(5)
        cols[0].metric("Original codon", result["original_codon"] or "NA")
        cols[1].metric("Mutated codon", result["mutated_codon"] or "NA")
        cols[2].metric("Original AA", result["original_amino_acid"] or "NA")
        cols[3].metric("Changed AA", result["mutated_amino_acid"] or "NA")
        cols[4].metric("Effect", result["effect"])
        st.code(short_sequence(result["mutated_dna"]), language="text")


def protein_features(sequences: dict, translation: dict) -> pd.DataFrame:
    protein = sequences.get("protein", "")
    rows = []
    if protein:
        rows.append({"feature": "Protein product", "range": f"1-{len(protein)}", "note": "Returned protein sequence"})
    if protein.startswith("M"):
        rows.append({"feature": "Start methionine", "range": "1", "note": "First translated residue"})
    hydrophobic_run = longest_hydrophobic_run(protein)
    if hydrophobic_run:
        start, end, run = hydrophobic_run
        rows.append({"feature": "Hydrophobic stretch", "range": f"{start}-{end}", "note": run})
    if translation.get("id"):
        rows.append({"feature": "Stable protein ID", "range": translation["id"], "note": "Useful for UniProt/AlphaFold lookup"})
    return pd.DataFrame(rows)


def longest_hydrophobic_run(protein: str) -> tuple[int, int, str] | None:
    hydrophobic = set("AILMFWVY")
    best_start = 0
    best = ""
    current_start = 0
    current = ""
    for index, residue in enumerate(protein, start=1):
        if residue in hydrophobic:
            if not current:
                current_start = index
            current += residue
        else:
            if len(current) > len(best):
                best_start = current_start
                best = current
            current = ""
    if len(current) > len(best):
        best_start = current_start
        best = current
    if len(best) >= 8:
        return best_start, best_start + len(best) - 1, best
    return None


def hbb_variant_examples(gene: dict) -> pd.DataFrame:
    symbol = (gene.get("display_name") or "").upper()
    if symbol != "HBB":
        curated = famous_gene_note(gene, "disease")
        if curated:
            return pd.DataFrame(
                [
                    {
                        "variant": "Known variant examples",
                        "coding_change": "Use ClinVar layer next",
                        "protein_effect": "Transcript-specific lookup pending",
                        "clinical_note": curated,
                    }
                ]
            )
        return pd.DataFrame()
    return pd.DataFrame(
        [
            {
                "variant": "HbS",
                "coding_change": "20 A>T",
                "protein_effect": "Glu7Val in the Ensembl protein sequence",
                "clinical_note": "Classic sickle hemoglobin example",
            },
            {
                "variant": "HbC",
                "coding_change": "19 G>A",
                "protein_effect": "Glu7Lys in the Ensembl protein sequence",
                "clinical_note": "Hemoglobin C example",
            },
            {
                "variant": "Early stop example",
                "coding_change": "16 G>T",
                "protein_effect": "Glu6Ter in the Ensembl protein sequence",
                "clinical_note": "Teaching example for nonsense effects",
            },
        ]
    )


def expression_hint(gene: dict) -> str:
    curated = famous_gene_note(gene, "expression")
    if curated:
        return curated
    return "Expression atlas data is not connected yet. Add a tissue-expression API here to show high and low tissues."


def conservation_score(protein_a: str, protein_b: str) -> float | None:
    if not protein_a or not protein_b:
        return None
    compared = min(len(protein_a), len(protein_b))
    if compared == 0:
        return None
    matches = sum(left == right for left, right in zip(protein_a[:compared], protein_b[:compared]))
    return round(matches / compared * 100, 2)


def markdown_report(data: dict) -> str:
    gene = data["gene"]
    sequences = data["sequences"]
    selected = data.get("selected_transcript") or {}
    translation = data.get("selected_translation") or {}
    lines = [
        f"# {gene.get('display_name', 'Gene')} central dogma report",
        "",
        "## Beginner explanation",
        why_gene_matters(gene),
        "",
        "In plain English: DNA is the stored instruction, RNA is the working copy, and protein is the molecule that often does the job in the cell.",
        "",
        "## Advanced summary",
        (
            f"{gene.get('display_name', 'This gene')} is a {gene.get('biotype', 'gene')} on "
            f"{gene_locus(gene)} on the {strand_label(gene.get('strand'))} strand. "
            f"The selected transcript is {selected.get('id', 'NA')} and the selected protein product is "
            f"{translation.get('id', 'NA')}."
        ),
        "",
        "## Central dogma summary",
        f"- Genomic DNA length: {len(sequences.get('genomic_dna', '')):,} bp",
        f"- Transcript cDNA length: {len(sequences.get('transcript_cdna', '')):,} bases",
        f"- Coding DNA length: {len(sequences.get('coding_dna', '')):,} bases",
        f"- Protein length: {len(sequences.get('protein', '')):,} amino acids",
        "",
        "## Known biology",
        known_function(gene),
        "",
        "## Disease relevance",
        famous_gene_note(gene, "disease")
        or "ClinVar-style variant lookup is not connected yet; use the mutation simulator for local sequence consequences.",
        "",
        "## Key sequences",
        "```text",
        f"CDS: {short_sequence(sequences.get('coding_dna', ''), flank=120)}",
        f"Protein: {short_sequence(sequences.get('protein', ''), flank=120)}",
        "```",
    ]
    return "\n".join(lines)


def pdf_report_bytes(report: str, title: str) -> bytes | None:
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except ImportError:
        return None

    from io import BytesIO

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title=title)
    styles = getSampleStyleSheet()
    story = []
    for line in report.splitlines():
        if not line.strip():
            story.append(Spacer(1, 8))
        elif line.startswith("# "):
            story.append(Paragraph(escape_html(line[2:]), styles["Title"]))
        elif line.startswith("## "):
            story.append(Paragraph(escape_html(line[3:]), styles["Heading2"]))
        else:
            story.append(Paragraph(escape_html(line), styles["BodyText"]))
    doc.build(story)
    return buffer.getvalue()


def study_questions(data: dict) -> list[dict]:
    gene = data["gene"]
    sequences = data["sequences"]
    selected = data.get("selected_transcript") or {}
    protein_len = len(sequences.get("protein", ""))
    coding_len = len(sequences.get("coding_dna", ""))
    questions = [
        {
            "question": f"What is the selected transcript for {gene.get('display_name', 'this gene')}?",
            "choices": [
                selected.get("display_name") or selected.get("id") or "No transcript returned",
                gene.get("id", "Gene ID"),
                gene.get("seq_region_name", "Chromosome"),
            ],
            "answer": selected.get("display_name") or selected.get("id") or "No transcript returned",
            "explanation": "A transcript is the RNA version of a gene that the app follows through the central dogma.",
        },
        {
            "question": "Which molecule is read three letters at a time to build a protein?",
            "choices": ["Coding DNA / mRNA", "Genomic coordinates", "Chromosome name"],
            "answer": "Coding DNA / mRNA",
            "explanation": "Three-letter codons in the coding sequence map to amino acids.",
        },
        {
            "question": f"How long is the selected protein sequence for {gene.get('display_name', 'this gene')}?",
            "choices": [f"{protein_len:,} amino acids", f"{coding_len:,} chromosomes", f"{len(data.get('transcripts') or []):,} species"],
            "answer": f"{protein_len:,} amino acids",
            "explanation": "Protein length is counted in amino-acid letters, not DNA bases.",
        },
        {
            "question": "What does a nonsense mutation usually create?",
            "choices": ["A premature stop signal", "A longer chromosome", "A new species"],
            "answer": "A premature stop signal",
            "explanation": "A nonsense change turns an amino-acid codon into a stop codon.",
        },
    ]
    return questions


def render_web_hero(data: dict) -> None:
    gene = data["gene"]
    sequences = data["sequences"]
    chips = [
        gene.get("biotype") or "gene",
        gene_locus(gene),
        f"{len(sequences.get('coding_dna', '')):,} coding bases",
        f"{len(sequences.get('protein', '')):,} amino acids",
    ]
    chip_html = "".join(f'<span class="pill">{escape_html(chip)}</span>' for chip in chips if chip)
    st.markdown(
        f"""
        <div class="web-hero">
          <div class="web-hero-kicker">Central dogma explorer</div>
          <div class="web-hero-title">{escape_html(gene.get("display_name", "Gene"))}</div>
          <div class="web-hero-copy">{escape_html(why_gene_matters(gene))}</div>
          <div class="pill-row">{chip_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_story_cards(data: dict) -> None:
    gene = data["gene"]
    sequences = data["sequences"]
    cards = [
        ("DNA", f"{gene.get('display_name', 'This gene')} sits at {gene_locus(gene)}."),
        ("RNA", f"The selected transcript is {(data.get('selected_transcript') or {}).get('display_name') or (data.get('selected_transcript') or {}).get('id') or 'not available'}."),
        ("Protein", f"The returned protein sequence has {len(sequences.get('protein', '')):,} amino acids."),
    ]
    html = ['<div class="story-grid">']
    for title, body in cards:
        html.append(
            (
                '<div class="story-card">'
                f'<div class="story-card-title">{escape_html(title)}</div>'
                f'<div class="story-card-body">{escape_html(body)}</div>'
                "</div>"
            )
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def render_sequence_strip(sequences: dict) -> None:
    items = [
        ("Genomic DNA", f"{len(sequences.get('genomic_dna', '')):,} bp"),
        ("Transcript", f"{len(sequences.get('transcript_cdna', '')):,} bases"),
        ("Coding DNA", f"{len(sequences.get('coding_dna', '')):,} bases"),
        ("Protein", f"{len(sequences.get('protein', '')):,} aa"),
    ]
    html = ['<div class="sequence-strip">']
    for label, value in items:
        html.append(
            (
                '<div class="sequence-chip">'
                f'<div class="sequence-chip-label">{escape_html(label)}</div>'
                f'<div class="sequence-chip-value">{escape_html(value)}</div>'
                "</div>"
            )
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def render_saved_genes_section() -> None:
    saved_df = saved_genes_table()
    if saved_df.empty:
        st.info("No saved genes yet. Save a gene from Overview to build a study list for this session.")
        return
    st.dataframe(saved_df, width="stretch", hide_index=True)
    st.download_button(
        "Download Saved Gene List",
        data=saved_df.to_json(orient="records", indent=2),
        file_name="saved_gene_study_list.json",
        mime="application/json",
    )


def render_isoform_section(transcripts: list[dict], selected: dict, symbol: str, species: str, gene: dict) -> None:
    tx_df = pd.DataFrame(transcript_rows(transcripts, selected.get("id")))
    if tx_df.empty:
        st.warning("No transcript records returned.")
        return
    selected_rows = tx_df[tx_df["selected"] == "Yes"]
    if not selected_rows.empty:
        st.dataframe(selected_rows, width="stretch", hide_index=True)
    with st.expander("All transcript isoforms"):
        st.dataframe(tx_df, width="stretch", hide_index=True)
        protein_tx = tx_df[tx_df["protein_id"].astype(str) != ""]
        if not protein_tx.empty:
            tx_options = protein_tx["transcript_id"].tolist()
            selected_tx_id = st.selectbox(
                "Reload a protein-coding transcript",
                tx_options,
                index=tx_options.index(selected.get("id")) if selected.get("id") in tx_options else 0,
            )
            if st.button("Reload Selected Transcript"):
                try:
                    st.session_state["dogma_data"] = cached_lookup(symbol or gene["display_name"], species, selected_tx_id)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Transcript reload failed: {exc}")


def render_study_section(data: dict) -> None:
    questions = study_questions(data)
    question_labels = [item["question"] for item in questions]
    chosen_question = st.selectbox("Question", question_labels)
    question = questions[question_labels.index(chosen_question)]
    answer = st.radio("Choose an answer", question["choices"], key=f"quiz-{data['gene'].get('display_name')}-{chosen_question}")
    if st.button("Check Answer"):
        if answer == question["answer"]:
            st.success("Correct.")
        else:
            st.error(f"Not quite. Correct answer: {question['answer']}")
        st.write(question["explanation"])


st.title("Gene Central Dogma Explorer")
st.caption("Start with a gene, then follow its DNA -> RNA -> protein story in plain English.")

if "dogma_data" not in st.session_state:
    st.session_state["dogma_data"] = load_example()
if "loaded_example_default" not in st.session_state:
    st.session_state["loaded_example_default"] = True
if "saved_genes" not in st.session_state:
    st.session_state["saved_genes"] = []

with st.sidebar:
    st.header("Lookup")
    species_label = st.selectbox("Species", list(SPECIES), index=0)
    custom_species = st.text_input("Custom Ensembl species alias", value="", help="Optional. Example: homo_sapiens.")
    species = custom_species.strip() or SPECIES[species_label]
    symbol = st.text_input("Gene symbol", value="HBB", help="Try HBB, BRCA1, TP53, CFTR, INS, or APOE.").strip()
    run_example = st.button("Load Built-in HBB Demo")
    run_lookup = st.button("Look Up Gene", type="primary")
    st.divider()
    st.subheader("Famous examples")
    famous_symbol = st.selectbox(
        "Quick load",
        list(FAMOUS_GENES),
        format_func=lambda key: f"{key} - {FAMOUS_GENES[key]['label']}",
    )
    run_famous = st.button("Load Famous Gene")
    st.divider()
    saved_count = len(st.session_state.get("saved_genes", []))
    st.write(f"Saved genes this session: {saved_count}")
    st.write("Live searches use Ensembl. The built-in HBB demo works offline.")

data = None
if run_example:
    st.session_state["dogma_data"] = load_example()
    st.session_state["loaded_example_default"] = True
elif run_famous:
    try:
        if famous_symbol == "HBB":
            st.session_state["dogma_data"] = load_example()
        else:
            st.session_state["dogma_data"] = cached_lookup(famous_symbol, "homo_sapiens")
        st.session_state["loaded_example_default"] = False
        st.success(f"Loaded {famous_symbol}.")
    except EnsemblError as exc:
        st.error(str(exc))
    except Exception as exc:
        st.error(f"Example lookup failed: {exc}")
elif run_lookup and symbol:
    try:
        st.session_state["dogma_data"] = cached_lookup(symbol, species)
        st.session_state["loaded_example_default"] = False
    except EnsemblError as exc:
        st.error(str(exc))
    except Exception as exc:
        st.error(f"Lookup failed: {exc}")

data = st.session_state["dogma_data"]
if data is None:
    st.info("Enter a gene symbol and click **Look Up Gene**, or use the bundled HBB example.")

if data:
    gene = data["gene"]
    sequences = data["sequences"]
    selected = data.get("selected_transcript") or {}
    translation = data.get("selected_translation") or {}
    transcripts = data.get("transcripts") or []

    if st.session_state.get("loaded_example_default"):
        st.info("Showing the bundled HBB demo. Search or load a famous example to switch genes.")

    render_web_hero(data)
    render_quick_facts(gene)
    st.markdown(dogma_visual_html(data), unsafe_allow_html=True)
    render_sequence_strip(sequences)

    action_cols = st.columns([1, 1, 2])
    with action_cols[0]:
        if st.button("Save Gene"):
            save_gene_record(data)
            st.success(f"Saved {gene.get('display_name', 'this gene')}.")
    with action_cols[1]:
        st.download_button(
            "Download Report",
            data=markdown_report(data),
            file_name=f"{gene.get('display_name', 'gene')}_central_dogma_report.md",
            mime="text/markdown",
        )
    with action_cols[2]:
        st.markdown(
            '<div class="disclaimer-band">Educational use only. This is not medical advice, diagnosis, treatment guidance, or clinical variant interpretation.</div>',
            unsafe_allow_html=True,
        )

    overview_tab, dogma_tab, mutation_tab, study_tab, advanced_tab = st.tabs(
        ["Overview", "Dogma", "Mutation", "Study", "Advanced"]
    )

    with overview_tab:
        st.subheader("Gene story")
        render_story_cards(data)
        st.write(known_function(gene))
        st.write(why_gene_matters(gene))
        with st.expander("Plain-English notes"):
            for point in beginner_summary(data):
                st.write(f"- {point}")
            st.dataframe(beginner_glossary(), width="stretch", hide_index=True)

        st.subheader("Gene identity")
        st.write(f"**Gene name:** {gene.get('display_name', 'NA')}")
        st.write(f"**Aliases:** {known_aliases(gene)}")
        st.write(f"**Species:** {data.get('query', {}).get('species', 'NA')}")
        st.write(f"**Chromosome location:** {gene_locus(gene)}")
        st.write(f"**Strand:** {strand_label(gene.get('strand'))}")
        st.write(f"**Gene type:** {gene.get('biotype') or 'NA'}")

    with dogma_tab:
        st.subheader("Central dogma map")
        central_dogma_map(data)

        st.subheader("Selected transcript")
        selected_cols = st.columns(2)
        selected_cols[0].write(f"`{selected.get('id', 'NA')}`")
        selected_cols[1].write(f"`{translation.get('id', 'No protein translation returned')}`")
        render_isoform_section(transcripts, selected, symbol, species, gene)

    with mutation_tab:
        st.subheader("Mutation simulator")
        st.write("Type a simple coding-DNA edit and see how the codon and amino acid change.")
        if sequences.get("coding_dna"):
            mutation_simulator(sequences)
        else:
            st.warning("No coding DNA returned, so local codon mutation simulation is unavailable.")
        st.caption("This is a simple coding-DNA teaching tool. It does not parse HGVS, map genomic coordinates, or classify clinical variants.")

    with study_tab:
        st.subheader("Study mode")
        render_study_section(data)
        st.subheader("Saved genes")
        render_saved_genes_section()

        report = markdown_report(data)
        with st.expander("Story report"):
            st.markdown(report)
            pdf_bytes = pdf_report_bytes(report, f"{gene.get('display_name', 'Gene')} central dogma report")
            if pdf_bytes:
                st.download_button(
                    "Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"{gene.get('display_name', 'gene')}_central_dogma_report.pdf",
                    mime="application/pdf",
                )

    with advanced_tab:
        st.subheader("Sequences")
        sequence_view = st.segmented_control("Sequence type", ["DNA", "RNA", "Protein", "Compare"], default="DNA")
        if sequence_view == "DNA":
            sequence_panel("genomic DNA", sequences["genomic_dna"], "dna", f"{gene['display_name']}|genomic_dna", "sequences-genomic-dna")
            if sequences["coding_dna"]:
                sequence_panel("coding DNA", sequences["coding_dna"], "dna", f"{gene['display_name']}|coding_dna", "sequences-coding-dna")
        elif sequence_view == "RNA":
            st.write("The pre-mRNA view is a teaching proxy: genomic DNA with T changed to U.")
            sequence_panel("pre-mRNA proxy", sequences["pre_mrna_proxy"], "rna", f"{gene['display_name']}|pre_mrna_proxy", "sequences-pre-mrna")
            if sequences["transcript_cdna"]:
                sequence_panel("transcript mRNA", to_mrna(sequences["transcript_cdna"]), "rna", f"{gene['display_name']}|transcript_mrna", "sequences-transcript-mrna")
            if sequences["coding_mrna"]:
                sequence_panel("coding mRNA", sequences["coding_mrna"], "rna", f"{gene['display_name']}|coding_mrna", "sequences-coding-mrna")
        elif sequence_view == "Protein":
            if sequences["protein"]:
                sequence_panel("protein", sequences["protein"], "protein", f"{gene['display_name']}|protein", "sequences-protein")
                translated = translate_dna(sequences["coding_dna"]).rstrip("*") if sequences["coding_dna"] else ""
                if translated:
                    match = "matches" if translated == sequences["protein"] else "differs from"
                    st.write(f"Local codon-table translation of coding DNA {match} the returned Ensembl protein.")
            else:
                st.warning("No protein sequence returned. This can happen for non-coding genes or non-translated transcripts.")
        else:
            compare = pd.DataFrame(
                [
                    {"molecule": "Genomic DNA", **summarize_sequence(sequences["genomic_dna"], "dna")},
                    {"molecule": "Transcript cDNA", **summarize_sequence(sequences["transcript_cdna"], "dna")},
                    {"molecule": "Coding DNA", **summarize_sequence(sequences["coding_dna"], "dna")},
                    {"molecule": "Protein", **summarize_sequence(sequences["protein"], "protein")},
                ]
            )
            st.dataframe(compare.drop(columns=["composition"]), width="stretch", hide_index=True)

        st.subheader("Protein and structure")
        if sequences.get("protein"):
            st.dataframe(protein_features(sequences, translation), width="stretch", hide_index=True)
        protein_id = translation.get("id", "")
        if protein_id:
            link_cols = st.columns(2)
            link_cols[0].link_button("Open AlphaFold entry", f"https://alphafold.ebi.ac.uk/entry/{protein_id}")
            link_cols[1].link_button("Search PDB", f"https://www.rcsb.org/search?request=%7B%22query%22:%7B%22type%22:%22terminal%22,%22service%22:%22full_text%22,%22parameters%22:%7B%22value%22:%22{protein_id}%22%7D%7D,%22return_type%22:%22entry%22%7D")

        st.subheader("Teaching context")
        variant_df = hbb_variant_examples(gene)
        if not variant_df.empty:
            st.dataframe(variant_df, width="stretch", hide_index=True)
        st.write(expression_hint(gene))
        with st.expander("Raw JSON response"):
            st.json(data)

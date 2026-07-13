from __future__ import annotations

import json
from pathlib import Path
from textwrap import shorten

import pandas as pd
import streamlit as st

from gene_dogma import EnsemblError, fetch_gene_central_dogma
from gene_dogma.sequence_utils import clean_sequence, simulate_dna_mutation, summarize_sequence, to_mrna, translate_dna, wrap_fasta
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

HUMAN_CHROMOSOME_LENGTHS = {
    "1": 248_956_422,
    "2": 242_193_529,
    "3": 198_295_559,
    "4": 190_214_555,
    "5": 181_538_259,
    "6": 170_805_979,
    "7": 159_345_973,
    "8": 145_138_636,
    "9": 138_394_717,
    "10": 133_797_422,
    "11": 135_086_622,
    "12": 133_275_309,
    "13": 114_364_328,
    "14": 107_043_718,
    "15": 101_991_189,
    "16": 90_338_345,
    "17": 83_257_441,
    "18": 80_373_285,
    "19": 58_617_616,
    "20": 64_444_167,
    "21": 46_709_983,
    "22": 50_818_468,
    "X": 156_040_895,
    "Y": 57_227_415,
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
      .beginner-card,
      .quick-fact,
      .web-hero,
      .story-card,
      .lesson-card,
      .teacher-card,
      .sequence-chip,
      .sequence-summary-card,
      .readable-sequence,
      .stage-note,
      .detail-panel,
      .detail-kv,
      .stage-card,
      .sequence-preview-panel {
        color-scheme: light;
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
      .lesson-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.75rem;
        margin: 0.85rem 0;
      }
      .lesson-card {
        border: 1px solid #d8dee9;
        border-radius: 8px;
        background: #ffffff;
        padding: 0.9rem;
        min-width: 0;
      }
      .lesson-card-title {
        color: #111827;
        font-size: 1rem;
        font-weight: 850;
        margin-bottom: 0.35rem;
      }
      .lesson-card-edit {
        display: inline-flex;
        border-radius: 999px;
        border: 1px solid #d8dee9;
        background: #f9fafb;
        color: #111827;
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: 0.82rem;
        font-weight: 850;
        padding: 0.25rem 0.55rem;
        margin-bottom: 0.45rem;
      }
      .lesson-card-copy {
        color: #4b5563;
        font-size: 0.9rem;
        line-height: 1.4;
      }
      .lesson-card-kv {
        color: #111827;
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: 0.82rem;
        margin-top: 0.55rem;
        overflow-wrap: anywhere;
      }
      .teacher-guide-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.75rem;
        margin: 0.85rem 0;
      }
      .teacher-card {
        border: 1px solid #d8dee9;
        border-radius: 8px;
        background: #ffffff;
        padding: 0.9rem;
        min-width: 0;
      }
      .teacher-card-kicker {
        color: #3a86ff;
        font-size: 0.75rem;
        font-weight: 850;
        text-transform: uppercase;
        margin-bottom: 0.25rem;
      }
      .teacher-card-title {
        color: #111827;
        font-weight: 850;
        margin-bottom: 0.35rem;
      }
      .teacher-card-copy {
        color: #4b5563;
        font-size: 0.9rem;
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
      .guide-panel {
        border: 1px solid #d8dee9;
        border-radius: 8px;
        background: #ffffff;
        padding: 0.95rem;
        margin: 0.85rem 0 1rem;
      }
      .guide-title {
        color: #111827;
        font-weight: 850;
        margin-bottom: 0.25rem;
      }
      .guide-copy {
        color: #4b5563;
        line-height: 1.4;
        margin-bottom: 0.75rem;
      }
      .friendly-error {
        border-left: 4px solid #ef476f;
        background: #fff7f8;
        color: #111827;
        padding: 0.85rem 0.95rem;
        border-radius: 8px;
        margin: 0.75rem 0;
      }
      .mode-note {
        border-left: 4px solid #1f9d8a;
        background: #f4fbfa;
        color: #374151;
        padding: 0.75rem 0.9rem;
        border-radius: 8px;
        margin: 0.75rem 0;
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
      .sequence-preview-panel {
        border: 1px solid #d8dee9;
        border-radius: 8px;
        background: #ffffff;
        padding: 0.85rem;
        margin: 0.7rem 0 0.9rem;
      }
      .sequence-preview-top {
        display: flex;
        justify-content: space-between;
        gap: 0.75rem;
        align-items: baseline;
        margin-bottom: 0.65rem;
      }
      .sequence-preview-title {
        color: #111827;
        font-weight: 850;
      }
      .sequence-preview-count {
        color: #4b5563;
        font-size: 0.82rem;
      }
      .sequence-blocks {
        display: flex;
        flex-wrap: wrap;
        gap: 0.2rem;
        max-width: 100%;
      }
      .seq-symbol {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 1.18rem;
        height: 1.35rem;
        border-radius: 5px;
        color: #ffffff;
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: 0.72rem;
        font-weight: 850;
      }
      .seq-a { background: #1f9d8a; }
      .seq-t, .seq-u { background: #ef476f; }
      .seq-g { background: #f4a261; }
      .seq-c { background: #3a86ff; }
      .seq-stop { background: #111827; }
      .seq-protein { background: #457b9d; }
      .seq-other { background: #9aa0a6; }
      .sequence-more {
        color: #4b5563;
        font-size: 0.84rem;
        margin-top: 0.55rem;
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
        overflow-x: auto;
        max-width: 100%;
      }
      .stage-note {
        border-left: 4px solid #1f9d8a;
        background: #ffffff;
        border-radius: 8px;
        color: #374151;
        padding: 0.75rem 0.9rem;
        margin: 0.7rem 0;
      }
      .detail-panel {
        border: 1px solid #d8dee9;
        border-radius: 8px;
        background: #ffffff;
        padding: 1rem;
        margin: 0.85rem 0 1rem;
      }
      .detail-title {
        color: #111827;
        font-size: 1.15rem;
        font-weight: 850;
        margin-bottom: 0.35rem;
      }
      .detail-copy {
        color: #374151;
        line-height: 1.45;
      }
      .detail-kv-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.65rem;
        margin-top: 0.85rem;
      }
      .detail-kv {
        border: 1px solid #d8dee9;
        border-radius: 8px;
        background: #f9fafb;
        padding: 0.7rem;
      }
      .detail-kv-label {
        color: #4b5563;
        font-size: 0.78rem;
        margin-bottom: 0.25rem;
      }
      .detail-kv-value {
        color: #111827;
        font-weight: 850;
        overflow-wrap: anywhere;
      }
      .chromosome-track {
        position: relative;
        height: 38px;
        border-radius: 999px;
        background: linear-gradient(90deg, #e5e7eb, #cbd5e1);
        border: 1px solid #cbd5e1;
        margin: 1rem 0 0.5rem;
        overflow: hidden;
      }
      .chromosome-band {
        position: absolute;
        top: 0;
        bottom: 0;
        width: 2px;
        background: rgba(17, 24, 39, 0.16);
      }
      .gene-marker {
        position: absolute;
        top: 4px;
        bottom: 4px;
        border-radius: 999px;
        background: linear-gradient(90deg, #3a86ff, #ef476f);
        box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.18);
      }
      .chromosome-label-row {
        display: flex;
        justify-content: space-between;
        color: #4b5563;
        font-size: 0.8rem;
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      }
      .mini-flow {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.5rem;
        margin-top: 0.85rem;
      }
      .mini-node {
        border: 1px solid #d8dee9;
        border-radius: 8px;
        color: #111827;
        background: #f9fafb;
        padding: 0.65rem;
        text-align: center;
        font-weight: 800;
      }
      .stage-card-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 0.65rem;
        margin: 0.75rem 0 0.9rem;
      }
      .stage-card {
        border: 1px solid #d8dee9;
        border-radius: 8px;
        background: #ffffff;
        padding: 0.8rem;
        min-width: 0;
      }
      .stage-card-active {
        border-color: #3a86ff;
        box-shadow: inset 0 0 0 1px #3a86ff;
      }
      .stage-card-number {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 1.55rem;
        height: 1.55rem;
        border-radius: 999px;
        background: #111827;
        color: #ffffff;
        font-size: 0.78rem;
        font-weight: 850;
        margin-bottom: 0.55rem;
      }
      .stage-card-title {
        color: #111827;
        font-weight: 850;
        line-height: 1.2;
      }
      .stage-card-copy {
        color: #4b5563;
        font-size: 0.86rem;
        line-height: 1.35;
        margin-top: 0.35rem;
      }
      .stage-card-meta {
        display: inline-flex;
        border: 1px solid #d8dee9;
        border-radius: 999px;
        color: #111827;
        background: #f9fafb;
        padding: 0.22rem 0.5rem;
        margin-top: 0.55rem;
        font-size: 0.78rem;
        font-weight: 800;
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
        .lesson-grid,
        .teacher-guide-grid,
        .sequence-strip,
        .sequence-summary-grid,
        .detail-kv-grid,
        .mini-flow,
        .stage-card-grid {
          grid-template-columns: 1fr;
        }
        .sequence-preview-top {
          display: block;
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


def friendly_error_message(exc: Exception, context: str = "lookup") -> str:
    text = str(exc)
    if context == "mutation":
        if "Reference base mismatch" in text:
            return "That edit does not match the selected coding DNA. Try one of the suggested examples for this gene."
        if "Position must be" in text:
            return text
        return "Try a simple coding-DNA edit like 20 A>T, 20del, or 20insA."
    if isinstance(exc, EnsemblError):
        return (
            "I could not load that live Ensembl gene right now. Try HBB, BRCA1, or TP53, "
            "or use the built-in HBB demo while the live lookup catches up."
        )
    if isinstance(exc, LookupError):
        return "We couldn't find that gene symbol for this species. Try checking the spelling or selecting another species."
    return "Something went sideways while loading this gene. Try another symbol or reload the built-in HBB demo."


def show_friendly_error(exc: Exception, context: str = "lookup") -> None:
    st.markdown(
        f'<div class="friendly-error">{escape_html(friendly_error_message(exc, context))}</div>',
        unsafe_allow_html=True,
    )
    if st.session_state.get("learning_mode") == "Advanced":
        with st.expander("Technical detail"):
            st.code(str(exc), language="text")


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


def sequence_symbol_class(symbol: str, alphabet: str) -> str:
    if symbol == "*":
        return "seq-stop"
    if alphabet == "protein":
        return "seq-protein"
    if symbol in {"A", "T", "U", "G", "C"}:
        return f"seq-{symbol.lower()}"
    return "seq-other"


def sequence_blocks_html(sequence: str, alphabet: str, max_symbols: int = 240) -> str:
    cleaned = clean_sequence(sequence).replace("T", "U") if alphabet == "rna" else clean_sequence(sequence)
    if not cleaned:
        return """
        <div class="sequence-preview-panel">
          <div class="sequence-preview-top">
            <div class="sequence-preview-title">Sequence preview</div>
            <div class="sequence-preview-count">No sequence returned</div>
          </div>
        </div>
        """

    shown = cleaned[:max_symbols]
    symbols = "".join(
        f'<span class="seq-symbol {sequence_symbol_class(symbol, alphabet)}">{escape_html(symbol)}</span>'
        for symbol in shown
    )
    hidden = len(cleaned) - len(shown)
    hidden_note = f'<div class="sequence-more">{hidden:,} more symbols hidden. Expand the full text below when you need it.</div>' if hidden > 0 else ""
    return f"""
    <div class="sequence-preview-panel">
      <div class="sequence-preview-top">
        <div class="sequence-preview-title">First {len(shown):,} symbols</div>
        <div class="sequence-preview-count">{len(cleaned):,} total</div>
      </div>
      <div class="sequence-blocks">{symbols}</div>
      {hidden_note}
    </div>
    """


def stage_card_grid_html(stages: list[dict], selected_label: str) -> str:
    cards = ['<div class="stage-card-grid">']
    for index, stage in enumerate(stages, start=1):
        active_class = " stage-card-active" if stage["label"] == selected_label else ""
        length = len(clean_sequence(stage["sequence"]))
        cards.append(
            (
                f'<div class="stage-card{active_class}">'
                f'<div class="stage-card-number">{index}</div>'
                f'<div class="stage-card-title">{escape_html(stage["label"])}</div>'
                f'<div class="stage-card-copy">{escape_html(stage["short"])}</div>'
                f'<div class="stage-card-meta">{length:,} {escape_html(stage["unit"])}</div>'
                "</div>"
            )
        )
    cards.append("</div>")
    return "".join(cards)


def chromosome_key(gene: dict) -> str:
    return str(gene.get("seq_region_name") or "").replace("chr", "").upper()


def detail_kv_grid(items: list[tuple[str, str]]) -> str:
    html = ['<div class="detail-kv-grid">']
    for label, value in items:
        html.append(
            (
                '<div class="detail-kv">'
                f'<div class="detail-kv-label">{escape_html(label)}</div>'
                f'<div class="detail-kv-value">{escape_html(value)}</div>'
                "</div>"
            )
        )
    html.append("</div>")
    return "".join(html)


def render_location_detail(gene: dict) -> None:
    chrom = chromosome_key(gene)
    start = int(gene.get("start") or 0)
    end = int(gene.get("end") or 0)
    chrom_length = HUMAN_CHROMOSOME_LENGTHS.get(chrom)
    track_html = ""
    if chrom_length and start and end:
        left = max(0.0, min(100.0, start / chrom_length * 100))
        width = max(0.6, min(100.0 - left, (end - start + 1) / chrom_length * 100))
        bands = "".join(f'<span class="chromosome-band" style="left:{pct}%"></span>' for pct in [20, 40, 60, 80])
        track_html = f"""
              <div class="chromosome-track">
                {bands}
                <span class="gene-marker" style="left:{left:.2f}%; width:{width:.2f}%"></span>
              </div>
              <div class="chromosome-label-row">
                <span>chr{escape_html(chrom)}:1</span>
                <span>{chrom_length:,} bp</span>
              </div>
        """
    else:
        track_html = """
          <div class="stage-note">A scaled chromosome track is available for human chromosomes when start/end coordinates are returned.</div>
        """
    st.markdown(
        f"""
        <div class="detail-panel">
          <div class="detail-title">Chromosome location</div>
          <div class="detail-copy">
            {escape_html(gene.get("display_name", "This gene"))} is located on chromosome {escape_html(chrom or "?")}
            at {escape_html(gene_locus(gene))}. The marker below shows the approximate position across the chromosome.
          </div>
          {track_html}
          {detail_kv_grid([
              ("Assembly", str(gene.get("assembly_name") or "NA")),
              ("Start", f"{start:,}" if start else "NA"),
              ("End", f"{end:,}" if end else "NA"),
              ("Strand", strand_label(gene.get("strand"))),
              ("Gene span", f"{end - start + 1:,} bp" if start and end else "NA"),
              ("Coordinate system", "Ensembl gene locus"),
          ])}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_gene_type_detail(gene: dict) -> None:
    biotype = gene.get("biotype") or "NA"
    explanation = (
        "Protein-coding genes can produce transcripts with coding sequence, which can be translated into an amino acid chain."
        if biotype == "protein_coding"
        else "This biotype may work through RNA function, regulation, or transcript processing rather than a translated protein."
    )
    st.markdown(
        f"""
        <div class="detail-panel">
          <div class="detail-title">Gene type: {escape_html(biotype)}</div>
          <div class="detail-copy">{escape_html(explanation)}</div>
          <div class="mini-flow">
            <div class="mini-node">Gene</div>
            <div class="mini-node">Transcript</div>
            <div class="mini-node">Coding sequence</div>
            <div class="mini-node">Protein if translated</div>
          </div>
          {detail_kv_grid([("Biotype", biotype), ("Source", str(gene.get("source") or "Ensembl")), ("Object type", str(gene.get("object_type") or "Gene"))])}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_assembly_detail(gene: dict) -> None:
    assembly = str(gene.get("assembly_name") or "NA")
    st.markdown(
        f"""
        <div class="detail-panel">
          <div class="detail-title">Genome assembly</div>
          <div class="detail-copy">
            The assembly is the reference genome coordinate system used for this gene. Coordinates only make sense relative
            to a specific assembly, so {escape_html(gene_locus(gene))} means this locus on {escape_html(assembly)}.
          </div>
          {detail_kv_grid([("Assembly", assembly), ("Chromosome", chromosome_key(gene) or "NA"), ("Locus", gene_locus(gene))])}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_transcript_detail(selected: dict, transcripts: list[dict]) -> None:
    exons = selected.get("Exon") or selected.get("exons") or []
    translation = selected.get("Translation") or {}
    st.markdown(
        f"""
        <div class="detail-panel">
          <div class="detail-title">Selected transcript</div>
          <div class="detail-copy">
            A transcript is the RNA version of the gene that this app follows through splicing, coding sequence, and protein translation.
            One gene can have many transcripts, so picking the transcript changes the central-dogma story.
          </div>
          {detail_kv_grid([("Transcript ID", str(selected.get("id") or "NA")), ("Name", str(selected.get("display_name") or "NA")), ("Canonical", "Yes" if selected.get("is_canonical") else "No"), ("Transcript length", f"{int(selected.get("length") or 0):,} bases" if selected.get("length") else "NA"), ("Exons returned", str(len(exons)) if exons else "Not in response"), ("Translation", str(translation.get("id") or "No protein translation"))])}
        </div>
        """,
        unsafe_allow_html=True,
    )
    if len(transcripts) > 1:
        st.caption(f"Ensembl returned {len(transcripts):,} transcript records for this gene. The selected transcript is highlighted in the Isoforms table below.")


def render_protein_detail(translation: dict, sequences: dict) -> None:
    protein = sequences.get("protein", "")
    st.markdown(
        f"""
        <div class="detail-panel">
          <div class="detail-title">Protein product</div>
          <div class="detail-copy">
            The protein product is the amino acid chain returned for the selected translated transcript. For HBB, this is beta-globin,
            one chain of adult hemoglobin.
          </div>
          {detail_kv_grid([("Protein ID", str(translation.get("id") or "NA")), ("Length", f"{len(protein):,} amino acids"), ("Starts with", protein[:12] or "NA"), ("Ends with", protein[-12:] or "NA")])}
        </div>
        """,
        unsafe_allow_html=True,
    )
    if protein:
        st.markdown(
            f'<div class="readable-sequence">{escape_html(wrap_for_display(protein, line_width=60, max_symbols=360))}</div>',
            unsafe_allow_html=True,
        )


def render_exons_detail(selected: dict) -> None:
    exons = selected.get("Exon") or selected.get("exons") or []
    st.markdown(
        """
        <div class="detail-panel">
          <div class="detail-title">Exons and introns</div>
          <div class="detail-copy">
            Exons are transcript pieces that remain after RNA processing. Introns are the genomic intervals removed during splicing.
            This is the transition between the broad gene locus and the spliced mRNA used later in the central dogma.
          </div>
          <div class="mini-flow">
            <div class="mini-node">Gene locus</div>
            <div class="mini-node">Exons + introns</div>
            <div class="mini-node">Spliced transcript</div>
            <div class="mini-node">CDS/protein</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
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
        st.info("Exon coordinates were not included in this lookup response, so the app explains the concept and shows sequence context instead.")


def render_clickable_gene_details(data: dict, selected: dict, translation: dict, transcripts: list[dict]) -> None:
    st.subheader("Tap a gene card to inspect it")
    details = [
        ("Location", "where it sits on the chromosome"),
        ("Gene Type", "what kind of gene this is"),
        ("Assembly", "which genome map is being used"),
        ("Transcript", "the RNA version selected"),
        ("Protein", "the amino acid product"),
        ("Exons", "what gets kept after splicing"),
    ]
    if "gene_detail_focus" not in st.session_state:
        st.session_state["gene_detail_focus"] = "Location"
    cols = st.columns(3)
    for index, (label, caption) in enumerate(details):
        with cols[index % 3]:
            if st.button(f"{label}\n{caption}", key=f"detail-{label}", use_container_width=True):
                st.session_state["gene_detail_focus"] = label

    focus = st.session_state["gene_detail_focus"]
    if focus == "Location":
        render_location_detail(data["gene"])
    elif focus == "Gene Type":
        render_gene_type_detail(data["gene"])
    elif focus == "Assembly":
        render_assembly_detail(data["gene"])
    elif focus == "Transcript":
        render_transcript_detail(selected, transcripts)
    elif focus == "Protein":
        render_protein_detail(translation, data["sequences"])
    else:
        render_exons_detail(selected)


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


def sequence_panel(label: str, sequence: str, alphabet: str, fasta_header: str, key_prefix: str, preview_symbols: int = 240) -> None:
    summary = summarize_sequence(sequence, alphabet)
    st.markdown(sequence_summary_cards(summary), unsafe_allow_html=True)
    st.markdown(sequence_blocks_html(sequence, alphabet, max_symbols=preview_symbols), unsafe_allow_html=True)
    with st.expander(f"Show readable {label} text"):
        st.markdown(
            f'<div class="readable-sequence">{escape_html(wrap_for_display(sequence, max_symbols=preview_symbols * 2))}</div>',
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
        {
            "label": "Genomic DNA",
            "short": "The gene's DNA at its chromosome locus.",
            "detail": "DNA at the gene locus, before transcript processing.",
            "sequence": sequences.get("genomic_dna", ""),
            "alphabet": "dna",
            "unit": "bp",
            "fasta": f"{gene['display_name']}|genomic_dna",
        },
        {
            "label": "Exons / Introns",
            "short": "The transcript model decides what is kept.",
            "detail": "Ensembl transcript models define exons. Introns are the genomic intervals removed during splicing.",
            "sequence": sequences.get("genomic_dna", ""),
            "alphabet": "dna",
            "unit": "bp context",
            "fasta": f"{gene['display_name']}|exon_intron_context",
        },
        {
            "label": "Spliced mRNA",
            "short": "The mature message after splicing.",
            "detail": "The transcript cDNA converted to RNA letters, representing the mature spliced transcript.",
            "sequence": to_mrna(sequences.get("transcript_cdna", "")),
            "alphabet": "rna",
            "unit": "nt",
            "fasta": f"{gene['display_name']}|spliced_mrna",
        },
        {
            "label": "Coding Sequence",
            "short": "The part read three bases at a time.",
            "detail": "The CDS is the part of the transcript read in codons to build the protein.",
            "sequence": sequences.get("coding_dna", ""),
            "alphabet": "dna",
            "unit": "bases",
            "fasta": f"{gene['display_name']}|coding_sequence",
        },
        {
            "label": "Amino Acid Chain",
            "short": "The translated protein sequence.",
            "detail": "The amino acid sequence produced by translating the coding sequence.",
            "sequence": sequences.get("protein", ""),
            "alphabet": "protein",
            "unit": "aa",
            "fasta": f"{gene['display_name']}|protein",
        },
    ]
    labels = [stage["label"] for stage in stages]
    selected_stage = st.segmented_control("Tap a central dogma step", labels, default=labels[0])
    stage = stages[labels.index(selected_stage or labels[0])]
    st.markdown(stage_card_grid_html(stages, stage["label"]), unsafe_allow_html=True)
    st.markdown(f'<div class="stage-note">{escape_html(stage["detail"])}</div>', unsafe_allow_html=True)
    if stage["label"] == "Exons / Introns":
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
    sequence_panel(stage["label"], stage["sequence"], stage["alphabet"], stage["fasta"], f"dogma-map-{selected_stage}")


def mutation_effect_explanation(effect: str) -> str:
    explanations = {
        "silent": "The DNA changed, but the codon still points to the same amino acid.",
        "missense": "One amino acid changed. This can matter if that residue is important for the protein.",
        "nonsense": "The edit creates a stop signal, so translation may stop early.",
        "frameshift": "The reading frame shifts, so many downstream codons can change.",
    }
    return explanations.get(effect, "The coding sequence changed.")


def mutation_result_row(label: str, result: dict) -> dict:
    return {
        "edit": label,
        "type": result["mutation_type"],
        "position": result["position"],
        "codon": result["codon_number"],
        "DNA codon": f"{result['original_codon'] or 'NA'} -> {result['mutated_codon'] or 'NA'}",
        "AA": f"{result['original_amino_acid'] or 'NA'} -> {result['mutated_amino_acid'] or 'NA'}",
        "effect": result["effect"],
        "plain English": mutation_effect_explanation(result["effect"]),
    }


def alternate_base(base: str) -> str:
    for candidate in "TGCA":
        if candidate != base:
            return candidate
    return "A"


def example_substitution_change(coding_dna: str, preferred_position: int = 20) -> str:
    cleaned = clean_sequence(coding_dna).replace("U", "T")
    if not cleaned:
        return ""
    position = min(max(1, preferred_position), len(cleaned))
    reference = cleaned[position - 1]
    return f"{position} {reference}>{alternate_base(reference)}"


def example_missense_change(coding_dna: str) -> str:
    cleaned = clean_sequence(coding_dna).replace("U", "T")
    preferred = example_substitution_change(cleaned)
    if preferred:
        try:
            result = simulate_dna_mutation(cleaned, preferred)
            if result["effect"] == "missense":
                return preferred
        except ValueError:
            pass
    for position, reference in enumerate(cleaned, start=1):
        for alternate in "ACGT":
            if alternate == reference:
                continue
            change = f"{position} {reference}>{alternate}"
            try:
                result = simulate_dna_mutation(cleaned, change)
            except ValueError:
                continue
            if result["effect"] == "missense":
                return change
    return example_substitution_change(coding_dna)


def example_deletion_change(coding_dna: str, preferred_position: int = 20) -> str:
    cleaned = clean_sequence(coding_dna).replace("U", "T")
    if not cleaned:
        return ""
    position = min(max(1, preferred_position), len(cleaned))
    return f"{position}del"


def example_nonsense_change(coding_dna: str) -> str:
    cleaned = clean_sequence(coding_dna).replace("U", "T")
    stops = {"TAA", "TAG", "TGA"}
    for codon_start in range(0, len(cleaned) - 2, 3):
        original = cleaned[codon_start : codon_start + 3]
        if original in stops or translate_dna(original) == "*":
            continue
        for offset, reference in enumerate(original):
            for alternate in "ACGT":
                if alternate == reference:
                    continue
                mutated = original[:offset] + alternate + original[offset + 1 :]
                if mutated in stops:
                    return f"{codon_start + offset + 1} {reference}>{alternate}"
    return ""


def mutation_lesson_rows(coding_dna: str) -> list[dict]:
    examples = [
        (
            "Missense",
            example_missense_change(coding_dna),
            "A DNA edit changes one codon so the protein gets a different amino acid.",
        ),
        (
            "Nonsense",
            example_nonsense_change(coding_dna),
            "A DNA edit creates an early stop signal, which can shorten the protein.",
        ),
        (
            "Frameshift",
            example_deletion_change(coding_dna),
            "A one-base deletion shifts the reading frame, changing downstream codons.",
        ),
    ]
    rows = []
    for title, change, explanation in examples:
        if not change:
            continue
        try:
            result = simulate_dna_mutation(coding_dna, change)
        except ValueError:
            continue
        rows.append(
            {
                "title": title,
                "change": change,
                "effect": result["effect"],
                "codon": f"{result['original_codon'] or 'NA'} -> {result['mutated_codon'] or 'NA'}",
                "amino_acid": f"{result['original_amino_acid'] or 'NA'} -> {result['mutated_amino_acid'] or 'NA'}",
                "explanation": explanation,
            }
        )
    return rows


def render_mutation_lesson(sequences: dict) -> None:
    rows = mutation_lesson_rows(sequences.get("coding_dna", ""))
    if not rows:
        st.warning("No coding DNA returned, so the two-minute mutation lesson is unavailable for this transcript.")
        return
    cards = ['<div class="lesson-grid">']
    for row in rows:
        cards.append(
            (
                '<div class="lesson-card">'
                f'<div class="lesson-card-title">{escape_html(row["title"])}</div>'
                f'<div class="lesson-card-edit">{escape_html(row["change"])}</div>'
                f'<div class="lesson-card-copy">{escape_html(row["explanation"])}</div>'
                f'<div class="lesson-card-kv">Effect: {escape_html(row["effect"])}</div>'
                f'<div class="lesson-card-kv">Codon: {escape_html(row["codon"])}</div>'
                f'<div class="lesson-card-kv">AA: {escape_html(row["amino_acid"])}</div>'
                "</div>"
            )
        )
    cards.append("</div>")
    st.markdown("".join(cards), unsafe_allow_html=True)
    st.caption("Use this as a fast teaching script: missense changes meaning, nonsense creates stop, frameshift changes the reading frame.")


def teacher_lesson_steps(data: dict) -> list[dict[str, str]]:
    gene = data["gene"]
    name = gene.get("display_name", "this gene")
    return [
        {
            "kicker": "0-30 sec",
            "title": "Hook",
            "copy": f"Ask: how can one DNA letter in {name} change a protein enough for biology to notice?",
        },
        {
            "kicker": "30-90 sec",
            "title": "Trace the path",
            "copy": "Open the dogma path: DNA is stored, RNA is copied and processed, codons are read, protein is built.",
        },
        {
            "kicker": "90-120 sec",
            "title": "Compare edits",
            "copy": "Run missense versus nonsense. Have students explain why one swaps an amino acid while the other creates a stop.",
        },
    ]


def render_teacher_guide(data: dict) -> None:
    cards = ['<div class="teacher-guide-grid">']
    for step in teacher_lesson_steps(data):
        cards.append(
            (
                '<div class="teacher-card">'
                f'<div class="teacher-card-kicker">{escape_html(step["kicker"])}</div>'
                f'<div class="teacher-card-title">{escape_html(step["title"])}</div>'
                f'<div class="teacher-card-copy">{escape_html(step["copy"])}</div>'
                "</div>"
            )
        )
    cards.append("</div>")
    st.markdown("".join(cards), unsafe_allow_html=True)
    with st.expander("Teacher prompts and exit ticket"):
        st.write("- Discussion prompt: Which step changes during transcription, splicing, translation, and mutation?")
        st.write("- Partner prompt: Compare a missense and nonsense result using the codon and amino-acid rows.")
        st.write("- Exit ticket: In one sentence, explain why not every DNA change has the same protein effect.")


def mutation_simulator(sequences: dict, key_prefix: str = "mutation") -> None:
    coding_dna = sequences.get("coding_dna", "")
    default_change = example_missense_change(coding_dna)
    nonsense_change = example_nonsense_change(coding_dna)
    deletion_change = example_deletion_change(coding_dna)
    example_text = ", ".join(change for change in [default_change, nonsense_change, deletion_change] if change)
    if example_text:
        st.caption(f"Try: {example_text}")
    change = st.text_input(
        "DNA change",
        value=default_change,
        placeholder="20 A>T, 20del, or 20insA",
        key=f"{key_prefix}-single-change",
    )
    if st.button("Simulate Mutation", key=f"{key_prefix}-single-submit"):
        try:
            result = simulate_dna_mutation(coding_dna, change)
        except ValueError as exc:
            show_friendly_error(exc, context="mutation")
            return

        cols = st.columns(5)
        cols[0].metric("Original codon", result["original_codon"] or "NA")
        cols[1].metric("Mutated codon", result["mutated_codon"] or "NA")
        cols[2].metric("Original AA", result["original_amino_acid"] or "NA")
        cols[3].metric("Changed AA", result["mutated_amino_acid"] or "NA")
        cols[4].metric("Effect", result["effect"])
        st.markdown(
            f'<div class="mode-note">{escape_html(mutation_effect_explanation(result["effect"]))}</div>',
            unsafe_allow_html=True,
        )
        st.code(short_sequence(result["mutated_dna"]), language="text")

    st.markdown("#### Compare two mutations")
    compare_cols = st.columns(2)
    change_a = compare_cols[0].text_input("Mutation A", value=default_change, key=f"{key_prefix}-compare-a")
    change_b_default = nonsense_change or deletion_change
    change_b = compare_cols[1].text_input("Mutation B", value=change_b_default, key=f"{key_prefix}-compare-b")
    if st.button("Compare Mutations", key=f"{key_prefix}-compare-submit"):
        try:
            result_a = simulate_dna_mutation(coding_dna, change_a)
            result_b = simulate_dna_mutation(coding_dna, change_b)
        except ValueError as exc:
            show_friendly_error(exc, context="mutation")
            return
        rows = [mutation_result_row(change_a, result_a), mutation_result_row(change_b, result_b)]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        if result_a["effect"] == result_b["effect"]:
            st.info(f"Both edits are classified as {result_a['effect']}. The sequence changes may still differ.")
        else:
            st.info(f"Mutation A is {result_a['effect']}; mutation B is {result_b['effect']}. Compare the AA and codon columns to see why.")


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
                    show_friendly_error(exc)


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


def load_famous_gene(symbol: str) -> None:
    if symbol == "HBB":
        st.session_state["dogma_data"] = load_example()
    else:
        st.session_state["dogma_data"] = cached_lookup(symbol, "homo_sapiens")
    st.session_state["loaded_example_default"] = symbol == "HBB"


def render_guided_start(default_species: str) -> None:
    st.markdown(
        """
        <div class="guide-panel">
          <div class="guide-title">Start with a real gene story</div>
          <div class="guide-copy">
            Open the offline HBB classic, try a famous live gene, search any Ensembl symbol, or jump straight into a mutation example.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(5)
    if cols[0].button("Explore HBB", type="primary", use_container_width=True):
        load_famous_gene("HBB")
        st.success("Loaded the offline HBB teaching example.")
    if cols[1].button("Try BRCA1", use_container_width=True):
        try:
            load_famous_gene("BRCA1")
            st.success("Loaded BRCA1.")
        except Exception as exc:
            show_friendly_error(exc)
    if cols[2].button("Try TP53", use_container_width=True):
        try:
            load_famous_gene("TP53")
            st.success("Loaded TP53.")
        except Exception as exc:
            show_friendly_error(exc)
    if cols[3].button("Search any gene", use_container_width=True):
        st.session_state["show_inline_search"] = not st.session_state.get("show_inline_search", False)
    if cols[4].button("Simulate mutation", use_container_width=True):
        st.session_state["show_mutation_quickstart"] = True

    if st.session_state.get("show_inline_search"):
        with st.form("inline-gene-search"):
            search_cols = st.columns([2, 2, 1])
            inline_symbol = search_cols[0].text_input("Gene symbol", value="HBB", key="inline-symbol").strip()
            inline_species = search_cols[1].text_input("Species alias", value=default_species, key="inline-species").strip()
            submitted = search_cols[2].form_submit_button("Load", use_container_width=True)
        if submitted and inline_symbol:
            try:
                st.session_state["dogma_data"] = cached_lookup(inline_symbol, inline_species or "homo_sapiens")
                st.session_state["loaded_example_default"] = False
                st.success(f"Loaded {inline_symbol.upper()}.")
            except Exception as exc:
                show_friendly_error(exc)


st.title("Gene Central Dogma Explorer")
st.caption("Start with a gene, then follow its DNA -> RNA -> protein story in plain English.")

if "dogma_data" not in st.session_state:
    st.session_state["dogma_data"] = load_example()
if "loaded_example_default" not in st.session_state:
    st.session_state["loaded_example_default"] = True
if "saved_genes" not in st.session_state:
    st.session_state["saved_genes"] = []
if "learning_mode" not in st.session_state:
    st.session_state["learning_mode"] = "Beginner"

with st.sidebar:
    st.header("Mode")
    st.session_state["learning_mode"] = st.segmented_control(
        "Reading level",
        ["Beginner", "Advanced"],
        default=st.session_state["learning_mode"],
        help="Beginner keeps the flow plain-English. Advanced keeps the same app, with more technical tables and raw data available.",
    )
    st.divider()
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
    load_famous_gene("HBB")
elif run_famous:
    try:
        load_famous_gene(famous_symbol)
        st.success(f"Loaded {famous_symbol}.")
    except Exception as exc:
        show_friendly_error(exc)
elif run_lookup and symbol:
    try:
        st.session_state["dogma_data"] = cached_lookup(symbol, species)
        st.session_state["loaded_example_default"] = False
    except Exception as exc:
        show_friendly_error(exc)

render_guided_start(species)
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

    mode = st.session_state.get("learning_mode", "Beginner")
    if mode == "Beginner":
        st.markdown(
            '<div class="mode-note">Beginner mode: start with the big story first. Raw sequences and technical tables are still available in Dogma and Advanced.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="mode-note">Advanced mode: identifiers, transcript tables, sequence downloads, and raw JSON are available in the lower tabs.</div>',
            unsafe_allow_html=True,
        )

    render_web_hero(data)
    render_quick_facts(gene)
    render_clickable_gene_details(data, selected, translation, transcripts)
    st.markdown(dogma_visual_html(data), unsafe_allow_html=True)
    render_sequence_strip(sequences)

    if st.session_state.get("show_mutation_quickstart"):
        st.subheader("Mutation quickstart")
        st.write("This uses the selected coding DNA sequence. The app suggests edits that match the loaded gene, including a missense-style substitution and a nonsense example when one is easy to make.")
        if sequences.get("coding_dna"):
            mutation_simulator(sequences, key_prefix="mutation-quickstart")
        else:
            st.warning("No coding DNA returned, so local codon mutation simulation is unavailable.")

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
            mutation_simulator(sequences, key_prefix="mutation-tab")
        else:
            st.warning("No coding DNA returned, so local codon mutation simulation is unavailable.")
        st.caption("This is a simple coding-DNA teaching tool. It does not parse HGVS, map genomic coordinates, or classify clinical variants.")

    with study_tab:
        st.subheader("Study mode")
        st.markdown(
            '<div class="mode-note">Teacher guide: a ready two-minute classroom flow for HBB or any loaded gene.</div>',
            unsafe_allow_html=True,
        )
        render_teacher_guide(data)
        st.markdown(
            '<div class="mode-note">Two-minute mutation lesson: compare a missense change, a nonsense stop, and a frameshift before you quiz yourself.</div>',
            unsafe_allow_html=True,
        )
        render_mutation_lesson(sequences)
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

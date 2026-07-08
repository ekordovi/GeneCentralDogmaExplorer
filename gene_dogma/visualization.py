"""HTML helpers for making gene sequence data visually scannable in Streamlit."""

from __future__ import annotations

from html import escape
from typing import Any


DNA_COLORS = {
    "A": "#1f9d8a",
    "T": "#ef476f",
    "U": "#ef476f",
    "G": "#f4a261",
    "C": "#3a86ff",
    "N": "#9aa0a6",
}

PROTEIN_COLORS = {
    "hydrophobic": "#2a9d8f",
    "polar": "#457b9d",
    "positive": "#e76f51",
    "negative": "#8338ec",
    "special": "#f4a261",
    "stop": "#1f2937",
    "other": "#9aa0a6",
}

HYDROPHOBIC = set("AILMFWVY")
POLAR = set("STNQ")
POSITIVE = set("KRH")
NEGATIVE = set("DE")
SPECIAL = set("CGP")


def _clean(sequence: Any) -> str:
    return "".join(char for char in str(sequence or "").upper() if char.isalpha() or char == "*")


def protein_color(residue: str) -> str:
    if residue == "*":
        return PROTEIN_COLORS["stop"]
    if residue in HYDROPHOBIC:
        return PROTEIN_COLORS["hydrophobic"]
    if residue in POLAR:
        return PROTEIN_COLORS["polar"]
    if residue in POSITIVE:
        return PROTEIN_COLORS["positive"]
    if residue in NEGATIVE:
        return PROTEIN_COLORS["negative"]
    if residue in SPECIAL:
        return PROTEIN_COLORS["special"]
    return PROTEIN_COLORS["other"]


def sequence_ribbon(sequence: str, molecule: str = "dna", limit: int = 180) -> str:
    """Return colored blocks for a sequence preview."""

    cleaned = _clean(sequence)[:limit]
    if not cleaned:
        return '<div class="sequence-ribbon empty">No sequence returned</div>'

    spans = []
    for char in cleaned:
        if molecule == "protein":
            color = protein_color(char)
        else:
            color = DNA_COLORS.get(char, "#9aa0a6")
        spans.append(f'<span title="{escape(char)}" style="background:{color}">{escape(char)}</span>')
    return f'<div class="sequence-ribbon">{"".join(spans)}</div>'


def sequence_preview(sequence: str, limit: int = 72) -> str:
    cleaned = _clean(sequence)
    if not cleaned:
        return "No sequence returned"
    if len(cleaned) <= limit:
        return cleaned
    flank = max(12, limit // 2)
    return f"{cleaned[:flank]} ... {cleaned[-flank:]}"


def molecule_card(title: str, subtitle: str, sequence: str, molecule: str) -> str:
    length = len(_clean(sequence))
    return f"""
    <div class="molecule-card">
      <div class="molecule-title">{escape(title)}</div>
      <div class="molecule-subtitle">{escape(subtitle)}</div>
      <div class="molecule-length">{length:,} symbols</div>
      <div class="sequence-text">{escape(sequence_preview(sequence))}</div>
      {sequence_ribbon(sequence, molecule=molecule, limit=144)}
    </div>
    """


def dogma_visual_html(data: dict[str, Any]) -> str:
    gene = data["gene"]
    sequences = data["sequences"]
    strand = "+" if gene.get("strand") == 1 else "-" if gene.get("strand") == -1 else "?"
    locus = f"{gene.get('seq_region_name', '?')}:{gene.get('start', '?')}-{gene.get('end', '?')} ({strand})"
    transcript = data.get("selected_transcript") or {}
    protein = data.get("selected_translation") or {}
    genomic_len = len(_clean(sequences.get("genomic_dna", "")))
    cdna_len = len(_clean(sequences.get("transcript_cdna", "")))
    cds_len = len(_clean(sequences.get("coding_dna", "")))
    protein_len = len(_clean(sequences.get("protein", "")))
    return f"""
    <style>
      .dogma-wrap {{
        border: 1px solid #d8dee9;
        border-radius: 8px;
        padding: 18px;
        background: linear-gradient(180deg, #ffffff 0%, #f7fafc 100%);
        overflow: hidden;
      }}
      .gene-hero {{
        display: grid;
        grid-template-columns: 1.2fr 2fr;
        gap: 16px;
        align-items: stretch;
        margin-bottom: 16px;
      }}
      .gene-card, .molecule-card {{
        border: 1px solid #d8dee9;
        border-radius: 8px;
        padding: 14px;
        background: #ffffff;
        min-width: 0;
      }}
      .gene-name {{
        font-size: 34px;
        font-weight: 800;
        color: #111827;
        line-height: 1;
        overflow-wrap: anywhere;
      }}
      .gene-locus {{
        margin-top: 8px;
        color: #4b5563;
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        overflow-wrap: anywhere;
      }}
      .locus-bar {{
        height: 18px;
        border-radius: 8px;
        margin-top: 14px;
        background: linear-gradient(90deg, #3a86ff 0%, #1f9d8a 36%, #f4a261 68%, #ef476f 100%);
      }}
      .dogma-arrow-row {{
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 10px;
        align-items: stretch;
        margin-top: 16px;
      }}
      .dogma-step {{
        border: 1px solid #d8dee9;
        border-radius: 8px;
        padding: 12px;
        background: #ffffff;
        min-height: 126px;
        min-width: 0;
        position: relative;
      }}
      .dogma-step strong {{
        display: block;
        font-size: 15px;
        color: #111827;
      }}
      .dogma-step span {{
        display: block;
        margin-top: 7px;
        color: #4b5563;
        font-size: 13px;
      }}
      .dogma-step-meta {{
        display: inline-flex;
        margin-top: 10px;
        border-radius: 999px;
        background: #f7fafc;
        border: 1px solid #d8dee9;
        color: #111827;
        font-size: 12px;
        font-weight: 800;
        padding: 4px 8px;
      }}
      .dogma-step-preview {{
        margin-top: 8px;
        color: #374151;
        font-size: 11px;
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        overflow-wrap: anywhere;
      }}
      .dogma-path-note {{
        margin-top: 12px;
        border-left: 4px solid #3a86ff;
        background: #ffffff;
        border-radius: 8px;
        padding: 10px 12px;
        color: #374151;
        font-size: 13px;
      }}
      .molecule-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
        margin-top: 16px;
      }}
      .molecule-title {{
        font-size: 15px;
        font-weight: 800;
        color: #111827;
      }}
      .molecule-subtitle, .molecule-length {{
        color: #4b5563;
        font-size: 12px;
        margin-top: 4px;
      }}
      .sequence-text {{
        margin-top: 9px;
        color: #111827;
        font-size: 11px;
        line-height: 1.35;
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        overflow-wrap: anywhere;
        word-break: break-word;
      }}
      .sequence-ribbon {{
        display: flex;
        flex-wrap: wrap;
        gap: 2px;
        margin-top: 10px;
        max-height: none;
        overflow: visible;
      }}
      .sequence-ribbon span {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 15px;
        height: 17px;
        border-radius: 4px;
        color: #ffffff;
        font-size: 9px;
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-weight: 700;
      }}
      .empty {{
        color: #6b7280;
        font-size: 13px;
      }}
      @media (max-width: 900px) {{
        .gene-hero, .dogma-arrow-row, .molecule-grid {{
          grid-template-columns: 1fr;
        }}
        .dogma-wrap {{
          padding: 12px;
        }}
        .gene-card, .molecule-card, .dogma-step {{
          padding: 11px;
        }}
        .gene-name {{
          font-size: 28px;
        }}
        .dogma-step {{
          min-height: auto;
        }}
        .sequence-ribbon span {{
          width: 14px;
          height: 16px;
          font-size: 8px;
        }}
      }}
    </style>
    <div class="dogma-wrap">
      <div class="gene-hero">
        <div class="gene-card">
          <div class="gene-name">{escape(str(gene.get("display_name", "Gene")))}</div>
          <div class="gene-locus">{escape(locus)}</div>
          <div class="locus-bar"></div>
          <div class="gene-locus">{escape(str(gene.get("biotype", "")))} | {escape(str(gene.get("assembly_name", "")))}</div>
        </div>
        <div class="gene-card">
          <div class="molecule-title">Selected transcript</div>
          <div class="gene-locus">{escape(str(transcript.get("id", "No transcript")))}</div>
          <div class="molecule-title" style="margin-top:14px">Protein product</div>
          <div class="gene-locus">{escape(str(protein.get("id", "No protein translation")))}</div>
        </div>
      </div>
      <div class="dogma-arrow-row">
        <div class="dogma-step"><strong>1. DNA</strong><span>Genomic sequence at the gene locus.</span><div class="dogma-step-meta">{genomic_len:,} bp</div><div class="dogma-step-preview">{escape(sequence_preview(sequences.get("genomic_dna", ""), 44))}</div></div>
        <div class="dogma-step"><strong>2. pre-mRNA</strong><span>Teaching proxy: DNA with U instead of T.</span><div class="dogma-step-meta">{genomic_len:,} nt</div><div class="dogma-step-preview">{escape(sequence_preview(sequences.get("pre_mrna_proxy", ""), 44))}</div></div>
        <div class="dogma-step"><strong>3. mRNA</strong><span>Spliced transcript sequence.</span><div class="dogma-step-meta">{cdna_len:,} nt</div><div class="dogma-step-preview">{escape(sequence_preview(sequences.get("transcript_cdna", ""), 44))}</div></div>
        <div class="dogma-step"><strong>4. CDS</strong><span>Protein-coding part read in codons.</span><div class="dogma-step-meta">{cds_len:,} bases</div><div class="dogma-step-preview">{escape(sequence_preview(sequences.get("coding_dna", ""), 44))}</div></div>
        <div class="dogma-step"><strong>5. Protein</strong><span>Amino acid product when translated.</span><div class="dogma-step-meta">{protein_len:,} aa</div><div class="dogma-step-preview">{escape(sequence_preview(sequences.get("protein", ""), 44))}</div></div>
      </div>
      <div class="dogma-path-note">
        DNA is copied into RNA, transcript processing selects a spliced message, the CDS is read three bases at a time, and the returned protein sequence shows the amino acid product for the selected transcript.
      </div>
      <div class="molecule-grid">
        {molecule_card("Genomic DNA", "locus sequence", sequences.get("genomic_dna", ""), "dna")}
        {molecule_card("mRNA", "spliced transcript proxy", sequences.get("transcript_cdna", ""), "dna")}
        {molecule_card("Coding mRNA", "CDS with U instead of T", sequences.get("coding_mrna", ""), "dna")}
        {molecule_card("Protein", "amino acid sequence", sequences.get("protein", ""), "protein")}
      </div>
    </div>
    """

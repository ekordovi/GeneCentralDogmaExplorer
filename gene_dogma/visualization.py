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


def sequence_summary(sequence: str, unit: str = "symbols") -> str:
    cleaned = _clean(sequence)
    if not cleaned:
        return f"0 {unit}; no sequence returned"
    start = cleaned[:10]
    end = cleaned[-10:]
    return f"{len(cleaned):,} {unit}; starts {start}; ends {end}"


def molecule_card(title: str, subtitle: str, sequence: str, molecule: str) -> str:
    length = len(_clean(sequence))
    return f"""
    <div class="molecule-card">
      <div class="molecule-title">{escape(title)}</div>
      <div class="molecule-subtitle">{escape(subtitle)}</div>
      <div class="molecule-length">{length:,} symbols</div>
      <div class="molecule-summary">{escape(sequence_summary(sequence))}</div>
      {sequence_ribbon(sequence, molecule=molecule, limit=96)}
    </div>
    """


def dogma_stage_card(
    number: int,
    title: str,
    subtitle: str,
    sequence: str,
    molecule: str,
    length_label: str,
    change_label: str,
) -> str:
    return f"""
    <div class="dogma-stage">
      <div class="dogma-stage-top">
        <div class="dogma-stage-number">{number}</div>
        <div>
          <div class="dogma-stage-title">{escape(title)}</div>
          <div class="dogma-stage-subtitle">{escape(subtitle)}</div>
        </div>
      </div>
      <div class="dogma-stage-change">{escape(change_label)}</div>
      <div class="dogma-stage-meta">{escape(length_label)}</div>
      <div class="dogma-stage-preview">{escape(sequence_summary(sequence, "symbols"))}</div>
      {sequence_ribbon(sequence, molecule=molecule, limit=42)}
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
        grid-template-columns: repeat(auto-fit, minmax(185px, 1fr));
        gap: 12px;
        align-items: stretch;
        margin-top: 14px;
      }}
      .dogma-flow-line {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 10px;
        margin-top: 16px;
        align-items: center;
      }}
      .dogma-flow-node {{
        border: 1px solid #d8dee9;
        border-radius: 8px;
        background: #ffffff;
        color: #111827;
        font-size: 12px;
        font-weight: 850;
        text-align: center;
        padding: 10px;
        position: relative;
      }}
      .dogma-flow-node:not(:last-child)::after {{
        content: "->";
        position: absolute;
        right: -19px;
        top: 50%;
        transform: translateY(-50%);
        color: #3a86ff;
        font-weight: 900;
        z-index: 1;
      }}
      .dogma-flow-kicker {{
        color: #3a86ff;
        font-size: 11px;
        font-weight: 900;
        text-transform: uppercase;
        margin-bottom: 3px;
      }}
      .dogma-flow-copy {{
        color: #4b5563;
        font-size: 12px;
        font-weight: 650;
        line-height: 1.25;
      }}
      .dogma-stage {{
        border: 1px solid #d8dee9;
        border-radius: 8px;
        padding: 13px;
        background: #ffffff;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 9px;
      }}
      .dogma-stage-top {{
        display: grid;
        grid-template-columns: auto minmax(0, 1fr);
        gap: 10px;
        align-items: start;
      }}
      .dogma-stage-number {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border-radius: 999px;
        background: #111827;
        color: #ffffff;
        font-weight: 850;
        font-size: 13px;
      }}
      .dogma-stage-title {{
        color: #111827;
        font-size: 15px;
        font-weight: 850;
        line-height: 1.2;
      }}
      .dogma-stage-subtitle {{
        color: #4b5563;
        font-size: 13px;
        line-height: 1.35;
        margin-top: 3px;
      }}
      .dogma-stage-meta {{
        display: inline-flex;
        align-self: flex-start;
        border-radius: 999px;
        background: #f7fafc;
        border: 1px solid #d8dee9;
        color: #111827;
        font-size: 12px;
        font-weight: 800;
        padding: 4px 8px;
      }}
      .dogma-stage-change {{
        border-left: 3px solid #3a86ff;
        background: #f7fafc;
        color: #374151;
        font-size: 12px;
        font-weight: 750;
        line-height: 1.35;
        padding: 7px 8px;
        border-radius: 6px;
      }}
      .dogma-stage-preview {{
        color: #374151;
        font-size: 12px;
        line-height: 1.45;
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        overflow-wrap: anywhere;
        word-break: break-word;
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
      .molecule-summary {{
        margin-top: 9px;
        color: #111827;
        font-size: 12px;
        line-height: 1.35;
        overflow-wrap: anywhere;
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
        min-width: 17px;
        height: 19px;
        border-radius: 4px;
        color: #ffffff;
        font-size: 10px;
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-weight: 700;
      }}
      .empty {{
        color: #6b7280;
        font-size: 13px;
      }}
      @media (max-width: 900px) {{
        .gene-hero, .dogma-flow-line, .molecule-grid {{
          grid-template-columns: 1fr;
        }}
        .dogma-arrow-row {{
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        }}
        .dogma-flow-node:not(:last-child)::after {{
          content: "↓";
          right: 50%;
          top: calc(100% + 2px);
          transform: translateX(50%);
          color: #111827;
        }}
        .dogma-flow-node {{
          margin-bottom: 8px;
        }}
        .dogma-wrap {{
          padding: 12px;
        }}
        .gene-card, .molecule-card, .dogma-stage {{
          padding: 11px;
        }}
        .gene-name {{
          font-size: 28px;
        }}
        .sequence-ribbon span {{
          min-width: 16px;
          height: 18px;
          font-size: 9px;
        }}
      }}
      @media (max-width: 560px) {{
        .dogma-arrow-row {{
          grid-template-columns: 1fr;
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
      <div class="dogma-flow-line">
        <div class="dogma-flow-node">
          <div class="dogma-flow-kicker">Transcription</div>
          <div class="dogma-flow-copy">DNA letters are copied into RNA letters.</div>
        </div>
        <div class="dogma-flow-node">
          <div class="dogma-flow-kicker">Splicing</div>
          <div class="dogma-flow-copy">Transcript processing keeps the mature message.</div>
        </div>
        <div class="dogma-flow-node">
          <div class="dogma-flow-kicker">Translation</div>
          <div class="dogma-flow-copy">Codons are read three bases at a time.</div>
        </div>
        <div class="dogma-flow-node">
          <div class="dogma-flow-kicker">Protein product</div>
          <div class="dogma-flow-copy">The amino acid chain is the visible result.</div>
        </div>
      </div>
      <div class="dogma-arrow-row">
        {dogma_stage_card(1, "DNA", "Genomic sequence at the chromosome locus.", sequences.get("genomic_dna", ""), "dna", f"{genomic_len:,} bp", "Source instruction")}
        {dogma_stage_card(2, "pre-mRNA", "Teaching proxy: copied RNA before splicing.", sequences.get("pre_mrna_proxy", ""), "dna", f"{genomic_len:,} nt", "T becomes U")}
        {dogma_stage_card(3, "mRNA", "Spliced transcript sequence selected by Ensembl.", sequences.get("transcript_cdna", ""), "dna", f"{cdna_len:,} nt", "Introns removed")}
        {dogma_stage_card(4, "CDS", "Protein-coding region read in three-letter codons.", sequences.get("coding_dna", ""), "dna", f"{cds_len:,} bases", "Reading frame chosen")}
        {dogma_stage_card(5, "Protein", "Amino acid product made from the codons.", sequences.get("protein", ""), "protein", f"{protein_len:,} aa", "Codons become amino acids")}
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

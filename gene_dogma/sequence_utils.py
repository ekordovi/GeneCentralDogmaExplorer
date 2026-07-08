"""Small sequence utilities for central-dogma views."""

from __future__ import annotations

from collections import Counter
import re
from typing import Any


DNA_COMPLEMENT = str.maketrans("ACGTNacgtn", "TGCANtgcan")

CODON_TABLE = {
    "TTT": "F",
    "TTC": "F",
    "TTA": "L",
    "TTG": "L",
    "TCT": "S",
    "TCC": "S",
    "TCA": "S",
    "TCG": "S",
    "TAT": "Y",
    "TAC": "Y",
    "TAA": "*",
    "TAG": "*",
    "TGT": "C",
    "TGC": "C",
    "TGA": "*",
    "TGG": "W",
    "CTT": "L",
    "CTC": "L",
    "CTA": "L",
    "CTG": "L",
    "CCT": "P",
    "CCC": "P",
    "CCA": "P",
    "CCG": "P",
    "CAT": "H",
    "CAC": "H",
    "CAA": "Q",
    "CAG": "Q",
    "CGT": "R",
    "CGC": "R",
    "CGA": "R",
    "CGG": "R",
    "ATT": "I",
    "ATC": "I",
    "ATA": "I",
    "ATG": "M",
    "ACT": "T",
    "ACC": "T",
    "ACA": "T",
    "ACG": "T",
    "AAT": "N",
    "AAC": "N",
    "AAA": "K",
    "AAG": "K",
    "AGT": "S",
    "AGC": "S",
    "AGA": "R",
    "AGG": "R",
    "GTT": "V",
    "GTC": "V",
    "GTA": "V",
    "GTG": "V",
    "GCT": "A",
    "GCC": "A",
    "GCA": "A",
    "GCG": "A",
    "GAT": "D",
    "GAC": "D",
    "GAA": "E",
    "GAG": "E",
    "GGT": "G",
    "GGC": "G",
    "GGA": "G",
    "GGG": "G",
}


def clean_sequence(sequence: Any) -> str:
    if sequence is None:
        return ""
    return "".join(char for char in str(sequence).upper() if char.isalpha() or char == "*")


def reverse_complement(sequence: str) -> str:
    return clean_sequence(sequence).translate(DNA_COMPLEMENT)[::-1]


def to_mrna(dna_sequence: str) -> str:
    return clean_sequence(dna_sequence).replace("T", "U")


def gc_content(sequence: str) -> float:
    cleaned = clean_sequence(sequence).replace("U", "T")
    bases = [base for base in cleaned if base in {"A", "C", "G", "T"}]
    if not bases:
        return 0.0
    gc = sum(base in {"G", "C"} for base in bases)
    return round(gc / len(bases) * 100, 2)


def translate_dna(dna_sequence: str) -> str:
    cleaned = clean_sequence(dna_sequence).replace("U", "T")
    protein = []
    for index in range(0, len(cleaned) - 2, 3):
        codon = cleaned[index : index + 3]
        protein.append(CODON_TABLE.get(codon, "X"))
    return "".join(protein)


def simulate_dna_mutation(dna_sequence: str, change: str) -> dict[str, Any]:
    """Apply a simple one-based CDS mutation and summarize the codon effect.

    Supported inputs:
    - ``20 A>T`` or ``20A>T`` for a substitution at base 20.
    - ``20del`` for a single-base deletion at base 20.
    - ``20insA`` for insertion after base 20.
    """

    cleaned = clean_sequence(dna_sequence).replace("U", "T")
    requested = str(change or "").strip().upper().replace(" ", "")
    if not cleaned:
        raise ValueError("No coding DNA sequence is available for mutation simulation.")
    if not requested:
        raise ValueError("Enter a mutation such as 20 A>T, 20del, or 20insA.")

    mutation_type = ""
    position = 0
    reference = ""
    alternate = ""

    substitution = re.fullmatch(r"(\d+)([ACGT])>([ACGT])", requested)
    deletion = re.fullmatch(r"(\d+)DEL([ACGT])?", requested)
    insertion = re.fullmatch(r"(\d+)INS([ACGT]+)", requested)

    if substitution:
        position = int(substitution.group(1))
        reference = substitution.group(2)
        alternate = substitution.group(3)
        mutation_type = "substitution"
    elif deletion:
        position = int(deletion.group(1))
        reference = deletion.group(2) or ""
        mutation_type = "deletion"
    elif insertion:
        position = int(insertion.group(1))
        alternate = insertion.group(2)
        mutation_type = "insertion"
    else:
        raise ValueError("Use a simple format like 20 A>T, 20del, or 20insA.")

    if position < 1 or position > len(cleaned):
        raise ValueError(f"Position must be between 1 and {len(cleaned):,}.")

    zero_index = position - 1
    actual_base = cleaned[zero_index]
    if mutation_type == "substitution":
        if actual_base != reference:
            raise ValueError(f"Reference base mismatch at {position}: expected {actual_base}, got {reference}.")
        mutated = cleaned[:zero_index] + alternate + cleaned[zero_index + 1 :]
        codon_index = zero_index // 3
    elif mutation_type == "deletion":
        if reference and actual_base != reference:
            raise ValueError(f"Reference base mismatch at {position}: expected {actual_base}, got {reference}.")
        mutated = cleaned[:zero_index] + cleaned[zero_index + 1 :]
        codon_index = zero_index // 3
    else:
        mutated = cleaned[:position] + alternate + cleaned[position:]
        codon_index = zero_index // 3

    codon_start = codon_index * 3
    original_codon = cleaned[codon_start : codon_start + 3]
    mutated_codon = mutated[codon_start : codon_start + 3]
    original_aa = translate_dna(original_codon) if len(original_codon) == 3 else ""
    mutated_aa = translate_dna(mutated_codon) if len(mutated_codon) == 3 else ""

    if len(mutated) % 3 != len(cleaned) % 3:
        effect = "frameshift"
    elif mutated_aa == "*":
        effect = "nonsense"
    elif original_aa == mutated_aa:
        effect = "silent"
    else:
        effect = "missense"

    return {
        "input": change,
        "mutation_type": mutation_type,
        "position": position,
        "codon_number": codon_index + 1,
        "original_base": actual_base,
        "original_codon": original_codon,
        "mutated_codon": mutated_codon,
        "original_amino_acid": original_aa,
        "mutated_amino_acid": mutated_aa,
        "effect": effect,
        "mutated_dna": mutated,
    }


def summarize_sequence(sequence: str, alphabet: str = "dna") -> dict[str, Any]:
    cleaned = clean_sequence(sequence)
    counts = Counter(cleaned)
    return {
        "length": len(cleaned),
        "gc_percent": gc_content(cleaned) if alphabet in {"dna", "rna"} else None,
        "starts_with": cleaned[:30],
        "ends_with": cleaned[-30:] if cleaned else "",
        "composition": dict(sorted(counts.items())),
    }


def wrap_fasta(header: str, sequence: str, width: int = 80) -> str:
    cleaned = clean_sequence(sequence)
    lines = [f">{header}"]
    lines.extend(cleaned[index : index + width] for index in range(0, len(cleaned), width))
    return "\n".join(lines)

"""Identifier-type detection for gene/protein identifiers.

Given a single raw string, decide what *kind* of identifier it most likely is.
Detection is purely syntactic (regex-based) and never touches the HGNC data;
the resolver is responsible for confirming a value actually exists.

Detected types
--------------
``hgnc_id``, ``ensembl_gene``, ``ensembl_transcript``, ``ensembl_protein``,
``refseq``, ``uniprot``, ``entrez``, ``symbol`` (the catch-all for things that
look like gene symbols), and ``unknown`` for empty / unrecognisable input.
"""

from __future__ import annotations

import re

# --- regexes -----------------------------------------------------------------

_HGNC_ID = re.compile(r"^HGNC:\d+$", re.IGNORECASE)
_ENSEMBL_GENE = re.compile(r"^ENSG\d{6,}(\.\d+)?$", re.IGNORECASE)
_ENSEMBL_TRANSCRIPT = re.compile(r"^ENST\d{6,}(\.\d+)?$", re.IGNORECASE)
_ENSEMBL_PROTEIN = re.compile(r"^ENSP\d{6,}(\.\d+)?$", re.IGNORECASE)
# RefSeq: NM_/NR_/XM_/XR_ (RNA), NP_/XP_ (protein), NG_/NC_/NT_/NW_ (genomic)
_REFSEQ = re.compile(r"^(N|X)(M|R|P|G|C|T|W)_\d+(\.\d+)?$", re.IGNORECASE)
# Entrez / NCBI Gene IDs are bare integers.
_ENTREZ = re.compile(r"^\d+$")
# UniProt accession (the official pattern, 6 or 10 chars).
_UNIPROT = re.compile(
    r"^([OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2})$"
)
# Gene-symbol-ish: letters/digits with optional - . _ separators, starts alpha.
_SYMBOL = re.compile(r"^[A-Za-z][A-Za-z0-9\-\._@/]*$")

# Public ordering used when reporting / iterating types.
ID_TYPES = (
    "hgnc_id",
    "ensembl_gene",
    "ensembl_transcript",
    "ensembl_protein",
    "refseq",
    "uniprot",
    "entrez",
    "symbol",
    "unknown",
)


def normalize_value(value) -> str:
    """Trim surrounding whitespace and normalise unicode-ish noise to a str.

    Does *not* change case (symbols are matched case-insensitively downstream)
    and does *not* strip internal characters.
    """
    if value is None:
        return ""
    s = str(value)
    # Collapse non-breaking spaces and trim.
    s = s.replace(" ", " ").strip()
    return s


def detect_type(value) -> str:
    """Return the most likely identifier type for a single value."""
    s = normalize_value(value)
    if not s:
        return "unknown"

    if _HGNC_ID.match(s):
        return "hgnc_id"
    if _ENSEMBL_GENE.match(s):
        return "ensembl_gene"
    if _ENSEMBL_TRANSCRIPT.match(s):
        return "ensembl_transcript"
    if _ENSEMBL_PROTEIN.match(s):
        return "ensembl_protein"
    if _REFSEQ.match(s):
        return "refseq"
    if _ENTREZ.match(s):
        return "entrez"
    # UniProt must be checked before the generic symbol rule because accessions
    # like "P04637" also satisfy the symbol pattern.
    if _UNIPROT.match(s):
        return "uniprot"
    if _SYMBOL.match(s):
        return "symbol"
    return "unknown"


def is_symbol_like(value) -> bool:
    """True if the value looks like a gene symbol (used by the resolver)."""
    return detect_type(value) == "symbol"

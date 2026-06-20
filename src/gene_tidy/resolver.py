"""Resolve a single identifier to an HGNC gene, with explicit ambiguity.

Core rule: *never guess silently*. Every value is resolved to exactly one of:

    matched / matched_alias / matched_prev / recovered_excel  -> clean
    ambiguous                                                 -> needs review
    unmatched / empty                                         -> failed

Ambiguous (one-to-many) and unmatched values are always flagged with a warning
and never silently collapsed to a single answer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import List, Optional

from .detect import detect_type, normalize_value
from .excel_fix import detect_excel_corruption
from .hgnc import GeneRecord, HgncData

# match_status -> output bucket
CLEAN_STATUSES = {"matched", "matched_alias", "matched_prev", "recovered_excel"}
AMBIGUOUS_STATUSES = {"ambiguous"}
FAILED_STATUSES = {"unmatched", "empty"}

# Maps the internal source_used token for a typed lookup to the HGNC field name.
_SOURCE_TO_FIELD = {
    "hgnc_id": "hgnc_id",
    "hgnc_ensembl_gene_id": "ensembl_gene_id",
    "hgnc_refseq": "refseq_accession",
    "hgnc_uniprot": "uniprot_ids",
    "hgnc_entrez": "entrez_id",
}


@dataclass
class ResolveResult:
    input_value: str = ""
    detected_type: str = "unknown"
    approved_symbol: str = ""
    hgnc_id: str = ""
    ensembl_gene_id: str = ""
    uniprot_id: str = ""
    entrez_id: str = ""
    refseq_id: str = ""
    match_status: str = "unmatched"
    warning: str = ""
    source_used: str = "none"
    manual_review_required: bool = True
    # Provenance for the mapping audit.
    matched_field: str = ""
    match_reason: str = ""
    candidate_count: int = 0

    def to_dict(self) -> dict:
        d = asdict(self)
        # Emit the boolean as a stable lowercase string for CSV/XLSX clarity.
        d["manual_review_required"] = bool(self.manual_review_required)
        return d

    @property
    def bucket(self) -> str:
        if self.match_status in CLEAN_STATUSES:
            return "clean"
        if self.match_status in AMBIGUOUS_STATUSES:
            return "ambiguous"
        return "failed"


def _fill_from_record(res: ResolveResult, rec: GeneRecord) -> None:
    res.approved_symbol = rec.symbol
    res.hgnc_id = rec.hgnc_id
    res.ensembl_gene_id = rec.ensembl_gene_id
    res.uniprot_id = rec.uniprot_id
    res.entrez_id = rec.entrez_id
    res.refseq_id = rec.refseq_id


def _dedupe_records(records: List[GeneRecord]) -> List[GeneRecord]:
    seen = set()
    out = []
    for r in records:
        key = r.hgnc_id or r.symbol
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def _alias_prev_candidates(key: str, hgnc: HgncData) -> List[GeneRecord]:
    """All distinct genes that list ``key`` as an alias or previous symbol."""
    alias_recs = hgnc.by_alias.get(key, [])
    prev_recs = hgnc.by_prev.get(key, [])
    return _dedupe_records(list(alias_recs) + list(prev_recs))


def _resolve_symbol(value: str, hgnc: HgncData, res: ResolveResult) -> bool:
    """Resolve a symbol-like value via approved / alias / prev. Returns True
    if a terminal status (matched*/ambiguous) was set."""
    key = value.upper()

    # 1. Exact approved symbol -- the most confident outcome.
    rec = hgnc.by_symbol.get(key)
    if rec is not None:
        _fill_from_record(res, rec)
        res.match_status = "matched"
        res.source_used = "hgnc_approved_symbol"
        res.matched_field = "symbol"
        res.match_reason = "exact approved symbol"
        res.candidate_count = 1
        res.manual_review_required = False
        return True

    # 2. Gather alias + prev candidates (a value can be both).
    candidates = _alias_prev_candidates(key, hgnc)

    if len(candidates) == 1:
        rec = candidates[0]
        _fill_from_record(res, rec)
        res.candidate_count = 1
        if key in {a.upper() for a in rec.aliases} and key not in {
            p.upper() for p in rec.prev_symbols
        }:
            res.match_status = "matched_alias"
            res.source_used = "hgnc_alias_symbol"
            res.matched_field = "alias_symbol"
            res.match_reason = "resolved via alias symbol"
            res.warning = f"resolved from alias {value} -> {rec.symbol}"
        else:
            res.match_status = "matched_prev"
            res.source_used = "hgnc_prev_symbol"
            res.matched_field = "prev_symbol"
            res.match_reason = "resolved via previous symbol"
            res.warning = f"resolved from previous symbol {value} -> {rec.symbol}"
        res.manual_review_required = False
        return True

    if len(candidates) > 1:
        syms = sorted({r.symbol for r in candidates})
        res.approved_symbol = ";".join(syms)
        res.match_status = "ambiguous"
        res.source_used = "hgnc_alias_symbol/hgnc_prev_symbol"
        res.matched_field = "alias_symbol/prev_symbol"
        res.match_reason = f"ambiguous: {len(candidates)} candidate genes"
        res.candidate_count = len(candidates)
        res.warning = (
            f"'{value}' is ambiguous; maps to multiple approved symbols: "
            f"{', '.join(syms)}"
        )
        res.manual_review_required = True
        return True

    return False


def _resolve_excel(value: str, hgnc: HgncData, res: ResolveResult) -> bool:
    """Handle Excel date-corrupted values. Returns True if handled here."""
    fix = detect_excel_corruption(value)
    if fix is None:
        return False

    res.detected_type = "excel_corrupted"
    # Resolve every candidate symbol against HGNC (approved/alias/prev).
    resolved: List[GeneRecord] = []
    for cand in fix.candidates:
        ckey = cand.upper()
        approved = hgnc.by_symbol.get(ckey)
        if approved is not None:
            resolved.append(approved)
        else:
            resolved.extend(_alias_prev_candidates(ckey, hgnc))
    resolved = _dedupe_records(resolved)

    if len(resolved) == 1:
        rec = resolved[0]
        _fill_from_record(res, rec)
        res.match_status = "recovered_excel"
        res.source_used = "excel_recovery+hgnc"
        res.matched_field = "excel_recovery"
        res.match_reason = "Excel date-corruption recovered to a single gene"
        res.candidate_count = 1
        res.warning = f"{fix.warning}; resolved to {rec.symbol}"
        res.manual_review_required = False
        return True

    if len(resolved) > 1:
        syms = sorted({r.symbol for r in resolved})
        res.approved_symbol = ";".join(syms)
        res.match_status = "ambiguous"
        res.source_used = "excel_recovery+hgnc"
        res.matched_field = "excel_recovery"
        res.match_reason = (
            f"Excel date-corruption recovered but ambiguous: "
            f"{len(resolved)} candidate genes"
        )
        res.candidate_count = len(resolved)
        res.warning = (
            f"{fix.warning}; recovered candidates resolve to multiple genes: "
            f"{', '.join(syms)}"
        )
        res.manual_review_required = True
        return True

    # Looked corrupted but no candidate exists in this HGNC dump.
    res.match_status = "unmatched"
    res.source_used = "excel_recovery"
    res.matched_field = ""
    res.match_reason = "Excel date-corruption suspected but no candidate in HGNC dump"
    res.candidate_count = 0
    res.warning = (
        f"{fix.warning}; none of the recovered candidates "
        f"({', '.join(fix.candidates)}) found in HGNC dump"
    )
    res.manual_review_required = True
    return True


def resolve_value(value, hgnc: HgncData) -> ResolveResult:
    """Resolve a single (already-split) identifier value."""
    raw = normalize_value(value)
    res = ResolveResult(input_value=raw)

    if not raw:
        res.detected_type = "unknown"
        res.match_status = "empty"
        res.source_used = "none"
        res.match_reason = "empty value"
        res.candidate_count = 0
        res.warning = "empty value"
        res.manual_review_required = False
        return res

    # Excel corruption is checked first because corrupted forms masquerade as
    # other types (e.g. "Sep-2" looks symbol-ish, "2-Sep" looks unknown).
    if _resolve_excel(raw, hgnc, res):
        return res

    dtype = detect_type(raw)
    res.detected_type = dtype

    rec: Optional[GeneRecord] = None
    source = "none"

    if dtype == "hgnc_id":
        rec = hgnc.by_hgnc_id.get(raw.upper())
        source = "hgnc_id"
    elif dtype == "ensembl_gene":
        rec = hgnc.by_ensembl_gene.get(raw.upper()) or hgnc.by_ensembl_gene.get(
            raw.split(".")[0].upper()
        )
        source = "hgnc_ensembl_gene_id"
    elif dtype == "refseq":
        rec = hgnc.by_refseq.get(raw.upper()) or hgnc.by_refseq.get(
            raw.split(".")[0].upper()
        )
        source = "hgnc_refseq"
    elif dtype == "uniprot":
        rec = hgnc.by_uniprot.get(raw.upper())
        source = "hgnc_uniprot"
    elif dtype == "entrez":
        rec = hgnc.by_entrez.get(raw)
        source = "hgnc_entrez"
    elif dtype in ("ensembl_transcript", "ensembl_protein"):
        # Gene-level dump cannot map transcript/protein-level Ensembl IDs.
        res.match_status = "unmatched"
        res.source_used = "none"
        res.match_reason = "unsupported id type for offline gene-level dump"
        res.candidate_count = 0
        res.warning = (
            f"{dtype} resolution requires transcript-level data not present "
            f"in the offline HGNC gene dump; left for manual review"
        )
        res.manual_review_required = True
        return res

    if rec is not None:
        _fill_from_record(res, rec)
        res.match_status = "matched"
        res.source_used = source
        res.matched_field = _SOURCE_TO_FIELD.get(source, "")
        res.match_reason = f"matched on {res.matched_field or source}"
        res.candidate_count = 1
        res.manual_review_required = False
        return res

    # Symbol resolution (primary path for symbols, fallback for everything
    # else in case the type was mis-detected, e.g. a symbol shaped like an
    # accession).
    if _resolve_symbol(raw, hgnc, res):
        return res

    # Nothing matched.
    res.match_status = "unmatched"
    res.source_used = "none"
    res.matched_field = ""
    res.match_reason = "no HGNC match"
    res.candidate_count = 0
    if not res.warning:
        res.warning = f"no HGNC match for '{raw}' (detected type: {dtype})"
    res.manual_review_required = True
    return res

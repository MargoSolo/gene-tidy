"""End-to-end orchestration: messy table in -> audited clean outputs out."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

import pandas as pd

from .columns import detect_id_columns
from .hgnc import HgncData, hgnc_version_info, load_hgnc
from .io import read_table, split_cell, write_outputs
from .resolver import resolve_value

# Traceability columns are prepended; the required output schema follows.
TRACE_COLUMNS = ["source_row", "source_column"]
REQUIRED_COLUMNS = [
    "input_value",
    "detected_type",
    "approved_symbol",
    "hgnc_id",
    "ensembl_gene_id",
    "uniprot_id",
    "entrez_id",
    "refseq_id",
    "match_status",
    "warning",
    "source_used",
    "manual_review_required",
]
# Per-row provenance, included in every output table.
PROVENANCE_COLUMNS = ["matched_field", "match_reason", "candidate_count"]
OUTPUT_COLUMNS = TRACE_COLUMNS + REQUIRED_COLUMNS + PROVENANCE_COLUMNS
# Run-level provenance, added to the full mapping audit only.
AUDIT_EXTRA_COLUMNS = ["hgnc_dump_date", "gene_tidy_version"]
AUDIT_COLUMNS = OUTPUT_COLUMNS + AUDIT_EXTRA_COLUMNS

# gene-tidy version, kept in sync with __init__.__version__.
TOOL_VERSION = "0.1.0"


@dataclass
class TidyResult:
    """Result of a tidy run: the four tables plus metadata."""

    clean: pd.DataFrame
    failed: pd.DataFrame
    ambiguous: pd.DataFrame
    audit: pd.DataFrame
    methods_text: str
    hgnc_version: dict
    id_columns: List[str]
    output_paths: Optional[dict] = None

    @property
    def counts(self) -> dict:
        return {
            "total": len(self.audit),
            "clean": len(self.clean),
            "ambiguous": len(self.ambiguous),
            "failed": len(self.failed),
        }


def _build_methods_text(version: dict, counts: dict, id_columns: Sequence[str]) -> str:
    release = version.get("hgnc_release", "unknown")
    date = version.get("downloaded_date", "unknown")
    source = version.get("source", "HGNC complete set")
    source_path = version.get("source_path")
    cols = ", ".join(id_columns) if id_columns else "auto-detected column(s)"
    # Surface the data boundary explicitly: which HGNC file and that only
    # status=='Approved' entries were used (relevant for --hgnc-file overrides).
    boundary = (
        f"Only HGNC entries with status 'Approved' were used; any "
        f"non-Approved entries (e.g. withdrawn symbols) were excluded."
    )
    if source_path:
        boundary += f" HGNC source file: {source_path}."
    return (
        "Methods\n"
        "-------\n"
        f"Gene and protein identifiers were standardised using gene-tidy "
        f"v{TOOL_VERSION}, a Python tool that maps identifiers to current HGNC "
        f"approved symbols and cross-references (Ensembl, UniProt, Entrez, "
        f"RefSeq). Identifiers were resolved against {source} "
        f"(release {release}, retrieved {date}) using approved symbol, alias "
        f"symbol, and previous symbol fields. {boundary} Identifier column(s) "
        f"processed: {cols}. Excel date-corrupted gene symbols (e.g. SEPT2 -> "
        f"'2-Sep', MARCH1 -> '1-Mar') were detected and recovered where "
        f"unambiguous and flagged otherwise. Of {counts['total']} input "
        f"identifier(s), {counts['clean']} were resolved to a single approved "
        f"symbol, {counts['ambiguous']} were one-to-many or otherwise ambiguous "
        f"and routed to manual review, and {counts['failed']} could not be "
        f"matched. No input rows were dropped; ambiguous and unmatched "
        f"identifiers were written to separate files for transparency. "
        f"Resolution was performed fully offline with no live API calls.\n"
    )


def tidy_dataframe(
    df: pd.DataFrame,
    id_columns: Optional[Sequence[str]] = None,
    hgnc: Optional[HgncData] = None,
    *,
    source: Optional[str] = None,
) -> TidyResult:
    """Resolve every identifier in ``df`` and split into clean/ambiguous/failed.

    Parameters
    ----------
    df: the input table (any columns).
    id_columns: which column(s) hold identifiers; auto-detected when omitted.
    hgnc: a preloaded :class:`HgncData` (loaded from the bundled dump if None).
    source: optional explicit HGNC file path (passed to :func:`load_hgnc`).
    """
    if hgnc is None:
        hgnc = load_hgnc(source)

    if id_columns is None:
        id_columns = detect_id_columns(df, hgnc=hgnc)
    id_columns = [c for c in id_columns if c in df.columns] or list(df.columns[:1])

    rows: List[dict] = []
    # Track duplicates by normalised input value.
    seen_count: dict = {}

    for row_idx in range(len(df)):
        for col in id_columns:
            cell = df.iloc[row_idx][col]
            for token in split_cell(cell):
                res = resolve_value(token, hgnc)
                record = {"source_row": row_idx, "source_column": col}
                record.update(res.to_dict())
                key = record["input_value"].upper()
                if key:
                    seen_count[key] = seen_count.get(key, 0) + 1
                rows.append((key, record))

    # Second pass: annotate duplicates (kept, never dropped).
    final_rows: List[dict] = []
    for key, record in rows:
        if key and seen_count.get(key, 0) > 1:
            note = f"duplicate input value (appears {seen_count[key]} times)"
            record["warning"] = (record["warning"] + "; " + note).lstrip("; ") \
                if record["warning"] else note
        final_rows.append(record)

    version = hgnc.version or hgnc_version_info()
    dump_date = version.get("downloaded_date", "unknown")

    if final_rows:
        base = pd.DataFrame(final_rows)[OUTPUT_COLUMNS]
    else:
        base = pd.DataFrame(columns=OUTPUT_COLUMNS)

    clean = base[base["match_status"].isin(
        ["matched", "matched_alias", "matched_prev", "recovered_excel"]
    )].reset_index(drop=True)
    ambiguous = base[base["match_status"] == "ambiguous"].reset_index(drop=True)
    failed = base[base["match_status"].isin(["unmatched", "empty"])].reset_index(drop=True)

    # The full audit adds run-level provenance columns.
    audit = base.copy()
    audit["hgnc_dump_date"] = dump_date
    audit["gene_tidy_version"] = TOOL_VERSION
    audit = audit[AUDIT_COLUMNS].reset_index(drop=True)

    counts = {
        "total": len(audit),
        "clean": len(clean),
        "ambiguous": len(ambiguous),
        "failed": len(failed),
    }
    methods = _build_methods_text(version, counts, id_columns)

    return TidyResult(
        clean=clean,
        failed=failed,
        ambiguous=ambiguous,
        audit=audit,
        methods_text=methods,
        hgnc_version=version,
        id_columns=list(id_columns),
    )


def tidy_values(
    values: Sequence,
    hgnc: Optional[HgncData] = None,
    *,
    source: Optional[str] = None,
) -> TidyResult:
    """Convenience: tidy a flat list of identifier strings."""
    df = pd.DataFrame({"input": [("" if v is None else str(v)) for v in values]})
    return tidy_dataframe(df, id_columns=["input"], hgnc=hgnc, source=source)


def tidy_file(
    input_path,
    out_dir,
    id_columns: Optional[Sequence[str]] = None,
    *,
    source: Optional[str] = None,
    write: bool = True,
) -> TidyResult:
    """Read a file, tidy it, and (by default) write the six output files."""
    df = read_table(input_path)
    result = tidy_dataframe(df, id_columns=id_columns, source=source)
    if write:
        result.output_paths = write_outputs(result, out_dir)
    return result

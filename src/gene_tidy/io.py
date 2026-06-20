"""Reading input tables and writing the gene-tidy output files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

import pandas as pd

from .detect import detect_type
from .columns import _NAME_HINTS

_REAL_ID_TYPES = {
    "symbol", "ensembl_gene", "ensembl_transcript", "ensembl_protein",
    "uniprot", "refseq", "hgnc_id",
}


def _stringify(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce every cell to a trimmed string; NaN -> ''."""
    out = df.copy()
    for col in out.columns:
        out[col] = (
            out[col]
            .astype("object")
            .map(lambda v: "" if (v is None or (isinstance(v, float) and pd.isna(v)))
                 else str(v).strip())
        )
    out.columns = [str(c).strip() for c in out.columns]
    return out


def _header_name_is_label(name: str) -> bool:
    """True if a column name looks like a *label* (header) rather than data."""
    h = re.sub(r"[^a-z0-9]", "", str(name).lower())
    if not h:
        return True
    if any(hint in h for hint in _NAME_HINTS):
        return True
    # If it doesn't look like a real identifier, it's probably a label.
    return detect_type(name) not in _REAL_ID_TYPES


def _maybe_fix_headerless(df: pd.DataFrame) -> pd.DataFrame:
    """If a single-column file's 'header' is actually a gene id, recover it."""
    if df.shape[1] == 1:
        header = df.columns[0]
        if not _header_name_is_label(header):
            # The header is really the first data value.
            recovered = pd.DataFrame({"input": [header] + df.iloc[:, 0].tolist()})
            return recovered
    return df


def read_table(path) -> pd.DataFrame:
    """Read a TXT / CSV / TSV / XLSX file into an all-string DataFrame."""
    path = Path(path)
    ext = path.suffix.lower()

    if ext in (".xlsx", ".xls", ".xlsm"):
        df = pd.read_excel(path, dtype=str)
        df = _maybe_fix_headerless(_stringify(df))
    elif ext in (".csv",):
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
        df = _maybe_fix_headerless(_stringify(df))
    elif ext in (".tsv", ".tab"):
        df = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)
        df = _maybe_fix_headerless(_stringify(df))
    else:
        # .txt or unknown: sniff the delimiter; we name a synthetic header
        # ourselves, so the headerless-recovery heuristic is not applied.
        df = _read_text(path)

    return _stringify(df)


def _read_text(path: Path) -> pd.DataFrame:
    raw = Path(path).read_text(encoding="utf-8-sig").splitlines()
    raw = [line for line in raw if line.strip() != ""]
    if not raw:
        return pd.DataFrame({"input": []})

    first = raw[0]
    if "\t" in first:
        sep = "\t"
    elif "," in first:
        sep = ","
    else:
        sep = None  # single column

    if sep is None:
        return pd.DataFrame({"input": [line.strip() for line in raw]})

    return pd.read_csv(path, sep=sep, dtype=str, keep_default_na=False)


def split_cell(value: str) -> List[str]:
    """Split a cell that may hold several identifiers (comma/semicolon/pipe)."""
    s = "" if value is None else str(value).strip()
    if not s:
        return [""]
    parts = re.split(r"[;,|]", s)
    parts = [p.strip() for p in parts]
    parts = [p for p in parts if p != ""]
    return parts if parts else [""]


# --- writing -----------------------------------------------------------------

def write_outputs(result, out_dir) -> dict:
    """Write the six gene-tidy output files. Returns a name->path mapping."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "clean_xlsx": out_dir / "clean_table.xlsx",
        "clean_csv": out_dir / "clean_table.csv",
        "failed_csv": out_dir / "failed_rows.csv",
        "ambiguous_csv": out_dir / "ambiguous_rows.csv",
        "audit_csv": out_dir / "mapping_audit.csv",
        "methods_txt": out_dir / "methods_text.txt",
    }

    result.clean.to_csv(paths["clean_csv"], index=False)
    result.clean.to_excel(paths["clean_xlsx"], index=False)
    result.failed.to_csv(paths["failed_csv"], index=False)
    result.ambiguous.to_csv(paths["ambiguous_csv"], index=False)
    result.audit.to_csv(paths["audit_csv"], index=False)
    paths["methods_txt"].write_text(result.methods_text, encoding="utf-8")

    return {k: str(v) for k, v in paths.items()}

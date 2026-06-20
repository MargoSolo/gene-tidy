"""Bundled example data for gene-tidy demos and the Colab notebook."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

EXAMPLE_PATH = Path(__file__).resolve().parent / "messy_example.xlsx"

# A deliberately messy table exercising every edge case gene-tidy handles.
# Columns mimic a typical differential-expression supplementary table.
EXAMPLE_ROWS = [
    # gene_symbol,        logFC,  p_value   -- comment
    ("TP53", 2.41, 0.0001),          # approved symbol
    ("  tp53 ", 2.39, 0.0002),       # whitespace + case + duplicate
    ("p53", 1.80, 0.003),            # alias -> TP53
    ("HER2", 3.10, 0.00005),         # alias -> ERBB2
    ("FRAP1", -1.20, 0.01),          # previous symbol -> MTOR
    ("VEGF", 1.05, 0.04),            # previous symbol -> VEGFA
    ("ERBB", 0.90, 0.05),            # previous symbol -> EGFR
    ("2-Sep", 1.33, 0.02),           # Excel corruption -> SEPT2 -> AMBIGUOUS (SEPTIN2/SEPTIN6)
    ("Sep-7", 0.75, 0.06),           # Excel corruption -> SEPT7 -> SEPTIN7 (clean)
    ("1-Mar", -0.60, 0.07),          # Excel corruption -> AMBIGUOUS MARCHF1/MTARC1
    ("1-Dec", 0.50, 0.08),           # Excel corruption -> DEC1 -> AMBIGUOUS (BHLHE40/DELEC1)
    ("KRAS, NRAS", 2.00, 0.001),     # multiple IDs in one cell
    ("ENSG00000141510", 2.20, 0.002),# Ensembl gene id -> TP53
    ("P38398", 1.95, 0.004),         # UniProt -> BRCA1
    ("672", 1.50, 0.006),            # Entrez -> BRCA1
    ("NM_000546", 2.10, 0.003),      # RefSeq -> TP53
    ("HGNC:11998", 2.05, 0.004),     # HGNC id -> TP53
    ("egfr", 1.10, 0.02),            # case variation -> EGFR
    ("FOOBAR1", 0.30, 0.5),          # unmatched
    ("", 0.00, 1.0),                 # empty value
]

EXAMPLE_COLUMNS = ["gene_symbol", "logFC", "p_value"]


def build_example_dataframe() -> pd.DataFrame:
    return pd.DataFrame(EXAMPLE_ROWS, columns=EXAMPLE_COLUMNS)


def write_example(path=EXAMPLE_PATH) -> Path:
    """(Re)generate the bundled messy_example.xlsx."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    build_example_dataframe().to_excel(path, index=False)
    return path


if __name__ == "__main__":
    p = write_example()
    print(f"Wrote {p}")

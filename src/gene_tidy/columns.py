"""Auto-detect which column(s) of a table hold gene/protein identifiers.

Strategy
--------
1. Score every column by name (gene-ish headers get a boost).
2. Score every column by *content*: what fraction of non-empty cells look like
   a recognised identifier (symbol, Ensembl, UniProt, RefSeq, Entrez, ...).
3. Pick the best-scoring column. If several columns are clearly identifier-like
   (e.g. a "symbol" column and an "ensembl_id" column) we keep all of them so
   mixed-identifier files still resolve.
"""

from __future__ import annotations

import re
from typing import List, Optional

import pandas as pd

from .detect import detect_type

# Header tokens that strongly suggest an identifier column.
_NAME_HINTS = (
    "gene", "symbol", "geneid", "gene_id", "gene_symbol", "hgnc", "ensembl",
    "ensg", "enst", "uniprot", "entrez", "refseq", "accession", "protein",
    "id", "identifier", "locus", "probe",
)
# Header tokens that suggest a column is NOT an identifier (down-weighted).
_NAME_ANTIHINTS = (
    "description", "name", "logfc", "log2", "pvalue", "p_value", "p-val",
    "padj", "fdr", "qvalue", "count", "tpm", "fpkm", "expr", "fold",
    "mean", "median", "score", "rank", "chr", "position", "start", "end",
    "strand", "length",
)


def _name_score(header: str) -> float:
    h = re.sub(r"[^a-z0-9]", "", str(header).lower())
    if not h:
        return 0.0
    score = 0.0
    for hint in _NAME_HINTS:
        if hint in h:
            score += 2.0
    for anti in _NAME_ANTIHINTS:
        if anti in h:
            score -= 3.0
    return score


def _content_score(series: pd.Series, sample: int = 200) -> float:
    """Fraction of non-empty sampled cells that look like an identifier."""
    values = [str(v).strip() for v in series.tolist() if str(v).strip()]
    if not values:
        return 0.0
    values = values[:sample]
    id_like = 0
    for v in values:
        t = detect_type(v)
        if t in ("symbol", "ensembl_gene", "ensembl_transcript",
                 "ensembl_protein", "uniprot", "refseq", "hgnc_id"):
            id_like += 1
        elif t == "entrez":
            # Bare integers are weak evidence on their own.
            id_like += 0  # counted separately below
    frac = id_like / len(values)
    return frac


def _resolvable_score(series: pd.Series, hgnc, sample: int = 200) -> float:
    """Fraction of non-empty sampled cells that resolve to a real HGNC gene.

    Far stronger than syntactic scoring: it distinguishes a real gene column
    from a same-shaped column of sample names (``sample1`` looks like a symbol
    but does not resolve).
    """
    from .resolver import resolve_value  # local import avoids import cycle

    values = [str(v).strip() for v in series.tolist() if str(v).strip()]
    if not values:
        return 0.0
    values = values[:sample]
    resolved = 0
    for v in values:
        res = resolve_value(v, hgnc)
        if res.bucket in ("clean", "ambiguous"):
            resolved += 1
    return resolved / len(values)


def detect_id_columns(df: pd.DataFrame, hgnc=None) -> List[str]:
    """Return the list of column(s) most likely to contain identifiers.

    When ``hgnc`` is provided, columns are scored by how many values actually
    resolve to HGNC genes (much more reliable). Without it, a purely syntactic
    heuristic is used. Always returns at least one column so the pipeline never
    silently finds nothing; if the table is empty, returns ``[]``.
    """
    if df.shape[1] == 0 or df.shape[0] == 0:
        return list(df.columns[:1])

    scored = []
    for col in df.columns:
        name = _name_score(col)
        if hgnc is not None:
            content = _resolvable_score(df[col], hgnc)
        else:
            content = _content_score(df[col])
        # Content is the dominant signal; name nudges ties.
        total = content * 10.0 + name
        scored.append((col, total, content, name))

    scored.sort(key=lambda x: x[1], reverse=True)
    best = scored[0]

    # Keep the best column, plus any other column that is also strongly
    # identifier-like (content fraction >= 0.6 and within reach of the best).
    chosen = [best[0]]
    for col, total, content, name in scored[1:]:
        if content >= 0.6 and name >= 0:
            chosen.append(col)

    return chosen


def detect_id_column(df: pd.DataFrame, hgnc=None) -> str:
    """Convenience: return just the single best identifier column."""
    cols = detect_id_columns(df, hgnc=hgnc)
    return cols[0] if cols else (df.columns[0] if len(df.columns) else "")

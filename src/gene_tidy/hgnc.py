"""Load the bundled (or user-supplied) HGNC dump into fast lookup indices.

Resolution is fully offline by default: a curated subset of the HGNC complete
set ships inside the package (``data/hgnc_subset.tsv``). Power users can point
``GENE_TIDY_HGNC_FILE`` at a full ``hgnc_complete_set.txt`` (same column
headers) or call :func:`cache_full_hgnc` once to download and cache it.

The loader is format-compatible with the official HGNC complete set, reading
the columns: ``hgnc_id``, ``symbol``, ``alias_symbol``, ``prev_symbol``,
``ensembl_gene_id``, ``uniprot_ids``, ``entrez_id``, ``refseq_accession``.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

_DATA_DIR = Path(__file__).resolve().parent / "data"
# Default runtime source: the bundled static HGNC complete set (all Approved
# gene records), gzipped so the wheel stays small. Resolution is fully offline.
_BUNDLED_COMPLETE_SET = _DATA_DIR / "hgnc_complete_set.tsv.gz"
_VERSION_JSON = _DATA_DIR / "hgnc_version.json"

# Columns we read from an HGNC-complete-set-style file.
_USED_COLUMNS = (
    "hgnc_id", "symbol", "alias_symbol", "prev_symbol",
    "ensembl_gene_id", "uniprot_ids", "entrez_id", "refseq_accession",
)


def _clean(value) -> str:
    """Normalise a single cell value to a trimmed string ('' if empty)."""
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    s = str(value).strip()
    if s.lower() in ("", "nan", "none"):
        return ""
    return s


def _split_multi(value) -> List[str]:
    """Split an HGNC pipe-separated field into a clean list of tokens."""
    s = _clean(value)
    if not s:
        return []
    parts = [p.strip() for p in s.split("|")]
    return [p for p in parts if p]


@dataclass
class GeneRecord:
    """A single resolved HGNC gene with its cross-references."""

    hgnc_id: str = ""
    symbol: str = ""
    aliases: List[str] = field(default_factory=list)
    prev_symbols: List[str] = field(default_factory=list)
    ensembl_gene_id: str = ""
    uniprot_ids: List[str] = field(default_factory=list)
    entrez_id: str = ""
    refseq_id: str = ""

    @property
    def uniprot_id(self) -> str:
        return self.uniprot_ids[0] if self.uniprot_ids else ""


class HgncData:
    """In-memory HGNC index supporting lookups by every identifier type."""

    def __init__(self, records: List[GeneRecord], version: Dict):
        self.records = records
        self.version = version

        self.by_symbol: Dict[str, GeneRecord] = {}
        self.by_alias: Dict[str, List[GeneRecord]] = {}
        self.by_prev: Dict[str, List[GeneRecord]] = {}
        self.by_ensembl_gene: Dict[str, GeneRecord] = {}
        self.by_uniprot: Dict[str, GeneRecord] = {}
        self.by_entrez: Dict[str, GeneRecord] = {}
        self.by_refseq: Dict[str, GeneRecord] = {}
        self.by_hgnc_id: Dict[str, GeneRecord] = {}

        for rec in records:
            if rec.symbol:
                self.by_symbol[rec.symbol.upper()] = rec
            for a in rec.aliases:
                self.by_alias.setdefault(a.upper(), []).append(rec)
            for p in rec.prev_symbols:
                self.by_prev.setdefault(p.upper(), []).append(rec)
            if rec.ensembl_gene_id:
                # Index without version suffix too.
                self.by_ensembl_gene[rec.ensembl_gene_id.upper()] = rec
                self.by_ensembl_gene[rec.ensembl_gene_id.split(".")[0].upper()] = rec
            for u in rec.uniprot_ids:
                self.by_uniprot[u.upper()] = rec
            if rec.entrez_id:
                self.by_entrez[rec.entrez_id] = rec
            if rec.refseq_id:
                self.by_refseq[rec.refseq_id.upper()] = rec
                self.by_refseq[rec.refseq_id.split(".")[0].upper()] = rec
            if rec.hgnc_id:
                self.by_hgnc_id[rec.hgnc_id.upper()] = rec

    def __len__(self) -> int:
        return len(self.records)


def _records_from_dataframe(df: pd.DataFrame) -> List[GeneRecord]:
    # If a user supplies a full HGNC complete set, keep only Approved entries
    # (the bundled dump is already filtered, so this is a no-op there).
    if "status" in df.columns:
        df = df[df["status"].astype(str).str.strip() == "Approved"]
    # Be tolerant of files that lack some optional columns.
    cols = {c: c for c in df.columns}
    records: List[GeneRecord] = []
    for _, row in df.iterrows():
        symbol = _clean(row.get("symbol"))
        if not symbol:
            continue
        refseq_list = _split_multi(row.get("refseq_accession")) if "refseq_accession" in cols else []
        records.append(
            GeneRecord(
                hgnc_id=_clean(row.get("hgnc_id")),
                symbol=symbol,
                aliases=_split_multi(row.get("alias_symbol")),
                prev_symbols=_split_multi(row.get("prev_symbol")),
                ensembl_gene_id=_clean(row.get("ensembl_gene_id")),
                uniprot_ids=_split_multi(row.get("uniprot_ids")),
                entrez_id=_clean(row.get("entrez_id")).split(".")[0],
                refseq_id=refseq_list[0] if refseq_list else "",
            )
        )
    return records


def _resolve_source_path() -> Path:
    """Decide which HGNC file to load (env override -> cache -> bundled)."""
    env = os.environ.get("GENE_TIDY_HGNC_FILE")
    if env:
        p = Path(env).expanduser()
        if p.exists():
            return p
        raise FileNotFoundError(
            f"GENE_TIDY_HGNC_FILE points to a missing file: {p}"
        )
    cached = cache_path()
    if cached.exists():
        return cached
    return _BUNDLED_COMPLETE_SET


def hgnc_version_info() -> Dict:
    """Return version metadata for whichever dump is in effect."""
    source = _resolve_source_path()
    if source == _BUNDLED_COMPLETE_SET:
        with open(_VERSION_JSON, "r", encoding="utf-8") as fh:
            info = json.load(fh)
    else:
        info = {
            "source": "User-supplied HGNC complete set",
            "source_url": "",
            "hgnc_release": "user-supplied",
            "downloaded_date": "unknown",
            "description": f"Loaded from {source}",
        }
    info = dict(info)
    info["source_path"] = str(source)
    return info


def _load_uncached(source: Optional[str] = None) -> HgncData:
    path = Path(source).expanduser() if source else _resolve_source_path()
    # HGNC complete set is tab-separated; keep everything as strings.
    df = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)
    records = _records_from_dataframe(df)
    version = hgnc_version_info() if source is None else {
        "source": "User-supplied HGNC complete set",
        "source_path": str(path),
        "hgnc_release": "user-supplied",
        "downloaded_date": "unknown",
    }
    return HgncData(records, version)


@lru_cache(maxsize=4)
def _load_cached(source: Optional[str]) -> HgncData:
    return _load_uncached(source)


def load_hgnc(source: Optional[str] = None, *, use_cache: bool = True) -> HgncData:
    """Load HGNC data.

    Parameters
    ----------
    source:
        Optional explicit path to an HGNC-complete-set-style TSV. When omitted,
        the env override / on-disk cache / bundled subset is used in that order.
    use_cache:
        Cache the parsed result in-process (default True).
    """
    if use_cache:
        return _load_cached(source)
    return _load_uncached(source)


# --- optional, network-only upgrade path (not used by tests) -----------------

def cache_path() -> Path:
    """Where a downloaded full HGNC complete set would be cached."""
    base = os.environ.get("GENE_TIDY_CACHE_DIR")
    if base:
        return Path(base).expanduser() / "hgnc_complete_set.txt"
    return Path.home() / ".cache" / "gene-tidy" / "hgnc_complete_set.txt"


HGNC_COMPLETE_SET_URL = (
    "https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/"
    "hgnc_complete_set.txt"
)


def cache_full_hgnc(url: str = HGNC_COMPLETE_SET_URL) -> Path:
    """Download the full HGNC complete set and cache it locally (network).

    Offline use never needs this; it only upgrades resolution coverage from the
    bundled subset to the full HGNC set. Returns the cached file path.
    """
    import urllib.request

    dest = cache_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)  # noqa: S310 (explicit user action)
    _load_cached.cache_clear()
    return dest

"""Developer-only: build the bundled HGNC complete-set dump for gene-tidy.

Run once when refreshing the bundled HGNC data. Reads (or downloads) the
official HGNC complete set, keeps the columns gene-tidy uses, filters to
Approved entries, and writes:

    src/gene_tidy/data/hgnc_complete_set.tsv.gz   (deterministic / reproducible)
    src/gene_tidy/data/hgnc_version.json          (provenance + hashes)

This script is NOT imported at runtime and NOT exercised by the test suite --
the package ships the generated .tsv.gz so end users never need network access.

Reproducibility
---------------
The gzip is written with a fixed member timestamp (mtime=0), fixed compression
level, a fixed '\\n' line terminator, and the source row order is preserved, so
the same input file always produces a byte-identical .tsv.gz. The version JSON
records both ``raw_download_sha256`` (of the input file) and
``bundled_tsv_gz_sha256`` (of the generated artifact); rebuilders can pin/verify
the data boundary by comparing these. Only ``generated_utc`` varies per run and
is excluded from the hashes.

Usage
-----
    # From an already-downloaded file (preferred; lets you pin the exact input):
    python tools/build_hgnc_data.py path/to/hgnc_complete_set.txt

    # Or fetch the current HGNC complete set (one-time developer download):
    python tools/build_hgnc_data.py --download
"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import sys
import tempfile
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
DATA_DIR = REPO / "src" / "gene_tidy" / "data"
OUT_TSV_GZ = DATA_DIR / "hgnc_complete_set.tsv.gz"
OUT_VERSION = DATA_DIR / "hgnc_version.json"

SOURCE_URL = (
    "https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/"
    "hgnc_complete_set.txt"
)

# Columns retained from the full HGNC complete set: every column gene-tidy
# resolves against, plus identity/provenance columns. All Approved HGNC records
# (rows) are kept; only unused wide columns are dropped to keep the wheel small.
KEEP_COLUMNS = [
    "hgnc_id",
    "symbol",
    "name",
    "locus_group",
    "status",
    "alias_symbol",
    "prev_symbol",
    "ensembl_gene_id",
    "uniprot_ids",
    "entrez_id",
    "refseq_accession",
]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _deterministic_gzip(payload: bytes) -> bytes:
    """Gzip ``payload`` reproducibly (no name/timestamp in the header)."""
    buf = io.BytesIO()
    # mtime=0 and a fixed compresslevel make the output byte-identical across
    # runs/platforms for the same payload. fileobj=BytesIO has no .name, so no
    # original filename is written into the gzip header.
    with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=9, mtime=0) as gz:
        gz.write(payload)
    return buf.getvalue()


def _download(url: str) -> Path:
    print(f"Downloading {url} ...")
    tmp = Path(tempfile.gettempdir()) / "hgnc_complete_set.txt"
    urllib.request.urlretrieve(url, tmp)  # noqa: S310 (explicit developer action)
    print(f"  saved to {tmp}")
    return tmp


def main(arg: str) -> None:
    if arg == "--download":
        src_path = _download(SOURCE_URL)
    else:
        src_path = Path(arg)

    raw_bytes = src_path.read_bytes()
    raw_sha = _sha256(raw_bytes)
    print(f"Reading {src_path} ...")
    df = pd.read_csv(io.BytesIO(raw_bytes), sep="\t", dtype=str, keep_default_na=False)
    total = len(df)
    print(f"  {total} rows, {df.shape[1]} columns, raw sha256={raw_sha[:12]}...")

    if "status" in df.columns:
        df = df[df["status"] == "Approved"].copy()
    approved = len(df)
    print(f"  {approved} Approved rows kept")

    keep = [c for c in KEEP_COLUMNS if c in df.columns]
    df = df[keep]

    # Serialize deterministically (fixed line terminator, preserved row order).
    tsv_text = df.to_csv(sep="\t", index=False, lineterminator="\n")
    gz_bytes = _deterministic_gzip(tsv_text.encode("utf-8"))
    gz_sha = _sha256(gz_bytes)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUT_TSV_GZ.write_bytes(gz_bytes)
    print(f"Wrote {OUT_TSV_GZ} ({len(gz_bytes) / 1e6:.2f} MB, sha256={gz_sha[:12]}...)")

    version = {
        "source": "HGNC complete set (Approved entries; core columns)",
        "source_url": SOURCE_URL,
        "hgnc_license": (
            "HGNC data are made freely available under a CC0 public-domain "
            "dedication. See https://www.genenames.org/about/license/"
        ),
        "hgnc_release": f"complete_set_{date.today().isoformat()}",
        "downloaded_date": date.today().isoformat(),
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "approved_record_count": approved,
        "record_count_total_in_source": total,
        "retained_columns": keep,
        "raw_download_sha256": raw_sha,
        "bundled_tsv_gz_sha256": gz_sha,
        "description": (
            "Static, bundled subset-of-columns of the HGNC complete set "
            "(all Approved gene records) shipped with gene-tidy so resolution "
            "works fully offline. Matched against approved symbol, alias_symbol "
            "and prev_symbol. Only status=='Approved' entries are retained. "
            "Rebuild/verify via tools/build_hgnc_data.py."
        ),
    }
    OUT_VERSION.write_text(json.dumps(version, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_VERSION}")
    print(json.dumps(version, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1])

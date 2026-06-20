"""gene-tidy: clean messy gene/protein identifier tables, fully offline.

Public API
----------
- ``tidy_file``: end-to-end cleaning of a file -> output files on disk.
- ``tidy_dataframe`` / ``tidy_values``: in-memory cleaning (handy in notebooks).
- ``OUTPUT_COLUMNS``: the canonical output schema.
"""

from .pipeline import (
    OUTPUT_COLUMNS,
    TidyResult,
    tidy_dataframe,
    tidy_file,
    tidy_values,
)
from .hgnc import HgncData, load_hgnc, hgnc_version_info

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "OUTPUT_COLUMNS",
    "TidyResult",
    "tidy_file",
    "tidy_dataframe",
    "tidy_values",
    "HgncData",
    "load_hgnc",
    "hgnc_version_info",
]

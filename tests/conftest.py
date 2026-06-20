"""Shared test fixtures.

The whole suite resolves against the small curated subset in
``tests/fixtures/hgnc_subset.tsv`` (NOT the bundled full HGNC complete set) so
tests stay fast and deterministic. The golden-output expectations assume this
subset. ``tests/test_data_boundary.py`` is the one place that exercises the real
bundled dump.
"""

import os
from pathlib import Path

import pytest

from gene_tidy.hgnc import _load_cached, load_hgnc

FIXTURE_SUBSET = Path(__file__).parent / "fixtures" / "hgnc_subset.tsv"


@pytest.fixture(scope="session", autouse=True)
def _use_fixture_hgnc():
    """Point gene-tidy's default resolution at the fixture subset for the suite."""
    prev = os.environ.get("GENE_TIDY_HGNC_FILE")
    os.environ["GENE_TIDY_HGNC_FILE"] = str(FIXTURE_SUBSET)
    _load_cached.cache_clear()
    yield
    if prev is None:
        os.environ.pop("GENE_TIDY_HGNC_FILE", None)
    else:
        os.environ["GENE_TIDY_HGNC_FILE"] = prev
    _load_cached.cache_clear()


@pytest.fixture(scope="session")
def hgnc(_use_fixture_hgnc):
    """Loaded curated subset, shared across the test session."""
    return load_hgnc(str(FIXTURE_SUBSET))

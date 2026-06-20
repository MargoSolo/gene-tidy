"""Verify the *bundled* runtime HGNC dump (the real complete set), not the
fast test fixture.

These tests load the gzipped complete set shipped inside the package directly,
bypassing the session-wide fixture override, and confirm the v0.1 data boundary:
the runtime ships a real, static HGNC complete set and resolves fully offline.
"""

import gzip
import json

import pytest

from gene_tidy.hgnc import _BUNDLED_COMPLETE_SET, _VERSION_JSON, load_hgnc
from gene_tidy.resolver import resolve_value


@pytest.fixture(scope="module")
def bundled():
    # Explicit source bypasses the GENE_TIDY_HGNC_FILE fixture override.
    return load_hgnc(str(_BUNDLED_COMPLETE_SET), use_cache=False)


def test_bundled_dump_exists_and_is_gzipped():
    assert _BUNDLED_COMPLETE_SET.exists()
    assert _BUNDLED_COMPLETE_SET.suffix == ".gz"
    # Confirm it is genuinely gzip (magic header) and tab-delimited.
    with gzip.open(_BUNDLED_COMPLETE_SET, "rt", encoding="utf-8") as fh:
        header = fh.readline()
    assert "\t" in header
    assert "symbol" in header


def test_bundled_dump_has_many_records(bundled):
    # The real complete set has tens of thousands of genes; the fixture has ~70.
    assert len(bundled) > 10000


def test_version_json_has_required_provenance():
    info = json.loads(_VERSION_JSON.read_text(encoding="utf-8"))
    for key in ("source", "source_url", "hgnc_license", "downloaded_date",
                "hgnc_release", "approved_record_count", "retained_columns",
                "raw_download_sha256", "bundled_tsv_gz_sha256"):
        assert key in info and info[key] not in ("", None)
    assert info["approved_record_count"] > 10000
    assert isinstance(info["retained_columns"], list) and info["retained_columns"]
    # CC0 license must be stated for attribution.
    assert "CC0" in info["hgnc_license"]


def test_bundled_gz_matches_recorded_hash():
    import hashlib
    info = json.loads(_VERSION_JSON.read_text(encoding="utf-8"))
    digest = hashlib.sha256(_BUNDLED_COMPLETE_SET.read_bytes()).hexdigest()
    assert digest == info["bundled_tsv_gz_sha256"], (
        "bundled hgnc_complete_set.tsv.gz does not match the sha256 recorded in "
        "hgnc_version.json -- regenerate with tools/build_hgnc_data.py"
    )


@pytest.mark.parametrize(
    "value,expected",
    [
        ("TP53", "TP53"),
        ("BRCA1", "BRCA1"),
        ("EGFR", "EGFR"),
        ("FRAP1", "MTOR"),        # previous symbol
        ("SEPT7", "SEPTIN7"),     # previous symbol (renamed family), unambiguous
    ],
)
def test_known_genes_resolve_against_bundled_dump(bundled, value, expected):
    r = resolve_value(value, bundled)
    assert r.approved_symbol == expected


def test_excel_recovery_against_bundled_dump(bundled):
    # Sep-7 -> SEPT7 -> SEPTIN7 is unambiguous in the real HGNC data.
    r = resolve_value("Sep-7", bundled)
    assert r.detected_type == "excel_corrupted"
    assert r.approved_symbol == "SEPTIN7"
    assert r.match_status == "recovered_excel"


def test_real_collision_flagged_not_guessed(bundled):
    # In the real HGNC data SEPT2 is a previous symbol of SEPTIN2 AND an alias
    # of SEPTIN6 -- a genuine one-to-many. The tool must flag, never guess.
    r = resolve_value("SEPT2", bundled)
    assert r.match_status == "ambiguous"
    assert set(r.approved_symbol.split(";")) == {"SEPTIN2", "SEPTIN6"}
    assert r.manual_review_required is True
    # The Excel-corrupted form inherits the same ambiguity.
    r2 = resolve_value("2-Sep", bundled)
    assert r2.match_status == "ambiguous"
    assert "SEPTIN2" in r2.approved_symbol


def test_bundled_dump_offline_no_network(bundled):
    # Smoke check that resolution needed no network: a fresh resolve works.
    assert resolve_value("HGNC:11998", bundled).approved_symbol == "TP53"

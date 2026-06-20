import pytest

from gene_tidy.excel_fix import (
    detect_excel_corruption,
    looks_excel_corrupted,
)


@pytest.mark.parametrize(
    "value,candidates",
    [
        ("2-Sep", ["SEPT2"]),
        ("Sep-2", ["SEPT2"]),
        ("02-Sep", ["SEPT2"]),
        ("Sep-7", ["SEPT7"]),
        ("9-Sep", ["SEPT9"]),
        ("2-September", ["SEPT2"]),
        ("1-Dec", ["DEC1"]),
        ("Dec-1", ["DEC1"]),
    ],
)
def test_unambiguous_recovery_candidates(value, candidates):
    res = detect_excel_corruption(value)
    assert res is not None
    assert res.is_corrupted
    assert res.candidates == candidates


@pytest.mark.parametrize("value", ["1-Mar", "Mar-1", "1-March", "March-1"])
def test_march_is_ambiguous(value):
    res = detect_excel_corruption(value)
    assert res is not None
    assert res.is_ambiguous
    assert set(res.candidates) == {"MARCH1", "MARC1"}


@pytest.mark.parametrize(
    "value",
    ["TP53", "BRCA1", "SEPT2", "MARCH1", "", "2-Apr", "5-HT", "2-XYZ", "ENSG00000141510"],
)
def test_non_corrupted_values_return_none(value):
    # Real symbols (even SEPT2/MARCH1 typed correctly) and unrelated date-ish
    # strings with no gene family are NOT flagged.
    assert detect_excel_corruption(value) is None
    assert not looks_excel_corrupted(value)


def test_warning_always_present_when_corrupted():
    res = detect_excel_corruption("2-Sep")
    assert "Excel date-corruption detected" in res.warning


def test_with_trailing_year():
    res = detect_excel_corruption("2-Sep-15")
    assert res is not None
    assert res.candidates == ["SEPT2"]

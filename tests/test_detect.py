import pytest

from gene_tidy.detect import detect_type, normalize_value, is_symbol_like


@pytest.mark.parametrize(
    "value,expected",
    [
        ("HGNC:11998", "hgnc_id"),
        ("hgnc:11998", "hgnc_id"),
        ("ENSG00000141510", "ensembl_gene"),
        ("ENSG00000141510.17", "ensembl_gene"),
        ("ENST00000269305", "ensembl_transcript"),
        ("ENSP00000269305", "ensembl_protein"),
        ("NM_000546", "refseq"),
        ("NM_000546.6", "refseq"),
        ("NP_000537", "refseq"),
        ("XM_011546151", "refseq"),
        ("P04637", "uniprot"),
        ("Q9BZS1", "uniprot"),
        ("A0A024RBG1", "uniprot"),
        ("7157", "entrez"),
        ("672", "entrez"),
        ("TP53", "symbol"),
        ("BRCA1", "symbol"),
        ("MARCHF1", "symbol"),
        ("C1orf112", "symbol"),
        ("", "unknown"),
        ("   ", "unknown"),
    ],
)
def test_detect_type(value, expected):
    assert detect_type(value) == expected


def test_symbol_not_confused_with_uniprot():
    # Real gene symbols that superficially resemble accessions still detect
    # as symbols where possible.
    assert detect_type("TP53") == "symbol"
    assert detect_type("S100A4") == "symbol"


def test_uniprot_before_symbol():
    # A genuine UniProt accession must win over the generic symbol rule.
    assert detect_type("P04637") == "uniprot"


def test_entrez_is_pure_digits_only():
    assert detect_type("672") == "entrez"
    assert detect_type("123abc") == "unknown"  # starts with a digit -> not a symbol
    assert detect_type("12.3") == "unknown"


def test_normalize_value_trims_and_handles_none():
    assert normalize_value("  TP53 ") == "TP53"
    assert normalize_value(None) == ""
    assert normalize_value(" TP53 ") == "TP53"


def test_is_symbol_like():
    assert is_symbol_like("TP53")
    assert not is_symbol_like("ENSG00000141510")
    assert not is_symbol_like("7157")

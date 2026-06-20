import pandas as pd

from gene_tidy.columns import detect_id_column, detect_id_columns


def test_detect_by_content_over_noise():
    df = pd.DataFrame(
        {
            "logFC": [2.1, -1.3, 0.5],
            "my_genes": ["TP53", "BRCA1", "EGFR"],
            "p_value": [0.01, 0.2, 0.04],
        }
    )
    assert detect_id_column(df) == "my_genes"


def test_detect_with_unhelpful_header_name(hgnc):
    # Both columns look symbol-shaped; only col_b actually resolves to genes.
    # HGNC-aware scoring disambiguates what syntax cannot.
    df = pd.DataFrame(
        {
            "col_a": ["sample1", "sample2", "sample3"],
            "col_b": ["TP53", "BRCA1", "KRAS"],
        }
    )
    assert detect_id_column(df, hgnc=hgnc) == "col_b"


def test_detect_multiple_id_columns():
    df = pd.DataFrame(
        {
            "symbol": ["TP53", "BRCA1", "EGFR"],
            "ensembl_id": ["ENSG00000141510", "ENSG00000012048", "ENSG00000146648"],
            "logFC": [1.0, 2.0, 3.0],
        }
    )
    cols = detect_id_columns(df)
    assert "symbol" in cols
    assert "ensembl_id" in cols
    assert "logFC" not in cols


def test_name_hint_breaks_tie():
    df = pd.DataFrame(
        {
            "gene_symbol": ["TP53", "BRCA1"],
            "other": ["TP53", "BRCA1"],
        }
    )
    # Identical content; the gene-ish header should win.
    assert detect_id_column(df) == "gene_symbol"


def test_single_column():
    df = pd.DataFrame({"input": ["TP53", "BRCA1"]})
    assert detect_id_columns(df) == ["input"]

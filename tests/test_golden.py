"""Golden-output regression test over the bundled messy example.

Pins the (input -> detected_type / status / approved symbol) mapping so any
change in detection, recovery, or resolution behaviour is caught.
"""

from gene_tidy.examples import EXAMPLE_PATH, build_example_dataframe
from gene_tidy.pipeline import tidy_dataframe, tidy_file

# Expected audit rows in order: (input_value, detected_type, match_status, approved_symbol)
GOLDEN = [
    ("TP53", "symbol", "matched", "TP53"),
    ("tp53", "symbol", "matched", "TP53"),
    ("p53", "symbol", "matched_alias", "TP53"),
    ("HER2", "symbol", "matched_alias", "ERBB2"),
    ("FRAP1", "symbol", "matched_prev", "MTOR"),
    ("VEGF", "symbol", "matched_prev", "VEGFA"),
    ("ERBB", "symbol", "matched_prev", "EGFR"),
    ("2-Sep", "excel_corrupted", "recovered_excel", "SEPTIN2"),
    ("Sep-7", "excel_corrupted", "recovered_excel", "SEPTIN7"),
    ("1-Mar", "excel_corrupted", "ambiguous", "MARCHF1;MTARC1"),
    ("1-Dec", "excel_corrupted", "ambiguous", "BHLHE40;DELEC1"),
    ("KRAS", "symbol", "matched", "KRAS"),
    ("NRAS", "symbol", "matched", "NRAS"),
    ("ENSG00000141510", "ensembl_gene", "matched", "TP53"),
    ("P38398", "uniprot", "matched", "BRCA1"),
    ("672", "entrez", "matched", "BRCA1"),
    ("NM_000546", "refseq", "matched", "TP53"),
    ("HGNC:11998", "hgnc_id", "matched", "TP53"),
    ("egfr", "symbol", "matched", "EGFR"),
    ("FOOBAR1", "symbol", "unmatched", ""),
    ("", "unknown", "empty", ""),
]


def _audit_tuples(audit):
    return [
        (row["input_value"], row["detected_type"], row["match_status"],
         row["approved_symbol"])
        for _, row in audit.iterrows()
    ]


def test_golden_from_dataframe():
    df = build_example_dataframe()
    result = tidy_dataframe(df, id_columns=["gene_symbol"])
    assert _audit_tuples(result.audit) == GOLDEN


def test_golden_from_file(tmp_path):
    result = tidy_file(EXAMPLE_PATH, tmp_path / "out")
    assert _audit_tuples(result.audit) == GOLDEN


def test_golden_bucket_counts():
    df = build_example_dataframe()
    result = tidy_dataframe(df, id_columns=["gene_symbol"])
    assert result.counts == {"total": 21, "clean": 17, "ambiguous": 2, "failed": 2}


def test_golden_no_rows_dropped():
    df = build_example_dataframe()
    result = tidy_dataframe(df, id_columns=["gene_symbol"])
    assert len(result.audit) == len(GOLDEN)

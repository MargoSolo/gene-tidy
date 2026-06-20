import pandas as pd
import pytest

from gene_tidy.io import read_table, split_cell, write_outputs
from gene_tidy.pipeline import OUTPUT_COLUMNS, REQUIRED_COLUMNS, tidy_dataframe, tidy_file


# --- reading -----------------------------------------------------------------

def test_read_csv_with_header(tmp_path):
    p = tmp_path / "genes.csv"
    p.write_text("gene,logFC\nTP53,2.1\nBRCA1,1.0\n", encoding="utf-8")
    df = read_table(p)
    assert list(df.columns) == ["gene", "logFC"]
    assert df.iloc[0]["gene"] == "TP53"


def test_read_tsv(tmp_path):
    p = tmp_path / "genes.tsv"
    p.write_text("gene\tlogFC\nTP53\t2.1\n", encoding="utf-8")
    df = read_table(p)
    assert list(df.columns) == ["gene", "logFC"]


def test_read_txt_single_column_no_header(tmp_path):
    p = tmp_path / "genes.txt"
    p.write_text("TP53\nBRCA1\nEGFR\n", encoding="utf-8")
    df = read_table(p)
    assert df.shape == (3, 1)
    assert df.iloc[0, 0] == "TP53"


def test_read_xlsx(tmp_path):
    p = tmp_path / "genes.xlsx"
    pd.DataFrame({"gene": ["TP53", "BRCA1"], "logFC": [1.0, 2.0]}).to_excel(p, index=False)
    df = read_table(p)
    assert df.iloc[1]["gene"] == "BRCA1"


def test_headerless_single_column_csv_recovered(tmp_path):
    # The 'header' is actually a gene -> must not be lost.
    p = tmp_path / "list.csv"
    p.write_text("TP53\nBRCA1\nEGFR\n", encoding="utf-8")
    df = read_table(p)
    values = df.iloc[:, 0].tolist()
    assert "TP53" in values and len(values) == 3


# --- splitting ---------------------------------------------------------------

@pytest.mark.parametrize(
    "cell,expected",
    [
        ("TP53", ["TP53"]),
        ("KRAS, NRAS", ["KRAS", "NRAS"]),
        ("KRAS; NRAS", ["KRAS", "NRAS"]),
        ("KRAS|NRAS", ["KRAS", "NRAS"]),
        ("", [""]),
        ("  ", [""]),
    ],
)
def test_split_cell(cell, expected):
    assert split_cell(cell) == expected


# --- writing -----------------------------------------------------------------

def test_write_outputs_creates_six_files(tmp_path):
    df = pd.DataFrame({"gene": ["TP53", "FOOBAR1", "1-Mar"]})
    result = tidy_dataframe(df, id_columns=["gene"])
    paths = write_outputs(result, tmp_path)
    assert len(paths) == 6
    for key in ("clean_xlsx", "clean_csv", "failed_csv", "ambiguous_csv",
                "audit_csv", "methods_txt"):
        assert (tmp_path / {
            "clean_xlsx": "clean_table.xlsx",
            "clean_csv": "clean_table.csv",
            "failed_csv": "failed_rows.csv",
            "ambiguous_csv": "ambiguous_rows.csv",
            "audit_csv": "mapping_audit.csv",
            "methods_txt": "methods_text.txt",
        }[key]).exists()


def test_output_has_all_required_columns(tmp_path):
    df = pd.DataFrame({"gene": ["TP53"]})
    result = tidy_dataframe(df, id_columns=["gene"])
    for col in REQUIRED_COLUMNS:
        assert col in result.clean.columns
        assert col in result.audit.columns


def test_audit_has_provenance_columns(tmp_path):
    df = pd.DataFrame({"gene": ["TP53", "1-Mar", "FOOBAR1"]})
    result = tidy_dataframe(df, id_columns=["gene"])
    for col in ("hgnc_dump_date", "source_used", "matched_field",
                "match_reason", "candidate_count", "gene_tidy_version"):
        assert col in result.audit.columns
    # And they survive the round-trip to disk.
    paths = write_outputs(result, tmp_path)
    audit = pd.read_csv(paths["audit_csv"], keep_default_na=False)
    for col in ("hgnc_dump_date", "source_used", "matched_field",
                "match_reason", "candidate_count", "gene_tidy_version"):
        assert col in audit.columns
    # Provenance is populated meaningfully.
    tp53 = audit[audit["input_value"] == "TP53"].iloc[0]
    assert tp53["matched_field"] == "symbol"
    assert str(tp53["candidate_count"]) == "1"
    assert tp53["gene_tidy_version"] == "0.1.0"
    mar = audit[audit["input_value"] == "1-Mar"].iloc[0]
    assert str(mar["candidate_count"]) == "2"


def test_methods_text_contains_versions(tmp_path):
    df = pd.DataFrame({"gene": ["TP53"]})
    result = tidy_dataframe(df, id_columns=["gene"])
    assert "gene-tidy v0.1.0" in result.methods_text
    assert "HGNC" in result.methods_text


def test_methods_text_states_approved_filtering(tmp_path):
    df = pd.DataFrame({"gene": ["TP53"]})
    result = tidy_dataframe(df, id_columns=["gene"])
    assert "Approved" in result.methods_text
    assert "fully offline" in result.methods_text


def test_no_rows_dropped(tmp_path):
    values = ["TP53", "FOOBAR1", "1-Mar", "", "KRAS, NRAS"]
    df = pd.DataFrame({"gene": values})
    result = tidy_dataframe(df, id_columns=["gene"])
    # 4 single cells + 2 from the split cell = 6 audit rows, none dropped.
    assert len(result.audit) == 6
    assert (len(result.clean) + len(result.ambiguous) + len(result.failed)
            == len(result.audit))


def test_tidy_file_end_to_end(tmp_path):
    src = tmp_path / "in.csv"
    src.write_text("gene\nTP53\nFOOBAR1\n1-Mar\n", encoding="utf-8")
    out = tmp_path / "out"
    result = tidy_file(src, out)
    assert (out / "clean_table.xlsx").exists()
    assert result.counts["clean"] >= 1
    assert result.counts["ambiguous"] >= 1
    assert result.counts["failed"] >= 1

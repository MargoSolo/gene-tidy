"""Windows / path-with-spaces robustness and import-laziness checks."""

import subprocess
import sys

import pandas as pd
from typer.testing import CliRunner

from gene_tidy.cli import app
from gene_tidy.pipeline import tidy_file

runner = CliRunner()


# --- paths with spaces -------------------------------------------------------

def test_tidy_file_input_and_output_with_spaces(tmp_path):
    in_dir = tmp_path / "input folder with spaces"
    in_dir.mkdir()
    src = in_dir / "my messy genes.csv"
    src.write_text("gene\nTP53\np53\n1-Mar\nFOOBAR1\n", encoding="utf-8")

    out_dir = tmp_path / "output dir with spaces"
    result = tidy_file(src, out_dir)

    for name in ("clean_table.xlsx", "clean_table.csv", "failed_rows.csv",
                 "ambiguous_rows.csv", "mapping_audit.csv", "methods_text.txt"):
        assert (out_dir / name).exists()
    assert result.counts["clean"] >= 1


def test_xlsx_input_and_output_with_spaces(tmp_path):
    src = tmp_path / "a b" / "table with spaces.xlsx"
    src.parent.mkdir()
    pd.DataFrame({"gene_symbol": ["TP53", "BRCA1"]}).to_excel(src, index=False)
    out_dir = tmp_path / "out put"
    tidy_file(src, out_dir)
    assert (out_dir / "clean_table.xlsx").exists()


def test_cli_with_spaces_in_paths(tmp_path):
    src = tmp_path / "spaced input.csv"
    src.write_text("gene\nTP53\nBRCA1\n", encoding="utf-8")
    out_dir = tmp_path / "spaced output"
    result = runner.invoke(app, [str(src), "--out", str(out_dir)])
    assert result.exit_code == 0, result.stdout
    assert (out_dir / "clean_table.csv").exists()
    assert (out_dir / "mapping_audit.csv").exists()


def test_cli_txt_with_spaces(tmp_path):
    src = tmp_path / "gene list.txt"
    src.write_text("TP53\np53\nSEPT7\n", encoding="utf-8")
    out_dir = tmp_path / "my outputs"
    result = runner.invoke(app, [str(src), "--out", str(out_dir), "--quiet"])
    assert result.exit_code == 0, result.stdout
    assert (out_dir / "clean_table.csv").exists()


# --- import laziness ---------------------------------------------------------

def test_import_does_not_load_hgnc_data():
    """`import gene_tidy` must not read/parse the HGNC dump.

    Runs in a fresh subprocess (no test env overrides) and asserts the resolver
    cache is empty right after import.
    """
    code = (
        "import gene_tidy;"
        "from gene_tidy.hgnc import _load_cached;"
        "print(_load_cached.cache_info().currsize)"
    )
    out = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True, check=True,
    )
    assert out.stdout.strip() == "0", out.stdout + out.stderr

from typer.testing import CliRunner

from gene_tidy.cli import app

runner = CliRunner()


def _write_csv(path):
    path.write_text("gene\nTP53\np53\n1-Mar\nFOOBAR1\n", encoding="utf-8")


def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "gene-tidy 0.1.1" in result.stdout


def test_cli_runs_and_writes_outputs(tmp_path):
    src = tmp_path / "in.csv"
    _write_csv(src)
    out = tmp_path / "out"
    result = runner.invoke(app, [str(src), "--out", str(out)])
    assert result.exit_code == 0, result.stdout
    for name in ("clean_table.xlsx", "clean_table.csv", "failed_rows.csv",
                 "ambiguous_rows.csv", "mapping_audit.csv", "methods_text.txt"):
        assert (out / name).exists()


def test_cli_summary_mentions_counts(tmp_path):
    src = tmp_path / "in.csv"
    _write_csv(src)
    out = tmp_path / "out"
    result = runner.invoke(app, [str(src), "--out", str(out)])
    assert "clean" in result.stdout
    assert "ambiguous" in result.stdout


def test_cli_explicit_column(tmp_path):
    src = tmp_path / "in.csv"
    src.write_text("id,score\nTP53,1.0\nBRCA1,2.0\n", encoding="utf-8")
    out = tmp_path / "out"
    result = runner.invoke(app, [str(src), "--out", str(out), "--column", "id"])
    assert result.exit_code == 0, result.stdout
    assert (out / "clean_table.csv").exists()


def test_cli_missing_file_errors(tmp_path):
    result = runner.invoke(app, [str(tmp_path / "nope.csv")])
    assert result.exit_code != 0


def test_cli_quiet(tmp_path):
    src = tmp_path / "in.csv"
    _write_csv(src)
    out = tmp_path / "out"
    result = runner.invoke(app, [str(src), "--out", str(out), "--quiet"])
    assert result.exit_code == 0
    assert result.stdout.strip() == ""

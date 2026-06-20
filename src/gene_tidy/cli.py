"""Command-line interface for gene-tidy.

    gene-tidy input.xlsx --out outputs/
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import typer

from . import __version__
from .hgnc import hgnc_version_info
from .pipeline import tidy_file

app = typer.Typer(
    add_completion=False,
    help="Clean messy gene/protein identifier tables, fully offline.",
    no_args_is_help=True,
)


def _version_callback(value: bool):
    if value:
        info = hgnc_version_info()
        typer.echo(f"gene-tidy {__version__}")
        typer.echo(
            f"HGNC dump: {info.get('source')} "
            f"(release {info.get('hgnc_release')}, "
            f"retrieved {info.get('downloaded_date')})"
        )
        raise typer.Exit()


@app.command()
def main(
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=False,
        readable=True,
        help="Input table: .txt, .csv, .tsv, or .xlsx",
    ),
    out: Path = typer.Option(
        Path("outputs"),
        "--out",
        "-o",
        help="Output directory (created if missing).",
    ),
    columns: Optional[List[str]] = typer.Option(
        None,
        "--column",
        "-c",
        help="Identifier column name(s). Repeat to pass several. "
        "Auto-detected when omitted.",
    ),
    hgnc_file: Optional[Path] = typer.Option(
        None,
        "--hgnc-file",
        help="Path to a full hgnc_complete_set.txt to use instead of the "
        "bundled offline subset.",
    ),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress the summary."),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show gene-tidy and HGNC dump versions, then exit.",
    ),
):
    """Resolve identifiers in INPUT_FILE and write the six output files to --out."""
    id_columns = list(columns) if columns else None
    source = str(hgnc_file) if hgnc_file else None

    result = tidy_file(input_file, out, id_columns=id_columns, source=source)

    if not quiet:
        c = result.counts
        typer.echo(f"gene-tidy {__version__}")
        typer.echo(
            f"HGNC dump: {result.hgnc_version.get('hgnc_release')} "
            f"(retrieved {result.hgnc_version.get('downloaded_date')})"
        )
        typer.echo(f"Identifier column(s): {', '.join(result.id_columns)}")
        typer.echo(
            f"Resolved {c['clean']}/{c['total']} clean, "
            f"{c['ambiguous']} ambiguous, {c['failed']} failed."
        )
        typer.echo(f"Outputs written to: {Path(out).resolve()}")
        for label, path in (result.output_paths or {}).items():
            typer.echo(f"  - {Path(path).name}")


if __name__ == "__main__":
    app()

# gene-tidy

<!-- Badge placeholders — update the URLs once the repo is public / on PyPI. -->
[![CI](https://img.shields.io/badge/tests-passing-brightgreen)](https://github.com/gene-tidy/gene-tidy/actions)
[![PyPI](https://img.shields.io/badge/pypi-v0.1.0-blue)](https://pypi.org/project/gene-tidy/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/gene-tidy/gene-tidy/blob/main/notebooks/gene_tidy_colab.ipynb)

**Clean messy gene/protein identifier tables — fully offline, fully audited, no code required.**

Drop in a TXT/CSV/XLSX from a paper, a supplementary file, or a lab Excel sheet,
and get back a clean, multi-ID, fully-traceable table. Every value is mapped to
the current HGNC approved symbol plus Ensembl / UniProt / Entrez / RefSeq
cross-references — and nothing is ever guessed silently or dropped.

Inspired by [HGNChelper](https://cran.r-project.org/package=HGNChelper) (R), but
in Python, mapping to all major IDs, with **explicit ambiguity handling** and
**Excel date-corruption recovery** (`SEPT2 → "2-Sep"`, `MARCH1 → "1-Mar"`).

![gene-tidy demo](docs/demo.gif)
<!-- TODO: replace docs/demo.gif with a real screencast of the CLI / Colab run. -->

---

## Scope

gene-tidy is **HGNC-centered, offline, and reproducible**: it standardises human
gene/protein identifiers against a bundled static HGNC complete set and records
exactly which version it used. It is **not** a full
[BioMart](https://www.ensembl.org/biomart/) / [VEP](https://www.ensembl.org/vep)
/ [UniProt](https://www.uniprot.org/) mapping service — it does no live lookups,
no transcript/variant annotation, and no cross-database ID expansion beyond the
gene-level cross-references HGNC itself provides. If you need exhaustive,
always-current, multi-database mapping, use those tools; if you need a fast,
offline, auditable HGNC cleanup you can cite in a methods section, use gene-tidy.

## Why

- **Works offline, out of the box.** The full [HGNC](https://www.genenames.org/)
  complete set (all Approved gene records) ships inside the package as a gzipped
  TSV. No network, no API keys, no surprises — and the exact HGNC version is
  recorded in every run.
- **Never guesses silently.** One-to-many or uncertain mappings are flagged
  `ambiguous` / `manual_review_required` and routed to a separate file.
- **Never drops a row.** Clean, ambiguous, and failed rows are all accounted for.
- **Reproducible.** Every run emits a `methods_text.txt` paragraph (tool version,
  HGNC version + date) ready to paste into a supplementary methods section.

## Install

```bash
pip install gene-tidy
```

From source:

```bash
git clone https://github.com/gene-tidy/gene-tidy
cd gene-tidy
pip install -e .
```

Requires Python 3.10+. Dependencies: `pandas`, `openpyxl`, `typer`.

## Quickstart (CLI)

```bash
gene-tidy input.xlsx --out outputs/
```

That's it. `outputs/` will contain six files (see below). Works the same on
`.txt`, `.csv`, `.tsv`, and `.xlsx`:

```bash
gene-tidy my_genes.txt --out outputs/
gene-tidy supp_table.csv --out outputs/
```

Useful flags:

```bash
gene-tidy data.xlsx -o out/ --column gene_symbol   # force the identifier column
gene-tidy data.csv  -o out/ --column symbol -c ensembl_id   # multiple columns
gene-tidy data.xlsx -o out/ --hgnc-file hgnc_complete_set.txt  # use the full HGNC set
gene-tidy --version                                 # tool + HGNC dump version
```

## Quickstart (Python)

```python
from gene_tidy import tidy_file, tidy_values

# Whole file -> writes the six output files, returns a result object.
result = tidy_file("supp_table.xlsx", "outputs/")
print(result.counts)   # {'total': 21, 'clean': 16, 'ambiguous': 3, 'failed': 2}

# Or clean an in-memory list of identifiers (no files written):
result = tidy_values(["TP53", "p53", "Sep-7", "ENSG00000141510", "1-Mar", "FOOBAR1"])
print(result.audit[["input_value", "approved_symbol", "match_status"]])
```

```text
       input_value approved_symbol     match_status
0             TP53            TP53          matched
1              p53            TP53    matched_alias
2            Sep-7         SEPTIN7  recovered_excel
3  ENSG00000141510            TP53          matched
4            1-Mar  MARCHF1;MTARC1        ambiguous
5          FOOBAR1                          unmatched
```

`1-Mar` (ambiguous between `MARCHF1` and `MTARC1`) lands in `result.ambiguous`;
`FOOBAR1` lands in `result.failed`. Nothing is dropped.

## What it handles

| Input | Example | Result |
|---|---|---|
| Approved symbol | `TP53` | `matched` → TP53 |
| Alias symbol | `p53`, `HER2` | `matched_alias` (warns "resolved from alias") |
| Previous symbol | `FRAP1`, `VEGF` | `matched_prev` (warns "resolved from previous symbol") |
| Ensembl gene | `ENSG00000141510` | `matched` → TP53 |
| UniProt | `P38398` | `matched` → BRCA1 |
| Entrez | `672` | `matched` → BRCA1 |
| RefSeq | `NM_000546` | `matched` → TP53 |
| HGNC ID | `HGNC:11998` | `matched` → TP53 |
| **Excel date corruption** | `Sep-7` | `recovered_excel` → SEPTIN7 (always warns) |
| **Ambiguous corruption** | `1-Mar`, `2-Sep`, `1-Dec` | `ambiguous` → e.g. MARCHF1/MTARC1, SEPTIN2/SEPTIN6 → manual review |
| Multiple IDs per cell | `KRAS, NRAS` | split and resolved independently |
| Case / whitespace | `  tp53 ` | normalised → TP53 |
| Duplicates | `TP53` ×2 | kept, flagged in `warning` |
| No match | `FOOBAR1` | `unmatched` → `failed_rows.csv` |

## Output files

Every run writes six files to `--out`:

| File | Contents |
|---|---|
| `clean_table.xlsx` / `clean_table.csv` | confidently resolved rows |
| `ambiguous_rows.csv` | one-to-many / uncertain rows needing manual review |
| `failed_rows.csv` | unmatched and empty rows |
| `mapping_audit.csv` | **every** input → output, with full provenance (see below) |
| `methods_text.txt` | paste-ready methods paragraph (tool + HGNC version/date) |

### Columns (required schema)

`input_value`, `detected_type`, `approved_symbol`, `hgnc_id`,
`ensembl_gene_id`, `uniprot_id`, `entrez_id`, `refseq_id`, `match_status`,
`warning`, `source_used`, `manual_review_required`
(plus `source_row` / `source_column` for traceability back to the original table).

`match_status` is one of: `matched`, `matched_alias`, `matched_prev`,
`recovered_excel` (→ clean) · `ambiguous` (→ review) · `unmatched`, `empty`
(→ failed).

Every table also carries per-row provenance — `matched_field` (which HGNC field
matched: `symbol` / `alias_symbol` / `prev_symbol` / `ensembl_gene_id` /
`uniprot_ids` / `entrez_id` / `refseq_accession` / `hgnc_id` / `excel_recovery`),
`match_reason` (human-readable), and `candidate_count` (1 for a clean hit, N for
ambiguous, 0 for no match). `mapping_audit.csv` additionally records
`hgnc_dump_date` and `gene_tidy_version` on every row for full reproducibility.

## Source of truth & offline guarantee

Resolution runs against a **static, bundled HGNC complete set** —
`src/gene_tidy/data/hgnc_complete_set.tsv.gz`, containing all ~45,000 Approved
HGNC gene records — matched against the approved symbol, `alias_symbol`, and
`prev_symbol` fields. The accompanying `hgnc_version.json` records the source
URL, HGNC license (CC0), download date, release tag, and record count; the same
provenance is printed by `gene-tidy --version`, written into every
`mapping_audit.csv` row, and summarised in `methods_text.txt`.

To use a **different / newer** HGNC release, pass
`--hgnc-file path/to/hgnc_complete_set.txt`, set the `GENE_TIDY_HGNC_FILE`
environment variable, or regenerate the bundled dump with
`python tools/build_hgnc_data.py hgnc_complete_set.txt`. A user-supplied file is
filtered to `status == Approved` automatically.

The package and its **tests never require network access.** (The test suite
resolves against a tiny curated fixture in `tests/fixtures/` for speed; the real
bundled dump is exercised separately in `tests/test_data_boundary.py`.)

> Real-world note: because the bundled data is the *real* HGNC set, genuine
> one-to-many cases surface honestly. For example `SEPT2` is a previous symbol of
> `SEPTIN2` **and** an alias of `SEPTIN6`, so gene-tidy reports it `ambiguous`
> rather than guessing.

## Colab notebook

Zero-setup, in-browser: upload a file → run → preview clean/failed/ambiguous
rows → download a ZIP of all outputs. A bundled `messy_example.xlsx` lets you
click **Run** and see results immediately.

[`notebooks/gene_tidy_colab.ipynb`](notebooks/gene_tidy_colab.ipynb)
<!-- TODO: add an "Open in Colab" badge pointing at the hosted repo path. -->

## Limitations (v0.1)

- Ensembl **transcript/protein** IDs (`ENST…`/`ENSP…`) are detected but not
  resolved offline (gene-level dump only); they are flagged for manual review.
- Numeric Excel date *serials* (e.g. `44075`) are indistinguishable from Entrez
  IDs and are intentionally **not** reinterpreted.
- Human only. No HGVS / ClinVar / VEP / gnomAD / liftover / genome-build
  detection / clinical interpretation (out of scope for v0.1).

## Development

```bash
pip install -e ".[test]"
pytest                 # 100+ tests, all offline
```

Test coverage: ID-type detection, column detection, resolver (alias / prev /
Excel-corruption / ambiguity), input/output file handling, CLI, golden-output
regression on the bundled example, and a data-boundary test that loads the real
bundled HGNC complete set. Most tests use a small curated fixture
(`tests/fixtures/hgnc_subset.tsv`) so the suite runs in seconds.

To refresh the bundled HGNC data (deterministic: the same input always produces
a byte-identical `.tsv.gz`, and the run records `raw_download_sha256` +
`bundled_tsv_gz_sha256` in `hgnc_version.json`):

```bash
python tools/build_hgnc_data.py path/to/hgnc_complete_set.txt   # from a pinned file
python tools/build_hgnc_data.py --download                      # or fetch current
```

## Attribution & citing HGNC

gene-tidy resolves identifiers using data from the **HUGO Gene Nomenclature
Committee (HGNC)**.

- **Source:** HGNC complete set, downloaded from
  <https://www.genenames.org/download/archive/>
  (file: `hgnc_complete_set.txt`).
- **Snapshot bundled in this release:** see `downloaded_date` and
  `bundled_tsv_gz_sha256` in
  [`src/gene_tidy/data/hgnc_version.json`](src/gene_tidy/data/hgnc_version.json)
  (also printed by `gene-tidy --version` and written into every
  `mapping_audit.csv` / `methods_text.txt`).
- **License:** HGNC data are released under a
  [CC0 1.0 public-domain dedication](https://www.genenames.org/about/license/),
  so they are free to redistribute; gene-tidy bundles a column-trimmed,
  Approved-only snapshot.
- **Recommendation:** in your own methods/supplementary text, cite HGNC and
  state the **retrieval month/year** of the dump you used (e.g. *"HGNC complete
  set, retrieved June 2026, via gene-tidy v0.1.0"*). The exact date and hash are
  in `hgnc_version.json` and the generated `methods_text.txt`.

Please cite HGNC: Seal RL, *et al.* *Genenames.org: the HGNC resources in 2023.*
Nucleic Acids Res. 2023;51(D1):D1003–D1009.

## License

gene-tidy itself is MIT — see [LICENSE](LICENSE). The bundled HGNC data is CC0
(see Attribution above).

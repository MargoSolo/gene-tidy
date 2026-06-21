# Changelog

All notable changes to gene-tidy are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-06-21

Documentation / metadata release for the public launch.

### Changed
- Improve the README / PyPI landing page with a clearer quick-start, before/after
  examples, and a visible "Scope & limitations" section.

### Unchanged
- No functional changes.
- Offline, HGNC-centered behavior unchanged.
- Ambiguity / manual-review behavior unchanged.

## [0.1.0] - 2026-06-20

First release candidate (`v0.1.0-rc1`).

### Added
- **Offline HGNC-centered identifier cleanup.** Resolve gene/protein
  identifiers to current HGNC approved symbols plus Ensembl / UniProt / Entrez /
  RefSeq cross-references, fully offline.
- **Bundled static HGNC complete set.** Ships all 44,997 Approved HGNC gene
  records as a deterministic, gzipped TSV
  (`src/gene_tidy/data/hgnc_complete_set.tsv.gz`); no network access at runtime.
- **Identifier-type detection** for HGNC IDs, Ensembl gene IDs, UniProt, Entrez,
  RefSeq, and gene symbols.
- **Automatic identifier-column detection** (HGNC-aware), with manual override.
- **Excel date-corruption recovery** — detects and recovers symbols mangled into
  dates (e.g. `SEPT2 → "2-Sep"`, `MARCH1 → "1-Mar"`); always warns, and flags
  genuinely ambiguous cases (e.g. `2-Sep → SEPTIN2/SEPTIN6`,
  `1-Mar → MARCHF1/MTARC1`) for manual review rather than guessing.
- **Alias / previous-symbol resolution** with explicit `matched_alias` /
  `matched_prev` status and warnings.
- **Never guess silently, never drop a row.** One-to-many or uncertain mappings
  are routed to `ambiguous_rows.csv` with `manual_review_required = True`;
  unmatched/empty go to `failed_rows.csv`.
- **Six output files**: `clean_table.xlsx`, `clean_table.csv`,
  `ambiguous_rows.csv`, `failed_rows.csv`, `mapping_audit.csv`,
  `methods_text.txt`.
- **Full audit provenance** in `mapping_audit.csv`: `source_used`,
  `matched_field`, `match_reason`, `candidate_count`, `hgnc_dump_date`,
  `gene_tidy_version`, plus row/column traceability.
- **Reproducible methods text** with HGNC version/date and an explicit statement
  that only `status == Approved` HGNC entries were used.
- **CLI** (`gene-tidy input.xlsx --out outputs/`) supporting TXT/CSV/TSV/XLSX,
  multiple identifier columns, `--hgnc-file` override, and `--version`.
- **Colab notebook** with a bundled `messy_example.xlsx` for zero-setup use.
- **Provenance hashes** in `hgnc_version.json` (`raw_download_sha256`,
  `bundled_tsv_gz_sha256`) and a reproducible data-build tool
  (`tools/build_hgnc_data.py`).
- **116 offline tests**: detection, column detection, resolver, Excel recovery,
  ambiguity, I/O, CLI, Windows/path-with-spaces, import-laziness, golden-output
  regression, and a data-boundary test against the real bundled dump.

### Data provenance
- HGNC complete set, retrieved 2026-06-20, CC0 licensed.
- `bundled_tsv_gz_sha256`:
  `6bb2951c56204cd7b387c4e40b8d46107f6bdc422e77b8e4f2088a5d39e1be4b`

### Scope (intentionally excluded in v0.1)
Live API calls; HGVS, ClinVar, VEP, gnomAD, liftover, genome-build detection,
clinical interpretation; non-human species; Ensembl transcript/protein-level
resolution; reinterpreting numeric Excel date serials.

[0.1.1]: https://github.com/MargoSolo/gene-tidy/releases/tag/v0.1.1
[0.1.0]: https://github.com/MargoSolo/gene-tidy/releases/tag/v0.1.0-rc1

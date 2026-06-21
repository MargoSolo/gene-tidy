# bio.tools registration draft — gene-tidy

Draft content for a [bio.tools](https://bio.tools/) registry entry. Fill these
values into the bio.tools submission form (or the equivalent `biotoolsSchema`
JSON). Nothing here changes package behavior; it is metadata only.

## Core fields

| Field | Value |
|---|---|
| **Name** | gene-tidy |
| **Description** | Offline, HGNC-centered Python/Colab tool for cleaning messy human gene/protein identifier tables. Maps inputs to the current HGNC approved symbol plus Ensembl / UniProt / Entrez / RefSeq cross-references, with explicit ambiguity handling and a full per-row audit trail — nothing is silently guessed or dropped. |
| **Homepage** | https://github.com/MargoSolo/gene-tidy |
| **Download** | https://pypi.org/project/gene-tidy/ (`pip install gene-tidy`) |
| **Documentation** | README: https://github.com/MargoSolo/gene-tidy#readme · Colab notebook: `notebooks/gene_tidy_colab.ipynb` |
| **License** | MIT |
| **Tool type** | Command-line tool; Library; Web application (Colab notebook) |
| **Programming language** | Python |
| **Operating system** | Linux, Mac, Windows |
| **Maturity** | Beta |
| **Cost** | Free of charge |
| **Accessibility** | Open access |

## Topics (EDAM-aligned keywords)

- bioinformatics
- genomics
- gene symbols / nomenclature
- identifier mapping
- data cleaning / data handling
- reproducible research

Suggested EDAM topic mappings for the form:
- `Genomics` (topic_0622)
- `Data management` (topic_3071)
- `Molecular genetics` (topic_3053)

## Function / operation

- **Operation:** identifier mapping; data cleaning / standardisation; format validation.
- **Suggested EDAM operations:** `Mapping` (operation_2429), `Data handling` (operation_2409), `Validation` (operation_2428).

## Inputs

- Tabular files: **TXT / CSV / TSV / XLSX** containing gene/protein identifiers
  (approved symbols, aliases, previous symbols, Ensembl gene IDs, UniProt, Entrez,
  RefSeq, HGNC IDs), including Excel date-corrupted symbols (e.g. `Sep-7`).
- Data format: plain text table / comma-separated values / Excel XLSX.

## Outputs

- `clean_table.xlsx` / `clean_table.csv` — confidently resolved rows.
- `ambiguous_rows.csv` — one-to-many / uncertain rows flagged for manual review.
- `failed_rows.csv` — unmatched and empty rows.
- `mapping_audit.csv` — every input → output with full provenance.
- `methods_text.txt` — paste-ready methods paragraph (tool + HGNC version/date).

## Scope limitations (state explicitly)

- **Human, HGNC-centered only.** No non-human species.
- **No clinical interpretation.** No HGVS / ClinVar / VEP / gnomAD / variant or
  disease annotation.
- **No live APIs / network calls.** Resolution runs against a static, bundled
  HGNC complete set; the exact version and SHA-256 hashes are recorded per run.
- **Gene-level only.** Ensembl transcript/protein IDs are detected but not
  resolved offline; cross-references are limited to those HGNC itself provides.

## Credit / contact

- **Developer / maintainer:** MargoSolo (GitHub).
- **Repository:** https://github.com/MargoSolo/gene-tidy
- **Issue tracker:** https://github.com/MargoSolo/gene-tidy/issues

## Attribution to embed in the entry

Resolution uses data from the HUGO Gene Nomenclature Committee (HGNC),
redistributed under CC0. Cite HGNC: Seal RL, *et al.* *Genenames.org: the HGNC
resources in 2023.* Nucleic Acids Res. 2023;51(D1):D1003–D1009.

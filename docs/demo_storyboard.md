# gene-tidy demo storyboard

This documents how the launch demo assets were produced and how to record a real
screencast GIF to accompany them.

## Assets in this folder

- **`demo_input.csv`** — the verified demo input (10 identifiers covering every case).
- **`demo_before_after.png`** — a figure rendered **directly from real `gene-tidy 0.1.1` output**
  on `demo_input.csv` (every cell is actual output, not a mockup). Used as the
  README hero image and as carousel slide 3.

## The demo input (real)

```text
TP53
p53
HER2
FRAP1
Sep-7
2-Sep
1-Mar
ENSG00000141510
P04637
FOOBAR1
```

## Reproduce the output

```bash
pip install gene-tidy==0.1.1
gene-tidy docs/demo_input.csv --out outputs/
```

Real result (`gene-tidy 0.1.1`, HGNC `complete_set_2026-06-20`):

```text
Resolved 7/10 clean, 2 ambiguous, 1 failed.
```

| You typed | → approved symbol | Why | Status |
|---|---|---|---|
| `TP53` | TP53 | approved symbol | matched |
| `p53` | TP53 | resolved from alias | matched_alias |
| `HER2` | ERBB2 | resolved from alias | matched_alias |
| `FRAP1` | MTOR | resolved from previous symbol | matched_prev |
| `Sep-7` | SEPTIN7 | recovered from Excel date corruption | recovered_excel |
| `ENSG00000141510` | TP53 | Ensembl gene ID | matched |
| `P04637` | TP53 | UniProt ID | matched |
| `2-Sep` | SEPTIN2 / SEPTIN6 | ambiguous → manual review | ambiguous |
| `1-Mar` | MARCHF1 / MTARC1 | ambiguous → manual review | ambiguous |
| `FOOBAR1` | (no match) | → `failed_rows.csv` | unmatched |

Six files are written every run: `clean_table.xlsx`, `clean_table.csv`,
`ambiguous_rows.csv`, `failed_rows.csv`, `mapping_audit.csv`, `methods_text.txt`.

## GIF storyboard (10–25 s, to record)

Record with a screen recorder (e.g. ScreenToGif / Peek / LICEcap), 1280×720+,
large font, light theme, then save as `docs/demo.gif`.

| Time | Frame | On screen |
|---|---|---|
| 0–3s | The problem | `demo_input.csv` open — highlight `p53`, `Sep-7`, `2-Sep`, `FOOBAR1`. Caption: "Real gene tables are messy." |
| 3–6s | One command | Terminal: `gene-tidy demo_input.csv --out outputs/` ↵ |
| 6–9s | The summary | Show `Resolved 7/10 clean, 2 ambiguous, 1 failed.` + the six output filenames. |
| 9–15s | Clean payoff | Open `clean_table.csv`: `p53→TP53`, `HER2→ERBB2`, `Sep-7→SEPTIN7`, `P04637→TP53`. |
| 15–20s | The trust | Open `ambiguous_rows.csv`: `2-Sep`, `1-Mar` flagged. Caption: "Ambiguous? Flagged, never guessed." |
| 20–25s | Audit + CTA | Flash one `mapping_audit.csv` row + `methods_text.txt`. End on `pip install gene-tidy`. |

## Honesty guardrail

Everything shown must be real output from the bundled HGNC dump. Do not stage,
edit, or fabricate cells, counts, or files. No usage/adoption/citation claims.

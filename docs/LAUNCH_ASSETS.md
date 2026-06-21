# gene-tidy — launch asset plan

Everything needed to produce the launch GIF, the LinkedIn carousel, and the
screenshots. All numbers and table rows below are **real, reproducible output**
from `gene-tidy 0.1.0` — do not invent usage, citation, or adoption claims.

## Key message (the one thing to land)

> **Clean messy human gene tables in seconds — offline, audited, and with no silent guessing.**

Three supporting pillars:
1. **Offline & reproducible** — bundled HGNC complete set, exact version + SHA-256 recorded every run. No network, no API keys.
2. **Never guesses silently** — ambiguous cases (e.g. `2-Sep`, `1-Mar`) are flagged for manual review, never auto-resolved.
3. **Full audit trail** — every input → output row is traceable; a paste-ready methods paragraph comes free.

## The demo dataset (use this everywhere)

Save as `messy_genes.csv` — a tiny table that hits every interesting case:

```csv
gene
TP53
p53
ENSG00000141510
HER2
FRAP1
Sep-7
2-Sep
1-Mar
FOOBAR1
```

### Expected before → after (verified with 0.1.0)

| Input | Detected as | Approved symbol | Status |
|---|---|---|---|
| `TP53` | symbol | `TP53` | matched ✅ |
| `p53` | symbol | `TP53` | matched_alias ✅ |
| `ENSG00000141510` | ensembl_gene | `TP53` | matched ✅ |
| `HER2` | symbol | `ERBB2` | matched_alias ✅ |
| `FRAP1` | symbol | `MTOR` | matched_prev ✅ |
| `Sep-7` | excel_corrupted | `SEPTIN7` | recovered_excel ✅ |
| `2-Sep` | excel_corrupted | `SEPTIN2;SEPTIN6` | **ambiguous** ⚠️ |
| `1-Mar` | excel_corrupted | `MARCHF1;MTARC1` | **ambiguous** ⚠️ |
| `FOOBAR1` | symbol | — | unmatched ❌ |

**Headline counts: 9 in → 6 clean, 2 ambiguous (flagged), 1 failed. Nothing dropped.**

The story this tells in one glance: aliases and previous symbols resolved, an
Ensembl ID mapped back to its symbol, an Excel-mangled `Sep-7` *recovered* to
`SEPTIN7`, the genuinely ambiguous `2-Sep`/`1-Mar` *honestly flagged* instead of
guessed, and a junk value cleanly isolated.

---

## 1. Demo GIF storyboard (10–20 seconds)

Target: ~15s, silent, looping. Replaces the `docs/demo.gif` placeholder.

| Time | Frame | What's on screen |
|---|---|---|
| 0–3s | **The problem** | The messy `messy_genes.csv` open in a spreadsheet — highlight `p53`, `Sep-7`, `2-Sep`, `FOOBAR1` in red. Caption: "Real gene tables are messy." |
| 3–5s | **One command** | Terminal: type `gene-tidy messy_genes.csv --out outputs/` and hit enter. |
| 5–8s | **The summary** | The printed line `Resolved 6/9 clean, 2 ambiguous, 1 failed.` appears. Caption: "Offline. Seconds." |
| 8–12s | **The payoff** | Open `clean_table.csv` — show `p53→TP53`, `Sep-7→SEPTIN7`, `HER2→ERBB2`. Caption: "Aliases, Ensembl IDs, Excel damage — fixed." |
| 12–15s | **The trust** | Open `ambiguous_rows.csv` — show `2-Sep` / `1-Mar` flagged. Caption: "Ambiguous? Flagged, never guessed." End on the gene-tidy name + `pip install gene-tidy`. |

Recording tips: 1280×720 minimum, large terminal font (16pt+), light theme for
contrast, trim dead air, export at ~12–15 fps to keep the GIF small.

## 2. LinkedIn carousel storyboard (5 slides)

Square (1080×1080). Consistent header, big readable type, one idea per slide.

- **Slide 1 — Hook.**
  Title: "Your gene table is lying to you."
  Sub: "`SEPT2` became `2-Sep`. `p53` isn't an official symbol. Here's a fix."
  Visual: a cramped messy spreadsheet snippet.

- **Slide 2 — The pain.**
  Title: "Why this is a real problem."
  Bullets: Excel auto-corrupts symbols; aliases & old names break joins; manual
  cleanup isn't reproducible. Visual: red-circled bad cells.

- **Slide 3 — The fix.**
  Title: "`pip install gene-tidy`"
  Show the one command and the before→after table (6 clean / 2 ambiguous / 1 failed).
  Visual: the verified table above.

- **Slide 4 — Why trust it.**
  Title: "Offline. Audited. No silent guessing."
  Bullets: bundled HGNC set + recorded version/hash; ambiguous rows flagged for
  review; full per-row audit + paste-ready methods text. Visual: a row of the
  `mapping_audit.csv` + the methods paragraph.

- **Slide 5 — Call to action.**
  Title: "Try it in 30 seconds."
  Lines: `pip install gene-tidy` · open the Colab (one click, no setup) · star the repo.
  Visual: the "Open in Colab" badge + GitHub URL.

Caption guardrail: describe what the tool *does*, not how many people use it.
No "trusted by labs" / "thousands of downloads" unless and until that is true.

## 3. Exact screenshots to capture

1. **Messy input** — `messy_genes.csv` in a spreadsheet, bad cells highlighted.
2. **The command + summary** — terminal showing `gene-tidy messy_genes.csv --out outputs/` and the `6/9 clean, 2 ambiguous, 1 failed` line.
3. **clean_table** — `clean_table.csv`/`.xlsx` with the recovered/aliased rows visible.
4. **ambiguous_rows** — `2-Sep` and `1-Mar` with both candidate symbols.
5. **mapping_audit** — one full row showing provenance columns (`matched_field`, `match_reason`, `candidate_count`, `hgnc_dump_date`, `gene_tidy_version`).
6. **methods_text.txt** — the generated methods paragraph.
7. **Colab** — the notebook running end-to-end on the bundled example (the "no install, click Run" wow shot).

## 4. Assets checklist

- [ ] `docs/demo.gif` recorded and committed (replaces placeholder).
- [ ] 5 carousel slides exported (PNG, 1080×1080).
- [ ] 7 screenshots captured at ≥1280px wide.
- [ ] `messy_genes.csv` saved alongside the post (or link the bundled `messy_example.xlsx`).
- [ ] Colab link verified to run top-to-bottom with zero setup.
- [ ] Final copy proofread against the "no fake claims" guardrail.

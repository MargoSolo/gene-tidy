# gene-tidy — distribution & discovery checklist

A practical, ordered checklist for getting `gene-tidy` in front of the people who
need it, after the first public release. Statuses are factual — only items
actually completed are marked done.

| Channel | Status | Notes |
|---|---|---|
| **PyPI** | ✅ done | `pip install gene-tidy` — published as `0.1.0`: https://pypi.org/project/gene-tidy/ |
| **GitHub Release** | ✅ done | Tag `v0.1.0` published on https://github.com/MargoSolo/gene-tidy |
| **bio.tools** | ⏭️ next | Registry entry for discoverability in the bioinformatics ecosystem. Draft in [`BIOTOOLS_DRAFT.md`](BIOTOOLS_DRAFT.md). |
| **LinkedIn launch** | ⏭️ next | Launch post + carousel + demo GIF. Plan in [`LAUNCH_ASSETS.md`](LAUNCH_ASSETS.md). |
| **Demo GIF / carousel** | ⏭️ next | Replace `docs/demo.gif` placeholder with a real screencast; build the 5-slide carousel. See [`LAUNCH_ASSETS.md`](LAUNCH_ASSETS.md). |
| **Bioconda** | 🕓 later | Conda-forge/Bioconda recipe so `conda install -c bioconda gene-tidy` works. Pure-Python + bundled data makes this straightforward once PyPI is stable. |
| **Zenodo DOI** | 🕓 before JOSS | Enable the GitHub↔Zenodo integration and cut an archived release to mint a citable DOI. Required as a prerequisite for the JOSS submission. |
| **JOSS paper** | 🕓 later | Short Journal of Open Source Software paper. Needs: stable releases, tests (have), docs (have), a Zenodo DOI, and `paper.md` + `paper.bib`. Do **not** start until Zenodo DOI exists. |

## Suggested order

1. **bio.tools** — cheap, high-signal, improves discoverability immediately.
2. **LinkedIn launch** with **demo GIF + carousel** — drives the first wave of real users.
3. **Bioconda** — broadens install reach for the conda-based bioinformatics crowd.
4. **Zenodo DOI** — archive a release, get a citable identifier.
5. **JOSS paper** — only after the above; reuse the README/methods text as the basis.

## Guardrails (do not violate when promoting)

- No fabricated usage/citation/benchmark numbers. Describe capabilities, not adoption we cannot prove.
- Keep the scope claim honest: offline, HGNC-centered, human-only; no live APIs, no clinical interpretation, no non-human species.
- Never imply silent guessing — the differentiator is *explicit* ambiguity handling and full audit trail.

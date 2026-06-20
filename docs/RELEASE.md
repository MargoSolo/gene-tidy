# Release verification

Run these checks before tagging/publishing a gene-tidy release. All commands are
run from the repository root. Everything is **offline** except the optional HGNC
data refresh.

Commands are shown for both Bash (Linux/macOS/Git Bash) and PowerShell
(Windows). Pick the set that matches your shell.

## 0. Fresh environment

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[test]"
pip install build
```

## 1. Run the test suite (must be fully offline)

```bash
pytest
```

Expected: all tests pass (116 as of v0.1.0). The suite uses the small fixture in
`tests/fixtures/hgnc_subset.tsv` for speed and exercises the real bundled dump in
`tests/test_data_boundary.py`.

## 2. Build the wheel + sdist

```bash
python -m build
```

Expected: `dist/gene_tidy-<version>-py3-none-any.whl` and
`dist/gene_tidy-<version>.tar.gz` are produced.

Confirm the bundled HGNC data is inside the wheel:

```bash
# Bash
python -c "import zipfile,glob; z=zipfile.ZipFile(glob.glob('dist/*.whl')[0]); print('\n'.join(n for n in z.namelist() if 'data/' in n))"
```

```powershell
# PowerShell
python -c "import zipfile,glob; z=zipfile.ZipFile(glob.glob('dist/*.whl')[0]); print(chr(10).join(n for n in z.namelist() if 'data/' in n))"
```

Expected to list `gene_tidy/data/hgnc_complete_set.tsv.gz` and
`gene_tidy/data/hgnc_version.json` (and NOT `hgnc_subset.tsv`).

## 3. Clean-venv wheel install (offline)

```bash
# Bash
python -m venv /tmp/gt_check
/tmp/gt_check/bin/pip install dist/*.whl
/tmp/gt_check/bin/gene-tidy --version
/tmp/gt_check/bin/python -c "import gene_tidy; from gene_tidy.hgnc import _load_cached; print('cache after import =', _load_cached.cache_info().currsize)"
```

```powershell
# PowerShell
python -m venv $env:TEMP\gt_check
& "$env:TEMP\gt_check\Scripts\pip.exe" install (Get-ChildItem dist\*.whl | Select-Object -First 1).FullName
& "$env:TEMP\gt_check\Scripts\gene-tidy.exe" --version
& "$env:TEMP\gt_check\Scripts\python.exe" -c "import gene_tidy; from gene_tidy.hgnc import _load_cached; print('cache after import =', _load_cached.cache_info().currsize)"
```

Expected: `gene-tidy --version` prints the tool + bundled HGNC release; the cache
size after a bare `import gene_tidy` is **0** (HGNC data must not load at import).

## 4. Import-time check (HGNC must not load on import)

```bash
python -X importtime -c "import gene_tidy" 2>&1 | grep gene_tidy
```

Expected: `gene_tidy.hgnc` appears only with a small module-load time; no
multi-hundred-millisecond data parse.

## 5. CLI on TXT / CSV / XLSX

```bash
# Bash
printf "gene\nTP53\np53\nSep-7\n1-Mar\nFOOBAR1\n" > /tmp/in.csv
printf "TP53\np53\nSEPT7\n"                         > /tmp/in.txt
python -c "import pandas as pd; pd.DataFrame({'gene_symbol':['TP53','BRCA1']}).to_excel('/tmp/in.xlsx', index=False)"

gene-tidy /tmp/in.csv  --out /tmp/out_csv
gene-tidy /tmp/in.txt  --out /tmp/out_txt
gene-tidy /tmp/in.xlsx --out /tmp/out_xlsx
ls /tmp/out_csv        # 6 output files
```

Expected for each: six output files written
(`clean_table.xlsx`, `clean_table.csv`, `failed_rows.csv`, `ambiguous_rows.csv`,
`mapping_audit.csv`, `methods_text.txt`). For `in.csv`, `1-Mar` lands in
`ambiguous_rows.csv` and `FOOBAR1` in `failed_rows.csv` — confirm ambiguity
handling is intact.

## 6. Notebook JSON validation

```bash
python -c "import json; json.load(open('notebooks/gene_tidy_colab.ipynb', encoding='utf-8')); print('notebook JSON OK')"
```

## 7. Bundled HGNC hash verification

The bundled gzip must match the hash recorded in `hgnc_version.json`:

```bash
# Bash
python -c "import hashlib,json,pathlib; d=json.loads(pathlib.Path('src/gene_tidy/data/hgnc_version.json').read_text()); h=hashlib.sha256(pathlib.Path('src/gene_tidy/data/hgnc_complete_set.tsv.gz').read_bytes()).hexdigest(); print('OK' if h==d['bundled_tsv_gz_sha256'] else 'MISMATCH', h)"
```

```powershell
# PowerShell
(Get-FileHash src\gene_tidy\data\hgnc_complete_set.tsv.gz -Algorithm SHA256).Hash.ToLower()
python -c "import json,pathlib; print(json.loads(pathlib.Path('src/gene_tidy/data/hgnc_version.json').read_text())['bundled_tsv_gz_sha256'])"
```

Expected: the two hashes are equal. (`tests/test_data_boundary.py` also asserts
this automatically.)

## 8. (Optional) Refresh the bundled HGNC data

Developer-only; requires network. Deterministic — the same input file always
produces a byte-identical `.tsv.gz`:

```bash
python tools/build_hgnc_data.py path/to/hgnc_complete_set.txt   # pin a file
python tools/build_hgnc_data.py --download                      # or fetch current
```

After refreshing, re-run steps 1–7.

## 9. Tag

Once all checks pass:

```bash
git tag v0.1.0-rc1
```

Do **not** publish to PyPI for the release candidate.

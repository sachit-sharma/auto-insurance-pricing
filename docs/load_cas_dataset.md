# Load a CASdatasets dataset

## Objective
Load any dataset from the `CASdatasets` R package (Dutang & Charpentier,
"Computational Actuarial Science with R") into this project as a CSV, without
installing/compiling the full R package.

## Why this approach
`CASdatasets` is not on CRAN — it's hosted at a separate repo and is a ~245MB
source tarball that needs compilation (`NeedsCompilation: yes`) to install
normally. We don't need the compiled package, just the data: each dataset is
a plain `.rda` file inside `CASdatasets/data/` in that tarball. We download
the tarball once (cached in `data/raw/`), extract only the requested `.rda`,
load it with R's `load()`, and write it straight to CSV.

## Required inputs
- `dataset_name`: the exact CASdatasets dataset name (case-sensitive), e.g.
  `beMTPL97`, `beMTPL16`, `freMTPL2freq`, `freMTPL2sev`, `ausMTPL8486`,
  `euMTPL`, `itamtplcost`. Full list: browse
  `CASdatasets/data/` inside the tarball, or see
  https://dutangc.github.io/CASdatasets/ for the catalog and each dataset's
  documented schema.

## Tool to use
`src/fetch_cas_dataset.R <dataset_name> <output_csv_path>`

Requires R (`Rscript`) on PATH. No R packages beyond base R are needed since
we load the `.rda` directly rather than installing `CASdatasets`.

Example:
```bash
Rscript src/fetch_cas_dataset.R beMTPL97 data/raw/beMTPL97.csv
```

Then in the notebook / Python:
```python
import pandas as pd
df = pd.read_csv("data/raw/beMTPL97.csv")
```

## Source
- Repo: `http://dutangc.perso.math.cnrs.fr/RRepository/`
- Tarball: `http://dutangc.perso.math.cnrs.fr/RRepository/pub/src/contrib/CASdatasets_1.2-1.tar.gz`
- Cached locally at `data/raw/CASdatasets_1.2-1.tar.gz` after first run (the tool
  reuses this cache instead of re-downloading).

## Known datasets used in this project
- **`beMTPL97`** — the canonical Belgian MTPL dataset (163,212 policyholders,
  1997 accident year) used in Henckaerts et al. (2018), *"A data driven
  binning strategy for the construction of insurance tariff classes"*, and
  widely reused in actuarial pricing/ML tutorials. Columns: `id`, `expo`,
  `claim`, `nclaims`, `amount`, `average`, `coverage`, `ageph`, `sex`, `bm`,
  `power`, `agec`, `fuel`, `use`, `fleet`, `postcode`, `long`, `lat`.
- `beMTPL16` also exists in the package (70,791 claims, different unknown
  Belgian insurer, different schema — vehicle brand/model, mileage, claim
  responsibility rate). Not the same dataset as `beMTPL97`; don't confuse
  the two if "Belgian MTPL" comes up again.

## Edge cases / things learned
- Don't `install.packages("CASdatasets", ...)` — it triggers a full source
  compile of a 245MB package you don't need just to read a data.frame.
  `load()`-ing the `.rda` directly is sufficient and much faster.
- The `average` column in `beMTPL97` is `NaN` for policies with zero claims
  (no average claim amount when there's nothing to average) — this is
  expected, not missing data, and applies to ~89% of rows.

# Gross-premium dashboard (Streamlit)

## Objective
Let someone enter a single policy's raw characteristics (age, bonus-malus,
horsepower, vehicle age, territory, fuel, use) and immediately see the
estimated claim frequency, severity, pure premium, and gross premium —
without opening the notebook or needing `statsmodels`.

## Why this approach
The notebook fits two GLMs (`final_model` for frequency, `severity_model`
for severity) and builds a rating table of relativities for each. Those
relativities fully determine `exp(Xβ)` for any combination of levels:
`prediction = base_rate × Π(relativity for each chosen level)`, where
`base_rate = exp(Intercept)`. That means a standalone app doesn't need
`statsmodels` or the fitted model objects at all — it just needs the
rating tables, the intercepts, the bin edges used to turn raw numbers into
levels, and the expense-loading assumptions. Exporting those as flat files
keeps the app lightweight (`pandas` only) and decoupled from the notebook's
heavier dependency stack (`geopandas`, `statsmodels`, `scikit-learn`).

## Required inputs
None — the export step reads everything it needs from variables already
in the notebook's kernel memory after running top to bottom.

## Step 1: regenerate the exported artifacts
Whenever the frequency or severity model changes (new predictors, new
bins, a refit), re-run the notebook end to end so the two export cells
(just before "## Example of calculating gross premiums") pick up the new
`final_model`, `severity_model`, `freq_rating`, `sev_rating`, and bin
variables, and rewrite:
- `data/processed/freq_rating_table.csv` — columns `variable, level, reference, coef, relativity, p_value, significant`
- `data/processed/sev_rating_table.csv` — same columns, one extra variable (`use`)
- `data/processed/model_config.json` — bin edges/labels for `bm`/`power`/`ageph`/`agec`, the 9 territory labels, `base_rates.{frequency,severity}` (`exp(Intercept)` for each model), and `expense_loadings.{fixed_expense,variable_expense_ratio,profit_contingency_loading}`

From the command line (equivalent to Run All in the kernel):
```bash
conda run -n base jupyter nbconvert --to notebook --execute --inplace "notebooks/pricing_project.ipynb"
```

These three files are regenerable intermediates, not deliverables — treat
them like everything else in `data/`.

## Step 2: install dependencies (one-time)
```bash
conda run -n base pip install -r requirements.txt
```
`requirements.txt` only lists `streamlit` and `pandas` — the app
deliberately avoids `statsmodels`/`numpy`/`geopandas` since it never
refits anything.

## Step 3: launch the app
```bash
cd "/Users/sachitsharma/Downloads/Projects-Actuary/Auto Insurance Pricing"
conda run -n base streamlit run app/streamlit_app.py
```
Opens at `http://localhost:8501`. Sliders/dropdowns are in the sidebar;
the four headline numbers (Frequency, Severity, Pure Premium, Gross
Premium) update live, and two expanders show the exact rating-table rows
used and the full rating tables.

## Code
- `src/premium_calculator.py` — `calculate_premium(age, bonus_malus, horsepower, vehicle_age, territory_label, fuel, use)` → dict with bins used, any clipped inputs, and all four predicted values. Clips out-of-range numeric inputs to the training range rather than erroring; raises `ValueError` for an invalid `territory_label`/`fuel`/`use` (the app's dropdowns prevent this in practice).
- `app/streamlit_app.py` — thin UI layer over `premium_calculator`.

## Gross premium formula
```
Gross Premium = (Pure Premium + Fixed Expense) / (1 - Variable Expense Ratio - Profit & Contingency Loading)
```
Current assumptions (set in the notebook's export cell, carried into
`model_config.json`): Fixed Expense = €60, Variable Expense Ratio = 25%,
Profit & Contingency Loading = 5%.

## Edge cases / things learned
- `build_rating_table()`'s output never includes the model's `Intercept` —
  only the `C(var)[T.level]` dummy coefficients. Forgetting to export
  `exp(Intercept)` as the base rate is the single easiest way to get a
  rating-table-only reconstruction subtly wrong (frequency/severity would
  be off by a constant multiplicative factor, not obviously broken).
- `sex` was removed entirely as a rating factor from the severity and
  Tweedie models (prohibited under regulations like the EU Gender
  Directive); the frequency model already excluded it on statistical
  grounds. The dashboard never asks for it.
- Verification baseline: age=40, bonus_malus=15, horsepower=60,
  vehicle_age=3, territory='1xxx - Brussels/Walloon-Brabant', fuel='diesel',
  use='private' → pred_frequency≈0.3082, pred_severity≈937.57,
  pred_pure_premium≈288.95, pred_gross_premium≈498.50. Re-check this after
  any change to the export cells or `premium_calculator.py`.

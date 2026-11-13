# Auto Insurance Pricing

Pricing model for Belgian motor third-party liability insurance (the
`beMTPL97` dataset): frequency and severity GLMs, rating tables, and a
Streamlit app for live premium quotes.

## Structure

```
data/
  raw/          # source dataset + cached downloads (gitignored, regenerate via src/fetch_*)
  processed/    # rating tables + model config exported by the notebook
notebooks/
  pricing_project.ipynb   # main analysis: EDA, GLMs, rating tables, diagnostics
src/
  fetch_cas_dataset.R         # downloads beMTPL97 from CASdatasets
  fetch_belgium_provinces.py  # downloads Belgium province boundaries for mapping
  premium_calculator.py       # reconstructs a premium from the exported rating tables
app/
  streamlit_app.py   # interactive premium quote dashboard
docs/
  load_cas_dataset.md       # how to fetch/refresh the raw dataset
  streamlit_dashboard.md    # how to regenerate artifacts and run the app
```

## Setup

```bash
pip install -r requirements.txt
```

## Running

1. Fetch the raw data (first time only) — see `docs/load_cas_dataset.md`.
2. Run `notebooks/pricing_project.ipynb` end to end to fit the models and
   export `data/processed/*`.
3. Launch the dashboard — see `docs/streamlit_dashboard.md`:
   ```bash
   streamlit run app/streamlit_app.py
   ```

"""Reconstructs frequency, severity, pure premium, and gross premium for a single
policy from the exported rating-table artifacts, without needing statsmodels.

Artifacts (produced by the notebook's export cells, under .tmp/):
  - freq_rating_table.csv, sev_rating_table.csv: per-level relativities
  - model_config.json: bin edges/labels, territory labels, base rates, expense loadings
"""
import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / ".tmp" / "model_config.json"
FREQ_RATING_PATH = PROJECT_ROOT / ".tmp" / "freq_rating_table.csv"
SEV_RATING_PATH = PROJECT_ROOT / ".tmp" / "sev_rating_table.csv"

FREQ_VARS = ["bm_bin", "power_bin", "ageph_bin", "agec_bin", "fuel", "territory"]
SEV_VARS = ["bm_bin", "power_bin", "ageph_bin", "agec_bin", "fuel", "use", "territory"]


def load_artifacts(config_path=CONFIG_PATH, freq_path=FREQ_RATING_PATH, sev_path=SEV_RATING_PATH):
    with open(config_path) as f:
        config = json.load(f)
    freq_rating = pd.read_csv(freq_path)
    sev_rating = pd.read_csv(sev_path)
    return config, freq_rating, sev_rating


def bin_value(value, feature, config):
    """Clip `value` into the training range for `feature` and return its bin label."""
    bin_cfg = config["bins"][feature]
    edges = bin_cfg["edges"]
    labels = bin_cfg["labels"]
    clipped = min(max(value, edges[0]), edges[-1])
    was_clipped = clipped != value
    label = pd.cut([clipped], bins=edges, labels=labels, include_lowest=True)[0]
    return str(label), was_clipped


def lookup_relativity(rating_df, variable, level):
    match = rating_df[(rating_df["variable"] == variable) & (rating_df["level"] == level)]
    if match.empty:
        return 1.0, False
    return float(match.iloc[0]["relativity"]), True


def calculate_premium(
    age,
    bonus_malus,
    horsepower,
    vehicle_age,
    territory_label,
    fuel,
    use,
    config=None,
    freq_rating=None,
    sev_rating=None,
):
    if config is None or freq_rating is None or sev_rating is None:
        config, freq_rating, sev_rating = load_artifacts()

    valid_territories = set(config["territory_labels"].values())
    if territory_label not in valid_territories:
        raise ValueError(f"territory_label must be one of {sorted(valid_territories)}")
    if fuel not in ("gasoline", "diesel"):
        raise ValueError("fuel must be 'gasoline' or 'diesel'")
    if use not in ("private", "work"):
        raise ValueError("use must be 'private' or 'work'")

    inputs_clipped = {}

    bm_bin, bm_clipped = bin_value(bonus_malus, "bm", config)
    power_bin, power_clipped = bin_value(horsepower, "power", config)
    ageph_bin, ageph_clipped = bin_value(age, "ageph", config)
    agec_bin, agec_clipped = bin_value(vehicle_age, "agec", config)

    if bm_clipped:
        inputs_clipped["bonus_malus"] = bonus_malus
    if power_clipped:
        inputs_clipped["horsepower"] = horsepower
    if ageph_clipped:
        inputs_clipped["age"] = age
    if agec_clipped:
        inputs_clipped["vehicle_age"] = vehicle_age

    bins = {
        "bm_bin": bm_bin,
        "power_bin": power_bin,
        "ageph_bin": ageph_bin,
        "agec_bin": agec_bin,
    }

    freq_levels = {
        "bm_bin": bm_bin,
        "power_bin": power_bin,
        "ageph_bin": ageph_bin,
        "agec_bin": agec_bin,
        "fuel": fuel,
        "territory": territory_label,
    }
    sev_levels = dict(freq_levels, use=use)

    unmatched = []

    freq_row_idx = []
    pred_frequency = config["base_rates"]["frequency"]
    for var in FREQ_VARS:
        rel, matched = lookup_relativity(freq_rating, var, freq_levels[var])
        if not matched:
            unmatched.append((var, freq_levels[var]))
        pred_frequency *= rel
        rows = freq_rating[(freq_rating["variable"] == var) & (freq_rating["level"] == freq_levels[var])]
        freq_row_idx.extend(rows.index.tolist())

    sev_row_idx = []
    pred_severity = config["base_rates"]["severity"]
    for var in SEV_VARS:
        rel, matched = lookup_relativity(sev_rating, var, sev_levels[var])
        if not matched:
            unmatched.append((var, sev_levels[var]))
        pred_severity *= rel
        rows = sev_rating[(sev_rating["variable"] == var) & (sev_rating["level"] == sev_levels[var])]
        sev_row_idx.extend(rows.index.tolist())

    if unmatched:
        raise ValueError(f"No rating-table entry for: {unmatched} — bin edges may be out of sync with model_config.json")

    pred_pure_premium = pred_frequency * pred_severity

    loadings = config["expense_loadings"]
    pred_gross_premium = (pred_pure_premium + loadings["fixed_expense"]) / (
        1 - loadings["variable_expense_ratio"] - loadings["profit_contingency_loading"]
    )

    return {
        "bins": bins,
        "inputs_clipped": inputs_clipped,
        "pred_frequency": pred_frequency,
        "pred_severity": pred_severity,
        "pred_pure_premium": pred_pure_premium,
        "pred_gross_premium": pred_gross_premium,
        "freq_rows": freq_rating.loc[freq_row_idx],
        "sev_rows": sev_rating.loc[sev_row_idx],
    }


if __name__ == "__main__":
    result = calculate_premium(
        age=40,
        bonus_malus=15,
        horsepower=60,
        vehicle_age=3,
        territory_label="1xxx - Brussels/Walloon-Brabant",
        fuel="diesel",
        use="private",
    )
    print("bins:", result["bins"])
    print("inputs_clipped:", result["inputs_clipped"])
    print(f"pred_frequency: {result['pred_frequency']:.6f}")
    print(f"pred_severity: {result['pred_severity']:.4f}")
    print(f"pred_pure_premium: {result['pred_pure_premium']:.4f}")
    print(f"pred_gross_premium: {result['pred_gross_premium']:.4f}")

#!/usr/bin/env python3
"""
predict_from_models.py

Loads latest CatBoost models & metadata from outputs/models/ and performs
a safe prediction based on user input + automatic fallbacks.

Usage:
    python predict_from_models.py

Notes:
 - Assumes models and metadata were saved in outputs/models/ by train_three_models.py
 - Looks for files like:
       metadata_Malaria_Risk_<TS>.json
       model_info_Malaria_Risk_<TS>.pkl
       catboost_Malaria_Risk_<TS>.cbm
 - Uses processed_dataset.csv (if present) to auto-fill lag features for a district when asked.
"""

import os
import glob
import json
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from catboost import CatBoostRegressor, Pool

OUTDIR = "outputs/models"
DATASET_CSV = "processed_dataset.csv"  # used for autofill if available

TARGETS = ["Malaria_Risk", "AD_Risk", "Typhoid_Risk"]

def find_latest_metadata(target):
    pattern = os.path.join(OUTDIR, f"metadata_{target}_*.json")
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None

def find_latest_model_info(target):
    pattern = os.path.join(OUTDIR, f"model_info_{target}_*.pkl")
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None

def find_latest_model_file(target):
    pattern = os.path.join(OUTDIR, f"catboost_{target}_*.cbm")
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None

def load_artifacts_for_target(target):
    meta_path = find_latest_metadata(target)
    info_path = find_latest_model_info(target)
    model_path = find_latest_model_file(target)
    if not (meta_path and info_path and model_path):
        return None
    with open(meta_path, "r") as fh:
        meta = json.load(fh)
    info = joblib.load(info_path)
    model = CatBoostRegressor()
    model.load_model(model_path)
    return {"meta": meta, "info": info, "model": model, "paths": {"meta": meta_path, "info": info_path, "model": model_path}}

def safe_median_map(df):
    """Return dict of medians for numeric columns in df."""
    med = {}
    for c in df.select_dtypes(include=[np.number]).columns:
        med[c] = float(df[c].median(skipna=True)) if not df[c].dropna().empty else 0.0
    return med

def try_autofill_from_dataset(dataset, district, feature_cols):
    """
    Attempt to obtain lag features from the provided dataset for the given district.
    Returns a dict {feature_name: value} for features it can fill.
    """
    out = {}
    if dataset is None:
        return out
    # prefer most recent weeks for that district
    dd = dataset[dataset['District'].astype(str).str.lower() == str(district).lower()].copy()
    if dd.empty:
        return out
    dd = dd.sort_values(['Year', 'week_index'], ascending=True)
    # get last row (most recent)
    last = dd.iloc[-1]
    # mapping heuristics - try fill *_lag1 as last week's corresponding base values
    # We support: Avg_rainfall_lag1/lag2, Avg_Temperature_lag1/lag2, Avg_Humidity_lag1/lag2,
    # Malaria_Risk_lag1 etc., and rolls if available.
    candidates = [
        "Avg_rainfall", "Avg_Temperature", "Avg_Humidity",
        "Malaria_Risk", "AD_Risk", "Typhoid_Risk"
    ]
    for base in candidates:
        # lag1: take last row's base; lag2: take second last if exists
        if f"{base}_lag1" in feature_cols:
            out[f"{base}_lag1"] = float(last.get(base, 0.0))
        if f"{base}_lag2" in feature_cols:
            # second last row
            if len(dd) >= 2:
                out[f"{base}_lag2"] = float(dd.iloc[-2].get(base, 0.0))
            else:
                out[f"{base}_lag2"] = float(0.0)
    # Try fill roll3/roll5 by computing means of last 3 or 5 base values if available
    for roll in ["Avg_rainfall", "Avg_Temperature", "Avg_Humidity", "Malaria_Risk", "AD_Risk", "Typhoid_Risk"]:
        for win in [3,5]:
            colname = f"{roll}_roll{win}"
            if colname in feature_cols:
                vals = dd[roll].dropna().astype(float).values
                if len(vals) >= 1:
                    out[colname] = float(vals[-win:].mean()) if len(vals) >= 1 else float(vals.mean() if len(vals)>0 else 0.0)
    return out

def build_input_row(feature_cols, cat_features, user_inputs, dataset_medians, autofill_vals):
    """
    Build a pandas DataFrame with one row containing values for feature_cols.
    Priority:
      1) user_inputs provided
      2) autofill_vals (from dataset)
      3) dataset_medians (median fallback)
      4) hard defaults (0)
    """
    row = {}
    for f in feature_cols:
        if f in user_inputs and user_inputs[f] is not None:
            row[f] = user_inputs[f]
        elif f in autofill_vals:
            row[f] = autofill_vals[f]
        elif f in dataset_medians:
            row[f] = dataset_medians[f]
        else:
            # special-case disease lags -> default 0
            if any(s in f.lower() for s in ["malaria_risk", "ad_risk", "typhoid_risk"]):
                # if it's a target lag/roll -> 0
                row[f] = 0.0
            else:
                row[f] = 0.0
    # enforce types for categorical columns: keep as string
    for c in cat_features:
        if c in row:
            row[c] = str(int(row[c])) if isinstance(row[c], (int, np.integer)) else str(row[c])
    # final dataframe
    df = pd.DataFrame([row], columns=feature_cols)
    return df

def main():
    print("Loading models and metadata from:", OUTDIR)
    artifacts = {}
    for t in TARGETS:
        art = load_artifacts_for_target(t)
        if art is None:
            print(f"WARNING: Could not find model/metadata for {t} in {OUTDIR}. Skipping {t}.")
        else:
            artifacts[t] = art
            print(f"Loaded {t} model from: {art['paths']['model']}")

    if not artifacts:
        print("No models found. Exit.")
        return

    # Load dataset if available (used for autofill medians/lag history)
    dataset = None
    if os.path.exists(DATASET_CSV):
        try:
            dataset = pd.read_csv(DATASET_CSV)
            print("Loaded dataset for autofill:", DATASET_CSV)
        except Exception as e:
            print("Could not load processed dataset for autofill:", e)

    # compute medians from dataset if available, else empty
    medians = safe_median_map(dataset) if dataset is not None else {}

    # Ask user for basic inputs
    print("\n--- User inputs (provide values or press Enter to skip where allowed) ---")
    district = input("District (string) [optional, helps autofill]: ").strip()
    # current-week weather & static
    def ask_float(prompt, allow_empty=True):
        v = input(prompt)
        if v.strip() == "" and allow_empty:
            return None
        try:
            return float(v)
        except:
            print("Invalid number, using None")
            return None

    Avg_rainfall = ask_float("Average Rainfall (mm) [current week] (press Enter to skip): ")
    Avg_Temperature = ask_float("Average Temperature (°C) [current week] (press Enter to skip): ")
    Avg_Humidity = ask_float("Average Humidity (%) [current week] (press Enter to skip): ")
    Population = ask_float("Population (press Enter to skip): ")
    Elevation_m = ask_float("Elevation (m) (press Enter to skip): ")
    rs = input("River Status (0=None,1=Border,2=Through) (press Enter to skip): ").strip()
    River_Status = int(rs) if rs != "" else None
    Area_sq_km = ask_float("Area (sq km) (press Enter to skip): ")
    Sanitation_Index = ask_float("Sanitation Index (0-1) (press Enter to skip): ")

    # Ask whether to attempt auto-fill of lags from dataset (if dataset present and district provided)
    autofill_vals = {}
    if dataset is not None and district:
        ans = input("Attempt auto-fill lag features from processed_dataset for this district (y/N)? ").strip().lower()
        if ans == "y":
            # choose the primary model's feature_cols to know what to try fill
            sample_target = next(iter(artifacts))
            feature_cols = artifacts[sample_target]['meta']['feature_cols']
            autofill_vals = try_autofill_from_dataset(dataset, district, feature_cols)
            if autofill_vals:
                print("Autofill found values for:", ", ".join(sorted(autofill_vals.keys())))
            else:
                print("No historical rows found for this district in dataset; autofill empty.")
    else:
        if dataset is None:
            print("No processed_dataset.csv found — autofill disabled.")
        else:
            print("District not supplied — autofill disabled.")

    # build a combined user_inputs dict using keys that models may expect
    # We'll use the feature_cols from the first model loaded as canonical ordering reference
    sample_target = next(iter(artifacts))
    canonical_feature_cols = artifacts[sample_target]['meta']['feature_cols']
    canonical_cat_features = artifacts[sample_target]['meta'].get('cat_features', [])

    # assemble user_inputs map
    user_inputs = {}
    # map only if value provided (not None)
    mapping = {
        "Avg_rainfall": Avg_rainfall,
        "Avg_Temperature": Avg_Temperature,
        "Avg_Humidity": Avg_Humidity,
        "Population": Population,
        "Elevation_m": Elevation_m,
        "River_Status": River_Status,
        "Area_sq_km": Area_sq_km,
        "Sanitation_Index": Sanitation_Index,
    }
    # include district if a feature
    if "District" in canonical_feature_cols:
        if district:
            user_inputs["District"] = str(district)
        else:
            # ask to choose one of known districts? skip, leave to median / default
            pass

    for k,v in mapping.items():
        if v is not None:
            user_inputs[k] = v

    # Build input row for each model (they should share same feature_cols in your pipeline)
    input_df = build_input_row(canonical_feature_cols, canonical_cat_features, user_inputs, medians, autofill_vals)

    # Final type enforcement: ensure categorical columns are strings
    for c in canonical_cat_features:
        if c in input_df.columns:
            input_df[c] = input_df[c].astype(str)

    print("\nFinal input dataframe (first row):")
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        print(input_df.head(1).T)

    # Predictions for each model
    print("\n--- Predictions ---")
    results = {}
    for t, art in artifacts.items():
        feature_cols = art['meta']['feature_cols']
        cat_feats = art['meta'].get('cat_features', [])
        model = art['model']
        # reorder input_df to feature_cols expected by this model; fill missing with medians or 0
        df_for_model = pd.DataFrame(columns=feature_cols)
        for c in feature_cols:
            if c in input_df.columns:
                df_for_model.at[0,c] = input_df.at[0,c]
            else:
                # fallback to median if available, else 0
                df_for_model.at[0,c] = medians.get(c, 0.0)
        # enforce categorical columns as strings (CatBoost expects str or int)
        for c in cat_feats:
            if c in df_for_model.columns:
                df_for_model[c] = df_for_model[c].astype(str)
        # create Pool to ensure CatBoost knows cat features
        cat_indices = [i for i, col in enumerate(feature_cols) if col in cat_feats]
        pool = Pool(df_for_model, cat_features=cat_indices) if cat_indices else Pool(df_for_model)
        pred = model.predict(pool)[0]
        results[t] = float(pred)
        print(f"{t}: {pred:.6f} (units: cases per 100k)")

    # Optional: present a small textual explanation of basis using feature importance if available
    print("\nTop contributing features (by training importance) - sample for Malaria_Risk:")
    sample_target = "Malaria_Risk"
    if sample_target in artifacts:
        fi_csv_pattern = os.path.join(OUTDIR, f"feature_importance_{sample_target}_*.csv")
        fi_files = sorted(glob.glob(fi_csv_pattern))
        if fi_files:
            try:
                fi_df = pd.read_csv(fi_files[-1])
                top3 = fi_df.sort_values("importance", ascending=False).head(5)
                for _, row in top3.iterrows():
                    print(f" - {row['feature']}: importance={row['importance']:.3f}")
            except Exception as e:
                pass

    print("\nDone. Save predictions or call this script programmatically for automation.")

if __name__ == "__main__":
    main()

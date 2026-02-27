#!/usr/bin/env python3
"""
test_predict_example.py

Example test script using a specific table entry (Abbottabad, week 43)
to demonstrate next-week disease risk prediction using CatBoost models.
Includes lag and rolling features.
"""

import pandas as pd
import joblib
from catboost import CatBoostRegressor, Pool
import os

model_dir = "outputs/models"
targets = ["Malaria_Risk_next_week", "AD_Risk_next_week", "Typhoid_Risk_next_week"]
models = {}
feature_cols = {}
cat_features = {}

for target in targets:
    info_file = [f for f in os.listdir(model_dir) if f"model_info_{target}" in f and f.endswith(".pkl")][0]
    info_file = os.path.join(model_dir, info_file)
    info = joblib.load(info_file)
    feature_cols[target] = info["feature_cols"]
    cat_features[target] = info["cat_features"]
    models[target] = CatBoostRegressor()
    models[target].load_model(info["model_path"])
    print(f"Loaded {target} model from: {info['model_path']}")

data = {
    "Year": 2024,
    "District": "Abbottabad",
    "week_index": 43,
    "Avg_rainfall": 0.0143,
    "Avg_Temperature": 19.9301,
    "Avg_Humidity": 54.2137,
    "Population": 1419072,
    "Elevation_m": 1256,
    "River_Status": 0,
    "Area_sq_km": 1967,
    "Sanitation_Index": 0.75,
    "Malaria_cases": 3,
    "AD_cases": 437,
    "Typhoid_cases": 23,
    "Malaria_Risk": 0.021140576376674332,
    "AD_Risk": 3.079477292202228,
    "Typhoid_Risk": 0.16207775222116988,
    "Avg_rainfall_lag1": 0.0,
    "Avg_rainfall_lag2": 1.1143,
    "Avg_Temperature_lag1": 20.545,
    "Avg_Temperature_lag2": 19.7137,
    "Avg_Humidity_lag1": 49.9082,
    "Avg_Humidity_lag2": 56.4356,
    "Avg_rainfall_roll3": 0.3762,
    "Avg_rainfall_roll5": 0.98108,
    "Avg_Temperature_roll3": 20.062933333333334,
    "Avg_Temperature_roll5": 21.19444,
    "Avg_Humidity_roll3": 53.51916666666667,
    "Avg_Humidity_roll5": 58.55016
}

df_input = pd.DataFrame([data])
for target in targets:
    for col in feature_cols[target]:
        if col not in df_input.columns:
            df_input[col] = 0.0

print("\n--- Predictions for Next Week ---")
predictions = {}
for target in targets:
    model = models[target]
    cols = feature_cols[target]
    cat_idx = [cols.index(c) for c in cat_features[target] if c in cols]
    raw_pred = model.predict(Pool(df_input[cols], cat_features=cat_idx))[0]
    pred = max(0, raw_pred)
    predictions[target] = round(pred, 4)
    print(f"{target}: {predictions[target]} (cases per 10,000)")

print("\nActual Risks: \nMalaria_Risk: 0.02114 \nAD_Risk: 3.536869165 \nTyphoid_Risk: 0.1409")

print("\nTest script complete.")
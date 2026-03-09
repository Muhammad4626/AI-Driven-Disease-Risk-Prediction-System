import pandas as pd
import numpy as np

df = pd.read_csv("final_master_dataset.csv")

# ---------------------------------
# Clean column names
# ---------------------------------
df.columns = df.columns.str.strip().str.replace(" ", "_")

# ---------------------------------
# Convert numeric columns
# ---------------------------------
numeric_cols = [
    "avg_rainfall", "avg_temperature", "avg_humidity", "population",
    "elevation_m", "river_status", "area_sq_km", "sanitation_index",
    "malaria_cases", "ad_cases", "typhoid_cases",
    "flood_inundation", "stagnant_water", "mean_ndvi"
]

for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# ---------------------------------
# Remove invalid population rows
# ---------------------------------
df = df.dropna(subset=["population"])
df = df[df["population"] > 0]

# ---------------------------------
# Fill environmental missing values
# ---------------------------------
env_cols = ["avg_rainfall", "avg_temperature", "avg_humidity",
            "flood_inundation", "stagnant_water", "mean_ndvi"]

for col in env_cols:
    if col in df.columns:
        df[col] = df[col].fillna(0)

# ---------------------------------
# Fill static district features
# ---------------------------------
static_cols = ["elevation_m", "river_status", "area_sq_km", "sanitation_index"]

for col in static_cols:
    if col in df.columns:
        df[col] = df[col].fillna(df[col].mean())

# ---------------------------------
# Sort correctly
# ---------------------------------
df = df.sort_values(by=["district", "year", "week_index"]).reset_index(drop=True)

# ---------------------------------
# Calculate disease RISK (incidence per 10,000)
# ---------------------------------
df["malaria_risk"]   = (df["malaria_cases"]   / df["population"]) * 10000
df["ad_risk"]        = (df["ad_cases"]        / df["population"]) * 10000
df["typhoid_risk"]   = (df["typhoid_cases"]   / df["population"]) * 10000

# ---------------------------------
# Shift target → predict NEXT week's RISK
# ---------------------------------
df['malaria_risk_next_week']  = df.groupby("district")['malaria_risk'].shift(-1)
df['ad_risk_next_week']       = df.groupby("district")['ad_risk'].shift(-1)
df['typhoid_risk_next_week']  = df.groupby("district")['typhoid_risk'].shift(-1)

# Drop rows where we can't predict next week
df = df.dropna(subset=["malaria_risk_next_week", "ad_risk_next_week", "typhoid_risk_next_week"])

# ---------------------------------
# We no longer need raw cases as features → drop them
# ---------------------------------
df = df.drop(columns=["malaria_cases", "ad_cases", "typhoid_cases"], errors='ignore')

# ---------------------------------
# Lag Features (env + RISK scores)
# ---------------------------------
lag_features = [
    "avg_rainfall", "avg_temperature", "avg_humidity",
    "flood_inundation", "stagnant_water", "mean_ndvi",
    "malaria_risk", "ad_risk", "typhoid_risk"          # ← now included
]

for feature in lag_features:
    if feature in df.columns:
        df[f"{feature}_lag1"] = df.groupby("district")[feature].shift(1)
        df[f"{feature}_lag2"] = df.groupby("district")[feature].shift(2)

df.fillna(0, inplace=True)

# ---------------------------------
# Rolling Features (env + RISK scores)
# ---------------------------------
rolling_features = lag_features  # same list

for feature in rolling_features:
    if feature in df.columns:
        df[f"{feature}_roll3"] = (
            df.groupby("district")[feature]
              .rolling(3)
              .mean()
              .reset_index(level=0, drop=True)
        )
        df[f"{feature}_roll5"] = (
            df.groupby("district")[feature]
              .rolling(5)
              .mean()
              .reset_index(level=0, drop=True)
        )

df.fillna(0, inplace=True)

# ---------------------------------
# Remove extreme outliers (99th percentile on targets)
# ---------------------------------
for risk in ["malaria_risk_next_week", "ad_risk_next_week", "typhoid_risk_next_week"]:
    if risk in df.columns:
        limit = df[risk].quantile(0.99)
        df = df[df[risk] <= limit]

# ---------------------------------
# Save processed file
# ---------------------------------
df.to_csv("processed_dataset_risk_based.csv", index=False)

print("\nFeature Engineering Complete (risk-based version)")
print("Saved as: processed_dataset_risk_based.csv")
print("Columns:", df.columns.tolist())
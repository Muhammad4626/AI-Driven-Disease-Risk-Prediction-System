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
    "Avg_rainfall", "Avg_Temperature", "Avg_Humidity", "Population",
    "Elevation_m", "River_Status", "Area_sq_km", "Sanitation_Index",
    "Malaria_cases", "AD_cases", "Typhoid_cases",
    "Flood_Inundation", "Stagnant_Water", "Mean_NDVI"
]

for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# ---------------------------------
# Remove invalid population rows
# ---------------------------------
df = df.dropna(subset=["Population"])
df = df[df["Population"] > 0]

# ---------------------------------
# Fill environmental missing values
# ---------------------------------
env_cols = ["Avg_rainfall", "Avg_Temperature", "Avg_Humidity",
            "Flood_Inundation", "Stagnant_Water", "Mean_NDVI"]

for col in env_cols:
    if col in df.columns:
        df[col] = df[col].fillna(0)

# ---------------------------------
# Fill static district features
# ---------------------------------
static_cols = ["Elevation_m", "River_Status", "Area_sq_km", "Sanitation_Index"]

for col in static_cols:
    if col in df.columns:
        df[col] = df[col].fillna(df[col].mean())

# ---------------------------------
# Sort correctly
# ---------------------------------
df = df.sort_values(by=["District", "Year", "week_index"]).reset_index(drop=True)

# ---------------------------------
# Calculate disease risk
# ---------------------------------
df["Malaria_Risk"] = (df["Malaria_cases"] / df["Population"]) * 10000
df["AD_Risk"] = (df["AD_cases"] / df["Population"]) * 10000
df["Typhoid_Risk"] = (df["Typhoid_cases"] / df["Population"]) * 10000

# ---------------------------------
# Shift target (predict next week)
# ---------------------------------
df['Malaria_Risk_next_week'] = df.groupby("District")['Malaria_Risk'].shift(-1)
df['AD_Risk_next_week'] = df.groupby("District")['AD_Risk'].shift(-1)
df['Typhoid_Risk_next_week'] = df.groupby("District")['Typhoid_Risk'].shift(-1)

# Remove last week per district
df = df.groupby('District').apply(lambda x: x.iloc[:-1]).reset_index(drop=True)

# ---------------------------------
# Lag Features (INCLUDING FLOOD)
# ---------------------------------
lag_features = [
    "Avg_rainfall", "Avg_Temperature", "Avg_Humidity",
    "Flood_Inundation", "Stagnant_Water", "Mean_NDVI"
]

for feature in lag_features:
    if feature in df.columns:
        df[f"{feature}_lag1"] = df.groupby("District")[feature].shift(1)
        df[f"{feature}_lag2"] = df.groupby("District")[feature].shift(2)

df.fillna(0, inplace=True)

# ---------------------------------
# Rolling Features (INCLUDING FLOOD)
# ---------------------------------
rolling_features = [
    "Avg_rainfall", "Avg_Temperature", "Avg_Humidity",
    "Flood_Inundation", "Stagnant_Water", "Mean_NDVI"
]

for feature in rolling_features:
    if feature in df.columns:
        df[f"{feature}_roll3"] = (
            df.groupby("District")[feature]
              .rolling(3)
              .mean()
              .reset_index(level=0, drop=True)
        )
        df[f"{feature}_roll5"] = (
            df.groupby("District")[feature]
              .rolling(5)
              .mean()
              .reset_index(level=0, drop=True)
        )

df.fillna(0, inplace=True)

# ---------------------------------
# Remove extreme outliers (99th percentile)
# ---------------------------------
for risk in ["Malaria_Risk_next_week", "AD_Risk_next_week", "Typhoid_Risk_next_week"]:
    limit = df[risk].quantile(0.99)
    df = df[df[risk] <= limit]

# ---------------------------------
# Save
# ---------------------------------
df.to_csv("processed_dataset.csv", index=False)

print("\nFeature Engineering Complete\n")
print("Saved as processed_dataset.csv\n")
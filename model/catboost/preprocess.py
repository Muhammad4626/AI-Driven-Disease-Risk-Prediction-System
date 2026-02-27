import pandas as pd
import numpy as np

df = pd.read_csv("final_flood_disease_data.csv")

df.columns = df.columns.str.strip().str.replace(" ", "_")

numeric_cols = [
    "Avg_rainfall", "Avg_Temperature", "Avg_Humidity", "Population",
    "Elevation_m", "River_Status", "Area_sq_km", "Sanitation_Index",
    "Malaria_cases", "AD_cases", "Typhoid_cases"
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

#drop rows with no population
df = df.dropna(subset=["Population"])
df = df[df["Population"] > 0]

env_cols = ["Avg_rainfall", "Avg_Temperature", "Avg_Humidity"]
df[env_cols] = df[env_cols].fillna(0)

#fill district-level static feature gaps with mean
static_cols = ["Elevation_m", "River_Status", "Area_sq_km", "Sanitation_Index"]
for col in static_cols:
    df[col] = df[col].fillna(df[col].mean())

#sorting
df = df.sort_values(by=["District", "Year", "week_index"]).reset_index(drop=True)

#calculate disease risk per 10000 people
df["Malaria_Risk"] = (df["Malaria_cases"] / df["Population"]) * 10000
df["AD_Risk"] = (df["AD_cases"] / df["Population"]) * 10000
df["Typhoid_Risk"] = (df["Typhoid_cases"] / df["Population"]) * 10000

#risk columns shifted upwards
df['Malaria_Risk_next_week'] = df.groupby("District")['Malaria_Risk'].shift(-1)
df['AD_Risk_next_week'] = df.groupby("District")['AD_Risk'].shift(-1)
df['Typhoid_Risk_next_week'] = df.groupby("District")['Typhoid_Risk'].shift(-1)

#last column of every district dropped
df = df.groupby('District').apply(lambda x: x.iloc[:-1]).reset_index(drop=True)

#lag features
lag_features = ["Avg_rainfall", "Avg_Temperature", "Avg_Humidity"]

for feature in lag_features:
    df[f"{feature}_lag1"] = df.groupby("District")[feature].shift(1)
    df[f"{feature}_lag2"] = df.groupby("District")[feature].shift(2)

df.fillna(0, inplace=True)

#rolling features
rolling_features = ["Avg_rainfall", "Avg_Temperature", "Avg_Humidity"]

for feature in rolling_features:
    df[f"{feature}_roll3"] = df.groupby("District")[feature].rolling(3).mean().reset_index(level=0, drop=True)
    df[f"{feature}_roll5"] = df.groupby("District")[feature].rolling(5).mean().reset_index(level=0, drop=True)

df.fillna(0, inplace=True)

#removing outliers
for risk in ["Malaria_Risk_next_week", "AD_Risk_next_week", "Typhoid_Risk_next_week"]:
    limit = df[risk].quantile(0.99)
    df = df[df[risk] <= limit]

#save dataset
df.to_csv("processed_dataset.csv", index=False)

print(" \nFeature Engineering Complete  \n")
print(" Saved as processed_dataset.csv\n")

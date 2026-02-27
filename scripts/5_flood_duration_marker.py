# 5_flood_duration_marker.py
import os
import pandas as pd

INPUT_CSV = "outputs/displaced_fatalities_cases.csv"
OUTPUT_CSV = "outputs/flood_duration_marker.csv"
os.makedirs("outputs", exist_ok=True)
YEAR = 2022

df = pd.read_csv(INPUT_CSV)
rows = []

# For simplicity, assume flood lasted from June-Oct, 2022
for _, row in df.iterrows():
    district = row["District"]
    # monthly granularity, multiple rows per district (June=6..Oct=10)
    for month in range(6,11):
        rows.append({
            "Year": YEAR,
            "District": district,
            "Month_Index": month,
            "Flood_Duration_Days": 30,  # rough approximation
            "Flood_Marker": 1
        })

pd.DataFrame(rows).to_csv(OUTPUT_CSV, index=False)
print("Flood duration/marker CSV saved:", OUTPUT_CSV)

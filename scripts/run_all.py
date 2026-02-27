# run_all.py
import os
import pandas as pd

scripts = [
    "1_geocode_districts.py",
    "2_weather_nasa_power.py",
    "3_population_density.py",
    "4_displaced_fatalities_cases.py",
    "5_flood_duration_marker.py",
    "6_waterbody_proximity.py",
    "7_flood_severity_index.py"
]

for s in scripts:
    print("Running", s)
    os.system(f"python {s}")

# Merge CSVs
csv_files = [
    "outputs/geocode_districts.csv",
    "outputs/weather_2022.csv",
    "outputs/population_density.csv",
    "outputs/displaced_fatalities_cases.csv",
    "outputs/flood_duration_marker.csv",
    "outputs/waterbody_proximity.csv",
    "outputs/flood_severity_index.csv"
]

dfs = [pd.read_csv(f) for f in csv_files]

from functools import reduce
df_merged = reduce(lambda left,right: pd.merge(left,right,on=["Year","District"], how="outer"), dfs)

df_merged.to_csv("outputs/pakistan_flood_2022_final_dataset.csv", index=False)
print("Final merged CSV saved: outputs/pakistan_flood_2022_final_dataset.csv")

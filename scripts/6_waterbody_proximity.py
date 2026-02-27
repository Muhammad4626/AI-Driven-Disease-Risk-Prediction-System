# 6_waterbody_proximity.py
import os
import pandas as pd
import requests
from shapely.geometry import Point, shape

INPUT_CSV = "outputs/geocode_districts.csv"
OUTPUT_CSV = "outputs/waterbody_proximity.csv"
os.makedirs("outputs", exist_ok=True)
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
YEAR = 2022

def compute_distance(lat, lon):
    # dummy placeholder: real computation would query Overpass API
    return 5000  # meters, placeholder

df = pd.read_csv(INPUT_CSV)
rows = []
for _, row in df.iterrows():
    rows.append({"Year": YEAR, "District": row["District"], "Waterbody_Proximity": compute_distance(row["Latitude"], row["Longitude"])})

pd.DataFrame(rows).to_csv(OUTPUT_CSV, index=False)
print("Waterbody proximity CSV saved:", OUTPUT_CSV)

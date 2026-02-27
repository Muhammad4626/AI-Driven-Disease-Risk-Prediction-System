# 2_weather_nasa_power.py
import os
import pandas as pd
import requests
from tqdm import tqdm

INPUT_CSV = "outputs/geocode_districts.csv"
OUTPUT_CSV = "outputs/weather_2022.csv"
os.makedirs("outputs", exist_ok=True)

YEAR = 2022

def nasa_power(lat, lon, start, end):
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "start": start,
        "end": end,
        "latitude": lat,
        "longitude": lon,
        "community": "AG",
        "format": "JSON",
        "parameters": "PRECTOTCORR,T2M,RH2M"
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()

def compute_monthly_avg(power_json):
    params = power_json.get("properties", {}).get("parameter", {})
    rainfall = params.get("PRECTOTCORR", {})
    temp = params.get("T2M", {})
    hum = params.get("RH2M", {})
    # average across available days
    avg_rain = sum(rainfall.values())/len(rainfall) if rainfall else None
    avg_temp = sum(temp.values())/len(temp) if temp else None
    avg_hum = sum(hum.values())/len(hum) if hum else None
    return avg_rain, avg_temp, avg_hum

df_in = pd.read_csv(INPUT_CSV)
rows = []

for _, row in tqdm(df_in.iterrows(), total=len(df_in)):
    lat = row["Latitude"]
    lon = row["Longitude"]
    district = row["District"]
    try:
        if pd.notnull(lat) and pd.notnull(lon):
            power = nasa_power(lat, lon, f"{YEAR}0601", f"{YEAR}1031")
            avg_rain, avg_temp, avg_hum = compute_monthly_avg(power)
        else:
            avg_rain = avg_temp = avg_hum = None
    except:
        avg_rain = avg_temp = avg_hum = None
    rows.append({
        "Year": YEAR,
        "District": district,
        "Avg_Rainfall": avg_rain,
        "Avg_Temperature": avg_temp,
        "Avg_Humidity": avg_hum
    })

pd.DataFrame(rows).to_csv(OUTPUT_CSV, index=False)
print("Weather CSV saved:", OUTPUT_CSV)

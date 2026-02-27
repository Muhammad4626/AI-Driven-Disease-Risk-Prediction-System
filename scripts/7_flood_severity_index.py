# 7_flood_severity_index.py
import os
import pandas as pd

POP_CSV = "outputs/displaced_fatalities_cases.csv"
WEATHER_CSV = "outputs/weather_2022.csv"
OUTPUT_CSV = "outputs/flood_severity_index.csv"
os.makedirs("outputs", exist_ok=True)

df_pop = pd.read_csv(POP_CSV)
df_weather = pd.read_csv(WEATHER_CSV)

rows = []
for _, pop_row in df_pop.iterrows():
    district = pop_row["District"]
    weather_row = df_weather[df_weather["District"]==district].iloc[0] if not df_weather[df_weather["District"]==district].empty else {}
    displaced = pop_row.get("People_Displaced")
    fatalities = pop_row.get("Fatalities")
    rain30 = weather_row.get("Avg_Rainfall")
    score = 0
    if pd.notnull(displaced): score += min(displaced/1000.0,50)
    if pd.notnull(fatalities): score += min(fatalities*0.5,20)
    if pd.notnull(rain30): score += min(rain30/50.0,30)
    score = round(score,2) if score>0 else None
    rows.append({"Year": 2022, "District": district, "Flood_Severity_Index": score})

pd.DataFrame(rows).to_csv(OUTPUT_CSV, index=False)
print("Flood severity index CSV saved:", OUTPUT_CSV)

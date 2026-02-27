# 4_displaced_fatalities_cases.py
import os
import pandas as pd
import requests
import json
import re
from tqdm import tqdm

OUTPUT_CSV = "outputs/displaced_fatalities_cases.csv"
os.makedirs("outputs", exist_ok=True)

DISTRICTS = pd.read_csv("outputs/geocode_districts.csv")["District"].tolist()
YEAR = 2022

def reliefweb_search(district):
    base = "https://api.reliefweb.int/v1/reports"
    params = {"query": f'("{district}" AND {YEAR} AND flood)'}
    try:
        r = requests.get(base, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except:
        return None

def extract_numbers(text):
    nums = {}
    m = re.search(r'([0-9,]+)\s+(?:people|persons)?\s*(?:displaced|evacuated)', text, re.I)
    if m: nums["People_Displaced"]=int(m.group(1).replace(",",""))
    m2 = re.search(r'([0-9,]+)\s+(?:people|persons)?\s*(?:killed|died|dead)', text, re.I)
    if m2: nums["Fatalities"]=int(m2.group(1).replace(",",""))
    # disease cases crude: look for "X cholera", "X dengue", "X malaria"
    m3 = re.search(r'([0-9,]+)\s*cholera', text, re.I)
    if m3: nums["Cholera_Cases"]=int(m3.group(1).replace(",",""))
    m4 = re.search(r'([0-9,]+)\s*dengue', text, re.I)
    if m4: nums["Dengue_Cases"]=int(m4.group(1).replace(",",""))
    m5 = re.search(r'([0-9,]+)\s*malaria', text, re.I)
    if m5: nums["Malaria_Cases"]=int(m5.group(1).replace(",",""))
    return nums

rows = []
for district in tqdm(DISTRICTS):
    data = reliefweb_search(district)
    displaced=fatalities=cholera=dengue=malaria=None
    if data and "data" in data:
        for item in data["data"][:5]:  # top 5 reports
            text = json.dumps(item)
            nums = extract_numbers(text)
            displaced = displaced or nums.get("People_Displaced")
            fatalities = fatalities or nums.get("Fatalities")
            cholera = cholera or nums.get("Cholera_Cases")
            dengue = dengue or nums.get("Dengue_Cases")
            malaria = malaria or nums.get("Malaria_Cases")
    rows.append({
        "Year": YEAR,
        "District": district,
        "People_Displaced": displaced,
        "Fatalities": fatalities,
        "Cholera_Cases": cholera,
        "Malaria_Cases": malaria,
        "Dengue_Cases": dengue
    })

pd.DataFrame(rows).to_csv(OUTPUT_CSV, index=False)
print("Displaced/fatalities/cases CSV saved:", OUTPUT_CSV)

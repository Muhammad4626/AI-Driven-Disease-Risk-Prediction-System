# 3_population_density.py
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

INPUT_CSV = "outputs/geocode_districts.csv"
OUTPUT_CSV = "outputs/population_density.csv"
os.makedirs("outputs", exist_ok=True)

WIKI_BASE = "https://en.wikipedia.org/wiki/"

def get_population_density(district):
    candidates = [district.replace(" ", "_")+"_District", district.replace(" ", "_")]
    for c in candidates:
        url = WIKI_BASE + c
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "lxml")
            infobox = soup.find("table", {"class":"infobox"})
            if infobox:
                pop = area = None
                for row in infobox.find_all("tr"):
                    th = row.find("th")
                    td = row.find("td")
                    if not th or not td:
                        continue
                    key = th.get_text(strip=True).lower()
                    val = td.get_text(" ", strip=True)
                    if "population" in key and pop is None:
                        pop = int(''.join(filter(str.isdigit,val)))
                    if "area" in key and area is None:
                        area = float(''.join(filter(lambda x: x.isdigit() or x=='.', val)))
                if pop and area:
                    return round(pop/area,2)
        except:
            continue
    return None

df_in = pd.read_csv(INPUT_CSV)
rows = []

for _, row in tqdm(df_in.iterrows(), total=len(df_in)):
    district = row["District"]
    pdens = get_population_density(district)
    rows.append({"Year": 2022, "District": district, "Population_Density": pdens})

pd.DataFrame(rows).to_csv(OUTPUT_CSV, index=False)
print("Population density CSV saved:", OUTPUT_CSV)

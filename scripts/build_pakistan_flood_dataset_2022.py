"""
build_pakistan_flood_dataset_2022.py
End-to-end pipeline (best-effort) to build dataset for 2022 flood-affected Pakistani districts.
Outputs: outputs/pakistan_flood_2022_dataset.csv and debug JSONs.

NOTE: Some fields (NDVI, Healthcare_Access_Index, some PDF-extracted numbers) require manual/credentialed steps.
Read inline comments for where to enable extra APIs (Google Earth Engine, Tabula, etc).
"""

import os
import time
import json
import math
import requests
import pandas as pd
from bs4 import BeautifulSoup
from dateutil import parser as dateparser
from datetime import datetime, timedelta, date
from shapely.geometry import Point, shape
from shapely.ops import nearest_points
from geopy.geocoders import Nominatim
from tqdm import tqdm

# ---------------------------
# CONFIG
# ---------------------------
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

CSV_OUT = os.path.join(OUTPUT_DIR, "pakistan_flood_2022_dataset.csv")

# District names provided by you (kept exact)
DISTRICTS = [
"East Karachi","West Karachi","South Karachi","Central Karachi","Malir Karachi","Korangi Karachi",
"Hyderabad","Jamshoro","Dadu","Matiari","Tando Allahyar","Tando Muhammad Khan","Thatta","Sujawal",
"Badin","Sukkur","Khairpur","Ghotki","Shaheed Benazirabad","Naushehro Feroze","Sanghar","Larkana",
"Kambar Shahdadkot","Shikarpur","Jacobabad","Kashmore","Mirpur Khas","Umer Kot","Tharparkar",
"Dera Ghazi Khan","Rajanpur","Muzaffargarh","Layyah","Bahawalpur","Bahawalnagar","Rahim Yar Khan",
"Mianwali","Khushab","Sargodha","Chiniot","Jhang","Khanewal","Multan","Vehari","Lodhran","Okara",
"Sheikhupura","Hafizabad","Gujranwala","Swat","Nowshera","Charsadda","Upper Dir","Lower Dir",
"Peshawar","Shangla","Kohistan","Dera Ismail Khan","Bannu","Lakki Marwat","Chitral","Kurram","Tank",
"Hangu","Lasbela","Jhal Magsi","Sohbatpur","Washuk","Dera Allah Yar","Kharan","Kalat","Naseerabad",
"Barkhan","Sibi","Loralai","Kachi","Musakhel"
]

YEAR = 2022

# ---------------------------
# FIELDS / OUTPUT SCHEMA
# ---------------------------
OUTPUT_FIELDS = [
"Year","District","Flood_Severity_Index","Flood_Duration_Days","Rainfall_Last_7Days",
"Rainfall_Last_30Days","Avg_Temperature","Avg_Humidity","Population_Density",
"People_Displaced","Fatalities","Healthcare_Access_Index","NDVI_Index",
"Flood_Recurrence_Count","Days_Since_Flood_Start","Month_Index","Waterbody_Proximity",
"Flood_Marker","Climate_Anomaly_Score","Cholera_cases","Malaria_cases","Dengue_cases",
"SourceNotes"
]

# ---------------------------
# UTIL: Normalize district -> used for geocoding / queries
# ---------------------------
def norm_name(n):
    # small normalization to help geocoding
    return n.replace(" ", "+").replace("Karachi+", "Karachi+")

# ---------------------------
# 1) Geocode district to lat/lon (Nominatim) -- fairly reliable for district centroids
# ---------------------------
geolocator = Nominatim(user_agent="pakistan_flood_dataset_builder", timeout=10)

def geocode_district(district):
    query = f"{district}, Pakistan"
    try:
        loc = geolocator.geocode(query)
        if loc:
            return {"lat": loc.latitude, "lon": loc.longitude, "display_name": loc.address}
    except Exception as e:
        # backoff
        time.sleep(1)
    return None

# ---------------------------
# 2) NASA POWER helper (no key)
#    We'll call daily data for the district centroid for days around typical flood months (2022 monsoon)
#    Docs: https://power.larc.nasa.gov/docs/services/api/v2/
# ---------------------------
def nasa_power_timeseries(lat, lon, start, end):
    """
    returns daily rainfall (PRECTOTCORR), t2m (avg temp), rh2m (rel hum) aggregated
    start, end as YYYYMMDD strings
    """
    base = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "start": start,
        "end": end,
        "latitude": lat,
        "longitude": lon,
        "community": "AG",
        "format": "JSON",
        "parameters": ",".join(["PRECTOTCORR","T2M","RH2M"])
    }
    r = requests.get(base, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

# compute rainfall sums/averages
def compute_rain_temp_humidity_from_power(power_json, ref_date):
    # power_json daily structure: properties -> parameter -> PRECTOTCORR -> '20220101': value
    props = power_json.get("properties", {})
    params = props.get("parameter", {})
    # Build ordered time series
    prec = params.get("PRECTOTCORR", {})
    t2m = params.get("T2M", {})
    rh2m = params.get("RH2M", {})
    # convert ref_date string to date
    rd = dateparser.parse(ref_date).date()
    # sum last 7 and 30 days relative to ref_date
    sum7 = 0.0; count7=0
    sum30=0.0; count30=0
    temp_vals=[]; hum_vals=[]
    for i in range(0,31):
        d = rd - timedelta(days=i)
        key = d.strftime("%Y%m%d")
        if key in prec:
            val = prec[key] or 0.0
            if i < 7:
                sum7 += val; count7 += 1
            sum30 += val; count30 += 1
        if key in t2m:
            tv = t2m[key]
            if tv is not None:
                temp_vals.append(tv)
        if key in rh2m:
            hv = rh2m[key]
            if hv is not None:
                hum_vals.append(hv)
    avg_temp = sum(temp_vals)/len(temp_vals) if temp_vals else None
    avg_hum = sum(hum_vals)/len(hum_vals) if hum_vals else None
    return {"rain7": sum7, "rain30": sum30, "avg_temp": avg_temp, "avg_hum": avg_hum}

# ---------------------------
# 3) Population & area -> population density: try Wikipedia first
# ---------------------------
WIKI_BASE = "https://en.wikipedia.org/wiki/"

def fetch_wikipedia_population_area(district):
    # try common patterns: "Dadu District" etc.
    candidates = []
    # heuristic for Sindh/Punjab etc:
    if district.lower().endswith("karachi"):
        # Karachi subdivisions have pages like "Karachi East District"
        candidates.append(district.replace(" ", "_") + "_District")
    else:
        candidates.append(district.replace(" ", "_") + "_District")
        candidates.append(district.replace(" ", "_"))
    for c in candidates:
        url = WIKI_BASE + c
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "lxml")
            infobox = soup.find("table", {"class": "infobox"})
            if infobox:
                text = infobox.get_text(" | ", strip=True)
                # crude extraction: look for "Population" and "Area"
                pop = None; area = None
                for row in infobox.find_all("tr"):
                    th = row.find("th")
                    td = row.find("td")
                    if not th or not td:
                        continue
                    key = th.get_text(strip=True).lower()
                    val = td.get_text(" ", strip=True)
                    if "population" in key and pop is None:
                        # remove references and commas
                        pop = ''.join(ch for ch in val if ch.isdigit() or ch=='.')
                        try:
                            pop = int(pop)
                        except:
                            pop = None
                    if ("area" in key or "total area" in key) and area is None:
                        area = ''.join(ch for ch in val if ch.isdigit() or ch=='.')
                        try:
                            area = float(area)
                        except:
                            area = None
                if pop or area:
                    return {"population": pop, "area_km2": area, "wiki_url": url}
        except Exception as e:
            continue
    return None

# ---------------------------
# 4) ReliefWeb simple search to get text snippets for "displaced" / "killed" numbers
#    ReliefWeb API: https://api.reliefweb.int
# ---------------------------
def reliefweb_search(district, year=2022):
    base = "https://api.reliefweb.int/v1/reports"
    q = f'fields[title]=true&query=value:("{district}" AND 2022 AND flood)'
    params = {
        "appname": "pak-flood-dataset-builder",
        "query": f'("{district}" AND 2022 AND flood)'
    }
    try:
        r = requests.get(base, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return None

def extract_numbers_from_text(text):
    # crude regexes: displacement often "X people" or "X displaced"
    import re
    nums = {}
    # displaced
    m = re.search(r'([0-9,]{3,})\s+(?:people|persons|pop\.)? (?:were )?(?:displaced|affected|evacuated)', text, flags=re.IGNORECASE)
    if m:
        nums["displaced"] = int(m.group(1).replace(",",""))
    m2 = re.search(r'([0-9,]{1,6})\s+(?:people|persons|people )?(?:killed|died|dead)', text, flags=re.IGNORECASE)
    if m2:
        nums["fatalities"] = int(m2.group(1).replace(",",""))
    # fallback any number near word 'displaced' or 'killed'
    if "displaced" in text.lower() and "displaced" not in nums:
        m3 = re.search(r'([0-9,]{2,})\s+displaced', text, flags=re.IGNORECASE)
        if m3:
            nums["displaced"] = int(m3.group(1).replace(",",""))
    return nums

# ---------------------------
# 5) Overpass API: distance to nearest waterbody (river/lake)
#    We'll query for waterways within a bounding box and compute shortest distance to district centroid
# ---------------------------
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def query_nearest_waterway(lat, lon, radius_m=50000):
    # bounding box ~ radius (degrees approx) - use small approx conversion
    # for reliable results, ask for waterways within radius in meters using around
    # We'll search for any waterway node/way with "waterway" tag around the point
    query = f"""
    [out:json][timeout:25];
    (
      way(around:{radius_m},{lat},{lon})["waterway"];
      way(around:{radius_m},{lat},{lon})["natural"="water"];
      relation(around:{radius_m},{lat},{lon})["waterway"];
    );
    out geom;
    """
    try:
        r = requests.post(OVERPASS_URL, data={"data": query}, timeout=60)
        r.raise_for_status()
        data = r.json()
        return data
    except Exception as e:
        return None

def compute_min_distance_to_waterway(overpass_json, lat, lon):
    if not overpass_json or "elements" not in overpass_json:
        return None
    # compute minimal distance from centroid to geometry
    p = Point(lon, lat)
    min_m = None
    for el in overpass_json["elements"]:
        geom = el.get("geometry")
        if not geom:
            continue
        coords = [(pt["lon"], pt["lat"]) for pt in geom]
        try:
            poly = shape({"type":"LineString","coordinates": coords})
        except Exception:
            continue
        dist_deg = p.distance(poly)  # in degrees (approx)
        # convert degrees to meters approx using 111km per degree
        dist_m = dist_deg * 111000
        if min_m is None or dist_m < min_m:
            min_m = dist_m
    return min_m

# ---------------------------
# 6) Climate anomaly score (simple z-score of rainfall compared to historical baseline)
#    For robust anomalies you'd need a long-term baseline (e.g. 1991-2020). Here we provide a simple approach:
#    - If you have baseline file, compute (obs - mean)/std. We'll leave scaffold and output "None" if baseline missing.
# ---------------------------
# (scaffold only)
def compute_climate_anomaly_score(dummy=None):
    return None

# ---------------------------
# 7) NDVI: Template using Google Earth Engine (requires account). We do NOT run it automatically here,
#    but we provide commented template to run once user enables GEE.
# ---------------------------
GEE_NDVI_TEMPLATE = """# Earth Engine NDVI example (run in your env after ee.Authenticate())
import ee
ee.Initialize()
# Example for a point and date range:
point = ee.Geometry.Point(LON, LAT)
collection = (ee.ImageCollection('MODIS/061/MOD13A2')
              .filterDate('2022-06-01','2022-10-01')
              .select('NDVI')
              .map(lambda im: im.clip(point.buffer(5000))))
mean_ndvi = collection.mean().reduceRegion(ee.Reducer.mean(), point.buffer(5000), 500).getInfo()
print(mean_ndvi)
"""

# ---------------------------
# 8) Main pipeline per district
# ---------------------------
def build_for_district(district):
    row = {k: "" for k in OUTPUT_FIELDS}
    row["Year"] = YEAR
    row["District"] = district
    row["SourceNotes"] = ""

    # 1) geocode
    geo = geocode_district(district)
    if geo:
        lat = geo["lat"]; lon = geo["lon"]
        row["SourceNotes"] += f"geocode:{geo.get('display_name')}; "
    else:
        lat = lon = None
        row["SourceNotes"] += "geocode:FAILED; "

    # 2) NASA POWER - request daily for 2022 monsoon window (June-Oct)
    if lat and lon:
        # fetch June 1 - Oct 31, 2022
        try:
            power_json = nasa_power_timeseries(lat, lon, "20220601", "20221031")
            # compute rainfall last 7/30 relative to Oct 31 (monsoon end)
            metrics = compute_rain_temp_humidity_from_power(power_json, "2022-10-31")
            row["Rainfall_Last_7Days"] = metrics["rain7"]
            row["Rainfall_Last_30Days"] = metrics["rain30"]
            row["Avg_Temperature"] = metrics["avg_temp"]
            row["Avg_Humidity"] = metrics["avg_hum"]
            row["SourceNotes"] += "nasa_power; "
        except Exception as e:
            row["SourceNotes"] += f"nasa_power_error:{e}; "

    # 3) population density via wikipedia
    try:
        wiki = fetch_wikipedia_population_area(district)
        if wiki:
            pop = wiki.get("population")
            area = wiki.get("area_km2")
            if pop and area:
                try:
                    pdens = pop / area
                    row["Population_Density"] = round(pdens,2)
                    row["SourceNotes"] += f"wikipedia({wiki.get('wiki_url')}); "
                except:
                    pass
            else:
                row["SourceNotes"] += "wiki_partial; "
    except Exception as e:
        row["SourceNotes"] += "wiki_error; "

    # 4) ReliefWeb search + naive number extraction
    try:
        rw = reliefweb_search(district)
        # store JSON for debugging
        with open(os.path.join(OUTPUT_DIR, f"reliefweb_{district.replace(' ','_')}.json"), "w", encoding="utf8") as fh:
            txt = json.dumps(rw, ensure_ascii=False, indent=2)
            fh.write(txt)
        # look through titles and extracts
        displaced=None; fatalities=None
        if rw and "data" in rw:
            for item in rw["data"][:10]:  # first 10 items
                title = item.get("fields",{}).get("title","")
                snippet = title + " " + json.dumps(item.get("fields",{}))
                nums = extract_numbers_from_text(snippet)
                if "displaced" in nums and not displaced:
                    displaced = nums["displaced"]
                if "fatalities" in nums and not fatalities:
                    fatalities = nums["fatalities"]
        if displaced:
            row["People_Displaced"] = displaced
        if fatalities:
            row["Fatalities"] = fatalities
        row["SourceNotes"] += "reliefweb; "
    except Exception as e:
        row["SourceNotes"] += f"reliefweb_error:{e}; "

    # 5) Waterbody proximity via Overpass
    try:
        if lat and lon:
            over = query_nearest_waterway(lat, lon, radius_m=50000)
            dmeters = compute_min_distance_to_waterway(over, lat, lon)
            row["Waterbody_Proximity"] = dmeters
            row["SourceNotes"] += "overpass; "
    except Exception as e:
        row["SourceNotes"] += f"overpass_error:{e}; "

    # 6) Flood marker and month / days since (we need flood_start date)
    # We'll attempt to find a flood start date via ReliefWeb titles (crude)
    flood_start = None
    try:
        if rw and "data" in rw:
            # try extract first date of flood mention in 2022
            dates = []
            for item in rw["data"]:
                # reliefweb items include 'date' in metadata sometimes
                meta = item.get("fields", {})
                if meta:
                    # try several fields
                    for k in ["date","published","source","info"]:
                        if k in meta:
                            try:
                                d = meta.get(k)
                                if isinstance(d,str):
                                    dd = dateparser.parse(d, default=datetime(2022,1,1))
                                    if dd.year == 2022:
                                        dates.append(dd.date())
                            except:
                                continue
            if dates:
                flood_start = min(dates)
        if flood_start:
            # Days since flood start measured to Oct 31, 2022 (monsoon end)
            ref = date(2022,10,31)
            row["Days_Since_Flood_Start"] = (ref - flood_start).days
            row["Month_Index"] = flood_start.month
            row["Flood_Marker"] = 1
            row["SourceNotes"] += f"flood_start:{flood_start.isoformat()}; "
        else:
            # fallback: set Flood_Marker 1 based on your district list
            row["Flood_Marker"] = 1
            row["SourceNotes"] += "flood_start:unknown_set_marker1; "
    except Exception as e:
        row["SourceNotes"] += f"flooddate_error:{e}; "

    # 7) Flood_Recurrence_Count: placeholder (requires historic records)
    row["Flood_Recurrence_Count"] = None

    # 8) Climate anomaly & healthcare/disease cases placeholders
    row["Climate_Anomaly_Score"] = None
    row["Healthcare_Access_Index"] = None
    row["Cholera_cases"] = None
    row["Malaria_cases"] = None
    row["Dengue_cases"] = None

    # 9) NDVI placeholder (GEE recommended)
    row["NDVI_Index"] = None

    # 10) Flood_Severity_Index: naive heuristic using displaced+fatalities+rain30
    try:
        sev = None
        d = row.get("People_Displaced")
        f = row.get("Fatalities")
        r30 = row.get("Rainfall_Last_30Days")
        score = 0.0
        if isinstance(d,int):
            score += min(d/1000.0, 50)  # more weight for many displaced
        if isinstance(f,int):
            score += min(f*0.5, 20)
        if r30:
            score += min(float(r30)/50.0, 30)
        if score>0:
            sev = round(score,2)
        row["Flood_Severity_Index"] = sev
    except:
        row["Flood_Severity_Index"] = None

    return row

# ---------------------------
# Run pipeline for all districts
# ---------------------------
def run_all():
    all_rows = []
    for d in tqdm(DISTRICTS, desc="Districts"):
        try:
            r = build_for_district(d)
            all_rows.append(r)
            # polite pause to avoid geo/API throttling
            time.sleep(1)
        except Exception as e:
            print("Error for", d, e)
            all_rows.append({"District": d, "Year": YEAR, "SourceNotes": f"error:{e}"})
    df = pd.DataFrame(all_rows, columns=OUTPUT_FIELDS)
    df.to_csv(CSV_OUT, index=False)
    print("Wrote:", CSV_OUT)
    # also dump full JSON for debugging
    with open(os.path.join(OUTPUT_DIR, "raw_output.json"), "w", encoding="utf8") as fh:
        json.dump(all_rows, fh, ensure_ascii=False, indent=2, default=str)
    print("Pipeline complete.")

if __name__ == "__main__":
    run_all()

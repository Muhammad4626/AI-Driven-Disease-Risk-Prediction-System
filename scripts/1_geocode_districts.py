# 1_geocode_districts.py
import os
import time
import pandas as pd
from geopy.geocoders import Nominatim
from tqdm import tqdm

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)
CSV_OUT = os.path.join(OUTPUT_DIR, "geocode_districts.csv")

YEAR = 2022

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

geolocator = Nominatim(user_agent="pak_flood_geocoder", timeout=10)
rows = []

for district in tqdm(DISTRICTS):
    try:
        loc = geolocator.geocode(f"{district}, Pakistan")
        lat, lon = (loc.latitude, loc.longitude) if loc else (None, None)
        rows.append({"Year": YEAR, "District": district, "Latitude": lat, "Longitude": lon})
        time.sleep(1)  # polite pause
    except Exception as e:
        rows.append({"Year": YEAR, "District": district, "Latitude": None, "Longitude": None})

df = pd.DataFrame(rows)
df.to_csv(CSV_OUT, index=False)
print("Geocode CSV saved:", CSV_OUT)

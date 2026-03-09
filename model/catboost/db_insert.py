#!/usr/bin/env python3
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# ===== Helper functions =====
def to_int(x):
    try:
        return int(x)
    except:
        return None

def to_float(x):
    try:
        return float(x)
    except:
        return None

# ===== Database connection =====
conn = psycopg2.connect(
    host="localhost",
    dbname="disease_prediction",
    user="postgres",
    password="1234"
)
cur = conn.cursor()

# ===== Load CSV =====
df = pd.read_csv("final_master_dataset_2026.csv")

# ===== Insert districts =====
districts = df['district'].dropna().unique()
district_values = [(i+1, str(d)) for i,d in enumerate(districts)]

execute_values(
    cur,
    "INSERT INTO district (district_id, district_name) VALUES %s ON CONFLICT (district_id) DO NOTHING",
    district_values
)
conn.commit()
print("Inserted districts")

# Create mapping for district names -> id
cur.execute("SELECT district_id, district_name FROM district")
district_map = {row[1]: row[0] for row in cur.fetchall()}

# ===== Insert weeks =====
weeks = df[['year','week_index']].drop_duplicates().reset_index(drop=True)
week_values = [(i+1, to_int(row['year']), to_int(row['week_index'])) for i,row in weeks.iterrows()]

execute_values(
    cur,
    "INSERT INTO week (week_id, year, week_number) VALUES %s ON CONFLICT (week_id) DO NOTHING",
    week_values
)
conn.commit()
print("Inserted weeks")

# Create mapping for (year, week_index) -> week_id
cur.execute("SELECT week_id, year, week_number FROM week")
week_map = {(row[1], row[2]): row[0] for row in cur.fetchall()}

# ===== Insert diseases =====
disease_names = ['malaria', 'ad', 'typhoid']
disease_values = [(i+1, d, 'vector_borne' if d=='malaria' else 'water_borne') for i,d in enumerate(disease_names)]

execute_values(
    cur,
    "INSERT INTO disease (disease_id, disease_name, category) VALUES %s ON CONFLICT (disease_id) DO NOTHING",
    disease_values
)
conn.commit()
print("Inserted diseases")

# Map disease names -> id
cur.execute("SELECT disease_id, disease_name FROM disease")
disease_map = {row[1]: row[0] for row in cur.fetchall()}

# ===== Insert weekly_climate_data =====
weekly_climate_values = []
for idx, row in df.iterrows():
    district_id = district_map.get(row['district'])
    week_id = week_map.get((row['year'], row['week_index']))
    if district_id and week_id:
        weekly_climate_values.append((
            idx+1,
            to_float(row.get('avg_temperature')),
            to_float(row.get('avg_rainfall')),
            to_float(row.get('avg_humidity')),
            district_id,
            week_id
        ))

execute_values(
    cur,
    """INSERT INTO weekly_climate_data
    (weekly_climate_id, avg_temperature, avg_rainfall, avg_humidity, district_id, week_id)
    VALUES %s ON CONFLICT (weekly_climate_id) DO NOTHING""",
    weekly_climate_values
)
conn.commit()
print("Inserted weekly_climate_data")

# ===== Insert weekly_environment_data =====
weekly_env_values = []
for idx, row in df.iterrows():
    district_id = district_map.get(row['district'])
    if district_id:
        weekly_env_values.append((
            idx+1,
            district_id,
            to_float(row.get('flood_inundation')),
            to_float(row.get('stagnant_water')),
            to_float(row.get('mean_ndvi'))
        ))

execute_values(
    cur,
    """INSERT INTO weekly_environment_data
    (weekly_env_id, district_id, flood_inundation, stagnant_water_duration, mean_ndvi)
    VALUES %s ON CONFLICT (weekly_env_id) DO NOTHING""",
    weekly_env_values
)
conn.commit()
print("Inserted weekly_environment_data")

# ===== Insert weekly_disease_data =====
weekly_disease_values = []
for idx, row in df.iterrows():
    district_id = district_map.get(row['district'])
    week_id = week_map.get((row['year'], row['week_index']))
    if district_id and week_id:
        for disease in disease_names:
            cases = row.get(f"{disease}_cases")
            if pd.notna(cases):
                weekly_disease_values.append((
                    idx+1,
                    to_int(cases),
                    None,  # risk_level placeholder
                    district_id,
                    week_id,
                    disease_map[disease]
                ))

execute_values(
    cur,
    """INSERT INTO weekly_disease_data
    (weekly_disease_id, cases_count, risk_level, district_id, week_id, disease_id)
    VALUES %s ON CONFLICT (weekly_disease_id) DO NOTHING""",
    weekly_disease_values
)
conn.commit()
print("Inserted weekly_disease_data")

# ===== Close connection =====
cur.close()
conn.close()
print("All data inserted successfully!")
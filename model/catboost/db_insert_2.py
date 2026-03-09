import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# Database connection
conn = psycopg2.connect(
    host="localhost",
    database="disease_prediction",
    user="postgres",
    password="1234"
)
cur = conn.cursor()

# Load district info CSV (TSV with tabs)
districts_df = pd.read_csv("district_metadata.csv", sep="\t")  # <-- tabs

# Strip spaces and lowercase column names
districts_df.columns = [c.strip().lower() for c in districts_df.columns]

# Check columns
print("Columns in CSV:", districts_df.columns.tolist())

# Prepare rows
records = [
    (
        row["district"],  # now lowercase and stripped
        int(row["population"]) if not pd.isna(row.get("population")) else None,
        int(row["elevation_m"]),
        int(row["river_status"]),
        float(row["area_sq_km"]),
        float(row["sanitation_index"])
    )
    for _, row in districts_df.iterrows()
]

# Insert/update districts
execute_values(
    cur,
    """
    INSERT INTO district (district_name, population, elevation_m, river_status, area_sq_km, sanitation_index)
    VALUES %s
    ON CONFLICT (district_name) DO UPDATE
    SET
        population = EXCLUDED.population,
        elevation_m = EXCLUDED.elevation_m,
        river_status = EXCLUDED.river_status,
        area_sq_km = EXCLUDED.area_sq_km,
        sanitation_index = EXCLUDED.sanitation_index
    """,
    records
)

conn.commit()
cur.close()
conn.close()
print("Inserted/Updated districts successfully!")
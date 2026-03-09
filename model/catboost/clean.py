import pandas as pd

# Load the CSV
df = pd.read_csv("final_master_dataset_2026.csv")

# Replace 'NR' with 0
df.replace("NR", 0, inplace=True)

# Fill any other missing values (NaN) with 0
df.fillna(0, inplace=True)

# Optionally, convert numeric columns to proper types (float/int)
numeric_cols = ['Avg_temp_C', 'Avg_humidity_%', 'Avg_rainfall_mm', 'Population',
                'Malaria_cases', 'AD_cases', 'Typhoid_cases', 'Elevation_m', 
                'River_Status', 'Area_sq_km', 'Sanitation_Index','Flood_Inundation','Mean_NDVI','Stagnant_Water']

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# Save the cleaned CSV
df.to_csv("cleaned_file.csv", index=False)

print("Missing and NR values replaced with 0 successfully.")
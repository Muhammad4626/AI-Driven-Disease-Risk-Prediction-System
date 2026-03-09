import pandas as pd

# 1. Load the 2025 datasets
disease_df = pd.read_excel('disease_data_2026.xlsx')
weather_df = pd.read_excel('weather_data_2026.xlsx')
metadata_df = pd.read_excel('district_metadata.xlsx')

# 2. Merge Disease and Weather Data
# Merging on 'Year', 'District', and 'week_index'
# Overlap expected in: 'Avg_rainfall' (will become _disease and _weather)
merged_df = pd.merge(
    disease_df, 
    weather_df, 
    on=['Year', 'District', 'week_index'], 
    how='left',
    suffixes=('_disease', '_weather')
)

# 3. Fill Missing Disease Data with Weather Data

# Fix Rainfall (Collision Occurred: Column 'Avg_rainfall' is gone, replaced by suffixes)
if 'Avg_rainfall_disease' in merged_df.columns and 'Avg_rainfall_weather' in merged_df.columns:
    merged_df['Avg_rainfall'] = merged_df['Avg_rainfall_disease'].fillna(merged_df['Avg_rainfall_weather'])

# Fix Temperature (No Collision: 'Avg_Temperature' exists, 'Avg_temp' comes from weather)
if 'Avg_Temperature' in merged_df.columns and 'Avg_temp' in merged_df.columns:
    merged_df['Avg_Temperature'] = merged_df['Avg_Temperature'].fillna(merged_df['Avg_temp'])

# Fix Humidity (No Collision: 'Avg_Humidity' exists, 'Avg_humidity' comes from weather)
if 'Avg_Humidity' in merged_df.columns and 'Avg_humidity' in merged_df.columns:
    merged_df['Avg_Humidity'] = merged_df['Avg_Humidity'].fillna(merged_df['Avg_humidity'])

# 4. Merge Metadata (Static District Info)
final_df = pd.merge(merged_df, metadata_df, on='District', how='left')

# 5. Clean up redundant columns
cols_to_drop = ['Avg_temp', 'Avg_humidity', 'Avg_rainfall_weather', 'Avg_rainfall_disease']
final_df = final_df.drop(columns=[c for c in cols_to_drop if c in final_df.columns])

# 6. Save the final combined dataset for 2025
final_df.to_csv('flood_disease_dataset_2026.csv', index=False)

print("Success! 2025 Dataset combined.")
print(final_df.head())
import pandas as pd

# 1. Load the datasets
disease_df = pd.read_csv('disease_data_2024.xlsx - Sheet1.csv')
weather_df = pd.read_csv('weather_data_2024.xlsx - Sheet1.csv')
metadata_df = pd.read_csv('district_metadata.xlsx - Sheet1.csv')

# 2. Clean and Standardize Weather Data
# Rename columns to match the Disease dataset for easy merging
weather_df = weather_df.rename(columns={
    'district': 'District',
    'week': 'week_index'
})

# 3. Merge Disease and Weather Data
# We use a "left" join to keep all disease records, even if weather data is missing for some.
# We merge on Year, District, and week_index.
merged_df = pd.merge(
    disease_df, 
    weather_df[['Year', 'District', 'week_index', 'avg_temp_C', 'avg_humidity_%', 'avg_rainfall_mm']], 
    on=['Year', 'District', 'week_index'], 
    how='left'
)

# 4. Merge Metadata (Static District Info)
# This adds elevation, area, etc. to every row based on the District name.
final_df = pd.merge(merged_df, metadata_df, on='District', how='left')

# 5. Fill Empty Placeholder Columns (Optional)
# Your disease data had empty columns for rainfall/temp. We can fill them with the new weather data.
final_df['avg_rainfall'] = final_df['avg_rainfall'].fillna(final_df['avg_rainfall_mm'])
final_df['Avg_Temperature'] = final_df['Avg_Temperature'].fillna(final_df['avg_temp_C'])
final_df['Avg_Humidity'] = final_df['Avg_Humidity'].fillna(final_df['avg_humidity_%'])

# Drop the duplicate/extra weather columns if you want a cleaner file
final_df = final_df.drop(columns=['avg_rainfall_mm', 'avg_temp_C', 'avg_humidity_%'])

# 6. Save the final combined dataset
final_df.to_csv('combined_flood_disease_dataset_2024.csv', index=False)

print("Success! Dataset combined.")
print(final_df.head())
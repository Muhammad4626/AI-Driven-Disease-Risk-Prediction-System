import pandas as pd

# 1. Define your file names (Change these to match your actual CSV file names)
weekly_data_file = "week_6_data.csv"   # The file with year, week_index, cases, etc.
metadata_file = "district_metadata_2.csv"         # The file with elevation, river_status, etc.
output_file = "fweek6_merged_data.csv"

print("Loading datasets...")
# 2. Load the datasets
# (If your data is tab-separated instead of comma-separated, add sep='\t' inside read_csv)
df_weekly = pd.read_csv(weekly_data_file)
df_meta = pd.read_csv(metadata_file)

# 3. Standardize column names to lowercase
# This ensures that "District" and "district" match perfectly
df_weekly.columns = [col.lower() for col in df_weekly.columns]
df_meta.columns = [col.lower() for col in df_meta.columns]

# 4. Clean district names to ensure a perfect match
# This removes any hidden spaces at the beginning or end of the names
df_weekly['district'] = df_weekly['district'].astype(str).str.strip()
df_meta['district'] = df_meta['district'].astype(str).str.strip()

# Add any specific name replacements if your two files spell districts differently
# Example: df_meta['district'] = df_meta['district'].replace({'Nawabshah': 'Shaheed Benazirabad'})

print("Merging datasets...")
# 5. Merge the datasets
# A 'left' join keeps all rows from df_weekly and attaches the matching metadata
final_df = pd.merge(
    df_weekly, 
    df_meta[['district', 'elevation_m', 'river_status', 'area_sq_km', 'sanitation_index']], 
    on='district', 
    how='left'
)

# 6. Save the final merged dataset
final_df.to_csv(output_file, index=False)

print(f"Success! Merged dataset saved as '{output_file}'")

# Quick check to see if any districts failed to match (resulting in empty metadata)
missing_metadata = final_df[final_df['elevation_m'].isna()]['district'].unique()
if len(missing_metadata) > 0:
    print(f"\nWarning: Could not find metadata for these districts: {missing_metadata}")
    print("You might need to check for spelling differences between the two files.")
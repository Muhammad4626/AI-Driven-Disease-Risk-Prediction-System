import pandas as pd
import numpy as np

# 1. Load your final CSV file
# Ensure the filename matches your actual CSV file
csv_filename = "processed_dataset_2026.csv" 
df = pd.read_csv(csv_filename)

# Replace any 'NR' or missing values with NaN, then fill with appropriate defaults
df = df.replace({'NR': np.nan})
df = df.fillna({
    'avg_temperature': 'NULL', 'avg_rainfall': 'NULL', 'avg_humidity': 'NULL',
    'flood_inundation': 'NULL', 'stagnant_water': 'NULL', 'mean_ndvi': 'NULL',
    'malaria_cases': 0, 'ad_cases': 0, 'typhoid_cases': 0,
    'malaria_risk': '0', 'ad_risk': '0', 'typhoid_risk': '0'
})

# 2. District ID Mapping Dictionary
district_map = {
    'Badin': 1, 'Dadu': 2, 'Ghotki': 3, 'Hyderabad': 4, 'Jacobabad': 5, 'Jamshoro': 6, 'Kamber': 7, 
    'Central': 8, 'East': 9, 'Keamari': 10, 'Korangi': 11, 'Malir': 12, 'South': 13, 'West': 14, 
    'Kashmore': 15, 'Khairpur': 16, 'Larkana': 17, 'Matiari': 18, 'Mirpurkhas': 19, 'Naushero Feroze': 20, 
    'Qambar Shahdadkot': 21, 'Sanghar': 22, 'Shaheed Benazirabad': 23, 'Shikarpur': 24, 'Sukkur': 25, 
    'Tando Allahyar': 26, 'Tando Muhammad Khan': 27, 'Tharparkar': 28, 'Thatta': 29, 'Umerkot': 30, 
    'Abbottabad': 31, 'Bajaur': 32, 'Bannu': 33, 'Battagram': 34, 'Buner': 35, 'Charsadda': 36, 
    'Chitral Lower': 37, 'Chitral Upper': 38, 'Dera Ismail Khan': 39, 'Dir Lower': 40, 'Dir Upper': 41, 
    'Hangu': 42, 'Haripur': 43, 'Karak': 44, 'Khyber': 45, 'Kohat': 46, 'Kolai Pallas': 47, 
    'Kohistan Lower': 48, 'Kohistan Upper': 49, 'Kurram': 50, 'Lakki Marwat': 51, 'Malakand': 52, 
    'Mansehra': 53, 'Mardan': 54, 'Mohmand': 55, 'North Waziristan': 56, 'Nowshera': 57, 'Orakzai': 58, 
    'Peshawar': 59, 'Shangla': 60, 'South Waziristan Lower': 61, 'South Waziristan Upper': 62, 
    'Swabi': 63, 'Swat': 64, 'Tank': 65, 'Torghar': 66, 'Upper Kohistan': 67, 'Awaran': 68, 
    'Barkhan': 69, 'Chagai': 70, 'Chaman': 71, 'Dera Bugti': 72, 'Duki': 73, 'Gwadar': 74, 
    'Harani': 75, 'Jaffarabad': 76, 'Jhal Magsi': 77, 'Kacchi': 78, 'Kalat': 79, 'Kech': 80, 
    'Kharan': 81, 'Khuzdar': 82, 'Killa Abdullah': 83, 'Killa Saifullah': 84, 'Kohlu': 85, 
    'Lasbela': 86, 'Loralai': 87, 'Mastung': 88, 'Musakhel': 89, 'Nasirabad': 90, 'Nushki': 91, 
    'Panjgur': 92, 'Pishin': 93, 'Quetta': 94, 'Sherani': 95, 'Sibi': 96, 'Sohbatpur': 97, 
    'Washuk': 98, 'Zhob': 99, 'Ziarat': 100, 'Attock': 101, 'Bahawalnagar': 102, 'Bahawalpur': 103, 
    'Bhakkar': 104, 'Chakwal': 105, 'Dera Ghazi Khan': 106, 'Faisalabad': 107, 'Gujranwala': 108, 
    'Gujrat': 109, 'Hafizabad': 110, 'Jhang': 111, 'Jhelum': 112, 'Kasur': 113, 'Khanewal': 114, 
    'Khushab': 115, 'Lahore': 116, 'Layyah': 117, 'Lodhran': 118, 'Mandi Bahauddin': 119, 
    'Multan': 120, 'Muzaffargarh': 121, 'Nankana Sahib': 122, 'Narowal': 123, 'Okara': 124, 
    'Pakpattan': 125, 'Rahim Yar Khan': 126, 'Rajanpur': 127
}

# Map District Names to IDs
df['district_id'] = df['district'].map(district_map)

# Drop rows where district_id couldn't be found (safety check)
df = df.dropna(subset=['district_id'])
df['district_id'] = df['district_id'].astype(int)

# 3. Open a file to write our SQL queries
sql_file = "bulk_insert_data.sql"

with open(sql_file, "w", encoding="utf-8") as f:
    f.write("-- BULK INSERT SCRIPT GENERATED FROM CSV\n\n")

    # --- A. WEEKLY CLIMATE DATA ---
    f.write("-- 1. Insert Weekly Climate Data\n")
    f.write("INSERT INTO weekly_climate_data (avg_temperature, avg_rainfall, avg_humidity, district_id, week_id) VALUES\n")
    climate_values = []
    for _, row in df.iterrows():
        climate_values.append(f"({row['avg_temperature']}, {row['avg_rainfall']}, {row['avg_humidity']}, {row['district_id']}, {row['week_index']})")
    f.write(",\n".join(climate_values) + ";\n\n")

    # --- B. WEEKLY ENVIRONMENT DATA ---
    f.write("-- 2. Insert Weekly Environment Data\n")
    f.write("INSERT INTO weekly_environment_data (district_id, flood_inundation, stagnant_water_duration, mean_ndvi) VALUES\n")
    env_values = []
    for _, row in df.iterrows():
        env_values.append(f"({row['district_id']}, {row['flood_inundation']}, {row['stagnant_water']}, {row['mean_ndvi']})")
    f.write(",\n".join(env_values) + ";\n\n")

    # --- C. WEEKLY DISEASE DATA ---
    f.write("-- 3. Insert Weekly Disease Data\n")
    f.write("INSERT INTO weekly_disease_data (cases_count, risk_level, district_id, week_id, disease_id) VALUES\n")
    disease_values = []
    
    for _, row in df.iterrows():
        # Malaria (disease_id = 1)
        disease_values.append(f"({int(row['malaria_cases'])}, '{row['malaria_risk']}', {row['district_id']}, {row['week_index']}, 1)")
        # AD (disease_id = 2)
        disease_values.append(f"({int(row['ad_cases'])}, '{row['ad_risk']}', {row['district_id']}, {row['week_index']}, 2)")
        # Typhoid (disease_id = 3)
        disease_values.append(f"({int(row['typhoid_cases'])}, '{row['typhoid_risk']}', {row['district_id']}, {row['week_index']}, 3)")
        
    f.write(",\n".join(disease_values) + ";\n")

print(f"Success! All data mapped and SQL queries written to {sql_file}")
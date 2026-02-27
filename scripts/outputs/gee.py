import ee
import geemap
import pandas as pd
import datetime

# Authenticate and Initialize (Follow the pop-up instructions)
try:
    ee.Initialize()
except Exception as e:
    ee.Authenticate()
    ee.Initialize()

# --- STEP 2: Define Functions ---

# 1. Load Pakistan Districts
# We filter for Pakistan. You can filter for specific districts if this times out.
districts = ee.FeatureCollection("FAO/GAUL/2015/level2") \
    .filter(ee.Filter.eq('ADM0_NAME', 'Pakistan'))

# 2. Water Detection Function (Sentinel-1 SAR)
def get_water_mask(start_date, end_date, region):
    s1 = ee.ImageCollection('COPERNICUS/S1_GRD') \
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')) \
        .filter(ee.Filter.eq('instrumentMode', 'IW')) \
        .filterBounds(region) \
        .filterDate(start_date, end_date)
    
    # If no images found, return an empty image
    mosaic = s1.mosaic().clip(region)
    
    # Thresholding: Pixels < -18 dB are classified as water
    water = mosaic.select('VH').lt(-18.0).rename('water')
    return water

# 3. NDVI Calculation Function (Sentinel-2 Optical)
def get_mean_ndvi(start_date, end_date, region):
    s2 = ee.ImageCollection('COPERNICUS/S2_SR') \
        .filterBounds(region) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30)) # Filter cloudy images
    
    def add_ndvi(image):
        ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
        return image.addBands(ndvi)

    # Create a composite (median value to remove remaining clouds)
    composite = s2.map(add_ndvi).median().clip(region)
    return composite.select('NDVI')

# --- STEP 3: Main Execution Loop ---

# Setup Years and Weeks
year = 2024
weeks_to_process = [30, 31, 32] # Add more weeks as needed: range(20, 45)

results = []

print(f"Processing data for {year}...")

for week in weeks_to_process:
    # Calculate dates
    start_date_curr = datetime.datetime.strptime(f'{year}-W{week}-1', "%Y-W%W-%w").strftime('%Y-%m-%d')
    end_date_curr = datetime.datetime.strptime(f'{year}-W{week}-6', "%Y-W%W-%w").strftime('%Y-%m-%d')
    
    # Previous week for Stagnant Water calculation
    start_date_prev = datetime.datetime.strptime(f'{year}-W{week-1}-1', "%Y-W%W-%w").strftime('%Y-%m-%d')
    end_date_prev = datetime.datetime.strptime(f'{year}-W{week-1}-6', "%Y-W%W-%w").strftime('%Y-%m-%d')

    print(f"Week {week}: {start_date_curr} to {end_date_curr}")

    # --- A. Flood Inundation ---
    water_curr = get_water_mask(start_date_curr, end_date_curr, districts)
    
    # --- B. Stagnant Water ---
    # Logic: It is stagnant if it is water NOW AND was water LAST WEEK
    water_prev = get_water_mask(start_date_prev, end_date_prev, districts)
    stagnant_water = water_curr.And(water_prev).rename('stagnant')

    # --- C. NDVI ---
    ndvi_img = get_mean_ndvi(start_date_curr, end_date_curr, districts)

    # Combine all into one image for reduction
    combined_img = water_curr.addBands(stagnant_water).addBands(ndvi_img)

    # --- D. Reduce Regions (Calculate Stats per District) ---
    # We calculate the MEAN. For binary masks (0/1), mean * 100 = Percentage coverage.
    stats = combined_img.reduceRegions(
        collection=districts,
        reducer=ee.Reducer.mean(),
        scale=100, # 100m resolution (increase to 500 if script crashes)
        tileScale=4
    )

    # Extract data to local list
    # Note: This .getInfo() is slow. For full year, use Export.table.toDrive()
    try:
        dist_stats = stats.select(['ADM2_NAME', 'water', 'stagnant', 'NDVI'], 
                                  ['District', 'Flood_Inundation', 'Stagnant_Water', 'Mean_NDVI']).getInfo()
        
        for feat in dist_stats['features']:
            props = feat['properties']
            results.append({
                'Year': year,
                'Week': week,
                'District': props.get('District'),
                'Flood_Inundation_Percent': (props.get('Flood_Inundation', 0) or 0) * 100,
                'Stagnant_Water_Percent': (props.get('Stagnant_Water', 0) or 0) * 100,
                'Mean_NDVI': props.get('Mean_NDVI', 0)
            })
    except Exception as e:
        print(f"Error processing week {week}: {e}")

# --- STEP 4: Convert to DataFrame ---
df_final = pd.DataFrame(results)

# Clean up: Replace NaN with 0 or appropriate values
df_final = df_final.fillna(0)

print("\nProcessing Complete!")
print(df_final.head())

# Formatted for copying to Excel
print("\n--- COPY DATA BELOW (Tab Separated) ---")
print(df_final.to_csv(sep='\t', index=False))
import pandas as pd
import numpy as np
import joblib
from tensorflow.keras.models import load_model

# 1. LOAD
print("Loading model...")
model = load_model('malaria_model.keras')
scaler = joblib.load('scaler.pkl')

# 2. DEFINE INPUT (Change these numbers to test)
input_data = {
    'Avg_rainfall': 15.0,
    'Avg_Temperature': 34.0,
    'Avg_Humidity': 70.0,
    'Elevation_m': 10.0,
    'Sanitation_Index': 0.35, # 0.35 = Poor, 0.8 = Good
    'River_Status': 1.0,
    'Rainfall_Lag_1': 50.0,   # Heavy rain last week
    'Temp_Lag_1': 33.0
}

# 3. PREDICT
input_df = pd.DataFrame([input_data])
input_scaled = scaler.transform(input_df)
prediction = model.predict(input_scaled)
risk_per_100k = prediction[0][0]

# 4. RESULTS
print(f"\n========================================")
print(f"PREDICTED RISK: {risk_per_100k:.2f} cases per 100,000 people")
print(f"========================================")

# Interpretation
if risk_per_100k < 10:
    print("Risk Level: LOW")
elif risk_per_100k < 50:
    print("Risk Level: MODERATE")
else:
    print("Risk Level: HIGH (Outbreak Warning!)")
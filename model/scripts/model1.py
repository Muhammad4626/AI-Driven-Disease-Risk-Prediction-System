import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Input

# ==========================================
# 1. LOAD & CLEAN DATA
# ==========================================
df = pd.read_csv('final_flood_disease_data.csv')

# Handle 'NR' and commas in disease columns
for col in ['Malaria_cases', 'AD_cases', 'Typhoid_cases']:
    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

# Drop rows where Population is 0 or Missing
df = df.dropna(subset=['Population'])
df = df[df['Population'] > 0]

# Fill missing environmental data
for col in ['Avg_rainfall', 'Avg_Temperature', 'Avg_Humidity']:
    df[col] = df[col].fillna(0)

for col in ['Elevation_m', 'Sanitation_Index', 'River_Status']:
    if col in df.columns:
        df[col] = df[col].fillna(df[col].mean())

# ==========================================
# 2. FEATURE ENGINEERING (Epidemiology Standard)
# ==========================================
# We use "Cases per 100,000 people" instead of raw %
# This avoids tiny numbers like 0.00005 which confuse the AI
df['Malaria_Risk'] = (df['Malaria_cases'] / df['Population']) * 100000
df['AD_Risk'] = (df['AD_cases'] / df['Population']) * 100000
df['Typhoid_Risk'] = (df['Typhoid_cases'] / df['Population']) * 100000

# Remove Extreme Outliers (Top 1% of highest risk to remove data errors)
q_high = df['Malaria_Risk'].quantile(0.99)
df = df[df['Malaria_Risk'] <= q_high]

# Lag Features
df['Rainfall_Lag_1'] = df.groupby('District')['Avg_rainfall'].shift(1).fillna(0)
df['Temp_Lag_1'] = df.groupby('District')['Avg_Temperature'].shift(1).fillna(0)

# --- DATA DISTRIBUTION CHECK ---
print(f"\n--- Data Stats ---")
print(f"Total Rows: {len(df)}")
print(f"Districts with 0 Risk: {len(df[df['Malaria_Risk'] == 0])}")
print(f"Average Risk (Cases/100k): {df['Malaria_Risk'].mean():.2f}")
print(f"Max Risk (Cases/100k): {df['Malaria_Risk'].max():.2f}")
print("------------------\n")

# ==========================================
# 3. PREPARE FOR TRAINING
# ==========================================
feature_cols = ['Avg_rainfall', 'Avg_Temperature', 'Avg_Humidity', 
                'Elevation_m', 'Sanitation_Index', 'River_Status', 
                'Rainfall_Lag_1', 'Temp_Lag_1']
target_col = 'Malaria_Risk'

X = df[feature_cols]
y = df[target_col]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale Data
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ==========================================
# 4. BUILD NEURAL NETWORK (Fixed Warning)
# ==========================================
model = Sequential()

# Input Layer (Fixed Syntax)
model.add(Input(shape=(X_train_scaled.shape[1],)))

# Hidden Layers
model.add(Dense(64, activation='relu'))
model.add(Dropout(0.2)) 
model.add(Dense(32, activation='relu'))
model.add(Dense(16, activation='relu'))

# Output Layer
model.add(Dense(1, activation='linear')) 

model.compile(optimizer='adam', loss='mse', metrics=['mae'])

# Train
print("Starting Training...")
history = model.fit(
    X_train_scaled, y_train, 
    epochs=100, 
    batch_size=32, 
    validation_split=0.2, 
    verbose=1
)

# ==========================================
# 5. EVALUATE & SAVE
# ==========================================
loss, mae = model.evaluate(X_test_scaled, y_test)
print(f"\nModel Performance:")
print(f"Mean Absolute Error: {mae:.2f} (On average, prediction is off by {mae:.2f} cases per 100k people)")

# Save
model.save('malaria_model.keras') # Using new .keras format
joblib.dump(scaler, 'scaler.pkl')
print("Model saved as malaria_model.keras")
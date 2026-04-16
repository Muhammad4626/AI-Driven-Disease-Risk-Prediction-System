import os
import pandas as pd
import shap
import matplotlib.pyplot as plt
from catboost import CatBoostRegressor

print("=== Generating Global SHAP Plots ===\n")

#config
models_dir = "Project-Backend/models"                    # Path to your .cbm files
output_dir = "global_shap"
processed_data_path = "global_shap/processed_dataset_risk_based.csv" 

# Create output directories
os.makedirs(f"{output_dir}/malaria", exist_ok=True)
os.makedirs(f"{output_dir}/ad", exist_ok=True)
os.makedirs(f"{output_dir}/typhoid", exist_ok=True)

# ========================== LOAD MODELS ==========================
malaria_model = CatBoostRegressor().load_model(f"{models_dir}/malaria_model.cbm")
ad_model      = CatBoostRegressor().load_model(f"{models_dir}/ad_model.cbm")
typhoid_model = CatBoostRegressor().load_model(f"{models_dir}/typhoid_model.cbm")

# ========================== LOAD BACKGROUND DATA ==========================
print("Loading background data for global SHAP...")
df = pd.read_csv(processed_data_path)

# Use a representative sample (recommended: 800-1500 rows)
background = df.sample(n=min(1200, len(df)), random_state=42).reset_index(drop=True)

# ========================== FEATURE ORDERS (Update these!) ==========================
# Paste your actual feature orders here from training
FEATURE_ORDER_TYPHOID = [
    'district', 'avg_rainfall', 'avg_temperature', 'avg_humidity', 'population',
    'elevation_m', 'river_status', 'area_sq_km', 'sanitation_index',
    'flood_inundation', 'mean_ndvi', 'stagnant_water', 'typhoid_risk',
    'avg_rainfall_lag1', 'avg_rainfall_lag2',
    'avg_temperature_lag1', 'avg_temperature_lag2',
    'avg_humidity_lag1', 'avg_humidity_lag2',
    'flood_inundation_lag1', 'flood_inundation_lag2',
    'stagnant_water_lag1', 'stagnant_water_lag2',
    'mean_ndvi_lag1', 'mean_ndvi_lag2',
    'typhoid_risk_lag1', 'typhoid_risk_lag2',
    'avg_rainfall_roll3', 'avg_rainfall_roll5',
    'avg_temperature_roll3', 'avg_temperature_roll5',
    'avg_humidity_roll3', 'avg_humidity_roll5',
    'flood_inundation_roll3', 'flood_inundation_roll5',
    'stagnant_water_roll3', 'stagnant_water_roll5',
    'mean_ndvi_roll3', 'mean_ndvi_roll5',
    'typhoid_risk_roll3', 'typhoid_risk_roll5'
]
FEATURE_ORDER_MALARIA = [
    'district', 'avg_rainfall', 'avg_temperature', 'avg_humidity', 'population',
    'elevation_m', 'river_status', 'area_sq_km', 'sanitation_index',
    'flood_inundation', 'mean_ndvi', 'stagnant_water', 'malaria_risk',
    'avg_rainfall_lag1', 'avg_rainfall_lag2',
    'avg_temperature_lag1', 'avg_temperature_lag2',
    'avg_humidity_lag1', 'avg_humidity_lag2',
    'flood_inundation_lag1', 'flood_inundation_lag2',
    'stagnant_water_lag1', 'stagnant_water_lag2',
    'mean_ndvi_lag1', 'mean_ndvi_lag2',
    'malaria_risk_lag1', 'malaria_risk_lag2',
    'avg_rainfall_roll3', 'avg_rainfall_roll5',
    'avg_temperature_roll3', 'avg_temperature_roll5',
    'avg_humidity_roll3', 'avg_humidity_roll5',
    'flood_inundation_roll3', 'flood_inundation_roll5',
    'stagnant_water_roll3', 'stagnant_water_roll5',
    'mean_ndvi_roll3', 'mean_ndvi_roll5',
    'malaria_risk_roll3', 'malaria_risk_roll5'
]
FEATURE_ORDER_AD = [
    'district', 'avg_rainfall', 'avg_temperature', 'avg_humidity', 'population',
    'elevation_m', 'river_status', 'area_sq_km', 'sanitation_index',
    'flood_inundation', 'mean_ndvi', 'stagnant_water', 'ad_risk',
    'avg_rainfall_lag1', 'avg_rainfall_lag2',
    'avg_temperature_lag1', 'avg_temperature_lag2',
    'avg_humidity_lag1', 'avg_humidity_lag2',
    'flood_inundation_lag1', 'flood_inundation_lag2',
    'stagnant_water_lag1', 'stagnant_water_lag2',
    'mean_ndvi_lag1', 'mean_ndvi_lag2',
    'ad_risk_lag1', 'ad_risk_lag2',
    'avg_rainfall_roll3', 'avg_rainfall_roll5',
    'avg_temperature_roll3', 'avg_temperature_roll5',
    'avg_humidity_roll3', 'avg_humidity_roll5',
    'flood_inundation_roll3', 'flood_inundation_roll5',
    'stagnant_water_roll3', 'stagnant_water_roll5',
    'mean_ndvi_roll3', 'mean_ndvi_roll5',
    'ad_risk_roll3', 'ad_risk_roll5'
]

# ========================== GENERATE GLOBAL SHAP ==========================
def generate_global_plots(model, explainer, background_df, feature_order, disease_name, save_dir):
    print(f"Generating global SHAP for {disease_name}...")

    X = background_df[feature_order]

    # Compute SHAP values
    shap_values = explainer.shap_values(X)

    # 1. Summary Plot (Beeswarm)
    plt.figure(figsize=(12, 8))
    shap.summary_plot(shap_values, X, plot_type="dot", show=False)
    plt.title(f"Global SHAP Summary - {disease_name.capitalize()} Risk Model")
    plt.tight_layout()
    plt.savefig(f"{save_dir}/summary_plot.png", dpi=180, bbox_inches='tight')
    plt.close()

    # 2. Feature Importance Bar
    plt.figure(figsize=(10, 7))
    shap.summary_plot(shap_values, X, plot_type="bar", show=False)
    plt.title(f"Global Feature Importance - {disease_name.capitalize()} Risk")
    plt.tight_layout()
    plt.savefig(f"{save_dir}/importance_bar.png", dpi=180, bbox_inches='tight')
    plt.close()

    print(f"Saved global plots for {disease_name}")

# ========================== RUN FOR ALL MODELS ==========================
malaria_explainer = shap.TreeExplainer(malaria_model)
ad_explainer      = shap.TreeExplainer(ad_model)
typhoid_explainer = shap.TreeExplainer(typhoid_model)

generate_global_plots(malaria_model, malaria_explainer, background, FEATURE_ORDER_MALARIA, "malaria", f"{output_dir}/malaria")
generate_global_plots(ad_model,      ad_explainer,      background, FEATURE_ORDER_AD,      "ad",      f"{output_dir}/ad")
generate_global_plots(typhoid_model, typhoid_explainer, background, FEATURE_ORDER_TYPHOID, "typhoid", f"{output_dir}/typhoid")

print("\n🎉 Global SHAP plots generated successfully!")
print(f"Plots saved in: {output_dir}/")
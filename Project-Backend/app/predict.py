from catboost import CatBoostRegressor
import pandas as pd
import os
import shap
import matplotlib.pyplot as plt
import base64
from io import BytesIO

# ========================== PATHS ==========================
models_dir = os.path.join(os.path.dirname(__file__), "..", "models")
global_shap_dir = os.path.join(os.path.dirname(__file__), "..", "global_shap")   # Points to root/global_shap

# ========================== LOAD MODELS ==========================
malaria_model = CatBoostRegressor().load_model(os.path.join(models_dir, "malaria_model.cbm"))
ad_model      = CatBoostRegressor().load_model(os.path.join(models_dir, "ad_model.cbm"))
typhoid_model = CatBoostRegressor().load_model(os.path.join(models_dir, "typhoid_model.cbm"))

# ========================== SHAP EXPLAINERS (Local) ==========================
malaria_explainer = shap.TreeExplainer(malaria_model)
ad_explainer      = shap.TreeExplainer(ad_model)
typhoid_explainer = shap.TreeExplainer(typhoid_model)

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
# ========================== LOAD GLOBAL SHAP PLOTS ==========================
def get_global_shap_plots(disease: str):
    """Read pre-generated global SHAP plots from root/global_shap/"""
    disease_dir = os.path.join(global_shap_dir, disease)
    
    try:
        with open(os.path.join(disease_dir, "summary_plot.png"), "rb") as f:
            summary_b64 = base64.b64encode(f.read()).decode("utf-8")
        
        with open(os.path.join(disease_dir, "importance_bar.png"), "rb") as f:
            importance_b64 = base64.b64encode(f.read()).decode("utf-8")
        
        return {
            "summary_plot": f"data:image/png;base64,{summary_b64}",
            "importance_bar": f"data:image/png;base64,{importance_b64}"
        }
    except FileNotFoundError:
        return {"error": f"Global SHAP plots for '{disease}' not found. Please run generate_global_shap.py first."}
    except Exception as e:
        return {"error": f"Error loading global plots for {disease}: {str(e)}"}


# ========================== LOCAL SHAP PLOTS ==========================
def generate_local_shap_plots(model, explainer, df_input: pd.DataFrame, disease_name: str):
    shap_values = explainer.shap_values(df_input)[0]

    exp = shap.Explanation(
        values=shap_values,
        base_values=explainer.expected_value,
        data=df_input.iloc[0],
        feature_names=df_input.columns.tolist()
    )

    plots = {}

    # Waterfall
    plt.figure(figsize=(10, 5.8))
    shap.plots.waterfall(exp, show=False)
    plt.title(f"SHAP Waterfall - {disease_name.capitalize()} Risk")
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", dpi=160)
    plt.close()
    plots["waterfall"] = base64.b64encode(buf.getvalue()).decode("utf-8")

    # Bar Plot
    plt.figure(figsize=(9, 5.8))
    shap.plots.bar(exp, max_display=10, show=False)
    plt.title(f"Top 10 Features - {disease_name.capitalize()} Risk")
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", dpi=160)
    plt.close()
    plots["bar"] = base64.b64encode(buf.getvalue()).decode("utf-8")

    return plots


# ========================== MAIN FUNCTION ==========================
def run_prediction(features_dict: dict) -> dict:
    """Main prediction with Local SHAP + Global SHAP"""

    # Malaria Prediction
    f_m = features_dict["malaria"]
    f_m["district"] = str(f_m["district"])
    df_m = pd.DataFrame([f_m])[FEATURE_ORDER_MALARIA]
    malaria_pred = float(malaria_model.predict(df_m)[0])

    # Acute Diarrhea
    f_a = features_dict["ad"]
    f_a["district"] = str(f_a["district"])
    df_a = pd.DataFrame([f_a])[FEATURE_ORDER_AD]
    ad_pred = float(ad_model.predict(df_a)[0])

    # Typhoid
    f_t = features_dict["typhoid"]
    f_t["district"] = str(f_t["district"])
    df_t = pd.DataFrame([f_t])[FEATURE_ORDER_TYPHOID]
    typhoid_pred = float(typhoid_model.predict(df_t)[0])

    # Environmental data
    env = {
        "avg_temperature": round(f_t.get("avg_temperature", 0.0), 4),
        "avg_rainfall": round(f_t.get("avg_rainfall", 0.0), 4),
        "avg_humidity": round(f_t.get("avg_humidity", 0.0), 2),
        "flood_inundation": round(f_t.get("flood_inundation", 0.0), 6),
        "stagnant_water": round(f_t.get("stagnant_water", 0.0), 6),
        "mean_ndvi": round(f_t.get("mean_ndvi", 0.0), 6),
    }

    return {
        "malaria_risk_next_week": round(malaria_pred, 4),
        "ad_risk_next_week": round(ad_pred, 4),
        "typhoid_risk_next_week": round(typhoid_pred, 4),
        **env,
        "local_explanations": {
            "malaria": generate_local_shap_plots(malaria_model, malaria_explainer, df_m, "malaria"),
            "ad":      generate_local_shap_plots(ad_model,      ad_explainer,      df_a, "acute diarrhea"),
            "typhoid": generate_local_shap_plots(typhoid_model, typhoid_explainer, df_t, "typhoid")
        },
        "global_explanations": {
            "malaria": get_global_shap_plots("malaria"),
            "ad":      get_global_shap_plots("ad"),
            "typhoid": get_global_shap_plots("typhoid")
        }
    }
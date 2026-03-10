from catboost import CatBoostRegressor
import pandas as pd
import os

models_dir = os.path.join(os.path.dirname(__file__), "..", "models")

malaria_model = CatBoostRegressor().load_model(os.path.join(models_dir, "malaria_model.cbm"))
ad_model     = CatBoostRegressor().load_model(os.path.join(models_dir, "ad_model.cbm"))
typhoid_model = CatBoostRegressor().load_model(os.path.join(models_dir, "typhoid_model.cbm"))

#typhoid feature order
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

#malaria feature order
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

#ad feature order
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

def run_prediction(features_dict: dict) -> dict:
    #seperate feature sets
    #malaria
    f_m = features_dict["malaria"]
    f_m["district"] = str(f_m["district"])
    df_m = pd.DataFrame([f_m])[FEATURE_ORDER_MALARIA]
    malaria_pred = float(malaria_model.predict(df_m)[0])

    #ad
    f_a = features_dict["ad"]
    f_a["district"] = str(f_a["district"])
    df_a = pd.DataFrame([f_a])[FEATURE_ORDER_AD]
    ad_pred = float(ad_model.predict(df_a)[0])

    #typhoid
    f_t = features_dict["typhoid"]
    f_t["district"] = str(f_t["district"])
    df_t = pd.DataFrame([f_t])[FEATURE_ORDER_TYPHOID]
    typhoid_pred = float(typhoid_model.predict(df_t)[0])

    env = {
        "avg_temperature": f_t.get("avg_temperature", 0.0),
        "avg_rainfall": f_t.get("avg_rainfall", 0.0),
        "avg_humidity": f_t.get("avg_humidity", 0.0),
        "flood_inundation": f_t.get("flood_inundation", 0.0),
        "stagnant_water": f_t.get("stagnant_water", 0.0),
        "mean_ndvi": f_t.get("mean_ndvi", 0.0),
    }

    return {
        "malaria_risk_next_week": malaria_pred,
        "ad_risk_next_week": ad_pred,
        "typhoid_risk_next_week": typhoid_pred,
        **env
    }
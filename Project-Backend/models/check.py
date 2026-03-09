from catboost import CatBoostRegressor
model = CatBoostRegressor().load_model("typhoid_model.cbm")
print(model.feature_names_)   # Should show malaria_risk, malaria_risk_lag1, etc. — NOT malaria_cases
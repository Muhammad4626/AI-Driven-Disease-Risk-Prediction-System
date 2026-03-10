from catboost import CatBoostRegressor
model = CatBoostRegressor().load_model("typhoid_model.cbm")
print(model.feature_names_)
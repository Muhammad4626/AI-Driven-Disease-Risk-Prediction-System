#!/usr/bin/env python3
import os
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from catboost import CatBoostRegressor, Pool
import datetime

DEFAULT_TARGETS = [
    "malaria_risk_next_week",
    "ad_risk_next_week",
    "typhoid_risk_next_week"
]

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=str, default="processed_dataset_risk_based.csv")
    p.add_argument("--targets", type=str, nargs="+", default=DEFAULT_TARGETS)
    p.add_argument("--cat_features", type=str, nargs="+", default=["district"])
    p.add_argument("--test_weeks", type=int, default=8)
    p.add_argument("--outdir", type=str, default="outputs/models")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--iterations", type=int, default=1500)
    p.add_argument("--learning_rate", type=float, default=0.03)
    p.add_argument("--depth", type=int, default=6)
    p.add_argument("--early_stopping", type=int, default=100)
    p.add_argument("--verbose", type=int, default=100)
    p.add_argument("--cv_folds", type=int, default=4)
    return p.parse_args()


def chrono_split(df, test_weeks=8):
    df = df.sort_values(["year", "week_index"]).reset_index(drop=True)
    df["time_id"] = df["year"] * 100 + df["week_index"]

    unique_times = sorted(df["time_id"].unique())
    if len(unique_times) <= test_weeks:
        raise ValueError("Not enough weeks for split")

    test_times = unique_times[-test_weeks:]
    train_times = unique_times[:-test_weeks]

    train_df = df[df["time_id"].isin(train_times)].reset_index(drop=True)
    test_df = df[df["time_id"].isin(test_times)].reset_index(drop=True)

    train_df = train_df.drop(columns=["time_id"])
    test_df = test_df.drop(columns=["time_id"])

    return train_df, test_df


def prepare_feature_list(df, cat_features, target):
    all_targets = [
        "malaria_risk_next_week",
        "ad_risk_next_week",
        "typhoid_risk_next_week"
    ]

    disease_name = target.replace("_risk_next_week", "")
    ignore = set(["year", "week_index"]) | set(all_targets)

    feature_cols = []
    for col in df.columns:
        if col in ignore:
            continue
        #diasease specific features
        if disease_name in col:
            feature_cols.append(col)
        #shared features
        elif not any(d in col for d in ["malaria", "ad", "typhoid"]):
            feature_cols.append(col)

    #exclude cases
    feature_cols = [c for c in feature_cols if "_cases" not in c]

    #categorical first
    cat_cols = [c for c in cat_features if c in feature_cols]
    other_cols = [c for c in feature_cols if c not in cat_features]

    return cat_cols + other_cols


def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = float(np.sqrt(mse))
    r2 = r2_score(y_test, y_pred)
    return {"mae": mae, "rmse": rmse, "r2": r2, "y_pred": y_pred}


def run_time_series_cv(train_df, feature_cols, target, cat_feature_indices, params, folds):
    print("\nRunning Time Series Cross Validation")
    X = train_df[feature_cols]
    y = train_df[target]
    tscv = TimeSeriesSplit(n_splits=folds)
    results = []

    for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
        print(f"\nFold {fold+1}/{folds}")
        X_train = X.iloc[train_idx]
        y_train = y.iloc[train_idx]
        X_val = X.iloc[val_idx]
        y_val = y.iloc[val_idx]

        train_pool = Pool(X_train, y_train, cat_features=cat_feature_indices)
        val_pool = Pool(X_val, y_val, cat_features=cat_feature_indices)

        model = CatBoostRegressor(**params)
        model.fit(train_pool, eval_set=val_pool, verbose=False)

        preds = model.predict(X_val)
        mae = mean_absolute_error(y_val, preds)
        rmse = np.sqrt(mean_squared_error(y_val, preds))
        r2 = r2_score(y_val, preds)
        print(f"MAE={mae:.4f} RMSE={rmse:.4f} R2={r2:.4f}")

        results.append({"fold": fold+1, "mae": mae, "rmse": rmse, "r2": r2})

    cv_df = pd.DataFrame(results)
    print("\nCV Average Metrics")
    print(cv_df.mean(numeric_only=True))
    return cv_df


def main():
    args = parse_args()
    np.random.seed(args.seed)
    Path(args.outdir).mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    print("Loading dataset:", args.input)
    df = pd.read_csv(args.input)

    #expected columns
    expected_shared = [
        "district", "year", "week_index",
        "avg_rainfall", "avg_temperature", "avg_humidity",
        "population", "elevation_m", "river_status", "area_sq_km", "sanitation_index",
        "flood_inundation", "stagnant_water", "mean_ndvi",
        #risk,lags,rolls added by preprocess
    ]

    print("Dataset columns:", df.columns.tolist())

    metrics_rows = []

    for target in args.targets:
        print("\n" + "="*60)
        print("Training target:", target)

        if target not in df.columns:
            print(f"Target {target} not found → skipping")
            continue

        feature_cols = prepare_feature_list(df, args.cat_features, target)
        cat_feature_indices = [feature_cols.index(c) for c in args.cat_features if c in feature_cols]

        df_t = df.dropna(subset=[target]).copy()
        print("Rows available:", len(df_t))

        numeric_cols = [c for c in feature_cols if c not in args.cat_features]
        df_t[numeric_cols] = df_t[numeric_cols].fillna(df_t[numeric_cols].median())

        train_df, test_df = chrono_split(df_t, args.test_weeks)
        print("Train rows:", len(train_df))
        print("Test rows:", len(test_df))

        params = {
            "iterations": args.iterations,
            "learning_rate": args.learning_rate,
            "depth": args.depth,
            "loss_function": "RMSE",
            "random_seed": args.seed,
            "early_stopping_rounds": args.early_stopping
        }

        #cv
        run_time_series_cv(
            train_df,
            feature_cols,
            target,
            cat_feature_indices,
            params,
            args.cv_folds
        )

        #training
        print("\nTraining Final Model")
        X_train = train_df[feature_cols]
        y_train = train_df[target]
        X_test = test_df[feature_cols]
        y_test = test_df[target]

        train_pool = Pool(X_train, y_train, cat_features=cat_feature_indices)
        val_pool = Pool(X_test, y_test, cat_features=cat_feature_indices)

        model = CatBoostRegressor(**params)
        model.fit(train_pool, eval_set=val_pool, use_best_model=True, verbose=args.verbose)

        model_name = f"{target.replace('_next_week','')}_model_{now}.cbm"
        model_path = os.path.join(args.outdir, model_name)
        model.save_model(model_path)
        print("Saved model:", model_path)

        eval_res = evaluate_model(model, X_test, y_test)
        metrics_rows.append({
            "target": target,
            "mae": eval_res["mae"],
            "rmse": eval_res["rmse"],
            "r2": eval_res["r2"]
        })

    metrics_df = pd.DataFrame(metrics_rows)
    metrics_csv = os.path.join(args.outdir, f"metrics_summary_{now}.csv")
    metrics_df.to_csv(metrics_csv, index=False)
    print("\nTraining complete")
    print(metrics_df)


if __name__ == "__main__":
    main()
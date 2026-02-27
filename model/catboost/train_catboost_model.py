#!/usr/bin/env python3
"""
train_catboost_model.py

Train a CatBoostRegressor on preprocessed weekly district-level data.
Saves model, metadata JSON, and a CSV with evaluation metrics.

Usage:
    python train_catboost_model.py \
        --input preprocessed.csv \
        --target Malaria_Risk \
        --cat_features District \
        --time_split_weeks 8 \
        --output_dir outputs/models/malaria

Notes:
- Input CSV must contain: Year, District, week_index, and feature columns plus the target column.
- The script performs a chronological split by week_index (last `time_split_weeks` weeks used as test set).
- CatBoost handles categorical features natively; pass District as cat_feature.
"""

import os
import json
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error
from catboost import CatBoostRegressor, Pool
import joblib
import datetime

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=str, required=True, help="Preprocessed CSV file path")
    p.add_argument("--target", type=str, required=True, help="Target column name (e.g. Malaria_Risk)")
    p.add_argument("--cat_features", type=str, nargs="+", default=["District"], help="Categorical feature names")
    p.add_argument("--time_split_weeks", type=int, default=8, help="Number of weeks to reserve for test (chronological split)")
    p.add_argument("--output_dir", type=str, default="outputs/models", help="Directory to save model and artifacts")
    p.add_argument("--random_seed", type=int, default=42)
    p.add_argument("--iterations", type=int, default=2000)
    p.add_argument("--early_stopping_rounds", type=int, default=100)
    p.add_argument("--learning_rate", type=float, default=0.05)
    p.add_argument("--depth", type=int, default=6)
    p.add_argument("--verbose", type=int, default=100)
    return p.parse_args()

def chrono_train_test_split(df, week_col="week_index", test_weeks=8):
    """
    Chronological split: use the latest `test_weeks` distinct week_index values as test set.
    """
    weeks = sorted(df[week_col].unique())
    if len(weeks) <= test_weeks:
        raise ValueError(f"Not enough weeks ({len(weeks)}) to reserve {test_weeks} test weeks")
    test_weeks_list = weeks[-test_weeks:]
    train_weeks_list = weeks[:-test_weeks]
    train_df = df[df[week_col].isin(train_weeks_list)].reset_index(drop=True)
    test_df = df[df[week_col].isin(test_weeks_list)].reset_index(drop=True)
    return train_df, test_df

def main():
    args = parse_args()
    np.random.seed(args.random_seed)

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    # 1) Load
    df = pd.read_csv(args.input)
    if args.target not in df.columns:
        raise ValueError(f"Target {args.target} not found in input CSV columns: {df.columns.tolist()}")

    # 2) Drop rows with missing target
    df = df.dropna(subset=[args.target]).copy()
    print(f"Loaded {len(df)} rows from {args.input}. After dropping NA target -> {len(df)} rows")

    # 3) Feature selection:
    #    - we'll use all numeric columns except identifiers and the target, plus passed cat_features
    ignore_cols = set(["Year", "week_index", args.target])
    # also ignore columns that are pure identifiers sometimes present
    id_like = set(["id", "ID"])
    ignore_cols |= id_like
    all_cols = df.columns.tolist()

    # Ensure categorical features exist
    for c in args.cat_features:
        if c not in all_cols:
            raise ValueError(f"Categorical feature '{c}' not present in input columns")

    # Build feature list: categorical + numeric features excluding ignore
    cat_features = [c for c in args.cat_features if c in all_cols]
    feature_cols = []
    for c in all_cols:
        if c in ignore_cols or c == "District":  # District in cat_features
            continue
        if c in cat_features:
            continue
        # keep numeric and lag features; exclude target
        feature_cols.append(c)
    # Prepend categorical features
    feature_cols = cat_features + feature_cols

    # Filter dataframe to relevant columns
    df_features = df[feature_cols + [args.target, "week_index"]].copy()

    # Fill missing numeric features sensibly
    numeric_cols = [c for c in feature_cols if c not in cat_features]
    df_features[numeric_cols] = df_features[numeric_cols].fillna(df_features[numeric_cols].median())

    # 4) Chronological split by week_index
    train_df, test_df = chrono_train_test_split(df_features, week_col="week_index", test_weeks=args.time_split_weeks)
    print(f"Train rows: {len(train_df)}, Test rows: {len(test_df)} (last {args.time_split_weeks} weeks used for test)")

    X_train = train_df[feature_cols]
    y_train = train_df[args.target]
    X_test = test_df[feature_cols]
    y_test = test_df[args.target]

    # 5) Convert categorical columns indices for CatBoost Pool
    cat_feature_indices = [feature_cols.index(c) for c in cat_features]

    train_pool = Pool(data=X_train, label=y_train, cat_features=cat_feature_indices)
    test_pool = Pool(data=X_test, label=y_test, cat_features=cat_feature_indices)

    # 6) CatBoost model config
    model = CatBoostRegressor(
        iterations=args.iterations,
        learning_rate=args.learning_rate,
        depth=args.depth,
        loss_function="RMSE",
        random_seed=args.random_seed,
        early_stopping_rounds=args.early_stopping_rounds,
        verbose=args.verbose
    )

    # 7) Fit
    print("Starting CatBoost training...")
    model.fit(train_pool, eval_set=test_pool, use_best_model=True)

    # 8) Predict and evaluate
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred, squared=False)
    print(f"Test MAE: {mae:.4f}, RMSE: {rmse:.4f}")

    # Save predictions for analysis
    preds_df = test_df.copy()
    preds_df["y_true"] = y_test.values
    preds_df["y_pred"] = y_pred
    preds_csv = os.path.join(args.output_dir, f"preds_{args.target}_{now}.csv")
    preds_df.to_csv(preds_csv, index=False)

    # 9) Save model and metadata
    model_path = os.path.join(args.output_dir, f"catboost_{args.target}_{now}.cbm")
    model.save_model(model_path)
    print("Saved CatBoost model to:", model_path)

    meta = {
        "model_path": model_path,
        "target": args.target,
        "feature_cols": feature_cols,
        "cat_features": cat_features,
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "mae": float(mae),
        "rmse": float(rmse),
        "timestamp": now,
        "training_args": {
            "iterations": args.iterations,
            "learning_rate": args.learning_rate,
            "depth": args.depth,
            "early_stopping_rounds": args.early_stopping_rounds
        }
    }
    meta_path = os.path.join(args.output_dir, f"metadata_{args.target}_{now}.json")
    with open(meta_path, "w") as fh:
        json.dump(meta, fh, indent=2)
    print("Saved metadata to:", meta_path)

    # 10) Feature importance (CatBoost native)
    fi = model.get_feature_importance(train_pool, type="FeatureImportance")
    fi_df = pd.DataFrame({"feature": feature_cols, "importance": fi})
    fi_csv = os.path.join(args.output_dir, f"feature_importance_{args.target}_{now}.csv")
    fi_df.sort_values("importance", ascending=False).to_csv(fi_csv, index=False)
    print("Saved feature importance to:", fi_csv)

    # 11) Save model via joblib wrapper for easy reload (optional)
    joblib.dump({"model_path": model_path, "feature_cols": feature_cols, "cat_features": cat_features}, os.path.join(args.output_dir, f"model_info_{args.target}_{now}.pkl"))
    print("Saved model info pickle.")

if __name__ == "__main__":
    main()

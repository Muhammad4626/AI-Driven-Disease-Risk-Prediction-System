#!/usr/bin/env python3
import os
import json
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from catboost import CatBoostRegressor, Pool
import joblib
import datetime

DEFAULT_TARGETS = ["Malaria_Risk_next_week", "AD_Risk_next_week", "Typhoid_Risk_next_week"]

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=str, default="processed_dataset.csv", help="Preprocessed dataset CSV")
    p.add_argument("--targets", type=str, nargs="+", default=DEFAULT_TARGETS, help="Target columns to train")
    p.add_argument("--cat_features", type=str, nargs="+", default=["District"], help="Categorical features")
    p.add_argument("--test_weeks", type=int, default=8, help="Number of most recent weeks to reserve as test set")
    p.add_argument("--outdir", type=str, default="outputs/models", help="Output directory for models and artifacts")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--iterations", type=int, default=1500)
    p.add_argument("--learning_rate", type=float, default=0.03)
    p.add_argument("--depth", type=int, default=6)
    p.add_argument("--early_stopping", type=int, default=100)
    p.add_argument("--verbose", type=int, default=100)
    return p.parse_args()

def chrono_split(df, test_weeks=8):
    """
    Chronological split using Year + week_index.
    Reserves the last `test_weeks` real chronological weeks as test set.
    """

    # Sort properly by full time order
    df = df.sort_values(["Year", "week_index"]).reset_index(drop=True)

    # Create a continuous time identifier
    # Example: 202401, 202402, ..., 202552
    df["time_id"] = df["Year"] * 100 + df["week_index"]

    # Get unique time steps in proper order
    unique_times = sorted(df["time_id"].unique())

    if len(unique_times) <= test_weeks:
        raise ValueError(
            f"Not enough distinct weeks ({len(unique_times)}) "
            f"for test_weeks={test_weeks}"
        )

    # Split
    test_times = unique_times[-test_weeks:]
    train_times = unique_times[:-test_weeks]

    train_df = df[df["time_id"].isin(train_times)].reset_index(drop=True)
    test_df = df[df["time_id"].isin(test_times)].reset_index(drop=True)

    # Drop helper column
    train_df = train_df.drop(columns=["time_id"])
    test_df = test_df.drop(columns=["time_id"])

    return train_df, test_df

def prepare_feature_list(df, cat_features, target):
    all_targets = [
        "Malaria_Risk_next_week",
        "AD_Risk_next_week",
        "Typhoid_Risk_next_week"
    ]

    # Identify disease name
    disease_name = target.replace("_Risk_next_week", "")

    ignore = set(["Year", "week_index"]) | set(all_targets)

    feature_cols = []

    for col in df.columns:
        if col in ignore:
            continue
        
        # If column contains disease name, keep it
        if disease_name in col:
            feature_cols.append(col)
        
        # If column is non-disease related, keep it
        elif not any(d in col for d in ["Malaria", "AD", "Typhoid"]):
            feature_cols.append(col)

    # Put categorical first
    feature_cols = [c for c in cat_features if c in feature_cols] + \
                   [c for c in feature_cols if c not in cat_features]

    return feature_cols

def train_single_model(X_train, y_train, X_val, y_val, feature_cols, cat_features_idx, params, model_out_path, verbose):
    train_pool = Pool(data=X_train, label=y_train, cat_features=cat_features_idx)
    val_pool = Pool(data=X_val, label=y_val, cat_features=cat_features_idx)
    model = CatBoostRegressor(**params)
    model.fit(train_pool, eval_set=val_pool, use_best_model=True, verbose=verbose)
    model.save_model(model_out_path)
    return model

def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = float(np.sqrt(mse))
    r2 = r2_score(y_test, y_pred) if len(y_test) > 1 else float("nan")
    return {"mae": float(mae), "rmse": rmse, "r2": float(r2), "y_pred": y_pred}

def main():
    args = parse_args()
    np.random.seed(args.seed)
    Path(args.outdir).mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    print("Loading dataset:", args.input)
    df = pd.read_csv(args.input)

    metrics_rows = []

    for target in args.targets:
        print("\n" + "="*60)
        print("Training target:", target)
        if target not in df.columns:
            print(f"Target {target} not found in dataset columns. Skipping.")
            continue

        #features list
        feature_cols = prepare_feature_list(df, args.cat_features, target)
        cat_feature_indices = [feature_cols.index(c) for c in args.cat_features if c in feature_cols]

        #dropping rows with missing target
        df_t = df.dropna(subset=[target]).copy()
        print(f"Rows available for {target}: {len(df_t)}")

        #fill numeric Nulls with median (per-feature)
        numeric_cols = [c for c in feature_cols if c not in args.cat_features]
        df_t[numeric_cols] = df_t[numeric_cols].fillna(df_t[numeric_cols].median())

        #chronological split
        train_df, test_df = chrono_split(df_t, test_weeks=args.test_weeks)
        X_train = train_df[feature_cols]
        y_train = train_df[target]
        X_test = test_df[feature_cols]
        y_test = test_df[target]

        print(f"Train rows: {len(X_train)}, Test rows: {len(X_test)}")

        #model params
        params = {
            "iterations": args.iterations,
            "learning_rate": args.learning_rate,
            "depth": args.depth,
            "loss_function": "RMSE",
            "random_seed": args.seed,
            "early_stopping_rounds": args.early_stopping
        }

        model_name = f"catboost_{target}_{now}.cbm"
        model_path = os.path.join(args.outdir, model_name)

        #train model
        model = train_single_model(X_train, y_train, X_test, y_test, feature_cols, cat_feature_indices, params, model_path, args.verbose)
        print("Saved model to:", model_path)

        #evaluate
        eval_res = evaluate_model(model, X_test, y_test)
        y_pred = eval_res["y_pred"]

        #save preds CSV
        preds_df = test_df.copy()
        preds_df["y_true"] = y_test.values
        preds_df["y_pred"] = y_pred
        preds_csv = os.path.join(args.outdir, f"preds_{target}_{now}.csv")
        preds_df.to_csv(preds_csv, index=False)
        print("Saved predictions to:", preds_csv)

        #feature importance
        fi = model.get_feature_importance(Pool(X_train, label=y_train, cat_features=cat_feature_indices), type="FeatureImportance")
        fi_df = pd.DataFrame({"feature": feature_cols, "importance": fi}).sort_values("importance", ascending=False)
        fi_csv = os.path.join(args.outdir, f"feature_importance_{target}_{now}.csv")
        fi_df.to_csv(fi_csv, index=False)
        print("Saved feature importance to:", fi_csv)

        #metadata
        meta = {
            "target": target,
            "model_path": model_path,
            "feature_cols": feature_cols,
            "cat_features": args.cat_features,
            "train_rows": len(X_train),
            "test_rows": len(X_test),
            "metrics": {"mae": eval_res["mae"], "rmse": eval_res["rmse"], "r2": eval_res["r2"]},
            "params": params,
            "timestamp": now
        }
        meta_path = os.path.join(args.outdir, f"metadata_{target}_{now}.json")
        with open(meta_path, "w") as fh:
            json.dump(meta, fh, indent=2)
        print("Saved metadata to:", meta_path)

        #save model info convenience pickle
        joblib.dump({"model_path": model_path, "feature_cols": feature_cols, "cat_features": args.cat_features}, os.path.join(args.outdir, f"model_info_{target}_{now}.pkl"))

        metrics_rows.append({
            "target": target,
            "model_path": model_path,
            "mae": eval_res["mae"],
            "rmse": eval_res["rmse"],
            "r2": eval_res["r2"],
            "train_rows": len(X_train),
            "test_rows": len(X_test)
        })

    #summary metrics
    metrics_df = pd.DataFrame(metrics_rows)
    metrics_csv = os.path.join(args.outdir, f"metrics_summary_{now}.csv")
    metrics_df.to_csv(metrics_csv, index=False)
    print("\nSaved metrics summary to:", metrics_csv)
    print("\nTraining complete.")

if __name__ == "__main__":
    main()

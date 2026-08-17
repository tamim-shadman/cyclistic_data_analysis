"""Predictive modeling utilities for Cyclistic bike-share analysis."""

from __future__ import annotations

import time
import warnings
from typing import Dict, List, Optional, Tuple

import lightgbm as lgb
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, TimeSeriesSplit

matplotlib.use("Agg")

warnings.filterwarnings("ignore")


def safe_mape(y_true, y_pred):
    """Calculate MAPE safely handling zero values."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    denom = np.where(y_true == 0, 1.0, y_true)
    return np.mean(np.abs((y_true - y_pred) / denom)) * 100


def coarse_to_fine_tuning(
    model, param_grid_coarse: dict, param_grid_fine: dict, X_train, y_train
):
    """
    RandomizedSearchCV followed by a smaller GridSearchCV.
    """
    tscv = TimeSeriesSplit(n_splits=3)

    rs = RandomizedSearchCV(
        estimator=model,
        param_distributions=param_grid_coarse,
        n_iter=8,
        scoring="neg_mean_squared_error",
        cv=tscv,
        random_state=42,
        n_jobs=-1,
        verbose=0,
    )
    rs.fit(X_train, y_train)

    best_coarse_params = rs.best_params_

    if not param_grid_fine:
        return rs.best_estimator_, best_coarse_params, best_coarse_params

    fine = {k: (v if isinstance(v, list) else [v]) for k, v in param_grid_fine.items()}

    for k, v in best_coarse_params.items():
        if k in fine and v not in fine[k]:
            fine[k] = fine[k] + [v]

    gs = GridSearchCV(
        estimator=model,
        param_grid=fine,
        scoring="neg_mean_squared_error",
        cv=tscv,
        n_jobs=-1,
        verbose=0,
    )
    gs.fit(X_train, y_train)

    return gs.best_estimator_, best_coarse_params, gs.best_params_


def build_predictive_models(
    df_clean: Optional[pd.DataFrame]
) -> Tuple[Optional[Dict], Optional[object]]:
    """Build and tune predictive models for ride demand forecasting."""
    if df_clean is None:
        print("❌ No data available for predictive modeling")
        return None, None

    print("🤖 Starting Predictive Modeling with Coarse-to-Fine Tuning...")

    if "start_time" not in df_clean.columns:
        print("❌ 'start_time' column not found")
        return None, None

    # 1. Prepare daily time-series features
    print("\n1. 📈 TIME SERIES PREPARATION")
    try:
        grp = df_clean.groupby(df_clean["start_time"].dt.date)

        daily_data = pd.DataFrame({"total_rides": grp.size()})

        if "ride_duration" in df_clean.columns:
            daily_data["avg_duration"] = grp["ride_duration"].mean()
        else:
            daily_data["avg_duration"] = 0

        if "distance_km" in df_clean.columns:
            daily_data["avg_distance"] = grp["distance_km"].mean()
        else:
            daily_data["avg_distance"] = 0

        if "member_type" in df_clean.columns:
            daily_data["member_rides"] = grp["member_type"].apply(lambda x: (x == "member").sum())
        else:
            daily_data["member_rides"] = 0

        daily_data.index = pd.to_datetime(daily_data.index)
        daily_data.index.name = "date"

        daily_data["day_of_week"] = daily_data.index.dayofweek
        daily_data["month"] = daily_data.index.month
        daily_data["quarter"] = daily_data.index.quarter
        daily_data["day_of_year"] = daily_data.index.dayofyear
        daily_data["week_of_year"] = daily_data.index.isocalendar().week.astype(int)

        for lag in [1, 7, 14, 21, 28]:
            daily_data[f"rides_lag_{lag}"] = daily_data["total_rides"].shift(lag)

        for window in [7, 14, 30]:
            daily_data[f"rides_rolling_mean_{window}"] = daily_data["total_rides"].rolling(window=window).mean()
            daily_data[f"rides_rolling_std_{window}"] = daily_data["total_rides"].rolling(window=window).std()

        daily_data = daily_data.dropna()

        print(f"✅ Prepared time series data with {len(daily_data)} daily observations")

    except Exception as e:
        print(f"❌ Error preparing time series data: {e}")
        return None, None

    # 2. Split data
    print("\n2. ✂️ DATA SPLITTING")
    test_days = 30

    if len(daily_data) <= test_days:
        test_days = max(7, int(len(daily_data) * 0.2))

    if len(daily_data) <= test_days + 14:
        print("❌ Not enough daily data for reliable train/test splitting.")
        return None, None

    train_data = daily_data.iloc[:-test_days]
    test_data = daily_data.iloc[-test_days:]

    X_train = train_data.drop(columns=["total_rides"]).select_dtypes(include=[np.number])
    y_train = train_data["total_rides"]

    X_test = test_data.drop(columns=["total_rides"]).select_dtypes(include=[np.number])
    y_test = test_data["total_rides"]

    X_test = X_test[X_train.columns]

    X_train = X_train.replace([np.inf, -np.inf], np.nan).fillna(0)
    X_test = X_test.replace([np.inf, -np.inf], np.nan).fillna(0)

    if X_train.shape[1] == 0:
        print("❌ No numeric features available for modeling.")
        return None, None

    feature_cols = X_train.columns.tolist()
    print(f"  Training data: {len(X_train)} days | Testing data: {len(X_test)} days")

    # 3. Model training and tuning
    print("\n3. 🧠 MODEL TRAINING & HYPERPARAMETER TUNING")

    tuning_configs = {
        "Random Forest": {
            "model": RandomForestRegressor(random_state=42, n_jobs=-1),
            "coarse": {
                "n_estimators": [100, 200],
                "max_depth": [10, 20, None],
                "min_samples_split": [5, 10],
                "min_samples_leaf": [2, 5],
            },
            "fine": {
                "n_estimators": [150, 200],
                "max_depth": [10, 20, None],
                "min_samples_split": [10],
                "min_samples_leaf": [4],
            },
        },
        "XGBoost": {
            "model": xgb.XGBRegressor(random_state=42, verbosity=0, objective="reg:squarederror"),
            "coarse": {
                "n_estimators": [100, 200],
                "max_depth": [3, 6, 9],
                "learning_rate": [0.05, 0.1],
                "subsample": [0.8],
                "colsample_bytree": [0.8],
            },
            "fine": {
                "n_estimators": [150, 200],
                "max_depth": [4, 6],
                "learning_rate": [0.08, 0.1],
                "subsample": [0.8],
                "colsample_bytree": [0.8],
            },
        },
        "LightGBM": {
            "model": lgb.LGBMRegressor(random_state=42, verbose=-1, n_jobs=-1),
            "coarse": {
                "n_estimators": [100, 200],
                "max_depth": [3, 5, -1],
                "num_leaves": [15, 31],
                "learning_rate": [0.05, 0.1],
                "min_child_samples": [20, 30],
            },
            "fine": {
                "n_estimators": [150, 200],
                "max_depth": [3, 5],
                "num_leaves": [25, 31],
                "learning_rate": [0.08, 0.1],
                "min_child_samples": [25, 30],
            },
        },
    }

    results = {}

    # Baseline linear regression
    print("\nTraining Linear Regression (Baseline)...")
    start_time = time.time()

    lr_model = LinearRegression()
    lr_model.fit(X_train, y_train)
    y_pred = lr_model.predict(X_test)

    results["Linear Regression"] = {
        "model": lr_model,
        "predictions": y_pred,
        "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
        "mae": float(mean_absolute_error(y_test, y_pred)),
        "r2": float(r2_score(y_test, y_pred)),
        "mape": float(safe_mape(y_test, y_pred)),
        "training_time": time.time() - start_time,
    }

    print(
        f"    ✅ Completed in {results['Linear Regression']['training_time']:.2f}s | "
        f"RMSE: {results['Linear Regression']['rmse']:.2f} | R²: {results['Linear Regression']['r2']:.4f}"
    )

    # Tuned tree models
    for name, config in tuning_configs.items():
        print(f"\nTraining {name}...")
        start_time = time.time()

        try:
            best_model, coarse_params, fine_params = coarse_to_fine_tuning(
                config["model"], config["coarse"], config["fine"], X_train, y_train
            )

            y_pred = best_model.predict(X_test)
            training_time = time.time() - start_time

            results[name] = {
                "model": best_model,
                "predictions": y_pred,
                "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
                "mae": float(mean_absolute_error(y_test, y_pred)),
                "r2": float(r2_score(y_test, y_pred)),
                "mape": float(safe_mape(y_test, y_pred)),
                "training_time": training_time,
            }

            print(f"    ⚙️ Phase 1 Best: {coarse_params}")
            print(f"    ⚙️ Phase 2 Best: {fine_params}")
            print(
                f"    ✅ Total Tuning Time: {training_time:.2f}s | "
                f"RMSE: {results[name]['rmse']:.2f} | R²: {results[name]['r2']:.4f}"
            )

        except Exception as e:
            print(f"    ❌ Error tuning {name}: {e}")
            continue

    if not results:
        print("❌ No models were successfully trained")
        return None, None

    # 4. Model comparison
    print("\n4. 📊 MODEL COMPARISON")

    comparison_df = pd.DataFrame(
        {
            "Model": list(results.keys()),
            "RMSE": [results[name]["rmse"] for name in results.keys()],
            "MAE": [results[name]["mae"] for name in results.keys()],
            "MAPE (%)": [results[name]["mape"] for name in results.keys()],
            "R²": [results[name]["r2"] for name in results.keys()],
            "Training Time (s)": [results[name]["training_time"] for name in results.keys()],
        }
    ).sort_values("R²", ascending=False).reset_index(drop=True)

    print("\n" + comparison_df.to_string(index=False))

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    axes[0, 0].bar(comparison_df["Model"], comparison_df["RMSE"], color="coral", edgecolor="black")
    axes[0, 0].set_title("RMSE (Lower is Better)", fontsize=12, fontweight="bold")
    axes[0, 0].set_ylabel("RMSE")
    axes[0, 0].tick_params(axis="x", rotation=45)
    axes[0, 0].grid(axis="y", alpha=0.3)

    axes[0, 1].bar(comparison_df["Model"], comparison_df["MAE"], color="skyblue", edgecolor="black")
    axes[0, 1].set_title("MAE (Lower is Better)", fontsize=12, fontweight="bold")
    axes[0, 1].set_ylabel("MAE")
    axes[0, 1].tick_params(axis="x", rotation=45)
    axes[0, 1].grid(axis="y", alpha=0.3)

    axes[1, 0].bar(comparison_df["Model"], comparison_df["R²"], color="lightgreen", edgecolor="black")
    axes[1, 0].set_title("R² Score (Higher is Better)", fontsize=12, fontweight="bold")
    axes[1, 0].set_ylabel("R² Score")
    axes[1, 0].tick_params(axis="x", rotation=45)
    axes[1, 0].grid(axis="y", alpha=0.3)
    axes[1, 0].set_ylim([min(0, comparison_df["R²"].min() - 0.1), 1])

    axes[1, 1].bar(comparison_df["Model"], comparison_df["Training Time (s)"], color="plum", edgecolor="black")
    axes[1, 1].set_title("Training Time (seconds)", fontsize=12, fontweight="bold")
    axes[1, 1].set_ylabel("Time (s)")
    axes[1, 1].tick_params(axis="x", rotation=45)
    axes[1, 1].grid(axis="y", alpha=0.3)

    plt.suptitle("Model Performance Comparison (Tuned)", fontsize=16, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig("eda_outputs/model_comparison.png", dpi=300, bbox_inches="tight")
    plt.close()

    # 5. Best model visualization
    print("\n5. 🏆 BEST MODEL VISUALIZATION")

    best_model_name = comparison_df.loc[comparison_df["R²"].idxmax(), "Model"]
    best_model = results[best_model_name]["model"]
    best_predictions = results[best_model_name]["predictions"]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))

    ax1.plot(test_data.index, y_test.values, label="Actual", color="blue", linewidth=2, marker="o", markersize=4)
    ax1.plot(test_data.index, best_predictions, label="Predicted", color="red", linewidth=2, linestyle="--", marker="x", markersize=4)
    ax1.fill_between(test_data.index, y_test.values, best_predictions, alpha=0.2, color="gray", label="Error")
    ax1.set_title(f"Ride Demand Forecasting: {best_model_name} (Tuned)", fontsize=16, fontweight="bold")
    ax1.set_xlabel("Date", fontsize=12)
    ax1.set_ylabel("Number of Rides", fontsize=12)
    ax1.legend(loc="upper right")
    ax1.grid(True, alpha=0.3)

    ax2.scatter(y_test.values, best_predictions, alpha=0.6, color="teal", edgecolors="black", s=60)
    min_val = min(y_test.min(), best_predictions.min())
    max_val = max(y_test.max(), best_predictions.max())
    ax2.plot([min_val, max_val], [min_val, max_val], "r--", linewidth=2, label="Perfect Prediction")
    ax2.set_xlabel("Actual Rides", fontsize=12)
    ax2.set_ylabel("Predicted Rides", fontsize=12)
    ax2.set_title(f"Actual vs Predicted: {best_model_name} (Tuned)", fontsize=16, fontweight="bold")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("eda_outputs/best_model_forecast.png", dpi=300, bbox_inches="tight")
    plt.close()

    # 6. Feature importance
    print("\n6. 🔍 FEATURE IMPORTANCE")

    if hasattr(best_model, "feature_importances_"):
        feature_importance = pd.DataFrame(
            {"Feature": feature_cols, "Importance": best_model.feature_importances_}
        ).sort_values("Importance", ascending=True)

        print("\nTop 10 Most Important Features:")
        print(feature_importance.tail(10).to_string(index=False))

        plt.figure(figsize=(10, 8))
        colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(feature_importance)))
        feature_importance.plot(x="Feature", y="Importance", kind="barh", color=colors, edgecolor="black")
        plt.title(f"Feature Importance: {best_model_name}", fontsize=16, fontweight="bold")
        plt.xlabel("Importance", fontsize=12)
        plt.grid(axis="x", alpha=0.3)
        plt.tight_layout()
        plt.savefig("eda_outputs/feature_importance.png", dpi=300, bbox_inches="tight")
        plt.close()

    elif hasattr(best_model, "coef_"):
        coef_importance = pd.DataFrame(
            {"Feature": feature_cols, "Coefficient": best_model.coef_}
        ).sort_values("Coefficient", key=abs, ascending=True)

        plt.figure(figsize=(10, 8))
        colors = ["red" if c < 0 else "blue" for c in coef_importance["Coefficient"]]
        coef_importance.plot(x="Feature", y="Coefficient", kind="barh", color=colors, edgecolor="black")
        plt.title("Feature Coefficients: Linear Regression", fontsize=16, fontweight="bold")
        plt.axvline(x=0, color="black", linewidth=0.8)
        plt.grid(axis="x", alpha=0.3)
        plt.tight_layout()
        plt.savefig("eda_outputs/feature_importance.png", dpi=300, bbox_inches="tight")
        plt.close()

    print("\n" + "=" * 60)
    print("✅ PREDICTIVE MODELING SUMMARY")
    print("=" * 60)
    print(f"  Best Model: {best_model_name}")
    print(f"  RMSE: {results[best_model_name]['rmse']:.2f} rides")
    print(f"  MAE: {results[best_model_name]['mae']:.2f} rides")
    print(f"  MAPE: {results[best_model_name]['mape']:.1f}%")
    print(f"  R²: {results[best_model_name]['r2']:.4f}")
    print("=" * 60)

    return results, best_model
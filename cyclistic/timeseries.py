"""Time series analysis utilities for Cyclistic bike-share analysis."""

from __future__ import annotations

import warnings
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller

import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")


def perform_time_series_analysis(df_clean: pd.DataFrame) -> Optional[Dict]:
    """Perform time series analysis on ride data."""
    if df_clean is None:
        print("❌ No data available for time series analysis")
        return None

    print("📈 Starting Time Series Analysis...")

    if "started_at" not in df_clean.columns:
        print("❌ 'started_at' column not found - cannot perform time series analysis")
        return None

    # Ensure datetime
    df_ts = df_clean.copy()
    df_ts["started_at"] = pd.to_datetime(df_ts["started_at"], errors="coerce")
    df_ts = df_ts.dropna(subset=["started_at"])

    if len(df_ts) == 0:
        print("❌ No valid datetime data")
        return None

    # Set datetime index
    df_ts = df_ts.set_index("started_at").sort_index()

    results = {}

    # 1. Daily ride counts
    print("\n1. 📅 DAILY RIDE COUNTS")
    daily_rides = df_ts.resample("D").size()
    results["daily_rides"] = daily_rides

    print(f"  Date range: {daily_rides.index.min()} to {daily_rides.index.max()}")
    print(f"  Total days: {len(daily_rides)}")
    print(f"  Mean daily rides: {daily_rides.mean():.1f}")
    print(f"  Std daily rides: {daily_rides.std():.1f}")

    # Plot daily rides
    plt.figure(figsize=(14, 6))
    daily_rides.plot(color="steelblue", alpha=0.7)
    plt.title("Daily Ride Counts Over Time", fontsize=16, fontweight="bold")
    plt.xlabel("Date", fontsize=14)
    plt.ylabel("Number of Rides", fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("eda_outputs/daily_rides.png", dpi=300, bbox_inches="tight")
    plt.show()

    # 2. Weekly patterns
    print("\n2. 📊 WEEKLY PATTERNS")
    weekly_rides = df_ts.resample("W").size()
    results["weekly_rides"] = weekly_rides

    # Day of week analysis
    df_ts["day_of_week"] = df_ts.index.dayofweek
    dow_counts = df_ts.groupby("day_of_week").size()
    dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    dow_counts.index = [dow_names[i] for i in dow_counts.index]

    print("  Rides by day of week:")
    for day, count in dow_counts.items():
        print(f"    {day}: {count:,}")

    plt.figure(figsize=(10, 6))
    dow_counts.plot(kind="bar", color="coral", edgecolor="black")
    plt.title("Rides by Day of Week", fontsize=16, fontweight="bold")
    plt.xlabel("Day of Week", fontsize=14)
    plt.ylabel("Number of Rides", fontsize=14)
    plt.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig("eda_outputs/rides_by_dow.png", dpi=300, bbox_inches="tight")
    plt.show()

    results["dow_counts"] = dow_counts

    # 3. Monthly patterns
    print("\n3. 📆 MONTHLY PATTERNS")
    monthly_rides = df_ts.resample("M").size()
    results["monthly_rides"] = monthly_rides

    print("  Rides by month:")
    for month, count in monthly_rides.items():
        print(f"    {month.strftime('%Y-%m')}: {count:,}")

    plt.figure(figsize=(12, 6))
    monthly_rides.plot(kind="bar", color="mediumseagreen", edgecolor="black")
    plt.title("Rides by Month", fontsize=16, fontweight="bold")
    plt.xlabel("Month", fontsize=14)
    plt.ylabel("Number of Rides", fontsize=14)
    plt.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig("eda_outputs/rides_by_month.png", dpi=300, bbox_inches="tight")
    plt.show()

    # 4. Hourly patterns
    print("\n4. ⏰ HOURLY PATTERNS")
    df_ts["hour"] = df_ts.index.hour
    hourly_counts = df_ts.groupby("hour").size()
    results["hourly_counts"] = hourly_counts

    print("  Rides by hour:")
    for hour, count in hourly_counts.items():
        print(f"    {hour:02d}:00: {count:,}")

    plt.figure(figsize=(12, 6))
    hourly_counts.plot(kind="bar", color="gold", edgecolor="black")
    plt.title("Rides by Hour of Day", fontsize=16, fontweight="bold")
    plt.xlabel("Hour", fontsize=14)
    plt.ylabel("Number of Rides", fontsize=14)
    plt.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig("eda_outputs/rides_by_hour.png", dpi=300, bbox_inches="tight")
    plt.show()

    # 5. Seasonal decomposition (if enough data)
    print("\n5. 🔄 SEASONAL DECOMPOSITION")
    if len(daily_rides) >= 30:
        try:
            # Use additive decomposition
            decomposition = seasonal_decompose(daily_rides, model="additive", period=7)
            results["decomposition"] = decomposition

            fig, axes = plt.subplots(4, 1, figsize=(14, 12))
            decomposition.observed.plot(ax=axes[0], title="Observed", color="steelblue")
            decomposition.trend.plot(ax=axes[1], title="Trend", color="orange")
            decomposition.seasonal.plot(ax=axes[2], title="Seasonal (Weekly)", color="green")
            decomposition.resid.plot(ax=axes[3], title="Residual", color="red")
            for ax in axes:
                ax.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig("eda_outputs/seasonal_decomposition.png", dpi=300, bbox_inches="tight")
            plt.show()

            print("  ✅ Seasonal decomposition completed")
            print(f"  Trend range: {decomposition.trend.min():.1f} to {decomposition.trend.max():.1f}")
            print(f"  Seasonal amplitude: {decomposition.seasonal.max() - decomposition.seasonal.min():.1f}")

        except Exception as e:
            print(f"  ⚠️ Seasonal decomposition failed: {e}")
            results["decomposition"] = None
    else:
        print("  ⚠️ Not enough data for seasonal decomposition (need ≥30 days)")
        results["decomposition"] = None

    # 6. Stationarity test
    print("\n6. 📐 STATIONARITY TEST (Augmented Dickey-Fuller)")
    try:
        adf_result = adfuller(daily_rides.dropna())
        results["adf_test"] = {
            "statistic": adf_result[0],
            "p_value": adf_result[1],
            "critical_values": adf_result[4],
        }
        print(f"  ADF Statistic: {adf_result[0]:.4f}")
        print(f"  p-value: {adf_result[1]:.4f}")
        print("  Critical Values:")
        for key, value in adf_result[4].items():
            print(f"    {key}: {value:.4f}")
        if adf_result[1] < 0.05:
            print("  ✅ Series is stationary (reject null hypothesis)")
        else:
            print("  ⚠️ Series is non-stationary (fail to reject null hypothesis)")
    except Exception as e:
        print(f"  ⚠️ ADF test failed: {e}")
        results["adf_test"] = None

    # 7. Rolling statistics
    print("\n7. 📊 ROLLING STATISTICS (7-day window)")
    rolling_mean = daily_rides.rolling(window=7, center=True).mean()
    rolling_std = daily_rides.rolling(window=7, center=True).std()

    plt.figure(figsize=(14, 6))
    plt.plot(daily_rides.index, daily_rides.values, label="Daily Rides", alpha=0.5, color="steelblue")
    plt.plot(rolling_mean.index, rolling_mean.values, label="7-Day Rolling Mean", color="red", linewidth=2)
    plt.plot(rolling_std.index, rolling_std.values, label="7-Day Rolling Std", color="orange", linewidth=2)
    plt.title("Rolling Mean & Standard Deviation (7-Day Window)", fontsize=16, fontweight="bold")
    plt.xlabel("Date", fontsize=14)
    plt.ylabel("Rides", fontsize=14)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("eda_outputs/rolling_stats.png", dpi=300, bbox_inches="tight")
    plt.show()

    results["rolling_mean"] = rolling_mean
    results["rolling_std"] = rolling_std

    print("\n✅ Time series analysis completed successfully!")
    return results


def forecast_arima(df_clean: pd.DataFrame, periods: int = 30) -> Optional[Dict]:
    """Simple ARIMA forecasting (placeholder for future implementation)."""
    print("🔮 ARIMA Forecasting - Not yet implemented")
    return None
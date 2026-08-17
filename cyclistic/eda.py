"""Exploratory Data Analysis utilities for Cyclistic bike-share analysis."""

from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import seaborn as sns

matplotlib.use("Agg")

warnings.filterwarnings("ignore")

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams["figure.figsize"] = [12, 8]
plt.rcParams["font.size"] = 12
plt.rcParams["axes.titlesize"] = 16
plt.rcParams["axes.labelsize"] = 14

np.random.seed(42)


def perform_eda(df: pd.DataFrame, output_dir: str = "eda_outputs") -> pd.DataFrame:
    """Generate a basic exploratory data analysis summary and plots."""
    if df is None or df.empty:
        print("No data available for EDA.")
        return df

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if "start_time" in df.columns and "ride_duration" in df.columns:
        daily_rides = df.groupby(df["start_time"].dt.date).size()

        plt.figure(figsize=(16, 6))
        daily_rides.plot(kind="line", color="skyblue", linewidth=1.2)
        plt.title("Daily Bike Ride Counts Over Time")
        plt.xlabel("Date")
        plt.ylabel("Number of Rides")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path / "daily_rides_trend.png", dpi=300, bbox_inches="tight")
        plt.close()

    if "start_hour" in df.columns:
        hourly_rides = df.groupby("start_hour").size()
        plt.figure(figsize=(12, 6))
        hourly_rides.plot(kind="bar", color="coral", edgecolor="black")
        plt.title("Ride Distribution by Hour of Day")
        plt.xlabel("Hour of Day")
        plt.ylabel("Number of Rides")
        plt.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path / "hourly_distribution.png", dpi=300, bbox_inches="tight")
        plt.close()

    if "member_type" in df.columns:
        user_type_counts = df["member_type"].value_counts()
        plt.figure(figsize=(8, 8))
        user_type_counts.plot(kind="pie", autopct="%1.1f%%", startangle=90, shadow=True)
        plt.title("Distribution of User Types")
        plt.ylabel("")
        plt.tight_layout()
        plt.savefig(output_path / "user_type_distribution.png", dpi=300, bbox_inches="tight")
        plt.close()

    if "ride_duration" in df.columns:
        print("\nRide duration summary:")
        print(df["ride_duration"].describe())

    if "start_lat" in df.columns and "start_lng" in df.columns:
        sample = df.dropna(subset=["start_lat", "start_lng"]).sample(
            min(100000, len(df)), random_state=42
        )
        plt.figure(figsize=(12, 10))
        plt.scatter(sample["start_lng"], sample["start_lat"], alpha=0.1, s=1, c="blue")
        plt.title("Geographic Distribution of Ride Start Points")
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path / "geographic_distribution.png", dpi=300, bbox_inches="tight")
        plt.close()

    daily_rides = None
    if "start_time" in df.columns and "ride_duration" in df.columns:
        daily_rides = df.groupby(df["start_time"].dt.date).size()
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=daily_rides.index,
                y=daily_rides.values,
                mode="lines",
                name="Daily Rides",
                line=dict(color="royalblue", width=2),
            )
        )
        if len(daily_rides) >= 7:
            moving_average = daily_rides.rolling(window=7, center=True).mean()
            fig.add_trace(
                go.Scatter(
                    x=moving_average.index,
                    y=moving_average.values,
                    mode="lines",
                    name="7-day Moving Average",
                    line=dict(color="firebrick", width=2, dash="dash"),
                )
            )
        fig.update_layout(
            title="Interactive Daily Ride Counts",
            xaxis_title="Date",
            yaxis_title="Number of Rides",
            template="plotly_white",
            width=1000,
            height=500,
        )
        fig.write_html(output_path / "interactive_daily_rides.html")

    print(f"EDA plots and summary saved to: {output_path}")
    return df
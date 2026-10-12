"""Export real Cyclistic data into Power BI Star-Schema format."""

from __future__ import annotations

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cyclistic.cleaning import aggressive_cleaning, haversine_vectorized
from cyclistic.data_loader import load_cyclistic_data, find_data_path


def export_to_powerbi(input_data_path: str = None, output_dir: str = "powerbi/data") -> None:
    """Read Cyclistic raw dataset, clean it, build dimensions, and export Star-Schema CSVs."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    data_file = input_data_path or find_data_path()
    if not data_file or not os.path.exists(data_file):
        print(f"No raw input dataset found at {data_file}. Keeping generated mock dataset.")
        return

    print(f"Loading raw data from: {data_file}")
    df, _ = load_cyclistic_data(data_file)
    if df is None or df.empty:
        print("Raw data could not be loaded.")
        return

    print("Cleaning data...")
    cleaned = aggressive_cleaning(df)

    # 1. Dim_UserType
    dim_user = pd.DataFrame([
        {"user_type_key": 1, "user_type_name": "Member", "target_persona": "Daily Commuter", "strategic_goal": "Retention & Renewal"},
        {"user_type_key": 2, "user_type_name": "Casual", "target_persona": "Leisure & Weekend", "strategic_goal": "Membership Conversion"},
    ])
    dim_user.to_csv(out_path / "Dim_UserType.csv", index=False)

    # 2. Dim_BikeType
    bike_types = []
    if "rideable_type" in cleaned.columns:
        unique_bikes = cleaned["rideable_type"].dropna().unique()
        for idx, b in enumerate(unique_bikes, 1):
            bike_types.append({"bike_type_key": idx, "bike_type_name": str(b).replace("_", " ").title()})
    else:
        bike_types = [
            {"bike_type_key": 1, "bike_type_name": "Classic Bike"},
            {"bike_type_key": 2, "bike_type_name": "Electric Bike"},
            {"bike_type_key": 3, "bike_type_name": "Docked Bike"},
        ]
    dim_bike = pd.DataFrame(bike_types)
    dim_bike.to_csv(out_path / "Dim_BikeType.csv", index=False)

    # 3. Dim_RideCategory
    dim_cat = pd.DataFrame([
        {"category_key": 1, "category_name": "Short Trip (<15 min)", "min_minutes": 1, "max_minutes": 15},
        {"category_key": 2, "category_name": "Medium Trip (15-60 min)", "min_minutes": 15, "max_minutes": 60},
        {"category_key": 3, "category_name": "Long / Day Trip (>60 min)", "min_minutes": 60, "max_minutes": 1440},
    ])
    dim_cat.to_csv(out_path / "Dim_RideCategory.csv", index=False)

    # 4. Dim_Time
    times = []
    for h in range(24):
        time_key = f"{h:02d}:00"
        h12 = 12 if h == 0 else (h - 12 if h > 12 else h)
        ampm = "AM" if h < 12 else "PM"
        if 0 <= h < 6:
            bucket = "Early Morning (00:00 - 06:00)"
        elif 7 <= h <= 9:
            bucket = "Morning Rush (07:00 - 09:00)"
        elif 10 <= h <= 15:
            bucket = "Midday (10:00 - 15:00)"
        elif 16 <= h <= 19:
            bucket = "Evening Rush (16:00 - 19:00)"
        else:
            bucket = "Night (20:00 - 23:00)"
        is_peak = 1 if (7 <= h <= 9 or 16 <= h <= 19) else 0
        times.append({
            "time_key": time_key,
            "hour_24": h,
            "hour_12": h12,
            "am_pm": ampm,
            "hour_label": f"{h12} {ampm}",
            "time_bucket": bucket,
            "is_peak_rush_hour": is_peak
        })
    pd.DataFrame(times).to_csv(out_path / "Dim_Time.csv", index=False)

    # 5. Dim_Date
    min_date = cleaned["start_time"].min().date()
    max_date = cleaned["start_time"].max().date()
    date_range = pd.date_range(min_date, max_date, freq="D")
    dim_dates = []
    for dt in date_range:
        dim_dates.append({
            "date_key": dt.year * 10000 + dt.month * 100 + dt.day,
            "date": dt.strftime("%Y-%m-%d"),
            "year": dt.year,
            "quarter": f"Q{dt.quarter}",
            "month_number": dt.month,
            "month_name": dt.strftime("%B"),
            "month_short": dt.strftime("%b"),
            "month_year": dt.strftime("%b %Y"),
            "week_number": dt.isocalendar().week,
            "day_of_week_number": dt.dayofweek + 1,
            "day_of_week_name": dt.strftime("%A"),
            "day_short": dt.strftime("%a"),
            "is_weekend_flag": 1 if dt.dayofweek in [5, 6] else 0,
            "day_type": "Weekend" if dt.dayofweek in [5, 6] else "Weekday",
        })
    pd.DataFrame(dim_dates).to_csv(out_path / "Dim_Date.csv", index=False)

    # 6. Dim_Station
    stations = {}
    for prefix in ["start", "end"]:
        name_col = f"{prefix}_station_name"
        lat_col = f"{prefix}_lat"
        lng_col = f"{prefix}_lng"
        if name_col in cleaned.columns:
            subset = cleaned[[name_col, lat_col, lng_col]].dropna(subset=[name_col])
            for _, row in subset.iterrows():
                name = str(row[name_col]).strip()
                if name and name.lower() != "unknown" and name not in stations:
                    stations[name] = {"lat": row[lat_col], "lng": row[lng_col]}

    dim_stations = []
    station_id_map = {}
    for idx, (name, coords) in enumerate(stations.items(), 101):
        station_id_map[name] = idx
        dim_stations.append({
            "station_id": idx,
            "station_name": name,
            "latitude": coords["lat"],
            "longitude": coords["lng"],
            "community_area": "Chicago Metro",
            "station_tier": "Standard Hub"
        })
    pd.DataFrame(dim_stations).to_csv(out_path / "Dim_Station.csv", index=False)

    # 7. Fact_Rides
    fact = pd.DataFrame()
    fact["ride_id"] = cleaned["ride_id"].astype(str)
    fact["date_key"] = cleaned["start_time"].dt.year * 10000 + cleaned["start_time"].dt.month * 100 + cleaned["start_time"].dt.day
    fact["time_key"] = cleaned["start_time"].dt.strftime("%H:00")
    fact["user_type_key"] = cleaned["member_type"].map(lambda x: 1 if "member" in str(x).lower() else 2)

    # Bike type mapping
    if "rideable_type" in cleaned.columns:
        bike_map = {row["bike_type_name"].lower(): row["bike_type_key"] for _, row in dim_bike.iterrows()}
        fact["bike_type_key"] = cleaned["rideable_type"].map(lambda x: bike_map.get(str(x).replace("_", " ").lower(), 1))
    else:
        fact["bike_type_key"] = 1

    # Ride category
    fact["ride_category_key"] = pd.cut(
        cleaned["ride_duration"],
        bins=[-np.inf, 15, 60, np.inf],
        labels=[1, 2, 3]
    ).astype(int)

    fact["start_station_id"] = cleaned["start_station_name"].map(station_id_map).fillna(999).astype(int)
    fact["end_station_id"] = cleaned["end_station_name"].map(station_id_map).fillna(999).astype(int)
    fact["route_key"] = fact["start_station_id"].astype(str) + "-" + fact["end_station_id"].astype(str)
    fact["ride_duration_minutes"] = cleaned["ride_duration"].round(1)
    fact["distance_km"] = cleaned.get("distance_km", 0.0).round(2)
    fact["speed_kmh"] = cleaned.get("speed_kmh", 0.0).round(1)
    fact["is_round_trip"] = (fact["start_station_id"] == fact["end_station_id"]).astype(int)
    fact["cluster_id"] = 1

    fact.to_csv(out_path / "Fact_Rides.csv", index=False)
    print(f"Exported {len(fact):,} Fact_Rides and full Star-Schema to {out_path} successfully!")


if __name__ == "__main__":
    export_to_powerbi()

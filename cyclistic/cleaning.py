"""Data cleaning utilities for Cyclistic bike-share analysis."""

from __future__ import annotations

import struct
import warnings
from typing import Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


def parse_wkb_point(wkb_value) -> Tuple[float, float]:
    """Extract latitude and longitude from WKB or WKT point strings."""
    try:
        if wkb_value is None or pd.isna(wkb_value):
            return np.nan, np.nan

        if isinstance(wkb_value, str):
            value = wkb_value.strip()
            if value.upper().startswith("POINT"):
                try:
                    coords = value.replace(")", "(").split("(")[1].split()
                    longitude = float(coords[0])
                    latitude = float(coords[1])
                    return latitude, longitude
                except Exception:
                    return np.nan, np.nan
            try:
                wkb_value = bytes.fromhex(value.replace(" ", ""))
            except Exception:
                return np.nan, np.nan

        if not isinstance(wkb_value, (bytes, bytearray)):
            return np.nan, np.nan
        if len(wkb_value) < 21:
            return np.nan, np.nan

        byte_order = wkb_value[0]
        fmt = "<" if byte_order == 1 else ">"
        geometry_type = struct.unpack(fmt + "I", wkb_value[1:5])[0]
        if geometry_type != 1:
            return np.nan, np.nan

        longitude = struct.unpack(fmt + "d", wkb_value[5:13])[0]
        latitude = struct.unpack(fmt + "d", wkb_value[13:21])[0]
        return latitude, longitude
    except Exception:
        return np.nan, np.nan


def haversine_vectorized(lat1, lon1, lat2, lon2):
    """Vectorized Haversine distance in kilometers."""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    )
    return 6371 * 2 * np.arcsin(np.sqrt(a))


def ensure_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """Populate start/end latitude and longitude columns when available."""
    for side in ("start", "end"):
        lat_col = f"{side}_lat"
        lng_col = f"{side}_lng"

        if lat_col in df.columns and lng_col in df.columns:
            if df[lat_col].notna().sum() > 0:
                continue

        coord_col = f"{side}_coordinates"
        if coord_col in df.columns:
            parsed = df[coord_col].apply(parse_wkb_point)
            df[lat_col] = parsed.apply(lambda item: item[0])
            df[lng_col] = parsed.apply(lambda item: item[1])
        else:
            lat_candidates = [f"{side}_latitude", f"{side}_lat", f"{side}_station_lat"]
            lng_candidates = [f"{side}_longitude", f"{side}_lng", f"{side}_lon", f"{side}_station_lng"]

            for candidate in lat_candidates:
                if candidate in df.columns:
                    df[lat_col] = pd.to_numeric(df[candidate], errors="coerce")
                    break
            for candidate in lng_candidates:
                if candidate in df.columns:
                    df[lng_col] = pd.to_numeric(df[candidate], errors="coerce")
                    break

    return df


def add_safety_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure a consistent schema for downstream analysis."""
    if df is None or df.empty:
        return df

    if "ride_id" not in df.columns or df["ride_id"].isna().all():
        df["ride_id"] = np.arange(1, len(df) + 1)

    if "member_type" not in df.columns:
        for alternate in ("member_casual", "usertype", "user_type", "subscriber_type"):
            if alternate in df.columns:
                df["member_type"] = df[alternate]
                break
        else:
            df["member_type"] = "unknown"

    if "member_type" in df.columns:
        df["member_type"] = df["member_type"].astype(str).str.strip().str.lower()
        df.loc[df["member_type"].isin(["nan", "none", ""]), "member_type"] = "unknown"

    for side in ("start", "end"):
        name_col = f"{side}_station_name"
        lat_col = f"{side}_lat"
        lng_col = f"{side}_lng"
        if name_col not in df.columns:
            if lat_col in df.columns and lng_col in df.columns and df[[lat_col, lng_col]].notna().any(axis=1).any():
                df[name_col] = (
                    df[lat_col].round(4).astype(str)
                    + ","
                    + df[lng_col].round(4).astype(str)
                )
                df.loc[df[lat_col].isna() | df[lng_col].isna(), name_col] = "unknown"
            else:
                df[name_col] = "unknown"
        else:
            df[name_col] = df[name_col].fillna("unknown").astype(str)
            df.loc[df[name_col].isin(["nan", "None", ""]), name_col] = "unknown"

    return df


def aggressive_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names and clean invalid data rows."""
    if df is None or df.empty:
        print("No data available for cleaning.")
        return df

    cleaned = df.copy()

    if "started_at" in cleaned.columns and "start_time" not in cleaned.columns:
        cleaned["start_time"] = cleaned["started_at"]
    if "ended_at" in cleaned.columns and "end_time" not in cleaned.columns:
        cleaned["end_time"] = cleaned["ended_at"]
    if "member_casual" in cleaned.columns and "member_type" not in cleaned.columns:
        cleaned["member_type"] = cleaned["member_casual"]

    for column in ["start_time", "end_time"]:
        if column in cleaned.columns:
            cleaned[column] = pd.to_datetime(cleaned[column], errors="coerce")

    for column in cleaned.select_dtypes(include=[np.number]).columns:
        if cleaned[column].isna().sum() > 0:
            median_value = cleaned[column].median()
            if pd.notna(median_value):
                cleaned[column] = cleaned[column].fillna(median_value)

    for column in cleaned.select_dtypes(include=["object", "category"]).columns:
        if column in {"start_coordinates", "end_coordinates", "geometry"}:
            continue
        if cleaned[column].isna().sum() > 0:
            mode_value = cleaned[column].mode()
            if not mode_value.empty:
                cleaned[column] = cleaned[column].fillna(mode_value.iloc[0])

    cleaned = cleaned.drop_duplicates().reset_index(drop=True)

    if "start_time" in cleaned.columns and "end_time" in cleaned.columns:
        cleaned["ride_duration"] = (
            (cleaned["end_time"] - cleaned["start_time"]).dt.total_seconds() / 60
        )
    elif "ride_duration" in cleaned.columns:
        cleaned["ride_duration"] = pd.to_numeric(cleaned["ride_duration"], errors="coerce")

    if "ride_duration" in cleaned.columns:
        cleaned = cleaned[cleaned["ride_duration"].notna()].copy()
        cleaned = cleaned[(cleaned["ride_duration"] >= 1) & (cleaned["ride_duration"] <= 1440)].copy()

    cleaned = ensure_coordinates(cleaned)

    if "start_time" in cleaned.columns:
        cleaned["start_hour"] = cleaned["start_time"].dt.hour
        cleaned["start_day"] = cleaned["start_time"].dt.day
        cleaned["start_month"] = cleaned["start_time"].dt.month
        cleaned["start_year"] = cleaned["start_time"].dt.year
        cleaned["day_of_week"] = cleaned["start_time"].dt.dayofweek
        cleaned["is_weekend"] = cleaned["day_of_week"].isin([5, 6]).astype(int)
        cleaned["quarter"] = cleaned["start_time"].dt.quarter
        cleaned["week_of_year"] = cleaned["start_time"].dt.isocalendar().week.astype(int)

    if all(column in cleaned.columns for column in ["start_lat", "start_lng", "end_lat", "end_lng"]):
        cleaned["distance_km"] = np.nan
        valid_coords = (
            cleaned["start_lat"].notna()
            & cleaned["start_lng"].notna()
            & cleaned["end_lat"].notna()
            & cleaned["end_lng"].notna()
        )
        if valid_coords.any():
            coords = cleaned.loc[valid_coords]
            cleaned.loc[valid_coords, "distance_km"] = haversine_vectorized(
                coords["start_lat"].values,
                coords["start_lng"].values,
                coords["end_lat"].values,
                coords["end_lng"].values,
            )

    if "ride_duration" in cleaned.columns and "distance_km" in cleaned.columns:
        cleaned["speed_kmh"] = np.where(
            cleaned["ride_duration"] > 0,
            (cleaned["distance_km"] / cleaned["ride_duration"]) * 60,
            0,
        )
        cleaned["speed_kmh"] = cleaned["speed_kmh"].replace([np.inf, -np.inf], 0).fillna(0)

    if "ride_duration" in cleaned.columns:
        cleaned["ride_category"] = pd.cut(
            cleaned["ride_duration"],
            bins=[-np.inf, 15, 60, np.inf],
            labels=["short", "medium", "long"],
        )

    cleaned = add_safety_columns(cleaned)
    cleaned = cleaned.reset_index(drop=True)
    print(f"Dataset cleaned successfully: {len(cleaned):,} rows remain.")
    return cleaned
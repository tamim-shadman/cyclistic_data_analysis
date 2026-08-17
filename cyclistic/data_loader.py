"""Data loading utilities for Cyclistic bike-share analysis."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple

import geopandas as gpd
import pandas as pd


DEFAULT_DATA_PATTERNS = ("*.csv", "*.parquet")


def find_data_path(explicit_path: Optional[str] = None) -> Optional[str]:
    """Find a Cyclistic dataset in common local or Kaggle locations."""
    if explicit_path and os.path.exists(explicit_path):
        return explicit_path

    candidates = [
        explicit_path,
        os.environ.get("CYCLISTIC_DATA_PATH"),
        "/kaggle/input/cyclistic-202505-202605/cleaned_data.parquet",
        "/kaggle/input/datasets/mrdragonbishop/cyclistic-202505-202605/cleaned_data.parquet",
        "/kaggle/input/datasets/mrdragonbishop/cyclistic-202505-202605",
        "/kaggle/input/cyclistic-202505-202605",
        "cleaned_data.parquet",
        "data",
    ]

    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate

    search_roots = ["/kaggle/input", "/kaggle/working", ".", "data"]
    for root in search_roots:
        if not os.path.exists(root):
            continue
        for dirpath, _, files in os.walk(root):
            if "cyclistic" not in dirpath.lower():
                continue
            for file_name in sorted(files):
                lower_name = file_name.lower()
                if lower_name.endswith((".csv", ".parquet")):
                    if "cleaned" in lower_name or "cyclistic" in lower_name:
                        return os.path.join(dirpath, file_name)
                    return os.path.join(dirpath, file_name)

    for root in search_roots:
        if not os.path.exists(root):
            continue
        for dirpath, _, files in os.walk(root):
            for file_name in sorted(files):
                if file_name.lower().endswith((".csv", ".parquet")):
                    return os.path.join(dirpath, file_name)

    return None


def find_geojson_path(explicit_path: Optional[str] = None) -> Optional[str]:
    """Find a GeoJSON file if one is available."""
    if explicit_path and os.path.exists(explicit_path):
        return explicit_path

    candidates = [
        os.environ.get("CYCLISTIC_GEOJSON_PATH"),
        "Boundaries_-_Community_Areas_20260619.geojson",
        "data/Boundaries_-_Community_Areas_20260619.geojson",
        "./Boundaries_-_Community_Areas_20260619.geojson",
    ]
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate

    search_roots = ["/kaggle/input", "/kaggle/working", ".", "data"]
    for root in search_roots:
        if not os.path.exists(root):
            continue
        for dirpath, _, files in os.walk(root):
            for file_name in sorted(files):
                if file_name.lower().endswith(".geojson"):
                    return os.path.join(dirpath, file_name)
    return None


def load_one_file(file_path: str) -> pd.DataFrame:
    """Load a CSV or Parquet file into a pandas DataFrame."""
    lower_name = file_path.lower()
    if lower_name.endswith(".parquet"):
        return pd.read_parquet(file_path)
    if lower_name.endswith(".csv"):
        return pd.read_csv(file_path, low_memory=False)
    raise ValueError(f"Unsupported file type: {file_path}")


def load_cyclistic_data(
    data_path: Optional[str], geojson_path: Optional[str] = None
) -> Tuple[Optional[pd.DataFrame], Optional[gpd.GeoDataFrame]]:
    """Load the Cyclistic data and optional GeoJSON metadata."""
    if data_path is None:
        print("No dataset path was found. Provide --data-path or place the file in the project directory.")
        return None, None

    print(f"Loading dataset from: {data_path}")
    try:
        if os.path.isdir(data_path):
            collected_files = []
            for root, _, files in os.walk(data_path):
                for file_name in sorted(files):
                    if file_name.lower().endswith((".csv", ".parquet")):
                        collected_files.append(os.path.join(root, file_name))
            if not collected_files:
                raise FileNotFoundError(f"No CSV/Parquet files found in {data_path}")
            frames = [load_one_file(path) for path in collected_files]
            df = pd.concat(frames, ignore_index=True)
            print(f"Loaded {len(frames)} file(s); combined rows: {len(df):,}")
        else:
            df = load_one_file(data_path)
            print(f"Loaded file: {os.path.basename(data_path)} ({len(df):,} rows)")
    except Exception as exc:  # pragma: no cover - runtime guard for missing input
        print(f"Error loading the dataset: {exc}")
        return None, None

    geo_df = None
    if geojson_path and os.path.exists(geojson_path):
        try:
            geo_df = gpd.read_file(geojson_path)
            print(f"Loaded GeoJSON with {len(geo_df)} records")
        except Exception as exc:  # pragma: no cover - runtime guard
            print(f"Error loading GeoJSON: {exc}")
    else:
        print("No GeoJSON file found; spatial mapping will be skipped.")

    return df, geo_df
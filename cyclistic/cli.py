"""Command-line interface for Cyclistic bike-share analysis."""

from __future__ import annotations

import argparse

from .cleaning import aggressive_cleaning
from .data_loader import find_data_path, find_geojson_path, load_cyclistic_data
from .eda import perform_eda
from .segmentation import perform_user_segmentation
from .timeseries import perform_time_series_analysis


def parse_args() -> argparse.Namespace:
    """Parse command line options."""
    parser = argparse.ArgumentParser(
        description="Load, clean, and analyze Cyclistic bike-share data."
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default=None,
        help="Path to a CSV, Parquet file, or a directory containing those files.",
    )
    parser.add_argument(
        "--geojson-path",
        type=str,
        default=None,
        help="Optional path to a Chicago community-area GeoJSON file.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="eda_outputs",
        help="Directory to save plots and analysis outputs.",
    )
    return parser.parse_args()


def main() -> None:
    """Command-line entry point."""
    args = parse_args()
    output_dir = args.output_dir
    data_path = args.data_path or find_data_path()
    geojson_path = args.geojson_path or find_geojson_path()

    print("Cyclistic analysis pipeline")
    print(f"Data path: {data_path}")
    print(f"GeoJSON path: {geojson_path}")
    print(f"Output directory: {output_dir}")

    df, _ = load_cyclistic_data(data_path, geojson_path)
    if df is None:
        print("No dataset could be loaded. Exiting.")
        return

    cleaned_df = aggressive_cleaning(df)
    if cleaned_df is None or cleaned_df.empty:
        print("The dataset was empty after cleaning. Exiting.")
        return

    perform_eda(cleaned_df, output_dir=output_dir)

    segmentation_results = perform_user_segmentation(cleaned_df)
    if segmentation_results:
        print("Segmented rider behavior successfully.")

    timeseries_results = perform_time_series_analysis(cleaned_df)
    if timeseries_results:
        print("Time-series analysis completed successfully.")

    print("Analysis complete.")


if __name__ == "__main__":
    main()
# Cyclistic Data Analysis

This project loads, cleans, and analyzes Cyclistic bike-share trip data. It is organized as a GitHub-ready Python project for reproducible analysis and reporting.

## Project structure

- `Cyclistic.py` — main CLI pipeline for loading, cleaning, and running EDA
- `requirements.txt` — Python dependencies for the project
- `eda_outputs/` — generated charts and HTML reports

## Quick start

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux/macOS
   .\.venv\Scripts\activate    # Windows
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the analysis:
   ```bash
   python Cyclistic.py --data-path path/to/dataset.csv
   ```

Optional GeoJSON mapping:

```bash
python Cyclistic.py --data-path path/to/dataset.csv --geojson-path path/to/areas.geojson
```

## Notes

- The script will automatically search common local and Kaggle paths if no explicit path is supplied.
- Plot outputs are saved under `eda_outputs/`.
- The workflow is intentionally resilient to multiple Cyclistic schema variations.

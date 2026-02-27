# create_daily_summary_year_subset.py

import pandas as pd
from pathlib import Path


def create_daily_summary_year_subset(input_csv: Path, year: int, output_csv: Path) -> Path:
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_csv, parse_dates=["date"])
    df_year = df[df["date"].dt.year == year].copy()
    df_year.to_csv(output_csv, index=False)

    print(f"Saved {len(df_year)} rows to {output_csv}")
    return output_csv

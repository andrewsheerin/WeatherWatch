import pandas as pd
from pathlib import Path


def compute_monthly_climatology(
    input_csv: Path,
    baseline_start: int,
    baseline_end: int,
    output_mean_csv: Path,
    output_std_csv: Path,
    output_median_csv: Path,
) -> tuple[Path, Path, Path]:
    output_mean_csv.parent.mkdir(parents=True, exist_ok=True)
    output_std_csv.parent.mkdir(parents=True, exist_ok=True)
    output_median_csv.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_csv, parse_dates=["date"])

    df = df[
        (df["date"].dt.year >= baseline_start) &
        (df["date"].dt.year <= baseline_end)
    ].copy()

    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    monthly_yearly = (
        df.groupby(["year", "month"])["precip_mm"]
        .sum()
        .reset_index()
    )

    monthly_mean = (
        monthly_yearly.groupby("month")["precip_mm"]
        .mean()
        .reset_index()
        .rename(columns={"precip_mm": "monthly_mean_mm"})
    )

    monthly_std = (
        monthly_yearly.groupby("month")["precip_mm"]
        .std()
        .reset_index()
        .rename(columns={"precip_mm": "monthly_std_mm"})
    )

    monthly_median = (
        monthly_yearly.groupby("month")["precip_mm"]
        .median()
        .reset_index()
        .rename(columns={"precip_mm": "monthly_median_mm"})
    )

    monthly_mean.to_csv(output_mean_csv, index=False)
    monthly_std.to_csv(output_std_csv, index=False)
    monthly_median.to_csv(output_median_csv, index=False)

    print("Saved:")
    print("  ", output_mean_csv)
    print("  ", output_std_csv)
    print("  ", output_median_csv)

    return output_mean_csv, output_std_csv, output_median_csv


import pandas as pd
from pathlib import Path


def compute_daily_climatology(
    input_csv: Path,
    baseline_start: int,
    baseline_end: int,
    output_mean_csv: Path,
    output_std_csv: Path,
    output_median_csv: Path,
    roll_windows: list[int],
) -> tuple[Path, Path, Path]:
    output_mean_csv.parent.mkdir(parents=True, exist_ok=True)
    output_std_csv.parent.mkdir(parents=True, exist_ok=True)
    output_median_csv.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_csv, parse_dates=["date"])

    df = df[
        (df["date"].dt.year >= baseline_start) &
        (df["date"].dt.year <= baseline_end)
    ].copy()

    df = df[~((df["date"].dt.month == 2) & (df["date"].dt.day == 29))]
    df["doy"] = df["date"].dt.dayofyear

    variables = [
        "tmax_C",
        "tmin_C",
        "precip_mm",
        "rh_max_pct",
        "rh_min_pct",
        "solar_MJ_m2",
    ]

    clim_mean = df.groupby("doy")[variables].mean().reset_index()
    clim_median = df.groupby("doy")[variables].median().reset_index()
    clim_std = df.groupby("doy")[variables].std().reset_index()

    for window in roll_windows:
        for var in variables:
            clim_mean[f"{var}_{window}d_mean"] = (
                clim_mean[var]
                .rolling(window, center=True, min_periods=1)
                .mean()
            )

            clim_median[f"{var}_{window}d_median"] = (
                clim_median[var]
                .rolling(window, center=True, min_periods=1)
                .mean()
            )

            clim_std[f"{var}_{window}d_std"] = (
                clim_std[var]
                .rolling(window, center=True, min_periods=1)
                .mean()
            )

    clim_mean.to_csv(output_mean_csv, index=False)
    clim_median.to_csv(output_median_csv, index=False)
    clim_std.to_csv(output_std_csv, index=False)

    print(f"Saved mean climatology to: {output_mean_csv}")
    print(f"Saved median climatology to: {output_median_csv}")
    print(f"Saved std climatology to: {output_std_csv}")

    return output_mean_csv, output_std_csv, output_median_csv

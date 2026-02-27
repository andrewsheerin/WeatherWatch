# compute_daily_metrics.py
#
# Compute daily weather metrics (including 7-day / 30-day rolling metrics) and
# attach climatology-based baselines by day-of-year.
#
# Assumes input daily CSV columns:
#   date, tmax_C, tmin_C, precip_mm, rh_max_pct, rh_min_pct, solar_MJ_m2
#
# Assumes climatology mean CSV produced by compute_daily_climatology.py contains:
#   doy, precip_mm, (and other vars; only precip_mm is required here)

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def _drop_feb29(df: pd.DataFrame) -> pd.DataFrame:
    dt = df["date"]
    return df[~((dt.dt.month == 2) & (dt.dt.day == 29))].copy()


def _circular_trailing_sum(values_365: np.ndarray, window: int) -> np.ndarray:
    """
    Circular trailing sum over 365-length array:
      out[i] = sum(values[i-window+1 : i+1]) with wrap-around.
    """
    if values_365.shape[0] != 365:
        raise ValueError(f"Expected 365 values, got {values_365.shape[0]}")

    v = values_365.astype(float)
    w = int(window)
    if w <= 0:
        raise ValueError("window must be >= 1")

    out = np.empty(365, dtype=float)
    # For each doy index i, sum last w days with wrap
    for i in range(365):
        idx = (np.arange(i - w + 1, i + 1) % 365)
        out[i] = v[idx].sum()
    return out


def _compute_dry_streak(dry_flag: pd.Series) -> pd.Series:
    """
    Consecutive dry days ending on each day. Wet days get 0.
    """
    # streak within runs of True; reset when False
    run_id = (~dry_flag).cumsum()
    streak = dry_flag.groupby(run_id).cumcount() + 1
    streak = streak.where(dry_flag, 0)
    return streak.astype(int)


def compute_daily_metrics(
    input_csv: Path,
    clim_mean_csv: Path,
    output_csv: Path,
    dry_threshold_mm: float = 1.0,
    heat_threshold_C: float = 35.0,
    windows: tuple[int, ...] = (7, 30),
) -> Path:
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_csv, parse_dates=["date"])
    df = _drop_feb29(df)
    df = df.sort_values("date").reset_index(drop=True)
    df["doy"] = df["date"].dt.dayofyear

    required = {"tmax_C", "tmin_C", "precip_mm"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Input CSV missing columns: {sorted(missing)}")

    # Rolling precip totals (trailing windows)
    for w in windows:
        df[f"p{w}_mm"] = df["precip_mm"].rolling(window=w, min_periods=1).sum()

    # Dry days + streaks
    df["dry_day"] = df["precip_mm"] < dry_threshold_mm
    df["dry_streak_days"] = _compute_dry_streak(df["dry_day"])

    # Rolling max dry streak within last 30 days (useful for stage summaries)
    df["cdd_30_max"] = df["dry_streak_days"].rolling(window=30, min_periods=1).max()

    # Heat stress
    df["heat_day_35C"] = df["tmax_C"] > heat_threshold_C
    df["heat_7_count"] = df["heat_day_35C"].rolling(window=7, min_periods=1).sum().astype(int)
    df["heat_30_count"] = df["heat_day_35C"].rolling(window=30, min_periods=1).sum().astype(int)

    # --- Climatology baselines (by DOY) ---
    clim = pd.read_csv(clim_mean_csv)
    if "doy" not in clim.columns or "precip_mm" not in clim.columns:
        raise ValueError("Climatology mean CSV must include columns: doy, precip_mm")

    clim = clim.copy()
    clim = clim[~clim["doy"].isna()]
    clim["doy"] = clim["doy"].astype(int)

    # Ensure we have a full 1..365 set; if not, fill by reindex + interpolate
    clim = clim.sort_values("doy").set_index("doy")
    clim = clim.reindex(range(1, 366))

    # Interpolate precip mean if there are gaps
    clim["precip_mm"] = clim["precip_mm"].astype(float).interpolate(limit_direction="both")
    precip_mean_365 = clim["precip_mm"].to_numpy()

    # Trailing-window climatology totals ending on each DOY
    clim_p7 = _circular_trailing_sum(precip_mean_365, 7)
    clim_p30 = _circular_trailing_sum(precip_mean_365, 30)

    clim_out = pd.DataFrame(
        {
            "doy": np.arange(1, 366, dtype=int),
            "precip_clim_daily_mean_mm": precip_mean_365,
            "p7_clim_mm": clim_p7,
            "p30_clim_mm": clim_p30,
        }
    )

    df = df.merge(clim_out, on="doy", how="left")

    # Percent of normal + anomaly (30d and 7d)
    eps = 1e-9
    df["p30_pct_of_normal"] = (df["p30_mm"] / (df["p30_clim_mm"] + eps)) * 100.0
    df["p30_anom_pct"] = (df["p30_mm"] - df["p30_clim_mm"]) / (df["p30_clim_mm"] + eps)

    df["p7_pct_of_normal"] = (df["p7_mm"] / (df["p7_clim_mm"] + eps)) * 100.0
    df["p7_anom_pct"] = (df["p7_mm"] - df["p7_clim_mm"]) / (df["p7_clim_mm"] + eps)

    df.to_csv(output_csv, index=False)
    print(f"Saved daily metrics to: {output_csv}")
    return output_csv


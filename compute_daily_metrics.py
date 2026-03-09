# compute_daily_metrics.py
#
# Compute daily weather metrics (including 7-day / 30-day rolling metrics) and
# attach climatology-based baselines by day-of-year.
#
# Assumes input daily CSV columns:
#   date, tmax_C, tmin_C, precip_mm, rh_max_pct, rh_min_pct, solar_MJ_m2
#
# Assumes baseline CSV contains daily precip for multiple years:
#   date, precip_mm

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
    baseline_csv: Path,
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
    original_cols = list(df.columns)

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
    baseline = pd.read_csv(baseline_csv, parse_dates=["date"])
    baseline = _drop_feb29(baseline)
    baseline = baseline.sort_values("date").reset_index(drop=True)

    if "precip_mm" not in baseline.columns:
        raise ValueError("Baseline CSV missing column: precip_mm")

    baseline["year"] = baseline["date"].dt.year
    baseline["doy"] = baseline["date"].dt.dayofyear

    # Rolling precip totals per year, then climatology median by DOY
    for w in windows:
        roll = (
            baseline.groupby("year")["precip_mm"]
            .rolling(window=w, min_periods=1)
            .sum()
            .reset_index(level=0, drop=True)
        )
        baseline[f"p{w}_mm"] = roll

    doy_index = pd.Index(range(1, 366), name="doy")
    precip_daily_med = (
        baseline.groupby("doy")["precip_mm"].median().reindex(doy_index)
    )
    precip_daily_med = precip_daily_med.astype(float).interpolate(limit_direction="both")

    clim_out = pd.DataFrame({
        "doy": np.arange(1, 366, dtype=int),
        "precip_clim_daily_median_mm": precip_daily_med.to_numpy(),
    })

    for w in windows:
        clim_roll = baseline.groupby("doy")[f"p{w}_mm"].median().reindex(doy_index)
        clim_roll = clim_roll.astype(float).interpolate(limit_direction="both")
        if np.nanmin(clim_roll.to_numpy()) < 5.0:
            print(f"Warning: p{w}_clim_mm has very low values (<5 mm). Check baseline data.")
        clim_out[f"p{w}_clim_mm"] = clim_roll.to_numpy()

    df = df.merge(clim_out, on="doy", how="left")

    # Percent of normal + anomaly (30d and 7d)
    eps = 1e-6
    df["p30_pct_of_normal"] = (df["p30_mm"] / (df["p30_clim_mm"] + eps)) * 100.0
    df["p30_anom_pct"] = (df["p30_mm"] - df["p30_clim_mm"]) / (df["p30_clim_mm"] + eps)

    df["p7_pct_of_normal"] = (df["p7_mm"] / (df["p7_clim_mm"] + eps)) * 100.0
    df["p7_anom_pct"] = (df["p7_mm"] - df["p7_clim_mm"]) / (df["p7_clim_mm"] + eps)

    df = df.rename(columns={
        "dry_streak_days": "dry_streak",
        "p30_anom_pct": "p30_anomaly_pct",
    })

    keep_cols = (
        original_cols +
        [
            "p7_mm",
            "p30_mm",
            "dry_day",
            "dry_streak",
            "heat_day_35C",
            "p30_pct_of_normal",
            "p30_anomaly_pct",
        ]
    )
    seen = set()
    keep_cols = [c for c in keep_cols if not (c in seen or seen.add(c))]
    df = df[keep_cols]

    df.to_csv(output_csv, index=False)
    print(f"Saved daily metrics to: {output_csv}")
    return output_csv


# compute_stage_cyi.py
#
# Outputs:
#   1) stage_metric_summary_YYYY.csv
#   2) stage_scores_cyi_YYYY.csv

from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np


# ---------------- STAGE DEFINITIONS ----------------
STAGES = {
    "preparation": {"start": "03-15", "end": "05-15", "stage_weight": 0.15},
    "planting": {"start": "05-16", "end": "06-30", "stage_weight": 0.25},
    "vegetative": {"start": "07-01", "end": "09-15", "stage_weight": 0.45},
    "harvest": {"start": "09-16", "end": "11-15", "stage_weight": 0.15},
}

# 4 Core Metrics Used Across All Stages
METRICS = [
    "p30_anom_pct",
    "cdd_max",
    "heat_stress_count",
    "p7_mm",
]

# Metric weights by stage
METRIC_WEIGHTS = {
    "preparation": {"p30_anom_pct": 0.45, "cdd_max": 0.55, "heat_stress_count": 0.0, "p7_mm": 0.0},
    "planting": {"p30_anom_pct": 0.35, "cdd_max": 0.65, "heat_stress_count": 0.0, "p7_mm": 0.0},
    "vegetative": {"p30_anom_pct": 0.35, "cdd_max": 0.15, "heat_stress_count": 0.50, "p7_mm": 0.0},
    "harvest": {"p30_anom_pct": 0.0, "cdd_max": 0.0, "heat_stress_count": 0.25, "p7_mm": 0.75},
}


# ---------------- UTILITY FUNCTIONS ----------------

def _clamp_score(x: float) -> float:
    return float(min(100.0, max(0.0, x)))


def interp(x, x0, x1, y0, y1):
    if x1 == x0:
        return y0
    return y0 + (x - x0) * (y1 - y0) / (x1 - x0)


# ---------------- THRESHOLD DERIVATION ----------------

def derive_thresholds_from_climatology(df):
    """
    Derive metric thresholds from dataset percentiles.
    This allows the model to adapt to any region automatically.
    """

    thresholds = {}

    if "p7_mm" in df.columns:
        r7 = df["p7_mm"].dropna()
        thresholds["p7"] = {
            "p25": np.percentile(r7, 25),
            "p50": np.percentile(r7, 50),
            "p75": np.percentile(r7, 75),
            "p90": np.percentile(r7, 90),
        }

    if "dry_streak" in df.columns:
        cdd = df["dry_streak"].dropna()
        thresholds["cdd"] = {
            "p50": np.percentile(cdd, 50),
            "p75": np.percentile(cdd, 75),
            "p90": np.percentile(cdd, 90),
        }

    if "heat_day_35C" in df.columns:
        heat = df["heat_day_35C"].astype(int).dropna()
        thresholds["heat"] = {
            "p50": np.percentile(heat, 50),
            "p75": np.percentile(heat, 75),
            "p90": np.percentile(heat, 90),
        }

    return thresholds


# ---------------- SCORING FUNCTIONS ----------------

def score_p30_anom(x):
    """
    Rainfall anomaly relative to climatology.
    These bands remain fixed because anomaly is already normalized.
    """

    if x > 0.40:
        return _clamp_score(interp(x, 0.40, 0.80, 80, 50))

    if 0.0 <= x <= 0.40:
        return _clamp_score(interp(x, 0.0, 0.40, 100, 80))

    if -0.10 <= x < 0.0:
        return _clamp_score(interp(x, -0.10, 0.0, 90, 100))

    if -0.25 <= x < -0.10:
        return _clamp_score(interp(x, -0.25, -0.10, 70, 90))

    if -0.40 <= x < -0.25:
        return _clamp_score(interp(x, -0.40, -0.25, 40, 70))

    return _clamp_score(interp(x, -0.80, -0.40, 0, 40))


def score_cdd(x, thresholds):

    p50 = thresholds["cdd"]["p50"]
    p75 = thresholds["cdd"]["p75"]
    p90 = thresholds["cdd"]["p90"]

    if x <= p50:
        return _clamp_score(interp(x, 0, p50, 100, 90))

    elif x <= p75:
        return _clamp_score(interp(x, p50, p75, 90, 60))

    elif x <= p90:
        return _clamp_score(interp(x, p75, p90, 60, 30))

    else:
        return _clamp_score(interp(x, p90, p90 * 1.5, 30, 0))


def score_heat(x, thresholds):

    p50 = thresholds["heat"]["p50"]
    p75 = thresholds["heat"]["p75"]
    p90 = thresholds["heat"]["p90"]

    if x <= p50:
        return _clamp_score(interp(x, 0, p50, 100, 90))

    elif x <= p75:
        return _clamp_score(interp(x, p50, p75, 90, 60))

    elif x <= p90:
        return _clamp_score(interp(x, p75, p90, 60, 30))

    else:
        return _clamp_score(interp(x, p90, p90 * 1.5, 30, 0))


def score_p7(x, thresholds):

    p25 = thresholds["p7"]["p25"]
    p50 = thresholds["p7"]["p50"]
    p75 = thresholds["p7"]["p75"]
    p90 = thresholds["p7"]["p90"]

    if x <= p25:
        return _clamp_score(interp(x, 0, p25, 100, 90))

    elif x <= p50:
        return _clamp_score(interp(x, p25, p50, 90, 80))

    elif x <= p75:
        return _clamp_score(interp(x, p50, p75, 80, 50))

    else:
        return _clamp_score(interp(x, p75, p90, 50, 0))


# ---------------- MAIN CYI FUNCTION ----------------

def compute_stage_cyi(
    metrics_csv: Path,
    stage_metric_summary_csv: Path,
    stage_scores_cyi_csv: Path,
):

    df = pd.read_csv(metrics_csv, parse_dates=["date"])

    if "p30_anom_pct" not in df.columns and "p30_anomaly_pct" in df.columns:
        df["p30_anom_pct"] = df["p30_anomaly_pct"]

    year = df["date"].dt.year.iloc[0]

    thresholds = derive_thresholds_from_climatology(df)

    metric_rows = []
    stage_rows = []

    for stage, cfg in STAGES.items():

        start = pd.to_datetime(f"{year}-{cfg['start']}")
        end = pd.to_datetime(f"{year}-{cfg['end']}")

        stage_df = df[(df["date"] >= start) & (df["date"] <= end)]

        if stage_df.empty:
            continue

        stage_range_str = f"{start.date()} to {end.date()}"

        stage_weight = cfg["stage_weight"]
        weights = METRIC_WEIGHTS[stage]

        stage_score_weighted_sum = 0

        row = {
            "stage": stage,
            "stage_date_range": stage_range_str,
        }

        for metric in METRICS:

            if metric == "cdd_max":
                series = stage_df["dry_streak"].fillna(0)
                summary_val = series.max()
                score = score_cdd(summary_val, thresholds)
                row["cdd_max"] = summary_val

            elif metric == "heat_stress_count":
                heat_series = stage_df["heat_day_35C"].fillna(0)
                summary_val = int(heat_series.sum())
                score = score_heat(summary_val, thresholds)
                row["heat_stress_count"] = summary_val

            else:
                series = stage_df[metric].fillna(0)

                if metric == "p30_anom_pct":
                    summary_val = series.mean()
                    score = score_p30_anom(summary_val)
                    row["p30_anom_pct_mean"] = summary_val

                elif metric == "p7_mm":
                    summary_val = series.mean()
                    score = score_p7(summary_val, thresholds)
                    row["R7_mean"] = summary_val

                else:
                    score = 0

            weight = weights.get(metric, 0)
            weighted_score = score * weight

            stage_score_weighted_sum += weighted_score

            row[f"{metric}_score_0_100"] = score
            row[f"{metric}_weight"] = weight

        row["stage_score_0_100"] = float(min(100.0, max(0.0, stage_score_weighted_sum)))

        metric_rows.append(row)

        stage_rows.append({
            "stage": stage,
            "stage_date_range": stage_range_str,
            "stage_weight": stage_weight,
            "stage_score_0_100": float(min(100.0, max(0.0, stage_score_weighted_sum))),
            "weighted_stage_score": stage_score_weighted_sum * stage_weight,
        })

    stage_metric_df = pd.DataFrame(metric_rows).fillna(0)
    stage_scores_df = pd.DataFrame(stage_rows).fillna(0)

    final_cyi = stage_scores_df["weighted_stage_score"].sum()
    stage_scores_df["CYI"] = final_cyi

    stage_metric_df.to_csv(stage_metric_summary_csv, index=False)
    stage_scores_df.to_csv(stage_scores_cyi_csv, index=False)

    print(f"CYI = {final_cyi:.2f}")
    print(f"Saved: {stage_metric_summary_csv}")
    print(f"Saved: {stage_scores_cyi_csv}")

    return final_cyi
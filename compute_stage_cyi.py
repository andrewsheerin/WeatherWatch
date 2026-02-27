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
    "preparation": {"start": "03-01", "end": "04-30", "stage_weight": 0.20},
    "planting": {"start": "05-01", "end": "05-31", "stage_weight": 0.20},
    "vegetative": {"start": "06-01", "end": "08-31", "stage_weight": 0.40},
    "harvest": {"start": "09-01", "end": "10-31", "stage_weight": 0.20},
}

# 4 Core Metrics Used Across All Stages
METRICS = [
    "p30_anom_pct",
    "cdd_30_max",
    "heat_30_count",
    "p7_mm",
]

# Metric weights by stage
METRIC_WEIGHTS = {
    "preparation": {"p30_anom_pct": 0.4, "cdd_30_max": 0.6, "heat_30_count": 0.0, "p7_mm": 0.0},
    "planting": {"p30_anom_pct": 0.5, "cdd_30_max": 0.5, "heat_30_count": 0.0, "p7_mm": 0.0},
    "vegetative": {"p30_anom_pct": 0.4, "cdd_30_max": 0.2, "heat_30_count": 0.4, "p7_mm": 0.0},
    "harvest": {"p30_anom_pct": 0.0, "cdd_30_max": 0.0, "heat_30_count": 0.4, "p7_mm": 0.6},
}


# ---------------- SCORING (0–100 SCALE) ----------------
def score_p30_anom(x):
    if x >= 0:
        return 100
    elif x >= -0.2:
        return 80
    elif x >= -0.5:
        return 50
    else:
        return 20


def score_cdd(x):
    if x <= 7:
        return 100
    elif x <= 14:
        return 70
    elif x <= 21:
        return 40
    else:
        return 20


def score_heat(x):
    if x <= 3:
        return 100
    elif x <= 7:
        return 70
    elif x <= 14:
        return 40
    else:
        return 20


def score_p7(x):
    if x <= 10:
        return 100
    elif x <= 30:
        return 70
    elif x <= 60:
        return 40
    else:
        return 20


def compute_stage_cyi(
    metrics_csv: Path,
    stage_metric_summary_csv: Path,
    stage_scores_cyi_csv: Path,
):

    df = pd.read_csv(metrics_csv, parse_dates=["date"])
    year = df["date"].dt.year.iloc[0]

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

            series = stage_df[metric].fillna(0)

            mean_val = series.mean()
            median_val = series.median()
            std_val = series.std()

            # scoring
            if metric == "p30_anom_pct":
                score = score_p30_anom(mean_val)
            elif metric == "cdd_30_max":
                score = score_cdd(mean_val)
            elif metric == "heat_30_count":
                score = score_heat(mean_val)
            elif metric == "p7_mm":
                score = score_p7(mean_val)
            else:
                score = 0

            weight = weights.get(metric, 0)
            weighted_score = score * weight

            stage_score_weighted_sum += weighted_score

            # Add to row
            row[f"{metric}_mean"] = mean_val
            row[f"{metric}_median"] = median_val
            row[f"{metric}_std"] = std_val
            row[f"{metric}_score_0_100"] = score
            row[f"{metric}_weight"] = weight

        row["stage_score_0_100"] = stage_score_weighted_sum

        metric_rows.append(row)

        stage_rows.append({
            "stage": stage,
            "stage_date_range": stage_range_str,
            "stage_weight": stage_weight,
            "stage_score_0_100": stage_score_weighted_sum,
            "weighted_stage_score": stage_score_weighted_sum * stage_weight,
        })

    # ---------- Convert to DataFrames ----------
    stage_metric_df = pd.DataFrame(metric_rows).fillna(0)
    stage_scores_df = pd.DataFrame(stage_rows).fillna(0)

    # ---------- Final CYI ----------
    final_cyi = stage_scores_df["weighted_stage_score"].sum()
    stage_scores_df["CYI"] = final_cyi

    # ---------- Reorder stage_metric_summary columns ----------
    if not stage_metric_df.empty:

        # 1) Stage info
        stage_cols = ["stage", "stage_date_range"]

        # 2) Metric statistics (grouped by metric)
        stat_cols = []
        for metric in METRICS:
            stat_cols.extend([
                f"{metric}_mean",
                f"{metric}_median",
                f"{metric}_std",
            ])

        # 3) Metric weights
        weight_cols = [f"{metric}_weight" for metric in METRICS]

        # 4) Metric scores
        score_cols = [f"{metric}_score_0_100" for metric in METRICS]

        # 5) Final stage score
        stage_score_cols = ["stage_score_0_100"]

        ordered_cols = (
            stage_cols +
            stat_cols +
            score_cols +
            weight_cols +
            stage_score_cols
        )

        # Keep only existing columns (in case of future changes)
        ordered_cols = [c for c in ordered_cols if c in stage_metric_df.columns]

        stage_metric_df = stage_metric_df[ordered_cols]

    # ---------- Save ----------
    stage_metric_df.fillna(0).to_csv(stage_metric_summary_csv, index=False)
    stage_scores_df.fillna(0).to_csv(stage_scores_cyi_csv, index=False)

    print(f"CYI = {final_cyi:.2f}")
    print(f"Saved: {stage_metric_summary_csv}")
    print(f"Saved: {stage_scores_cyi_csv}")

    return final_cyi
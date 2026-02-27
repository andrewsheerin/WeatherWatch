# WeatherWatch

Lightweight scripts for downloading and summarizing Open-Meteo archive data for a point location.

## What is in this repo
- Download, summaries, and plots for local CYI prototyping.
- Simple, readable Python scripts (no CLI, no framework).

## Pipeline overview
The pipeline is a simple, linear flow that turns Open-Meteo archive data into clean time series and summary products:
1. **Download**: fetch daily time series for the target lat/lon from the Open-Meteo archive.
2. **Climatology**: compute daily and monthly baseline statistics for a chosen baseline period.
3. **Metrics**: compute rolling totals, dry streaks, heat counts, and baseline anomalies for a target year.
4. **CYI scoring**: aggregate weather metrics into stage scores and a final Crop Yield Index.
5. **Plots**: create temperature and rainfall comparison visuals for quick reporting.

## What we calculate
The workflow focuses on weather variables needed for a Crop Yield Index (CYI) prototype. At minimum, the pipeline produces:
- **Temperature**: daily max/min (°C) to characterize heat stress and growing conditions.
- **Rainfall**: daily totals and rolling 7/30-day sums (mm) to track moisture availability.
- **Relative humidity**: daily max/min (%) as a proxy for atmospheric moisture stress.
- **Solar radiation**: daily sums (MJ/m²) to capture energy input for crop growth.

## CYI metrics, stages, and scoring
The CYI prototype summarizes daily weather into stage-based stress metrics and combines them into a single score for the season.

### Core metrics (daily and rolling)
These are computed for the target year in `compute_daily_metrics.py`:
- **`p30_anom_pct`**: 30-day precipitation anomaly vs climatology. It is computed as `(p30_mm - p30_clim_mm) / p30_clim_mm`.
- **`cdd_30_max`**: maximum consecutive dry days within the last 30 days. A dry day is `precip_mm < 1.0`.
- **`heat_30_count`**: number of days in the past 30 days where `tmax_C > 35°C`.
- **`p7_mm`**: 7-day precipitation total (trailing sum).

### Crop stages and stage weights
Stages are defined in `compute_stage_cyi.py`:
- **Preparation**: Mar 1 – Apr 30 (weight 0.20)
- **Planting**: May 1 – May 31 (weight 0.20)
- **Vegetative**: Jun 1 – Aug 31 (weight 0.40)
- **Harvest**: Sep 1 – Oct 31 (weight 0.20)

### Metric weights by stage
Each stage uses a weighted combination of the four metrics:

| Stage | `p30_anom_pct` | `cdd_30_max` | `heat_30_count` | `p7_mm` |
| --- | --- | --- | --- | --- |
| Preparation | 0.40 | 0.60 | 0.00 | 0.00 |
| Planting | 0.50 | 0.50 | 0.00 | 0.00 |
| Vegetative | 0.40 | 0.20 | 0.40 | 0.00 |
| Harvest | 0.00 | 0.00 | 0.40 | 0.60 |

### Metric scoring (0–100)
For each stage, each metric is scored on a 0–100 scale using simple bins:
- **`p30_anom_pct`**: higher (less negative) anomalies score better.
- **`cdd_30_max`**: shorter dry streaks score better.
- **`heat_30_count`**: fewer hot days score better.
- **`p7_mm`**: lower 7-day totals score better (used for harvest conditions).

Stage score = sum(metric_score × metric_weight)

### Final CYI
Final CYI is the weighted sum of stage scores:

`CYI = Σ (stage_score × stage_weight)`

## Outputs
All outputs go under `outputs/<subdir>/` and are split into `csv/` and `plot/` subfolders.

**CSV outputs**
- `all_daily_weather.csv`: full daily Open-Meteo time series.
- `daily_climatology_mean.csv`, `daily_climatology_median.csv`, `daily_climatology_std.csv`
- `monthly_climatology_mean.csv`, `monthly_climatology_median.csv`, `monthly_climatology_std.csv`
- `daily_weather_<year>.csv`: target-year subset.
- `daily_metrics_<year>.csv`: target-year derived metrics and anomalies.
- `stage_metric_summary_<year>.csv`: per-stage metric stats and scores.
- `stage_scores_cyi_<year>.csv`: per-stage weights and final CYI.

**Plot outputs**
- `rain_<year>_daily_rolling.png`: daily rain + 7/30-day rolling totals.
- `temperature_<year>_vs_baseline.png`: target-year temp vs baseline range.
- `rain_<year>_monthly_ci.png`: monthly rainfall vs baseline mean ± 95% CI.

## Quick start
1. Create and activate a Python environment.
2. Install dependencies.
3. Run the pipeline.

```powershell
pip install -r requirements.txt
python run_pipeline.py
```

## Notes
- Default location and years are configured in `run_pipeline.py`.
- Data is sourced from the Open-Meteo archive API.

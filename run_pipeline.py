from pathlib import Path

from compute_daily_climatology import compute_daily_climatology
from compute_daily_metrics import compute_daily_metrics
from compute_monthly_climatology import compute_monthly_climatology
from create_daily_summary_year_subset import create_daily_summary_year_subset
from custom_rain_plot import plot_custom_rain
from download_openmeteo import download_openmeteo
from plot_year_monthly_rain_ci import plot_monthly_rain_ci
from plot_year_vs_climatology import plot_year_vs_climatology
from compute_stage_cyi import compute_stage_cyi

def run() -> None:
    # ---------------- CONFIG ----------------
    lat = 9.407
    lon = -0.853
    timezone = "Africa/Accra"

    baseline_start = 1995
    baseline_end = 2025
    target_year = 2025

    download_data = True
    start_date = "1995-01-01"
    end_date = "2025-12-31"

    output_subdir = "tamale_ghana"
    base_dir = Path("outputs") / output_subdir
    csv_dir = base_dir / "csv"
    plot_dir = base_dir / "plot"

    # ---------------- PIPELINE ----------------
    print("Pipeline starting...")
    print(f"Config: lat/lon={lat}, {lon}")
    print(f"Config: baseline={baseline_start}-{baseline_end}, target_year={target_year}")
    print(f"Config: outputs csv={csv_dir}, plot={plot_dir}")

    all_daily_csv = csv_dir / "all_daily_weather.csv"
    if download_data:
        print("Step 1: downloading Open-Meteo archive data...")
        download_openmeteo(
            lat=lat,
            lon=lon,
            start_date=start_date,
            end_date=end_date,
            output_csv=all_daily_csv,
            timezone=timezone,
        )
    else:
        print("Step 1: skipping download (download_data=False)")

    print("Step 2: computing daily climatology...")
    daily_mean_csv = csv_dir / "daily_climatology_mean.csv"
    daily_std_csv = csv_dir / "daily_climatology_std.csv"
    daily_median_csv = csv_dir / "daily_climatology_median.csv"
    compute_daily_climatology(
        input_csv=all_daily_csv,
        baseline_start=baseline_start,
        baseline_end=baseline_end,
        output_mean_csv=daily_mean_csv,
        output_std_csv=daily_std_csv,
        output_median_csv=daily_median_csv,
        roll_windows=[7, 30],
    )

    print("Step 3: computing monthly climatology...")
    monthly_mean_csv = csv_dir / "monthly_climatology_mean.csv"
    monthly_std_csv = csv_dir / "monthly_climatology_std.csv"
    monthly_median_csv = csv_dir / "monthly_climatology_median.csv"
    compute_monthly_climatology(
        input_csv=all_daily_csv,
        baseline_start=baseline_start,
        baseline_end=baseline_end,
        output_mean_csv=monthly_mean_csv,
        output_std_csv=monthly_std_csv,
        output_median_csv=monthly_median_csv,
    )

    print("Step 4: extracting target year subset...")
    year_csv = csv_dir / f"daily_weather_{target_year}.csv"
    create_daily_summary_year_subset(
        input_csv=all_daily_csv,
        year=target_year,
        output_csv=year_csv,
    )

    print("Step 5: computing daily metrics for target year...")
    metrics_csv = csv_dir / f"daily_metrics_{target_year}.csv"
    compute_daily_metrics(
        input_csv=year_csv,
        baseline_csv=all_daily_csv,
        output_csv=metrics_csv,
        dry_threshold_mm=1.0,
        heat_threshold_C=33.0,
        windows=(7, 30),
    )

    print("Step 6: computing stage metrics + CYI...")

    stage_metric_summary_csv = csv_dir / f"stage_metric_summary_{target_year}.csv"
    stage_scores_cyi_csv = csv_dir / f"stage_scores_cyi_{target_year}.csv"

    compute_stage_cyi(
        metrics_csv=metrics_csv,
        stage_metric_summary_csv=stage_metric_summary_csv,
        stage_scores_cyi_csv=stage_scores_cyi_csv,
    )

    print("Step 7: plotting custom rain...")
    plot_custom_rain(year_csv, plot_dir / f"rain_{target_year}_daily_rolling.png")

    print("Step 8: plotting year vs baseline...")
    plot_year_vs_climatology(
        year_csv=year_csv,
        clim_mean_csv=daily_mean_csv,
        out_temp_plot=plot_dir / f"temperature_{target_year}_vs_baseline.png",
        title_year=target_year,
    )

    print("Step 9: plotting monthly rain CI...")
    plot_monthly_rain_ci(
        year_csv=year_csv,
        clim_mean_csv=monthly_mean_csv,
        clim_std_csv=monthly_std_csv,
        out_plot=plot_dir / f"rain_{target_year}_monthly_ci.png",
        title_year=target_year,
    )

    print("Pipeline complete.")


if __name__ == "__main__":
    run()

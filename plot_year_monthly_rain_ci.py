from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import calendar
from matplotlib.ticker import FixedLocator, NullFormatter, FixedFormatter
from matplotlib.patches import Patch


def plot_monthly_rain_ci(
    year_csv: Path,
    clim_mean_csv: Path,
    clim_std_csv: Path,
    out_plot: Path,
    title_year: int,
) -> Path:
    out_plot.parent.mkdir(parents=True, exist_ok=True)

    df_year = pd.read_csv(year_csv, parse_dates=["date"])
    clim_mean = pd.read_csv(clim_mean_csv)
    clim_std = pd.read_csv(clim_std_csv)

    df_year["month"] = df_year["date"].dt.month

    monthly_year = (
        df_year.groupby("month")["precip_mm"]
        .sum()
        .reset_index()
        .rename(columns={"precip_mm": "rain_year_mm"})
    )

    df_plot = (
        monthly_year
        .merge(clim_mean, on="month")
        .merge(clim_std, on="month")
    )

    df_plot["ci_lower"] = df_plot["monthly_mean_mm"] - 1.96 * df_plot["monthly_std_mm"]
    df_plot["ci_upper"] = df_plot["monthly_mean_mm"] + 1.96 * df_plot["monthly_std_mm"]
    df_plot["ci_lower"] = df_plot["ci_lower"].clip(lower=0)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    def _month_x(mmdd: str) -> float:
        dt = pd.Timestamp(f"{title_year}-{mmdd}")
        days_in_month = calendar.monthrange(dt.year, dt.month)[1]
        frac = (dt.day - 1) / days_in_month
        return (dt.month - 1) + frac

    stage_colors = {
        "Preparation": "#e6e0f3",
        "Planting": "#dcebdc",
        "Vegetative": "#dbe7f6",
        "Harvest": "#f3e2d7",
    }
    stage_spans = [
        ("Preparation", _month_x("03-15"), _month_x("05-15")),
        ("Planting", _month_x("05-16"), _month_x("06-30")),
        ("Vegetative", _month_x("07-01"), _month_x("09-15")),
        ("Harvest", _month_x("09-16"), _month_x("11-15")),
    ]

    for name, start_x, end_x in stage_spans:
        ax.axvspan(start_x, end_x, color=stage_colors[name], alpha=0.5, zorder=0)

    months = df_plot["month"]
    x = months - 0.5

    ax.fill_between(
        x,
        df_plot["ci_lower"],
        df_plot["ci_upper"],
        color="gray",
        alpha=0.25,
        label="Baseline 95% CI"
    )

    ax.plot(
        x,
        df_plot["monthly_mean_mm"],
        linestyle="--",
        color="black",
        linewidth=1.5,
        label="Baseline Mean"
    )

    ax.bar(
        x,
        df_plot["rain_year_mm"],
        color="#3b6fa5",
        alpha=0.95,
        label=f"Monthly Total"
    )

    ax.set_title(f"Monthly Rainfall vs 30-year Baseline \n Tamale, Ghana (2025)", y=1.08)
    ax.set_xlabel("Month")
    ax.set_ylabel("Rainfall (mm)")

    ax.set_xlim(0, 12)
    month_boundaries = list(range(0, 13))
    month_mids = [m + 0.5 for m in range(0, 12)]

    ax.xaxis.set_major_locator(FixedLocator(month_boundaries))
    ax.xaxis.set_major_formatter(NullFormatter())
    ax.xaxis.set_minor_locator(FixedLocator(month_mids))
    ax.xaxis.set_minor_formatter(FixedFormatter([calendar.month_abbr[i] for i in range(1, 13)]))
    ax.tick_params(axis="x", which="minor", length=0, pad=6)
    ax.tick_params(axis="x", which="major", length=4)

    ax.set_axisbelow(True)
    ax.grid(True, alpha=0.8)

    data_legend = ax.legend(frameon=False)
    ax.add_artist(data_legend)

    stage_handles = [Patch(facecolor=stage_colors[name], edgecolor="none", label=name) for name, _, _ in stage_spans]
    ax.legend(
        handles=stage_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.10),
        ncol=4,
        frameon=False,
    )

    plt.tight_layout()
    plt.savefig(out_plot, dpi=160)
    plt.close()

    print("Saved:", out_plot)
    return out_plot


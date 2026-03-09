from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import NullFormatter, FixedLocator
from matplotlib.patches import Patch


def plot_year_vs_climatology(
    year_csv: Path,
    clim_mean_csv: Path,
    out_temp_plot: Path,
    title_year: int,
) -> Path:
    out_temp_plot.parent.mkdir(parents=True, exist_ok=True)

    df_2025 = pd.read_csv(year_csv, parse_dates=["date"])
    clim = pd.read_csv(clim_mean_csv)

    df_2025["doy"] = df_2025["date"].dt.dayofyear

    df_2025 = df_2025[~((df_2025["date"].dt.month == 2) & (df_2025["date"].dt.day == 29))]

    df = df_2025.merge(clim, on="doy", suffixes=("", "_clim"))

    fig, ax = plt.subplots(figsize=(8, 4.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.fill_between(
        df["date"],
        df["tmin_C_clim"],
        df["tmax_C_clim"],
        color="gray",
        alpha=0.25,
        label="Baseline Avg Range"
    )

    ax.plot(df["date"], df["tmax_C"], color="#d33f49", linewidth=2, label=f"{title_year} High")
    ax.plot(df["date"], df["tmin_C"], color="#2c7fb8", linewidth=2, label=f"{title_year} Low")

    ax.set_title(f"Daily Temperature vs 30-year Baseline \n Tamale, Ghana (2025)", y=1.08)
    ax.set_ylabel("Temperature (°C)")
    ax.set_axisbelow(True)
    ax.grid(True, alpha=0.8)

    year_start = pd.Timestamp(title_year, 1, 1)
    year_end = pd.Timestamp(title_year, 12, 31)
    ax.set_xlim(year_start, year_end)

    month_starts = pd.date_range(year_start, year_end, freq="MS")
    month_mids = month_starts + pd.offsets.Day(14)

    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(NullFormatter())
    ax.xaxis.set_minor_locator(FixedLocator(mdates.date2num(month_mids)))
    ax.xaxis.set_minor_formatter(mdates.DateFormatter("%b"))
    ax.tick_params(axis="x", which="minor", length=0, pad=6)
    ax.tick_params(axis="x", which="major", length=4)

    stage_colors = {
        "Preparation": "#e6e0f3",
        "Planting": "#dcebdc",
        "Vegetative": "#dbe7f6",
        "Harvest": "#f3e2d7",
    }
    stages = [
        ("Preparation", "03-15", "05-15"),
        ("Planting", "05-16", "06-30"),
        ("Vegetative", "07-01", "09-15"),
        ("Harvest", "09-16", "11-15"),
    ]

    for name, start_mmdd, end_mmdd in stages:
        start = pd.Timestamp(f"{title_year}-{start_mmdd}")
        end = pd.Timestamp(f"{title_year}-{end_mmdd}")
        ax.axvspan(start, end, color=stage_colors[name], alpha=0.5, zorder=0)

    data_legend = ax.legend(frameon=False)
    ax.add_artist(data_legend)

    stage_handles = [Patch(facecolor=stage_colors[name], edgecolor="none", label=name) for name, _, _ in stages]
    ax.legend(
        handles=stage_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.10),
        ncol=4,
        frameon=False,
    )

    plt.tight_layout()
    plt.savefig(out_temp_plot, dpi=160)
    plt.close()

    print("Plot saved:")
    print("  ", out_temp_plot)

    return out_temp_plot


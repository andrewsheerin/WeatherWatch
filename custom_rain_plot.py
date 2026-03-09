# custom_rain_plot.py

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import NullFormatter, FixedLocator
from matplotlib.patches import Patch
import pandas as pd


def plot_custom_rain(year_csv: Path, out_plot: Path) -> Path:
    out_plot.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(year_csv, parse_dates=["date"])

    fig, ax = plt.subplots(figsize=(8, 4.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    daily_color = "#9cc4e4"
    rolling_7_color = "#3b6fa5"
    rolling_30_color = "#0b2d5b"

    ax.bar(df["date"], df["precip_mm"], color=daily_color, alpha=0.85, label="Daily Total")

    rolling_7 = df["precip_mm"].rolling(7).sum()
    rolling_30 = df["precip_mm"].rolling(30).sum()

    ax2 = ax.twinx()
    ax2.plot(df["date"], rolling_7, color=rolling_7_color, linewidth=2.1, label="7-day Rolling")
    ax2.plot(df["date"], rolling_30, color=rolling_30_color, linewidth=2.1, label="30-day Rolling")

    ax.set_ylim(bottom=0)
    ax2.set_ylim(bottom=0)

    ax.set_title("Daily Rolling Rainfall \n Tamale, Ghana (2025)", y=1.08)
    ax.set_xlabel("Date")
    ax.set_ylabel("Rain (mm)")
    ax2.set_ylabel("Rolling Total (mm)")
    ax.set_axisbelow(True)
    ax.grid(True, alpha=0.8)

    year = int(df["date"].dt.year.mode().iloc[0])
    year_start = pd.Timestamp(year, 1, 1)
    year_end = pd.Timestamp(year, 12, 31)
    ax.set_xlim(year_start, year_end)

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
        start = pd.Timestamp(f"{year}-{start_mmdd}")
        end = pd.Timestamp(f"{year}-{end_mmdd}")
        ax.axvspan(start, end, color=stage_colors[name], alpha=0.5, zorder=0)

    month_starts = pd.date_range(year_start, year_end, freq="MS")
    month_mids = month_starts + pd.offsets.Day(14)

    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(NullFormatter())
    ax.xaxis.set_minor_locator(FixedLocator(mdates.date2num(month_mids)))
    ax.xaxis.set_minor_formatter(mdates.DateFormatter("%b"))
    ax.tick_params(axis="x", which="minor", length=0, pad=6)
    ax.tick_params(axis="x", which="major", length=4)

    data_lines, data_labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    data_legend = ax.legend(
        data_lines + lines2,
        data_labels + labels2,
        frameon=False,
        loc="upper left",
    )
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
    plt.savefig(out_plot, dpi=160)
    plt.close()

    print("Saved:", out_plot)
    return out_plot


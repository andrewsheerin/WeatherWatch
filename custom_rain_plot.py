# custom_rain_plot.py

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd


def plot_custom_rain(year_csv: Path, out_plot: Path) -> Path:
    out_plot.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(year_csv, parse_dates=["date"])

    fig, ax = plt.subplots(figsize=(11, 5.2))
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#f8f8f8")

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

    ax.set_title("Rainfall")
    ax.set_xlabel("Date")
    ax.set_ylabel("Rain (mm)")
    ax2.set_ylabel("Rolling Total (mm)")
    ax.set_axisbelow(True)
    ax.grid(True, alpha=0.8)

    locator = mdates.AutoDateLocator(minticks=4, maxticks=10)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))

    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines + lines2, labels + labels2, frameon=False)

    plt.tight_layout()
    plt.savefig(out_plot, dpi=160)
    plt.close()

    print("Saved:", out_plot)
    return out_plot

